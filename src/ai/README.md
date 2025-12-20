# Peak Trade AI Agent Framework

## Overview

The Peak Trade AI Agent Framework provides autonomous AI agents for trading research, strategy execution, risk management, and system monitoring. Built on LangChain with support for multiple LLM providers.

## Features

- 🤖 **4 Core Agents**: Research, Risk Review, Strategy Execution, System Monitoring
- 🔄 **Multi-Agent Workflows**: Orchestrate complex tasks across multiple agents
- 📡 **Event-Driven Architecture**: Pub/Sub system for agent communication
- 🧠 **Memory Management**: Persistent memory and vector-based semantic search
- 💰 **Cost Tracking**: Monitor and limit LLM usage costs
- 🔒 **Safety First**: Approval gates, risk checks, decision logging
- 🧪 **Well-Tested**: 103 tests with 100% pass rate
- 📚 **Comprehensive Documentation**: Complete guides and examples

## Quick Start

### Installation

Install with AI dependencies:

```bash
pip install -e ".[ai]"
```

This installs:
- langchain >= 0.1.0
- langchain-openai >= 0.0.5
- langchain-community >= 0.0.20
- chromadb >= 0.4.0
- tiktoken >= 0.5.0

### Configuration

Set up your LLM API key:

```bash
export OPENAI_API_KEY="your-api-key"
```

Configure agents in `config/ai.toml`:

```toml
[ai]
enabled = true
default_provider = "openai"
daily_cost_limit = 10.0

[ai.research_agent]
enabled = true
min_confidence = 0.75

[ai.llm]
provider = "openai"
model = "gpt-4-turbo-preview"
```

### Basic Usage

```python
from src.ai.agents.research_agent import StrategyResearchAgent

# Create agent
agent = StrategyResearchAgent()

# Research a strategy
report = agent.research_strategy(
    objective="Find mean-reversion strategy for BTC",
    symbols=["BTC/EUR"],
    timeframe="1h",
)

print(f"Strategy: {report.strategy_name}")
print(f"Confidence: {report.confidence}")
```

### Multi-Agent Workflow

```python
from src.ai.coordinator import AgentCoordinator
from src.ai.workflows import STRATEGY_DISCOVERY_WORKFLOW

# Create coordinator
coordinator = AgentCoordinator()

# Execute workflow
result = coordinator.execute_workflow(STRATEGY_DISCOVERY_WORKFLOW)

if result.success:
    strategy = result.outputs["strategy"]
    backtest = result.outputs["backtest_result"]
    print(f"Strategy discovered: {strategy}")
```

## Architecture

### Core Components

```
src/ai/
├── framework.py          # Base agent class
├── registry.py           # Agent registry
├── coordinator.py        # Multi-agent orchestration
├── event_bus.py          # Event-driven communication
├── memory.py             # Memory management
├── llm_config.py         # LLM configuration
├── agents/               # Agent implementations
│   ├── research_agent.py
│   ├── risk_agent.py
│   ├── execution_agent.py
│   └── monitoring_agent.py
├── tools/                # Agent tools
│   ├── data_loader_tool.py
│   ├── backtest_tool.py
│   ├── analysis_tool.py
│   └── risk_tool.py
├── workflows/            # Predefined workflows
└── prompts/              # Prompt templates
```

### Agents

1. **Strategy Research Agent** (`research_agent.py`)
   - Analyzes market data
   - Generates strategy hypotheses
   - Runs backtests
   - Provides recommendations

2. **Risk Review Agent** (`risk_agent.py`)
   - Monitors portfolio risk
   - Validates strategies
   - Generates risk alerts
   - Enforces risk limits

3. **Strategy Execution Agent** (`execution_agent.py`)
   - Executes strategies (paper/live)
   - Pre-trade risk checks
   - Order management
   - Post-trade analysis

4. **Monitoring Agent** (`monitoring_agent.py`)
   - System health checks
   - Performance tracking
   - Anomaly detection
   - Self-healing triggers

### Tools

Agents use tools to interact with the system:

- **DataLoaderTool**: Load market data
- **BacktestTool**: Run backtests
- **AnalysisTool**: Statistical analysis
- **RiskCalculatorTool**: Risk metrics

### Event Bus

Event-driven communication between agents:

```python
from src.ai.event_bus import get_global_event_bus, EventType

event_bus = get_global_event_bus()

@event_bus.on(EventType.RISK_ALERT.value)
def handle_risk_alert(event):
    print(f"Risk alert: {event.data}")

# Agents publish events automatically
```

