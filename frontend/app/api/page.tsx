
'use client'
import { useState } from 'react'
import Link from 'next/link'

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api/v1'
const DEMO_KEY_VAL = 'ps_privascan_shared_demo_key_v1_2026_public'

// Shared primitives
function M({ m, path }: { m: string; path: string }) {
  const bg = m === 'GET' ? '#1a56db' : '#057a55'
  return (
    <div className="flex items-center gap-3 mb-2">
      <span className="font-mono text-xs font-bold px-2.5 py-1 rounded-full"
        style={{ background: bg, color: '#fff' }}>{m}</span>
      <code className="font-mono text-sm text-slate-300">{path}</code>
    </div>
  )
}

function Tag({ children }: { children: React.ReactNode }) {
  return (
    <code className="font-mono text-xs px-1.5 py-0.5 rounded"
      style={{ color: '#00d4ff', background: 'rgba(0,212,255,0.1)' }}>
      {children}
    </code>
  )
}

function Code({ children, title }: { children: React.ReactNode; title?: string }) {
  return (
    <div className="rounded-xl overflow-hidden my-4"
      style={{ background: '#050d18', border: '1px solid rgba(255,255,255,0.07)' }}>
      {title && (
        <div className="px-4 py-2 font-mono text-xs text-slate-600 border-b"
          style={{ borderColor: 'rgba(255,255,255,0.07)' }}>{title}</div>
      )}
      <div className="p-4 font-mono text-xs text-slate-300 leading-relaxed overflow-x-auto whitespace-pre">
        {children}
      </div>
    </div>
  )
}

function Param({ name, type_, req, desc }: { name: string; type_: string; req?: boolean; desc: string }) {
  return (
    <div className="grid gap-4 py-3 border-b"
      style={{ gridTemplateColumns: '140px 1fr', borderColor: 'rgba(255,255,255,0.06)' }}>
      <div>
        <code className="font-mono text-xs font-bold" style={{ color: '#f59e0b' }}>{name}</code>
        {req && <span className="ml-1 text-xs" style={{ color: '#ef4444' }}>*</span>}
        <div className="font-mono text-xs text-slate-600 mt-0.5">{type_}</div>
      </div>
      <p className="font-mono text-xs text-slate-400 leading-relaxed">{desc}</p>
    </div>
  )
}

