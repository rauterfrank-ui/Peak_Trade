"""
Base class for agent tools.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging


logger = logging.getLogger(__name__)


class AgentTool(ABC):
    """
    Base class for agent tools.
    
    Tools provide specific capabilities to agents, such as:
    - Loading market data
    - Running backtests
    - Calculating risk metrics
    - Analyzing statistics
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the tool.
        
        Args:
            config: Tool configuration
        """
        self.config = config or {}
        self.call_count = 0
        logger.debug(f"Initialized tool: {self.name}")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass
    
    @abstractmethod
    def run(self, **kwargs) -> Any:
        """
        Run the tool.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool result
        """
        pass
    
    def _run_wrapper(self, **kwargs) -> Any:
        """
        Wrapper for run method that handles logging and metrics.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            Tool result
        """
        self.call_count += 1
        logger.info(f"Running tool: {self.name} (call #{self.call_count})")
        
        try:
            result = self.run(**kwargs)
            logger.debug(f"Tool {self.name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {self.name} failed: {e}")
            raise
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get tool schema for LangChain integration.
        
        Returns:
            Tool schema dict
        """
        return {
            "name": self.name,
            "description": self.description,
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
