from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from musicapp.db import Base

if TYPE_CHECKING:
    from musicapp.models.log import AlbumLog


class ReleaseGroup(Base):
    """Cached MusicBrainz release group (album as a concept, not a release)."""

    __tablename__ = "release_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    mbid: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512))
    primary_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    artist_credit: Mapped[str] = mapped_column(String(512))
    first_release_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    cover_art_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    logs: Mapped[list[AlbumLog]] = relationship(back_populates="release_group")