## Examples

### Run Demo Script

```bash
PYTHONPATH=. python examples/ai_framework_demo.py
```

The demo shows:
1. Basic agent usage
2. Agent registry
3. Multi-agent workflows
4. Event-driven communication
5. LLM configuration and cost tracking

### Create Custom Agent

```python
from src.ai.framework import PeakTradeAgent

class MyCustomAgent(PeakTradeAgent):
    def __init__(self, config=None):
        super().__init__(
            agent_id="my_agent",
            name="My Custom Agent",
            description="Does something awesome",
            config=config,
        )
    
    def execute(self, task):
        # Implement your logic
        return {"success": True}
```

See [docs/ai/ai_agent_development.md](../../docs/ai/ai_agent_development.md) for details.

## Testing

Run all AI framework tests:

```bash
pytest tests/ai/ -v
```

Current test coverage:
- 103 tests
- 100% pass rate
- Tests for agents, tools, workflows, and LLM config

## Documentation

- **[AI Agent Development Guide](../../docs/ai/ai_agent_development.md)**: How to create custom agents
- **[AI Workflows Guide](../../docs/ai/ai_workflows.md)**: Multi-agent workflow orchestration
- **[Prompt Engineering Guide](../../docs/ai/prompt_engineering.md)**: Writing effective prompts

## Configuration Reference

See `config/ai.toml` for complete configuration options:

```toml
[ai]
enabled = true
default_provider = "openai"
max_concurrent_agents = 5
daily_cost_limit = 10.0

[ai.research_agent]
enabled = true
auto_backtest = true
min_confidence = 0.75

[ai.risk_agent]
enabled = true
auto_enforcement = false
alert_threshold = 0.8

[ai.execution_agent]
enabled = true
mode = "paper"
require_approval = true

[ai.monitoring_agent]
enabled = true
check_interval = 60

[ai.llm]
provider = "openai"
model = "gpt-4-turbo-preview"
api_key = "${OPENAI_API_KEY}"
max_tokens = 4000
cost_limit_daily = 10.0
```

## LLM Providers

### OpenAI

```bash
export OPENAI_API_KEY="sk-..."
```

```toml
[ai.llm]
provider = "openai"
model = "gpt-4-turbo-preview"
```

### Anthropic

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

```toml
[ai.llm]
provider = "anthropic"
model = "claude-3-opus"
```

### Local (Ollama)

```toml
[ai.llm]
provider = "local"
model = "llama2"
```

### Mock (Testing)

```toml
[ai.llm]
provider = "mock"
```

No API key required, returns placeholder responses.

## Safety & Compliance

### Approval Gates

Live trading requires explicit approval:

```python
agent = StrategyExecutionAgent(config={
    "require_approval": True  # Default
})

# This will raise an error
agent.execute_strategy(strategy_id="test", mode="live")
```

### Cost Limits

Set daily limits to control costs:

```toml
[ai.llm]
cost_limit_daily = 10.0  # USD
token_budget_per_agent = 100000
```

### Decision Logging

All agent decisions are logged for traceability:

```python
agent.log_decision(
    action="place_order",
    reasoning="Entry signal with confidence 0.85",
    outcome={"order_id": "12345"},
)

# View history
history = agent.get_decision_history()
```

## Troubleshooting

### "No module named langchain"

Install AI dependencies:

```bash
pip install -e ".[ai]"
```

### "OPENAI_API_KEY not set"

Set your API key:

```bash
export OPENAI_API_KEY="your-key"
```

Or use mock provider for testing:

```toml
[ai.llm]
provider = "mock"
```

### "Live trading requires approval"

This is a safety feature. Either:
1. Use paper trading mode
2. Disable approval gate (not recommended):
   ```python
   agent = StrategyExecutionAgent(config={"require_approval": False})
   ```

## Contributing

When adding new agents:

1. Extend `PeakTradeAgent` base class
2. Implement `execute()` method
3. Add configuration to `config/ai.toml`
4. Write tests in `tests/ai/`
5. Update documentation

See [AI Agent Development Guide](../../docs/ai/ai_agent_development.md).

## License

Proprietary - Peak Trade

## Support

- Documentation: `docs/ai/`
- Examples: `examples/ai_framework_demo.py`
- Tests: `tests/ai/`
- Issues: GitHub Issues
