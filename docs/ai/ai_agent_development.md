# AI Agent Development Guide

## Overview

This guide explains how to develop custom AI agents for the Peak Trade system. The AI agent framework provides a foundation for building autonomous agents that can research strategies, manage risk, execute trades, and monitor system health.

## Architecture

### Core Components

1. **PeakTradeAgent**: Base class for all agents
2. **AgentRegistry**: Central registry for agent management
3. **AgentCoordinator**: Orchestrates multi-agent workflows
4. **EventBus**: Event-driven communication between agents
5. **AgentMemory**: Persistent memory and context management
6. **Tools**: Reusable tools that agents can use

## Creating a New Agent

### Step 1: Define Your Agent Class

```python
from typing import Any, Dict, Optional
from src.ai.framework import PeakTradeAgent

class MyCustomAgent(PeakTradeAgent):
    """
    Custom agent for [specific purpose].
    
    Capabilities:
    - Capability 1
    - Capability 2
    - Capability 3
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            agent_id="my_custom_agent",
            name="My Custom Agent",
            description="Description of what this agent does",
            config=config,
        )
        
        # Initialize agent-specific attributes
        self.my_setting = self.config.get("my_setting", "default_value")
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task.
        
        Args:
            task: Task definition with 'action' and parameters
            
        Returns:
            Task result
        """
        action = task.get("action")
        
        if action == "my_action":
            return self._handle_my_action(task)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def _handle_my_action(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle my_action task."""
        # Implement your logic here
        
        # Log the decision
        self.log_decision(
            action="my_action",
            reasoning="Why I took this action",
            outcome=result,
            metadata={"param": "value"},
        )
        
        return {
            "success": True,
            "result": result,
        }
```

### Step 2: Register Your Agent

```python
from src.ai.registry import get_global_registry

# Register the agent
registry = get_global_registry()
registry.register("my_custom_agent", MyCustomAgent)
```

### Step 3: Configure Your Agent

Add configuration to `config/ai.toml`:

```toml
[ai.my_custom_agent]
enabled = true
my_setting = "custom_value"
check_interval = 60
```

### Step 4: Use Your Agent

```python
from src.ai.registry import get_global_registry

# Get agent instance
registry = get_global_registry()
agent = registry.get_agent("my_custom_agent")

# Execute tasks
result = agent.execute({
    "action": "my_action",
    "param1": "value1",
})

# Check status
status = agent.get_status()
print(f"Agent status: {status}")

# View decision history
history = agent.get_decision_history()
for decision in history:
    print(f"{decision['timestamp']}: {decision['action']}")
```

## Creating Agent Tools

Tools provide specific capabilities that agents can use. Here's how to create a custom tool:

```python
from typing import Any, Dict
from src.ai.tools.base import AgentTool

class MyCustomTool(AgentTool):
    """Custom tool for [specific purpose]."""
    
    @property
    def name(self) -> str:
        return "my_custom_tool"
    
    @property
    def description(self) -> str:
        return "Description of what this tool does"
    
    def run(self, **kwargs) -> Any:
        """
        Run the tool.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool result
        """
        # Implement your tool logic here
        param1 = kwargs.get("param1")
        param2 = kwargs.get("param2")
        
        # Process and return result
        result = {"success": True, "data": processed_data}
        return result
```

### Adding Tools to Agents

```python
# Create tool instance
tool = MyCustomTool(config={"setting": "value"})

# Add to agent
agent.add_tool(tool)

# Use the tool in agent logic
result = tool.run(param1="value1", param2="value2")
```

## Event-Driven Architecture

### Publishing Events

```python
from src.ai.event_bus import get_global_event_bus, Event, EventType

event_bus = get_global_event_bus()

# Create and publish an event
event = Event.create(
    event_type=EventType.STRATEGY_DISCOVERED.value,
    source="my_custom_agent",
    data={
        "strategy_name": "new_strategy",
        "confidence": 0.85,
    },
)
event_bus.publish(event)
```

### Subscribing to Events

