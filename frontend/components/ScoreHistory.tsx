'use client'
import {AreaChart,Area,XAxis,YAxis,Tooltip,ResponsiveContainer} from 'recharts'
const GC:Record<string,string>={A:'#22c55e',B:'#84cc16',C:'#f59e0b',D:'#f97316',F:'#ef4444'}
interface HP{composite_score:number;grade:string;scored_at:string}
interface Props{history:HP[];grade:string}
export default function ScoreHistory({history,grade}:Props){
  const c=GC[grade]||'#64748b'
  const data=[...history].reverse().map(h=>({
    date:new Date(h.scored_at).toLocaleDateString('en-US',{month:'short',day:'numeric'}),
    score:Number(h.composite_score.toFixed(1)),
  }))
  if(!data.length) return <p className="font-mono text-xs text-slate-500 text-center py-8">No history yet.</p>
  return(
    <ResponsiveContainer width="100%" height={160}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={c} stopOpacity={.22}/>
            <stop offset="95%" stopColor={c} stopOpacity={0}/>
          </linearGradient>
        </defs>
        <XAxis dataKey="date" tick={{fill:'#4a7090',fontSize:10,fontFamily:'var(--font-mono)'}} axisLine={false} tickLine={false}/>
        <YAxis domain={[0,100]} tick={{fill:'#4a7090',fontSize:10,fontFamily:'var(--font-mono)'}} axisLine={false} tickLine={false} width={28}/>
        <Tooltip contentStyle={{background:'#0d1a2e',border:'1px solid rgba(0,212,255,0.15)',borderRadius:8,fontFamily:'var(--font-mono)',fontSize:12}}
          labelStyle={{color:'#4a7090'}}/>
        <Area type="monotone" dataKey="score" stroke={c} strokeWidth={2} fill="url(#sg)" dot={{fill:c,r:3}}/>
      </AreaChart>
    </ResponsiveContainer>
  )
}
