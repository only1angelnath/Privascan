'use client'
import {RadarChart,Radar,PolarGrid,PolarAngleAxis,ResponsiveContainer} from 'recharts'
const GC:Record<string,string>={A:'#22c55e',B:'#84cc16',C:'#f59e0b',D:'#f97316',F:'#ef4444'}
interface Props{subScores:{code:number;ownership:number;liquidity:number;audit:number;compliance:number;governance:number};grade:string}
export default function ScoreRadar({subScores,grade}:Props){
  const c=GC[grade]||'#64748b'
  const data=[
    {dim:'Code',v:subScores.code},{dim:'Ownership',v:subScores.ownership},
    {dim:'Liquidity',v:subScores.liquidity},{dim:'Audit',v:subScores.audit},
    {dim:'Compliance',v:subScores.compliance},{dim:'Governance',v:subScores.governance},
  ]
  return(
    <ResponsiveContainer width="100%" height={240}>
      <RadarChart data={data}>
        <PolarGrid stroke="rgba(255,255,255,0.08)"/>
        <PolarAngleAxis dataKey="dim" tick={{fill:'#4a7090',fontSize:11,fontFamily:'var(--font-mono)'}}/>
        <Radar dataKey="v" stroke={c} fill={c} fillOpacity={0.12} strokeWidth={2}/>
      </RadarChart>
    </ResponsiveContainer>
  )
}
