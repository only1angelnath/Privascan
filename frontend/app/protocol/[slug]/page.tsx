import Link from 'next/link'
import GradeBadge from '@/components/GradeBadge'
import { getProtocol } from '@/lib/api'
const CHAIN:Record<number,string>={1:'Ethereum',10:'Optimism',56:'BNB Smart Chain',137:'Polygon',42161:'Arbitrum',8453:'Base',43114:'Avalanche'}
const CHAIN_SLUG:Record<number,string>={1:'ethereum',10:'optimism',56:'bsc',137:'polygon',42161:'arbitrum',8453:'base',43114:'avalanche'}
const API = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api/v1'

async function getContractScore(chain_id:number, address:string) {
  try {
    const slug = CHAIN_SLUG[chain_id] || 'ethereum'
    const r = await fetch(`${API}/score/${slug}/${address}`, { next: { revalidate: 300 } })
    if (!r.ok) return null
    return await r.json()
  } catch { return null }
}

export default async function ProtocolPage({params}:{params:{slug:string}}){
  let proto:any=null
  try{ proto=await getProtocol(params.slug) }catch{}
  if(!proto) return(
    <div className="max-w-7xl mx-auto px-6 pt-28 text-center">
      <div className="font-orbitron text-2xl text-white mb-4">Protocol Not Found</div>
      <Link href="/protocols" className="font-mono text-xs text-cyan-400">← Back to directory</Link>
    </div>
  )
  const ls=proto.latest_score

  // Fetch scores for all contracts in parallel
  const contractScores: Record<string, any> = {}
  await Promise.all(
    (proto.contracts || []).map(async (c: any) => {
      const score = await getContractScore(c.chain_id, c.address)
      if (score) contractScores[c.address] = score
    })
  )

  return(
    <div className="max-w-7xl mx-auto px-6 pt-28 pb-16">
      <Link href="/protocols" className="font-mono text-xs text-slate-500 hover:text-slate-300 transition-colors inline-flex items-center gap-2 mb-8">
        ← PROTOCOLS
      </Link>
      <div className="flex flex-col md:flex-row gap-6 items-start mb-10">
        <div className="flex-1">
          <div className="font-mono text-xs tracking-widest mb-3" style={{color:'#00d4ff'}}>// PROTOCOL REPORT</div>
          <h1 className="font-orbitron font-black text-white mb-2" style={{fontSize:'clamp(2rem,5vw,3rem)'}}>
            {proto.name}
          </h1>
          {proto.description&&<p className="font-mono text-sm text-slate-400 max-w-xl leading-relaxed">{proto.description}</p>}
          <div className="flex gap-3 mt-4 flex-wrap">
            {proto.website_url&&<a href={proto.website_url} target="_blank" rel="noreferrer" className="font-mono text-xs text-slate-400 hover:text-white transition-colors">Website →</a>}
            {proto.github_url&&<a href={proto.github_url} target="_blank" rel="noreferrer" className="font-mono text-xs text-slate-400 hover:text-white transition-colors">GitHub →</a>}
          </div>
        </div>
        {ls&&(
          <div className="glass rounded-xl p-6 text-center min-w-[180px]" style={{borderColor:`${ls.grade==='A'?'#22c55e':ls.grade==='B'?'#84cc16':ls.grade==='C'?'#f59e0b':'#ef4444'}33`}}>
            <div className="font-mono text-xs text-slate-500 mb-2 tracking-widest">ECOSYSTEM SCORE</div>
            <GradeBadge grade={ls.grade} size="lg"/>
            <div className="font-orbitron text-4xl font-black text-white mt-2">{Math.round(ls.composite_score)}</div>
            <div className="font-mono text-xs text-slate-500 mt-2">{ls.grade_label}</div>
          </div>
        )}
      </div>
      <div className="mb-6">
        <div className="font-mono text-xs tracking-widest text-slate-500 mb-4">// CONTRACTS ({proto.contracts?.length||0})</div>
        <div className="glass rounded-xl overflow-hidden">
          <div className="grid font-mono text-xs text-slate-500 tracking-widest px-6 py-3" style={{gridTemplateColumns:'3fr 1fr 1fr 1fr',borderBottom:'1px solid rgba(255,255,255,0.07)'}}>
            <span>ADDRESS</span><span>CHAIN</span><span>ROLE</span><span>SCORE</span>
          </div>
          {(proto.contracts||[]).map((c:any)=>(
            <Link key={c.address} href={`/score/${CHAIN_SLUG[c.chain_id]||'ethereum'}/${c.address}`}
              className="grid items-center px-6 py-3 hover:bg-white/[0.03] transition-colors border-b"
              style={{gridTemplateColumns:'3fr 1fr 1fr 1fr',borderColor:'rgba(255,255,255,0.05)'}}>
              <div>
                <div className="font-mono text-xs text-slate-300" style={{letterSpacing:'.02em'}}>{c.address.slice(0,18)}...{c.address.slice(-6)}</div>
                {c.label&&<div className="font-mono text-xs text-slate-500 mt-0.5">{c.label}</div>}
              </div>
              <div className="font-mono text-xs text-slate-400">{CHAIN[c.chain_id]||c.chain_id}</div>
              <div className="font-mono text-xs text-slate-400">{c.role}</div>
              <div>{contractScores[c.address]
                ? <GradeBadge grade={contractScores[c.address].grade} />
                : <span className="font-mono text-xs" style={{color:'#00d4ff'}}>→ scan</span>
              }</div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
