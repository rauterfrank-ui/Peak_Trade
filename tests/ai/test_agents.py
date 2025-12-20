"""
Tests for AI agents.
"""

import pytest
from src.ai.agents.research_agent import StrategyResearchAgent, StrategyReport
from src.ai.agents.risk_agent import RiskReviewAgent, RiskReport
from src.ai.agents.execution_agent import StrategyExecutionAgent, ExecutionReport
from src.ai.agents.monitoring_agent import MonitoringAgent, MonitoringReport


class TestStrategyResearchAgent:
    """Tests for StrategyResearchAgent."""
    
    def test_research_agent_initialization(self):
        """Test research agent can be initialized."""
        agent = StrategyResearchAgent()
        assert agent.agent_id == "research_agent"
        assert agent.name == "Strategy Research Agent"
        assert agent.enabled is True
    
    def test_research_agent_with_config(self):
        """Test research agent with custom config."""
        config = {
            "min_confidence": 0.9,
            "auto_backtest": False,
        }
        agent = StrategyResearchAgent(config=config)
        assert agent.min_confidence == 0.9
        assert agent.auto_backtest is False
    
    def test_research_strategy(self):
        """Test researching a strategy."""
        agent = StrategyResearchAgent()
        report = agent.research_strategy(
            objective="Find mean-reversion strategy",
            symbols=["BTC/EUR"],
            timeframe="1h",
        )
        
        assert isinstance(report, StrategyReport)
        assert report.objective == "Find mean-reversion strategy"
        assert report.symbols == ["BTC/EUR"]
        assert report.timeframe == "1h"
    
    def test_execute_research_task(self):
        """Test executing research task."""
        agent = StrategyResearchAgent()
        result = agent.execute({
            "action": "research_strategy",
            "objective": "Find strategy",
            "symbols": ["ETH/EUR"],
            "timeframe": "1d",
        })
        
        assert result["success"] is True
        assert "report" in result
    
    def test_research_logs_decisions(self):
        """Test that research logs decisions."""
        agent = StrategyResearchAgent()
        agent.research_strategy(
            objective="Test objective",
            symbols=["BTC/EUR"],
            timeframe="1h",
        )
        
        history = agent.get_decision_history()
        assert len(history) == 1
        assert history[0]["action"] == "research_strategy"


class TestRiskReviewAgent:
    """Tests for RiskReviewAgent."""
    
    def test_risk_agent_initialization(self):
        """Test risk agent can be initialized."""
        agent = RiskReviewAgent()
        assert agent.agent_id == "risk_agent"
        assert agent.name == "Risk Review Agent"
        assert agent.enabled is True
    
    def test_risk_agent_with_config(self):
        """Test risk agent with custom config."""
        config = {
            "auto_enforcement": True,
            "alert_threshold": 0.9,
        }
        agent = RiskReviewAgent(config=config)
        assert agent.auto_enforcement is True
        assert agent.alert_threshold == 0.9
    
    def test_review_portfolio_risk(self):
        """Test reviewing portfolio risk."""
        agent = RiskReviewAgent()
        report = agent.review_portfolio_risk(portfolio_id="test_portfolio")
        
        assert isinstance(report, RiskReport)
        assert report.portfolio_id == "test_portfolio"
        assert report.severity in ["low", "medium", "high", "critical"]
    
    def test_validate_risk(self):
        """Test validating strategy risk."""
        agent = RiskReviewAgent()
        result = agent.validate_risk(
            strategy_data={"name": "test_strategy"},
        )
        
        assert "valid" in result
        assert "risk_score" in result
    
    def test_execute_review_task(self):
        """Test executing review task."""
        agent = RiskReviewAgent()
        result = agent.execute({
            "action": "review_portfolio_risk",
            "portfolio_id": "test_portfolio",
        })
        
        assert result["success"] is True
        assert "report" in result
    
    def test_execute_validate_task(self):
        """Test executing validate task."""
        agent = RiskReviewAgent()
        result = agent.execute({
            "action": "validate_risk",
            "strategy": {"name": "test_strategy"},
        })
        
        assert result["success"] is True
        assert "validation" in result
    
    def test_risk_logs_decisions(self):
        """Test that risk agent logs decisions."""
        agent = RiskReviewAgent()
        agent.review_portfolio_risk(portfolio_id="test_portfolio")
        
        history = agent.get_decision_history()
        assert len(history) == 1
        assert history[0]["action"] == "review_portfolio_risk"


