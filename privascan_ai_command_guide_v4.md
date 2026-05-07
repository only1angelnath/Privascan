# PrivaScan — Context & Command Guide
## Paste this as your first message in any new AI session

---

## IDENTITY

**Project:** PrivaScan
**Domain:** privascan.xyz
**API:** https://api.privascan.xyz/api/v1
**Frontend:** https://privascan.xyz
**Bot:** @PrivaScanBot
**Type:** Open-source public good · EVM privacy protocol risk scoring
**Language:** Python · V1 MVP (2-week build)

---

## WHAT THIS PROJECT IS

PrivaScan scores EVM privacy protocol smart contract ecosystems for risk. Given a contract address, it:

1. Fetches verified Solidity source from Etherscan v2
2. Runs Slither static analysis (Python library — never subprocess)
3. Reads on-chain ownership via Web3.py across all ecosystem contracts
4. Gets TVL from DefiLlama → falls back to Dune SIM API if not listed
5. Uses CoinGecko (paid key) for token price lookups
6. Queries curated audit DB
7. Checks OFAC SDN list and DeFiHackLabs exploit DB (with resolved state)
8. Reads governance token distribution (HHI formula)
9. Aggregates into 0–100 composite score + A–F letter grade
10. Pushes styled Telegram alerts on meaningful score changes

**Key differentiators:**
- Scores full protocol ecosystems (pools + verifiers + routers + vaults + governance), not just token contracts
- Role-weighted code risk aggregation across all contracts
- Resolved override states — exploits and OFAC sanctions can exit override when resolved
- Visual design system: grade colours, score ring, radar chart, styled Telegram messages
- Dune SIM API for accurate TVL on protocols not listed on DefiLlama

---

## V1 SCOPE — EVM ONLY

V1 is EVM-only. Non-EVM (Zcash, Monero, Penumbra) is documented in the V2 roadmap. Do not implement any non-EVM scoring logic in V1.

---

## CURATED PROTOCOLS — 19 EVM PROTOCOLS

Protocols removed: Umbra Protocol, Twister Cash, Offshore Cash (removed from tracked list).

| Protocol | Chain(s) | DefiLlama Slug | TVL Source | Notes |
|---|---|---|---|---|
| Tornado Cash | Ethereum | `tornado-cash` | DefiLlama high | OFAC sanctioned — override active |
| Tornado Cash Nova | Ethereum | `tornado-cash-nova` | DefiLlama high | OFAC sanctioned |
| Railgun | ETH, Polygon, BNB | `railgun` | DefiLlama high | Active |
| Aztec | Ethereum | `aztec` | DefiLlama high | Active |
| Privacy Pools | Ethereum | `privacy-pools` | DefiLlama high | Active |
| Hinkal | Ethereum | `hinkal` | DefiLlama high | Active |
| Nocturne | Ethereum | `nocturne` | DefiLlama high | Active — confirmed on DefiLlama |
| Typhoon Cash | BNB Chain | `typhoon-cash` | DefiLlama high | Active — confirmed on DefiLlama |
| Silent Protocol | Ethereum | `silent-protocol` | DefiLlama high | Active |
| 0x0.ai | Ethereum | `0x0.ai` | DefiLlama high | Active |
| zkBob | Polygon, Optimism | `zkbob` | DefiLlama high | Active |
| Panther Protocol | Polygon | `panther-protocol` | DefiLlama high | Active |
| Veil Cash | Base L2 | `veil-cash` | DefiLlama high | Active — zk-SNARK on Base, confirmed |
| Sherpa Cash | Avalanche | `sherpa-cash` | DefiLlama high | Active — confirmed on DefiLlama |
| Zama FHEVM | Ethereum | `zama` | DefiLlama high + adoption | FHE — wrapper contracts tracked |
| Cyclone Protocol | BNB, IoTeX | `cyclone` | DefiLlama medium | Partial data |
| FOOM Cash | Ethereum | `foom-cash` | DefiLlama medium | Minimal TVL |
| Nocturne | Ethereum | nocturne_xyz | Dune SIM medium | Active — confirmed on DefiLlama |
| Secret Network | Cosmos/EVM | Partial | Dune SIM medium | Partial EVM exposure |

