import Link from 'next/link'

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <div id={id} className="glass rounded-xl p-8 scroll-mt-24">
      <h2 className="font-orbitron text-xl font-bold text-white mb-6 pb-4" style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        {title}
      </h2>
      <div className="font-mono text-sm text-slate-400 leading-relaxed space-y-4">{children}</div>
    </div>
  )
}

const TOC = [
  { id: 'abstract',    title: 'Abstract'                   },
  { id: 'problem',     title: 'The Problem'                },
  { id: 'solution',    title: 'Our Approach'               },
  { id: 'methodology', title: 'Scoring Methodology'        },
  { id: 'dimensions',  title: 'The Six Dimensions'         },
  { id: 'overrides',   title: 'Hard Overrides'             },
  { id: 'detectors',   title: 'Custom Privacy Detectors'   },
  { id: 'curated',     title: 'Curated Protocol Registry'  },
  { id: 'api',         title: 'The API'                    },
  { id: 'bot',         title: 'The Telegram Bot'           },
  { id: 'roadmap',     title: 'Roadmap'                    },
  { id: 'disclaimer',  title: 'Disclaimer'                 },
]

export default function WhitepaperPage() {
  return (
    <div className="max-w-7xl mx-auto px-6 pt-24 pb-16 flex gap-8">
      <aside className="w-52 shrink-0 hidden md:block">
        <div className="sticky top-24">
          <div className="font-mono text-xs tracking-widest mb-4" style={{ color: '#00d4ff' }}>// WHITEPAPER</div>
          <nav className="space-y-0.5">
            {TOC.map(s => (
              <a key={s.id} href={`#${s.id}`}
                className="block font-mono text-xs px-3 py-1.5 rounded transition-colors hover:text-white hover:bg-white/[0.05] cursor-pointer"
                style={{ color: '#4a7090' }}>
                {s.title}
              </a>
            ))}
          </nav>
          <div className="mt-6 pt-4 space-y-2" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
            <Link href="/api" className="font-mono text-xs text-slate-500 hover:text-slate-300 transition-colors cursor-pointer block">
              API Reference →
            </Link>
            <a href="https://github.com/only1angelnath/Privascan" target="_blank" rel="noreferrer"
              className="font-mono text-xs text-slate-500 hover:text-slate-300 transition-colors cursor-pointer block">
              GitHub ↗
            </a>
          </div>
        </div>
      </aside>

      <div className="flex-1 min-w-0 space-y-6">
        <div className="mb-4">
          <div className="font-mono text-xs tracking-widest mb-2" style={{ color: '#00d4ff' }}>v1.0 · May 2026</div>
          <h1 className="font-orbitron font-black text-white mb-2" style={{ fontSize: 'clamp(2rem,5vw,3.2rem)' }}>
            PrivaScan Whitepaper
          </h1>
          <p className="font-mono text-slate-400">Deterministic Risk Intelligence for EVM Privacy Protocols</p>
        </div>

        <Section id="abstract" title="Abstract">
          <p>
            Privacy protocols on EVM blockchains serve a legitimate and growing purpose: they give users
            the same financial confidentiality that traditional bank accounts provide by default.
            But the protocols themselves carry technical and regulatory risks that are harder to
            evaluate than standard DeFi contracts. Their whole design obscures information — including,
            sometimes, their own vulnerabilities.
          </p>
          <p>
            PrivaScan is an open-source risk scoring system that evaluates EVM privacy protocol
            contracts across six measurable dimensions — code quality, ownership structure,
            liquidity depth, audit coverage, regulatory compliance, and governance maturity —
            and computes a single deterministic composite score from 0 to 100.
          </p>
          <p>
            The score is not a recommendation. It is a structured, reproducible data point
            that gives users, researchers, and builders a consistent basis for their own
            risk assessment. Every number is derived from on-chain data, public audit records,
            and automated static analysis. No black boxes. No opinions.
          </p>
        </Section>

        <Section id="problem" title="The Problem">
          <p>
            When you use a privacy protocol to shield a transaction, you are trusting a set of
            smart contracts with more than your funds. You are trusting them with your privacy.
            If those contracts are exploited, you may lose both.
          </p>
          <p>
            The challenge is that evaluating privacy protocol risk requires skills and data
            across multiple disciplines simultaneously:
          </p>
          <ul className="space-y-2 ml-4">
            <li>• <strong className="text-white">Static analysis</strong> — reading the bytecode for vulnerabilities. Requires Slither, custom detectors, and understanding of ZK circuit patterns.</li>
            <li>• <strong className="text-white">Ownership analysis</strong> — determining who controls the protocol, whether timelocks exist, and whether upgrades can happen without warning.</li>
            <li>• <strong className="text-white">Liquidity context</strong> — understanding TVL as a proxy for protocol maturity and the financial exposure of users inside it.</li>
            <li>• <strong className="text-white">Audit provenance</strong> — knowing which firm audited it, when, whether findings were remediated, and how the auditor’s track record holds up.</li>
            <li>• <strong className="text-white">Regulatory screening</strong> — checking contracts against OFAC’s Specially Designated Nationals list and known exploit registries.</li>
          </ul>
          <p>
            No single tool covers all five. Most users do none of them. PrivaScan covers all of them
            and surfaces the result as a single actionable grade.
          </p>
        </Section>

        <Section id="solution" title="Our Approach">
          <p>
            PrivaScan treats a privacy protocol not as a single contract but as an <strong className="text-white">ecosystem</strong> —
            every deployed contract (router, verifier, pool, vault, proxy) is scored individually,
            then aggregated into a single ecosystem-level grade.
          </p>
          <p>
            This matters because risk in privacy protocols is often distributed. A clean core contract
            with a vulnerable peripheral contract is not a safe protocol. Our ecosystem model captures this.
          </p>
          <p>
            The system has two tracks:
          </p>
          <ul className="space-y-2 ml-4">
            <li>• <strong className="text-white">Curated track</strong> — 14 manually vetted protocols, automatically rescored every 6 hours via Celery beat. All contracts verified, all metadata confirmed.</li>
            <li>• <strong className="text-white">Community track</strong> — any EVM address on any supported chain. First scan runs full Slither analysis (30–60s), then cached for 1 hour.</li>
          </ul>
        </Section>

        <Section id="methodology" title="Scoring Methodology">
          <p>The composite score is a weighted sum of six sub-scores:</p>
          <div className="glass rounded-xl p-5 my-3 font-mono text-sm" style={{ borderColor: 'rgba(0,212,255,0.2)' }}>
            <div className="text-slate-300">composite =</div>
            <div className="pl-4 mt-1 space-y-0.5">
              <div><span style={{ color: '#22c55e' }}>0.30</span> × code_risk</div>
              <div><span style={{ color: '#84cc16' }}>0.25</span> × ownership</div>
              <div><span style={{ color: '#f59e0b' }}>0.20</span> × liquidity</div>
              <div><span style={{ color: '#f97316' }}>0.12</span> × audit</div>
              <div><span style={{ color: '#ef4444' }}>0.08</span> × compliance</div>
              <div><span style={{ color: '#0ea5e9' }}>0.05</span> × governance</div>
            </div>
          </div>
          <p>
            Each sub-score is independently bounded to [0, 100]. The composite is also bounded to [0, 100].
            Hard overrides can cap the composite below the calculated value — see the Hard Overrides section.
          </p>
          <p>
            Weights reflect the relative importance of each dimension for privacy protocol risk,
            based on post-mortem analysis of historical privacy protocol incidents.
            Code risk carries the highest weight because smart contract vulnerabilities are
            the proximate cause of most protocol failures.
          </p>
        </Section>

        <Section id="dimensions" title="The Six Dimensions">
          {[
            { d: 'Code Risk — 30%', c: '#22c55e', t: 'Slither static analysis runs on the verified bytecode of each contract. We use the standard Slither detector suite plus 5 custom detectors written specifically for privacy protocol patterns. The code risk score starts at 100 and is reduced by finding severity: each high-severity finding reduces the score by 25 points, medium by 10, and low by 3. Unverified contracts receive a base score of 70 (a significant penalty) since we cannot analyse their bytecode. The minimum code risk score is 0. Custom detectors target: mixer reentrancy, ZK verifier bypass patterns, upgrades without timelocks, unlocked privacy pool withdrawal functions, and proxy storage collision vulnerabilities.' },
            { d: 'Ownership — 25%', c: '#84cc16', t: "Ownership analysis starts at 100 and deducts points for centralisation risk. Deductions: no multisig wallet controlling admin functions (−30), no timelock on protocol changes (−20), contract upgradeable without a timelock (−25), single EOA admin key (−15), proxy implementation pattern risk (−10). Bonuses are applied for renounced ownership where the contract is permanently immutable. The final ownership score reflects how much trust the protocol places in a single point of failure." },
            { d: 'Liquidity — 20%', c: '#f59e0b', t: 'TVL (Total Value Locked) is used as a proxy for protocol maturity, user trust, and real-world financial exposure. Data is sourced primarily from DefiLlama (high confidence) with Dune Analytics SIM as a fallback (medium confidence). When both sources have data, a confidence-weighted blend is used. TVL tiers: Whale (>$100M) → 20 pts, Large (>$10M) → 40 pts, Medium (>$1M) → 60 pts, Small (>$100K) → 80 pts, Micro (<$100K) → 95 pts. The score represents liquidity risk — lower TVL = higher risk score.' },
            { d: 'Audit History — 12%', c: '#f97316', t: 'Audit coverage and quality are assessed across eight major smart contract audit firms, tiered by track record and rigour. Tier 1 (Trail of Bits, OpenZeppelin, ConsenSys Diligence, Halborn) → base score 15. Tier 2 (Quantstamp, PeckShield, CertiK) → 30. Tier 3 (others) → 50. No audit → 80. Formal verification adds a −10 bonus. Each unresolved critical finding adds 10 points, each high adds 5. Recency decay applies — audits older than 24 months are weighted down by 50%.' },
            { d: 'Compliance — 8%', c: '#ef4444', t: 'Two compliance checks run on every score request. First: OFAC SDN (Specially Designated Nationals) screening against the US Treasury’s consolidated list, updated daily. Second: DeFiHackLabs exploit registry check for known attacks on the contract or protocol. An active OFAC match triggers a hard override: score capped at 10, grade forced to F. An unresolved exploit triggers a hard override: score capped at 30, grade forced to F. A resolved exploit carries a +20 point penalty without the cap. A clean record scores 0 (no penalty).' },
            { d: 'Governance — 5%', c: '#0ea5e9', t: 'In v1.0, governance is fixed at 50 for all contracts — a neutral value pending the v1.1 implementation. Planned: Herfindahl-Hirschman Index (HHI) for token holder concentration, multisig quorum depth (what percentage of signers are needed), on-chain governance proposal history, and time-average participation rate. The 5% weight reflects that governance is a lagging indicator — poor governance becomes a code or ownership problem before it becomes measurable in token distributions.' },
          ].map(x => (
            <div key={x.d} className="glass rounded-lg p-5">
              <div className="font-orbitron text-sm font-bold mb-3" style={{ color: x.c }}>{x.d}</div>
              <p>{x.t}</p>
            </div>
          ))}
        </Section>

        <Section id="overrides" title="Hard Overrides">
          <p>
            Two conditions trigger hard overrides that cap the composite score regardless of what the
            six dimensions calculate. These are non-negotiable and cannot be offset by strong performance
            in other dimensions.
          </p>
          <div className="space-y-3">
            <div className="glass rounded-lg p-5" style={{ borderColor: 'rgba(124,58,237,0.3)' }}>
              <div className="font-orbitron text-sm font-bold mb-2" style={{ color: '#7c3aed' }}>OFAC ACTIVE — Score capped at 10, grade F</div>
              <p>Any contract matching an active entry in the OFAC Specially Designated Nationals list receives this override. The override is removed automatically when the OFAC entry is delisted. Example: Tornado Cash core contracts.</p>
            </div>
            <div className="glass rounded-lg p-5" style={{ borderColor: 'rgba(185,28,28,0.3)' }}>
              <div className="font-orbitron text-sm font-bold mb-2" style={{ color: '#b91c1c' }}>EXPLOIT ACTIVE — Score capped at 30, grade F</div>
              <p>Any contract with an unresolved entry in the DeFiHackLabs exploit registry. Removed via the admin override API endpoint when the protocol provides documented remediation evidence (post-mortem, compensation plan, or redeployment).</p>
            </div>
          </div>
        </Section>

        <Section id="detectors" title="Custom Privacy Detectors">
          <p>
            Standard Slither detectors are not designed for privacy protocol patterns. We wrote
            five custom detectors that target the vulnerability classes most common in ZK-based
            and mixer-based protocols:
          </p>
          <div className="space-y-3">
            {[
              { n: 'MixerReentrancy',         d: 'Detects reentrancy vulnerabilities in withdrawal functions of mixer-pattern contracts, including cross-function reentrancy via shared state.' },
              { n: 'ZKVerifierBypass',         d: 'Identifies patterns where ZK proof verification can be bypassed through calldata manipulation or missing input validation on the verifier contract.' },
              { n: 'UpgradeWithoutTimelock',   d: 'Flags upgradeable proxy patterns (EIP-1967, UUPS, Transparent) where the upgrade function is not protected by a timelock of at least 24 hours.' },
              { n: 'UnlockedPrivacyWithdrawal',d: 'Detects withdrawal functions in privacy pools that lack nullifier checks, making double-spend attacks possible.' },
              { n: 'ProxyStorageCollision',    d: 'Identifies storage layout conflicts between proxy contracts and their implementation contracts, a known vulnerability class in privacy protocol architectures.' },
            ].map(x => (
              <div key={x.n} className="glass rounded-lg p-4">
                <code className="font-mono text-xs font-bold" style={{ color: '#00d4ff' }}>{x.n}</code>
                <p className="mt-2 text-xs">{x.d}</p>
              </div>
            ))}
          </div>
        </Section>

        <Section id="curated" title="Curated Protocol Registry">
          <p>
            The curated registry contains 14 privacy protocols that have been manually vetted
            for inclusion. Criteria: verified source code on a block explorer, live mainnet
            deployment, documented architecture, and a public point of contact.
          </p>
          <p>
            Curated protocols are rescored every 6 hours via an automated Celery beat schedule.
            All contracts in the ecosystem are scored individually and the results are aggregated
            using the same methodology as community scans.
          </p>
          <p>
            To request addition to the curated registry, use the{' '}
            <Link href="/request" className="cursor-pointer hover:underline" style={{ color: '#00d4ff' }}>Add Protocol</Link>{' '}
            form. Submissions are reviewed within 72 hours.
          </p>
          <div className="glass rounded-xl overflow-hidden mt-3">
            <div className="grid font-mono text-xs text-slate-500 tracking-widest px-5 py-3"
              style={{ gridTemplateColumns: '2fr 1fr 1fr', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
              <span>PROTOCOL</span><span>ECOSYSTEM</span><span>CONTRACTS</span>
            </div>
            {[
              ['Railgun',           'Ethereum + L2s', '12'],
              ['Aztec',             'Ethereum',       '12'],
              ['Privacy Pools',     'Ethereum',       '5' ],
              ['Hinkal',            'Multi-chain',    '29'],
              ['Tornado Cash',      'Multi-chain',    '41'],
              ['0x0.ai',            'Multi-chain',    '8' ],
              ['iExec',             'Ethereum',       '14'],
              ['… 7 more',     '',               ''  ],
            ].map(([n,e,c], i) => (
              <div key={i} className="grid px-5 py-3 border-b font-mono text-xs"
                style={{ gridTemplateColumns: '2fr 1fr 1fr', borderColor: 'rgba(255,255,255,0.05)' }}>
                <span className="text-slate-300">{n}</span>
                <span className="text-slate-500">{e}</span>
                <span className="text-slate-500">{c}</span>
              </div>
            ))}
          </div>
        </Section>

        <Section id="api" title="The API">
          <p>
            All PrivaScan scores are accessible via a REST API. The API is free for community
            use at 500 requests per hour with a free key. It is designed to be embedded into
            wallets, DeFi frontends, research tools, and risk dashboards.
          </p>
          <p>
            Full API documentation including endpoint specifications, request/response schemas,
            error codes, and code examples is available at:
          </p>
          <Link href="/api"
            className="inline-flex items-center gap-2 font-orbitron text-xs font-bold px-5 py-3 rounded-lg transition-all cursor-pointer hover:opacity-90 mt-2"
            style={{ background: '#00d4ff', color: '#0a0f1e' }}>
            View API Documentation →
          </Link>
        </Section>

        <Section id="bot" title="The Telegram Bot">
          <p>
            @PrivaScanBot brings risk scoring to Telegram. Users can score contracts,
            set up watchlists with alert thresholds, and receive real-time notifications
            when a protocol’s risk grade changes — without leaving Telegram.
          </p>
          <p>Commands: <code className="font-mono text-xs" style={{ color: '#00d4ff' }}>/score</code> · <code className="font-mono text-xs" style={{ color: '#00d4ff' }}>/watch</code> · <code className="font-mono text-xs" style={{ color: '#00d4ff' }}>/unwatch</code> · <code className="font-mono text-xs" style={{ color: '#00d4ff' }}>/mylist</code> · <code className="font-mono text-xs" style={{ color: '#00d4ff' }}>/protocol</code></p>
          <a href="https://t.me/PrivaScanBot" target="_blank" rel="noreferrer"
            className="inline-flex items-center gap-2 font-mono text-sm font-bold px-5 py-3 rounded-lg transition-all cursor-pointer hover:opacity-90 mt-2 glass glass-hover">
            Open @PrivaScanBot ↗
          </a>
        </Section>

        <Section id="roadmap" title="Roadmap">
          <div className="space-y-3">
            {[
              { v: 'v1.0', s: 'Live', c: '#22c55e', items: ['14 curated protocols', '6-dimension scoring', 'REST API', 'Telegram bot', 'Free API keys', 'OFAC + exploit overrides'] },
              { v: 'v1.1', s: 'Q3 2026', c: '#f59e0b', items: ['Governance dimension (HHI, quorum)', 'Twitter OAuth for API key verification', 'Real-time trending feed', 'Score webhooks', 'Protocol comparison view'] },
              { v: 'v1.2', s: 'Q4 2026', c: '#4a7090', items: ['Pro tier (1,000 req/hr)', 'Score embed widget', 'Historical score database (full history)', 'Multi-chain ecosystem aggregation', 'Formal verification detection'] },
            ].map(r => (
              <div key={r.v} className="glass rounded-lg p-5 flex gap-4">
                <div className="shrink-0">
                  <div className="font-orbitron text-sm font-bold" style={{ color: r.c }}>{r.v}</div>
                  <div className="font-mono text-xs mt-1" style={{ color: r.c }}>{r.s}</div>
                </div>
                <ul className="space-y-1">
                  {r.items.map(i => <li key={i} className="font-mono text-xs text-slate-400">• {i}</li>)}
                </ul>
              </div>
            ))}
          </div>
        </Section>

        <Section id="disclaimer" title="Disclaimer">
          <p>
            PrivaScan scores are informational tools produced by automated analysis.
            They are not financial advice, legal advice, or security certifications.
            A grade A score does not mean a contract is safe. A grade F score does not mean
            a contract will fail. Scores reflect the state of a contract at the time of analysis
            and may become stale.
          </p>
          <p>
            PrivaScan is open source under the MIT licence. The codebase, detectors, and
            methodology are publicly reviewable at{' '}
            <a href="https://github.com/only1angelnath/Privascan" target="_blank" rel="noreferrer"
              className="cursor-pointer hover:underline" style={{ color: '#00d4ff' }}>
              github.com/only1angelnath/Privascan
            </a>.
          </p>
          <p>
            Do not interact with any smart contract based solely on a PrivaScan score.
            Always conduct your own independent research.
          </p>
        </Section>

      </div>
    </div>
  )
}
