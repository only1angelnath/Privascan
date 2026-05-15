"""
Alchemy RPC client.
Uses eth_call to read owner(), paused(), admin() from contracts.
Uses eth_getStorageAt for EIP-1967 proxy implementation slot.
Single API key works across all chains via different subdomain prefixes.
"""

import structlog
from app.core.clients.base import BaseClient
from app.core.clients.chains import get_chain
from app.core.models.contract import OnChainState, BytecodeResult
from app.config import settings

log = structlog.get_logger()

# EIP-1967 implementation slot
EIP1967_IMPL_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"

# Common function selectors
SELECTOR_OWNER   = "0x8da5cb5b"   # owner()
SELECTOR_ADMIN   = "0xf851a440"   # admin()
SELECTOR_PAUSED  = "0x5c975abb"   # paused()


def _rpc_url(chain_slug: str) -> str:
    chain = get_chain(chain_slug)
    return f"https://{chain.alchemy_prefix}.g.alchemy.com/v2/{settings.alchemy_api_key}"


class AlchemyClient(BaseClient):

    def __init__(self):
        super().__init__()

    async def _rpc_call(self, chain_slug: str, method: str, params: list) -> dict:
        url = _rpc_url(chain_slug)
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
        return await self.post(url, json=payload)

    async def get_bytecode(self, address: str, chain_slug: str) -> BytecodeResult:
        """Fetch raw bytecode — used to detect EOAs and undeployed addresses."""
        chain = get_chain(chain_slug)
        log.info("alchemy.get_bytecode", address=address, chain=chain_slug)

        resp = await self._rpc_call(chain_slug, "eth_getCode", [address, "latest"])
        bytecode = resp.get("result", "0x")

        return BytecodeResult(
            address=address,
            chain_id=chain.chain_id,
            bytecode=bytecode,
            is_eoa=bytecode in ("0x", "0x0", ""),
        )

    async def get_on_chain_state(self, address: str, chain_slug: str) -> OnChainState:
        """
        Read owner(), admin(), paused() via eth_call.
        EIP-1967 implementation slot via eth_getStorageAt.
        Gracefully returns None for any field the contract doesn't implement.
        """
        chain = get_chain(chain_slug)
        log.info("alchemy.get_on_chain_state", address=address, chain=chain_slug)

        owner = await self._eth_call_address(chain_slug, address, SELECTOR_OWNER)
        admin = await self._eth_call_address(chain_slug, address, SELECTOR_ADMIN)
        paused = await self._eth_call_bool(chain_slug, address, SELECTOR_PAUSED)
        impl = await self._get_eip1967_impl(chain_slug, address)
        balance = await self._get_balance(chain_slug, address)

        return OnChainState(
            address=address,
            chain_id=chain.chain_id,
            owner=owner,
            admin=admin,
            is_paused=paused,
            eth_balance_wei=balance,
            implementation=impl,
        )

    async def _eth_call_address(
        self, chain_slug: str, to: str, selector: str
    ) -> str | None:
        """Make an eth_call and decode a returned address (32-byte padded)."""
        try:
            resp = await self._rpc_call(
                chain_slug,
                "eth_call",
                [{"to": to, "data": selector}, "latest"],
            )
            result = resp.get("result", "0x")
            if result and result != "0x" and len(result) >= 66:
                # Last 20 bytes of 32-byte return value = address
                addr = "0x" + result[-40:]
                # Filter out zero address
                if addr != "0x" + "0" * 40:
                    return addr
        except Exception:
            pass
        return None

    async def _eth_call_bool(
        self, chain_slug: str, to: str, selector: str
    ) -> bool | None:
        """Make an eth_call and decode a returned bool."""
        try:
            resp = await self._rpc_call(
                chain_slug,
                "eth_call",
                [{"to": to, "data": selector}, "latest"],
            )
            result = resp.get("result", "0x")
            if result and result != "0x":
                return result.endswith("1")
        except Exception:
            pass
        return None

    async def _get_eip1967_impl(self, chain_slug: str, address: str) -> str | None:
        """Read EIP-1967 implementation slot directly from storage."""
        try:
            resp = await self._rpc_call(
                chain_slug,
                "eth_getStorageAt",
                [address, EIP1967_IMPL_SLOT, "latest"],
            )
            result = resp.get("result", "0x")
            if result and result != "0x" and result != "0x" + "0" * 64:
                return "0x" + result[-40:]
        except Exception:
            pass
        return None

    async def _get_balance(self, chain_slug: str, address: str) -> int | None:
        """Get ETH balance in wei."""
        try:
            resp = await self._rpc_call(
                chain_slug,
                "eth_getBalance",
                [address, "latest"],
            )
            result = resp.get("result", "0x0")
            return int(result, 16)
        except Exception:
            pass
        return None


# Module-level singleton
alchemy_client = AlchemyClient()
