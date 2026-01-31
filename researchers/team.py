"""Researcher Team Coordinator.

Orchestrates bullish and bearish researchers through multi-round debates
using LangGraph to produce balanced investment research reports.
"""

from typing import Optional, Literal
from langgraph.graph import StateGraph, END

from langchain_groq import ChatGroq

from .state import ResearcherState
from .bullish_researcher import BullishResearcher
from .bearish_researcher import BearishResearcher
from .debate import DebateCoordinator


class ResearcherTeam:
    """Coordinates researcher agents through structured debate using LangGraph."""

    def __init__(
        self,
        llm: Optional[ChatGroq] = None,
        max_debate_rounds: int = 2,
    ):
        self.llm = llm or ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
        self.max_rounds = max_debate_rounds

        # Initialize researcher agents
        self.bullish_researcher = BullishResearcher(llm=self.llm)
        self.bearish_researcher = BearishResearcher(llm=self.llm)
        self.debate_coordinator = DebateCoordinator(llm=self.llm, max_rounds=max_debate_rounds)

        # Build the debate graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for the debate process."""
        
        workflow = StateGraph(ResearcherState)

        # Add nodes
        workflow.add_node("bullish_analysis", self._bullish_node)
        workflow.add_node("bearish_analysis", self._bearish_node)
        workflow.add_node("evaluate_round", self._evaluate_node)
        workflow.add_node("increment_round", self._increment_round)
        workflow.add_node("synthesize", self._synthesize_node)

        # Set entry point
        workflow.set_entry_point("bullish_analysis")

        # Define edges
        workflow.add_edge("bullish_analysis", "bearish_analysis")
        workflow.add_edge("bearish_analysis", "evaluate_round")
        
        # Conditional edge: continue debate or synthesize
        workflow.add_conditional_edges(
            "evaluate_round",
            self._should_continue_debate,
            {
                "continue": "increment_round",
                "conclude": "synthesize",
            }
        )
        
        workflow.add_edge("increment_round", "bullish_analysis")
        workflow.add_edge("synthesize", END)

        return workflow.compile()

    def _bullish_node(self, state: ResearcherState) -> dict:
        """Execute bullish researcher analysis."""
        return self.bullish_researcher(state)

    def _bearish_node(self, state: ResearcherState) -> dict:
        """Execute bearish researcher analysis."""
        return self.bearish_researcher(state)

    def _evaluate_node(self, state: ResearcherState) -> dict:
        """Evaluate the current debate round."""
        return self.debate_coordinator.evaluate_round(state)

    def _increment_round(self, state: ResearcherState) -> dict:
        """Increment the debate round counter."""
        current = state.get("current_round", 1)
        return {"current_round": current + 1}

    def _synthesize_node(self, state: ResearcherState) -> dict:
        """Synthesize debate into final research report."""
        return self.debate_coordinator.synthesize_debate(state)

    def _should_continue_debate(self, state: ResearcherState) -> Literal["continue", "conclude"]:
        """Determine if debate should continue or conclude."""
        current_round = state.get("current_round", 1)
        should_continue = state.get("should_continue", False)
        
        if current_round >= self.max_rounds:
            return "conclude"
        
        if should_continue:
            return "continue"
        
        return "conclude"

    def research(
        self,
        ticker: str,
        analyst_report: dict,
        market_data: dict,
    ) -> dict:
        """
        Run the full research debate process.

        Args:
            ticker: Stock ticker symbol
            analyst_report: Output from AnalystsTeam.analyze()
            market_data: Market data dictionary

        Returns:
            Research report with balanced investment thesis
        """
        initial_state: ResearcherState = {
            "ticker": ticker,
            "analyst_report": analyst_report,
            "market_data": market_data,
            "current_round": 1,
            "max_rounds": self.max_rounds,
            "debate_history": [],
            "bullish_analysis": None,
            "bearish_analysis": None,
            "debate_rounds": [],
            "research_report": None,
            "consensus_reached": False,
            "messages": [],
        }

        result = self.graph.invoke(initial_state)
        return result.get("research_report", {})

    def get_debate_history(
        self,
        ticker: str,
        analyst_report: dict,
        market_data: dict,
    ) -> dict:
        """Run research and return full debate history."""
        initial_state: ResearcherState = {
            "ticker": ticker,
            "analyst_report": analyst_report,
            "market_data": market_data,
            "current_round": 1,
            "max_rounds": self.max_rounds,
            "debate_history": [],
            "bullish_analysis": None,
            "bearish_analysis": None,
            "debate_rounds": [],
            "research_report": None,
            "consensus_reached": False,
            "messages": [],
        }

        result = self.graph.invoke(initial_state)
        
        return {
            "ticker": ticker,
            "debate_history": result.get("debate_history", []),
            "bullish_final": result.get("bullish_analysis"),
            "bearish_final": result.get("bearish_analysis"),
            "research_report": result.get("research_report"),
            "rounds_completed": result.get("current_round", 1),
        }
