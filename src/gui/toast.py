"""Small bottom-right slide-in toast for completion / error messages.

Self-contained: only depends on PyQt6 and the QSS rules for #toast
already defined in style.py. Multiple toasts stack upward; each one
auto-dismisses after a few seconds.
"""
from __future__ import annotations

from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    Qt,
    QTimer,
)
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class _Toast(QFrame):
    """Single toast tile. Animates in, then out after `lifetime_ms`."""

    def __init__(self, parent: QWidget, icon: str, title: str,
                 body: str, lifetime_ms: int = 4500) -> None:
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # The toast paints over normal content but should not steal clicks
        # from underneath when it's mid-animation.
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setFixedWidth(340)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(0, 0, 0, 90))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 12, 10, 12)
        outer.setSpacing(12)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 22px; color: white;")
        icon_lbl.setFixedWidth(28)
        outer.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignTop)

        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("toast_title")
        col.addWidget(title_lbl)
        body_lbl = QLabel(body)
        body_lbl.setObjectName("toast_body")
        body_lbl.setWordWrap(True)
        col.addWidget(body_lbl)
        outer.addLayout(col, 1)

        close = QPushButton("✕")
        close.setFlat(True)
        close.setFixedSize(24, 24)
        close.setStyleSheet(
            "QPushButton { color: #d2d2d7; background: transparent; border: none; "
            "font-size: 14px; }"
            "QPushButton:hover { color: white; }"
        )
        close.clicked.connect(self._dismiss)
        outer.addWidget(close, 0, Qt.AlignmentFlag.AlignTop)

        self.adjustSize()

        self._slide_in: QPropertyAnimation | None = None
        self._slide_out: QPropertyAnimation | None = None
        self._lifetime = lifetime_ms

    def show_at(self, target_pos: QPoint, start_offset: int = 320) -> None:
        # Start off-screen to the right, slide left into target_pos.
        start = QPoint(target_pos.x() + start_offset, target_pos.y())
        self.move(start)
        self.show()
        self.raise_()

        self._slide_in = QPropertyAnimation(self, b"pos", self)
        self._slide_in.setDuration(280)
        self._slide_in.setStartValue(start)
        self._slide_in.setEndValue(target_pos)
        self._slide_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._slide_in.start()

        QTimer.singleShot(self._lifetime, self._dismiss)

    def _dismiss(self) -> None:
        if self._slide_out is not None:
            return
        end = self.pos() + QPoint(self.width() + 40, 0)
        self._slide_out = QPropertyAnimation(self, b"pos", self)
        self._slide_out.setDuration(220)
        self._slide_out.setStartValue(self.pos())
        self._slide_out.setEndValue(end)
        self._slide_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self._slide_out.finished.connect(self.deleteLater)
        self._slide_out.start()


class ToastManager:
    """Stacks toasts in the bottom-right corner of the host window."""

    MARGIN = 16
    SPACING = 10

    def __init__(self, host: QWidget) -> None:
        self.host = host
        self._toasts: list[_Toast] = []

    def show(self, icon: str, title: str, body: str = "") -> None:
        toast = _Toast(self.host, icon, title, body)
        toast.destroyed.connect(lambda *_: self._remove(toast))
        self._toasts.append(toast)
        self._relayout()

    def _remove(self, toast: _Toast) -> None:
        if toast in self._toasts:
            self._toasts.remove(toast)
        self._relayout()

    def _relayout(self) -> None:
        # Position each toast from bottom-right upward.
        host_rect = self.host.rect()
        x = host_rect.right() - 340 - self.MARGIN
        y = host_rect.bottom() - self.MARGIN
        for t in reversed(self._toasts):
            t.adjustSize()
            y -= t.height()
            target = QPoint(x, y)
            if t.isVisible():
                # Already showing — slide to the new spot if it moved.
                if t.pos() != target:
                    anim = QPropertyAnimation(t, b"pos", t)
                    anim.setDuration(180)
                    anim.setStartValue(t.pos())
                    anim.setEndValue(target)
                    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                    anim.start()
            else:
                t.show_at(target)
            y -= self.SPACING
