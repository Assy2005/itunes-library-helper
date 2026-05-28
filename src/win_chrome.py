"""Windows 11 backdrop effects (Mica / Acrylic) via dwmapi.

Calling `enable_mica(hwnd)` on a Windows 11 22H2+ system turns the
window's title bar + non-client area into the same translucent
material used by Settings, Calculator, and Apple Music itself.
On older Windows (10 / early 11) the call silently becomes a no-op.
"""
from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes


# DWMWINDOWATTRIBUTE values (dwmapi.h)
_DWMWA_USE_IMMERSIVE_DARK_MODE = 20
_DWMWA_SYSTEMBACKDROP_TYPE = 38

# DWM_SYSTEMBACKDROP_TYPE
_DWMSBT_AUTO = 0
_DWMSBT_NONE = 1
_DWMSBT_MAINWINDOW = 2          # Mica (opaque-ish, recommended for app windows)
_DWMSBT_TRANSIENTWINDOW = 3     # Acrylic (more translucent)
_DWMSBT_TABBEDWINDOW = 4        # Mica Alt


def _set_dwm_attr(hwnd: int, attr: int, value: int) -> bool:
    try:
        v = ctypes.c_int(value)
        hr = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            wintypes.DWORD(attr),
            ctypes.byref(v),
            ctypes.sizeof(v),
        )
        return hr == 0
    except Exception:
        return False


def enable_dark_titlebar(hwnd: int) -> bool:
    """Switch the window's title bar to dark mode (Win10 1809+)."""
    if sys.platform != "win32" or not hwnd:
        return False
    return _set_dwm_attr(hwnd, _DWMWA_USE_IMMERSIVE_DARK_MODE, 1)


def enable_mica(hwnd: int, *, acrylic: bool = False) -> bool:
    """Apply Mica (default) or Acrylic backdrop. Requires Win11 22H2+."""
    if sys.platform != "win32" or not hwnd:
        return False
    backdrop = _DWMSBT_TRANSIENTWINDOW if acrylic else _DWMSBT_MAINWINDOW
    return _set_dwm_attr(hwnd, _DWMWA_SYSTEMBACKDROP_TYPE, backdrop)
