"""Fundamentals Analyst Agent.

Analyzes financial reports, earnings, balance sheets, and company fundamentals
to assess intrinsic value and long-term investment potential.
"""

from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

from .state import AnalystState, AnalystReport


FUNDAMENTALS_PROMPT = """You are an AI Fundamental Stock Analysis Engine designed for analyzing companies listed in the Indian stock market.

Your task is to analyze the provided company fundamentals for {ticker} and classify the stock into exactly ONE of these categories:
* BUY
* HOLD
* SELL

IMPORTANT:
Do not make the classification based on a single metric. Evaluate all available parameters together.

==================================================
INPUT DATA FOR {ticker}
=======================
{financial_data}

CURRENT PRICE: {current_price}

==================================================
ANALYSIS FRAMEWORK
==================

Calculate a Fundamental Score out of 100 using the following weights:

1. BUSINESS GROWTH — 25 POINTS
   - Evaluate: Revenue Growth, Earnings Growth, EPS Growth.
   - Growth Score = 0–25.

2. PROFITABILITY — 25 POINTS
   - Evaluate: ROE, ROCE, Operating Margin, Profit Margin.
   - Profitability Score = 0–25.

3. FINANCIAL HEALTH — 20 POINTS
   - Evaluate: Debt/Equity, Interest Coverage.
   - Consider Sector (Banks/NBFCs operate with different leverage).
   - Financial Health Score = 0–20.

4. VALUATION — 20 POINTS
   - Evaluate: P/E, P/B, EV/EBITDA relative to growth and profitability.
   - Valuation Score = 0–20.

5. CASH FLOW — 10 POINTS
   - Evaluate: Operating Cash Flow, Free Cash Flow.
   - Cash Flow Score = 0–10.

TOTAL = 100 POINTS

==================================================
CLASSIFICATION RULE
===================
75–100: BUY
55–74: HOLD
0–54: SELL

==================================================
OUTPUT FORMAT
=============
Return the result ONLY as valid JSON.

Use exactly this structure:
{{
"classification": "BUY | HOLD | SELL",
"fundamental_score": 0,
"confidence": 0,

"scores": {{
"growth": 0,
"profitability": 0,
"financial_health": 0,
"valuation": 0,
"cash_flow": 0
}},

"analysis": {{
"growth": "",
"profitability": "",
"financial_health": "",
"valuation": "",
"cash_flow": ""
}},

"positive_factors": [
"",
"",
""
],

"risk_factors": [
"",
"",
""
],

"key_reason": "",

"data_quality": "HIGH | MEDIUM | LOW"
}}
"""


class FundamentalsAnalyst:
    """Fundamentals analyst that evaluates company financial health using the 100-point framework."""

    def __init__(self, llm: Optional[ChatGroq] = None):
        self.llm = llm or ChatGroq(model="qwen/qwen3.8-27b", temperature=0.1)
        self.prompt = ChatPromptTemplate.from_template(FUNDAMENTALS_PROMPT)
        self.parser = JsonOutputParser()

    def analyze(self, state: AnalystState) -> dict:
        """Analyze fundamentals and return updated state."""
        market_data = state.get("market_data", {})
        financial_reports = market_data.get("financial_reports", {})

        if not financial_reports:
            return {
                "fundamentals_analysis": {
                    "analyst_type": "fundamentals",
                    "signal": "HOLD",
                    "confidence": 0.0,
                    "reasoning": "No financial data available for analysis.",
                    "key_factors": [],
                }
            }

        financial_text = self._format_financial_data(financial_reports)

        chain = self.prompt | self.llm | self.parser

        try:
            result = chain.invoke({
                "ticker": state["ticker"],
                "financial_data": financial_text,
                "current_price": market_data.get("current_price", "N/A"),
            })

            signal = result.get("classification") or result.get("signal") or "HOLD"
            score = result.get("fundamental_score", 50)
            reasoning = result.get("key_reason") or str(result.get("analysis", {}))
            positives = result.get("positive_factors", [])
            risks = result.get("risk_factors", [])

            return {
                "fundamentals_analysis": {
                    "analyst_type": "fundamentals",
                    "signal": signal.upper(),
                    "confidence": float(result.get("confidence", 0.75)),
                    "reasoning": f"Fundamental Score: {score}/100. {reasoning}",
                    "key_factors": positives + risks,
                    "raw_report": result,
                }
            }
        except Exception as e:
            return {
                "fundamentals_analysis": {
                    "analyst_type": "fundamentals",
                    "signal": "HOLD",
                    "confidence": 0.0,
                    "reasoning": f"Analysis failed: {str(e)}",
                    "key_factors": [],
                }
            }

    def _format_financial_data(self, data: dict) -> str:
        """Format financial data dictionary into readable text."""
        lines = []
        for k, v in data.items():
            lines.append(f"  - {k}: {v}")
        return "\n".join(lines)

    def __call__(self, state: AnalystState) -> dict:
        """Make the analyst callable for LangGraph nodes."""
        return self.analyze(state)
