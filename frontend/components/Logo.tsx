interface Props { size?:'sm'|'md'|'lg' }
export default function Logo({ size='md' }: Props) {
  const s = size==='sm'?28:size==='lg'?54:36
  const fs = size==='sm'?'text-base':size==='lg'?'text-3xl':'text-xl'
  return (
    <div className="flex items-center gap-2.5">
      <svg width={s} height={s} viewBox="0 0 80 80" fill="none">
        <polygon points="40,3 71,21 71,59 40,77 9,59 9,21" stroke="#00d4ff" strokeWidth="1.5"/>
        <circle cx="40" cy="40" r="24" stroke="#00d4ff" strokeWidth=".7" style={{animation:'logo-pulse 2s ease-in-out infinite'}}/>
        <circle cx="40" cy="40" r="16" stroke="#00d4ff" strokeWidth=".7" style={{animation:'logo-pulse 2s ease-in-out infinite',animationDelay:'.55s'}}/>
        <circle cx="40" cy="40" r="8"  stroke="#00d4ff" strokeWidth=".7" style={{animation:'logo-pulse 2s ease-in-out infinite',animationDelay:'1.1s'}}/>
        <line x1="40" y1="16" x2="40" y2="64" stroke="#00d4ff" strokeWidth=".4" opacity=".3"/>
        <line x1="16" y1="40" x2="64" y2="40" stroke="#00d4ff" strokeWidth=".4" opacity=".3"/>
        <g style={{transformOrigin:'40px 40px',animation:'sweep 3s linear infinite'}}>
          <line x1="40" y1="40" x2="64" y2="40" stroke="#00d4ff" strokeWidth="1.5" opacity=".9"/>
          <path d="M40 40 L64 40 A24 24 0 0 0 40 16 Z" fill="#00d4ff" fillOpacity=".07"/>
        </g>
        <line x1="71" y1="21" x2="65" y2="24" stroke="#f59e0b" strokeWidth="1.5"/>
        <line x1="71" y1="59" x2="65" y2="56" stroke="#f59e0b" strokeWidth="1.5"/>
        <line x1="9"  y1="21" x2="15" y2="24" stroke="#f59e0b" strokeWidth="1.5"/>
        <line x1="9"  y1="59" x2="15" y2="56" stroke="#f59e0b" strokeWidth="1.5"/>
        <circle cx="40" cy="40" r="4.5" fill="#f59e0b" fillOpacity=".2"/>
        <circle cx="40" cy="40" r="2"   fill="#f59e0b"/>
      </svg>
      <div>
        <div className={`font-orbitron font-bold ${fs} tracking-widest leading-none`}>
          <span style={{color:'#00d4ff'}}>PRIVA</span><span style={{color:'#f59e0b'}}>SCAN</span>
        </div>
        {size!=='sm' && <div className="font-mono text-slate-600 mt-0.5" style={{fontSize:'8px',letterSpacing:'.22em'}}>RISK INTELLIGENCE</div>}
      </div>
    </div>
  )
}
