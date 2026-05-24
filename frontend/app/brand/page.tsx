'use client'
import Link from 'next/link'
import { useState } from 'react'

const ASSETS = [
  { file: 'privascan_logo.png',            label: 'Logo' },
  { file: 'privascan_icon_512.png',        label: 'Icon' },
  { file: 'privascan_twitter_profile.png', label: 'Twitter Profile' },
  { file: 'privascan_twitter_banner.png',  label: 'Twitter Banner' },
  { file: 'privascan_telegram.png',        label: 'Telegram' },
]

const COLORS = [
  { hex: '#0a0f1e', name: 'Background' },
  { hex: '#00d4ff', name: 'Cyan'       },
  { hex: '#f59e0b', name: 'Gold'       },
]

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(text)
        setCopied(true)
        setTimeout(() => setCopied(false), 1400)
      }}
      className="font-mono text-xs px-2 py-0.5 rounded transition-all cursor-pointer"
      style={{
        color:      copied ? '#22c55e' : '#64748b',
        border:     `1px solid ${copied ? 'rgba(34,197,94,0.25)' : 'rgba(255,255,255,0.07)'}`,
        background: copied ? 'rgba(34,197,94,0.06)' : 'transparent',
      }}
    >
      {copied ? '✓' : 'copy'}
    </button>
  )
}

export default function BrandPage() {
  return (
    <div className="max-w-4xl mx-auto px-6 pt-28 pb-20">
      <Link href="/" className="font-mono text-xs text-slate-500 hover:text-slate-300 transition-colors inline-flex items-center gap-2 mb-10">
        ← HOME
      </Link>

      <div className="mb-12">
        <div className="font-mono text-xs tracking-widest mb-3" style={{ color: '#00d4ff' }}>// BRAND KIT</div>
        <h1 className="font-orbitron font-black text-white mb-3" style={{ fontSize: 'clamp(1.8rem,4vw,2.6rem)' }}>
          Brand Assets
        </h1>
        <p className="font-mono text-sm text-slate-500 leading-relaxed">
          Free to use with attribution. Do not alter colours or proportions.
        </p>
      </div>

      {/* ── Asset grid ─────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-14">
        {ASSETS.map(a => (
          <div
            key={a.file}
            className="glass rounded-xl overflow-hidden"
            style={{ borderColor: 'rgba(255,255,255,0.05)' }}
          >
            {/* Preview */}
            <div
              className="w-full flex items-center justify-center"
              style={{ height: '180px', background: 'rgba(0,0,0,0.25)' }}
            >
              <img
                src={`/brand/${a.file}`}
                alt={a.label}
                style={{
                  maxWidth:    '100%',
                  maxHeight:   '100%',
                  objectFit:   'contain',
                  padding:     a.file === 'privascan_twitter_banner.png' ? '0' : '20px',
                }}
              />
            </div>

            {/* Download row */}
            <div
              className="flex items-center justify-between px-4 py-3"
              style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}
            >
              <span className="font-mono text-xs text-slate-500">{a.label}</span>
              <a
                href={`/brand/${a.file}`}
                download
                className="font-mono text-xs font-bold px-3 py-1.5 rounded transition-all hover:opacity-80 cursor-pointer"
                style={{
                  color:      '#00d4ff',
                  border:     '1px solid rgba(0,212,255,0.2)',
                  background: 'rgba(0,212,255,0.06)',
                }}
              >
                ↓ PNG
              </a>
            </div>
          </div>
        ))}
      </div>

      {/* ── Colours ────────────────────────────────────── */}
      <div className="mb-14">
        <div className="font-mono text-xs tracking-widest text-slate-500 mb-5">COLOURS</div>
        <div className="flex gap-4 flex-wrap">
          {COLORS.map(c => (
            <div
              key={c.hex}
              className="glass rounded-xl px-5 py-4 flex items-center gap-4"
              style={{ borderColor: 'rgba(255,255,255,0.05)' }}
            >
              <div
                className="w-9 h-9 rounded-lg flex-shrink-0"
                style={{
                  background: c.hex,
                  border: c.hex === '#0a0f1e'
                    ? '1px solid rgba(255,255,255,0.12)'
                    : 'none',
                }}
              />
              <div>
                <div className="font-mono text-xs text-slate-300 mb-1">{c.name}</div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-slate-600">{c.hex}</span>
                  <CopyButton text={c.hex} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Typography ─────────────────────────────────── */}
      <div>
        <div className="font-mono text-xs tracking-widest text-slate-500 mb-5">TYPEFACES</div>
        <div className="flex gap-4 flex-wrap">
          {[
            { name: 'Orbitron',      url: 'https://fonts.google.com/specimen/Orbitron' },
            { name: 'IBM Plex Mono', url: 'https://fonts.google.com/specimen/IBM+Plex+Mono' },
          ].map(f => (
            <a
              key={f.name}
              href={f.url}
              target="_blank"
              rel="noreferrer"
              className="glass rounded-xl px-5 py-4 hover:opacity-80 transition-all cursor-pointer"
              style={{ borderColor: 'rgba(255,255,255,0.05)' }}
            >
              <div
                className="text-white mb-1"
                style={{
                  fontFamily:    f.name === 'Orbitron' ? 'Orbitron, sans-serif' : 'IBM Plex Mono, monospace',
                  fontWeight:    700,
                  fontSize:      f.name === 'Orbitron' ? '20px' : '16px',
                  letterSpacing: f.name === 'Orbitron' ? '.1em' : '.02em',
                }}
              >
                {f.name}
              </div>
              <div className="font-mono text-xs" style={{ color: '#00d4ff' }}>Google Fonts →</div>
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}
