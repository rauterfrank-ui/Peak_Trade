"""
Peak Trade API Server
=====================
FastAPI backend for Peak Trade Dashboard with real-time monitoring,
backtest execution, and system health tracking.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import asyncio
from datetime import datetime
import logging
import traceback

# Import Peak Trade modules
from src.core.resilience import health_check
from src.core.performance import performance_monitor

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Peak Trade API",
    description="Trading Platform API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections
active_connections: List[WebSocket] = []

# ==================== Models ====================

class BacktestConfig(BaseModel):
    strategy: str
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float = 10000.0
    parameters: Dict[str, float] = {}

class BacktestResult(BaseModel):
    run_id: str
    strategy: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    num_trades: int
    win_rate: float
    equity_curve: List[Dict[str, Any]]

class HealthStatus(BaseModel):
    service: str
    healthy: bool
    details: Optional[str] = None

# ==================== Health Endpoints ====================

@app.get("/health")
async def get_health():
    """Get overall health status."""
    try:
        is_healthy = health_check.is_system_healthy()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/health/detailed", response_model=List[HealthStatus])
async def get_health_detailed():
    """Get detailed health status for all services."""
    try:
        results = health_check.check_all()
        
        statuses = []
        for service_name, result in results.items():
            statuses.append(HealthStatus(
                service=service_name,
                healthy=result.healthy,
                details=result.message
            ))
        
        return statuses
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return [HealthStatus(
            service="system",
            healthy=False,
            details=f"Error: {str(e)}"
        )]

# ==================== Backtest Endpoints ====================

@app.post("/backtest/run", response_model=BacktestResult)
async def run_backtest(config: BacktestConfig):
    """
    Run backtest with given configuration.
    
    Example:
    ```json
    {
      "strategy": "momentum",
      "symbol": "BTC/USD",
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "initial_capital": 10000,
      "parameters": {
        "lookback_period": 20,
        "threshold": 0.02
      }
    }
    ```
    """
    try:
        # Import backtest engine
        from src.backtest.engine import BacktestEngine
        from src.strategies import load_strategy
        import pandas as pd
        import numpy as np
        
        # Generate mock data for now (replace with real data loader later)
        # TODO: Integrate with actual data loader
        dates = pd.date_range(start=config.start_date, end=config.end_date, freq='1H')
        base_price = 100
        price_changes = np.random.randn(len(dates)).cumsum()
        close_prices = base_price + price_changes
        open_prices = np.roll(close_prices, 1)
        open_prices[0] = base_price
        
        # Ensure OHLC constraints: low <= min(open, close), high >= max(open, close)
        high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.randn(len(dates)))
        low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.randn(len(dates)))
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': np.random.randint(1000, 10000, len(dates))
        })
        
        # Load strategy
        strategy_fn = load_strategy(config.strategy)
        
        # Run backtest
        engine = BacktestEngine()
        result = engine.run(
            df=data,
            signal_fn=strategy_fn,
            params=config.parameters,
            initial_capital=config.initial_capital
        )
        
        # Generate run_id
        run_id = f"{config.strategy}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Format response
        return BacktestResult(
            run_id=run_id,
            strategy=config.strategy,
            total_return=result.total_return if hasattr(result, 'total_return') else 0.0,
            sharpe_ratio=result.sharpe_ratio if hasattr(result, 'sharpe_ratio') else 0.0,
            max_drawdown=result.max_drawdown if hasattr(result, 'max_drawdown') else 0.0,
            num_trades=result.num_trades if hasattr(result, 'num_trades') else 0,
            win_rate=result.win_rate if hasattr(result, 'win_rate') else 0.0,
            equity_curve=[
                {"timestamp": str(idx), "equity": val}
                for idx, val in result.equity.items()
            ] if hasattr(result, 'equity') else []
        )
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/backtest/results")
async def list_backtest_results():
    """List all backtest results."""
    # TODO: Implement result storage and retrieval
    return {"results": []}

# ==================== Portfolio Endpoints ====================

@app.get("/portfolio/summary")
async def get_portfolio_summary():
    """Get current portfolio summary."""
    try:
        # TODO: Integrate with actual portfolio manager
        # Mock data for now
        return {
            "total_value": 12345.67,
            "cash": 5000.00,
            "positions": 7345.67,
            "pnl": 2345.67,
            "pnl_percent": 0.234
        }
    except Exception as e:
        logger.error(f"Portfolio summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio/positions")
async def get_positions():
    """Get all open positions."""
    try:
        # TODO: Integrate with actual portfolio manager
        # Mock data for now
        return {"positions": [
            {
                "symbol": "BTC/USD",
                "size": 0.5,
                "entry_price": 40000.0,
                "current_price": 42000.0,
                "pnl": 1000.0,
                "pnl_percent": 0.05
            }
        ]}
    except Exception as e:
        logger.error(f"Get positions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Metrics Endpoints ====================

@app.get("/metrics/performance")
async def get_performance_metrics():
    """Get performance metrics."""
    try:
        summary = performance_monitor.get_summary()
        
        operations = []
        for name, stats in summary.items():
            operations.append({
                "name": name,
                "count": stats.get("count", 0),
                "mean": stats.get("mean", 0.0),
                "p95": stats.get("p95", 0.0),
                "p99": stats.get("p99", 0.0)
            })
        
        return {"operations": operations}
    except Exception as e:
        logger.error(f"Performance metrics failed: {e}")
        return {"operations": []}

# ==================== Circuit Breaker Endpoints ====================

@app.get("/circuit-breakers")
async def get_circuit_breakers():
    """Get status of all circuit breakers."""
    # TODO: Integrate with circuit breaker registry
    return {"circuit_breakers": []}

# ==================== Backup Endpoints ====================

@app.get("/backups/list")
async def list_backups():
    """List all backups."""
    try:
        from src.core.backup_recovery import RecoveryManager
        
        recovery = RecoveryManager()
        backups = recovery.list_backups()
        
        return {"backups": backups}
    except Exception as e:
        logger.error(f"List backups failed: {e}")
        return {"backups": []}

@app.post("/backups/create")
async def create_backup(
    tags: List[str] = None,
    description: str = "Manual backup from dashboard"
):
    """Create new backup."""
    if tags is None:
        tags = []
    try:
        from src.core.backup_recovery import RecoveryManager
        
        recovery = RecoveryManager()
        backup_id = recovery.create_backup(
            include_config=True,
            include_state=True,
            tags=tags,
            description=description
        )
        
        return {"backup_id": backup_id, "status": "success"}
    except Exception as e:
        logger.error(f"Create backup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== WebSocket for Real-time Updates ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(5)
            
            # Get latest metrics
            health_status = health_check.is_system_healthy()
            perf_summary = performance_monitor.get_summary()
            
            await websocket.send_json({
                "type": "update",
                "timestamp": datetime.now().isoformat(),
                "health": health_status,
                "metrics": perf_summary
            })
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

# ==================== Startup ====================

@app.on_event("startup")
async def startup_event():
    logger.info("Peak Trade API started")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
