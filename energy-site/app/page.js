'use client'

import { useEffect, useRef } from 'react'

/* ---------- Service visuals (SVG) ---------- */
const visuals = {
  // Energy consumption — heatmap grid + trend line
  consumption: (
    <svg viewBox="0 0 320 130" fill="none" className="w-full h-full">
      {Array.from({ length: 4 }).map((_, row) =>
        Array.from({ length: 12 }).map((_, col) => {
          const op = (((row * 7 + col * 3) % 9) / 9) * 0.16 + 0.04
          // scattered hot cells across the grid, varying intensity
          const hotCells = { '0-2': 0.5, '0-7': 0.3, '1-0': 0.35, '1-4': 0.55, '1-9': 0.3, '2-2': 0.3, '2-6': 0.5, '2-11': 0.4, '3-3': 0.45, '3-8': 0.32 }
          const hot = hotCells[`${row}-${col}`]
          return (
            <rect
              key={`${row}-${col}`}
              x={col * 26 + 4}
              y={row * 22 + 10}
              width={22}
              height={18}
              rx="2"
              fill={hot ? '#4cc406' : 'white'}
              fillOpacity={hot || op}
            />
          )
        })
      )}
      <polyline
        points="4,112 30,104 56,108 82,86 108,92 134,68 160,74 186,52 212,58 238,36 264,42 290,24 316,18"
        stroke="#4cc406" strokeOpacity="0.65" strokeWidth="1.5" fill="none" strokeLinejoin="round"
      />
    </svg>
  ),
  // Excel automation — multiple sources consolidating into a dashboard
  automation: (
    <svg viewBox="0 0 320 130" fill="none" className="w-full h-full">
      {/* source files */}
      {[18, 48, 78].map((y, i) => (
        <rect key={y} x="16" y={y} width="36" height="22" rx="3"
          fill="white" fillOpacity={0.06 - i * 0.01} stroke="white" strokeOpacity="0.12" strokeWidth="1"/>
      ))}
      {/* flow arrows */}
      {[29, 59, 89].map((y) => (
        <line key={y} x1="56" y1={y} x2="150" y2="65" stroke="white" strokeOpacity="0.12" strokeWidth="1"/>
      ))}
      {/* dashboard */}
      <rect x="158" y="20" width="148" height="90" rx="5" fill="white" fillOpacity="0.05" stroke="white" strokeOpacity="0.12" strokeWidth="1"/>
      {/* regression line — clean diagonal bottom-left to top-right */}
      <line x1="170" y1="94" x2="294" y2="38" stroke="#4cc406" strokeOpacity="0.45" strokeWidth="1.3" strokeDasharray="5 3"/>
      {/* scatter points — small residuals around the diagonal */}
      {[[172, 95], [187, 81], [202, 83], [217, 69], [232, 68], [247, 54], [262, 55], [277, 42], [292, 40]].map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r="2.5" fill="#4cc406" fillOpacity="0.7" />
      ))}
    </svg>
  ),
  // PV producer — production vs estimate (two curves + sun)
  pv: (
    <svg viewBox="0 0 320 130" fill="none" className="w-full h-full">
      <circle cx="262" cy="32" r="13" fill="#4cc406" fillOpacity="0.12"/>
      <circle cx="262" cy="32" r="7" fill="#4cc406" fillOpacity="0.22"/>
      <line x1="0" y1="115" x2="320" y2="115" stroke="white" strokeOpacity="0.06" strokeWidth="1"/>
      {/* estimate — dashed */}
      <path d="M0,108 C60,108 90,40 160,40 C230,40 260,108 320,108"
        stroke="white" strokeOpacity="0.16" strokeWidth="1.5" fill="none" strokeDasharray="5 4"/>
      {/* actual production — solid */}
      <path d="M0,110 C60,110 95,55 160,55 C225,55 260,110 320,110"
        stroke="#4cc406" strokeOpacity="0.6" strokeWidth="1.5" fill="none"/>
      <path d="M0,110 C60,110 95,55 160,55 C225,55 260,110 320,110 L320,115 L0,115 Z"
        fill="#4cc406" fillOpacity="0.05"/>
    </svg>
  ),
  // Investor — portfolio KPIs (bars + financial line)
  investor: (
    <svg viewBox="0 0 320 130" fill="none" className="w-full h-full">
      <line x1="0" y1="110" x2="320" y2="110" stroke="white" strokeOpacity="0.06" strokeWidth="1"/>
      {[24, 70, 116, 162, 208, 254].map((x, i) => {
        const h = [40, 58, 50, 74, 64, 88][i]
        return <rect key={x} x={x} y={110 - h} width={30} height={h} rx="2" fill="white" fillOpacity={0.06 + i * 0.012}/>
      })}
      <polyline points="39,78 85,58 131,64 177,40 223,48 269,24"
        stroke="#4cc406" strokeOpacity="0.6" strokeWidth="1.5" fill="none" strokeLinejoin="round"/>
      {[39, 85, 131, 177, 223, 269].map((x, i) => {
        const y = [78, 58, 64, 40, 48, 24][i]
        return <circle key={x} cx={x} cy={y} r="3" fill="#4cc406" fillOpacity="0.7"/>
      })}
    </svg>
  ),
}

