"""Drop Shadow VideoFilterComponent — ClassID d10da199-…, MatchName AE.ADBE Drop Shadow.

Per-clip composite shadow on V6 multicam picks. Reverse-engineered from
EP106's Multicam_1 V6 Drop Shadow (filter ObjectID 3397). Default values
match 106's NBQ-talent-over-BG-plate look.

Param layout (6 params, ParameterIDs 1–6):
  0  Shadow Color (color)        — default 18374686479671623680 (encoded RGBA)
  1  Opacity (scalar 0-255)      — default 176.999801635742
  2  Direction (scalar w/CT=3)   — default 479
  3  Distance (scalar 0-4000)    — default 186, UpperUI=120
  4  Softness (scalar 0-30000)   — default 641, UpperUI=250
  5  Shadow Only (bool)          — default false

Mirrors `effects/motion.py`'s build pattern: emit from scratch with fresh
ObjectIDs, no XML cloning. See feedback memory:
~/.claude/projects/-Users-dandj-DevApps-roughcut-ai/memory/feedback_reverse_engineer_dont_clone.md
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from ..core.classids import (
    CID_VIDEO_FILTER_COMPONENT,
    CID_VIDEO_COMPONENT_PARAM,
    CID_VIDEO_COMPONENT_PARAM_BOOL,
    CID_VIDEO_COMPONENT_PARAM_COLOR,
)
from ..core.seed_loader import IdFactory
from ..core.tick_math import start_keyframe as _start_keyframe


def build_drop_shadow_filter(ids: IdFactory) -> tuple[ET.Element, list[ET.Element], str]:
    """Build a Drop Shadow VideoFilterComponent with EP106's NBQ defaults.

    Returns (filter_element, param_elements, filter_object_id). All elements
    must be appended to PremiereData root, and the filter_id must be added
    as a Component in the parent VideoComponentChain's Components list.
    """
    filter_id = ids.fresh_id()
    pids = [ids.fresh_id() for _ in range(6)]

    elements: list[ET.Element] = []

    # The Drop Shadow VideoFilterComponent
    f = ET.Element("VideoFilterComponent", {
        "ObjectID": filter_id,
        "ClassID": CID_VIDEO_FILTER_COMPONENT,
        "Version": "9",
    })
    comp = ET.SubElement(f, "Component", {"Version": "7"})
    params = ET.SubElement(comp, "Params", {"Version": "1"})
    for i, pid in enumerate(pids):
        ET.SubElement(params, "Param", {"Index": str(i), "ObjectRef": pid})
    ET.SubElement(comp, "DisplayName").text = "Drop Shadow"
    # Per-clip Drop Shadow is NOT intrinsic (no <Intrinsic>true</Intrinsic>) — Motion is.
    ET.SubElement(f, "MatchName").text = "AE.ADBE Drop Shadow"
    ET.SubElement(f, "VideoFilterType").text = "2"
    elements.append(f)

    # Param 0: Shadow Color
    p0 = ET.Element("VideoComponentParam", {
        "ObjectID": pids[0],
        "ClassID": CID_VIDEO_COMPONENT_PARAM_COLOR,
        "Version": "10",
    })
    ET.SubElement(p0, "Name").text = "Shadow Color"
    ET.SubElement(p0, "ParameterID").text = "1"
    ET.SubElement(p0, "StartKeyframe").text = _start_keyframe("18374686479671623680")
    elements.append(p0)

    # Param 1: Opacity (0-255)
    p1 = ET.Element("VideoComponentParam", {
        "ObjectID": pids[1],
        "ClassID": CID_VIDEO_COMPONENT_PARAM,
        "Version": "10",
    })
    ET.SubElement(p1, "Name").text = "Opacity"
    ET.SubElement(p1, "ParameterID").text = "2"
    ET.SubElement(p1, "StartKeyframe").text = _start_keyframe("176.999801635742")
    ET.SubElement(p1, "LowerBound").text = "0"
    ET.SubElement(p1, "UpperBound").text = "255"
    elements.append(p1)

    # Param 2: Direction (with ParameterControlType=3, dial)
    p2 = ET.Element("VideoComponentParam", {
        "ObjectID": pids[2],
        "ClassID": CID_VIDEO_COMPONENT_PARAM,
        "Version": "10",
    })
    ET.SubElement(p2, "Name").text = "Direction"
    ET.SubElement(p2, "ParameterID").text = "3"
    ET.SubElement(p2, "ParameterControlType").text = "3"
    ET.SubElement(p2, "StartKeyframe").text = _start_keyframe("479.")
    ET.SubElement(p2, "LowerBound").text = "-32768"
    ET.SubElement(p2, "UpperBound").text = "32767"
    elements.append(p2)

    # Param 3: Distance
    p3 = ET.Element("VideoComponentParam", {
        "ObjectID": pids[3],
        "ClassID": CID_VIDEO_COMPONENT_PARAM,
        "Version": "10",
    })
    ET.SubElement(p3, "Name").text = "Distance"
    ET.SubElement(p3, "ParameterID").text = "4"
    ET.SubElement(p3, "UpperUIBound").text = "120"
    ET.SubElement(p3, "StartKeyframe").text = _start_keyframe("186.")
    ET.SubElement(p3, "LowerBound").text = "0"
    ET.SubElement(p3, "UpperBound").text = "4000"
    elements.append(p3)

    # Param 4: Softness
    p4 = ET.Element("VideoComponentParam", {
        "ObjectID": pids[4],
        "ClassID": CID_VIDEO_COMPONENT_PARAM,
        "Version": "10",
    })
    ET.SubElement(p4, "Name").text = "Softness"
    ET.SubElement(p4, "ParameterID").text = "5"
    ET.SubElement(p4, "UpperUIBound").text = "250"
    ET.SubElement(p4, "StartKeyframe").text = _start_keyframe("641.")
    ET.SubElement(p4, "LowerBound").text = "0"
    ET.SubElement(p4, "UpperBound").text = "30000"
    elements.append(p4)

    # Param 5: Shadow Only (bool)
    p5 = ET.Element("VideoComponentParam", {
        "ObjectID": pids[5],
        "ClassID": CID_VIDEO_COMPONENT_PARAM_BOOL,
        "Version": "10",
    })
    ET.SubElement(p5, "Name").text = "Shadow Only"
    ET.SubElement(p5, "ParameterID").text = "6"
    ET.SubElement(p5, "StartKeyframe").text = _start_keyframe("false")
    elements.append(p5)

    return f, elements, filter_id
