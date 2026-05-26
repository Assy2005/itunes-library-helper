"""Convert unsupported audio formats to something iTunes can read."""
from __future__ import annotations

import os
import shutil
import subprocess

# iTunes natively handles these; everything else needs conversion.
ITUNES_NATIVE_EXTS = {".mp3", ".m4a", ".aac", ".wav", ".aiff", ".aif"}


def needs_conversion(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext not in ITUNES_NATIVE_EXTS


def convert_to_m4a(src: str, out_dir: str | None = None) -> str:
    """Convert `src` to AAC inside an .m4a container. Returns the output path."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg is not on PATH. Install it from https://ffmpeg.org/ "
            "and ensure `ffmpeg --version` works in PowerShell."
        )

    out_dir = out_dir or os.path.dirname(src)
    base = os.path.splitext(os.path.basename(src))[0]
    out_path = os.path.join(out_dir, f"{base}.m4a")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", src,
            "-c:a", "aac",
            "-b:a", "256k",
            out_path,
        ],
        check=True,
        capture_output=True,
    )
    return out_path
