"""remove excerpt from articles

Revision ID: e5c9d1a7b4f2
Revises: d2a8e5f1c3b7
Create Date: 2026-03-14 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5c9d1a7b4f2"
down_revision: Union[str, Sequence[str], None] = "d2a8e5f1c3b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("articles", "excerpt_ka")
    op.drop_column("articles", "excerpt_en")


def downgrade() -> None:
    op.add_column("articles", sa.Column("excerpt_en", sa.Text(), nullable=True))
    op.add_column("articles", sa.Column("excerpt_ka", sa.Text(), nullable=True))