---

## MULTI-CONTRACT ECOSYSTEM SCORING — CRITICAL DESIGN DECISION

PrivaScan does NOT score just the ERC-20 token contract. It scores the full deployed ecosystem.

### Contract roles tracked per protocol

| Role | Code Risk Weight | What it is |
|---|---|---|
| `pool` | 1.5× | Main TVL holder — highest risk weight |
| `verifier` | 1.4× | ZK proof verifier — bypass risk |
| `vault` | 1.3× | Yield/holding contract |
| `router` | 1.2× | Entry point — fee manipulation |
| `proxy` | 1.2× | Upgrade risk, storage collisions |
| `governance` | 1.0× | Voting/proposal contracts |
| `token` | 0.8× | ERC-20 governance token |
| `timelock` | 0.7× | Delay contract |
| `other` | 1.0× | Anything else |

### Code risk aggregation formula

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

### Protocol contracts table

```sql
CREATE TABLE protocol_contracts (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocol_id   UUID REFERENCES protocols(id),
    address       VARCHAR(42) NOT NULL,
    chain_id      INTEGER NOT NULL,
    contract_role VARCHAR(50) NOT NULL,
    label         VARCHAR(200),    -- "ETH 0.1 Pool", "ZK Verifier", etc.
    is_primary    BOOLEAN DEFAULT FALSE,
    added_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(address, chain_id)
);
```

---

## RISK SCORING MODEL

### Six dimensions (all EVM)

| # | Dimension | Weight | Source |
|---|---|---|---|
| 1 | Code Risk | 30% | Slither across all ecosystem contracts |
| 2 | Ownership Risk | 25% | Web3.py reads across all admin roles |
| 3 | Liquidity Risk | 20% | DefiLlama → Dune SIM fallback |
| 4 | Audit History | 12% | Internal audit DB |
| 5 | Compliance Flags | 8% | OFAC + DeFiHackLabs (with resolved state) |
| 6 | Governance Concentration | 5% | On-chain HHI |

### Composite formula

```
composite = 0.30×code + 0.25×ownership + 0.20×liquidity
          + 0.12×audit + 0.08×compliance + 0.05×governance
```

### Grade + Colour System — apply everywhere consistently

```
Grade A [85–100]  #22c55e  emerald-500  ✅  "Low Risk"
Grade B [70–84]   #84cc16  lime-500     🟢  "Moderate-Low Risk"
Grade C [55–69]   #f59e0b  amber-500    🟡  "Moderate Risk"
Grade D [40–54]   #f97316  orange-500   🟠  "High Risk"
Grade F [0–39]    #ef4444  red-500      🔴  "Critical Risk"

Override states:
OFAC active:       #7c3aed  violet-700   ⛔  "Sanctioned"
Exploit active:    #b91c1c  red-800      💀  "Exploit History"
OFAC resolved:     #0ea5e9  sky-500      🔵  "Sanction Lifted"
Exploit resolved:  #06b6d4  cyan-500     🔵  "Exploit Resolved"
```

### Sub-score bar colours

```
0–29:    fill #ef4444  bg #fef2f2  (red)
30–54:   fill #f97316  bg #fff7ed  (orange)
55–69:   fill #f59e0b  bg #fffbeb  (amber)
70–84:   fill #84cc16  bg #f7fee7  (lime)
85–100:  fill #22c55e  bg #f0fdf4  (emerald)
```

### Hard override rules (active state)

