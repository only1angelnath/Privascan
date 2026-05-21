const B = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api/v1'
export interface SubScores { code:number; ownership:number; liquidity:number; audit:number; compliance:number; governance:number }
export interface Finding { check:string; impact:string; confidence:string; description:string; is_custom:boolean }
export interface ScoreResult {
  address:string; chain:string; chain_id:number; scan_type:string
  composite_score:number; grade:string; grade_label:string
  override_applied:boolean; override_status:string|null
  sub_scores:SubScores
  details:{ code:{score:number;is_verified:boolean;high_count:number;medium_count:number;low_count:number;findings:Finding[];error:string|null}; ownership:{score:number;flags:string[];details:Record<string,unknown>}; liquidity:{score:number;tvl_usd:number|null;tvl_tier:string;tvl_source:string;tvl_confidence:string}; audit:{score:number;note?:string}; compliance:{score:number} }
  scored_at:string; cached:boolean
}
export interface HistoryPoint { composite_score:number; grade:string; scored_at:string }
export interface Protocol { slug:string; name:string; description:string|null; website_url:string|null; github_url:string|null; defillama_slug:string|null }
export interface ProtocolContract { address:string; chain_id:number; role:string; label:string|null; is_primary:boolean }
export async function getScore(chain:string, address:string): Promise<ScoreResult> {
  const r = await fetch(`${B}/score/${chain}/${address}`, { cache:'no-store' })
  if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error((e as Record<string,string>).detail || `${r.status}`) }
  return r.json()
}
export async function getScoreHistory(chain:string, address:string): Promise<{history:HistoryPoint[]}> {
  const r = await fetch(`${B}/score/${chain}/${address}/history?limit=30`, { cache:'no-store' })
  if (!r.ok) return { history:[] }
  return r.json()
}
export async function getProtocols(): Promise<{count:number; protocols:Protocol[]}> {
  const r = await fetch(`${B}/protocols/`, { next:{revalidate:300} })
  if (!r.ok) throw new Error('Failed to fetch protocols')
  return r.json()
}
export async function getProtocol(slug:string): Promise<Protocol&{contracts:ProtocolContract[];latest_score:Record<string,unknown>|null}> {
  const r = await fetch(`${B}/protocols/${slug}`, { next:{revalidate:300} })
  if (!r.ok) throw new Error(`Protocol not found: ${slug}`)
  return r.json()
}
