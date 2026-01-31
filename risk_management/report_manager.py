"""Report Manager - Synthesizes risk recommendations from all advisors.

Consolidates perspectives from Risky, Neutral, and Safe advisors
to provide final risk recommendation with approval conditions.
"""

from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

from .state import RiskManagementState


REPORT_MANAGER_PROMPT = """You are the Risk Management Report Manager responsible for synthesizing 
recommendations from your team of risk advisors and providing the final investment recommendation.

TICKER: {ticker}
PROPOSED TRADE: {trade_action} - {position_size}% position

═══════════════════════════════════════════════════════════════
RISKY ADVISOR (Aggressive Perspective):
Risk Level: {risky_risk_level}
Risk Score: {risky_risk_score}
Recommendation: {risky_recommendation}
Position Adjustment: {risky_position_adj}x
Key Points: {risky_reasoning}
Opportunities: {risky_opportunities}
═══════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════
NEUTRAL ADVISOR (Balanced Perspective):
Risk Level: {neutral_risk_level}
Risk Score: {neutral_risk_score}
Recommendation: {neutral_recommendation}
Position Adjustment: {neutral_position_adj}x
Key Points: {neutral_reasoning}
Concerns: {neutral_concerns}
═══════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════
SAFE ADVISOR (Conservative Perspective):
Risk Level: {safe_risk_level}
Risk Score: {safe_risk_score}
Recommendation: {safe_recommendation}
Position Adjustment: {safe_position_adj}x
Key Points: {safe_reasoning}
Key Concerns: {safe_concerns}
Worst Case: {safe_worst_case}
═══════════════════════════════════════════════════════════════

PORTFOLIO CONTEXT:
Risk Tolerance: {risk_tolerance}
Available Capital: ${available_capital}
Current Exposure: ${current_exposure}

YOUR TASK:
As Report Manager, synthesize all advisor perspectives to provide:
1. Final risk recommendation balancing all views
2. Approved position size based on risk tolerance
3. Required risk controls and monitoring
4. Conditions for approval (if any)
5. Feedback for traders on adjustments needed

Weight advisor opinions based on the firm's risk tolerance:
- Conservative: Weight Safe advisor more heavily
- Moderate: Equal weighting
- Aggressive: Weight Risky advisor more heavily

Respond in JSON format:
{{
    "action": "APPROVE" | "APPROVE_WITH_CONDITIONS" | "REDUCE_POSITION" | "REJECT" | "HOLD_FOR_REVIEW",
    "confidence": <float 0-1>,
    "risk_level": "LOW" | "MODERATE" | "HIGH" | "CRITICAL",
    "approved_position_size": <float, percentage of original request, e.g., 0.75 = 75%>,
    "max_position_value": <float, dollar amount>,
    "required_stop_loss": <float, percentage>,
    "suggested_take_profit": <float, percentage>,
    "risk_limits": {{
        "max_daily_loss": <float, percentage>,
        "max_drawdown": <float, percentage>,
        "position_limit": <float, percentage of portfolio>
    }},
    "monitoring_requirements": ["<requirement>", ...],
    "escalation_triggers": ["<trigger condition>", ...],
    "consensus_view": "<synthesized view from all advisors>",
    "key_risks_identified": ["<risk>", ...],
    "mitigation_strategies": ["<strategy>", ...],
    "dissenting_opinions": ["<where advisors disagreed>", ...],
    "requires_senior_approval": <boolean>,
    "approval_conditions": ["<condition>", ...],
    "trader_feedback": {{
        "position_adjustment": <float, final multiplier>,
        "stop_loss_adjustment": <float, new stop loss %>,
        "additional_requirements": ["<requirement>", ...]
    }},
    "reasoning": "<comprehensive synthesis reasoning>"
}}
"""


