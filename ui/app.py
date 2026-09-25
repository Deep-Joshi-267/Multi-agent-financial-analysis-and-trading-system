"""
TradingAgents Web UI - Flask Application (v4)
- Model: qwen/qwen3.8-27b via Groq
- Per-stage error handling — crash in one stage emits error event, doesn't kill stream
- Qwen3 thinking-mode disabled (no_think system prompt)
- Full traceback logged server-side
"""

import json
import math
import os
import sys
import threading
import time
import queue
import logging
import traceback
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS

# ── Path Setup ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

DIST_DIR = Path(__file__).parent / "dist"
app = Flask(__name__, template_folder="templates", static_folder="dist" if DIST_DIR.exists() else "static", static_url_path="")
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("TradingUI")

# ── Model config ───────────────────────────────────────────────────────────
PRIMARY_MODEL   = "qwen/qwen3.8-27b"
MARKET          = "IN"   # IN = Indian market (NSE/BSE)
FALLBACK_MODELS = ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]

# ── Job store ──────────────────────────────────────────────────────────────
analysis_jobs: dict = {}


# ── Helpers ────────────────────────────────────────────────────────────────

def _safe(d):
    """Recursively make a value JSON-serialisable."""
    if isinstance(d, dict):
        return {k: _safe(v) for k, v in d.items()}
    if isinstance(d, list):
        return [_safe(i) for i in d]
    if isinstance(d, float):
        return None if (math.isnan(d) or math.isinf(d)) else d
    return d


def _emit(q: queue.Queue, stage: str, message: str,
          status: str = "running", data: dict = None):
    payload = {"stage": stage, "message": message,
               "status": status, "ts": datetime.utcnow().isoformat()}
    if data:
        payload["data"] = _safe(data)
    q.put(payload)
    logger.info(f"[{stage.upper()}:{status}] {message[:120]}")


def _get_llm(temperature: float = 0.1):
    """Return a working ChatGroq instance, trying fallbacks."""
    from langchain_groq import ChatGroq
    for model in [PRIMARY_MODEL] + FALLBACK_MODELS:
        try:
            llm = ChatGroq(model=model, temperature=temperature)
            logger.info(f"Using model: {model}")
            return llm
        except Exception as e:
            logger.warning(f"Model {model} init failed: {e}")
    raise RuntimeError("No Groq models available. Check GROQ_API_KEY.")


# ══════════════════════════════════════════════════════════════════════════════
# Analysis Engine
# ══════════════════════════════════════════════════════════════════════════════

