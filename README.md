<div align="center">

# 🎵 iTunes Library Helper

### *URLからでも、ファイルからでも。あなたの音楽を最速でライブラリへ。*

<br />

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg?style=for-the-badge&logo=windows&logoColor=white)](#)
[![GUI: PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52.svg?style=for-the-badge&logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)
[![Status: Alpha](https://img.shields.io/badge/Status-Alpha-orange.svg?style=for-the-badge)](#)

<br />

旧 iTunes の「ファイルを追加」フローは古く、分かりづらく、
**動画URL** や **非対応フォーマット** からの取り込みには毎回手作業が必要でした。
このアプリは、その面倒さをすべて吸収します。

</div>

---

## 📥 ダウンロード

<div align="center">

### 👉 **[最新版 .exe をダウンロード](https://github.com/Assy2005/itunes-library-helper/releases/latest)**

<sub>Windows 10 / 11 ・ Python インストール不要 ・ ダブルクリックで起動</sub>

</div>

---

## ✨ 一目でわかる、できること

<table>
<tr>
<td width="33%" align="center" valign="top">
<h3>🌐</h3>
<b>URLから直接追加</b><br/>
<sub>YouTube等の動画URL、<br/>または <code>.mp3</code> / <code>.wav</code> の直リンクを<br/>貼るだけで取り込み</sub>
</td>
<td width="33%" align="center" valign="top">
<h3>📁</h3>
<b>ドラッグ&ドロップ</b><br/>
<sub>ローカルの音楽ファイルを<br/>まとめてウィンドウに放り込むだけ。<br/>複数ファイル同時OK</sub>
</td>
<td width="33%" align="center" valign="top">
<h3>🎚️</h3>
<b>音質プリセット & カスタム</b><br/>
<sub>原音忠実 / ポップ / EDM・重低音 /<br/>ボーカル強調 / クリア・高解像度<br/>+ 全項目カスタム</sub>
</td>
</tr>
<tr>
<td width="33%" align="center" valign="top">
<h3>🔊</h3>
<b>重低音強化 & 高音強化</b><br/>
<sub>ffmpegフィルターで<br/>bass +12dB / treble +6dB まで<br/>段階的にブースト</sub>
</td>
<td width="33%" align="center" valign="top">
<h3>🎛️</h3>
<b>ノイズ除去 & 音量正規化</b><br/>
<sub>FFTデノイズ、EBU R128 ラウドネス、<br/>ダイナミクス補正、アップサンプリングを<br/>自由に組み合わせ</sub>
</td>
<td width="33%" align="center" valign="top">
<h3>🎵</h3>
<b>Apple Music 取り込み補助</b><br/>
<sub>処理完了後、エクスプローラで<br/>ファイル選択 + Apple Music起動を<br/>自動実行 → ドラッグするだけ</sub>
</td>
</tr>
</table>

---

## 🎚️ 音質プリセット

| プリセット | ビットレート | 主な処理 | 向いている音楽 |
|---|---|---|---|
| **原音忠実** | 320 kbps | 処理なし | クラシック・ジャズ・ハイレゾ |
| **ポップ** | 256 kbps | 低音+3dB / 高音+2dB / ダイナミクス補正 | J-POP・洋楽ポップス |
| **EDM・重低音** | 320 kbps | 低音+8dB / ラウドネス正規化 | EDM・HipHop・ダンス |
| **ボーカル強調** | 256 kbps | 高音+4dB / ノイズ除去 / ラウドネス正規化 | アコースティック・歌モノ |
| **クリア・高解像度** | 320 kbps | 軽いノイズ除去 / 48kHz アップサンプリング | 全般・配信音源の底上げ |
| **カスタム** | 128–320 kbps | 全パラメータ手動調整 | こだわり派 |

---

## 🏗️ アーキテクチャ

```mermaid
flowchart LR
    subgraph UI[" 🖥️  GUI Layer "]
        MW[MainWindow<br/>PyQt6]
    end
    subgraph WORK[" ⚙️  Worker Layer "]
        IW[ImportWorker<br/>QThread]
    end
    subgraph CORE[" 🎯  Core Modules "]
        DL[downloader<br/>yt-dlp / requests]
        CV[converter<br/>ffmpeg]
        MD[metadata<br/>mutagen]
        IT[itunes_client<br/>COM API]
    end
    subgraph EXT[" 🍎  External "]
        ITUNES[(iTunes<br/>Library)]
    end

    MW -->|URL or File| IW
    IW --> DL
    IW --> CV
    IW --> MD
    IW --> IT
    IT --> ITUNES

    style UI fill:#1e293b,stroke:#3b82f6,color:#fff
    style WORK fill:#1e293b,stroke:#a855f7,color:#fff
    style CORE fill:#1e293b,stroke:#10b981,color:#fff
    style EXT fill:#1e293b,stroke:#f43f5e,color:#fff
```

---

## 🚀 クイックスタート

### 動作要件

| 項目 | 要件 |
|------|------|
| **OS** | Windows 10 / 11 |
| **Python** | 3.10 以上 |
| **Apple Music for Windows** | （推奨）処理完了後に自動起動 → ドラッグで取り込み |
| **iTunes** | （旧版オプション）あれば自動でライブラリ追加 |
| **ffmpeg** | 音質処理 / フォーマット変換を使う場合は必須 |

> 💡 **新しい Apple Music for Windows には公式の自動追加APIが存在しません** (Apple確認済み)。
> このアプリは **「処理完了 → エクスプローラで対象ファイルを選択表示 + Apple Music を起動」**
> を自動化することで、最後の "ドラッグするだけ" の状態をお膳立てします。
>
> 旧 **iTunes** をお使いの方は COM API 経由で**完全自動**でライブラリ追加できます (設定タブでON)。

### インストール & 起動

```powershell
# 1. クローン
git clone https://github.com/Assy2005/itunes-library-helper.git
cd itunes-library-helper

# 2. 仮想環境を作成
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. 依存関係をインストール
pip install -r requirements.txt

# 4. 起動！
python -m src.main
```

---

## 📂 プロジェクト構成

```
itunes-library-helper/
├── 📄 README.md
├── 📄 LICENSE                  ← MIT
├── 📄 requirements.txt
├── 📄 .gitignore
└── 📁 src/
    ├── 🐍 main.py              ← エントリポイント
    ├── 🍎 itunes_client.py     ← iTunes COM API ラッパー
    ├── 🌐 downloader.py        ← yt-dlp / 直リンク ダウンローダ
    ├── 🔄 converter.py         ← ffmpeg フォーマット変換
    ├── 🏷️  metadata.py          ← mutagen タグ読み書き
    └── 📁 gui/
        └── 🖥️  main_window.py    ← メインウィンドウ
```

---

## 🛠️ 使用技術

<div align="center">

| カテゴリ | ライブラリ | 役割 |
|:--:|:--:|:--|
| **GUI** | [PyQt6](https://pypi.org/project/PyQt6/) | デスクトップUI |
| **iTunes連携** | [pywin32](https://pypi.org/project/pywin32/) | COM API 経由でライブラリ操作 |
| **動画/音声DL** | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | YouTube等から音源抽出 |
| **HTTP** | [requests](https://pypi.org/project/requests/) | 直リンク・アートワーク取得 |
| **タグ** | [mutagen](https://pypi.org/project/mutagen/) | ID3 / FLAC / MP4 タグ編集 |
| **変換** | [ffmpeg](https://ffmpeg.org/) (via [ffmpeg-python](https://pypi.org/project/ffmpeg-python/)) | フォーマット変換 |

</div>

---

## 🗺️ ロードマップ

- [x] プロジェクトスケルトン
- [x] URL / ファイル取り込みの基本フロー
- [x] 非同期 (QThread) 処理
- [x] PyInstaller でのワンファイル配布
- [x] **音質プリセット 5種 + カスタム** (bass / treble / denoise / loudnorm / dynaudnorm / resample)
- [x] **iTunes 任意化 — ファイル出力モード**
- [x] **Apple Music 風 GUI** (タブ + カードUI + ピンクアクセント)
- [x] **設定の永続化** (QSettings)
- [x] **Apple Music 取り込み補助** (エクスプローラ自動表示 + Apple Music 起動)
- [ ] OLE Drag&Drop シミュレーションで Apple Music 完全自動化 (R&D)
- [ ] yt-dlp / ffmpeg 進捗の詳細表示
- [ ] メタデータ編集ダイアログ
- [ ] アートワーク自動取得 (iTunes Search API)
- [ ] プレイリスト一括作成 UI
- [ ] ダーク/ライト切り替え
- [ ] アプリアイコン

---

## 🤝 コントリビュート

Issue / PR 歓迎です。バグ報告や機能リクエストはお気軽にどうぞ。

---

<div align="center">

## 📜 ライセンス

[**MIT License**](LICENSE)

<br/>

<sub>Made with ☕ and a long-standing frustration with iTunes' "Add File" dialog.</sub>

</div>
