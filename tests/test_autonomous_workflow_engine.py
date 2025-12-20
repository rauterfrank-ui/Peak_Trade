"""
Tests for Autonomous Workflow Engine
=====================================
"""
import pytest
from datetime import datetime

from src.autonomous.workflow_engine import (
    WorkflowEngine,
    WorkflowState,
    WorkflowStatus,
    WorkflowResult,
)


class TestWorkflowState:
    """Tests for WorkflowState dataclass."""
    
    def test_workflow_state_creation(self):
        """Test creating a workflow state."""
        state = WorkflowState(
            workflow_id="test-123",
            name="test_workflow",
            status=WorkflowStatus.PENDING,
        )
        
        assert state.workflow_id == "test-123"
        assert state.name == "test_workflow"
        assert state.status == WorkflowStatus.PENDING
        assert state.started_at is None
        assert state.finished_at is None
    
    def test_duration_calculation(self):
        """Test duration calculation."""
        state = WorkflowState(
            workflow_id="test-123",
            name="test_workflow",
        )
        
        # No duration initially
        assert state.duration_seconds is None
        
        # With timestamps
        state.started_at = datetime(2025, 1, 1, 12, 0, 0)
        state.finished_at = datetime(2025, 1, 1, 12, 0, 30)
        
        assert state.duration_seconds == 30.0


class TestWorkflowEngine:
    """Tests for WorkflowEngine."""
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = WorkflowEngine()
        
        assert engine.active_workflows == {}
        assert engine.workflow_history == []
    
    def test_create_workflow(self):
        """Test creating a workflow."""
        engine = WorkflowEngine()
        
        workflow_id = engine.create_workflow(
            name="test_workflow",
            workflow_type="signal_analysis",
            parameters={"symbol": "BTC/EUR"}
        )
        
        assert workflow_id is not None
        assert workflow_id in engine.active_workflows
        
        state = engine.active_workflows[workflow_id]
        assert state.name == "test_workflow"
        assert state.status == WorkflowStatus.PENDING
        assert state.metadata["type"] == "signal_analysis"
    
    def test_execute_workflow_dry_run(self):
        """Test workflow execution in dry-run mode."""
        engine = WorkflowEngine()
        
        workflow_id = engine.create_workflow(
            name="test_workflow",
            workflow_type="signal_analysis",
            parameters={"symbol": "BTC/EUR"}
        )
        
        result = engine.execute_workflow(workflow_id, dry_run=True)
        
        assert result.success is True
        assert result.status == WorkflowStatus.COMPLETED
        assert result.output["simulated"] is True
        assert workflow_id not in engine.active_workflows  # Moved to history
        assert len(engine.workflow_history) == 1
    
    def test_execute_nonexistent_workflow(self):
        """Test executing a non-existent workflow."""
        engine = WorkflowEngine()
        
        result = engine.execute_workflow("nonexistent-id")
        
        assert result.success is False
        assert result.status == WorkflowStatus.FAILED
        assert "not found" in result.error.lower()
    
    def test_get_workflow_state(self):
        """Test getting workflow state."""
        engine = WorkflowEngine()
        
        workflow_id = engine.create_workflow(
            name="test_workflow",
            workflow_type="signal_analysis"
        )
        
        state = engine.get_workflow_state(workflow_id)
        
        assert state is not None
        assert state.workflow_id == workflow_id
        assert state.name == "test_workflow"
    
    def test_cancel_workflow(self):
        """Test cancelling a workflow."""
        engine = WorkflowEngine()
        
        workflow_id = engine.create_workflow(
            name="test_workflow",
            workflow_type="signal_analysis"
        )
        
        success = engine.cancel_workflow(workflow_id)
        
        assert success is True
        assert workflow_id not in engine.active_workflows
        assert len(engine.workflow_history) == 1
        
        state = engine.workflow_history[0]
        assert state.status == WorkflowStatus.CANCELLED
    
    def test_get_active_workflows(self):
        """Test getting active workflows."""
        engine = WorkflowEngine()
        
        # Create multiple workflows
        wf1 = engine.create_workflow("workflow1", "signal_analysis")
        wf2 = engine.create_workflow("workflow2", "risk_check")
        
        active = engine.get_active_workflows()
        
        assert len(active) == 2
        assert any(w.workflow_id == wf1 for w in active)
        assert any(w.workflow_id == wf2 for w in active)
    
    def test_get_workflow_history(self):
        """Test getting workflow history."""
        engine = WorkflowEngine()
        
        # Create and execute workflows
        for i in range(3):
            wf_id = engine.create_workflow(f"workflow{i}", "signal_analysis")
            engine.execute_workflow(wf_id, dry_run=True)
        
        history = engine.get_workflow_history()
        assert len(history) == 3
        
        # Test with limit
        limited = engine.get_workflow_history(limit=2)
        assert len(limited) == 2
    
    def test_workflow_metadata(self):
        """Test workflow metadata handling."""
        engine = WorkflowEngine()
        
        workflow_id = engine.create_workflow(
            name="test_workflow",
            workflow_type="signal_analysis",
            parameters={
                "symbol": "BTC/EUR",
                "strategy": "ma_crossover",
                "timeframe": "1h"
            }
        )
        
        state = engine.get_workflow_state(workflow_id)
        
        assert state.metadata["type"] == "signal_analysis"
        assert state.metadata["parameters"]["symbol"] == "BTC/EUR"
        assert state.metadata["parameters"]["strategy"] == "ma_crossover"
        assert "created_at" in state.metadata


