# Adding a New Protocol to PrivaScan

One file to edit, one command to run. No migrations needed.

---

## Step 1 — Add the protocol to the seed file

Open `app/core/data/seed_protocols.py` and append a new entry to the `PROTOCOLS` list:

```python
{
    "name": "Protocol Name",           # Display name
    "slug": "protocol-slug",           # URL-safe, lowercase, hyphens only
    "defillama_slug": "defillama-slug",# From DefiLlama URL — None if not listed
    "description": "One sentence.",
    "website_url": "https://...",
    "github_url": "https://github.com/...",  # None if no public repo
    "contracts": [
        {
            "address": "0x...",         # Always lowercase
            "chain": "ethereum",        # Must be one of the 7 supported chains (see below)
            "role": "pool",             # pool | router | token | treasury | governance |
                                        # verifier | vault | other
            "label": "Human label",     # Short description shown in API/UI
            "is_primary": True,         # True for ONE contract per protocol only
        },
        # ... more contracts
    ],
},
```

**Supported chain slugs:**

| Slug | Chain | Chain ID |
|---|---|---|
| `ethereum` | Ethereum Mainnet | 1 |
| `polygon` | Polygon PoS | 137 |
| `arbitrum` | Arbitrum One | 42161 |
| `optimism` | Optimism | 10 |
| `base` | Base | 8453 |
| `bnb` | BNB Chain | 56 |
| `avalanche` | Avalanche C-Chain | 43114 |

> Contracts on unsupported chains (Gnosis, ETC, IoTeX, Solana, etc.) are automatically
> skipped with a `seed.unknown_chain` warning — add the chain to `app/core/clients/chains.py`
> first if you need it.

---

## Step 2 — Run the idempotent seeder

```bash
docker compose exec worker python3 -m app.core.data.seed_protocols
```

The seeder skips any slug that already exists — safe to run repeatedly.
Only the new protocol gets inserted.

---

## Step 3 — Verify

```bash
# Check it landed in the DB
docker compose exec postgres psql -U privascan -d privascan -c "
SELECT p.name, p.slug, COUNT(pc.id) AS contracts
FROM protocols p
LEFT JOIN protocol_contracts pc ON pc.protocol_id = p.id
WHERE p.slug = 'your-new-slug'
GROUP BY p.name, p.slug;"

# Hit the API
curl -s http://localhost:8000/api/v1/protocols/your-new-slug | python3 -m json.tool
```

---

## Quick checklist before submitting a new protocol

- [ ] All addresses are valid 42-char `0x...` EVM addresses (checksummed or lowercase, both work)
- [ ] `slug` is unique — check with `curl http://localhost:8000/api/v1/protocols/`
- [ ] `is_primary: True` is set on exactly ONE contract per protocol
- [ ] Addresses verified against block explorer (Etherscan / BscScan / etc.)
- [ ] Chain slug is in the supported list above
- [ ] `defillama_slug` tested at `https://api.llama.fi/protocol/<slug>`

---

## Adding a contract to an existing protocol

Edit the `contracts` list for that protocol in `seed_protocols.py`, then:

```bash
# The seeder won't re-insert the protocol (slug exists) but won't add the new contract either.
# Use a direct DB insert for adding contracts to already-seeded protocols:

docker compose exec postgres psql -U privascan -d privascan -c "
INSERT INTO protocol_contracts (id, protocol_id, address, chain_id, contract_role, label, is_primary, added_at)
SELECT
  gen_random_uuid(),
  p.id,
  '0xyournewaddress',
  1,           -- chain_id: 1=ETH, 137=Polygon, 42161=ARB, 10=OP, 8453=Base, 56=BNB, 43114=AVAX
  'pool',      -- role
  'Your Label',
  false,       -- is_primary
  NOW()
FROM protocols p WHERE p.slug = 'existing-protocol-slug';"
```

Or simply re-run the seeder after adding the contract — if you haven't deployed yet (dev environment), wipe and reseed:

```bash
docker compose exec postgres psql -U privascan -d privascan -c \
  "TRUNCATE protocol_contracts, protocols RESTART IDENTITY CASCADE;"
docker compose exec worker python3 -m app.core.data.seed_protocols
```

---

## File locations

| File | Purpose |
|---|---|
| `app/core/data/seed_protocols.py` | Master protocol + contract registry |
| `app/db/models.py` | `Protocol` and `ProtocolContract` ORM models |
| `app/api/v1/protocols.py` | REST endpoints that read from the registry |
| `docs/ADD_PROTOCOL.md` | This file |

---

## Adding audit records for a new protocol

After seeding the protocol contracts, add its audit history to `app/core/data/seed_audits.py`:

```python
# In the AUDITS dict, add:
"your-new-slug": [
    {
        "auditor": "Trail of Bits",   # auditor name
        "auditor_tier": 1,             # 1=Tier1, 2=Tier2, 3=Tier3/community
        "audit_date": date(2024, 6, 1),
        "report_url": "https://link-to-report.pdf",
        "critical_findings": 0,
        "high_findings": 1,
        "critical_resolved": True,
        "is_formal_verification": False,
    },
],
```

Then run:
```bash
docker compose exec worker python3 -m app.core.data.seed_audits
```

**If the protocol has no public audits yet** — omit it from AUDITS entirely.
The `audit_analyser` will return 80.0 (maximum audit risk) automatically.
This is the correct behaviour — no audit = high risk.

### Auditor tier reference

| Tier | Auditors |
|---|---|
| 1 | Trail of Bits, OpenZeppelin, Consensys Diligence, Zellic, Spearbit, ABDK, Sigma Prime, Certora, Veridise |
| 2 | Certik, Hacken, Quantstamp, Peckshield, Dedaub, Salus Security |
| 3 | All others, community audits, internal reviews |
