"""
Etherscan v2 API client.
v2 uses a single endpoint with chainid param — works for all 7 supported chains.
Docs: https://docs.etherscan.io/etherscan-v2
"""

import structlog
from app.core.clients.base import BaseClient
from app.core.clients.chains import get_chain
from app.core.models.contract import (
    SourceCodeResult,
    ContractCreationResult,
    BytecodeResult,
)
from app.config import settings

log = structlog.get_logger()

ETHERSCAN_API_URL = "https://api.etherscan.io/v2/api"


class EtherscanClient(BaseClient):
    base_url = ETHERSCAN_API_URL

    def __init__(self):
        super().__init__()
        self._api_key = settings.etherscan_api_key

    def _base_params(self, chain_id: int) -> dict:
        return {
            "chainid": chain_id,
            "apikey": self._api_key,
        }

    async def get_source_code(self, address: str, chain_slug: str) -> SourceCodeResult:
        """
        Fetch verified source code, ABI, proxy info.
        Returns is_verified=False if contract is not verified on Etherscan.
        """
        chain = get_chain(chain_slug)
        params = {
            **self._base_params(chain.chain_id),
            "module": "contract",
            "action": "getsourcecode",
            "address": address,
        }

        log.info("etherscan.get_source_code", address=address, chain=chain_slug)
        data = await self.get("", params=params)

        if data.get("status") != "1" or not data.get("result"):
            log.warning("etherscan.not_verified", address=address, chain=chain_slug)
            return SourceCodeResult(
                address=address,
                chain_id=chain.chain_id,
                is_verified=False,
            )

        r = data["result"][0]
        source = r.get("SourceCode", "")
        is_verified = bool(source and source != "")

        # Detect proxy — Etherscan returns proxy info in the result
        is_proxy = r.get("Proxy", "0") == "1"
        impl = r.get("Implementation", "") or None

        return SourceCodeResult(
            address=address,
            chain_id=chain.chain_id,
            is_verified=is_verified,
            source_code=source if is_verified else None,
            abi=r.get("ABI") if r.get("ABI") != "Contract source code not verified" else None,
            contract_name=r.get("ContractName") or None,
            compiler_version=r.get("CompilerVersion") or None,
            optimization_used=r.get("OptimizationUsed", "0") == "1",
            runs=int(r["Runs"]) if r.get("Runs", "").isdigit() else None,
            evm_version=r.get("EVMVersion") or None,
            license_type=r.get("LicenseType") or None,
            is_proxy=is_proxy,
            implementation_address=impl,
        )

    async def get_contract_creation(
        self, address: str, chain_slug: str
    ) -> ContractCreationResult:
        """Fetch deployer address and creation tx hash."""
        chain = get_chain(chain_slug)
        params = {
            **self._base_params(chain.chain_id),
            "module": "contract",
            "action": "getcontractcreation",
            "contractaddresses": address,
        }

        log.info("etherscan.get_creation", address=address, chain=chain_slug)
        data = await self.get("", params=params)

        if data.get("status") != "1" or not data.get("result"):
            return ContractCreationResult(address=address)

        r = data["result"][0]
        return ContractCreationResult(
            address=address,
            creator_address=r.get("contractCreator"),
            creation_tx_hash=r.get("txHash"),
        )

    async def get_abi(self, address: str, chain_slug: str) -> str | None:
        """Fetch ABI only — lighter call when source not needed."""
        chain = get_chain(chain_slug)
        params = {
            **self._base_params(chain.chain_id),
            "module": "contract",
            "action": "getabi",
            "address": address,
        }

        data = await self.get("", params=params)
        if data.get("status") != "1":
            return None
        return data.get("result")


# Module-level singleton — import and use directly
etherscan_client = EtherscanClient()
