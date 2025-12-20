# AI Agent Workflows

## Overview

Workflows orchestrate multiple agents to accomplish complex tasks. The Peak Trade AI framework supports defining, executing, and monitoring multi-agent workflows.

## Predefined Workflows

### 1. Strategy Discovery Workflow

Discovers, validates, and backtests new trading strategies.

**Steps:**
1. **Research Agent**: Analyzes data and generates strategy hypothesis
2. **Risk Agent**: Validates risk characteristics
3. **Execution Agent**: Runs backtest
4. **Monitoring Agent**: Checks system health

**Usage:**
```python
from src.ai.coordinator import AgentCoordinator
from src.ai.workflows import STRATEGY_DISCOVERY_WORKFLOW

coordinator = AgentCoordinator()
result = coordinator.execute_workflow(STRATEGY_DISCOVERY_WORKFLOW)

if result.success:
    strategy = result.outputs["strategy"]
    backtest = result.outputs["backtest_result"]
    print(f"Strategy: {strategy}")
    print(f"Backtest return: {backtest['total_return']}")
```

### 2. Portfolio Risk Review Workflow

Comprehensive portfolio risk analysis.

**Steps:**
1. **Risk Agent**: Analyzes portfolio risk metrics
2. **Monitoring Agent**: Checks system health

**Usage:**
```python
from src.ai.workflows import PORTFOLIO_RISK_REVIEW_WORKFLOW

result = coordinator.execute_workflow(PORTFOLIO_RISK_REVIEW_WORKFLOW)

if result.success:
    risk_report = result.outputs["risk_report"]
    print(f"Risk severity: {risk_report.severity}")
    print(f"Violations: {risk_report.violations}")
```

### 3. Strategy Execution Workflow

Executes a strategy with risk checks.

**Steps:**
1. **Risk Agent**: Validates strategy risk
2. **Execution Agent**: Executes strategy
3. **Monitoring Agent**: Monitors execution

**Usage:**
```python
from src.ai.workflows import STRATEGY_EXECUTION_WORKFLOW

result = coordinator.execute_workflow(STRATEGY_EXECUTION_WORKFLOW)

if result.success:
    execution = result.outputs["execution_report"]
    print(f"Orders placed: {execution.orders_placed}")
    print(f"Status: {execution.status}")
```

## Creating Custom Workflows

### Basic Workflow Definition

```python
from src.ai.coordinator import Workflow, WorkflowStep

# Define workflow
my_workflow = Workflow(
    name="my_custom_workflow",
    description="My custom workflow description",
    steps=[
        WorkflowStep(
            agent="research_agent",
            action="research_strategy",
            output_to="strategy",
            params={
                "objective": "Find profitable strategy",
                "symbols": ["BTC/EUR"],
                "timeframe": "1h",
            },
        ),
        WorkflowStep(
            agent="risk_agent",
            action="validate_risk",
            input_from="strategy",  # Uses output from previous step
            output_to="risk_validation",
        ),
    ],
    agents=["research_agent", "risk_agent"],
)

# Execute workflow
coordinator = AgentCoordinator()
result = coordinator.execute_workflow(my_workflow)
```

### Workflow with Conditional Logic

For more complex workflows, you can implement conditional logic:

```python
from src.ai.coordinator import Workflow, WorkflowStep

# First, define the workflow steps
workflow = Workflow(
    name="conditional_workflow",
    description="Workflow with conditional execution",
    steps=[
        WorkflowStep(
            agent="research_agent",
            action="research_strategy",
            output_to="strategy",
        ),
        WorkflowStep(
            agent="risk_agent",
            action="validate_risk",
            input_from="strategy",
            output_to="risk_validation",
        ),
    ],
    agents=["research_agent", "risk_agent"],
)

# Execute and check results
result = coordinator.execute_workflow(workflow)

# Conditional logic based on results
if result.success:
    risk_validation = result.outputs["risk_validation"]
    
    if risk_validation["validation"]["valid"]:
        # Proceed with execution
        execution_workflow = Workflow(
            name="execute_strategy",
            description="Execute validated strategy",
            steps=[
                WorkflowStep(
                    agent="execution_agent",
                    action="execute_strategy",
                    params={
                        "strategy_id": result.outputs["strategy"]["strategy_name"],
                        "mode": "paper",
                    },
                    output_to="execution_result",
                ),
            ],
            agents=["execution_agent"],
        )
        
        execution_result = coordinator.execute_workflow(execution_workflow)
```