| Condition | Score Cap | Grade | Status |
|---|---|---|---|
| OFAC SDN match | ≤ 10 | F | `ofac_active` |
| DeFiHackLabs exploit (unresolved) | ≤ 30 | F | `exploit_active` |
| Composite > 55 with exploit | Capped at 55 | — | `exploit_composite_cap` |
| Unverified source code | Code risk = 0 | — | `unverified_source_code` |
| Contract age < 30 days | Audit score = 0 | — | `contract_too_new` |
| Slither `suicidal` | Code risk ≤ 20 | — | `selfdestruct_detected` |

---

## RESOLVED OVERRIDE STATES — IMPORTANT

Overrides are NOT permanent. They have exit pathways.

### OFAC resolution (automatic)

```python
# Runs daily, 30min after OFAC refresh (03:30 UTC)
async def check_ofac_delisting(db_session):
    """
    Compare today's SDN list against previously flagged addresses.
    If an address is no longer present, mark as resolved.
    """
    previously_flagged = await get_active_ofac_overrides(db_session)
    current_sdn = await get_current_ofac_set(db_session)

    for address in previously_flagged:
        if address not in current_sdn:
            await resolve_ofac_override(db_session, address)
            await append_override_history(db_session, address, "ofac", "resolved")
            await publish_resolution_alert(address, "ofac")
```

### Exploit resolution (manual, admin endpoint)

```
POST /admin/override/resolve
Body: {
  "protocol_id": "...",
  "exploit_record_id": "...",
  "resolution_type": "remediated" | "compensated" | "redeployed",
  "resolution_evidence": "https://link-to-post-mortem-or-audit",
  "resolved_by": "admin"
}
```

Resolution requires at least ONE of:
- `remediated` — new audit confirming vulnerability patched
- `compensated` — on-chain proof of user compensation
- `redeployed` — new contracts deployed (old address stays flagged, new ones scored fresh)

### Override history in DB

```sql
CREATE TABLE override_history (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id       UUID REFERENCES contracts(id),
    protocol_id       UUID REFERENCES protocols(id),
    override_type     VARCHAR(20) NOT NULL,   -- 'ofac' | 'exploit'
    override_status   VARCHAR(20) NOT NULL,   -- 'active' | 'resolved'
    applied_at        TIMESTAMPTZ NOT NULL,
    resolved_at       TIMESTAMPTZ,
    resolution_type   VARCHAR(30),
    resolution_evidence TEXT,
    resolution_note   TEXT,
    resolved_by       VARCHAR(100)
);
```

### API response when resolved

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

---

## TVL DATA STRATEGY

### Decision tree

```
1. Does DefiLlama have a slug? → YES → use DefiLlama → tvl_confidence: "high"
2. Is it Zama? → use DefiLlama slug "zama" + adoption count → tvl_confidence: "high"
3. No DefiLlama slug → use Dune SIM API per pool address → tvl_confidence: "medium"
   Cache TTL: 48h (extended for Dune data quality vs 24h default)
```

### TVL confidence reference

| Value | Source | Cache TTL |
|---|---|---|
| `high` | DefiLlama | 6h (curated) |
| `medium` | Dune SIM API | 48h |
| `not_applicable` | Adoption proxy only | 6h |

### Dune SIM client

```python
# app/core/clients/dune_sim.py
DUNE_SIM_BASE = "https://api.sim.dune.com/v1/evm"

async def get_contract_tvl_dune(address: str, chain_id: int) -> dict:
    headers = {"X-Dune-Api-Key": settings.DUNE_API_KEY}
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            f"{DUNE_SIM_BASE}/balances/{address}",
            headers=headers,
            params={"chain_ids": str(chain_id)},
        )
        r.raise_for_status()
    balances = r.json().get("balances", [])
    total = sum(b.get("value_usd", 0) or 0 for b in balances
                if not b.get("low_liquidity", False))
    return {"tvl_usd": total, "tvl_source": "dune_sim", "tvl_confidence": "medium"}
```

### CoinGecko (paid key — price lookups only in V1)

```python
# app/core/clients/coingecko.py
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

async def get_token_price_usd(contract_address: str, chain: str) -> float:
    headers = {"x-cg-pro-api-key": settings.COINGECKO_API_KEY}
    # Fetch price by contract address on the relevant platform
    ...
```

