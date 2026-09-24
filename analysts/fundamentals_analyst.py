"""Fundamentals Analyst Agent.

Analyzes financial reports, earnings, balance sheets, and company fundamentals
to assess intrinsic value and long-term investment potential.
"""

from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

from .state import AnalystState, AnalystReport


FUNDAMENTALS_PROMPT = """You are a senior fundamental analyst with expertise in financial statement analysis.

TASK: Analyze the financial data for {ticker} and assess investment potential.

FINANCIAL DATA:
{financial_data}

CURRENT PRICE: ${current_price}

Evaluate the following:
1. Revenue growth and profitability trends
2. Balance sheet strength (debt ratios, liquidity)
3. Cash flow quality and sustainability
4. Valuation metrics (P/E, P/B, EV/EBITDA if available)
5. Competitive positioning and moat

Respond in JSON format:
{{
    "signal": "BUY" | "SELL" | "HOLD",
    "confidence": <float 0.0-1.0>,
    "reasoning": "<detailed fundamental analysis>",
    "key_factors": ["<factor1>", "<factor2>", ...]
}}
"""


class FundamentalsAnalyst:
    """Fundamentals analyst that evaluates company financial health."""

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

            return {
                "fundamentals_analysis": {
                    "analyst_type": "fundamentals",
                    "signal": result.get("signal", "HOLD"),
                    "confidence": float(result.get("confidence", 0.5)),
                    "reasoning": result.get("reasoning", ""),
                    "key_factors": result.get("key_factors", []),
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
        for category, values in data.items():
            lines.append(f"\n{category.upper()}:")
            if isinstance(values, dict):
                for key, val in values.items():
                    lines.append(f"  - {key}: {val}")
            else:
                lines.append(f"  {values}")
        return "\n".join(lines)

    def __call__(self, state: AnalystState) -> dict:
        """Make the analyst callable for LangGraph nodes."""
        return self.analyze(state)
