"""
Agent Registry for managing all AI agents in the system.
"""

from typing import Dict, List, Type, Optional
import logging

from .framework import PeakTradeAgent


logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Central registry for all AI agents.
    
    This registry maintains a catalog of available agents and provides
    methods to register, retrieve, and list agents.
    """
    
    def __init__(self):
        """Initialize the agent registry."""
        self._agents: Dict[str, Type[PeakTradeAgent]] = {}
        self._instances: Dict[str, PeakTradeAgent] = {}
        logger.info("Initialized AgentRegistry")
    
    def register(
        self,
        agent_id: str,
        agent_class: Type[PeakTradeAgent],
    ) -> None:
        """
        Register an agent class.
        
        Args:
            agent_id: Unique identifier for this agent
            agent_class: Agent class to register
            
        Raises:
            ValueError: If agent_id is already registered
        """
        if agent_id in self._agents:
            raise ValueError(f"Agent {agent_id} is already registered")
        
        if not issubclass(agent_class, PeakTradeAgent):
            raise TypeError(f"Agent class must be a subclass of PeakTradeAgent")
        
        self._agents[agent_id] = agent_class
        logger.info(f"Registered agent class: {agent_id} -> {agent_class.__name__}")
    
    def get_agent(
        self,
        agent_id: str,
        config: Optional[Dict] = None,
        create_new: bool = False,
    ) -> PeakTradeAgent:
        """
        Get an agent instance.
        
        Args:
            agent_id: Agent identifier
            config: Configuration to pass to agent (for new instances)
            create_new: If True, always create a new instance
            
        Returns:
            Agent instance
            
        Raises:
            KeyError: If agent_id is not registered
        """
        if agent_id not in self._agents:
            raise KeyError(f"Agent {agent_id} is not registered")
        
        # Return existing instance if available and not creating new
        if not create_new and agent_id in self._instances:
            return self._instances[agent_id]
        
        # Create new instance
        agent_class = self._agents[agent_id]
        agent_instance = agent_class(config=config or {})
        
        # Store instance if not creating new
        if not create_new:
            self._instances[agent_id] = agent_instance
        
        logger.debug(f"Retrieved agent: {agent_id}")
        return agent_instance
    
    def list_agents(self) -> List[str]:
        """
        List all registered agent IDs.
        
        Returns:
            List of agent IDs
        """
        return list(self._agents.keys())
    
    def unregister(self, agent_id: str) -> None:
        """
        Unregister an agent.
        
        Args:
            agent_id: Agent identifier
        """
        if agent_id in self._agents:
            del self._agents[agent_id]
        if agent_id in self._instances:
            del self._instances[agent_id]
        logger.info(f"Unregistered agent: {agent_id}")
    
    def clear(self) -> None:
        """Clear all registered agents."""
        self._agents.clear()
        self._instances.clear()
        logger.info("Cleared all agents from registry")
    
    def get_agent_info(self, agent_id: str) -> Dict:
        """
        Get information about a registered agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dict with agent information
            
        Raises:
            KeyError: If agent_id is not registered
        """
        if agent_id not in self._agents:
            raise KeyError(f"Agent {agent_id} is not registered")
        
        agent_class = self._agents[agent_id]
        has_instance = agent_id in self._instances
        
        return {
            "agent_id": agent_id,
            "class_name": agent_class.__name__,
            "has_instance": has_instance,
            "module": agent_class.__module__,
        }


# Global registry instance
_global_registry: Optional[AgentRegistry] = None


def get_global_registry() -> AgentRegistry:
    """
    Get the global agent registry.
    
    Returns:
        Global AgentRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry
