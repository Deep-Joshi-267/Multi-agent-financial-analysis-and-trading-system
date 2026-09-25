import React, { useState, useEffect, useCallback } from 'react';
import {
  TrendingUp, TrendingDown, Minus, RefreshCw, Zap, BookOpen,
  Activity, AlertTriangle, Globe, ChevronRight, Loader
} from 'lucide-react';

// ── Curated AI Insights pool (3 shown at a time, rotate on refresh) ──────────
const AI_INSIGHTS_POOL = [
  {
    id: 1, type: 'FUNDAMENTAL ANALYSIS', badge: 'BUY', badgeKey: 'buy',
    ticker: 'RELIANCE', company: 'Reliance Industries', sector: 'Energy / Conglom.',
    icon: 'R', iconBg: '#0ea5e9',
    headline: 'Revenue diversification accelerating; Jio + Retail driving upside',
    body: "Reliance's Q1FY27 EBITDA grew 14% YoY driven by Jio's 5G subscriber addition of 22M and Retail's 19% revenue growth. New Energy segment capex on track.",
    signal: '+12% upside in 12M', confidence: 82,
  },
  {
    id: 2, type: 'TECHNICAL BREAKOUT', badge: 'BREAKOUT', badgeKey: 'breakout',
    ticker: 'ZOMATO', company: 'Zomato Limited', sector: 'Consumer Tech',
    icon: 'Z', iconBg: '#ef4444',
    headline: 'Cup-and-handle breakout — 18% upside projected',
    body: 'ZOMATO has completed a textbook cup-and-handle pattern on weekly charts. Volume surge 2.4x average on breakout day confirms institutional buying. RSI at 61 — room to run.',
    signal: 'Target Rs.275 | SL Rs.218', confidence: 76,
  },
  {
    id: 3, type: 'RISK ALERT', badge: 'CAUTION', badgeKey: 'caution',
    ticker: 'ADANIPORTS', company: 'Adani Ports & SEZ', sector: 'Infrastructure',
    icon: 'A', iconBg: '#f59e0b',
    headline: 'FII selling pressure + USD headwinds elevated',
    body: 'FII net outflows in Adani Ports crossed Rs.820 Cr in the last 3 sessions. DXY at 104.2 creates currency headwind on USD-denominated debt. Reduce position to 50%.',
    signal: 'Risk: HIGH | Reduce', confidence: 68,
  },
  {
    id: 4, type: 'SECTOR ROTATION', badge: 'WATCH', badgeKey: 'watch',
    ticker: 'HDFCBANK', company: 'HDFC Bank Ltd', sector: 'Banking',
    icon: 'H', iconBg: '#8b5cf6',
    headline: 'Credit growth normalising; NIM pressure easing in Q2',
    body: "HDFC Bank's loan-to-deposit ratio improved to 86.8% from 88.1%. Retail CASA up 120bps QoQ. Management guided for 15-17% credit growth in FY27. P/B at 2.1x — fair value zone.",
    signal: 'Accumulate on dips', confidence: 71,
  },
  {
    id: 5, type: 'FUNDAMENTAL ANALYSIS', badge: 'BUY', badgeKey: 'buy',
    ticker: 'INFY', company: 'Infosys Ltd', sector: 'IT Services',
    icon: 'I', iconBg: '#10b981',
    headline: 'Deal wins at $2.1B in Q1 — highest in 6 quarters',
    body: 'Infosys reported large deal TCV of $2.1B, up 38% YoY with 55% net new. AI-enabled services now 28% of revenue. Guidance raised to 4.5-6.5% CC growth for FY27.',
    signal: 'Target Rs.2,050 | 14% upside', confidence: 79,
  },
];

