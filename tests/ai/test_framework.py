"""
Tests for AI Agent Framework.
"""

import pytest
from src.ai.framework import PeakTradeAgent
from src.ai.registry import AgentRegistry
from src.ai.event_bus import EventBus, Event, EventType
from src.ai.memory import AgentMemory, VectorMemory
from src.ai.coordinator import AgentCoordinator, Workflow, WorkflowStep


class MockAgent(PeakTradeAgent):
    """Mock agent for testing."""
    
    def __init__(self, config=None):
        super().__init__(
            agent_id="mock_agent",
            name="Mock Agent",
            description="Test agent",
            config=config,
        )
    
    def execute(self, task):
        """Execute mock task."""
        action = task.get("action")
        return {
            "success": True,
            "action": action,
            "result": "mock_result",
        }


class TestPeakTradeAgent:
    """Tests for PeakTradeAgent base class."""
    
    def test_agent_initialization(self):
        """Test agent can be initialized."""
        agent = MockAgent()
        assert agent.agent_id == "mock_agent"
        assert agent.name == "Mock Agent"
        assert agent.enabled is True
    
    def test_agent_with_config(self):
        """Test agent accepts configuration."""
        config = {"enabled": False, "test_param": 123}
        agent = MockAgent(config=config)
        assert agent.enabled is False
        assert agent.config["test_param"] == 123
    
    def test_agent_execute(self):
        """Test agent can execute tasks."""
        agent = MockAgent()
        result = agent.execute({"action": "test_action"})
        assert result["success"] is True
        assert result["action"] == "test_action"
    
    def test_agent_log_decision(self):
        """Test decision logging."""
        agent = MockAgent()
        agent.log_decision(
            action="test_action",
            reasoning="test reasoning",
            outcome={"result": "success"},
        )
        
        history = agent.get_decision_history()
        assert len(history) == 1
        assert history[0]["action"] == "test_action"
        assert history[0]["reasoning"] == "test reasoning"
    
    def test_agent_add_tool(self):
        """Test adding tools to agent."""
        agent = MockAgent()
        
        class MockTool:
            name = "mock_tool"
        
        tool = MockTool()
        agent.add_tool(tool)
        assert len(agent.tools) == 1
        assert agent.tools[0].name == "mock_tool"
    
    def test_agent_get_status(self):
        """Test getting agent status."""
        agent = MockAgent()
        status = agent.get_status()
        
        assert status["agent_id"] == "mock_agent"
        assert status["name"] == "Mock Agent"
        assert status["enabled"] is True
        assert status["tools_count"] == 0
        assert status["decisions_count"] == 0


class TestAgentRegistry:
    """Tests for AgentRegistry."""
    
    def test_registry_initialization(self):
        """Test registry can be initialized."""
        registry = AgentRegistry()
        assert registry.list_agents() == []
    
    def test_register_agent(self):
        """Test registering an agent."""
        registry = AgentRegistry()
        registry.register("mock_agent", MockAgent)
        
        assert "mock_agent" in registry.list_agents()
    
    def test_register_duplicate_agent(self):
        """Test registering duplicate agent raises error."""
        registry = AgentRegistry()
        registry.register("mock_agent", MockAgent)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register("mock_agent", MockAgent)
    
    def test_get_agent(self):
        """Test getting an agent instance."""
        registry = AgentRegistry()
        registry.register("mock_agent", MockAgent)
        
        agent = registry.get_agent("mock_agent")
        assert isinstance(agent, MockAgent)
        assert agent.agent_id == "mock_agent"
    
    def test_get_agent_not_found(self):
        """Test getting non-existent agent raises error."""
        registry = AgentRegistry()
        
        with pytest.raises(KeyError, match="not registered"):
            registry.get_agent("nonexistent")
    
    def test_get_agent_singleton(self):
        """Test getting same agent instance."""
        registry = AgentRegistry()
        registry.register("mock_agent", MockAgent)
        
        agent1 = registry.get_agent("mock_agent")
        agent2 = registry.get_agent("mock_agent")
        
        assert agent1 is agent2
    
    def test_get_agent_create_new(self):
        """Test creating new agent instance."""
        registry = AgentRegistry()
        registry.register("mock_agent", MockAgent)
        
        agent1 = registry.get_agent("mock_agent")
        agent2 = registry.get_agent("mock_agent", create_new=True)
        
        assert agent1 is not agent2
    
    def test_unregister_agent(self):
        """Test unregistering an agent."""
        registry = AgentRegistry()
        registry.register("mock_agent", MockAgent)
        
        registry.unregister("mock_agent")
        assert "mock_agent" not in registry.list_agents()
    
    def test_clear_registry(self):
        """Test clearing all agents."""
        registry = AgentRegistry()
        registry.register("agent1", MockAgent)
        registry.register("agent2", MockAgent)
        
        registry.clear()
        assert len(registry.list_agents()) == 0
    
    def test_get_agent_info(self):
        """Test getting agent info."""
        registry = AgentRegistry()
        registry.register("mock_agent", MockAgent)
        
        info = registry.get_agent_info("mock_agent")
        assert info["agent_id"] == "mock_agent"
        assert info["class_name"] == "MockAgent"
        assert "module" in info


