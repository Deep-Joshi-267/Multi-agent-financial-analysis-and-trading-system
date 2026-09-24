/* TradingAgents UI v2 — Real-time Analysis Frontend */

// ── State ──────────────────────────────────────────────────────────────────
const state = {
  jobId: null,
  eventSource: null,
  ticker: null,
  result: null,
};

// ── Ticker Autocomplete DB ─────────────────────────────────────────────────
const TICKERS = [
  { symbol: "AAPL",        name: "Apple Inc." },
  { symbol: "MSFT",        name: "Microsoft Corp." },
  { symbol: "GOOGL",       name: "Alphabet Inc." },
  { symbol: "AMZN",        name: "Amazon.com Inc." },
  { symbol: "TSLA",        name: "Tesla Inc." },
  { symbol: "NVDA",        name: "NVIDIA Corp." },
  { symbol: "META",        name: "Meta Platforms" },
  { symbol: "BRK-B",       name: "Berkshire Hathaway" },
  { symbol: "JPM",         name: "JPMorgan Chase" },
  { symbol: "V",           name: "Visa Inc." },
  { symbol: "JNJ",         name: "Johnson & Johnson" },
  { symbol: "WMT",         name: "Walmart Inc." },
  { symbol: "NFLX",        name: "Netflix Inc." },
  { symbol: "AMD",         name: "Advanced Micro Devices" },
  { symbol: "INTC",        name: "Intel Corp." },
  { symbol: "DIS",         name: "Walt Disney Co." },
  { symbol: "PYPL",        name: "PayPal Holdings" },
  { symbol: "RELIANCE.NS", name: "Reliance Industries" },
  { symbol: "TCS.NS",      name: "Tata Consultancy Services" },
  { symbol: "INFY.NS",     name: "Infosys Ltd." },
  { symbol: "HDFCBANK.NS", name: "HDFC Bank" },
  { symbol: "WIPRO.NS",    name: "Wipro Ltd." },
  { symbol: "BAJFINANCE.NS", name: "Bajaj Finance" },
];

// ── Init ───────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  checkApiHealth();
  setupTickerAutocomplete();
  setupQuotePreview();
  document.getElementById("tickerInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter") startAnalysis();
  });
});

// ── Navigation ─────────────────────────────────────────────────────────────
function showSection(section) {
  document.querySelectorAll(".nav-pill").forEach((p) => p.classList.remove("active"));
  document.getElementById(`nav-${section}`)?.classList.add("active");

  document.getElementById("section-analyze").style.display   = "none";
  document.getElementById("pipelineSection").style.display   = "none";
  document.getElementById("section-pipeline").style.display  = "none";
  document.getElementById("section-about").style.display     = "none";

  if (section === "analyze") {
    document.getElementById("section-analyze").style.display = "";
    if (state.jobId) document.getElementById("pipelineSection").style.display = "";
  } else if (section === "pipeline") {
    document.getElementById("section-pipeline").style.display = "";
  } else if (section === "about") {
    document.getElementById("section-about").style.display = "";
  }
}

// ── Health Check ───────────────────────────────────────────────────────────
async function checkApiHealth() {
  try {
    const res  = await fetch("/api/health");
    const data = await res.json();
    const dot  = document.querySelector(".status-dot");
    const text = document.querySelector(".status-text");
    if (data.groq_configured) {
      dot.classList.add("ok"); text.textContent = "Groq API ready";
    } else {
      dot.classList.add("err"); text.textContent = "GROQ_API_KEY missing";
    }
  } catch {
    document.querySelector(".status-text").textContent = "Server offline";
  }
}

