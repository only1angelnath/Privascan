const GC:Record<string,string>={A:'#22c55e',B:'#84cc16',C:'#f59e0b',D:'#f97316',F:'#ef4444',sanctioned:'#7c3aed',exploit:'#b91c1c'}
const GL:Record<string,string>={A:'Low Risk',B:'Moderate-Low',C:'Moderate Risk',D:'High Risk',F:'Critical Risk'}
interface Props{grade:string;showLabel?:boolean;size?:'sm'|'md'|'lg'}
export default function GradeBadge({grade,showLabel=false,size='md'}:Props){
  const c=GC[grade]||'#64748b'
  const sz=size==='sm'?'text-xs px-1.5 py-0.5':size==='lg'?'text-lg px-3 py-1':'text-sm px-2 py-0.5'
  return(
    <span className="inline-flex items-center gap-2">
      <span className={`font-orbitron font-black rounded ${sz}`} style={{color:c,background:`${c}22`,border:`1px solid ${c}44`}}>{grade}</span>
      {showLabel&&<span className="font-mono text-xs text-slate-400">{GL[grade]}</span>}
    </span>
  )
}
