"""User settings persisted across sessions via QSettings."""
from __future__ import annotations

import os
import tempfile

from PyQt6.QtCore import QSettings

from .audio_presets import DEFAULT_PRESET, PRESETS, AudioSettings


# Storage identifiers match the repository name and intentionally do NOT
# follow the app's UI branding. Renaming these would orphan every user's
# previously-saved preset, output folder, and audio settings.
_ORG = "itunes-library-helper"
_APP = "itunes-library-helper"


def _qs() -> QSettings:
    return QSettings(_ORG, _APP)


# ---- output destinations ----

def auto_reveal_in_explorer() -> bool:
    return _qs().value("output/auto_reveal", True, type=bool)


def set_auto_reveal_in_explorer(v: bool) -> None:
    _qs().setValue("output/auto_reveal", v)


def auto_launch_apple_music() -> bool:
    return _qs().value("output/auto_launch_apple_music", True, type=bool)


def set_auto_launch_apple_music(v: bool) -> None:
    _qs().setValue("output/auto_launch_apple_music", v)


def output_folder() -> str:
    default = os.path.join(os.path.expanduser("~"), "Music", "itunes-library-helper")
    return _qs().value("output/folder", default, type=str)


def set_output_folder(path: str) -> None:
    _qs().setValue("output/folder", path)


def work_folder() -> str:
    """Where downloads and intermediate files are staged."""
    path = os.path.join(tempfile.gettempdir(), "itunes-library-helper")
    os.makedirs(path, exist_ok=True)
    return path


# ---- audio processing ----

def preset_name() -> str:
    return _qs().value("audio/preset", DEFAULT_PRESET, type=str)


def set_preset_name(name: str) -> None:
    _qs().setValue("audio/preset", name)


def audio_settings() -> AudioSettings:
    """Resolve the currently-active AudioSettings.

    For the built-in presets we just return the preset values. For
    "カスタム" we read each field individually from QSettings.
    """
    name = preset_name()
    if name != "カスタム":
        return PRESETS.get(name, PRESETS[DEFAULT_PRESET])

    s = _qs()
    base = PRESETS["カスタム"]
    return AudioSettings(
        bitrate_kbps=int(s.value("audio/custom/bitrate", base.bitrate_kbps)),
        bass_gain_db=int(s.value("audio/custom/bass", base.bass_gain_db)),
        treble_gain_db=int(s.value("audio/custom/treble", base.treble_gain_db)),
        denoise_strength=int(s.value("audio/custom/denoise", base.denoise_strength)),
        loudness_normalize=s.value("audio/custom/loudnorm", base.loudness_normalize, type=bool),
        dynaudnorm=s.value("audio/custom/dynaudnorm", base.dynaudnorm, type=bool),
        sample_rate=int(s.value("audio/custom/sample_rate", base.sample_rate)),
        output_format=str(s.value("audio/custom/format", base.output_format)),
    )


def save_custom(a: AudioSettings) -> None:
    s = _qs()
    s.setValue("audio/custom/bitrate", a.bitrate_kbps)
    s.setValue("audio/custom/bass", a.bass_gain_db)
    s.setValue("audio/custom/treble", a.treble_gain_db)
    s.setValue("audio/custom/denoise", a.denoise_strength)
    s.setValue("audio/custom/loudnorm", a.loudness_normalize)
    s.setValue("audio/custom/dynaudnorm", a.dynaudnorm)
    s.setValue("audio/custom/sample_rate", a.sample_rate)
    s.setValue("audio/custom/format", a.output_format)
