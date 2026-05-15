"""
Supported chains — maps slug names to chain IDs, Etherscan endpoints,
Alchemy RPC base URLs, and DefiLlama chain names.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ChainConfig:
    chain_id: int
    name: str                    # human label
    alchemy_prefix: str          # e.g. "eth-mainnet" → rpc.alchemy.com/v2
    etherscan_api_url: str       # Etherscan-compatible API root
    defillama_name: str          # as used in DefiLlama API
    native_symbol: str


CHAINS: dict[str, ChainConfig] = {
    "ethereum": ChainConfig(
        chain_id=1,
        name="Ethereum",
        alchemy_prefix="eth-mainnet",
        etherscan_api_url="https://api.etherscan.io/v2/api",
        defillama_name="ethereum",
        native_symbol="ETH",
    ),
    "polygon": ChainConfig(
        chain_id=137,
        name="Polygon",
        alchemy_prefix="polygon-mainnet",
        etherscan_api_url="https://api.etherscan.io/v2/api",
        defillama_name="polygon",
        native_symbol="MATIC",
    ),
    "arbitrum": ChainConfig(
        chain_id=42161,
        name="Arbitrum One",
        alchemy_prefix="arb-mainnet",
        etherscan_api_url="https://api.etherscan.io/v2/api",
        defillama_name="arbitrum",
        native_symbol="ETH",
    ),
    "optimism": ChainConfig(
        chain_id=10,
        name="Optimism",
        alchemy_prefix="opt-mainnet",
        etherscan_api_url="https://api.etherscan.io/v2/api",
        defillama_name="optimism",
        native_symbol="ETH",
    ),
    "base": ChainConfig(
        chain_id=8453,
        name="Base",
        alchemy_prefix="base-mainnet",
        etherscan_api_url="https://api.etherscan.io/v2/api",
        defillama_name="base",
        native_symbol="ETH",
    ),
    "bnb": ChainConfig(
        chain_id=56,
        name="BNB Chain",
        alchemy_prefix="bnb-mainnet",
        etherscan_api_url="https://api.etherscan.io/v2/api",
        defillama_name="bsc",
        native_symbol="BNB",
    ),
    "avalanche": ChainConfig(
        chain_id=43114,
        name="Avalanche",
        alchemy_prefix="avax-mainnet",
        etherscan_api_url="https://api.etherscan.io/v2/api",
        defillama_name="avax",
        native_symbol="AVAX",
    ),
}

# Reverse lookup: chain_id → slug
CHAIN_ID_TO_SLUG: dict[int, str] = {v.chain_id: k for k, v in CHAINS.items()}


def get_chain(slug: str) -> ChainConfig:
    """Return ChainConfig or raise ValueError for unknown chain."""
    if slug not in CHAINS:
        supported = ", ".join(CHAINS.keys())
        raise ValueError(f"Unsupported chain '{slug}'. Supported: {supported}")
    return CHAINS[slug]
