"""
Predefined AI agent workflows.
"""

from ..coordinator import Workflow, WorkflowStep


# Strategy Discovery Workflow
STRATEGY_DISCOVERY_WORKFLOW = Workflow(
    name="strategy_discovery",
    description="Discover, validate, and backtest a new trading strategy",
    steps=[
        WorkflowStep(
            agent="research_agent",
            action="research_strategy",
            output_to="strategy",
            params={
                "objective": "Find profitable trading strategy",
                "symbols": ["BTC/EUR"],
                "timeframe": "1h",
            },
        ),
        WorkflowStep(
            agent="risk_agent",
            action="validate_risk",
            input_from="strategy",
            output_to="risk_report",
        ),
        WorkflowStep(
            agent="execution_agent",
            action="backtest",
            input_from="strategy",
            output_to="backtest_result",
        ),
        WorkflowStep(
            agent="monitoring_agent",
            action="monitor_system",
            output_to="system_status",
        ),
    ],
    agents=["research_agent", "risk_agent", "execution_agent", "monitoring_agent"],
)


# Portfolio Risk Review Workflow
PORTFOLIO_RISK_REVIEW_WORKFLOW = Workflow(
    name="portfolio_risk_review",
    description="Comprehensive portfolio risk analysis",
    steps=[
        WorkflowStep(
            agent="risk_agent",
            action="review_portfolio_risk",
            output_to="risk_report",
            params={"portfolio_id": "default"},
        ),
        WorkflowStep(
            agent="monitoring_agent",
            action="check_health",
            output_to="health_status",
        ),
    ],
    agents=["risk_agent", "monitoring_agent"],
)


# Strategy Execution Workflow
STRATEGY_EXECUTION_WORKFLOW = Workflow(
    name="strategy_execution",
    description="Execute a strategy with risk checks",
    steps=[
        WorkflowStep(
            agent="risk_agent",
            action="validate_risk",
            output_to="risk_validation",
            params={"strategy": {"name": "ma_crossover"}},
        ),
        WorkflowStep(
            agent="execution_agent",
            action="execute_strategy",
            output_to="execution_report",
            params={"strategy_id": "ma_crossover", "mode": "paper"},
        ),
        WorkflowStep(
            agent="monitoring_agent",
            action="monitor_system",
            output_to="system_status",
        ),
    ],
    agents=["risk_agent", "execution_agent", "monitoring_agent"],
)


# All predefined workflows
PREDEFINED_WORKFLOWS = {
    "strategy_discovery": STRATEGY_DISCOVERY_WORKFLOW,
    "portfolio_risk_review": PORTFOLIO_RISK_REVIEW_WORKFLOW,
    "strategy_execution": STRATEGY_EXECUTION_WORKFLOW,
}


def get_workflow(name: str) -> Workflow:
    """
    Get a predefined workflow by name.
    
    Args:
        name: Workflow name
        
    Returns:
        Workflow instance
        
    Raises:
        KeyError: If workflow not found
    """
    if name not in PREDEFINED_WORKFLOWS:
        raise KeyError(f"Workflow not found: {name}")
    return PREDEFINED_WORKFLOWS[name]


def list_workflows() -> list:
    """
    List all available workflows.
    
    Returns:
        List of workflow names
    """
    return list(PREDEFINED_WORKFLOWS.keys())
