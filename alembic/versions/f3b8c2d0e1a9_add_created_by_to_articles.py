"""add created_by to articles

Revision ID: f3b8c2d0e1a9
Revises: e5c9d1a7b4f2
Create Date: 2026-03-19 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3b8c2d0e1a9"
down_revision: Union[str, Sequence[str], None] = "e5c9d1a7b4f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("created_by", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_articles_created_by_users",
        "articles", "users",
        ["created_by"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_articles_created_by", "articles", ["created_by"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_articles_created_by", table_name="articles")
    op.drop_constraint("fk_articles_created_by_users", "articles", type_="foreignkey")
    op.drop_column("articles", "created_by")
