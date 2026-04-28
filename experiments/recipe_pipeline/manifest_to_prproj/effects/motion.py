"""Motion VideoFilterComponent — ClassID d10da199-…, MatchName AE.ADBE Motion.

Used in Round 1 to compensate for source/sequence resolution mismatch — most
common case: 4K (2160h) source in a 1080p sequence, scale = 50%. Without this
override, Premiere shows the clip at native pixel size (i.e. cropped to the
center 1920×1080 of the 4K frame).

The 11-param layout, ClassIDs, and the chain-shape change required at the
VideoComponentChain level are documented in
Brain/Knowledge/API Integration/Premiere prproj Media Chain and Clip Placement Graph.md
under "Motion Scale override".

Round 3 will extend this to full position/rotation/anchor-point animation
keyframes for adjustment-layer Transform intents. For Round 1 every param
except Scale stays at default (single keyframe at the start anchor).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from ..core.classids import (
    CID_VIDEO_FILTER_COMPONENT,
    CID_VIDEO_COMPONENT_PARAM,
    CID_VIDEO_COMPONENT_PARAM_BOOL,
    CID_VIDEO_COMPONENT_PARAM_CLAMPED,
    CID_POINT_COMPONENT_PARAM,
)
from ..core.seed_loader import IdFactory
from ..core.tick_math import START_KEYFRAME_TICK, start_keyframe as _start_keyframe


def build_motion_filter(scale_pct: float, ids: IdFactory) -> tuple[ET.Element, list[ET.Element], str]:
    """Build a Motion VideoFilterComponent with custom Scale + default everything else.

    Returns (filter_element, param_elements, filter_object_id). All elements
    must be appended to PremiereData root.

    Param layout (from steak_tacos reference, IDs 924-934):
      0 Position (point)        — default 0.5,0.5
      1 Scale (scalar)           — set per call
      2 Scale Width (scalar)     — default 100 (ignored when uniform=true)
      3 Uniform Scale (bool)     — true
      4 Rotation (scalar)        — default 0
      5 Anchor Point (point)     — default 0.5,0.5
      6 Anti-flicker (clamped)   — default 0
      7 Crop Left (scalar)       — default 0
      8 Crop Top (scalar)        — default 0
      9 Crop Right (scalar)      — default 0
      10 Crop Bottom (scalar)    — default 0
    """
    filter_id = ids.fresh_id()
    pids = [ids.fresh_id() for _ in range(11)]

    elements: list[ET.Element] = []

    # The Motion VideoFilterComponent
    f = ET.Element("VideoFilterComponent", {
        "ObjectID": filter_id,
        "ClassID": CID_VIDEO_FILTER_COMPONENT,
        "Version": "9",
    })
    comp = ET.SubElement(f, "Component", {"Version": "7"})
    params = ET.SubElement(comp, "Params", {"Version": "1"})
    for i, pid in enumerate(pids):
        ET.SubElement(params, "Param", {"Index": str(i), "ObjectRef": pid})
    ET.SubElement(comp, "ID").text = "1"
    ET.SubElement(comp, "DisplayName").text = "Motion"
    ET.SubElement(comp, "Intrinsic").text = "true"
    # PremiereFilterPrivateData copied from steak_tacos's Motion (the "ARM=" blob is harmless)
    pfpd = ET.SubElement(f, "PremiereFilterPrivateData", {
        "Encoding": "base64",
        "BinaryHash": "4b0b6857-bf41-31a9-a7e7-0ca80000000e",
    })
    pfpd.text = "ARM="
    ET.SubElement(f, "MatchName").text = "AE.ADBE Motion"
    ET.SubElement(f, "VideoFilterType").text = "2"
    elements.append(f)

    def make_scalar_param(pid: str, name: str, parameter_id: int, start_value: str,
                          upper_ui: str, lower: str, upper: str) -> ET.Element:
        p = ET.Element("VideoComponentParam", {
            "ObjectID": pid,
            "ClassID": CID_VIDEO_COMPONENT_PARAM,
            "Version": "10",
        })
        ET.SubElement(p, "Name").text = name
        ET.SubElement(p, "ParameterID").text = str(parameter_id)
        ET.SubElement(p, "UpperUIBound").text = upper_ui
        ET.SubElement(p, "StartKeyframe").text = _start_keyframe(start_value)
        ET.SubElement(p, "LowerBound").text = lower
        ET.SubElement(p, "UpperBound").text = upper
        return p

    def make_point_param(pid: str, name: str, parameter_id: int, x: float, y: float) -> ET.Element:
        p = ET.Element("PointComponentParam", {
            "ObjectID": pid,
            "ClassID": CID_POINT_COMPONENT_PARAM,
            "Version": "4",
        })
        ET.SubElement(p, "Name").text = name
        ET.SubElement(p, "ParameterID").text = str(parameter_id)
        ET.SubElement(p, "StartKeyframe").text = (
            f"{START_KEYFRAME_TICK},{x}:{y},0,0,0,0,0,0,5,4,0,0,0,0"
        )
        return p

    def make_bool_param(pid: str, parameter_id: int, value: bool) -> ET.Element:
        p = ET.Element("VideoComponentParam", {
            "ObjectID": pid,
            "ClassID": CID_VIDEO_COMPONENT_PARAM_BOOL,
            "Version": "10",
        })
        ET.SubElement(p, "Name")  # empty name
        ET.SubElement(p, "ParameterID").text = str(parameter_id)
        ET.SubElement(p, "StartKeyframe").text = _start_keyframe("true" if value else "false")
        return p

    def make_clamped_param(pid: str, name: str, parameter_id: int, start_value: str) -> ET.Element:
        p = ET.Element("VideoComponentParam", {
            "ObjectID": pid,
            "ClassID": CID_VIDEO_COMPONENT_PARAM_CLAMPED,
            "Version": "10",
        })
        ET.SubElement(p, "Name").text = name
        ET.SubElement(p, "ParameterID").text = str(parameter_id)
        ET.SubElement(p, "StartKeyframe").text = _start_keyframe(start_value)
        return p

    elements.append(make_point_param(pids[0], "Position", 1, 0.5, 0.5))
    elements.append(make_scalar_param(pids[1], "Scale", 2, f"{scale_pct}.", "200", "0", "10000"))
    elements.append(make_scalar_param(pids[2], "Scale Width", 3, "100.", "200", "0", "10000"))
    elements.append(make_bool_param(pids[3], 4, True))
    elements.append(make_scalar_param(pids[4], "Rotation", 5, "0.", "360", "-3.40282346638528860e+38", "3.40282346638528860e+38"))
    elements.append(make_point_param(pids[5], "Anchor Point", 6, 0.5, 0.5))
    elements.append(make_clamped_param(pids[6], "Anti-flicker Filter", 7, "0."))
    elements.append(make_scalar_param(pids[7], "Crop Left", 8, "0.", "100", "0", "100"))
    elements.append(make_scalar_param(pids[8], "Crop Top", 9, "0.", "100", "0", "100"))
    elements.append(make_scalar_param(pids[9], "Crop Right", 10, "0.", "100", "0", "100"))
    elements.append(make_scalar_param(pids[10], "Crop Bottom", 11, "0.", "100", "0", "100"))

    return f, elements, filter_id
