# PrivaScan — Product Roadmap
## v1.1 · v2.0 · Beyond

**Author:** angelnath
**Date:** May 2026
**Status:** Post-demo. v1.0 live and stable. Ready to build.

---

## How to read this document

Each feature has:
- **What it is** — plain description
- **Why it matters** — the user problem it solves
- **How to build it** — files to touch, rough approach
- **Effort** — S (half day) / M (1 day) / L (2-3 days) / XL (1 week+)

---

## INFRASTRUCTURE MIGRATION — Do Before Any v1.1 Feature

### 0. Dune SIM Sunset Migration
**Deadline:** August 1, 2026
**Status:** Day 17 task.

Dune SIM (`api.sim.dune.com`) shuts down August 1, 2026. In PrivaScan it is used in exactly one place: community scan TVL fallback in `app/core/clients/dune.py` via `get_contract_balance_usd()`.

**Decision — split by use case:**

| Use case | Current | Replacement |
|---|---|---|
| Community scan contract TVL | Dune SIM | Alchemy getTokenBalances + CoinGecko price |
| Curated protocol TVL | DefiLlama | DefiLlama (no change) |
| Multi-chain TVL aggregation (Feature 16) | N/A | DefiLlama /protocol/{slug} chainTvls |
| TVL anomaly detection (Feature 30) | N/A | DefiLlama TVL history endpoint |

**Why Alchemy for community scans:**
- Zerion API is wallet-focused — unreliable for arbitrary smart contract addresses
- Alchemy already in codebase, already authenticated, already on Railway
- CoinGecko already in codebase for token pricing
- No new API keys, no new Railway env vars, no new services

**How:**
- Replace `dune.py` implementation — keep file, swap internals
- Add `get_token_balances_usd(address, chain_slug)` using Alchemy + CoinGecko
- Return same `TvlResult` shape — nothing else in codebase changes
- Remove `DUNE_API_KEY` from Railway env vars after confirmed working

**Effort:** S

---

# v1.1 — Depth & Distribution

> Goal: make PrivaScan indispensable for people already using it.
> Ship target: 2-3 weeks after v1.0 demo.

---

## Privacy Technology Classification (Judge Feedback — Build First)

### 1. Protocol Privacy Tech Classification

**What:** Classify each curated protocol by its underlying privacy technology. Add `privacy_tech` enum and `privacy_tech_label` to the Protocol model. Show classification badge on protocol cards and detail pages.

**Privacy tech classes:**

| Enum | Label | Protocols | Key Risks |
|---|---|---|---|
| zk_snark | ZK-SNARK | Tornado Cash, Aztec, Railgun, Privacy Pools | Verifier bypass, trusted setup, circuit bugs |
| fhe | Fully Homomorphic Encryption | Zama fhEVM | Decryption ACL bypass, key management |
| tee | Trusted Execution Environment | iExec | Enclave escape, remote attestation forgery |
| mpc | Multi-Party Computation | Hinkal | Key share compromise, collusion |
| stealth | Stealth Addresses | Veil Cash, Cyclone | Linkability, metadata leakage |
| hybrid | Hybrid | Panther, 0x0.ai, FOOM Cash, AnomaPay | Combination of above |
| zk_stark | ZK-STARK | Horizen | No trusted setup but circuit complexity |

**Why:** Direct judge feedback. Different privacy tech = fundamentally different attack surface. A ZK-SNARK mixer and a TEE protocol cannot be fairly compared without knowing the tech class.

**How:**
- Alembic migration: add `privacy_tech VARCHAR(20)` and `privacy_tech_label VARCHAR(50)` to protocols table
- Update `seed_protocols.py` to include `privacy_tech` per protocol
- Include both fields in `GET /protocols/` and `GET /protocols/{slug}` responses
- `PrivacyTechBadge` component: pill badge with tech-specific colour. Add to protocol cards and detail page header
- Scoring modifier map in `aggregator.py`: ZK gets higher code weight, FHE gets higher ownership weight

**Effort:** M

---

## Frontend Pages

### 2. Leaderboard Page `/leaderboard`