class TestWorkflowResult:
    """Tests for WorkflowResult dataclass."""
    
    def test_workflow_result_creation(self):
        """Test creating a workflow result."""
        result = WorkflowResult(
            workflow_id="test-123",
            success=True,
            status=WorkflowStatus.COMPLETED,
            output={"key": "value"},
        )
        
        assert result.workflow_id == "test-123"
        assert result.success is True
        assert result.status == WorkflowStatus.COMPLETED
        assert result.output["key"] == "value"
        assert result.error is None
    
    def test_workflow_result_with_error(self):
        """Test workflow result with error."""
        result = WorkflowResult(
            workflow_id="test-123",
            success=False,
            status=WorkflowStatus.FAILED,
            error="Test error message"
        )
        
        assert result.success is False
        assert result.error == "Test error message"


class TestWorkflowEngineIntegration:
    """Integration tests for WorkflowEngine."""
    
    def test_full_workflow_lifecycle(self):
        """Test complete workflow lifecycle."""
        engine = WorkflowEngine()
        
        # Create
        workflow_id = engine.create_workflow(
            name="integration_test",
            workflow_type="signal_analysis",
            parameters={"symbol": "BTC/EUR"}
        )
        
        assert workflow_id in engine.active_workflows
        state = engine.get_workflow_state(workflow_id)
        assert state.status == WorkflowStatus.PENDING
        
        # Execute
        result = engine.execute_workflow(workflow_id, dry_run=True)
        
        assert result.success is True
        assert workflow_id not in engine.active_workflows
        assert len(engine.workflow_history) == 1
        
        # Check history
        history_state = engine.workflow_history[0]
        assert history_state.status == WorkflowStatus.COMPLETED
        assert history_state.started_at is not None
        assert history_state.finished_at is not None
        assert history_state.duration_seconds is not None
    
    def test_multiple_workflows_execution(self):
        """Test executing multiple workflows."""
        engine = WorkflowEngine()
        
        results = []
        for i in range(3):
            wf_id = engine.create_workflow(
                name=f"workflow_{i}",
                workflow_type="signal_analysis"
            )
            result = engine.execute_workflow(wf_id, dry_run=True)
            results.append(result)
        
        # All should succeed
        assert all(r.success for r in results)
        
        # All should be in history
        assert len(engine.workflow_history) == 3
        
        # No active workflows
        assert len(engine.active_workflows) == 0
