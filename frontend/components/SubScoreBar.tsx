const GC:Record<string,string>={A:'#22c55e',B:'#84cc16',C:'#f59e0b',D:'#f97316',F:'#ef4444'}
const g=(s:number)=>s<=20?'A':s<=40?'B':s<=60?'C':s<=80?'D':'F'
interface Props{label:string;score:number;weight:string}
export default function SubScoreBar({label,score,weight}:Props){
  const c=GC[g(score)]
  return(
    <div className="flex items-center gap-3 py-2">
      <span className="w-28 font-mono text-xs text-slate-300 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 rounded-full" style={{background:'rgba(255,255,255,0.07)'}}>
        <div className="h-full rounded-full" style={{width:`${score}%`,background:c,transition:'width 0.8s ease-out'}}/>
      </div>
      <span className="w-8 text-right font-orbitron text-xs font-bold shrink-0" style={{color:c}}>{Math.round(score)}</span>
      <span className="w-10 text-right font-mono text-xs text-slate-600 shrink-0">{weight}</span>
    </div>
  )
}
