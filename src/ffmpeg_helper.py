"""ffmpeg detection + assisted install.

ffmpeg is the most common missing dependency for first-time users. It
is not a Python package — it's a separate binary that needs to be on
PATH. This module:

  * detects whether ffmpeg (and ffprobe, which yt-dlp also needs) are
    resolvable;
  * identifies failure messages that point at ffmpeg, so the GUI can
    show the assist dialog instead of a raw stack trace;
  * launches `winget` to install the standard `Gyan.FFmpeg` package
    when the user asks for it.

The actual UI is in src/gui/ffmpeg_dialog.py — this module is
intentionally GUI-free so it can be tested headlessly.
"""
from __future__ import annotations

import shutil
import subprocess
import sys


# Standard Microsoft winget package that ships ffmpeg + ffprobe + ffplay
# and registers them on the system PATH.
WINGET_PACKAGE_ID = "Gyan.FFmpeg"

# Manual download page (used as fallback link).
MANUAL_DOWNLOAD_URL = "https://www.gyan.dev/ffmpeg/builds/"


def is_installed() -> bool:
    """True only if BOTH ffmpeg and ffprobe are resolvable.

    yt-dlp's postprocessing step needs ffprobe in addition to ffmpeg,
    so checking only ffmpeg would still let the original error through.
    """
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def looks_like_missing_ffmpeg(message: str) -> bool:
    """Heuristic: does this error string suggest ffmpeg/ffprobe is missing?"""
    if not message:
        return False
    text = message.lower()
    needles = ("ffmpeg", "ffprobe")
    return any(n in text for n in needles) and (
        "not found" in text or "not on path" in text or "no such file" in text
        or "could not find" in text or "is not on path" in text
        or "not installed" in text
    )


def winget_available() -> bool:
    return sys.platform == "win32" and shutil.which("winget") is not None


def install_via_winget() -> subprocess.Popen:
    """Kick off `winget install Gyan.FFmpeg` and return the Popen handle.

    The caller is responsible for streaming output and waiting for exit.
    Returns immediately; does NOT block.
    """
    if not winget_available():
        raise RuntimeError("winget is not available on this machine.")

    return subprocess.Popen(
        [
            "winget", "install",
            "--id", WINGET_PACKAGE_ID,
            "--source", "winget",
            "--accept-source-agreements",
            "--accept-package-agreements",
            "--silent",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        text=True,
        bufsize=1,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
