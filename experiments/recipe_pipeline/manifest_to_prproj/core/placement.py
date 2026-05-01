"""Per-placement clip emission — the THREE-hop placement chain.

For each timeline entry the writer emits:

  VideoClipTrackItem (VCTI)        — own ObjectID, lives on V1 ClipTrack.TrackItems
    └─ ClipTrackItem
         ├─ TrackItem.Start, .End  (timeline-coord ticks)
         ├─ ComponentOwner.Components ObjectRef ─▶ VideoComponentChain (always emitted, see below)
         └─ SubClip ObjectRef           ─▶ SubClip element (own ClassID e0c58dc9-…)
                                              ├─ Clip ObjectRef ─▶ subclip VideoClip
                                              └─ MasterClip ObjectURef ─▶ media's MasterClip

  VideoComponentChain (VCC)         — required even when the clip has no effects.
                                       If this dangles, the timeline silently
                                       renders blank (soft fail — no error
                                       dialog). Two shapes:
                                       (a) DEFAULT — emits DefaultMotion=true
                                           + MZ.ComponentChain.* properties
                                       (b) CUSTOM (when motion_filter passed) —
                                           drops DefaultMotion + MZ props,
                                           emits a Components list with the
                                           filter ObjectRef. Matches steak_tacos.

  Subclip VideoClip                 — has InPoint/OutPoint pointing into source
                                       coords. Reuses the master's Markers and
                                       VideoMediaSource (one per source, NOT
                                       per placement).

The PlaybackSpeed insertion lives here. To avoid zebra bars at the clip's
tail, the speed is recomputed from tick-exact source/timeline durations
inside this function (passing through TICKS_PER_SECOND division loses bits).
The float is written with repr() — full 17-digit precision, NOT :.6f.

The SubClip indirection layer is the gotcha that broke initial Round 1
attempts — the original writer-plan diagram showed VCTI→VideoClip directly.
That's wrong. SubClip is its own element type with ClassID e0c58dc9-… .

To keep core/ free of effect-specific code, this function does NOT call
build_motion_filter. Instead, the orchestrator (or a future effect emitter
registry) builds the motion filter elements and passes them in via
`motion_filter`. That keeps the core→effects import direction clean.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Callable, Optional

from .classids import (
    CID_VIDEO_CLIP_TRACK_ITEM,
    CID_SUB_CLIP,
    CID_VIDEO_CLIP,
    CID_VIDEO_COMPONENT_CHAIN,
    CID_AUDIO_CLIP_TRACK_ITEM,
    CID_AUDIO_CLIP,
    CID_AUDIO_COMPONENT_CHAIN,
    CID_SECONDARY_CONTENT,
    CID_LINK,
)
from .seed_loader import IdFactory


# Type alias for a deferred motion-filter builder. The placement function
# allocates its own IDs first (vcti, subclip, video clip, components), then
# invokes this callable to build the motion filter. This preserves the ID
# allocation order from the pre-refactor code (where build_motion_filter was
# called inline INSIDE build_clip_placement), so ObjectID values stay byte-
# identical to the pre-refactor output. The factory is bound to its scale_pct
# at the orchestrator's call site.
MotionFilterFactory = Callable[[IdFactory], tuple[ET.Element, list[ET.Element], str]]


def build_clip_placement(
    media_chain: dict,
    timeline_in_ticks: int,
    timeline_out_ticks: int,
    source_in_ticks: int,
    source_out_ticks: int,
    ids: IdFactory,
    playback_speed: Optional[float] = None,
    motion_filter_factory: Optional[MotionFilterFactory] = None,
) -> dict:
    """Build VideoClipTrackItem + SubClip element + subclip VideoClip + VideoComponentChain
    for one placement.

    Args:
      media_chain: result of build_media_chain — must include
                   master_clip_uid, video_media_source_id, markers_id, name.
      timeline_in_ticks/timeline_out_ticks: timeline-coord placement bounds.
      source_in_ticks/source_out_ticks: source-coord cut bounds.
      playback_speed: when not None and != 1.0, emits a <PlaybackSpeed>
                      element on the subclip VideoClip's Clip block. The
                      tick-exact ratio is recomputed inside (the caller's
                      seconds-based estimate is just a "should-emit?" gate).
      motion_filter_factory: optional callable that takes the IdFactory and
                              returns (filter_element, param_elements,
                              filter_id) — typically a partial of
                              effects.motion.build_motion_filter bound to a
                              scale_pct. When provided, the VideoComponentChain
                              switches from default to custom shape and the
                              filter elements are appended to the placement's
                              element list. The callable is invoked AFTER the
                              placement's own ID allocations, matching the
                              pre-refactor ID assignment order.

    Returns:
      {"elements": list[ET.Element], "vcti_id": str}
    """
    vcti_id = ids.fresh_id()
    subclip_element_id = ids.fresh_id()
    video_clip_id = ids.fresh_id()
    components_id = ids.fresh_id()

    elements: list[ET.Element] = []

    # 1. VideoClipTrackItem
    vcti = ET.Element("VideoClipTrackItem", {
        "ObjectID": vcti_id,
        "ClassID": CID_VIDEO_CLIP_TRACK_ITEM,
        "Version": "8",
    })
    cti = ET.SubElement(vcti, "ClipTrackItem", {"Version": "8"})
    co = ET.SubElement(cti, "ComponentOwner", {"Version": "1"})
    ET.SubElement(co, "Components", {"ObjectRef": components_id})
    ti = ET.SubElement(cti, "TrackItem", {"Version": "4"})
    ET.SubElement(ti, "Start").text = str(timeline_in_ticks)
    ET.SubElement(ti, "End").text = str(timeline_out_ticks)
    ET.SubElement(cti, "SubClip", {"ObjectRef": subclip_element_id})
    ET.SubElement(vcti, "PixelAspectRatio").text = "1,1"
    ET.SubElement(vcti, "ToneMapSettings").text = '{"peak":-1,"version":3}'
    ET.SubElement(vcti, "FrameRect").text = "0,0,1920,1080"
    elements.append(vcti)

    # 2. SubClip element (the indirection layer between VCTI and VideoClip)
    sub = ET.Element("SubClip", {
        "ObjectID": subclip_element_id,
        "ClassID": CID_SUB_CLIP,
        "Version": "6",
    })
    ET.SubElement(sub, "Clip", {"ObjectRef": video_clip_id})
    ET.SubElement(sub, "MasterClip", {"ObjectURef": media_chain["master_clip_uid"]})
    ET.SubElement(sub, "Name").text = media_chain["name"]
    ET.SubElement(sub, "OrigChGrp").text = "0"
    elements.append(sub)

    # 3. VideoClip (the subclip on timeline; has InPoint/OutPoint into the source)
    vc = ET.Element("VideoClip", {
        "ObjectID": video_clip_id,
        "ClassID": CID_VIDEO_CLIP,
        "Version": "11",
    })
    clip = ET.SubElement(vc, "Clip", {"Version": "18"})
    cnode = ET.SubElement(clip, "Node", {"Version": "1"})
    cprops = ET.SubElement(cnode, "Properties", {"Version": "1"})
    ET.SubElement(cprops, "asl.clip.label.name").text = "BE.Prefs.LabelColors.0"
    ET.SubElement(cprops, "asl.clip.label.color").text = "11405886"
    mowner = ET.SubElement(clip, "MarkerOwner", {"Version": "1"})
    ET.SubElement(mowner, "Markers", {"ObjectRef": media_chain["markers_id"]})
    ET.SubElement(clip, "Source", {"ObjectRef": media_chain["video_media_source_id"]})
    ET.SubElement(clip, "InPoint").text = str(source_in_ticks)
    ET.SubElement(clip, "OutPoint").text = str(source_out_ticks)
    if playback_speed is not None and abs(playback_speed - 1.0) > 1e-6:
        # Recompute from actual source/timeline tick ranges for tick-exact ratio.
        # This guarantees Premiere's internal "natural duration on timeline"
        # ((OutPoint-InPoint)/PlaybackSpeed) matches End-Start exactly — otherwise
        # any rounding shows as zebra bars at the clip's tail edge.
        tl_dur_ticks = timeline_out_ticks - timeline_in_ticks
        src_dur_ticks = source_out_ticks - source_in_ticks
        if tl_dur_ticks > 0:
            playback_speed = src_dur_ticks / tl_dur_ticks
        # Use full Python float precision (~17 digits) — `:.6f` truncates to ~µs.
        ET.SubElement(clip, "PlaybackSpeed").text = repr(playback_speed)
    ET.SubElement(clip, "ClipID").text = ids.fresh_uid()
    elements.append(vc)

    # 4. VideoComponentChain (target of VCTI's Components ObjectRef).
    # Required even when the clip carries no effects — Premiere silently
    # refuses to render the timeline if this dangles.
    vcc = ET.Element("VideoComponentChain", {
        "ObjectID": components_id,
        "ClassID": CID_VIDEO_COMPONENT_CHAIN,
        "Version": "3",
    })

    if motion_filter_factory is not None:
        # Custom Motion override: invoke the factory NOW (after the placement
        # IDs have been allocated) to build the filter + 11 params. Chain shape
        # matches steak_tacos's custom-motion clips: no DefaultMotion field,
        # no MZ.ComponentChain props, just a Components list with the filter.
        _, motion_elements, motion_filter_id = motion_filter_factory(ids)
        elements.extend(motion_elements)
        ET.SubElement(vcc, "DefaultOpacity").text = "true"
        ET.SubElement(vcc, "DefaultOpacityComponentID").text = "2"
        cc = ET.SubElement(vcc, "ComponentChain", {"Version": "3"})
        comps = ET.SubElement(cc, "Components", {"Version": "1"})
        ET.SubElement(comps, "Component", {"Index": "0", "ObjectRef": motion_filter_id})
    else:
        ET.SubElement(vcc, "DefaultMotion").text = "true"
        ET.SubElement(vcc, "DefaultOpacity").text = "true"
        ET.SubElement(vcc, "DefaultMotionComponentID").text = "1"
        ET.SubElement(vcc, "DefaultOpacityComponentID").text = "2"
        cc = ET.SubElement(vcc, "ComponentChain", {"Version": "3"})
        ccnode = ET.SubElement(cc, "Node", {"Version": "1"})
        ccprops = ET.SubElement(ccnode, "Properties", {"Version": "1"})
        ET.SubElement(ccprops, "MZ.ComponentChain.ActiveComponentID").text = "2"
        ET.SubElement(ccprops, "MZ.ComponentChain.ActiveComponentParamIndex").text = "4294967295"
    elements.append(vcc)

    return {"elements": elements, "vcti_id": vcti_id}


def build_audio_clip_placement(
    media_chain: dict,
    timeline_in_ticks: int,
    timeline_out_ticks: int,
    source_in_ticks: int,
    source_out_ticks: int,
    ids: IdFactory,
) -> dict:
    """Audio side of a clip placement — sibling of build_clip_placement.

    Emits AudioClipTrackItem + SubClip + subclip AudioClip + AudioComponentChain
    + 2× SecondaryContent (stereo). Decoded from AUDIO_REF_B.prproj
    (2026-05-01).

    Requires media_chain to have been built with with_audio=True (so
    audio_media_source_id is populated).

    Returns:
      {"elements": list[ET.Element], "acti_id": str}
    """
    if not media_chain.get("audio_media_source_id"):
        raise RuntimeError(
            "build_audio_clip_placement requires media chain built with "
            "with_audio=True (audio_media_source_id missing)"
        )

    acti_id = ids.fresh_id()
    subclip_element_id = ids.fresh_id()
    audio_clip_id = ids.fresh_id()
    components_id = ids.fresh_id()
    sec_content_left_id = ids.fresh_id()
    sec_content_right_id = ids.fresh_id()

    stereo_layout = '[{"channellabel":100},{"channellabel":101}]'
    elements: list[ET.Element] = []

    # 1. AudioClipTrackItem
    acti = ET.Element("AudioClipTrackItem", {
        "ObjectID": acti_id,
        "ClassID": CID_AUDIO_CLIP_TRACK_ITEM,
        "Version": "11",
    })
    cti = ET.SubElement(acti, "ClipTrackItem", {"Version": "8"})
    co = ET.SubElement(cti, "ComponentOwner", {"Version": "1"})
    ET.SubElement(co, "Components", {"ObjectRef": components_id})
    ti = ET.SubElement(cti, "TrackItem", {"Version": "4"})
    ET.SubElement(ti, "Start").text = str(timeline_in_ticks)
    ET.SubElement(ti, "End").text = str(timeline_out_ticks)
    ET.SubElement(cti, "SubClip", {"ObjectRef": subclip_element_id})
    ET.SubElement(acti, "ID").text = ids.fresh_uid()
    ET.SubElement(acti, "PreRenderComponentChainHashVersion").text = "1"
    elements.append(acti)

    # 2. SubClip element (audio side)
    sub = ET.Element("SubClip", {
        "ObjectID": subclip_element_id,
        "ClassID": CID_SUB_CLIP,
        "Version": "6",
    })
    ET.SubElement(sub, "Clip", {"ObjectRef": audio_clip_id})
    ET.SubElement(sub, "MasterClip", {"ObjectURef": media_chain["master_clip_uid"]})
    ET.SubElement(sub, "Name").text = media_chain["name"]
    ET.SubElement(sub, "OrigChGrp").text = "0"
    elements.append(sub)

    # 3. Subclip AudioClip — InPoint/OutPoint into the audio source
    ac = ET.Element("AudioClip", {
        "ObjectID": audio_clip_id,
        "ClassID": CID_AUDIO_CLIP,
        "Version": "8",
    })
    clip = ET.SubElement(ac, "Clip", {"Version": "18"})
    cnode = ET.SubElement(clip, "Node", {"Version": "1"})
    cprops = ET.SubElement(cnode, "Properties", {"Version": "1"})
    ET.SubElement(cprops, "asl.clip.label.name").text = "BE.Prefs.LabelColors.0"
    ET.SubElement(cprops, "asl.clip.label.color").text = "11405886"
    mowner = ET.SubElement(clip, "MarkerOwner", {"Version": "1"})
    ET.SubElement(mowner, "Markers", {"ObjectRef": media_chain["markers_id"]})
    ET.SubElement(clip, "Source", {"ObjectRef": media_chain["audio_media_source_id"]})
    ET.SubElement(clip, "InPoint").text = str(source_in_ticks)
    ET.SubElement(clip, "OutPoint").text = str(source_out_ticks)
    ET.SubElement(clip, "ClipID").text = ids.fresh_uid()
    sec_contents = ET.SubElement(ac, "SecondaryContents", {"Version": "1"})
    ET.SubElement(sec_contents, "SecondaryContentItem", {"Index": "0", "ObjectRef": sec_content_left_id})
    ET.SubElement(sec_contents, "SecondaryContentItem", {"Index": "1", "ObjectRef": sec_content_right_id})
    ET.SubElement(ac, "AudioChannelLayout").text = stereo_layout
    elements.append(ac)

    # 4. AudioComponentChain for the placement
    acc = ET.Element("AudioComponentChain", {
        "ObjectID": components_id,
        "ClassID": CID_AUDIO_COMPONENT_CHAIN,
        "Version": "4",
    })
    ET.SubElement(acc, "DefaultVol").text = "true"
    ET.SubElement(acc, "DefaultVolumeComponentID").text = "1"
    ET.SubElement(acc, "DefaultChannelVolumeComponentID").text = "2"
    ET.SubElement(acc, "ComponentChain", {"Version": "3"})
    ET.SubElement(acc, "AudioChannelLayout").text = stereo_layout
    ET.SubElement(acc, "ChannelType").text = "1"
    elements.append(acc)

    # 5. SecondaryContent × 2 (stereo channels) for the placement
    for i, sc_id in enumerate((sec_content_left_id, sec_content_right_id)):
        sc = ET.Element("SecondaryContent", {
            "ObjectID": sc_id,
            "ClassID": CID_SECONDARY_CONTENT,
            "Version": "1",
        })
        ET.SubElement(sc, "Content", {"ObjectRef": media_chain["audio_media_source_id"]})
        ET.SubElement(sc, "ChannelIndex").text = str(i)
        elements.append(sc)

    return {"elements": elements, "acti_id": acti_id}


def build_link_element(vcti_id: str, acti_id: str, ids: IdFactory) -> ET.Element:
    """Link element — pairs a V-track item and an A-track item so they move
    as a linked-selection group (the default behavior when you drag a video
    clip with embedded audio onto the timeline).

    Decoded from AUDIO_REF_B.prproj.
    """
    link_id = ids.fresh_id()
    link = ET.Element("Link", {
        "ObjectID": link_id,
        "ClassID": CID_LINK,
        "Version": "1",
    })
    group = ET.SubElement(link, "TrackItemGroup", {"Version": "1"})
    items = ET.SubElement(group, "TrackItems", {"Version": "1"})
    ET.SubElement(items, "TrackItem", {"Index": "0", "ObjectRef": vcti_id})
    ET.SubElement(items, "TrackItem", {"Index": "1", "ObjectRef": acti_id})
    return link