**What:** Ranked table of all 14 curated protocols sorted by composite score. Columns: Rank, Protocol, Privacy Tech badge, Grade, Composite, Audit score, TVL tier, Last scored. Sortable. Links to `/protocol/{slug}`.

**Why:** Most shareable page on the site. Showcases privacy tech classification.

**How:**
- Backend: `GET /api/v1/leaderboard?sort=composite&order=asc&limit=20` in protocols.py
- Frontend: `app/leaderboard/page.tsx`. Server component. Revalidate every 5 min. Add to NavBar and Footer.

**Effort:** S

---

### 3. Protocol Comparison Page `/compare`

**What:** Side-by-side two protocols. Radar chart, sub-score bars, grade badges, privacy tech badges. URL: `/compare/railgun/aztec`. Shareable.

**Why:** Core research question PrivaScan answers. Privacy tech context makes comparison meaningful.

**How:**
- Backend: `GET /api/v1/protocols/compare?a=railgun&b=aztec`
- Frontend: `app/compare/[slugA]/[slugB]/page.tsx`. Reuse ScoreRadar, SubScoreBar, GradeBadge.

**Effort:** M

---

### 4. Methodology Page `/methodology`

**What:** Full explanation of scoring: dimensions, weights, grade thresholds, privacy tech classification, data sources, Slither, OFAC, audit tiers, TVL sources.

**Why:** Trust signal. Without it PrivaScan is a black box.

**How:** `app/methodology/page.tsx`. Static content, no fetch. Add "How is this calculated?" link from score page.

**Effort:** S

---

### 5. Score Changelog `/protocol/{slug}/changelog`

**What:** Timeline of every rescore. Timestamp, composite, grade, sub-score movements > 2pts with direction arrow.

**How:**
- Backend: `GET /api/v1/protocols/{slug}/history` — all score_reports, diffs computed
- Frontend: timeline component in protocol detail page

**Effort:** M

---

### 6. Embeddable Grade Badge `/badge/{chain}/{address}.svg`

**What:** Dynamically generated SVG badge. Protocols embed in GitHub README. Renders live grade in PrivaScan colours.

**How:**
- Backend: `GET /api/v1/badge/{chain}/{address}.svg` — fetch from Redis, render SVG, return `image/svg+xml`
- Frontend: "Copy badge code" button on score page

**Effort:** M

---

### 7. API Playground Upgrade

**What:** Full interactive playground on `/api` docs. Pick endpoint, fill params, see live JSON response with syntax highlighting.

**How:** Upgrade `app/api/page.tsx`. React component builds URL client-side, fires request, highlights response with highlight.js.

**Effort:** M

---

## Telegram Bot Commands

### 8. `/top` — Top 5 Safest Protocols

**What:** 5 curated protocols with lowest composite score, with grade emoji and score.

**How:** Add `_cmd_top` to `telegram_bot.py`. Register `CommandHandler("top", _cmd_top)`.

**Effort:** S

---

### 9. `/compare {slug1} {slug2}` — Protocol Comparison

**What:** Side-by-side sub-score table as formatted Telegram monospace message.

**How:** Add `_cmd_compare`. Parse two slugs. Fetch both latest scores. Format as table.

**Effort:** S

---

### 10. `/alert {slug} {grade}` — Grade Drop Alert

**What:** `/alert railgun B` — DM when Railgun drops below grade B.

**How:**
- Store alerts in Redis as `privascan:alert:{chat_id}`
- In `tasks.py` after saving ScoreReport, compare to previous grade, fire DM if degraded
- Add `/unalert {slug}` to remove

**Effort:** M

---

## API Endpoints

### 11. `GET /api/v1/leaderboard`

All curated protocols ranked. Query params: sort, order, limit.

**Effort:** S

---

### 12. `GET /api/v1/protocols/compare`

`?a=railgun&b=aztec` — both protocols full latest scores in one response.

**Effort:** S

---

### 13. `POST /api/v1/score/batch`

Up to 10 {chain, address} pairs scored concurrently. Rate limited 1 batch/min free tier.

**How:** `asyncio.gather()` across all addresses. Batch-specific rate limit key.

