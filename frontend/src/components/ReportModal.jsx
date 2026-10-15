import React from 'react';
import { X } from 'lucide-react';

export default function ReportModal({ report, onClose }) {
  if (!report) return null;

  const { ticker, action, confidence, date, result } = report;
  const confidencePct = Math.round((confidence || 0) <= 1 ? (confidence || 0) * 100 : confidence);
  const actionBadgeClass = (action || '').includes('BUY') ? 'badge-buy' : (action || '').includes('SELL') ? 'badge-sell' : 'badge-hold';

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(4, 5, 7, 0.85)',
      backdropFilter: 'blur(12px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }} onClick={onClose}>
      
      <div 
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-hover)',
          borderRadius: 'var(--radius-xl)',
          maxWidth: '840px',
          width: '100%',
          maxHeight: '90vh',
          overflowY: 'auto',
          padding: '32px',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.8)',
          position: 'relative'
        }}
        className="animate-fade-in"
      >
        
        {/* CLOSE BUTTON */}
        <button 
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid var(--border)',
            color: 'var(--text-secondary)',
            borderRadius: '50%',
            width: '36px',
            height: '36px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            transition: 'all 0.2s ease'
          }}
        >
          <X size={18} />
        </button>

        {/* HEADER */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '4px' }}>
            Analysis Report · {new Date(date).toLocaleString()}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <h2 style={{ fontSize: '2rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--orange-primary)' }}>
              {ticker}
            </h2>
            <span className={actionBadgeClass} style={{ fontSize: '0.9rem', padding: '6px 16px' }}>
              {action.replace(/_/g, ' ')}
            </span>
          </div>
        </div>

        {/* CONFIDENCE & REASONING */}
        <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '20px', marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-secondary)' }}>Signal Confidence</span>
            <span style={{ fontSize: '0.88rem', fontWeight: 800, color: 'var(--orange-light)', fontFamily: 'var(--font-mono)' }}>{confidencePct}%</span>
          </div>
          <div style={{ width: '100%', height: '8px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ width: `${confidencePct}%`, height: '100%', background: 'var(--gradient-orange-red)', transition: 'width 0.5s ease' }} />
          </div>
          {result?.reasoning && (
            <p style={{ marginTop: '16px', fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
              {result.reasoning}
            </p>
          )}
        </div>

        {/* ANALYST BREAKDOWN */}
        {result?.analyst_report && (
          <div style={{ marginBottom: '24px' }}>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: '12px' }}>
              Analyst Team Breakdown
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '12px' }}>
              {[
                { title: 'News Analyst', sig: result.analyst_report.news_signal, reason: result.analyst_report.news_reasoning },
                { title: 'Fundamentals Analyst', sig: result.analyst_report.fundamentals_signal, reason: result.analyst_report.fundamentals_reasoning },
                { title: 'Sentiment Analyst', sig: result.analyst_report.sentiment_signal, reason: result.analyst_report.sentiment_reasoning },
                { title: 'Technical Analyst', sig: result.analyst_report.technical_signal, reason: result.analyst_report.technical_reasoning },
              ].filter(a => a.sig && a.sig !== 'N/A').map((analyst, i) => (
                <div key={i} style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '14px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>{analyst.title}</span>
                    <span className={analyst.sig.includes('BUY') ? 'badge-buy' : analyst.sig.includes('SELL') ? 'badge-sell' : 'badge-hold'}>
                      {analyst.sig.replace(/_/g, ' ')}
                    </span>
                  </div>
                  {analyst.reason && (
                    <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                      {analyst.reason.slice(0, 180)}…
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* BULL VS BEAR RESEARCH */}
        {result?.research_report && (
          <div style={{ marginBottom: '24px' }}>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: '12px' }}>
              Research Case Debate
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              {result.research_report.bull_case_summary && (
                <div style={{ background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: 'var(--radius-md)', padding: '16px' }}>
                  <div style={{ color: 'var(--green)', fontWeight: 700, fontSize: '0.85rem', marginBottom: '6px' }}>🐂 Bull Case</div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{result.research_report.bull_case_summary}</div>
                </div>
              )}
              {result.research_report.bear_case_summary && (
                <div style={{ background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: 'var(--radius-md)', padding: '16px' }}>
                  <div style={{ color: 'var(--red)', fontWeight: 700, fontSize: '0.85rem', marginBottom: '6px' }}>🐻 Bear Case</div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{result.research_report.bear_case_summary}</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ACTION BUTTON */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
          <button onClick={onClose} className="btn-white">
            Close Report
          </button>
        </div>

      </div>
    </div>
  );
}
