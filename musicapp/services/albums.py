"""Release group cache: check local DB before calling MusicBrainz."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from musicapp.models import ReleaseGroup
from musicapp.services.musicbrainz import MusicBrainzClient, ReleaseGroupData


def get_or_fetch_release_group(
    db: Session,
    mbid: str,
    client: MusicBrainzClient,
) -> ReleaseGroup:
    existing = db.scalar(select(ReleaseGroup).where(ReleaseGroup.mbid == mbid))
    if existing is not None:
        return existing

    data = client.get_release_group(mbid)
    return upsert_release_group(db, data)


def upsert_release_group(db: Session, data: ReleaseGroupData) -> ReleaseGroup:
    row = db.scalar(select(ReleaseGroup).where(ReleaseGroup.mbid == data.mbid))
    if row is None:
        row = ReleaseGroup(mbid=data.mbid)
        db.add(row)

    row.title = data.title
    row.primary_type = data.primary_type
    row.artist_credit = data.artist_credit
    row.first_release_date = data.first_release_date
    row.cover_art_url = data.cover_art_url
    row.fetched_at = datetime.now(UTC)
    db.flush()
    return row
