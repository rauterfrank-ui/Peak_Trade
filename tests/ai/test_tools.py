"""
Tests for AI agent tools.
"""

import pytest
from src.ai.tools.base import AgentTool
from src.ai.tools.data_loader_tool import DataLoaderTool
from src.ai.tools.backtest_tool import BacktestTool
from src.ai.tools.analysis_tool import AnalysisTool
from src.ai.tools.risk_tool import RiskCalculatorTool


class MockTool(AgentTool):
    """Mock tool for testing."""
    
    @property
    def name(self) -> str:
        return "mock_tool"
    
    @property
    def description(self) -> str:
        return "A mock tool for testing"
    
    def run(self, **kwargs):
        """Run the mock tool."""
        return {"success": True, "kwargs": kwargs}


class TestAgentTool:
    """Tests for AgentTool base class."""
    
    def test_tool_initialization(self):
        """Test tool can be initialized."""
        tool = MockTool()
        assert tool.name == "mock_tool"
        assert tool.description == "A mock tool for testing"
    
    def test_tool_with_config(self):
        """Test tool accepts configuration."""
        config = {"test_param": 123}
        tool = MockTool(config=config)
        assert tool.config["test_param"] == 123
    
    def test_tool_run(self):
        """Test tool can be run."""
        tool = MockTool()
        result = tool.run(param1="value1", param2="value2")
        
        assert result["success"] is True
        assert result["kwargs"]["param1"] == "value1"
        assert result["kwargs"]["param2"] == "value2"
    
    def test_tool_run_wrapper(self):
        """Test tool run wrapper."""
        tool = MockTool()
        result = tool._run_wrapper(test_param="test")
        
        assert tool.call_count == 1
        assert result["kwargs"]["test_param"] == "test"
    
    def test_tool_get_schema(self):
        """Test getting tool schema."""
        tool = MockTool()
        schema = tool.get_schema()
        
        assert schema["name"] == "mock_tool"
        assert schema["description"] == "A mock tool for testing"


class TestDataLoaderTool:
    """Tests for DataLoaderTool."""
    
    def test_data_loader_initialization(self):
        """Test data loader can be initialized."""
        tool = DataLoaderTool()
        assert tool.name == "data_loader"
    
    def test_load_data(self):
        """Test loading data."""
        tool = DataLoaderTool()
        result = tool.run(
            symbol="BTC/EUR",
            timeframe="1h",
            limit=100,
        )
        
        # Should return DataFrame or dict
        assert result is not None
    
    def test_load_data_different_timeframes(self):
        """Test loading data with different timeframes."""
        tool = DataLoaderTool()
        
        for timeframe in ["1h", "4h", "1d"]:
            result = tool.run(
                symbol="ETH/EUR",
                timeframe=timeframe,
                limit=50,
            )
            assert result is not None


class TestBacktestTool:
    """Tests for BacktestTool."""
    
    def test_backtest_tool_initialization(self):
        """Test backtest tool can be initialized."""
        tool = BacktestTool()
        assert tool.name == "backtest"
    
    def test_run_backtest(self):
        """Test running backtest."""
        tool = BacktestTool()
        result = tool.run(
            strategy_code="ma_crossover",
            symbols=["BTC/EUR"],
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_cash=10000.0,
        )
        
        assert result["strategy"] == "ma_crossover"
        assert "total_return" in result
        assert "sharpe_ratio" in result
        assert "max_drawdown" in result
    
    def test_backtest_multiple_symbols(self):
        """Test backtest with multiple symbols."""
        tool = BacktestTool()
        result = tool.run(
            strategy_code="test_strategy",
            symbols=["BTC/EUR", "ETH/EUR"],
        )
        
        assert len(result["symbols"]) == 2


class TestAnalysisTool:
    """Tests for AnalysisTool."""
    
    def test_analysis_tool_initialization(self):
        """Test analysis tool can be initialized."""
        tool = AnalysisTool()
        assert tool.name == "analysis"
    
    def test_summary_analysis(self):
        """Test summary analysis."""
        pytest.importorskip("pandas")
        import pandas as pd
        import numpy as np
        
        # Create test data
        df = pd.DataFrame({
            "close": np.random.randn(100).cumsum() + 100,
            "volume": np.random.randint(100, 1000, 100),
        })
        
        tool = AnalysisTool()
        result = tool.run(data=df, analysis_type="summary")
        
        assert result["analysis_type"] == "summary"
        assert "mean_price" in result
        assert "std_price" in result
        assert "total_return" in result
    
    def test_volatility_analysis(self):
        """Test volatility analysis."""
        pytest.importorskip("pandas")
        import pandas as pd
        import numpy as np
        
        df = pd.DataFrame({
            "close": np.random.randn(100).cumsum() + 100,
        })
        
        tool = AnalysisTool()
        result = tool.run(data=df, analysis_type="volatility")
        
        assert result["analysis_type"] == "volatility"
        assert "volatility_daily" in result
        assert "volatility_annual" in result
    
    def test_sharpe_analysis(self):
        """Test Sharpe ratio analysis."""
        pytest.importorskip("pandas")
        import pandas as pd
        import numpy as np
        
        df = pd.DataFrame({
            "close": np.random.randn(100).cumsum() + 100,
        })
        
        tool = AnalysisTool()
        result = tool.run(
            data=df,
            analysis_type="sharpe",
            risk_free_rate=0.02,
        )
        
        assert result["analysis_type"] == "sharpe"
        assert "sharpe_ratio" in result
    
    def test_drawdown_analysis(self):
        """Test drawdown analysis."""
        pytest.importorskip("pandas")
        import pandas as pd
        import numpy as np
        
        df = pd.DataFrame({
            "close": np.random.randn(100).cumsum() + 100,
        })
        
        tool = AnalysisTool()
        result = tool.run(data=df, analysis_type="drawdown")
        
        assert result["analysis_type"] == "drawdown"
        assert "max_drawdown" in result
        assert "max_drawdown_pct" in result
    
    def test_correlation_analysis(self):
        """Test correlation analysis."""
        pytest.importorskip("pandas")
        import pandas as pd
        import numpy as np
        
        df = pd.DataFrame({
            "close": np.random.randn(100).cumsum() + 100,
            "volume": np.random.randint(100, 1000, 100),
        })
        
        tool = AnalysisTool()
        result = tool.run(data=df, analysis_type="correlation")
        
        assert result["analysis_type"] == "correlation"
        assert "correlation_matrix" in result


class TestRiskCalculatorTool:
    """Tests for RiskCalculatorTool."""
    
    def test_risk_calculator_initialization(self):
        """Test risk calculator can be initialized."""
        tool = RiskCalculatorTool()
        assert tool.name == "risk_calculator"
    
    def test_calculate_risk_metrics(self):
        """Test calculating risk metrics."""
        tool = RiskCalculatorTool()
        result = tool.run(portfolio_id="test_portfolio")
        
        assert result["portfolio_id"] == "test_portfolio"
        assert "metrics" in result
    
    def test_calculate_specific_metrics(self):
        """Test calculating specific metrics."""
        tool = RiskCalculatorTool()
        result = tool.run(
            portfolio_id="test_portfolio",
            metrics=["var", "sharpe"],
        )
        
        metrics = result["metrics"]
        assert "var_95" in metrics
        assert "sharpe_ratio" in metrics
    
    def test_calculate_all_metrics(self):
        """Test calculating all metrics."""
        tool = RiskCalculatorTool()
        result = tool.run(portfolio_id="test_portfolio")
        
        metrics = result["metrics"]
        # Should have default metrics
        assert len(metrics) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
