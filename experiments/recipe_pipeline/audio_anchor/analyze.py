#!/usr/bin/env python3
"""
analyze.py — Audio → events.json for animation-driving.

Given an audio file, emit a typed event stream that downstream consumers
(prproj writer, UXP panel, MOGRT param feeder) can use to anchor animations:

  - rms     amplitude envelope sampled at fps  (scipy only, always works)
  - peaks   local RMS maxima above threshold  (scipy only)
  - onsets  spectral-flux transient detection  (librosa, optional)
  - beats   tempo + beat grid for music         (librosa, optional)

Schema (matches the audio_anchors.json shape from the plan):

  {
    "version": 1,
    "source_audio": "/path/to/source.wav",
    "duration_s": 32.45,
    "sample_rate": 48000,
    "envelope": {"fps": 30, "rms": [...], "from": "scipy"},
    "onsets": [{"t": 0.42, "strength": 0.81, "from": "librosa"}],
    "peaks":  [{"t": 1.20, "rms": 0.78,    "from": "scipy"}],
    "beats":  {"tempo_bpm": 124.0, "grid": [0.48, 0.97, ...], "from": "librosa"}
  }

Usage:
  python analyze.py SOURCE.wav --mode all --fps 30 -o events.json
  python analyze.py SOURCE.wav --mode rms,peaks       (scipy-only path)
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.signal import find_peaks

DEFAULT_FPS = 30
DEFAULT_TARGET_SR = 22050  # librosa's default; balances accuracy and speed


def have_module(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def decode_audio_to_mono_float(path: Path, target_sr: int = DEFAULT_TARGET_SR) -> tuple[np.ndarray, int]:
    """Decode any audio file to mono float32 PCM via ffmpeg.

    Avoids needing soundfile/audioread; works on .wav/.mp3/.m4a/.mov/.aac/etc.
    """
    if not shutil.which("ffmpeg"):
        sys.exit("[err] ffmpeg not found on PATH. brew install ffmpeg.")
    cmd = [
        "ffmpeg", "-loglevel", "error", "-i", str(path),
        "-f", "f32le", "-acodec", "pcm_f32le",
        "-ac", "1", "-ar", str(target_sr),
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, check=False)
    if proc.returncode != 0:
        sys.exit(f"[err] ffmpeg failed: {proc.stderr.decode('utf-8','replace')}")
    samples = np.frombuffer(proc.stdout, dtype=np.float32)
    return samples, target_sr


def windowed_rms(samples: np.ndarray, sr: int, fps: int) -> np.ndarray:
    """RMS amplitude envelope, one value per output frame at fps."""
    hop = max(1, sr // fps)
    n_frames = (len(samples) + hop - 1) // hop
    pad = n_frames * hop - len(samples)
    if pad > 0:
        samples = np.concatenate([samples, np.zeros(pad, dtype=samples.dtype)])
    frames = samples.reshape(n_frames, hop)
    rms = np.sqrt(np.mean(frames * frames, axis=1))
    return rms.astype(np.float32)


def detect_peaks_scipy(rms: np.ndarray, fps: int, min_distance_s: float = 0.1, height_pct: float = 0.5) -> list[dict]:
    """Local maxima in the RMS envelope above a fraction of the global max."""
    if len(rms) == 0:
        return []
    height = float(np.max(rms)) * height_pct
    distance = max(1, int(min_distance_s * fps))
    peak_idx, _ = find_peaks(rms, height=height, distance=distance)
    return [
        {"t": round(float(i) / fps, 4), "rms": round(float(rms[i]), 4), "from": "scipy"}
        for i in peak_idx
    ]


def detect_onsets_librosa(samples: np.ndarray, sr: int) -> list[dict]:
    """Spectral-flux onset detection. Falls back to [] if librosa missing."""
    if not have_module("librosa"):
        print("[warn] onsets requested but librosa not installed. pip install librosa", file=sys.stderr)
        return []
    import librosa  # noqa: PLC0415
    onset_env = librosa.onset.onset_strength(y=samples, sr=sr)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    # Normalize strength to [0,1] for portability
    if len(onset_env):
        max_env = float(onset_env.max()) or 1.0
        strengths = [float(onset_env[min(f, len(onset_env)-1)]) / max_env for f in onset_frames]
    else:
        strengths = [0.0] * len(onset_times)
    return [
        {"t": round(float(t), 4), "strength": round(float(s), 4), "from": "librosa"}
        for t, s in zip(onset_times, strengths)
    ]


def detect_beats_librosa(samples: np.ndarray, sr: int) -> dict | None:
    """Tempo (BPM) + beat grid. Returns None if librosa missing."""
    if not have_module("librosa"):
        print("[warn] beats requested but librosa not installed. pip install librosa", file=sys.stderr)
        return None
    import librosa  # noqa: PLC0415
    tempo, beat_frames = librosa.beat.beat_track(y=samples, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    return {
        "tempo_bpm": round(float(np.atleast_1d(tempo)[0]), 2),
        "grid": [round(float(t), 4) for t in beat_times],
        "from": "librosa",
    }


def parse_modes(s: str) -> set[str]:
    if s == "all":
        return {"rms", "peaks", "onsets", "beats"}
    out = {m.strip() for m in s.split(",") if m.strip()}
    bad = out - {"rms", "peaks", "onsets", "beats"}
    if bad:
        sys.exit(f"[err] unknown modes: {bad}. valid: rms peaks onsets beats all")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Audio → events.json")
    ap.add_argument("source", type=Path, help="audio file (any ffmpeg-readable format)")
    ap.add_argument("--mode", default="all",
                    help="comma-list of: rms,peaks,onsets,beats  (or 'all'). default=all")
    ap.add_argument("--fps", type=int, default=DEFAULT_FPS, help=f"envelope sample rate (Hz). default={DEFAULT_FPS}")
    ap.add_argument("--target-sr", type=int, default=DEFAULT_TARGET_SR,
                    help=f"resample audio to this rate before analysis. default={DEFAULT_TARGET_SR}")
    ap.add_argument("-o", "--output", type=Path,
                    help="write JSON here (default: stdout)")
    args = ap.parse_args()

    if not args.source.exists():
        sys.exit(f"[err] source not found: {args.source}")
    modes = parse_modes(args.mode)

    samples, sr = decode_audio_to_mono_float(args.source, args.target_sr)
    duration = len(samples) / sr if sr else 0.0

    out = {
        "version": 1,
        "source_audio": str(args.source.resolve()),
        "duration_s": round(duration, 4),
        "sample_rate": sr,
    }

    if "rms" in modes or "peaks" in modes:
        rms = windowed_rms(samples, sr, args.fps)
        if "rms" in modes:
            out["envelope"] = {
                "fps": args.fps,
                "rms": [round(float(v), 5) for v in rms],
                "from": "scipy",
            }
        if "peaks" in modes:
            out["peaks"] = detect_peaks_scipy(rms, args.fps)

    if "onsets" in modes:
        out["onsets"] = detect_onsets_librosa(samples, sr)

    if "beats" in modes:
        beats = detect_beats_librosa(samples, sr)
        if beats is not None:
            out["beats"] = beats

    payload = json.dumps(out, indent=2)
    if args.output:
        args.output.write_text(payload)
        print(f"[ok] wrote {args.output} ({len(payload)} bytes)")
    else:
        print(payload)


if __name__ == "__main__":
    main()
