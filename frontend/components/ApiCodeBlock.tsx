'use client'
import {useState} from 'react'
const TABS=['curl','JavaScript','Python'] as const
type T=typeof TABS[number]
const CODE:Record<T,string>={
  curl:`curl -X GET \\
  "http://localhost:8000/api/v1/score/ethereum/0xYOUR_CONTRACT" \\
  -H "X-API-Key: ps_your_api_key_here"`,
  JavaScript:`const response = await fetch(
  'http://localhost:8000/api/v1/score/ethereum/0xYOUR_CONTRACT',
  { headers: { 'X-API-Key': 'ps_your_api_key_here' } }
)
const data = await response.json()
// data.composite_score → 74.2
// data.grade           → "B"
// data.sub_scores      → { code: 82, ownership: 91, ... }`,
  Python:`import requests

resp = requests.get(
    'http://localhost:8000/api/v1/score/ethereum/0xYOUR_CONTRACT',
    headers={'X-API-Key': 'ps_your_api_key_here'}
)
data = resp.json()
print(data['composite_score'])  # 74.2
print(data['grade'])            # B
print(data['grade_label'])      # Moderate-Low Risk`
}
export default function ApiCodeBlock(){
  const [tab,setTab]=useState<T>('curl')
  return(
    <div className="glass rounded-xl overflow-hidden">
      <div className="flex border-b" style={{borderColor:'rgba(255,255,255,0.07)'}}>
        {TABS.map(t=>(
          <button key={t} onClick={()=>setTab(t)}
            className={`font-mono text-xs px-6 py-3 transition-colors ${tab===t?'tab-active':'tab-idle'}`}>
            {t}
          </button>
        ))}
      </div>
      <div className="p-6 overflow-x-auto">
        <pre className="font-mono text-sm text-slate-300 leading-relaxed whitespace-pre">{CODE[tab]}</pre>
      </div>
    </div>
  )
}
