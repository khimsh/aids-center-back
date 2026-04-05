"""extend doctors with order and profile fields

Revision ID: a7c4e9f1d2b6
Revises: f3b8c2d0e1a9
Create Date: 2026-04-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7c4e9f1d2b6"
down_revision: Union[str, Sequence[str], None] = "f3b8c2d0e1a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("doctors", sa.Column("profile_url", sa.String(length=500), nullable=True))
    op.add_column("doctors", sa.Column("specialty", sa.String(length=255), nullable=True))
    op.add_column("doctors", sa.Column("degree", sa.String(length=255), nullable=True))
    op.add_column("doctors", sa.Column("department", sa.String(length=255), nullable=True))
    op.add_column("doctors", sa.Column("pedagogical_experience", sa.Text(), nullable=True))
    op.add_column("doctors", sa.Column("memberships", sa.Text(), nullable=True))
    op.add_column("doctors", sa.Column("publications", sa.Text(), nullable=True))
    op.add_column("doctors", sa.Column("expertise", sa.Text(), nullable=True))
    op.add_column("doctors", sa.Column("sort_order", sa.Integer(), nullable=True))

    op.execute("UPDATE doctors SET sort_order = id WHERE sort_order IS NULL")

    op.alter_column("doctors", "sort_order", nullable=False)
    op.create_index(op.f("ix_doctors_sort_order"), "doctors", ["sort_order"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_doctors_sort_order"), table_name="doctors")
    op.drop_column("doctors", "sort_order")
    op.drop_column("doctors", "expertise")
    op.drop_column("doctors", "publications")
    op.drop_column("doctors", "memberships")
    op.drop_column("doctors", "pedagogical_experience")
    op.drop_column("doctors", "department")
    op.drop_column("doctors", "degree")
    op.drop_column("doctors", "specialty")
    op.drop_column("doctors", "profile_url")
