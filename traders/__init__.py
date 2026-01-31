"""Trader Team Module.

Implements trading agents responsible for executing decisions based on
analyst and researcher insights, with human-in-the-loop approval and
feedback-driven reasoning.
"""

from .state import (
    TraderState,
    TradeOrder,
    TradeDecision,
    FeedbackScore,
    PortfolioPosition,
)
from .trader_agent import TraderAgent
from .risk_manager import RiskManager
from .portfolio_manager import PortfolioManager
from .execution import TradeExecutor
from .team import TraderTeam

__all__ = [
    "TraderState",
    "TradeOrder",
    "TradeDecision",
    "FeedbackScore",
    "PortfolioPosition",
    "TraderAgent",
    "RiskManager",
    "PortfolioManager",
    "TradeExecutor",
    "TraderTeam",
]
