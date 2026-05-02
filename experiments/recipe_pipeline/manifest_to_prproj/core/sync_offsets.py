"""Compute multicam sub-sequence layout from sync_groups offsets.

Given a sync_group entry from sync_groups.json (a_cam, optional b_cam, optional
ext_audio plus offsets), produce the per-clip InPoint values and the WAV→sub-seq
time conversion needed to emit a Premiere multicam sub-sequence with no empty
leading frames.

Sign convention (from tools/manifest_gen/audio_sync.py:159-160):
    offset_seconds: how much audio_b is shifted relative to audio_a
        positive = b starts later than a

For an sg row, a_cam is the reference. So:
    a_cam wall-clock start = 0
    b_cam wall-clock start = b_cam_offset_s         (positive = later)
    ext_audio wall-clock start = ext_audio_offset_s (positive = later)

Sub-sequence origin = the LATEST signal start. Every clip starts at sub-seq t=0
with its source InPoint = (subseq_origin - clip_start_wallclock). This guarantees
no empty leading frames, no matter which signal was late.

WAV-time → sub-seq-time conversion:
    sub_seq_t = wav_t - wav_inpoint
where wav_inpoint = subseq_origin - ext_audio_start_wallclock (always >= 0).
"""

from dataclasses import dataclass


@dataclass
class SubseqLayout:
    """Layout describing one sg's multicam sub-sequence."""

    sg_id: str
    subseq_origin_wallclock_s: float  # wall-clock time at which the sub-seq begins (= max signal start)
    a_cam_inpoint_s: float            # source InPoint for the a_cam clip inside the sub-seq
    b_cam_inpoint_s: float | None     # None if no b_cam
    wav_inpoint_s: float | None       # None if no ext_audio
    subseq_duration_s: float          # duration spanned by all signals' overlap
    has_b_cam: bool
    has_wav: bool


def compute_subseq_layout(sg: dict) -> SubseqLayout:
    """Compute per-clip InPoints + sub-seq duration from a sync_groups[].

    The sg dict comes from sync_groups.json, schema:
        {
            "group_id": "sg_001",
            "a_cam": "...mp4",
            "a_cam_duration_s": 30.0,
            "b_cam": "...mp4" or None,
            "b_cam_duration_s": 30.0 or None,
            "ext_audio": "...WAV" or None,
            "ext_audio_duration_s": 30.0 or None,
            "b_cam_offset_s": float or None,
            "ext_audio_offset_s": float or None,
        }

    Returns SubseqLayout. All InPoints >= 0; sub-seq begins at t=0 with all
    available signals present.

    Notes on durations: the sync_groups file caps durations at 30s for the
    correlation window — that is NOT the file duration, so subseq_duration_s
    reflects the FULL overlap from (subseq_origin) to (earliest signal end).
    Callers that need the actual file durations must ffprobe the source files.
    For sub-seq emission, the writer should clamp `subseq_duration_s` to the
    minimum of the actual file durations.
    """
    sg_id = sg["group_id"]

    # Wall-clock anchor: a_cam starts at t=0
    a_cam_start_wc = 0.0

    has_b_cam = bool(sg.get("b_cam"))
    has_wav = bool(sg.get("ext_audio"))

    b_cam_start_wc = float(sg.get("b_cam_offset_s") or 0.0) if has_b_cam else None
    wav_start_wc = float(sg.get("ext_audio_offset_s") or 0.0) if has_wav else None

    starts = [a_cam_start_wc]
    if b_cam_start_wc is not None:
        starts.append(b_cam_start_wc)
    if wav_start_wc is not None:
        starts.append(wav_start_wc)

    subseq_origin = max(starts)

    # Per-clip InPoint = subseq_origin - clip_start_wallclock
    a_cam_inpoint = subseq_origin - a_cam_start_wc
    b_cam_inpoint = (subseq_origin - b_cam_start_wc) if has_b_cam else None
    wav_inpoint = (subseq_origin - wav_start_wc) if has_wav else None

    # Subseq duration = (earliest end) - (subseq_origin)
    # earliest end = min(start_wc + clip_duration) over all signals
    a_cam_dur = float(sg.get("a_cam_duration_s") or 0.0)
    a_cam_end = a_cam_start_wc + a_cam_dur

    ends = [a_cam_end]
    if has_b_cam:
        b_cam_dur = float(sg.get("b_cam_duration_s") or 0.0)
        ends.append(b_cam_start_wc + b_cam_dur)
    if has_wav:
        wav_dur = float(sg.get("ext_audio_duration_s") or 0.0)
        ends.append(wav_start_wc + wav_dur)

    earliest_end = min(ends)
    subseq_duration = max(0.0, earliest_end - subseq_origin)

    return SubseqLayout(
        sg_id=sg_id,
        subseq_origin_wallclock_s=subseq_origin,
        a_cam_inpoint_s=a_cam_inpoint,
        b_cam_inpoint_s=b_cam_inpoint,
        wav_inpoint_s=wav_inpoint,
        subseq_duration_s=subseq_duration,
        has_b_cam=has_b_cam,
        has_wav=has_wav,
    )


def wav_t_to_subseq_t(wav_t: float, layout: SubseqLayout) -> float:
    """Convert a WAV-time timestamp (e.g. from paragraph_alignment.json) to
    sub-sequence time (suitable for V1/V6 cut IN/OUT on the main timeline).

    sub_seq_t = wav_t - wav_inpoint

    Falls back to wav_t when there's no WAV (single-camera sg with embedded mp4
    audio): in that case sub_seq_t aligns to a_cam-time directly, but cut times
    in paragraph_alignment.json are still in WAV-time when a WAV existed... if
    no WAV, the upstream pipeline should already be in a_cam-time.
    """
    if layout.wav_inpoint_s is None:
        return wav_t
    return wav_t - layout.wav_inpoint_s


def cam_t_at_wav_t(wav_t: float, layout: SubseqLayout) -> float:
    """For the V1-only validation path (Step 2 of the migration): given a WAV-t
    cut point, return the a_cam-t to apply as the source InPoint on the raw
    a_cam mp4.

    This is the inverse of audio_sync's offset:
        ext_audio_offset_s = how much WAV is shifted relative to a_cam (positive = later)
        ext_audio_t = a_cam_t - ext_audio_offset_s
        ⇒ a_cam_t = ext_audio_t + ext_audio_offset_s

    For sg_006 (ext_audio_offset_s=-5.516):
        a_cam_t at WAV-t=141.86 = 141.86 + (-5.516) = 136.344 ✓
    """
    if not layout.has_wav:
        # No external WAV — paragraph_alignment timestamps are already in a_cam-time
        return wav_t
    # ext_audio_offset_s = wav_start_wc - a_cam_start_wc = wav_start_wc (since a_cam_wc=0)
    # which is also (subseq_origin - wav_inpoint) - 0 = subseq_origin - wav_inpoint
    ext_audio_offset_s = layout.subseq_origin_wallclock_s - layout.wav_inpoint_s
    return wav_t + ext_audio_offset_s
