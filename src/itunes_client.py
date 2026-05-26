"""Wrapper around the iTunes COM API (Windows).

iTunes exposes a scriptable COM object (`iTunes.Application`) which lets
us add files to the library. This module isolates all COM interaction
behind a small typed surface and degrades gracefully when iTunes is not
installed (so the rest of the app can run in file-output mode).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable


@dataclass
class AddedTrack:
    name: str
    artist: str
    album: str
    location: str


class ITunesNotAvailableError(RuntimeError):
    pass


def is_available() -> bool:
    """Return True if iTunes is installed and the COM server is reachable.

    Does not keep the dispatched object — callers should instantiate
    ITunesClient when they actually want to add files.
    """
    try:
        import win32com.client  # type: ignore
        win32com.client.Dispatch("iTunes.Application")
        return True
    except Exception:
        return False


class ITunesClient:
    def __init__(self) -> None:
        try:
            import win32com.client  # type: ignore
        except ImportError as e:
            raise ITunesNotAvailableError(
                "pywin32 is required. Install with `pip install pywin32`."
            ) from e

        try:
            self._app = win32com.client.Dispatch("iTunes.Application")
        except Exception as e:
            raise ITunesNotAvailableError(
                "Could not connect to iTunes. Make sure iTunes is installed."
            ) from e

    def add_file(self, path: str) -> AddedTrack:
        if not os.path.isfile(path):
            raise FileNotFoundError(path)

        op_status = self._app.LibraryPlaylist.AddFile(path)
        tracks = op_status.Tracks
        if tracks.Count < 1:
            raise RuntimeError(f"iTunes did not import the file: {path}")

        t = tracks.Item(1)
        return AddedTrack(
            name=t.Name or "",
            artist=t.Artist or "",
            album=t.Album or "",
            location=t.Location or path,
        )

    def add_files(self, paths: Iterable[str]) -> list[AddedTrack]:
        return [self.add_file(p) for p in paths]

    def create_playlist(self, name: str) -> "Playlist":
        return Playlist(self._app.CreatePlaylist(name))

    def find_playlist(self, name: str) -> "Playlist | None":
        for i in range(1, self._app.LibrarySource.Playlists.Count + 1):
            pl = self._app.LibrarySource.Playlists.Item(i)
            if pl.Name == name:
                return Playlist(pl)
        return None


class Playlist:
    def __init__(self, com_playlist) -> None:
        self._pl = com_playlist

    @property
    def name(self) -> str:
        return self._pl.Name

    def add_file(self, path: str) -> None:
        self._pl.AddFile(path)
