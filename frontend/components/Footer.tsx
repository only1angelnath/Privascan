import Link from 'next/link'
import Logo from './Logo'

const COLS = {
  Product: [
    { l: 'Score a Contract', h: '/' },
    { l: 'Protocol Directory', h: '/protocols' },
    { l: 'Request Protocol',  h: '/request'    },
    { l: 'Get API Key',       h: '/keys'        },
  ],
  Developers: [
    { l: 'Whitepaper',       h: '/whitepaper'   },
    { l: 'API Reference',    h: '/api'          },
    { l: 'Rate Limits',     h: '/docs#rate'    },
    { l: 'Authentication',  h: '/docs#auth'    },
  ],
  Community: [
    { l: 'Brand Kit',      h: '/brand'                        },
    { l: 'Twitter / X',      h: 'https://x.com/privascan'       },
    { l: 'Telegram Channel', h: 'https://t.me/privascan'        },
    { l: 'Telegram Bot',     h: 'https://t.me/PrivaScanBot'     },
    { l: 'GitHub',           h: 'https://github.com/only1angelnath/Privascan'            },
    { l: 'Support & FAQ',    h: '/support'                      },
  ],
  Legal: [
    { l: 'Terms of Service', h: '/legal'   },
    { l: 'Privacy Policy',   h: '/privacy' },
    { l: 'Disclaimer',       h: '/legal#disclaimer' },
    { l: 'Contact',          h: '/support#contact'  },
  ],
}

export default function Footer() {
  return (
    <footer className="relative z-10 mt-24" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-10">
          <div className="col-span-2 md:col-span-1">
            <Logo size="sm" />
            <p className="font-mono text-xs text-slate-500 leading-relaxed mt-4 max-w-[200px]">
              Open-source deterministic risk scoring for EVM privacy protocols. Free API. No tracking.
            </p>
            <div className="flex gap-2 mt-5">
              {[{l:'X',h:'https://x.com/privascan'},{l:'TG',h:'https://t.me/privascan'},{l:'GH',h:'https://github.com/only1angelnath/Privascan'}].map(s=>(
                <a key={s.l} href={s.h} target="_blank" rel="noreferrer"
                  className="glass glass-hover w-8 h-8 rounded flex items-center justify-center font-mono text-xs text-slate-400 cursor-pointer hover:text-white transition-colors">
                  {s.l}
                </a>
              ))}
            </div>
          </div>
          {Object.entries(COLS).map(([cat, links]) => (
            <div key={cat}>
              <div className="font-mono text-xs tracking-widest mb-4" style={{ color: '#00d4ff' }}>{cat.toUpperCase()}</div>
              <ul className="space-y-2.5">
                {links.map(l => (
                  <li key={l.l}>
                    <Link href={l.h}
                      className="font-mono text-xs text-slate-500 hover:text-slate-200 transition-colors cursor-pointer">
                      {l.l}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="flex flex-col md:flex-row justify-between items-center gap-4 mt-12 pt-8"
          style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          <div className="font-mono text-xs text-slate-600">
            © 2026 PrivaScan. MIT License. Not financial advice.
          </div>
          <div className="flex gap-6 font-mono text-xs text-slate-600">
            <Link href="/legal" className="hover:text-slate-400 transition-colors cursor-pointer">Terms</Link>
            <Link href="/privacy" className="hover:text-slate-400 transition-colors cursor-pointer">Privacy</Link>
            <Link href="/support" className="hover:text-slate-400 transition-colors cursor-pointer">Support</Link>
            <span>v1.0.0</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
