"""Analysts Team Coordinator — Indian Stock Market (NSE/BSE).

Runs 4 specialist analysts in sequence via LangGraph and consolidates
their signals into a DECISIVE BUY / SELL / HOLD recommendation.
"""

import time
from typing import Optional
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

from .state import AnalystState
from .news_analyst import NewsAnalyst
from .fundamentals_analyst import FundamentalsAnalyst
from .sentiment_analyst import SentimentAnalyst
from .technical_analyst import TechnicalAnalyst


CONSOLIDATION_PROMPT = """You are the Chief Investment Officer of a top Indian equity fund.

STOCK: {ticker} (NSE/BSE listed)

YOUR ANALYST TEAM REPORTS:

1. NEWS ANALYST: {news_signal} (Confidence: {news_confidence})
   {news_reasoning}
   Key factors: {news_factors}

2. FUNDAMENTALS ANALYST: {fundamentals_signal} (Confidence: {fundamentals_confidence})
   {fundamentals_reasoning}
   Key factors: {fundamentals_factors}

3. SENTIMENT ANALYST: {sentiment_signal} (Confidence: {sentiment_confidence})
   {sentiment_reasoning}
   Key factors: {sentiment_factors}

4. TECHNICAL ANALYST: {technical_signal} (Confidence: {technical_confidence})
   {technical_reasoning}
   Key factors: {technical_factors}

STRICT DECISION RULES (follow in order):
- Count BUY votes and SELL votes from all 4 analysts
- 3+ BUY votes → final_signal = BUY (regardless of HOLD votes)
- 3+ SELL votes → final_signal = SELL (regardless of HOLD votes)
- Technical BUY + Fundamentals BUY → final_signal = BUY
- Technical SELL + Fundamentals SELL → final_signal = SELL
- News BUY + Technical BUY → final_signal = BUY
- Only use HOLD if signals are genuinely 2-2 split or ALL 4 are neutral
- NEVER default to HOLD out of uncertainty — make a DECISION
- Position sizing: FULL (confidence>70%), HALF (50-70%), QUARTER (<50%)

Respond ONLY in valid JSON — no markdown, no extra text:
{{
    "final_signal": "BUY" | "SELL" | "HOLD",
    "confidence": <float 0.0-1.0>,
    "position_size": "FULL" | "HALF" | "QUARTER" | "NONE",
    "reasoning": "<3-4 sentences citing analyst vote count and key reasons>",
    "risk_factors": ["<risk1>", "<risk2>", "<risk3>"],
    "analyst_agreement": "<e.g. 3/4 analysts bullish, technical and fundamental aligned>",
    "time_horizon": "SHORT" | "MEDIUM" | "LONG"
}}
"""


