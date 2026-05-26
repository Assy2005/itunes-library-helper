"""Audio processing presets.

Each preset describes a chain of ffmpeg audio filters plus an output
bitrate. They are designed to be musically sensible defaults — the user
can still override any individual value via the "Custom" preset.

A value of `0` for bass_gain / treble_gain / denoise / dynaudnorm means
"do not apply that filter at all" (kept out of the chain entirely).
"""
from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class AudioSettings:
    bitrate_kbps: int = 256           # 128 / 192 / 256 / 320
    bass_gain_db: int = 0             # 0 = off, typical range 0–12
    treble_gain_db: int = 0           # 0 = off, typical range 0–6
    denoise_strength: int = 0         # 0 = off, 1–3 maps to afftdn nr=8/12/18
    loudness_normalize: bool = False  # apply EBU R128 loudnorm
    dynaudnorm: bool = False          # smooth out volume dips
    sample_rate: int = 0              # 0 = passthrough, e.g. 48000 to upsample
    output_format: str = "m4a"        # m4a or mp3


PRESETS: dict[str, AudioSettings] = {
    "原音忠実": AudioSettings(
        bitrate_kbps=320,
    ),
    "ポップ": AudioSettings(
        bitrate_kbps=256,
        bass_gain_db=3,
        treble_gain_db=2,
        dynaudnorm=True,
    ),
    "EDM・重低音": AudioSettings(
        bitrate_kbps=320,
        bass_gain_db=8,
        treble_gain_db=2,
        loudness_normalize=True,
    ),
    "ボーカル強調": AudioSettings(
        bitrate_kbps=256,
        treble_gain_db=4,
        denoise_strength=2,
        loudness_normalize=True,
    ),
    "クリア・高解像度": AudioSettings(
        bitrate_kbps=320,
        treble_gain_db=2,
        denoise_strength=1,
        sample_rate=48000,
    ),
    "カスタム": AudioSettings(),  # filled in by the user in the GUI
}

DEFAULT_PRESET = "ポップ"


def from_preset(name: str) -> AudioSettings:
    return PRESETS.get(name, PRESETS[DEFAULT_PRESET])


def customize(base: AudioSettings, **overrides) -> AudioSettings:
    return replace(base, **overrides)
