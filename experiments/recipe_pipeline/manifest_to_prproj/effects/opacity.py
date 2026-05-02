"""Opacity VideoFilterComponent — ClassID d10da199-…, MatchName AE.ADBE Opacity.

Per-clip opacity control on V6 multicam talent. Reverse-engineered from
`nbq_person with luts and ec.prproj`'s talent treatment chain.

Param layout (3 params, ParameterIDs 1–3):
  0  Opacity (scalar 0-100)              — default 100 (fully opaque)
  1  Blend Mode (int 0-27, ControlType=10) — default 18
  2  Blend Mode (int 0-31)                — default 0

Mirrors `effects/motion.py` build pattern. Intrinsic=true matches Premiere's
treatment of Opacity as a built-in component (slot ID 2 conventionally).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from ..core.classids import (
    CID_VIDEO_FILTER_COMPONENT,
    CID_VIDEO_COMPONENT_PARAM,
    CID_VIDEO_COMPONENT_PARAM_INT,
)
from ..core.seed_loader import IdFactory
from ..core.tick_math import start_keyframe as _start_keyframe


def build_opacity_filter(ids: IdFactory, *, body_mask_id: str | None = None
                         ) -> tuple[ET.Element, list[ET.Element], str]:
    """Build an Opacity VideoFilterComponent with nbq_person's defaults.

    When `body_mask_id` is provided, wires an AEMask2 SubComponent (talent
    body mask — opacity-clips the talent outline). Matches nbq_person's
    talent treatment for log footage.

    Returns (filter_element, param_elements, filter_object_id).
    """
    filter_id = ids.fresh_id()
    pids = [ids.fresh_id() for _ in range(3)]
    elements: list[ET.Element] = []

    f = ET.Element("VideoFilterComponent", {
        "ObjectID": filter_id,
        "ClassID": CID_VIDEO_FILTER_COMPONENT,
        "Version": "9",
    })
    comp = ET.SubElement(f, "Component", {"Version": "7"})
    params = ET.SubElement(comp, "Params", {"Version": "1"})
    for i, pid in enumerate(pids):
        ET.SubElement(params, "Param", {"Index": str(i), "ObjectRef": pid})
    # <ID>2</ID> + <Intrinsic>true</Intrinsic> tells Premiere this Opacity
    # REPLACES the default-intrinsic Opacity (slot 2). Without these, you'd
    # get two Opacities — the default + this custom — duplicating the param.
    ET.SubElement(comp, "ID").text = "2"
    ET.SubElement(comp, "DisplayName").text = "Opacity"
    ET.SubElement(comp, "Intrinsic").text = "true"
    if body_mask_id is not None:
        sub = ET.SubElement(f, "SubComponents", {"Version": "1"})
        ET.SubElement(sub, "SubComponent", {"Index": "0", "ObjectRef": body_mask_id})
    ET.SubElement(f, "MatchName").text = "AE.ADBE Opacity"
    ET.SubElement(f, "VideoFilterType").text = "2"
    elements.append(f)

    # Param 0 (PID 1): Opacity 0-100, default 100
    p0 = ET.Element("VideoComponentParam", {
        "ObjectID": pids[0],
        "ClassID": CID_VIDEO_COMPONENT_PARAM,
        "Version": "10",
    })
    ET.SubElement(p0, "Name").text = "Opacity"
    ET.SubElement(p0, "ParameterID").text = "1"
    ET.SubElement(p0, "StartKeyframe").text = _start_keyframe("100.")
    ET.SubElement(p0, "LowerBound").text = "0"
    ET.SubElement(p0, "UpperBound").text = "100"
    elements.append(p0)

    # Param 1 (PID 2): Blend Mode int 0-27, default 18, ControlType=10
    p1 = ET.Element("VideoComponentParam", {
        "ObjectID": pids[1],
        "ClassID": CID_VIDEO_COMPONENT_PARAM_INT,
        "Version": "10",
    })
    ET.SubElement(p1, "Name").text = "Blend Mode"
    ET.SubElement(p1, "DiscontinuousInterpolate").text = "true"
    ET.SubElement(p1, "ParameterID").text = "2"
    ET.SubElement(p1, "ParameterControlType").text = "10"
    ET.SubElement(p1, "StartKeyframe").text = _start_keyframe("18")
    ET.SubElement(p1, "LowerBound").text = "0"
    ET.SubElement(p1, "UpperBound").text = "27"
    elements.append(p1)

    # Param 2 (PID 3): Blend Mode int 0-31, default 0
    p2 = ET.Element("VideoComponentParam", {
        "ObjectID": pids[2],
        "ClassID": CID_VIDEO_COMPONENT_PARAM_INT,
        "Version": "10",
    })
    ET.SubElement(p2, "Name").text = "Blend Mode"
    ET.SubElement(p2, "DiscontinuousInterpolate").text = "true"
    ET.SubElement(p2, "ParameterID").text = "3"
    ET.SubElement(p2, "StartKeyframe").text = _start_keyframe("0")
    ET.SubElement(p2, "LowerBound").text = "0"
    ET.SubElement(p2, "UpperBound").text = "31"
    elements.append(p2)

    return f, elements, filter_id
