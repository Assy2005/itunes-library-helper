"""Per-import job card.

One card represents one ongoing or finished import. It surfaces the
current pipeline step, a progress bar, and post-completion actions
(reveal-again / launch Apple Music / dismiss / retry-on-error).

The card has its own signals so a parent queue widget can react to
"dismiss me" without coupling to the worker lifetime.
"""
from __future__ import annotations

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from .. import apple_music_helper


def _truncate(text: str, limit: int = 64) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


class ImportItemCard(QFrame):
    """Visual representation of one import job."""

    dismissed = pyqtSignal(object)        # emits self
    retry_requested = pyqtSignal(object)  # emits self

    def __init__(self, source: str, is_url: bool) -> None:
        super().__init__()
        self.setObjectName("job_card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._source = source
        self._is_url = is_url
        self._output_path: str | None = None

    # Accessors for the parent to drive a retry without storing extra state.
    @property
    def source(self) -> str:
        return self._source

    @property
    def is_url(self) -> bool:
        return self._is_url

        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 12, 12, 12)
        outer.setSpacing(12)

        icon = QLabel("🌐" if is_url else "📁")
        icon.setStyleSheet("font-size: 22px;")
        icon.setFixedWidth(28)
        outer.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)

        center = QVBoxLayout()
        center.setContentsMargins(0, 0, 0, 0)
        center.setSpacing(4)

        display_name = source if is_url else os.path.basename(source)
        self._title = QLabel(_truncate(display_name))
        self._title.setObjectName("job_title")
        self._title.setToolTip(source)
        center.addWidget(self._title)

        self._status = QLabel("待機中…")
        self._status.setObjectName("job_status")
        center.addWidget(self._status)

        self._progress = QProgressBar()
        self._progress.setObjectName("job_progress")
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(4)
        center.addWidget(self._progress)

        outer.addLayout(center, 1)

        self._actions = QHBoxLayout()
        self._actions.setContentsMargins(0, 0, 0, 0)
        self._actions.setSpacing(6)
        actions_wrap = QFrame()
        actions_wrap.setLayout(self._actions)
        outer.addWidget(actions_wrap, 0, Qt.AlignmentFlag.AlignTop)

        self._dismiss_btn: QPushButton | None = None

    # -- slots called by the worker ----------------------------------------- #

    def set_status(self, text: str) -> None:
        self._status.setText(text)
        self._status.setObjectName("job_status")
        self._restyle(self._status)

    def set_progress(self, value: int) -> None:
        self._progress.setValue(max(0, min(100, value)))

    def mark_success(self, output_path: str, summary: str) -> None:
        self._output_path = output_path
        self._status.setText(f"✓ {summary}")
        self._status.setObjectName("job_status_ok")
        self._restyle(self._status)
        self._progress.setValue(100)
        self._show_success_actions()

    def mark_error(self, message: str) -> None:
        self._status.setText(f"❌ {message}")
        self._status.setObjectName("job_status_err")
        self._restyle(self._status)
        self._progress.setValue(0)
        self._show_error_actions()

    def reset_for_retry(self) -> None:
        """Restore visual state so the same card can be reused for a retry."""
        self._output_path = None
        self._progress.setValue(0)
        self._status.setText("待機中…")
        self._status.setObjectName("job_status")
        self._restyle(self._status)
        self._clear_actions()

    # -- internals ---------------------------------------------------------- #

    def _restyle(self, widget) -> None:
        # QSS reapplies based on objectName; force a refresh.
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)

    def _clear_actions(self) -> None:
        while self._actions.count():
            item = self._actions.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _show_success_actions(self) -> None:
        self._clear_actions()
        if self._output_path:
            edit = QPushButton("✏️")
            edit.setObjectName("secondary")
            edit.setToolTip("メタデータ / アートワーク編集")
            edit.setFixedWidth(40)
            edit.clicked.connect(self._open_metadata_dialog)
            self._actions.addWidget(edit)

            reveal = QPushButton("📂")
            reveal.setObjectName("secondary")
            reveal.setToolTip("エクスプローラで開く")
            reveal.setFixedWidth(40)
            reveal.clicked.connect(
                lambda: apple_music_helper.reveal_in_explorer(
                    self._output_path or "")
            )
            self._actions.addWidget(reveal)
        self._add_dismiss()

    def _open_metadata_dialog(self) -> None:
        if not self._output_path:
            return
        # Imported lazily to avoid a circular import at module load.
        from .metadata_dialog import MetadataDialog
        MetadataDialog(self._output_path, self).exec()

    def _show_dismiss_only(self) -> None:
        self._clear_actions()
        self._add_dismiss()

    def _show_error_actions(self) -> None:
        self._clear_actions()
        retry = QPushButton("↻")
        retry.setObjectName("secondary")
        retry.setToolTip("もう一度実行")
        retry.setFixedWidth(40)
        retry.clicked.connect(lambda: self.retry_requested.emit(self))
        self._actions.addWidget(retry)
        self._add_dismiss()

    def _add_dismiss(self) -> None:
        btn = QPushButton("✕")
        btn.setObjectName("secondary")
        btn.setToolTip("リストから消す")
        btn.setFixedWidth(40)
        btn.clicked.connect(lambda: self.dismissed.emit(self))
        self._actions.addWidget(btn)
        self._dismiss_btn = btn