class ReportManager:
    """Synthesizes risk recommendations from all advisors."""

    def __init__(self, llm: Optional[ChatGroq] = None):
        self.llm = llm or ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
        self.prompt = ChatPromptTemplate.from_template(REPORT_MANAGER_PROMPT)
        self.parser = JsonOutputParser()

    def synthesize(self, state: RiskManagementState) -> dict:
        """Synthesize final risk recommendation from all advisors."""
        trade_execution = state.get("trade_execution", {})
        trade_decision = trade_execution.get("trade_decision", {})
        
        risky = state.get("risky_assessment", {})
        neutral = state.get("neutral_assessment", {})
        safe = state.get("safe_assessment", {})
        
        available_capital = state.get("available_capital", 100000)
        position_percent = trade_decision.get("quantity_percent", 0) * 100

        try:
            chain = self.prompt | self.llm | self.parser
            result = chain.invoke({
                "ticker": state["ticker"],
                "trade_action": trade_decision.get("action", "HOLD"),
                "position_size": position_percent,
                # Risky advisor
                "risky_risk_level": risky.get("overall_risk_level", "N/A"),
                "risky_risk_score": risky.get("risk_score", 0),
                "risky_recommendation": risky.get("recommendation", "N/A"),
                "risky_position_adj": risky.get("position_adjustment", 1.0),
                "risky_reasoning": risky.get("reasoning", "N/A")[:300],
                "risky_opportunities": ", ".join(risky.get("opportunities", [])[:3]),
                # Neutral advisor
                "neutral_risk_level": neutral.get("overall_risk_level", "N/A"),
                "neutral_risk_score": neutral.get("risk_score", 0),
                "neutral_recommendation": neutral.get("recommendation", "N/A"),
                "neutral_position_adj": neutral.get("position_adjustment", 1.0),
                "neutral_reasoning": neutral.get("reasoning", "N/A")[:300],
                "neutral_concerns": ", ".join(neutral.get("key_concerns", [])[:3]),
                # Safe advisor
                "safe_risk_level": safe.get("overall_risk_level", "N/A"),
                "safe_risk_score": safe.get("risk_score", 0),
                "safe_recommendation": safe.get("recommendation", "N/A"),
                "safe_position_adj": safe.get("position_adjustment", 1.0),
                "safe_reasoning": safe.get("reasoning", "N/A")[:300],
                "safe_concerns": ", ".join(safe.get("key_concerns", [])[:3]),
                "safe_worst_case": safe.get("worst_case_scenario", "N/A")[:200],
                # Context
                "risk_tolerance": state.get("risk_tolerance", "moderate"),
                "available_capital": available_capital,
                "current_exposure": state.get("current_exposure", 0),
            })

            recommendation = {
                "action": result.get("action", "HOLD_FOR_REVIEW"),
                "confidence": float(result.get("confidence", 0.5)),
                "risk_level": result.get("risk_level", "MODERATE"),
                "approved_position_size": float(result.get("approved_position_size", 1.0)),
                "max_position_value": float(result.get("max_position_value", 0)),
                "required_stop_loss": float(result.get("required_stop_loss", 5)),
                "suggested_take_profit": float(result.get("suggested_take_profit", 10)),
                "risk_limits": result.get("risk_limits", {}),
                "monitoring_requirements": result.get("monitoring_requirements", []),
                "escalation_triggers": result.get("escalation_triggers", []),
                "consensus_view": result.get("consensus_view", ""),
                "key_risks_identified": result.get("key_risks_identified", []),
                "mitigation_strategies": result.get("mitigation_strategies", []),
                "dissenting_opinions": result.get("dissenting_opinions", []),
                "requires_senior_approval": result.get("requires_senior_approval", False),
                "approval_conditions": result.get("approval_conditions", []),
                "trader_feedback": result.get("trader_feedback", {}),
                "reasoning": result.get("reasoning", ""),
            }

            # Compile all assessments
            all_assessments = [
                {"type": "risky", **risky},
                {"type": "neutral", **neutral},
                {"type": "safe", **safe},
            ]

            return {
                "final_recommendation": recommendation,
                "all_assessments": all_assessments,
                "trader_feedback": result.get("trader_feedback", {}),
                "position_adjustments": {
                    "original_percent": position_percent,
                    "approved_percent": position_percent * recommendation["approved_position_size"],
                    "adjustment_factor": recommendation["approved_position_size"],
                },
            }

        except Exception as e:
            return {
                "final_recommendation": {
                    "action": "HOLD_FOR_REVIEW",
                    "error": str(e),
                    "reasoning": f"Synthesis failed: {str(e)}",
                },
            }

    def __call__(self, state: RiskManagementState) -> dict:
        """Make report manager callable for LangGraph."""
        return self.synthesize(state)
