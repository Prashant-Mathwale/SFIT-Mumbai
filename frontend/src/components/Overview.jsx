import React, { useState, useEffect, useRef, useCallback } from 'react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getOverviewMetrics, getInterventionLog, getModelInfo, getAtRiskCustomers } from '../api/client';
import Loader from './ui/Loader';

/* ═══════════════════════════════════════════
   OVERVIEW — Enterprise Dashboard v2.0
   Live Ticker + KPI Glow + Donut + Velocity + Portfolio
   ═══════════════════════════════════════════ */

function AnimatedNumber({ target, duration = 1800, suffix = '', prefix = '', color = 'var(--accent-cyan)', decimals = 0, onDone }) {
  const [val, setVal] = useState(0);
  const ref = useRef(null);
  useEffect(() => {
    let start = null;
    const step = (ts) => {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      setVal(ease * target);
      if (progress < 1) {
        ref.current = requestAnimationFrame(step);
      } else if (onDone) onDone();
    };
    ref.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(ref.current);
  }, [target, duration, onDone]);
  return <span style={{ color }}>{prefix}{val.toFixed(decimals).replace(/\B(?=(\d{2})+(\d)(?!\d))/g, ',')}{suffix}</span>;
}

// ── Live Alert Ticker ──
function AlertTicker({ atRiskData }) {
  const alerts = atRiskData && atRiskData.length > 0
    ? atRiskData.slice(0, 8).map(c => {
      let severity = '#f59e0b'; // Medium
      if (c.risk_level === 'HIGH' || c.anomaly_flag) severity = '#ff4757';
      return { severity, text: `${c.anomaly_flag ? '🔴' : '⚠️'} ${c.name} — Risk ${Math.round(c.risk_score * 100)} — ${c.top_signal || 'Requires attention'}` };
    })
    : [
      { severity: '#ff4757', text: '🔴 Loading live security feeds...' },
    ];
  const doubled = [...alerts, ...alerts];
  return (
    <div className="alert-ticker">
      <div className="alert-ticker-badge">
        <span className="dot" />
        LIVE MONITORING
      </div>
      <div className="alert-ticker-track">
        {doubled.map((alert, i) => (
          <div key={i} className="alert-ticker-item">
            <span className="severity" style={{ background: alert.severity }} />
            {alert.text}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Animated SVG Donut ──
function AnimatedDonut({ data }) {
  const [animProgress, setAnimProgress] = useState(0);
  const total = data.reduce((s, d) => s + d.value, 0);
  const svgSize = 220;
  const cx = svgSize / 2, cy = svgSize / 2, r = 85, strokeWidth = 22;
  const circumference = 2 * Math.PI * r;
  const [hovered, setHovered] = useState(null);

  useEffect(() => {
    let start = null;
    const animate = (ts) => {
      if (!start) start = ts;
      const p = Math.min((ts - start) / 1000, 1);
      setAnimProgress(p);
      if (p < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, []);

  let accum = 0;
  const segments = data.map((d, i) => {
    const fraction = d.value / total;
    const offset = circumference * (1 - fraction * animProgress);
    const rotation = (accum / total) * 360 * animProgress - 90;
    accum += d.value;
    const isHovered = hovered === i;
    const tx = isHovered ? Math.cos((rotation + fraction * 180) * Math.PI / 180) * 8 : 0;
    const ty = isHovered ? Math.sin((rotation + fraction * 180) * Math.PI / 180) * 8 : 0;
    return (
      <circle
        key={i}
        cx={cx} cy={cy} r={r}
        fill="none" stroke={d.color} strokeWidth={strokeWidth}
        strokeDasharray={`${circumference}`}
        strokeDashoffset={offset}
        transform={`rotate(${rotation} ${cx} ${cy}) translate(${tx} ${ty})`}
        style={{ transition: 'transform 200ms ease', cursor: 'pointer' }}
        onMouseEnter={() => setHovered(i)}
        onMouseLeave={() => setHovered(null)}
        strokeLinecap="round"
      />
    );
  });

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
      <div style={{ position: 'relative' }}>
        <svg width={svgSize} height={svgSize}>
          <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth={strokeWidth} />
          {segments}
        </svg>
        <div style={{
          position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
          textAlign: 'center', animation: 'breathe 2s ease-in-out infinite',
        }}>
          <div style={{ fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: 36, color: '#e0e0f0' }}>{total}</div>
          <div style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 11, color: '#5a5a7a', textTransform: 'uppercase' }}>Total</div>
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {data.map((d, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}
            onMouseEnter={() => setHovered(i)} onMouseLeave={() => setHovered(null)}>
            <span style={{
              width: 8, height: 8, borderRadius: '50%', background: d.color,
              animation: 'dotBlink 2s infinite', animationDelay: `${i * 0.3}s`,
            }} />
            <span style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 13, color: hovered === i ? '#e0e0f0' : '#9999bb', transition: 'color 200ms' }}>
              {d.name}: <strong style={{ color: d.color }}>{d.value}</strong>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Portfolio Exposure Bar ──
function PortfolioBar({ label, value, maxVal, color, delay }) {
  const [visible, setVisible] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) setVisible(true);
    }, { threshold: 0.5 });
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  const pct = (value / maxVal) * 100;
  return (
    <div ref={ref} style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 13, color: '#9999bb' }}>{label}</span>
        <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 13, color }}>{value}%</span>
      </div>
      <div style={{ height: 8, borderRadius: 100, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
        <div style={{
          height: '100%', borderRadius: 100, background: color,
          width: visible ? `${pct}%` : '0%',
          transition: `width 0.8s ease-out ${delay}ms`,
          boxShadow: `0 0 12px ${color}40`,
        }} />
      </div>
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: '#151525', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '10px 14px', boxShadow: '0 12px 40px rgba(0,0,0,0.5)' }}>
      <div style={{ fontFamily: 'DM Mono', fontSize: 11, color: '#5a5a7a', marginBottom: 4 }}>Week {label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ fontFamily: 'DM Mono', fontSize: 12, color: p.color }}>{p.name}: {typeof p.value === 'number' ? p.value.toFixed(0) : p.value}</div>
      ))}
    </div>
  );
};

