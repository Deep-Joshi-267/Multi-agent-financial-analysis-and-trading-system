import React, { useState, useEffect, useRef } from 'react';
import { Search, Zap, Terminal } from 'lucide-react';
import PriceChart from './PriceChart';

const POPULAR_TICKERS = [
  { symbol: 'RELIANCE.NS', name: 'Reliance Industries' },
  { symbol: 'TCS.NS', name: 'Tata Consultancy Services' },
  { symbol: 'INFY.NS', name: 'Infosys Ltd.' },
  { symbol: 'HDFCBANK.NS', name: 'HDFC Bank' },
  { symbol: 'TATAMOTORS.NS', name: 'Tata Motors' },
  { symbol: 'AAPL', name: 'Apple Inc.' },
  { symbol: 'MSFT', name: 'Microsoft Corp.' },
  { symbol: 'NVDA', name: 'NVIDIA Corp.' },
];

export default function AnalysisTab({ onAnalysisComplete }) {
  const [ticker, setTicker] = useState('RELIANCE.NS');
  const [selectedChartSymbol, setSelectedChartSymbol] = useState('RELIANCE.NS');
  const [capital, setCapital] = useState(100000);
  const [risk, setRisk] = useState('moderate');
  const [quickMode, setQuickMode] = useState(false); // DEFAULT FALSE FOR FULL 5-STAGE PIPELINE
  
  const [quotePreview, setQuotePreview] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  
  const [isRunning, setIsRunning] = useState(false);
  const [logMessages, setLogMessages] = useState([]);
  const [stagesStatus, setStagesStatus] = useState({
    data: 'idle',
    analysts: 'idle',
    researchers: 'idle',
    cio: 'idle',
    traders: 'idle'
  });
  const [finalResult, setFinalResult] = useState(null);

  const eventSourceRef = useRef(null);
  const logEndRef = useRef(null);

  // Quote preview debouncer
  useEffect(() => {
    if (!ticker || ticker.length < 2) {
      const resetTimer = setTimeout(() => setQuotePreview(null), 0);
      return () => clearTimeout(resetTimer);
    }
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/quote/${encodeURIComponent(ticker.toUpperCase())}`);
        const data = await res.json();
        if (!data.error) setQuotePreview(data);
        else setQuotePreview(null);
      } catch {
        setQuotePreview(null);
      }
    }, 600);
    return () => clearTimeout(timer);
  }, [ticker]);

  // Scroll log terminal automatically
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logMessages]);

  const handleSelectTicker = (sym) => {
    const norm = sym.toUpperCase();
    setTicker(norm);
    setSelectedChartSymbol(norm);
    setSuggestions([]);
  };

  const handleInputChange = (e) => {
    const val = e.target.value.toUpperCase();
    setTicker(val);
    if (val.trim()) {
      const hits = POPULAR_TICKERS.filter(t => t.symbol.includes(val) || t.name.toUpperCase().includes(val));
      setSuggestions(hits);
    } else {
      setSuggestions([]);
    }
  };

  const startAnalysis = async () => {
    const targetTicker = ticker.trim().toUpperCase();
    if (!targetTicker) return;

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    setSelectedChartSymbol(targetTicker);
    setIsRunning(true);
    setFinalResult(null);
    setLogMessages([{ 
      time: new Date().toLocaleTimeString(), 
      msg: `Initiating ${quickMode ? 'quick (2-stage)' : 'full (5-stage)'} multi-agent analysis for ${targetTicker}…`, 
      type: 'info' 
    }]);

    setStagesStatus({
      data: 'running',
      analysts: 'idle',
      researchers: quickMode ? 'skipped' : 'idle',
      cio: quickMode ? 'skipped' : 'idle',
      traders: quickMode ? 'skipped' : 'idle'
    });

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker: targetTicker, capital: parseFloat(capital) || 100000, risk, quick: quickMode })
      });
      const data = await res.json();
      if (data.error) {
        addLog(`Error: ${data.error}`, 'err');
        setIsRunning(false);
        return;
      }
      listenToStream(data.job_id, targetTicker);
    } catch (err) {
      addLog(`Failed to connect to backend: ${err.message}`, 'err');
      setIsRunning(false);
    }
  };

  const addLog = (msg, type = '') => {
    setLogMessages(prev => [...prev, { time: new Date().toLocaleTimeString(), msg, type }]);
  };

  const listenToStream = (jobId, targetTicker) => {
    const es = new EventSource(`/api/stream/${jobId}`);
    eventSourceRef.current = es;

    es.onmessage = (e) => {
      if (e.data === '[DONE]') {
        es.close();
        setIsRunning(false);
        return;
      }
      try {
        const evt = JSON.parse(e.data);
        if (evt.stage === 'heartbeat') return;

        addLog(evt.message, evt.status === 'done' ? 'ok' : evt.status === 'error' ? 'err' : '');

        if (evt.stage && evt.stage !== 'complete' && evt.stage !== 'heartbeat') {
          setStagesStatus(prev => ({
            ...prev,
            [evt.stage]: evt.status
          }));
        }

        if (evt.stage === 'complete' && evt.data?.result) {
          const resObj = evt.data.result;
          setFinalResult(resObj);
          
          // Save to history state & localStorage
          const newRecord = {
            ticker: targetTicker,
            action: resObj.action || 'HOLD',
            confidence: resObj.confidence || 0.5,
            date: new Date().toISOString(),
            result: resObj
          };
          onAnalysisComplete(newRecord);
        }
      } catch {
        // Heartbeat or parse error
      }
    };

    es.onerror = () => {
      addLog('Stream connection closed.', 'err');
      setIsRunning(false);
      es.close();
    };
  };

  return (
    <div className="animate-fade-in" style={{ maxWidth: '1180px', margin: '0 auto', padding: '24px 20px 60px' }}>
      
      {/* ── ANALYSIS PARAMETERS CARD ─────────────────────────────────── */}
      <div className="glass-card" style={{ marginBottom: '28px', border: '1px solid var(--border-hover)' }}>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>AI Analysis Studio</h2>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Full 5-Agent Pipeline for Indian Stocks (NSE / BSE)
            </p>
          </div>

          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', background: 'rgba(255,255,255,0.04)', padding: '8px 16px', borderRadius: '99px', border: '1px solid var(--border)' }}>
            <input 
              type="checkbox" 
              checked={quickMode} 
              onChange={(e) => setQuickMode(e.target.checked)} 
              style={{ accentColor: 'var(--orange-primary)', width: '16px', height: '16px' }}
            />
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: quickMode ? 'var(--orange-light)' : 'var(--text-secondary)' }}>
              Quick Mode (Fast 2-Stage Analysis)
            </span>
          </label>
        </div>

        {/* INPUT FORM ROW */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '20px' }}>
          
          {/* Ticker Input */}
          <div style={{ position: 'relative' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
              Stock Symbol
            </label>
            <div style={{ position: 'relative' }}>
              <Search size={16} color="var(--orange-primary)" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                value={ticker}
                onChange={handleInputChange}
                onKeyDown={(e) => e.key === 'Enter' && startAnalysis()}
                placeholder="RELIANCE.NS, TCS.NS, AAPL…"
                style={{
                  width: '100%',
                  padding: '12px 14px 12px 42px',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  color: '#ffffff',
                  fontSize: '0.95rem',
                  fontWeight: 700,
                  fontFamily: 'var(--font-mono)',
                  outline: 'none'
                }}
              />
            </div>
            {/* Auto suggestions */}
            {suggestions.length > 0 && (
              <div style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                background: 'var(--bg-card)',
                border: '1px solid var(--border-hover)',
                borderRadius: 'var(--radius-md)',
                zIndex: 20,
                marginTop: '4px',
                overflow: 'hidden',
                boxShadow: '0 10px 30px rgba(0,0,0,0.8)'
              }}>
                {suggestions.map((item, i) => (
                  <div
                    key={i}
                    onClick={() => handleSelectTicker(item.symbol)}
                    style={{
                      padding: '10px 14px',
                      cursor: 'pointer',
                      display: 'flex',
                      justify: 'space-between',
                      borderBottom: '1px solid rgba(255,255,255,0.04)',
                      fontSize: '0.85rem'
                    }}
                  >
                    <span style={{ fontWeight: 700, color: 'var(--orange-light)', fontFamily: 'var(--font-mono)' }}>{item.symbol}</span>
                    <span style={{ color: 'var(--text-muted)' }}>{item.name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Capital Input */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
              Capital (INR / USD)
            </label>
            <input
              type="number"
              value={capital}
              onChange={(e) => setCapital(e.target.value)}
              style={{
                width: '100%',
                padding: '12px 14px',
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                color: '#ffffff',
                fontSize: '0.95rem',
                fontFamily: 'var(--font-mono)',
                outline: 'none'
              }}
            />
          </div>

          {/* Risk Selector */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
              Risk Tolerance
            </label>
            <select
              value={risk}
              onChange={(e) => setRisk(e.target.value)}
              style={{
                width: '100%',
                padding: '12px 14px',
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                color: '#ffffff',
                fontSize: '0.9rem',
                fontWeight: 600,
                outline: 'none'
              }}
            >
              <option value="conservative">Conservative</option>
              <option value="moderate">Moderate</option>
              <option value="aggressive">Aggressive</option>
            </select>
          </div>

        </div>

        {/* POPULAR CHIPS & ACTION BUTTON */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>Popular:</span>
            {POPULAR_TICKERS.map((t, i) => (
              <button
                key={i}
                onClick={() => handleSelectTicker(t.symbol)}
                style={{
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-secondary)',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontFamily: 'var(--font-mono)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                {t.symbol.replace('.NS', '')}
              </button>
            ))}
          </div>

          <button 
            onClick={startAnalysis}
            disabled={isRunning}
            className="btn-orange"
            style={{ opacity: isRunning ? 0.7 : 1, padding: '12px 32px' }}
          >
            <Zap size={18} />
            <span>{isRunning ? 'Analyzing…' : `Analyse Stock (${quickMode ? 'Quick' : 'Full 5-Stage'})`}</span>
          </button>

        </div>

        {/* QUICK QUOTE PREVIEW */}
        {quotePreview && (
          <div style={{
            marginTop: '20px',
            background: 'rgba(255, 87, 34, 0.04)',
            border: '1px solid rgba(255, 87, 34, 0.2)',
            borderRadius: 'var(--radius-md)',
            padding: '16px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1.1rem', color: 'var(--orange-primary)' }}>
                  {quotePreview.symbol}
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginLeft: '8px' }}>
                  {quotePreview.name} · {quotePreview.sector}
                </span>
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1.2rem' }}>
                Rs. {quotePreview.price ? quotePreview.price.toFixed(2) : '—'}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '8px' }}>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '6px 10px', borderRadius: '4px' }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>RSI (14)</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.85rem' }}>{quotePreview.rsi ? quotePreview.rsi.toFixed(1) : '—'}</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '6px 10px', borderRadius: '4px' }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>5d Momentum</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.85rem' }}>{quotePreview.momentum ? `${quotePreview.momentum.toFixed(2)}%` : '—'}</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '6px 10px', borderRadius: '4px' }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>P/E Ratio</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.85rem' }}>{quotePreview.pe_ratio ? quotePreview.pe_ratio.toFixed(1) : '—'}</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '6px 10px', borderRadius: '4px' }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>SMA 20</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.85rem' }}>{quotePreview.sma_20 ? quotePreview.sma_20.toFixed(1) : '—'}</div>
              </div>
            </div>
          </div>
        )}

      </div>

      {/* ── LIVE PRICE CHART ────────────────────────────────────────── */}
      {selectedChartSymbol && <PriceChart symbol={selectedChartSymbol} />}

      {/* ── LIVE PIPELINE TRACKER & TERMINAL LOG ─────────────────────── */}
      {(isRunning || logMessages.length > 0) && (
        <div className="glass-card" style={{ marginTop: '24px' }}>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Terminal size={18} color="var(--orange-primary)" />
              <h3 style={{ fontSize: '1rem', fontWeight: 800 }}>Pipeline Execution Stream (5-Stage Architecture)</h3>
            </div>
            {isRunning && (
              <span style={{ fontSize: '0.78rem', color: 'var(--green)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--green)', animation: 'pulseDot 1.2s infinite' }} />
                Streaming Live Events
              </span>
            )}
          </div>

          {/* STAGES TRACK - ALL 5 STAGES VISIBLE & TRACKED */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px', marginBottom: '16px' }}>
            {[
              { id: 'data', label: 'Data Ingestion' },
              { id: 'analysts', label: 'Analyst Team' },
              { id: 'researchers', label: 'Researchers' },
              { id: 'cio', label: 'CIO Decision' },
              { id: 'traders', label: 'Trader Execution' }
            ].map((st) => {
              const stVal = stagesStatus[st.id] || 'idle';
              const isDone = stVal === 'done';
              const isRun = stVal === 'running';
              const isSkip = stVal === 'skipped';
              const isErr = stVal === 'error';

              return (
                <div 
                  key={st.id}
                  style={{
                    background: isDone ? 'rgba(16, 185, 129, 0.12)' : isRun ? 'rgba(255, 87, 34, 0.2)' : isErr ? 'rgba(239, 68, 68, 0.15)' : 'rgba(255,255,255,0.03)',
                    border: `1px solid ${isDone ? 'rgba(16, 185, 129, 0.4)' : isRun ? 'var(--orange-primary)' : isErr ? 'var(--red)' : 'var(--border)'}`,
                    borderRadius: 'var(--radius-sm)',
                    padding: '10px 12px',
                    fontSize: '0.8rem',
                    fontWeight: 700,
                    opacity: isSkip ? 0.4 : 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}
                >
                  <span style={{ color: isRun ? 'var(--orange-light)' : isDone ? 'var(--green)' : 'var(--text-secondary)' }}>
                    {st.label}
                  </span>
                  <span style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: isDone ? 'var(--green)' : isRun ? 'var(--orange-primary)' : isErr ? 'var(--red)' : '#475569',
                    boxShadow: isRun ? '0 0 8px var(--orange-primary)' : isDone ? '0 0 8px var(--green)' : 'none'
                  }} />
                </div>
              );
            })}
          </div>

          {/* LOG BODY */}
          <div style={{
            background: '#07080a',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-md)',
            padding: '14px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.8rem',
            maxHeight: '220px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px'
          }}>
            {logMessages.map((log, index) => (
              <div key={index} style={{ display: 'flex', gap: '10px', color: log.type === 'err' ? 'var(--red)' : log.type === 'ok' ? 'var(--green)' : 'var(--text-secondary)' }}>
                <span style={{ color: 'var(--text-muted)' }}>[{log.time}]</span>
                <span>{log.msg}</span>
              </div>
            ))}
            <div ref={logEndRef} />
          </div>

        </div>
      )}

      {/* ── FINAL ANALYSIS RESULT DASHBOARD ───────────────────────────── */}
      {finalResult && (
        <div style={{ marginTop: '28px' }} className="animate-fade-in">
          
          {/* DECISION CARD */}
          <div className="glass-card" style={{ border: '1px solid var(--border-hover)', marginBottom: '24px' }}>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>
              Final AI Trading Recommendation
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
              <span className={finalResult.action?.includes('BUY') ? 'badge-buy' : finalResult.action?.includes('SELL') ? 'badge-sell' : 'badge-hold'} style={{ fontSize: '1.2rem', padding: '8px 24px' }}>
                {finalResult.action?.replace(/_/g, ' ')}
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.2rem', fontWeight: 800 }}>
                Confidence: {Math.round((finalResult.confidence || 0) * 100)}%
              </span>
            </div>

            {finalResult.reasoning && (
              <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                {finalResult.reasoning}
              </p>
            )}
          </div>

          {/* ANALYST CARDS BREAKDOWN */}
          {finalResult.analyst_report && (
            <div style={{ marginBottom: '24px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '16px' }}>Analyst Team Consensus</h3>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
                {[
                  { name: 'News Analyst', sig: finalResult.analyst_report.news_signal, conf: finalResult.analyst_report.news_confidence, reason: finalResult.analyst_report.news_reasoning },
                  { name: 'Fundamentals Analyst', sig: finalResult.analyst_report.fundamentals_signal, conf: finalResult.analyst_report.fundamentals_confidence, reason: finalResult.analyst_report.fundamentals_reasoning },
                  { name: 'Sentiment Analyst', sig: finalResult.analyst_report.sentiment_signal, conf: finalResult.analyst_report.sentiment_confidence, reason: finalResult.analyst_report.sentiment_reasoning },
                  { name: 'Technical Analyst', sig: finalResult.analyst_report.technical_signal, conf: finalResult.analyst_report.technical_confidence, reason: finalResult.analyst_report.technical_reasoning },
                ].map((an, i) => (
                  <div key={i} className="glass-card" style={{ padding: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.88rem' }}>{an.name}</span>
                      <span className={an.sig?.includes('BUY') ? 'badge-buy' : an.sig?.includes('SELL') ? 'badge-sell' : 'badge-hold'}>
                        {an.sig?.replace(/_/g, ' ') || 'HOLD'}
                      </span>
                    </div>
                    {an.reason && (
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                        {an.reason.slice(0, 160)}…
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* RESEARCH CASE DEBATE (FULL MODE STAGE 3) */}
          {finalResult.research_report && (
            <div style={{ marginBottom: '24px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '16px' }}>Research Case Debate (Bull vs Bear)</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                {finalResult.research_report.bull_case_summary && (
                  <div style={{ background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: 'var(--radius-md)', padding: '16px' }}>
                    <div style={{ color: 'var(--green)', fontWeight: 700, fontSize: '0.9rem', marginBottom: '6px' }}>🐂 Bull Case</div>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{finalResult.research_report.bull_case_summary}</p>
                  </div>
                )}
                {finalResult.research_report.bear_case_summary && (
                  <div style={{ background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: 'var(--radius-md)', padding: '16px' }}>
                    <div style={{ color: 'var(--red)', fontWeight: 700, fontSize: '0.9rem', marginBottom: '6px' }}>🐻 Bear Case</div>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{finalResult.research_report.bear_case_summary}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TRADE EXECUTION PLAN (FULL MODE STAGE 5) */}
          {finalResult.trade_execution && finalResult.trade_execution.action && (
            <div className="glass-card" style={{ marginBottom: '24px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '16px' }}>Trader Execution Plan</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Order Type</div>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{finalResult.trade_execution.order_type || 'MARKET'}</div>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Quantity</div>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{finalResult.trade_execution.quantity || 'N/A'}</div>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Entry Price</div>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--orange-light)' }}>
                    Rs. {finalResult.trade_execution.entry_price ? finalResult.trade_execution.entry_price.toFixed(2) : 'Market'}
                  </div>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Status</div>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--green)' }}>{finalResult.trade_execution.status || 'PLANNED'}</div>
                </div>
              </div>
            </div>
          )}

        </div>
      )}

    </div>
  );
}
