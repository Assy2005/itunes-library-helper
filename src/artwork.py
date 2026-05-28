"""iTunes Search API client — find and download album artwork.

No auth required, no API key. Just plain HTTP requests against
`https://itunes.apple.com/search`.

We also know how to upgrade the default 100×100 thumbnail URL to a
higher-resolution version (Apple serves the asset at multiple sizes
via simple URL substitution).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import requests


_SEARCH_URL = "https://itunes.apple.com/search"
_REQUEST_TIMEOUT = 10


@dataclass
class ArtworkHit:
    title: str
    artist: str
    album: str
    artwork_url_100: str

    def artwork_url(self, size: int = 600) -> str:
        """Apple stores higher-res versions by changing the size suffix."""
        return re.sub(r"/\d+x\d+(?:bb)?\.(jpg|png)$",
                      f"/{size}x{size}bb.\\1", self.artwork_url_100)


def search(term: str, *, limit: int = 5) -> list[ArtworkHit]:
    """Search the iTunes catalog for a track.

    `term` is whatever you have — typically "<artist> <title>" but a
    plain title alone often works too.
    """
    try:
        r = requests.get(
            _SEARCH_URL,
            params={
                "term": term,
                "entity": "song",
                "limit": limit,
                "country": "JP",
            },
            timeout=_REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    hits: list[ArtworkHit] = []
    for item in data.get("results", []):
        art = item.get("artworkUrl100") or ""
        if not art:
            continue
        hits.append(ArtworkHit(
            title=item.get("trackName", ""),
            artist=item.get("artistName", ""),
            album=item.get("collectionName", ""),
            artwork_url_100=art,
        ))
    return hits


def fetch_artwork_bytes(url: str) -> bytes | None:
    """Download artwork at the URL and return the raw image bytes."""
    try:
        r = requests.get(url, timeout=_REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.content
    except Exception:
        return None


def best_match(query: str) -> tuple[ArtworkHit, bytes] | None:
    """Convenience: search by query, fetch the top hit's hi-res artwork."""
    hits = search(query, limit=1)
    if not hits:
        return None
    top = hits[0]
    img = fetch_artwork_bytes(top.artwork_url(600))
    if img is None:
        return None
    return top, img
