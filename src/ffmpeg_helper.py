"""ffmpeg detection + assisted install via winget.

ffmpeg is the most common missing dependency for first-time users. It
is not a Python package — it's a separate binary that needs to be on
PATH. This module:

  * detects whether ffmpeg/ffprobe are reachable, with a fallback to
    the winget-managed install path (so we can see a freshly-installed
    ffmpeg even before PATH has been refreshed for our process);
  * identifies failure messages that point at ffmpeg, so the GUI can
    show the assist dialog instead of a raw stack trace;
  * launches `winget install Gyan.FFmpeg` in a NEW visible console
    window so UAC, progress, and any prompts behave normally — we do
    NOT pipe stdout, because winget uses '\\r' spinner output that
    deadlocks line-buffered readers.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


WINGET_PACKAGE_ID = "Gyan.FFmpeg"
MANUAL_DOWNLOAD_URL = "https://www.gyan.dev/ffmpeg/builds/"


def _winget_links_dir() -> Path:
    """Where winget places shim executables for installed packages."""
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "Microsoft" / "WinGet" / "Links"


def is_installed() -> bool:
    """True if BOTH ffmpeg and ffprobe are reachable.

    yt-dlp's postprocessing step needs ffprobe in addition to ffmpeg.
    We check PATH first, then the standard winget shim dir as a
    fallback (handy right after a fresh install, before this process
    has a chance to pick up the new PATH).
    """
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return True

    links = _winget_links_dir()
    if (links / "ffmpeg.exe").exists() and (links / "ffprobe.exe").exists():
        return True

    return False


def looks_like_missing_ffmpeg(message: str) -> bool:
    if not message:
        return False
    text = message.lower()
    if "ffmpeg" not in text and "ffprobe" not in text:
        return False
    return any(s in text for s in (
        "not found", "not on path", "no such file",
        "could not find", "is not on path", "not installed",
    ))


def winget_available() -> bool:
    return sys.platform == "win32" and shutil.which("winget") is not None


def launch_winget_install() -> None:
    """Open a NEW visible console window running `winget install`.

    We deliberately don't pipe stdout — winget uses carriage-return
    progress animation which would deadlock a line-buffered reader and
    suppress the UAC prompt. The dialog polls is_installed() instead.

    `cmd /k` keeps the console open after winget exits so the user can
    read the final result.
    """
    if not winget_available():
        raise RuntimeError("winget が見つかりません。")

    cmd = (
        f'winget install --id {WINGET_PACKAGE_ID} '
        f'--accept-source-agreements --accept-package-agreements'
    )
    subprocess.Popen(
        ["cmd.exe", "/c", "start", "ffmpeg のインストール", "cmd.exe", "/k", cmd],
        creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
        close_fds=True,
    )
