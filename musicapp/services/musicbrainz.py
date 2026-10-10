"""MusicBrainz API client with rate limiting and retry.

MusicBrainz asks for max 1 request/sec. All outbound calls go through this
client so the token-bucket limiter is shared app-wide.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx

from musicapp.config import settings

MUSICBRAINZ_BASE = "https://musicbrainz.org/ws/2"
COVERART_BASE = "https://coverartarchive.org"


@dataclass(frozen=True)
class ReleaseGroupData:
    mbid: str
    title: str
    primary_type: str | None
    artist_credit: str
    first_release_date: str | None
    cover_art_url: str | None


class TokenBucket:
    """Simple 1-token-per-second limiter."""

    def __init__(self, rate: float = 1.0) -> None:
        self._rate = rate
        self._tokens = rate
        self._updated_at = time.monotonic()

    def acquire(self) -> None:
        while True:
            now = time.monotonic()
            elapsed = now - self._updated_at
            self._updated_at = now
            self._tokens = min(self._rate, self._tokens + elapsed * self._rate)
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return
            sleep_for = (1.0 - self._tokens) / self._rate
            time.sleep(sleep_for)


class MusicBrainzClient:
    def __init__(
        self,
        *,
        user_agent: str | None = None,
        client: httpx.Client | None = None,
        limiter: TokenBucket | None = None,
        max_retries: int = 3,
    ) -> None:
        self._user_agent = user_agent or settings.musicbrainz_user_agent
        self._owns_client = client is None
        self._client = client or httpx.Client(
            headers={"User-Agent": self._user_agent, "Accept": "application/json"},
            timeout=30.0,
        )
        self._limiter = limiter or TokenBucket(rate=1.0)
        self._max_retries = max_retries

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> MusicBrainzClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _get(self, url: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            self._limiter.acquire()
            try:
                response = self._client.get(url, params=params)
            except httpx.HTTPError as exc:
                last_error = exc
                time.sleep(2**attempt)
                continue

            if response.status_code == 503:
                time.sleep(2**attempt)
                continue

            response.raise_for_status()
            return response

        if last_error is not None:
            raise last_error
        raise httpx.HTTPStatusError(
            "MusicBrainz unavailable after retries",
            request=httpx.Request("GET", url),
            response=response,  # type: ignore[possibly-undefined]
        )

    def search_release_groups(self, query: str, *, limit: int = 10) -> list[ReleaseGroupData]:
        response = self._get(
            f"{MUSICBRAINZ_BASE}/release-group",
            params={"query": query, "fmt": "json", "limit": limit},
        )
        payload = response.json()
        results: list[ReleaseGroupData] = []
        for item in payload.get("release-groups", []):
            results.append(self._parse_release_group(item, fetch_cover=False))
        return results

    def get_release_group(self, mbid: str) -> ReleaseGroupData:
        response = self._get(
            f"{MUSICBRAINZ_BASE}/release-group/{mbid}",
            params={"fmt": "json", "inc": "artist-credits"},
        )
        return self._parse_release_group(response.json(), fetch_cover=True)

    def get_cover_art_url(self, release_group_mbid: str) -> str | None:
        """Cover art may be missing; callers must handle None."""
        url = f"{COVERART_BASE}/release-group/{release_group_mbid}"
        try:
            self._limiter.acquire()
            response = self._client.get(url, follow_redirects=True)
        except httpx.HTTPError:
            return None

        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            return None

        try:
            images = response.json().get("images", [])
        except ValueError:
            return None

        for image in images:
            if image.get("front"):
                return image.get("image") or image.get("thumbnails", {}).get("large")
        if images:
            first = images[0]
            return first.get("image") or first.get("thumbnails", {}).get("large")
        return None

    def _parse_release_group(
        self, item: dict[str, Any], *, fetch_cover: bool
    ) -> ReleaseGroupData:
        mbid = item["id"]
        artist_credit = _format_artist_credit(item.get("artist-credit", []))
        cover_art_url = self.get_cover_art_url(mbid) if fetch_cover else None
        return ReleaseGroupData(
            mbid=mbid,
            title=item.get("title", ""),
            primary_type=item.get("primary-type"),
            artist_credit=artist_credit,
            first_release_date=item.get("first-release-date"),
            cover_art_url=cover_art_url,
        )


def _format_artist_credit(credits: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for credit in credits:
        name = credit.get("name") or credit.get("artist", {}).get("name", "")
        joinphrase = credit.get("joinphrase", "")
        parts.append(f"{name}{joinphrase}")
    return "".join(parts) if parts else "Unknown Artist"
