"""Download audio from a URL.

Supports two paths:
  * YouTube / generic video URL → yt-dlp (audio extracted to mp3/m4a)
  * Direct link to .mp3 / .wav / .flac / .m4a → plain HTTP download

The yt-dlp path accepts optional `log_cb` and `progress_cb` callbacks
so the GUI can stream verbose output and per-chunk progress instead of
sitting silent for minutes on long videos / playlist URLs.

`noplaylist=True` is set unconditionally — YouTube "Mix" / Radio links
(`?list=RD…`) would otherwise trigger downloads of the entire 50+ track
playlist with no warning.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlparse

import requests


_DIRECT_AUDIO_EXTS = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".opus"}

LogCb = Callable[[str], None]
ProgressCb = Callable[[dict], None]


@dataclass
class DownloadResult:
    path: str
    title: str | None = None
    artist: str | None = None


def is_direct_audio_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in _DIRECT_AUDIO_EXTS)


def download_direct(url: str, out_dir: str,
                    log_cb: LogCb | None = None) -> DownloadResult:
    os.makedirs(out_dir, exist_ok=True)
    filename = os.path.basename(urlparse(url).path) or "audio"
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    out_path = os.path.join(out_dir, filename)

    if log_cb:
        log_cb(f"HTTP GET {url}")

    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        downloaded = 0
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
        if log_cb:
            mb = downloaded / (1024 * 1024)
            log_cb(f"received {mb:.1f} MB → {out_path}")

    return DownloadResult(path=out_path, title=os.path.splitext(filename)[0])


def download_via_ytdlp(url: str, out_dir: str, audio_format: str = "mp3",
                       *,
                       log_cb: LogCb | None = None,
                       progress_cb: ProgressCb | None = None) -> DownloadResult:
    try:
        import yt_dlp  # type: ignore
    except ImportError as e:
        raise RuntimeError("yt-dlp is required. `pip install yt-dlp`.") from e

    os.makedirs(out_dir, exist_ok=True)

    class _Logger:
        # yt-dlp dispatches by these method names.
        def debug(self, msg: str) -> None:
            if log_cb and msg and not msg.startswith("[debug]"):
                log_cb(msg)

        def info(self, msg: str) -> None:
            if log_cb:
                log_cb(msg)

        def warning(self, msg: str) -> None:
            if log_cb:
                log_cb(f"⚠️  {msg}")

        def error(self, msg: str) -> None:
            if log_cb:
                log_cb(f"❌ {msg}")

    ydl_opts: dict = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": "192",
            }
        ],
        # Important: a YouTube "Mix" / Radio URL includes ?list=RD… and
        # without this yt-dlp would happily download the entire 50+
        # track auto-generated playlist.
        "noplaylist": True,
        "no_warnings": False,
        "quiet": False,
        "logger": _Logger(),
    }
    if progress_cb is not None:
        ydl_opts["progress_hooks"] = [progress_cb]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        out_path = ydl.prepare_filename(info)
        # postprocessor renames the extension to the chosen audio format
        base, _ = os.path.splitext(out_path)
        final_path = f"{base}.{audio_format}"

    return DownloadResult(
        path=final_path,
        title=info.get("title"),
        artist=info.get("uploader") or info.get("artist"),
    )


def download(url: str, out_dir: str, *,
             log_cb: LogCb | None = None,
             progress_cb: ProgressCb | None = None) -> DownloadResult:
    """Dispatch to the appropriate downloader based on the URL."""
    if is_direct_audio_url(url):
        return download_direct(url, out_dir, log_cb=log_cb)
    return download_via_ytdlp(url, out_dir, log_cb=log_cb, progress_cb=progress_cb)
