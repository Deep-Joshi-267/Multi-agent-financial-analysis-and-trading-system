"""Shared state definitions for the Risk Management Team.

Defines TypedDicts and dataclasses for risk assessment workflow
with multiple risk perspectives and final recommendations.
"""

from typing import TypedDict, List, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskAction(str, Enum):
    APPROVE = "APPROVE"
    APPROVE_WITH_CONDITIONS = "APPROVE_WITH_CONDITIONS"
    REDUCE_POSITION = "REDUCE_POSITION"
    REJECT = "REJECT"
    HOLD_FOR_REVIEW = "HOLD_FOR_REVIEW"


@dataclass
class RiskFactor:
    """Individual risk factor assessment."""
    name: str
    level: RiskLevel
    score: float  # 0-1, higher = more risky
    description: str
    mitigation: Optional[str] = None


@dataclass
class RiskAssessment:
    """Complete risk assessment from an advisor."""
    advisor_type: str  # "risky", "neutral", "safe"
    overall_risk_level: RiskLevel
    risk_score: float  # 0-1
    recommendation: RiskAction
    position_adjustment: float  # Multiplier: 1.5 = increase 50%, 0.5 = reduce 50%
    
    # Detailed factors
    market_volatility: RiskFactor
    liquidity_risk: RiskFactor
    concentration_risk: RiskFactor
    counterparty_risk: RiskFactor
    
    # Strategy suggestions
    stop_loss_recommendation: Optional[float] = None
    take_profit_recommendation: Optional[float] = None
    hedging_suggestions: List[str] = field(default_factory=list)
    diversification_suggestions: List[str] = field(default_factory=list)
    
    # Reasoning
    reasoning: str = ""
    key_concerns: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RiskRecommendation:
    """Final synthesized risk recommendation from Report Manager."""
    action: RiskAction
    confidence: float
    risk_level: RiskLevel
    
    # Position guidance
    approved_position_size: float  # Percentage of original request
    max_position_value: float
    required_stop_loss: float
    suggested_take_profit: float
    
    # Risk controls
    risk_limits: dict
    monitoring_requirements: List[str]
    escalation_triggers: List[str]
    
    # Synthesis
    consensus_view: str
    key_risks_identified: List[str]
    mitigation_strategies: List[str]
    dissenting_opinions: List[str]
    
    # Approval
    requires_senior_approval: bool = False
    approval_conditions: List[str] = field(default_factory=list)
    
    reasoning: str = ""


class RiskManagementState(TypedDict):
    """State shared across the Risk Management Team workflow."""
    
    # Input from previous stages
    ticker: str
    trade_execution: dict  # From Trader Team
    final_decision: dict   # CIO decision
    analyst_report: dict
    research_report: dict
    market_data: dict
    
    # Portfolio context
    portfolio: List[dict]
    available_capital: float
    current_exposure: float
    risk_tolerance: str
    
    # Risk assessments from each advisor
    risky_assessment: Optional[dict]
    neutral_assessment: Optional[dict]
    safe_assessment: Optional[dict]
    
    # Synthesis
    all_assessments: List[dict]
    final_recommendation: Optional[dict]
    
    # Control flow
    assessments_complete: bool
    recommendation_approved: bool
    
    # Feedback to traders
    trader_feedback: Optional[dict]
    position_adjustments: Optional[dict]
    
    # Messages for LangGraph
    messages: List[dict]
