"""
Peak Trade AI Agent Framework

AI-powered autonomous agents for trading research, strategy execution,
risk review, and system monitoring.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .framework import PeakTradeAgent
    from .registry import AgentRegistry
    from .coordinator import AgentCoordinator

__all__ = ["PeakTradeAgent", "AgentRegistry", "AgentCoordinator"]
