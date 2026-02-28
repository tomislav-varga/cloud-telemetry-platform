"""create telemetry and devices tables

Revision ID: 20260223_0001
Revises: 
Create Date: 2026-02-23 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260223_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("device_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_devices_device_id", "devices", ["device_id"], unique=True)

    op.create_table(
        "telemetry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("device_id", sa.String(length=255), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("humidity", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("device_id", "timestamp", name="uq_telemetry_device_timestamp"),
    )

    op.create_index("idx_telemetry_device_id", "telemetry", ["device_id"], unique=False)
    op.create_index("idx_telemetry_timestamp", "telemetry", ["timestamp"], unique=False)
    op.create_index(
        "idx_telemetry_device_timestamp",
        "telemetry",
        ["device_id", sa.text("timestamp DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_telemetry_device_timestamp", table_name="telemetry")
    op.drop_index("idx_telemetry_timestamp", table_name="telemetry")
    op.drop_index("idx_telemetry_device_id", table_name="telemetry")
    op.drop_table("telemetry")

    op.drop_index("ix_devices_device_id", table_name="devices")
    op.drop_table("devices")
