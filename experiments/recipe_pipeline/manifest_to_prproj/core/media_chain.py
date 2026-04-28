"""Per-source media chain — the 9-element block emitted once per imported file.

Per Brain/Knowledge/API Integration/Premiere prproj Media Chain and Clip
Placement Graph.md, every unique source file in the manifest gets:

  ClipProjectItem  → MasterClip → ClipLoggingInfo
                                ↓
                                VideoClip (master rep, no InPoint/OutPoint)
                                + ClipChannelGroupVectorSerializer (empty body, required)
                                + Markers (3 known-zero fields, required)
                                + VideoMediaSource → Media → VideoStream

Three of these are "required-but-empty" — skipping them is a hard fail at
load even though they have no content. Documented inline.

The MediaMeta dataclass + ffprobe() are also here because they're inputs to
build_media_chain — same module keeps the data and the consumer together.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .classids import (
    CID_CLIP_PROJECT_ITEM,
    CID_MASTER_CLIP,
    CID_CLIP_LOGGING_INFO,
    CID_VIDEO_CLIP,
    CID_CLIP_CHANNEL_GROUP_VECTOR_SERIALIZER,
    CID_MARKERS,
    CID_VIDEO_MEDIA_SOURCE,
    CID_MEDIA,
    CID_VIDEO_STREAM,
)
from .seed_loader import IdFactory
from .tick_math import TICKS_PER_SECOND


logger = logging.getLogger("manifest_to_prproj")


@dataclass
class MediaMeta:
    abs_path: Path
    duration_seconds: float
    width: int
    height: int
    fps_num: int
    fps_den: int
    codec_name: str
    audio_layout: str
    audio_sample_rate: Optional[int]

    @property
    def duration_ticks(self) -> int:
        return int(round(self.duration_seconds * TICKS_PER_SECOND))

    @property
    def fps(self) -> float:
        return self.fps_num / self.fps_den if self.fps_den else 0.0

    @property
    def framerate_ticks(self) -> int:
        # Ticks per frame
        return int(round(TICKS_PER_SECOND * self.fps_den / self.fps_num))


def _parse_rational(s: str) -> tuple[int, int]:
    if "/" in s:
        a, b = s.split("/")
        return int(a), int(b)
    return int(s), 1


def ffprobe(path: Path) -> MediaMeta:
    cmd = [
        "ffprobe", "-v", "error",
        "-print_format", "json",
        "-show_streams", "-show_format",
        str(path),
    ]
    logger.debug("ffprobe cmd: %s", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        logger.error("ffprobe failed for %s: %s", path, res.stderr)
        raise RuntimeError(f"ffprobe failed for {path}: {res.stderr}")
    data = json.loads(res.stdout)
    logger.debug("ffprobe json: %s", json.dumps(data)[:400])

    vstream = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    astream = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    if not vstream:
        raise RuntimeError(f"no video stream in {path}")

    duration = float(data["format"].get("duration") or vstream.get("duration") or 0)
    fps_num, fps_den = _parse_rational(vstream.get("r_frame_rate", "24/1"))

    return MediaMeta(
        abs_path=path,
        duration_seconds=duration,
        width=int(vstream["width"]),
        height=int(vstream["height"]),
        fps_num=fps_num,
        fps_den=fps_den,
        codec_name=vstream.get("codec_name", "unknown"),
        audio_layout=astream.get("channel_layout", "none") if astream else "none",
        audio_sample_rate=int(astream["sample_rate"]) if astream and astream.get("sample_rate") else None,
    )


def build_media_chain(meta: MediaMeta, ids: IdFactory) -> dict:
    """Build the 9-element chain for one source file.

    Returns dict with:
      - elements: list[ET.Element] to append to PremiereData root
      - clip_project_item_uid: ObjectURef the bin uses to reference this media
      - master_clip_uid: back-pointer used by every SubClip element placed
                         from this source
      - video_media_source_id: ObjectID; subclip VideoClips reference this via
                                Source ObjectRef (shared across all placements)
      - markers_id: ObjectID; same Markers shared across all placements'
                     VideoClip MarkerOwner ObjectRefs
      - duration_ticks, name: convenience for placement loop
    """
    # IDs for all elements
    clip_project_item_uid = ids.fresh_uid()
    master_clip_uid = ids.fresh_uid()
    media_uid = ids.fresh_uid()

    video_stream_id = ids.fresh_id()
    video_media_source_id = ids.fresh_id()
    clip_logging_info_id = ids.fresh_id()
    master_video_clip_id = ids.fresh_id()
    channel_group_serializer_id = ids.fresh_id()
    markers_id = ids.fresh_id()

    name = meta.abs_path.name
    duration_ticks = meta.duration_ticks

    elements: list[ET.Element] = []

    # 1. ClipProjectItem (bin entry)
    cpi = ET.Element("ClipProjectItem", {
        "ObjectUID": clip_project_item_uid,
        "ClassID": CID_CLIP_PROJECT_ITEM,
        "Version": "1",
    })
    pi = ET.SubElement(cpi, "ProjectItem", {"Version": "1"})
    node = ET.SubElement(pi, "Node", {"Version": "1"})
    props = ET.SubElement(node, "Properties", {"Version": "1"})
    ET.SubElement(props, "project.icon.view.grid.order").text = "0"
    ET.SubElement(props, "Column.PropertyText.Label").text = "BE.Prefs.LabelColors.0"
    ET.SubElement(pi, "Name").text = name
    ET.SubElement(cpi, "MasterClip", {"ObjectURef": master_clip_uid})
    elements.append(cpi)

    # 2. MasterClip
    mc = ET.Element("MasterClip", {
        "ObjectUID": master_clip_uid,
        "ClassID": CID_MASTER_CLIP,
        "Version": "12",
    })
    mc_node = ET.SubElement(mc, "Node", {"Version": "1"})
    mc_props = ET.SubElement(mc_node, "Properties", {"Version": "1"})
    ET.SubElement(mc_props, "monitor.edit.time").text = "0"
    ET.SubElement(mc_props, "monitor.zoom.in.time").text = "0"
    ET.SubElement(mc_props, "monitor.zoom.out.time").text = str(duration_ticks)
    ET.SubElement(mc_props, "monitor.take.video").text = "true"
    # take.audio=false avoids needing an audio media-chain in Round 1
    ET.SubElement(mc_props, "monitor.take.audio").text = "false"
    ET.SubElement(mc, "LoggingInfo", {"ObjectRef": clip_logging_info_id})
    clips = ET.SubElement(mc, "Clips", {"Version": "1"})
    ET.SubElement(clips, "Clip", {"Index": "0", "ObjectRef": master_video_clip_id})
    ET.SubElement(mc, "AudioClipChannelGroups", {"ObjectRef": channel_group_serializer_id})
    ET.SubElement(mc, "Name").text = name
    ET.SubElement(mc, "TimeDisplay").text = "104"
    ET.SubElement(mc, "MasterClipChangeVersion").text = "0"
    elements.append(mc)

    # 3. ClipLoggingInfo
    cli = ET.Element("ClipLoggingInfo", {
        "ObjectID": clip_logging_info_id,
        "ClassID": CID_CLIP_LOGGING_INFO,
        "Version": "10",
    })
    ET.SubElement(cli, "CaptureMode").text = "2"
    ET.SubElement(cli, "ClipName").text = name
    ET.SubElement(cli, "TimecodeFormat").text = "104"
    ET.SubElement(cli, "MediaInPoint").text = "0"
    ET.SubElement(cli, "MediaOutPoint").text = str(duration_ticks)
    ET.SubElement(cli, "MediaFrameRate").text = str(meta.framerate_ticks)
    elements.append(cli)

    # 4. VideoClip (the master representation for the asset)
    vc = ET.Element("VideoClip", {
        "ObjectID": master_video_clip_id,
        "ClassID": CID_VIDEO_CLIP,
        "Version": "11",
    })
    clip = ET.SubElement(vc, "Clip", {"Version": "18"})
    cnode = ET.SubElement(clip, "Node", {"Version": "1"})
    cprops = ET.SubElement(cnode, "Properties", {"Version": "1"})
    ET.SubElement(cprops, "asl.clip.label.name").text = "BE.Prefs.LabelColors.0"
    ET.SubElement(cprops, "asl.clip.label.color").text = "11405886"
    mowner = ET.SubElement(clip, "MarkerOwner", {"Version": "1"})
    ET.SubElement(mowner, "Markers", {"ObjectRef": markers_id})
    ET.SubElement(clip, "Source", {"ObjectRef": video_media_source_id})
    ET.SubElement(clip, "ClipID").text = ids.fresh_uid()
    ET.SubElement(clip, "InUse").text = "false"
    elements.append(vc)

    # 4b. ClipChannelGroupVectorSerializer (target of MasterClip's AudioClipChannelGroups ref)
    ccg = ET.Element("ClipChannelGroupVectorSerializer", {
        "ObjectID": channel_group_serializer_id,
        "ClassID": CID_CLIP_CHANNEL_GROUP_VECTOR_SERIALIZER,
        "Version": "1",
    })
    elements.append(ccg)

    # 4c. Markers (target of every VideoClip's MarkerOwner ref for this masterclip)
    mk = ET.Element("Markers", {
        "ObjectID": markers_id,
        "ClassID": CID_MARKERS,
        "Version": "4",
    })
    ET.SubElement(mk, "ByGUID").text = "byGUID"
    ET.SubElement(mk, "LastMetadataState").text = "00000000-0000-0000-0000-000000000000"
    ET.SubElement(mk, "LastContentState").text = "00000000-0000-0000-0000-000000000000"
    elements.append(mk)

    # 5. VideoMediaSource
    vms = ET.Element("VideoMediaSource", {
        "ObjectID": video_media_source_id,
        "ClassID": CID_VIDEO_MEDIA_SOURCE,
        "Version": "2",
    })
    msrc = ET.SubElement(vms, "MediaSource", {"Version": "4"})
    ET.SubElement(msrc, "Content", {"Version": "10"})
    ET.SubElement(msrc, "Media", {"ObjectURef": media_uid})
    ET.SubElement(vms, "OriginalDuration").text = str(duration_ticks)
    elements.append(vms)

    # 6. Media
    md = ET.Element("Media", {
        "ObjectUID": media_uid,
        "ClassID": CID_MEDIA,
        "Version": "30",
    })
    ET.SubElement(md, "VideoStream", {"ObjectRef": video_stream_id})
    rel = os.path.relpath(meta.abs_path, Path.home())
    ET.SubElement(md, "RelativePath").text = rel
    ET.SubElement(md, "TimeDisplay").text = "104"
    ET.SubElement(md, "Start").text = "0"
    ET.SubElement(md, "FilePath").text = str(meta.abs_path)
    ET.SubElement(md, "ImplementationID").text = ids.fresh_uid()
    ET.SubElement(md, "Title").text = name
    ET.SubElement(md, "FileKey").text = ids.fresh_uid()
    ET.SubElement(md, "ActualMediaFilePath").text = str(meta.abs_path)
    elements.append(md)

    # 7. VideoStream
    vs = ET.Element("VideoStream", {
        "ObjectID": video_stream_id,
        "ClassID": CID_VIDEO_STREAM,
        "Version": "22",
    })
    ET.SubElement(vs, "Duration").text = str(duration_ticks)
    ET.SubElement(vs, "CodecType").text = "1634743400"  # avc1; harmless if codec differs
    ET.SubElement(vs, "FrameRect").text = f"0,0,{meta.width},{meta.height}"
    ET.SubElement(vs, "AlphaType").text = "2"
    ET.SubElement(vs, "OriginalImageOrientationType").text = "1"
    ET.SubElement(vs, "FrameRate").text = str(meta.framerate_ticks)
    elements.append(vs)

    return {
        "elements": elements,
        "clip_project_item_uid": clip_project_item_uid,
        "master_clip_uid": master_clip_uid,
        "video_media_source_id": video_media_source_id,
        "markers_id": markers_id,
        "duration_ticks": duration_ticks,
        "name": name,
    }