// ── Live Quote Preview ─────────────────────────────────────────────────────
let quoteDebounce = null;
function setupQuotePreview() {
  const input = document.getElementById("tickerInput");
  input.addEventListener("input", () => {
    clearTimeout(quoteDebounce);
    quoteDebounce = setTimeout(async () => {
      const sym = input.value.trim().toUpperCase();
      if (sym.length < 2) { hideQuotePreview(); return; }
      try {
        const res  = await fetch(`/api/quote/${sym}`);
        const data = await res.json();
        if (data.error) { hideQuotePreview(); return; }
        showQuotePreview(data);
        loadStockChart(sym, currentChartPeriod || "1m");
      } catch { hideQuotePreview(); }
    }, 700);
  });
}

function showQuotePreview(d) {
  let panel = document.getElementById("quotePreview");
  if (!panel) {
    panel = document.createElement("div");
    panel.id = "quotePreview";
    panel.className = "quote-preview card";
    document.querySelector(".analysis-card .form-row").after(panel);
  }
  const isUS = ["AAPL","MSFT","GOOGL","AMZN","TSLA","NVDA","META"].includes(d.symbol);
  const cur  = isUS ? "$" : "Rs.";
  const rsiClass = !d.rsi ? "" : d.rsi < 30 ? "rsi-oversold" : d.rsi > 70 ? "rsi-overbought" : "rsi-neutral";
  const momClass = !d.momentum ? "" : d.momentum > 0 ? "pos" : "neg";
  const mcap = d.market_cap ? fmtMcap(d.market_cap) : "—";
  panel.innerHTML = `
    <div class="qp-header">
      <div>
        <div class="qp-symbol">${esc(d.symbol)}</div>
        <div class="qp-name">${esc(d.name || "")} · ${esc(d.sector || "")}</div>
      </div>
      <div class="qp-price">${cur} ${d.price ? d.price.toFixed(2) : "—"}</div>
    </div>
    <div class="qp-metrics">
      <div class="qp-metric">
        <div class="qp-metric-label">RSI (14)</div>
        <div class="qp-metric-val ${rsiClass}">${d.rsi ? d.rsi.toFixed(1) : "—"}</div>
      </div>
      <div class="qp-metric">
        <div class="qp-metric-label">5d Momentum</div>
        <div class="qp-metric-val ${momClass}">${d.momentum ? (d.momentum > 0 ? "+" : "") + d.momentum.toFixed(2) + "%" : "—"}</div>
      </div>
      <div class="qp-metric">
        <div class="qp-metric-label">P/E Ratio</div>
        <div class="qp-metric-val">${d.pe_ratio ? d.pe_ratio.toFixed(1) : "—"}</div>
      </div>
      <div class="qp-metric">
        <div class="qp-metric-label">Market Cap</div>
        <div class="qp-metric-val">${mcap}</div>
      </div>
      <div class="qp-metric">
        <div class="qp-metric-label">SMA 20</div>
        <div class="qp-metric-val">${cur} ${d.sma_20 ? d.sma_20.toFixed(2) : "—"}</div>
      </div>
      <div class="qp-metric">
        <div class="qp-metric-label">SMA 50</div>
        <div class="qp-metric-val">${cur} ${d.sma_50 ? d.sma_50.toFixed(2) : "—"}</div>
      </div>
    </div>`;
  panel.style.display = "";
}

function hideQuotePreview() {
  const p = document.getElementById("quotePreview");
  if (p) p.style.display = "none";
}

// ── Ticker Autocomplete ────────────────────────────────────────────────────
function setupTickerAutocomplete() {
  const input       = document.getElementById("tickerInput");
  const suggestions = document.getElementById("tickerSuggestions");

  input.addEventListener("input", () => {
    const q = input.value.trim().toUpperCase();
    if (!q) { suggestions.style.display = "none"; return; }
    const hits = TICKERS.filter((t) =>
      t.symbol.startsWith(q) || t.name.toUpperCase().includes(q)
    ).slice(0, 6);
    if (!hits.length) { suggestions.style.display = "none"; return; }
    suggestions.innerHTML = hits.map((t) =>
      `<div class="ticker-suggestion-item" onclick="setTicker('${t.symbol}')">
         <span class="ts-symbol">${t.symbol}</span>
         <span class="ts-name">${t.name}</span>
       </div>`
    ).join("");
    suggestions.style.display = "block";
  });

  document.addEventListener("click", (e) => {
    if (!e.target.closest(".ticker-input-wrap")) suggestions.style.display = "none";
  });
}