// ── Live news pool ────────────────────────────────────────────────────────────
const NEWS_POOL = [
  {
    id: 1, sentiment: 'Bullish',
    source: 'Moneycontrol', sourceInitials: 'M', sourceBg: '#dc2626',
    headline: 'RBI holds repo rate at 6.5%; signals possible cut in Q3 FY27 amid softening inflation',
    summary: 'The Monetary Policy Committee voted 5-1 to hold rates, citing moderation in core CPI to 3.8% while flagging global commodity risks.',
    timeAgo: '12 min ago', category: 'Macro', tags: ['HDFCBANK', 'SBIN'],
  },
  {
    id: 2, sentiment: 'Bullish',
    source: 'Mint', sourceInitials: 'Mn', sourceBg: '#2563eb',
    headline: 'Tata Motors Q1 FY27: Net profit surges 74% to Rs.5,566 Cr on JLR recovery and EV push',
    summary: 'JLR EBIT margin expanded 280 bps to 9.4%. Domestic CV market share rose to 42.3%. Management guides for 10-12% revenue growth in FY27.',
    timeAgo: '38 min ago', category: 'Earnings', tags: ['TATAMOTORS'],
  },
  {
    id: 3, sentiment: 'Bearish',
    source: 'Economic Times', sourceInitials: 'ET', sourceBg: '#7c3aed',
    headline: 'SEBI tightens F&O margin rules; weekly expiry contracts under review for retail protection',
    summary: 'The regulator proposed raising minimum contract sizes and increasing margin requirements by 15-20% for weekly expiry options to curb speculation.',
    timeAgo: '1 hr ago', category: 'Regulation', tags: ['NSE', 'BSE'],
  },
  {
    id: 4, sentiment: 'Bullish',
    source: 'Business Standard', sourceInitials: 'BS', sourceBg: '#059669',
    headline: "India's PMI Manufacturing hits 58.3 in July — highest in 16 years on domestic demand surge",
    summary: 'New orders sub-index climbed to 62.1, signalling broad-based expansion. Input cost inflation remained contained at 52.4, boosting sector margins.',
    timeAgo: '2 hr ago', category: 'Macro', tags: ['MARUTI', 'BAJAJ-AUTO'],
  },
  {
    id: 5, sentiment: 'Neutral',
    source: 'CNBCTV18', sourceInitials: 'C', sourceBg: '#0284c7',
    headline: 'Wipro Management Day: Company targets doubling cloud revenue by FY28',
    summary: 'Wipro outlined its AI-first strategy, expecting GenAI deals to contribute 8-10% of new wins by FY27. Margins guided to remain in 17-17.5% band.',
    timeAgo: '3 hr ago', category: 'Technology', tags: ['WIPRO'],
  },
  {
    id: 6, sentiment: 'Bearish',
    source: 'Reuters', sourceInitials: 'R', sourceBg: '#dc2626',
    headline: 'Crude oil slips 3.2% on surprise US inventory build; ONGC, IOC may face margin pressure',
    summary: 'Brent crude fell to $76.8/bbl after EIA data showed a 4.2M barrel inventory build. India refiners may see short-term GRM compression.',
    timeAgo: '4 hr ago', category: 'Commodities', tags: ['ONGC', 'IOC', 'BPCL'],
  },
  {
    id: 7, sentiment: 'Bullish',
    source: 'Financial Express', sourceInitials: 'FE', sourceBg: '#f59e0b',
    headline: 'GST collections hit Rs.2.1 lakh crore in July — second highest ever; signals strong consumption',
    summary: 'July GST mop-up grew 11.7% YoY, driven by services and import-related taxes. Finance Ministry attributed the growth to improved compliance and economic momentum.',
    timeAgo: '5 hr ago', category: 'Economy', tags: ['IRFC', 'NTPC'],
  },
  {
    id: 8, sentiment: 'Neutral',
    source: 'LiveMint', sourceInitials: 'LM', sourceBg: '#6366f1',
    headline: 'Sun Pharma receives USFDA tentative approval for specialty oncology drug',
    summary: 'The tentative approval for Lenalidomide Capsules (25mg) paves the way for launch upon patent expiry. US generics market opportunity estimated at $180M annually.',
    timeAgo: '6 hr ago', category: 'Pharma', tags: ['SUNPHARMA'],
  },
];

const INDEX_NAMES = ['NIFTY 50', 'SENSEX', 'NIFTY BANK', 'NIFTY IT'];

// Fallback skeleton when index data hasn't loaded yet
const INDEX_FALLBACK = {
  value: null, change: null, changePct: null,
  high: null, low: null, vol: '—', trend: 'neutral',
};

const BADGE_STYLES = {
  buy:      { bg: 'rgba(16,185,129,0.15)', color: '#10b981', border: 'rgba(16,185,129,0.3)' },
  breakout: { bg: 'rgba(99,102,241,0.15)',  color: '#818cf8', border: 'rgba(99,102,241,0.3)' },
  caution:  { bg: 'rgba(245,158,11,0.15)',  color: '#f59e0b', border: 'rgba(245,158,11,0.3)' },
  watch:    { bg: 'rgba(14,165,233,0.15)',  color: '#38bdf8', border: 'rgba(14,165,233,0.3)' },
};

