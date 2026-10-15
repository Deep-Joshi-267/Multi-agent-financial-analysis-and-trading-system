import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Chart as ChartJS, registerables } from 'chart.js';
import { TrendingUp, TrendingDown, Clock, ShieldAlert } from 'lucide-react';

ChartJS.register(...registerables);

export default function PriceChart({ symbol }) {
  const canvasRef = useRef(null);
  const chartInstanceRef = useRef(null);
  const [period, setPeriod] = useState('1m');
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchChart = useCallback(async (sym, p) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/chart/${encodeURIComponent(sym)}/${p}`);
      const data = await res.json();
      if (data.error) {
        setError(data.error);
        setChartData(null);
      } else {
        setChartData(data);
      }
    } catch {
      setError('Failed to load chart data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!symbol) return;
    let isMounted = true;
    Promise.resolve().then(() => {
      if (isMounted) fetchChart(symbol, period);
    });
    return () => { isMounted = false; };
  }, [symbol, period, fetchChart]);

  useEffect(() => {
    if (!chartData || !canvasRef.current) return;

    const ctx = canvasRef.current.getContext('2d');
    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy();
    }

    const isPositive = chartData.change >= 0;
    const strokeColor = isPositive ? '#10b981' : '#ef4444';
    const gradientTop = isPositive ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.25)';
    const gradientBottom = 'rgba(16, 185, 129, 0.0)';

    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, gradientTop);
    gradient.addColorStop(1, gradientBottom);

    chartInstanceRef.current = new ChartJS(ctx, {
      type: 'line',
      data: {
        labels: chartData.labels,
        datasets: [
          {
            label: 'Price',
            data: chartData.prices,
            borderColor: strokeColor,
            borderWidth: 2.5,
            pointRadius: chartData.prices.length > 60 ? 0 : 2,
            pointHoverRadius: 6,
            pointHoverBackgroundColor: strokeColor,
            fill: true,
            backgroundColor: gradient,
            tension: 0.2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            titleColor: '#94a3b8',
            bodyColor: '#f8fafc',
            borderColor: 'rgba(255, 255, 255, 0.12)',
            borderWidth: 1,
            padding: 12,
            displayColors: false,
            callbacks: {
              label: function (context) {
                return ` Price: ${chartData.currency} ${context.parsed.y.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
              },
            },
          },
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: { color: '#64748b', maxTicksLimit: 9, font: { family: 'Inter', size: 11 } },
          },
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: {
              color: '#64748b',
              font: { family: 'JetBrains Mono', size: 11 },
              callback: function (val) {
                return `${chartData.currency} ${val.toLocaleString('en-IN')}`;
              },
            },
          },
        },
      },
    });

    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
      }
    };
  }, [chartData]);

  if (!symbol) return null;

  return (
    <div className="glass-card" style={{ marginTop: '20px' }}>
      
      {/* HEADER BAR */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
        <div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.4rem', fontWeight: 800, color: 'var(--orange-primary)' }}>
            {chartData ? chartData.symbol : symbol}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Live Interactive Price Chart</div>
        </div>

        {chartData && (
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.6rem', fontWeight: 800 }}>
              {chartData.currency} {chartData.current_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
            <span className={chartData.change >= 0 ? 'badge-buy' : 'badge-sell'} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              {chartData.change >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              {chartData.change >= 0 ? '+' : ''}{chartData.change.toFixed(2)} ({chartData.change_pct >= 0 ? '+' : ''}{chartData.change_pct.toFixed(2)}%)
            </span>
          </div>
        )}
      </div>

      {/* METRICS & TIMEFRAMES */}
      <div style={{
        display: 'flex',
        justify: 'space-between',
        alignItems: 'center',
        background: 'rgba(255, 255, 255, 0.03)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        padding: '10px 16px',
        marginBottom: '20px',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        {chartData ? (
          <div style={{ display: 'flex', gap: '24px' }}>
            <div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Period High: </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: '0.85rem' }}>
                {chartData.currency} {chartData.high.toLocaleString('en-IN')}
              </span>
            </div>
            <div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Period Low: </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: '0.85rem' }}>
                {chartData.currency} {chartData.low.toLocaleString('en-IN')}
              </span>
            </div>
          </div>
        ) : (
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Fetching live timeframe history…</div>
        )}

        {/* 5 TIMEFRAME BUTTONS */}
        <div style={{ display: 'flex', gap: '4px', background: 'rgba(0,0,0,0.4)', padding: '3px', borderRadius: '8px', border: '1px solid var(--border)' }}>
          {['1d', '1m', '6m', 'ytd', '5y'].map((tf) => (
            <button
              key={tf}
              onClick={() => setPeriod(tf)}
              style={{
                background: period === tf ? 'var(--gradient-orange-red)' : 'transparent',
                color: period === tf ? '#ffffff' : 'var(--text-muted)',
                border: 'none',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.75rem',
                fontWeight: 700,
                padding: '6px 14px',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: period === tf ? '0 2px 8px var(--orange-glow)' : 'none'
              }}
            >
              {tf.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* CANVAS CONTAINER */}
      <div style={{ position: 'relative', width: '100%', height: '300px' }}>
        {loading && (
          <div style={{
            position: 'absolute',
            inset: 0,
            background: 'rgba(18, 20, 28, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 'var(--radius-md)',
            zIndex: 5
          }}>
            <div style={{ fontSize: '0.88rem', color: 'var(--orange-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Clock className="animate-spin" size={18} /> Loading {period.toUpperCase()} price chart…
            </div>
          </div>
        )}
        {error ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--red)', fontSize: '0.88rem', gap: '8px' }}>
            <ShieldAlert size={18} /> {error}
          </div>
        ) : (
          <canvas ref={canvasRef} />
        )}
      </div>

    </div>
  );
}
