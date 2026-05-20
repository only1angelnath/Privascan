import Link from 'next/link'
import FAQ from '@/components/FAQ'

const CHANNELS = [
  { icon:'✈', title:'Telegram Support', desc:'Fastest response. Post in the community channel or DM the bot.', cta:'Open Telegram', href:'https://t.me/privascan', c:'#00d4ff' },
  { icon:'⌥', title:'GitHub Issues',    desc:'For bugs, incorrect scores, or feature requests. Include the contract address and chain.', cta:'Open Issue', href:'https://github.com', c:'#e2e8f0' },
  { icon:'@', title:'Email',            desc:'For API key issues, abuse reports, or legal/compliance queries.', cta:'support@privascan.xyz', href:'mailto:support@privascan.xyz', c:'#f59e0b' },
]

export default function SupportPage() {
  return (
    <div className="max-w-4xl mx-auto px-6 pt-28 pb-16">
      <Link href="/" className="font-mono text-xs text-slate-500 hover:text-slate-300 transition-colors inline-flex items-center gap-2 mb-8 cursor-pointer">← HOME</Link>
      <div className="mb-12">
        <div className="font-mono text-xs tracking-widest mb-3" style={{ color: '#00d4ff' }}>// HELP</div>
        <h1 className="font-orbitron font-black text-white mb-3" style={{ fontSize: 'clamp(2rem,5vw,3rem)' }}>
          Support
        </h1>
        <p className="font-mono text-sm text-slate-400">Find answers below or reach us directly through any of these channels.</p>
      </div>

      <div className="grid md:grid-cols-3 gap-4 mb-16" id="contact">
        {CHANNELS.map(c => (
          <a key={c.title} href={c.href} target="_blank" rel="noreferrer"
            className="glass glass-hover rounded-xl p-6 block cursor-pointer transition-all hover:scale-[1.01]">
            <div className="font-orbitron text-2xl font-black mb-3" style={{ color: c.c }}>{c.icon}</div>
            <div className="font-orbitron text-sm font-bold text-white mb-2">{c.title}</div>
            <p className="font-mono text-xs text-slate-500 leading-relaxed mb-4">{c.desc}</p>
            <span className="font-mono text-xs font-bold" style={{ color: c.c }}>{c.cta} →</span>
          </a>
        ))}
      </div>

      <FAQ />
    </div>
  )
}
