"""Apple Music-style top header bar: page title + right-aligned status chips."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)


PAGE_TITLES = ["取り込み", "音質", "設定", "ログ"]


class StatusChip(QLabel):
    """Pill-shaped chip used in the header right side."""

    def __init__(self, text: str = "") -> None:
        super().__init__(text)
        self.setObjectName("chip")

    def set_state(self, text: str, *, ok: bool | None = None) -> None:
        self.setText(text)
        self.setObjectName("chip_ok" if ok else "chip_warn" if ok is False else "chip")
        self.style().unpolish(self)
        self.style().polish(self)


class HeaderBar(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("header")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(64)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 28, 0)
        row.setSpacing(8)

        self.title = QLabel(PAGE_TITLES[0])
        self.title.setObjectName("header_title")
        row.addWidget(self.title, 1)

        # Right-aligned status chips
        self.queue_chip = StatusChip("⏸  アイドル")
        self.preset_chip = StatusChip("🎚 —")
        self.ffmpeg_chip = StatusChip("ffmpeg —")
        for w in (self.queue_chip, self.preset_chip, self.ffmpeg_chip):
            row.addWidget(w)

    def set_page(self, index: int) -> None:
        if 0 <= index < len(PAGE_TITLES):
            self.title.setText(PAGE_TITLES[index])

    def set_queue(self, n: int) -> None:
        self.queue_chip.set_state(
            f"⏵  処理中 {n}件" if n else "⏸  アイドル",
            ok=True if n > 0 else None,
        )

    def set_preset(self, name: str) -> None:
        self.preset_chip.set_state(f"🎚 {name}")

    def set_ffmpeg(self, available: bool) -> None:
        self.ffmpeg_chip.set_state(
            "● ffmpeg" if available else "○ ffmpeg",
            ok=available,
        )
