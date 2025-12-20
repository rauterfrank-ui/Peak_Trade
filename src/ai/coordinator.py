"""
Agent Coordinator for multi-agent workflows.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import logging

from .framework import PeakTradeAgent
from .registry import AgentRegistry


logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """
    Single step in a workflow.
    
    Attributes:
        agent: Agent identifier
        action: Action to execute
        input_from: Input from previous step (optional)
        output_to: Output variable name
        params: Additional parameters
    """
    agent: str
    action: str
    input_from: Optional[str] = None
    output_to: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


@dataclass
class Workflow:
    """
    Multi-agent workflow definition.
    
    Attributes:
        name: Workflow name
        description: Workflow description
        steps: List of workflow steps
        agents: Agent IDs used in workflow
    """
    name: str
    description: str
    steps: List[WorkflowStep]
    agents: List[str]


@dataclass
class WorkflowResult:
    """
    Workflow execution result.
    
    Attributes:
        workflow_name: Name of executed workflow
        success: Whether workflow succeeded
        outputs: Outputs from each step
        errors: Any errors encountered
        duration_seconds: Execution duration
    """
    workflow_name: str
    success: bool
    outputs: Dict[str, Any]
    errors: List[str]
    duration_seconds: float = 0.0


class AgentCoordinator:
    """
    Orchestrates multi-agent workflows.
    
    Features:
    - Agent-to-agent communication
    - Task distribution
    - Result aggregation
    - Conflict resolution
    """
    
    def __init__(self, registry: Optional[AgentRegistry] = None):
        """
        Initialize the coordinator.
        
        Args:
            registry: Agent registry to use
        """
        self.registry = registry or AgentRegistry()
        logger.info("Initialized AgentCoordinator")
    
    def execute_workflow(
        self,
        workflow: Workflow,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """
        Execute a multi-agent workflow.
        
        Args:
            workflow: Workflow to execute
            initial_context: Initial context/inputs
            
        Returns:
            WorkflowResult with outputs
            
        Example:
            workflow = Workflow(
                name="strategy_discovery",
                description="Discover and validate a strategy",
                steps=[
                    WorkflowStep(agent="research", action="research_strategy", output_to="strategy"),
                    WorkflowStep(agent="risk", action="validate_risk", input_from="strategy", output_to="risk_report"),
                    WorkflowStep(agent="execution", action="backtest", input_from="strategy", output_to="backtest_result"),
                ],
                agents=["research", "risk", "execution"],
            )
            result = coordinator.execute_workflow(workflow)
        """
        logger.info(f"Starting workflow: {workflow.name}")
        
        import time
        start_time = time.time()
        
        context = initial_context or {}
        outputs = {}
        errors = []
        
        try:
            for step_idx, step in enumerate(workflow.steps):
                logger.debug(f"Executing step {step_idx + 1}/{len(workflow.steps)}: {step.agent}.{step.action}")
                
                # Get agent
                try:
                    agent = self.registry.get_agent(step.agent)
                except KeyError:
                    error_msg = f"Agent not found: {step.agent}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
                
                # Prepare task
                task = {
                    "action": step.action,
                }
                
                # Add input from previous step if specified
                if step.input_from and step.input_from in outputs:
                    task["input"] = outputs[step.input_from]
                
                # Add additional parameters
                if step.params:
                    task.update(step.params)
                
                # Add context
                task["context"] = context
                
                # Execute task
                try:
                    result = agent.execute(task)
                    
                    # Store output
                    if step.output_to:
                        outputs[step.output_to] = result
                    
                    logger.debug(f"Step {step_idx + 1} completed successfully")
                    
                except Exception as e:
                    error_msg = f"Step {step_idx + 1} failed: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
            
            success = len(errors) == 0
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            success = False
        
        duration = time.time() - start_time
        
        result = WorkflowResult(
            workflow_name=workflow.name,
            success=success,
            outputs=outputs,
            errors=errors,
            duration_seconds=duration,
        )
        
        logger.info(f"Workflow {workflow.name} completed: success={success}, duration={duration:.2f}s")
        return result
    
    def register_agent(self, agent_id: str, agent_class: type) -> None:
        """
        Register an agent with the coordinator.
        
        Args:
            agent_id: Agent identifier
            agent_class: Agent class
        """
        self.registry.register(agent_id, agent_class)
    
    def list_agents(self) -> List[str]:
        """
        List all registered agents.
        
        Returns:
            List of agent IDs
        """
        return self.registry.list_agents()
