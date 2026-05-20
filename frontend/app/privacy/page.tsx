import Link from 'next/link'

const ITEMS = [
  { h:'What we collect', t:'Email addresses submitted during API key generation. API request logs (endpoint, timestamp, anonymised IP) for rate limiting and abuse prevention. No personal browsing data, no tracking pixels, no third-party analytics.' },
  { h:'What we do not collect', t:'We do not track which contract addresses you scan. We do not store wallet addresses, transaction histories, or any on-chain data linked to your identity. We do not use cookies for tracking.' },
  { h:'How data is used', t:'Email addresses are stored to associate API keys with a point of contact. They are never sold, shared with third parties, or used for marketing without explicit opt-in. API logs are retained for 30 days for rate limit enforcement and deleted automatically.' },
  { h:'API key security', t:'Raw API keys are shown once at generation and never stored. We store only the SHA-256 hash of each key. If you lose your key, generate a new one — we cannot recover the original.' },
  { h:'Data retention', t:'Email addresses associated with active API keys are retained until you request deletion. Keys that have been inactive for 12 months are purged. Score reports and analysis results contain no user-identifying information.' },
  { h:'Third-party services', t:'PrivaScan queries Etherscan, Alchemy, DefiLlama, and Dune Analytics for on-chain data. We also screen against the OFAC consolidated SDN list. These services have their own privacy policies.' },
  { h:'Your rights', t:'You may request deletion of your email and associated API keys at any time by emailing privacy@privascan.xyz. We will process requests within 14 days.' },
  { h:'Contact', t:'For privacy-related requests: privacy@privascan.xyz. For general support: support@privascan.xyz or Telegram @privascan.' },
]

export default function PrivacyPage() {
  return (
    <div className="max-w-3xl mx-auto px-6 pt-28 pb-16">
      <Link href="/" className="font-mono text-xs text-slate-500 hover:text-slate-300 transition-colors inline-flex items-center gap-2 mb-8 cursor-pointer">← HOME</Link>
      <div className="mb-10">
        <div className="font-mono text-xs tracking-widest mb-3" style={{ color: '#00d4ff' }}>// PRIVACY</div>
        <h1 className="font-orbitron font-black text-white mb-2" style={{ fontSize: 'clamp(2rem,5vw,3rem)' }}>
          Privacy Policy
        </h1>
        <p className="font-mono text-xs text-slate-500">Last updated: May 2026 · PrivaScan collects minimal data and never sells it.</p>
      </div>
      <div className="glass rounded-xl p-8">
        <div className="space-y-6">
          {ITEMS.map((item,i) => (
            <div key={i} style={i > 0 ? { borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 24 } : {}}>
              <div className="font-orbitron text-sm font-bold mb-2" style={{ color: '#00d4ff' }}>{item.h}</div>
              <p className="font-mono text-sm text-slate-400 leading-relaxed">{item.t}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
