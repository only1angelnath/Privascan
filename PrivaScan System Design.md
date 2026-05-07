# PrivaScan — Privacy Protocol Smart Contract Risk Scoring API
## System Design & Technical Proposal

```
**Project Codename:** PrivaScan
**Domain:** privascan.xyz
**Version:** 1.0 (EVM only) — Final pre-build specification
**Type:** Open-Source Public Good 
**Primary Language:** Python
**Deployment:** Railway (backend + workers + bot) · Vercel (frontend)
**Scoring Model:** Rule-based deterministic
**Concurrency Model:** Async I/O (FastAPI + asyncio) + Celery workers (CPU-bound)
**Product Model:** Hybrid — curated EVM protocol registry + open EVM contract scanner
**Protocol Coverage V1:** 19 curated EVM protocols (all contracts — pools, routers, vaults)
**Protocol Coverage V2:** Non-EVM (Zcash, Monero, Penumbra)
```

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Market Gap Analysis](#3-market-gap-analysis)
4. [Architectural Decisions & Rationale](#4-architectural-decisions--rationale)
5. [Product Model — Hybrid Two-Track System](#5-product-model--hybrid-two-track-system)
6. [Multi-Contract Coverage Strategy](#6-multi-contract-coverage-strategy)
7. [System Architecture](#7-system-architecture)
8. [Data Sources & Integration Strategy](#8-data-sources--integration-strategy)
9. [TVL Data Strategy — DefiLlama + Dune SIM Fallback](#9-tvl-data-strategy--defillama--dune-sim-fallback)
10. [Risk Scoring Model & Visual Design](#10-risk-scoring-model--visual-design)
11. [Override Rules — Resolved State Handling](#11-override-rules--resolved-state-handling)
12. [Slither Integration — Full Capability Map](#12-slither-integration--full-capability-map)
13. [Backend Design](#13-backend-design)
14. [Database Schema](#14-database-schema)
15. [Async & Concurrency Architecture](#15-async--concurrency-architecture)
16. [Telegram Alert System & Visual Design](#16-telegram-alert-system--visual-design)
17. [Frontend Design & Visual System](#17-frontend-design--visual-system)
18. [API Reference](#18-api-reference)
19. [Infrastructure & Deployment](#19-infrastructure--deployment)
20. [Security & Rate Limiting](#20-security--rate-limiting)
21. [Build Plan — 2-Week MVP](#21-build-plan--2-week-mvp)
22. [Deliverables](#22-deliverables)
23. [Monetisation & Grant Strategy](#23-monetisation--grant-strategy)
24. [V2 Roadmap](#24-v2-roadmap)
25. [Appendices](#25-appendices)

---

## 1. Executive Summary

PrivaScan (privascan.xyz) is a production-grade, open-source smart contract risk scoring API built for EVM-compatible privacy protocols. It scores entire protocol ecosystems — not just token contracts — analysing every deployed contract including privacy pools, routers, vaults, verifiers, and governance contracts as a unified risk surface.

V1 covers 19 curated EVM privacy protocols with confirmed DefiLlama TVL data, plus an open scanner for any EVM address. For the small number of protocols not indexed on DefiLlama, the Dune SIM API provides real-time on-chain balance data with a 48-hour cache TTL instead of 24 hours (rewarding data quality with longer freshness windows).

The scoring model is fully rule-based and deterministic. Every score is explainable, traceable, and reproducible. Hard override rules now include a resolved state pathway — when an exploit is remediated or an OFAC listing is removed, the protocol can exit the override and re-enter normal scoring territory, with the resolution event permanently logged in the score history.

**Total external infrastructure cost at MVP: $0** (CoinGecko paid key owned by developer, Dune SIM key available, all other sources free tier).

---

## 2. Problem Statement

Privacy protocols carry unique risk profiles not covered by existing tooling: privacy-specific Solidity vulnerabilities (mixer reentrancy, ZK verifier bypass), OFAC exposure, liquidity fragility, opaque admin key structures, and audit deficiency. No existing free tool provides a composable, explainable risk score across the entire smart contract surface of a privacy protocol — all pools, routers, verifiers, and vaults together.

---

## 3. Market Gap Analysis

| Tool | Scope | Privacy-Specific | Free API | Explainable | Multi-Contract |
|---|---|---|---|---|---|
| TRM Labs | General DeFi | No | No | No | No |
| Token Sniffer | Rug pulls | No | Limited | Partial | No |
| Slither (CLI) | Code only | No | No REST | Yes | No |
| Chainalysis | Compliance only | Partial | No | No | No |
| GoPlus | Token safety | No | Limited | No | No |
| **PrivaScan V1** | **EVM privacy protocols** | **Yes** | **Yes** | **Yes** | **Yes** |

---

## 4. Architectural Decisions & Rationale

### 4.1 Rule-Based V1, ML in V2
Every V1 score traces to a verifiable data point. No model weights, no inference infrastructure. ML deferred to V2 as additive sub-scores (TVL anomaly detection, bytecode similarity, audit NLP).

### 4.2 Async I/O + Celery Workers
API layer fully async (FastAPI + httpx + asyncpg + aioredis). Slither is CPU-bound — runs in Celery worker processes (separate OS processes, bypasses GIL). No manual threading.

### 4.3 Hybrid Two-Track Model
Track A: 19 curated protocols, 6-hour scheduled rescore. Track B: any EVM contract, on-demand. Both use the same scoring engine.

### 4.4 Multi-Contract Ecosystem Scoring
We score all deployed contracts of a protocol, not just the token. Pools, routers, vaults, verifiers, timelock, governance — all analysed as a unified risk surface with an ecosystem-level composite score.

### 4.5 Dune SIM API for TVL Gap Fill
For EVM protocols not indexed on DefiLlama, the Dune SIM API provides real-time per-address token balances with USD pricing — accurate TVL directly from chain state. Cache TTL is extended to 48 hours for Dune-sourced TVL (vs 24 hours for community scans) because Dune data is freshly priced and accurate. CoinGecko paid key is used for token price lookups when needed.

### 4.6 Resolved Override States
OFAC sanctions and exploit overrides are not permanent. When a protocol resolves an exploit (bug fix, compensation, re-audit) or is removed from the OFAC SDN list, the override lifts and the protocol re-enters normal scoring. The resolution event is permanently appended to the score history for full auditability.

### 4.7 Domain
privascan.xyz — API: api.privascan.xyz · Frontend: privascan.xyz · Bot: @PrivaScanBot

---

## 5. Product Model — Hybrid Two-Track System

### 5.1 Track A — Curated Protocol Registry

19 pre-seeded EVM privacy protocols (see Appendix B). Rescored every 6 hours via Celery beat. Cache TTL: 6 hours. Label: `"scan_type": "curated"`. Telegram alerts broadcast to all subscribers when composite score changes > 10 points or a new hard flag appears.

### 5.2 Track B — Open EVM Contract Scanner

Any user-submitted EVM contract address on any supported chain. Triggered on-demand. Cache TTL: 24 hours (or 48 hours if Dune SIM is the TVL source). Label: `"scan_type": "community"`. Personal watchlist alerts only. Rate limit: 5 scans/hour anonymous, 50/hour free key.

### 5.3 Request Lifecycle

```
TRACK A (every 6h):
  Celery beat → for each curated protocol ecosystem:
    → check Redis TTL → skip if fresh
    → dispatch score_ecosystem_task(protocol_id, scan_type="curated")
    → on completion: store, diff vs previous, push Telegram if alert condition met

TRACK B (on-demand):
  User submits address
    → EIP-55 validation + chain whitelist check + rate limit
    → detect: is this a known protocol address? → link to ecosystem
    → Redis cache check → return if TTL valid
    → dispatch score_contract_task(address, chain_id, scan_type="community")
    → return 202 + task_id
    → client polls GET /score/task/{task_id}
```

---

## 6. Multi-Contract Coverage Strategy

This is a key differentiator. PrivaScan does not score just the ERC-20 token contract of a privacy protocol. It scores the full deployed contract ecosystem.

### 6.1 Why This Matters

A privacy protocol's risk surface is spread across multiple contracts:

| Contract Type | Risk Relevance |
|---|---|
| Privacy pool contracts | Core TVL holder — reentrancy, drain risk |
| ZK verifier contracts | Bypass risk — `controlled-delegatecall` |
| Router / relayer contracts | Fee manipulation, access control |
| Vault / yield contracts | Upgrade risk, locked funds |
| Governance / timelock | Admin key centralisation |
| Token contract (ERC-20) | Governance concentration (HHI) |
| Proxy contracts | Upgradeability, storage collision |

Scoring only the token misses all pool-level and verifier-level risk — which is where privacy protocols are actually exploited.

### 6.2 Protocol Contract Registry

Each curated protocol has a contract registry stored in the `protocol_contracts` table. The registry maps each known contract address to its role within the ecosystem.

```sql
CREATE TABLE protocol_contracts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocol_id     UUID REFERENCES protocols(id),
    address         VARCHAR(42) NOT NULL,
    chain_id        INTEGER NOT NULL,
    contract_role   VARCHAR(50) NOT NULL,  -- 'pool', 'verifier', 'router',
                                           -- 'vault', 'governance', 'token',
                                           -- 'timelock', 'proxy', 'other'
    label           VARCHAR(200),          -- human-readable: "ETH 0.1 Pool"
    is_primary      BOOLEAN DEFAULT FALSE, -- TRUE for the main scoring contract
    added_at        TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(address, chain_id)
);
```

### 6.3 Ecosystem Scoring Logic

When a curated protocol is scored, all registered contracts are analysed. The code risk and ownership sub-scores aggregate across the full contract set:

```
code_risk_score = weighted_mean(
    [slither_score(contract) for contract in protocol.contracts],
    weights=[contract_role_weight(c.contract_role) for c in protocol.contracts]
)

Role weights for code risk aggregation:
  pool:        1.5×  (highest — holds user funds)
  verifier:    1.4×  (critical — ZK bypass risk)
  vault:       1.3×
  router:      1.2×
  proxy:       1.2×
  governance:  1.0×
  token:       0.8×
  timelock:    0.7×
  other:       1.0×
```

For Track B (open scanner, single address), the contract is scored individually. If the address matches a known protocol registry entry, the system appends a note: "This contract is part of the [Protocol Name] ecosystem. Consider viewing the full ecosystem score."

### 6.4 TVL Aggregation Across Contracts

For protocols with multiple pool contracts, TVL is summed across all pool addresses. DefiLlama protocol-level TVL already aggregates across pools. For Dune SIM gap fill, we query the balance of each pool contract individually and sum.

---

## 7. System Architecture

### 7.1 Five-Layer Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — DATA SOURCES                                                  │
│                                                                          │
│  Etherscan v2        DefiLlama Free API    Alchemy RPC                  │
│  (source code,       (TVL, fees,           (on-chain state:             │
│   ABI, creator,       30d trend,            owner(), proxy slots,       │
│   logs, internal tx)  protocol metadata)    multisig, token dist.)      │
│                                                                          │
│  Dune SIM API        OFAC SDN XML          DeFiHackLabs DB              │
│  (real-time token    (sanctions list,      (exploit records,            │
│   balances for TVL   daily refresh)        weekly GitHub pull)          │
│   gap fill — paid)                                                       │
│                                                                          │
│  CoinGecko API       Internal Audit DB     Slither (local)              │
│  (paid key,          (curated audits,      (Python library,             │
│   price lookups      manually seeded)       5 custom detectors)         │
│   for Dune gap fill)                                                     │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────────────┐
│  LAYER 2 — DATA LAYER (Railway)                                          │
│  PostgreSQL · Redis (cache + broker) · Celery task queue                │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────────────┐
│  LAYER 3 — BACKEND CORE (FastAPI on Railway)                             │
│  REST API · Override state manager · API key auth · Rate limiter        │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────────────┐
│  LAYER 4 — SCORING ENGINE (Celery workers — separate OS processes)       │
│                                                                          │
│  Six analysers run as Celery group (parallel across all ecosystem        │
│  contracts):                                                             │
│  [1] Code risk   — Slither per-contract + role-weighted aggregation     │
│  [2] Ownership   — Web3.py per ecosystem: admin keys, proxy, multisig   │
│  [3] Liquidity   — DefiLlama → Dune SIM fallback → CoinGecko pricing   │
│  [4] Audit       — Internal DB · formula per protocol                   │
│  [5] Compliance  — OFAC SDN · DeFiHackLabs · resolved state check      │
│  [6] Governance  — On-chain HHI across token + governance contracts     │
│                                                                          │
│  → Aggregator → Override engine (with resolution state) → Grade        │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────────────┐
│  LAYER 5 — DISTRIBUTION                                                  │
│  REST API (api.privascan.xyz) · Dashboard (privascan.xyz) · @PrivaScanBot│
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Data Sources & Integration Strategy

### 8.1 Etherscan API v2

**URL:** `https://api.etherscan.io/v2/api` · **Auth:** Free API key · **Limits:** 5 req/sec, 100K/day
**Coverage:** Ethereum, Polygon, Arbitrum, Optimism, Base, BNB Chain, Avalanche — one key via `chainid`

Endpoints used: `getsourcecode`, `getabi`, `getcontractcreation`, `txlistinternal`, `getLogs`, `tokeninfo`

For unverified contracts: fallback to `eth.get_code()` via Web3.py → Slither bytecode mode. Penalised + flagged `"source_verified": false`.

---

### 8.2 DefiLlama Free API

**URL:** `https://api.llama.fi` · **Auth:** None · **Limits:** Unlimited

Endpoints: `GET /protocol/{slug}`, `GET /tvl/{protocol}`, `GET /protocols`, `GET /yields/pools`, `GET /summary/fees/{protocol}`

TVL confidence when DefiLlama is source: `"tvl_confidence": "high"`

---

### 8.3 Dune SIM API — TVL Gap Fill

**URL:** `https://api.sim.dune.com/v1/evm/` · **Auth:** Dune API key (paid, developer-owned)
**Purpose:** Real-time per-address token balance reads for EVM protocols not indexed on DefiLlama
**Cost per request:** Fixed 1 Compute Unit

The Dune SIM Balances endpoint returns all token holdings of a contract address with USD pricing — ideal for computing TVL across multiple pool contracts.

```python
# app/core/clients/dune_sim.py
import httpx
from app.config import settings

DUNE_SIM_BASE = "https://api.sim.dune.com/v1/evm"

async def get_contract_tvl_dune(address: str, chain_id: int) -> dict:
    """
    Fetch all token balances held by a contract address.
    Used as TVL fallback for protocols not tracked on DefiLlama.
    Returns sum of all token values in USD.
    """
    headers = {"X-Dune-Api-Key": settings.DUNE_API_KEY}
    params = {"chain_ids": str(chain_id)}

    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            f"{DUNE_SIM_BASE}/balances/{address}",
            headers=headers,
            params=params,
        )
        r.raise_for_status()
        data = r.json()

    balances = data.get("balances", [])
    total_tvl_usd = sum(
        b.get("value_usd", 0) or 0
        for b in balances
        if not b.get("low_liquidity", False)
    )
    return {
        "tvl_usd": total_tvl_usd,
        "token_breakdown": [
            {
                "symbol": b.get("symbol"),
                "amount": b.get("amount"),
                "value_usd": b.get("value_usd", 0),
            }
            for b in balances
            if not b.get("low_liquidity", False)
        ],
        "tvl_source": "dune_sim",
        "tvl_confidence": "medium",
    }

async def get_ecosystem_tvl_dune(pool_addresses: list[str], chain_id: int) -> float:
    """
    Sum TVL across multiple pool contracts for a protocol.
    Called once per pool, results aggregated.
    """
    total = 0.0
    for address in pool_addresses:
        result = await get_contract_tvl_dune(address, chain_id)
        total += result["tvl_usd"]
    return total
```

**Cache TTL for Dune-sourced TVL:** 48 hours (extended from 24h default — Dune data is directly on-chain priced, warranting a longer freshness window while conserving Compute Units).

**TVL confidence when Dune is source:** `"tvl_confidence": "medium"` (accurate but protocol-level aggregation not as comprehensive as DefiLlama's adapter).

---

### 8.4 CoinGecko API (Paid Key)

**URL:** `https://api.coingecko.com/api/v3`
**Auth:** Paid API key (developer-owned) — higher rate limits, better reliability
**V1 use:** Token price lookups to support Dune SIM TVL calculation when ERC-20 prices are needed; also provides protocol market cap and token price context for score reports.

```python
# app/core/clients/coingecko.py
import httpx
from app.config import settings

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

async def get_token_price_usd(contract_address: str, chain: str) -> float:
    """Price lookup for ERC-20 tokens by contract address."""
    chain_map = {
        "ethereum": "ethereum", "polygon": "polygon-pos",
        "arbitrum": "arbitrum-one", "optimism": "optimistic-ethereum",
        "base": "base", "bnb": "binance-smart-chain",
        "avalanche": "avalanche",
    }
    platform = chain_map.get(chain, "ethereum")
    headers = {"x-cg-pro-api-key": settings.COINGECKO_API_KEY}
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            f"{COINGECKO_BASE}/simple/token_price/{platform}",
            headers=headers,
            params={"contract_addresses": contract_address, "vs_currencies": "usd"},
        )
        r.raise_for_status()
        data = r.json()
    return data.get(contract_address.lower(), {}).get("usd", 0.0)
```

---

### 8.5 Web3.py + Alchemy RPC

**Library:** `web3` (PyPI) · **RPC:** Alchemy free tier (300M CU/month)
**Chains:** Ethereum, Polygon, Arbitrum, Optimism, Base; public RPCs for BNB and Avalanche

On-chain reads across all ecosystem contracts:
- `owner()` / `getOwner()` — ownership per contract
- EIP-1967 slot `0x360894...` — proxy detection
- `getThreshold()`, `getOwners()` — Gnosis Safe
- `minDelay()` — TimelockController
- `balanceOf()` top 20 — HHI governance score
- `paused()` — circuit breaker detection

---

### 8.6 OFAC SDN List

**URL:** `https://www.treasury.gov/ofac/downloads/sdn.xml`
**Auth:** None · **Refresh:** Daily 03:00 UTC via Celery beat

Addresses checked: all ecosystem contract addresses, all deployer addresses, all owner/admin addresses, all multisig signers.

Hard override on any match. Resolution pathway documented in Section 11.

---

### 8.7 DeFiHackLabs Exploit Database

**Source:** `https://github.com/SunWeb3Sec/DeFiHackLabs`
**Access:** Open-source, cloned weekly via Celery beat
**Matches against:** All ecosystem contract addresses + all associated attacker addresses

Hard override on match. Resolution pathway documented in Section 11.

---

### 8.8 Internal Audit Database

**Type:** Internal Postgres `audit_records`, manually seeded, open for community contribution.
**Scope:** Audits of the full contract ecosystem (pool audits, verifier audits, governance audits) — not just token audits.

**Audit scoring formula:**
```
audit_base      = min(100, num_audits × 20)
auditor_bonus   = mean(tier_score)
                  tier 1 (Trail of Bits, OpenZeppelin, Certora) = 30pts
                  tier 2 (Halborn, Sigma Prime, Nethermind)     = 20pts
                  tier 3 (others)                               = 10pts
recency_factor  = 1.0 if most_recent_audit ≤ 12 months else 0.7
fv_bonus        = 15 if formally verified else 0
crit_penalty    = unresolved_critical_count × 25

audit_score = min(100, max(0,
    (audit_base + auditor_bonus + fv_bonus) × recency_factor − crit_penalty
))
```

---

### 8.9 Data Source Summary

| Source | Provides | Auth | Cost | TVL Confidence |
|---|---|---|---|---|
| Etherscan v2 | Source, ABI, creator, logs | Free key | $0 | — |
| DefiLlama | TVL, fees, trends | None | $0 | `high` |
| Alchemy RPC | On-chain state | Free key | $0 | — |
| Dune SIM API | Real-time contract balances | Paid key (dev-owned) | Paid | `medium` |
| CoinGecko | Token price lookups | Paid key (dev-owned) | Paid | — |
| OFAC SDN XML | Sanctions list | None | $0 | — |
| DeFiHackLabs | Exploit records | None (GitHub) | $0 | — |
| Audit DB | Known audits | Internal | $0 | — |
| Slither | Solidity analysis | Local library | $0 | — |

---

## 9. TVL Data Strategy — DefiLlama + Dune SIM Fallback

### 9.1 Decision Tree

```
For each protocol needing TVL:
  │
  ├── Does DefiLlama have a slug for this protocol?
  │       │
  │       ├── YES → fetch /protocol/{slug}
  │       │         tvl_confidence = "high"
  │       │         cache TTL = 6h (curated) / 24h (community)
  │       │
  │       └── NO → Is this a known Zama-style adoption-proxy protocol?
  │                   │
  │                   ├── YES → Use protocol adoption proxy
  │                   │         tvl_confidence = "not_applicable"
  │                   │         BUT ALSO fetch Dune SIM TVL for wrapper contracts
  │                   │         and add to score report as supplementary data
  │                   │
  │                   └── NO → Query Dune SIM API for all pool contract balances
  │                             Sum across all pool addresses
  │                             tvl_confidence = "medium"
  │                             cache TTL = 48h (extended for Dune data quality)
```

### 9.2 Zama FHEVM — Combined TVL Approach

Zama has both a DefiLlama adapter (tracking cUSDC, ctGBP, cUSDT wrapper contracts — $27.68M TVS at first run) AND a role as a middleware protocol. We use both signals:

1. **DefiLlama TVL:** Use the DefiLlama adapter data for the TVL sub-score base. Slug: `zama`
2. **Protocol adoption metric:** Supplement with a deployment count signal (number of live FHEVM contracts using Zama) tracked via Dune SQL query.
3. **TVL confidence:** `"high"` (DefiLlama adapter now merged)

```python
# For Zama: combine DefiLlama TVL with adoption metric
async def get_zama_liquidity_data() -> dict:
    # Primary: DefiLlama TVL (wrapper contract reserves)
    llama_data = await get_protocol_tvl_data("zama")

    # Supplementary: count deployed FHEVM contracts (Dune SQL)
    fhevm_count = await get_fhevm_deployment_count()

    return {
        **llama_data,
        "fhevm_contract_count": fhevm_count,
        "liquidity_metric_note": (
            "TVL reflects ERC-20 reserves in Zama's confidential wrapper contracts. "
            "FHEVM deployment count included as protocol adoption signal."
        )
    }
```

### 9.3 TVL Confidence Reference

| Value | Meaning | Cache TTL |
|---|---|---|
| `high` | DefiLlama adapter with full TVL history | 6h (curated) |
| `medium` | Dune SIM real-time balance reads | 48h |
| `not_applicable` | Adoption proxy only (no TVL-holding contracts) | 6h |

---

## 10. Risk Scoring Model & Visual Design

### 10.1 Six Scoring Dimensions

| # | Dimension | Weight | Source |
|---|---|---|---|
| 1 | Code Risk | 30% | Slither across all ecosystem contracts |
| 2 | Ownership Risk | 25% | Web3.py across all admin roles |
| 3 | Liquidity Risk | 20% | DefiLlama → Dune SIM |
| 4 | Audit History | 12% | Internal audit DB |
| 5 | Compliance Flags | 8% | OFAC + DeFiHackLabs |
| 6 | Governance Concentration | 5% | On-chain HHI |

All sub-scores: 0–100, **100 = safest**. Composite: 0–100.

### 10.2 Composite Formula

```
composite = 0.30×code + 0.25×ownership + 0.20×liquidity
          + 0.12×audit + 0.08×compliance + 0.05×governance
```

### 10.3 Letter Grade + Colour System

The colour system is consistent across the web dashboard, Telegram alerts, and all API badge outputs. Every grade has a primary colour, a background tint, and an icon.

```
Grade A  [85–100]   Colour: #22c55e  (Emerald Green)    Icon: ✅  "Low Risk"
Grade B  [70–84]    Colour: #84cc16  (Lime Green)        Icon: 🟢  "Moderate-Low Risk"
Grade C  [55–69]    Colour: #f59e0b  (Amber)             Icon: 🟡  "Moderate Risk"
Grade D  [40–54]    Colour: #f97316  (Orange)            Icon: 🟠  "High Risk"
Grade F  [0–39]     Colour: #ef4444  (Red)               Icon: 🔴  "Critical Risk"

Override states:
  OFAC sanctioned:    Colour: #7c3aed  (Purple)           Icon: ⛔  "Sanctioned"
  Exploit record:     Colour: #b91c1c  (Deep Red)         Icon: 💀  "Exploit History"
  Resolved (OFAC):    Colour: #0ea5e9  (Sky Blue)         Icon: 🔵  "Sanction Lifted"
  Resolved (exploit): Colour: #06b6d4  (Cyan)             Icon: 🔵  "Exploit Resolved"
```

### 10.4 Sub-Score Colour Bands (Progress Bars)

Each sub-score bar on the dashboard and in Telegram uses a gradient that shifts colour based on value:

```
0–29    Background: #fef2f2  Bar fill: #ef4444   (Red)
30–54   Background: #fff7ed  Bar fill: #f97316   (Orange)
55–69   Background: #fffbeb  Bar fill: #f59e0b   (Amber)
70–84   Background: #f7fee7  Bar fill: #84cc16   (Lime)
85–100  Background: #f0fdf4  Bar fill: #22c55e   (Emerald)
```

### 10.5 Score Ring Visual (Dashboard)

The primary score display is a circular ring gauge — not a simple number. The ring fills clockwise from 0 (bottom-left) to 100 (full circle). The ring colour matches the grade colour. The score number sits in the centre with the grade letter below it.

```
Ring design spec:
  Outer radius:      80px
  Stroke width:      12px
  Track colour:      #1e293b  (dark slate, fills unfilled portion)
  Fill colour:       grade colour (dynamic)
  Center text:       score number — font: 700, size: 32px, colour: white
  Sub-text:          grade letter — font: 800, size: 18px, colour: grade colour
  Animation:         ring fills on page load over 800ms ease-out
```

### 10.6 Radar Chart Design (Sub-Scores)

The six sub-score dimensions are displayed as a hexagonal radar chart. Colours:

```
Radar chart spec:
  Background:         #0f172a  (dark navy)
  Grid lines:         #334155  (slate, 4 concentric rings at 25/50/75/100)
  Grid labels:        #64748b  (muted slate text)
  Dimension labels:   #e2e8f0  (white-ish)
  Fill:               grade colour at 20% opacity
  Stroke:             grade colour at 80% opacity, 2px
  Data points:        grade colour solid circles, 5px radius
```

---

## 11. Override Rules — Resolved State Handling

### 11.1 Active Override States

| Condition | Score Cap | Grade | Status Code | Badge |
|---|---|---|---|---|
| Address on OFAC SDN list | ≤ 10 | F | `ofac_active` | ⛔ Purple |
| Exploit in DeFiHackLabs (unresolved) | ≤ 30 | F | `exploit_active` | 💀 Deep Red |
| Composite > 55 with active exploit | Capped at 55 | — | `exploit_composite_cap` | — |
| Unverified source code | Code risk = 0 | — | `unverified_source_code` | — |
| Contract age < 30 days | Audit score = 0 | — | `contract_too_new` | — |
| Slither detects `suicidal` | Code risk ≤ 20 | — | `selfdestruct_detected` | — |

### 11.2 Resolved Override States — Exit Pathways

Overrides are not permanent. Each has a defined resolution pathway.

**OFAC Resolution:**
```
Trigger for resolution check:
  - Daily OFAC refresh task compares new SDN list against previously flagged addresses
  - If an address was previously in the SDN list and is no longer present:
      → set override_status = "ofac_resolved"
      → set resolved_at = NOW()
      → score cap lifted on next rescore cycle
      → "Resolution event" appended to score_history with timestamp
      → Telegram broadcast: "⚠️ [Protocol] — OFAC sanction lifted. Scores will update."

Response when resolved:
  "override_applied": false,
  "override_history": [
    {
      "reason": "ofac_sanctions_match",
      "applied_at": "2022-08-08T00:00:00Z",
      "resolved_at": "2025-01-15T00:00:00Z",
      "resolution_note": "Address removed from OFAC SDN list"
    }
  ]
```

**Exploit Resolution:**
```
Resolution is manually triggered via admin API endpoint:
  POST /admin/override/resolve
  Body: {
    "protocol_id": "...",
    "exploit_record_id": "...",
    "resolution_type": "remediated",  -- "remediated" | "compensated" | "redeployed"
    "resolution_evidence": "https://...",  -- link to post-mortem, new audit, etc.
    "resolved_by": "admin"
  }

Resolution conditions (at least ONE required):
  - "remediated": new audit confirming the vulnerability is patched
  - "compensated": verified on-chain proof of user compensation
  - "redeployed": protocol redeployed with new contracts (old address stays flagged)

When resolved:
  → exploit_records.is_resolved = TRUE, resolved_at = NOW()
  → score cap lifted on next rescore
  → "Resolution event" appended to score_history
  → Badge changes from 💀 (exploit_active) to 🔵 (exploit_resolved)
  → Score report shows: "Historical exploit — resolved on [date]. Evidence: [link]"
  → Telegram: "🔵 [Protocol] — Previous exploit marked as resolved. Re-scoring underway."
```

**Resolved state display in API response:**
```json
{
  "override_applied": false,
  "has_override_history": true,
  "override_history": [
    {
      "type": "exploit",
      "status": "resolved",
      "exploit_date": "2023-11-28",
      "loss_usd": 62000000,
      "resolved_at": "2024-03-15",
      "resolution_type": "remediated",
      "resolution_evidence": "https://...",
      "resolution_note": "Vulnerability patched. Re-audited by Trail of Bits."
    }
  ],
  "composite_score": 71.4,
  "grade": "B"
}
```

**Resolved state display in UI:**
A persistent yellow info banner appears on the score report page:
> ⚠️ Historical Notice: This protocol had an exploit on 28 Nov 2023 ($62M lost). The vulnerability was remediated and re-audited in March 2024. This is reflected in the Audit History score. [View resolution evidence →]

---

## 12. Slither Integration — Full Capability Map

### 12.1 Core Analysis

```python
from slither.slither import Slither
from slither.detectors.abstract_detector import DetectorClassification

# Always import as library — never subprocess
sl = Slither(tmp_path)
results = sl.run_detectors()
```

Penalty formula with privacy amplifier:
```python
SEVERITY_WEIGHTS = {HIGH: 10.0, MEDIUM: 4.0, LOW: 1.5, INFO: 0.3, OPT: 0.1}
PRIVACY_SPECIFIC_CHECKS = {
    "reentrancy-eth", "arbitrary-send-eth", "controlled-delegatecall",
    "suicidal", "unprotected-upgrade", "msg-value-loop",
}
# Privacy-specific checks get 1.5× multiplier
code_risk_score = max(0.0, 100.0 - weighted_penalty)
```

### 12.2 Upgradeability Checks

Triggered when EIP-1967 slot read returns non-null implementation address.

```python
from slither.tools.upgradeability.checks import all_checks as upgradeability_checks
```

Checks across all proxy contracts in the protocol ecosystem. Storage slot collisions between proxy and implementation are especially critical for privacy pools — they can corrupt shielded state.

### 12.3 Code Similarity Detector

```python
from slither.tools.similarity.detect_similar_contracts import detect_similar_contracts
```

Threshold: similarity > 0.85 → flagged as mixer fork. Valuable for Track B to contextualise unknown submitted contracts.

### 12.4 Five Custom Privacy Detectors

| File | ARGUMENT | IMPACT | Target |
|---|---|---|---|
| `mixer_reentrancy.py` | `mixer-reentrancy` | HIGH | Reentrancy in deposit/withdraw |
| `zk_verifier_bypass.py` | `zk-verifier-bypass` | HIGH | ZK verifier bypassed via delegatecall |
| `relayer_fee_manipulation.py` | `relayer-fee-manipulation` | MEDIUM | Relayer fee drain |
| `fhe_decryption_acl_bypass.py` | `fhe-decryption-acl-bypass` | HIGH | Zama: decryption ACL not enforced |
| `fhe_handle_leak.py` | `fhe-handle-leak` | MEDIUM | Zama: ciphertext handle exposed |

### 12.5 Role-Weighted Aggregation Across Contracts

```python
ROLE_WEIGHTS = {
    "pool": 1.5, "verifier": 1.4, "vault": 1.3,
    "router": 1.2, "proxy": 1.2, "governance": 1.0,
    "token": 0.8, "timelock": 0.7, "other": 1.0,
}

def aggregate_code_risk(contract_scores: list[dict]) -> float:
    total_weight = sum(ROLE_WEIGHTS.get(c["role"], 1.0) for c in contract_scores)
    weighted_sum = sum(
        c["risk_score"] * ROLE_WEIGHTS.get(c["role"], 1.0)
        for c in contract_scores
    )
    return weighted_sum / total_weight if total_weight > 0 else 0.0
```

---

## 13. Backend Design

### 13.1 Project Directory Structure

```
privascan/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   ├── api/v1/
│   │   ├── router.py
│   │   ├── score.py
│   │   ├── protocols.py
│   │   ├── alerts.py
│   │   ├── keys.py
│   │   ├── admin.py               # Override resolution endpoints
│   │   └── health.py
│   ├── core/
│   │   ├── scoring/
│   │   │   ├── aggregator.py      # Weighted composite + override engine
│   │   │   ├── code_risk.py       # Slither: per-contract + role-weighted
│   │   │   ├── ownership.py       # Web3.py across ecosystem contracts
│   │   │   ├── liquidity.py       # DefiLlama → Dune SIM → adoption proxy
│   │   │   ├── audit_history.py
│   │   │   ├── compliance.py      # OFAC + DeFiHackLabs + resolved state
│   │   │   └── governance.py      # HHI across token + governance contracts
│   │   ├── clients/
│   │   │   ├── etherscan.py
│   │   │   ├── defillama.py
│   │   │   ├── web3_client.py
│   │   │   ├── ofac.py
│   │   │   ├── dune_sim.py        # Dune SIM API — TVL gap fill
│   │   │   └── coingecko.py       # Paid key — price lookups
│   │   ├── detectors/
│   │   │   ├── mixer_reentrancy.py
│   │   │   ├── zk_verifier_bypass.py
│   │   │   ├── relayer_fee_manipulation.py
│   │   │   ├── fhe_decryption_acl_bypass.py
│   │   │   └── fhe_handle_leak.py
│   │   └── models/
│   │       ├── score.py
│   │       ├── protocol.py
│   │       └── alert.py
│   ├── db/
│   │   ├── session.py
│   │   ├── models.py
│   │   └── migrations/
│   ├── workers/
│   │   ├── celery_app.py
│   │   ├── tasks.py
│   │   └── scheduler.py
│   └── bot/
│       ├── telegram_bot.py
│       └── handlers.py
├── tests/
├── Dockerfile
├── railway.json
├── pyproject.toml
└── .env.example
```

---

## 14. Database Schema

```sql
-- Protocol registry (curated protocol metadata)
CREATE TABLE protocols (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(200) NOT NULL,
    slug            VARCHAR(100) UNIQUE,
    defillama_slug  VARCHAR(100),
    description     TEXT,
    website_url     TEXT,
    github_url      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- All contracts in a protocol ecosystem
CREATE TABLE protocol_contracts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocol_id     UUID REFERENCES protocols(id),
    address         VARCHAR(42) NOT NULL,
    chain_id        INTEGER NOT NULL,
    contract_role   VARCHAR(50) NOT NULL,
    -- 'pool' | 'verifier' | 'router' | 'vault' | 'governance'
    -- | 'token' | 'timelock' | 'proxy' | 'other'
    label           VARCHAR(200),
    is_primary      BOOLEAN DEFAULT FALSE,
    added_at        TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(address, chain_id)
);

-- Individual contract tracking (both curated and community)
CREATE TABLE contracts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    address         VARCHAR(42) NOT NULL,
    chain_id        INTEGER NOT NULL,
    chain_name      VARCHAR(50),
    protocol_id     UUID REFERENCES protocols(id),  -- NULL for community scans
    scan_type       VARCHAR(20) NOT NULL DEFAULT 'community',
    is_verified     BOOLEAN DEFAULT FALSE,
    tvl_source      VARCHAR(30),
    tvl_confidence  VARCHAR(20),
    first_seen_at   TIMESTAMPTZ DEFAULT NOW(),
    last_scored_at  TIMESTAMPTZ,
    UNIQUE(address, chain_id)
);

-- Score reports (append-only)
CREATE TABLE score_reports (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id         UUID REFERENCES contracts(id) ON DELETE CASCADE,
    protocol_id         UUID REFERENCES protocols(id),
    composite_score     NUMERIC(5,2) NOT NULL,
    grade               CHAR(1) NOT NULL,
    code_risk_score     NUMERIC(5,2),
    ownership_score     NUMERIC(5,2),
    liquidity_score     NUMERIC(5,2),
    audit_score         NUMERIC(5,2),
    compliance_score    NUMERIC(5,2),
    governance_score    NUMERIC(5,2),
    tvl_usd             NUMERIC(20,2),
    tvl_confidence      VARCHAR(20),
    tvl_source          VARCHAR(30),
    override_applied    BOOLEAN DEFAULT FALSE,
    override_status     VARCHAR(30),
    -- 'ofac_active' | 'exploit_active' | 'ofac_resolved' | 'exploit_resolved'
    raw_findings        JSONB,
    recommendations     TEXT[],
    score_version       VARCHAR(10) DEFAULT '1.0',
    scored_at           TIMESTAMPTZ DEFAULT NOW()
);

-- Override history (resolution events)
CREATE TABLE override_history (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id         UUID REFERENCES contracts(id),
    protocol_id         UUID REFERENCES protocols(id),
    override_type       VARCHAR(20) NOT NULL,  -- 'ofac' | 'exploit'
    override_status     VARCHAR(20) NOT NULL,  -- 'active' | 'resolved'
    applied_at          TIMESTAMPTZ NOT NULL,
    resolved_at         TIMESTAMPTZ,
    resolution_type     VARCHAR(30),           -- 'remediated' | 'compensated' | 'redeployed'
    resolution_evidence TEXT,
    resolution_note     TEXT,
    resolved_by         VARCHAR(100)
);

-- Exploit records (DeFiHackLabs)
CREATE TABLE exploit_records (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_address    VARCHAR(42),
    attacker_address    VARCHAR(42),
    protocol_name       VARCHAR(200),
    exploit_date        DATE,
    loss_usd            NUMERIC(20,2),
    description         TEXT,
    source_url          TEXT,
    is_resolved         BOOLEAN DEFAULT FALSE,
    resolved_at         TIMESTAMPTZ
);

-- OFAC sanctions
CREATE TABLE ofac_addresses (
    address         VARCHAR(42) PRIMARY KEY,
    name            VARCHAR(500),
    program         VARCHAR(200),
    last_updated    TIMESTAMPTZ DEFAULT NOW(),
    was_delisted    BOOLEAN DEFAULT FALSE,
    delisted_at     TIMESTAMPTZ
);

-- Audit records
CREATE TABLE audit_records (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocol_id             UUID REFERENCES protocols(id),
    contract_address        VARCHAR(42),
    auditor                 VARCHAR(200) NOT NULL,
    auditor_tier            INTEGER CHECK (auditor_tier IN (1, 2, 3)),
    audit_date              DATE,
    report_url              TEXT,
    critical_findings       INTEGER DEFAULT 0,
    high_findings           INTEGER DEFAULT 0,
    critical_resolved       BOOLEAN,
    is_formal_verification  BOOLEAN DEFAULT FALSE
);

-- API keys
CREATE TABLE api_keys (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash        VARCHAR(64) UNIQUE NOT NULL,
    tier            VARCHAR(20) DEFAULT 'free',
    owner_email     VARCHAR(200),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    last_used_at    TIMESTAMPTZ,
    is_active       BOOLEAN DEFAULT TRUE
);

-- Watchlists
CREATE TABLE watchlists (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_chat_id    BIGINT NOT NULL,
    contract_id         UUID REFERENCES contracts(id) ON DELETE CASCADE,
    threshold_score     NUMERIC(5,2),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(telegram_chat_id, contract_id)
);

-- Indexes
CREATE INDEX idx_contracts_address_chain ON contracts(address, chain_id);
CREATE INDEX idx_score_reports_contract_time ON score_reports(contract_id, scored_at DESC);
CREATE INDEX idx_ofac_address ON ofac_addresses(address);
CREATE INDEX idx_exploit_contract ON exploit_records(contract_address);
CREATE INDEX idx_watchlists_chat ON watchlists(telegram_chat_id);
CREATE INDEX idx_protocol_contracts_address ON protocol_contracts(address, chain_id);
CREATE INDEX idx_override_history_contract ON override_history(contract_id);
```

---

## 15. Async & Concurrency Architecture

**Async stack:** FastAPI + httpx.AsyncClient + asyncpg + aioredis + python-telegram-bot v20+

**Celery workers:** Separate OS processes for CPU-bound Slither analysis. Six analysers run as Celery `group` — genuine parallel execution across CPU cores. Multi-contract scoring runs per-contract then aggregates.

**Celery config:** `task_soft_time_limit=120`, `task_time_limit=180`, `worker_prefetch_multiplier=1`, `task_acks_late=True`

---

## 16. Telegram Alert System & Visual Design

### 16.1 Three Alert Types

**Type 1 — Ecosystem broadcast (Track A):** Score delta > 10 or new hard flag → all curated protocol subscribers
**Type 2 — Watchlist alert (Track B):** Daily 2am UTC sweep → individual user
**Type 3 — Threshold breach:** `new_score < threshold AND prev_score ≥ threshold` → individual user

### 16.2 Alert Visual Design

Telegram supports a subset of HTML and Markdown. PrivaScan alerts use Telegram's MarkdownV2 format for clean, visually structured messages.

**Standard score change alert:**
```
━━━━━━━━━━━━━━━━━━━━━━━
🟠 PRIVASCAN RISK ALERT
━━━━━━━━━━━━━━━━━━━━━━━

📋 Protocol: Railgun v2
🔗 Chain: Ethereum
🏷️ Type: Curated Protocol

📉 Score Changed
   74 ──▶ 55  (−19 pts)
   Grade: B ──▶ C

🚨 New Flags
   • Critical reentrancy in withdraw()
   • TVL dropped 28% in 7 days

📊 Sub-scores
   Code Risk        ██████░░░░  62/100
   Ownership        ████████░░  91/100
   Liquidity        █████░░░░░  52/100
   Audit History    ████████░░  80/100
   Compliance       ██████████ 100/100
   Governance       █████░░░░░  55/100

💡 Recommendations
   1. Investigate reentrancy in withdraw()
   2. Monitor TVL — continued decline signals stress

🔗 Full report: privascan.xyz/score/ethereum/0xfa70...

⚙️ Stop alerts: /unwatch ethereum 0xfa70...
━━━━━━━━━━━━━━━━━━━━━━━
```

**OFAC override alert (purple badge):**
```
━━━━━━━━━━━━━━━━━━━━━━━
⛔ SANCTIONS ALERT
━━━━━━━━━━━━━━━━━━━━━━━

📋 Protocol: Tornado Cash
🔗 Chain: Ethereum

🚫 OFAC SDN Match Detected
   One or more contract addresses match
   the US Treasury sanctions list.

⚠️ Score Override Applied
   Score: 8/100  Grade: F
   Status: SANCTIONED

   This score will remain at maximum
   override until the sanction is lifted.

🔗 Full report: privascan.xyz/score/ethereum/0x...
━━━━━━━━━━━━━━━━━━━━━━━
```

**Exploit resolution alert (cyan badge):**
```
━━━━━━━━━━━━━━━━━━━━━━━
🔵 RESOLUTION NOTICE
━━━━━━━━━━━━━━━━━━━━━━━

📋 Protocol: [Protocol Name]
🔗 Chain: Ethereum

✅ Previous exploit marked as resolved
   Exploit date: 28 Nov 2023
   Loss: $62,000,000
   Resolution: Vulnerability patched +
               re-audited by Trail of Bits

📈 Score override lifted. Re-scoring now.
🔗 Evidence: [link to post-mortem]

🔔 You will receive an updated score
   report within 30 minutes.
━━━━━━━━━━━━━━━━━━━━━━━
```

**Score display colour mapping in Telegram:**
Since Telegram doesn't render HTML colours, we use emoji colour indicators consistently:

```
Score 85–100: 🟢  (green)
Score 70–84:  🟩  (lighter green)
Score 55–69:  🟡  (yellow)
Score 40–54:  🟠  (orange)
Score 0–39:   🔴  (red)
OFAC:         ⛔  (prohibited)
Exploit:      💀  (skull)
Resolved:     🔵  (blue)
```

**Progress bar rendering in Telegram:**
```python
def render_progress_bar(score: float, width: int = 10) -> str:
    """Render a Unicode progress bar for Telegram messages."""
    filled = round((score / 100) * width)
    empty = width - filled
    return "█" * filled + "░" * empty
```

---

## 17. Frontend Design & Visual System

### 17.1 Tech Stack

Next.js 14 (App Router) · Tailwind CSS · Recharts · v0.dev scaffolding · Vercel

### 17.2 Colour Tokens (Tailwind CSS Custom Config)

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        grade: {
          a:        "#22c55e",   // emerald-500
          b:        "#84cc16",   // lime-500
          c:        "#f59e0b",   // amber-500
          d:        "#f97316",   // orange-500
          f:        "#ef4444",   // red-500
          sanctioned: "#7c3aed", // violet-700
          exploit:    "#b91c1c", // red-800
          resolved:   "#0ea5e9", // sky-500
        },
        surface: {
          base:     "#0f172a",   // slate-900 (page background)
          card:     "#1e293b",   // slate-800 (card background)
          border:   "#334155",   // slate-700
          muted:    "#64748b",   // slate-500
          text:     "#e2e8f0",   // slate-200
        }
      }
    }
  }
}
```

### 17.3 Score Report Page — Full Visual Spec

```
┌─────────────────────────────────────────────────────────────────────┐
│ [bg: #0f172a — dark navy]                                           │
│                                                                     │
│  ← Back   0xfa7093cC6...   [Ethereum]   [CURATED badge — teal]    │
│                                                                     │
│ ┌────────────────────────────────────────────────────────────────┐  │
│ │ [card: #1e293b]                                                │  │
│ │                                                                │  │
│ │  Railgun v2                    [Grade B badge — lime #84cc16] │  │
│ │                                                                │  │
│ │  ┌──────────────┐   ┌──────────────────────────────────────┐  │  │
│ │  │  Score Ring  │   │  Moderate-Low Risk                   │  │  │
│ │  │              │   │  This protocol has some concerns     │  │  │
│ │  │   ●●●●●●●    │   │  but overall shows good security     │  │  │
│ │  │  ● 74   ●   │   │  practices.                          │  │  │
│ │  │  ●  B   ●   │   │                                      │  │  │
│ │  │   ●●●●●●●    │   │  TVL: $84.2M  [high confidence 🟢]  │  │  │
│ │  │ [lime ring]  │   │  Source: DefiLlama                   │  │  │
│ │  └──────────────┘   └──────────────────────────────────────┘  │  │
│ └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│ ┌────────────────────────────────────────────────────────────────┐  │
│ │ Sub-score breakdown              [Radar chart — right side]    │  │
│ │ [card: #1e293b]                                                │  │
│ │                                                                │  │
│ │  Code Risk      ████████░░ 82  [weight 30%]  [lime bar]      │  │
│ │  Ownership      ██████████ 91  [weight 25%]  [emerald bar]   │  │
│ │  Liquidity      ███████░░░ 71  [weight 20%]  [lime bar]      │  │
│ │  Audit History  ████████░░ 80  [weight 12%]  [lime bar]      │  │
│ │  Compliance     ██████████ 100 [weight 8%]   [emerald bar]   │  │
│ │  Governance     █████░░░░░ 55  [weight 5%]   [amber bar]     │  │
│ │                                                                │  │
│ └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│ ┌────────────────────────────────────────────────────────────────┐  │
│ │ Ecosystem Contracts    [card: #1e293b]                         │  │
│ │                                                                │  │
│ │  [POOL]  ETH 0.1 Pool     0x1234... [Ethereum]  82/100  B    │  │
│ │  [POOL]  ETH 1 Pool       0x5678... [Ethereum]  79/100  B    │  │
│ │  [VERIF] ZK Verifier      0x9abc... [Ethereum]  91/100  A    │  │
│ │  [PROXY] Proxy Admin      0xdef0... [Ethereum]  65/100  C    │  │
│ │  [TOKEN] RAIL Token       0x1111... [Ethereum]  88/100  A    │  │
│ │                                                                │  │
│ └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│ ┌────────────────────────────────────────────────────────────────┐  │
│ │ Flags & Recommendations     [card: #1e293b]                    │  │
│ │                                                                │  │
│ │  ⚠️  Upgradeable proxy — no timelock                          │  │
│ │  ⚠️  Governance: top 3 holders = 68%                          │  │
│ │  ✅  OFAC: Not sanctioned                                     │  │
│ │  ✅  Audited: Nethermind 2023 (Tier 2)                       │  │
│ │                                                                │  │
│ │  Recommendations:                                             │  │
│ │  1. Add 48h timelock to proxy admin                          │  │
│ │  2. Resolve 2 medium Slither findings in Pool contract       │  │
│ └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│ ┌────────────────────────────────────────────────────────────────┐  │
│ │ Score History — 30 days   [line chart, lime gradient fill]     │  │
│ │ TVL History — 30 days     [area chart, teal gradient fill]     │  │
│ └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Data: 2h ago · Source: DefiLlama (high) · v1.0 · [Subscribe 🔔]  │
└─────────────────────────────────────────────────────────────────────┘
```

### 17.4 Override State Page Variants

**OFAC Sanctioned Protocol:**
- Full-width purple banner at top of score card: `⛔ OFAC SANCTIONED — This protocol has addresses on the US Treasury SDN list. Score is overridden.`
- Score ring: purple (#7c3aed), displays "10" with "F" grade
- Sub-score bars: all greyed out (#334155) — individual sub-scores not shown during active override

**Exploit Override:**
- Full-width deep red banner: `💀 EXPLOIT HISTORY — Unresolved exploit detected ($62M loss, Nov 2023). Score capped at 30.`
- Score ring: deep red (#b91c1c)

**Resolved State:**
- Amber info banner (non-blocking): `⚠️ Historical: Previous exploit resolved March 2024. See resolution details below.`
- Score ring: shows actual composite score with normal grade colour
- Resolution card appended at bottom of page with exploit date, loss, resolution type, evidence link

---

## 18. API Reference

**Base URL:** `https://api.privascan.xyz/api/v1`
**Auth:** `X-API-Key: your_key`

| Method | Path | Description |
|---|---|---|
| GET | `/score/{chain}/{address}` | Score any EVM contract |
| GET | `/score/{chain}/{address}/history` | Score history — 30 data points |
| GET | `/score/task/{task_id}` | Poll async task |
| POST | `/score/request` | Trigger community scan |
| GET | `/protocols` | Curated protocol directory |
| GET | `/protocols/{slug}` | Protocol detail with all contracts |
| GET | `/protocols/{slug}/contracts` | List all ecosystem contracts |
| POST | `/admin/override/resolve` | Mark override as resolved (admin only) |
| GET | `/health` | System health |

**Rate limits:** Anonymous 10/hr · Free 100/hr · Pro 1000/hr

---

## 19. Infrastructure & Deployment

### 19.1 Railway Services

| Service | Purpose |
|---|---|
| `privascan-api` | FastAPI, port 8000 |
| `privascan-worker` | Celery workers (2 replicas) |
| `privascan-beat` | Celery beat scheduler |
| `privascan-bot` | Telegram bot — isolated |
| `privascan-postgres` | Managed PostgreSQL |
| `privascan-redis` | Cache + Celery broker |

### 19.2 Environment Variables

```bash
APP_ENV=production
SECRET_KEY=<32-byte hex>
SCORE_CACHE_TTL_CURATED=21600       # 6h
SCORE_CACHE_TTL_COMMUNITY=86400     # 24h
SCORE_CACHE_TTL_DUNE=172800         # 48h — extended for Dune-sourced TVL

DATABASE_URL=postgresql+asyncpg://...   # Railway-injected
REDIS_URL=redis://...                   # Railway-injected

ETHERSCAN_API_KEY=<your_key>
ALCHEMY_API_KEY=<your_key>
TELEGRAM_BOT_TOKEN=<your_token>
DUNE_API_KEY=<your_paid_key>
COINGECKO_API_KEY=<your_paid_key>

CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
```

### 19.3 Celery Beat Schedule

```python
CELERYBEAT_SCHEDULE = {
    "rescore-curated": {
        "task": "app.workers.tasks.rescore_all_curated",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    "rescore-watchlist": {
        "task": "app.workers.tasks.rescore_watchlist_addresses",
        "schedule": crontab(minute=0, hour=2),
    },
    "refresh-ofac": {
        "task": "app.workers.tasks.refresh_ofac_list",
        "schedule": crontab(minute=0, hour=3),
    },
    "refresh-exploits": {
        "task": "app.workers.tasks.refresh_exploit_db",
        "schedule": crontab(minute=0, hour=4, day_of_week=0),
    },
    "check-ofac-resolutions": {
        "task": "app.workers.tasks.check_ofac_delisting",
        "schedule": crontab(minute=30, hour=3),  # 30min after OFAC refresh
    },
}
```

---

## 20. Security & Rate Limiting

```python
import hashlib, secrets

def generate_api_key() -> tuple[str, str]:
    raw_key = "pvs_" + secrets.token_hex(28)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, key_hash  # Only hash stored in Postgres
```

Redis token bucket rate limiting. EIP-55 address validation. Chain whitelist enforcement. Admin override resolution endpoint protected by separate admin API key.

---

## 21. Build Plan — 2-Week MVP

### Week 1 — Backend + Scoring Engine

| Day(s) | Tasks | Deliverable |
|---|---|---|
| 1–2 | Project scaffold · Railway setup · Postgres schema (incl. protocol_contracts, override_history tables) · Alembic · Redis · Celery · `.env.example` | Skeleton running, DB migrated |
| 3–4 | Etherscan client · Slither (detectors + upgradeability + similarity + 5 custom detectors) · Role-weighted code risk aggregator · Multi-contract analysis loop | Code risk sub-score across ecosystem contracts |
| 5–6 | Web3.py ownership (per ecosystem) · DefiLlama client · Dune SIM client · Liquidity analyser with decision tree · CoinGecko price client | Ownership + liquidity sub-scores, all TVL sources wired |
| 7 | Score aggregator · Override engine with resolved state · FastAPI endpoints · Redis caching with variable TTL | `GET /score/{chain}/{address}` returning full scored reports |

### Week 2 — Remaining Scores + Distribution + Visual Polish

| Day(s) | Tasks | Deliverable |
|---|---|---|
| 8–9 | Seed audit DB (19 protocols) · Seed protocol_contracts registry · OFAC refresh + resolution check task · DeFiHackLabs parser · Compliance + audit + governance analysers | All 6 sub-scores live · Full multi-contract pipeline |
| 10–11 | Telegram bot (all commands + visual message templates) · Watchlist + alert delivery (Redis pub/sub) · API key auth + rate limiting · Admin override endpoint | Bot live · Alerts firing with designed message format |
| 12–13 | Next.js dashboard (v0.dev scaffold) · Score ring component · Radar chart · Sub-score bars with colour system · Ecosystem contracts table · Score history chart · TVL history chart · Override state page variants | Dashboard live at privascan.xyz with full visual system |
| 14 | Seed all 19 curated protocols with contract registries · End-to-end test · README · GitHub public release · Demo video 3–5 min | MVP shipped |

---

## 22. Deliverables

| Deliverable | Target |
|---|---|
| Live REST API at api.privascan.xyz | End of Week 1 |
| Web dashboard at privascan.xyz | End of Week 2 |
| Telegram bot @PrivaScanBot | Day 11 |
| GitHub repo (public, MIT) | Day 14 |
| OpenAPI docs at /docs | End of Week 1 |
| Demo video (3–5 min) | Day 14 |
| 19 protocols seeded with contract registries | Day 14 |

---

## 23. Monetisation & Grant Strategy

**Primary path:** Open-source + grants — Ethereum Foundation, Optimism RPGF, Gitcoin Grants, Uniswap Foundation.

**Grant pitch:** "PrivaScan is the first free, open risk scoring API that treats privacy protocols as a distinct risk class and scores entire protocol ecosystems — all pools, verifiers, routers, and governance contracts — not just tokens. It includes the industry's first machine-readable resolved override state for exploit remediation and OFAC delisting."

**Future monetisation:** Pro API tier (higher limits, webhooks, batch) · B2B data licensing · Enterprise compliance monitoring.

---

## 24. V2 Roadmap

**Non-EVM support:** Zcash, Monero, Penumbra — 3-dimension metadata scoring (audit maturity 40%, market health 35%, compliance 25%). Separate `metadata_score_task`, CoinGecko full integration, block explorer scraping, regulatory events DB table.

**ML sub-scores:** TVL anomaly detection (Isolation Forest on 90-day time series), bytecode similarity (k-NN), audit report NLP (distilBERT). All additive — V1 scores unchanged.

**Additional V2 features:** Webhooks for Pro tier · Batch scoring endpoint · Score comparison · CSV export · Embeddable score badge widget.

---

## 25. Appendices

### Appendix A — Supported EVM Chains

| Chain | Chain ID | Etherscan | Alchemy |
|---|---|---|---|
| Ethereum | 1 | Yes | Yes |
| Polygon | 137 | Yes | Yes |
| Arbitrum One | 42161 | Yes | Yes |
| Optimism | 10 | Yes | Yes |
| Base | 8453 | Yes | Yes |
| BNB Chain | 56 | Yes | Public RPC |
| Avalanche C-Chain | 43114 | Yes | Public RPC |

### Appendix B — Curated EVM Protocol Index (19 Protocols, V1)

| Protocol | Chain(s) | Type | DefiLlama Slug | TVL Source | TVL Confidence |
|---|---|---|---|---|---|
| Tornado Cash | Ethereum | ETH mixer | `tornado-cash` | DefiLlama | High |
| Tornado Cash Nova | Ethereum | L2 mixer | `tornado-cash-nova` | DefiLlama | High |
| Railgun | ETH, Polygon, BNB | ZK shielded | `railgun` | DefiLlama | High |
| Aztec | Ethereum | ZK rollup | `aztec` | DefiLlama | High |
| Privacy Pools | Ethereum | Mixer + compliance | `privacy-pools` | DefiLlama | High |
| Hinkal | Ethereum | ZK privacy layer | `hinkal` | DefiLlama | High |
| Nocturne | Ethereum | ZK shielded | `nocturne` | DefiLlama | High |
| Typhoon Cash | BNB Chain | Mixer fork | `typhoon-cash` | DefiLlama | High |
| Silent Protocol | Ethereum | ZK transfers | `silent-protocol` | DefiLlama | High |
| 0x0.ai | Ethereum | AI privacy + mixer | `0x0.ai` | DefiLlama | High |
| zkBob | Polygon, Optimism | ZK transfers | `zkbob` | DefiLlama | High |
| Panther Protocol | Polygon | ZK multi-asset | `panther-protocol` | DefiLlama | High |
| Veil Cash | Base L2 | zk-SNARK privacy | `veil-cash` | DefiLlama | High |
| Sherpa Cash | Avalanche | ZK mixer | `sherpa-cash` | DefiLlama | High |
| Zama FHEVM | Ethereum | FHE confidential | `zama` | DefiLlama + adoption proxy | High |
| Cyclone Protocol | BNB, IoTeX | Mixer fork | `cyclone` | DefiLlama (partial) | Medium |
| FOOM Cash | Ethereum | Privacy mixer | `foom-cash` | DefiLlama (minimal) | Medium |
| Nocturne v2 | Ethereum | ZK accounts v2 | Pending | Dune SIM (fallback) | Medium |
| Secret Network | Cosmos/EVM | TEE privacy | Partial | Dune SIM (fallback) | Medium |

### Appendix C — Python Dependencies

```
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
httpx>=0.27.0
pydantic>=2.6.0
pydantic-settings>=2.2.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
aioredis>=2.0.1
celery>=5.3.0
redis>=5.0.0
web3>=6.15.0
slither-analyzer>=0.10.0
python-telegram-bot>=20.8
alembic>=1.13.0
defillama-sdk>=0.1.0
```

### Appendix D — Slither Reference Links

- Python API: https://github.com/crytic/slither/wiki/Python-API
- Detector docs: https://github.com/crytic/slither/wiki/Detector-Documentation
- Upgradeability: https://github.com/crytic/slither/wiki/Upgradeability-Checks
- Code similarity: https://github.com/crytic/slither/wiki/Code-Similarity-detector
- Custom detectors: https://github.com/crytic/slither/wiki/Adding-a-new-detector
- JSON output: https://github.com/crytic/slither/wiki/JSON-output

---

*PrivaScan System Design v5.0 — Final Pre-Build*
*privascan.xyz · api.privascan.xyz · @PrivaScanBot*
*V1: 19 EVM protocols · Full ecosystem multi-contract scoring · Resolved override states · Visual design system*
*V2: Non-EVM (Zcash, Monero) · ML sub-scores · Webhooks · Batch scoring*