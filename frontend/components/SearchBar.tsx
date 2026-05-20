'use client'
import {useState,FormEvent} from 'react'
import {useRouter} from 'next/navigation'
const CHAINS=[{s:'ethereum',l:'Ethereum'},{s:'arbitrum',l:'Arbitrum'},{s:'optimism',l:'Optimism'},{s:'base',l:'Base'},{s:'polygon',l:'Polygon'},{s:'bsc',l:'BNB Chain'},{s:'avalanche',l:'Avalanche'}]
export default function SearchBar({large=false}:{large?:boolean}){
  const router=useRouter()
  const [chain,setChain]=useState('ethereum')
  const [addr,setAddr]=useState('')
  const [err,setErr]=useState('')
  function submit(e:FormEvent){
    e.preventDefault()
    const a=addr.trim().toLowerCase()
    if(!/^0x[0-9a-f]{40}$/.test(a)){setErr('Enter a valid EVM address (0x + 40 hex chars)');return}
    setErr(''); router.push(`/score/${chain}/${a}`)
  }
  const py=large?'py-4 text-base':'py-3 text-sm'
  return(
    <form onSubmit={submit} className="w-full max-w-2xl">
      <div className="flex gap-2">
        <select value={chain} onChange={e=>setChain(e.target.value)}
          className={`glass font-mono ${py} px-3 text-sm text-slate-300 focus:outline-none focus:border-cyan-400/40 shrink-0 rounded-lg`}>
          {CHAINS.map(c=><option key={c.s} value={c.s} style={{background:'#0a0f1e'}}>{c.l}</option>)}
        </select>
        <input type="text" value={addr} onChange={e=>setAddr(e.target.value)} placeholder="0x contract address..."
          className={`flex-1 glass font-mono ${py} px-4 focus:outline-none focus:border-cyan-400/40 placeholder:text-slate-700 rounded-lg`}/>
        <button type="submit" className={`font-orbitron text-xs font-bold ${py} px-6 rounded-lg hover:opacity-85 transition-opacity shrink-0`}
          style={{background:'#00d4ff',color:'#0a0f1e'}}>SCAN</button>
      </div>
      {err&&<p className="font-mono text-xs text-red-400 mt-2">{err}</p>}
    </form>
  )
}
