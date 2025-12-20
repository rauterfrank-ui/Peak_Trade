"""
Tests for Pydantic Config Models
================================
Comprehensive validation tests for all config models.

Test Coverage:
- Valid configurations
- Invalid values (negative, out of range)
- Missing required fields
- Wrong types
- Cross-field validation (e.g., end_date > start_date)
- Edge cases
"""

import pytest
from pydantic import ValidationError

from src.config.models import (
    BacktestConfig,
    DataConfig,
    RiskConfig,
    PeakTradeConfig,
)


class TestBacktestConfig:
    """Tests for BacktestConfig validation."""
    
    def test_valid_backtest_config(self):
        """Test: Valid backtest config."""
        config = BacktestConfig(
            initial_capital=10000.0,
            start_date="2024-01-01",
            end_date="2024-12-31",
            max_drawdown=0.25,
            commission=0.001
        )
        assert config.initial_capital == 10000.0
        assert config.start_date == "2024-01-01"
        assert config.end_date == "2024-12-31"
        assert config.max_drawdown == 0.25
        assert config.commission == 0.001
    
    def test_backtest_alias_initial_cash(self):
        """Test: Support initial_cash alias for backward compatibility."""
        config = BacktestConfig(initial_cash=5000.0)
        assert config.initial_capital == 5000.0
    
    def test_backtest_invalid_negative_capital(self):
        """Test: Negative initial capital raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BacktestConfig(initial_capital=-1000.0)
        
        errors = exc_info.value.errors()
        assert any("greater than 0" in str(err) for err in errors)
    
    def test_backtest_invalid_zero_capital(self):
        """Test: Zero initial capital raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BacktestConfig(initial_capital=0.0)
        
        errors = exc_info.value.errors()
        assert any("greater than 0" in str(err) for err in errors)
    
    def test_backtest_invalid_date_format(self):
        """Test: Invalid date format raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BacktestConfig(
                initial_capital=10000.0,
                start_date="01-01-2024"  # Wrong format
            )
        
        errors = exc_info.value.errors()
        assert any("pattern" in str(err).lower() or "match" in str(err).lower() for err in errors)
    
    def test_backtest_end_before_start(self):
        """Test: end_date before start_date raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BacktestConfig(
                initial_capital=10000.0,
                start_date="2024-12-31",
                end_date="2024-01-01"
            )
        
        errors = exc_info.value.errors()
        assert any("after start_date" in str(err) for err in errors)
    
    def test_backtest_end_equals_start(self):
        """Test: end_date equal to start_date raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BacktestConfig(
                initial_capital=10000.0,
                start_date="2024-01-01",
                end_date="2024-01-01"
            )
        
        errors = exc_info.value.errors()
        assert any("after start_date" in str(err) for err in errors)
    
    def test_backtest_invalid_max_drawdown_negative(self):
        """Test: Negative max_drawdown raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BacktestConfig(
                initial_capital=10000.0,
                max_drawdown=-0.1
            )
        
        errors = exc_info.value.errors()
        assert any("greater than or equal to 0" in str(err) for err in errors)
    
    def test_backtest_invalid_max_drawdown_too_large(self):
        """Test: max_drawdown > 1 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BacktestConfig(
                initial_capital=10000.0,
                max_drawdown=1.5
            )
        
        errors = exc_info.value.errors()
        assert any("less than or equal to 1" in str(err) for err in errors)
    
    def test_backtest_invalid_commission_negative(self):
        """Test: Negative commission raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BacktestConfig(
                initial_capital=10000.0,
                commission=-0.001
            )
        
        errors = exc_info.value.errors()
        assert any("greater than or equal to 0" in str(err) for err in errors)
    
    def test_backtest_invalid_commission_too_large(self):
        """Test: Commission > 0.1 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BacktestConfig(
                initial_capital=10000.0,
                commission=0.15
            )
        
        errors = exc_info.value.errors()
        assert any("less than or equal to 0.1" in str(err) for err in errors)
    
    def test_backtest_optional_dates(self):
        """Test: Dates are optional."""
        config = BacktestConfig(initial_capital=10000.0)
        assert config.start_date is None
        assert config.end_date is None
    
    def test_backtest_defaults(self):
        """Test: Default values are set."""
        config = BacktestConfig(initial_capital=10000.0)
        assert config.commission == 0.001
        assert config.results_dir == "results"


class TestDataConfig:
    """Tests for DataConfig validation."""
    
    def test_valid_data_config(self):
        """Test: Valid data config."""
        config = DataConfig(
            provider="kraken",
            cache_enabled=True,
            cache_ttl=3600,
            symbols=["BTC/USD", "ETH/USD"]
        )
        assert config.provider == "kraken"
        assert config.cache_enabled is True
        assert config.cache_ttl == 3600
        assert config.symbols == ["BTC/USD", "ETH/USD"]
    
    def test_data_alias_use_cache(self):
        """Test: Support use_cache alias for backward compatibility."""
        config = DataConfig(use_cache=False)
        assert config.cache_enabled is False
    
    def test_data_invalid_provider(self):
        """Test: Invalid provider raises error."""
        with pytest.raises(ValidationError) as exc_info:
            DataConfig(provider="invalid")
        
        errors = exc_info.value.errors()
        assert any("literal" in str(err).lower() or "input" in str(err).lower() for err in errors)
    
    def test_data_invalid_cache_ttl_zero(self):
        """Test: Zero cache_ttl raises error."""
        with pytest.raises(ValidationError) as exc_info:
            DataConfig(cache_ttl=0)
        
        errors = exc_info.value.errors()
        assert any("greater than 0" in str(err) for err in errors)
    
    def test_data_invalid_cache_ttl_negative(self):
        """Test: Negative cache_ttl raises error."""
        with pytest.raises(ValidationError) as exc_info:
            DataConfig(cache_ttl=-100)
        
        errors = exc_info.value.errors()
        assert any("greater than 0" in str(err) for err in errors)
    
    def test_data_empty_symbols_list(self):
        """Test: Empty symbols list raises error."""
        with pytest.raises(ValidationError) as exc_info:
            DataConfig(symbols=[])
        
        errors = exc_info.value.errors()
        assert any("at least 1" in str(err).lower() for err in errors)
    
    def test_data_defaults(self):
        """Test: Default values are set."""
        config = DataConfig()
        assert config.provider == "kraken"
        assert config.cache_enabled is True
        assert config.cache_ttl == 3600
        assert config.default_timeframe == "1h"
        assert config.data_dir == "data"
        assert config.cache_format == "parquet"


class TestRiskConfig:
    """Tests for RiskConfig validation."""
    
    def test_valid_risk_config(self):
        """Test: Valid risk config."""
        config = RiskConfig(
            max_position_size=0.1,
            max_portfolio_leverage=1.5,
            stop_loss_pct=0.02
        )
        assert config.max_position_size == 0.1
        assert config.max_portfolio_leverage == 1.5
        assert config.stop_loss_pct == 0.02
    
    def test_risk_invalid_position_size_zero(self):
        """Test: Zero max_position_size raises error."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(max_position_size=0.0)
        
        errors = exc_info.value.errors()
        assert any("greater than 0" in str(err) for err in errors)
    
    def test_risk_invalid_position_size_negative(self):
        """Test: Negative max_position_size raises error."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(max_position_size=-0.1)
        
        errors = exc_info.value.errors()
        assert any("greater than 0" in str(err) for err in errors)
    
    def test_risk_invalid_position_size_too_large(self):
        """Test: max_position_size > 1 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(max_position_size=1.5)
        
        errors = exc_info.value.errors()
        assert any("less than or equal to 1" in str(err) for err in errors)
    
    def test_risk_invalid_leverage_too_small(self):
        """Test: max_portfolio_leverage < 1 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(max_portfolio_leverage=0.5)
        
        errors = exc_info.value.errors()
        assert any("greater than or equal to 1" in str(err) for err in errors)
    
    def test_risk_invalid_leverage_too_large(self):
        """Test: max_portfolio_leverage > 10 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(max_portfolio_leverage=15.0)
        
        errors = exc_info.value.errors()
        assert any("less than or equal to 10" in str(err) for err in errors)
    
    def test_risk_invalid_stop_loss_negative(self):
        """Test: Negative stop_loss_pct raises error."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(stop_loss_pct=-0.01)
        
        errors = exc_info.value.errors()
        assert any("greater than or equal to 0" in str(err) for err in errors)
    
    def test_risk_invalid_stop_loss_too_large(self):
        """Test: stop_loss_pct > 1 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(stop_loss_pct=1.5)
        
        errors = exc_info.value.errors()
        assert any("less than or equal to 1" in str(err) for err in errors)
    
    def test_risk_defaults(self):
        """Test: Default values are set."""
        config = RiskConfig()
        assert config.max_position_size == 0.1
        assert config.max_portfolio_leverage == 1.0
        assert config.stop_loss_pct is None
        assert config.risk_per_trade == 0.01
        assert config.max_daily_loss == 0.03
        assert config.max_positions == 2
        assert config.min_position_value == 50.0
        assert config.min_stop_distance == 0.005


