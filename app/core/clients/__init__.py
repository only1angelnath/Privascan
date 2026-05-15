from app.core.clients.etherscan import etherscan_client
from app.core.clients.alchemy import alchemy_client
from app.core.clients.defillama import defillama_client
from app.core.clients.dune import dune_sim_client
from app.core.clients.collector import collect_contract_data

__all__ = [
    "etherscan_client",
    "alchemy_client",
    "defillama_client",
    "dune_sim_client",
    "collect_contract_data",
]
