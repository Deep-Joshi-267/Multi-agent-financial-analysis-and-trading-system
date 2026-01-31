"""Risky Advisor - Advocates for high-reward, high-risk strategies.

Evaluates trades from an aggressive growth perspective,
identifying opportunities for maximizing returns while
acknowledging but accepting higher risk levels.
"""

from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

from .state import RiskManagementState


RISKY_ADVISOR_PROMPT = """You are an aggressive risk advisor who advocates for high-reward, 
high-risk investment strategies. Your role is to identify opportunities for maximizing returns.

TICKER: {ticker}
CURRENT PRICE: ${current_price}

═══════════════════════════════════════════════════════════════
PROPOSED TRADE:
Action: {trade_action}
Position Size: {position_size}% of capital (${position_value})
Stop Loss: {stop_loss}%
Take Profit: {take_profit}%
Trader Confidence: {trader_confidence}
═══════════════════════════════════════════════════════════════

CIO DECISION:
Action: {cio_action}
Confidence: {cio_confidence}
Time Horizon: {time_horizon}

ANALYST SIGNAL: {analyst_signal} ({analyst_confidence} confidence)
RESEARCHER CONVICTION: {research_conviction}

MARKET CONDITIONS:
Volatility Indicators: {volatility}
Recent Price Change: {price_change}

PORTFOLIO CONTEXT:
Current Exposure: ${current_exposure}
Risk Tolerance: {risk_tolerance}

YOUR PERSPECTIVE (Aggressive/Growth-Focused):
As a risk-tolerant advisor, evaluate this trade considering:
1. Upside potential and reward opportunity
2. Whether position size could be INCREASED for greater gains
3. Aggressive entry/exit strategies
4. Market momentum and timing opportunities
5. Accept higher volatility for better returns

Respond in JSON format:
{{
    "overall_risk_level": "LOW" | "MODERATE" | "HIGH" | "CRITICAL",
    "risk_score": <float 0-1, your risk assessment>,
    "recommendation": "APPROVE" | "APPROVE_WITH_CONDITIONS" | "REDUCE_POSITION" | "REJECT",
    "position_adjustment": <float, multiplier e.g., 1.5 = increase 50%, 1.0 = keep same>,
    "market_volatility": {{
        "level": "LOW" | "MODERATE" | "HIGH" | "CRITICAL",
        "score": <float 0-1>,
        "description": "<assessment>",
        "opportunity": "<how volatility creates opportunity>"
    }},
    "liquidity_risk": {{
        "level": "LOW" | "MODERATE" | "HIGH" | "CRITICAL",
        "score": <float 0-1>,
        "description": "<assessment>"
    }},
    "concentration_risk": {{
        "level": "LOW" | "MODERATE" | "HIGH" | "CRITICAL",
        "score": <float 0-1>,
        "description": "<assessment>"
    }},
    "counterparty_risk": {{
        "level": "LOW" | "MODERATE" | "HIGH" | "CRITICAL",
        "score": <float 0-1>,
        "description": "<assessment>"
    }},
    "stop_loss_recommendation": <float, percentage - can be wider for more room>,
    "take_profit_recommendation": <float, percentage - aggressive target>,
    "hedging_suggestions": ["<suggestion>", ...],
    "reasoning": "<aggressive case for this trade>",
    "key_concerns": ["<concern despite bullish stance>", ...],
    "opportunities": ["<upside opportunity>", ...]
}}
"""


class RiskyAdvisor:
    """Aggressive risk advisor advocating for high-reward strategies."""

    def __init__(self, llm: Optional[ChatGroq] = None):
        self.llm = llm or ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)
        self.prompt = ChatPromptTemplate.from_template(RISKY_ADVISOR_PROMPT)
        self.parser = JsonOutputParser()

    def assess(self, state: RiskManagementState) -> dict:
        """Generate aggressive risk assessment."""
        trade_execution = state.get("trade_execution", {})
        trade_decision = trade_execution.get("trade_decision", {})
        final_decision = state.get("final_decision", {})
        analyst_report = state.get("analyst_report", {})
        research_report = state.get("research_report", {})
        market_data = state.get("market_data", {})

        available_capital = state.get("available_capital", 100000)
        position_percent = trade_decision.get("quantity_percent", 0) * 100
        position_value = available_capital * trade_decision.get("quantity_percent", 0)

        try:
            chain = self.prompt | self.llm | self.parser
            result = chain.invoke({
                "ticker": state["ticker"],
                "current_price": market_data.get("current_price", 0),
                "trade_action": trade_decision.get("action", "HOLD"),
                "position_size": position_percent,
                "position_value": position_value,
                "stop_loss": trade_decision.get("stop_loss_percent", 5),
                "take_profit": trade_decision.get("take_profit_percent", 10),
                "trader_confidence": f"{trade_decision.get('confidence', 0):.0%}",
                "cio_action": final_decision.get("action", "N/A"),
                "cio_confidence": f"{final_decision.get('confidence', 0):.0%}",
                "time_horizon": final_decision.get("time_horizon", "MEDIUM"),
                "analyst_signal": analyst_report.get("final_signal", "N/A"),
                "analyst_confidence": f"{analyst_report.get('confidence', 0):.0%}",
                "research_conviction": research_report.get("position_conviction", "N/A"),
                "volatility": market_data.get("volatility", "Unknown"),
                "price_change": f"{market_data.get('price_change_percent', 0):.2f}%",
                "current_exposure": state.get("current_exposure", 0),
                "risk_tolerance": state.get("risk_tolerance", "moderate"),
            })

            assessment = {
                "advisor_type": "risky",
                "overall_risk_level": result.get("overall_risk_level", "MODERATE"),
                "risk_score": float(result.get("risk_score", 0.5)),
                "recommendation": result.get("recommendation", "APPROVE"),
                "position_adjustment": float(result.get("position_adjustment", 1.0)),
                "market_volatility": result.get("market_volatility", {}),
                "liquidity_risk": result.get("liquidity_risk", {}),
                "concentration_risk": result.get("concentration_risk", {}),
                "counterparty_risk": result.get("counterparty_risk", {}),
                "stop_loss_recommendation": result.get("stop_loss_recommendation"),
                "take_profit_recommendation": result.get("take_profit_recommendation"),
                "hedging_suggestions": result.get("hedging_suggestions", []),
                "reasoning": result.get("reasoning", ""),
                "key_concerns": result.get("key_concerns", []),
                "opportunities": result.get("opportunities", []),
            }

            return {"risky_assessment": assessment}

        except Exception as e:
            return {
                "risky_assessment": {
                    "advisor_type": "risky",
                    "error": str(e),
                    "recommendation": "HOLD_FOR_REVIEW",
                }
            }

    def __call__(self, state: RiskManagementState) -> dict:
        """Make advisor callable for LangGraph."""
        return self.assess(state)
