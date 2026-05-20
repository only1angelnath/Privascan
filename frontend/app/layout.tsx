import type { Metadata } from 'next'
import './globals.css'
import NavBar from '@/components/NavBar'
import Footer from '@/components/Footer'

export const metadata: Metadata = {
  title: 'PrivaScan — EVM Privacy Protocol Risk Intelligence',
  description: 'Deterministic risk scoring for EVM privacy protocols. Code analysis, OFAC screening, TVL confidence, audit history. Free API.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=IBM+Plex+Mono:ital,wght@0,400;0,500;0,700;1,400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen antialiased" style={{ background: '#0a0f1e', color: '#e2e8f0' }}>
        <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
          <div style={{ position: 'absolute', top: '12%', left: '6%', width: '520px', height: '520px', background: 'rgba(0,212,255,0.045)', borderRadius: '50%', filter: 'blur(110px)' }} />
          <div style={{ position: 'absolute', top: '58%', right: '6%', width: '420px', height: '420px', background: 'rgba(245,158,11,0.038)', borderRadius: '50%', filter: 'blur(100px)' }} />
          <div style={{ position: 'absolute', bottom: '12%', left: '38%', width: '360px', height: '360px', background: 'rgba(0,212,255,0.028)', borderRadius: '50%', filter: 'blur(90px)' }} />
        </div>
        <NavBar />
        <main className="relative z-10">{children}</main>
        <Footer />
      </body>
    </html>
  )
}
