"""
Peak_Trade Autonomous Workflow Engine
======================================

Workflow execution and coordination for autonomous workflows.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import subprocess
import sys


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowState:
    """
    Current state of a workflow.
    
    Attributes:
        workflow_id: Unique workflow identifier
        name: Workflow name
        status: Current execution status
        started_at: Start timestamp
        finished_at: Finish timestamp
        metadata: Additional state information
    """
    workflow_id: str
    name: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate workflow duration."""
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None


@dataclass
class WorkflowResult:
    """
    Result of workflow execution.
    
    Attributes:
        workflow_id: Unique workflow identifier
        success: Whether execution was successful
        status: Final status
        output: Workflow output data
        error: Error message if failed
        metadata: Additional result information
    """
    workflow_id: str
    success: bool
    status: WorkflowStatus
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowEngine:
    """
    Autonomous workflow execution engine.
    
    Coordinates workflow execution, manages state, and integrates
    with the existing scheduler and research pipeline.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize workflow engine.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.active_workflows: Dict[str, WorkflowState] = {}
        self.workflow_history: List[WorkflowState] = []
        
    def create_workflow(
        self,
        name: str,
        workflow_type: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new workflow.
        
        Args:
            name: Workflow name
            workflow_type: Type of workflow (e.g., 'signal_analysis', 'risk_check')
            parameters: Workflow parameters
            
        Returns:
            Workflow ID
        """
        workflow_id = str(uuid.uuid4())
        
        state = WorkflowState(
            workflow_id=workflow_id,
            name=name,
            status=WorkflowStatus.PENDING,
            metadata={
                "type": workflow_type,
                "parameters": parameters or {},
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        
        self.active_workflows[workflow_id] = state
        return workflow_id
    
    def execute_workflow(
        self,
        workflow_id: str,
        dry_run: bool = False,
    ) -> WorkflowResult:
        """
        Execute a workflow.
        
        Args:
            workflow_id: Workflow identifier
            dry_run: If True, simulate execution
            
        Returns:
            WorkflowResult with execution outcome
        """
        if workflow_id not in self.active_workflows:
            return WorkflowResult(
                workflow_id=workflow_id,
                success=False,
                status=WorkflowStatus.FAILED,
                error="Workflow not found"
            )
        
        state = self.active_workflows[workflow_id]
        state.status = WorkflowStatus.RUNNING
        state.started_at = datetime.utcnow()
        
        try:
            # Get workflow type and parameters
            workflow_type = state.metadata.get("type", "")
            parameters = state.metadata.get("parameters", {})
            
            # Execute workflow based on type
            if dry_run:
                output = self._simulate_workflow(workflow_type, parameters)
            else:
                output = self._execute_workflow_internal(workflow_type, parameters)
            
            # Mark as completed
            state.status = WorkflowStatus.COMPLETED
            state.finished_at = datetime.utcnow()
            
            result = WorkflowResult(
                workflow_id=workflow_id,
                success=True,
                status=WorkflowStatus.COMPLETED,
                output=output,
                metadata={
                    "duration_seconds": state.duration_seconds,
                    "finished_at": state.finished_at.isoformat() if state.finished_at else None,
                }
            )
            
        except Exception as e:
            # Mark as failed
            state.status = WorkflowStatus.FAILED
            state.finished_at = datetime.utcnow()
            
            result = WorkflowResult(
                workflow_id=workflow_id,
                success=False,
                status=WorkflowStatus.FAILED,
                error=str(e),
                metadata={
                    "duration_seconds": state.duration_seconds,
                    "finished_at": state.finished_at.isoformat() if state.finished_at else None,
                }
            )
        
        # Move to history
        self.workflow_history.append(state)
        del self.active_workflows[workflow_id]
        
        return result
    
    def _simulate_workflow(
        self,
        workflow_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simulate workflow execution (dry-run).
        
        Args:
            workflow_type: Type of workflow
            parameters: Workflow parameters
            
        Returns:
            Simulated output
        """
        return {
            "simulated": True,
            "workflow_type": workflow_type,
            "parameters": parameters,
            "message": f"Would execute {workflow_type} with {len(parameters)} parameters"
        }
    
    def _execute_workflow_internal(
        self,
        workflow_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute workflow internally.
        
        Args:
            workflow_type: Type of workflow
            parameters: Workflow parameters
            
        Returns:
            Workflow output
        """
        # Map workflow types to script execution
        workflow_scripts = {
            "signal_analysis": "scripts/run_forward_signals.py",
            "risk_check": "scripts/check_live_risk_limits.py",
            "market_scan": "scripts/run_market_scan.py",
            "portfolio_analysis": "scripts/research_cli.py",
        }
        
        script = workflow_scripts.get(workflow_type)
        if not script:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        
        # Build command
        cmd = [sys.executable, script]
        for key, value in parameters.items():
            if isinstance(value, bool):
                if value:
                    cmd.append(f"--{key.replace('_', '-')}")
            elif value is not None:
                cmd.append(f"--{key.replace('_', '-')}")
                cmd.append(str(value))
        
        # Execute
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes default
        )
        
        return {
            "return_code": result.returncode,
            "stdout": result.stdout[:500],  # Truncate for storage
            "stderr": result.stderr[:500],
            "success": result.returncode == 0,
        }
    
    def get_workflow_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """
        Get current workflow state.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            WorkflowState or None if not found
        """
        return self.active_workflows.get(workflow_id)
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """
        Cancel a running workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            True if cancelled successfully
        """
        if workflow_id not in self.active_workflows:
            return False
        
        state = self.active_workflows[workflow_id]
        state.status = WorkflowStatus.CANCELLED
        state.finished_at = datetime.utcnow()
        
        # Move to history
        self.workflow_history.append(state)
        del self.active_workflows[workflow_id]
        
        return True
    
    def get_active_workflows(self) -> List[WorkflowState]:
        """Get list of active workflows."""
        return list(self.active_workflows.values())
    
    def get_workflow_history(
        self,
        limit: Optional[int] = None
    ) -> List[WorkflowState]:
        """
        Get workflow history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of historical workflow states
        """
        if limit:
            return self.workflow_history[-limit:]
        return self.workflow_history.copy()
