'use client'
import {useEffect,useState} from 'react'
import {useParams} from 'next/navigation'
import Link from 'next/link'
import dynamic from 'next/dynamic'
import {getScore,getScoreHistory,type ScoreResult,type HistoryPoint} from '@/lib/api'
import ScoreRing from '@/components/ScoreRing'
import SubScoreBar from '@/components/SubScoreBar'
import GradeBadge from '@/components/GradeBadge'
const ScoreRadar = dynamic(()=>import('@/components/ScoreRadar'),{ssr:false})
const ScoreHistory = dynamic(()=>import('@/components/ScoreHistory'),{ssr:false})
const FindingsAccordion = dynamic(()=>import('@/components/FindingsAccordion'),{ssr:false})
const STAGES=['Fetching bytecode...','Running Slither analysis...','Checking ownership patterns...','Querying TVL data...','Verifying OFAC status...','Computing composite score...']
const BARS=[{label:'Code Risk',key:'code',w:'30%'},{label:'Ownership',key:'ownership',w:'25%'},{label:'Liquidity',key:'liquidity',w:'20%'},{label:'Audit',key:'audit',w:'12%'},{label:'Compliance',key:'compliance',w:'8%'},{label:'Governance',key:'governance',w:'5%'}]
const FLAG_LABELS: Record<string, {label: string; impact: string; color: string}> = {
  no_multisig:             { label: 'No multisig wallet',             impact: '-30 pts', color: '#ef4444' },
  no_timelock:             { label: 'No timelock on upgrades',        impact: '-20 pts', color: '#ef4444' },
  upgradeable_no_timelock: { label: 'Upgradeable without timelock',   impact: '-25 pts', color: '#ef4444' },
  single_admin_key:        { label: 'Single EOA admin key',           impact: '-15 pts', color: '#f59e0b' },
  proxy_risk:              { label: 'Proxy implementation risk',      impact: '-10 pts', color: '#f59e0b' },
  unverified:              { label: 'Source code unverified',         impact: 'Base 70',  color: '#ef4444' },
  high_tvl:                { label: 'High TVL (low risk)',            impact: '+',       color: '#22c55e' },
  ofac_active:             { label: 'OFAC sanctioned address',        impact: 'Cap 10',  color: '#7c3aed' },
  exploit_active:          { label: 'Active unresolved exploit',      impact: 'Cap 30',  color: '#b91c1c' },
}

const TVL_TIER_DESC: Record<string, string> = {
  Whale:  '>$100M — institutional-grade liquidity',
  Large:  '>$10M  — well-established protocol',
  Medium: '>$1M   — growing adoption',
  Small:  '>$100K — early stage',
  Micro:  '<$100K — minimal liquidity, high risk',
  Unknown:'TVL data unavailable',
}

