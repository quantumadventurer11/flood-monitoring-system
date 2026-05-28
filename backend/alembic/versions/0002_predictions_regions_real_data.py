"""predictions and regions real data fields

Revision ID: 0002_real_data_fields
Revises: 0001_initial_schema
Create Date: 2026-05-28
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002_real_data_fields"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("regions", sa.Column("risk_baseline", sa.Float(), nullable=False, server_default="0.1"))
    op.add_column("predictions", sa.Column("data_source", sa.String(length=40), nullable=False, server_default="fallback"))
    op.add_column("predictions", sa.Column("satellite_date", sa.Date(), nullable=True))
    op.execute("UPDATE predictions SET satellite_date = target_date WHERE satellite_date IS NULL")
    op.alter_column("predictions", "satellite_date", nullable=False)


def downgrade() -> None:
    op.drop_column("predictions", "satellite_date")
    op.drop_column("predictions", "data_source")
    op.drop_column("regions", "risk_baseline")
