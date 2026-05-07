import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, BigInteger, CHAR, Column, Date, ForeignKey,
    Integer, Numeric, String, Text, TIMESTAMP, UniqueConstraint,
    CheckConstraint, ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class Protocol(Base):
    __tablename__ = "protocols"
    id             = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    name           = Column(String(200), nullable=False)
    slug           = Column(String(100), unique=True)
    defillama_slug = Column(String(100))
    description    = Column(Text)
    website_url    = Column(Text)
    github_url     = Column(Text)
    created_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    contracts      = relationship("ProtocolContract", back_populates="protocol")
    score_reports  = relationship("ScoreReport", back_populates="protocol")


class ProtocolContract(Base):
    __tablename__ = "protocol_contracts"
    __table_args__ = (UniqueConstraint("address", "chain_id"),)
    id            = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    protocol_id   = Column(UUID(as_uuid=False), ForeignKey("protocols.id"))
    address       = Column(String(42), nullable=False)
    chain_id      = Column(Integer, nullable=False)
    contract_role = Column(String(50), nullable=False)
    label         = Column(String(200))
    is_primary    = Column(Boolean, default=False)
    added_at      = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    protocol      = relationship("Protocol", back_populates="contracts")


class Contract(Base):
    __tablename__ = "contracts"
    __table_args__ = (UniqueConstraint("address", "chain_id"),)
    id             = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    address        = Column(String(42), nullable=False)
    chain_id       = Column(Integer, nullable=False)
    chain_name     = Column(String(50))
    protocol_id    = Column(UUID(as_uuid=False), ForeignKey("protocols.id"), nullable=True)
    scan_type      = Column(String(20), nullable=False, default="community")
    is_verified    = Column(Boolean, default=False)
    tvl_source     = Column(String(30))
    tvl_confidence = Column(String(20))
    first_seen_at  = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    last_scored_at = Column(TIMESTAMP(timezone=True))
    score_reports  = relationship("ScoreReport", back_populates="contract")
    watchlists     = relationship("Watchlist", back_populates="contract")


class ScoreReport(Base):
    __tablename__ = "score_reports"
    id               = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    contract_id      = Column(UUID(as_uuid=False), ForeignKey("contracts.id", ondelete="CASCADE"))
    protocol_id      = Column(UUID(as_uuid=False), ForeignKey("protocols.id"), nullable=True)
    composite_score  = Column(Numeric(5, 2), nullable=False)
    grade            = Column(CHAR(1), nullable=False)
    code_risk_score  = Column(Numeric(5, 2))
    ownership_score  = Column(Numeric(5, 2))
    liquidity_score  = Column(Numeric(5, 2))
    audit_score      = Column(Numeric(5, 2))
    compliance_score = Column(Numeric(5, 2))
    governance_score = Column(Numeric(5, 2))
    tvl_usd          = Column(Numeric(20, 2))
    tvl_confidence   = Column(String(20))
    tvl_source       = Column(String(30))
    override_applied = Column(Boolean, default=False)
    override_status  = Column(String(30))
    raw_findings     = Column(JSONB)
    recommendations  = Column(ARRAY(Text))
    score_version    = Column(String(10), default="1.0")
    scored_at        = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    contract         = relationship("Contract", back_populates="score_reports")
    protocol         = relationship("Protocol", back_populates="score_reports")


class OverrideHistory(Base):
    __tablename__ = "override_history"
    id                  = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    contract_id         = Column(UUID(as_uuid=False), ForeignKey("contracts.id"))
    protocol_id         = Column(UUID(as_uuid=False), ForeignKey("protocols.id"))
    override_type       = Column(String(20), nullable=False)
    override_status     = Column(String(20), nullable=False)
    applied_at          = Column(TIMESTAMP(timezone=True), nullable=False)
    resolved_at         = Column(TIMESTAMP(timezone=True))
    resolution_type     = Column(String(30))
    resolution_evidence = Column(Text)
    resolution_note     = Column(Text)
    resolved_by         = Column(String(100))


class ExploitRecord(Base):
    __tablename__ = "exploit_records"
    id               = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    contract_address = Column(String(42))
    attacker_address = Column(String(42))
    protocol_name    = Column(String(200))
    exploit_date     = Column(Date)
    loss_usd         = Column(Numeric(20, 2))
    description      = Column(Text)
    source_url       = Column(Text)
    is_resolved      = Column(Boolean, default=False)
    resolved_at      = Column(TIMESTAMP(timezone=True))


class OfacAddress(Base):
    __tablename__ = "ofac_addresses"
    address      = Column(String(42), primary_key=True)
    name         = Column(String(500))
    program      = Column(String(200))
    last_updated = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    was_delisted = Column(Boolean, default=False)
    delisted_at  = Column(TIMESTAMP(timezone=True))


class AuditRecord(Base):
    __tablename__ = "audit_records"
    __table_args__ = (CheckConstraint("auditor_tier IN (1, 2, 3)", name="ck_auditor_tier"),)
    id                     = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    protocol_id            = Column(UUID(as_uuid=False), ForeignKey("protocols.id"))
    contract_address       = Column(String(42))
    auditor                = Column(String(200), nullable=False)
    auditor_tier           = Column(Integer)
    audit_date             = Column(Date)
    report_url             = Column(Text)
    critical_findings      = Column(Integer, default=0)
    high_findings          = Column(Integer, default=0)
    critical_resolved      = Column(Boolean)
    is_formal_verification = Column(Boolean, default=False)


class ApiKey(Base):
    __tablename__ = "api_keys"
    id           = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    key_hash     = Column(String(64), unique=True, nullable=False)
    tier         = Column(String(20), default="free")
    owner_email  = Column(String(200))
    created_at   = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    last_used_at = Column(TIMESTAMP(timezone=True))
    is_active    = Column(Boolean, default=True)


class Watchlist(Base):
    __tablename__ = "watchlists"
    __table_args__ = (UniqueConstraint("telegram_chat_id", "contract_id"),)
    id               = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    telegram_chat_id = Column(BigInteger, nullable=False)
    contract_id      = Column(UUID(as_uuid=False), ForeignKey("contracts.id", ondelete="CASCADE"))
    threshold_score  = Column(Numeric(5, 2))
    created_at       = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    contract         = relationship("Contract", back_populates="watchlists")
