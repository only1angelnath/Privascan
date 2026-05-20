'use client'
import { useState } from 'react'

const ITEMS = [
  { q: 'What does a PrivaScan risk score mean?',
    a: 'A number from 0 to 100. Lower is safer. It combines six dimensions — code vulnerabilities, ownership structure, liquidity depth, audit coverage, OFAC compliance, and governance — into a single composite. Grades run A (0–20) through F (81–100).' },
  { q: 'How long does a scan take?',
    a: 'First-time scans take 30–60 seconds while Slither analyses the bytecode. Results are cached for one hour — repeat requests return instantly. Curated protocols are automatically rescored every 6 hours.' },
  { q: 'Is PrivaScan free?',
    a: 'Yes. You can scan without an account at 10 requests per hour. Generate a free API key for 100/hr. Pro keys unlock 1,000/hr. No credit card required for either free tier.' },
  { q: 'Which chains are supported?',
    a: 'Ethereum, Arbitrum, Optimism, Base, Polygon, BNB Chain, and Avalanche. More chains are added based on where curated privacy protocols deploy.' },
  { q: 'What does a grade F mean?',
    a: 'Either the composite score exceeded 80, or a hard override is active — OFAC sanctions cap the score at 10, an unresolved exploit caps it at 30. Both result in grade F regardless of other dimensions. Do not interact with grade F contracts without thorough independent investigation.' },
  { q: 'How do I get my protocol added to the curated list?',
    a: 'Submit a request via the Add Protocol page. We review submissions within 72 hours. Requirements: verified source code, mainnet deployment, documented architecture, and a public point of contact.' },
  { q: 'Can I use PrivaScan scores inside my own product?',
    a: 'Yes — that’s what the API is for. Generate a key at /keys, include it as an X-API-Key header, and you get structured JSON back. Free tier handles most use cases. See /docs for full endpoint reference.' },
  { q: 'Is this financial or legal advice?',
    a: 'No. PrivaScan scores are informational tools for risk assessment only. They reflect automated analysis at a point in time and may not capture every risk. Never interact with a protocol based solely on a PrivaScan score.' },
]

export default function FAQ() {
  const [open, setOpen] = useState<number | null>(null)
  return (
    <section className="py-20 max-w-3xl mx-auto px-6">
      <div className="text-center mb-12">
        <div className="font-mono text-xs tracking-widest mb-3" style={{ color: '#00d4ff' }}>// FAQ</div>
        <h2 className="font-orbitron font-bold text-white" style={{ fontSize: 'clamp(1.8rem,4vw,2.4rem)' }}>
          Common Questions
        </h2>
      </div>
      <div className="space-y-2">
        {ITEMS.map((item, i) => (
          <div key={i} className="glass glass-hover rounded-xl overflow-hidden cursor-pointer"
            onClick={() => setOpen(open === i ? null : i)}>
            <div className="flex items-center justify-between px-6 py-4 gap-4">
              <span className="font-mono text-sm text-white font-medium">{item.q}</span>
              <span className="font-mono text-slate-500 text-lg shrink-0 transition-transform"
                style={{ transform: open === i ? 'rotate(45deg)' : 'none' }}>+</span>
            </div>
            {open === i && (
              <div className="px-6 pb-5 font-mono text-sm text-slate-400 leading-relaxed"
                style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 16 }}>
                {item.a}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