### Parallel Agent Execution

For tasks that can run in parallel:

```python
from src.ai.coordinator import Workflow, WorkflowStep

# Create workflow with parallel-capable steps
# (Steps that don't depend on each other can be run in parallel)
parallel_workflow = Workflow(
    name="parallel_analysis",
    description="Parallel analysis of multiple symbols",
    steps=[
        # These steps don't have input_from, so can run in parallel
        WorkflowStep(
            agent="research_agent",
            action="research_strategy",
            output_to="btc_analysis",
            params={"symbols": ["BTC/EUR"]},
        ),
        WorkflowStep(
            agent="research_agent",
            action="research_strategy",
            output_to="eth_analysis",
            params={"symbols": ["ETH/EUR"]},
        ),
        WorkflowStep(
            agent="research_agent",
            action="research_strategy",
            output_to="ltc_analysis",
            params={"symbols": ["LTC/EUR"]},
        ),
    ],
    agents=["research_agent"],
)
```

## Workflow Parameters

### Initial Context

Pass initial context to workflows:

```python
result = coordinator.execute_workflow(
    workflow,
    initial_context={
        "user_id": "trader_123",
        "risk_tolerance": "medium",
        "max_drawdown": -0.20,
    },
)
```

Agents can access context in their task:
```python
def execute(self, task):
    context = task.get("context", {})
    risk_tolerance = context.get("risk_tolerance", "medium")
    # Use context in decision making
```

### Step Parameters

Pass parameters to individual steps:

```python
WorkflowStep(
    agent="research_agent",
    action="research_strategy",
    output_to="strategy",
    params={
        "objective": "Find momentum strategy",
        "symbols": ["BTC/EUR", "ETH/EUR"],
        "timeframe": "4h",
        "lookback_days": 30,
    },
)
```

## Error Handling

### Handling Failed Steps

```python
result = coordinator.execute_workflow(workflow)

if not result.success:
    print(f"Workflow failed: {result.errors}")
    for error in result.errors:
        print(f"  - {error}")

# Partial results may still be available
if "step1_result" in result.outputs:
    print(f"Step 1 completed: {result.outputs['step1_result']}")
```

### Retry Logic

Implement retry logic for critical workflows:

```python
def execute_workflow_with_retry(coordinator, workflow, max_retries=3):
    """Execute workflow with retry logic."""
    for attempt in range(max_retries):
        result = coordinator.execute_workflow(workflow)
        
        if result.success:
            return result
        
        print(f"Attempt {attempt + 1} failed, retrying...")
        time.sleep(2 ** attempt)  # Exponential backoff
    
    raise Exception("Workflow failed after maximum retries")
```

## Monitoring Workflows

### Execution Time

```python
result = coordinator.execute_workflow(workflow)
print(f"Workflow completed in {result.duration_seconds:.2f} seconds")
```

### Step-by-Step Results

```python
result = coordinator.execute_workflow(workflow)

for step_name, step_result in result.outputs.items():
    print(f"\n{step_name}:")
    print(f"  Success: {step_result.get('success')}")
    # Print step-specific results
```

## Best Practices

### 1. Workflow Naming

Use clear, descriptive names:
- ✅ `"strategy_discovery_and_validation"`
- ✅ `"portfolio_rebalancing_workflow"`
- ❌ `"workflow1"`
- ❌ `"test"`

### 2. Step Dependencies

Make dependencies explicit through `input_from` and `output_to`:

```python
WorkflowStep(
    agent="risk_agent",
    action="validate_risk",
    input_from="strategy",  # Explicitly depends on previous step
    output_to="risk_report",
)
```

### 3. Error Recovery

Design workflows with error recovery in mind:

```python
# Check intermediate results
result = coordinator.execute_workflow(workflow)

if not result.success and "strategy" in result.outputs:
    # Strategy was generated but validation failed
    # Save strategy for manual review
    save_strategy_for_review(result.outputs["strategy"])
```

### 4. Configuration

Store workflow parameters in configuration:

```toml
# config/ai.toml
[ai.workflows.strategy_discovery]
default_symbols = ["BTC/EUR", "ETH/EUR"]
default_timeframe = "1h"
min_confidence = 0.75
```

Load in code:
```python
import toml

config = toml.load("config/ai.toml")
workflow_config = config["ai"]["workflows"]["strategy_discovery"]

params = {
    "symbols": workflow_config["default_symbols"],
    "timeframe": workflow_config["default_timeframe"],
}
```

