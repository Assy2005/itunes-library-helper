"""Clickable preset card used by the Audio tab.

Looks like a tile: emoji + preset name + 1-line tagline. Selected
state styled via QSS object names so themes apply consistently.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
)


# Visual metadata for each preset name. Matches keys in audio_presets.PRESETS.
PRESET_META: dict[str, dict[str, str]] = {
    "原音忠実":     {"icon": "💎", "tag": "320kbps ・ 処理なし"},
    "ポップ":       {"icon": "🎤", "tag": "低音+3 高音+2 ・ 256k"},
    "EDM・重低音":  {"icon": "🔊", "tag": "低音+8 ・ ラウドネス"},
    "ボーカル強調": {"icon": "🎙", "tag": "高音+4 デノイズ"},
    "クリア・高解像度": {"icon": "✨", "tag": "デノイズ + 48kHz"},
    "カスタム":     {"icon": "🎚", "tag": "全パラメータ調整"},
}


class PresetCard(QFrame):
    clicked = pyqtSignal(str)  # emits preset name

    def __init__(self, name: str) -> None:
        super().__init__()
        self._name = name
        self.setObjectName("preset_card")
        self.setProperty("selected", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(96)

        meta = PRESET_META.get(name, {"icon": "🎵", "tag": ""})

        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(12)

        icon = QLabel(meta["icon"])
        icon.setObjectName("preset_card_icon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedWidth(40)
        outer.addWidget(icon)

        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(2)
        title = QLabel(name)
        title.setObjectName("preset_card_title")
        col.addWidget(title)
        tag = QLabel(meta["tag"])
        tag.setObjectName("preset_card_tag")
        col.addWidget(tag)
        outer.addLayout(col, 1)

    def name(self) -> str:
        return self._name

    def set_selected(self, sel: bool) -> None:
        self.setProperty("selected", sel)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, e) -> None:  # noqa: D401
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._name)
        super().mousePressEvent(e)
