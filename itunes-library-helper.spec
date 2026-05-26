# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for itunes-library-helper.

Build with:
    pyinstaller itunes-library-helper.spec --noconfirm
"""

from PyInstaller.utils.hooks import collect_submodules


hidden = []
# yt-dlp registers extractors dynamically; PyInstaller needs the full tree.
hidden += collect_submodules("yt_dlp")
# mutagen loads tag handlers by name.
hidden += collect_submodules("mutagen")
# pywin32 COM client uses runtime-generated modules.
hidden += [
    "win32com",
    "win32com.client",
    "win32com.client.dynamic",
    "pythoncom",
    "pywintypes",
]


a = Analysis(
    ["src/main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Trim some unused stdlib / Qt modules to shrink the binary.
        "tkinter",
        "unittest",
        "test",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="itunes-library-helper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,        # GUI app — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,            # add an .ico here once you have one
)
