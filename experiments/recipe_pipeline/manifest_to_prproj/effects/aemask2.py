"""AEMask2 VideoFilterComponent — ClassID d10da199-…, MatchName AE.ADBE AEMask2.

Used as a garbage-matte SubComponent of an Ultra Key in NBQ talent treatment
for log footage. Reverse-engineered from
`experiments/PREMIERE PROJECTS/TESTS/nbq_person with luts and ec.prproj`.

27 params include scalars (Position, Scale, Anchor Point, Feather, Opacity,
Expansion, etc.), bools (visibility, transform-enable, …), ints (Blend Mode,
Type), plus 4 ArbVideoComponentParam binary blobs (Tracker x2, Path, User
Interactions). The Path blob carries the actual mask shape coordinates inline.

Builder pattern (matching motion.py / drop_shadow.py / ultra_key.py): emit a
clean filter envelope from scratch with fresh ObjectIDs; load the 27 param
definitions from a JSON spec (more compact than 27 hand-written _param()
calls). The spec is reverse-engineering reference, not a clone target — only
the param XML is constructed from spec data.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from ..core.classids import CID_VIDEO_FILTER_COMPONENT
from ..core.seed_loader import IdFactory


_AEMASK2_TEMPLATES_DIR = Path(
    "/Users/dandj/DevApps/roughcut-ai/tools/nbq/templates"
)
_AEMASK2_UK_SPEC_PATH = _AEMASK2_TEMPLATES_DIR / "aemask2_params_spec.json"
_AEMASK2_OPACITY_SPEC_PATH = _AEMASK2_TEMPLATES_DIR / "aemask2_opacity_params_spec.json"


def _build_param_from_spec(entry: dict, fresh_id: str) -> ET.Element:
    """Recursively reconstruct a param element with fresh ObjectID."""
    attrib = dict(entry.get("attrib", {}))
    attrib["ObjectID"] = fresh_id
    el = ET.Element(entry["tag"], attrib)
    if entry.get("text"):
        el.text = entry["text"]
    for ch in entry.get("children", []):
        # Children of params are typically leaf elements (Name, ParameterID,
        # StartKeyframe, etc.) — recurse anyway in case of nesting.
        sub_attrib = dict(ch.get("attrib", {}))
        sub = ET.SubElement(el, ch["tag"], sub_attrib)
        if ch.get("text"):
            sub.text = ch["text"]
        for gc in ch.get("children", []):
            _append_recursive(sub, gc)
    return el


def _append_recursive(parent: ET.Element, entry: dict):
    """Append a generic spec entry as a child element (no ObjectID rewrite —
    used for grandchildren of params, which don't carry ObjectIDs)."""
    el = ET.SubElement(parent, entry["tag"], dict(entry.get("attrib", {})))
    if entry.get("text"):
        el.text = entry["text"]
    for ch in entry.get("children", []):
        _append_recursive(el, ch)


def build_aemask2_filter(ids: IdFactory, *, variant: str = "ultra_key"
                         ) -> tuple[ET.Element, list[ET.Element], str]:
    """Build an AEMask2 VideoFilterComponent (mask) with nbq_person's defaults.

    Args:
        variant: "ultra_key" → garbage matte (UK's mask geometry, position
                 around 0.50:0.47). "opacity" → talent body mask (Opacity's
                 mask geometry, position around 0.45:0.56).

    Returns (filter_element, param_elements, filter_object_id). Wired as a
    SubComponent of either an Ultra Key (garbage matte) or an Opacity
    (body mask).
    """
    spec_path = (_AEMASK2_OPACITY_SPEC_PATH if variant == "opacity"
                 else _AEMASK2_UK_SPEC_PATH)
    spec = json.loads(spec_path.read_text())
    # Skip ArbVideoComponentParam entries whose StartKeyframeValue is BLOB-ONLY
    # (BinaryHash reference + empty inline text). Those carry editor session
    # state in Premiere's local cache and may not resolve cross-machine.
    # Params with inline base64 text (Path, plus Trackers/UI on the Opacity
    # mask) are self-contained — we keep those.
    def _is_blob_only(p):
        if p.get("tag") != "ArbVideoComponentParam":
            return False
        skv = next((c for c in p.get("children", []) if c["tag"] == "StartKeyframeValue"), None)
        if skv is None:
            return False
        return not (skv.get("text") or "").strip()
    param_specs = [p for p in spec["params"] if not _is_blob_only(p)]

    filter_id = ids.fresh_id()
    pids = [ids.fresh_id() for _ in param_specs]
    elements: list[ET.Element] = []

    # 1. AEMask2 VideoFilterComponent envelope (clean, no inner <ID>, no PFPD)
    f = ET.Element("VideoFilterComponent", {
        "ObjectID": filter_id,
        "ClassID": CID_VIDEO_FILTER_COMPONENT,
        "Version": "9",
    })
    comp = ET.SubElement(f, "Component", {"Version": "7"})
    params = ET.SubElement(comp, "Params", {"Version": "1"})
    for i, pid in enumerate(pids):
        ET.SubElement(params, "Param", {"Index": str(i), "ObjectRef": pid})
    ET.SubElement(comp, "DisplayName").text = "Mask2"
    ET.SubElement(f, "MatchName").text = "AE.ADBE AEMask2"
    ET.SubElement(f, "VideoFilterType").text = "2"
    elements.append(f)

    # 2. The 27 params, faithfully reconstructed from spec
    for spec_entry, pid in zip(param_specs, pids):
        elements.append(_build_param_from_spec(spec_entry, pid))

    return f, elements, filter_id
