"""Wrapper around the iTunes COM API (Windows).

iTunes exposes a scriptable COM object (`iTunes.Application`) which allows us
to enumerate playlists and add files to the library. This module isolates all
COM interaction behind a small typed surface so the rest of the app does not
need to know about win32com.
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
                "Could not connect to iTunes. Make sure iTunes is installed and can be launched."
            ) from e

    def add_file(self, path: str) -> AddedTrack:
        """Add a single audio file to the main library."""
        if not os.path.isfile(path):
            raise FileNotFoundError(path)

        op_status = self._app.LibraryPlaylist.AddFile(path)
        # AddFile returns an OperationStatus; tracks become available on .Tracks
        # once InProgress flips to False. For typical files this is immediate.
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
        pl = self._app.CreatePlaylist(name)
        return Playlist(pl)

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
