"""Researcher Team Module.

Implements bullish and bearish researchers that debate to reach
balanced investment conclusions through dialectical analysis.
"""

from .state import ResearcherState, DebateRound, ResearchReport
from .bullish_researcher import BullishResearcher
from .bearish_researcher import BearishResearcher
from .debate import DebateCoordinator
from .team import ResearcherTeam

__all__ = [
    "ResearcherState",
    "DebateRound",
    "ResearchReport",
    "BullishResearcher",
    "BearishResearcher",
    "DebateCoordinator",
    "ResearcherTeam",
]
