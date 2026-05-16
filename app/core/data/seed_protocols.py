"""
Protocol Registry Seed

13 protocols — all addresses verified directly from the PRD document.

Removed per spec: Nocturne, Tornado Cash Nova, Typhoon Cash, zkBob,
                  Sherpa Cash, Nocturne v2, Secret Network, Silent Protocol
Added per spec:   AnomaPay, Horizen

Chains in our system (7):
  ethereum, polygon, arbitrum, optimism, base, bnb, avalanche

NOTE: Gnosis/xDAI and Ethereum Classic (ETC) are NOT in our 7-chain list.
      Those TC pool contracts are logged as skipped (unknown_chain).
      Add them to CHAINS config when Gnosis/ETC support is added.

Run once (idempotent — skips existing slugs):
  docker compose exec worker python3 -m app.core.data.seed_protocols
"""

import logging
from app.db.session import get_sync_session
from app.db.models import Protocol, ProtocolContract
from app.core.clients.chains import CHAINS

log = logging.getLogger(__name__)

_CID = {slug: cfg.chain_id for slug, cfg in CHAINS.items()}

PROTOCOLS = [

    # ──────────────────────────────────────────────────────────────────────────
    # 1. TORNADO CASH
    # Source: PRD §Tornado Cash
    # Supported chains: ethereum, arbitrum, optimism, bnb, polygon, avalanche
    # Skipped (not in our 7): gnosis/xDAI, ethereum classic (ETC)
    # ──────────────────────────────────────────────────────────────────────────
    {
        "name": "Tornado Cash",
        "slug": "tornado-cash",
        "defillama_slug": "tornado-cash",
        "description": "Non-custodial zk-SNARK privacy mixer. ETH, DAI, cDAI, USDC, USDT, and WBTC pools across 6 EVM chains.",
        "website_url": "https://tornado.cash",
        "github_url": "https://github.com/tornadocash",
        "contracts": [
            # ── Ethereum — ETH pools ──────────────────────────────────────────
            {"address": "0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc", "chain": "ethereum",  "role": "pool",       "label": "TC ETH 0.1",          "is_primary": False},
            {"address": "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936", "chain": "ethereum",  "role": "pool",       "label": "TC ETH 1",            "is_primary": False},
            {"address": "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf", "chain": "ethereum",  "role": "pool",       "label": "TC ETH 10",           "is_primary": False},
            {"address": "0xa160cdab225685da1d56aa342ad8841c3b53f291", "chain": "ethereum",  "role": "pool",       "label": "TC ETH 100",          "is_primary": True},
            # ── Ethereum — DAI pools ──────────────────────────────────────────
            {"address": "0xd4b88df4d29f5cedd6857912842cff3b20c8cfa3", "chain": "ethereum",  "role": "pool",       "label": "TC DAI 100",          "is_primary": False},
            {"address": "0xfd8610d20aa15b7b2e3be39b396a1bc3516c7144", "chain": "ethereum",  "role": "pool",       "label": "TC DAI 1000",         "is_primary": False},
            {"address": "0x07687e702b410fa43f4cb4af7fa097918ffd2730", "chain": "ethereum",  "role": "pool",       "label": "TC DAI 10000",        "is_primary": False},
            {"address": "0x23773e65ed146a459791799d01336db287f25334", "chain": "ethereum",  "role": "pool",       "label": "TC DAI 100000",       "is_primary": False},
            # ── Ethereum — cDAI pools ─────────────────────────────────────────
            {"address": "0x22aaa7720ddd5388a3c0a3333430953c68f1849b", "chain": "ethereum",  "role": "pool",       "label": "TC cDAI 5000",        "is_primary": False},
            {"address": "0x03893a7c7463ae47d46bc7f091665f1893656003", "chain": "ethereum",  "role": "pool",       "label": "TC cDAI 50000",       "is_primary": False},
            {"address": "0x2717c5e28cf931547b621a5dddb772ab6a35b701", "chain": "ethereum",  "role": "pool",       "label": "TC cDAI 500000",      "is_primary": False},
            {"address": "0xd21be7248e0197ee08e0c20d4a96debdac3d20af", "chain": "ethereum",  "role": "pool",       "label": "TC cDAI 5000000",     "is_primary": False},
            # ── Ethereum — USDC pools ─────────────────────────────────────────
            {"address": "0x4736dcf1b7a3d580672cce6e7c65cd5cc9cfba9d", "chain": "ethereum",  "role": "pool",       "label": "TC USDC 100",         "is_primary": False},
            {"address": "0xd96f2b1c14db8458374d9aca76e26c3d18364307", "chain": "ethereum",  "role": "pool",       "label": "TC USDC 1000",        "is_primary": False},
            # ── Ethereum — USDT pools ─────────────────────────────────────────
            {"address": "0x169ad27a470d064dede56a2d3ff727986b15d52b", "chain": "ethereum",  "role": "pool",       "label": "TC USDT 100",         "is_primary": False},
            {"address": "0x0836222f2b2b24a3f36f98668ed8f0b38d1a872f", "chain": "ethereum",  "role": "pool",       "label": "TC USDT 1000",        "is_primary": False},
            # ── Ethereum — WBTC pools ─────────────────────────────────────────
            {"address": "0x178169b423a011fff22b9e3f3abea13414ddd0f1", "chain": "ethereum",  "role": "pool",       "label": "TC WBTC 0.1",         "is_primary": False},
            {"address": "0x610b717796ad172b316836ac95a2ffad065ceab4", "chain": "ethereum",  "role": "pool",       "label": "TC WBTC 1",           "is_primary": False},
            {"address": "0xbb93e510bbcd0b7beb5a853875f9ec60275cf498", "chain": "ethereum",  "role": "pool",       "label": "TC WBTC 10",          "is_primary": False},
            # ── Ethereum — core contracts ─────────────────────────────────────
            {"address": "0x5efda50f22d34f262c29268506c5fa42cb56a1ce", "chain": "ethereum",  "role": "treasury",   "label": "TC Treasury",         "is_primary": False},
            {"address": "0x179f48c78f57a3a78f0608cc9197b8972921d1d2", "chain": "ethereum",  "role": "other",      "label": "TC Vesting",          "is_primary": False},
            {"address": "0x77777feddddFfC19ff86db637967013e6c6a116c", "chain": "ethereum",  "role": "token",      "label": "TORN Token",          "is_primary": False},
            # ── Arbitrum — ETH pools ──────────────────────────────────────────
            {"address": "0x84443cfd09a48af6ef360c6976c5392ac5023a1f", "chain": "arbitrum",  "role": "pool",       "label": "TC ETH 0.1 ARB",      "is_primary": False},
            {"address": "0xd47438c816c9e7f2e2888e060936a499af9582b3", "chain": "arbitrum",  "role": "pool",       "label": "TC ETH 1 ARB",        "is_primary": False},
            {"address": "0x330bdfade01ee9bf63c209ee33102dd334618e0a", "chain": "arbitrum",  "role": "pool",       "label": "TC ETH 10 ARB",       "is_primary": False},
            {"address": "0x1e34a77868e19a6647b1f2f47b51ed72dede95dd", "chain": "arbitrum",  "role": "pool",       "label": "TC ETH 100 ARB",      "is_primary": False},
            # ── Optimism — ETH pools ──────────────────────────────────────────
            {"address": "0x84443cfd09a48af6ef360c6976c5392ac5023a1f", "chain": "optimism",  "role": "pool",       "label": "TC ETH 0.1 OP",       "is_primary": False},
            {"address": "0xd47438c816c9e7f2e2888e060936a499af9582b3", "chain": "optimism",  "role": "pool",       "label": "TC ETH 1 OP",         "is_primary": False},
            {"address": "0x330bdfade01ee9bf63c209ee33102dd334618e0a", "chain": "optimism",  "role": "pool",       "label": "TC ETH 10 OP",        "is_primary": False},
            {"address": "0x1e34a77868e19a6647b1f2f47b51ed72dede95dd", "chain": "optimism",  "role": "pool",       "label": "TC ETH 100 OP",       "is_primary": False},
            # ── BNB Chain — BNB pools ─────────────────────────────────────────
            {"address": "0x84443cfd09a48af6ef360c6976c5392ac5023a1f", "chain": "bnb",       "role": "pool",       "label": "TC BNB 0.1",          "is_primary": False},
            {"address": "0xd47438c816c9e7f2e2888e060936a499af9582b3", "chain": "bnb",       "role": "pool",       "label": "TC BNB 1",            "is_primary": False},
            {"address": "0x330bdfade01ee9bf63c209ee33102dd334618e0a", "chain": "bnb",       "role": "pool",       "label": "TC BNB 10",           "is_primary": False},
            {"address": "0x1e34a77868e19a6647b1f2f47b51ed72dede95dd", "chain": "bnb",       "role": "pool",       "label": "TC BNB 100",          "is_primary": False},
            # ── Polygon — MATIC pools ─────────────────────────────────────────
            {"address": "0x1e34a77868e19a6647b1f2f47b51ed72dede95dd", "chain": "polygon",   "role": "pool",       "label": "TC MATIC 100",        "is_primary": False},
            {"address": "0xdf231d99ff8b6c6cbf4e9b9a945cbacef9339178", "chain": "polygon",   "role": "pool",       "label": "TC MATIC 1000",       "is_primary": False},
            {"address": "0xaf4c0b70b2ea9fb7487c7cbb37ada259579fe040", "chain": "polygon",   "role": "pool",       "label": "TC MATIC 10000",      "is_primary": False},
            {"address": "0xa5c2254e4253490c54cef0a4347fddb8f75a4998", "chain": "polygon",   "role": "pool",       "label": "TC MATIC 100000",     "is_primary": False},
            # ── Avalanche — AVAX pools ────────────────────────────────────────
            {"address": "0x330bdfade01ee9bf63c209ee33102dd334618e0a", "chain": "avalanche", "role": "pool",       "label": "TC AVAX 10",          "is_primary": False},
            {"address": "0x1e34a77868e19a6647b1f2f47b51ed72dede95dd", "chain": "avalanche", "role": "pool",       "label": "TC AVAX 100",         "is_primary": False},
            {"address": "0xaf8d1839c3c67cf571aa74b5c12398d4901147b3", "chain": "avalanche", "role": "pool",       "label": "TC AVAX 500",         "is_primary": False},
            # NOTE: Gnosis/xDAI + ETC pools omitted — not in our 7-chain set
        ],
    },

    # ──────────────────────────────────────────────────────────────────────────
    # 2. RAILGUN
    # Source: PRD §Railgun Protocol
    # Chains: ethereum, bnb, polygon, arbitrum
    # ──────────────────────────────────────────────────────────────────────────
    {
        "name": "Railgun",
        "slug": "railgun",
        "defillama_slug": "railgun",
        "description": "ZK shielded privacy system. Private DeFi interactions via shielded pools on 4 EVM chains.",
        "website_url": "https://railgun.org",
        "github_url": "https://github.com/Railgun-Community",
        "contracts": [
            # Ethereum
            {"address": "0xee6a649aa3766bd117e12c161726b693a1b2ee20", "chain": "ethereum",  "role": "other",      "label": "RAIL Staking",               "is_primary": False},
            {"address": "0xe76c6c83af64e4c60245d8c7de953df673a7a33d", "chain": "ethereum",  "role": "token",      "label": "RAIL Token ETH",             "is_primary": False},
            {"address": "0xfa7093cdd9ee6932b4eb2c9e1cde7ce00b1fa4b9", "chain": "ethereum",  "role": "pool",       "label": "RailgunSmartWallet ETH",     "is_primary": True},
            {"address": "0xe8a8b458bcd1ececc6b6b58f80929b29ccecff40", "chain": "ethereum",  "role": "treasury",   "label": "Treasury ETH",               "is_primary": False},
            # BNB Chain
            {"address": "0x3f847b01d4d498a293e3197b186356039ecd737f", "chain": "bnb",       "role": "token",      "label": "RAIL Token BSC",             "is_primary": False},
            {"address": "0x590162bf4b50f6576a459b75309ee21d92178a10", "chain": "bnb",       "role": "pool",       "label": "RailgunSmartWallet BSC",     "is_primary": False},
            {"address": "0xdca05161ee5b5fa6df170191c88857e70ffb4094", "chain": "bnb",       "role": "treasury",   "label": "Treasury BSC",               "is_primary": False},
            # Polygon
            {"address": "0x92a9c92c215092720c731c96d4ff508c831a714f", "chain": "polygon",   "role": "token",      "label": "RAIL Token Polygon",         "is_primary": False},
            {"address": "0x19b620929f97b7b990801496c3b361ca5def8c71", "chain": "polygon",   "role": "pool",       "label": "RailgunSmartWallet Polygon", "is_primary": False},
            {"address": "0xdca05161ee5b5fa6df170191c88857e70ffb4094", "chain": "polygon",   "role": "treasury",   "label": "Treasury Polygon",           "is_primary": False},
            # Arbitrum
            {"address": "0xfa7093cdd9ee6932b4eb2c9e1cde7ce00b1fa4b9", "chain": "arbitrum",  "role": "pool",       "label": "RailgunSmartWallet ARB",     "is_primary": False},
            {"address": "0x3b374464a714525498e445ba050b91571937bfc8", "chain": "arbitrum",  "role": "treasury",   "label": "Treasury ARB",               "is_primary": False},
        ],
    },

    # ──────────────────────────────────────────────────────────────────────────
    # 3. AZTEC
    # Source: PRD §Aztec Protocol
    # Chain: ethereum
    # ──────────────────────────────────────────────────────────────────────────
    {
        "name": "Aztec",
        "slug": "aztec",
        "defillama_slug": "aztec",
        "description": "ZK-rollup for private DeFi on Ethereum. Rollup processor, governance, staking, and registry infrastructure.",
        "website_url": "https://aztec.network",
        "github_url": "https://github.com/AztecProtocol",
        "contracts": [
            {"address": "0x737901bea3eeb88459df9ef1be8ff3ae1b42a2ba", "chain": "ethereum",  "role": "pool",       "label": "aztecRollupProcessor",        "is_primary": True},
            {"address": "0xff1f2b4adb9df6fc8eafecdcbf96a2b351680455", "chain": "ethereum",  "role": "pool",       "label": "aztecConnect",                "is_primary": False},
            {"address": "0xa27ec0006e59f245217ff08cd52a7e8b169e62d2", "chain": "ethereum",  "role": "token",      "label": "AZTEC Token",                 "is_primary": False},
            {"address": "0x1102471eb3378fee427121c9efcea452e4b6b75e", "chain": "ethereum",  "role": "governance", "label": "AZTEC Governance",            "is_primary": False},
            {"address": "0x662de311f94bdbb571d95b5909e9cc6a25a6802a", "chain": "ethereum",  "role": "treasury",   "label": "Aztec Treasury",              "is_primary": False},
            {"address": "0x3d6a1b00c830c5f278fc5dfb3f6ff0b74db6dfe0", "chain": "ethereum",  "role": "other",      "label": "Aztec Reward Distributor",    "is_primary": False},
            {"address": "0xae2001f7e21d5ecabf6234e9fdd1e76f50f74962", "chain": "ethereum",  "role": "pool",       "label": "Aztec Rollup",                "is_primary": False},
            {"address": "0x35b22e09ee0390539439e24f06da43d83f90e298", "chain": "ethereum",  "role": "other",      "label": "Aztec Registry",              "is_primary": False},
            {"address": "0xa92ecfd0e70c9cd5e5cd76c50af0f7da93567a4f", "chain": "ethereum",  "role": "other",      "label": "Aztec GSE Staking Manager",   "is_primary": False},
            {"address": "0x41a57f5581adF11b25f3edb7c1db19f18bb76734", "chain": "ethereum",  "role": "other",      "label": "Aztec Fee Distributor",       "is_primary": False},
            {"address": "0x603bb2c05d474794ea97805e8de69bccfb3bca12", "chain": "ethereum",  "role": "pool",       "label": "Rollup",                      "is_primary": False},
            {"address": "0x042df8f42790d6943f41c25c2132400fd727f452", "chain": "ethereum",  "role": "other",      "label": "Staking Registry",            "is_primary": False},
        ],
    },

    # ──────────────────────────────────────────────────────────────────────────
    # 4. PRIVACY POOLS
    # Source: PRD §Privacy Pools Protocol
    # Chains: ethereum, arbitrum, optimism, bnb
    # ──────────────────────────────────────────────────────────────────────────
    {
        "name": "Privacy Pools",
        "slug": "privacy-pools",
        "defillama_slug": "privacy-pools",
        "description": "Compliance-first privacy mixer with cryptographic association sets. Vitalik-co-authored.",
        "website_url": "https://privacypools.com/",
        "github_url": "https://github.com/ameensol/privacy-pools",
        "contracts": [
            # Ethereum
            {"address": "0x6818809eefce719e480a7526d76bd3e561526b46", "chain": "ethereum",  "role": "pool",  "label": "Entrypoint ETH",        "is_primary": True},
            {"address": "0xf241d57c6debae225c0f2e6ea1529373c9a9c9fb", "chain": "ethereum",  "role": "pool",  "label": "PrivacyPoolSimple ETH", "is_primary": False},
            # Arbitrum
            {"address": "0x44192215fed782896be2ce24e0bfbf0bf825d15e", "chain": "arbitrum",  "role": "pool",  "label": "Entrypoint ARB",        "is_primary": False},
            # Optimism
            {"address": "0x44192215fed782896be2ce24e0bfbf0bf825d15e", "chain": "optimism",  "role": "pool",  "label": "Entrypoint OP",         "is_primary": False},
            # BNB Chain
            {"address": "0x44192215fed782896be2ce24e0bfbf0bf825d15e", "chain": "bnb",       "role": "pool",  "label": "Entrypoint BSC",        "is_primary": False},
        ],
    },

    # ──────────────────────────────────────────────────────────────────────────
    # 5. HINKAL
    # Source: PRD §Hinkal
    # Chains: ethereum, arbitrum, polygon, optimism, base
    # Note: Optimism legacy address in PRD is truncated (39 chars) — skipped.
    # ──────────────────────────────────────────────────────────────────────────
    {
        "name": "Hinkal",
        "slug": "hinkal",
        "defillama_slug": "hinkal",
        "description": "ZK privacy layer and wallet abstraction system. Core + wallet + helper + logic contracts on 5 EVM chains.",
        "website_url": "https://hinkal.pro",
        "github_url": "https://github.com/Hinkal-Protocol",
        "contracts": [
            # Core (shared across all chains)
            {"address": "0x25e5e82f5702a27c3466fe68f14abdbbadfca826", "chain": "ethereum",  "role": "pool",   "label": "Hinkal Core ETH",         "is_primary": True},
            {"address": "0x25e5e82f5702a27c3466fe68f14abdbbadfca826", "chain": "polygon",   "role": "pool",   "label": "Hinkal Core Polygon",     "is_primary": False},
            {"address": "0x25e5e82f5702a27c3466fe68f14abdbbadfca826", "chain": "optimism",  "role": "pool",   "label": "Hinkal Core OP",          "is_primary": False},
            {"address": "0x25e5e82f5702a27c3466fe68f14abdbbadfca826", "chain": "base",      "role": "pool",   "label": "Hinkal Core Base",        "is_primary": False},
            {"address": "0x25e5e82f5702a27c3466fe68f14abdbbadfca826", "chain": "arbitrum",  "role": "pool",   "label": "Hinkal Core ARB",         "is_primary": False},
            # Wallet contracts (chain-specific)
            {"address": "0xab6363ebc7b2b769938eaa22909da533a9f1ee52", "chain": "ethereum",  "role": "other",  "label": "Hinkal Wallet ETH",       "is_primary": False},
            {"address": "0x5332c70a98ff45d16098e25f2d69971ce46de395", "chain": "polygon",   "role": "other",  "label": "Hinkal Wallet Polygon",   "is_primary": False},
            {"address": "0xf95e20d23262ad4be6b3c1d9930098443fe23482", "chain": "optimism",  "role": "other",  "label": "Hinkal Wallet OP",        "is_primary": False},
            {"address": "0xd079adceaec7276f693a097248246da6ac581a19", "chain": "base",      "role": "other",  "label": "Hinkal Wallet Base",      "is_primary": False},
            {"address": "0x27e94345eacb931fce5b9645f078368ddb67eca8", "chain": "arbitrum",  "role": "other",  "label": "Hinkal Wallet ARB",       "is_primary": False},
            # Logic contract (shared)
            {"address": "0x6d29a6e451c541cf2b94382c56b853d2d6d80469", "chain": "ethereum",  "role": "other",  "label": "HinkalInLogic ETH",       "is_primary": False},
            {"address": "0x6d29a6e451c541cf2b94382c56b853d2d6d80469", "chain": "polygon",   "role": "other",  "label": "HinkalInLogic Polygon",   "is_primary": False},
            {"address": "0x6d29a6e451c541cf2b94382c56b853d2d6d80469", "chain": "optimism",  "role": "other",  "label": "HinkalInLogic OP",        "is_primary": False},
            {"address": "0x6d29a6e451c541cf2b94382c56b853d2d6d80469", "chain": "base",      "role": "other",  "label": "HinkalInLogic Base",      "is_primary": False},
            {"address": "0x6d29a6e451c541cf2b94382c56b853d2d6d80469", "chain": "arbitrum",  "role": "other",  "label": "HinkalInLogic ARB",       "is_primary": False},
            # Helper contracts (chain-specific)
            {"address": "0x305647287ae8e27876019b45e5b47a0985e1331d", "chain": "ethereum",  "role": "other",  "label": "Hinkal Helper ETH",       "is_primary": False},
            {"address": "0x97c2a7d8876e79d4dfac05f8413624bc352a43ef", "chain": "polygon",   "role": "other",  "label": "Hinkal Helper Polygon",   "is_primary": False},
            {"address": "0x86ffbd1eb2161fccd2fa7fd04842cc5dc8dbb619", "chain": "optimism",  "role": "other",  "label": "Hinkal Helper OP",        "is_primary": False},
            {"address": "0xd0191a3fb8f0a6c05ac393fb338ceba3fb5555e5", "chain": "base",      "role": "other",  "label": "Hinkal Helper Base",      "is_primary": False},
            {"address": "0x99d14eef260c0bf30005e399866321c64c7f4766", "chain": "arbitrum",  "role": "other",  "label": "Hinkal Helper ARB",       "is_primary": False},
            # Access token (shared)
            {"address": "0x82c4b40bfb0ed6af3675adf3fba655f01c132d33", "chain": "ethereum",  "role": "token",  "label": "Hinkal Access Token ETH", "is_primary": False},
            {"address": "0x82c4b40bfb0ed6af3675adf3fba655f01c132d33", "chain": "polygon",   "role": "token",  "label": "Hinkal Access Token Poly","is_primary": False},
            {"address": "0x82c4b40bfb0ed6af3675adf3fba655f01c132d33", "chain": "optimism",  "role": "token",  "label": "Hinkal Access Token OP",  "is_primary": False},
            {"address": "0x82c4b40bfb0ed6af3675adf3fba655f01c132d33", "chain": "base",      "role": "token",  "label": "Hinkal Access Token Base","is_primary": False},
            {"address": "0x82c4b40bfb0ed6af3675adf3fba655f01c132d33", "chain": "arbitrum",  "role": "token",  "label": "Hinkal Access Token ARB", "is_primary": False},
            # Legacy contracts
            {"address": "0x2ea81946ff675d5eb88192144ffc1418fa442e28", "chain": "ethereum",  "role": "other",  "label": "Hinkal Legacy ETH",       "is_primary": False},
            {"address": "0x41658b0daf59bb2fbb2d9a5249207011d2b364de", "chain": "arbitrum",  "role": "other",  "label": "Hinkal Legacy ARB",       "is_primary": False},
            {"address": "0xeeeb52e36c78b153caab2761c369a50b066cdd5",  "chain": "polygon",   "role": "other",  "label": "Hinkal Legacy Polygon",   "is_primary": False},
            {"address": "0x41658b0daf59bb2fbb2d9a5249207011d2b364de", "chain": "base",      "role": "other",  "label": "Hinkal Legacy Base",      "is_primary": False},
            # NOTE: Optimism legacy address in PRD is truncated (39 chars) — skipped
        ],
    },

    # ──────────────────────────────────────────────────────────────────────────
    # 6. 0x0.ai
    # Source: PRD §0x0.ai
    # Chain: ethereum
    # ──────────────────────────────────────────────────────────────────────────
    {
        "name": "0x0.ai",
        "slug": "0x0-ai",
        "defillama_slug": "0x0.ai",
        "description": "AI-powered privacy mixer and smart contract auditing platform on Ethereum.",
        "website_url": "https://0x0.ai",
        "github_url": "https://github.com/0x0exchange",
        "contracts": [
            {"address": "0x3d18ad735f949febd59bbfcb5864ee0157607616", "chain": "ethereum",  "role": "pool",  "label": "0x0 ETH Pool",  "is_primary": True},
            {"address": "0x5a3e6a77ba2f983ec0d371ea3b475f8bc0811ad5", "chain": "ethereum",  "role": "token", "label": "0x0 Token",     "is_primary": False},
        ],
    },

    # ──────────────────────────────────────────────────────────────────────────
    # 7. PANTHER PROTOCOL
    # Source: PRD §Panther Protocol
    # Chains: ethereum, polygon, base
    # ──────────────────────────────────────────────────────────────────────────
    {
        "name": "Panther Protocol",
        "slug": "panther-protocol",
        "defillama_slug": "panther-protocol",
        "description": "Multi-asset ZK privacy protocol. Staking, vesting, reward, and treasury infrastructure across 3 chains.",
        "website_url": "https://pantherprotocol.io",
        "github_url": "https://github.com/pantherprotocol",
        "contracts": [
            # Ethereum mainnet
            {"address": "0x909e34d3f6124c324ac83dcca84b74398a6fa173", "chain": "ethereum",  "role": "pool",       "label": "ZKP Token / Core ETH",          "is_primary": True},
            {"address": "0xf4d06d72dacdd8393fa4ea72fdcc10049711f899", "chain": "ethereum",  "role": "other",      "label": "Staking ETH",                   "is_primary": False},
            {"address": "0xb476104aa9d1f30180a01987fb09b1e96ddcf14b", "chain": "ethereum",  "role": "other",      "label": "Vesting Pools ETH",             "is_primary": False},
            {"address": "0x347a58878d04951588741d4d16d54b742c7f60fc", "chain": "ethereum",  "role": "other",      "label": "Reward Master ETH",             "is_primary": False},
            {"address": "0x5df8ec95d8b96ada2b4041d639ab66361564b050", "chain": "ethereum",  "role": "other",      "label": "Stake Reward Adviser ETH",      "is_primary": False},
            {"address": "0x1b316635a9ed279995c78e5a630e13aad7c0086b", "chain": "ethereum",  "role": "other",      "label": "Stake Reward Controller 2 ETH", "is_primary": False},
            {"address": "0xcf463713521af5ce31ad18f6914f3706493f10e5", "chain": "ethereum",  "role": "treasury",   "label": "Reward Pool ETH",               "is_primary": False},
            {"address": "0x208fb9169bbec5915722e0aff8b0eeEdabf8a6f0", "chain": "ethereum",  "role": "governance", "label": "DAO Multisig",                  "is_primary": False},
            # Polygon
            {"address": "0x9a06db14d639796b25a6cec6a1bf614fd98815ec", "chain": "polygon",   "role": "pool",       "label": "ZKP Token / Core Polygon",      "is_primary": False},
            {"address": "0x4cec451f63dbe47d9da2debe2b734e4cb4000eac", "chain": "polygon",   "role": "other",      "label": "Staking Polygon 1",             "is_primary": False},
            {"address": "0x5e7fda6d9f5024c4ad1c780839987ab8c76486c9", "chain": "polygon",   "role": "other",      "label": "Staking Polygon 2",             "is_primary": False},
            {"address": "0x09220dd0c342ee92c333faa6879984d63b4dff03", "chain": "polygon",   "role": "other",      "label": "Reward Master Polygon",         "is_primary": False},
            {"address": "0xaa943954eb256cc8c170c1bacf538d65d9eb9069", "chain": "polygon",   "role": "other",      "label": "Stake Reward Adviser Polygon",  "is_primary": False},
            {"address": "0x17f590df4dd5000a223cc08e31695cb83b181730", "chain": "polygon",   "role": "other",      "label": "Stake Reporter Polygon",        "is_primary": False},
            {"address": "0xdcd54b9355f60a7b596d1b7a9ac10e6477d6f1bb", "chain": "polygon",   "role": "other",      "label": "Stake Reward Controller Poly",  "is_primary": False},
            {"address": "0x20ad9300bde78a24798b1ee2e14858e5581585bc", "chain": "polygon",   "role": "treasury",   "label": "Reward Treasury Polygon",       "is_primary": False},
            {"address": "0x773d49309c4e9fc2e9254e7250f157d99efe2d75", "chain": "polygon",   "role": "pool",       "label": "MATIC Reward Pool Polygon",     "is_primary": False},
            # Base
            {"address": "0x0a776c1c22b8b8e7eab346744daa33722b80fda4", "chain": "base",      "role": "token",      "label": "ZKP Token Base",               "is_primary": False},
        ],
    },

    # ──────────────────────────────────────────────────────────────────────────
    # 8. VEIL CASH
    # Source: PRD §Veil Cash
    # Chain: base
    # ──────────────────────────────────────────────────────────────────────────
    {
        "name": "Veil Cash",
        "slug": "veil-cash",
        "defillama_slug": "veil-cash",
        "description": "zk-SNARK privacy mixer on Base L2. ETH and USDC pools with verifier and queue infrastructure.",
        "website_url": "https://veil.cash",
        "github_url": "https://github.com/veildotcash",
        "contracts": [
            # Pool contracts
            {"address": "0xc2535c547b64b997a4bd9202e1663deaf11c78a5", "chain": "base",      "role": "pool",     "label": "Veil Entry",       "is_primary": True},
            {"address": "0x293dcda114533ff8f477271c5ca517209ffdeee7", "chain": "base",      "role": "pool",     "label": "ETH Pool",         "is_primary": False},
            {"address": "0x5c50d58e49c59d112680c187de2bf989d2a91242", "chain": "base",      "role": "pool",     "label": "USDC Pool",        "is_primary": False},
            # Queue contracts
            {"address": "0xa4a926a2e7a22c38e8dfc6744a61a6aa8b06b230", "chain": "base",      "role": "other",    "label": "ETH Queue",        "is_primary": False},
            {"address": "0x5530241b24504bf05c9a22e95a1f5458888e6a9b", "chain": "base",      "role": "other",    "label": "USDC Queue",       "is_primary": False},
            # Helper + verifier contracts
            {"address": "0x2460da3acda8a3bdbB2149c948363233d3453ac2", "chain": "base",      "role": "verifier", "label": "Hasher",           "is_primary": False},
            {"address": "0x69013e62ef76bf1a7b980957607c944c9bd4fdf5", "chain": "base",      "role": "verifier", "label": "Verifier2",        "is_primary": False},
            {"address": "0xb5e025044b09cae75bace1c8db9701ae383792e4", "chain": "base",      "role": "verifier", "label": "Verifier16",       "is_primary": False},
            {"address": "0xb5b3c6192e1871c613e0c415108ba3934237f360", "chain": "base",      "role": "verifier", "label": "OnchainVerify",    "is_primary": False},
            # Token + staking
            {"address": "0x767a739d1a152639e9ea1d8c1bd55fdc5b217d7f", "chain": "base",      "role": "token",    "label": "VEIL Token",       "is_primary": False},
            {"address": "0x7bc834b3d64662eb2fff868f55d3a9994d4252a0", "chain": "base",      "role": "other",    "label": "Staking",          "is_primary": False},
        ],
    },

    # ──────────────────────────────────────────────────────────────────────────
    # 9. ZAMA FHEVM
    # Source: PRD §Zama FHEVM
    # Chain: ethereum
    # ──────────────────────────────────────────────────────────────────────────
    {
        "name": "Zama fhEVM",
        "slug": "zama-fhevm",
        "defillama_slug": "zama",
        "description": "Fully Homomorphic Encryption EVM protocol. Registry, staking, OFT adapter on Ethereum.",
        "website_url": "https://www.zama.org",
        "github_url": "https://github.com/zama-ai/fhevm",
        "contracts": [
            {"address": "0xeb5015ff021db115ace010f23f55c2591059bba0", "chain": "ethereum",  "role": "other",  "label": "Registry",                    "is_primary": True},
            {"address": "0xe9b176ccaa8840dc3b3567bb83e2cd2a6c36f4ab", "chain": "ethereum",  "role": "other",  "label": "KMS Protocol Staking",        "is_primary": False},
            {"address": "0x7147485b892158f2b875f7ac5ea48a9937c66ae8", "chain": "ethereum",  "role": "other",  "label": "Coprocessor Protocol Staking","is_primary": False},
            {"address": "0xa12cc123ba206d4031d1c7f6223d1c2ec249f4f3", "chain": "ethereum",  "role": "token",  "label": "ZAMA Token",                  "is_primary": False},
            {"address": "0xa798b04149e7a61cc95b7d114ad420e8969ea268", "chain": "ethereum",  "role": "other",  "label": "ZAMA OFT Adapter",            "is_primary": False},
        ],
    },

    # ──────────────────────────────────────────────────────────────────────────
    # 10. CYCLONE PROTOCOL
    # Source: PRD §Cyclone Protocol
    # Chains: ethereum, bnb, polygon
    # ──────────────────────────────────────────────────────────────────────────
    {
        "name": "Cyclone Protocol",
        "slug": "cyclone-protocol",
        "defillama_slug": "cyclone",
        "description": "Cross-chain zk-SNARK mixer with named anonymity pools and LP mining. ETH, BNB, Polygon.",
        "website_url": "https://cyclone.xyz",
        "github_url": "https://github.com/cycloneprotocol",
        "contracts": [
            # Ethereum
            {"address": "0x8861cff2366c1128fd699b68304ad99a0764ef9a", "chain": "ethereum",  "role": "token",   "label": "CYC Token ETH",            "is_primary": False},
            {"address": "0xdc71bc29d12960a3ee5452fac6f033a1b8e756fb", "chain": "ethereum",  "role": "other",   "label": "Aeolus LP Mining v2.1",    "is_primary": False},
            {"address": "0x949452e32db13a5771445cf20b304474b866202b", "chain": "ethereum",  "role": "verifier","label": "Hasher ETH",               "is_primary": False},
            {"address": "0x7c994fb3a8c208c1750df937d473040c604292d6", "chain": "ethereum",  "role": "verifier","label": "Verifier ETH",             "is_primary": False},
            {"address": "0x602b40bf327c10370483ae5ecde15a7bb480dcca", "chain": "ethereum",  "role": "router",  "label": "UniswapV2 Router ETH",     "is_primary": False},
            # Ethereum anonymity pools
            {"address": "0xd619c8da0a58b63be7fa69b4cc648916fe95fa1b", "chain": "ethereum",  "role": "pool",    "label": "Latte 100 ETH",            "is_primary": True},
            {"address": "0xa38b6742cef9573f7f97c387278fa31482539c3d", "chain": "ethereum",  "role": "pool",    "label": "Expresso 100k USDT",       "is_primary": False},
            {"address": "0x09f03488291063a8f3c67d2aab7002419d11c113", "chain": "ethereum",  "role": "pool",    "label": "Cold Brew 100 TORN",       "is_primary": False},
            # BNB Chain
            {"address": "0x810ee35443639348adbbc467b33310d2ab43c168", "chain": "bnb",       "role": "token",   "label": "CYC Token BSC",            "is_primary": False},
            {"address": "0x9286e9271bf497ec39b3fdaef53e38bfc6b4cf14", "chain": "bnb",       "role": "verifier","label": "Verifier BSC",             "is_primary": False},
            {"address": "0x92a737097d711bec4c31351997254e98e5f0d430", "chain": "bnb",       "role": "other",   "label": "Aeolus LP Mining v2 BSC",  "is_primary": False},
            {"address": "0x10ed43c718714eb63d5aa57b78b54704e256024e", "chain": "bnb",       "role": "router",  "label": "PancakeSwap Router",       "is_primary": False},
            # BNB anonymity pools
            {"address": "0x66b5e322dc31f8c7a33ffd23975163795f8d16c7", "chain": "bnb",       "role": "pool",    "label": "C3PO 100 BNB",             "is_primary": False},
            {"address": "0xbe19d541389c9d3e03efc08f3d5008e8c9cc42a5", "chain": "bnb",       "role": "pool",    "label": "R2D2 10k BUSD",            "is_primary": False},
            {"address": "0x79459751f6882868d1299bfa412428488b434541", "chain": "bnb",       "role": "pool",    "label": "BB8 25k IOTX",             "is_primary": False},
            {"address": "0xd90a6bf8439ef7214cf00da83e926068b6a507ec", "chain": "bnb",       "role": "pool",    "label": "Jonny5 3 CYC",             "is_primary": False},
            # Polygon
            {"address": "0xcfb54a6d2da14abecd231174fc5735b4436965d8", "chain": "polygon",   "role": "token",   "label": "CYC Token Polygon",        "is_primary": False},
            {"address": "0xb6e9ea062a7719846bc9e3e3ae8712e74faad376", "chain": "polygon",   "role": "verifier","label": "Verifier Polygon",         "is_primary": False},
            {"address": "0xa8c187d8773bc9e49a10554715ff49bdcf39d55d", "chain": "polygon",   "role": "other",   "label": "Aeolus LP Mining v2 Poly", "is_primary": False},
            {"address": "0xfcb851ad3d98bd241dbe395ca1e6080f489d4624", "chain": "polygon",   "role": "router",  "label": "QuickSwap Router",         "is_primary": False},
            # Polygon anonymity pools
            {"address": "0x5194932ad0f889b1e31041b8006a58ff70a11f43", "chain": "polygon",   "role": "pool",    "label": "Pentagon 1k MATIC",        "is_primary": False},
            {"address": "0x8e6e472e4a3f8b1951d2970f59b3944eff707e10", "chain": "polygon",   "role": "pool",    "label": "Hexagon 1k USDC",          "is_primary": False},
            {"address": "0x517ceee661b57ed7d5b615bf700cb307d87a025b", "chain": "polygon",   "role": "pool",    "label": "Octagon 2 QUICK",          "is_primary": False},
        ],
    },

    # ──────────────────────────────────────────────────────────────────────────
    # 11. FOOM CASH
    # Source: PRD §FOOM Cash
    # Chains: ethereum, base
    # ──────────────────────────────────────────────────────────────────────────
    {
        "name": "FOOM Cash",
        "slug": "foom-cash",
        "defillama_slug": "foom-cash",
        "description": "Privacy mixer protocol on Ethereum and Base. Token + holder contract architecture.",
        "website_url": "https://foom.cash",
        "github_url": "https://github.com/Terrestrials",
        "contracts": [
            # Ethereum
            {"address": "0xd0d56273290d339aaf1417d9bfa1bb8cfe8a0933", "chain": "ethereum",  "role": "token", "label": "FOOM Token ETH",    "is_primary": True},
            {"address": "0x239af915abcd0a5dcb8566e863088423831951f8", "chain": "ethereum",  "role": "other", "label": "Holder ETH",        "is_primary": False},
            # Base
            {"address": "0x02300ac24838570012027e0a90d3feccef3c51d2", "chain": "base",      "role": "token", "label": "FOOM Token Base",   "is_primary": False},
            {"address": "0xdb203504ba1fea79164af3ceffba88c59ee8aafd", "chain": "base",      "role": "other", "label": "Holder Base",       "is_primary": False},
        ],
    },

    # ──────────────────────────────────────────────────────────────────────────
    # 12. ANOMAPAY  (NEW)
    # Source: PRD §AnomaPay
    # Chains: ethereum, arbitrum, base, optimism
    # ──────────────────────────────────────────────────────────────────────────
    {
        "name": "AnomaPay",
        "slug": "anomapay",
        "defillama_slug": None,
        "description": "Privacy payment and protocol adapter system. Shared adapter across Arbitrum and Base.",
        "website_url": "https://anomapay.app/",
        "github_url": "https://github.com/anoma",
        "contracts": [
            # Ethereum
            {"address": "0x46e622226f93ed52c584f3f66135cd06af01c86c", "chain": "ethereum",  "role": "router", "label": "Protocol Adapter ETH",    "is_primary": True},
            {"address": "0xca81f370d0adb9eeb746b136a4ec0cbc710062fc", "chain": "ethereum",  "role": "other",  "label": "Token Distributor ETH",   "is_primary": False},
            # Arbitrum (shared adapter address with Base)
            {"address": "0x6d0a05e3535bd4d2c32aad37ffb28fd0e1e528c3", "chain": "arbitrum",  "role": "router", "label": "Protocol Adapter ARB",    "is_primary": False},
            # Base (same adapter address as Arbitrum per PRD)
            {"address": "0x6d0a05e3535bd4d2c32aad37ffb28fd0e1e528c3", "chain": "base",      "role": "router", "label": "Protocol Adapter Base",   "is_primary": False},
            # Optimism
            {"address": "0x094fcc095323080e71a037b2b1e3519c07dd84f8", "chain": "optimism",  "role": "router", "label": "Protocol Adapter OP",     "is_primary": False},
        ],
    },

    # ──────────────────────────────────────────────────────────────────────────
    # 13. HORIZEN  (NEW)
    # Source: PRD §Horizen
    # Chain: ethereum (L1 bridge + infrastructure)
    # ──────────────────────────────────────────────────────────────────────────
    {
        "name": "Horizen",
        "slug": "horizen",
        "defillama_slug": None,
        "description": "zk-enabled privacy infrastructure network. L2 bridge, proxy, system config, and ZEN token on Ethereum.",
        "website_url": "https://www.horizen.io",
        "github_url": "https://github.com/HorizenOfficial",
        "contracts": [
            # Token
            {"address": "0xf43eb8de897fbc7f2502483b2bef7bb9ea179229", "chain": "ethereum",  "role": "token",   "label": "ZEN Token",                      "is_primary": True},
            # Core L2 infrastructure (Ethereum L1 side)
            {"address": "0x23e9345926ef161027292d60f80be43ad01bdf8f", "chain": "ethereum",  "role": "other",   "label": "AddressManager",                 "is_primary": False},
            {"address": "0x5988f7dfc8f81d4a9f1834f8707e87e519e10b55", "chain": "ethereum",  "role": "other",   "label": "AnchorStateRegistryProxy",       "is_primary": False},
            {"address": "0x4e2c464380fb26b0c5f9b90edf754c4e2a8d1a90", "chain": "ethereum",  "role": "other",   "label": "DisputeGameFactoryProxy",        "is_primary": False},
            {"address": "0x9f5e33f901ad50b50d6a27f63adabea4c81e953c", "chain": "ethereum",  "role": "other",   "label": "L1CrossDomainMessengerProxy",    "is_primary": False},
            {"address": "0xc4d2246a4c17bc62d98ad1ed130e9190d1768a39", "chain": "ethereum",  "role": "other",   "label": "L1ERC721BridgeProxy",            "is_primary": False},
            {"address": "0xf4a6cc4171fda694439f856d912777aa6ab05369", "chain": "ethereum",  "role": "pool",    "label": "L1StandardBridgeProxy",          "is_primary": False},
            {"address": "0xb7f32763a2f4704d0bb3ac3c6fe2e6bed593479d", "chain": "ethereum",  "role": "other",   "label": "OptimismMintableERC20FactoryProxy","is_primary": False},
            {"address": "0x78e794d10a355468a0e7a14aa1a9f9a253d78784", "chain": "ethereum",  "role": "pool",    "label": "OptimismPortalProxy",            "is_primary": False},
            {"address": "0x2bf281c451f0056065fa7d79540ef634f42f7653", "chain": "ethereum",  "role": "other",   "label": "ProtocolVersionsProxy",          "is_primary": False},
            {"address": "0xee07da11d10452e0ba0670b2aaa317c5178b5cf0", "chain": "ethereum",  "role": "other",   "label": "ProxyAdmin",                     "is_primary": False},
            {"address": "0x4da82a327773965b8d4d85fa3db8249b387458e7", "chain": "ethereum",  "role": "other",   "label": "SuperchainConfig",               "is_primary": False},
            {"address": "0x2c59d35d2716b0b0269c5eccc0a6569c98f60be9", "chain": "ethereum",  "role": "other",   "label": "SuperchainConfigProxy",          "is_primary": False},
            {"address": "0x359d292f97084c4bce3652ee91a166b827aef028", "chain": "ethereum",  "role": "other",   "label": "SystemConfigProxy",              "is_primary": False},
            # NOTE: AnchorStateRegistry + L2OutputOracle are 0x000...000 (zero addr) — skipped
        ],
    },
    # ──────────────────────────────────────────────────────────────────────────
    # 14. IEXEC
    # Source: iex.ec/developers/quick-reference-guide-to-iexec-protocol-addresses
    # Chains: ethereum, arbitrum
    # Testnets (Arbitrum Sepolia) excluded
    # Audits: ChainSecurity, Consensys Diligence, Halborn
    # ──────────────────────────────────────────────────────────────────────────
    {
        "name": "iExec",
        "slug": "iexec",
        "defillama_slug": None,
        "description": "Decentralized computing marketplace with TEE-based confidential computing and data privacy. PoCo protocol manages trustless computation.",
        "website_url": "https://www.iex.ec",
        "github_url": "https://github.com/iExecBlockchainComputing",
        "contracts": [
            # ── Ethereum Mainnet ──────────────────────────────────────────────
            {"address": "0x607f4c5bb672230e8672085532f7e901544a7375", "chain": "ethereum",  "role": "token",   "label": "RLC Token ETH",                   "is_primary": False},
            {"address": "0x3eca1b216a7df1c7689aeb259efb04ad753aafe5", "chain": "ethereum",  "role": "pool",    "label": "PoCo Diamond Proxy ETH",          "is_primary": True},
            {"address": "0x9950d94fb074182ee93ff79a50cd698c4983281f", "chain": "ethereum",  "role": "other",   "label": "AppRegistry ETH",                 "is_primary": False},
            {"address": "0x07cc4e1ea30dd02796795876509a3bfc5053128d", "chain": "ethereum",  "role": "other",   "label": "DatasetRegistry ETH",             "is_primary": False},
            {"address": "0xe3c13bb4a5068601c6a08041cb50887b07b5f398", "chain": "ethereum",  "role": "other",   "label": "WorkerpoolRegistry ETH",          "is_primary": False},
            # ── Arbitrum Mainnet ──────────────────────────────────────────────
            {"address": "0xe649e6a1f2afc63ca268c2363691cecaf75cf47c", "chain": "arbitrum",  "role": "token",   "label": "RLC Token ARB",                   "is_primary": False},
            {"address": "0x098bfcb1e50ebca0baa92c12ea0c3f045a1ad9f0", "chain": "arbitrum",  "role": "pool",    "label": "PoCo Diamond Proxy ARB",          "is_primary": False},
            {"address": "0x9950d94fb074182ee93ff79a50cd698c4983281f", "chain": "arbitrum",  "role": "other",   "label": "AppRegistry ARB",                 "is_primary": False},
            {"address": "0x07cc4e1ea30dd02796795876509a3bfc5053128d", "chain": "arbitrum",  "role": "other",   "label": "DatasetRegistry ARB",             "is_primary": False},
            {"address": "0xe3c13bb4a5068601c6a08041cb50887b07b5f398", "chain": "arbitrum",  "role": "other",   "label": "WorkerpoolRegistry ARB",          "is_primary": False},
            # ── Arbitrum — Data Protector ─────────────────────────────────────
            {"address": "0xf08f91f7646fdb95a4e24977b8db91318252a667", "chain": "arbitrum",  "role": "vault",   "label": "DataProtector Core",              "is_primary": False},
            {"address": "0xe4f319adf2f3dbfd3270f35cec90575dc858a0da", "chain": "arbitrum",  "role": "other",   "label": "AddOnlyAppWhitelistRegistry",     "is_primary": False},
            {"address": "0x2da2d268281d79b81d609d68e4507e7acdfd7e05", "chain": "arbitrum",  "role": "other",   "label": "DataProtector Sharing",           "is_primary": False},
            # ── Arbitrum — Applications ───────────────────────────────────────
            {"address": "0xfa9cceff9431ee0e2a3fe58911073f1357f24e31", "chain": "arbitrum",  "role": "other",   "label": "Web3Mail Whitelist",              "is_primary": False},
            {"address": "0xa7101cf61d4602d55a715be4f2b9e1bc71d22301", "chain": "arbitrum",  "role": "other",   "label": "Web3Telegram Whitelist",          "is_primary": False},
            {"address": "0x8ef2ec3ef9535d4b4349bfec7d8b31a580e60244", "chain": "arbitrum",  "role": "other",   "label": "Default Workerpool ARB",          "is_primary": False},
        ],
    },

    # ──────────────────────────────────────────────────────────────────────────
    # 14. IEXEC
    # Source: iex.ec/developers/quick-reference-guide-to-iexec-protocol-addresses
    # Chains: ethereum, arbitrum
    # Testnets (Arbitrum Sepolia) excluded
    # Audits: ChainSecurity, Consensys Diligence, Halborn
    # ──────────────────────────────────────────────────────────────────────────

]


def seed() -> dict:
    """Idempotent — skips protocols whose slug already exists."""
    added_protocols = 0
    added_contracts = 0
    skipped_protocols = 0
    skipped_contracts = 0

    with get_sync_session() as db:
        existing_slugs = {r.slug for r in db.query(Protocol.slug).all()}

        for p in PROTOCOLS:
            if p["slug"] in existing_slugs:
                skipped_protocols += 1
                log.info("seed.skip slug=%s", p["slug"])
                continue

            protocol = Protocol(
                name=p["name"],
                slug=p["slug"],
                defillama_slug=p.get("defillama_slug"),
                description=p.get("description"),
                website_url=p.get("website_url"),
                github_url=p.get("github_url"),
            )
            db.add(protocol)
            db.flush()

            for c in p.get("contracts", []):
                chain_id = _CID.get(c["chain"])
                if chain_id is None:
                    log.warning(
                        "seed.unknown_chain slug=%s chain=%s label=%s — skipping",
                        p["slug"], c["chain"], c.get("label", ""),
                    )
                    skipped_contracts += 1
                    continue

                db.add(ProtocolContract(
                    protocol_id=protocol.id,
                    address=c["address"].lower(),
                    chain_id=chain_id,
                    contract_role=c["role"],
                    label=c.get("label", ""),
                    is_primary=c.get("is_primary", False),
                ))
                added_contracts += 1

            added_protocols += 1
            log.info(
                "seed.added slug=%s contracts=%d",
                p["slug"], len(p.get("contracts", [])),
            )

    log.info(
        "seed.complete added=%d skipped=%d contracts_added=%d contracts_skipped=%d",
        added_protocols, skipped_protocols, added_contracts, skipped_contracts,
    )
    return {
        "added_protocols":   added_protocols,
        "skipped_protocols": skipped_protocols,
        "added_contracts":   added_contracts,
        "skipped_contracts": skipped_contracts,
    }


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = seed()
    print("\n── Seed result ─────────────────────────────────────────────────")
    for k, v in result.items():
        print(f"  {k}: {v}")
    print("────────────────────────────────────────────────────────────────\n")
