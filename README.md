# itunes-library-helper

iTunes / Apple Music ライブラリへの楽曲追加を、直感的なGUIで簡単に行うためのWindows向けデスクトップアプリです。

旧iTunesの「ファイルを追加」フローは分かりづらく、対応していないフォーマットや動画URLからの取り込みには手作業が必要でした。本アプリはそのギャップを埋めることを目的としています。

## 主な機能

- **動画URL / 直リンクからの取り込み** — YouTube等の動画URL、または `.mp3` / `.wav` などへの直リンクから音源を取得してライブラリへ追加（yt-dlp利用）
- **ローカル音楽ファイルからの取り込み** — ドラッグ&ドロップで複数ファイルを一括追加
- **メタデータ自動取得・編集** — アーティスト、アルバム、アートワークを自動補完／GUIで編集
- **プレイリスト一括作成** — URLリストやフォルダから一気にプレイリストを生成
- **フォーマット自動変換** — iTunesが非対応の形式（FLAC等）をAAC/MP3へ自動変換（ffmpeg利用）

## 動作要件

- Windows 10 / 11
- Python 3.10+
- iTunes（Microsoft Store版または旧デスクトップ版）
  - ※ 新しい「Apple Music」アプリ単体ではスクリプタブルAPIが未提供のため、現状はiTunesが必要です
- ffmpeg（フォーマット変換機能を使う場合）

## セットアップ

```powershell
git clone https://github.com/<your-account>/itunes-library-helper.git
cd itunes-library-helper
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.main
```

## プロジェクト構成

```
src/
  main.py              # エントリポイント
  itunes_client.py     # iTunes COM API ラッパー
  downloader.py        # yt-dlp ラッパー（URLからの音源取得）
  converter.py         # ffmpeg ラッパー（フォーマット変換）
  metadata.py          # mutagen ラッパー（タグ操作）
  gui/
    main_window.py     # メインウィンドウ
```

## ライセンス

MIT