**Effort:** M

---

### 14. `GET /api/v1/badge/{chain}/{address}.svg`

See Frontend item 6.

**Effort:** M

---

## Scoring Engine Improvements

### 15. Real Governance Scoring

**What:** Replace static governance score (currently fixed value) with real calculation: multisig threshold, timelock delay, upgradeability pattern, distinct admin count, on-chain governance presence.

**How:** `app/core/scoring/governance.py`. Use existing Alchemy on-chain state + Etherscan for timelock chain.

**Effort:** L

---

### 16. Multi-Chain TVL Aggregation

**What:** Sum TVL across all chains a curated protocol is deployed on. Use DefiLlama `get_protocol_tvl(slug)` total instead of per-chain.

**How:** In `tasks.py` score_ecosystem, fetch total TVL from DefiLlama before scoring. Pass as `tvl_override` to `analyse_liquidity` for every contract.

**Effort:** M

---

### 17. Stale Score Detection

**What:** ScoreReport older than 12h marked stale in API response. Frontend shows "Last scored X hours ago" banner with "Rescore now" button.

**How:** Add `is_stale` and `scored_hours_ago` to API response. Frontend banner if `is_stale=true`.

**Effort:** S

---

### 18. Audit Record Auto-Indexing

**What:** Auto-index new audits by watching GitHub repos of known audit firms for new PDF/markdown reports mentioning known protocol addresses.

**How:** New Celery task `refresh_audit_index` weekly. GitHub API, parse filenames, cross-reference protocols table.

**Effort:** L

---

### 19. Score Confidence Intervals

**What:** Return `composite: 32.4, confidence_low: 28.1, confidence_high: 36.7, confidence: "medium"`. Lower confidence when data is sparse.

**How:** In `engine.py` aggregator, track which sub-scores used real data vs defaults.

**Effort:** M

---

### 20. AI-Generated Risk Summary

**What:** 3-sentence plain-English risk summary per protocol generated by Claude. Cached 6 hours. New `risk_summary` field on ScoreReport.

**How:** After scoring in `tasks.py`, call Anthropic API with sub-scores and key findings. Use `claude-haiku-4-5` for speed and cost.

**Effort:** M

---

## Developer Ecosystem

### 21. Public Score API Dashboard

**What:** Public stats page: total scans, most-scanned protocols, active API keys, average score. Updated daily.

**How:** Celery beat `compute_public_stats` daily. New `GET /api/v1/stats/public`. New `/stats` page or homepage section.

**Effort:** S

---

### 22. Official SDKs

**What:** `privascan-python` (PyPI) and `privascan-js` (npm). Typed methods, auto-retry, rate limit handling.

**How:** httpx-based Python client, fetch-based ESM JS client. Both read `PRIVASCAN_API_KEY` from env.

**Effort:** M per SDK

---

### 23. MCP Server

**What:** Model Context Protocol server exposing PrivaScan as AI tools: `score_contract`, `get_protocol_risk`, `compare_protocols`, `get_leaderboard`.

**How:** `mcp_server.py` using `mcp` Python library. Deploy as separate Railway service. Publish to MCP registry.

**Effort:** M

---

# v2.0 — Platform

> Goal: transform PrivaScan from a tool into a standard.
> Ship target: 2-3 months after v1.1.

---

### 24. Twitter/X OAuth API Key Verification

Alternative to Telegram. OAuth2 flow, Twitter handle stored on ApiKey model.

**Effort:** L

---

### 25. Pro Tier + Stripe ($29/month, 2,000 req/hr)

Stripe checkout, webhook listener, tier upgrade on payment. Pro gets batch scoring, webhook notifications, priority rescore.

**Effort:** XL

---

### 26. Webhook Notifications (Pro Tier)

POST JSON payload to registered URL within 30s of rescore. HMAC-SHA256 signed. Celery task `dispatch_webhooks`.

**Effort:** XL

---

### 27. Non-EVM Chain Support

Zcash, Monero, Penumbra, Aztec native. Chain-type-aware dispatcher. Non-EVM uses lightweight scorer: source availability, audit lookup, community signals.

