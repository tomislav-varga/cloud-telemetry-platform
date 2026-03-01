"""add device api key authentication columns

Revision ID: 20260301_0002
Revises: 20260223_0001
Create Date: 2026-03-01 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260301_0002"
down_revision = "20260223_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("devices", sa.Column("key_prefix", sa.String(length=32), nullable=True))
    op.add_column("devices", sa.Column("api_key_hash", sa.String(length=255), nullable=True))
    op.add_column(
        "devices",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column("devices", sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True))

    op.execute(
        """
        UPDATE devices
        SET key_prefix = 'migr_' || substr(replace(id::text, '-', ''), 1, 8)
        WHERE key_prefix IS NULL
        """
    )
    op.execute(
        """
        UPDATE devices
        SET api_key_hash = '$2b$12$C6UzMDM.H6dfI/f/IKcEeO5oW6iQWmvMRGsiE9zraFMvx6bMpiK2e'
        WHERE api_key_hash IS NULL
        """
    )

    op.alter_column("devices", "key_prefix", nullable=False)
    op.alter_column("devices", "api_key_hash", nullable=False)
    op.create_index("idx_devices_key_prefix", "devices", ["key_prefix"], unique=True)


def downgrade() -> None:
    op.drop_index("idx_devices_key_prefix", table_name="devices")
    op.drop_column("devices", "last_used_at")
    op.drop_column("devices", "is_active")
    op.drop_column("devices", "api_key_hash")
    op.drop_column("devices", "key_prefix")
