"""Helpers for getting a processed file into Apple Music for Windows.

Apple Music for Windows has no public automation API (Apple has stated
this is intentional), so we can't programmatically add a file. The next
best thing is to make the final manual drag as friction-free as
possible: open Explorer with the file pre-selected, and launch the
Apple Music app so the user can drop the file onto it.
"""
from __future__ import annotations

import ctypes
import functools
import os
import subprocess
import sys
import webbrowser
from ctypes import wintypes


# Microsoft Store deep-link to Apple Music for Windows.
_APPLE_MUSIC_STORE_URL = "ms-windows-store://pdp/?productid=9PFHDD62MXS1"


def _reveal_via_shell_api(abs_path: str) -> bool:
    """Use the Windows Shell API directly to select a file in Explorer.

    The `explorer.exe /select,<path>` trick is widely-cited but is
    fragile: any quoting / spacing weirdness causes Explorer to fall
    back to opening the Documents folder. Calling the Shell API gets
    rid of the entire command-line escaping layer.
    """
    try:
        shell32 = ctypes.windll.shell32
        ole32 = ctypes.windll.ole32

        SHParseDisplayName = shell32.SHParseDisplayName
        SHParseDisplayName.argtypes = [
            wintypes.LPCWSTR, ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p), wintypes.ULONG,
            ctypes.POINTER(wintypes.ULONG),
        ]
        SHParseDisplayName.restype = ctypes.c_long  # HRESULT

        SHOpenFolderAndSelectItems = shell32.SHOpenFolderAndSelectItems
        SHOpenFolderAndSelectItems.argtypes = [
            ctypes.c_void_p, wintypes.UINT,
            ctypes.c_void_p, wintypes.DWORD,
        ]
        SHOpenFolderAndSelectItems.restype = ctypes.c_long  # HRESULT

        pidl = ctypes.c_void_p()
        attr = wintypes.ULONG(0)
        hr = SHParseDisplayName(
            abs_path, None, ctypes.byref(pidl), 0, ctypes.byref(attr))
        if hr != 0 or not pidl:
            return False
        try:
            hr2 = SHOpenFolderAndSelectItems(pidl, 0, None, 0)
            return hr2 == 0
        finally:
            ole32.CoTaskMemFree(pidl)
    except Exception:
        return False


def open_folder(path: str, log_cb=None) -> bool:
    """Open a folder in Explorer (without selecting anything).

    If the folder doesn't exist yet, create it — this lets the user
    click the sidebar shortcut on a fresh install before they've ever
    imported anything.
    """
    if sys.platform != "win32":
        return False
    if not path:
        return False
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as e:
        if log_cb:
            log_cb(f"⚠️  フォルダ作成に失敗: {e}")
        return False
    if log_cb:
        log_cb(f"📂 フォルダを開く: {path}")
    try:
        subprocess.Popen(["explorer.exe", os.path.abspath(path)])
        return True
    except OSError:
        return False


def reveal_in_explorer(path: str, log_cb=None) -> bool:
    """Open File Explorer with `path` selected (so it's ready to be dragged).

    Returns True on success. Logs the resolved target path via log_cb
    if provided, so users (and us) can see exactly what the OS was
    asked to open when something goes wrong.
    """
    if sys.platform != "win32":
        return False
    if not path or not os.path.exists(path):
        if log_cb:
            log_cb(f"⚠️  reveal_in_explorer: path does not exist: {path!r}")
        return False

    abs_path = os.path.abspath(path)
    if log_cb:
        log_cb(f"📂 explorer で開く: {abs_path}")

    # Preferred path: direct Shell API call (no command-line escaping).
    if _reveal_via_shell_api(abs_path):
        return True

    # Fallback: classic /select, invocation. Generally works for simple
    # ASCII paths and is a last-resort safety net.
    try:
        subprocess.Popen(["explorer.exe", f"/select,{abs_path}"])
        return True
    except OSError:
        if log_cb:
            log_cb("⚠️  explorer.exe の起動に失敗しました")
        return False


@functools.cache
def _find_apple_music_aumid() -> str | None:
    """Look up Apple Music's Application User Model ID via PowerShell.

    Cached for the lifetime of the process: PowerShell startup is slow
    (~0.5–1s) and the answer doesn't change while we're running.

    Returns the AUMID string (e.g. `AppleInc.AppleMusicWin_…!App`) or
    None if the app isn't installed / detection failed.
    """
    if sys.platform != "win32":
        return None
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "(Get-StartApps | Where-Object { $_.Name -like 'Apple Music*' } | "
             "Select-Object -First 1).AppID"],
            capture_output=True, text=True, timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        aumid = (result.stdout or "").strip()
        return aumid or None
    except Exception:
        return None


def launch_apple_music(log_cb=None) -> bool:
    """Open the Apple Music for Windows app via its AUMID.

    Microsoft Store apps don't reliably expose a URI protocol; calling
    `os.startfile("apple-music:")` causes Windows to pop up the
    "choose an app to open this link" dialog. Instead, we look up the
    app's Application User Model ID and launch it via
    `explorer.exe shell:AppsFolder\\<AUMID>`, which is the documented
    way to launch a Store app from another process.
    """
    if sys.platform != "win32":
        return False

    aumid = _find_apple_music_aumid()
    if aumid:
        if log_cb:
            log_cb(f"🎵 Apple Music を起動 (AUMID: {aumid})")
        try:
            subprocess.Popen(
                ["explorer.exe", f"shell:AppsFolder\\{aumid}"],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return True
        except Exception as e:
            if log_cb:
                log_cb(f"⚠️  Apple Music の起動に失敗: {e}")
            # fall through to Store fallback

    if log_cb:
        log_cb("ℹ️  Apple Music が見つかりません → Microsoft Store を開きます")
    try:
        webbrowser.open(_APPLE_MUSIC_STORE_URL)
        return True
    except Exception:
        return False
