"""Apple Music Library Helper — main application window.

Layout:
    ┌──────────────────────────────────────────┐
    │ Sidebar │       Content (QStackedWidget) │
    │         ├────────────────────────────────┤
    │         │       Status bar               │
    └──────────────────────────────────────────┘

A full-window drop overlay covers the central area whenever a drag of
file URLs enters the main window, regardless of which tab is active.
"""
from __future__ import annotations

import os
import re
import shutil
import sys
import time

from PyQt6.QtCore import QSize, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent, QIcon
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .. import (
    apple_music_helper, converter, downloader, ffmpeg_helper, settings,
    win_chrome, win_notify,
)
from ..audio_presets import PRESETS, AudioSettings
from .eq_visualizer import EQVisualizer
from .ffmpeg_dialog import FFmpegInstallDialog
from .header_bar import HeaderBar
from .import_card import ImportItemCard
from .preset_card import PresetCard
from .sidebar import Sidebar
from .toast import ToastManager


# --------------------------------------------------------------------------- #
# Small UI helpers                                                            #
# --------------------------------------------------------------------------- #

def _card(layout_cls=QVBoxLayout) -> tuple[QFrame, QVBoxLayout | QHBoxLayout]:
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
    """Pipeline: (download?) → ffmpeg processing → file output.

    Emits short `status` strings for the per-job card and verbose `log`
    strings for the global log tab.
    """

    log = pyqtSignal(str)
    status = pyqtSignal(str)
    progress = pyqtSignal(int)
    finished_ok = pyqtSignal(str, str)      # summary, output_path
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

    def _on_ytdlp_progress(self, d: dict) -> None:
        """Translate yt-dlp's progress dict into card-friendly updates."""
        status = d.get("status")
        if status == "downloading":
            downloaded = d.get("downloaded_bytes") or 0
            total = (d.get("total_bytes")
                     or d.get("total_bytes_estimate")
                     or 0)
            speed = d.get("speed") or 0       # bytes/sec
            eta = d.get("eta") or 0           # seconds

            if total > 0:
                pct = int(downloaded * 100 / total)
                # Map 0–100% of download to 5–45% of the overall pipeline.
                self.progress.emit(5 + int(pct * 0.40))
                parts = [f"⬇️  ダウンロード中  {pct}%"]
            else:
                mb = downloaded / (1024 * 1024)
                parts = [f"⬇️  ダウンロード中  {mb:.1f} MB"]

            if speed:
                parts.append(f"{speed / (1024 * 1024):.1f} MB/s")
            if eta:
                parts.append(f"残り {int(eta)} 秒")
            self.status.emit("  ・  ".join(parts))

        elif status == "finished":
            self.progress.emit(45)
            self.status.emit("✓  ダウンロード完了、後処理を待機中…")
            self.log.emit("[ダウンロード完了] 後処理 (音声抽出) に入ります")

        elif status == "error":
            self.log.emit("[ダウンロードエラー] yt-dlp が失敗しました")

    def run(self) -> None:
        try:
            self.progress.emit(5)

            if self.is_url:
                self.status.emit("⬇️  ダウンロード準備中…")
                self.log.emit(f"⬇️  取り込み開始: {self.source}")
                result = downloader.download(
                    self.source, self.work_dir,
                    log_cb=lambda m: self.log.emit(m),
                    progress_cb=self._on_ytdlp_progress,
                )
                path = result.path
                self.log.emit(f"⬇️  保存先: {path}")
            else:
                path = self.source
                self.log.emit(f"📁 ローカルファイル: {path}")

            self.progress.emit(50)

            preset = settings.preset_name()
            self.status.emit(
                f"🎚️  音質処理 ({preset} ・ {self.audio.bitrate_kbps}kbps)"
            )
            self.log.emit(
                f"🎚️  ffmpeg 開始 (preset={preset}, "
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
            self.log.emit(f"🎚️  ffmpeg 完了 → {path}")

            self.progress.emit(95)

            self.status.emit("✓ 完了")
            self.log.emit(f"📁 出力完了: {path}")
            self.finished_ok.emit(os.path.basename(path), path)
            self.progress.emit(100)
        except Exception as e:
            self.failed.emit(f"{type(e).__name__}: {e}")


# --------------------------------------------------------------------------- #
# Import queue widget                                                         #
# --------------------------------------------------------------------------- #

class ImportQueue(QWidget):
    """A vertical stack of ImportItemCard widgets with an empty state."""

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
        self._cards_layout.insertWidget(0, card)  # newest at top
        self._empty.setVisible(False)

    def remove(self, card: ImportItemCard) -> None:
        if card in self._cards:
            self._cards.remove(card)
            self._cards_layout.removeWidget(card)
            card.deleteLater()
        if not self._cards:
            self._empty.setVisible(True)

    def active_count(self) -> int:
        """Number of jobs that haven't finished yet (best-effort)."""
        n = 0
        for c in self._cards:
            # Cards that are done style their status as job_status_ok/err.
            if c.findChild(QLabel, "job_status") is not None:
                n += 1
        return n


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
        layout.addWidget(_hint(
            "URL（YouTube などの動画 / .mp3 などの直リンク）または"
            "ローカルの音楽ファイルから取り込めます。"
            "ウィンドウのどこにでもドロップ可能です。"
        ))

        # URL card
        url_card, url_l = _card()
        url_l.addWidget(_subheading("🌐 URL から追加"))
        url_l.addWidget(_hint(
            "1行に1URL、または改行・カンマ・スペース区切りで複数URLを"
            "一度に貼り付けられます。"
        ))
        row = QHBoxLayout()
        row.setSpacing(8)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "https://www.youtube.com/watch?v=…   または複数URLをカンマ区切りで"
        )
        self.url_input.returnPressed.connect(self._submit_url)
        url_btn = QPushButton("追加")
        url_btn.clicked.connect(self._submit_url)
        row.addWidget(self.url_input, 1)
        row.addWidget(url_btn)
        url_l.addLayout(row)

        pick_btn = QPushButton("📁 ファイルを選択…")
        pick_btn.setObjectName("secondary")
        pick_btn.clicked.connect(self._pick_files)
        url_l.addWidget(pick_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(url_card)

        # Queue label + queue
        layout.addWidget(_subheading("📋 取り込みキュー"))
        self.queue = ImportQueue()
        layout.addWidget(self.queue, 1)

    # URLs separated by whitespace, commas, semicolons, or newlines.
    _URL_SPLIT_RE = re.compile(r"[\s,;]+")

    def _submit_url(self) -> None:
        raw = self.url_input.text().strip()
        if not raw:
            return
        urls = [u for u in self._URL_SPLIT_RE.split(raw) if u]
        for u in urls:
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


# --------------------------------------------------------------------------- #
# Audio settings tab                                                          #
# --------------------------------------------------------------------------- #

class AudioTab(QWidget):
    preset_changed = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        layout.addWidget(_heading("音質設定"))
        layout.addWidget(_hint(
            "プリセットを選ぶか、カスタムで細かく調整できます。"
            "変更内容は次回起動時にも保持されます。"
        ))

        preset_card_outer, preset_l = _card()
        preset_l.addWidget(_subheading("🎛️ プリセット"))

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        self._preset_cards: dict[str, PresetCard] = {}
        for i, name in enumerate(PRESETS):
            card = PresetCard(name)
            card.clicked.connect(self._on_preset_changed)
            self._preset_cards[name] = card
            grid.addWidget(card, i // 3, i % 3)
        preset_l.addLayout(grid)

        self.preset_desc = _hint("")
        preset_l.addWidget(self.preset_desc)
        layout.addWidget(preset_card_outer)

        custom_card, custom_l = _card()
        custom_l.addWidget(_subheading("🎚️ 詳細"))
        custom_l.addWidget(_hint(
            "「カスタム」プリセット選択時のみ編集可能。"
            "他プリセット時は現在の値を表示。"
        ))

        # Wrap the EQ visualizer in a fixed-height container. We previously
        # tried setFixedHeight + sizeHint overrides on the widget itself,
        # but the parent QVBoxLayout still allocated zero vertical space
        # in some configurations, causing the form rows below to render
        # on top of the EQ paint. A QFrame container with a hard fixed
        # height is consistently respected.
        eq_box = QFrame()
        eq_box.setFixedHeight(EQVisualizer.HEIGHT)
        eq_box_l = QVBoxLayout(eq_box)
        eq_box_l.setContentsMargins(0, 0, 0, 0)
        eq_box_l.setSpacing(0)
        self.eq = EQVisualizer()
        eq_box_l.addWidget(self.eq)
        custom_l.addWidget(eq_box)

        self.bitrate_combo = QComboBox()
        for kbps in (128, 192, 256, 320):
            self.bitrate_combo.addItem(f"{kbps} kbps", kbps)
        self._add_row(custom_l, "ビットレート", self.bitrate_combo)

        self.format_combo = QComboBox()
        self.format_combo.addItem("AAC (.m4a) — Apple Music 標準", "m4a")
        self.format_combo.addItem("MP3 (.mp3) — 汎用", "mp3")
        self._add_row(custom_l, "出力フォーマット", self.format_combo)

        self.bass_slider, self.bass_label = self._make_slider(0, 12, "dB")
        self.bass_slider.valueChanged.connect(self._refresh_eq)
        self._add_row(custom_l, "重低音強化",
                      self._wrap_slider(self.bass_slider, self.bass_label))

        self.treble_slider, self.treble_label = self._make_slider(0, 6, "dB")
        self.treble_slider.valueChanged.connect(self._refresh_eq)
        self._add_row(custom_l, "高音強化",
                      self._wrap_slider(self.treble_slider, self.treble_label))

        self.denoise_slider, self.denoise_label = self._make_slider(0, 3, "段階")
        self._add_row(custom_l, "ノイズ除去",
                      self._wrap_slider(self.denoise_slider, self.denoise_label))

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
        self._on_preset_changed(settings.preset_name())

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
        if name not in PRESETS:
            return
        settings.set_preset_name(name)
        # Reflect selected state on the grid of preset cards.
        for n, c in self._preset_cards.items():
            c.set_selected(n == name)
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
        out_l.addWidget(_hint(
            "音質処理後のファイルがここに保存されます。"
            "ここから Apple Music にドラッグして取り込みます。"
        ))
        layout.addWidget(out_card)

        am_card, am_l = _card()
        am_l.addWidget(_subheading("🎵 Apple Music 連携"))
        am_l.addWidget(_hint(
            "Apple Music for Windows には外部から自動追加する公式APIがありません。"
            "代わりに、処理完了後にエクスプローラでファイルを選択表示 + "
            "Apple Music を起動して、ドラッグするだけの状態でお膳立てします。"
        ))
        self.auto_reveal_cb = QCheckBox(
            "処理完了後にエクスプローラでファイルを選択表示")
        self.auto_reveal_cb.setChecked(settings.auto_reveal_in_explorer())
        self.auto_reveal_cb.toggled.connect(settings.set_auto_reveal_in_explorer)
        am_l.addWidget(self.auto_reveal_cb)

        self.auto_launch_cb = QCheckBox("処理完了後に Apple Music を自動起動")
        self.auto_launch_cb.setChecked(settings.auto_launch_apple_music())
        self.auto_launch_cb.toggled.connect(settings.set_auto_launch_apple_music)
        am_l.addWidget(self.auto_launch_cb)
        layout.addWidget(am_card)

        nf_card, nf_l = _card()
        nf_l.addWidget(_subheading("🔔 通知"))
        self.flash_cb = QCheckBox(
            "処理完了時にタスクバーを点滅 (非アクティブ時のみ)")
        self.flash_cb.setChecked(settings.taskbar_flash_on_done())
        self.flash_cb.toggled.connect(settings.set_taskbar_flash_on_done)
        nf_l.addWidget(self.flash_cb)
        self.toast_cb = QCheckBox("画面右下にトースト通知を表示")
        self.toast_cb.setChecked(settings.show_toast_on_done())
        self.toast_cb.toggled.connect(settings.set_show_toast_on_done)
        nf_l.addWidget(self.toast_cb)
        layout.addWidget(nf_card)

        ui_card, ui_l = _card()
        ui_l.addWidget(_subheading("🪟 UI 状態"))
        ui_l.addWidget(_hint(
            "ウィンドウサイズ・位置・最後に開いていたタブの記憶をクリアします。"
            "画面のレイアウトが崩れている場合は試してみてください。"
            "音質プリセットや出力フォルダなどの設定は維持されます。"
        ))
        reset_btn = QPushButton("🔄 UI 状態をリセット")
        reset_btn.setObjectName("secondary")
        reset_btn.clicked.connect(self._reset_ui_state)
        ui_l.addWidget(reset_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(ui_card)

        ff_card, ff_l = _card()
        ff_l.addWidget(_subheading("🎬 ffmpeg"))
        from .. import ffmpeg_helper as _ff
        ff_ok = _ff.is_installed()
        ff_status = QLabel(
            "● ffmpeg / ffprobe 検出済み" if ff_ok
            else "● ffmpeg または ffprobe が見つかりません — 音質処理が使えません"
        )
        ff_status.setObjectName("status_ok" if ff_ok else "status_warn")
        ff_l.addWidget(ff_status)
        if not ff_ok:
            ff_l.addWidget(_hint(
                "下のボタンからワンクリックでインストールできます (winget使用)。"
                "うまく行かない場合は ダウンロードページ ボタンで手動DL。"
            ))
            install_btn = QPushButton("⚡ ffmpeg を自動インストール…")
            install_btn.clicked.connect(self._open_ffmpeg_dialog)
            ff_l.addWidget(install_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(ff_card)

    def _open_ffmpeg_dialog(self) -> None:
        from .ffmpeg_dialog import FFmpegInstallDialog
        FFmpegInstallDialog(self).exec()

    def _reset_ui_state(self) -> None:
        from PyQt6.QtCore import QSettings
        from PyQt6.QtWidgets import QMessageBox
        s = QSettings("itunes-library-helper", "itunes-library-helper")
        for key in ("ui/window_geometry", "ui/last_tab"):
            s.remove(key)
        QMessageBox.information(
            self,
            "UI 状態をリセットしました",
            "ウィンドウ状態をクリアしました。次回起動時にデフォルトサイズで開きます。",
        )

        layout.addStretch(1)

    def _pick_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "出力フォルダ", self.folder_edit.text())
        if path:
            self.folder_edit.setText(path)
            settings.set_output_folder(path)


# --------------------------------------------------------------------------- #
# Log tab                                                                     #
# --------------------------------------------------------------------------- #

class LogTab(QWidget):
    """Console-style log: monospace, timestamps, auto-scroll, clear button."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.addWidget(_heading("ログ"))
        header.addStretch(1)
        clear_btn = QPushButton("🗑 クリア")
        clear_btn.setObjectName("secondary")
        clear_btn.clicked.connect(lambda: self.text.clear())
        header.addWidget(clear_btn)
        layout.addLayout(header)

        layout.addWidget(_hint(
            "ダウンロードと音質処理の詳細出力をリアルタイム表示します。"
            "yt-dlp / ffmpeg のメッセージもここに流れます。"
        ))

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setPlaceholderText("まだログはありません。")
        self.text.setStyleSheet(
            "QPlainTextEdit {"
            "  background: #1d1d1f;"
            "  color: #f5f5f7;"
            "  font-family: Consolas, 'SF Mono', Menlo, monospace;"
            "  font-size: 12px;"
            "  border: 1px solid #e5e5ea;"
            "  border-radius: 10px;"
            "  padding: 10px;"
            "  selection-background-color: #fc3c44;"
            "  selection-color: white;"
            "}"
        )
        # Cap the in-memory buffer so a runaway log can't OOM the app.
        self.text.setMaximumBlockCount(5000)
        layout.addWidget(self.text, 1)

    def append(self, msg: str) -> None:
        ts = time.strftime("%H:%M:%S")
        self.text.appendPlainText(f"[{ts}]  {msg}")
        sb = self.text.verticalScrollBar()
        sb.setValue(sb.maximum())


# --------------------------------------------------------------------------- #
# Sidebar                                                                     #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# Full-window drop overlay                                                    #
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
        self.resize(1040, 720)
        self.setMinimumSize(QSize(880, 560))
        self.setAcceptDrops(True)

        # Resources base: PyInstaller onefile extracts under sys._MEIPASS;
        # development uses the repo root.
        base = getattr(sys, "_MEIPASS", os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        resources_dir = os.path.join(base, "resources")
        icon_path = os.path.join(resources_dir, "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        from .style import QSS, checkbox_check_extra_qss
        self.setStyleSheet(QSS + checkbox_check_extra_qss(resources_dir))

        # Restore previous window geometry (size, position, maximized state)
        # if we have it stashed from a previous session. Defensive: if the
        # restored size ends up below the minimum (e.g. a previous version
        # saved a broken size), kick it back up to the default. This avoids
        # the layout being squeezed into an impossible shape and laying
        # widgets on top of each other.
        geom = settings.window_geometry()
        if geom:
            self.restoreGeometry(geom)
            if (self.width() < 880 or self.height() < 560):
                self.resize(1040, 720)

        self._workers: list[ImportWorker] = []

        # ----- Central layout: sidebar | (header + stacked content) ----- #
        central = QWidget()
        central.setObjectName("central")
        h = QHBoxLayout(central)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        self.sidebar = Sidebar()
        h.addWidget(self.sidebar)

        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.setSpacing(0)

        self.header = HeaderBar()
        right_l.addWidget(self.header)

        self.stack = QStackedWidget()
        self.import_tab = ImportTab()
        self.audio_tab = AudioTab()
        self.settings_tab = SettingsTab()
        self.log_tab = LogTab()
        for w in (self.import_tab, self.audio_tab,
                  self.settings_tab, self.log_tab):
            self.stack.addWidget(w)
        right_l.addWidget(self.stack, 1)
        h.addWidget(right, 1)

        self.setCentralWidget(central)

        # ----- Drop overlay (sits over the central widget) ----- #
        self.drop_overlay = DropOverlay(self)
        self.drop_overlay.hide()

        # ----- Toast manager for completion / error notifications ----- #
        self.toasts = ToastManager(self)

        # ----- Wire up ----- #
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

        # Initial header chip values + a 1s refresh tick for queue count.
        self.header.set_ffmpeg(ffmpeg_helper.is_installed())
        self.header.set_preset(settings.preset_name())
        self.header.set_queue(0)
        self._header_timer = QTimer(self)
        self._header_timer.timeout.connect(self._refresh_header)
        self._header_timer.start(1000)

        # Restore the tab we left off on (after the stack is set up).
        last = settings.last_tab_index()
        if 0 <= last < self.stack.count():
            self.stack.setCurrentIndex(last)
            self.sidebar.select(last)
            self.header.set_page(last)

        # Windows 11 Mica + dark title bar (no-op elsewhere).
        QTimer.singleShot(0, self._apply_native_chrome)

        # First-launch ffmpeg check: nudge the user to install it before
        # they hit any errors mid-import.
        QTimer.singleShot(300, self._check_ffmpeg_on_startup)

    def closeEvent(self, e) -> None:  # noqa: D401
        # Save geometry so the next session opens at the same size/place.
        settings.set_window_geometry(bytes(self.saveGeometry()))
        super().closeEvent(e)

    # ----- drag & drop (whole-window) ----------------------------------- #
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
        # Keep stacked toasts pinned to the bottom-right corner.
        if hasattr(self, "toasts"):
            self.toasts._relayout()

    def _show_drop_overlay(self) -> None:
        self._reposition_overlay()
        self.drop_overlay.show()
        self.drop_overlay.raise_()

    def _reposition_overlay(self) -> None:
        # Cover the content area (right of the sidebar, below the header).
        margin = 16
        header_h = self.header.height() if hasattr(self, "header") else 0
        x = self.sidebar.width() + margin
        y = header_h + margin
        w = self.width() - self.sidebar.width() - margin * 2
        h = self.height() - header_h - margin * 2
        self.drop_overlay.setGeometry(x, y, max(0, w), max(0, h))

    # ----- ffmpeg helpers ----------------------------------------------- #
    def _check_ffmpeg_on_startup(self) -> None:
        if not ffmpeg_helper.is_installed():
            self._show_ffmpeg_dialog(reason="アプリ起動時の検査で見つかりませんでした")

    def _show_ffmpeg_dialog(self, *, reason: str | None = None) -> None:
        # Avoid stacking multiple copies if errors fire in quick succession.
        if getattr(self, "_ffmpeg_dialog_open", False):
            return
        self._ffmpeg_dialog_open = True
        dlg = FFmpegInstallDialog(self, reason=reason)
        dlg.exec()
        self._ffmpeg_dialog_open = False

    # ----- import orchestration ----------------------------------------- #
    def _start_import(self, source: str, is_url: bool,
                      card: ImportItemCard | None = None) -> None:
        # Pre-flight: if ffmpeg isn't available, don't even start the
        # download — yt-dlp would crash partway through postprocessing.
        if not ffmpeg_helper.is_installed():
            self._show_ffmpeg_dialog(
                reason="取り込み開始時のチェックで見つかりませんでした")
            return

        if card is None:
            card = ImportItemCard(source=source, is_url=is_url)
            card.retry_requested.connect(self._retry_card)
            self.import_tab.queue.add(card)

        worker = ImportWorker(
            source=source,
            is_url=is_url,
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

    # ----- header bar refresh ------------------------------------------- #
    def _refresh_header(self) -> None:
        self.header.set_ffmpeg(ffmpeg_helper.is_installed())
        self.header.set_preset(settings.preset_name())
        self.header.set_queue(len(self._workers))

    # ----- sidebar primary action --------------------------------------- #
    def _focus_import(self) -> None:
        self.stack.setCurrentIndex(0)
        self.sidebar.select(0)
        self.header.set_page(0)
        self.import_tab.url_input.setFocus()

    # ----- Windows 11 chrome -------------------------------------------- #
    def _apply_native_chrome(self) -> None:
        hwnd = int(self.winId())
        win_chrome.enable_dark_titlebar(hwnd)
        win_chrome.enable_mica(hwnd, acrylic=False)
