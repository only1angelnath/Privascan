"""
Pydantic schemas for raw contract data fetched from external APIs.
These are NOT ORM models — they're typed data transfer objects (DTOs).
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SourceCodeResult(BaseModel):
    """Etherscan getSourceCode response."""
    address: str
    chain_id: int
    is_verified: bool
    source_code: Optional[str] = None
    abi: Optional[str] = None          # raw JSON string
    contract_name: Optional[str] = None
    compiler_version: Optional[str] = None
    optimization_used: bool = False
    runs: Optional[int] = None
    evm_version: Optional[str] = None
    license_type: Optional[str] = None
    is_proxy: bool = False
    implementation_address: Optional[str] = None  # if proxy


class ContractCreationResult(BaseModel):
    """Etherscan getContractCreation response."""
    address: str
    creator_address: Optional[str] = None
    creation_tx_hash: Optional[str] = None
    created_at_block: Optional[int] = None


class BytecodeResult(BaseModel):
    """Raw bytecode from RPC eth_getCode."""
    address: str
    chain_id: int
    bytecode: str          # hex string
    is_eoa: bool           # True if bytecode == "0x"


class OnChainState(BaseModel):
    """Ownership + admin data fetched via Alchemy RPC."""
    address: str
    chain_id: int
    owner: Optional[str] = None          # from owner() call
    admin: Optional[str] = None          # from admin() / getAdmin()
    is_paused: Optional[bool] = None     # from paused()
    eth_balance_wei: Optional[int] = None
    implementation: Optional[str] = None # EIP-1967 proxy slot


class TvlResult(BaseModel):
    """TVL data from DefiLlama or Dune SIM."""
    protocol_slug: Optional[str] = None
    contract_address: Optional[str] = None
    chain: Optional[str] = None
    tvl_usd: Optional[float] = None
    source: str                           # "defillama" | "dune_sim" | "none"
    confidence: str                       # "high" | "medium" | "low" | "none"
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class RawContractData(BaseModel):
    """
    Aggregated raw data for one contract — passed to the scoring engine.
    All fields optional because community scans may have partial data.
    """
    address: str
    chain_id: int
    chain_slug: str

    source: Optional[SourceCodeResult] = None
    creation: Optional[ContractCreationResult] = None
    bytecode: Optional[BytecodeResult] = None
    on_chain: Optional[OnChainState] = None
    tvl: Optional[TvlResult] = None

    # Populated by scoring engine later
    slither_findings: Optional[dict] = None
