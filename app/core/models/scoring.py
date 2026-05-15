from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SlitherFinding(BaseModel):
    """One vulnerability finding from Slither static analysis."""
    check: str                        # detector name e.g. "reentrancy-eth"
    impact: str                       # "High" | "Medium" | "Low" | "Informational"
    confidence: str                   # "High" | "Medium" | "Low"
    description: str                  # human readable summary
    elements: list[dict] = []         # affected functions/variables
    is_custom: bool = False           # True for our privacy-specific detectors
    amplifier: float = 1.0            # privacy context multiplier (1.0 = no amplification)


class CodeRiskResult(BaseModel):
    """Output of the code risk analyser for one contract."""
    address: str
    chain_id: int
    score: float                      # 0-100, higher = more risk
    is_verified: bool
    findings: list[SlitherFinding] = []
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    analysis_duration_seconds: float = 0.0
    error: Optional[str] = None       # set if Slither failed
    analysed_at: datetime = Field(default_factory=datetime.utcnow)


class OwnershipResult(BaseModel):
    """Output of the ownership/centralisation analyser."""
    address: str = ""
    chain_id: int = 0
    score: float                      # 0-100, higher = more risk
    owner_address: Optional[str] = None
    is_multisig: Optional[bool] = None
    has_timelock: Optional[bool] = None
    timelock_delay_hours: Optional[float] = None
    is_renounced: bool = False
    is_upgradeable: bool = False
    upgrade_pattern: Optional[str] = None   # "transparent" | "uups" | "beacon"
    flags: list[str] = []             # human-readable flag strings
    details: dict = {}                # full breakdown for API response
    error: Optional[str] = None
    analysed_at: datetime = Field(default_factory=datetime.utcnow)


class LiquidityResult(BaseModel):
    """Output of the liquidity/TVL analyser."""
    address: str
    chain_id: int
    score: float                      # 0-100, higher = more risk
    tvl_usd: Optional[float] = None
    tvl_source: str = "none"
    tvl_confidence: str = "none"
    tvl_tier: str = "unknown"         # "whale" | "large" | "medium" | "small" | "unknown"


class CompositeScore(BaseModel):
    """Final aggregated score for one contract."""
    address: str
    chain_id: int
    chain_slug: str
    composite_score: float            # 0-100
    grade: str                        # A | B | C | D | F
    code_risk: Optional[CodeRiskResult] = None
    ownership: Optional[OwnershipResult] = None
    liquidity: Optional[LiquidityResult] = None
    override_applied: bool = False
    override_status: Optional[str] = None
    recommendations: list[str] = []
    scored_at: datetime = Field(default_factory=datetime.utcnow)