def run_analysis(job_id: str, ticker: str, capital: float,
                 risk: str, quick: bool, q: queue.Queue):
    # Initialise a single shared LLM instance for all stages
    llm = _get_llm(temperature=0.1)
    try:
        # ── Stage 1: Fetch Market Data ───────────────────────────────────
        _emit(q, "data", f"Fetching live market data for {ticker} via Yahoo Finance...")
        try:
            from data import MarketDataFetcher
            from data.stock_data import StockDataFetcher

            mdf = MarketDataFetcher(verbose=False)
            sdf = StockDataFetcher(verbose=False)

            market_data  = mdf.fetch_market_data(ticker, news_days=7, price_days=90, news_limit=10)
            company_info = sdf.get_company_info(ticker)
            indicators   = sdf.get_technical_indicators(ticker, days=365)

            price      = float(market_data.get("current_price") or 0)
            news_count = len(market_data.get("news_articles") or [])
            rsi_val    = float(indicators.get("rsi_14") or 0)
            momentum   = float(indicators.get("momentum_5d") or 0)

            data_summary = _safe({
                "company":      company_info.get("name", ticker),
                "sector":       company_info.get("sector", "N/A"),
                "industry":     company_info.get("industry", "N/A"),
                "current_price": price,
                "market_cap":   company_info.get("market_cap"),
                "pe_ratio":     company_info.get("pe_ratio"),
                "forward_pe":   company_info.get("forward_pe"),
                "eps":          company_info.get("eps"),
                "beta":         company_info.get("beta"),
                "52w_high":     company_info.get("52_week_high"),
                "52w_low":      company_info.get("52_week_low"),
                "avg_volume":   company_info.get("avg_volume"),
                "rsi_14":       rsi_val,
                "macd":         indicators.get("macd"),
                "macd_signal":  indicators.get("macd_signal"),
                "sma_20":       indicators.get("sma_20"),
                "sma_50":       indicators.get("sma_50"),
                "sma_200":      indicators.get("sma_200"),
                "momentum_5d":  momentum,
                "momentum_20d": indicators.get("momentum_20d"),
                "bb_upper":     indicators.get("bb_upper"),
                "bb_lower":     indicators.get("bb_lower"),
                "news_count":   news_count,
            })

            _emit(q, "data",
                  f"Data ready: Rs.{price:.2f} | RSI {rsi_val:.1f} | {news_count} news | {momentum:+.1f}% 5d",
                  status="done", data=data_summary)

        except Exception as e:
            logger.error(f"Data fetch failed: {traceback.format_exc()}")
            _emit(q, "data", f"Data fetch error: {e} — using empty data", status="error")
            market_data = {}; data_summary = {}; price = 0; company_info = {}

        # ── Stage 2: Analyst Team ────────────────────────────────────────
        _emit(q, "analysts", "Running 4 AI analysts: News, Fundamentals, Sentiment, Technical...")
        analyst_summary = {}
        final_signal = "HOLD"
        conf = 0.5
        try:
            from analysts import AnalystsTeam
            team = AnalystsTeam()
            analyst_report = team.analyze(ticker=ticker, market_data=market_data)

            ind   = analyst_report.get("individual_reports", {})
            n_rep = ind.get("news", {})
            f_rep = ind.get("fundamentals", {})
            s_rep = ind.get("sentiment", {})
            t_rep = ind.get("technical", {})
            final_signal = analyst_report.get("final_signal", "HOLD")
            conf = float(analyst_report.get("confidence", 0.5))

            analyst_summary = _safe({
                "final_signal":            final_signal,
                "confidence":              conf,
                "reasoning":               analyst_report.get("reasoning", ""),
                "position_size":           analyst_report.get("position_size", "N/A"),
                "time_horizon":            analyst_report.get("time_horizon", "MEDIUM"),
                "risk_factors":            analyst_report.get("risk_factors", []),
                "analyst_agreement":       analyst_report.get("analyst_agreement", ""),
                "news_signal":             n_rep.get("signal", "N/A"),
                "news_confidence":         n_rep.get("confidence", 0),
                "news_reasoning":          n_rep.get("reasoning", ""),
                "news_key_factors":        n_rep.get("key_factors", []),
                "fundamentals_signal":     f_rep.get("signal", "N/A"),
                "fundamentals_confidence": f_rep.get("confidence", 0),
                "fundamentals_reasoning":  f_rep.get("reasoning", ""),
                "fundamentals_key_factors":f_rep.get("key_factors", []),
                "sentiment_signal":        s_rep.get("signal", "N/A"),
                "sentiment_confidence":    s_rep.get("confidence", 0),
                "sentiment_reasoning":     s_rep.get("reasoning", ""),
                "sentiment_key_factors":   s_rep.get("key_factors", []),
                "technical_signal":        t_rep.get("signal", "N/A"),
                "technical_confidence":    t_rep.get("confidence", 0),
                "technical_reasoning":     t_rep.get("reasoning", ""),
                "technical_key_factors":   t_rep.get("key_factors", []),
            })

            _emit(q, "analysts",
                  f"Consensus: {final_signal} ({conf:.0%} confidence) — "
                  f"News:{n_rep.get('signal','?')} Fund:{f_rep.get('signal','?')} "
                  f"Sent:{s_rep.get('signal','?')} Tech:{t_rep.get('signal','?')}",
                  status="done", data=analyst_summary)

        except Exception as e:
            logger.error(f"Analyst team failed: {traceback.format_exc()}")
            _emit(q, "analysts", f"Analyst error: {e}", status="error")

        # Quick mode — stop here
        if quick:
            _emit(q, "complete",
                  f"Analysis complete: {final_signal} for {ticker} @ Rs.{price:.2f}",
                  status="done",
                  data={"result": {
                      "ticker": ticker, "action": final_signal,
                      "confidence": conf,
                      "reasoning": analyst_summary.get("reasoning", ""),
                      "position_size": analyst_summary.get("position_size", "N/A"),
                      "time_horizon": analyst_summary.get("time_horizon", "MEDIUM"),
                      "risk_factors": analyst_summary.get("risk_factors", []),
                      "analyst_report": analyst_summary,
                      "market_data": data_summary,
                      "mode": "quick",
                  }})
            return

        # ── Stage 3: Researcher Debate ───────────────────────────────────
        _emit(q, "researchers", "Bull vs Bear researcher debate starting (2 rounds)...")
        research_summary = {}
        rec_action = final_signal
        try:
            from researchers import ResearcherTeam
            # Reuse the same LLM instance to avoid extra init overhead
            r_team = ResearcherTeam(llm=llm, max_debate_rounds=2)
            research = r_team.research(
                ticker=ticker,
                analyst_report=analyst_summary,
                market_data=market_data,
            ) or {}

            rec_action  = research.get("recommended_action", final_signal)
            conviction  = research.get("position_conviction", "MEDIUM")
            thesis      = research.get("investment_thesis", "")
            bull_case   = research.get("bull_case_summary", "")
            bear_case   = research.get("bear_case_summary", "")
            risk_reward = research.get("risk_reward_assessment", research.get("risk_reward_ratio", ""))

            research_summary = _safe({
                "recommended_action":   rec_action,
                "conviction":           conviction,
                "investment_thesis":    thesis,
                "bull_case_summary":    bull_case,
                "bear_case_summary":    bear_case,
                "risk_reward_assessment": risk_reward,
                "risk_reward_ratio":    risk_reward,  # alias for backward compat
                "key_risks":            research.get("key_risks", []),
                "key_opportunities":    research.get("key_opportunities", []),
                "consensus_points":     research.get("consensus_points", []),
                "key_disagreements":    research.get("key_disagreements", []),
                "position_conviction":  conviction,
            })

            _emit(q, "researchers",
                  f"Debate complete: {rec_action} (conviction: {conviction})",
                  status="done", data=research_summary)

        except Exception as e:
            logger.error(f"Researcher failed: {traceback.format_exc()}")
            _emit(q, "researchers", f"Researcher error: {e}", status="error")
            research_summary = {
                "recommended_action": rec_action,
                "investment_thesis": "",
                "bull_case_summary": "",
                "bear_case_summary": "",
                "position_conviction": "LOW",
                "key_risks": [],
                "key_opportunities": [],
            }

        # ── Stage 4: CIO Decision ────────────────────────────────────────
        _emit(q, "cio", "CIO synthesising analyst + research inputs...")
        cio_action    = rec_action
        cio_conf      = conf
        cio_reasoning = analyst_summary.get("reasoning", "")
        cio_data      = {}
        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import JsonOutputParser

            FINAL_DECISION_PROMPT = """You are the Chief Investment Officer making the final trading decision.

TICKER: {ticker}

ANALYST TEAM REPORT:
Signal: {analyst_signal}
Confidence: {analyst_confidence}
Reasoning: {analyst_reasoning}

RESEARCHER TEAM REPORT:
Investment Thesis: {research_thesis}
Bull Case: {bull_case}
Bear Case: {bear_case}
Risk/Reward: {risk_reward}
Researcher Recommendation: {research_action}
Conviction: {research_conviction}

KEY RISKS: {key_risks}
KEY OPPORTUNITIES: {key_opportunities}

CONSENSUS POINTS: {consensus_points}
DISAGREEMENTS: {disagreements}

Make the final trading decision. Respond ONLY in JSON format:
{{
    "final_action": "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL",
    "confidence": <float 0.0-1.0>,
    "position_size": "FULL" | "THREE_QUARTER" | "HALF" | "QUARTER" | "NONE",
    "time_horizon": "SHORT" | "MEDIUM" | "LONG",
    "entry_strategy": "<how to enter the position>",
    "exit_strategy": "<when to exit or stop-loss levels>",
    "risk_management": "<position sizing and risk controls>",
    "key_catalysts": ["<catalyst>"],
    "reasoning": "<comprehensive reasoning>",
    "dissenting_view": "<counter-arguments>"
}}"""

            decision_prompt = ChatPromptTemplate.from_template(FINAL_DECISION_PROMPT)
            parser = JsonOutputParser()
            chain = decision_prompt | llm | parser

            cio_result = chain.invoke({
                "ticker":               ticker,
                "analyst_signal":       analyst_summary.get("final_signal", "N/A"),
                "analyst_confidence":   f"{analyst_summary.get('confidence', 0):.0%}",
                "analyst_reasoning":    analyst_summary.get("reasoning", "N/A"),
                "research_thesis":      research_summary.get("investment_thesis", "N/A"),
                "bull_case":            research_summary.get("bull_case_summary", "N/A"),
                "bear_case":            research_summary.get("bear_case_summary", "N/A"),
                "risk_reward":          research_summary.get("risk_reward_assessment", "N/A"),
                "research_action":      research_summary.get("recommended_action", "N/A"),
                "research_conviction":  research_summary.get("position_conviction", "N/A"),
                "key_risks":            ", ".join(research_summary.get("key_risks", [])[:5]),
                "key_opportunities":    ", ".join(research_summary.get("key_opportunities", [])[:5]),
                "consensus_points":     ", ".join(research_summary.get("consensus_points", [])[:3]),
                "disagreements":        ", ".join(research_summary.get("key_disagreements", [])[:3]),
            })

            cio_action    = cio_result.get("final_action", rec_action)
            cio_conf      = float(cio_result.get("confidence", conf))
            cio_reasoning = cio_result.get("reasoning", cio_reasoning)

            cio_data = _safe({
                "action":           cio_action,
                "confidence":       cio_conf,
                "reasoning":        cio_reasoning,
                "position_size":    cio_result.get("position_size", "N/A"),
                "time_horizon":     cio_result.get("time_horizon", "MEDIUM"),
                "entry_strategy":   cio_result.get("entry_strategy", ""),
                "exit_strategy":    cio_result.get("exit_strategy", ""),
                "risk_management":  cio_result.get("risk_management", ""),
                "key_catalysts":    cio_result.get("key_catalysts", []),
                "dissenting_view":  cio_result.get("dissenting_view", ""),
            })

            _emit(q, "cio",
                  f"CIO decision: {cio_action} ({cio_conf:.0%} confidence)",
                  status="done", data=cio_data)

        except Exception as e:
            logger.error(f"CIO decision failed: {traceback.format_exc()}")
            _emit(q, "cio", f"CIO error: {e} — using researcher recommendation", status="error")
            cio_data = {"action": cio_action, "confidence": cio_conf, "reasoning": cio_reasoning}

        # ── Stage 5: Trader Execution ────────────────────────────────────
        _emit(q, "traders", f"Trader team computing execution plan for {cio_action}...")
        trade_summary = {}
        try:
            from traders import TraderTeam

            # Build a final_decision dict that matches what TraderAgent expects
            final_decision_for_trader = {
                "ticker":        ticker,
                "action":        cio_action,
                "confidence":    cio_conf,
                "position_size": cio_data.get("position_size", "HALF"),
                "time_horizon":  cio_data.get("time_horizon", "MEDIUM"),
                "entry_strategy": cio_data.get("entry_strategy", ""),
                "exit_strategy":  cio_data.get("exit_strategy", ""),
                "reasoning":     cio_reasoning,
                "analyst_report":  analyst_summary,
                "research_report": research_summary,
            }

            t_team = TraderTeam(
                llm=llm,
                max_iterations=2,
                score_threshold=0.5,
                require_human_approval=False,   # Web UI: no CLI blocking input
            )

            trade_result = t_team.execute_trade(
                ticker=ticker,
                analyst_report=analyst_summary,
                research_report=research_summary,
                final_decision=final_decision_for_trader,
                market_data=market_data,
                available_capital=capital,
                risk_tolerance=risk,
                portfolio=[],
            )

            td = trade_result.get("trade_decision") or {}
            ep = float(market_data.get("current_price") or price)
            sl_pct = float(td.get("stop_loss_percent") or 5)
            tp_pct = float(td.get("take_profit_percent") or 10)

            if td.get("action", "HOLD") == "BUY":
                sl_price = ep * (1 - sl_pct / 100)
                tp_price = ep * (1 + tp_pct / 100)
            else:
                sl_price = ep * (1 + sl_pct / 100)
                tp_price = ep * (1 - tp_pct / 100)

            qty_pct = float(td.get("quantity_percent") or 0)
            qty = int((capital * qty_pct) / ep) if ep > 0 and qty_pct > 0 else 0

            trade_summary = _safe({
                "action":       td.get("action", cio_action),
                "order_type":   td.get("order_type", "MARKET"),
                "quantity":     qty,
                "quantity_percent": qty_pct,
                "entry_price":  ep,
                "stop_loss":    round(sl_price, 2),
                "take_profit":  round(tp_price, 2),
                "status":       trade_result.get("execution_status", "PLANNED"),
                "reasoning":    td.get("reasoning", ""),
                "confidence":   td.get("confidence", cio_conf),
                "risk_reward":  td.get("risk_reward_ratio", 1.0),
                "entry_timing": td.get("entry_timing", "IMMEDIATE"),
                "iterations":   trade_result.get("iterations_used", 1),
            })

            action_str = trade_summary.get("action", cio_action)
            ep_str = f"Rs.{ep:.2f}" if ep else "market"
            qty_str = str(qty) if qty > 0 else "N/A"
            _emit(q, "traders",
                  f"Execution plan: {action_str} {qty_str} shares @ {ep_str} "
                  f"| SL: Rs.{round(sl_price,2)} | TP: Rs.{round(tp_price,2)}",
                  status="done", data=trade_summary)

        except Exception as e:
            logger.error(f"Trader failed: {traceback.format_exc()}")
            _emit(q, "traders", f"Trader error: {e}", status="error")
            trade_summary = {
                "action": cio_action,
                "status": "ERROR",
                "entry_price": price,
            }

        # ── Final result ─────────────────────────────────────────────────
        _emit(q, "complete",
              f"Analysis complete: {cio_action} for {ticker} @ Rs.{price:.2f}",
              status="done",
              data={"result": {
                  "ticker":        ticker,
                  "action":        cio_action,
                  "confidence":    cio_conf,
                  "reasoning":     cio_reasoning,
                  "position_size": cio_data.get("position_size", analyst_summary.get("position_size", "N/A")),
                  "time_horizon":  cio_data.get("time_horizon", analyst_summary.get("time_horizon", "MEDIUM")),
                  "risk_factors":  analyst_summary.get("risk_factors", []),
                  "key_catalysts": cio_data.get("key_catalysts", []),
                  "entry_strategy": cio_data.get("entry_strategy", ""),
                  "exit_strategy":  cio_data.get("exit_strategy", ""),
                  "dissenting_view": cio_data.get("dissenting_view", ""),
                  "analyst_report":  analyst_summary,
                  "research_report": research_summary,
                  "trade_execution": trade_summary,
                  "market_data":     data_summary,
                  "mode":            "full",
              }})

    except Exception as e:
        logger.error(f"Fatal analysis error: {traceback.format_exc()}")
        _emit(q, "error", f"Fatal error: {e}", status="error")
    finally:
        q.put(None)   # always close the stream


