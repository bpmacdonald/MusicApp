from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from musicapp.db import Base

if TYPE_CHECKING:
    from musicapp.models.album import ReleaseGroup
    from musicapp.models.user import User


class AlbumLog(Base):
    """A user's logged listen / rating of a release group."""

    __tablename__ = "album_logs"
    __table_args__ = (
        UniqueConstraint("user_id", "release_group_id", name="uq_user_release_group"),
        CheckConstraint("rating >= 1 AND rating <= 10", name="ck_rating_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    release_group_id: Mapped[int] = mapped_column(
        ForeignKey("release_groups.id"), index=True
    )
    # Half-stars: 1–10 maps to 0.5–5.0 stars
    rating: Mapped[int] = mapped_column(Integer)
    review: Mapped[str | None] = mapped_column(Text, nullable=True)
    listened_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="logs")
    release_group: Mapped[ReleaseGroup] = relationship(back_populates="logs")
