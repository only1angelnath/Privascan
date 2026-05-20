'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import Logo from './Logo'

const LINKS = [
  { href: '/protocols',  label: 'Protocols'    },
  { href: '/request',    label: 'Add Protocol' },
  { href: '/whitepaper', label: 'Whitepaper'   },
  { href: '/api',        label: 'API Docs'     },
  { href: '/usage',      label: 'API Usage'    },
]

export default function NavBar() {
  const [sc, setSc]     = useState(false)
  const [open, setOpen] = useState(false)
  const path = usePathname()

  useEffect(() => {
    const fn = () => setSc(window.scrollY > 30)
    window.addEventListener('scroll', fn, { passive: true })
    return () => window.removeEventListener('scroll', fn)
  }, [])

  const cls = (href: string) =>
    `font-mono text-sm px-3 py-1.5 rounded-md transition-all cursor-pointer link-lift ${
      path === href
        ? 'text-white bg-white/10 font-bold'
        : 'text-slate-300 hover:text-white hover:bg-white/[0.08]'
    }`

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 transition-all duration-300"
      style={{
        background: sc ? 'rgba(10,15,30,0.88)' : 'rgba(10,15,30,0.6)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
      }}>
      <div className="max-w-7xl mx-auto px-6 h-[66px] flex items-center justify-between gap-4">
        <Link href="/" className="shrink-0 cursor-pointer"><Logo size="sm" /></Link>

        <div className="hidden md:flex items-center gap-1">
          {LINKS.map(l => (
            <Link key={l.href} href={l.href} className={cls(l.href)}>{l.label}</Link>
          ))}
          <a href="https://t.me/PrivaScanBot" target="_blank" rel="noreferrer"
            className="font-mono text-sm text-slate-300 hover:text-white hover:bg-white/[0.08] transition-all px-3 py-1.5 rounded-md cursor-pointer link-lift">
            Bot ↗
          </a>
        </div>

        <div className="hidden md:flex items-center gap-2 shrink-0">
          <Link href="/keys"
            className="font-orbitron text-xs font-bold px-4 py-2 rounded-lg transition-all cursor-pointer hover:opacity-90 active:scale-95"
            style={{ background: '#00d4ff', color: '#0a0f1e' }}>
            Get API Key
          </Link>
        </div>

        <button className="md:hidden text-slate-300 hover:text-white p-2 rounded cursor-pointer"
          onClick={() => setOpen(!open)}>
          {open ? '✕' : '☰'}
        </button>
      </div>

      {open && (
        <div className="md:hidden border-t px-6 py-4 space-y-1"
          style={{ background: 'rgba(10,15,30,0.96)', borderColor: 'rgba(255,255,255,0.08)' }}>
          {LINKS.map(l => (
            <Link key={l.href} href={l.href} onClick={() => setOpen(false)}
              className="block font-mono text-sm text-slate-300 hover:text-white py-2 px-3 rounded-md hover:bg-white/[0.08] transition-all cursor-pointer">
              {l.label}
            </Link>
          ))}
          <a href="https://t.me/PrivaScanBot" target="_blank" rel="noreferrer"
            className="block font-mono text-sm text-slate-300 hover:text-white py-2 px-3 rounded-md cursor-pointer">
            Bot ↗
          </a>
          <div className="pt-3">
            <Link href="/keys" onClick={() => setOpen(false)}
              className="font-orbitron text-xs font-bold px-4 py-2 rounded-lg cursor-pointer"
              style={{ background: '#00d4ff', color: '#0a0f1e' }}>
              Get API Key
            </Link>
          </div>
        </div>
      )}
    </nav>
  )
}