const SENTIMENT_STYLES = {
  Bullish: { bg: 'rgba(16,185,129,0.12)', color: '#10b981', border: 'rgba(16,185,129,0.3)' },
  Bearish: { bg: 'rgba(239,68,68,0.12)',  color: '#ef4444', border: 'rgba(239,68,68,0.3)'  },
  Neutral: { bg: 'rgba(245,158,11,0.12)', color: '#f59e0b', border: 'rgba(245,158,11,0.3)' },
};

// ── SVG Sentiment Gauge ───────────────────────────────────────────────────────
function SentimentGauge({ label }) {
  const angle  = label === 'Bullish' ? 130 : label === 'Bearish' ? -130 : 0;
  const color  = label === 'Bullish' ? '#10b981' : label === 'Bearish' ? '#ef4444' : '#f59e0b';
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
      <svg width="120" height="72" viewBox="0 0 120 72">
        <defs>
          <linearGradient id="gGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%"   stopColor="#ef4444" />
            <stop offset="50%"  stopColor="#f59e0b" />
            <stop offset="100%" stopColor="#10b981" />
          </linearGradient>
        </defs>
        <path d="M 10 67 A 50 50 0 0 1 110 67" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="10" strokeLinecap="round" />
        <path d="M 10 67 A 50 50 0 0 1 110 67" fill="none" stroke="url(#gGrad)" strokeWidth="10" strokeLinecap="round" opacity="0.55" />
        <g transform={`rotate(${angle}, 60, 67)`}>
          <line x1="60" y1="67" x2="60" y2="24" stroke={color} strokeWidth="2.5" strokeLinecap="round" />
          <circle cx="60" cy="67" r="5" fill={color} />
        </g>
      </svg>
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: color, boxShadow: `0 0 8px ${color}` }} />
        <span style={{ fontWeight: 700, fontSize: '0.95rem', color }}>{label}</span>
      </div>
      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
        BEAR &nbsp; NEUTRAL &nbsp; BULL
      </div>
    </div>
  );
}