export default function ScorePage(){
  const p=useParams() as {chain:string;address:string}
  const [data,setData]=useState<ScoreResult|null>(null)
  const [hist,setHist]=useState<HistoryPoint[]>([])
  const [loading,setLoading]=useState(true)
  const [stage,setStage]=useState(0)
  const [err,setErr]=useState('')
  useEffect(()=>{
    let si=0
    const sid=setInterval(()=>{ if(si<STAGES.length-1) setStage(++si) },8000)
    Promise.all([getScore(p.chain,p.address),getScoreHistory(p.chain,p.address)])
      .then(([sc,hs])=>{ setData(sc); setHist(hs.history||[]) })
      .catch(e=>setErr(e.message||'Failed to score contract'))
      .finally(()=>{ clearInterval(sid); setLoading(false) })
    return()=>clearInterval(sid)
  },[p.chain,p.address])
  if(loading) return(
    <div className="min-h-screen flex flex-col items-center justify-center px-6 pt-20">
      <div className="glass rounded-2xl p-12 text-center max-w-lg w-full" style={{borderColor:'rgba(0,212,255,0.2)'}}>
        <div className="font-orbitron text-lg font-bold text-white mb-2">SCANNING CONTRACT</div>
        <div className="font-mono text-xs text-slate-400 mb-8 tracking-widest">{p.address.slice(0,18)}...{p.address.slice(-6)}</div>
        <div className="w-full h-0.5 rounded-full mb-6" style={{background:'rgba(255,255,255,0.07)'}}>
          <div className="h-full rounded-full" style={{background:'#00d4ff',width:`${((stage+1)/STAGES.length)*100}%`,transition:'width 2s ease'}}/>
        </div>
        <div className="font-mono text-xs tracking-widest" style={{color:'#00d4ff'}}>
          {STAGES[stage]}
        </div>
        <p className="font-mono text-xs text-slate-600 mt-6">Slither analysis may take 30–60 seconds for unverified contracts.</p>
      </div>
    </div>
  )
  if(err) return(
    <div className="min-h-screen flex flex-col items-center justify-center px-6 pt-20">
      <div className="glass rounded-2xl p-12 text-center max-w-lg" style={{borderColor:'rgba(239,68,68,0.2)'}}>
        <div className="font-orbitron text-lg font-bold mb-3" style={{color:'#ef4444'}}>SCAN FAILED</div>
        <p className="font-mono text-xs text-slate-400 mb-6">{err}</p>
        <Link href="/" className="font-mono text-xs" style={{color:'#00d4ff'}}>← Return home</Link>
      </div>
    </div>
  )
  if(!data) return null
  const ss=data.sub_scores
  const overrideColor=data.override_status==='ofac_active'?'#7c3aed':data.override_status==='exploit_active'?'#ef4444':null
  return(
    <div className="max-w-7xl mx-auto px-6 pt-28 pb-16">
      <Link href="/" className="font-mono text-xs text-slate-500 hover:text-slate-300 transition-colors inline-flex items-center gap-2 mb-8">← HOME</Link>
      {data.override_status&&(
        <div className="glass rounded-lg px-5 py-3 mb-6 flex items-center gap-3" style={{borderColor:`${overrideColor}44`,background:`${overrideColor}11`}}>
          <span className="font-orbitron text-xs font-bold" style={{color:overrideColor||'#ef4444'}}>{data.override_status==='ofac_active'?'⛔ OFAC SANCTIONED':'⚠ ACTIVE EXPLOIT'}</span>
          <span className="font-mono text-xs text-slate-400">Score override applied. Grade is non-negotiable until resolved.</span>
        </div>
      )}
      <div className="grid md:grid-cols-3 gap-6 mb-6">
        <div className="glass rounded-xl p-6 flex flex-col items-center justify-center">
          <ScoreRing score={data.composite_score} grade={data.grade} overrideStatus={data.override_status}/>
          <div className="font-mono text-xs text-slate-500 mt-2 text-center">{data.grade_label}</div>
          {data.cached&&<div className="font-mono text-xs text-slate-600 mt-1">cached</div>}
        </div>
        <div className="glass rounded-xl p-6">
          <div className="font-mono text-xs text-slate-500 tracking-widest mb-4">SUB-SCORES</div>
          {BARS.map(b=><SubScoreBar key={b.key} label={b.label} score={(ss as any)[b.key]||0} weight={b.w}/>)}
        </div>
        <div className="glass rounded-xl p-6">
          <div className="font-mono text-xs text-slate-500 tracking-widest mb-2">RADAR</div>
          <ScoreRadar subScores={ss} grade={data.grade}/>
          <div className="mt-4 space-y-1">
            <div className="flex justify-between font-mono text-xs text-slate-500">
              <span>Chain</span><span className="text-slate-300">{data.chain} #{data.chain_id}</span>
            </div>
            <div className="flex justify-between font-mono text-xs text-slate-500">
              <span>Verified</span><span style={{color:data.details.code.is_verified?'#22c55e':'#ef4444'}}>{data.details.code.is_verified?'YES':'NO'}</span>
            </div>
            <div className="flex justify-between font-mono text-xs text-slate-500">
              <span>TVL</span><span className="text-slate-300">{data.details.liquidity.tvl_usd!=null?`$${(data.details.liquidity.tvl_usd/1e6).toFixed(1)}M`:'—'}</span>
            </div>
            <div className="flex justify-between font-mono text-xs text-slate-500">
              <span>High findings</span><span style={{color:data.details.code.high_count>0?'#ef4444':'#22c55e'}}>{data.details.code.high_count}</span>
            </div>
          </div>
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-6 mb-6">
        <div className="glass rounded-xl p-6">
          <div className="font-mono text-xs text-slate-500 tracking-widest mb-4">CODE FINDINGS ({data.details.code.findings?.length||0})</div>
          <FindingsAccordion findings={data.details.code.findings||[]}/>
        </div>
        <div className="glass rounded-xl p-6">
          <div className="font-mono text-xs text-slate-500 tracking-widest mb-4">SCORE HISTORY</div>
          <ScoreHistory history={hist} grade={data.grade}/>
        </div>
      </div>
      <div className="flex justify-center">
        <Link href={`/score/${data.chain}/${data.address}`} className="glass glass-hover font-mono text-xs text-slate-300 px-6 py-3 rounded-lg tracking-wider">
          ↻ Rescan This Contract
        </Link>
      </div>
    </div>
  )
}
