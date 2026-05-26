"""Dialog that explains ffmpeg and offers a one-click winget install."""
from __future__ import annotations

import webbrowser

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import ffmpeg_helper


class _InstallWorker(QThread):
    """Streams winget output line-by-line; emits exit code at the end."""

    line = pyqtSignal(str)
    finished_code = pyqtSignal(int)

    def run(self) -> None:
        try:
            proc = ffmpeg_helper.install_via_winget()
        except Exception as e:
            self.line.emit(f"⚠️  起動エラー: {e}")
            self.finished_code.emit(-1)
            return

        assert proc.stdout is not None
        for raw in proc.stdout:
            text = raw.rstrip()
            if text:
                self.line.emit(text)
        proc.wait()
        self.finished_code.emit(proc.returncode)


class FFmpegInstallDialog(QDialog):
    """Modal dialog prompting the user to install ffmpeg.

    Behaviour:
      - shows what ffmpeg is and why we need it;
      - if winget is available, offers a one-click install;
      - otherwise (or as a fallback) offers a "download page" link.
    """

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
            "下のボタンから <b>ワンクリックで自動インストール</b> できます (winget利用)。"
            "うまく行かない場合は手動ダウンロードのリンクもあります。"
        )
        body.setWordWrap(True)
        body.setStyleSheet("color: #1d1d1f; font-size: 13px; line-height: 18px;")
        layout.addWidget(body)

        # Output log box (hidden until install starts)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("インストール出力がここに表示されます…")
        self.log.setMaximumHeight(160)
        self.log.setStyleSheet(
            "background: #1d1d1f; color: #f5f5f7; font-family: Consolas, "
            "Menlo, monospace; font-size: 11px; border-radius: 8px; padding: 8px;")
        self.log.hide()
        layout.addWidget(self.log)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.hide()
        layout.addWidget(self.progress)

        # Status line (success / error after install)
        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        self.result_label.hide()
        layout.addWidget(self.result_label)

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
            note = QLabel("ℹ️ winget が見つからないため自動インストールは使えません。"
                          "右のボタンから手動ダウンロードしてください。")
            note.setStyleSheet("color: #b46100; font-size: 11px;")
            note.setWordWrap(True)
            layout.addWidget(note)

        # Restart hint shown after a successful install
        self.restart_btn = QPushButton("🔄 アプリを再起動するには閉じる")
        self.restart_btn.clicked.connect(self.accept)
        self.restart_btn.hide()
        btn_row.addWidget(self.restart_btn)

        layout.addLayout(btn_row)

        self._worker: _InstallWorker | None = None

    # --------------------------------------------------------------------- #

    def _start_install(self) -> None:
        if self.install_btn:
            self.install_btn.setEnabled(False)
            self.install_btn.setText("インストール中…")
        self.later_btn.setEnabled(False)
        self.download_btn.setEnabled(False)
        self.log.show()
        self.progress.show()
        self.log.appendPlainText(
            f"$ winget install --id {ffmpeg_helper.WINGET_PACKAGE_ID}")

        self._worker = _InstallWorker()
        self._worker.line.connect(self.log.appendPlainText)
        self._worker.finished_code.connect(self._on_install_done)
        self._worker.start()

    def _on_install_done(self, code: int) -> None:
        self.progress.hide()
        # winget exit codes: 0 = success, -1978335212 = already installed, etc.
        # Treat ffmpeg being on PATH as the real success signal regardless.
        now_installed = ffmpeg_helper.is_installed()

        if code == 0 or now_installed:
            self.result_label.setText(
                "✅ <b>インストール成功</b><br>"
                "PATH 反映のため、このアプリを<b>一度終了して再起動</b>してください。"
            )
            self.result_label.setStyleSheet(
                "color: #1f8a37; font-size: 13px; padding: 8px;")
            self.result_label.show()
            if self.install_btn:
                self.install_btn.hide()
            self.download_btn.hide()
            self.later_btn.hide()
            self.restart_btn.show()
        else:
            self.result_label.setText(
                f"❌ <b>インストールに失敗しました</b> (winget exit code: {code})<br>"
                "右上の「ダウンロードページ」から手動でインストールしてください。"
            )
            self.result_label.setStyleSheet(
                "color: #cf2e35; font-size: 13px; padding: 8px;")
            self.result_label.show()
            if self.install_btn:
                self.install_btn.setEnabled(True)
                self.install_btn.setText("⚡ 自動インストール (winget)")
            self.later_btn.setEnabled(True)
            self.download_btn.setEnabled(True)
