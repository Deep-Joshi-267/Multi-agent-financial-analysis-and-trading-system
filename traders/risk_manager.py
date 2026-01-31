"""Risk Manager - Assesses trade risks and validates position sizing.

Implements feedback-driven scoring to evaluate trade decisions
and ensure they meet risk management criteria.
"""

from typing import Optional, Dict, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

from .state import TraderState, FeedbackScore


RISK_ASSESSMENT_PROMPT = """You are a senior risk manager evaluating a proposed trade.

TICKER: {ticker}
CURRENT PRICE: ${current_price}

PROPOSED TRADE:
Action: {trade_action}
Order Type: {order_type}
Position Size: {position_percent}% of capital (${position_value})
Entry Timing: {entry_timing}
Stop Loss: {stop_loss}%
Take Profit: {take_profit}%
Risk/Reward Ratio: {risk_reward}

TRADE REASONING:
{trade_reasoning}

PORTFOLIO CONTEXT:
Available Capital: ${available_capital}
Risk Tolerance: {risk_tolerance}
Current Portfolio Exposure: {portfolio_exposure}

ANALYST CONFIDENCE: {analyst_confidence}
RESEARCHER CONVICTION: {research_conviction}

Evaluate this trade on the following criteria:

1. RISK SCORE (0-1, lower is better):
   - Is position sizing appropriate for risk tolerance?
   - Are stop-loss levels reasonable?
   - Is concentration risk acceptable?

2. REWARD SCORE (0-1, higher is better):
   - Is the expected return justified?
   - Is risk/reward ratio favorable?
   - Does timing maximize opportunity?

3. TIMING SCORE (0-1, higher is better):
   - Is entry timing optimal?
   - Are market conditions favorable?
   - Is urgency appropriate?

4. ALIGNMENT SCORE (0-1, higher is better):
   - Does trade align with analyst recommendations?
   - Does trade align with researcher conclusions?
   - Is position size consistent with conviction levels?

Respond in JSON format:
{{
    "risk_score": <float 0-1>,
    "reward_score": <float 0-1>,
    "timing_score": <float 0-1>,
    "alignment_score": <float 0-1>,
    "overall_score": <float 0-1, weighted average>,
    "risk_flags": ["<flag1>", "<flag2>", ...],
    "improvement_suggestions": ["<suggestion1>", "<suggestion2>", ...],
    "position_size_recommendation": "<keep | reduce | increase>",
    "stop_loss_recommendation": "<keep | tighten | loosen>",
    "approval_recommendation": "APPROVE" | "REVISE" | "REJECT",
    "reasoning": "<detailed risk assessment>"
}}
"""


class RiskManager:
    """Risk manager for evaluating and scoring trade decisions."""

    def __init__(self, llm: Optional[ChatGroq] = None):
        self.llm = llm or ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
        self.prompt = ChatPromptTemplate.from_template(RISK_ASSESSMENT_PROMPT)
        self.parser = JsonOutputParser()

    def assess_risk(self, state: TraderState) -> dict:
        """Assess risk of proposed trade and generate feedback score."""
        trade_decision = state.get("trade_decision", {})
        market_data = state.get("market_data", {})
        analyst_report = state.get("analyst_report", {})
        research_report = state.get("research_report", {})
        current_iteration = state.get("current_iteration", 1)

        current_price = market_data.get("current_price", 0)
        available_capital = state.get("available_capital", 0)
        position_percent = trade_decision.get("quantity_percent", 0) * 100
        position_value = available_capital * trade_decision.get("quantity_percent", 0)

        # Calculate portfolio exposure
        portfolio = state.get("portfolio", [])
        total_value = sum(p.get("quantity", 0) * p.get("current_price", 0) for p in portfolio)
        portfolio_exposure = f"${total_value:,.2f}" if total_value else "No existing positions"

        try:
            chain = self.prompt | self.llm | self.parser
            result = chain.invoke({
                "ticker": state["ticker"],
                "current_price": current_price,
                "trade_action": trade_decision.get("action", "HOLD"),
                "order_type": trade_decision.get("order_type", "MARKET"),
                "position_percent": position_percent,
                "position_value": position_value,
                "entry_timing": trade_decision.get("entry_timing", "IMMEDIATE"),
                "stop_loss": trade_decision.get("stop_loss_percent", 5),
                "take_profit": trade_decision.get("take_profit_percent", 10),
                "risk_reward": trade_decision.get("risk_reward_ratio", 1.0),
                "trade_reasoning": trade_decision.get("reasoning", "N/A"),
                "available_capital": available_capital,
                "risk_tolerance": state.get("risk_tolerance", "moderate"),
                "portfolio_exposure": portfolio_exposure,
                "analyst_confidence": f"{analyst_report.get('confidence', 0):.0%}",
                "research_conviction": research_report.get("position_conviction", "N/A"),
            })

            # Build feedback score
            risk_score = float(result.get("risk_score", 0.5))
            reward_score = float(result.get("reward_score", 0.5))
            timing_score = float(result.get("timing_score", 0.5))
            alignment_score = float(result.get("alignment_score", 0.5))
            
            # Calculate weighted overall score
            # Lower risk is better, so we invert it
            overall_score = (
                (1 - risk_score) * 0.3 +  # Risk (inverted)
                reward_score * 0.3 +       # Reward
                timing_score * 0.2 +       # Timing
                alignment_score * 0.2      # Alignment
            )

            feedback_score = {
                "risk_score": risk_score,
                "reward_score": reward_score,
                "timing_score": timing_score,
                "alignment_score": alignment_score,
                "overall_score": overall_score,
                "iteration": current_iteration,
                "feedback_notes": result.get("improvement_suggestions", []),
                "risk_flags": result.get("risk_flags", []),
                "approval_recommendation": result.get("approval_recommendation", "REVISE"),
                "position_size_recommendation": result.get("position_size_recommendation", "keep"),
                "stop_loss_recommendation": result.get("stop_loss_recommendation", "keep"),
                "reasoning": result.get("reasoning", ""),
            }

            # Update score history
            score_history = state.get("score_history", []) + [feedback_score]

            # Determine if refinement is needed
            score_threshold = state.get("score_threshold", 0.6)
            should_refine = overall_score < score_threshold
            refinement_reason = None
            
            if should_refine:
                if risk_score > 0.7:
                    refinement_reason = "Risk too high - reduce position or tighten stops"
                elif alignment_score < 0.5:
                    refinement_reason = "Poor alignment with analyst/researcher recommendations"
                elif reward_score < 0.4:
                    refinement_reason = "Insufficient reward potential"
                else:
                    refinement_reason = "Overall score below threshold"

            return {
                "current_score": feedback_score,
                "score_history": score_history,
                "should_refine": should_refine,
                "refinement_reason": refinement_reason,
                "feedback_history": state.get("feedback_history", []) + [feedback_score],
            }

        except Exception as e:
            return {
                "current_score": {
                    "overall_score": 0.0,
                    "feedback_notes": [f"Risk assessment failed: {str(e)}"],
                    "approval_recommendation": "REJECT",
                    "error": str(e),
                },
                "should_refine": False,
                "refinement_reason": f"Error: {str(e)}",
            }

    def __call__(self, state: TraderState) -> dict:
        """Make risk manager callable for LangGraph."""
        return self.assess_risk(state)
