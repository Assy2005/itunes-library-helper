"""Apple Music Library Helper — main application window (v2 rebuild).

Layout principle: stay on Qt's well-trodden path.
  * Each tab content is wrapped in a QScrollArea so undersized
    windows can never break the layout.
  * Sections within a tab use QGroupBox (not custom QFrame cards) so
    that Qt fully understands the geometry and pixel-perfect padding
    isn't tied to fragile QSS rules.
  * Form rows use QFormLayout. Qt handles label alignment so we can't
    misalign things by drifting label widths.
"""
from __future__ import annotations

import os
import re
import sys
import time

from PyQt6.QtCore import QSize, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent, QIcon
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .. import (
    apple_music_helper, artwork, converter, downloader, ffmpeg_helper,
    metadata, settings, win_chrome, win_notify,
)
from ..audio_presets import PRESETS, AudioSettings
from .eq_visualizer import EQVisualizer
from .ffmpeg_dialog import FFmpegInstallDialog
from .header_bar import HeaderBar
from .import_card import ImportItemCard
from .sidebar import Sidebar
from .toast import ToastManager


# --------------------------------------------------------------------------- #
# Small helpers                                                               #
# --------------------------------------------------------------------------- #

def _hint(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("hint")
    lbl.setWordWrap(True)
    return lbl


def _scrollable(child: QWidget) -> QScrollArea:
    """Wrap a content widget in a vertical-only scroll area."""
    area = QScrollArea()
    area.setWidget(child)
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    return area


# --------------------------------------------------------------------------- #
# Worker                                                                      #
# --------------------------------------------------------------------------- #

class ImportWorker(QThread):
    log = pyqtSignal(str)
    status = pyqtSignal(str)
    progress = pyqtSignal(int)
    finished_ok = pyqtSignal(str, str)
    failed = pyqtSignal(str)

    def __init__(self, source: str, is_url: bool, work_dir: str,
                 out_dir: str, audio: AudioSettings) -> None:
        super().__init__()
        self.source = source
        self.is_url = is_url
        self.work_dir = work_dir
        self.out_dir = out_dir
        self.audio = audio

    def _on_ytdlp_progress(self, d: dict) -> None:
        s = d.get("status")
        if s == "downloading":
            dl = d.get("downloaded_bytes") or 0
            tot = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            speed = d.get("speed") or 0
            eta = d.get("eta") or 0
            if tot > 0:
                pct = int(dl * 100 / tot)
                self.progress.emit(5 + int(pct * 0.40))
                parts = [f"⬇️ ダウンロード中 {pct}%"]
            else:
                parts = [f"⬇️ ダウンロード中 {dl / (1024 * 1024):.1f} MB"]
            if speed:
                parts.append(f"{speed / (1024 * 1024):.1f} MB/s")
            if eta:
                parts.append(f"残り {int(eta)} 秒")
            self.status.emit("  ・  ".join(parts))
        elif s == "finished":
            self.progress.emit(45)
            self.status.emit("✓ ダウンロード完了、後処理中…")
            self.log.emit("[ダウンロード完了] 後処理 (音声抽出) に入ります")
        elif s == "error":
            self.log.emit("[ダウンロードエラー] yt-dlp が失敗しました")

    def run(self) -> None:
        try:
            self.progress.emit(5)
            dl_title: str | None = None
            dl_artist: str | None = None
            if self.is_url:
                self.status.emit("⬇️ ダウンロード準備中…")
                self.log.emit(f"⬇️ 取り込み開始: {self.source}")
                result = downloader.download(
                    self.source, self.work_dir,
                    log_cb=lambda m: self.log.emit(m),
                    progress_cb=self._on_ytdlp_progress,
                )
                path = result.path
                dl_title = result.title
                dl_artist = result.artist
                self.log.emit(f"⬇️ 保存先: {path}")
            else:
                path = self.source
                self.log.emit(f"📁 ローカルファイル: {path}")

            self.progress.emit(50)
            preset = settings.preset_name()
            self.status.emit(
                f"🎚 音質処理 ({preset} ・ {self.audio.bitrate_kbps}kbps)")
            self.log.emit(
                f"🎚 ffmpeg 開始 (preset={preset}, "
                f"{self.audio.bitrate_kbps}kbps {self.audio.output_format}"
                + (f", bass+{self.audio.bass_gain_db}dB"
                   if self.audio.bass_gain_db else "")
                + (f", treble+{self.audio.treble_gain_db}dB"
                   if self.audio.treble_gain_db else "")
                + (f", denoise={self.audio.denoise_strength}"
                   if self.audio.denoise_strength else "")
                + (", loudnorm" if self.audio.loudness_normalize else "")
                + (", dynaudnorm" if self.audio.dynaudnorm else "")
                + ")"
            )
            path = converter.process(path, self.out_dir, self.audio)
            self.log.emit(f"🎚 ffmpeg 完了 → {path}")

            # ---- Metadata enrichment (artwork + tags) ---- #
            if settings.auto_fetch_artwork():
                self.status.emit("🎨 アートワークを検索中…")
                query = " ".join(filter(None, (dl_artist, dl_title))) \
                    or dl_title or os.path.splitext(os.path.basename(path))[0]
                self.log.emit(f"🎨 iTunes Search: \"{query}\"")
                try:
                    found = artwork.best_match(query)
                    if found:
                        hit, img = found
                        meta = metadata.TrackMetadata(
                            title=hit.title or dl_title,
                            artist=hit.artist or dl_artist,
                            album=hit.album or None,
                            artwork_bytes=img,
                        )
                        metadata.apply(path, meta)
                        self.log.emit(
                            f"🎨 アートワーク埋め込み: "
                            f"{hit.artist} — {hit.album}")
                    else:
                        self.log.emit("🎨 一致するアートワークが見つかりませんでした")
                except Exception as e:
                    self.log.emit(f"🎨 アートワーク取得に失敗: {e}")

            self.progress.emit(95)
            self.status.emit("✓ 完了")
            self.log.emit(f"📁 出力完了: {path}")
            self.finished_ok.emit(os.path.basename(path), path)
            self.progress.emit(100)
        except Exception as e:
            self.failed.emit(f"{type(e).__name__}: {e}")


# --------------------------------------------------------------------------- #
# Import queue (used inside ImportTab)                                        #
# --------------------------------------------------------------------------- #

class ImportQueue(QWidget):
    def __init__(self) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        self._empty = QLabel(
            "📭  まだ取り込みがありません\n\n"
            "上のURL欄に貼り付けるか、\nウィンドウのどこにでも音楽ファイルをドロップしてください。"
        )
        self._empty.setObjectName("empty_state")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(self._empty)

        self._cards_layout = QVBoxLayout()
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(8)
        outer.addLayout(self._cards_layout)
        outer.addStretch(1)

        self._cards: list[ImportItemCard] = []

    def add(self, card: ImportItemCard) -> None:
        self._cards.append(card)
        card.dismissed.connect(self.remove)
        self._cards_layout.insertWidget(0, card)
        self._empty.setVisible(False)

    def remove(self, card: ImportItemCard) -> None:
        if card in self._cards:
            self._cards.remove(card)
            self._cards_layout.removeWidget(card)
            card.deleteLater()
        if not self._cards:
            self._empty.setVisible(True)


# --------------------------------------------------------------------------- #
# Tabs                                                                        #
# --------------------------------------------------------------------------- #

class ImportTab(QWidget):
    request_import = pyqtSignal(str, bool)

    _URL_SPLIT_RE = re.compile(r"[\s,;]+")

    def __init__(self) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 18, 28, 18)
        root.setSpacing(14)

        root.addWidget(_hint(
            "URL（YouTube などの動画 / .mp3 などの直リンク）または"
            "ローカルの音楽ファイルから取り込めます。"
            "ウィンドウのどこにでもドロップ可能です。"
        ))

        url_box = QGroupBox("🌐  URL から追加")
        url_l = QVBoxLayout(url_box)
        url_l.setContentsMargins(16, 18, 16, 14)
        url_l.setSpacing(8)
        url_l.addWidget(_hint(
            "1行に1URL、または改行・カンマ・スペース区切りで複数URLを"
            "一度に貼り付けられます。"
        ))
        row = QHBoxLayout()
        row.setSpacing(8)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "https://www.youtube.com/watch?v=…  または複数URLをカンマ区切りで"
        )
        self.url_input.returnPressed.connect(self._submit_url)
        url_btn = QPushButton("追加")
        url_btn.clicked.connect(self._submit_url)
        row.addWidget(self.url_input, 1)
        row.addWidget(url_btn)
        url_l.addLayout(row)
        pick_btn = QPushButton("📁  ファイルを選択…")
        pick_btn.setObjectName("secondary")
        pick_btn.clicked.connect(self._pick_files)
        url_l.addWidget(pick_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        root.addWidget(url_box)

        queue_box = QGroupBox("📋  取り込みキュー")
        queue_l = QVBoxLayout(queue_box)
        queue_l.setContentsMargins(16, 18, 16, 14)
        queue_l.setSpacing(8)
        self.queue = ImportQueue()
        queue_l.addWidget(self.queue, 1)
        root.addWidget(queue_box, 1)

    def _submit_url(self) -> None:
        raw = self.url_input.text().strip()
        if not raw:
            return
        for u in self._URL_SPLIT_RE.split(raw):
            if u:
                self.request_import.emit(u, True)
        self.url_input.clear()

    def _pick_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "音楽ファイルを選択", "",
            "Audio Files (*.mp3 *.m4a *.aac *.wav *.flac *.ogg *.opus *.aiff);;"
            "All Files (*.*)",
        )
        for p in paths:
            self.request_import.emit(p, False)


