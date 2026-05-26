"""Download audio from a URL.

Supports two paths:
  * YouTube / generic video URL → yt-dlp (audio extracted to mp3/m4a)
  * Direct link to .mp3 / .wav / .flac / .m4a → plain HTTP download
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import requests


_DIRECT_AUDIO_EXTS = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".opus"}


@dataclass
class DownloadResult:
    path: str
    title: str | None = None
    artist: str | None = None


def is_direct_audio_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in _DIRECT_AUDIO_EXTS)


def download_direct(url: str, out_dir: str) -> DownloadResult:
    os.makedirs(out_dir, exist_ok=True)
    filename = os.path.basename(urlparse(url).path) or "audio"
    # Sanitize filename
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    out_path = os.path.join(out_dir, filename)

    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                if chunk:
                    f.write(chunk)

    return DownloadResult(path=out_path, title=os.path.splitext(filename)[0])


def download_via_ytdlp(url: str, out_dir: str, audio_format: str = "mp3") -> DownloadResult:
    """Use yt-dlp to extract audio from a video URL."""
    try:
        import yt_dlp  # type: ignore
    except ImportError as e:
        raise RuntimeError("yt-dlp is required. `pip install yt-dlp`.") from e

    os.makedirs(out_dir, exist_ok=True)
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        out_path = ydl.prepare_filename(info)
        # postprocessor changes the extension
        base, _ = os.path.splitext(out_path)
        final_path = f"{base}.{audio_format}"

    return DownloadResult(
        path=final_path,
        title=info.get("title"),
        artist=info.get("uploader") or info.get("artist"),
    )


def download(url: str, out_dir: str) -> DownloadResult:
    """Dispatch to the appropriate downloader based on the URL."""
    if is_direct_audio_url(url):
        return download_direct(url, out_dir)
    return download_via_ytdlp(url, out_dir)
