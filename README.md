# PrivaScan

**Open-source deterministic risk scoring API for EVM privacy protocols.**

privascan.xyz · api.privascan.xyz · [@PrivaScanBot](https://t.me/PrivaScanBot)

---

## What is PrivaScan?

PrivaScan scores entire EVM privacy protocol ecosystems — not just token contracts. Every pool, router, vault, verifier, and governance contract is analysed as a unified risk surface across 6 dimensions:

| Dimension | Weight | What it measures |
|---|---|---|
| Code Risk | 30% | Slither static analysis + 5 custom privacy detectors |
| Ownership | 20% | Admin key centralisation, proxy upgradeability, timelock |
| Liquidity | 20% | TVL size, concentration, source confidence |
| Audit | 15% | Auditor tier, recency, critical finding resolution |
| Compliance | 10% | OFAC SDN list, DeFiHackLabs exploit history |
| Governance | 5% | On-chain governance presence |

Scores are fully explainable and reproducible. No model weights — every point traces to a verifiable data point.

---

## Grading

| Grade | Score Range | Risk Level |
|---|---|---|
| A | 0–20 | Low Risk |
| B | 21–40 | Moderate-Low |
| C | 41–60 | Moderate Risk |
| D | 61–80 | High Risk |
| F | 81–100 | Critical Risk |

Hard overrides apply for OFAC-sanctioned and actively exploited protocols. Override states are resolvable — when an exploit is remediated or a sanction lifted, the protocol re-enters normal scoring with the resolution permanently logged.

---

## API

Base URL: `https://api.privascan.xyz/api/v1`

### Score a contract

```bash
GET /score/{chain}/{address}
```

```bash
curl https://api.privascan.xyz/api/v1/score/ethereum/0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF
```

### List curated protocols

```bash
GET /protocols/
```

### Get protocol detail

```bash
GET /protocols/{slug}
```

### Generate API key

```bash
POST /keys/generate
```

### Check usage

```bash
GET /keys/usage?key=YOUR_KEY
```

Supported chains: `ethereum`, `arbitrum`, `optimism`, `base`, `polygon`, `bsc`, `avalanche`

**Rate limits:**

| Tier | Per minute | Per hour |
|---|---|---|
| Anonymous | 2 | 10 |
| Free (API key) | 15 | 500 |

Get a free API key at [privascan.xyz/keys](https://privascan.xyz/keys) — verified via Telegram in under 30 seconds.

---

## Telegram Bot

[@PrivaScanBot](https://t.me/PrivaScanBot)

| Command | Description |
|---|---|
| `/score ethereum 0x...` | Score any EVM contract |
| `/protocol tornado-cash` | Get protocol summary |
| `/watch ethereum 0x... 60` | Alert when score exceeds threshold |
| `/unwatch 0x...` | Remove from watchlist |
| `/mylist` | View your watchlist |
| `/verify` | Generate API key verification code |
| `/help` | Full command list |

---

## Curated Protocols (V1)

14 EVM privacy protocols pre-seeded and rescored every 6 hours:

Tornado Cash · Railgun · Aztec · Privacy Pools · Hinkal · 0x0.ai · Panther Protocol · Veil Cash · Zama fhEVM · Cyclone Protocol · FOOM Cash · AnomaPay · Horizen · iExec

---

## Self-Hosting

### Requirements

- Docker + Docker Compose
- Node.js 18+ (frontend)
- API keys: Etherscan, Alchemy, Dune, CoinGecko, Telegram Bot Token

### Setup

```bash
git clone https://github.com/only1angelnath/Privascan
cd Privascan
cp .env.example .env
# Fill in your API keys in .env
docker compose up -d
```

Run migrations and seed data:

```bash
docker compose exec api alembic upgrade head
docker compose exec api python -m app.core.data.seed_protocols
docker compose exec api python -m app.core.data.seed_audits
```

Frontend:

```bash
cd frontend
cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

Register the Telegram bot admin:

```bash
# Send /admin_register to @PrivaScanBot once
```

### Docker services

| Service | Role |
|---|---|
| `privascan-api` | FastAPI REST API (port 8000) |
| `privascan-worker` | Celery workers (Slither analysis) |
| `privascan-beat` | Celery beat (6h scheduled rescores) |
| `privascan-bot` | Telegram bot (polling) |
| `privascan-postgres` | PostgreSQL 16 |
| `privascan-redis` | Redis 7 (cache + rate limits) |

---

## Tech Stack

**Backend:** Python 3.12 · FastAPI · Celery · PostgreSQL 16 · Redis 7 · Slither · python-telegram-bot · Web3.py

**Frontend:** Next.js 14 App Router · Tailwind CSS · Recharts · TypeScript

**Deployment:** Railway (backend) · Vercel (frontend)

---

## Architecture
Request → FastAPI (async)
→ Redis cache check → return if fresh
→ ThreadPoolExecutor → Slither (CPU-bound)
→ async I/O → Etherscan + Alchemy + DefiLlama + Dune
→ 6 sub-score analysers → aggregator → override engine
→ store in Postgres + Redis → return scored report
Celery beat rescores all 14 curated protocols every 6 hours. Score changes > 10 points or new hard flags trigger Telegram alerts to all watchlist subscribers.

---

## Roadmap

**V1 (current):** 14 curated EVM protocols · Open EVM scanner · Telegram bot · Free API

**V2:** Non-EVM support (Zcash, Monero, Penumbra) · ML sub-scores (TVL anomaly, bytecode similarity) · Webhooks · Pro tier · Batch scoring · Score embed widget

---

## License

MIT — see [LICENSE](LICENSE)

Not financial advice. Scores are informational only.

---

*Built by [angelnath](https://github.com/only1angelnath) · privascan.xyz*
