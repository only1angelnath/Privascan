'use client'
import {useState} from 'react'
const IC:Record<string,string>={High:'#ef4444',Medium:'#f59e0b',Low:'#64748b',Informational:'#334155',Optimization:'#334155'}
interface F{check:string;impact:string;confidence:string;description:string;is_custom:boolean}
export default function FindingsAccordion({findings}:{findings:F[]}){
  const [open,setOpen]=useState<number|null>(null)
  if(!findings.length) return <p className="font-mono text-xs text-slate-500 py-4">No Slither findings detected.</p>
  return(
    <div className="divide-y" style={{borderColor:'rgba(255,255,255,0.06)'}}>
      {findings.map((f,i)=>{
        const c=IC[f.impact]||'#64748b'
        return(
          <div key={i}>
            <button className="w-full flex items-center gap-3 py-3 text-left hover:text-white transition-colors"
              onClick={()=>setOpen(open===i?null:i)}>
              <span className="font-mono text-xs font-bold px-2 py-0.5 rounded shrink-0" style={{color:c,background:`${c}22`}}>{f.impact.toUpperCase()}</span>
              <span className="font-mono text-xs text-slate-300">{f.check}</span>
              {f.is_custom&&<span className="font-mono text-xs px-1.5 py-0.5 rounded" style={{color:'#0ea5e9',background:'#0ea5e910'}}>custom</span>}
              <span className="ml-auto font-mono text-xs text-slate-600">{open===i?'▲':'▼'}</span>
            </button>
            {open===i&&<p className="pb-3 pl-2 font-mono text-xs text-slate-400 leading-relaxed">{f.description}</p>}
          </div>
        )
      })}
    </div>
  )
}
