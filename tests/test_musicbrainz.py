"""MusicBrainz client tests — never hit the live API."""

import httpx

from musicapp.services.albums import upsert_release_group
from musicapp.services.musicbrainz import MusicBrainzClient, ReleaseGroupData, TokenBucket


def test_token_bucket_allows_immediate_first_acquire() -> None:
    bucket = TokenBucket(rate=1.0)
    bucket.acquire()  # should not block meaningfully


def test_search_release_groups_parses_mock_response() -> None:
    mock_response = httpx.Response(
        200,
        json={
            "release-groups": [
                {
                    "id": "b84ee12a-09ef-421b-82de-0441a926901d",
                    "title": "OK Computer",
                    "primary-type": "Album",
                    "first-release-date": "1997-05-21",
                    "artist-credit": [
                        {"name": "Radiohead", "joinphrase": ""},
                    ],
                }
            ]
        },
        request=httpx.Request("GET", "https://musicbrainz.org/ws/2/release-group"),
    )
    transport = httpx.MockTransport(lambda request: mock_response)
    http_client = httpx.Client(transport=transport)

    client = MusicBrainzClient(
        client=http_client,
        limiter=TokenBucket(rate=1000.0),
    )
    results = client.search_release_groups("OK Computer")

    assert len(results) == 1
    assert results[0].mbid == "b84ee12a-09ef-421b-82de-0441a926901d"
    assert results[0].title == "OK Computer"
    assert results[0].artist_credit == "Radiohead"
    assert results[0].cover_art_url is None


def test_get_cover_art_handles_404() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, request=request)

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = MusicBrainzClient(
        client=http_client,
        limiter=TokenBucket(rate=1000.0),
    )
    assert client.get_cover_art_url("missing-mbid") is None


def test_retries_on_503_then_succeeds() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503, request=request)
        return httpx.Response(
            200,
            json={"release-groups": []},
            request=request,
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = MusicBrainzClient(
        client=http_client,
        limiter=TokenBucket(rate=1000.0),
        max_retries=3,
    )
    assert client.search_release_groups("anything") == []
    assert calls["n"] == 3


def test_upsert_release_group(db_session) -> None:
    data = ReleaseGroupData(
        mbid="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        title="In Rainbows",
        primary_type="Album",
        artist_credit="Radiohead",
        first_release_date="2007-10-10",
        cover_art_url=None,
    )
    row = upsert_release_group(db_session, data)
    db_session.commit()

    assert row.id is not None
    assert row.title == "In Rainbows"

    updated = upsert_release_group(
        db_session,
        ReleaseGroupData(
            mbid=data.mbid,
            title="In Rainbows",
            primary_type="Album",
            artist_credit="Radiohead",
            first_release_date="2007-10-10",
            cover_art_url="https://example.com/cover.jpg",
        ),
    )
    db_session.commit()
    assert updated.id == row.id
    assert updated.cover_art_url == "https://example.com/cover.jpg"