function setTicker(symbol) {
  document.getElementById("tickerInput").value = symbol;
  document.getElementById("tickerSuggestions").style.display = "none";
  loadStockChart(symbol, currentChartPeriod || "1m");
  fetch(`/api/quote/${symbol}`)
    .then(res => res.json())
    .then(data => { if (!data.error) showQuotePreview(data); })
    .catch(() => {});
}

// ── Start Analysis ─────────────────────────────────────────────────────────
async function startAnalysis() {
  const ticker  = document.getElementById("tickerInput").value.trim().toUpperCase();
  const capital = parseFloat(document.getElementById("capitalInput").value) || 100000;
  const risk    = document.getElementById("riskSelect").value;
  const quick   = document.getElementById("quickMode").checked;

  if (!ticker) { flashInput(); return; }

  if (state.eventSource) { state.eventSource.close(); state.eventSource = null; }
  state.ticker = ticker;

  // Loading state
  const btn = document.getElementById("analyzeBtn");
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner"></div><span>Analysing…</span>';

  // Show pipeline section
  document.getElementById("pipelineSection").style.display = "";
  document.getElementById("resultsSection").style.display = "none";
  document.getElementById("analysisTicker").textContent = ticker;
  document.getElementById("analysisMeta").textContent =
    `$${capital.toLocaleString()} · ${cap(risk)} risk · ${quick ? "Quick" : "Full"} pipeline`;

  // Hide quick-mode stages if needed
  const researchersStage = document.getElementById("stage-researchers");
  const cioStage         = document.getElementById("stage-cio");
  const tradersStage     = document.getElementById("stage-traders");
  const arrows           = document.querySelectorAll(".stage-arrow");

  if (quick) {
    [researchersStage, cioStage, tradersStage].forEach((s) => s && (s.style.opacity = "0.3"));
    arrows.forEach((a, i) => i >= 1 && (a.style.opacity = "0.3"));
  } else {
    [researchersStage, cioStage, tradersStage].forEach((s) => s && (s.style.opacity = ""));
    arrows.forEach((a) => a.style.opacity = "");
  }

  resetStages();
  clearLog();
  appendLog(`Starting ${quick ? "quick" : "full pipeline"} analysis for ${ticker}…`, "warn");

  try {
    const res  = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker, capital, risk, quick }),
    });
    const data = await res.json();
    if (data.error) { appendLog(`Error: ${data.error}`, "err"); resetButton(); return; }
    state.jobId = data.job_id;
    listenToStream(data.job_id);
  } catch (e) {
    appendLog(`Connection failed: ${e.message}`, "err");
    resetButton();
  }
}

// ── SSE Stream ─────────────────────────────────────────────────────────────
function listenToStream(jobId) {
  const es = new EventSource(`/api/stream/${jobId}`);
  state.eventSource = es;
  document.getElementById("logPulse").classList.add("active");

  es.onmessage = (e) => {
    if (e.data === "[DONE]") {
      es.close(); document.getElementById("logPulse").classList.remove("active");
      resetButton(); return;
    }
    try { handleEvent(JSON.parse(e.data)); } catch { /* heartbeat */ }
  };
  es.onerror = () => {
    appendLog("Stream disconnected.", "err");
    document.getElementById("logPulse").classList.remove("active");
    resetButton(); es.close();
  };
}

// ── Event Dispatcher ───────────────────────────────────────────────────────
function handleEvent(event) {
  const { stage, message, status, data } = event;
  if (stage === "heartbeat") return;

  const cls = status === "done" ? "ok" : status === "error" ? "err" : "";
  appendLog(message, cls);

  const stageMap = { data:"data", analysts:"analysts", researchers:"researchers", cio:"cio", traders:"traders" };
  if (stageMap[stage]) updateStage(stageMap[stage], status);

  if (stage === "complete" && data?.result) {
    state.result = data.result;
    showResults(data.result);
  }
}