---

## TECH STACK — DO NOT SUGGEST ALTERNATIVES

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Task queue | Celery |
| Cache + broker | Redis |
| Database | PostgreSQL (SQLAlchemy async + asyncpg) |
| HTTP client | httpx.AsyncClient |
| On-chain | web3.py |
| Static analysis | slither-analyzer — **Python import, NEVER subprocess** |
| Migrations | Alembic |
| Settings | pydantic-settings |
| Frontend | Next.js 14 App Router + Tailwind CSS |
| Scaffolding | v0.dev |
| Charts | Recharts |
| Bot | python-telegram-bot v20+ (native async) |
| Backend infra | Railway |
| Frontend infra | Vercel |
| TVL primary | DefiLlama (free) |
| TVL fallback | Dune SIM API (paid key) |
| Price lookups | CoinGecko API (paid key) |
| Compiler | solc-select (in Dockerfile) |

**Concurrency:** FastAPI + httpx + asyncpg + aioredis = fully async. Slither = Celery worker processes (separate OS processes). No threading.

---

## INFRASTRUCTURE — 6 RAILWAY SERVICES + VERCEL

| Service | Role |
|---|---|
| `privascan-api` | FastAPI, port 8000 |
| `privascan-worker` | Celery workers (2 replicas) |
| `privascan-beat` | Celery beat + OFAC resolution task |
| `privascan-bot` | Telegram bot — isolated |
| `privascan-postgres` | Managed PostgreSQL |
| `privascan-redis` | Cache + broker |
| Vercel | Next.js frontend |

---

## ENVIRONMENT VARIABLES

```bash
APP_ENV=production
SECRET_KEY=<32-byte hex>
SCORE_CACHE_TTL_CURATED=21600       # 6h
SCORE_CACHE_TTL_COMMUNITY=86400     # 24h
SCORE_CACHE_TTL_DUNE=172800         # 48h — Dune TVL

DATABASE_URL=postgresql+asyncpg://...   # Railway-injected
REDIS_URL=redis://...                   # Railway-injected

ETHERSCAN_API_KEY=<key>
ALCHEMY_API_KEY=<key>
TELEGRAM_BOT_TOKEN=<token>
DUNE_API_KEY=<paid_key>
COINGECKO_API_KEY=<paid_key>

CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
```

---

## SLITHER INTEGRATION

### Always import as library

```python
from slither.slither import Slither
sl = Slither(tmp_path)        # Never: subprocess.run(["slither", ...])
results = sl.run_detectors()
```

### Three capabilities

1. `sl.run_detectors()` — all 80+ built-in detectors
2. `from slither.tools.upgradeability.checks import all_checks` — proxy safety
3. `from slither.tools.similarity.detect_similar_contracts import detect_similar_contracts` — fork detection

### Five custom detectors (in app/core/detectors/)

| File | ARGUMENT | IMPACT |
|---|---|---|
| `mixer_reentrancy.py` | `mixer-reentrancy` | HIGH |
| `zk_verifier_bypass.py` | `zk-verifier-bypass` | HIGH |
| `relayer_fee_manipulation.py` | `relayer-fee-manipulation` | MEDIUM |
| `fhe_decryption_acl_bypass.py` | `fhe-decryption-acl-bypass` | HIGH |
| `fhe_handle_leak.py` | `fhe-handle-leak` | MEDIUM |

### Penalty formula

```python
SEVERITY_WEIGHTS = {HIGH: 10.0, MEDIUM: 4.0, LOW: 1.5, INFO: 0.3}
PRIVACY_CHECKS = {"reentrancy-eth", "arbitrary-send-eth", "controlled-delegatecall",
                   "suicidal", "unprotected-upgrade", "msg-value-loop"}

penalty = sum(
    SEVERITY_WEIGHTS[sev] * (1.5 if check in PRIVACY_CHECKS else 1.0)
    for check, sev in findings
)
code_risk_score = max(0.0, 100.0 - penalty)
```

