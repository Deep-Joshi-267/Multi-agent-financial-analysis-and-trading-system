import React, { useState } from 'react';
import { Search, Trash2, Clock, Calendar, ArrowUpRight } from 'lucide-react';

export default function PastAnalysisTab({ pastAnalyses, onClearHistory, onSelectReport }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterAction, setFilterAction] = useState('ALL');

  const filteredAnalyses = pastAnalyses.filter((item) => {
    const matchesSearch = item.ticker.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter =
      filterAction === 'ALL' ||
      (filterAction === 'BUY' && item.action?.includes('BUY')) ||
      (filterAction === 'HOLD' && item.action?.includes('HOLD')) ||
      (filterAction === 'SELL' && item.action?.includes('SELL'));
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="animate-fade-in" style={{ maxWidth: '1100px', margin: '0 auto', padding: '24px 20px 60px' }}>
      
      {/* HEADER BAR */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Past Analyses History</h1>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
            Complete archive of all previous AI trading analysis runs
          </p>
        </div>

        {pastAnalyses.length > 0 && (
          <button 
            onClick={onClearHistory}
            className="btn-secondary"
            style={{ color: 'var(--red)', borderColor: 'rgba(239, 68, 68, 0.3)' }}
          >
            <Trash2 size={16} /> Clear History
          </button>
        )}
      </div>

      {/* FILTER & SEARCH BAR */}
      <div style={{
        display: 'flex',
        gap: '16px',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '24px'
      }}>
        {/* Search Input */}
        <div style={{ position: 'relative', flex: 1, minWidth: '240px' }}>
          <Search size={18} color="var(--text-muted)" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            placeholder="Search symbol (e.g. RELIANCE, TCS)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              padding: '12px 14px 12px 42px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-md)',
              color: '#ffffff',
              fontSize: '0.9rem',
              outline: 'none',
              fontFamily: 'var(--font-mono)'
            }}
          />
        </div>

        {/* Filter Pills */}
        <div style={{ display: 'flex', gap: '6px', background: 'rgba(255, 255, 255, 0.04)', padding: '4px', borderRadius: '99px', border: '1px solid var(--border)' }}>
          {['ALL', 'BUY', 'HOLD', 'SELL'].map((f) => (
            <button
              key={f}
              onClick={() => setFilterAction(f)}
              style={{
                background: filterAction === f ? 'var(--gradient-orange-red)' : 'transparent',
                color: filterAction === f ? '#ffffff' : 'var(--text-muted)',
                border: 'none',
                padding: '6px 16px',
                borderRadius: '99px',
                fontSize: '0.78rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* ANALYSES GRID */}
      {filteredAnalyses.length === 0 ? (
        <div className="glass-card" style={{ textAlign: 'center', padding: '60px 24px' }}>
          <Clock size={40} color="var(--text-muted)" style={{ marginBottom: '16px' }} />
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '8px' }}>No Past Analyses Found</h3>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
            {pastAnalyses.length === 0 ? 'You have not run any stock analysis yet.' : 'No analyses match your search criteria.'}
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
          {filteredAnalyses.map((item, index) => {
            const badgeClass = item.action?.includes('BUY') ? 'badge-buy' : item.action?.includes('SELL') ? 'badge-sell' : 'badge-hold';
            const confidencePct = Math.round((item.confidence || 0) <= 1 ? (item.confidence || 0) * 100 : item.confidence);

            return (
              <div key={index} className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.4rem', fontWeight: 800, color: 'var(--orange-primary)' }}>
                      {item.ticker}
                    </div>
                    <span className={badgeClass}>{item.action?.replace(/_/g, ' ')}</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '14px' }}>
                    <Calendar size={14} />
                    <span>{new Date(item.date).toLocaleString()}</span>
                  </div>

                  <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', marginBottom: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                      <span>Confidence</span>
                      <span style={{ fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--orange-light)' }}>{confidencePct}%</span>
                    </div>
                    <div style={{ width: '100%', height: '4px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ width: `${confidencePct}%`, height: '100%', background: 'var(--gradient-orange-red)' }} />
                    </div>
                  </div>

                  {item.result?.reasoning && (
                    <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '20px' }}>
                      {item.result.reasoning.slice(0, 120)}…
                    </p>
                  )}
                </div>

                <button 
                  onClick={() => onSelectReport(item)} 
                  className="btn-white" 
                  style={{ width: '100%', justifyContent: 'center', fontSize: '0.85rem' }}
                >
                  View Full Analysis <ArrowUpRight size={16} />
                </button>
              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}
