"""initial schema: telemetry

Revision ID: 0001
Revises:
Create Date: 2026-10-28

Only the telemetry daemon's tables. Application models start from the next
revision: `alembic revision --autogenerate -m "..."`.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "telemetry_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trace_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("service", sa.String(length=64), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("epoch", sa.Double(), nullable=False),
        sa.Column("exec_ms", sa.Double(), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip", postgresql.INET(), nullable=True),
        sa.Column("method", sa.String(length=8), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("url_params", postgresql.JSONB(), nullable=True),
        sa.Column("data", postgresql.JSONB(), nullable=True),
        sa.Column("status_code", sa.SmallInteger(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_telemetry_log__trace_id", "telemetry_log", ["trace_id"])
    op.create_index(
        "idx_telemetry_log__service__ts", "telemetry_log", ["service", "ts"]
    )
    op.create_index("idx_telemetry_log__user_id__ts", "telemetry_log", ["user_id", "ts"])
    op.create_index("idx_telemetry_log__level", "telemetry_log", ["level"])
    op.create_index("idx_telemetry_log__status_code", "telemetry_log", ["status_code"])

    op.create_table(
        "telemetry_log_traceback",
        sa.Column("log_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("traceback", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("log_id", name="pk_telemetry_log_traceback__log_id"),
        sa.ForeignKeyConstraint(
            ["log_id"],
            ["telemetry_log.id"],
            name="pk_telemetry_log_traceback__log_id__telemetry_log__id",
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    op.drop_table("telemetry_log_traceback")
    op.drop_table("telemetry_log")
