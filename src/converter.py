"""Audio processing via ffmpeg.

Builds an ffmpeg filter chain from AudioSettings, optionally adding bass
boost, treble boost, denoising, loudness normalization, and resampling.
Always re-encodes (so iTunes-compatible AAC/MP3 falls out the other
side).
"""
from __future__ import annotations

import os
import shutil
import subprocess

from .audio_presets import AudioSettings


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _build_filter_chain(s: AudioSettings) -> str:
    parts: list[str] = []
    if s.bass_gain_db > 0:
        parts.append(f"bass=g={s.bass_gain_db}")
    if s.treble_gain_db > 0:
        parts.append(f"treble=g={s.treble_gain_db}")
    if s.denoise_strength > 0:
        # 1 → mild, 2 → medium, 3 → strong
        nr = {1: 8, 2: 12, 3: 18}.get(s.denoise_strength, 12)
        parts.append(f"afftdn=nr={nr}")
    if s.dynaudnorm:
        parts.append("dynaudnorm=f=200:g=15")
    if s.loudness_normalize:
        # EBU R128, broadcast-loud-ish target
        parts.append("loudnorm=I=-16:TP=-1.5:LRA=11")
    if s.sample_rate > 0:
        parts.append(f"aresample={s.sample_rate}")
    return ",".join(parts)


def process(src: str, out_dir: str, settings: AudioSettings) -> str:
    """Run ffmpeg on `src` with the configured filter chain.

    Always produces a new file in `out_dir` matching `settings.output_format`.
    """
    if not ffmpeg_available():
        raise RuntimeError(
            "ffmpeg is not on PATH. Install it from https://ffmpeg.org/ "
            "and ensure `ffmpeg -version` works in PowerShell."
        )

    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(src))[0]
    out_path = os.path.join(out_dir, f"{base}.{settings.output_format}")

    cmd: list[str] = ["ffmpeg", "-y", "-i", src]

    chain = _build_filter_chain(settings)
    if chain:
        cmd += ["-af", chain]

    codec = "aac" if settings.output_format == "m4a" else "libmp3lame"
    cmd += ["-c:a", codec, "-b:a", f"{settings.bitrate_kbps}k", out_path]

    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


# Backwards-compatible helper used elsewhere in the codebase.
ITUNES_NATIVE_EXTS = {".mp3", ".m4a", ".aac", ".wav", ".aiff", ".aif"}


def needs_conversion(path: str) -> bool:
    return os.path.splitext(path)[1].lower() not in ITUNES_NATIVE_EXTS
