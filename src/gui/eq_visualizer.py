"""Frequency response curve visualization.

Renders a small "EQ curve" reflecting the current bass/treble shelf
gains, so the user can see at a glance what their settings will do
to the audio. Pure QPainter — no extra dependencies.

The curves are simple analytical approximations of low-shelf and
high-shelf filters, not literal ffmpeg responses; the goal is to
communicate the shape of the change, not to be DSP-accurate.
"""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import QSizePolicy, QWidget


# Display range
_FREQ_MIN = 50.0       # Hz
_FREQ_MAX = 16000.0    # Hz
_DB_RANGE = 14.0       # ± dB shown around 0dB

# Filter shaping constants (rough approximations to a shelf)
_BASS_CORNER = 250.0   # frequency where bass shelf is at half effect
_TREBLE_CORNER = 3000.0


def _bass_factor(freq_hz: float) -> float:
    # Returns 1.0 at low freqs, decays to ~0 well above the corner.
    return 1.0 / (1.0 + (freq_hz / _BASS_CORNER) ** 2)


def _treble_factor(freq_hz: float) -> float:
    return 1.0 / (1.0 + (_TREBLE_CORNER / freq_hz) ** 2)


class EQVisualizer(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._bass_db = 0
        self._treble_db = 0
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(140)

    def set_values(self, bass_db: int, treble_db: int) -> None:
        self._bass_db = bass_db
        self._treble_db = treble_db
        self.update()

    # ------------------------------------------------------------------ #

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        if w <= 0 or h <= 0:
            return

        # Background — rounded card-like rectangle.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#fafafc"))
        painter.drawRoundedRect(0, 0, w, h, 10, 10)

        margin_x = 24
        margin_y = 18
        inner_w = w - margin_x * 2
        inner_h = h - margin_y * 2
        center_y = margin_y + inner_h // 2

        # Horizontal reference lines: 0dB and ±half-range markers.
        grid_pen = QPen(QColor("#e5e5ea"))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        for db_offset in (-_DB_RANGE / 2, 0, _DB_RANGE / 2):
            y = center_y - int((db_offset / _DB_RANGE) * inner_h)
            painter.drawLine(margin_x, y, margin_x + inner_w, y)

        # Compute curve points across log-spaced frequencies.
        points: list[QPointF] = []
        log_min = math.log10(_FREQ_MIN)
        log_max = math.log10(_FREQ_MAX)
        steps = max(64, inner_w)
        for i in range(steps + 1):
            t = i / steps
            freq = 10 ** (log_min + t * (log_max - log_min))
            gain = (self._bass_db * _bass_factor(freq)
                    + self._treble_db * _treble_factor(freq))
            x = margin_x + t * inner_w
            y = center_y - (gain / _DB_RANGE) * inner_h
            points.append(QPointF(x, y))

        # Filled gradient under the curve, anchored at the 0dB line so
        # negative gains would show below — even though our presets
        # never go negative.
        path = QPainterPath()
        path.moveTo(points[0].x(), center_y)
        for p in points:
            path.lineTo(p)
        path.lineTo(points[-1].x(), center_y)
        path.closeSubpath()
        grad = QLinearGradient(0, margin_y, 0, center_y)
        grad.setColorAt(0.0, QColor(252, 60, 68, 110))
        grad.setColorAt(1.0, QColor(252, 60, 68, 0))
        painter.setBrush(grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)

        # Curve line on top.
        curve_pen = QPen(QColor("#fc3c44"))
        curve_pen.setWidthF(2.0)
        painter.setPen(curve_pen)
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

        # Labels.
        painter.setPen(QColor("#86868b"))
        font = QFont(self.font())
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(4, margin_y + 10, "+dB")
        painter.drawText(4, h - 4, "−dB")
        painter.drawText(margin_x, h - 4, "50Hz")
        painter.drawText(margin_x + inner_w // 2 - 14, h - 4, "1kHz")
        painter.drawText(margin_x + inner_w - 36, h - 4, "16kHz")
        painter.drawText(4, center_y + 4, "0dB")

        # Numeric readout in the corner.
        readout = (f"Bass +{self._bass_db}dB   "
                   f"Treble +{self._treble_db}dB"
                   if (self._bass_db or self._treble_db)
                   else "フラット")
        painter.setPen(QColor("#6e6e73"))
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(margin_x, margin_y + 4, readout)
