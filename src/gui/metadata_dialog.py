"""Edit a processed file's tags + artwork.

Reads current tags via mutagen, lets the user tweak them or fetch a
new artwork via the iTunes Search API, then writes everything back to
the file.
"""
from __future__ import annotations

import os

from PyQt6.QtCore import QSize, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import artwork, metadata


class _SearchWorker(QThread):
    """Runs iTunes Search off the UI thread so the dialog stays responsive."""

    done = pyqtSignal(object, bytes)   # ArtworkHit, image bytes
    failed = pyqtSignal(str)

    def __init__(self, query: str) -> None:
        super().__init__()
        self.query = query

    def run(self) -> None:
        try:
            result = artwork.best_match(self.query)
            if result:
                hit, img = result
                self.done.emit(hit, img)
            else:
                self.failed.emit("一致する曲が見つかりませんでした")
        except Exception as e:
            self.failed.emit(f"{type(e).__name__}: {e}")


class MetadataDialog(QDialog):
    def __init__(self, path: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.path = path
        self.setWindowTitle(f"メタデータ編集 — {os.path.basename(path)}")
        self.setModal(True)
        self.resize(560, 480)

        self._artwork_bytes: bytes | None = None
        self._search_worker: _SearchWorker | None = None

        root = QHBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(16)

        # Left: artwork preview + actions
        left = QVBoxLayout()
        left.setSpacing(8)
        self.art_label = QLabel("(なし)")
        self.art_label.setFixedSize(200, 200)
        self.art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.art_label.setStyleSheet(
            "background: #1c1c1e; border: 1px dashed #48484a; "
            "border-radius: 8px; color: #8e8e93;"
        )
        left.addWidget(self.art_label)

        pick_btn = QPushButton("📁  画像ファイルを選択…")
        pick_btn.setObjectName("secondary")
        pick_btn.clicked.connect(self._pick_image)
        left.addWidget(pick_btn)

        self.search_btn = QPushButton("🔍  Apple Music で検索")
        self.search_btn.clicked.connect(self._search)
        left.addWidget(self.search_btn)

        clear_btn = QPushButton("✕  アートワーク削除")
        clear_btn.setObjectName("secondary")
        clear_btn.clicked.connect(self._clear_artwork)
        left.addWidget(clear_btn)

        left.addStretch(1)
        root.addLayout(left)

        # Right: text fields + save/cancel
        right = QVBoxLayout()
        right.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(10)
        self.title_edit = QLineEdit()
        self.artist_edit = QLineEdit()
        self.album_edit = QLineEdit()
        form.addRow("タイトル", self.title_edit)
        form.addRow("アーティスト", self.artist_edit)
        form.addRow("アルバム", self.album_edit)
        right.addLayout(form)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #aeaeb2; font-size: 11px;")
        self.status_label.setWordWrap(True)
        right.addWidget(self.status_label)

        right.addStretch(1)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        cancel = QPushButton("キャンセル")
        cancel.setObjectName("secondary")
        cancel.clicked.connect(self.reject)
        save = QPushButton("💾  保存")
        save.clicked.connect(self._save)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        right.addLayout(btn_row)

        root.addLayout(right, 1)

        # Populate with current file tags.
        try:
            current = metadata.read(path)
            self.title_edit.setText(current.title or "")
            self.artist_edit.setText(current.artist or "")
            self.album_edit.setText(current.album or "")
        except Exception:
            pass

    # ---- artwork helpers ---- #
    def _set_artwork(self, data: bytes) -> None:
        self._artwork_bytes = data
        pix = QPixmap()
        if not pix.loadFromData(data):
            self.art_label.setText("(画像を読めません)")
            return
        scaled = pix.scaled(
            QSize(200, 200),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.art_label.setPixmap(scaled)
        self.art_label.setText("")

    def _clear_artwork(self) -> None:
        self._artwork_bytes = None
        self.art_label.clear()
        self.art_label.setText("(なし)")

    def _pick_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "アートワーク画像", "",
            "Images (*.jpg *.jpeg *.png);;All Files (*.*)",
        )
        if path:
            try:
                with open(path, "rb") as f:
                    self._set_artwork(f.read())
                self.status_label.setText(f"✓ {os.path.basename(path)} を選択")
            except OSError as e:
                self.status_label.setText(f"❌ 読み込みに失敗: {e}")

    def _search(self) -> None:
        query = f"{self.artist_edit.text()} {self.title_edit.text()}".strip()
        if not query:
            self.status_label.setText("⚠️ タイトルまたはアーティストを入力してください")
            return
        self.search_btn.setEnabled(False)
        self.search_btn.setText("検索中…")
        self.status_label.setText(f"🔍 \"{query}\" を検索しています…")

        self._search_worker = _SearchWorker(query)
        self._search_worker.done.connect(self._on_search_done)
        self._search_worker.failed.connect(self._on_search_failed)
        self._search_worker.start()

    def _on_search_done(self, hit, img: bytes) -> None:
        self.search_btn.setEnabled(True)
        self.search_btn.setText("🔍  Apple Music で検索")
        self._set_artwork(img)
        if hit.title:
            self.title_edit.setText(hit.title)
        if hit.artist:
            self.artist_edit.setText(hit.artist)
        if hit.album:
            self.album_edit.setText(hit.album)
        self.status_label.setText(
            f"✓ 一致: {hit.artist} — {hit.album}")

    def _on_search_failed(self, msg: str) -> None:
        self.search_btn.setEnabled(True)
        self.search_btn.setText("🔍  Apple Music で検索")
        self.status_label.setText(f"❌ {msg}")

    # ---- save ---- #
    def _save(self) -> None:
        meta = metadata.TrackMetadata(
            title=self.title_edit.text().strip() or None,
            artist=self.artist_edit.text().strip() or None,
            album=self.album_edit.text().strip() or None,
            artwork_bytes=self._artwork_bytes,
        )
        try:
            metadata.apply(self.path, meta)
        except Exception as e:
            QMessageBox.warning(self, "保存に失敗しました", str(e))
            return
        self.accept()
