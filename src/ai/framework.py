"""
Base framework for Peak Trade AI Agents.

This module provides the base class and core functionality for all AI agents
in the Peak Trade system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

try:
    from langchain.memory import ConversationBufferMemory
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ConversationBufferMemory = None


logger = logging.getLogger(__name__)


class PeakTradeAgent(ABC):
    """
    Base class for all Peak Trade AI Agents.
    
    Features:
    - LangChain Integration (optional)
    - Tool Access (Backtest, Data, Analysis)
    - Memory/Context Management
    - Event-Driven Actions
    
    Attributes:
        agent_id: Unique identifier for this agent
        name: Human-readable name
        description: Agent description
        tools: List of tools available to this agent
        memory: Conversation/context memory
        config: Agent configuration
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        config: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Any]] = None,
    ):
        """
        Initialize the agent.
        
        Args:
            agent_id: Unique identifier for this agent
            name: Human-readable name
            description: Agent description
            config: Agent configuration dict
            tools: List of tools available to this agent
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.config = config or {}
        self.tools = tools or []
        self.enabled = self.config.get("enabled", True)
        
        # Initialize memory if LangChain is available
        if LANGCHAIN_AVAILABLE and self.config.get("use_memory", True):
            self.memory = ConversationBufferMemory()
        else:
            self.memory = None
        
        # Decision log
        self.decision_log: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized agent: {self.name} ({self.agent_id})")
    
    @abstractmethod
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task.
        
        Args:
            task: Task definition with parameters
            
        Returns:
            Task result
        """
        pass
    
    def log_decision(
        self,
        action: str,
        reasoning: str,
        outcome: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log an agent decision for traceability.
        
        Args:
            action: Action taken
            reasoning: Why this action was chosen
            outcome: Result of the action
            metadata: Additional metadata
        """
        decision = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": self.agent_id,
            "action": action,
            "reasoning": reasoning,
            "outcome": outcome,
            "metadata": metadata or {},
        }
        self.decision_log.append(decision)
        logger.info(f"Decision logged: {action} by {self.agent_id}")
    
    def get_decision_history(self) -> List[Dict[str, Any]]:
        """Get the agent's decision history."""
        return self.decision_log
    
    def add_tool(self, tool: Any) -> None:
        """
        Add a tool to this agent.
        
        Args:
            tool: Tool instance to add
        """
        self.tools.append(tool)
        logger.debug(f"Added tool to {self.agent_id}: {getattr(tool, 'name', 'unknown')}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of this agent.
        
        Returns:
            Status dict with agent information
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "enabled": self.enabled,
            "tools_count": len(self.tools),
            "decisions_count": len(self.decision_log),
            "memory_enabled": self.memory is not None,
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.agent_id}>"
