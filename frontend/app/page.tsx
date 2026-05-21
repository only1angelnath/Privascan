import Link from 'next/link'
import dynamic from 'next/dynamic'
import SearchBar from '@/components/SearchBar'
import GradeBadge from '@/components/GradeBadge'
import FAQ from '@/components/FAQ'
const ParticleCanvas = dynamic(() => import('@/components/ParticleCanvas'), { ssr: false })
const FeatureTabs    = dynamic(() => import('@/components/FeatureTabs'),    { ssr: false })

const SPOTLIGHT_BASE = [
  { name: 'Railgun',       chain: 'Ethereum', color: '#84cc16', slug: 'railgun',       contracts: 12, desc: 'ZK shielded balances for private DeFi. Most active privacy pool on mainnet.' },
  { name: 'Aztec',         chain: 'Ethereum', color: '#22c55e', slug: 'aztec',         contracts: 12, desc: 'ZK rollup with native account abstraction and private execution layer.' },
  { name: 'Privacy Pools', chain: 'Ethereum', color: '#84cc16', slug: 'privacy-pools', contracts: 5,  desc: 'Association set proofs for regulatory-compliant privacy. Vitalik-endorsed.' },
]

const API = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api/v1'

async function getSpotlight() {
  return Promise.all(
    SPOTLIGHT_BASE.map(async (item) => {
      try {
        const r = await fetch(`${API}/protocols/${item.slug}`, { next: { revalidate: 300 } })
        const d = await r.json()
        const s = d.latest_score
        return { ...item, grade: s?.grade ?? null, score: s?.composite_score ?? null }
      } catch {
        return { ...item, grade: null, score: null }
      }
    })
  )
}

