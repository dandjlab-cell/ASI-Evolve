"""Core writer modules — bucket-agnostic primitives shared by all content types.

These modules form the stable "core engine" per Decision 3 in
Brain/Projects/RoughCut/Architecture — Lessons from Claude Code Paper.md:
seed_loader, media_chain, placement, bins, serializer, tick_math.

ClassIDs are also exposed at this package level for convenience — every
core module that emits XML needs them.
"""

from .classids import (
    CID_BIN_PROJECT_ITEM,
    CID_CLIP_PROJECT_ITEM,
    CID_MASTER_CLIP,
    CID_MEDIA,
    CID_VIDEO_STREAM,
    CID_VIDEO_MEDIA_SOURCE,
    CID_CLIP_LOGGING_INFO,
    CID_VIDEO_CLIP,
    CID_VIDEO_CLIP_TRACK_ITEM,
    CID_CLIP_CHANNEL_GROUP_VECTOR_SERIALIZER,
    CID_MARKERS,
    CID_SUB_CLIP,
    CID_VIDEO_COMPONENT_CHAIN,
    CID_VIDEO_FILTER_COMPONENT,
    CID_VIDEO_COMPONENT_PARAM,
    CID_VIDEO_COMPONENT_PARAM_BOOL,
    CID_VIDEO_COMPONENT_PARAM_CLAMPED,
    CID_POINT_COMPONENT_PARAM,
)
from .tick_math import (
    TICKS_PER_SECOND,
    START_KEYFRAME_TICK,
    FRAMERATE_TICKS_23_976,
    timecode_to_seconds,
    seconds_to_ticks,
    start_keyframe,
)

__all__ = [
    "CID_BIN_PROJECT_ITEM",
    "CID_CLIP_PROJECT_ITEM",
    "CID_MASTER_CLIP",
    "CID_MEDIA",
    "CID_VIDEO_STREAM",
    "CID_VIDEO_MEDIA_SOURCE",
    "CID_CLIP_LOGGING_INFO",
    "CID_VIDEO_CLIP",
    "CID_VIDEO_CLIP_TRACK_ITEM",
    "CID_CLIP_CHANNEL_GROUP_VECTOR_SERIALIZER",
    "CID_MARKERS",
    "CID_SUB_CLIP",
    "CID_VIDEO_COMPONENT_CHAIN",
    "CID_VIDEO_FILTER_COMPONENT",
    "CID_VIDEO_COMPONENT_PARAM",
    "CID_VIDEO_COMPONENT_PARAM_BOOL",
    "CID_VIDEO_COMPONENT_PARAM_CLAMPED",
    "CID_POINT_COMPONENT_PARAM",
    "TICKS_PER_SECOND",
    "START_KEYFRAME_TICK",
    "FRAMERATE_TICKS_23_976",
    "timecode_to_seconds",
    "seconds_to_ticks",
    "start_keyframe",
]
