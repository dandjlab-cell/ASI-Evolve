"""Tick math + timecode primitives — leaf module, no internal dependencies.

Premiere stores all temporal coordinates as integer ticks at the rate
TICKS_PER_SECOND = 254_016_000_000. This rate is divisible by every common
video framerate's denominator, which is why Premiere chose it.

Float-precision pitfall on PlaybackSpeed:
  Premiere computes the clip's "natural duration on timeline" as
  (OutPoint - InPoint) / PlaybackSpeed in ticks. If that doesn't precisely
  equal End - Start, the tail edge of the clip renders as zebra bars. Compute
  the ratio in ticks (NOT seconds — going through TICKS_PER_SECOND division
  loses bits) and write the result with repr() (full 17-digit precision), not
  a :.6f formatter. Helper not provided here — done inline at the placement
  call site so the source/timeline tick values stay close to the math.
"""

from __future__ import annotations


TICKS_PER_SECOND = 254_016_000_000

# Anchor for StartKeyframe (~-360000s expressed in ticks). Premiere uses this
# fixed sentinel to mean "the clip's beginning" for static (single-keyframe)
# parameter values.
START_KEYFRAME_TICK = "-91445760000000000"

# Default frame rate as ticks-per-frame for 23.976 = 24000/1001:
# ticks_per_frame = TICKS_PER_SECOND * 1001 / 24000 = 10597793000
FRAMERATE_TICKS_23_976 = 10597793000


def timecode_to_seconds(tc: str, fps: float) -> float:
    """Parse 'HH:MM:SS:FF' (non-drop frame) at given fps to seconds."""
    parts = tc.split(":")
    if len(parts) != 4:
        raise ValueError(f"bad timecode: {tc!r}")
    h, m, s, f = (int(p) for p in parts)
    return h * 3600 + m * 60 + s + f / fps


def seconds_to_ticks(sec: float) -> int:
    return int(round(sec * TICKS_PER_SECOND))


def start_keyframe(value: str) -> str:
    """Format a StartKeyframe with a single scalar value (or 'X:Y' for points)."""
    return f"{START_KEYFRAME_TICK},{value},0,0,0,0,0,0"
