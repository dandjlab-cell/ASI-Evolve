"""Lumetri Color VideoFilterComponent — ClassID d10da199-…, MatchName AE.ADBE Lumetri.

Per-clip color grade applied to V6 multicam talent picks. Lumetri has 130 params
(106 VideoComponentParam + 24 ArbVideoComponentParam for binary-blob settings
like LUTs and curves). The "iShares look" is encoded in those binary blobs.

Reverse-engineered from EP106's Multicam_1 V6 Lumetri (filter ObjectID 3398).
Param spec is data-driven (loaded from tools/nbq/templates/lumetri_spec.json)
to avoid hand-authoring 130 elements.

Across 106's 119 Lumetri instances, 93 of 106 scalar params are constant
(the canonical grade); 13 vary per-clip (editor-tweaked). We emit the
canonical-grade values from Multicam_1 — matches majority of clips.

The 24 ArbVideoComponentParam elements have `<StartKeyframeValue>` with
`Encoding="base64"` + `BinaryHash="..."` attributes. The actual binary data
isn't in the prproj XML — it lives in a Premiere local cache keyed by
BinaryHash. Cloning the BinaryHash gets the look IF Premiere has 106's
cache; otherwise the filter applies with default (no-grade) settings.

Mirrors `effects/motion.py`'s build pattern (no XML cloning).
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from ..core.classids import CID_VIDEO_FILTER_COMPONENT
from ..core.seed_loader import IdFactory


LUMETRI_SPEC_PATH = (
    Path(__file__).resolve().parents[3]
    / "roughcut-ai" / "tools" / "nbq" / "templates" / "lumetri_spec.json"
)
# Fallback location for spec if running outside the canonical layout
_FALLBACK_SPEC = Path("/Users/dandj/DevApps/roughcut-ai/tools/nbq/templates/lumetri_spec.json")


def _load_spec() -> list[dict]:
    path = LUMETRI_SPEC_PATH if LUMETRI_SPEC_PATH.exists() else _FALLBACK_SPEC
    return json.loads(path.read_text())


def _build_from_spec(entry: dict, override_attribs: dict | None = None) -> ET.Element:
    """Recursively reconstruct an XML element from a serialized spec entry.

    Spec entry shape: {tag, attrib, text, tail, children: [...]}.
    `override_attribs` lets the caller replace attributes (e.g., set a fresh
    ObjectID) on the top-level element only.
    """
    attrib = dict(entry.get("attrib", {}))
    if override_attribs:
        attrib.update(override_attribs)
    el = ET.Element(entry["tag"], attrib)
    if entry.get("text"):
        el.text = entry["text"]
    for ch in entry.get("children", []):
        el.append(_build_from_spec(ch))
    return el


def build_lumetri_filter(ids: IdFactory) -> tuple[ET.Element, list[ET.Element], str]:
    """Build a Lumetri VideoFilterComponent with EP106's NBQ canonical grade.

    Returns (filter_element, param_elements, filter_object_id). All elements
    must be appended to PremiereData root, and the filter_id must be added
    as a Component in the parent VideoComponentChain's Components list.
    """
    # FIXED: emit all 130 params from spec
    spec = _load_spec()
    filter_id = ids.fresh_id()
    pids = [ids.fresh_id() for _ in spec]
    elements: list[ET.Element] = []

    # 1. The Lumetri VideoFilterComponent — bare envelope, NO PFPD.
    # PFPD's BinaryHash points to a Premiere local cache that 106 wrote when
    # the iShares grade was authored. That cache doesn't exist on a fresh
    # install / different machine, so emitting PFPD with 106's hash makes
    # Premiere reject the project on load. Without PFPD the Lumetri filter
    # exists on every clip with default-ish settings (encoded by the 130
    # params we emit); editor can apply a saved .lrtemplate / .cube LUT or
    # paste a graded clip's settings to all V6 picks for the final look.
    f = ET.Element("VideoFilterComponent", {
        "ObjectID": filter_id,
        "ClassID": CID_VIDEO_FILTER_COMPONENT,
        "Version": "9",
    })
    comp = ET.SubElement(f, "Component", {"Version": "7"})
    params = ET.SubElement(comp, "Params", {"Version": "1"})
    for i, pid in enumerate(pids):
        ET.SubElement(params, "Param", {"Index": str(i), "ObjectRef": pid})
    ET.SubElement(comp, "DisplayName").text = "Lumetri Color"
    ET.SubElement(f, "MatchName").text = "AE.ADBE Lumetri"
    ET.SubElement(f, "VideoFilterType").text = "2"
    elements.append(f)

    # 2. Each of the 130 param elements, faithfully reconstructed from spec
    # (preserves full nested structure including <Node><Properties> on the 10
    # ArbVideoComponentParam entries that have ECP.Custom.Expanded).
    for spec_entry, pid in zip(spec, pids):
        p = _build_from_spec(spec_entry, override_attribs={"ObjectID": pid})
        elements.append(p)

    return f, elements, filter_id
