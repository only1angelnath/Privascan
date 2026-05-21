'use client'
import { useRef, useCallback } from 'react'
const C = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%*<>?'
interface Props {
  text: string
  className?: string
  style?: React.CSSProperties
  as?: keyof JSX.IntrinsicElements
}
export default function CipherText({ text, className = '', style, as: Tag = 'span' }: Props) {
  const ref = useRef<HTMLElement>(null)
  const live = useRef(false)
  const play = useCallback(() => {
    if (live.current || !ref.current) return
    live.current = true
    const el = ref.current
    const F = 5; let f = 0
    const id = setInterval(() => {
      let out = ''
      for (let i = 0; i < text.length; i++) {
        if (text[i] === ' ') { out += '\u00a0'; continue }
        out += f > F * (i / text.length) + 1.5 ? text[i] : C[Math.floor(Math.random() * C.length)]
      }
      el.textContent = out
      if (f++ >= F + text.length) { clearInterval(id); el.textContent = text; live.current = false }
    }, 22)
  }, [text])
  return <Tag ref={ref as React.Ref<HTMLElement>} className={className} style={style} onMouseEnter={play}>{text}</Tag>
}
