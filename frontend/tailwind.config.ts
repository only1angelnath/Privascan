import type { Config } from 'tailwindcss'
const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        orbitron: ['Orbitron', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
      colors: {
        grade: {
          a: '#22c55e', b: '#84cc16', c: '#f59e0b',
          d: '#f97316', f: '#ef4444',
          sanctioned: '#7c3aed', exploit: '#b91c1c',
        },
      },
    },
  },
  plugins: [],
}
export default config
