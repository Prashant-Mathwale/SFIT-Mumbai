import React, { useState, useEffect, useCallback, useRef } from 'react';
import { getInterventionLog, getCustomerDetail, triggerIntervention, recordIntervention } from '../api/client';
import Loader from './ui/Loader';

/* ═══════════════════════════════════════════
   OUTREACH PANEL — Intervention Hub v2.0
   KPI Command Strip + Slide-In Cards + Enhanced Preview
   ═══════════════════════════════════════════ */

function AnimatedNumber({ target, duration = 1200, color = 'var(--text-primary)' }) {
  const [val, setVal] = useState(0);
  const ref = useRef(null);
  useEffect(() => {
    let start = null;
    const step = (ts) => {
      if (!start) start = ts;
      const p = Math.min((ts - start) / duration, 1);
      const ease = 1 - Math.pow(1 - p, 3);
      setVal(ease * target);
      if (p < 1) ref.current = requestAnimationFrame(step);
    };
    ref.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(ref.current);
  }, [target, duration]);
  return <span style={{ color }}>{Math.round(val)}</span>;
}

export default function OutreachPanel({ seedCustomers = [] }) {
  const [queue, setQueue] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [channel, setChannel] = useState('SMS');
  const [message, setMessage] = useState('');
  const [interventionObj, setInterventionObj] = useState('');
  const [complianceApproved, setComplianceApproved] = useState(true);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQueue, setSearchQueue] = useState('');

  const buildQueueFromSeeds = useCallback((rows = []) => {
    if (!Array.isArray(rows) || rows.length === 0) return [];
    return rows
      .filter((c) => c?.intervention_eligible !== false)
      .slice(0, 24)
      .map((c) => ({
      customer_id: c.customer_id,
      week_number: 52,
      risk_score_at_trigger: c.risk_score || 0,
      intervention_type: 'PROACTIVE_OUTREACH',
      channel: 'SMS',
      status: 'PENDING',
      outcome: 'PENDING',
      top_signal: c.top_signal || ''
    }));
  }, []);

  const refreshQueue = useCallback(() => {
    getInterventionLog(1, 80).then(data => {
      const rows = Array.isArray(data) ? data : [];
      const pending = rows.filter(d => d.status === 'SENT' || d.status === 'DELIVERED' || d.outcome === 'PENDING');
      const fallback = buildQueueFromSeeds(seedCustomers);
      setQueue(pending.length > 0 ? pending : (rows.length > 0 ? rows.slice(0, 24) : fallback));
      setLoading(false);
    }).catch(() => {
      setQueue(buildQueueFromSeeds(seedCustomers));
      setLoading(false);
    });
  }, [buildQueueFromSeeds, seedCustomers]);

  useEffect(() => {
    setLoading(true);
    refreshQueue();
    const timer = setInterval(refreshQueue, 20000);
    return () => clearInterval(timer);
  }, [refreshQueue]);

  const handleSelect = async (item) => {
    setSelected(item);
    setSent(false);
    setMessage('Loading authorized outreach message from intervention AI...');
    setComplianceApproved(true);
    try {
      const res = await triggerIntervention(item.customer_id, item.week_number || 52);
      setMessage(res.outreach_message || 'Please reach out to us regarding your account.');
      setChannel(res.chosen_channel || 'SMS');
      setInterventionObj(res.chosen_intervention?.replace(/_/g, ' ') || 'Payment Restructuring');
      if (res.compliance_approved !== undefined) {
          setComplianceApproved(res.compliance_approved);
      }
      const d = await getCustomerDetail(item.customer_id);
      setDetail(d);
    } catch {
      setDetail(null);
      setMessage(`We care about your financial wellness. Our team is here to help with flexible repayment options. Please reach out to us.`);
    }
  };

  const handleSend = async () => {
    if (!selected) return;
    setSending(true);
    
    try {
      await recordIntervention({
        customer_id: selected.customer_id,
        week_number: selected.week_number || 52,
        risk_score_at_trigger: selected.risk_score_at_trigger,
        intervention_type: interventionObj.replace(/ /g, '_').toUpperCase(),
        channel: channel,
        top_signal: selected.top_signal || ""
      });
      
      setSending(false);
      setSent(true);
      addToast(`Intervention dispatched for ${selected.customer_id}`, 'success');
      setQueue(q => q.map(i => i.customer_id === selected.customer_id ? { ...i, status: 'SENT', outcome: 'PENDING' } : i));
    } catch (err) {
      setSending(false);
      addToast("Failed to record intervention. Please try again.", "error");
    }
  };

  const addToast = (text, type = 'success') => {
    const id = Date.now();
    setToasts(t => [...t.slice(-2), { id, text, type }]);
    setTimeout(() => setToasts(t => t.filter(toast => toast.id !== id)), 4000);
  };

  const filteredQueue = queue.filter(q =>
    !searchQueue || q.customer_id.toLowerCase().includes(searchQueue.toLowerCase())
  );

  const riskColor = (s) => s >= 0.70 ? 'var(--accent-red)' : s >= 0.40 ? 'var(--accent-orange)' : 'var(--accent-green)';
  const detailView = detail?.scored_details || detail || {};
  const accountView = detail?.account_info || {};

  const pendingCount = queue.filter(q => q.outcome === 'PENDING' || q.status === 'SENT').length;
  const sentCount = queue.filter(q => q.status === 'SENT' || q.status === 'DELIVERED').length;
  const criticalCount = queue.filter(q => q.risk_score_at_trigger >= 0.70).length;
  const resolvedCount = queue.filter(q => q.outcome === 'RECOVERED').length;

  if (loading) return <Loader message="ACCESSING COMMUNICATIONS GRID..." />;

  return (
    <div>
      <div className="page-header" style={{ animation: 'fadeSlideDown 500ms ease' }}>
        <div>
          <h1>Intervention Outreach Center</h1>
          <p className="subtitle">Review, edit, and dispatch AI-generated intervention messages</p>
        </div>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <span style={{ fontFamily: 'DM Mono', fontSize: 13, color: 'var(--accent-orange)' }}>● {pendingCount} Pending</span>
          <span style={{ fontFamily: 'DM Mono', fontSize: 13, color: 'var(--accent-cyan)' }}>● {sentCount} Sent</span>
          <span style={{ fontFamily: 'DM Mono', fontSize: 13, color: 'var(--accent-green)' }}>● {queue.filter(q => q.status === 'DELIVERED').length} Delivered</span>
        </div>
      </div>

      {/* Command Center KPI Strip */}
      <div className="kpi-strip" style={{ animation: 'fadeSlideUp 500ms 100ms ease both' }}>
        <div className="kpi-strip-tile">
          <div className="kpi-strip-value" style={{ color: 'var(--text-primary)' }}>
            <AnimatedNumber target={queue.length} color="var(--text-primary)" />
          </div>
          <div className="kpi-strip-label">Total Alerts</div>
        </div>
        <div className="kpi-strip-tile" style={{ border: '1px solid rgba(255,71,87,0.3)' }}>
          <div className="kpi-strip-value" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#ff4757', animation: 'dotBlink 1.2s infinite' }} />
            <AnimatedNumber target={criticalCount} color="var(--accent-red)" />
          </div>
          <div className="kpi-strip-label">Active Critical</div>
        </div>
        <div className="kpi-strip-tile">
          <div className="kpi-strip-value"><AnimatedNumber target={pendingCount} color="var(--accent-orange)" /></div>
          <div className="kpi-strip-label">Pending High</div>
        </div>
        <div className="kpi-strip-tile">
          <div className="kpi-strip-value"><AnimatedNumber target={resolvedCount} color="var(--accent-cyan)" /></div>
          <div className="kpi-strip-label">Resolved</div>
        </div>
        <div className="kpi-strip-tile">
          <div className="kpi-strip-value"><AnimatedNumber target={queue.length} color="var(--accent-green)" /></div>
          <div className="kpi-strip-label">Auto-Triggered</div>
        </div>
      </div>

      <div className="two-col outreach">
        {/* LEFT: Queue */}
        <div className="card" style={{ animation: 'fadeSlideRight 500ms ease', maxHeight: 'calc(100vh - 280px)', overflowY: 'auto', padding: 24 }}>
          <div className="card-header" style={{ marginBottom: 16 }}>
            <div>
              <span className="card-title" style={{ fontSize: 18 }}>Pending Outreach</span>
              <span style={{ marginLeft: 8, fontFamily: 'DM Mono', fontSize: 12, background: 'rgba(255,107,53,0.1)', color: 'var(--accent-orange)', padding: '2px 8px', borderRadius: 4 }}>
                <span style={{ animation: 'dotBlink 1.2s infinite' }}>●</span> {pendingCount} pending
              </span>
            </div>
          </div>

          <input className="search-input" style={{ width: '100%', marginBottom: 16, paddingLeft: 16 }} placeholder="Filter by customer ID..." value={searchQueue} onChange={e => setSearchQueue(e.target.value)} />

          {loading ? Array(5).fill(0).map((_, i) => (
            <div key={i} className="shimmer" style={{ height: 80, marginBottom: 8, borderRadius: 10 }}></div>
          )) : filteredQueue.map((item, i) => (
            <div key={`${item.customer_id}-${i}`}
              className={`queue-card ${selected?.customer_id === item.customer_id ? 'selected' : ''}`}
              onClick={() => handleSelect(item)}
              style={{
                animation: `slideInRight 400ms ease ${Math.min(i, 12) * 100}ms both`,
              }}>
              <div className="queue-card-row">
                <span className="cid">{item.customer_id}</span>
                <span style={{ fontFamily: 'DM Mono', fontSize: 12, padding: '2px 8px', borderRadius: 100, background: `${riskColor(item.risk_score_at_trigger)}20`, color: riskColor(item.risk_score_at_trigger) }}>
                  {(item.risk_score_at_trigger * 100).toFixed(0)}
                </span>
              </div>
              <div className="queue-card-row">
                <span className="intervention">{item.intervention_type?.replace(/_/g, ' ')}</span>
                <span className={`status-pill ${item.status?.toLowerCase()}`}>{item.status}</span>
              </div>
              <div className="queue-card-row">
                <span className="time">Week {item.week_number}</span>
                <span className="signal-pill">{(item.top_signal || '').replace(/_/g, ' ')}</span>
              </div>
              {/* Active badge for critical */}
              {item.risk_score_at_trigger >= 0.70 && (
                <div style={{
                  position: 'absolute', top: 8, right: 8, fontFamily: 'DM Mono', fontSize: 9,
                  padding: '2px 6px', borderRadius: 4,
                  background: 'rgba(255,71,87,0.1)', color: '#ff4757', border: '1px solid rgba(255,71,87,0.25)',
                  animation: 'dotBlink 2s infinite',
                }}>
                  ACTIVE
                </div>
              )}
            </div>
          ))}
        </div>

        {/* RIGHT: Preview */}
        <div className="card" style={{ animation: 'fadeSlideLeft 500ms 100ms ease both', padding: 32 }}>
          {!selected ? (
            <div className="empty-state">
              <span style={{ fontSize: 40, display: 'block', marginBottom: 16 }}>✉️</span>
              Select an alert from the queue to review AI-generated outreach.
            </div>
          ) : (
            <>
              {/* Customer Header */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 24 }}>
                <div style={{ width: 44, height: 44, borderRadius: '50%', background: 'linear-gradient(135deg, var(--accent-purple), var(--accent-cyan))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'DM Mono', fontSize: 14, color: 'white', fontWeight: 500 }}>
                  {(detailView?.name || accountView?.name || 'CU').slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <div style={{ fontFamily: 'var(--font-heading)', fontWeight: 600, fontSize: 20, color: 'var(--text-primary)' }}>{detailView?.name || accountView?.name || selected.customer_id}</div>
                  <div style={{ fontFamily: 'DM Mono', fontSize: 13, color: 'var(--text-secondary)' }}>{selected.customer_id}</div>
                </div>
                <span className={`risk-badge ${(detailView?.risk_level || 'MEDIUM').toLowerCase()}`} style={{ marginLeft: 'auto' }}>
                  {detailView?.risk_level || 'MEDIUM'}
                </span>
              </div>

              {detail && (
                <div style={{ display: 'flex', gap: 6, marginBottom: 20, flexWrap: 'wrap' }}>
                  {(detailView?.city || accountView?.city) && <span className="pill" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 100, padding: '4px 10px', fontFamily: 'DM Sans', fontSize: 12, color: 'var(--text-secondary)' }}>{detailView?.city || accountView?.city}</span>}
                  {(detailView?.occupation || accountView?.occupation) && <span className="pill" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 100, padding: '4px 10px', fontFamily: 'DM Sans', fontSize: 12, color: 'var(--text-secondary)' }}>{detailView?.occupation || accountView?.occupation}</span>}
                  {(detailView?.product_type || accountView?.product_type) && <span className="pill" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 100, padding: '4px 10px', fontFamily: 'DM Sans', fontSize: 12, color: 'var(--text-secondary)' }}>{detailView?.product_type || accountView?.product_type}</span>}
                </div>
              )}

              {/* Channel Switcher */}
              <div className="channel-switcher">
                {['SMS', 'Email', 'In-App'].map(ch => (
                  <button key={ch} className={`channel-btn ${channel === ch ? 'active' : ''}`} onClick={() => setChannel(ch)}>{ch}</button>
                ))}
              </div>

              {/* Intervention Type */}
              <div className="intervention-pill">{selected.intervention_type?.replace(/_/g, ' ')}</div>
              <div style={{ fontFamily: 'DM Sans', fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
                Recommended by LangGraph Agent · Risk Score {(selected.risk_score_at_trigger * 100).toFixed(0)}
              </div>

              {/* Message */}
              <textarea className="message-textarea" value={message} onChange={e => setMessage(e.target.value)} placeholder="Type your outreach message..." />
              <div className="char-counter" style={{ color: message.length > 160 && channel === 'SMS' ? 'var(--accent-red)' : message.length > 140 ? 'var(--accent-orange)' : 'var(--text-muted)' }}>
                {message.length}{channel === 'SMS' ? '/160' : '/500'} chars
                {message.length > 160 && channel === 'SMS' && ' ⚠ Exceeds SMS limit'}
              </div>

              {/* Compliance Badges */}
              <div className="compliance-row">
                <div className={`compliance-badge ${complianceApproved ? 'cyan' : 'red'}`}>
                  <span className="icon">{complianceApproved ? '🛡' : '⚠'}</span>
                  <div>
                    <div className="badge-title">{complianceApproved ? 'Policy Approved' : 'Compliance Warning'}</div>
                    <div className="badge-subtitle">{complianceApproved ? 'Supportive · Regulatory-compliant' : 'Message exceeds length or tone constraints'}</div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="action-buttons">
                <button className="btn-ghost">Edit Message</button>
                <button className="btn-ghost orange">Schedule for Later</button>
                <button className={`btn-primary ${sent ? 'success' : ''} ${sending ? 'loading' : ''}`} onClick={handleSend} disabled={sending || sent}>
                  {sending ? <span className="spinner"></span> : sent ? '✓ Dispatched Successfully' : 'Approve & Send Outreach'}
                </button>
              </div>

              {/* Intervention History */}
              <details style={{ marginTop: 24 }}>
                <summary style={{ fontFamily: 'DM Sans', fontSize: 14, color: 'var(--text-secondary)', cursor: 'pointer', padding: '8px 0' }}>
                  Previous Interventions ▾
                </summary>
                <div style={{ marginTop: 8 }}>
                  {queue.filter(q => q.customer_id === selected.customer_id).slice(0, 5).map((h, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: i % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent', borderRadius: 6, fontFamily: 'DM Mono', fontSize: 12 }}>
                      <span style={{ color: 'var(--text-muted)' }}>Week {h.week_number}</span>
                      <span style={{ color: 'var(--text-secondary)' }}>{h.intervention_type?.replace(/_/g, ' ')}</span>
                      <span className={`status-pill ${h.status?.toLowerCase()}`}>{h.status}</span>
                      <span style={{ color: h.outcome === 'RECOVERED' ? 'var(--accent-green)' : 'var(--text-muted)' }}>{h.outcome}</span>
                    </div>
                  ))}
                </div>
              </details>
            </>
          )}
        </div>
      </div>

      {/* Toasts */}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast ${toast.type}`}>
            <span style={{ fontSize: 18 }}>{toast.type === 'success' ? '✓' : '✗'}</span>
            <span className="toast-text">{toast.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
