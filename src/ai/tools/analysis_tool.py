"""
Analysis Tool for agents.

Performs statistical analysis on market data.
"""

from typing import Any, Dict, Optional
import logging

try:
    import pandas as pd
    import numpy as np
    ANALYSIS_AVAILABLE = True
except ImportError:
    ANALYSIS_AVAILABLE = False
    pd = None
    np = None

from .base import AgentTool


logger = logging.getLogger(__name__)


class AnalysisTool(AgentTool):
    """
    Statistical analysis of data.
    
    Provides various analysis methods:
    - Correlation analysis
    - Volatility calculation
    - Sharpe ratio
    - Drawdown analysis
    - Trend detection
    """
    
    @property
    def name(self) -> str:
        return "analysis"
    
    @property
    def description(self) -> str:
        return "Perform statistical analysis on market data (correlation, volatility, Sharpe, etc.)"
    
    def run(
        self,
        data: Any,
        analysis_type: str = "summary",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Perform statistical analysis.
        
        Args:
            data: DataFrame or data to analyze
            analysis_type: Type of analysis ("summary", "correlation", "volatility", "sharpe")
            **kwargs: Additional parameters
            
        Returns:
            Analysis results dict
        """
        logger.info(f"Running {analysis_type} analysis")
        
        if not ANALYSIS_AVAILABLE:
            return {
                "analysis_type": analysis_type,
                "error": "Analysis libraries not available",
                "note": "Requires pandas and numpy",
            }
        
        # Ensure data is DataFrame
        if not isinstance(data, pd.DataFrame):
            return {
                "analysis_type": analysis_type,
                "error": "Data must be a pandas DataFrame",
            }
        
        if analysis_type == "summary":
            return self._summary_analysis(data, **kwargs)
        elif analysis_type == "correlation":
            return self._correlation_analysis(data, **kwargs)
        elif analysis_type == "volatility":
            return self._volatility_analysis(data, **kwargs)
        elif analysis_type == "sharpe":
            return self._sharpe_analysis(data, **kwargs)
        elif analysis_type == "drawdown":
            return self._drawdown_analysis(data, **kwargs)
        else:
            return {
                "analysis_type": analysis_type,
                "error": f"Unknown analysis type: {analysis_type}",
            }
    
    def _summary_analysis(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Generate summary statistics."""
        if "close" not in data.columns:
            return {"error": "Data must contain 'close' column"}
        
        close = data["close"]
        returns = close.pct_change().dropna()
        
        return {
            "analysis_type": "summary",
            "count": len(data),
            "mean_price": float(close.mean()),
            "std_price": float(close.std()),
            "min_price": float(close.min()),
            "max_price": float(close.max()),
            "mean_return": float(returns.mean()),
            "std_return": float(returns.std()),
            "total_return": float((close.iloc[-1] / close.iloc[0]) - 1),
        }
    
    def _correlation_analysis(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Calculate correlations between columns."""
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        corr_matrix = data[numeric_cols].corr()
        
        return {
            "analysis_type": "correlation",
            "correlation_matrix": corr_matrix.to_dict(),
        }
    
    def _volatility_analysis(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Calculate volatility metrics."""
        if "close" not in data.columns:
            return {"error": "Data must contain 'close' column"}
        
        close = data["close"]
        returns = close.pct_change().dropna()
        
        # Annualization factor (assuming daily data)
        annualization = kwargs.get("annualization_factor", 252)
        
        volatility_daily = float(returns.std())
        volatility_annual = volatility_daily * np.sqrt(annualization)
        
        return {
            "analysis_type": "volatility",
            "volatility_daily": volatility_daily,
            "volatility_annual": volatility_annual,
            "annualization_factor": annualization,
        }
    
    def _sharpe_analysis(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Calculate Sharpe ratio."""
        if "close" not in data.columns:
            return {"error": "Data must contain 'close' column"}
        
        close = data["close"]
        returns = close.pct_change().dropna()
        
        risk_free_rate = kwargs.get("risk_free_rate", 0.0)
        annualization = kwargs.get("annualization_factor", 252)
        
        excess_returns = returns - (risk_free_rate / annualization)
        sharpe = float(excess_returns.mean() / excess_returns.std() * np.sqrt(annualization))
        
        return {
            "analysis_type": "sharpe",
            "sharpe_ratio": sharpe,
            "risk_free_rate": risk_free_rate,
            "annualization_factor": annualization,
        }
    
    def _drawdown_analysis(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Calculate drawdown metrics."""
        if "close" not in data.columns:
            return {"error": "Data must contain 'close' column"}
        
        close = data["close"]
        
        # Calculate drawdowns
        cummax = close.cummax()
        drawdown = (close - cummax) / cummax
        
        max_drawdown = float(drawdown.min())
        max_drawdown_idx = drawdown.idxmin()
        
        return {
            "analysis_type": "drawdown",
            "max_drawdown": max_drawdown,
            "max_drawdown_pct": max_drawdown * 100,
            "max_drawdown_date": str(max_drawdown_idx) if hasattr(max_drawdown_idx, '__str__') else None,
        }
