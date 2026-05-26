"""Main application window."""
from __future__ import annotations

import os
import tempfile

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import converter, downloader, itunes_client


class ImportWorker(QThread):
    """Runs the download → convert → add-to-library pipeline off the UI thread."""

    log = pyqtSignal(str)
    finished_ok = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, source: str, is_url: bool, work_dir: str) -> None:
        super().__init__()
        self.source = source
        self.is_url = is_url
        self.work_dir = work_dir

    def run(self) -> None:
        try:
            if self.is_url:
                self.log.emit(f"Downloading: {self.source}")
                result = downloader.download(self.source, self.work_dir)
                path = result.path
            else:
                path = self.source

            if converter.needs_conversion(path):
                self.log.emit(f"Converting to .m4a: {os.path.basename(path)}")
                path = converter.convert_to_m4a(path, self.work_dir)

            self.log.emit("Adding to iTunes library…")
            client = itunes_client.ITunesClient()
            added = client.add_file(path)
            self.finished_ok.emit(
                f"Added: {added.name or os.path.basename(path)}"
                + (f" — {added.artist}" if added.artist else "")
            )
        except Exception as e:  # surfaced to the UI
            self.failed.emit(f"{type(e).__name__}: {e}")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("iTunes Library Helper")
        self.resize(720, 480)
        self.setAcceptDrops(True)

        self._work_dir = os.path.join(tempfile.gettempdir(), "itunes-library-helper")
        os.makedirs(self._work_dir, exist_ok=True)
        self._workers: list[ImportWorker] = []

        central = QWidget()
        layout = QVBoxLayout(central)

        layout.addWidget(QLabel("URL から追加（YouTube 等の動画 / .mp3 などの直リンク）"))
        url_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://…")
        add_url_btn = QPushButton("URL から追加")
        add_url_btn.clicked.connect(self._on_add_url)
        url_row.addWidget(self.url_input)
        url_row.addWidget(add_url_btn)
        layout.addLayout(url_row)

        layout.addWidget(QLabel("ファイルから追加（ボタンまたはドラッグ&ドロップ）"))
        pick_btn = QPushButton("ファイルを選択…")
        pick_btn.clicked.connect(self._on_pick_files)
        layout.addWidget(pick_btn)

        layout.addWidget(QLabel("ログ"))
        self.log_list = QListWidget()
        layout.addWidget(self.log_list, 1)

        self.setCentralWidget(central)

    # ---- drag & drop ----
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        for p in paths:
            self._start_import(p, is_url=False)

    # ---- actions ----
    def _on_add_url(self) -> None:
        url = self.url_input.text().strip()
        if not url:
            return
        self._start_import(url, is_url=True)
        self.url_input.clear()

    def _on_pick_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "音楽ファイルを選択",
            "",
            "Audio Files (*.mp3 *.m4a *.aac *.wav *.flac *.ogg *.opus *.aiff);;All Files (*.*)",
        )
        for p in paths:
            self._start_import(p, is_url=False)

    # ---- worker plumbing ----
    def _start_import(self, source: str, is_url: bool) -> None:
        worker = ImportWorker(source, is_url, self._work_dir)
        worker.log.connect(self._append_log)
        worker.finished_ok.connect(self._on_done)
        worker.failed.connect(self._on_failed)
        worker.finished.connect(lambda w=worker: self._workers.remove(w))
        self._workers.append(worker)
        worker.start()

    def _append_log(self, msg: str) -> None:
        self.log_list.addItem(msg)

    def _on_done(self, msg: str) -> None:
        self._append_log(msg)

    def _on_failed(self, msg: str) -> None:
        self._append_log(f"ERROR: {msg}")
        QMessageBox.warning(self, "追加に失敗しました", msg)
