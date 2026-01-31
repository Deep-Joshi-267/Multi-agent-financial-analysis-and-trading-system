"""Safe Advisor - Emphasizes conservative investment strategy.

Evaluates trades from a risk-averse perspective,
prioritizing capital preservation and risk mitigation.
"""

from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

from .state import RiskManagementState


SAFE_ADVISOR_PROMPT = """You are a conservative risk advisor who emphasizes capital preservation 
and risk mitigation. Your role is to protect against adverse market events.

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

YOUR PERSPECTIVE (Conservative/Risk-Averse):
As a conservative advisor, evaluate this trade considering:
1. Capital preservation as top priority
2. Whether position size should be REDUCED for safety
3. Tight stop-loss and conservative targets
4. Worst-case scenario analysis
5. Regulatory compliance and risk limits

Respond in JSON format:
{{
    "overall_risk_level": "LOW" | "MODERATE" | "HIGH" | "CRITICAL",
    "risk_score": <float 0-1, conservative risk assessment>,
    "recommendation": "APPROVE" | "APPROVE_WITH_CONDITIONS" | "REDUCE_POSITION" | "REJECT",
    "position_adjustment": <float, multiplier e.g., 0.5 = reduce 50%, 0.75 = reduce 25%>,
    "market_volatility": {{
        "level": "LOW" | "MODERATE" | "HIGH" | "CRITICAL",
        "score": <float 0-1>,
        "description": "<conservative assessment>",
        "mitigation": "<required mitigation>"
    }},
    "liquidity_risk": {{
        "level": "LOW" | "MODERATE" | "HIGH" | "CRITICAL",
        "score": <float 0-1>,
        "description": "<assessment>",
        "mitigation": "<required mitigation>"
    }},
    "concentration_risk": {{
        "level": "LOW" | "MODERATE" | "HIGH" | "CRITICAL",
        "score": <float 0-1>,
        "description": "<assessment>",
        "mitigation": "<required mitigation>"
    }},
    "counterparty_risk": {{
        "level": "LOW" | "MODERATE" | "HIGH" | "CRITICAL",
        "score": <float 0-1>,
        "description": "<assessment>",
        "mitigation": "<required mitigation>"
    }},
    "stop_loss_recommendation": <float, percentage - tight stop for protection>,
    "take_profit_recommendation": <float, percentage - conservative target>,
    "hedging_suggestions": ["<required hedge>", ...],
    "diversification_suggestions": ["<required diversification>", ...],
    "risk_limits": {{
        "max_position_size": <float, percentage of capital>,
        "max_daily_loss": <float, percentage>,
        "max_drawdown": <float, percentage>
    }},
    "reasoning": "<conservative case analysis>",
    "key_concerns": ["<serious risk>", ...],
    "worst_case_scenario": "<what could go wrong>",
    "capital_at_risk": <float, dollar amount that could be lost>
}}
"""


class SafeAdvisor:
    """Conservative risk advisor prioritizing capital preservation."""

    def __init__(self, llm: Optional[ChatGroq] = None):
        self.llm = llm or ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
        self.prompt = ChatPromptTemplate.from_template(SAFE_ADVISOR_PROMPT)
        self.parser = JsonOutputParser()

    def assess(self, state: RiskManagementState) -> dict:
        """Generate conservative risk assessment."""
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
                "advisor_type": "safe",
                "overall_risk_level": result.get("overall_risk_level", "HIGH"),
                "risk_score": float(result.get("risk_score", 0.7)),
                "recommendation": result.get("recommendation", "REDUCE_POSITION"),
                "position_adjustment": float(result.get("position_adjustment", 0.5)),
                "market_volatility": result.get("market_volatility", {}),
                "liquidity_risk": result.get("liquidity_risk", {}),
                "concentration_risk": result.get("concentration_risk", {}),
                "counterparty_risk": result.get("counterparty_risk", {}),
                "stop_loss_recommendation": result.get("stop_loss_recommendation"),
                "take_profit_recommendation": result.get("take_profit_recommendation"),
                "hedging_suggestions": result.get("hedging_suggestions", []),
                "diversification_suggestions": result.get("diversification_suggestions", []),
                "risk_limits": result.get("risk_limits", {}),
                "reasoning": result.get("reasoning", ""),
                "key_concerns": result.get("key_concerns", []),
                "worst_case_scenario": result.get("worst_case_scenario", ""),
                "capital_at_risk": result.get("capital_at_risk", 0),
            }

            return {"safe_assessment": assessment}

        except Exception as e:
            return {
                "safe_assessment": {
                    "advisor_type": "safe",
                    "error": str(e),
                    "recommendation": "REJECT",
                }
            }

    def __call__(self, state: RiskManagementState) -> dict:
        """Make advisor callable for LangGraph."""
        return self.assess(state)
