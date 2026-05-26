"""Dialog that explains ffmpeg and offers a one-click winget install.

Strategy:
  * The actual install runs in a *new visible cmd window* spawned by
    `ffmpeg_helper.launch_winget_install`. We never pipe its stdout —
    winget's spinner output deadlocks line-buffered readers, and
    suppressing the console hides the UAC prompt.
  * This dialog polls `ffmpeg_helper.is_installed()` once a second.
    When ffmpeg appears on disk (either on PATH or in the winget
    Links shim directory) we surface a "再起動" call to action.
  * The "あとで" and "ダウンロードページ" buttons stay enabled at all
    times so the user can never get trapped on this screen.
"""
from __future__ import annotations

import webbrowser

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import ffmpeg_helper


class FFmpegInstallDialog(QDialog):
    def __init__(self, parent: QWidget | None = None,
                 *, reason: str | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ffmpeg が必要です")
        self.setModal(True)
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 22)
        layout.setSpacing(14)

        title = QLabel("🎬  ffmpeg が見つかりません")
        title.setStyleSheet(
            "font-size: 20px; font-weight: 700; color: #1d1d1f;")
        layout.addWidget(title)

        if reason:
            r = QLabel(f"原因: {reason}")
            r.setStyleSheet("color: #b46100; font-size: 12px;")
            r.setWordWrap(True)
            layout.addWidget(r)

        body = QLabel(
            "このアプリは音質処理 (ビットレート変換 / 重低音強化 / ノイズ除去など) と、"
            "YouTube等からの音源抽出に <b>ffmpeg</b> を使用します。"
            "ffmpeg は無料の独立ツールで、別途インストールが必要です。"
            "<br><br>"
            "下の <b>「自動インストール」</b> を押すと、新しいコンソール窓で "
            "<code>winget</code> によるインストールが始まります "
            "(UAC許可ダイアログが出たら「はい」を押してください)。"
            "完了すると下のステータスが自動で更新されます。"
        )
        body.setWordWrap(True)
        body.setStyleSheet("color: #1d1d1f; font-size: 13px; line-height: 18px;")
        body.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(body)

        # Live status indicator (updated every second)
        self.status_label = QLabel("⚪  ffmpeg 未検出")
        self.status_label.setStyleSheet(
            "color: #6e6e73; font-size: 13px; padding: 6px 0;")
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.hide()
        layout.addWidget(self.progress)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        self.later_btn = QPushButton("あとで")
        self.later_btn.setObjectName("secondary")
        self.later_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.later_btn)

        self.download_btn = QPushButton("📥 ダウンロードページ")
        self.download_btn.setObjectName("secondary")
        self.download_btn.clicked.connect(
            lambda: webbrowser.open(ffmpeg_helper.MANUAL_DOWNLOAD_URL))
        btn_row.addWidget(self.download_btn)

        if ffmpeg_helper.winget_available():
            self.install_btn = QPushButton("⚡ 自動インストール (winget)")
            self.install_btn.clicked.connect(self._start_install)
            btn_row.addWidget(self.install_btn)
        else:
            self.install_btn = None
            note = QLabel(
                "ℹ️ winget が見つからないため自動インストールは使えません。"
                "「ダウンロードページ」から手動でインストールしてください。"
            )
            note.setStyleSheet("color: #b46100; font-size: 11px;")
            note.setWordWrap(True)
            layout.addWidget(note)

        self.restart_btn = QPushButton("🔄 完了 — アプリを終了して再起動")
        self.restart_btn.clicked.connect(self.accept)
        self.restart_btn.hide()
        btn_row.addWidget(self.restart_btn)

        layout.addLayout(btn_row)

        # Poll for ffmpeg every second.
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll)
        self._poll_timer.start(1000)
        self._installed_seen = ffmpeg_helper.is_installed()
        self._update_status()

    # --------------------------------------------------------------------- #

    def _start_install(self) -> None:
        try:
            ffmpeg_helper.launch_winget_install()
        except Exception as e:
            self.status_label.setText(f"❌  winget の起動に失敗: {e}")
            self.status_label.setStyleSheet(
                "color: #cf2e35; font-size: 13px; padding: 6px 0;")
            return

        if self.install_btn:
            self.install_btn.setEnabled(False)
            self.install_btn.setText("インストール窓で進行中…")
        self.progress.show()
        self.status_label.setText(
            "⏳  別ウィンドウでインストール中です。"
            "UAC が出たら「はい」を押してください。"
        )
        self.status_label.setStyleSheet(
            "color: #3478f6; font-size: 13px; padding: 6px 0;")

    def _poll(self) -> None:
        installed_now = ffmpeg_helper.is_installed()
        if installed_now and not self._installed_seen:
            self._on_detected()
        self._installed_seen = installed_now

    def _update_status(self) -> None:
        if self._installed_seen:
            self._on_detected()

    def _on_detected(self) -> None:
        self._poll_timer.stop()
        self.progress.hide()
        self.status_label.setText(
            "✅  <b>ffmpeg を検出しました！</b><br>"
            "PATH 反映のため、このアプリを<b>一度終了して再起動</b>してください。"
        )
        self.status_label.setStyleSheet(
            "color: #1f8a37; font-size: 13px; padding: 6px 0;")
        self.status_label.setTextFormat(Qt.TextFormat.RichText)
        if self.install_btn:
            self.install_btn.hide()
        self.download_btn.hide()
        self.later_btn.hide()
        self.restart_btn.show()