export default async function HomePage() {
  const SPOTLIGHT = await getSpotlight()
  return (
    <>
      {/* HERO */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        <ParticleCanvas />
        <div className="absolute inset-0" style={{ background: 'linear-gradient(to bottom, transparent 50%, #0a0f1e 100%)' }} />
        <div className="relative z-10 text-center max-w-4xl mx-auto px-6 pt-24 pb-20">
          <h1 className="font-orbitron font-black leading-tight mb-5"
            style={{ fontSize: 'clamp(1.6rem,4vw,2.8rem)', letterSpacing: '-0.02em' }}>
            <span className="hero-shimmer block">Your Privacy Is as Strong</span>
            <span className="text-white block">as the Protocol</span>
            <span className="hero-accent block">Behind It.</span>
          </h1>
          <p className="font-mono text-slate-300 mb-10 max-w-xl mx-auto leading-relaxed"
            style={{ fontSize: 'clamp(1rem,2vw,1.15rem)' }}>
            The protocol won’t tell you its risks. That’s our job.
          </p>
          <div className="flex justify-center mb-8"><SearchBar large /></div>
          <div className="flex flex-wrap gap-3 justify-center">
            <Link href="/protocols"
              className="glass font-mono text-sm text-slate-200 px-6 py-3 rounded-lg border-white/15 hover:border-cyan-400/40 hover:text-white transition-all cursor-pointer active:scale-95">
              Browse Protocols →
            </Link>
            <Link href="/whitepaper"
              className="glass font-mono text-sm px-6 py-3 rounded-lg transition-all cursor-pointer active:scale-95 hover:opacity-90"
              style={{ color: '#00d4ff', borderColor: 'rgba(0,212,255,0.25)' }}>
              Read Whitepaper →
            </Link>
          </div>
        </div>
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 animate-scroll-hint">
          <div className="font-mono text-xs tracking-widest" style={{ color: 'rgba(255,255,255,0.2)' }}>SCROLL</div>
          <div style={{ width: 1, height: 28, background: 'linear-gradient(to bottom, rgba(0,212,255,0.3), transparent)' }} />
        </div>
      </section>

      {/* COMPACT STATS */}
      <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'rgba(0,212,255,0.015)' }}>
        <div className="max-w-7xl mx-auto px-6 py-3 flex flex-wrap justify-center gap-x-6 gap-y-1">
          {[
            { v: '14',   l: 'protocols curated',  c: '#00d4ff' },
            { v: '197',  l: 'contracts scored',   c: '#f59e0b' },
            { v: '9',    l: 'chains supported',   c: '#00d4ff' },
            { v: '6h',   l: 'rescore interval',   c: '#22c55e' },
            { v: 'Free', l: 'API access',         c: '#22c55e' },
          ].map(s => (
            <span key={s.l} className="font-mono text-sm text-slate-400">
              <span className="font-bold" style={{ color: s.c }}>{s.v}</span> {s.l}
            </span>
          ))}
        </div>
      </div>

      {/* FEATURE TABS */}
      <FeatureTabs />

      {/* PROTOCOL SPOTLIGHT */}
      <section className="py-20 max-w-7xl mx-auto px-6">
        <div className="flex items-end justify-between mb-10 flex-wrap gap-4">
          <div>
            <div className="font-mono text-xs tracking-widest mb-2" style={{ color: '#f59e0b' }}>// PROTOCOL SPOTLIGHT</div>
            <h2 className="font-orbitron font-bold text-white heading-glow" style={{ fontSize: 'clamp(1.6rem,3.5vw,2.2rem)' }}>Featured Risk Reports
            </h2>
          </div>
          <Link href="/protocols"
            className="font-mono text-sm text-slate-400 hover:text-white border border-white/15 hover:border-white/30 px-4 py-2 rounded-lg transition-all cursor-pointer active:scale-95">
            View all 14 protocols →
          </Link>
        </div>
        <div className="grid md:grid-cols-3 gap-5">
          {SPOTLIGHT.map(p => (
            <Link key={p.slug} href={`/protocol/${p.slug}`}
              className="glass card-hover rounded-xl p-6 block cursor-pointer"
              style={{ borderColor: `${p.color}22` }}>
              <div className="flex justify-between items-start mb-3">
                <div>
                  <div className="font-orbitron text-base font-bold text-white">{p.name}</div>
                  <div className="font-mono text-xs text-slate-500 mt-0.5">{p.chain} · {p.contracts} contracts</div>
                </div>
                <div className="text-right">
                  <div className="font-orbitron text-3xl font-black" style={{ color: p.color }}>{p.grade}</div>
                  <div className="font-mono text-xs text-slate-500">{p.score}/100</div>
                </div>
              </div>
              <p className="font-mono text-xs text-slate-500 leading-relaxed mb-4">{p.desc}</p>
              <div className="font-mono text-xs" style={{ color: '#00d4ff' }}>View full report →</div>
            </Link>
          ))}
        </div>
      </section>
{/* FAQ */}
      <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        <FAQ />
      </div>

      {/* COMMUNITY */}
      <section className="py-16 max-w-7xl mx-auto px-6">
        <div className="text-center mb-10">
          <div className="font-mono text-xs tracking-widest mb-3" style={{ color: '#00d4ff' }}>// JOIN</div>
          <h2 className="font-orbitron font-bold text-white heading-glow" style={{ fontSize: 'clamp(1.6rem,3.5vw,2.2rem)' }}>Stay in the Loop
          </h2>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { icon: 'X',  title: 'Twitter / X',     desc: 'Risk alerts and protocol updates',          href: 'https://x.com/privascan',     c: '#e2e8f0' },
            { icon: 'TG', title: 'Telegram Channel', desc: 'Community discussion and risk intelligence', href: 'https://t.me/privascan',      c: '#00d4ff' },
            { icon: '⧡', title: 'Telegram Bot', desc: 'Score contracts and watchlist alerts',      href: 'https://t.me/PrivaScanBot',   c: '#00d4ff' },
            { icon: 'GH', title: 'GitHub',           desc: 'Open source — PRs and issues welcome', href: 'https://github.com/only1angelnath/Privascan', c: '#e2e8f0' },
          ].map(s => (
            <a key={s.title} href={s.href} target="_blank" rel="noreferrer"
              className="glass glass-hover rounded-xl p-5 block cursor-pointer hover:scale-[1.02] transition-all active:scale-100">
              <div className="font-orbitron text-2xl font-black mb-3" style={{ color: s.c }}>{s.icon}</div>
              <div className="font-orbitron text-sm font-bold text-white mb-1">{s.title}</div>
              <p className="font-mono text-xs text-slate-500">{s.desc}</p>
            </a>
          ))}
        </div>
      </section>
    </>
  )
}