### 5. Testing Workflows

Test workflows with mock agents:

```python
import pytest
from src.ai.coordinator import AgentCoordinator, Workflow, WorkflowStep

def test_custom_workflow():
    """Test custom workflow execution."""
    coordinator = AgentCoordinator()
    
    # Register mock agents
    coordinator.register_agent("mock_agent", MockAgent)
    
    # Define test workflow
    workflow = Workflow(
        name="test_workflow",
        description="Test workflow",
        steps=[
            WorkflowStep(
                agent="mock_agent",
                action="test_action",
                output_to="result",
            ),
        ],
        agents=["mock_agent"],
    )
    
    # Execute and verify
    result = coordinator.execute_workflow(workflow)
    assert result.success
    assert "result" in result.outputs
```

## Event-Driven Workflows

Workflows can be triggered by events:

```python
from src.ai.event_bus import get_global_event_bus, EventType

event_bus = get_global_event_bus()

@event_bus.on(EventType.RISK_ALERT.value)
def handle_risk_alert(event):
    """Trigger risk review workflow on alert."""
    if event.data.get("severity") == "critical":
        coordinator = AgentCoordinator()
        result = coordinator.execute_workflow(PORTFOLIO_RISK_REVIEW_WORKFLOW)
        
        if not result.success:
            # Escalate
            send_emergency_alert()
```

## Examples

### Complete Strategy Research Flow

```python
from src.ai.coordinator import AgentCoordinator, Workflow, WorkflowStep

def research_and_deploy_strategy():
    """Complete flow from research to deployment."""
    
    coordinator = AgentCoordinator()
    
    # 1. Research workflow
    research_workflow = Workflow(
        name="research_phase",
        description="Research new strategy",
        steps=[
            WorkflowStep(
                agent="research_agent",
                action="research_strategy",
                params={
                    "objective": "Find mean-reversion strategy",
                    "symbols": ["BTC/EUR"],
                    "timeframe": "1h",
                },
                output_to="strategy",
            ),
        ],
        agents=["research_agent"],
    )
    
    research_result = coordinator.execute_workflow(research_workflow)
    
    if not research_result.success:
        return {"success": False, "stage": "research"}
    
    strategy = research_result.outputs["strategy"]
    
    # 2. Validation workflow
    validation_workflow = Workflow(
        name="validation_phase",
        description="Validate strategy",
        steps=[
            WorkflowStep(
                agent="risk_agent",
                action="validate_risk",
                params={"strategy": strategy},
                output_to="risk_validation",
            ),
            WorkflowStep(
                agent="execution_agent",
                action="backtest",
                params={"strategy_id": strategy["report"].strategy_name},
                output_to="backtest_result",
            ),
        ],
        agents=["risk_agent", "execution_agent"],
    )
    
    validation_result = coordinator.execute_workflow(validation_workflow)
    
    if not validation_result.success:
        return {"success": False, "stage": "validation"}
    
    # 3. Deployment decision
    risk_validation = validation_result.outputs["risk_validation"]
    backtest = validation_result.outputs["backtest_result"]
    
    if (risk_validation["validation"]["valid"] and
        backtest["backtest_result"]["sharpe_ratio"] > 1.0):
        
        # Deploy to paper trading
        deployment_workflow = Workflow(
            name="deployment_phase",
            description="Deploy to paper trading",
            steps=[
                WorkflowStep(
                    agent="execution_agent",
                    action="execute_strategy",
                    params={
                        "strategy_id": strategy["report"].strategy_name,
                        "mode": "paper",
                    },
                    output_to="execution",
                ),
                WorkflowStep(
                    agent="monitoring_agent",
                    action="monitor_system",
                    output_to="monitoring",
                ),
            ],
            agents=["execution_agent", "monitoring_agent"],
        )
        
        deployment_result = coordinator.execute_workflow(deployment_workflow)
        
        return {
            "success": deployment_result.success,
            "stage": "deployment",
            "execution": deployment_result.outputs.get("execution"),
        }
    
    return {
        "success": False,
        "stage": "approval",
        "reason": "Did not meet deployment criteria",
    }
```

## Further Reading

- [AI Agent Development Guide](ai_agent_development.md)
- [Prompt Engineering Guide](prompt_engineering.md)
- API Reference: `src/ai/coordinator.py`
