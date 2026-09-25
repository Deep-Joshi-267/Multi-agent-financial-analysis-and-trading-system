import React from 'react';
import { ShieldCheck, Cpu, Globe } from 'lucide-react';

export default function Footer() {
  return (
    <footer style={{
      background: '#040507',
      borderTop: '1px solid var(--border)',
      padding: '32px 24px',
      marginTop: 'auto'
    }}>
      <div style={{
        maxWidth: '1280px',
        margin: '0 auto',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '16px'
      }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#ffffff' }}>
            TradingAgents <span style={{ color: 'var(--orange-primary)' }}>AI</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Multi-Agent Financial Intelligence Platform tailored for Indian Stock Markets (NSE / BSE).
          </p>
        </div>

        <div style={{ display: 'flex', gap: '20px', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Cpu size={14} color="var(--orange-primary)" />
            Model: qwen/qwen3.8-27b
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Globe size={14} color="var(--orange-primary)" />
            Market: NSE/BSE (India)
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <ShieldCheck size={14} color="var(--green)" />
            SEBI Compliant Context
          </span>
        </div>
      </div>
    </footer>
  );
}
