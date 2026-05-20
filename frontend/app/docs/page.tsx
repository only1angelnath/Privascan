'use client'
import { useEffect, useRef } from 'react'
import { useSearchParams } from 'next/navigation'
import { Suspense } from 'react'
import Link from 'next/link'

const SECTIONS = [
  { id: 'whitepaper',  title: 'Whitepaper'                          },
  { id: 'intro',       title: 'Introduction'                        },
  { id: 'auth',        title: 'Authentication'                      },
  { id: 'rate',        title: 'Rate Limits'                         },
  { id: 'api',         title: 'API Endpoints'                       },
  { id: 'score',       title: '  GET /score/{chain}/{address}'           },
  { id: 'history',     title: '  GET /score/.../history'                },
  { id: 'request',     title: '  POST /score/request'                   },
  { id: 'protocols',   title: '  GET /protocols/'                       },
  { id: 'protocol',    title: '  GET /protocols/{slug}'                 },
  { id: 'keygen',      title: '  POST /keys/generate'                   },
  { id: 'errors',      title: 'Error Reference'                     },
  { id: 'grades',      title: 'Grade System'                        },
  { id: 'dims',        title: 'Risk Dimensions'                     },
]

function M({ m, path }: { m: string; path: string }) {
  const bg = m === 'GET' ? '#1d4ed8' : '#15803d'
  return (
    <div className="flex items-center gap-3 mb-4">
      <span className="font-mono text-xs font-bold px-2.5 py-1 rounded" style={{ background: bg, color: '#fff' }}>{m}</span>
      <span className="font-mono text-sm text-slate-300">{path}</span>
    </div>
  )
}

function Tag({ children }: { children: React.ReactNode }) {
  return <code className="font-mono text-xs px-1.5 py-0.5 rounded" style={{ color: '#00d4ff', background: 'rgba(0,212,255,0.1)' }}>{children}</code>
}

function Gold({ children }: { children: React.ReactNode }) {
  return <span style={{ color: '#f59e0b' }}>{children}</span>
}

function Code({ children }: { children: React.ReactNode }) {
  return (
    <div className="glass rounded-xl p-4 font-mono text-xs text-slate-300 leading-relaxed my-3 overflow-x-auto whitespace-pre">
      {children}
    </div>
  )
}

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <div id={id} className="glass rounded-xl p-8 scroll-mt-24">
      <h2 className="font-orbitron text-xl font-bold text-white mb-6 pb-4" style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        {title}
      </h2>
      <div className="space-y-4 font-mono text-sm text-slate-400 leading-relaxed">
        {children}
      </div>
    </div>
  )
}

