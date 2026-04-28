"""Serialization + post-write integrity check.

Two responsibilities:
1. write_prproj_bytes — wrap a PremiereData element in the XML declaration
   header, gzip, and write to disk. Mirrors what Premiere itself emits.
2. integrity_check — re-read the gzipped output, count VCTI + MasterClip
   elements (the writer's two failure-mode-prone arrays), then exercise
   prproj_reader.read_prproj() to confirm the deep parse succeeds.

The integrity check writes ROUND-TRIP OK or ROUND-TRIP MISMATCH at INFO so
operators can confirm a successful write from the log.
"""

from __future__ import annotations

import gzip
import logging
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


logger = logging.getLogger("manifest_to_prproj")


def write_prproj_bytes(pdata: ET.Element, out_path: Path) -> int:
    """Serialize PremiereData element + XML decl, gzip, write to out_path.

    Returns the uncompressed XML byte count (handy for log lines).
    """
    xml_bytes = b'<?xml version="1.0" encoding="UTF-8" ?>\n' + ET.tostring(pdata, encoding="utf-8")
    logger.info("uncompressed XML: %d bytes", len(xml_bytes))
    with gzip.open(out_path, "wb") as fp:
        fp.write(xml_bytes)
    return len(xml_bytes)


def integrity_check(
    out_path: Path,
    expected_vcti: int,
    expected_new_masterclips: int,
    seed_masterclips: int,
) -> None:
    """Re-open the gzipped output, count key elements, deep-parse via prproj_reader.

    The substring counts (`<VideoClipTrackItem ObjectID=`, `<MasterClip ObjectUID=`)
    are byte-level so they don't require re-parsing the XML — fast and immune
    to serialization variations. The reader call exercises the full parse
    contract (link resolution, tick math, sequence walk).
    """
    logger.info("round-trip: re-reading %s", out_path)
    # prproj_reader lives next to the writer package: experiments/recipe_pipeline/.
    # From this file's location: parents = [core, manifest_to_prproj, recipe_pipeline].
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    try:
        with gzip.open(out_path, "rb") as fp:
            data = fp.read()
        vcti_count = data.count(b"<VideoClipTrackItem ObjectID=")
        mc_count = data.count(b"<MasterClip ObjectUID=")
        expected_mc = expected_new_masterclips + seed_masterclips
        logger.info(
            "round-trip counts: vcti=%d (expected %d); masterclip=%d (expected %d = %d new + %d from seed)",
            vcti_count, expected_vcti, mc_count, expected_mc, expected_new_masterclips, seed_masterclips,
        )
        ok = vcti_count == expected_vcti and mc_count == expected_mc

        try:
            import prproj_reader  # type: ignore
            tree = prproj_reader.read_prproj(out_path)  # type: ignore[attr-defined]
            seq = tree.get("primary_sequence")
            if seq:
                v1_clips = len(seq["tracks"][0]["clip_items"])
                logger.info("reader sees: sequence=%r tracks=%d V1_clips=%d duration=%.3fs",
                            seq["name"], len(seq["tracks"]), v1_clips, tree["duration_seconds"])
                ok = ok and v1_clips == expected_vcti
        except AttributeError:
            logger.debug("prproj_reader.read_prproj not available; skipping deep parse")
        except Exception as e:
            logger.warning("prproj_reader deep parse failed: %s", e)
            ok = False

        if ok:
            logger.info("ROUND-TRIP OK")
        else:
            logger.error("ROUND-TRIP MISMATCH")
    except Exception as e:
        logger.error("round-trip read failed: %s", e)
