"""Trader Team Coordinator.

Orchestrates the complete trade execution workflow using LangGraph with:
- Feedback-driven reasoning with scoring
- Max iteration threshold to prevent infinite loops
- Human-in-the-loop for trade approval
"""

from typing import Optional, Literal, Callable
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

from .state import TraderState
from .trader_agent import TraderAgent
from .risk_manager import RiskManager
from .portfolio_manager import PortfolioManager
from .execution import TradeExecutor, create_cli_approval_callback


class TraderTeam:
    """
    Coordinates trader agents through a feedback-driven workflow.
    
    Workflow:
    1. TraderAgent makes initial decision
    2. RiskManager scores the decision
    3. If score < threshold AND iterations < max, refine decision
    4. PortfolioManager optimizes allocation
    5. TradeExecutor prepares order
    6. Human approval (if required)
    7. Execute or reject
    
    Key Features:
    - Feedback loop with scoring (converges to quality decisions)
    - Max iterations to prevent infinite loops
    - Human-in-the-loop for final approval
    """

    def __init__(
        self,
        llm: Optional[ChatGroq] = None,
        max_iterations: int = 3,
        score_threshold: float = 0.6,
        require_human_approval: bool = True,
        auto_approve_threshold: float = 0.85,
        approval_callback: Optional[Callable] = None,
    ):
        """
        Initialize the Trader Team.
        
        Args:
            llm: Language model for agents
            max_iterations: Maximum refinement iterations (prevents infinite loops)
            score_threshold: Minimum score to proceed without refinement
            require_human_approval: Whether human must approve trades
            auto_approve_threshold: Score threshold for auto-approval
            approval_callback: Optional callback for approval (default: CLI prompt)
        """
        self.llm = llm or ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
        self.max_iterations = max_iterations
        self.score_threshold = score_threshold
        self.require_human_approval = require_human_approval

        # Initialize agents
        self.trader_agent = TraderAgent(llm=self.llm)
        self.risk_manager = RiskManager(llm=self.llm)
        self.portfolio_manager = PortfolioManager(llm=self.llm)
        self.executor = TradeExecutor(
            require_approval=require_human_approval,
            auto_approve_threshold=auto_approve_threshold,
            approval_callback=approval_callback,
        )

        # Build the workflow graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with feedback loops."""
        
        workflow = StateGraph(TraderState)

        # Add nodes
        workflow.add_node("make_decision", self._make_decision_node)
        workflow.add_node("assess_risk", self._assess_risk_node)
        workflow.add_node("check_iteration", self._check_iteration_node)
        workflow.add_node("optimize_portfolio", self._optimize_portfolio_node)
        workflow.add_node("prepare_execution", self._prepare_execution_node)
        workflow.add_node("human_approval", self._human_approval_node)
        workflow.add_node("execute_trade", self._execute_trade_node)
        workflow.add_node("increment_iteration", self._increment_iteration_node)

        # Set entry point
        workflow.set_entry_point("make_decision")

        # Decision → Risk Assessment
        workflow.add_edge("make_decision", "assess_risk")
        
        # Risk Assessment → Check if refinement needed
        workflow.add_edge("assess_risk", "check_iteration")
        
        # Conditional: Refine or proceed
        workflow.add_conditional_edges(
            "check_iteration",
            self._should_refine_decision,
            {
                "refine": "increment_iteration",
                "proceed": "optimize_portfolio",
                "max_reached": "optimize_portfolio",
            }
        )
        
        # Refinement loop
        workflow.add_edge("increment_iteration", "make_decision")
        
        # Portfolio optimization → Execution preparation
        workflow.add_edge("optimize_portfolio", "prepare_execution")
        
        # Conditional: Human approval needed?
        workflow.add_conditional_edges(
            "prepare_execution",
            self._needs_human_approval,
            {
                "needs_approval": "human_approval",
                "auto_approved": "execute_trade",
                "no_action": END,
            }
        )
        
        # Human approval → Execute or End
        workflow.add_conditional_edges(
            "human_approval",
            self._approval_decision,
            {
                "approved": "execute_trade",
                "rejected": END,
                "awaiting": END,  # Will need to resume later
            }
        )
        
        # Execute → End
        workflow.add_edge("execute_trade", END)

        return workflow.compile()

    # ========== Node Functions ==========

    def _make_decision_node(self, state: TraderState) -> dict:
        """Execute trader agent decision-making."""
        return self.trader_agent(state)

    def _assess_risk_node(self, state: TraderState) -> dict:
        """Execute risk assessment and scoring."""
        return self.risk_manager(state)

    def _check_iteration_node(self, state: TraderState) -> dict:
        """Check iteration status - no state change, just for routing."""
        return {}

    def _optimize_portfolio_node(self, state: TraderState) -> dict:
        """Execute portfolio optimization."""
        return self.portfolio_manager(state)

    def _prepare_execution_node(self, state: TraderState) -> dict:
        """Prepare trade order for execution."""
        return self.executor.prepare_order(state)

    def _human_approval_node(self, state: TraderState) -> dict:
        """Handle human approval workflow."""
        return self.executor.request_human_approval(state)

    def _execute_trade_node(self, state: TraderState) -> dict:
        """Execute the approved trade."""
        return self.executor.execute_order(state)

    def _increment_iteration_node(self, state: TraderState) -> dict:
        """Increment iteration counter for refinement loop."""
        current = state.get("current_iteration", 1)
        return {"current_iteration": current + 1}

    # ========== Routing Functions ==========

    def _should_refine_decision(
        self, state: TraderState
    ) -> Literal["refine", "proceed", "max_reached"]:
        """
        Determine if decision needs refinement based on score and iteration count.
        
        This implements the feedback-driven reasoning with iteration limits.
        """
        current_iteration = state.get("current_iteration", 1)
        should_refine = state.get("should_refine", False)
        current_score = state.get("current_score", {})
        overall_score = current_score.get("overall_score", 0)
        
        # Check max iterations to prevent infinite loop
        if current_iteration >= self.max_iterations:
            return "max_reached"
        
        # Check if refinement is needed based on score
        if should_refine and overall_score < self.score_threshold:
            return "refine"
        
        return "proceed"

    def _needs_human_approval(
        self, state: TraderState
    ) -> Literal["needs_approval", "auto_approved", "no_action"]:
        """Determine if human approval is needed."""
        execution_status = state.get("execution_status", "")
        requires_approval = state.get("requires_human_approval", True)
        
        if execution_status == "NO_ACTION":
            return "no_action"
        
        if requires_approval:
            return "needs_approval"
        
        return "auto_approved"

    def _approval_decision(
        self, state: TraderState
    ) -> Literal["approved", "rejected", "awaiting"]:
        """Route based on human approval decision."""
        human_approved = state.get("human_approved")
        execution_status = state.get("execution_status", "")
        
        if execution_status == "AWAITING_HUMAN_APPROVAL":
            return "awaiting"
        
        if human_approved is True:
            return "approved"
        
        return "rejected"

    # ========== Public Interface ==========

    def execute_trade(
        self,
        ticker: str,
        analyst_report: dict,
        research_report: dict,
        final_decision: dict,
        market_data: dict,
        available_capital: float = 100000.0,
        risk_tolerance: str = "moderate",
        portfolio: list = None,
    ) -> dict:
        """
        Execute the complete trading workflow.
        
        Args:
            ticker: Stock ticker symbol
            analyst_report: Output from AnalystsTeam
            research_report: Output from ResearcherTeam
            final_decision: CIO decision from pipeline
            market_data: Current market data
            available_capital: Capital available for trading
            risk_tolerance: "conservative", "moderate", or "aggressive"
            portfolio: Current portfolio positions
            
        Returns:
            Complete execution result including orders and feedback
        """
        initial_state: TraderState = {
            "ticker": ticker,
            "analyst_report": analyst_report,
            "research_report": research_report,
            "final_decision": final_decision,
            "market_data": market_data,
            "portfolio": portfolio or [],
            "available_capital": available_capital,
            "risk_tolerance": risk_tolerance,
            "current_iteration": 1,
            "max_iterations": self.max_iterations,
            "trade_decision": None,
            "feedback_history": [],
            "current_score": None,
            "score_history": [],
            "score_threshold": self.score_threshold,
            "requires_human_approval": self.require_human_approval,
            "human_approved": None,
            "human_feedback": None,
            "pending_orders": [],
            "executed_orders": [],
            "execution_status": "INITIALIZED",
            "should_refine": False,
            "refinement_reason": None,
            "messages": [],
        }

        result = self.graph.invoke(initial_state)
        
        return {
            "ticker": ticker,
            "trade_decision": result.get("trade_decision"),
            "final_score": result.get("current_score"),
            "score_history": result.get("score_history", []),
            "iterations_used": result.get("current_iteration", 1),
            "portfolio_impact": result.get("portfolio_impact"),
            "executed_orders": result.get("executed_orders", []),
            "pending_orders": result.get("pending_orders", []),
            "execution_status": result.get("execution_status"),
            "human_approved": result.get("human_approved"),
            "human_feedback": result.get("human_feedback"),
        }

    def get_execution_details(
        self,
        ticker: str,
        analyst_report: dict,
        research_report: dict,
        final_decision: dict,
        market_data: dict,
        **kwargs,
    ) -> dict:
        """Run workflow and return full state for debugging."""
        initial_state: TraderState = {
            "ticker": ticker,
            "analyst_report": analyst_report,
            "research_report": research_report,
            "final_decision": final_decision,
            "market_data": market_data,
            "portfolio": kwargs.get("portfolio", []),
            "available_capital": kwargs.get("available_capital", 100000.0),
            "risk_tolerance": kwargs.get("risk_tolerance", "moderate"),
            "current_iteration": 1,
            "max_iterations": self.max_iterations,
            "trade_decision": None,
            "feedback_history": [],
            "current_score": None,
            "score_history": [],
            "score_threshold": self.score_threshold,
            "requires_human_approval": self.require_human_approval,
            "human_approved": None,
            "human_feedback": None,
            "pending_orders": [],
            "executed_orders": [],
            "execution_status": "INITIALIZED",
            "should_refine": False,
            "refinement_reason": None,
            "messages": [],
        }

        return self.graph.invoke(initial_state)