PRESET_META: dict[str, tuple[str, str]] = {
    "原音忠実":           ("💎", "320 kbps ・ 処理なし"),
    "ポップ":             ("🎤", "低音 +3 / 高音 +2 ・ 256 kbps"),
    "EDM・重低音":        ("🔊", "低音 +8 ・ ラウドネス"),
    "ボーカル強調":       ("🎙", "高音 +4 ・ デノイズ"),
    "クリア・高解像度":   ("✨", "デノイズ ・ 48 kHz"),
    "カスタム":           ("🎚", "全パラメータ手動調整"),
}


class AudioTab(QWidget):
    preset_changed = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 18, 28, 18)
        root.setSpacing(14)

        root.addWidget(_hint(
            "プリセットを選ぶか、カスタムでスライダー調整できます。"
            "変更内容は次回起動時にも保持されます。"
        ))

        # ---- Preset grid ---- #
        preset_box = QGroupBox("🎛  プリセット")
        pl = QVBoxLayout(preset_box)
        pl.setContentsMargins(16, 18, 16, 14)
        pl.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        self._preset_group = QButtonGroup(self)
        self._preset_group.setExclusive(True)
        self._preset_buttons: dict[str, QToolButton] = {}
        for i, name in enumerate(PRESETS):
            icon, tag = PRESET_META.get(name, ("🎵", ""))
            btn = QToolButton()
            btn.setObjectName("preset_btn")
            btn.setText(f"  {icon}   {name}\n      {tag}")
            btn.setCheckable(True)
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding,
                              QSizePolicy.Policy.Fixed)
            btn.setMinimumHeight(60)
            btn.clicked.connect(lambda _checked, n=name: self._on_preset_changed(n))
            self._preset_group.addButton(btn)
            self._preset_buttons[name] = btn
            grid.addWidget(btn, i // 3, i % 3)
        pl.addLayout(grid)

        self.preset_desc = _hint("")
        pl.addWidget(self.preset_desc)
        root.addWidget(preset_box)

        # ---- EQ visualization ---- #
        eq_box = QGroupBox("📊  EQ プレビュー")
        eqv = QVBoxLayout(eq_box)
        eqv.setContentsMargins(16, 18, 16, 14)
        eqv.setSpacing(8)
        self.eq = EQVisualizer()
        eqv.addWidget(self.eq)
        root.addWidget(eq_box)

        # ---- Custom details (QFormLayout) ---- #
        details_box = QGroupBox("🎚  詳細 (カスタム時のみ編集可)")
        form = QFormLayout(details_box)
        form.setContentsMargins(16, 18, 16, 14)
        form.setSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft
                               | Qt.AlignmentFlag.AlignVCenter)

        self.bitrate_combo = QComboBox()
        for kbps in (128, 192, 256, 320):
            self.bitrate_combo.addItem(f"{kbps} kbps", kbps)
        form.addRow("ビットレート", self.bitrate_combo)

        self.format_combo = QComboBox()
        self.format_combo.addItem("AAC (.m4a) — Apple Music 標準", "m4a")
        self.format_combo.addItem("MP3 (.mp3) — 汎用", "mp3")
        form.addRow("出力フォーマット", self.format_combo)

        self.bass_slider, bass_wrap = self._make_slider(0, 12, "dB")
        self.bass_slider.valueChanged.connect(self._refresh_eq)
        form.addRow("重低音強化", bass_wrap)

        self.treble_slider, treble_wrap = self._make_slider(0, 6, "dB")
        self.treble_slider.valueChanged.connect(self._refresh_eq)
        form.addRow("高音強化", treble_wrap)

        self.denoise_slider, denoise_wrap = self._make_slider(0, 3, "段階")
        form.addRow("ノイズ除去", denoise_wrap)

        self.sample_combo = QComboBox()
        self.sample_combo.addItem("そのまま (passthrough)", 0)
        self.sample_combo.addItem("44.1 kHz", 44100)
        self.sample_combo.addItem("48 kHz", 48000)
        self.sample_combo.addItem("96 kHz (ハイレゾ風)", 96000)
        form.addRow("サンプリングレート", self.sample_combo)

        self.loudnorm_cb = QCheckBox("ラウドネス正規化 (-16 LUFS, 放送基準)")
        form.addRow("", self.loudnorm_cb)
        self.dynaudnorm_cb = QCheckBox("ダイナミクス補正 (小さい音を聴きやすく)")
        form.addRow("", self.dynaudnorm_cb)

        save_row = QHBoxLayout()
        save_row.addStretch(1)
        save_btn = QPushButton("カスタム設定を保存")
        save_btn.clicked.connect(self._save_custom)
        save_row.addWidget(save_btn)
        form.addRow("", save_row)

        root.addWidget(details_box)
        root.addStretch(1)

        self._load_into_controls(settings.audio_settings())
        # Sync the button group + description for the persisted preset.
        self._on_preset_changed(settings.preset_name(), persist=False)

    def _make_slider(self, lo: int, hi: int, suffix: str) -> tuple[QSlider, QWidget]:
        s = QSlider(Qt.Orientation.Horizontal)
        s.setRange(lo, hi)
        lbl = QLabel(f"0 {suffix}")
        lbl.setMinimumWidth(64)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        s.valueChanged.connect(lambda v, l=lbl, sx=suffix: l.setText(f"{v} {sx}"))
        wrap = QWidget()
        h = QHBoxLayout(wrap)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(s, 1)
        h.addWidget(lbl)
        return s, wrap

    def _on_preset_changed(self, name: str, *, persist: bool = True) -> None:
        if name not in PRESETS:
            return
        if persist:
            settings.set_preset_name(name)
        btn = self._preset_buttons.get(name)
        if btn and not btn.isChecked():
            btn.setChecked(True)
        a = settings.audio_settings()
        self._load_into_controls(a)
        is_custom = name == "カスタム"
        for w in (self.bitrate_combo, self.format_combo, self.bass_slider,
                  self.treble_slider, self.denoise_slider, self.sample_combo,
                  self.loudnorm_cb, self.dynaudnorm_cb):
            w.setEnabled(is_custom)
        descriptions = {
            "原音忠実": "320kbps・処理なし。原音をそのまま高品質で保存。",
            "ポップ": "256kbps・軽い低音&高音ブースト+ダイナミクス補正。",
            "EDM・重低音": "320kbps・重低音 +8dB、ラウドネス正規化。",
            "ボーカル強調": "256kbps・高音 +4dB、ノイズ除去、ラウドネス正規化。",
            "クリア・高解像度": "320kbps・軽いノイズ除去 + 48kHz アップサンプリング。",
            "カスタム": "下のスライダーで全パラメータを個別調整できます。",
        }
        self.preset_desc.setText(descriptions.get(name, ""))
        if persist:
            self.preset_changed.emit(name)

    def _load_into_controls(self, a: AudioSettings) -> None:
        self.bitrate_combo.setCurrentIndex(
            max(0, self.bitrate_combo.findData(a.bitrate_kbps)))
        self.format_combo.setCurrentIndex(
            max(0, self.format_combo.findData(a.output_format)))
        self.bass_slider.setValue(a.bass_gain_db)
        self.treble_slider.setValue(a.treble_gain_db)
        self.denoise_slider.setValue(a.denoise_strength)
        self.sample_combo.setCurrentIndex(
            max(0, self.sample_combo.findData(a.sample_rate)))
        self.loudnorm_cb.setChecked(a.loudness_normalize)
        self.dynaudnorm_cb.setChecked(a.dynaudnorm)
        self._refresh_eq()

    def _refresh_eq(self) -> None:
        self.eq.set_values(self.bass_slider.value(), self.treble_slider.value())

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


class SettingsTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 18, 28, 18)
        root.setSpacing(14)

        # Output folder
        folder_box = QGroupBox("📁  出力フォルダ")
        folder_l = QVBoxLayout(folder_box)
        folder_l.setContentsMargins(16, 18, 16, 14)
        folder_l.setSpacing(8)
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
        folder_l.addLayout(row)
        folder_l.addWidget(_hint(
            "音質処理後のファイルがここに保存されます。"
            "ここから Apple Music にドラッグして取り込みます。"
        ))
        root.addWidget(folder_box)

        # Apple Music integration
        am_box = QGroupBox("🎵  Apple Music 連携")
        am_l = QVBoxLayout(am_box)
        am_l.setContentsMargins(16, 18, 16, 14)
        am_l.setSpacing(8)
        am_l.addWidget(_hint(
            "Apple Music for Windows には外部から自動追加する公式APIがありません。"
            "代わりに処理完了後にエクスプローラでファイルを選択表示 + "
            "Apple Music を起動して、ドラッグするだけの状態でお膳立てします。"
        ))
        self.auto_reveal_cb = QCheckBox("処理完了後にエクスプローラでファイルを選択表示")
        self.auto_reveal_cb.setChecked(settings.auto_reveal_in_explorer())
        self.auto_reveal_cb.toggled.connect(settings.set_auto_reveal_in_explorer)
        am_l.addWidget(self.auto_reveal_cb)
        self.auto_launch_cb = QCheckBox("処理完了後に Apple Music を自動起動")
        self.auto_launch_cb.setChecked(settings.auto_launch_apple_music())
        self.auto_launch_cb.toggled.connect(settings.set_auto_launch_apple_music)
        am_l.addWidget(self.auto_launch_cb)
        root.addWidget(am_box)

        # Metadata enrichment
        md_box = QGroupBox("🎨  メタデータ")
        md_l = QVBoxLayout(md_box)
        md_l.setContentsMargins(16, 18, 16, 14)
        md_l.setSpacing(8)
        md_l.addWidget(_hint(
            "取り込み完了時に iTunes Search API でアートワークを検索し、"
            "ファイルに自動で埋め込みます。"
            "検索結果が違う場合はカードの ✏️ ボタンから手動で編集できます。"
        ))
        self.auto_artwork_cb = QCheckBox("取り込み完了時にアートワークを自動取得")
        self.auto_artwork_cb.setChecked(settings.auto_fetch_artwork())
        self.auto_artwork_cb.toggled.connect(settings.set_auto_fetch_artwork)
        md_l.addWidget(self.auto_artwork_cb)
        root.addWidget(md_box)

        # Notifications
        nf_box = QGroupBox("🔔  通知")
        nf_l = QVBoxLayout(nf_box)
        nf_l.setContentsMargins(16, 18, 16, 14)
        nf_l.setSpacing(8)
        self.flash_cb = QCheckBox("処理完了時にタスクバーを点滅 (非アクティブ時のみ)")
        self.flash_cb.setChecked(settings.taskbar_flash_on_done())
        self.flash_cb.toggled.connect(settings.set_taskbar_flash_on_done)
        nf_l.addWidget(self.flash_cb)
        self.toast_cb = QCheckBox("画面右下にトースト通知を表示")
        self.toast_cb.setChecked(settings.show_toast_on_done())
        self.toast_cb.toggled.connect(settings.set_show_toast_on_done)
        nf_l.addWidget(self.toast_cb)
        root.addWidget(nf_box)

        # UI state
        ui_box = QGroupBox("🪟  UI 状態")
        ui_l = QVBoxLayout(ui_box)
        ui_l.setContentsMargins(16, 18, 16, 14)
        ui_l.setSpacing(8)
        ui_l.addWidget(_hint(
            "ウィンドウサイズ・位置・最後に開いていたタブの記憶をクリアします。"
            "画面のレイアウトが崩れている場合に試してみてください。"
            "音質プリセットや出力フォルダなどの設定は維持されます。"
        ))
        reset_btn = QPushButton("🔄 UI 状態をリセット")
        reset_btn.setObjectName("secondary")
        reset_btn.clicked.connect(self._reset_ui_state)
        ui_l.addWidget(reset_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        root.addWidget(ui_box)

        # ffmpeg
        ff_box = QGroupBox("🎬  ffmpeg")
        ff_l = QVBoxLayout(ff_box)
        ff_l.setContentsMargins(16, 18, 16, 14)
        ff_l.setSpacing(8)
        ff_ok = ffmpeg_helper.is_installed()
        ff_status = QLabel(
            "● ffmpeg / ffprobe 検出済み" if ff_ok
            else "● ffmpeg または ffprobe が見つかりません — 音質処理が使えません"
        )
        ff_status.setObjectName("status_ok" if ff_ok else "status_warn")
        ff_l.addWidget(ff_status)
        if not ff_ok:
            ff_l.addWidget(_hint(
                "下のボタンからワンクリックでインストールできます (winget使用)。"
            ))
            install_btn = QPushButton("⚡ ffmpeg を自動インストール…")
            install_btn.clicked.connect(self._open_ffmpeg_dialog)
            ff_l.addWidget(install_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        root.addWidget(ff_box)

        root.addStretch(1)

    def _pick_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "出力フォルダ", self.folder_edit.text())
        if path:
            self.folder_edit.setText(path)
            settings.set_output_folder(path)

    def _open_ffmpeg_dialog(self) -> None:
        FFmpegInstallDialog(self).exec()

    def _reset_ui_state(self) -> None:
        from PyQt6.QtCore import QSettings
        s = QSettings("itunes-library-helper", "itunes-library-helper")
        for key in ("ui/window_geometry", "ui/last_tab"):
            s.remove(key)
        QMessageBox.information(
            self, "UI 状態をリセットしました",
            "ウィンドウ状態をクリアしました。次回起動時にデフォルトサイズで開きます。",
        )


class LogTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 18, 28, 18)
        root.setSpacing(10)

        header = QHBoxLayout()
        header.addStretch(1)
        clear_btn = QPushButton("🗑 クリア")
        clear_btn.setObjectName("secondary")
        clear_btn.clicked.connect(lambda: self.text.clear())
        header.addWidget(clear_btn)
        root.addLayout(header)

        root.addWidget(_hint(
            "ダウンロードと音質処理の詳細出力をリアルタイム表示します。"
            "yt-dlp / ffmpeg のメッセージもここに流れます。"
        ))

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setPlaceholderText("まだログはありません。")
        self.text.setStyleSheet(
            "QPlainTextEdit {"
            "  font-family: Consolas, 'SF Mono', Menlo, monospace;"
            "  font-size: 12px;"
            "  padding: 10px;"
            "}"
        )
        self.text.setMaximumBlockCount(5000)
        root.addWidget(self.text, 1)

    def append(self, msg: str) -> None:
        self.text.appendPlainText(f"[{time.strftime('%H:%M:%S')}]  {msg}")
        sb = self.text.verticalScrollBar()
        sb.setValue(sb.maximum())