```python
from src.ai.event_bus import get_global_event_bus, EventType

event_bus = get_global_event_bus()

def handle_risk_alert(event):
    """Handle risk alert events."""
    print(f"Risk alert from {event.source}: {event.data}")
    # Take appropriate action

# Subscribe using decorator
@event_bus.on(EventType.RISK_ALERT.value)
def auto_handle_risk(event):
    if event.data.get("severity") == "critical":
        # Emergency action
        pass

# Or subscribe explicitly
event_bus.subscribe(EventType.RISK_ALERT.value, handle_risk_alert)
```

## Memory and Context Management

### Using Agent Memory

```python
from src.ai.memory import AgentMemory

memory = AgentMemory()

# Store data
memory.store("strategy_performance", {
    "sharpe": 1.5,
    "max_drawdown": -0.15,
})

# Retrieve data
perf = memory.retrieve("strategy_performance")

# Search memory
results = memory.search("strategy")

# Export memory
json_str = memory.export_json()
```

### Using Vector Memory

```python
from src.ai.memory import VectorMemory

vector_memory = VectorMemory("trading_knowledge")

# Add documents
vector_memory.add_document(
    "Mean reversion works well in ranging markets",
    metadata={"topic": "strategy", "regime": "ranging"},
)

# Search for similar documents
similar = vector_memory.search_similar("range trading", k=5)
```

## Best Practices

### 1. Decision Logging

Always log important decisions for traceability:

```python
self.log_decision(
    action="place_order",
    reasoning="Entry signal triggered with confidence 0.85",
    outcome={"order_id": "12345", "status": "filled"},
    metadata={"symbol": "BTC/EUR", "size": 0.1},
)
```

### 2. Error Handling

Handle errors gracefully and log them:

```python
try:
    result = self.execute_risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    self.log_decision(
        action="operation_failed",
        reasoning=f"Error: {str(e)}",
        outcome={"success": False},
    )
    raise
```

### 3. Configuration Management

Use configuration for all tunable parameters:

```python
def __init__(self, config=None):
    super().__init__(...)
    
    # Load from config
    self.threshold = self.config.get("threshold", 0.75)
    self.timeout = self.config.get("timeout", 30)
    self.retry_count = self.config.get("retry_count", 3)
```

### 4. Testing

Write tests for your agents:

```python
import pytest
from src.ai.agents.my_custom_agent import MyCustomAgent

class TestMyCustomAgent:
    def test_agent_initialization(self):
        agent = MyCustomAgent()
        assert agent.agent_id == "my_custom_agent"
    
    def test_execute_task(self):
        agent = MyCustomAgent()
        result = agent.execute({"action": "my_action"})
        assert result["success"] is True
```

### 5. Cost Tracking

Track LLM usage for cost control:

```python
from src.ai.llm_config import get_global_llm_config

llm_config = get_global_llm_config()

# Use LLM
llm = llm_config.get_llm()
response = llm.invoke(messages)

# Track usage
llm_config.track_usage(
    input_tokens=100,
    output_tokens=50,
)

# Check stats
stats = llm_config.get_stats()
print(f"Total cost: ${stats['total_cost_usd']:.2f}")
```

## Safety and Approval Gates

### Live Trading Approval

Always require explicit approval for live trading:

```python
class TradingAgent(PeakTradeAgent):
    def execute_trade(self, mode="paper"):
        if mode == "live" and self.require_approval:
            raise ValueError("Live trading requires explicit approval")
        
        # Execute trade
        ...
```

### Risk Checks

Perform pre-trade risk checks:

```python
def execute_strategy(self, strategy_id):
    # Pre-trade risk check
    risk_result = self.risk_tool.run(portfolio_id="main")
    
    if risk_result["risk_score"] > 0.8:
        logger.warning("Risk too high, aborting execution")
        return {"success": False, "reason": "risk_too_high"}
    
    # Proceed with execution
    ...
```

## Examples

See the existing agents for complete examples:
- `src/ai/agents/research_agent.py` - Strategy research
- `src/ai/agents/risk_agent.py` - Risk management
- `src/ai/agents/execution_agent.py` - Trade execution
- `src/ai/agents/monitoring_agent.py` - System monitoring

## Further Reading

- [AI Workflows Guide](ai_workflows.md)
- [Prompt Engineering Guide](prompt_engineering.md)
- Configuration reference: `config/ai.toml`
