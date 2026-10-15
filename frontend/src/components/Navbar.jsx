import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, Flame, Clock, BarChart3, Newspaper } from 'lucide-react';

export default function Navbar({ runningState }) {
  const [apiStatus, setApiStatus] = useState({ ok: false, text: 'Checking API...' });
  const location = useLocation();

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('/api/health');
        const data = await res.json();
        if (data.groq_configured) {
          setApiStatus({ ok: true, text: 'Groq LLM Active' });
        } else {
          setApiStatus({ ok: false, text: 'API Key Missing' });
        }
      } catch {
        setApiStatus({ ok: false, text: 'Server Offline' });
      }
    };
    checkHealth();
  }, []);

  const getTabStyle = (path) => {
    const isActive = location.pathname === path || (path === '/' && location.pathname === '');
    return {
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      padding: '8px 20px',
      borderRadius: '99px',
      border: 'none',
      fontSize: '0.88rem',
      fontWeight: 700,
      cursor: 'pointer',
      textDecoration: 'none',
      transition: 'all 0.2s ease',
      background: isActive ? 'var(--gradient-orange-red)' : 'transparent',
      color: isActive ? '#ffffff' : 'var(--text-secondary)',
      boxShadow: isActive ? '0 4px 14px var(--orange-glow)' : 'none'
    };
  };

  return (
    <header style={{
      background: 'rgba(7, 8, 10, 0.85)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--border)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
      padding: '14px 24px'
    }}>
      <div style={{
        maxWidth: '1280px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        
        {/* LOGO */}
        <Link 
          to="/"
          style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer', textDecoration: 'none', color: 'inherit' }}
        >
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'var(--gradient-orange-red)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 14px var(--orange-glow)'
          }}>
            <Flame color="#ffffff" size={22} />
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: '1.25rem', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span>TradingAgents</span>
              <span style={{
                fontSize: '0.65rem',
                fontWeight: 700,
                background: 'rgba(255, 87, 34, 0.15)',
                color: 'var(--orange-primary)',
                padding: '2px 6px',
                borderRadius: '4px',
                border: '1px solid rgba(255, 87, 34, 0.3)'
              }}>INDIA</span>
            </div>
          </div>
        </Link>

        {/* 4 TABS NAVIGATION */}
        <nav style={{
          display: 'flex',
          background: 'rgba(255, 255, 255, 0.04)',
          padding: '4px',
          borderRadius: '99px',
          border: '1px solid var(--border)'
        }}>
          <Link to="/" style={getTabStyle('/')}>
            <Activity size={16} />
            <span>Home</span>
          </Link>

          <Link to="/analysis" style={getTabStyle('/analysis')}>
            <BarChart3 size={16} />
            <span>AI Analysis</span>
            {runningState?.isRunning && (
              <span style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: '#10b981',
                boxShadow: '0 0 10px #10b981',
                animation: 'pulse 1.2s infinite'
              }} />
            )}
          </Link>

          <Link to="/past-analysis" style={getTabStyle('/past-analysis')}>
            <Clock size={16} />
            <span>Past Analysis</span>
          </Link>

          <Link to="/insights" style={getTabStyle('/insights')}>
            <Newspaper size={16} />
            <span>Insights</span>
          </Link>
        </nav>

        {/* API STATUS */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'rgba(255, 255, 255, 0.03)',
          padding: '6px 14px',
          borderRadius: '99px',
          border: '1px solid var(--border)',
          fontSize: '0.78rem',
          color: 'var(--text-secondary)'
        }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: apiStatus.ok ? 'var(--green)' : 'var(--red)',
            boxShadow: apiStatus.ok ? '0 0 8px var(--green)' : '0 0 8px var(--red)'
          }} />
          <span>{apiStatus.text}</span>
        </div>

      </div>
    </header>
  );
}
