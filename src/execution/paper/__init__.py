# Canary: exec override mechanism validation
"""
Paper Execution - WP1B (Phase 1 Shadow Trading)

Paper trading simulation with deterministic fill simulation.
"""

from src.execution.paper.broker import PaperBroker, FillSimulationConfig
from src.execution.paper.engine import PaperExecutionEngine
from src.execution.paper.journal import TradeJournal, JournalEntry
from src.execution.paper.daily_summary import DailySummaryGenerator

__all__ = [
    "PaperBroker",
    "FillSimulationConfig",
    "PaperExecutionEngine",
    "TradeJournal",
    "JournalEntry",
    "DailySummaryGenerator",
]
