"""Risk Management Team Coordinator.

Orchestrates the risk assessment workflow using LangGraph with:
- Three parallel risk advisors (Risky, Neutral, Safe)
- Report Manager for synthesis
- Feedback generation for traders
"""

from typing import Optional, Literal
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

from .state import RiskManagementState
from .risky_advisor import RiskyAdvisor
from .neutral_advisor import NeutralAdvisor
from .safe_advisor import SafeAdvisor
from .report_manager import ReportManager


class RiskManagementTeam:
    """
    Coordinates risk management advisors through structured workflow.
    
    Workflow:
    1. Three advisors assess risk in parallel (Risky, Neutral, Safe)
    2. Report Manager synthesizes all perspectives
    3. Final recommendation generated with trader feedback
    
    Key Features:
    - Multiple risk perspectives for comprehensive assessment
    - Weighted synthesis based on firm's risk tolerance
    - Actionable feedback for position adjustments
    - Clear approval conditions and monitoring requirements
    """

    def __init__(
        self,
        llm: Optional[ChatGroq] = None,
    ):
        """
        Initialize the Risk Management Team.
        
        Args:
            llm: Language model for agents
        """
        self.llm = llm or ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)

        # Initialize advisors
        self.risky_advisor = RiskyAdvisor(llm=self.llm)
        self.neutral_advisor = NeutralAdvisor(llm=self.llm)
        self.safe_advisor = SafeAdvisor(llm=self.llm)
        self.report_manager = ReportManager(llm=self.llm)

        # Build the workflow graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for risk assessment."""
        
        workflow = StateGraph(RiskManagementState)

        # Add nodes for each advisor and manager
        workflow.add_node("risky_assessment", self._risky_node)
        workflow.add_node("neutral_assessment", self._neutral_node)
        workflow.add_node("safe_assessment", self._safe_node)
        workflow.add_node("synthesize", self._synthesize_node)

        # Set entry point - all advisors run in sequence
        # (LangGraph will handle them, could be parallelized in production)
        workflow.set_entry_point("risky_assessment")

        # Sequential flow through advisors
        workflow.add_edge("risky_assessment", "neutral_assessment")
        workflow.add_edge("neutral_assessment", "safe_assessment")
        workflow.add_edge("safe_assessment", "synthesize")
        workflow.add_edge("synthesize", END)

        return workflow.compile()

    # ========== Node Functions ==========

    def _risky_node(self, state: RiskManagementState) -> dict:
        """Execute risky advisor assessment."""
        return self.risky_advisor(state)

    def _neutral_node(self, state: RiskManagementState) -> dict:
        """Execute neutral advisor assessment."""
        return self.neutral_advisor(state)

    def _safe_node(self, state: RiskManagementState) -> dict:
        """Execute safe advisor assessment."""
        return self.safe_advisor(state)

    def _synthesize_node(self, state: RiskManagementState) -> dict:
        """Execute report manager synthesis."""
        return self.report_manager(state)

    # ========== Public Interface ==========

    def assess_risk(
        self,
        ticker: str,
        trade_execution: dict,
        final_decision: dict,
        analyst_report: dict,
        research_report: dict,
        market_data: dict,
        available_capital: float = 100000.0,
        current_exposure: float = 0.0,
        risk_tolerance: str = "moderate",
        portfolio: list = None,
    ) -> dict:
        """
        Run complete risk assessment workflow.
        
        Args:
            ticker: Stock ticker symbol
            trade_execution: Output from Trader Team
            final_decision: CIO decision from pipeline
            analyst_report: Output from Analyst Team
            research_report: Output from Researcher Team
            market_data: Current market data
            available_capital: Capital available for trading
            current_exposure: Current portfolio exposure
            risk_tolerance: "conservative", "moderate", or "aggressive"
            portfolio: Current portfolio positions
            
        Returns:
            Complete risk assessment with recommendation
        """
        initial_state: RiskManagementState = {
            "ticker": ticker,
            "trade_execution": trade_execution,
            "final_decision": final_decision,
            "analyst_report": analyst_report,
            "research_report": research_report,
            "market_data": market_data,
            "portfolio": portfolio or [],
            "available_capital": available_capital,
            "current_exposure": current_exposure,
            "risk_tolerance": risk_tolerance,
            "risky_assessment": None,
            "neutral_assessment": None,
            "safe_assessment": None,
            "all_assessments": [],
            "final_recommendation": None,
            "assessments_complete": False,
            "recommendation_approved": False,
            "trader_feedback": None,
            "position_adjustments": None,
            "messages": [],
        }

        result = self.graph.invoke(initial_state)
        
        return {
            "ticker": ticker,
            "final_recommendation": result.get("final_recommendation"),
            "advisor_assessments": {
                "risky": result.get("risky_assessment"),
                "neutral": result.get("neutral_assessment"),
                "safe": result.get("safe_assessment"),
            },
            "trader_feedback": result.get("trader_feedback"),
            "position_adjustments": result.get("position_adjustments"),
        }

    def get_quick_assessment(
        self,
        ticker: str,
        trade_action: str,
        position_percent: float,
        risk_tolerance: str = "moderate",
    ) -> dict:
        """
        Quick risk assessment without full context.
        
        For rapid evaluation of simple trades.
        """
        # Simplified state for quick assessment
        initial_state: RiskManagementState = {
            "ticker": ticker,
            "trade_execution": {
                "trade_decision": {
                    "action": trade_action,
                    "quantity_percent": position_percent / 100,
                    "confidence": 0.5,
                    "stop_loss_percent": 5,
                    "take_profit_percent": 10,
                }
            },
            "final_decision": {"action": trade_action, "confidence": 0.5},
            "analyst_report": {},
            "research_report": {},
            "market_data": {},
            "portfolio": [],
            "available_capital": 100000,
            "current_exposure": 0,
            "risk_tolerance": risk_tolerance,
            "risky_assessment": None,
            "neutral_assessment": None,
            "safe_assessment": None,
            "all_assessments": [],
            "final_recommendation": None,
            "assessments_complete": False,
            "recommendation_approved": False,
            "trader_feedback": None,
            "position_adjustments": None,
            "messages": [],
        }

        result = self.graph.invoke(initial_state)
        return result.get("final_recommendation", {})
