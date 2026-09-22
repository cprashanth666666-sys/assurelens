"""Asset record content: what suite 1 actually scans.

The estate had assets and it had principals, but nothing held the content an
asset stores. Identifier discovery has to read something -- a scan that
inspects only a data inventory is checking what an organisation *says* it
holds, which is the claim under test, not evidence about it.

The gap between declared and actual is the whole finding.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "est_asset_records",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "asset_id", sa.Integer,
            sa.ForeignKey("est_data_assets.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "principal_id", sa.BigInteger,
            sa.ForeignKey("est_data_principals.id", ondelete="CASCADE"),
        ),
        # Whatever the asset stores, as the asset stores it. Structured
        # columns for a CRM row; a single free-text body for a transcript.
        # Suite 1 scans the values without assuming a shape, because an
        # identifier hiding in prose is exactly the case a column-aware
        # scanner misses.
        sa.Column("content", postgresql.JSONB, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index("ix_asset_records_asset", "est_asset_records", ["asset_id"])


def downgrade() -> None:
    op.drop_index("ix_asset_records_asset", table_name="est_asset_records")
    op.drop_table("est_asset_records")
