"""Shared state definitions for the Trader Team.

Defines TypedDicts and dataclasses for trade execution workflow with
feedback-driven reasoning and human-in-the-loop support.
"""

from typing import TypedDict, List, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"


@dataclass
class TradeOrder:
    """Represents a single trade order."""
    ticker: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    order_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    reasoning: str = ""
    confidence: float = 0.0


@dataclass
class FeedbackScore:
    """Scoring for feedback-driven reasoning."""
    risk_score: float  # 0-1, lower is better
    reward_score: float  # 0-1, higher is better
    timing_score: float  # 0-1, higher is better
    alignment_score: float  # 0-1, alignment with analyst/researcher
    overall_score: float  # Weighted composite score
    iteration: int
    feedback_notes: List[str] = field(default_factory=list)
    
    @property
    def passes_threshold(self) -> bool:
        """Check if score passes minimum threshold (0.6)."""
        return self.overall_score >= 0.6
    
    @property
    def needs_improvement(self) -> bool:
        """Check if significant improvement is needed."""
        return self.overall_score < 0.4


@dataclass
class TradeDecision:
    """Complete trade decision with reasoning and scoring."""
    order: TradeOrder
    score: FeedbackScore
    analyst_signal: str
    researcher_recommendation: str
    risk_assessment: dict
    portfolio_impact: dict
    human_approval_required: bool = True
    human_approved: Optional[bool] = None
    human_feedback: Optional[str] = None
    revision_history: List[dict] = field(default_factory=list)


@dataclass
class PortfolioPosition:
    """Current portfolio position for a ticker."""
    ticker: str
    quantity: float
    avg_price: float
    current_price: float
    unrealized_pnl: float
    weight: float  # Portfolio weight percentage
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price


class TraderState(TypedDict):
    """State shared across the Trader Team workflow."""
    
    # Input from previous stages
    ticker: str
    analyst_report: dict
    research_report: dict
    market_data: dict
    final_decision: dict  # CIO decision from pipeline
    
    # Current portfolio state
    portfolio: List[dict]
    available_capital: float
    risk_tolerance: str  # "conservative", "moderate", "aggressive"
    
    # Trading decision state
    current_iteration: int
    max_iterations: int
    trade_decision: Optional[dict]
    feedback_history: List[dict]
    
    # Scoring
    current_score: Optional[dict]
    score_history: List[dict]
    score_threshold: float
    
    # Human-in-the-loop
    requires_human_approval: bool
    human_approved: Optional[bool]
    human_feedback: Optional[str]
    
    # Execution state
    pending_orders: List[dict]
    executed_orders: List[dict]
    execution_status: str
    
    # Control flow
    should_refine: bool
    refinement_reason: Optional[str]
    
    # Messages for LangGraph
    messages: List[dict]
