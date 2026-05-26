"""Native Windows notification helpers (taskbar flash).

PyQt does not expose Windows' FlashWindowEx directly, so we call it
through ctypes. Flashing only kicks in when the target window is not
already the foreground — Windows itself is responsible for that
suppression, so we don't need to check ourselves.
"""
from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes


# FlashWindowEx flags (winuser.h)
_FLASHW_STOP = 0
_FLASHW_CAPTION = 0x01
_FLASHW_TRAY = 0x02
_FLASHW_ALL = _FLASHW_CAPTION | _FLASHW_TRAY
_FLASHW_TIMER = 0x04
_FLASHW_TIMERNOFG = 0x0C  # Flash until the window comes to the foreground


class _FLASHWINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("hwnd", wintypes.HWND),
        ("dwFlags", wintypes.DWORD),
        ("uCount", wintypes.UINT),
        ("dwTimeout", wintypes.DWORD),
    ]


def flash_taskbar(hwnd: int, count: int = 3) -> bool:
    """Flash the given window's taskbar button + caption.

    The OS only flashes if the window is not currently in the foreground,
    so calling this when the user is already looking at the app is a
    cheap no-op.

    Pass 0 for `count` to flash until the window is activated; the
    default of 3 is friendly for "task complete" notifications.
    """
    if sys.platform != "win32" or not hwnd:
        return False
    try:
        info = _FLASHWINFO(
            cbSize=ctypes.sizeof(_FLASHWINFO),
            hwnd=hwnd,
            dwFlags=_FLASHW_ALL if count > 0 else _FLASHW_TIMERNOFG,
            uCount=count,
            dwTimeout=0,
        )
        return bool(ctypes.windll.user32.FlashWindowEx(ctypes.byref(info)))
    except Exception:
        return False
