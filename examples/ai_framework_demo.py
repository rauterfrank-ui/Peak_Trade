#!/usr/bin/env python
"""
Example script demonstrating the AI Agent Framework.

This script shows how to:
1. Initialize agents
2. Execute tasks
3. Run workflows
4. Use event bus
5. Track decisions
"""

from src.ai.registry import AgentRegistry
from src.ai.coordinator import AgentCoordinator, Workflow, WorkflowStep
from src.ai.agents.research_agent import StrategyResearchAgent
from src.ai.agents.risk_agent import RiskReviewAgent
from src.ai.agents.execution_agent import StrategyExecutionAgent
from src.ai.agents.monitoring_agent import MonitoringAgent
from src.ai.event_bus import get_global_event_bus, EventType
from src.ai.llm_config import get_global_llm_config


def example_1_basic_agent_usage():
    """Example 1: Basic agent usage."""
    print("\n" + "="*60)
    print("Example 1: Basic Agent Usage")
    print("="*60)
    
    # Create research agent
    research_agent = StrategyResearchAgent(config={
        "min_confidence": 0.75,
        "auto_backtest": True,
    })
    
    print(f"\nAgent: {research_agent.name}")
    print(f"Status: {research_agent.get_status()}")
    
    # Execute research task
    report = research_agent.research_strategy(
        objective="Find mean-reversion strategy for BTC",
        symbols=["BTC/EUR"],
        timeframe="1h",
    )
    
    print(f"\nResearch Report:")
    print(f"  Strategy: {report.strategy_name}")
    print(f"  Objective: {report.objective}")
    print(f"  Confidence: {report.confidence:.2f}")
    print(f"  Recommendation: {report.recommendation}")
    
    # View decision history
    print(f"\nDecision History:")
    for decision in research_agent.get_decision_history():
        print(f"  - {decision['action']} at {decision['timestamp']}")


def example_2_agent_registry():
    """Example 2: Using the agent registry."""
    print("\n" + "="*60)
    print("Example 2: Agent Registry")
    print("="*60)
    
    # Create registry
    registry = AgentRegistry()
    
    # Register agents
    registry.register("research", StrategyResearchAgent)
    registry.register("risk", RiskReviewAgent)
    registry.register("execution", StrategyExecutionAgent)
    registry.register("monitoring", MonitoringAgent)
    
    print(f"\nRegistered agents: {registry.list_agents()}")
    
    # Get agent instances
    research_agent = registry.get_agent("research")
    risk_agent = registry.get_agent("risk")
    
    print(f"\nResearch Agent: {research_agent.name}")
    print(f"Risk Agent: {risk_agent.name}")


def example_3_workflow_execution():
    """Example 3: Multi-agent workflow."""
    print("\n" + "="*60)
    print("Example 3: Multi-Agent Workflow")
    print("="*60)
    
    # Create coordinator with registry
    coordinator = AgentCoordinator()
    
    # Register agents
    coordinator.register_agent("research_agent", StrategyResearchAgent)
    coordinator.register_agent("risk_agent", RiskReviewAgent)
    coordinator.register_agent("execution_agent", StrategyExecutionAgent)
    
    # Define workflow
    workflow = Workflow(
        name="strategy_validation",
        description="Research and validate a strategy",
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
                input_from="strategy",
                output_to="risk_validation",
            ),
            WorkflowStep(
                agent="execution_agent",
                action="backtest",
                input_from="strategy",
                output_to="backtest_result",
            ),
        ],
        agents=["research_agent", "risk_agent", "execution_agent"],
    )
    
    # Execute workflow
    print("\nExecuting workflow...")
    result = coordinator.execute_workflow(workflow)
    
    print(f"\nWorkflow Result:")
    print(f"  Success: {result.success}")
    print(f"  Duration: {result.duration_seconds:.2f}s")
    print(f"  Outputs: {list(result.outputs.keys())}")
    
    if result.errors:
        print(f"  Errors: {result.errors}")


def example_4_event_bus():
    """Example 4: Event-driven communication."""
    print("\n" + "="*60)
    print("Example 4: Event-Driven Communication")
    print("="*60)
    
    # Get event bus
    event_bus = get_global_event_bus()
    
    # Subscribe to events
    received_events = []
    
    @event_bus.on(EventType.STRATEGY_DISCOVERED.value)
    def handle_strategy_discovered(event):
        print(f"\n  Event received: {event.event_type}")
        print(f"  Source: {event.source}")
        print(f"  Data: {event.data}")
        received_events.append(event)
    
    # Publish event
    from src.ai.event_bus import Event
    
    print("\nPublishing strategy_discovered event...")
    event = Event.create(
        event_type=EventType.STRATEGY_DISCOVERED.value,
        source="example_script",
        data={
            "strategy_name": "example_strategy",
            "confidence": 0.85,
        },
    )
    event_bus.publish(event)
    
    print(f"\nTotal events received: {len(received_events)}")


def example_5_llm_config():
    """Example 5: LLM configuration and cost tracking."""
    print("\n" + "="*60)
    print("Example 5: LLM Configuration & Cost Tracking")
    print("="*60)
    
    # Get LLM config
    llm_config = get_global_llm_config()
    
    print(f"\nLLM Provider: {llm_config.provider}")
    print(f"Model: {llm_config.model}")
    print(f"Cost tracking: {llm_config.cost_tracking}")
    
    # Get LLM (will use mock since no API key)
    llm = llm_config.get_llm()
    print(f"\nLLM instance: {type(llm).__name__}")
    
    # Track usage
    cost = llm_config.track_usage(
        input_tokens=1000,
        output_tokens=500,
        provider="openai",
        model="gpt-3.5-turbo",
    )
    
    print(f"\nTracked usage:")
    print(f"  Input tokens: 1000")
    print(f"  Output tokens: 500")
    print(f"  Cost: ${cost:.4f}")
    
    # Get stats
    stats = llm_config.get_stats()
    print(f"\nTotal statistics:")
    print(f"  Total cost: ${stats['total_cost_usd']:.4f}")
    print(f"  Total tokens: {stats['total_tokens']}")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("AI AGENT FRAMEWORK EXAMPLES")
    print("="*60)
    
    try:
        example_1_basic_agent_usage()
        example_2_agent_registry()
        example_3_workflow_execution()
        example_4_event_bus()
        example_5_llm_config()
        
        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
