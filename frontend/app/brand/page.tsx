'use client'
import Link from 'next/link'
import { useState } from 'react'

const ASSETS = [
  { id:'logo',            file:'privascan_logo.png',            label:'Logo — Horizontal',    desc:'Full wordmark with icon. Use on dark backgrounds.',  size:'960 × 360px',  use:'Website · README · Press kit' },
  { id:'icon',            file:'privascan_icon_512.png',        label:'Icon — 512px',          desc:'Hex radar icon only. Use at small sizes.',           size:'512 × 512px',  use:'Favicon · App icon · OG image' },
  { id:'twitter-profile', file:'privascan_twitter_profile.png', label:'X / Twitter Profile',   desc:'Square profile image for @PrivaScan.',               size:'800 × 800px',  use:'X profile picture' },
  { id:'twitter-banner',  file:'privascan_twitter_banner.png',  label:'X / Twitter Banner',    desc:'Header image. Crops to 3:1 on mobile.',              size:'1500 × 500px', use:'X header image' },
  { id:'telegram',        file:'privascan_telegram.png',        label:'Telegram Bot Image',    desc:'Profile image for @PrivaScanBot.',                   size:'640 × 640px',  use:'Telegram bot profile' },
]

const COLORS = [
  { name:'Background',  hex:'#0a0f1e', label:'Page bg' },
  { name:'Cyan',        hex:'#00d4ff', label:'Primary accent' },
  { name:'Gold',        hex:'#f59e0b', label:'Secondary accent' },
  { name:'Grade A',     hex:'#22c55e', label:'Low risk' },
  { name:'Grade D',     hex:'#f97316', label:'High risk' },
  { name:'Grade F',     hex:'#ef4444', label:'Critical' },
  { name:'OFAC',        hex:'#7c3aed', label:'Sanctioned' },
  { name:'Exploit',     hex:'#b91c1c', label:'Exploit active' },
]

const FONTS = [
  { name:'Orbitron',      role:'Display / Headings', weights:'700, 900', url:'https://fonts.google.com/specimen/Orbitron' },
  { name:'IBM Plex Mono', role:'Body / Data / UI',   weights:'400, 500', url:'https://fonts.google.com/specimen/IBM+Plex+Mono' },
]

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500) }}
      className="font-mono text-xs px-2 py-0.5 rounded transition-all cursor-pointer"
      style={{ color: copied ? '#22c55e' : '#00d4ff', border: `1px solid ${copied ? 'rgba(34,197,94,0.3)' : 'rgba(0,212,255,0.2)'}`, background: copied ? 'rgba(34,197,94,0.06)' : 'rgba(0,212,255,0.05)' }}
    >
      {copied ? '✓ copied' : 'copy'}
    </button>
  )
}

