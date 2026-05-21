'use client'
import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

function ScanPreview() {
  const router = useRouter()
  const [addr, setAddr] = useState('')
  const [chain, setChain] = useState('ethereum')
  const [err, setErr] = useState('')

  function go() {
    const a = addr.trim().toLowerCase()
    if (!/^0x[0-9a-f]{40}$/.test(a)) { setErr('Enter a valid 0x address (42 chars)'); return }
    setErr('')
    router.push(`/score/${chain}/${a}`)
  }

  return (
    <div className="p-6 space-y-4">
      <div>
        <label className="font-mono text-xs text-slate-500 tracking-widest block mb-2">SELECT CHAIN</label>
        <select value={chain} onChange={e => setChain(e.target.value)}
          className="w-full glass font-mono text-xs text-slate-300 px-3 py-2.5 rounded-lg focus:outline-none cursor-pointer"
          style={{ background: 'rgba(255,255,255,0.04)' }}>
          {['ethereum','arbitrum','optimism','base','polygon','bsc','avalanche'].map(c => (
            <option key={c} value={c} style={{ background: '#0a0f1e' }}>{c.charAt(0).toUpperCase()+c.slice(1)}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="font-mono text-xs text-slate-500 tracking-widest block mb-2">CONTRACT ADDRESS</label>
        <input type="text" value={addr} onChange={e => setAddr(e.target.value)}
          placeholder="0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF"
          className="w-full glass font-mono text-xs text-slate-300 px-3 py-2.5 rounded-lg focus:outline-none placeholder:text-slate-700 cursor-text" />
        {err && <p className="font-mono text-xs text-red-400 mt-1">{err}</p>}
      </div>
      <button onClick={go}
        className="w-full font-orbitron text-xs font-bold py-2.5 rounded-lg transition-all cursor-pointer hover:opacity-90 active:scale-[0.99]"
        style={{ background: '#00d4ff', color: '#0a0f1e' }}>
        SCAN CONTRACT →
      </button>
      <p className="font-mono text-xs text-slate-600 text-center">
        First scan: 30–60s · Cached results return instantly
      </p>
    </div>
  )
}

function DirectoryPreview() {
  return (
    <div className="p-5">
      <div className="font-mono text-xs text-slate-500 tracking-widest mb-3">14 CURATED PROTOCOLS — RESCORED EVERY 6H</div>
      <div className="glass rounded-xl overflow-hidden">
        <div className="grid font-mono text-xs text-slate-500 px-4 py-2.5"
          style={{ gridTemplateColumns: '2fr 1fr 1fr', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
          <span>PROTOCOL</span><span>GRADE</span><span>SCORE</span>
        </div>
        {[['Railgun','B',74,'#84cc16'],['Aztec','A',31,'#22c55e'],['Privacy Pools','B',68,'#84cc16'],['Hinkal','C',54,'#f59e0b'],['Tornado Cash','F',9,'#7c3aed']].map(([n,g,s,c]: any) => (
          <div key={n} className="grid px-4 py-2.5 border-b hover:bg-white/[0.03] transition-colors cursor-pointer"
            style={{ gridTemplateColumns: '2fr 1fr 1fr', borderColor: 'rgba(255,255,255,0.05)' }}>
            <span className="font-mono text-xs text-slate-300">{n}</span>
            <span className="font-orbitron text-xs font-bold" style={{ color: c }}>{g}</span>
            <span className="font-mono text-xs" style={{ color: c }}>{s}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function BotPreview() {
  return (
    <div className="p-5 space-y-2">
      {[
        { from: 'you', text: '/score 0x910Cbd... ethereum' },
        { from: 'bot', text: '✅ Railgun v2 — Ethereum\nGrade: B  Score: 74/100\nCompliance: 100  Ownership: 91' },
        { from: 'you', text: '/watch 0x910Cbd... 10' },
        { from: 'bot', text: '⧡ Watching 0x910Cbd...\nYou will be alerted if score changes by ±10 points' },
      ].map((m, i) => (
        <div key={i} className={`flex ${m.from === 'you' ? 'justify-end' : 'justify-start'}`}>
          <div className="max-w-[85%] rounded-xl px-3 py-2 font-mono text-xs whitespace-pre-line"
            style={{ background: m.from === 'you' ? 'rgba(0,212,255,0.15)' : 'rgba(255,255,255,0.07)', color: m.from === 'you' ? '#00d4ff' : '#e2e8f0' }}>
            {m.text}
          </div>
        </div>
      ))}
    </div>
  )
}

function ApiPreview() {
  return (
    <div className="p-5">
      <div className="glass rounded-xl p-4 font-mono text-xs leading-relaxed">
        <div className="text-slate-500 mb-3">$ curl /api/v1/score/ethereum/0x910Cbd...</div>
        <div><span className="code-key">"composite_score"</span><span className="text-slate-400">: </span><span className="code-num">74.2</span>,</div>
        <div><span className="code-key">"grade"</span><span className="text-slate-400">: </span><span className="code-str">"B"</span>,</div>
        <div><span className="code-key">"grade_label"</span><span className="text-slate-400">: </span><span className="code-str">"Moderate-Low Risk"</span>,</div>
        <div><span className="code-key">"override_status"</span><span className="text-slate-400">: </span><span className="text-slate-500">null</span>,</div>
        <div><span className="code-key">"sub_scores"</span><span className="text-slate-400">: {"{"}</span></div>
        <div className="pl-4"><span className="code-key">"code"</span><span className="text-slate-400">: </span><span className="code-num">82</span>,</div>
        <div className="pl-4"><span className="code-key">"ownership"</span><span className="text-slate-400">: </span><span className="code-num">91</span>,</div>
        <div className="pl-4"><span className="code-key">"compliance"</span><span className="text-slate-400">: </span><span className="code-num">100</span></div>
        <div><span className="text-slate-400">{"}"}</span></div>
      </div>
    </div>
  )
}

const TABS = [
  { id: 'scan',      label: 'Score Any Contract', icon: '⧡', tagline: 'Any EVM address. Any chain. Full risk report in under 60 seconds.', desc: 'Paste a contract address, select a chain, and PrivaScan runs Slither static analysis, checks OFAC lists, queries TVL, and parses audit coverage. No signup required.', cta: null, Preview: ScanPreview },
  { id: 'directory', label: 'Protocol Directory', icon: '⊞', tagline: '14 curated privacy protocols. Scored independently from community scans.', desc: 'These protocols are manually vetted, have verified source code, and are rescored automatically every 6 hours. Different from community scans — these are the gold standard.', cta: { label: 'Browse directory →', href: '/protocols' }, Preview: DirectoryPreview },
  { id: 'bot',       label: 'Telegram Alerts',   icon: '✉', tagline: 'Score contracts and get grade-change alerts without opening a browser.', desc: 'Add any contract to your watchlist via @PrivaScanBot. Set a score threshold. Get a Telegram message the moment the risk grade changes.', cta: { label: 'Open @PrivaScanBot →', href: 'https://t.me/PrivaScanBot' }, Preview: BotPreview },
  { id: 'api',       label: 'REST API',           icon: '</>', tagline: 'Integrate risk scores directly into your product or research workflow.', desc: 'Clean JSON API. Free access at 500 req/hr with a free key. No SDK required — a single curl command gets you a full risk report.', cta: { label: 'Get API key →', href: '/keys' }, Preview: ApiPreview },
]

export default function FeatureTabs() {
  const [active, setActive] = useState('scan')
  const tab = TABS.find(t => t.id === active) || TABS[0]
  const { Preview } = tab

  return (
    <section className="py-24 max-w-7xl mx-auto px-6">
      <div className="text-center mb-12">
        <div className="font-mono text-xs tracking-widest mb-3" style={{ color: '#00d4ff' }}>// CAPABILITIES</div>
        <h2 className="font-orbitron font-bold text-white" style={{ fontSize: 'clamp(1.8rem,4vw,2.6rem)' }}>
          Everything You Need to Assess a Privacy Protocol
        </h2>
      </div>

      <div className="flex flex-wrap gap-2 justify-center mb-8">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setActive(t.id)}
            className="font-mono text-sm px-4 py-2.5 rounded-lg border transition-all cursor-pointer active:scale-95"
            style={{
              background: active === t.id ? 'rgba(0,212,255,0.1)' : 'rgba(255,255,255,0.03)',
              borderColor: active === t.id ? 'rgba(0,212,255,0.5)' : 'rgba(255,255,255,0.1)',
              color: active === t.id ? '#ffffff' : '#94a3b8',
              fontWeight: active === t.id ? 700 : 400,
            }}>
            <span className="mr-2">{t.icon}</span>{t.label}
          </button>
        ))}
      </div>

      <div className="glass rounded-2xl overflow-hidden grid md:grid-cols-2" style={{ borderColor: 'rgba(0,212,255,0.15)' }}>
        <div className="p-8 flex flex-col justify-between">
          <div>
            <p className="font-orbitron text-lg font-bold text-white mb-3">{tab.tagline}</p>
            <p className="font-mono text-sm text-slate-400 leading-relaxed">{tab.desc}</p>
          </div>
          {tab.cta && <Link href={tab.cta.href}
            className="inline-flex items-center gap-2 mt-8 font-orbitron text-xs font-bold px-5 py-3 rounded-lg transition-all cursor-pointer hover:opacity-90 active:scale-95 self-start"
            style={{ background: '#00d4ff', color: '#0a0f1e' }}>
            {tab.cta.label}}</Link>}
          </Link>
        </div>
        <div className="border-l" style={{ borderColor: 'rgba(255,255,255,0.07)', background: 'rgba(0,0,0,0.2)' }}>
          <Preview />
        </div>
      </div>
    </section>
  )
}