// ── Stage Visual Updates ───────────────────────────────────────────────────
function updateStage(stageName, status) {
  const card = document.getElementById(`stage-${stageName}`);
  if (!card) return;
  const dot = card.querySelector(".stage-status-dot");
  card.classList.remove("running", "done", "error");
  dot.classList.remove("running", "done", "error", "idle");
  if (status === "running") { card.classList.add("running"); dot.classList.add("running"); }
  else if (status === "done") { card.classList.add("done"); dot.classList.add("done"); }
  else if (status === "error") { card.classList.add("error"); dot.classList.add("error"); }
}

function resetStages() {
  ["data","analysts","researchers","cio","traders"].forEach((s) => {
    const card = document.getElementById(`stage-${s}`);
    if (!card) return;
    card.classList.remove("running","done","error");
    const dot = card.querySelector(".stage-status-dot");
    dot.classList.remove("running","done","error"); dot.classList.add("idle");
  });
}

// ── Log ────────────────────────────────────────────────────────────────────
function appendLog(msg, cls = "") {
  const body = document.getElementById("logBody");
  const now  = new Date().toLocaleTimeString();
  const line = document.createElement("div");
  line.className = "log-line";
  line.innerHTML = `<span class="log-time">${now}</span><span class="log-msg ${cls}">${esc(msg)}</span>`;
  body.appendChild(line);
  body.scrollTop = body.scrollHeight;
}
function clearLog() { document.getElementById("logBody").innerHTML = ""; }

// ══════════════════════════════════════════════════════════════════════════
// Results Rendering
// ══════════════════════════════════════════════════════════════════════════