export default function BrandPage() {
  return (
    <div className="max-w-5xl mx-auto px-6 pt-28 pb-20">
      <Link href="/" className="font-mono text-xs text-slate-500 hover:text-slate-300 transition-colors inline-flex items-center gap-2 mb-10">← HOME</Link>

      <div className="mb-14">
        <div className="font-mono text-xs tracking-widest mb-3" style={{color:'#00d4ff'}}>// BRAND KIT</div>
        <h1 className="font-orbitron font-black text-white mb-4" style={{fontSize:'clamp(2rem,5vw,3rem)'}}>PrivaScan Brand Assets</h1>
        <p className="font-mono text-sm text-slate-400 leading-relaxed max-w-2xl">
          Official logos, icons, and colour values for press, integrations, and community use.
          Assets are free to use with attribution. Do not alter colours, proportions, or typography.
        </p>
      </div>

      {/* Download grid */}
      <section className="mb-16">
        <div className="font-mono text-xs tracking-widest text-slate-500 mb-6">DOWNLOADABLE ASSETS</div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {ASSETS.map(a => (
            <div key={a.id} className="glass rounded-xl overflow-hidden flex flex-col" style={{borderColor:'rgba(0,212,255,0.08)'}}>
              <div className="w-full flex items-center justify-center bg-black/20" style={{height:'160px'}}>
                <img
                  src={`/brand/${a.file}`}
                  alt={a.label}
                  style={{maxWidth:'100%', maxHeight:'100%', objectFit:'contain', padding: a.id === 'twitter-banner' ? '0' : '16px'}}
                />
              </div>
              <div className="p-5 flex flex-col gap-3 flex-1">
                <div>
                  <div className="font-orbitron text-sm font-bold text-white mb-1">{a.label}</div>
                  <p className="font-mono text-xs text-slate-500">{a.desc}</p>
                </div>
                <div className="flex gap-4 font-mono text-xs">
                  <div><div className="text-slate-600 mb-0.5">SIZE</div><div className="text-slate-400">{a.size}</div></div>
                  <div><div className="text-slate-600 mb-0.5">USE FOR</div><div className="text-slate-400">{a.use}</div></div>
                </div>
                <a
                  href={`/brand/${a.file}`}
                  download
                  className="mt-auto inline-flex items-center justify-center gap-2 font-orbitron text-xs font-bold py-2.5 px-4 rounded-lg tracking-wider hover:opacity-90 transition-all"
                  style={{background:'rgba(0,212,255,0.1)',color:'#00d4ff',border:'1px solid rgba(0,212,255,0.25)'}}
                >
                  ↓ DOWNLOAD PNG
                </a>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Colours */}
      <section className="mb-16">
        <div className="font-mono text-xs tracking-widest text-slate-500 mb-6">COLOUR PALETTE</div>
        <div className="glass rounded-xl p-6" style={{borderColor:'rgba(0,212,255,0.08)'}}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {COLORS.map(c => (
              <div key={c.hex} className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg flex-shrink-0" style={{background:c.hex, border: c.hex==='#0a0f1e' ? '1px solid rgba(255,255,255,0.1)' : 'none'}}/>
                <div>
                  <div className="font-mono text-xs text-slate-300">{c.name}</div>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="font-mono text-xs text-slate-600">{c.hex}</span>
                    <CopyButton text={c.hex}/>
                  </div>
                  <div className="font-mono text-xs text-slate-600 mt-0.5">{c.label}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Typography */}
      <section className="mb-16">
        <div className="font-mono text-xs tracking-widest text-slate-500 mb-6">TYPOGRAPHY</div>
        <div className="grid md:grid-cols-2 gap-4">
          {FONTS.map(f => (
            <div key={f.name} className="glass rounded-xl p-6" style={{borderColor:'rgba(0,212,255,0.08)'}}>
              <div className="font-mono text-xs text-slate-600 mb-3 tracking-widest">{f.role.toUpperCase()}</div>
              <div className="text-white mb-3" style={{fontFamily: f.name==='Orbitron' ? 'Orbitron, sans-serif' : 'IBM Plex Mono, monospace', fontWeight:700, fontSize: f.name==='Orbitron' ? '28px' : '22px', letterSpacing: f.name==='Orbitron' ? '.1em' : '.02em'}}>{f.name}</div>
              <div className="font-mono text-xs text-slate-500 mb-4">Weights: {f.weights}</div>
              <a href={f.url} target="_blank" rel="noreferrer" className="font-mono text-xs hover:underline" style={{color:'#00d4ff'}}>Google Fonts →</a>
            </div>
          ))}
        </div>
      </section>

      {/* Usage rules */}
      <section className="mb-16">
        <div className="font-mono text-xs tracking-widest text-slate-500 mb-6">USAGE GUIDELINES</div>
        <div className="glass rounded-xl p-6" style={{borderColor:'rgba(245,158,11,0.15)'}}>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <div className="font-mono text-xs tracking-widest mb-3" style={{color:'#22c55e'}}>✓ YOU MAY</div>
              <ul className="space-y-2">
                {['Use assets in press articles and reviews','Display the logo when integrating the API','Use in open-source project READMEs','Reference in community content with credit'].map(r => (
                  <li key={r} className="flex gap-2 font-mono text-xs text-slate-400"><span style={{color:'#22c55e'}}>·</span>{r}</li>
                ))}
              </ul>
            </div>
            <div>
              <div className="font-mono text-xs tracking-widest mb-3" style={{color:'#ef4444'}}>✗ DO NOT</div>
              <ul className="space-y-2">
                {["Alter colours, proportions, or typography","Use as your own product's brand mark","Place on backgrounds that reduce legibility","Imply official endorsement without permission"].map(r => (
                  <li key={r} className="flex gap-2 font-mono text-xs text-slate-400"><span style={{color:'#ef4444'}}>·</span>{r}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <div className="glass rounded-xl p-8 text-center" style={{borderColor:'rgba(0,212,255,0.1)'}}>
        <div className="font-mono text-xs text-slate-500 mb-2 tracking-widest">NEED SOMETHING ELSE?</div>
        <p className="font-mono text-sm text-slate-400 mb-6">SVG source files, white logo variants, or custom sizes — open an issue on GitHub.</p>
        <a href="https://github.com/only1angelnath/Privascan/issues" target="_blank" rel="noreferrer"
          className="inline-block font-orbitron text-sm font-bold px-8 py-3 rounded-lg tracking-wider hover:opacity-90 transition-all"
          style={{background:'rgba(0,212,255,0.08)',color:'#00d4ff',border:'1px solid rgba(0,212,255,0.2)'}}>
          OPEN A GITHUB ISSUE →
        </a>
      </div>
    </div>
  )
}
