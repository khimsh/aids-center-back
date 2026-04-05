"""create doctor translations table

Revision ID: b9f1d3c7e4a2
Revises: a7c4e9f1d2b6
Create Date: 2026-04-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b9f1d3c7e4a2"
down_revision: Union[str, Sequence[str], None] = "a7c4e9f1d2b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "doctor_translations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("lang", sa.String(length=5), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("specialty", sa.String(length=255), nullable=True),
        sa.Column("degree", sa.String(length=255), nullable=True),
        sa.Column("department", sa.String(length=255), nullable=True),
        sa.Column("education", sa.Text(), nullable=False),
        sa.Column("experience", sa.Text(), nullable=False),
        sa.Column("pedagogical_experience", sa.Text(), nullable=True),
        sa.Column("memberships", sa.Text(), nullable=True),
        sa.Column("publications", sa.Text(), nullable=True),
        sa.Column("expertise", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("doctor_id", "lang", name="uq_doctor_translations_doctor_lang"),
    )
    op.create_index(op.f("ix_doctor_translations_id"), "doctor_translations", ["id"], unique=False)
    op.create_index(op.f("ix_doctor_translations_doctor_id"), "doctor_translations", ["doctor_id"], unique=False)
    op.create_index(op.f("ix_doctor_translations_lang"), "doctor_translations", ["lang"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_doctor_translations_lang"), table_name="doctor_translations")
    op.drop_index(op.f("ix_doctor_translations_doctor_id"), table_name="doctor_translations")
    op.drop_index(op.f("ix_doctor_translations_id"), table_name="doctor_translations")
    op.drop_table("doctor_translations")
