"""Initial schema: users, release_groups, album_logs

Revision ID: 001
Revises:
Create Date: 2026-10-09

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "release_groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mbid", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("primary_type", sa.String(length=64), nullable=True),
        sa.Column("artist_credit", sa.String(length=512), nullable=False),
        sa.Column("first_release_date", sa.String(length=10), nullable=True),
        sa.Column("cover_art_url", sa.Text(), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_release_groups_mbid", "release_groups", ["mbid"], unique=True)

    op.create_table(
        "album_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "release_group_id",
            sa.Integer(),
            sa.ForeignKey("release_groups.id"),
            nullable=False,
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("review", sa.Text(), nullable=True),
        sa.Column("listened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("rating >= 1 AND rating <= 10", name="ck_rating_range"),
        sa.UniqueConstraint(
            "user_id", "release_group_id", name="uq_user_release_group"
        ),
    )
    op.create_index("ix_album_logs_user_id", "album_logs", ["user_id"])
    op.create_index(
        "ix_album_logs_release_group_id", "album_logs", ["release_group_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_album_logs_release_group_id", table_name="album_logs")
    op.drop_index("ix_album_logs_user_id", table_name="album_logs")
    op.drop_table("album_logs")
    op.drop_index("ix_release_groups_mbid", table_name="release_groups")
    op.drop_table("release_groups")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
