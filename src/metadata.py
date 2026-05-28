"""Read and write audio file tags (incl. embedded artwork) via mutagen."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class TrackMetadata:
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    artwork_bytes: bytes | None = None       # JPEG / PNG bytes
    artwork_mime: str = "image/jpeg"


def _detect_mime(data: bytes) -> str:
    if not data:
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    return "image/jpeg"


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


def write_tags(path: str, meta: TrackMetadata) -> None:
    """Write text tags (no artwork) using the easy interface."""
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


def write_artwork(path: str, data: bytes) -> None:
    """Embed cover artwork into the file. Container handling depends on
    the file's format because mutagen's "easy" interface doesn't expose
    cover art uniformly.
    """
    if not data:
        return
    ext = os.path.splitext(path)[1].lower()
    mime = _detect_mime(data)

    if ext in (".m4a", ".mp4", ".aac"):
        from mutagen.mp4 import MP4, MP4Cover  # type: ignore

        f = MP4(path)
        cover_fmt = (MP4Cover.FORMAT_PNG if mime == "image/png"
                     else MP4Cover.FORMAT_JPEG)
        f.tags = f.tags or {}
        f.tags["covr"] = [MP4Cover(data, imageformat=cover_fmt)]
        f.save()

    elif ext == ".mp3":
        from mutagen.id3 import APIC, ID3, ID3NoHeaderError  # type: ignore

        try:
            tags = ID3(path)
        except ID3NoHeaderError:
            tags = ID3()
        # Drop any existing covers so we don't accumulate duplicates.
        tags.delall("APIC")
        tags.add(APIC(
            encoding=3, mime=mime, type=3,
            desc="Cover", data=data,
        ))
        tags.save(path)

    elif ext == ".flac":
        from mutagen.flac import FLAC, Picture  # type: ignore

        f = FLAC(path)
        pic = Picture()
        pic.data = data
        pic.type = 3  # Cover (front)
        pic.mime = mime
        f.clear_pictures()
        f.add_picture(pic)
        f.save()

    elif ext in (".ogg", ".opus"):
        import base64

        from mutagen.flac import Picture  # type: ignore
        from mutagen.oggvorbis import OggVorbis  # type: ignore

        f = OggVorbis(path)
        pic = Picture()
        pic.data = data
        pic.type = 3
        pic.mime = mime
        f["metadata_block_picture"] = [base64.b64encode(
            pic.write()).decode("ascii")]
        f.save()

    else:
        # WAV, AIFF, and a handful of others don't have a clean way to
        # embed artwork via mutagen. Silently skip rather than fail the
        # whole import flow.
        return


def apply(path: str, meta: TrackMetadata) -> None:
    """Apply both text tags and artwork in one call."""
    write_tags(path, meta)
    if meta.artwork_bytes:
        write_artwork(path, meta.artwork_bytes)
