"""Apple Music-styled main window."""
from __future__ import annotations

import os
import shutil

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .. import converter, downloader, itunes_client, settings
from ..audio_presets import PRESETS, AudioSettings


def _card(layout_cls=QVBoxLayout) -> tuple[QFrame, QVBoxLayout | QHBoxLayout]:
    """Create a styled card frame with an inner layout."""
    frame = QFrame()
    frame.setObjectName("card")
    inner = layout_cls(frame)
    inner.setContentsMargins(20, 18, 20, 18)
    inner.setSpacing(10)
    return frame, inner


def _heading(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("heading")
    return lbl


def _subheading(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("subheading")
    return lbl


def _hint(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("hint")
    lbl.setWordWrap(True)
    return lbl


# --------------------------------------------------------------------------- #
# Worker                                                                      #
# --------------------------------------------------------------------------- #

class ImportWorker(QThread):
    """Pipeline: (download?) → ffmpeg process → (iTunes add | file output)."""

    log = pyqtSignal(str)
    progress = pyqtSignal(int)         # 0..100
    finished_ok = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(
        self,
        source: str,
        is_url: bool,
        work_dir: str,
        out_dir: str,
        audio: AudioSettings,
        add_to_itunes: bool,
    ) -> None:
        super().__init__()
        self.source = source
        self.is_url = is_url
        self.work_dir = work_dir
        self.out_dir = out_dir
        self.audio = audio
        self.add_to_itunes = add_to_itunes

    def run(self) -> None:
        try:
            self.progress.emit(5)

            if self.is_url:
                self.log.emit(f"⬇️  ダウンロード開始: {self.source}")
                result = downloader.download(self.source, self.work_dir)
                path = result.path
                self.log.emit(f"   → {os.path.basename(path)}")
            else:
                path = self.source

            self.progress.emit(45)

            self.log.emit(f"🎚️  音質処理中 (preset={settings.preset_name()}, "
                          f"{self.audio.bitrate_kbps}kbps {self.audio.output_format})")
            path = converter.process(path, self.out_dir, self.audio)
            self.log.emit(f"   → {os.path.basename(path)}")

            self.progress.emit(80)

            if self.add_to_itunes and itunes_client.is_available():
                self.log.emit("🍎 iTunes ライブラリに追加中…")
                added = itunes_client.ITunesClient().add_file(path)
                name = added.name or os.path.basename(path)
                tail = f" — {added.artist}" if added.artist else ""
                self.finished_ok.emit(f"✓ ライブラリに追加: {name}{tail}")
            else:
                reason = (
                    "iTunes 連携OFF" if not self.add_to_itunes
                    else "iTunes 未インストール"
                )
                self.log.emit(f"📁 出力フォルダに保存（{reason}）")
                self.finished_ok.emit(f"✓ 保存しました: {path}")

            self.progress.emit(100)
        except Exception as e:
            self.failed.emit(f"{type(e).__name__}: {e}")


# --------------------------------------------------------------------------- #
# Import tab                                                                  #
# --------------------------------------------------------------------------- #

class ImportTab(QWidget):
    request_import = pyqtSignal(str, bool)  # source, is_url

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        layout.addWidget(_heading("音楽を追加"))
        layout.addWidget(_hint("URL（YouTube などの動画 / .mp3 などの直リンク）または"
                               "ローカルの音楽ファイルから取り込めます。"))

        # URL card
        url_card, url_l = _card()
        url_l.addWidget(_subheading("🌐 URL から追加"))
        row = QHBoxLayout()
        row.setSpacing(8)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=…  または  https://example.com/song.mp3")
        self.url_input.returnPressed.connect(self._submit_url)
        url_btn = QPushButton("追加")
        url_btn.clicked.connect(self._submit_url)
        row.addWidget(self.url_input, 1)
        row.addWidget(url_btn)
        url_l.addLayout(row)
        layout.addWidget(url_card)

        # File card
        file_card, file_l = _card()
        file_l.addWidget(_subheading("📁 ファイルから追加"))
        self.drop_target = QLabel("ここに音楽ファイルをドラッグ&ドロップ\n— または —")
        self.drop_target.setObjectName("drop_target")
        self.drop_target.setAlignment(Qt.AlignmentFlag.AlignCenter)
        file_l.addWidget(self.drop_target)
        pick_btn = QPushButton("ファイルを選択…")
        pick_btn.setObjectName("secondary")
        pick_btn.clicked.connect(self._pick_files)
        file_l.addWidget(pick_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(file_card)

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        layout.addStretch(1)

    def _submit_url(self) -> None:
        url = self.url_input.text().strip()
        if url:
            self.request_import.emit(url, True)
            self.url_input.clear()

    def _pick_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "音楽ファイルを選択", "",
            "Audio Files (*.mp3 *.m4a *.aac *.wav *.flac *.ogg *.opus *.aiff);;All Files (*.*)",
        )
        for p in paths:
            self.request_import.emit(p, False)

    def set_progress(self, v: int) -> None:
        self.progress.setValue(v)


# --------------------------------------------------------------------------- #
# Audio settings tab                                                          #
# --------------------------------------------------------------------------- #

class AudioTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        layout.addWidget(_heading("音質設定"))
        layout.addWidget(_hint("プリセットを選ぶか、カスタムで細かく調整できます。"
                               "変更内容は次回起動時にも保持されます。"))

        # Preset selector card
        preset_card, preset_l = _card()
        preset_l.addWidget(_subheading("🎛️ プリセット"))
        row = QHBoxLayout()
        self.preset_combo = QComboBox()
        for name in PRESETS:
            self.preset_combo.addItem(name)
        self.preset_combo.setCurrentText(settings.preset_name())
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        row.addWidget(self.preset_combo, 1)
        preset_l.addLayout(row)
        self.preset_desc = _hint("")
        preset_l.addWidget(self.preset_desc)
        layout.addWidget(preset_card)

        # Custom controls card
        custom_card, custom_l = _card()
        custom_l.addWidget(_subheading("🎚️ 詳細"))
        custom_l.addWidget(_hint("「カスタム」プリセット選択時のみ編集可能。他プリセット時は現在の値を表示。"))

        self.bitrate_combo = QComboBox()
        for kbps in (128, 192, 256, 320):
            self.bitrate_combo.addItem(f"{kbps} kbps", kbps)
        self._add_row(custom_l, "ビットレート", self.bitrate_combo)

        self.format_combo = QComboBox()
        self.format_combo.addItem("AAC (.m4a) — iTunes標準", "m4a")
        self.format_combo.addItem("MP3 (.mp3) — 汎用", "mp3")
        self._add_row(custom_l, "出力フォーマット", self.format_combo)

        self.bass_slider, self.bass_label = self._make_slider(0, 12, "dB")
        self._add_row(custom_l, "重低音強化", self._wrap_slider(self.bass_slider, self.bass_label))

        self.treble_slider, self.treble_label = self._make_slider(0, 6, "dB")
        self._add_row(custom_l, "高音強化", self._wrap_slider(self.treble_slider, self.treble_label))

        self.denoise_slider, self.denoise_label = self._make_slider(0, 3, "段階")
        self._add_row(custom_l, "ノイズ除去", self._wrap_slider(self.denoise_slider, self.denoise_label))

        self.sample_combo = QComboBox()
        self.sample_combo.addItem("そのまま (passthrough)", 0)
        self.sample_combo.addItem("44.1 kHz", 44100)
        self.sample_combo.addItem("48 kHz", 48000)
        self.sample_combo.addItem("96 kHz (ハイレゾ風)", 96000)
        self._add_row(custom_l, "サンプリングレート", self.sample_combo)

        self.loudnorm_cb = QCheckBox("ラウドネス正規化 (-16 LUFS, 放送基準)")
        self.dynaudnorm_cb = QCheckBox("ダイナミクス補正 (小さい音を聴きやすく)")
        custom_l.addWidget(self.loudnorm_cb)
        custom_l.addWidget(self.dynaudnorm_cb)

        save_btn = QPushButton("カスタム設定を保存")
        save_btn.clicked.connect(self._save_custom)
        custom_l.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(custom_card)
        layout.addStretch(1)

        self._load_into_controls(settings.audio_settings())
        self._on_preset_changed(self.preset_combo.currentText())

    def _add_row(self, parent: QVBoxLayout, label: str, widget: QWidget) -> None:
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setMinimumWidth(140)
        row.addWidget(lbl)
        row.addWidget(widget, 1)
        parent.addLayout(row)

    def _make_slider(self, lo: int, hi: int, suffix: str) -> tuple[QSlider, QLabel]:
        s = QSlider(Qt.Orientation.Horizontal)
        s.setRange(lo, hi)
        lbl = QLabel(f"0 {suffix}")
        lbl.setMinimumWidth(64)
        s.valueChanged.connect(lambda v, l=lbl, sx=suffix: l.setText(f"{v} {sx}"))
        return s, lbl

    def _wrap_slider(self, s: QSlider, lbl: QLabel) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(s, 1)
        h.addWidget(lbl)
        return w

    def _on_preset_changed(self, name: str) -> None:
        settings.set_preset_name(name)
        a = settings.audio_settings()
        self._load_into_controls(a)
        is_custom = name == "カスタム"
        for w in (self.bitrate_combo, self.format_combo, self.bass_slider,
                  self.treble_slider, self.denoise_slider, self.sample_combo,
                  self.loudnorm_cb, self.dynaudnorm_cb):
            w.setEnabled(is_custom)
        descriptions = {
            "原音忠実": "320kbps・処理なし。原音をそのまま高品質で保存。",
            "ポップ": "256kbps・軽い低音&高音ブースト+ダイナミクス補正。ポップ/J-POPに。",
            "EDM・重低音": "320kbps・重低音 +8dB、ラウドネス正規化。EDM/HipHop向け。",
            "ボーカル強調": "高音 +4dB、ノイズ除去、ラウドネス正規化。歌モノに。",
            "クリア・高解像度": "320kbps・軽いノイズ除去 + 48kHz アップサンプリング。",
            "カスタム": "下のスライダーで全パラメータを個別調整できます。",
        }
        self.preset_desc.setText(descriptions.get(name, ""))

    def _load_into_controls(self, a: AudioSettings) -> None:
        self.bitrate_combo.setCurrentIndex(max(0, self.bitrate_combo.findData(a.bitrate_kbps)))
        self.format_combo.setCurrentIndex(max(0, self.format_combo.findData(a.output_format)))
        self.bass_slider.setValue(a.bass_gain_db)
        self.treble_slider.setValue(a.treble_gain_db)
        self.denoise_slider.setValue(a.denoise_strength)
        self.sample_combo.setCurrentIndex(max(0, self.sample_combo.findData(a.sample_rate)))
        self.loudnorm_cb.setChecked(a.loudness_normalize)
        self.dynaudnorm_cb.setChecked(a.dynaudnorm)

    def _save_custom(self) -> None:
        a = AudioSettings(
            bitrate_kbps=self.bitrate_combo.currentData() or 256,
            bass_gain_db=self.bass_slider.value(),
            treble_gain_db=self.treble_slider.value(),
            denoise_strength=self.denoise_slider.value(),
            loudness_normalize=self.loudnorm_cb.isChecked(),
            dynaudnorm=self.dynaudnorm_cb.isChecked(),
            sample_rate=self.sample_combo.currentData() or 0,
            output_format=self.format_combo.currentData() or "m4a",
        )
        settings.save_custom(a)


# --------------------------------------------------------------------------- #
# Settings tab                                                                #
# --------------------------------------------------------------------------- #

class SettingsTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        layout.addWidget(_heading("設定"))

        out_card, out_l = _card()
        out_l.addWidget(_subheading("📁 出力フォルダ"))
        row = QHBoxLayout()
        self.folder_edit = QLineEdit(settings.output_folder())
        self.folder_edit.editingFinished.connect(
            lambda: settings.set_output_folder(self.folder_edit.text())
        )
        browse = QPushButton("変更…")
        browse.setObjectName("secondary")
        browse.clicked.connect(self._pick_folder)
        row.addWidget(self.folder_edit, 1)
        row.addWidget(browse)
        out_l.addLayout(row)
        out_l.addWidget(_hint("音質処理後のファイルがここに保存されます。"
                              "iTunes連携OFF時はここから手動で取り込んでください。"))
        layout.addWidget(out_card)

        it_card, it_l = _card()
        it_l.addWidget(_subheading("🍎 iTunes 連携"))
        self.itunes_cb = QCheckBox("取り込み時に自動で iTunes ライブラリに追加")
        self.itunes_cb.setChecked(settings.add_to_itunes())
        self.itunes_cb.toggled.connect(settings.set_add_to_itunes)
        it_l.addWidget(self.itunes_cb)

        itunes_ok = itunes_client.is_available()
        status = QLabel("● iTunes 検出済み" if itunes_ok else "● iTunes 未検出 — ファイル出力モードで動作")
        status.setObjectName("status_ok" if itunes_ok else "status_warn")
        it_l.addWidget(status)
        layout.addWidget(it_card)

        ff_card, ff_l = _card()
        ff_l.addWidget(_subheading("🎬 ffmpeg"))
        ff_ok = shutil.which("ffmpeg") is not None
        ff_status = QLabel(
            "● ffmpeg 検出済み" if ff_ok
            else "● ffmpeg が見つかりません — フォーマット変換と音質処理が使えません"
        )
        ff_status.setObjectName("status_ok" if ff_ok else "status_warn")
        ff_l.addWidget(ff_status)
        ff_l.addWidget(_hint("https://ffmpeg.org/ からダウンロードして PATH を通してください。"))
        layout.addWidget(ff_card)

        layout.addStretch(1)

    def _pick_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "出力フォルダ", self.folder_edit.text())
        if path:
            self.folder_edit.setText(path)
            settings.set_output_folder(path)


# --------------------------------------------------------------------------- #
# Log tab                                                                     #
# --------------------------------------------------------------------------- #

class LogTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)
        layout.addWidget(_heading("ログ"))
        self.list = QListWidget()
        layout.addWidget(self.list, 1)

    def append(self, msg: str) -> None:
        self.list.addItem(msg)
        self.list.scrollToBottom()


# --------------------------------------------------------------------------- #
# Main window                                                                 #
# --------------------------------------------------------------------------- #

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("iTunes Library Helper")
        self.resize(880, 640)
        self.setAcceptDrops(True)

        from .style import QSS
        self.setStyleSheet(QSS)

        self._workers: list[ImportWorker] = []

        central = QWidget()
        central.setObjectName("central")
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.import_tab = ImportTab()
        self.audio_tab = AudioTab()
        self.settings_tab = SettingsTab()
        self.log_tab = LogTab()
        self.tabs.addTab(self.import_tab, "📥  取り込み")
        self.tabs.addTab(self.audio_tab, "🎚️  音質")
        self.tabs.addTab(self.settings_tab, "⚙️  設定")
        self.tabs.addTab(self.log_tab, "📋  ログ")
        outer.addWidget(self.tabs)

        self.setCentralWidget(central)

        self.import_tab.request_import.connect(self._start_import)

    # ---- drag & drop ----
    def dragEnterEvent(self, e: QDragEnterEvent) -> None:
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent) -> None:
        for u in e.mimeData().urls():
            if u.isLocalFile():
                self._start_import(u.toLocalFile(), False)

    # ---- worker ----
    def _start_import(self, source: str, is_url: bool) -> None:
        worker = ImportWorker(
            source=source,
            is_url=is_url,
            work_dir=settings.work_folder(),
            out_dir=settings.output_folder(),
            audio=settings.audio_settings(),
            add_to_itunes=settings.add_to_itunes(),
        )
        worker.log.connect(self.log_tab.append)
        worker.progress.connect(self.import_tab.set_progress)
        worker.finished_ok.connect(self.log_tab.append)
        worker.failed.connect(lambda m: self.log_tab.append(f"❌ {m}"))
        worker.finished.connect(lambda w=worker: self._workers.remove(w))
        self._workers.append(worker)
        worker.start()
