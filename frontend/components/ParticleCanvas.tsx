'use client'
import { useEffect, useRef } from 'react'
interface Props { className?:string; n?:number }
export default function ParticleCanvas({ className='', n=58 }: Props) {
  const ref = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    const cv = ref.current; if (!cv) return
    const cx = cv.getContext('2d')!; let aid: number
    const resize = () => { cv.width=cv.offsetWidth; cv.height=cv.offsetHeight }
    resize(); window.addEventListener('resize', resize)
    const pts = Array.from({length:n}, ()=>({
      x:Math.random()*(cv.width||800), y:Math.random()*(cv.height||600),
      vx:(Math.random()-.5)*.28, vy:(Math.random()-.5)*.28,
      r:Math.random()*1.4+.6, g:Math.random()<.18,
    }))
    const draw = () => {
      cx.clearRect(0,0,cv.width,cv.height)
      for (let i=0;i<pts.length;i++) for (let j=i+1;j<pts.length;j++) {
        const dx=pts[i].x-pts[j].x, dy=pts[i].y-pts[j].y, d=Math.sqrt(dx*dx+dy*dy)
        if (d<115) {
          const a=(1-d/115)*.5
          cx.beginPath(); cx.moveTo(pts[i].x,pts[i].y); cx.lineTo(pts[j].x,pts[j].y)
          cx.strokeStyle=(pts[i].g||pts[j].g)?`rgba(245,158,11,${a*.55})`:`rgba(0,212,255,${a*.5})`
          cx.lineWidth=.6; cx.stroke()
        }
      }
      pts.forEach(p=>{
        cx.beginPath(); cx.arc(p.x,p.y,p.r,0,Math.PI*2)
        cx.fillStyle=p.g?'#f59e0b':'#00d4ff'; cx.fill()
        p.x+=p.vx; p.y+=p.vy
        if(p.x<0||p.x>cv.width) p.vx*=-1
        if(p.y<0||p.y>cv.height) p.vy*=-1
      })
      aid = requestAnimationFrame(draw)
    }
    draw()
    return () => { window.removeEventListener('resize',resize); cancelAnimationFrame(aid) }
  }, [n])
  return <canvas ref={ref} className={`absolute inset-0 w-full h-full ${className}`} style={{opacity:.55}} />
}