// ── AI Insight Card ───────────────────────────────────────────────────────────
function InsightCard({ insight }) {
  const bs = BADGE_STYLES[insight.badgeKey] || BADGE_STYLES.watch;
  const typeIcon = {
    'FUNDAMENTAL ANALYSIS': <BookOpen size={12} />,
    'TECHNICAL BREAKOUT': <Activity size={12} />,
    'RISK ALERT': <AlertTriangle size={12} />,
    'SECTOR ROTATION': <RefreshCw size={12} />,
  }[insight.type];

  const [hovered, setHovered] = useState(false);

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: 'var(--bg-card)',
        border: `1px solid ${hovered ? bs.border : 'var(--border)'}`,
        borderRadius: 'var(--radius-lg)', padding: '20px',
        display: 'flex', flexDirection: 'column', gap: '14px',
        transition: 'all 0.25s ease',
        boxShadow: hovered ? '0 12px 36px rgba(0,0,0,0.55)' : 'none',
        transform: hovered ? 'translateY(-2px)' : 'none',
        cursor: 'default',
      }}
    >
      {/* Type + Badge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.68rem', fontWeight: 700, color: bs.color, textTransform: 'uppercase', letterSpacing: '0.07em' }}>
          {typeIcon} {insight.type}
        </div>
        <span style={{ background: bs.bg, color: bs.color, border: `1px solid ${bs.border}`, padding: '3px 10px', borderRadius: '99px', fontSize: '0.69rem', fontWeight: 800, letterSpacing: '0.06em' }}>
          {insight.badge}
        </span>
      </div>

      {/* Company row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: insight.iconBg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 900, fontSize: '1.1rem', color: '#fff', flexShrink: 0, boxShadow: `0 4px 12px ${insight.iconBg}55` }}>
          {insight.icon}
        </div>
        <div>
          <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '0.88rem', color: '#fff' }}>{insight.ticker}</div>
          <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>{insight.company}</div>
          <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>{insight.sector}</div>
        </div>
      </div>

      {/* Headline + Body */}
      <div>
        <div style={{ fontWeight: 700, fontSize: '0.88rem', lineHeight: 1.45, color: '#fff', marginBottom: '7px' }}>{insight.headline}</div>
        <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.65 }}>{insight.body}</p>
      </div>

      {/* Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
        <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: bs.color, fontWeight: 700 }}>{insight.signal}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>AI Conf.</span>
          <div style={{ width: '56px', height: '4px', borderRadius: '99px', background: 'rgba(255,255,255,0.07)' }}>
            <div style={{ width: `${insight.confidence}%`, height: '100%', borderRadius: '99px', background: bs.color, transition: 'width 0.6s ease' }} />
          </div>
          <span style={{ fontSize: '0.7rem', color: bs.color, fontWeight: 800 }}>{insight.confidence}%</span>
        </div>
      </div>
    </div>
  );
}

// ── News Card ─────────────────────────────────────────────────────────────────
// ── News Card ─────────────────────────────────────────────────────────────────
function NewsCard({ item }) {
  const ss = SENTIMENT_STYLES[item.sentiment] || SENTIMENT_STYLES.Neutral;
  const [hovered, setHovered] = useState(false);

  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        textDecoration: 'none',
        color: 'inherit',
        background: hovered ? 'var(--bg-card-hover)' : 'var(--bg-card)',
        border: `1px solid ${hovered ? 'rgba(255,87,34,0.4)' : 'var(--border)'}`,
        borderRadius: 'var(--radius-md)', padding: '18px 20px',
        display: 'flex', gap: '16px', alignItems: 'flex-start',
        transition: 'all 0.2s ease', cursor: 'pointer',
        boxShadow: hovered ? '0 8px 24px rgba(0,0,0,0.4)' : 'none',
        transform: hovered ? 'translateY(-1px)' : 'none',
      }}
    >
      <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: item.sourceBg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.72rem', color: '#fff', flexShrink: 0, letterSpacing: '0.01em' }}>
        {item.sourceInitials}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px', marginBottom: '7px' }}>
          <h4 style={{ fontWeight: 700, fontSize: '0.9rem', lineHeight: 1.4, color: hovered ? 'var(--orange-light)' : '#fff', margin: 0, transition: 'color 0.2s ease' }}>
            {item.headline}
          </h4>
          <span style={{ flexShrink: 0, padding: '3px 10px', borderRadius: '99px', fontSize: '0.69rem', fontWeight: 700, background: ss.bg, color: ss.color, border: `1px solid ${ss.border}`, display: 'flex', alignItems: 'center', gap: '4px', whiteSpace: 'nowrap' }}>
            <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: ss.color }} />
            {item.sentiment}
          </span>
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '10px' }}>{item.summary}</p>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.71rem', color: 'var(--text-muted)', fontWeight: 600 }}>{item.source}</span>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>·</span>
          <span style={{ fontSize: '0.71rem', color: 'var(--text-muted)' }}>{item.timeAgo}</span>
          <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '0.67rem', fontWeight: 700, background: 'rgba(255,87,34,0.1)', color: 'var(--orange-light)', border: '1px solid rgba(255,87,34,0.2)' }}>
            {item.category}
          </span>
          {item.tags && item.tags.map(t => (
            <span key={t} style={{ padding: '2px 7px', borderRadius: '4px', fontSize: '0.64rem', fontWeight: 700, background: 'rgba(255,255,255,0.05)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>
              {t}
            </span>
          ))}
        </div>
      </div>
    </a>
  );
}

// ── Section label helper ───────────────────────────────────────────────────────
function SectionLabel({ text, right }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{ width: '4px', height: '18px', borderRadius: '2px', background: 'var(--gradient-orange-red)' }} />
        <span style={{ fontSize: '0.72rem', fontWeight: 800, letterSpacing: '0.1em', color: 'var(--text-muted)', textTransform: 'uppercase' }}>{text}</span>
      </div>
      {right}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
// ── Main Component ────────────────────────────────────────────────────────────
export default function InsightsTab() {
  const [activeIdx, setActiveIdx]     = useState('NIFTY 50');
  const [newsFilter, setNewsFilter]   = useState('All');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastSync, setLastSync]       = useState('');
  const [shownIdxs, setShownIdxs]     = useState([0, 1, 2]);

  // Live index state
  const [indexData, setIndexData]     = useState({});
  const [indexLoading, setIndexLoading] = useState(true);
  const [indexError, setIndexError]   = useState(null);
  const [breadth, setBreadth]         = useState({ advancing: 0, declining: 0, unchanged: 0 });

  // Live news state
  const [newsList, setNewsList]       = useState([]);
  const [newsLoading, setNewsLoading] = useState(true);
  const [newsError, setNewsError]     = useState(null);

  const fetchNews = useCallback(async () => {
    setNewsLoading(true);
    setNewsError(null);
    try {
      const res = await fetch('/api/news');
      const ct = res.headers.get('content-type') || '';
      if (!ct.includes('application/json')) {
        throw new Error('Server returned HTML instead of JSON.');
      }
      const json = await res.json();
      if (json.news && Array.isArray(json.news)) {
        setNewsList(json.news);
      }
    } catch (err) {
      setNewsError(err.message);
    } finally {
      setNewsLoading(false);
    }
  }, []);

  const fetchIndices = useCallback(async () => {
    setIndexLoading(true);
    setIndexError(null);
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10_000);

      const res = await fetch('/api/indices', { signal: controller.signal });
      clearTimeout(timeout);

      const ct = res.headers.get('content-type') || '';
      if (!ct.includes('application/json')) {
        throw new Error(
          'Server returned HTML instead of JSON. ' +
          'Please restart Flask: stop ui/app.py and run it again.'
        );
      }

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || `HTTP ${res.status}`);
      }

      const json = await res.json();
      if (json.error) throw new Error(json.error);

      setIndexData(json.indices || {});
      const adv = json.advancing ?? 0;
      const dec = json.declining ?? 0;
      setBreadth({
        advancing: adv,
        declining: dec,
        unchanged: Math.max(0, 4 - adv - dec),
      });
      setLastSync(
        new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }) + ' IST'
      );
    } catch (err) {
      if (err.name === 'AbortError') {
        setIndexError('Request timed out. Check server connection.');
      } else {
        setIndexError(err.message);
      }
    } finally {
      setIndexLoading(false);
    }
  }, []);

  // Fetch indices & news on mount
  useEffect(() => {
    fetchIndices();
    fetchNews();
  }, [fetchIndices, fetchNews]);

  // Auto-refresh indices every 60s
  useEffect(() => {
    const interval = setInterval(fetchIndices, 60_000);
    return () => clearInterval(interval);
  }, [fetchIndices]);

  // Auto-refresh news every 3 hours
  useEffect(() => {
    const interval = setInterval(fetchNews, 3 * 3600 * 1000);
    return () => clearInterval(interval);
  }, [fetchNews]);

  const handleRefresh = useCallback(() => {
    setIsRefreshing(true);
    setShownIdxs(prev => {
      const n = AI_INSIGHTS_POOL.length;
      return [(prev[0] + 1) % n, (prev[0] + 2) % n, (prev[0] + 3) % n];
    });
    Promise.all([fetchIndices(), fetchNews()]).finally(() => setIsRefreshing(false));
  }, [fetchIndices, fetchNews]);

  const idx  = indexData[activeIdx] || INDEX_FALLBACK;
  const isUp = idx.trend === 'up', isDn = idx.trend === 'down';
  const trendColor = isUp ? '#10b981' : isDn ? '#ef4444' : '#f59e0b';

  const overallSentiment = breadth.advancing >= 3 ? 'Bullish'
    : breadth.declining >= 3 ? 'Bearish' : 'Neutral';

  const fmt = (v, decimals = 2) =>
    v != null ? v.toLocaleString('en-IN', { minimumFractionDigits: decimals }) : '—';

  // Use live fetched news if available, or fallback to pool while loading
  const currentNewsPool = newsList.length > 0 ? newsList : NEWS_POOL;
  const filteredNews = newsFilter === 'All'
    ? currentNewsPool
    : currentNewsPool.filter(n => n.sentiment === newsFilter);

  const now = new Date();

  return (
    <div className="animate-fade-in" style={{ maxWidth: '1180px', margin: '0 auto', padding: '28px 20px 60px' }}>

      {/* ── PAGE HEADER ─────────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '30px', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h1 style={{ fontSize: '1.9rem', fontWeight: 900, letterSpacing: '-0.03em', marginBottom: '4px' }}>
            Insights &amp; News
          </h1>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            AI-powered market intelligence · Updated live · MoneyControl · LiveMint · CNBC
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Last synced: {lastSync}</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 14px', borderRadius: '99px', background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)' }}>
            <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#10b981', animation: 'pulseDot 1.5s infinite' }} />
            <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#10b981' }}>Live</span>
          </div>
          <button
            onClick={handleRefresh}
            style={{ padding: '7px 16px', borderRadius: 'var(--radius-sm)', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', fontWeight: 600, transition: 'all 0.2s ease' }}
          >
            <RefreshCw size={13} style={{ animation: isRefreshing ? 'spin 0.9s linear infinite' : 'none' }} />
            Refresh
          </button>
        </div>
      </div>

      {/* ── MARKET SENTIMENT ────────────────────────────────────────── */}
      <SectionLabel text="Overall Market Sentiment" />

      {indexError && (
        <div style={{
          background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.35)',
          borderRadius: 'var(--radius-md)', padding: '14px 18px', marginBottom: '16px',
          display: 'flex', alignItems: 'flex-start', gap: '12px',
        }}>
          <AlertTriangle size={18} color="#ef4444" style={{ flexShrink: 0, marginTop: '1px' }} />
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, fontSize: '0.88rem', color: '#ef4444', marginBottom: '4px' }}>
              Could not load live index data
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {indexError.includes('HTML instead of JSON')
                ? <>
                    The Flask server needs to be restarted to load the new
                    <code style={{ background: 'rgba(255,255,255,0.08)', padding: '1px 6px', borderRadius: '4px', margin: '0 4px', fontFamily: 'var(--font-mono)' }}>/api/indices</code>
                    route. Stop <code style={{ background: 'rgba(255,255,255,0.08)', padding: '1px 6px', borderRadius: '4px', fontFamily: 'var(--font-mono)' }}>ui/app.py</code> and run it again.
                  </>
                : indexError
              }
            </div>
          </div>
          <button
            onClick={fetchIndices}
            style={{ flexShrink: 0, padding: '6px 14px', borderRadius: 'var(--radius-sm)', background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.4)', color: '#ef4444', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '5px' }}
          >
            <RefreshCw size={12} /> Retry
          </button>
        </div>
      )}

      <div className="glass-card" style={{ marginBottom: '32px', padding: 0 }}>
        {/* Index tabs */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', overflowX: 'auto' }}>
          {INDEX_NAMES.map(name => {
            const data   = indexData[name] || INDEX_FALLBACK;
            const active = name === activeIdx;
            const up = data.trend === 'up', dn = data.trend === 'down';
            const col = up ? '#10b981' : dn ? '#ef4444' : '#f59e0b';
            return (
              <button key={name} onClick={() => setActiveIdx(name)} style={{
                padding: '14px 22px', border: 'none', background: 'transparent', cursor: 'pointer',
                borderBottom: active ? `2px solid ${col}` : '2px solid transparent',
                color: active ? col : 'var(--text-muted)', fontWeight: active ? 800 : 600,
                fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '6px',
                whiteSpace: 'nowrap', transition: 'all 0.18s ease',
              }}>
                {name}
                {indexLoading
                  ? <Loader size={12} style={{ animation: 'spin 1s linear infinite', opacity: 0.5 }} />
                  : up ? <TrendingUp size={13} color={col} />
                  : dn ? <TrendingDown size={13} color={col} />
                  : <Minus size={13} color={col} />}
              </button>
            );
          })}
        </div>

        {/* Index detail */}
        <div style={{ padding: '26px 28px', display: 'grid', gridTemplateColumns: '1fr auto auto', gap: '32px', alignItems: 'center' }}>
          {/* Price block */}
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '10px' }}>
              As of {now.toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })} · NSE
              {indexError && <span style={{ color: '#ef4444', marginLeft: '8px' }}>⚠ {indexError}</span>}
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '18px', marginBottom: '18px', flexWrap: 'wrap' }}>
              {indexLoading && idx.value == null ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Loader size={24} style={{ animation: 'spin 1s linear infinite', color: 'var(--text-muted)' }} />
                  <span style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>Loading live data…</span>
                </div>
              ) : (
                <>
                  <span style={{ fontSize: '2.8rem', fontWeight: 900, fontFamily: 'var(--font-mono)', letterSpacing: '-0.04em', lineHeight: 1 }}>
                    {fmt(idx.value)}
                  </span>
                  <span style={{ fontSize: '1.1rem', fontWeight: 700, color: trendColor, fontFamily: 'var(--font-mono)' }}>
                    {isUp ? '+' : ''}{fmt(idx.change)} ({isUp ? '+' : ''}{fmt(idx.changePct)}%)
                  </span>
                </>
              )}
            </div>
            <div style={{ display: 'flex', gap: '28px', flexWrap: 'wrap' }}>
              {[
                { label: 'DAY HIGH', val: fmt(idx.high), color: '#10b981' },
                { label: 'DAY LOW',  val: fmt(idx.low),  color: '#ef4444' },
                { label: 'VOLUME',   val: idx.vol || '—', color: 'var(--text-secondary)' },
              ].map(s => (
                <div key={s.label}>
                  <div style={{ fontSize: '0.63rem', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '0.08em', marginBottom: '3px' }}>{s.label}</div>
                  <div style={{ fontSize: '0.88rem', fontWeight: 700, color: s.color, fontFamily: 'var(--font-mono)' }}>{s.val}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Gauge */}
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.63rem', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '0.08em', marginBottom: '10px', textTransform: 'uppercase' }}>Sentiment Gauge</div>
            <SentimentGauge label={overallSentiment} />
          </div>

          {/* Market Breadth */}
          <div style={{ minWidth: '185px' }}>
            <div style={{ fontSize: '0.63rem', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '0.08em', marginBottom: '14px', textTransform: 'uppercase' }}>Market Breadth</div>
            {[
              { label: 'Advancing', val: breadth.advancing, color: '#10b981', total: 4 },
              { label: 'Declining', val: breadth.declining, color: '#ef4444', total: 4 },
              { label: 'Unchanged', val: breadth.unchanged, color: '#f59e0b', total: 4 },
            ].map(row => (
              <div key={row.label} style={{ marginBottom: '11px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{row.label}</span>
                  <span style={{ fontSize: '0.78rem', fontWeight: 800, color: row.color, fontFamily: 'var(--font-mono)' }}>
                    {indexLoading ? '…' : row.val}
                  </span>
                </div>
                <div style={{ height: '4px', borderRadius: '99px', background: 'rgba(255,255,255,0.07)', overflow: 'hidden' }}>
                  <div style={{ width: `${indexLoading ? 0 : (row.val / row.total * 100).toFixed(1)}%`, height: '100%', borderRadius: '99px', background: row.color, transition: 'width 0.8s ease' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── AI AGENT INSIGHTS ────────────────────────────────────────── */}
      <SectionLabel
        text="AI Agent Insights"
        right={
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            <Zap size={12} color="var(--orange-primary)" />
            Powered by TradingAgents AI · GPT-4o
          </div>
        }
      />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px', marginBottom: '34px' }}>
        {shownIdxs.map(i => <InsightCard key={AI_INSIGHTS_POOL[i].id} insight={AI_INSIGHTS_POOL[i]} />)}
      </div>

      {/* ── LIVE NEWS FEED ───────────────────────────────────────────── */}
      <SectionLabel
        text="Live News Feed"
        right={
          <div style={{ display: 'flex', gap: '5px', background: 'rgba(255,255,255,0.04)', padding: '4px', borderRadius: '99px', border: '1px solid var(--border)' }}>
            {['All', 'Bullish', 'Bearish', 'Neutral'].map(f => {
              const active = newsFilter === f;
              const fColor = f === 'Bullish' ? '#10b981' : f === 'Bearish' ? '#ef4444' : f === 'Neutral' ? '#f59e0b' : 'var(--orange-primary)';
              return (
                <button key={f} onClick={() => setNewsFilter(f)} style={{
                  padding: '6px 16px', borderRadius: '99px', border: active && f !== 'All' ? `1px solid ${fColor}55` : '1px solid transparent',
                  background: active ? (f === 'All' ? 'var(--gradient-orange-red)' : `${fColor}20`) : 'transparent',
                  color: active ? (f === 'All' ? '#fff' : fColor) : 'var(--text-muted)',
                  fontSize: '0.78rem', fontWeight: 700, cursor: 'pointer',
                  boxShadow: active && f === 'All' ? '0 4px 12px var(--orange-glow)' : 'none',
                  transition: 'all 0.18s ease',
                }}>
                  {f}
                </button>
              );
            })}
          </div>
        }
      />

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {newsLoading && newsList.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)', fontSize: '0.88rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
            <Loader size={18} style={{ animation: 'spin 1s linear infinite' }} /> Loading live news from MoneyControl, LiveMint &amp; CNBC…
          </div>
        ) : filteredNews.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)', fontSize: '0.88rem' }}>
            No {newsFilter.toLowerCase()} news at this moment.
          </div>
        ) : (
          filteredNews.slice(0, 10).map(item => <NewsCard key={item.id} item={item} />)
        )}
      </div>
    </div>
  );
}