/* ---------- Content (bilingual) ---------- */
const t = {
  ro: {
    badge: 'Analiză & Raportare Energetică',
    heroTitle1: 'Datele tale energetice,',
    heroTitle2: 'transformate în decizii clare.',
    heroSub:
      'Te ajut să înțelegi unde se duc costurile, să elimini raportarea manuală și să ai mereu o imagine clară asupra performanței energetice.',
    ctaPrimary: 'Hai să vorbim',
    ctaSecondary: 'Vezi serviciile ↓',
    servicesLabel: 'Servicii',
    servicesTitle: 'Ce pot face pentru tine',
    problemsLabel: 'Probleme pe care le rezolv',
    problemsTitle: 'Îți sună cunoscut?',
    problemsSub: 'Dacă recunoști vreuna dintre acestea, te pot ajuta.',
    portfolioLabel: 'Studiu de caz',
    portfolioTitle: 'Analiză: producția solară vs. prețurile day-ahead',
    portfolioDesc:
      'Date orare OPCOM pentru parcuri fotovoltaice. Producția maximă cade fix la prânz, când prețul pe piața day-ahead (DAM) e cel mai mic.',
    portfolioPoints: [
      'Capture rate ~96% — PV prinde un preț sub media pieței',
      'Vârf de producție la ora 13, exact unde prețul atinge minimul',
      'Date reale OPCOM → Python (pandas) → grafic interactiv',
    ],
    finalTitle: 'Datele tale energetice îți spun mai multe decât crezi.',
    finalSub: 'Scrie-mi și hai să descoperim împreună ce poți afla din ele.',
    finalCta: 'Contactează-mă',
    services: [
      {
        visual: 'consumption',
        title: 'Analiza consumului energetic',
        desc: 'Înțelegi exact unde, când și cât consumi — și unde pierzi bani.',
        points: [
          'Identificarea costurilor și a anomaliilor',
          'Analiza tendințelor de consum',
          'Rapoarte clare pentru management',
        ],
      },
      {
        visual: 'automation',
        title: 'Automatizarea rapoartelor Excel',
        desc: 'Scapi de munca manuală repetitivă și de fișierele răspândite peste tot.',
        points: [
          'Eliminarea proceselor manuale',
          'Consolidarea datelor din mai multe surse',
          'Dashboard-uri și KPI-uri actualizate automat',
        ],
      },
      {
        visual: 'pv',
        title: 'Analiză pentru producători fotovoltaici',
        desc: 'Vezi dacă instalația produce cât ar trebui — și unde pierzi randament.',
        points: [
          'Producție reală vs. estimare',
          'Monitorizarea performanței',
          'Identificarea pierderilor de producție',
        ],
      },
      {
        visual: 'investor',
        title: 'Analiză pentru investitori',
        desc: 'Ai o imagine de ansamblu asupra portofoliului, fără să sapi prin tabele.',
        points: [
          'KPI operaționali și financiari',
          'Monitorizarea portofoliului',
          'Rapoarte automate pentru decizii rapide',
        ],
      },
    ],
    problems: [
      'Facturi energetice greu de înțeles',
      'Date răspândite în zeci de fișiere Excel',
      'Raportare manuală care consumă timp prețios',
      'Lipsa indicatorilor de performanță (KPI)',
      'Lipsa unei imagini clare asupra costurilor energetice',
    ],
  },
  en: {
    badge: 'Energy Analytics & Reporting',
    heroTitle1: 'See How Your',
    heroTitle2: 'Energy Performs',
    heroSub:
      'Analytics for solar performance, energy reporting, and operational insights.',
    ctaPrimary: "Let's talk",
    ctaSecondary: 'See services ↓',
    servicesLabel: 'Services',
    servicesTitle: 'What I can do for you',
    problemsLabel: 'Where energy data becomes a challenge',
    problemsTitle: 'From fragmented spreadsheets to optimized energy performance.',
    problemsSub: '',
    portfolioLabel: 'Case study',
    portfolioTitle: 'Analysis: Solar Output vs. Day-Ahead Prices',
    portfolioDesc:
      'Hourly OPCOM data for solar parks. Peak production lands exactly at midday, when the day-ahead market (DAM) price is lowest.',
    portfolioPoints: [
      'Capture Rate 96%: PV captures a price below the market average',
      'Production peaks at 1 PM, exactly where price bottoms out',
      'Selling at midday lows cuts PV revenue by 4% vs. the market average',
    ],
    finalTitle: 'Your energy data tells you more than you think.',
    finalSub: "Get in touch and let's find out what it can reveal.",
    finalCta: 'Get in touch',
    services: [
      {
        visual: 'consumption',
        title: 'Energy consumption analysis',
        desc: 'Understand exactly where, when and how much you consume — and where money leaks.',
        points: [
          'Identifying costs and anomalies',
          'Consumption trend analysis',
          'Clear reports for management',
        ],
      },
      {
        visual: 'automation',
        title: 'Excel report automation',
        desc: 'Cut out the repetitive manual work and the files scattered everywhere.',
        points: [
          'Eliminating manual processes',
          'Consolidating data from multiple sources',
          'Dashboards and KPIs updated automatically',
        ],
      },
      {
        visual: 'pv',
        title: 'Analytics for PV producers',
        desc: 'See whether your plant produces what it should — and where yield is lost.',
        points: [
          'Actual production vs. estimate',
          'Performance monitoring',
          'Identifying production losses',
        ],
      },
      {
        visual: 'investor',
        title: 'Analytics for investors',
        desc: 'Get a portfolio-wide overview without digging through spreadsheets.',
        points: [
          'Operational and financial KPIs',
          'Portfolio monitoring',
          'Automated reports for fast decisions',
        ],
      },
    ],
    problems: [
      'Energy bills that are hard to understand',
      'Data scattered across dozens of Excel files',
      'Manual reporting that eats up valuable time',
      'No visibility into solar asset performance',
      'Production data without actionable insights',
    ],
  },
}