# --------------------------------------------------------------------------- #
# Drop overlay                                                                #
# --------------------------------------------------------------------------- #

class DropOverlay(QFrame):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("drop_overlay")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        v = QVBoxLayout(self)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("🎵  ここにドロップ")
        title.setObjectName("drop_overlay_label")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel("音楽ファイルを取り込みキューに追加します")
        sub.setObjectName("drop_overlay_sub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(title)
        v.addWidget(sub)
        self.hide()


# --------------------------------------------------------------------------- #
# Main window                                                                 #
# --------------------------------------------------------------------------- #

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Apple Music Library Helper")
        self.resize(1080, 740)
        self.setMinimumSize(QSize(900, 560))
        self.setAcceptDrops(True)

        # Bundled resources path (PyInstaller-aware).
        base = getattr(sys, "_MEIPASS", os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        resources_dir = os.path.join(base, "resources")
        icon_path = os.path.join(resources_dir, "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        from .style import QSS, checkbox_check_extra_qss
        self.setStyleSheet(QSS + checkbox_check_extra_qss(resources_dir))

        # Restore prior window geometry, with a defensive minimum bounce.
        geom = settings.window_geometry()
        if geom:
            self.restoreGeometry(geom)
            if self.width() < 900 or self.height() < 560:
                self.resize(1080, 740)

        self._workers: list[ImportWorker] = []

        # Central widget: sidebar | (header + stacked content) #
        central = QWidget()
        central.setObjectName("central")
        h = QHBoxLayout(central)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        self.sidebar = Sidebar()
        h.addWidget(self.sidebar)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        self.header = HeaderBar()
        rl.addWidget(self.header)

        self.stack = QStackedWidget()
        self.import_tab = ImportTab()
        self.audio_tab = AudioTab()
        self.settings_tab = SettingsTab()
        self.log_tab = LogTab()
        for w in (self.import_tab, self.audio_tab,
                  self.settings_tab, self.log_tab):
            self.stack.addWidget(_scrollable(w))
        rl.addWidget(self.stack, 1)
        h.addWidget(right, 1)

        self.setCentralWidget(central)

        # Drop overlay + toast manager.
        self.drop_overlay = DropOverlay(self)
        self.drop_overlay.hide()
        self.toasts = ToastManager(self)

        # Wire signals.
        self.sidebar.nav_clicked.connect(self.stack.setCurrentIndex)
        self.sidebar.nav_clicked.connect(self.header.set_page)
        self.sidebar.new_import_clicked.connect(self._focus_import)
        self.sidebar.open_output_clicked.connect(
            lambda: apple_music_helper.open_folder(
                settings.output_folder(), log_cb=self.log_tab.append))
        self.import_tab.request_import.connect(self._start_import)
        self.audio_tab.preset_changed.connect(self.sidebar.set_current_preset)
        self.audio_tab.preset_changed.connect(self.header.set_preset)
        self.stack.currentChanged.connect(settings.set_last_tab_index)
        self.stack.currentChanged.connect(self.header.set_page)

        # Initial header chip values + refresh tick for queue count.
        self.header.set_ffmpeg(ffmpeg_helper.is_installed())
        self.header.set_preset(settings.preset_name())
        self.header.set_queue(0)
        self._header_timer = QTimer(self)
        self._header_timer.timeout.connect(self._refresh_header)
        self._header_timer.start(1000)

        # Restore last visited tab.
        last = settings.last_tab_index()
        if 0 <= last < self.stack.count():
            self.stack.setCurrentIndex(last)
            self.sidebar.select(last)
            self.header.set_page(last)

        # Windows 11 native chrome (Mica + dark titlebar).
        QTimer.singleShot(0, self._apply_native_chrome)

        # First-launch ffmpeg check.
        QTimer.singleShot(300, self._check_ffmpeg_on_startup)

    # ----- Lifecycle ---------------------------------------------------- #
    def closeEvent(self, e) -> None:
        settings.set_window_geometry(bytes(self.saveGeometry()))
        super().closeEvent(e)

    # ----- Drag and drop ------------------------------------------------ #
    def dragEnterEvent(self, e: QDragEnterEvent) -> None:
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self._show_drop_overlay()

    def dragLeaveEvent(self, e: QDragLeaveEvent) -> None:
        self.drop_overlay.hide()

    def dropEvent(self, e: QDropEvent) -> None:
        self.drop_overlay.hide()
        for u in e.mimeData().urls():
            if u.isLocalFile():
                self._start_import(u.toLocalFile(), False)
        self.sidebar.select(0)
        self.stack.setCurrentIndex(0)

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        self._reposition_overlay()
        if hasattr(self, "toasts"):
            self.toasts._relayout()

    def _show_drop_overlay(self) -> None:
        self._reposition_overlay()
        self.drop_overlay.show()
        self.drop_overlay.raise_()

    def _reposition_overlay(self) -> None:
        margin = 16
        header_h = self.header.height() if hasattr(self, "header") else 0
        x = self.sidebar.width() + margin
        y = header_h + margin
        w = self.width() - self.sidebar.width() - margin * 2
        h = self.height() - header_h - margin * 2
        self.drop_overlay.setGeometry(x, y, max(0, w), max(0, h))

    # ----- ffmpeg ------------------------------------------------------- #
    def _check_ffmpeg_on_startup(self) -> None:
        if not ffmpeg_helper.is_installed():
            self._show_ffmpeg_dialog(reason="アプリ起動時の検査で見つかりませんでした")

    def _show_ffmpeg_dialog(self, *, reason: str | None = None) -> None:
        if getattr(self, "_ffmpeg_dialog_open", False):
            return
        self._ffmpeg_dialog_open = True
        FFmpegInstallDialog(self, reason=reason).exec()
        self._ffmpeg_dialog_open = False

    # ----- Imports ------------------------------------------------------ #
    def _start_import(self, source: str, is_url: bool,
                      card: ImportItemCard | None = None) -> None:
        if not ffmpeg_helper.is_installed():
            self._show_ffmpeg_dialog(
                reason="取り込み開始時のチェックで見つかりませんでした")
            return

        if card is None:
            card = ImportItemCard(source=source, is_url=is_url)
            card.retry_requested.connect(self._retry_card)
            self.import_tab.queue.add(card)

        worker = ImportWorker(
            source=source, is_url=is_url,
            work_dir=settings.work_folder(),
            out_dir=settings.output_folder(),
            audio=settings.audio_settings(),
        )
        worker.log.connect(self.log_tab.append)
        worker.status.connect(card.set_status)
        worker.progress.connect(card.set_progress)
        worker.finished_ok.connect(
            lambda summary, path: self._on_import_done(card, summary, path))
        worker.failed.connect(
            lambda m: self._on_import_failed(card, m))
        worker.finished.connect(lambda w=worker: self._workers.remove(w))
        self._workers.append(worker)
        worker.start()

    def _retry_card(self, card: ImportItemCard) -> None:
        card.reset_for_retry()
        self.log_tab.append(f"↻ リトライ: {card.source}")
        self._start_import(card.source, card.is_url, card=card)

    def _on_import_failed(self, card: ImportItemCard, message: str) -> None:
        card.mark_error(message)
        self.log_tab.append(f"❌ {message}")
        if settings.show_toast_on_done():
            self.toasts.show("⚠️", "取り込み失敗",
                             message[:120] + ("…" if len(message) > 120 else ""))
        if ffmpeg_helper.looks_like_missing_ffmpeg(message):
            self._show_ffmpeg_dialog(reason=message)

    def _on_import_done(self, card: ImportItemCard,
                        summary: str, output_path: str) -> None:
        card.mark_success(output_path, summary)
        self.log_tab.append(f"✓ 完了: {summary}")
        if settings.show_toast_on_done():
            self.toasts.show("✓", "取り込み完了", summary)
        if settings.taskbar_flash_on_done() and not self.isActiveWindow():
            win_notify.flash_taskbar(int(self.winId()))
        if not output_path:
            return
        if settings.auto_reveal_in_explorer():
            apple_music_helper.reveal_in_explorer(
                output_path, log_cb=self.log_tab.append)
        if settings.auto_launch_apple_music():
            apple_music_helper.launch_apple_music(log_cb=self.log_tab.append)

    # ----- Chrome / header ---------------------------------------------- #
    def _refresh_header(self) -> None:
        self.header.set_ffmpeg(ffmpeg_helper.is_installed())
        self.header.set_preset(settings.preset_name())
        self.header.set_queue(len(self._workers))

    def _focus_import(self) -> None:
        self.stack.setCurrentIndex(0)
        self.sidebar.select(0)
        self.header.set_page(0)
        self.import_tab.url_input.setFocus()

    def _apply_native_chrome(self) -> None:
        hwnd = int(self.winId())
        win_chrome.enable_dark_titlebar(hwnd)
        win_chrome.enable_mica(hwnd, acrylic=False)