**Effort:** XL

---

### 28. Curated List Expansion to 50 Protocols

Penumbra, Namada, Secret Network, Oasis, Nocturne, Umbra, Lit Protocol, Threshold, Keep Network, and others. Each needs privacy_tech classification.

**Effort:** L

---

### 29. Real Compliance Data (Chainalysis / TRM Labs)

Replace sparse OFAC XML with Chainalysis Sanctions API and TRM Labs. Fixes compliance_score = 0 for most protocols.

**Effort:** L

---

### 30. Exploit Early Warning System

Monitor every 15 min: flash loan spikes, large withdrawals, admin key movements, proxy implementation changes. TVL anomaly via DefiLlama history (not Dune). Trigger immediate rescore + Telegram alert.

**Effort:** XL

---

# Priority Matrix

| Feature | Version | Effort | Impact | Build order |
|---|---|---|---|---|
| Dune SIM migration (Alchemy) | Infra | S | Critical | 0 |
| Privacy tech classification | v1.1 | M | Very High | 1 |
| Leaderboard page + API | v1.1 | S | High | 2 |
| Methodology page | v1.1 | S | High | 3 |
| /top and /compare bot commands | v1.1 | S | Medium | 4 |
| Public stats dashboard | v1.1 | S | Medium | 5 |
| Stale score detection | v1.1 | S | Medium | 6 |
| Score comparison page | v1.1 | M | High | 7 |
| Embeddable badge | v1.1 | M | High | 8 |
| Batch scoring API | v1.1 | M | High | 9 |
| /alert bot command | v1.1 | M | Medium | 10 |
| Score changelog | v1.1 | M | Medium | 11 |
| API playground upgrade | v1.1 | M | Medium | 12 |
| Multi-chain TVL aggregation | v1.1 | M | Medium | 13 |
| Score confidence intervals | v1.1 | M | Medium | 14 |
| AI-generated risk summary | v1.1 | M | High | 15 |
| Real governance scoring | v1.1 | L | High | 16 |
| Audit record auto-indexing | v1.1 | L | High | 17 |
| Real compliance data | v1.1 | L | High | 18 |
| Curated list expansion (50) | v2.0 | L | High | 19 |
| Twitter/X OAuth | v2.0 | L | Medium | 20 |
| Official SDKs (Python + JS) | v2.0 | M | High | 21 |
| MCP server | v2.0 | M | High | 22 |
| Pro tier + Stripe | v2.0 | XL | High | 23 |
| Webhook notifications | v2.0 | XL | High | 24 |
| Non-EVM chain support | v2.0 | XL | Medium | 25 |
| Exploit early warning system | v2.0 | XL | Very High | 26 |

---

# Build Schedule

| Day | What to ship |
|---|---|
| Day 17 | Dune SIM migration to Alchemy + CoinGecko (remove SIM dependency) |
| Day 18 | Privacy tech classification (DB migration + seed + API + frontend badge) |
| Day 19 | Leaderboard page + API + Methodology page |
| Day 20 | Score comparison page + /compare API |
| Day 21 | Embeddable badge + stale score detection |
| Day 22 | Bot commands: /top, /compare, /alert |
| Day 23 | Batch scoring API + confidence intervals |
| Day 24 | AI risk summaries (Claude haiku integration) |
| Day 25 | Real governance scoring |
| Day 26 | Audit auto-indexing |
| Day 27 | Curated list expansion to 50 protocols |
| Day 28 | SDKs: privascan-python + privascan-js |
| Day 29 | MCP server + registry submission |
| Day 30 | Pro tier + Stripe |

---

# Technical Debt to Clear Before v2

1. Dune SIM sunset — migrate to Alchemy + CoinGecko (Day 17, deadline Aug 1 2026)
2. No test suite — add pytest for audit_analyser, aggregator, /score endpoint before scaling
3. score_reports protocol_id nullable for community scans — confirm join handles NULLs under load

---

*PrivaScan Roadmap — May 2026*
*angelnath · privascanxyz.vercel.app · api-production-c35ab.up.railway.app*
