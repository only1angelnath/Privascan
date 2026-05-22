'use client'
import { useState, FormEvent } from 'react'
import Link from 'next/link'

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api/v1'
const CHAINS = ['Ethereum','Arbitrum','Optimism','Base','Polygon','BNB Chain','Avalanche','Multiple']
const REQS = [
  'Verified and published source code on a block explorer',
  'Live mainnet deployment (testnet-only protocols not eligible)',
  'Documented architecture — whitepaper, GitHub, or technical specification',
  'No active OFAC sanctions on core contracts',
  'A public point of contact (Twitter, email, or Telegram)',
]

export default function RequestPage() {
  const [sent, setSent]       = useState(false)
  const [loading, setLoading] = useState(false)
  const [err, setErr]         = useState('')
  const [form, setForm]       = useState({
    name:'', website:'', github:'', chain:'Ethereum',
    desc:'', email:'', address:'', x_handle:'',
  })
  function set(k: string, v: string) { setForm(f => ({ ...f, [k]: v })) }

  async function submit(e: FormEvent) {
    e.preventDefault(); setErr(''); setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/protocols/request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: form.name, website: form.website, github: form.github,
          address: form.address, chain: form.chain,
          description: form.desc, email: form.email, x_handle: form.x_handle,
        }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error((data as Record<string,string>).detail || `Error ${res.status}`)
      }
      setSent(true)
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Submission failed. Please try again.')
    } finally { setLoading(false) }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 pt-28 pb-16">
      <Link href="/" className="font-mono text-xs text-slate-500 hover:text-slate-300 transition-colors inline-flex items-center gap-2 mb-8">← HOME</Link>
      <div className="mb-10">
        <div className="font-mono text-xs tracking-widest mb-3" style={{color:'#00d4ff'}}>// CURATED LIST</div>
        <h1 className="font-orbitron font-black text-white mb-3" style={{fontSize:'clamp(2rem,5vw,3rem)'}}>Request Protocol Addition</h1>
        <p className="font-mono text-sm text-slate-400 leading-relaxed">We review every submission within 72 hours. Approved protocols are added to the curated list and automatically rescored every 6 hours.</p>
      </div>
      <div className="glass rounded-xl p-6 mb-8" style={{borderColor:'rgba(245,158,11,0.2)'}}>
        <div className="font-mono text-xs tracking-widest mb-4" style={{color:'#f59e0b'}}>REQUIREMENTS FOR INCLUSION</div>
        <ul className="space-y-2">{REQS.map((r,i)=>(
          <li key={i} className="flex gap-3 font-mono text-xs text-slate-400">
            <span style={{color:'#00d4ff'}}>✓</span> {r}
          </li>
        ))}</ul>
      </div>
      {!sent ? (
        <form onSubmit={submit} className="glass rounded-2xl p-8 space-y-5">
          {[
            {k:'name',    l:'Protocol Name',            ph:'Railgun, Aztec, etc.',  type:'text',  req:true},
            {k:'website', l:'Website URL',              ph:'https://',               type:'url',   req:true},
            {k:'github',  l:'GitHub Repository',        ph:'https://github.com/',    type:'url',   req:false},
            {k:'address', l:'Primary Contract Address', ph:'0x…',                   type:'text',  req:true},
            {k:'email',   l:'Your Contact Email',       ph:'you@example.com',        type:'email', req:true},
            {k:'x_handle',l:'X / Twitter Handle',       ph:'@protocol',              type:'text',  req:false},
          ].map(f=>(
            <div key={f.k}>
              <label className="font-mono text-xs text-slate-500 tracking-widest block mb-2">
                {f.l.toUpperCase()} {f.req&&<span style={{color:'#ef4444'}}>*</span>}
              </label>
              <input type={f.type} value={(form as Record<string,string>)[f.k]}
                onChange={e=>set(f.k,e.target.value)} required={f.req} placeholder={f.ph}
                className="w-full glass font-mono text-sm text-white px-4 py-3 rounded-lg focus:outline-none placeholder:text-slate-700 transition-colors"/>
            </div>
          ))}
          <div>
            <label className="font-mono text-xs text-slate-500 tracking-widest block mb-2">PRIMARY CHAIN <span style={{color:'#ef4444'}}>*</span></label>
            <select value={form.chain} onChange={e=>set('chain',e.target.value)}
              className="w-full glass font-mono text-sm text-slate-300 px-4 py-3 rounded-lg focus:outline-none">
              {CHAINS.map(c=><option key={c} value={c} style={{background:'#0a0f1e'}}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="font-mono text-xs text-slate-500 tracking-widest block mb-2">PROTOCOL DESCRIPTION <span style={{color:'#ef4444'}}>*</span></label>
            <textarea value={form.desc} onChange={e=>set('desc',e.target.value)} required rows={4}
              placeholder="Briefly describe what the protocol does and why it should be included…"
              className="w-full glass font-mono text-sm text-white px-4 py-3 rounded-lg focus:outline-none placeholder:text-slate-700 resize-none"/>
          </div>
          {err&&(
            <div className="glass rounded-lg px-4 py-3" style={{borderColor:'rgba(239,68,68,0.3)'}}>
              <p className="font-mono text-xs text-red-400">{err}</p>
            </div>
          )}
          <button type="submit" disabled={loading}
            className="w-full font-orbitron text-sm font-bold py-3.5 rounded-lg tracking-wider hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            style={{background:'#00d4ff',color:'#0a0f1e'}}>
            {loading ? 'SUBMITTING…' : 'SUBMIT FOR REVIEW →'}
          </button>
          <p className="font-mono text-xs text-slate-600 text-center">
            Submissions are reviewed by the PrivaScan team within 72 hours.
          </p>
        </form>
      ) : (
        <div className="glass rounded-2xl p-10 text-center" style={{borderColor:'rgba(34,197,94,0.3)'}}>
          <div className="font-orbitron text-2xl font-black mb-3" style={{color:'#22c55e'}}>✓ SUBMITTED</div>
          <p className="font-mono text-sm text-slate-400 mb-6 leading-relaxed">
            Thanks for the submission. We will review <strong className="text-white">{form.name}</strong> within 72 hours and reach out to {form.email}.
          </p>
          <Link href="/" className="font-mono text-sm hover:underline" style={{color:'#00d4ff'}}>← Back to home</Link>
        </div>
      )}
    </div>
  )
}
