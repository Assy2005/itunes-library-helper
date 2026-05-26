"""Read and write audio file tags using mutagen."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TrackMetadata:
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    artwork_bytes: bytes | None = None  # JPEG/PNG bytes


def read(path: str) -> TrackMetadata:
    from mutagen import File  # type: ignore

    f = File(path, easy=True)
    if f is None:
        return TrackMetadata()

    def first(key: str) -> str | None:
        v = f.get(key)
        if isinstance(v, list) and v:
            return str(v[0])
        return None

    return TrackMetadata(
        title=first("title"),
        artist=first("artist"),
        album=first("album"),
    )


def write(path: str, meta: TrackMetadata) -> None:
    from mutagen import File  # type: ignore

    f = File(path, easy=True)
    if f is None:
        raise ValueError(f"Unsupported audio file: {path}")

    if meta.title is not None:
        f["title"] = meta.title
    if meta.artist is not None:
        f["artist"] = meta.artist
    if meta.album is not None:
        f["album"] = meta.album
    f.save()

    # Artwork handling is format-specific; left as a follow-up.