export default function Home() {
  const c = t.en
  const ref = useRef(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) e.target.classList.add('fade-visible')
        })
      },
      { threshold: 0.1 }
    )
    const cards = document.querySelectorAll('.fade-card')
    cards.forEach((card) => observer.observe(card))
    return () => observer.disconnect()
  }, [])

  return (
    <div className="min-h-screen bg-[#060810] text-white">
      <div className="hero-glow fixed inset-0 z-0" />

      {/* Nav */}
      <nav className="relative z-20 px-6 sm:px-8 py-4 flex justify-between items-center border-b border-white/[0.06] backdrop-blur-sm bg-[#060810]/80 sticky top-0">
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold tracking-widest text-white flex items-center">
            S
            <span className="inline-block w-2.5 h-2.5 mx-[2px] rounded-full bg-[#4cc406] shadow-[0_0_8px_#4cc406]" />
            LAR&nbsp;INSIGHTS
          </span>
        </div>
        <div className="flex items-center gap-3 sm:gap-5">
          <a
            href="mailto:simo.fleanta@gmail.com"
            className="text-sm bg-white text-[#060810] font-medium px-4 py-1.5 rounded-full hover:bg-white/90 transition-colors"
          >
            Contact
          </a>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 flex flex-col items-center text-center px-6 sm:px-8 pt-24 sm:pt-28 pb-20">
        <div className="inline-flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-4 py-1.5 text-xs text-white/40 mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-[#4cc406] shadow-[0_0_8px_#4cc406]" />
          {c.badge}
        </div>
        <h1 className="text-4xl sm:text-6xl font-bold leading-[1.1] tracking-tight mb-6 max-w-3xl">
          {c.heroTitle1}<br />
          <span className="text-white/55">{c.heroTitle2}</span>
          <span className="inline-block w-2.5 h-2.5 sm:w-3.5 sm:h-3.5 ml-1.5 rounded-full bg-[#4cc406] shadow-[0_0_14px_#4cc406] align-baseline" />
        </h1>
        <p className="text-white/40 text-base sm:text-lg max-w-xl leading-relaxed mb-10">
          {c.heroSub}
        </p>
        <div className="flex items-center gap-6">
          <a
            href="mailto:simo.fleanta@gmail.com"
            className="bg-white text-[#060810] font-semibold px-6 py-2.5 rounded-full hover:bg-white/90 transition-colors text-sm"
          >
            {c.ctaPrimary}
          </a>
          <a
            href="#servicii"
            className="text-sm text-white/40 hover:text-white/70 transition-colors"
          >
            {c.ctaSecondary}
          </a>
        </div>
      </section>

      {/* Services */}
      <section id="servicii" ref={ref} className="relative z-10 px-6 sm:px-8 pb-20 max-w-4xl mx-auto">
        <p className="text-xs tracking-widest uppercase text-white/20 mb-3 text-center">{c.servicesLabel}</p>
        <h2 className="text-2xl sm:text-3xl font-semibold text-center mb-12">{c.servicesTitle}</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {c.services.map((s, i) => (
            <div
              key={s.title}
              className="fade-card card-glass rounded-2xl overflow-hidden flex flex-col"
              style={{ transitionDelay: `${i * 90}ms` }}
            >
              <div className="h-36 bg-[#0A0E18] relative overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center">
                  {visuals[s.visual]}
                </div>
                <div className="absolute inset-0 bg-gradient-to-t from-[#0A0E18] via-transparent to-transparent" />
              </div>
              <div className="p-6 flex flex-col flex-1">
                <h3 className="font-semibold text-base text-white/90 mb-2">{s.title}</h3>
                <p className="text-white/40 text-sm leading-relaxed mb-5">{s.desc}</p>
                <ul className="mt-auto space-y-2">
                  {s.points.map((p) => (
                    <li key={p} className="flex items-start gap-2.5 text-sm text-white/55">
                      <span className="mt-[7px] w-1 h-1 rounded-full bg-[#4cc406]/70 shrink-0" />
                      {p}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Case study / Portfolio */}
      <section id="case-study" className="relative z-10 px-6 sm:px-8 pb-20 max-w-4xl mx-auto">
        <p className="text-xs tracking-widest uppercase text-white/20 mb-3 text-center">{c.portfolioLabel}</p>
        <h2 className="text-2xl sm:text-3xl font-semibold text-center mb-4">{c.portfolioTitle}</h2>
        <p className="text-white/40 text-sm sm:text-base text-center max-w-2xl mx-auto mb-8 leading-relaxed">
          {c.portfolioDesc}
        </p>
        <div className="fade-card card-glass rounded-2xl overflow-hidden p-2 sm:p-4">
          <iframe
            src="/pzu-profil.html"
            title="PZU hourly profile"
            className="w-full rounded-xl"
            style={{ height: '460px', border: 'none', background: 'transparent' }}
          />
        </div>
        <ul className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-3">
          {c.portfolioPoints.map((p, i) => (
            <li key={p} style={{ transitionDelay: `${i * 90}ms` }}
              className="fade-card card-glass rounded-xl px-4 py-3 text-sm text-white/60 flex items-start gap-2.5">
              <span className="mt-[7px] w-1 h-1 rounded-full bg-[#4cc406]/70 shrink-0" />
              {p}
            </li>
          ))}
        </ul>
      </section>

      {/* Problems I solve */}
      <section className="relative z-10 px-6 sm:px-8 pb-20 max-w-2xl mx-auto">
        <p className="text-xs tracking-widest uppercase text-white/20 mb-3 text-center">{c.problemsLabel}</p>
        <h2 className="text-lg sm:text-xl font-semibold text-center mb-10 max-w-md mx-auto leading-snug">{c.problemsTitle}</h2>
        {c.problemsSub && <p className="text-white/35 text-sm text-center mb-10 -mt-6">{c.problemsSub}</p>}
        <div className="space-y-2.5">
          {c.problems.map((p) => (
            <div
              key={p}
              className="card-glass rounded-xl px-5 py-4 flex items-center gap-3.5 text-sm text-white/65"
            >
              <span className="w-2 h-2 rounded-full bg-[#4cc406] shadow-[0_0_8px_#4cc406] shrink-0" />
              {p}
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 px-6 sm:px-8 py-6 border-t border-white/[0.06] flex justify-between items-center max-w-5xl mx-auto">
        <span className="text-white/20 text-xs tracking-widest flex items-center">
          S
          <span className="inline-block w-1.5 h-1.5 mx-[1.5px] rounded-full bg-[#4cc406]/80" />
          LAR&nbsp;INSIGHTS&nbsp;·&nbsp;BY&nbsp;INSIGHTS&nbsp;HOUSE
        </span>
        <a href="mailto:simo.fleanta@gmail.com" className="text-white/25 text-xs hover:text-white/50 transition-colors">
          simo.fleanta@gmail.com
        </a>
      </footer>
    </div>
  )
}
