"""Shared state definitions for the Researcher Team.

Defines TypedDicts for state management across the debate workflow.
"""

from typing import TypedDict, List, Optional, Literal
from dataclasses import dataclass, field


@dataclass
class DebateArgument:
    """A single argument in the debate."""
    perspective: Literal["bullish", "bearish"]
    argument: str
    key_points: List[str]
    confidence: float
    evidence: List[str]
    counter_to: Optional[str] = None


@dataclass
class DebateRound:
    """Represents one round of debate between bullish and bearish researchers."""
    round_number: int
    bullish_argument: DebateArgument
    bearish_argument: DebateArgument
    key_disagreements: List[str] = field(default_factory=list)
    areas_of_consensus: List[str] = field(default_factory=list)


@dataclass
class ResearchReport:
    """Final research report after debate rounds."""
    investment_thesis: str
    bull_case_summary: str
    bear_case_summary: str
    risk_reward_ratio: str
    key_risks: List[str]
    key_opportunities: List[str]
    confidence_score: float
    recommended_action: Literal["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]
    position_conviction: Literal["HIGH", "MEDIUM", "LOW"]
    debate_rounds_summary: str


class ResearcherState(TypedDict):
    """State shared across the Researcher Team workflow."""
    
    # Input from Analysts Team
    ticker: str
    analyst_report: dict
    market_data: dict
    
    # Debate state
    current_round: int
    max_rounds: int
    debate_history: List[dict]
    
    # Individual perspectives
    bullish_analysis: Optional[dict]
    bearish_analysis: Optional[dict]
    
    # Debate rounds
    debate_rounds: List[dict]
    
    # Final output
    research_report: Optional[dict]
    consensus_reached: bool
    
    # Message history for LangGraph
    messages: List[dict]
