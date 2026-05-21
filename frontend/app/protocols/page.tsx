import Link from 'next/link'
import GradeBadge from '@/components/GradeBadge'
import { getProtocols, getProtocol } from '@/lib/api'
export const dynamic='force-dynamic'
export default async function ProtocolsPage(){
  let protocols:any[]=[]
  try{
    const d=await getProtocols()
    const base=d.protocols||[]
    protocols=await Promise.all(base.map(async(p:any)=>{
      try{ const full=await getProtocol(p.slug); return{...p,latest_score:full.latest_score} }
      catch{ return p }
    }))
  }catch{}
  return(
    <div className="max-w-7xl mx-auto px-6 pt-28 pb-16">
      <div className="mb-12">
        <div className="font-mono text-xs tracking-widest mb-4" style={{color:'#00d4ff'}}>// CURATED REGISTRY</div>
        <h1 className="font-orbitron font-black text-white mb-3" style={{fontSize:'clamp(2rem,5vw,3.5rem)'}}>
          Protocol Directory
        </h1>
        <p className="font-mono text-slate-500 text-sm max-w-xl leading-relaxed">
          14 EVM privacy protocols scored across all deployed contracts. Rescored every 6 hours via Celery beat.
        </p>
      </div>
      <div className="glass rounded-xl overflow-hidden">
        <div className="grid font-mono text-xs text-slate-500 tracking-widest px-6 py-3" style={{gridTemplateColumns:'2fr 1fr 1fr 1fr 1fr',borderBottom:'1px solid rgba(255,255,255,0.07)'}}>
          <span>PROTOCOL</span><span>GRADE</span><span>SCORE</span><span>CHAIN</span><span>CONTRACTS</span>
        </div>
        {protocols.length===0?(
          <div className="px-6 py-12 text-center font-mono text-xs text-slate-600">Loading protocol data from API...</div>
        ):(
          protocols.map((p:any)=>(
            <Link key={p.slug} href={`/protocol/${p.slug}`}
              className="grid items-center px-6 py-4 hover:bg-white/[0.03] transition-colors border-b"
              style={{gridTemplateColumns:'2fr 1fr 1fr 1fr 1fr',borderColor:'rgba(255,255,255,0.05)'}}>
              <div>
                <div className="font-orbitron text-sm font-bold text-white">{p.name}</div>
                {p.description&&<div className="font-mono text-xs text-slate-500 mt-0.5 line-clamp-1">{p.description}</div>}
              </div>
              <div>{p.latest_score?<GradeBadge grade={p.latest_score.grade||'?'}/>:<span className="font-mono text-xs text-slate-600">Pending</span>}</div>
              <div className="font-orbitron text-sm font-bold" style={{color:p.latest_score?undefined:'#4a7090'}}>{p.latest_score?Math.round(p.latest_score.composite_score):'-'}</div>
              <div className="font-mono text-xs text-slate-400">Multi-chain</div>
              <div className="font-mono text-xs text-slate-400">{p.contract_count||'—'}</div>
            </Link>
          ))
        )}
      </div>
    </div>
  )
}