# ══════════════════════════════════════════════════════════════════════════════
# Routes
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    if (DIST_DIR / "index.html").exists():
        return app.send_static_file("index.html")
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    body    = request.get_json() or {}
    ticker  = body.get("ticker", "").strip().upper()
    capital = float(body.get("capital", 100000))
    risk    = body.get("risk", "moderate")
    quick   = bool(body.get("quick", False))

    # Auto-append .NS for Indian stocks
    if "." not in ticker:
        ticker += ".NS"

    if not ticker:
        return jsonify({"error": "Ticker is required"}), 400

    job_id  = f"{ticker}_{int(time.time() * 1000)}"
    event_q = queue.Queue()
    analysis_jobs[job_id] = event_q

    threading.Thread(
        target=run_analysis,
        args=(job_id, ticker, capital, risk, quick, event_q),
        daemon=True,
    ).start()

    return jsonify({"job_id": job_id})


@app.route("/api/stream/<job_id>")
def stream(job_id: str):
    event_q = analysis_jobs.get(job_id)
    if not event_q:
        return jsonify({"error": "Job not found"}), 404

    def generate():
        while True:
            try:
                event = event_q.get(timeout=300)
                if event is None:
                    yield "data: [DONE]\n\n"
                    break
                yield f"data: {json.dumps(event)}\n\n"
            except queue.Empty:
                yield 'data: {"stage":"heartbeat"}\n\n'

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.route("/api/quote/<symbol>")
def quick_quote(symbol: str):
    try:
        from data.stock_data import StockDataFetcher
        f    = StockDataFetcher()
        info = f.get_company_info(symbol.upper())
        ind  = f.get_technical_indicators(symbol.upper(), days=60)
        return jsonify(_safe({
            "symbol":    symbol.upper(),
            "name":      info.get("name", symbol),
            "price":     ind.get("current_price"),
            "rsi":       ind.get("rsi_14"),
            "momentum":  ind.get("momentum_5d"),
            "sma_20":    ind.get("sma_20"),
            "sma_50":    ind.get("sma_50"),
            "sector":    info.get("sector"),
            "pe_ratio":  info.get("pe_ratio"),
            "market_cap": info.get("market_cap"),
            "52w_high":  info.get("52_week_high"),
            "52w_low":   info.get("52_week_low"),
        }))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chart/<symbol>/<period>")
