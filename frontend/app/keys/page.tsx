'use client'
import { useState, FormEvent } from 'react'
import Link from 'next/link'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export default function KeysPage() {
  const [step, setStep]         = useState<1|2|3|4>(1)
  const [code, setCode]         = useState('')
  const [tgUserId, setTgUserId] = useState('')
  const [email, setEmail]       = useState('')
  const [key, setKey]           = useState('')
  const [err, setErr]           = useState('')
  const [loading, setLoad]      = useState(false)
  const [visible, setVis]       = useState(false)
  const [copied, setCopied]     = useState(false)

  async function verifyCode(e: FormEvent) {
    e.preventDefault()
    if (code.length !== 6) { setErr('Enter the 6-digit code from @PrivaScanBot'); return }
    setErr(''); setLoad(true)
    try {
      const r = await fetch(`${API}/keys/verify-telegram`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'Verification failed')
      setTgUserId(d.telegram_user_id)
      setStep(3)
    } catch (e: any) { setErr(e.message) }
    finally { setLoad(false) }
  }

  async function generateKey(e: FormEvent) {
    e.preventDefault()
    setErr(''); setLoad(true)
    try {
      const r = await fetch(`${API}/keys/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, tier: 'free' }),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'Generation failed')
      setKey(d.api_key); setStep(4)
    } catch (e: any) { setErr(e.message) }
    finally { setLoad(false) }
  }

  function copyKey() {
    navigator.clipboard.writeText(key).then(() => {
      setCopied(true); setTimeout(() => setCopied(false), 2500)
    })
  }

  const masked = key ? key.slice(0, 6) + '•'.repeat(28) + key.slice(-4) : ''

  const STEPS = [
    { n: 1, l: 'Open Bot'  },
    { n: 2, l: 'Enter Code'},
    { n: 3, l: 'Email'     },
    { n: 4, l: 'Done'      },
  ] as const

  return (
    <div className="max-w-xl mx-auto px-6 pt-28 pb-16">
      <Link href="/" className="font-mono text-xs text-slate-500 hover:text-white link-lift transition-colors inline-flex items-center gap-2 mb-8 cursor-pointer">
        ← HOME
      </Link>

      <div className="mb-10 text-center">
        <div className="font-mono text-xs tracking-widest mb-3" style={{ color: '#00d4ff' }}>// API ACCESS</div>
        <h1 className="font-orbitron font-black text-white mb-2 heading-glow" style={{ fontSize: 'clamp(1.8rem,5vw,2.8rem)' }}>
          Get Your Free API Key
        </h1>
        <p className="font-mono text-xs text-slate-500">500 req/hr · No credit card · Verified via Telegram</p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center justify-center gap-1 mb-10">
        {STEPS.map((s, i) => (
          <div key={s.n} className="flex items-center gap-1">
            <div className="flex items-center gap-1.5">
              <div className="w-6 h-6 rounded-full flex items-center justify-center font-orbitron text-xs font-bold transition-all"
                style={{ background: step >= s.n ? '#00d4ff' : 'rgba(255,255,255,0.08)', color: step >= s.n ? '#0a0f1e' : '#4a7090' }}>
                {step > s.n ? '✓' : s.n}
              </div>
              <span className="font-mono text-xs hidden sm:block" style={{ color: step >= s.n ? '#e2e8f0' : '#4a7090' }}>{s.l}</span>
            </div>
            {i < STEPS.length - 1 && (
              <div className="w-6 h-px mx-1" style={{ background: step > s.n ? '#00d4ff' : 'rgba(255,255,255,0.1)' }} />
            )}
          </div>
        ))}
      </div>

      {/* STEP 1 — Open @PrivaScanBot */}
      {step === 1 && (
        <div className="glass rounded-2xl p-8" style={{ borderColor: 'rgba(0,212,255,0.2)' }}>
          <div className="text-center mb-6">
            <div className="font-orbitron text-4xl font-black mb-3" style={{ color: '#00d4ff' }}>TG</div>
            <h2 className="font-orbitron text-xl font-bold text-white mb-2">Open @PrivaScanBot</h2>
            <p className="font-mono text-sm text-slate-400 leading-relaxed">
              Send <code className="font-mono text-xs px-1.5 py-0.5 rounded" style={{ color: '#00d4ff', background: 'rgba(0,212,255,0.1)' }}>/verify</code> to
              the bot. It will reply with a 6-digit code. Then come back here and enter it.
            </p>
          </div>
          <a href="https://t.me/PrivaScanBot" target="_blank" rel="noreferrer"
            className="flex items-center justify-center gap-2 font-orbitron text-sm font-bold px-6 py-3.5 rounded-xl mb-4 w-full transition-all hover:opacity-90 active:scale-95 cursor-pointer"
            style={{ background: '#00d4ff', color: '#0a0f1e' }}>
            Open @PrivaScanBot →
          </a>
          <button onClick={() => setStep(2)}
            className="w-full font-mono text-sm text-slate-300 hover:text-white py-2.5 rounded-xl glass glass-hover cursor-pointer transition-all link-lift">
            I’ve got my code →
          </button>
          <div className="mt-6 pt-5 border-t" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
            <div className="glass rounded-xl px-4 py-3 flex items-center justify-between" style={{ borderColor: 'rgba(255,255,255,0.08)' }}>
              <div>
                <div className="font-orbitron text-sm font-bold text-white">Pro Tier</div>
                <div className="font-mono text-xs text-slate-500 mt-0.5">2,000 req/hr · No verification required</div>
              </div>
              <span className="font-mono text-xs font-bold px-2.5 py-1 rounded" style={{ background: 'rgba(245,158,11,0.15)', color: '#f59e0b' }}>
                Coming Soon
              </span>
            </div>
          </div>
        </div>
      )}

      {/* STEP 2 — Enter code */}
      {step === 2 && (
        <form onSubmit={verifyCode} className="glass rounded-2xl p-8 space-y-5">
          <div className="text-center mb-2">
            <h2 className="font-orbitron text-xl font-bold text-white mb-1">Enter Your Code</h2>
            <p className="font-mono text-xs text-slate-400">
              Paste the 6-digit code from @PrivaScanBot
            </p>
          </div>
          <div>
            <input
              type="text"
              value={code}
              onChange={e => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              maxLength={6}
              className="w-full glass font-orbitron text-3xl font-black text-center text-white px-4 py-5 rounded-xl focus:outline-none placeholder:text-slate-700 tracking-[0.4em] cursor-text"
              style={{ letterSpacing: '0.4em' }}
            />
          </div>
          {err && <p className="font-mono text-xs text-red-400 text-center">{err}</p>}
          <button type="submit" disabled={loading || code.length !== 6}
            className="w-full font-orbitron text-sm font-bold py-3.5 rounded-xl transition-all cursor-pointer hover:opacity-90 active:scale-[0.99] disabled:opacity-40 disabled:cursor-not-allowed"
            style={{ background: '#00d4ff', color: '#0a0f1e' }}>
            {loading ? 'VERIFYING…' : 'VERIFY CODE →'}
          </button>
          <div className="flex gap-3">
            <button type="button" onClick={() => setStep(1)}
              className="flex-1 font-mono text-xs text-slate-500 hover:text-white link-lift transition-colors cursor-pointer py-2">
              ← Back
            </button>
            <a href="https://t.me/PrivaScanBot" target="_blank" rel="noreferrer"
              className="flex-1 font-mono text-xs text-slate-500 hover:text-white link-lift transition-colors cursor-pointer py-2 text-center">
              Get new code ↗
            </a>
          </div>
        </form>
      )}

      {/* STEP 3 — Email */}
      {step === 3 && (
        <form onSubmit={generateKey} className="glass rounded-2xl p-8 space-y-5">
          <div className="glass rounded-xl px-4 py-3 flex items-center gap-3" style={{ borderColor: 'rgba(34,197,94,0.3)' }}>
            <span className="font-mono text-xs" style={{ color: '#22c55e' }}>✓ Telegram verified</span>
            <span className="font-mono text-xs text-slate-500 ml-auto">ID: {tgUserId.slice(-6)}</span>
          </div>
          <div>
            <label className="font-mono text-xs text-slate-500 tracking-widest block mb-2">
              EMAIL ADDRESS <span style={{ color: '#ef4444' }}>*</span>
            </label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required
              placeholder="you@example.com"
              className="w-full glass font-mono text-sm text-white px-4 py-3 rounded-xl focus:outline-none placeholder:text-slate-700 cursor-text" />
            <p className="font-mono text-xs text-slate-600 mt-1.5">To associate your key. Never used for marketing.</p>
          </div>
          <div className="glass rounded-xl px-4 py-3" style={{ borderColor: 'rgba(0,212,255,0.2)' }}>
            <div className="font-orbitron text-sm font-bold text-white">Free Tier</div>
            <div className="font-mono text-xs mt-1" style={{ color: '#00d4ff' }}>500 requests / hour · 15 requests / minute</div>
          </div>
          {err && <p className="font-mono text-xs text-red-400">{err}</p>}
          <button type="submit" disabled={loading}
            className="w-full font-orbitron text-sm font-bold py-3.5 rounded-xl transition-all cursor-pointer hover:opacity-90 active:scale-[0.99] disabled:opacity-50"
            style={{ background: '#00d4ff', color: '#0a0f1e' }}>
            {loading ? 'GENERATING…' : 'GENERATE FREE KEY →'}
          </button>
        </form>
      )}

      {/* STEP 4 — Key with copy + eye */}
      {step === 4 && (
        <div className="glass rounded-2xl p-8" style={{ borderColor: 'rgba(34,197,94,0.3)' }}>
          <div className="text-center mb-6">
            <div className="font-orbitron text-2xl font-black mb-1" style={{ color: '#22c55e' }}>✓ KEY GENERATED</div>
            <p className="font-mono text-xs text-slate-400">This key will <strong className="text-white">not</strong> be shown again. Copy it now.</p>
          </div>
          <div className="glass rounded-xl p-4 mb-3 min-h-[56px] flex items-center" style={{ borderColor: 'rgba(0,212,255,0.3)' }}>
            <span className="font-mono text-sm break-all" style={{ color: '#00d4ff' }}>
              {visible ? key : masked}
            </span>
          </div>
          <div className="flex gap-2 mb-5">
            <button onClick={() => setVis(!visible)}
              className="flex-1 flex items-center justify-center gap-2 font-mono text-xs py-2.5 rounded-xl glass glass-hover cursor-pointer transition-all">
              {visible ? '● Hide' : '○ Reveal'}
            </button>
            <button onClick={copyKey}
              className="flex-1 font-orbitron text-xs font-bold py-2.5 rounded-xl transition-all cursor-pointer hover:opacity-90 active:scale-[0.99]"
              style={{ background: copied ? '#22c55e' : '#00d4ff', color: '#0a0f1e' }}>
              {copied ? '✓ Copied!' : '□ Copy Key'}
            </button>
          </div>
          <div className="glass rounded-xl px-4 py-3 mb-5 space-y-1.5" style={{ borderColor: 'rgba(255,255,255,0.08)' }}>
            <div className="font-mono text-xs text-slate-500">Add to all requests:</div>
            <div className="font-mono text-xs" style={{ color: '#f59e0b' }}>X-API-Key: {key.slice(0, 14)}…</div>
            <div className="font-mono text-xs text-slate-600">500 req/hr · Free tier · Resets every hour</div>
          </div>
          <div className="flex gap-3">
            <Link href="/api"
              className="flex-1 font-mono text-xs py-2.5 rounded-xl glass glass-hover cursor-pointer transition-all text-center link-lift">
              API Docs
            </Link>
            <Link href="/usage"
              className="flex-1 font-mono text-xs py-2.5 rounded-xl glass glass-hover cursor-pointer transition-all text-center link-lift">
              Check Usage
            </Link>
            <Link href="/score/ethereum/0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF"
              className="flex-1 font-orbitron text-xs font-bold py-2.5 rounded-xl cursor-pointer transition-all hover:opacity-90 text-center"
              style={{ background: '#00d4ff', color: '#0a0f1e' }}>
              Start Scanning
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
