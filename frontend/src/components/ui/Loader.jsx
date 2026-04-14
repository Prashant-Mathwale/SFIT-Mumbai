import React from 'react';

export default function Loader({ message = "LOADING DATA..." }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: 20 }}>
      {/* 2-ring neon spinner */}
      <div style={{ position: 'relative', width: 64, height: 64 }}>
        <div style={{
          position: 'absolute', inset: 0, borderRadius: '50%', border: '4px solid rgba(0,212,255,0.1)', borderTopColor: '#00d4ff',
          animation: 'spinRing 1s linear infinite'
        }}></div>
        <div style={{
          position: 'absolute', inset: 8, borderRadius: '50%', border: '4px solid rgba(6,255,165,0.1)', borderTopColor: '#06ffa5',
          animation: 'spinRing 1.5s linear infinite reverse'
        }}></div>
      </div>
      <div style={{ fontFamily: 'DM Mono', fontSize: 13, color: '#00d4ff', letterSpacing: 3, animation: 'livePulse 2s infinite' }}>{message}</div>
      <style>{`
        @keyframes spinRing { to { transform: rotate(360deg); } }
        @keyframes livePulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
      `}</style>
    </div>
  );
}
