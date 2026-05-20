'use client'
import { useState, FormEvent } from 'react'
import dynamic from 'next/dynamic'
import Link from 'next/link'

const BarChart    = dynamic(() => import('recharts').then(m => ({ default: m.BarChart })),    { ssr: false })
const Bar         = dynamic(() => import('recharts').then(m => ({ default: m.Bar })),         { ssr: false })
const XAxis       = dynamic(() => import('recharts').then(m => ({ default: m.XAxis })),       { ssr: false })
const YAxis       = dynamic(() => import('recharts').then(m => ({ default: m.YAxis })),       { ssr: false })
const Tooltip     = dynamic(() => import('recharts').then(m => ({ default: m.Tooltip })),     { ssr: false })
const ResponsiveContainer = dynamic(() => import('recharts').then(m => ({ default: m.ResponsiveContainer })), { ssr: false })

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

interface UsageData {
  key_prefix: string
  tier: string
  email: string
  created_at: string | null
  rate_limits: { per_minute: number; per_hour: number }
  current_hour: { used: number; remaining: number; resets_in_seconds: number }
  all_time: { total_requests: number }
  last_7_days: { date: string; label: string; requests: number }[]
}

function StatCard({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color?: string }) {
  return (
    <div className="glass rounded-xl p-5">
      <div className="font-mono text-xs text-slate-500 tracking-widest mb-2">{label}</div>
      <div className="font-orbitron text-3xl font-black text-white mb-1" style={color ? { color } : {}}>
        {value}
      </div>
      {sub && <div className="font-mono text-xs text-slate-500">{sub}</div>}
    </div>
  )
}

function ResetTimer({ seconds }: { seconds: number }) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return <span className="font-mono text-xs" style={{ color: '#f59e0b' }}>Resets in {m}m {s}s</span>
}

