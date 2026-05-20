'use client'
import {useEffect,useState} from 'react'
const GC:Record<string,string>={A:'#22c55e',B:'#84cc16',C:'#f59e0b',D:'#f97316',F:'#ef4444',sanctioned:'#7c3aed',exploit:'#b91c1c'}
interface Props{score:number;grade:string;overrideStatus?:string|null;size?:number}
export default function ScoreRing({score,grade,overrideStatus,size=160}:Props){
  const [anim,setAnim]=useState(false)
  useEffect(()=>{const t=setTimeout(()=>setAnim(true),120);return()=>clearTimeout(t)},[])
  const R=60,C=2*Math.PI*R,filled=anim?(score/100)*C:0
  const color=overrideStatus==='ofac_active'?GC.sanctioned:overrideStatus==='exploit_active'?GC.exploit:GC[grade]||'#64748b'
  const cx=size/2,cy=size/2
  return(
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={cx} cy={cy} r={R} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={10}/>
      <circle cx={cx} cy={cy} r={R} fill="none" stroke={color} strokeWidth={10} strokeLinecap="round"
        strokeDasharray={`${filled} ${C-filled}`} strokeDashoffset={C/4}
        style={{transition:'stroke-dasharray 0.9s ease-out'}}/>
      <text x={cx} y={cy-8}  textAnchor="middle" fill="white"  fontSize="28" fontWeight="700" fontFamily="var(--font-orbitron)">{Math.round(score)}</text>
      <text x={cx} y={cy+18} textAnchor="middle" fill={color} fontSize="16" fontWeight="900" fontFamily="var(--font-orbitron)">{grade}</text>
    </svg>
  )
}