class TestStrategyExecutionAgent:
    """Tests for StrategyExecutionAgent."""
    
    def test_execution_agent_initialization(self):
        """Test execution agent can be initialized."""
        agent = StrategyExecutionAgent()
        assert agent.agent_id == "execution_agent"
        assert agent.name == "Strategy Execution Agent"
        assert agent.enabled is True
    
    def test_execution_agent_with_config(self):
        """Test execution agent with custom config."""
        config = {
            "mode": "live",
            "require_approval": False,
        }
        agent = StrategyExecutionAgent(config=config)
        assert agent.default_mode == "live"
        assert agent.require_approval is False
    
    def test_execute_strategy_paper(self):
        """Test executing strategy in paper mode."""
        agent = StrategyExecutionAgent()
        report = agent.execute_strategy(
            strategy_id="test_strategy",
            mode="paper",
        )
        
        assert isinstance(report, ExecutionReport)
        assert report.strategy_id == "test_strategy"
        assert report.mode == "paper"
    
    def test_execute_strategy_live_requires_approval(self):
        """Test live trading requires approval."""
        agent = StrategyExecutionAgent(config={"require_approval": True})
        
        with pytest.raises(ValueError, match="requires approval"):
            agent.execute_strategy(
                strategy_id="test_strategy",
                mode="live",
            )
    
    def test_execute_strategy_live_without_approval_gate(self):
        """Test live trading without approval gate."""
        agent = StrategyExecutionAgent(config={"require_approval": False})
        report = agent.execute_strategy(
            strategy_id="test_strategy",
            mode="live",
        )
        
        assert report.mode == "live"
    
    def test_run_backtest(self):
        """Test running backtest."""
        agent = StrategyExecutionAgent()
        result = agent.run_backtest(
            strategy_id="test_strategy",
            start_date="2023-01-01",
            end_date="2023-12-31",
        )
        
        assert result["strategy_id"] == "test_strategy"
        assert "total_return" in result
        assert "sharpe_ratio" in result
    
    def test_execute_execution_task(self):
        """Test executing execution task."""
        agent = StrategyExecutionAgent()
        result = agent.execute({
            "action": "execute_strategy",
            "strategy_id": "test_strategy",
            "mode": "paper",
        })
        
        assert result["success"] is True
        assert "report" in result
    
    def test_execute_backtest_task(self):
        """Test executing backtest task."""
        agent = StrategyExecutionAgent()
        result = agent.execute({
            "action": "backtest",
            "strategy_id": "test_strategy",
        })
        
        assert result["success"] is True
        assert "backtest_result" in result
    
    def test_execution_logs_decisions(self):
        """Test that execution agent logs decisions."""
        agent = StrategyExecutionAgent()
        agent.execute_strategy(
            strategy_id="test_strategy",
            mode="paper",
        )
        
        history = agent.get_decision_history()
        assert len(history) == 1
        assert history[0]["action"] == "execute_strategy"


class TestMonitoringAgent:
    """Tests for MonitoringAgent."""
    
    def test_monitoring_agent_initialization(self):
        """Test monitoring agent can be initialized."""
        agent = MonitoringAgent()
        assert agent.agent_id == "monitoring_agent"
        assert agent.name == "Monitoring Agent"
        assert agent.enabled is True
    
    def test_monitoring_agent_with_config(self):
        """Test monitoring agent with custom config."""
        config = {
            "check_interval": 30,
            "anomaly_threshold": 0.9,
        }
        agent = MonitoringAgent(config=config)
        assert agent.check_interval == 30
        assert agent.anomaly_threshold == 0.9
    
    def test_monitor_system(self):
        """Test monitoring system."""
        agent = MonitoringAgent()
        report = agent.monitor_system()
        
        assert isinstance(report, MonitoringReport)
        assert report.system_status in ["healthy", "degraded", "unhealthy", "unknown"]
        assert report.health_checks is not None
    
    def test_check_health(self):
        """Test checking health."""
        agent = MonitoringAgent()
        health = agent.check_health()
        
        assert isinstance(health, dict)
        assert len(health) > 0
    
    def test_check_health_specific_components(self):
        """Test checking specific components."""
        agent = MonitoringAgent()
        health = agent.check_health(components=["api", "database"])
        
        assert "api" in health
        assert "database" in health
    
    def test_detect_anomalies(self):
        """Test detecting anomalies."""
        agent = MonitoringAgent()
        anomalies = agent.detect_anomalies()
        
        assert isinstance(anomalies, list)
    
    def test_execute_monitor_task(self):
        """Test executing monitor task."""
        agent = MonitoringAgent()
        result = agent.execute({
            "action": "monitor_system",
        })
        
        assert result["success"] is True
        assert "report" in result
    
    def test_execute_health_check_task(self):
        """Test executing health check task."""
        agent = MonitoringAgent()
        result = agent.execute({
            "action": "check_health",
            "components": ["api"],
        })
        
        assert result["success"] is True
        assert "health_status" in result
    
    def test_execute_anomaly_detection_task(self):
        """Test executing anomaly detection task."""
        agent = MonitoringAgent()
        result = agent.execute({
            "action": "detect_anomalies",
            "metrics": {},
        })
        
        assert result["success"] is True
        assert "anomalies" in result
    
    def test_monitoring_logs_decisions(self):
        """Test that monitoring agent logs decisions."""
        agent = MonitoringAgent()
        agent.monitor_system()
        
        history = agent.get_decision_history()
        assert len(history) == 1
        assert history[0]["action"] == "monitor_system"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