export default function UsagePage() {
  const [key, setKey]       = useState('')
  const [data, setData]     = useState<UsageData | null>(null)
  const [err, setErr]       = useState('')
  const [loading, setLoad]  = useState(false)

  async function check(e: FormEvent) {
    e.preventDefault()
    if (!key.startsWith('ps_')) { setErr('Enter your full API key (starts with ps_)'); return }
    setErr(''); setLoad(true)
    try {
      const r = await fetch(`${API}/keys/usage?key=${encodeURIComponent(key)}`)
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'Failed to fetch usage')
      setData(d)
    } catch (e: any) { setErr(e.message) }
    finally { setLoad(false) }
  }

  const usedPct = data ? Math.min(100, (data.current_hour.used / data.rate_limits.per_hour) * 100) : 0
  const usedColor = usedPct > 80 ? '#ef4444' : usedPct > 50 ? '#f59e0b' : '#22c55e'

  return (
    <div className="max-w-3xl mx-auto px-6 pt-28 pb-16">
      <Link href="/" className="font-mono text-xs text-slate-500 hover:text-white link-lift transition-colors inline-flex items-center gap-2 mb-8 cursor-pointer">
        ← HOME
      </Link>
      <div className="mb-10">
        <div className="font-mono text-xs tracking-widest mb-3" style={{ color: '#00d4ff' }}>// API USAGE</div>
        <h1 className="font-orbitron font-black text-white mb-2 heading-glow" style={{ fontSize: 'clamp(1.8rem,5vw,2.8rem)' }}>
          Check Your API Usage
        </h1>
        <p className="font-mono text-xs text-slate-500">Enter your API key to see how many credits you’ve used and your remaining quota.</p>
      </div>

      <form onSubmit={check} className="glass rounded-xl p-6 mb-8">
        <label className="font-mono text-xs text-slate-500 tracking-widest block mb-2">YOUR API KEY</label>
        <div className="flex gap-3">
          <input type="text" value={key} onChange={e => setKey(e.target.value)}
            placeholder="ps_your_api_key_here"
            className="flex-1 glass font-mono text-sm text-white px-4 py-3 rounded-lg focus:outline-none placeholder:text-slate-700 cursor-text" />
          <button type="submit" disabled={loading}
            className="font-orbitron text-xs font-bold px-5 py-3 rounded-lg transition-all cursor-pointer hover:opacity-90 active:scale-95 disabled:opacity-50"
            style={{ background: '#00d4ff', color: '#0a0f1e' }}>
            {loading ? 'LOADING…' : 'CHECK →'}
          </button>
        </div>
        {err && <p className="font-mono text-xs text-red-400 mt-2">{err}</p>}
        <p className="font-mono text-xs text-slate-600 mt-2">Your key is never stored by this page — it goes directly to the API.</p>
      </form>

      {data && (
        <div className="space-y-5">
          {/* Key info */}
          <div className="glass rounded-xl p-5 flex flex-wrap gap-6">
            <div>
              <div className="font-mono text-xs text-slate-500 mb-1">KEY</div>
              <div className="font-mono text-sm text-white">{data.key_prefix}</div>
            </div>
            <div>
              <div className="font-mono text-xs text-slate-500 mb-1">TIER</div>
              <div className="font-orbitron text-sm font-bold" style={{ color: '#00d4ff' }}>{data.tier.toUpperCase()}</div>
            </div>
            <div>
              <div className="font-mono text-xs text-slate-500 mb-1">EMAIL</div>
              <div className="font-mono text-sm text-slate-300">{data.email}</div>
            </div>
            <div>
              <div className="font-mono text-xs text-slate-500 mb-1">LIMITS</div>
              <div className="font-mono text-xs text-slate-300">{data.rate_limits.per_minute}/min · {data.rate_limits.per_hour}/hr</div>
            </div>
          </div>

          {/* Current hour */}
          <div className="glass rounded-xl p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="font-mono text-xs text-slate-500 tracking-widest">CURRENT HOUR</div>
              <ResetTimer seconds={data.current_hour.resets_in_seconds} />
            </div>
            <div className="flex gap-4 mb-4">
              <div className="flex-1 text-center">
                <div className="font-orbitron text-4xl font-black" style={{ color: usedColor }}>{data.current_hour.used}</div>
                <div className="font-mono text-xs text-slate-500 mt-1">Used</div>
              </div>
              <div className="flex-1 text-center">
                <div className="font-orbitron text-4xl font-black text-white">{data.current_hour.remaining}</div>
                <div className="font-mono text-xs text-slate-500 mt-1">Remaining</div>
              </div>
              <div className="flex-1 text-center">
                <div className="font-orbitron text-4xl font-black text-white">{data.rate_limits.per_hour}</div>
                <div className="font-mono text-xs text-slate-500 mt-1">Limit</div>
              </div>
            </div>
            <div className="w-full h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.07)' }}>
              <div className="h-full rounded-full transition-all" style={{ width: `${usedPct}%`, background: usedColor }} />
            </div>
            <div className="font-mono text-xs text-slate-600 mt-2 text-right">{usedPct.toFixed(1)}% used</div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-4">
            <StatCard label="ALL-TIME REQUESTS" value={data.all_time.total_requests.toLocaleString()} color="#00d4ff" />
            <StatCard label="HOURLY RATE LIMIT" value={`${data.rate_limits.per_hour}/hr`} sub={`${data.rate_limits.per_minute}/min burst limit`} />
          </div>

          {/* 7-day chart */}
          <div className="glass rounded-xl p-6">
            <div className="font-mono text-xs text-slate-500 tracking-widest mb-4">LAST 7 DAYS</div>
            <div style={{ height: 180 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.last_7_days} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <XAxis dataKey="label" tick={{ fill: '#4a7090', fontSize: 10, fontFamily: 'var(--font-mono)' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#4a7090', fontSize: 10, fontFamily: 'var(--font-mono)' }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: '#0d1a2e', border: '1px solid rgba(0,212,255,0.15)', borderRadius: 8, fontFamily: 'var(--font-mono)', fontSize: 12 }}
                    labelStyle={{ color: '#4a7090' }} cursor={{ fill: 'rgba(0,212,255,0.05)' }} />
                  <Bar dataKey="requests" fill="#00d4ff" fillOpacity={0.7} radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="glass rounded-xl p-4" style={{ borderColor: 'rgba(245,158,11,0.2)' }}>
            <div className="font-mono text-xs text-slate-500">
              ℹ️ Each API request consumes 1 credit. Cached responses (where <span style={{color:'#00d4ff'}}>"cached": true</span>) still consume 1 credit.
              Failed requests (4xx, 5xx) do not consume credits. Counters reset every hour from your first request in that window.
            </div>
          </div>
        </div>
      )}

      {!data && (
        <div className="text-center py-12">
          <div className="font-mono text-xs text-slate-600">Enter your API key above to see detailed usage statistics</div>
          <div className="mt-4">
            <Link href="/keys" className="font-mono text-xs link-lift transition-colors cursor-pointer" style={{ color: '#00d4ff' }}>
              Don’t have a key yet? Generate one free →
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
