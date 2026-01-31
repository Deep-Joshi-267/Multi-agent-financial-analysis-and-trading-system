"""Portfolio Manager - Manages portfolio allocations and position sizing.

Handles portfolio-level decisions including rebalancing,
concentration limits, and capital allocation.
"""

from typing import Optional, Dict, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

from .state import TraderState


PORTFOLIO_PROMPT = """You are a portfolio manager optimizing position sizing and allocation.

TICKER: {ticker}
PROPOSED ACTION: {trade_action}
PROPOSED SIZE: {position_percent}% of capital

CURRENT PORTFOLIO:
{portfolio_summary}

AVAILABLE CAPITAL: ${available_capital}
RISK TOLERANCE: {risk_tolerance}

TRADE CONFIDENCE: {confidence}
CIO RECOMMENDED SIZE: {cio_size}

Optimize the trade for portfolio context:
1. Check concentration limits (single position max 20% for conservative, 30% moderate, 40% aggressive)
2. Ensure diversification is maintained
3. Validate capital allocation efficiency
4. Consider correlation with existing positions

Respond in JSON format:
{{
    "adjusted_position_percent": <float 0-1>,
    "adjustment_reason": "<why adjustment was made if any>",
    "portfolio_impact": {{
        "new_concentration": <float, % of portfolio in this ticker>,
        "diversification_score": <float 0-1>,
        "capital_efficiency": <float 0-1>
    }},
    "rebalancing_needed": <boolean>,
    "rebalancing_suggestions": ["<suggestion1>", ...],
    "risk_budget_used": <float 0-1, how much of risk budget this uses>
}}
"""


class PortfolioManager:
    """Manages portfolio allocations and validates position sizing."""

    def __init__(self, llm: Optional[ChatGroq] = None):
        self.llm = llm or ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
        self.prompt = ChatPromptTemplate.from_template(PORTFOLIO_PROMPT)
        self.parser = JsonOutputParser()
        
        # Concentration limits by risk tolerance
        self.concentration_limits = {
            "conservative": 0.20,
            "moderate": 0.30,
            "aggressive": 0.40,
        }

    def _build_portfolio_summary(self, portfolio: List[dict]) -> str:
        """Build human-readable portfolio summary."""
        if not portfolio:
            return "No existing positions"
        
        lines = []
        total_value = 0
        for pos in portfolio:
            value = pos.get("quantity", 0) * pos.get("current_price", 0)
            total_value += value
            lines.append(
                f"  {pos.get('ticker', 'N/A')}: {pos.get('quantity', 0)} shares "
                f"@ ${pos.get('current_price', 0):.2f} = ${value:,.2f}"
            )
        
        lines.append(f"\n  Total Portfolio Value: ${total_value:,.2f}")
        return "\n".join(lines)

    def optimize_allocation(self, state: TraderState) -> dict:
        """Optimize position sizing for portfolio context."""
        trade_decision = state.get("trade_decision", {})
        portfolio = state.get("portfolio", [])
        available_capital = state.get("available_capital", 0)
        risk_tolerance = state.get("risk_tolerance", "moderate")
        final_decision = state.get("final_decision", {})

        try:
            chain = self.prompt | self.llm | self.parser
            result = chain.invoke({
                "ticker": state["ticker"],
                "trade_action": trade_decision.get("action", "HOLD"),
                "position_percent": trade_decision.get("quantity_percent", 0) * 100,
                "portfolio_summary": self._build_portfolio_summary(portfolio),
                "available_capital": available_capital,
                "risk_tolerance": risk_tolerance,
                "confidence": trade_decision.get("confidence", 0),
                "cio_size": final_decision.get("position_size", "N/A"),
            })

            # Apply concentration limit check
            max_concentration = self.concentration_limits.get(risk_tolerance, 0.30)
            adjusted_percent = float(result.get("adjusted_position_percent", 0))
            
            if adjusted_percent > max_concentration:
                adjusted_percent = max_concentration
                result["adjustment_reason"] = (
                    f"Reduced to {max_concentration*100}% concentration limit for {risk_tolerance} risk"
                )

            portfolio_impact = {
                "adjusted_position_percent": adjusted_percent,
                "adjustment_reason": result.get("adjustment_reason", "No adjustment needed"),
                "portfolio_impact": result.get("portfolio_impact", {}),
                "rebalancing_needed": result.get("rebalancing_needed", False),
                "rebalancing_suggestions": result.get("rebalancing_suggestions", []),
                "risk_budget_used": result.get("risk_budget_used", 0),
                "concentration_limit": max_concentration,
            }

            # Update trade decision with adjusted size
            updated_decision = trade_decision.copy()
            updated_decision["quantity_percent"] = adjusted_percent
            updated_decision["portfolio_adjusted"] = True

            return {
                "trade_decision": updated_decision,
                "portfolio_impact": portfolio_impact,
            }

        except Exception as e:
            return {
                "portfolio_impact": {
                    "error": str(e),
                    "adjusted_position_percent": trade_decision.get("quantity_percent", 0),
                },
            }

    def __call__(self, state: TraderState) -> dict:
        """Make portfolio manager callable for LangGraph."""
        return self.optimize_allocation(state)