class TestEventBus:
    """Tests for EventBus."""
    
    def test_event_bus_initialization(self):
        """Test event bus can be initialized."""
        bus = EventBus()
        assert bus._subscribers == {}
        assert bus._event_history == []
    
    def test_publish_event(self):
        """Test publishing an event."""
        bus = EventBus()
        event = Event.create(
            event_type=EventType.STRATEGY_DISCOVERED.value,
            source="test",
            data={"strategy": "test_strategy"},
        )
        
        bus.publish(event)
        
        history = bus.get_event_history()
        assert len(history) == 1
        assert history[0].event_type == EventType.STRATEGY_DISCOVERED.value
    
    def test_subscribe_to_event(self):
        """Test subscribing to events."""
        bus = EventBus()
        received_events = []
        
        def handler(event):
            received_events.append(event)
        
        bus.subscribe(EventType.RISK_ALERT.value, handler)
        
        event = Event.create(
            event_type=EventType.RISK_ALERT.value,
            source="test",
            data={"risk": "high"},
        )
        bus.publish(event)
        
        assert len(received_events) == 1
        assert received_events[0].event_type == EventType.RISK_ALERT.value
    
    def test_multiple_subscribers(self):
        """Test multiple subscribers to same event."""
        bus = EventBus()
        count = [0]
        
        def handler1(event):
            count[0] += 1
        
        def handler2(event):
            count[0] += 10
        
        bus.subscribe(EventType.SYSTEM_ERROR.value, handler1)
        bus.subscribe(EventType.SYSTEM_ERROR.value, handler2)
        
        event = Event.create(
            event_type=EventType.SYSTEM_ERROR.value,
            source="test",
            data={},
        )
        bus.publish(event)
        
        assert count[0] == 11
    
    def test_unsubscribe_from_event(self):
        """Test unsubscribing from events."""
        bus = EventBus()
        received_events = []
        
        def handler(event):
            received_events.append(event)
        
        bus.subscribe(EventType.EXECUTION_COMPLETED.value, handler)
        bus.unsubscribe(EventType.EXECUTION_COMPLETED.value, handler)
        
        event = Event.create(
            event_type=EventType.EXECUTION_COMPLETED.value,
            source="test",
            data={},
        )
        bus.publish(event)
        
        assert len(received_events) == 0
    
    def test_event_decorator(self):
        """Test decorator for subscribing to events."""
        bus = EventBus()
        received_events = []
        
        @bus.on(EventType.MARKET_ANOMALY.value)
        def handle_anomaly(event):
            received_events.append(event)
        
        event = Event.create(
            event_type=EventType.MARKET_ANOMALY.value,
            source="test",
            data={"anomaly": "spike"},
        )
        bus.publish(event)
        
        assert len(received_events) == 1
    
    def test_clear_history(self):
        """Test clearing event history."""
        bus = EventBus()
        
        for i in range(5):
            event = Event.create(
                event_type=EventType.CUSTOM.value,
                source="test",
                data={"index": i},
            )
            bus.publish(event)
        
        bus.clear_history()
        assert len(bus.get_event_history()) == 0