function showResults(result) {
  document.getElementById("resultsSection").style.display = "";

  const action     = result.action || "N/A";
  const confidence = parseFloat(result.confidence || 0);
  const reasoning  = result.reasoning || "";

  // ── Decision banner ──────────────────────────────────────────────────
  const actionEl = document.getElementById("decisionAction");
  actionEl.textContent = action.replace(/_/g, " ");
  actionEl.className = "decision-action " + actionClass(action);

  const confPct = Math.round(confidence <= 1 ? confidence * 100 : confidence);
  document.getElementById("confidenceText").textContent = confPct + "%";
  setTimeout(() => { document.getElementById("confidenceFill").style.width = confPct + "%"; }, 120);
  document.getElementById("decisionReasoning").textContent =
    reasoning || "No reasoning provided.";

  // Meta chips
  renderDecisionMeta(result);

  // ── Market Data ──────────────────────────────────────────────────────
  const md = result.market_data || {};
  if (Object.keys(md).length) {
    renderMarketData(md);
    document.getElementById("marketDataCard").style.display = "";
  }

  // ── Analyst Breakdown ────────────────────────────────────────────────
  renderAnalystSignals(result.analyst_report || result);

  // ── Research (full pipeline) ─────────────────────────────────────────
  const rr = result.research_report;
  if (rr && rr.investment_thesis) {
    renderResearch(rr);
    document.getElementById("researchCard").style.display = "";
  }

  // ── Trade Execution ──────────────────────────────────────────────────
  const te = result.trade_execution;
  if (te && te.action) {
    renderTrade(te);
    document.getElementById("tradeCard").style.display = "";
  }

  // ── Risk Factors ─────────────────────────────────────────────────────
  const rf = result.risk_factors || result.analyst_report?.risk_factors || [];
  if (rf.length) {
    renderRiskFactors(rf);
    document.getElementById("riskCard").style.display = "";
  }

  document.getElementById("resultsSection").scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderDecisionMeta(result) {
  const ar  = result.analyst_report || {};
  const chips = [
    result.position_size && `Position: ${result.position_size}`,
    result.time_horizon  && `Horizon: ${result.time_horizon}`,
    ar.analyst_agreement && `Consensus: ${ar.analyst_agreement.slice(0, 60)}`,
  ].filter(Boolean);
  const el = document.getElementById("decisionMeta");
  if (!el) return;
  el.innerHTML = chips.map((c) =>
    `<span class="meta-chip">${esc(c)}</span>`
  ).join("");
}

function renderMarketData(md) {
  const el = document.getElementById("marketDataContent");
  if (!el) return;

  const price = md.current_price;
  const hi    = md["52w_high"];
  const lo    = md["52w_low"];
  const rsi   = md.rsi_14;
  const mom5  = md.momentum_5d;
  const mom20 = md.momentum_20d;

  const rsiClass = !rsi ? "" : rsi < 30 ? "rsi-oversold" : rsi > 70 ? "rsi-overbought" : "rsi-neutral";

  el.innerHTML = `
    <div class="md-header">
      <div>
        <div class="md-company">${esc(md.company || "")}</div>
        <div class="md-sector">${esc(md.sector || "")} ${md.industry ? "· " + esc(md.industry) : ""}</div>
      </div>
      <div class="md-price">$${price ? price.toFixed(2) : "—"}</div>
    </div>
    <div class="md-grid">
      ${mdMetric("Market Cap",  md.market_cap ? fmtMcap(md.market_cap) : "—")}
      ${mdMetric("P/E Ratio",   md.pe_ratio ? md.pe_ratio.toFixed(1) : "—")}
      ${mdMetric("Fwd P/E",     md.forward_pe ? md.forward_pe.toFixed(1) : "—")}
      ${mdMetric("EPS",         md.eps ? "$" + md.eps.toFixed(2) : "—")}
      ${mdMetric("Beta",        md.beta ? md.beta.toFixed(2) : "—")}
      ${mdMetric("52w High",    hi ? "$" + hi.toFixed(2) : "—")}
      ${mdMetric("52w Low",     lo ? "$" + lo.toFixed(2) : "—")}
      ${mdMetric("Avg Volume",  md.avg_volume ? fmtNum(md.avg_volume) : "—")}
      ${mdMetricClass("RSI (14)", rsi ? rsi.toFixed(1) : "—", rsiClass)}
      ${mdMetricClass("5d Momentum", mom5 ? (mom5 > 0 ? "+" : "") + mom5.toFixed(2) + "%" : "—", mom5 > 0 ? "pos" : "neg")}
      ${mdMetric("20d Momentum", mom20 ? (mom20 > 0 ? "+" : "") + mom20.toFixed(2) + "%" : "—")}
      ${mdMetric("SMA 20",      md.sma_20 ? "$" + md.sma_20.toFixed(2) : "—")}
      ${mdMetric("SMA 50",      md.sma_50 ? "$" + md.sma_50.toFixed(2) : "—")}
      ${mdMetric("SMA 200",     md.sma_200 ? "$" + md.sma_200.toFixed(2) : "—")}
      ${mdMetric("MACD",        md.macd ? md.macd.toFixed(3) : "—")}
      ${mdMetric("MACD Signal", md.macd_signal ? md.macd_signal.toFixed(3) : "—")}
      ${mdMetric("BB Upper",    md.bb_upper ? "$" + md.bb_upper.toFixed(2) : "—")}
      ${mdMetric("BB Lower",    md.bb_lower ? "$" + md.bb_lower.toFixed(2) : "—")}
      ${mdMetric("News Count",  md.news_count ?? "—")}
    </div>`;
}

function mdMetric(label, val) {
  return `<div class="md-metric"><div class="md-metric-label">${label}</div><div class="md-metric-val">${val}</div></div>`;
}
function mdMetricClass(label, val, cls) {
  return `<div class="md-metric"><div class="md-metric-label">${label}</div><div class="md-metric-val ${cls}">${val}</div></div>`;
}

function renderAnalystSignals(report) {
  const container = document.getElementById("analystSignals");
  if (!container) return;
  container.innerHTML = "";

  const agents = [
    { name: "News Analyst",         sigKey: "news_signal",         confKey: "news_confidence",         reasonKey: "news_reasoning",         factsKey: "news_key_factors" },
    { name: "Fundamentals Analyst", sigKey: "fundamentals_signal", confKey: "fundamentals_confidence", reasonKey: "fundamentals_reasoning", factsKey: "fundamentals_key_factors" },
    { name: "Sentiment Analyst",    sigKey: "sentiment_signal",    confKey: "sentiment_confidence",    reasonKey: "sentiment_reasoning",    factsKey: "sentiment_key_factors" },
    { name: "Technical Analyst",    sigKey: "technical_signal",    confKey: "technical_confidence",    reasonKey: "technical_reasoning",    factsKey: "technical_key_factors" },
  ];

  let anyFound = false;
  agents.forEach(({ name, sigKey, confKey, reasonKey, factsKey }) => {
    const sig    = report?.[sigKey];
    if (!sig || sig === "N/A") return;
    anyFound = true;
    const conf   = report?.[confKey] || 0;
    const reason = report?.[reasonKey] || "";
    const facts  = report?.[factsKey] || [];
    const confPct = Math.round(conf <= 1 ? conf * 100 : conf);

    const div = document.createElement("div");
    div.className = "analyst-block";
    div.innerHTML = `
      <div class="analyst-block-header">
        <span class="analyst-name">${name}</span>
        <div class="analyst-right">
          <span class="signal-badge ${sig.replace(/ /g,"_")}">${sig.replace(/_/g," ")}</span>
          <span class="analyst-conf">${confPct}%</span>
        </div>
      </div>
      ${reason ? `<div class="analyst-reasoning">${esc(reason.slice(0, 220))}${reason.length > 220 ? "…" : ""}</div>` : ""}
      ${facts.length ? `<div class="analyst-factors">${facts.slice(0,4).map((f) => `<span class="factor-tag">${esc(f)}</span>`).join("")}</div>` : ""}`;
    container.appendChild(div);
  });

  if (!anyFound) {
    container.innerHTML = `<div style="color:var(--text-muted);font-size:.85rem">Analyst signals not available.</div>`;
  }
}

function renderResearch(r) {
  const el = document.getElementById("researchContent");
  if (!el) return;
  el.innerHTML = `
    ${r.investment_thesis ? `
      <div class="research-section">
        <div class="research-section-title">Investment Thesis</div>
        <div class="research-text">${esc(r.investment_thesis)}</div>
      </div>` : ""}
    <div class="bull-bear-grid">
      ${r.bull_case_summary ? `
        <div class="bull-card">
          <div class="bb-label">🐂 Bull Case</div>
          <div class="bb-text">${esc(r.bull_case_summary)}</div>
        </div>` : ""}
      ${r.bear_case_summary ? `
        <div class="bear-card">
          <div class="bb-label">🐻 Bear Case</div>
          <div class="bb-text">${esc(r.bear_case_summary)}</div>
        </div>` : ""}
    </div>
    ${r.risk_reward_ratio ? `
      <div class="kv-row">
        <span class="kv-label">Risk/Reward</span>
        <span class="kv-val">${esc(r.risk_reward_ratio)}</span>
      </div>` : ""}
    <div class="kv-row">
      <span class="kv-label">Recommended Action</span>
      <span class="kv-val signal-badge ${(r.recommended_action||"").replace(/ /g,"_")}">${(r.recommended_action||"").replace(/_/g," ")}</span>
    </div>
    <div class="kv-row">
      <span class="kv-label">Conviction</span>
      <span class="kv-val">${esc(r.conviction || r.position_conviction || "—")}</span>
    </div>
    ${r.key_risks?.length ? `
      <div class="risk-list">
        <div class="research-section-title">Key Risks</div>
        ${r.key_risks.slice(0,5).map((k) => `<div class="risk-item">⚠ ${esc(k)}</div>`).join("")}
      </div>` : ""}
    ${r.key_opportunities?.length ? `
      <div class="risk-list">
        <div class="research-section-title">Key Opportunities</div>
        ${r.key_opportunities.slice(0,5).map((k) => `<div class="opp-item">✦ ${esc(k)}</div>`).join("")}
      </div>` : ""}`;
}

function renderTrade(t) {
  const el = document.getElementById("tradeContent");
  if (!el) return;
  const ep = t.entry_price;
  const sl = t.stop_loss;
  const tp = t.take_profit;
  const riskReward = (ep && sl && tp)
    ? ((tp - ep) / (ep - sl)).toFixed(2)
    : null;

  el.innerHTML = `
    <div class="trade-action-badge ${actionClass(t.action)}">${(t.action||"").replace(/_/g," ")}</div>
    <div class="trade-grid">
      ${tradeKV("Order Type",   t.order_type || "MARKET")}
      ${tradeKV("Quantity",     t.quantity ?? "—")}
      ${tradeKV("Entry Price",  ep ? "$" + ep.toFixed(2) : "—")}
      ${tradeKV("Stop Loss",    sl ? "$" + sl.toFixed(2) : "—")}
      ${tradeKV("Take Profit",  tp ? "$" + tp.toFixed(2) : "—")}
      ${riskReward ? tradeKV("Risk/Reward", "1:" + riskReward) : ""}
      ${tradeKV("Status",       t.status || "PLANNED")}
    </div>
    ${t.notes ? `<div class="trade-notes">${esc(t.notes.slice(0, 300))}</div>` : ""}`;
}
function tradeKV(k, v) {
  return `<div class="kv-row"><span class="kv-label">${k}</span><span class="kv-val">${esc(String(v))}</span></div>`;
}

function renderRiskFactors(factors) {
  const el = document.getElementById("riskContent");
  if (!el) return;
  el.innerHTML = factors.map((f) =>
    `<div class="risk-factor-item"><span class="risk-dot">▸</span>${esc(f)}</div>`
  ).join("");
}

// ── Helpers ────────────────────────────────────────────────────────────────
function resetAnalysis() {
  if (state.eventSource) state.eventSource.close();
  state.jobId = null; state.eventSource = null; state.result = null;
  document.getElementById("pipelineSection").style.display = "none";
  document.getElementById("resultsSection").style.display  = "none";
  resetStages(); resetButton();
  hideQuotePreview();
}

function resetButton() {
  const btn = document.getElementById("analyzeBtn");
  btn.disabled = false;
  btn.innerHTML = '<span class="btn-icon">⚡</span><span class="btn-text">Analyse Stock</span>';
}

function flashInput() {
  const input = document.getElementById("tickerInput");
  input.style.borderColor = "var(--red)";
  input.style.boxShadow   = "0 0 0 3px rgba(239,68,68,.2)";
  input.focus();
  setTimeout(() => { input.style.borderColor = ""; input.style.boxShadow = ""; }, 1200);
}

function actionClass(action) {
  const a = (action || "").toLowerCase().replace(/[_ ]/g, "-");
  if (a.includes("strong") && a.includes("buy"))  return "strong-buy";
  if (a.includes("strong") && a.includes("sell")) return "strong-sell";
  if (a.includes("buy"))  return "buy";
  if (a.includes("sell")) return "sell";
  return "hold";
}

function cap(s)        { return s ? s[0].toUpperCase() + s.slice(1) : s; }
function esc(str)      { return String(str).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
function fmtMcap(n)    { if (n >= 1e12) return (n/1e12).toFixed(2) + "T"; if (n >= 1e9) return (n/1e9).toFixed(2) + "B"; return (n/1e6).toFixed(0) + "M"; }
function fmtNum(n)     { return n?.toLocaleString?.() ?? String(n); }


// ══════════════════════════════════════════════════════════════════════════
// Chart.js Live Stock Price Chart
// ══════════════════════════════════════════════════════════════════════════
let currentChart = null;
let currentChartSymbol = null;
let currentChartPeriod = "1m";

async function loadStockChart(symbol, period = "1m") {
  if (!symbol) return;
  currentChartSymbol = symbol;
  currentChartPeriod = period;

  const card = document.getElementById("stockChartCard");
  if (card) card.style.display = "";

  // Highlight active timeframe button
  document.querySelectorAll("#timeframeSelector .tf-btn").forEach((btn) => {
    if (btn.dataset.period === period) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  try {
    const res = await fetch(`/api/chart/${encodeURIComponent(symbol)}/${period}`);
    const data = await res.json();

    if (data.error) {
      console.warn("Chart API error:", data.error);
      return;
    }

    renderPriceChart(data);
  } catch (err) {
    console.error("Failed to load chart data:", err);
  }
}

function renderPriceChart(data) {
  const canvas = document.getElementById("priceChartCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  // Header info
  const symEl = document.getElementById("chartSymbol");
  if (symEl) symEl.textContent = data.symbol;

  const priceEl = document.getElementById("chartCurrentPrice");
  if (priceEl) priceEl.textContent = `${data.currency} ${data.current_price.toLocaleString("en-IN", {minimumFractionDigits: 2})}`;

  const changeEl = document.getElementById("chartChangeBadge");
  if (changeEl) {
    const isPos = data.change >= 0;
    const sign = isPos ? "+" : "";
    changeEl.textContent = `${sign}${data.change.toFixed(2)} (${sign}${data.change_pct.toFixed(2)}%)`;
    changeEl.className = `chart-change badge ${isPos ? "badge-buy" : "badge-sell"}`;
  }

  const highEl = document.getElementById("chartHigh");
  if (highEl) highEl.textContent = `${data.currency} ${data.high.toLocaleString("en-IN", {minimumFractionDigits: 2})}`;

  const lowEl = document.getElementById("chartLow");
  if (lowEl) lowEl.textContent = `${data.currency} ${data.low.toLocaleString("en-IN", {minimumFractionDigits: 2})}`;

  if (currentChart) {
    currentChart.destroy();
  }

  const isPositive = data.change >= 0;
  const strokeColor = isPositive ? "#10b981" : "#ef4444";
  const gradientTop = isPositive ? "rgba(16, 185, 129, 0.25)" : "rgba(239, 68, 68, 0.25)";
  const gradientBottom = "rgba(16, 185, 129, 0.0)";

  const gradient = ctx.createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(0, gradientTop);
  gradient.addColorStop(1, gradientBottom);

  currentChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.labels,
      datasets: [
        {
          label: "Price",
          data: data.prices,
          borderColor: strokeColor,
          borderWidth: 2.5,
          pointRadius: data.prices.length > 60 ? 0 : 2,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: strokeColor,
          fill: true,
          backgroundColor: gradient,
          tension: 0.2,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(15, 23, 42, 0.95)",
          titleColor: "#94a3b8",
          bodyColor: "#f8fafc",
          borderColor: "rgba(255, 255, 255, 0.12)",
          borderWidth: 1,
          padding: 12,
          displayColors: false,
          callbacks: {
            label: function (context) {
              return ` Price: ${data.currency} ${context.parsed.y.toLocaleString("en-IN", {minimumFractionDigits: 2})}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(255, 255, 255, 0.04)" },
          ticks: { color: "#64748b", maxTicksLimit: 9, font: { family: "Inter", size: 11 } }
        },
        y: {
          grid: { color: "rgba(255, 255, 255, 0.04)" },
          ticks: {
            color: "#64748b",
            font: { family: "JetBrains Mono", size: 11 },
            callback: function (val) {
              return `${data.currency} ${val.toLocaleString("en-IN")}`;
            }
          }
        }
      }
    }
  });
}

function changeChartPeriod(period) {
  if (currentChartSymbol) {
    loadStockChart(currentChartSymbol, period);
  }
}

