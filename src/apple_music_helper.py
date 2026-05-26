"""Helpers for getting a processed file into Apple Music for Windows.

Apple Music for Windows has no public automation API (Apple has stated
this is intentional), so we can't programmatically add a file. The next
best thing is to make the final manual drag as friction-free as
possible: pop open Explorer with the file pre-selected, and launch the
Apple Music app so the user can drop the file onto it.
"""
from __future__ import annotations

import os
import subprocess
import sys
import webbrowser


# Microsoft Store deep-link to Apple Music for Windows.
_APPLE_MUSIC_STORE_URL = "ms-windows-store://pdp/?productid=9PFHDD62MXS1"
# Apple's custom protocol — registered by the Apple Music for Windows installer.
_APPLE_MUSIC_PROTOCOL = "apple-music:"


def reveal_in_explorer(path: str) -> bool:
    """Open File Explorer with `path` selected (so it's ready to be dragged).

    Returns True on success, False if the path doesn't exist or Explorer
    couldn't be launched.
    """
    if not os.path.exists(path):
        return False
    if sys.platform != "win32":
        return False

    # /select, must be a single argument with the path appended. Quoting
    # matters because the path may contain spaces.
    try:
        subprocess.Popen(["explorer.exe", f"/select,{path}"])
        return True
    except OSError:
        return False


def launch_apple_music() -> bool:
    """Open the Apple Music for Windows app.

    Tries the `apple-music:` protocol first (installed app). If that
    fails — typically because the app isn't installed — falls back to
    the Microsoft Store page so the user can install it.
    """
    if sys.platform != "win32":
        return False

    try:
        os.startfile(_APPLE_MUSIC_PROTOCOL)  # type: ignore[attr-defined]
        return True
    except OSError:
        # Protocol not registered → app not installed. Send the user to
        # the Store instead.
        try:
            webbrowser.open(_APPLE_MUSIC_STORE_URL)
            return True
        except Exception:
            return False