function DocsContent() {
  const params = useSearchParams()
  const didScroll = useRef(false)

  useEffect(() => {
    if (didScroll.current) return
    const section = params.get('section')
    if (section) {
      setTimeout(() => {
        const el = document.getElementById(section)
        if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'start' }); didScroll.current = true }
      }, 300)
    }
  }, [params])

  return (
    <div className="max-w-7xl mx-auto px-6 pt-24 pb-16 flex gap-8 min-h-screen">
      {/* Sidebar */}
      <aside className="w-52 shrink-0 hidden md:block">
        <div className="sticky top-24">
          <div className="font-mono text-xs tracking-widest mb-4" style={{ color: '#00d4ff' }}>// CONTENTS</div>
          <nav className="space-y-0.5">
            {SECTIONS.map(s => (
              <a key={s.id} href={`#${s.id}`}
                className="block font-mono text-xs px-3 py-1.5 rounded transition-colors hover:text-white hover:bg-white/[0.05] cursor-pointer"
                style={{ color: '#4a7090' }}>
                {s.title}
              </a>
            ))}
          </nav>
          <div className="mt-6 pt-4" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
            <a href="https://github.com/only1angelnath/Privascan" target="_blank" rel="noreferrer"
              className="font-mono text-xs text-slate-500 hover:text-slate-300 transition-colors cursor-pointer block mb-2">
              GitHub ↗
            </a>
            <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer"
              className="font-mono text-xs text-slate-500 hover:text-slate-300 transition-colors cursor-pointer block">
              OpenAPI / Swagger ↗
            </a>
          </div>
        </div>
      </aside>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-6">

        <Section id="whitepaper" title="Whitepaper">
          <p>
            The full PrivaScan whitepaper covers the complete risk methodology, scoring formulas,
            detector specifications, audit tier definitions, and governance scoring plans.
            It is the authoritative reference for anyone building on or integrating with PrivaScan.
          </p>
          <a href="https://privascan.gitbook.io/docs" target="_blank" rel="noreferrer"
            className="inline-flex items-center gap-2 font-orbitron text-xs font-bold px-5 py-3 rounded-lg transition-all cursor-pointer hover:opacity-90 mt-2"
            style={{ background: '#00d4ff', color: '#0a0f1e' }}>
            Read the Whitepaper on GitBook ↗
          </a>
          <div className="glass rounded-xl p-5 mt-4" style={{ borderColor: 'rgba(245,158,11,0.2)' }}>
            <div className="font-orbitron text-xs font-bold mb-3" style={{ color: '#f59e0b' }}>QUICK SUMMARY</div>
            <ul className="space-y-2 text-xs">
              <li>• <strong className="text-white">Composite score</strong> = 0.30×code + 0.25×ownership + 0.20×liquidity + 0.12×audit + 0.08×compliance + 0.05×governance</li>
              <li>• <strong className="text-white">Grades</strong> run A (0–20, safe) through F (81–100, critical). Hard overrides exist for OFAC and active exploits.</li>
              <li>• <strong className="text-white">Curated protocols</strong> are rescored every 6 hours. Community scans are cached for 1 hour.</li>
              <li>• <strong className="text-white">Slither</strong> is run against verified bytecode with 5 custom privacy-specific detectors.</li>
              <li>• <strong className="text-white">OFAC</strong> screening runs against the consolidated SDN list, updated daily.</li>
            </ul>
          </div>
        </Section>

        <Section id="intro" title="Introduction">
          <p>
            PrivaScan is an open-source risk scoring engine for EVM smart contracts, purpose-built
            for privacy protocols. It was created because privacy protocols handle a fundamentally
            different threat model than standard DeFi — they shield transactions by design, which
            means their own risks are harder to see.
          </p>
          <p>
            The API returns a deterministic risk score for any EVM contract on 7 supported chains.
            No black boxes, no opinions — every score is reproducible from the same inputs.
          </p>
          <div className="glass rounded-xl p-4 mt-2" style={{ borderColor: 'rgba(0,212,255,0.15)' }}>
            <div className="font-mono text-xs text-slate-500 mb-1">Base URL</div>
            <div className="font-mono text-sm" style={{ color: '#00d4ff' }}>http://localhost:8000/api/v1</div>
            <div className="font-mono text-xs text-slate-600 mt-2">Supported chains: ethereum · arbitrum · optimism · base · polygon · bsc · avalanche</div>
          </div>
        </Section>

        <Section id="auth" title="Authentication">
          <p>
            The API works without authentication at a lower rate limit. To get a higher limit,
            generate a free API key at <Tag>/api/v1/keys/generate</Tag> and include it as a header.
          </p>
          <Code>{`# Without a key — 10 requests/hour (IP-based)
curl https://localhost:8000/api/v1/score/ethereum/0x910Cbd...

# With a free key — 500 requests/hour
curl https://localhost:8000/api/v1/score/ethereum/0x910Cbd... \
  -H "X-API-Key: ps_your_key_here"`}</Code>
          <p>
            API keys are prefixed with <Tag>ps_</Tag> and are 46 characters long.
            The raw key is shown once at generation and never stored — we store only the SHA-256 hash.
            Treat your key like a password.
          </p>
        </Section>

        <Section id="rate" title="Rate Limits">
          <p>Rate limits are enforced per hour using a sliding window in Redis. The window resets 1 hour after your first request in that window.</p>
          <div className="glass rounded-xl overflow-hidden mt-3">
            <div className="grid text-xs text-slate-500 tracking-widest px-5 py-3"
              style={{ gridTemplateColumns: '1fr 1fr 1fr 1fr', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
              <span>TIER</span><span>LIMIT</span><span>IDENTIFIER</span><span>HOW TO GET</span>
            </div>
            {[
              ['Anonymous', '10 req/hr',  'Client IP',  'No action needed'],
              ['Free',      '500 req/hr', 'Key hash',   'Generate key at /keys'],
              ['Pro',       '1,000 req/hr','Key hash',  'Coming soon'],
            ].map(([t,l,i,h]) => (
              <div key={t} className="grid px-5 py-3 border-b text-sm"
                style={{ gridTemplateColumns: '1fr 1fr 1fr 1fr', borderColor: 'rgba(255,255,255,0.05)' }}>
                <span className="text-white">{t}</span>
                <span style={{ color: '#00d4ff' }}>{l}</span>
                <span className="text-slate-400">{i}</span>
                <span className="text-slate-500">{h}</span>
              </div>
            ))}
          </div>
          <p className="mt-3 text-xs">
            On a 429 response, the <Gold>Retry-After</Gold> header tells you how many seconds to wait.
            Rate limit keys in Redis use the format <Tag>rate:{'{tier}'}:{'{identifier}'}</Tag>.
          </p>
        </Section>

        <Section id="api" title="API Endpoints">
          <p>All endpoints return JSON. Errors follow a consistent shape: <Tag>{"{ detail: string }"}</Tag>.</p>
        </Section>

        <Section id="score" title="GET /score/{'{chain}'}/{'{address}'}">
          <M m="GET" path="/api/v1/score/{chain}/{address}" />
          <p>
            The core endpoint. Runs a full risk pipeline and returns a composite score for any EVM contract.
            Results are cached in Redis for 1 hour — subsequent requests return instantly with <Tag>cached: true</Tag>.
          </p>
          <p className="text-xs text-slate-500">
            First-time scans may take 30–60 seconds while Slither analyses the bytecode.
          </p>
          <Code>{`curl http://localhost:8000/api/v1/score/ethereum/0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF \
  -H "X-API-Key: ps_your_key_here"

{
  "address":         "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf",
  "chain":           "ethereum",
  "chain_id":        1,
  "composite_score": 74.2,
  "grade":           "B",
  "grade_label":     "Moderate-Low Risk",
  "override_applied": false,
  "override_status":  null,
  "sub_scores": {
    "code":        82.0,
    "ownership":   91.0,
    "liquidity":   71.0,
    "audit":       80.0,
    "compliance":  100.0,
    "governance":  50.0
  },
  "details": {
    "code":       { "is_verified": true, "high_count": 0, "medium_count": 2, "findings": [] },
    "liquidity":  { "tvl_usd": 12400000, "tvl_tier": "Large", "tvl_source": "defillama" },
    "compliance": { "score": 100 }
  },
  "scored_at": "2026-05-17T21:00:00Z",
  "cached":    false
}`}</Code>
        </Section>

        <Section id="history" title="GET /score/{'{chain}'}/{'{address}'}/history">
          <M m="GET" path="/api/v1/score/{chain}/{address}/history" />
          <p>Returns historical score snapshots, newest first. Use <Gold>?limit=N</Gold> to control count (default 10, max 30).</p>
          <Code>{`curl http://localhost:8000/api/v1/score/ethereum/0x910Cbd.../history?limit=5

{
  "history": [
    { "composite_score": 74.2, "grade": "B", "scored_at": "2026-05-17T21:00:00Z" },
    { "composite_score": 76.1, "grade": "B", "scored_at": "2026-05-17T15:00:00Z" }
  ]
}`}</Code>
        </Section>

        <Section id="request" title="POST /score/request">
          <M m="POST" path="/api/v1/score/request" />
          <p>
            Dispatches a background Celery task for scoring. Useful when you want to trigger a rescore
            without waiting for the result. Returns a <Tag>task_id</Tag> you can poll.
          </p>
          <Code>{`curl -X POST http://localhost:8000/api/v1/score/request \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ps_your_key_here" \
  -d '{ "chain": "ethereum", "address": "0x910Cbd..." }'

{ "task_id": "abc123-def456-...", "status": "queued" }

# Poll the result:
curl http://localhost:8000/api/v1/score/task/abc123-def456-...`}</Code>
        </Section>

        <Section id="protocols" title="GET /protocols/">
          <M m="GET" path="/api/v1/protocols/" />
          <p>Returns all curated protocols with metadata. Supports <Gold>?page</Gold> and <Gold>?page_size</Gold> (default 20).</p>
          <Code>{`curl http://localhost:8000/api/v1/protocols/

{
  "count": 14,
  "protocols": [
    {
      "slug":        "railgun",
      "name":        "Railgun",
      "description": "ZK shielded balances for private DeFi",
      "website_url": "https://railgun.org",
      "github_url":  "https://github.com/Railgun-Community"
    }
  ]
}`}</Code>
        </Section>

        <Section id="protocol" title="GET /protocols/{'{slug}'}">
          <M m="GET" path="/api/v1/protocols/{slug}" />
          <p>Full protocol detail including all deployed contracts and the latest ecosystem score.</p>
          <Code>{`curl http://localhost:8000/api/v1/protocols/railgun

{
  "slug": "railgun",
  "name": "Railgun",
  "contracts": [
    { "address": "0xfa7093...", "chain_id": 1, "role": "core", "is_primary": true }
  ],
  "latest_score": {
    "composite_score": 74.2,
    "grade": "B",
    "grade_label": "Moderate-Low Risk"
  }
}`}</Code>
        </Section>

        <Section id="keygen" title="POST /keys/generate">
          <M m="POST" path="/api/v1/keys/generate" />
          <p>
            Generates a new API key. The raw key is returned once — never stored on our end.
            Copy it immediately. If lost, generate a new one.
          </p>
          <Code>{`curl -X POST http://localhost:8000/api/v1/keys/generate \
  -H "Content-Type: application/json" \
  -d '{ "email": "you@example.com", "tier": "free" }'

{
  "api_key": "ps_CwkQ0JQnWeTFIgJbNMZ7Jukxdftyd0RBPuiPAbtGGjQ",
  "tier":    "free",
  "email":   "you@example.com",
  "message": "Store this key safely. Rate limit: 500 req/hr."
}`}</Code>
        </Section>

        <Section id="errors" title="Error Reference">
          <p>All errors return a JSON body with a <Tag>detail</Tag> field explaining what went wrong.</p>
          <div className="glass rounded-xl overflow-hidden mt-3">
            <div className="grid text-xs text-slate-500 tracking-widest px-5 py-3"
              style={{ gridTemplateColumns: '1fr 3fr 2fr', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
              <span>CODE</span><span>MEANING</span><span>COMMON CAUSE</span>
            </div>
            {[
              ['400', 'Bad request',        'Missing or invalid parameters'],
              ['401', 'Unauthorized',        'Invalid or inactive API key'],
              ['404', 'Not found',           'Unknown protocol slug or task ID'],
              ['422', 'Validation error',    'Wrong field types in request body'],
              ['429', 'Rate limit exceeded', 'Too many requests — check Retry-After header'],
              ['500', 'Server error',        'Slither failed or upstream API unavailable'],
            ].map(([c,m,e]) => (
              <div key={c} className="grid px-5 py-3 border-b text-xs"
                style={{ gridTemplateColumns: '1fr 3fr 2fr', borderColor: 'rgba(255,255,255,0.05)' }}>
                <span className="font-orbitron font-bold" style={{ color: parseInt(c) >= 500 ? '#ef4444' : parseInt(c) >= 400 ? '#f59e0b' : '#22c55e' }}>{c}</span>
                <span className="text-slate-300">{m}</span>
                <span className="text-slate-500">{e}</span>
              </div>
            ))}
          </div>
        </Section>

        <Section id="grades" title="Grade System">
          <p>Scores run from 0 to 100. Lower is safer. Grades are assigned as follows:</p>
          <div className="space-y-3 mt-3">
            {[
              { g:'A', r:'0–20',   c:'#22c55e', d:'Low risk. Strong code, decentralised ownership, healthy TVL, audited, clean compliance record.' },
              { g:'B', r:'21–40',  c:'#84cc16', d:'Moderate-low risk. Generally sound with one or two dimensions that could be improved.' },
              { g:'C', r:'41–60',  c:'#f59e0b', d:'Moderate risk. Multiple risk vectors present. Due diligence strongly advised.' },
              { g:'D', r:'61–80',  c:'#f97316', d:'High risk. Significant vulnerabilities or compliance concerns. Elevated investigation needed.' },
              { g:'F', r:'81–100', c:'#ef4444', d:'Critical or hard override active. OFAC cap (score 10) or exploit cap (score 30) may apply.' },
            ].map(g => (
              <div key={g.g} className="glass rounded-lg p-4 flex gap-4 items-start">
                <span className="font-orbitron text-3xl font-black shrink-0" style={{ color: g.c, minWidth: 36 }}>{g.g}</span>
                <div><div className="font-mono text-xs text-slate-500 mb-1">{g.r}</div><div className="font-mono text-xs text-slate-400">{g.d}</div></div>
              </div>
            ))}
          </div>
        </Section>

        <Section id="dims" title="Risk Dimensions">
          <p>The composite score is a weighted sum of six dimensions:</p>
          <div className="space-y-3 mt-3">
            {[
              { d:'Code Risk — 30%',      t:'Slither static analysis + 5 custom privacy detectors. Checks for mixer reentrancy, ZK verifier bypass, upgrade-without-timelock, unlocked withdrawal patterns, and proxy storage collisions. Score = 100 − (high×25 + med×10 + low×3), min 0. Unverified contracts receive a base penalty of 70.' },
              { d:'Ownership — 25%',       t:'Starts at 100. Deductions: no multisig (−30), no timelock (−20), upgradeable without timelock (−25), centralised admin key (−15), proxy pattern risk (−10). Rewarded for renounced ownership.' },
              { d:'Liquidity — 20%',       t:'TVL tiers via DefiLlama (high confidence) or Dune SIM (medium confidence). Whale >$100M → 20pts, Large >$10M → 40pts, Medium >$1M → 60pts, Small >$100K → 80pts, Micro → 95pts. Confidence-weighted between sources.' },
              { d:'Audit History — 12%',   t:'Tier 1 (Trail of Bits, OpenZeppelin, etc.) → 15pts base. Tier 2 → 30pts. Tier 3 → 50pts. No audit → 80pts. Formal verification bonus −10. Each critical finding +10, high +5. Recency decay applied over 24 months.' },
              { d:'Compliance — 8%',       t:'OFAC SDN active → score capped at 10, grade F (hard override). Exploit active and unresolved → capped at 30, grade F (hard override). Resolved exploit → +20 penalty. Clean record → 0.' },
              { d:'Governance — 5%',       t:'Fixed at 50.0 in v1.0. Planned for v1.1: Herfindahl-Hirschman Index (HHI) for token concentration, multisig quorum depth, on-chain governance proposal history and participation rate.' },
            ].map(x => (
              <div key={x.d} className="glass rounded-lg p-4">
                <div className="font-orbitron text-xs font-bold mb-2" style={{ color: '#00d4ff' }}>{x.d}</div>
                <div className="font-mono text-xs text-slate-400 leading-relaxed">{x.t}</div>
              </div>
            ))}
          </div>
        </Section>

      </div>
    </div>
  )
}

export default function DocsPage() {
  return (
    <Suspense fallback={<div className="pt-28 text-center font-mono text-slate-500">Loading docs...</div>}>
      <DocsContent />
    </Suspense>
  )
}