---

## CELERY BEAT SCHEDULE

| Task | Schedule | Purpose |
|---|---|---|
| `rescore_all_curated` | Every 6h | Refresh 19 curated protocols |
| `rescore_watchlist` | Daily 2am UTC | User watchlist contracts |
| `refresh_ofac_list` | Daily 3am UTC | Download OFAC SDN XML |
| `check_ofac_delisting` | Daily 3:30am UTC | Auto-detect OFAC resolutions |
| `refresh_exploit_db` | Weekly Sunday 4am | Pull DeFiHackLabs |

---

## API ENDPOINTS

| Method | Path | Description |
|---|---|---|
| GET | `/score/{chain}/{address}` | Score any EVM contract |
| GET | `/score/{chain}/{address}/history` | 30-point history |
| GET | `/score/task/{task_id}` | Poll async task |
| POST | `/score/request` | Trigger community scan |
| GET | `/protocols` | Curated directory |
| GET | `/protocols/{slug}` | Protocol detail |
| GET | `/protocols/{slug}/contracts` | All ecosystem contracts |
| POST | `/admin/override/resolve` | Resolve exploit override (admin) |
| GET | `/health` | System status |

**Rate limits:** Anonymous 10/hr · Free 100/hr · Pro 1000/hr

---

## TELEGRAM BOT COMMANDS

| Command | Description |
|---|---|
| `/scan <chain> <address>` | Score any EVM contract |
| `/watch <protocol_name>` | Broadcast alerts for curated protocol |
| `/watch <chain> <address> [threshold=N]` | Watchlist any contract |
| `/unwatch <chain> <address>` | Remove from watchlist |
| `/watchlist` | Show all watching |
| `/protocols` | List curated with grades |
| `/help` | Commands |

### Alert visual format (MarkdownV2)

```
━━━━━━━━━━━━━━━━━━━━━━━
🟠 PRIVASCAN RISK ALERT
━━━━━━━━━━━━━━━━━━━━━━━
📋 Protocol: [Name]
📉 Score: 74 ──▶ 55 (−19)
   Grade: B ──▶ C
🚨 New Flags:
   • [flag description]
📊 Sub-scores:
   Code Risk    ██████░░░░  62/100
   [repeat for all 6]
🔗 privascan.xyz/score/...
━━━━━━━━━━━━━━━━━━━━━━━
```

Score emoji in alerts: 🟢 A · 🟩 B · 🟡 C · 🟠 D · 🔴 F · ⛔ OFAC · 💀 Exploit · 🔵 Resolved

Progress bar: `"█" * filled + "░" * (10 - filled)` where `filled = round((score/100) * 10)`

---

## DATABASE — KEY TABLES

| Table | Purpose |
|---|---|
| `protocols` | Curated protocol metadata |
| `protocol_contracts` | All contracts per protocol with role labels |
| `contracts` | All tracked addresses (curated + community) |
| `score_reports` | Append-only history — has `override_status` field |
| `override_history` | Resolution events — applied_at, resolved_at, evidence |
| `exploit_records` | DeFiHackLabs — has `is_resolved`, `resolved_at` |
| `ofac_addresses` | OFAC SDN — has `was_delisted`, `delisted_at` |
| `audit_records` | Curated audits — scoped to protocol_id |
| `api_keys` | SHA-256 hashes only |
| `watchlists` | `(telegram_chat_id, contract_id, threshold_score)` |

---

## FRONTEND VISUAL DESIGN SYSTEM

### Tailwind colour tokens

```javascript
grade: {
  a: "#22c55e", b: "#84cc16", c: "#f59e0b",
  d: "#f97316", f: "#ef4444",
  sanctioned: "#7c3aed", exploit: "#b91c1c",
  resolved: "#0ea5e9"
},
surface: {
  base: "#0f172a", card: "#1e293b",
  border: "#334155", muted: "#64748b", text: "#e2e8f0"
}
```

