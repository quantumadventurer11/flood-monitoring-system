"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-27
"""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "regions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("country", sa.String(length=120), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("buffer_km", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=24), nullable=False),
    )
    op.create_index(op.f("ix_regions_country"), "regions", ["country"], unique=True)
    op.create_index(op.f("ix_regions_id"), "regions", ["id"], unique=False)

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("country", sa.String(length=120), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("flood_probability", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=24), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
    )
    op.create_index(op.f("ix_events_country"), "events", ["country"], unique=False)
    op.create_index(op.f("ix_events_id"), "events", ["id"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("country", sa.String(length=120), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_alerts_country"), "alerts", ["country"], unique=False)
    op.create_index(op.f("ix_alerts_id"), "alerts", ["id"], unique=False)

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("country", sa.String(length=120), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("flood_probability", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=24), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_predictions_country"), "predictions", ["country"], unique=False)
    op.create_index(op.f("ix_predictions_id"), "predictions", ["id"], unique=False)

    op.create_table(
        "paper_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=80), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index(op.f("ix_paper_results_key"), "paper_results", ["key"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_paper_results_key"), table_name="paper_results")
    op.drop_table("paper_results")
    op.drop_index(op.f("ix_predictions_id"), table_name="predictions")
    op.drop_index(op.f("ix_predictions_country"), table_name="predictions")
    op.drop_table("predictions")
    op.drop_index(op.f("ix_alerts_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_country"), table_name="alerts")
    op.drop_table("alerts")
    op.drop_index(op.f("ix_events_id"), table_name="events")
    op.drop_index(op.f("ix_events_country"), table_name="events")
    op.drop_table("events")
    op.drop_index(op.f("ix_regions_id"), table_name="regions")
    op.drop_index(op.f("ix_regions_country"), table_name="regions")
    op.drop_table("regions")