def get_chart_data(symbol: str, period: str):
    try:
        import yfinance as yf
        ticker_str = symbol.strip().upper()

        us_tickers = {"AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "TSLA", "NVDA", "META", "NFLX", "AMD", "SPY", "QQQ"}
        if "." not in ticker_str and ticker_str not in us_tickers:
            norm_ticker = f"{ticker_str}.NS"
        else:
            norm_ticker = ticker_str

        period_map = {
            "1d":  ("1d",  "5m"),
            "1m":  ("1mo", "1d"),
            "6m":  ("6mo", "1d"),
            "ytd": ("ytd", "1d"),
            "5y":  ("5y",  "1wk"),
        }

        p, i = period_map.get(period.lower(), ("1mo", "1d"))
        t = yf.Ticker(norm_ticker)
        df = t.history(period=p, interval=i)

        if df.empty:
            alt_ticker = ticker_str.replace(".NS", "") if norm_ticker.endswith(".NS") else f"{ticker_str}.NS"
            t = yf.Ticker(alt_ticker)
            df = t.history(period=p, interval=i)
            if df.empty:
                return jsonify({"error": f"No price history found for {symbol}"}), 404
            norm_ticker = alt_ticker

        labels = []
        prices = []
        volumes = []

        for idx, row in df.iterrows():
            close_val = round(float(row["Close"]), 2)
            if math.isnan(close_val):
                continue
            prices.append(close_val)
            volumes.append(int(row["Volume"]) if not math.isnan(row["Volume"]) else 0)

            dt = idx.to_pydatetime()
            if p == "1d":
                labels.append(dt.strftime("%H:%M"))
            elif p in ["1mo", "6mo", "ytd"]:
                labels.append(dt.strftime("%d %b"))
            else:
                labels.append(dt.strftime("%b %Y"))

        if not prices:
            return jsonify({"error": "No price points available"}), 404

        start_p = prices[0]
        curr_p  = prices[-1]
        change  = round(curr_p - start_p, 2)
        change_pct = round((change / start_p) * 100, 2) if start_p else 0.0
        high_p  = round(float(df["High"].max()), 2)
        low_p   = round(float(df["Low"].min()), 2)
        currency = "$" if norm_ticker in us_tickers else "Rs."

        return jsonify(_safe({
            "symbol": norm_ticker,
            "period": period.lower(),
            "labels": labels,
            "prices": prices,
            "volumes": volumes,
            "start_price": start_p,
            "current_price": curr_p,
            "change": change,
            "change_pct": change_pct,
            "high": high_p,
            "low": low_p,
            "currency": currency,
        }))
    except Exception as e:
        logger.error(f"Error fetching chart data for {symbol}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/indices")
def get_indices():
    """Fetch live NSE index data: NIFTY 50, SENSEX, NIFTY BANK, NIFTY IT."""
    try:
        import yfinance as yf

        INDICES = {
            "NIFTY 50":   "^NSEI",
            "SENSEX":     "^BSESN",
            "NIFTY BANK": "^NSEBANK",
            "NIFTY IT":   "^CNXIT",
        }

        result = {}
        for display_name, symbol in INDICES.items():
            try:
                ticker = yf.Ticker(symbol)
                # Get today's intraday data for current price + day range
                hist = ticker.history(period="2d", interval="1d")
                info = ticker.fast_info  # lightweight, no heavy API calls

                if hist.empty:
                    raise ValueError(f"No data for {symbol}")

                today   = hist.iloc[-1]
                prev    = hist.iloc[-2] if len(hist) >= 2 else hist.iloc[-1]

                current = round(float(today["Close"]), 2)
                prev_cl = round(float(prev["Close"]), 2)
                change  = round(current - prev_cl, 2)
                change_pct = round((change / prev_cl) * 100, 2) if prev_cl else 0.0
                day_high = round(float(today["High"]), 2)
                day_low  = round(float(today["Low"]), 2)
                volume   = int(today["Volume"]) if not math.isnan(float(today["Volume"])) else 0

                # Format volume
                if volume >= 10_000_000:
                    vol_str = f"{volume / 10_000_000:.1f}Cr"
                elif volume >= 100_000:
                    vol_str = f"{volume / 100_000:.1f}L"
                else:
                    vol_str = str(volume)

                trend = "up" if change > 0 else ("down" if change < 0 else "neutral")

                result[display_name] = {
                    "symbol":     symbol,
                    "value":      current,
                    "change":     change,
                    "changePct":  change_pct,
                    "high":       day_high,
                    "low":        day_low,
                    "vol":        vol_str,
                    "trend":      trend,
                    "prev_close": prev_cl,
                }
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol}: {e}")
                result[display_name] = None

        advancing = sum(1 for v in result.values() if v and v["trend"] == "up")
        declining = sum(1 for v in result.values() if v and v["trend"] == "down")

        return jsonify(_safe({
            "indices": result,
            "advancing": advancing,
            "declining": declining,
            "timestamp": datetime.utcnow().isoformat(),
        }))

    except Exception as e:
        logger.error(f"Indices fetch error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/health")
def health():
    key = os.getenv("GROQ_API_KEY", "")
    return jsonify({
        "status": "ok",
        "model":  PRIMARY_MODEL,
        "groq_configured": bool(key and key.startswith("gsk_") and len(key) > 20),
        "timestamp": datetime.utcnow().isoformat(),
    })


if __name__ == "__main__":
    port = int(os.getenv("UI_PORT", 5050))
    print(f"\n  TradingAgents UI  ->  http://localhost:{port}")
    print(f"  Model: {PRIMARY_MODEL}\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
