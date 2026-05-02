"""Ultra Key VideoFilterComponent — ClassID d10da199-…, MatchName AE.ADBE Ultra Key.

Per-clip green-screen chroma key on V6 multicam talent picks. Reverse-engineered
from EP106's Multicam_1 V6 Ultra Key (filter ObjectID 3399). 27 params; defaults
match 106's NBQ-talent green-screen key settings.

Param layout (27 params, ParameterIDs 1–27):
  0  Output (int)             — 0 (Composite)
  1  Setting (int)            — 3 (Aggressive)
  2  Key Color (color)        — 18374820623512797184 (NBQ green-screen green)
  3  Matte Generation (bool/header)
  4  Transparency (clamped)   — 40
  5  Highlight (clamped)      — 10
  6  Shadow (clamped)         — 55
  7  Tolerance (clamped)      — 90
  8  Pedestal (clamped)       — 50
  9  (unnamed bool, ParameterControlType=12)
  10 Matte Cleanup (bool/header, ControlType=11)
  11 Choke (clamped)          — 0
  12 Soften (clamped)         — 93
  13 Contrast (clamped)       — 24
  14 Mid Point (clamped)      — 14
  15 (unnamed bool, ParameterControlType=12)
  16 Spill Suppression (bool/header, ControlType=11)
  17 Desaturate (clamped)     — 0
  18 Range (clamped)          — 50
  19 Spill (clamped)          — 50
  20 Luma (clamped)           — 50
  21 (unnamed bool, ParameterControlType=12)
  22 Color Correction (bool/header, ControlType=11)
  23 Saturation (clamped)     — 100
  24 Hue (clamped)            — 0
  25 Luminance (clamped)      — 100
  26 (unnamed bool, ParameterControlType=12)
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from ..core.classids import (
    CID_VIDEO_FILTER_COMPONENT,
    CID_VIDEO_COMPONENT_PARAM_BOOL,
    CID_VIDEO_COMPONENT_PARAM_CLAMPED,
    CID_VIDEO_COMPONENT_PARAM_COLOR,
    CID_VIDEO_COMPONENT_PARAM_INT,
)
from ..core.seed_loader import IdFactory
from ..core.tick_math import start_keyframe as _start_keyframe


def _int_param(pid: str, name: str, parameter_id: int, value: int) -> ET.Element:
    p = ET.Element("VideoComponentParam", {
        "ObjectID": pid, "ClassID": CID_VIDEO_COMPONENT_PARAM_INT, "Version": "10",
    })
    ET.SubElement(p, "Name").text = name
    ET.SubElement(p, "ParameterID").text = str(parameter_id)
    ET.SubElement(p, "StartKeyframe").text = _start_keyframe(str(value))
    return p


def _color_param(pid: str, name: str, parameter_id: int, color: str) -> ET.Element:
    p = ET.Element("VideoComponentParam", {
        "ObjectID": pid, "ClassID": CID_VIDEO_COMPONENT_PARAM_COLOR, "Version": "10",
    })
    ET.SubElement(p, "Name").text = name
    ET.SubElement(p, "ParameterID").text = str(parameter_id)
    ET.SubElement(p, "StartKeyframe").text = _start_keyframe(color)
    return p


def _bool_param(pid: str, name: str, parameter_id: int, value: bool,
                control_type: int | None = None,
                with_upper_bound: bool = False) -> ET.Element:
    p = ET.Element("VideoComponentParam", {
        "ObjectID": pid, "ClassID": CID_VIDEO_COMPONENT_PARAM_BOOL, "Version": "10",
    })
    if name:
        # 106 omits <Name> for anonymous bool dividers — emit only when set.
        ET.SubElement(p, "Name").text = name
    ET.SubElement(p, "ParameterID").text = str(parameter_id)
    if control_type is not None:
        ET.SubElement(p, "ParameterControlType").text = str(control_type)
    ET.SubElement(p, "StartKeyframe").text = _start_keyframe("true" if value else "false")
    if with_upper_bound:
        # 106's anonymous control_type=12 bool params include this trailing element.
        ET.SubElement(p, "UpperBound").text = "false"
    return p


def _clamped_param(pid: str, name: str, parameter_id: int, value: float) -> ET.Element:
    p = ET.Element("VideoComponentParam", {
        "ObjectID": pid, "ClassID": CID_VIDEO_COMPONENT_PARAM_CLAMPED, "Version": "10",
    })
    ET.SubElement(p, "Name").text = name
    ET.SubElement(p, "ParameterID").text = str(parameter_id)
    ET.SubElement(p, "StartKeyframe").text = _start_keyframe(f"{value}.")
    return p


_TEMPLATES_DIR = Path("/Users/dandj/DevApps/roughcut-ai/tools/nbq/templates")
_UK0_SPEC_PATH = _TEMPLATES_DIR / "ultrakey_0_params_spec.json"
_UK1_SPEC_PATH = _TEMPLATES_DIR / "ultrakey_1_params_spec.json"


def _build_param_from_spec(entry: dict, fresh_id: str) -> ET.Element:
    """Recursively reconstruct an Ultra Key param element with fresh ObjectID."""
    attrib = dict(entry.get("attrib", {}))
    attrib["ObjectID"] = fresh_id
    el = ET.Element(entry["tag"], attrib)
    if entry.get("text"):
        el.text = entry["text"]
    for ch in entry.get("children", []):
        sub = ET.SubElement(el, ch["tag"], dict(ch.get("attrib", {})))
        if ch.get("text"):
            sub.text = ch["text"]
        for gc in ch.get("children", []):
            _append_recursive(sub, gc)
    return el


def _append_recursive(parent: ET.Element, entry: dict):
    el = ET.SubElement(parent, entry["tag"], dict(entry.get("attrib", {})))
    if entry.get("text"):
        el.text = entry["text"]
    for ch in entry.get("children", []):
        _append_recursive(el, ch)


def build_ultra_key_filter(ids: IdFactory, *, garbage_matte_id: str | None = None,
                           variant: str = "primary"
                           ) -> tuple[ET.Element, list[ET.Element], str]:
    """Build an Ultra Key VideoFilterComponent with EP106's NBQ green-screen defaults.

    Returns (filter_element, param_elements, filter_object_id). All elements
    must be appended to PremiereData root, and the filter_id must be added
    as a Component in the parent VideoComponentChain's Components list.
    """
    # Choose param spec by variant. nbq_person tunes its TWO Ultra Keys
    # differently (8 params differ between primary and refinement key).
    spec_path = _UK1_SPEC_PATH if variant == "refinement" else _UK0_SPEC_PATH
    spec = json.loads(spec_path.read_text())
    spec_params = spec["params"]

    filter_id = ids.fresh_id()
    pids = [ids.fresh_id() for _ in spec_params]
    elements: list[ET.Element] = []

    # The Ultra Key VideoFilterComponent. When `garbage_matte_id` is provided,
    # an AEMask2 SubComponent is wired in (matches nbq_person's Ultra Key #1
    # which uses the mask as a garbage matte for selective edge cleanup).
    f = ET.Element("VideoFilterComponent", {
        "ObjectID": filter_id, "ClassID": CID_VIDEO_FILTER_COMPONENT, "Version": "9",
    })
    comp = ET.SubElement(f, "Component", {"Version": "7"})
    params = ET.SubElement(comp, "Params", {"Version": "1"})
    for i, pid in enumerate(pids):
        ET.SubElement(params, "Param", {"Index": str(i), "ObjectRef": pid})
    ET.SubElement(comp, "DisplayName").text = "Ultra Key"
    if garbage_matte_id is not None:
        sub = ET.SubElement(f, "SubComponents", {"Version": "1"})
        ET.SubElement(sub, "SubComponent", {"Index": "0", "ObjectRef": garbage_matte_id})
    ET.SubElement(f, "MatchName").text = "AE.ADBE Ultra Key"
    ET.SubElement(f, "VideoFilterType").text = "2"
    elements.append(f)

    # Emit each param from spec (faithfully matches nbq_person's primary or
    # refinement key tuning per variant)
    for spec_entry, pid in zip(spec_params, pids):
        elements.append(_build_param_from_spec(spec_entry, pid))
    return f, elements, filter_id