class TestAgentMemory:
    """Tests for AgentMemory."""
    
    def test_memory_initialization(self):
        """Test memory can be initialized."""
        memory = AgentMemory()
        assert memory._storage == {}
    
    def test_store_and_retrieve(self):
        """Test storing and retrieving values."""
        memory = AgentMemory()
        memory.store("key1", "value1")
        
        value = memory.retrieve("key1")
        assert value == "value1"
    
    def test_retrieve_default(self):
        """Test retrieving with default value."""
        memory = AgentMemory()
        value = memory.retrieve("nonexistent", default="default_value")
        assert value == "default_value"
    
    def test_delete(self):
        """Test deleting a key."""
        memory = AgentMemory()
        memory.store("key1", "value1")
        
        deleted = memory.delete("key1")
        assert deleted is True
        
        value = memory.retrieve("key1")
        assert value is None
    
    def test_delete_nonexistent(self):
        """Test deleting non-existent key."""
        memory = AgentMemory()
        deleted = memory.delete("nonexistent")
        assert deleted is False
    
    def test_search(self):
        """Test searching for keys."""
        memory = AgentMemory()
        memory.store("strategy_1", "data1")
        memory.store("strategy_2", "data2")
        memory.store("portfolio_1", "data3")
        
        results = memory.search("strategy")
        assert len(results) == 2
        assert "strategy_1" in results
        assert "strategy_2" in results
    
    def test_get_history(self):
        """Test getting access history."""
        memory = AgentMemory()
        memory.store("key1", "value1")
        memory.retrieve("key1")
        
        history = memory.get_history()
        assert len(history) >= 2
        assert history[0]["action"] == "store"
        assert history[1]["action"] == "retrieve"
    
    def test_clear_memory(self):
        """Test clearing all memory."""
        memory = AgentMemory()
        memory.store("key1", "value1")
        memory.store("key2", "value2")
        
        memory.clear()
        
        assert memory.retrieve("key1") is None
        assert memory.retrieve("key2") is None


class TestVectorMemory:
    """Tests for VectorMemory."""
    
    def test_vector_memory_initialization(self):
        """Test vector memory can be initialized."""
        memory = VectorMemory("test_collection")
        assert memory.collection_name == "test_collection"
    
    def test_add_document(self):
        """Test adding a document."""
        memory = VectorMemory()
        memory.add_document("test document", {"source": "test"})
        
        assert len(memory._documents) == 1
    
    def test_search_similar(self):
        """Test searching for similar documents."""
        memory = VectorMemory()
        memory.add_document("BTC trading strategy", {"type": "strategy"})
        memory.add_document("ETH trading strategy", {"type": "strategy"})
        memory.add_document("Risk management", {"type": "risk"})
        
        results = memory.search_similar("strategy", k=2)
        assert len(results) == 2
    
    def test_clear_vector_memory(self):
        """Test clearing vector memory."""
        memory = VectorMemory()
        memory.add_document("test", {})
        
        memory.clear()
        assert len(memory._documents) == 0


class TestAgentCoordinator:
    """Tests for AgentCoordinator."""
    
    def test_coordinator_initialization(self):
        """Test coordinator can be initialized."""
        coordinator = AgentCoordinator()
        assert isinstance(coordinator.registry, AgentRegistry)
    
    def test_register_agent_with_coordinator(self):
        """Test registering agent with coordinator."""
        coordinator = AgentCoordinator()
        coordinator.register_agent("mock_agent", MockAgent)
        
        assert "mock_agent" in coordinator.list_agents()
    
    def test_execute_simple_workflow(self):
        """Test executing a simple workflow."""
        coordinator = AgentCoordinator()
        coordinator.register_agent("mock_agent", MockAgent)
        
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
        
        result = coordinator.execute_workflow(workflow)
        
        assert result.success is True
        assert "result" in result.outputs
        assert result.outputs["result"]["success"] is True
    
    def test_execute_multi_step_workflow(self):
        """Test executing multi-step workflow."""
        coordinator = AgentCoordinator()
        coordinator.register_agent("mock_agent", MockAgent)
        
        workflow = Workflow(
            name="multi_step_workflow",
            description="Multi-step test workflow",
            steps=[
                WorkflowStep(
                    agent="mock_agent",
                    action="action1",
                    output_to="step1_result",
                ),
                WorkflowStep(
                    agent="mock_agent",
                    action="action2",
                    input_from="step1_result",
                    output_to="step2_result",
                ),
            ],
            agents=["mock_agent"],
        )
        
        result = coordinator.execute_workflow(workflow)
        
        assert result.success is True
        assert "step1_result" in result.outputs
        assert "step2_result" in result.outputs
    
    def test_workflow_with_missing_agent(self):
        """Test workflow execution with missing agent."""
        coordinator = AgentCoordinator()
        
        workflow = Workflow(
            name="failing_workflow",
            description="Workflow with missing agent",
            steps=[
                WorkflowStep(
                    agent="nonexistent_agent",
                    action="test_action",
                    output_to="result",
                ),
            ],
            agents=["nonexistent_agent"],
        )
        
        result = coordinator.execute_workflow(workflow)
        
        assert result.success is False
        assert len(result.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
