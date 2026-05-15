"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("protocols",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), unique=True),
        sa.Column("defillama_slug", sa.String(100)),
        sa.Column("description", sa.Text()),
        sa.Column("website_url", sa.Text()),
        sa.Column("github_url", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("protocol_contracts",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("protocol_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("protocols.id")),
        sa.Column("address", sa.String(42), nullable=False),
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("contract_role", sa.String(50), nullable=False),
        sa.Column("label", sa.String(200)),
        sa.Column("is_primary", sa.Boolean(), server_default="false"),
        sa.Column("added_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("address", "chain_id", name="uq_protocol_contracts_address_chain"),
    )
    op.create_index("idx_protocol_contracts_address", "protocol_contracts", ["address", "chain_id"])

    op.create_table("contracts",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("address", sa.String(42), nullable=False),
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("chain_name", sa.String(50)),
        sa.Column("protocol_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("protocols.id"), nullable=True),
        sa.Column("scan_type", sa.String(20), nullable=False, server_default="community"),
        sa.Column("is_verified", sa.Boolean(), server_default="false"),
        sa.Column("tvl_source", sa.String(30)),
        sa.Column("tvl_confidence", sa.String(20)),
        sa.Column("first_seen_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("last_scored_at", sa.TIMESTAMP(timezone=True)),
        sa.UniqueConstraint("address", "chain_id", name="uq_contracts_address_chain"),
    )
    op.create_index("idx_contracts_address_chain", "contracts", ["address", "chain_id"])

    op.create_table("score_reports",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("contract_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("contracts.id", ondelete="CASCADE")),
        sa.Column("protocol_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("protocols.id"), nullable=True),
        sa.Column("composite_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("grade", sa.String(1), nullable=False),
        sa.Column("code_risk_score", sa.Numeric(5, 2)),
        sa.Column("ownership_score", sa.Numeric(5, 2)),
        sa.Column("liquidity_score", sa.Numeric(5, 2)),
        sa.Column("audit_score", sa.Numeric(5, 2)),
        sa.Column("compliance_score", sa.Numeric(5, 2)),
        sa.Column("governance_score", sa.Numeric(5, 2)),
        sa.Column("tvl_usd", sa.Numeric(20, 2)),
        sa.Column("tvl_confidence", sa.String(20)),
        sa.Column("tvl_source", sa.String(30)),
        sa.Column("override_applied", sa.Boolean(), server_default="false"),
        sa.Column("override_status", sa.String(30)),
        sa.Column("raw_findings", postgresql.JSONB()),
        sa.Column("recommendations", postgresql.ARRAY(sa.Text())),
        sa.Column("score_version", sa.String(10), server_default="1.0"),
        sa.Column("scored_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_score_reports_contract_time", "score_reports", ["contract_id", sa.text("scored_at DESC")])

    op.create_table("override_history",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("contract_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("contracts.id")),
        sa.Column("protocol_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("protocols.id")),
        sa.Column("override_type", sa.String(20), nullable=False),
        sa.Column("override_status", sa.String(20), nullable=False),
        sa.Column("applied_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("resolution_type", sa.String(30)),
        sa.Column("resolution_evidence", sa.Text()),
        sa.Column("resolution_note", sa.Text()),
        sa.Column("resolved_by", sa.String(100)),
    )
    op.create_index("idx_override_history_contract", "override_history", ["contract_id"])

    op.create_table("exploit_records",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("contract_address", sa.String(42)),
        sa.Column("attacker_address", sa.String(42)),
        sa.Column("protocol_name", sa.String(200)),
        sa.Column("exploit_date", sa.Date()),
        sa.Column("loss_usd", sa.Numeric(20, 2)),
        sa.Column("description", sa.Text()),
        sa.Column("source_url", sa.Text()),
        sa.Column("is_resolved", sa.Boolean(), server_default="false"),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True)),
    )
    op.create_index("idx_exploit_contract", "exploit_records", ["contract_address"])

    op.create_table("ofac_addresses",
        sa.Column("address", sa.String(42), primary_key=True),
        sa.Column("name", sa.String(500)),
        sa.Column("program", sa.String(200)),
        sa.Column("last_updated", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("was_delisted", sa.Boolean(), server_default="false"),
        sa.Column("delisted_at", sa.TIMESTAMP(timezone=True)),
    )
    op.create_index("idx_ofac_address", "ofac_addresses", ["address"])

    op.create_table("audit_records",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("protocol_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("protocols.id")),
        sa.Column("contract_address", sa.String(42)),
        sa.Column("auditor", sa.String(200), nullable=False),
        sa.Column("auditor_tier", sa.Integer()),
        sa.Column("audit_date", sa.Date()),
        sa.Column("report_url", sa.Text()),
        sa.Column("critical_findings", sa.Integer(), server_default="0"),
        sa.Column("high_findings", sa.Integer(), server_default="0"),
        sa.Column("critical_resolved", sa.Boolean()),
        sa.Column("is_formal_verification", sa.Boolean(), server_default="false"),
        sa.CheckConstraint("auditor_tier IN (1, 2, 3)", name="ck_auditor_tier"),
    )

    op.create_table("api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("key_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("tier", sa.String(20), server_default="free"),
        sa.Column("owner_email", sa.String(200)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("last_used_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
    )

    op.create_table("watchlists",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=False),
        sa.Column("contract_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("contracts.id", ondelete="CASCADE")),
        sa.Column("threshold_score", sa.Numeric(5, 2)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("telegram_chat_id", "contract_id", name="uq_watchlist_chat_contract"),
    )
    op.create_index("idx_watchlists_chat", "watchlists", ["telegram_chat_id"])


def downgrade() -> None:
    op.drop_table("watchlists")
    op.drop_table("api_keys")
    op.drop_table("audit_records")
    op.drop_table("ofac_addresses")
    op.drop_table("exploit_records")
    op.drop_table("override_history")
    op.drop_table("score_reports")
    op.drop_table("contracts")
    op.drop_table("protocol_contracts")
    op.drop_table("protocols")