class AnalystsTeam:
    """Coordinates 4 analyst agents and produces a consolidated trading recommendation."""

    def __init__(self, llm: Optional[ChatGroq] = None):
        self.llm = llm or ChatGroq(model="qwen/qwen3.8-27b", temperature=0.1)

        self.news_analyst        = NewsAnalyst(llm=self.llm)
        self.fundamentals_analyst = FundamentalsAnalyst(llm=self.llm)
        self.sentiment_analyst   = SentimentAnalyst(llm=self.llm)
        self.technical_analyst   = TechnicalAnalyst(llm=self.llm)

        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AnalystState)
        workflow.add_node("news_analyst",         self.news_analyst)
        workflow.add_node("fundamentals_analyst", self.fundamentals_analyst)
        workflow.add_node("sentiment_analyst",    self.sentiment_analyst)
        workflow.add_node("technical_analyst",    self.technical_analyst)
        workflow.add_node("consolidate",          self._consolidate_reports)

        workflow.set_entry_point("news_analyst")
        workflow.add_edge("news_analyst",         "fundamentals_analyst")
        workflow.add_edge("fundamentals_analyst", "sentiment_analyst")
        workflow.add_edge("sentiment_analyst",    "technical_analyst")
        workflow.add_edge("technical_analyst",    "consolidate")
        workflow.add_edge("consolidate",          END)
        return workflow.compile()

    def _invoke_with_retry(self, chain, inputs: dict, retries: int = 3) -> dict:
        last_err = None
        for attempt in range(retries):
            try:
                return chain.invoke(inputs)
            except Exception as e:
                last_err = e
                time.sleep(2 ** attempt)
        raise last_err

    def _consolidate_reports(self, state: AnalystState) -> dict:
        """Consolidate all 4 analyst reports into final recommendation."""
        news         = state.get("news_analysis")        or {}
        fundamentals = state.get("fundamentals_analysis") or {}
        sentiment    = state.get("sentiment_analysis")   or {}
        technical    = state.get("technical_analysis")   or {}

        # Count votes for rule-based override (belt-and-suspenders)
        signals = [
            news.get("signal", "HOLD"),
            fundamentals.get("signal", "HOLD"),
            sentiment.get("signal", "HOLD"),
            technical.get("signal", "HOLD"),
        ]
        buy_votes  = signals.count("BUY")
        sell_votes = signals.count("SELL")

        prompt = ChatPromptTemplate.from_template(CONSOLIDATION_PROMPT)
        parser = JsonOutputParser()
        chain  = prompt | self.llm | parser

        try:
            result = self._invoke_with_retry(chain, {
                "ticker":                  state["ticker"],
                "news_signal":             news.get("signal", "HOLD"),
                "news_confidence":         f"{float(news.get('confidence', 0.5)):.0%}",
                "news_reasoning":          (news.get("reasoning", "No analysis") or "")[:300],
                "news_factors":            ", ".join(news.get("key_factors", []))[:200] or "None",
                "fundamentals_signal":     fundamentals.get("signal", "HOLD"),
                "fundamentals_confidence": f"{float(fundamentals.get('confidence', 0.5)):.0%}",
                "fundamentals_reasoning":  (fundamentals.get("reasoning", "No analysis") or "")[:300],
                "fundamentals_factors":    ", ".join(fundamentals.get("key_factors", []))[:200] or "None",
                "sentiment_signal":        sentiment.get("signal", "HOLD"),
                "sentiment_confidence":    f"{float(sentiment.get('confidence', 0.5)):.0%}",
                "sentiment_reasoning":     (sentiment.get("reasoning", "No analysis") or "")[:300],
                "sentiment_factors":       ", ".join(sentiment.get("key_factors", []))[:200] or "None",
                "technical_signal":        technical.get("signal", "HOLD"),
                "technical_confidence":    f"{float(technical.get('confidence', 0.5)):.0%}",
                "technical_reasoning":     (technical.get("reasoning", "No analysis") or "")[:300],
                "technical_factors":       ", ".join(technical.get("key_factors", []))[:200] or "None",
            })

            llm_signal = result.get("final_signal", "HOLD")

            # Rule-based override: if LLM still says HOLD but votes clearly say otherwise
            if llm_signal == "HOLD":
                if buy_votes >= 3:
                    llm_signal = "BUY"
                elif sell_votes >= 3:
                    llm_signal = "SELL"
                elif buy_votes == 2 and sell_votes == 0:
                    llm_signal = "BUY"
                elif sell_votes == 2 and buy_votes == 0:
                    llm_signal = "SELL"

            return {
                "consolidated_report": {
                    "final_signal":    llm_signal,
                    "confidence":      float(result.get("confidence", 0.5)),
                    "position_size":   result.get("position_size", "QUARTER"),
                    "reasoning":       result.get("reasoning", ""),
                    "risk_factors":    result.get("risk_factors", []),
                    "analyst_agreement": result.get("analyst_agreement",
                                                    f"{buy_votes}/4 BUY, {sell_votes}/4 SELL"),
                    "time_horizon":    result.get("time_horizon", "MEDIUM"),
                    "individual_reports": {
                        "news":         news,
                        "fundamentals": fundamentals,
                        "sentiment":    sentiment,
                        "technical":    technical,
                    },
                }
            }

        except Exception as e:
            # Fallback: pure vote-based decision
            if buy_votes >= 3:
                fallback_signal = "BUY"
            elif sell_votes >= 3:
                fallback_signal = "SELL"
            else:
                fallback_signal = "HOLD"

            return {
                "consolidated_report": {
                    "final_signal":    fallback_signal,
                    "confidence":      0.45,
                    "position_size":   "QUARTER",
                    "reasoning":       f"LLM consolidation failed ({e}). Vote-based: {buy_votes} BUY, {sell_votes} SELL.",
                    "risk_factors":    ["Consolidation error — use individual signals"],
                    "analyst_agreement": f"{buy_votes}/4 BUY, {sell_votes}/4 SELL",
                    "time_horizon":    "MEDIUM",
                    "individual_reports": {
                        "news":         news,
                        "fundamentals": fundamentals,
                        "sentiment":    sentiment,
                        "technical":    technical,
                    },
                }
            }

    def analyze(self, ticker: str, market_data: dict) -> dict:
        """Run full analyst team on a ticker. Returns consolidated report."""
        initial_state: AnalystState = {
            "ticker":                ticker,
            "market_data":           market_data,
            "news_analysis":         None,
            "fundamentals_analysis": None,
            "sentiment_analysis":    None,
            "technical_analysis":    None,
            "consolidated_report":   None,
            "messages":              [],
        }
        result = self.graph.invoke(initial_state)
        return result.get("consolidated_report", {})
