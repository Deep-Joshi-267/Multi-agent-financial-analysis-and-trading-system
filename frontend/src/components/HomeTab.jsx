import React from 'react';
import { Clock, Sparkles, TrendingUp, Cpu, ArrowRight, Zap, Award } from 'lucide-react';

export default function HomeTab({ setActiveTab, pastAnalyses, onSelectReport }) {
  const recentAnalyses = pastAnalyses.slice(0, 3);

  return (
    <div className="animate-fade-in" style={{ paddingBottom: '60px' }}>
      
      {/* ── HERO SECTION ──────────────────────────────────────────────── */}
      <section style={{
        position: 'relative',
        padding: '60px 0 40px',
        textAlign: 'center',
        background: 'radial-gradient(circle at 50% 20%, rgba(255, 87, 34, 0.12) 0%, transparent 60%)'
      }}>
        <div style={{ maxWidth: '840px', margin: '0 auto', padding: '0 20px' }}>
          
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(255, 87, 34, 0.1)',
            border: '1px solid rgba(255, 87, 34, 0.3)',
            padding: '6px 16px',
            borderRadius: '99px',
            fontSize: '0.82rem',
            fontWeight: 700,
            color: 'var(--orange-light)',
            marginBottom: '24px'
          }}>
            <Sparkles size={14} color="var(--orange-primary)" />
            <span>Powered by LangGraph + Groq LLM (`qwen/qwen3.8-27b`)</span>
          </div>

          <h1 style={{
            fontSize: 'clamp(2.5rem, 5vw, 4rem)',
            fontWeight: 800,
            lineHeight: 1.1,
            letterSpacing: '-0.03em',
            marginBottom: '20px'
          }}>
            Multi-Agent <br />
            <span style={{
              background: 'var(--gradient-orange-red)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              Financial Intelligence System
            </span>
          </h1>

          <p style={{
            fontSize: '1.1rem',
            color: 'var(--text-secondary)',
            lineHeight: 1.6,
            marginBottom: '36px',
            maxWidth: '680px',
            margin: '0 auto 36px'
          }}>
            5 specialised AI agents collaborate to fetch real-time market data, scrape Indian financial news, execute technical analysis, and formulate risk-managed trading decisions.
          </p>

          <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', flexWrap: 'wrap' }}>
            <button 
              onClick={() => setActiveTab('analysis')} 
              className="btn-orange"
              style={{ padding: '14px 32px', fontSize: '1rem' }}
            >
              <Zap size={18} />
              <span>Start New Analysis</span>
            </button>

            <button 
              onClick={() => setActiveTab('past')} 
              className="btn-white"
              style={{ padding: '14px 28px' }}
            >
              <Clock size={18} />
              <span>View Past Analysis</span>
            </button>
          </div>

        </div>
      </section>

      {/* ── KEY METRICS BAR ───────────────────────────────────────────── */}
      <section style={{ maxWidth: '1100px', margin: '0 auto 48px', padding: '0 20px' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '16px',
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-xl)',
          padding: '24px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'rgba(255, 87, 34, 0.1)', display: 'flex', alignItems: 'center', justify: 'center' }}>
              <Cpu size={22} color="var(--orange-primary)" />
            </div>
            <div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>5 Specialized</div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>AI Analyst Agents</div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'rgba(16, 185, 129, 0.1)', display: 'flex', alignItems: 'center', justify: 'center' }}>
              <TrendingUp size={22} color="var(--green)" />
            </div>
            <div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>NSE / BSE</div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Indian Stock Market</div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'rgba(255, 107, 0, 0.1)', display: 'flex', alignItems: 'center', justify: 'center' }}>
              <Award size={22} color="var(--orange-bright)" />
            </div>
            <div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>100% Real-Time</div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>SSE Streaming Pipeline</div>
            </div>
          </div>
        </div>
      </section>

      {/* ── RECENT ANALYSIS (PAST 3 ANALYSIS) ───────────────────────── */}
      <section style={{ maxWidth: '1100px', margin: '0 auto 60px', padding: '0 20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '20px' }}>
          <div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Recent Analysis</h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Past 3 analyses executed in this session</p>
          </div>
          <button 
            onClick={() => setActiveTab('past')}
            className="btn-secondary"
            style={{ fontSize: '0.82rem' }}
          >
            View All ({pastAnalyses.length}) <ArrowRight size={14} />
          </button>
        </div>

        {recentAnalyses.length === 0 ? (
          <div className="glass-card" style={{ textAlign: 'center', padding: '48px 24px' }}>
            <Clock size={36} color="var(--text-muted)" style={{ marginBottom: '12px' }} />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '6px' }}>No Recent Analysis Yet</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '20px' }}>
              Run your first AI stock analysis to populate history.
            </p>
            <button onClick={() => setActiveTab('analysis')} className="btn-orange">
              <Zap size={16} /> Run Analysis Now
            </button>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
            {recentAnalyses.map((item, index) => {
              const badgeClass = item.action?.includes('BUY') ? 'badge-buy' : item.action?.includes('SELL') ? 'badge-sell' : 'badge-hold';
              return (
                <div 
                  key={index}
                  className="glass-card"
                  style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
                >
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.3rem', fontWeight: 800, color: 'var(--orange-primary)' }}>
                        {item.ticker}
                      </span>
                      <span className={badgeClass}>{item.action?.replace(/_/g, ' ')}</span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                      Executed: {new Date(item.date).toLocaleString()}
                    </div>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '16px' }}>
                      {item.result?.reasoning ? `${item.result.reasoning.slice(0, 110)}…` : 'Analysis completed successfully.'}
                    </p>
                  </div>

                  <button 
                    onClick={() => onSelectReport(item)}
                    className="btn-white"
                    style={{ width: '100%', justifyContent: 'center', fontSize: '0.85rem', padding: '10px' }}
                  >
                    View Report Details
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* ── AGENT ARCHITECTURE PREVIEW ─────────────────────────────────── */}
      <section style={{ maxWidth: '1100px', margin: '0 auto', padding: '0 20px' }}>
        <h2 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: '20px', textAlign: 'center' }}>
          Collaborative AI Agent Architecture
        </h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          {[
            { title: 'News Analyst', desc: 'Scrapes Google News RSS for Indian stock sentiment & SEBI updates.', icon: '📰' },
            { title: 'Fundamentals Analyst', desc: 'Evaluates P/E ratios, EPS, market cap & quarterly metrics.', icon: '📊' },
            { title: 'Sentiment Analyst', desc: 'Processes market sentiment, trader discussions & news context.', icon: '💬' },
            { title: 'Technical Analyst', desc: 'Computes RSI(14), 5d/20d Momentum, SMA 20/50 & MACD.', icon: '📈' },
            { title: 'Risk Manager', desc: 'Ensures capital protection with stop loss & position sizing rules.', icon: '🛡️' }
          ].map((agent, i) => (
            <div key={i} className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '2rem', marginBottom: '10px' }}>{agent.icon}</div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '6px' }}>{agent.title}</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>{agent.desc}</p>
            </div>
          ))}
        </div>
      </section>

    </div>
  );
}
