"""Trader Agent - Core decision-making for trade execution.

Evaluates analyst and researcher recommendations to determine
optimal trading actions with feedback-driven reasoning.
"""

from typing import Optional, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

from .state import TraderState, OrderSide, OrderType


TRADER_DECISION_PROMPT = """You are an experienced trader making execution decisions based on 
comprehensive analysis from your analyst and researcher teams.

TICKER: {ticker}
CURRENT PRICE: ${current_price}

═══════════════════════════════════════════════════════════════
ANALYST TEAM RECOMMENDATION:
Signal: {analyst_signal}
Confidence: {analyst_confidence}
Reasoning: {analyst_reasoning}
═══════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════
RESEARCHER TEAM CONCLUSION:
Investment Thesis: {research_thesis}
Bull Case: {bull_case}
Bear Case: {bear_case}
Recommended Action: {research_action}
Position Conviction: {research_conviction}
═══════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════
CIO FINAL DECISION:
Action: {cio_action}
Confidence: {cio_confidence}
Position Size: {cio_position_size}
Time Horizon: {cio_time_horizon}
═══════════════════════════════════════════════════════════════

PORTFOLIO CONTEXT:
Available Capital: ${available_capital}
Risk Tolerance: {risk_tolerance}
Current Position: {current_position}

{feedback_context}

YOUR TASK:
Design a precise trading plan that:
1. Aligns with the CIO decision while considering analyst and researcher insights
2. Determines optimal entry timing and price levels
3. Sets appropriate position size based on conviction and risk tolerance
4. Defines clear stop-loss and take-profit levels
5. Considers portfolio impact and diversification

Respond in JSON format:
{{
    "action": "BUY" | "SELL" | "HOLD",
    "order_type": "MARKET" | "LIMIT" | "STOP_LOSS",
    "quantity_percent": <float 0.0-1.0, percentage of available capital>,
    "limit_price": <float or null for market orders>,
    "stop_loss_percent": <float, percentage below entry for stop>,
    "take_profit_percent": <float, percentage above entry for take profit>,
    "entry_timing": "IMMEDIATE" | "WAIT_FOR_DIP" | "SCALE_IN",
    "reasoning": "<detailed trade rationale>",
    "confidence": <float 0.0-1.0>,
    "risk_reward_ratio": <float, expected reward/risk>,
    "key_levels": {{
        "support": <float>,
        "resistance": <float>,
        "entry_target": <float>
    }},
    "exit_conditions": ["<condition1>", "<condition2>", ...],
    "position_management": "<how to manage the position over time>"
}}
"""


class TraderAgent:
    """Core trader agent for making execution decisions."""

    def __init__(self, llm: Optional[ChatGroq] = None):
        self.llm = llm or ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
        self.prompt = ChatPromptTemplate.from_template(TRADER_DECISION_PROMPT)
        self.parser = JsonOutputParser()

    def make_decision(self, state: TraderState) -> dict:
        """Generate trading decision based on all inputs."""
        analyst_report = state.get("analyst_report", {})
        research_report = state.get("research_report", {})
        final_decision = state.get("final_decision", {})
        market_data = state.get("market_data", {})
        feedback_history = state.get("feedback_history", [])
        current_iteration = state.get("current_iteration", 1)

        # Build feedback context for refinement iterations
        feedback_context = ""
        if feedback_history and current_iteration > 1:
            last_feedback = feedback_history[-1]
            feedback_context = f"""
═══════════════════════════════════════════════════════════════
PREVIOUS ITERATION FEEDBACK (Iteration {current_iteration - 1}):
Score: {last_feedback.get('overall_score', 0):.2f}/1.0
Issues: {', '.join(last_feedback.get('feedback_notes', []))}

IMPROVEMENT REQUIRED: Address the feedback above to improve your decision.
═══════════════════════════════════════════════════════════════
"""

        # Get current position info
        portfolio = state.get("portfolio", [])
        current_position = "No existing position"
        for pos in portfolio:
            if pos.get("ticker") == state["ticker"]:
                current_position = f"{pos.get('quantity', 0)} shares @ ${pos.get('avg_price', 0):.2f}"
                break

        try:
            chain = self.prompt | self.llm | self.parser
            result = chain.invoke({
                "ticker": state["ticker"],
                "current_price": market_data.get("current_price", 0),
                "analyst_signal": analyst_report.get("final_signal", "N/A"),
                "analyst_confidence": f"{analyst_report.get('confidence', 0):.0%}",
                "analyst_reasoning": analyst_report.get("reasoning", "N/A"),
                "research_thesis": research_report.get("investment_thesis", "N/A"),
                "bull_case": research_report.get("bull_case_summary", "N/A"),
                "bear_case": research_report.get("bear_case_summary", "N/A"),
                "research_action": research_report.get("recommended_action", "N/A"),
                "research_conviction": research_report.get("position_conviction", "N/A"),
                "cio_action": final_decision.get("action", "N/A"),
                "cio_confidence": f"{final_decision.get('confidence', 0):.0%}",
                "cio_position_size": final_decision.get("position_size", "N/A"),
                "cio_time_horizon": final_decision.get("time_horizon", "N/A"),
                "available_capital": state.get("available_capital", 0),
                "risk_tolerance": state.get("risk_tolerance", "moderate"),
                "current_position": current_position,
                "feedback_context": feedback_context,
            })

            trade_decision = {
                "action": result.get("action", "HOLD"),
                "order_type": result.get("order_type", "MARKET"),
                "quantity_percent": float(result.get("quantity_percent", 0)),
                "limit_price": result.get("limit_price"),
                "stop_loss_percent": float(result.get("stop_loss_percent", 5)),
                "take_profit_percent": float(result.get("take_profit_percent", 10)),
                "entry_timing": result.get("entry_timing", "IMMEDIATE"),
                "reasoning": result.get("reasoning", ""),
                "confidence": float(result.get("confidence", 0.5)),
                "risk_reward_ratio": float(result.get("risk_reward_ratio", 1.0)),
                "key_levels": result.get("key_levels", {}),
                "exit_conditions": result.get("exit_conditions", []),
                "position_management": result.get("position_management", ""),
                "iteration": current_iteration,
            }

            return {"trade_decision": trade_decision}

        except Exception as e:
            return {
                "trade_decision": {
                    "action": "HOLD",
                    "order_type": "MARKET",
                    "quantity_percent": 0,
                    "reasoning": f"Decision failed: {str(e)}",
                    "confidence": 0.0,
                    "iteration": current_iteration,
                    "error": str(e),
                }
            }

    def __call__(self, state: TraderState) -> dict:
        """Make the agent callable for LangGraph."""
        return self.make_decision(state)