### Score ring

Circular SVG gauge. Fills clockwise. Colour = grade colour. Center: score number (700 weight, 32px). Below: grade letter (800 weight, 18px, grade colour). Animation: 800ms ease-out fill on load.

### Radar chart

Hexagonal, 6 dimensions. Background #0f172a. Grid #334155. Fill = grade colour at 20% opacity. Stroke = grade colour 80%, 2px.

### Override page variants

- **OFAC active:** Full-width purple banner, score ring purple #7c3aed, sub-scores greyed out
- **Exploit active:** Full-width deep red banner, ring #b91c1c
- **Resolved:** Amber info banner (non-blocking), normal score ring, resolution card at bottom

---

## CODE RULES — ALWAYS FOLLOW

1. FastAPI handlers: `async def` with `await`
2. HTTP: `httpx.AsyncClient` only — never `requests`
3. DB: `asyncpg` via SQLAlchemy async session
4. Redis: `aioredis`
5. Celery tasks: **sync** `def` — separate processes, not event loop
6. Slither: always import — never subprocess
7. Each analyser returns `{"risk_score": float, "flags": list[str], "details": dict}`
8. Aggregator takes 6 dicts → weighted composite → overrides → grade
9. Pydantic v2 syntax throughout
10. `score_reports`: append-only — INSERT only, never UPDATE
11. `tvl_confidence` always explicitly set
12. API keys: `secrets.token_hex(28)`, store only SHA-256 hash
13. Non-EVM: do not implement in V1 — V2 only
14. Multi-contract: always score ecosystem contracts, not just token
15. Override states: always check `override_history` table before displaying score

---

## WHAT NEVER TO CHANGE

- Language: Python
- Framework: FastAPI
- Task queue: Celery
- Static analysis: Slither as Python import — never subprocess
- Concurrency: async I/O + Celery workers — no threads
- Scoring: rule-based deterministic in V1 — no ML
- TVL fallback: Dune SIM API — not CoinGecko proxy assumptions
- Domain: privascan.xyz
- Non-EVM: V2 only
- Contracts: always score full ecosystem, never just token

---

## SPECIAL PROTOCOL NOTES

**Tornado Cash / Nova:** OFAC override active at launch. Include in curated list. Will show score 8/100, grade F, purple sanctioned badge. Include in history for completeness.

**Zama FHEVM:** DefiLlama slug `zama` now live (PR #18951 merged, $27.68M TVS on first run). TVL tracks cUSDC, ctGBP, cUSDT wrapper contracts. Also count deployed FHEVM contracts as adoption signal. Two custom Slither detectors: `fhe-decryption-acl-bypass` (HIGH) and `fhe-handle-leak` (MEDIUM). Flag coprocessor + KMS dependency as centralisation risk in ownership.

**Sherpa Cash:** Confirmed on DefiLlama at `sherpa-cash`. TVL = sum of Sherpa Cash privacy pool balances in AVAX. Avalanche chain (chain_id=43114).

**Nocturne:** Confirmed on DefiLlama at `nocturne`. Ethereum. TVL ~$68K.

**Veil Cash:** Confirmed on DefiLlama. zk-SNARK privacy on Base L2 (chain_id=8453).

**Nocturne:** Confrimed on DefiLlama at `nocturne_xyz`. Use Dune SIM API for pool contract balances. Cache 48h.

**Secret Network:** Partial EVM exposure (IBC bridge + EVM compatibility layer). Use Dune SIM for EVM-side contracts.

---

*PrivaScan AI Command Guide *
*V1: 19 EVM protocols · Multi-contract ecosystem scoring · Resolved overrides · Visual design system · Dune SIM TVL fallback*
*V2: Non-EVM (Zcash, Monero) · ML sub-scores · Webhooks*
*Paste this first in any new session — Claude, Cursor, GPT, Copilot*
