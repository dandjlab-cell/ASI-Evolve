"""Bin construction + root/track mutation helpers for the seed prproj.

Two responsibilities:

1. build_bin — emits a fresh BinProjectItem (matches BIN_FLAT shape with
   icon-grid order property + a Name + a list of child ObjectURefs).

2. mutators on the seed's existing structure: locating the RootProjectItem,
   the V1 VideoClipTrack, the seed's pre-existing VCTI; clearing/repopulating
   the root bin's Items list; clearing/repopulating the V1 track's TrackItems
   list; classifying root ClipProjectItems as 'sequence' vs 'media' for
   reparent routing (sequence → 1_CUTS, media → 2_FOOTAGE, anything else
   orphaned and invisible in Premiere).

The classification heuristic is explained inline in
classify_root_clip_project_item — short version: walk MasterClip→Clip→Source
fails for sequence-backed MasterClips because they reference an AudioClip at
the same Clip level (not a VideoClip). Name-matching against the document's
<Sequence><Name> values is robust.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Optional

from .classids import CID_BIN_PROJECT_ITEM
from .seed_loader import IdFactory


def build_bin(name: str, ids: IdFactory, child_urefs: list[str]) -> tuple[ET.Element, str]:
    """BinProjectItem matching the BIN_FLAT shape. Returns (element, ObjectUID)."""
    uid = ids.fresh_uid()
    bin_el = ET.Element("BinProjectItem", {
        "ObjectUID": uid,
        "ClassID": CID_BIN_PROJECT_ITEM,
        "Version": "1",
    })
    project_item = ET.SubElement(bin_el, "ProjectItem", {"Version": "1"})
    node = ET.SubElement(project_item, "Node", {"Version": "1"})
    props = ET.SubElement(node, "Properties", {"Version": "1"})
    ET.SubElement(props, "project.icon.view.grid.order").text = "0"
    ET.SubElement(project_item, "Name").text = name

    container = ET.SubElement(bin_el, "ProjectItemContainer", {"Version": "1"})
    items = ET.SubElement(container, "Items", {"Version": "1"})
    for i, uref in enumerate(child_urefs):
        ET.SubElement(items, "Item", {"Index": str(i), "ObjectURef": uref})
    return bin_el, uid


def find_root_project_item(premiere_data: ET.Element) -> ET.Element:
    for el in premiere_data:
        if el.tag == "RootProjectItem" and "ObjectUID" in el.attrib:
            return el
    raise RuntimeError("RootProjectItem not found")


def find_v1_clip_track(premiere_data: ET.Element) -> ET.Element:
    """Return the first VideoClipTrack element with ObjectUID (the V1 track)."""
    for el in premiere_data:
        if el.tag == "VideoClipTrack" and "ObjectUID" in el.attrib:
            return el
    raise RuntimeError("V1 VideoClipTrack not found")


def find_existing_vcti(premiere_data: ET.Element) -> Optional[ET.Element]:
    for el in premiere_data:
        if el.tag == "VideoClipTrackItem" and "ObjectID" in el.attrib:
            return el
    return None


def replace_root_bin_items(root_bin: ET.Element, new_urefs: list[str]) -> None:
    container = root_bin.find("ProjectItemContainer")
    items = container.find("Items")
    # Clear and repopulate
    for child in list(items):
        items.remove(child)
    for i, uref in enumerate(new_urefs):
        ET.SubElement(items, "Item", {"Index": str(i), "ObjectURef": uref})


def replace_v1_clip_items(v1_track: ET.Element, vcti_ids: list[str]) -> None:
    clip_items = v1_track.find("ClipTrack/ClipItems")
    track_items = clip_items.find("TrackItems")
    for child in list(track_items):
        track_items.remove(child)
    for i, oid in enumerate(vcti_ids):
        ET.SubElement(track_items, "TrackItem", {"Index": str(i), "ObjectRef": oid})


def remove_existing_vcti(premiere_data: ET.Element) -> None:
    for el in list(premiere_data):
        if el.tag == "VideoClipTrackItem" and "ObjectID" in el.attrib:
            premiere_data.remove(el)


def classify_root_clip_project_item(
    cpi_uref: str, premiere_data: ET.Element
) -> str:
    """Classify a root ClipProjectItem as 'sequence' or 'media'.

    Heuristic: if the document contains a `<Sequence>` element whose `<Name>`
    matches the ClipProjectItem's `<Name>`, treat it as a sequence project item.
    Otherwise it's media.

    Walking the MasterClip→Clip→Source chain doesn't work for sequences because
    sequence-backed MasterClips reference an AudioClip at the same Clip level
    (not a VideoClip), and the chain to VideoSequenceSource is not as clean as
    media-backed clips. Name-matching is robust because Premiere keeps the
    ClipProjectItem name in lockstep with the Sequence name.
    """
    cpi = next(
        (e for e in premiere_data
         if e.tag == "ClipProjectItem" and e.get("ObjectUID") == cpi_uref),
        None,
    )
    if cpi is None:
        return "unknown"
    name_el = cpi.find("ProjectItem/Name")
    if name_el is None or not name_el.text:
        return "unknown"
    name = name_el.text

    sequence_names = {
        s.find("Name").text
        for s in premiere_data
        if s.tag == "Sequence"
        and "ObjectUID" in s.attrib
        and s.find("Name") is not None
        and s.find("Name").text
    }
    return "sequence" if name in sequence_names else "media"