export default function Overview({ clock }) {
  const [metrics, setMetrics] = useState(null);
  const [interventions, setInterventions] = useState([]);
  const [modelInfoData, setModelInfoData] = useState(null);
  const [atRisk, setAtRisk] = useState([]);
  const [loading, setLoading] = useState(true);

  const refreshOverview = useCallback(() => {
    Promise.all([
      getOverviewMetrics().catch(() => null),
      getInterventionLog(1, 200).catch(() => []),
      getModelInfo().catch(() => null),
      getAtRiskCustomers(null, 0.40, 10).catch(() => [])
    ]).then(([m, logs, mInfo, riskList]) => {
      setMetrics(m || {});
      setInterventions(logs || []);
      setModelInfoData(mInfo);
      setAtRisk(riskList || []);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    refreshOverview();
    const timer = setInterval(refreshOverview, 15000);
    return () => clearInterval(timer);
  }, [refreshOverview]);

  const m = metrics || {};

  // Risk velocity data (52 weeks) 
  const riskVelocityData = m.risk_velocity || [];

  // Donut data
  const donutData = m.donut_data || [];

  if (loading) return <Loader message="LOADING SECURE DASHBOARD..." />;

  return (
    <div style={{ animation: 'fadeSlideUp 600ms ease' }}>
      {/* Live Alert Ticker */}
      <AlertTicker atRiskData={atRisk} />

      <div className="page-header">
        <div>
          <h1>Risk Operations Center</h1>
          <p className="subtitle">Real-time ensemble risk scoring across {m.total_customers || 0} monitored customers</p>
        </div>
        <div className="page-header-right">
          <span className="clock">{clock}</span>
          <span className="week-badge">Week 52 — Latest</span>
        </div>
      </div>

      {/* KPI Cards — 5 columns with glow effects */}
      <div className="kpi-grid">
        {/* Hero Card: Total Portfolio */}
        <div className="kpi-card" style={{ '--kpi-color': 'var(--accent-green)' }}>
          <div className="kpi-card-top">
            <div className="kpi-icon" style={{ background: 'rgba(6,255,165,0.1)' }}>
              <svg width="24" height="24" fill="var(--accent-green)" viewBox="0 0 24 24"><path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z" /></svg>
            </div>
            <span className="kpi-label">Total Portfolio</span>
          </div>
          <div className="kpi-value"><AnimatedNumber target={m.total_portfolio || 0} prefix="₹" suffix=" Cr" color="var(--accent-green)" decimals={1} duration={1200} /></div>
          <div className="kpi-delta" style={{ color: 'var(--accent-green)' }}>{m.portfolio_delta || "—"}</div>
        </div>

        {/* Monitored */}
        <div className="kpi-card" style={{ '--kpi-color': 'var(--accent-cyan)' }}>
          <div className="kpi-card-top">
            <div className="kpi-icon" style={{ background: 'rgba(0,212,255,0.1)' }}>
              <svg width="24" height="24" fill="var(--accent-cyan)" viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" /></svg>
            </div>
            <span className="kpi-label">Total Monitored</span>
          </div>
          <div className="kpi-value"><AnimatedNumber target={m.total_customers || 0} color="var(--accent-cyan)" duration={1200} /></div>
          <div className="kpi-delta" style={{ color: 'var(--text-muted)' }}>{m.at_risk_delta || "—"}</div>
        </div>

        {/* Critical — pulsing red border */}
        <div className="kpi-card critical-card" style={{ '--kpi-color': 'var(--accent-red)' }}>
          <div className="kpi-card-top">
            <div className="kpi-icon" style={{ background: 'rgba(255,71,87,0.1)' }}>
              <svg width="24" height="24" fill="var(--accent-red)" viewBox="0 0 24 24"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z" /></svg>
            </div>
            <span className="kpi-label">Avoided Loss</span>
          </div>
          <div className="kpi-value"><AnimatedNumber target={m.avoided_loss_cr || 0} prefix="₹" suffix=" Cr" color="var(--accent-red)" decimals={1} duration={1200} /></div>
          <div className="kpi-delta" style={{ color: 'var(--accent-red)' }}>
            <span style={{ animation: 'dotBlink 1.2s infinite', marginRight: 4 }}>●</span>
            Prevented via early intervention
          </div>
        </div>

        {/* Interventions — robot icon */}
        <div className="kpi-card" style={{ '--kpi-color': 'var(--accent-orange)' }}>
          <div className="kpi-card-top">
            <div className="kpi-icon" style={{ background: 'rgba(255,107,53,0.1)' }}>
              <span style={{ fontSize: 20, animation: 'rotateOnce 1s ease-out', display: 'inline-block' }}>🤖</span>
            </div>
            <span className="kpi-label">Auto Interventions</span>
          </div>
          <div className="kpi-value"><AnimatedNumber target={m.interventions_sent_today || 0} color="var(--accent-orange)" duration={1200} /></div>
          <div className="kpi-delta" style={{ color: 'var(--accent-orange)' }}>{m.intervention_delta || "—"}</div>
        </div>

        {/* Recovery Rate */}
        <div className="kpi-card" style={{ '--kpi-color': 'var(--accent-green)' }}>
          <div className="kpi-card-top">
            <div className="kpi-icon" style={{ background: 'rgba(6,255,165,0.1)' }}>
              <svg width="24" height="24" fill="var(--accent-green)" viewBox="0 0 24 24"><path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z" /></svg>
            </div>
            <span className="kpi-label">Recovery Rate</span>
          </div>
          <div className="kpi-value"><AnimatedNumber target={Math.round(m.recovery_rate || 0)} suffix="%" color="var(--accent-green)" duration={1200} /></div>
          <div className="kpi-delta" style={{ color: 'var(--accent-green)' }}>{m.recovery_delta || "—"}</div>
        </div>
      </div>

      {/* Charts Row — Donut + Risk Velocity */}
      <div className="charts-row">
        {/* Animated Donut */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Risk Distribution</span>
            <div className="legend-row">
              <span className="legend-pill high">Critical ≥0.70</span>
              <span className="legend-pill medium">High 0.40–0.69</span>
              <span className="legend-pill low">Low &lt;0.40</span>
            </div>
          </div>
          <AnimatedDonut data={donutData} />
        </div>

        {/* Risk Velocity AreaChart */}
        <div className="card" style={{ position: 'relative' }}>
          <div className="card-header">
            <span className="card-title">Portfolio Risk Velocity</span>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 6,
              background: 'rgba(6,255,165,0.08)', border: '1px solid rgba(6,255,165,0.2)',
              padding: '3px 10px', borderRadius: 100,
            }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#06ffa5', animation: 'livePulse 2s infinite' }} />
              <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, color: '#06ffa5' }}>LIVE</span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={riskVelocityData}>
              <defs>
                <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ff4757" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#ff4757" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
              <XAxis dataKey="week" tick={{ fontFamily: 'DM Mono', fontSize: 11, fill: '#5a5a7a' }} />
              <YAxis tick={{ fontFamily: 'DM Mono', fontSize: 11, fill: '#5a5a7a' }} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="stress" stroke="#ff4757" strokeWidth={2} fill="url(#riskGradient)" animationDuration={1500} animationBegin={0} name="Stress %" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Portfolio Exposure + Model Strip */}
      <div className="charts-row">
        <div className="card">
          <div className="card-header">
            <span className="card-title">Portfolio Exposure by Product</span>
          </div>
          {(m.portfolio_exposure && m.portfolio_exposure.length > 0 ? m.portfolio_exposure : []).map((p, i) => (
            <PortfolioBar key={i} label={p.label} value={p.value} maxVal={100} color={p.color} delay={i * 150} />
          ))}
        </div>

        {/* Model Performance */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Ensemble Performance</span>
            <span className="live-badge" style={{ background: modelInfoData?.models_loaded ? 'rgba(6,255,165,0.1)' : 'rgba(255,71,87,0.1)', color: modelInfoData?.models_loaded ? '#06ffa5' : '#ff4757' }}>
              {modelInfoData?.models_loaded ? '● MODELS LIVE' : '✗ MODELS OFFLINE'}
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {(m.model_performance && m.model_performance.length > 0 ? m.model_performance : []).map((perf, i) => (
              <div key={i}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 13, color: '#9999bb' }}>{perf.name}</span>
                  <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 14, fontWeight: 600, color: perf.color }}>
                    <AnimatedNumber target={perf.value} suffix="%" color={perf.color} duration={1200} />
                  </span>
                </div>
                <div style={{ height: 4, borderRadius: 100, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', borderRadius: 100, background: perf.color,
                    width: `${perf.value}%`, transition: 'width 1.2s ease-out',
                    boxShadow: `0 0 8px ${perf.color}40`,
                  }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