class TestPeakTradeConfig:
    """Tests for PeakTradeConfig (root model)."""
    
    def test_valid_full_config(self):
        """Test: Valid complete config."""
        config_dict = {
            "backtest": {
                "initial_capital": 10000.0,
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            },
            "data": {
                "provider": "kraken",
                "symbols": ["BTC/USD"]
            },
            "risk": {
                "max_position_size": 0.2
            }
        }
        config = PeakTradeConfig(**config_dict)
        
        assert config.backtest.initial_capital == 10000.0
        assert config.data.provider == "kraken"
        assert config.risk.max_position_size == 0.2
    
    def test_missing_required_section(self):
        """Test: Missing required section raises error."""
        config_dict = {
            "backtest": {"initial_capital": 10000.0},
            "data": {"provider": "kraken"}
            # Missing risk section
        }
        
        with pytest.raises(ValidationError) as exc_info:
            PeakTradeConfig(**config_dict)
        
        errors = exc_info.value.errors()
        assert any("risk" in str(err) for err in errors)
    
    def test_invalid_nested_field(self):
        """Test: Invalid nested field raises error."""
        config_dict = {
            "backtest": {
                "initial_capital": -5000.0  # Invalid: negative
            },
            "data": {"provider": "kraken"},
            "risk": {"max_position_size": 0.2}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            PeakTradeConfig(**config_dict)
        
        errors = exc_info.value.errors()
        assert any("initial_capital" in str(err) for err in errors)
    
    def test_extra_fields_allowed(self):
        """Test: Extra fields are allowed for backward compatibility."""
        config_dict = {
            "backtest": {"initial_capital": 10000.0},
            "data": {"provider": "kraken"},
            "risk": {"max_position_size": 0.2},
            "extra_section": {"foo": "bar"}  # Extra field
        }
        
        # Should not raise error due to extra="allow"
        config = PeakTradeConfig(**config_dict)
        assert config.backtest.initial_capital == 10000.0


class TestEdgeCases:
    """Tests for edge cases and boundary values."""
    
    def test_backtest_max_valid_commission(self):
        """Test: Commission at upper boundary (0.1) is valid."""
        config = BacktestConfig(
            initial_capital=10000.0,
            commission=0.1
        )
        assert config.commission == 0.1
    
    def test_backtest_min_valid_commission(self):
        """Test: Commission at lower boundary (0.0) is valid."""
        config = BacktestConfig(
            initial_capital=10000.0,
            commission=0.0
        )
        assert config.commission == 0.0
    
    def test_risk_max_valid_leverage(self):
        """Test: Leverage at upper boundary (10.0) is valid."""
        config = RiskConfig(max_portfolio_leverage=10.0)
        assert config.max_portfolio_leverage == 10.0
    
    def test_risk_min_valid_leverage(self):
        """Test: Leverage at lower boundary (1.0) is valid."""
        config = RiskConfig(max_portfolio_leverage=1.0)
        assert config.max_portfolio_leverage == 1.0
    
    def test_risk_min_valid_position_size(self):
        """Test: Very small but positive position size is valid."""
        config = RiskConfig(max_position_size=0.001)
        assert config.max_position_size == 0.001
    
    def test_risk_max_valid_position_size(self):
        """Test: Position size at upper boundary (1.0) is valid."""
        config = RiskConfig(max_position_size=1.0)
        assert config.max_position_size == 1.0
