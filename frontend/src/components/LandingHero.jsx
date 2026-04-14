import React, { useEffect, useRef } from 'react';
import { TextRevealCardPreview } from './ui/TextRevealCard';

/* ═══════════════════════════════════════════
   LANDING HERO — TextRevealCard + Neural BG
   Canvas 2D neural network (smooth, no lag)
   ═══════════════════════════════════════════ */

// ── Lightweight Canvas 2D Neural Network ──
function NeuralBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;
    let w, h;

    const PARTICLE_COUNT = 55;
    const MAX_DIST = 120;
    const particles = [];

    const resize = () => {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    // Init particles
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        r: 1.5 + Math.random() * 1.5,
        color: i % 2 === 0 ? 'rgba(6,182,212,' : 'rgba(99,102,241,',
      });
    }

    let frame = 0;

    const draw = () => {
      animId = requestAnimationFrame(draw);
      frame++;
      ctx.clearRect(0, 0, w, h);

      // Move particles
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = w;
        if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h;
        if (p.y > h) p.y = 0;
      }

      // Draw connections (every 2nd frame for perf)
      if (frame % 2 === 0) {
        for (let i = 0; i < PARTICLE_COUNT; i++) {
          for (let j = i + 1; j < PARTICLE_COUNT; j++) {
            const dx = particles[i].x - particles[j].x;
            const dy = particles[i].y - particles[j].y;
            const dist = dx * dx + dy * dy;
            if (dist < MAX_DIST * MAX_DIST) {
              const alpha = 1 - Math.sqrt(dist) / MAX_DIST;
              ctx.beginPath();
              ctx.strokeStyle = `rgba(6,182,212,${alpha * 0.12})`;
              ctx.lineWidth = 0.5;
              ctx.moveTo(particles[i].x, particles[i].y);
              ctx.lineTo(particles[j].x, particles[j].y);
              ctx.stroke();
            }
          }
        }
      }

      // Draw particles
      for (const p of particles) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.color + '0.6)';
        ctx.fill();

        // Glow
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * 3, 0, Math.PI * 2);
        ctx.fillStyle = p.color + '0.04)';
        ctx.fill();
      }
    };

    draw();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed', inset: 0, zIndex: 0,
        pointerEvents: 'none',
      }}
    />
  );
}

export default function LandingHero({ onEnterDashboard }) {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'flex-start',
      padding: '40px 24px',
      background: '#0a0a0f',
      position: 'relative',
    }}>
      <NeuralBackground />

      {/* Card wrapper — relative so it sits above canvas */}
      <div style={{ position: 'relative', zIndex: 1, width: '100%', maxWidth: 800, marginTop: '10vh' }}>
        <TextRevealCardPreview />
      </div>

      {/* CTA Button */}
      <button
        onClick={onEnterDashboard}
        style={{
          position: 'relative', zIndex: 1,
          marginTop: 40, padding: '14px 40px', borderRadius: 12,
          background: 'linear-gradient(135deg, #00d4ff, #6366F1)',
          border: 'none', color: '#0a0a0f', fontFamily: "'Syne', sans-serif",
          fontWeight: 700, fontSize: 16, cursor: 'pointer',
          transition: 'all 200ms', letterSpacing: '0.5px',
        }}
        onMouseEnter={(e) => { e.target.style.transform = 'translateY(-3px) scale(1.03)'; e.target.style.boxShadow = '0 12px 40px rgba(0,212,255,0.4)'; }}
        onMouseLeave={(e) => { e.target.style.transform = ''; e.target.style.boxShadow = ''; }}
      >
        Enter Risk Operations Center →
      </button>

      <section className="project-brief" style={{ position: 'relative', zIndex: 1 }}>
        <h2>Pre-Delinquency Intervention Engine</h2>
        <p>
          Banks lose recovery potential when intervention begins only after missed payments.
          This platform detects early stress signals 2-4 weeks in advance and enables timely,
          explainable, and empathetic outreach.
        </p>

        <div className="brief-grid">
          <article className="brief-card">
            <h3>Problem Statement</h3>
            <p>
              Traditional collections are reactive, expensive, and relationship-damaging.
              Institutions need an early-warning system that identifies distress before delinquency.
            </p>
          </article>

          <article className="brief-card">
            <h3>Challenge</h3>
            <p>
              Early stress signals are subtle and scattered across channels, accounts, and products.
              Banks need a unified predictive view with fair and explainable decisions.
            </p>
          </article>

          <article className="brief-card">
            <h3>Technology Stack</h3>
            <ul>
              <li>Open Source: LightGBM, XGBoost, scikit-learn, PyTorch, TensorFlow</li>
              <li>Realtime/Data: Feast, Airflow, Kafka, BentoML, MLflow</li>
              <li>AWS: SageMaker, Kinesis, Redshift, DynamoDB, SNS, QuickSight</li>
            </ul>
          </article>

          <article className="brief-card">
            <h3>Realtime Signals</h3>
            <ul>
              <li>Salary credited later than usual</li>
              <li>Savings balance drop week-over-week</li>
              <li>UPI transfers to lending apps spike</li>
              <li>Utility payment delays in billing cycle</li>
              <li>Discretionary spend drops, ATM withdrawals rise</li>
              <li>Failed auto-debit attempts</li>
            </ul>
          </article>

          <article className="brief-card">
            <h3>Design Considerations</h3>
            <ul>
              <li>Data analytics across multiple source systems</li>
              <li>Low-noise alerting and automation</li>
              <li>Scalable predictive modeling and orchestration</li>
              <li>Context-aware, cross-channel correlation</li>
              <li>Clear visualization for operations teams</li>
            </ul>
          </article>

          <article className="brief-card">
            <h3>What to Build</h3>
            <ul>
              <li>Realtime transaction pattern analysis</li>
              <li>Early-warning detection of financial stress</li>
              <li>Default risk forecast 2-4 weeks ahead</li>
              <li>Automated pre-delinquency intervention triggers</li>
            </ul>
          </article>
        </div>

        <article className="brief-card benefits">
          <h3>Expected Benefits</h3>
          <ul>
            <li>Reduced credit losses through earlier action</li>
            <li>Lower collections cost and manual overhead</li>
            <li>Higher recovery rates and portfolio performance</li>
            <li>Stronger customer trust with supportive outreach</li>
            <li>Regulatory alignment via fair, explainable treatment</li>
          </ul>
        </article>
      </section>
    </div>
  );
}
