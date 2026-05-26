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

from .. import apple_music_helper, converter, downloader, settings
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
    """Pipeline: (download?) → ffmpeg processing → file output."""

    log = pyqtSignal(str)
    progress = pyqtSignal(int)              # 0..100
    finished_ok = pyqtSignal(str, str)      # message, output_path
    failed = pyqtSignal(str)

    def __init__(
        self,
        source: str,
        is_url: bool,
        work_dir: str,
        out_dir: str,
        audio: AudioSettings,
    ) -> None:
        super().__init__()
        self.source = source
        self.is_url = is_url
        self.work_dir = work_dir
        self.out_dir = out_dir
        self.audio = audio

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

            self.log.emit(f"📁 出力完了: {path}")
            self.finished_ok.emit(f"✓ 完了: {os.path.basename(path)}", path)
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

        # Post-processing hint banner — appears after a successful import
        self.hint_card = QFrame()
        self.hint_card.setObjectName("card")
        hint_l = QVBoxLayout(self.hint_card)
        hint_l.setContentsMargins(20, 16, 20, 16)
        hint_l.setSpacing(8)
        self.hint_title = QLabel("🎵 Apple Music にドラッグして取り込み")
        self.hint_title.setObjectName("subheading")
        self.hint_body = QLabel(
            "ファイルがエクスプローラで選択された状態で開き、Apple Music も起動しました。\n"
            "ハイライトされたファイルを Apple Music のウィンドウにドラッグすると、"
            "あなたのライブラリに追加されます。"
        )
        self.hint_body.setObjectName("hint")
        self.hint_body.setWordWrap(True)
        hint_btns = QHBoxLayout()
        self.reveal_btn = QPushButton("📂 もう一度エクスプローラで開く")
        self.reveal_btn.setObjectName("secondary")
        self.launch_btn = QPushButton("🎵 Apple Music を起動")
        self.launch_btn.setObjectName("secondary")
        hint_btns.addWidget(self.reveal_btn)
        hint_btns.addWidget(self.launch_btn)
        hint_btns.addStretch(1)
        hint_l.addWidget(self.hint_title)
        hint_l.addWidget(self.hint_body)
        hint_l.addLayout(hint_btns)
        self.hint_card.setVisible(False)
        layout.addWidget(self.hint_card)

        self._last_output_path: str | None = None
        self.reveal_btn.clicked.connect(self._reveal_again)
        self.launch_btn.clicked.connect(lambda: apple_music_helper.launch_apple_music())

        layout.addStretch(1)

    def show_post_import_hint(self, output_path: str) -> None:
        self._last_output_path = output_path
        self.hint_card.setVisible(True)

    def _reveal_again(self) -> None:
        if self._last_output_path:
            apple_music_helper.reveal_in_explorer(self._last_output_path)

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
        self.format_combo.addItem("AAC (.m4a) — Apple Music 標準", "m4a")
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
                              "ここから Apple Music にドラッグして取り込みます。"))
        layout.addWidget(out_card)

        am_card, am_l = _card()
        am_l.addWidget(_subheading("🎵 Apple Music 連携"))
        am_l.addWidget(_hint(
            "Apple Music for Windows には外部から自動追加する公式APIがありません。"
            "代わりに、処理完了後にエクスプローラでファイルを選択表示 + Apple Music を起動して、"
            "ドラッグするだけの状態でお膳立てします。"
        ))
        self.auto_reveal_cb = QCheckBox("処理完了後にエクスプローラでファイルを選択表示")
        self.auto_reveal_cb.setChecked(settings.auto_reveal_in_explorer())
        self.auto_reveal_cb.toggled.connect(settings.set_auto_reveal_in_explorer)
        am_l.addWidget(self.auto_reveal_cb)

        self.auto_launch_cb = QCheckBox("処理完了後に Apple Music を自動起動")
        self.auto_launch_cb.setChecked(settings.auto_launch_apple_music())
        self.auto_launch_cb.toggled.connect(settings.set_auto_launch_apple_music)
        am_l.addWidget(self.auto_launch_cb)
        layout.addWidget(am_card)

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
        self.setWindowTitle("Apple Music Library Helper")
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
        )
        worker.log.connect(self.log_tab.append)
        worker.progress.connect(self.import_tab.set_progress)
        worker.finished_ok.connect(self._on_import_done)
        worker.failed.connect(lambda m: self.log_tab.append(f"❌ {m}"))
        worker.finished.connect(lambda w=worker: self._workers.remove(w))
        self._workers.append(worker)
        worker.start()

    def _on_import_done(self, message: str, output_path: str) -> None:
        self.log_tab.append(message)
        if not output_path:
            return
        if settings.auto_reveal_in_explorer():
            apple_music_helper.reveal_in_explorer(output_path)
        if settings.auto_launch_apple_music():
            apple_music_helper.launch_apple_music()
        self.import_tab.show_post_import_hint(output_path)