// Try It component
function TryIt({ method, pathTemplate, defaults, fields }: {
  method: string
  pathTemplate: string
  defaults: Record<string, string>
  fields: { key: string; label: string; placeholder: string }[]
}) {
  const [open, setOpen]     = useState(false)
  const [vals, setVals]     = useState<Record<string,string>>(defaults)
  const [useOwn, setUseOwn] = useState(false)
  const [ownKey, setOwnKey] = useState('')
  const [resp, setResp]     = useState('')
  const [status, setStatus] = useState(0)
  const [ms, setMs]         = useState(0)
  const [loading, setLoad]  = useState(false)

  async function run() {
    setLoad(true); setResp(''); setStatus(0)
    let url = API_BASE + pathTemplate
    Object.entries(vals).forEach(([k, v]) => {
      url = url.replace('{' + k + '}', v.trim())
    })
    const key = useOwn ? ownKey : DEMO_KEY_VAL
    const t0 = Date.now()
    try {
      const r = await fetch(url, { headers: { 'X-API-Key': key } })
      const d = await r.json()
      setStatus(r.status)
      setMs(Date.now() - t0)
      setResp(JSON.stringify(d, null, 2))
    } catch (e: any) {
      setResp(e.message); setStatus(0)
    }
    setLoad(false)
  }

  return (
    <div className="mt-4">
      <button onClick={() => setOpen(!open)}
        className="inline-flex items-center gap-2 font-mono text-xs px-4 py-2 rounded-lg border transition-all cursor-pointer hover:text-white link-lift"
        style={{ borderColor: 'rgba(0,212,255,0.3)', color: '#00d4ff', background: 'rgba(0,212,255,0.05)' }}>
        {open ? '▼ Close' : '▶ Try it'}
      </button>

      {open && (
        <div className="mt-3 rounded-xl overflow-hidden"
          style={{ background: '#060e1a', border: '1px solid rgba(0,212,255,0.15)' }}>
          <div className="px-5 py-3 font-mono text-xs text-slate-500 border-b"
            style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
            PARAMETERS
          </div>
          <div className="p-5 space-y-3">
            {fields.map(f => (
              <div key={f.key}>
                <label className="font-mono text-xs text-slate-400 block mb-1">{f.label}</label>
                <input
                  value={vals[f.key] || ''}
                  onChange={e => setVals(p => ({ ...p, [f.key]: e.target.value }))}
                  placeholder={f.placeholder}
                  className="w-full glass font-mono text-xs text-slate-300 px-3 py-2 rounded-lg focus:outline-none placeholder:text-slate-700 cursor-text"
                />
              </div>
            ))}
            <div>
              <label className="font-mono text-xs text-slate-400 block mb-2">API KEY</label>
              <label className="flex items-center gap-2 mb-2 cursor-pointer">
                <input type="checkbox" checked={useOwn} onChange={e => setUseOwn(e.target.checked)}
                  style={{ accentColor: '#00d4ff' }} />
                <span className="font-mono text-xs text-slate-400">Use my own key</span>
              </label>
              {useOwn ? (
                <input value={ownKey} onChange={e => setOwnKey(e.target.value)}
                  placeholder="ps_your_key_here"
                  className="w-full glass font-mono text-xs text-slate-300 px-3 py-2 rounded-lg focus:outline-none placeholder:text-slate-700" />
              ) : (
                <div className="font-mono text-xs text-slate-600 px-3 py-2 rounded-lg"
                  style={{ background: 'rgba(255,255,255,0.03)' }}>
                  Using shared demo key (500 req/hr shared)
                </div>
              )}
            </div>
            <button onClick={run} disabled={loading}
              className="w-full font-orbitron text-xs font-bold py-2.5 rounded-lg transition-all cursor-pointer hover:opacity-90 active:scale-[0.99] disabled:opacity-50"
              style={{ background: '#00d4ff', color: '#0a0f1e' }}>
              {loading ? 'Running...' : 'Run Request'}
            </button>
          </div>
          {resp && (
            <div className="border-t" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
              <div className="px-5 py-2 flex items-center gap-3 border-b font-mono text-xs"
                style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
                <span className="font-bold"
                  style={{ color: status >= 200 && status < 300 ? '#22c55e' : '#ef4444' }}>
                  {status} {status >= 200 && status < 300 ? 'OK' : 'Error'}
                </span>
                <span className="text-slate-600">{ms}ms</span>
              </div>
              <pre className="p-5 font-mono text-xs text-slate-300 overflow-x-auto max-h-80 leading-relaxed">
                {resp}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function Section({ id, title, badge, children }: {
  id: string; title: string; badge?: string; children: React.ReactNode
}) {
  return (
    <div id={id} className="glass rounded-xl p-8 scroll-mt-20">
      <div className="flex items-center gap-3 mb-4">
        {badge && (
          <span className="font-mono text-xs font-bold px-2.5 py-1 rounded-full shrink-0"
            style={{ background: badge === 'GET' ? '#1a56db' : '#057a55', color: '#fff' }}>
            {badge}
          </span>
        )}
        <h2 className="font-orbitron text-xl font-bold text-white heading-glow">{title}</h2>
      </div>
      <div className="font-mono text-sm text-slate-400 leading-relaxed space-y-4">{children}</div>
    </div>
  )
}

const SIDEBAR = [
  { section: 'OVERVIEW', items: [
    { id: 'introduction',   label: 'Introduction'          },
    { id: 'auth',           label: 'Authentication'        },
    { id: 'rate-limits',    label: 'Rate Limits'           },
    { id: 'usage-credits',  label: 'Usage Credits'         },
    { id: 'endpoint-index', label: 'Endpoint Index'        },
    { id: 'errors',         label: 'Error Reference'       },
  ]},
  { section: 'CONTRACT SCORING', items: [
    { id: 'ep-score',     label: 'Get Contract Risk Score' },
    { id: 'ep-history',   label: 'Get Score History'       },
    { id: 'ep-async',     label: 'Queue Background Scan'   },
  ]},
  { section: 'PROTOCOLS', items: [
    { id: 'ep-protocols', label: 'List Privacy Protocols'  },
    { id: 'ep-protocol',  label: 'Get Protocol Detail'     },
  ]},
  { section: 'API KEYS', items: [
    { id: 'ep-keygen',    label: 'Generate API Key'        },
    { id: 'ep-usage',     label: 'Check Your Usage'        },
  ]},
  { section: 'REFERENCE', items: [
    { id: 'grades',       label: 'Grade Reference'         },
    { id: 'chains',       label: 'Supported Chains'        },
    { id: 'schema',       label: 'Response Schema'         },
  ]},
]

export default function ApiDocsPage() {
  const [active, setActive] = useState('introduction')
  return (
    <div className="max-w-7xl mx-auto px-4 pt-20 pb-16 flex gap-0 min-h-screen">
      <aside className="w-56 shrink-0 hidden lg:flex flex-col">
        <div className="sticky top-20 pr-4 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 80px)' }}>
          <div className="font-mono text-xs tracking-widest mb-4 pt-4" style={{ color: '#00d4ff' }}>
            // API REFERENCE
          </div>
          <nav className="space-y-4">
            {SIDEBAR.map(group => (
              <div key={group.section}>
                <div className="font-mono text-xs text-slate-600 tracking-widest mb-1">{group.section}</div>
                <div className="space-y-0.5">
                  {group.items.map(item => (
                    <a key={item.id} href={'#' + item.id}
                      onClick={() => setActive(item.id)}
                      className="block font-mono text-xs px-3 py-1.5 rounded transition-all cursor-pointer link-lift"
                      style={{
                        color: active === item.id ? '#ffffff' : '#4a7090',
                        background: active === item.id ? 'rgba(0,212,255,0.08)' : 'transparent',
                        borderLeft: active === item.id ? '2px solid #00d4ff' : '2px solid transparent',
                      }}>
                      {item.label}
                    </a>
                  ))}
                </div>
              </div>
            ))}
          </nav>
          <div className="mt-4 pt-4 space-y-2" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
            <Link href="/whitepaper"
              className="font-mono text-xs text-slate-500 hover:text-slate-300 link-lift transition-colors cursor-pointer block">
              Whitepaper
            </Link>
            <Link href="/usage"
              className="font-mono text-xs text-slate-500 hover:text-slate-300 link-lift transition-colors cursor-pointer block">
              Check My Usage
            </Link>
          </div>
        </div>
      </aside>

      <div className="flex-1 min-w-0 lg:pl-8 space-y-5">

        <Section id="introduction" title="Introduction">
          <p>
            The PrivaScan API gives you programmatic access to smart contract risk scores for EVM
            privacy protocols. One request returns a deterministic composite score (0-100), a letter
            grade, and six sub-scores covering code, ownership, liquidity, audits, compliance, and
            governance. No SDK required.
          </p>
          <div className="glass rounded-xl p-5" style={{ borderColor: 'rgba(0,212,255,0.2)' }}>
            <div className="font-mono text-xs text-slate-500 mb-1">Base URL</div>
            <div className="font-mono text-lg font-bold" style={{ color: '#00d4ff' }}>
              http://localhost:8000/api/v1
            </div>
            <div className="font-mono text-xs text-slate-500 mt-2">
              JSON responses only &middot; CORS enabled &middot; No SDK required
            </div>
          </div>
        </Section>

        <Section id="auth" title="Authentication">
          <p>
            Pass your API key in the <Tag>X-API-Key</Tag> header. Without a key you get 10 requests
            per hour based on your IP address. A free key gives you 500 per hour, isolated to your key
            so other users never affect your quota. Generate one at{' '}
            <Link href="/keys" className="link-lift cursor-pointer" style={{ color: '#00d4ff' }}>
              privascan.xyz/keys
            </Link>
            .
          </p>
          <Code title="authenticated">
{`curl http://localhost:8000/api/v1/score/ethereum/0x910Cbd... \
  -H "X-API-Key: ps_your_key_here"`}
          </Code>
          <Code title="no key (10 req/hr)">
{`curl http://localhost:8000/api/v1/score/ethereum/0x910Cbd...`}
          </Code>
        </Section>

        <Section id="rate-limits" title="Rate Limits">
          <p>
            Two windows run simultaneously: per-minute prevents burst abuse, per-hour caps sustained
            usage. Both must be within limit for a request to succeed. On 429, check the{' '}
            <Tag>Retry-After</Tag> header for seconds to wait.
          </p>
          <div className="glass rounded-xl overflow-hidden mt-3">
            <div className="grid font-mono text-xs text-slate-500 tracking-widest px-5 py-3"
              style={{ gridTemplateColumns: '1fr 1fr 1fr 1fr', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
              <span>TIER</span><span>PER MIN</span><span>PER HOUR</span><span>IDENTIFIER</span>
            </div>
            {[
              ['Anonymous', '2',  '10',   'Client IP'  ],
              ['Free',      '15', '500',  'Key hash'   ],
              ['Pro',       '60', '2000', 'Key hash'   ],
            ].map(([t,m,h,i]) => (
              <div key={t} className="grid px-5 py-3 border-b font-mono text-xs"
                style={{ gridTemplateColumns: '1fr 1fr 1fr 1fr', borderColor: 'rgba(255,255,255,0.05)' }}>
                <span className="text-white">{t}</span>
                <span style={{ color: '#00d4ff' }}>{m}/min</span>
                <span style={{ color: '#84cc16' }}>{h}/hr</span>
                <span className="text-slate-500">{i}</span>
              </div>
            ))}
          </div>
        </Section>

        <Section id="usage-credits" title="API Key Usage Credits">
          <p>
            Every API request consumes 1 credit from your hourly allowance. Credits reset one hour after
            your first request in that window. Here is what counts and what does not:
          </p>
          <div className="glass rounded-xl p-5 space-y-3 mt-3"
            style={{ borderColor: 'rgba(0,212,255,0.15)' }}>
            {[
              ['YES', '200 OK responses',          '#22c55e', 'Consumes 1 credit'       ],
              ['YES', 'Cached responses',           '#22c55e', 'Consumes 1 credit'       ],
              ['NO',  '400, 401, 422 client errors','#ef4444', 'Does NOT consume credits'],
              ['NO',  '500 server errors',          '#ef4444', 'Does NOT consume credits'],
              ['NO',  '429 rate limit responses',   '#ef4444', 'Does NOT consume credits'],
            ].map(([yn, desc, c, note]) => (
              <div key={desc} className="flex justify-between items-center font-mono text-xs">
                <div className="flex items-center gap-2">
                  <span className="font-bold w-7" style={{ color: c }}>{yn}</span>
                  <span className="text-slate-400">{desc}</span>
                </div>
                <span className="text-slate-600">{note}</span>
              </div>
            ))}
          </div>
          <p className="text-xs mt-3">
            Track real-time usage at{' '}
            <Link href="/usage" className="link-lift cursor-pointer" style={{ color: '#00d4ff' }}>
              privascan.xyz/usage
            </Link>
            .
          </p>
        </Section>

        <Section id="endpoint-index" title="Endpoint Index">
          <p>All available endpoints at a glance:</p>
          <div className="glass rounded-xl overflow-hidden mt-3">
            <div className="grid font-mono text-xs text-slate-500 tracking-widest px-5 py-3"
              style={{ gridTemplateColumns: '60px 1fr 1fr', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
              <span></span><span>ENDPOINT TITLE</span><span>PATH</span>
            </div>
            {[
              ['GET',  'Get Contract Risk Score', '/score/{chain}/{address}'],
              ['GET',  'Get Score History',        '/score/{chain}/{address}/history'],
              ['POST', 'Queue Background Scan',    '/score/request'],
              ['GET',  'List Privacy Protocols',   '/protocols/'],
              ['GET',  'Get Protocol Detail',      '/protocols/{slug}'],
              ['POST', 'Generate API Key',         '/keys/generate'],
              ['GET',  'Check API Usage',          '/keys/usage'],
            ].map(([m, t, p]) => (
              <div key={p} className="grid px-5 py-3 border-b font-mono text-xs"
                style={{ gridTemplateColumns: '60px 1fr 1fr', borderColor: 'rgba(255,255,255,0.05)' }}>
                <span className="font-bold"
                  style={{ color: m === 'GET' ? '#1a56db' : '#057a55' }}>{m}</span>
                <span className="text-slate-300">{t}</span>
                <code className="text-slate-500">{p}</code>
              </div>
            ))}
          </div>
        </Section>

        <Section id="errors" title="Error Reference">
          <p>
            All errors return a JSON object with a single <Tag>detail</Tag> field containing a
            human-readable explanation. Use the HTTP status code to identify the error class.
          </p>
          <Code title="error shape">
{`{ "detail": "Invalid or inactive API key." }`}
          </Code>
          <div className="glass rounded-xl overflow-hidden mt-3">
            {[
              ['400', 'Bad Request',        'Missing or invalid parameters. Check your request body.'],
              ['401', 'Unauthorized',       'API key is invalid, inactive, or missing the ps_ prefix.'],
              ['404', 'Not Found',          'Unknown protocol slug, expired task ID, or unindexed address.'],
              ['422', 'Validation Error',   'Wrong field type in request body. Check the endpoint schema.'],
              ['429', 'Rate Limited',       'Check Retry-After header. Implement exponential backoff.'],
              ['500', 'Server Error',       'Slither failed or upstream API unavailable. Retry in 60s.'],
            ].map(([code, name, desc]) => (
              <div key={code} className="grid px-5 py-3 border-b font-mono text-xs"
                style={{ gridTemplateColumns: '60px 140px 1fr', borderColor: 'rgba(255,255,255,0.05)' }}>
                <span className="font-orbitron font-bold"
                  style={{ color: parseInt(code) >= 500 ? '#ef4444' : '#f59e0b' }}>{code}</span>
                <span className="text-slate-300">{name}</span>
                <span className="text-slate-500">{desc}</span>
              </div>
            ))}
          </div>
        </Section>

        <Section id="ep-score" title="Get Contract Risk Score" badge="GET">
          <M m="GET" path="/api/v1/score/{chain}/{address}" />
          <p>
            The primary endpoint. Runs a full 6-dimension risk analysis on any EVM contract and
            returns a composite score from 0 to 100 (lower is safer), a letter grade A through F,
            and detailed per-dimension sub-scores. First-time scans take 30-60 seconds while Slither
            analyses the bytecode. Results are cached for 1 hour after that.
          </p>
          <div className="glass rounded-xl px-5 mt-4">
            <Param name="chain" type_="string" req
              desc="EVM chain slug. One of: ethereum, arbitrum, optimism, base, polygon, bsc, avalanche" />
            <Param name="address" type_="string" req
              desc="Contract address. 0x-prefixed EVM address, 42 characters. Lowercased automatically." />
          </div>
          <Code title="request">
{`curl http://localhost:8000/api/v1/score/ethereum/0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF \
  -H "X-API-Key: ps_your_key_here"`}
          </Code>
          <Code title="200 response">
{`{
  "address":          "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf",
  "chain":            "ethereum",
  "chain_id":         1,
  "composite_score":  74.2,
  "grade":            "B",
  "grade_label":      "Moderate-Low Risk",
  "override_applied": false,
  "override_status":  null,
  "sub_scores": {
    "code": 82, "ownership": 91, "liquidity": 71,
    "audit": 80, "compliance": 100, "governance": 50
  },
  "scored_at": "2026-05-17T21:00:00Z",
  "cached":    false
}`}
          </Code>
          <TryIt method="GET" pathTemplate="/score/{chain}/{address}"
            defaults={{ chain: 'ethereum', address: '0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF' }}
            fields={[
              { key: 'chain',   label: 'Chain',            placeholder: 'ethereum' },
              { key: 'address', label: 'Contract Address', placeholder: '0x910Cbd...' },
            ]} />
        </Section>

        <Section id="ep-history" title="Get Score History" badge="GET">
          <M m="GET" path="/api/v1/score/{chain}/{address}/history" />
          <p>
            Returns historical score snapshots for a contract address, newest first. Curated protocols
            accumulate 4 snapshots per day (rescored every 6 hours). Community scans accumulate only
            on request. Use the <Tag>limit</Tag> query param to control how many you get back.
          </p>
          <div className="glass rounded-xl px-5 mt-4">
            <Param name="limit" type_="integer (query)"
              desc="Number of snapshots to return. Default: 10. Maximum: 30." />
          </div>
          <Code title="request + response">
{`GET /api/v1/score/ethereum/0x910Cbd.../history?limit=3

{
  "history": [
    { "composite_score": 74.2, "grade": "B", "scored_at": "2026-05-17T21:00:00Z" },
    { "composite_score": 76.1, "grade": "B", "scored_at": "2026-05-17T15:00:00Z" },
    { "composite_score": 74.8, "grade": "B", "scored_at": "2026-05-17T09:00:00Z" }
  ]
}`}
          </Code>
          <TryIt method="GET" pathTemplate="/score/{chain}/{address}/history"
            defaults={{ chain: 'ethereum', address: '0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF' }}
            fields={[
              { key: 'chain',   label: 'Chain',   placeholder: 'ethereum' },
              { key: 'address', label: 'Address', placeholder: '0x...' },
            ]} />
        </Section>

        <Section id="ep-async" title="Queue Background Scan" badge="POST">
          <M m="POST" path="/api/v1/score/request" />
          <p>
            Dispatches a Slither analysis to the background worker queue and returns a task ID
            immediately without waiting for the result. Poll the task endpoint to check completion.
            Useful when you want to trigger a rescore without blocking your application.
          </p>
          <Code title="request">
{`POST /api/v1/score/request
Content-Type: application/json

{ "chain": "ethereum", "address": "0x910Cbd..." }

-> { "task_id": "d9330c89-7ef8-4780-8a6e-663ba6741c49", "status": "queued" }`}
          </Code>
          <Code title="polling the result">
{`GET /api/v1/score/task/d9330c89-7ef8-4780-8a6e-663ba6741c49

# While processing:
{ "status": "running" }

# When complete:
{ "status": "complete", "result": { ...full score object... } }

# If it failed:
{ "status": "failed", "error": "Slither analysis failed for unverified contract" }`}
          </Code>
        </Section>

        <Section id="ep-protocols" title="List Privacy Protocols" badge="GET">
          <M m="GET" path="/api/v1/protocols/" />
          <p>
            Returns all 14 curated protocols with metadata and their latest ecosystem scores. These
            protocols are manually vetted, have verified source code, and are automatically rescored
            every 6 hours. Results include the aggregated ecosystem grade across all deployed contracts.
          </p>
          <Code title="request + response">
{`GET /api/v1/protocols/

{
  "count": 14,
  "protocols": [
    {
      "slug":          "railgun",
      "name":          "Railgun",
      "description":   "ZK shielded balances for private DeFi on Ethereum and L2s.",
      "website_url":   "https://railgun.org",
      "github_url":    "https://github.com/Railgun-Community",
      "latest_score":  { "composite_score": 74.2, "grade": "B" }
    }
  ]
}`}
          </Code>
          <TryIt method="GET" pathTemplate="/protocols/"
            defaults={{}} fields={[]} />
        </Section>

        <Section id="ep-protocol" title="Get Protocol Detail" badge="GET">
          <M m="GET" path="/api/v1/protocols/{slug}" />
          <p>
            Full protocol metadata, the complete list of all deployed contracts across all chains,
            and the latest ecosystem-level score. Use this to get contract addresses for individual
            scoring via the <Tag>GET /score</Tag> endpoint.
          </p>
          <div className="glass rounded-xl px-5 mt-4">
            <Param name="slug" type_="string" req
              desc="Protocol slug. Examples: railgun, aztec, privacy-pools, hinkal, tornado-cash" />
          </div>
          <TryIt method="GET" pathTemplate="/protocols/{slug}"
            defaults={{ slug: 'railgun' }}
            fields={[{ key: 'slug', label: 'Protocol Slug', placeholder: 'railgun' }]} />
        </Section>

        <Section id="ep-keygen" title="Generate API Key" badge="POST">
          <M m="POST" path="/api/v1/keys/generate" />
          <p>
            Generates a new <Tag>ps_</Tag> prefixed API key. The raw key is returned exactly once
            and is never stored on the server. Save it immediately. If you lose it, generate a new
            one. Free keys require Telegram verification first — use the guided flow at{' '}
            <Link href="/keys" className="link-lift cursor-pointer" style={{ color: '#00d4ff' }}>
              privascan.xyz/keys
            </Link>
            .
          </p>
          <Code title="request + response">
{`POST /api/v1/keys/generate
Content-Type: application/json

{ "email": "you@example.com", "tier": "free" }

->
{
  "api_key":  "ps_CwkQ0JQnWeTFIgJbNMZ7Jukxdftyd0RBPuiPAbtGGjQ",
  "tier":     "free",
  "email":    "you@example.com",
  "message":  "Store this key safely. Rate limit: 500 req/hr."
}`}
          </Code>
        </Section>

        <Section id="ep-usage" title="Check API Usage" badge="GET">
          <M m="GET" path="/api/v1/keys/usage" />
          <p>
            Returns detailed usage stats for an API key: credits used this hour, remaining credits,
            time until the window resets, all-time request count, and a daily breakdown for the last
            7 days. Or use the{' '}
            <Link href="/usage" className="link-lift cursor-pointer" style={{ color: '#00d4ff' }}>
              visual usage dashboard
            </Link>
            .
          </p>
          <div className="glass rounded-xl px-5 mt-4">
            <Param name="key" type_="string (query)" req
              desc="Your full API key starting with ps_. Passed as a URL query parameter." />
          </div>
          <Code title="example">
{`GET /api/v1/keys/usage?key=ps_your_key_here

{
  "tier": "free",
  "email": "you@example.com",
  "rate_limits": { "per_minute": 15, "per_hour": 500 },
  "current_hour": {
    "used": 42, "remaining": 458, "resets_in_seconds": 2341
  },
  "all_time": { "total_requests": 1847 },
  "last_7_days": [
    { "date": "20260517", "label": "May 17", "requests": 234 }
  ]
}`}
          </Code>
        </Section>

        <Section id="grades" title="Grade Reference">
          <div className="space-y-3">
            {[
              { g: 'A', r: '0-20',   c: '#22c55e', d: 'Low risk. Strong code, decentralised ownership, sufficient TVL, audited, clean compliance record.' },
              { g: 'B', r: '21-40',  c: '#84cc16', d: 'Moderate-low risk. Generally sound with minor areas for improvement. Most established protocols land here.' },
              { g: 'C', r: '41-60',  c: '#f59e0b', d: 'Moderate risk. Multiple risk vectors present. Proceed carefully and verify independently.' },
              { g: 'D', r: '61-80',  c: '#f97316', d: 'High risk. Significant vulnerabilities or compliance concerns. Investigate thoroughly before interacting.' },
              { g: 'F', r: '81-100', c: '#ef4444', d: 'Critical or hard override active. OFAC cap (score 10) or exploit cap (score 30) may apply.' },
            ].map(g => (
              <div key={g.g} className="flex gap-4 glass rounded-lg p-4">
                <span className="font-orbitron text-3xl font-black shrink-0"
                  style={{ color: g.c, minWidth: 36 }}>{g.g}</span>
                <div>
                  <div className="font-mono text-xs text-slate-500 mb-1">{g.r}</div>
                  <div className="font-mono text-xs text-slate-400">{g.d}</div>
                </div>
              </div>
            ))}
          </div>
        </Section>

        <Section id="chains" title="Supported Chains">
          <div className="glass rounded-xl overflow-hidden">
            {[
              ['ethereum',  'Ethereum Mainnet',  '1'    ],
              ['arbitrum',  'Arbitrum One',      '42161'],
              ['optimism',  'Optimism Mainnet',  '10'   ],
              ['base',      'Base',              '8453' ],
              ['polygon',   'Polygon PoS',       '137'  ],
              ['bsc',       'BNB Smart Chain',   '56'   ],
              ['avalanche', 'Avalanche C-Chain', '43114'],
            ].map(([slug, name, id]) => (
              <div key={slug} className="grid px-5 py-3 border-b font-mono text-xs"
                style={{ gridTemplateColumns: '120px 1fr 80px', borderColor: 'rgba(255,255,255,0.05)' }}>
                <code style={{ color: '#00d4ff' }}>{slug}</code>
                <span className="text-slate-300">{name}</span>
                <span className="text-slate-500">{id}</span>
              </div>
            ))}
          </div>
        </Section>

        <Section id="schema" title="Response Schema">
          <p>Complete shape of the score response object:</p>
          <Code title="ScoreResult">
{`{
  address:           string      // lowercased 0x contract address
  chain:             string      // chain slug
  chain_id:          integer     // EVM chain ID
  composite_score:   float       // 0-100, lower is safer
  grade:             string      // "A" | "B" | "C" | "D" | "F"
  grade_label:       string      // e.g. "Moderate-Low Risk"
  override_applied:  boolean     // true if OFAC or exploit override changed the score
  override_status:   string|null // "ofac_active" | "exploit_active" | null
  sub_scores: {
    code:        float  // Slither analysis + custom privacy detectors
    ownership:   float  // Admin key, multisig, timelock, proxy
    liquidity:   float  // Protocol-level TVL via DefiLlama
    audit:       float  // Audit tier, recency, unresolved findings
    compliance:  float  // OFAC SDN + DeFiHackLabs exploit screening
    governance:  float  // v1.0: static 50.0
  }
  details:    object    // per-dimension raw data (findings, TVL, etc.)
  scored_at:  string    // ISO 8601 timestamp
  cached:     boolean   // true if served from Redis cache
}`}
          </Code>
        </Section>

      </div>
    </div>
  )
}
