# Peak Trade WebUI Dashboard

## Overview

The Peak Trade WebUI Dashboard provides a comprehensive web-based interface for monitoring, backtesting, and managing your trading system. Built with FastAPI for the backend and Streamlit for the frontend, it offers real-time updates, interactive visualizations, and system health tracking.

## Features

### 📊 Dashboard
- Real-time portfolio overview
- Key metrics: Total Value, P&L, Win Rate, Sharpe Ratio
- Interactive equity curve visualization
- Recent trades table

### 🔬 Backtest
- Configure and run backtests with custom parameters
- Multiple strategy support
- Visual backtest results with equity curves
- Performance metrics: Total Return, Sharpe Ratio, Max Drawdown, Win Rate

### 💼 Portfolio
- Current portfolio summary
- Open positions tracking
- Portfolio allocation pie chart
- P&L tracking

### 📡 Monitoring
- Performance metrics for all operations
- Circuit breaker status
- System operation statistics

### 🏥 System Health
- Overall health status
- Detailed service health checks
- Backup management
- One-click backup creation

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for local development)

### Using Docker (Recommended)

Start the complete WebUI stack:

```bash
bash scripts/start_webui.sh
```

Access the dashboard:
- **Dashboard**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **API**: http://localhost:8000

View logs:
```bash
cd docker
docker-compose -f docker-compose.webui.yml logs -f
```

Stop services:
```bash
cd docker
docker-compose -f docker-compose.webui.yml down
```

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the API server:
```bash
uvicorn src.webui.api.app:app --reload --host 127.0.0.1 --port 8000
```

3. Start the Streamlit dashboard (in another terminal):
```bash
streamlit run src/webui/streamlit_app.py
```

## API Endpoints

### Health
- `GET /health` - Overall system health
- `GET /health/detailed` - Detailed service health checks

### Backtest
- `POST /backtest/run` - Run a backtest
- `GET /backtest/results` - List backtest results

### Portfolio
- `GET /portfolio/summary` - Portfolio summary
- `GET /portfolio/positions` - Open positions

### Metrics
- `GET /metrics/performance` - Performance metrics

### Circuit Breakers
- `GET /circuit-breakers` - Circuit breaker status

### Backups
- `GET /backups/list` - List backups
- `POST /backups/create` - Create new backup

### WebSocket
- `WS /ws` - Real-time updates

## Configuration

### API Configuration

The API uses the following default settings:
- Host: `0.0.0.0`
- Port: `8000`
- CORS: Enabled for all origins (customize in production)

### Streamlit Configuration

The Streamlit app uses:
- API Base URL: `http://localhost:8000` (local) or `http://api:8000` (Docker)
- Port: `8501`
- Layout: Wide mode

## Architecture

### Backend (FastAPI)

The backend API (`src/webui/api/app.py`) provides:
- RESTful endpoints for data access
- WebSocket support for real-time updates
- Integration with Peak Trade core modules:
  - `src.core.resilience` - Health checks
  - `src.core.performance` - Performance monitoring
  - `src.core.backup_recovery` - Backup management
  - `src.backtest.engine` - Backtest execution
  - `src.strategies` - Strategy loading

### Frontend (Streamlit)

The Streamlit dashboard (`src/webui/streamlit_app.py`) provides:
- 5 main pages with intuitive navigation
- Interactive Plotly charts
- Real-time data updates via API polling
- Responsive layout

### Docker Setup

Two Docker containers:
1. **API Container** (`peak-api`): Runs FastAPI backend
2. **Streamlit Container** (`peak-streamlit`): Runs Streamlit dashboard

Connected via Docker network for seamless communication.

## Customization

### Adding New Strategies

1. Add strategy to `src/strategies/`
2. Register in `src/strategies/__init__.py`
3. Strategy will appear in backtest dropdown automatically

### Adding New Metrics

1. Implement metric collection in relevant module
2. Add endpoint in `src/webui/api/app.py`
3. Add visualization in `src/webui/streamlit_app.py`

### Custom Themes

Streamlit supports custom themes. Create `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#00ff00"
backgroundColor = "#0e1117"
secondaryBackgroundColor = "#262730"
textColor = "#ffffff"
font = "sans serif"
```

## Troubleshooting

### API not accessible from Streamlit

- Check if both containers are running: `docker ps`
- Check network connectivity: `docker network inspect peak-network`
- Review logs: `docker-compose -f docker/docker-compose.webui.yml logs`

### Port already in use

Change ports in `docker-compose.webui.yml`:
```yaml
ports:
  - "8001:8000"  # API
  - "8502:8501"  # Streamlit
```

### Import errors

Ensure `PYTHONPATH` is set correctly:
```bash
export PYTHONPATH=/home/runner/work/Peak_Trade/Peak_Trade
```

## Development

### Running Tests

```bash
pytest tests/webui/
```

### Code Style

The project follows PEP 8 style guidelines. Use:
```bash
ruff check src/webui/
black src/webui/
```

## Future Enhancements

- [ ] Real data integration with exchanges
- [ ] User authentication and authorization
- [ ] Multi-user support
- [ ] Trade execution from dashboard
- [ ] Advanced charting (candlesticks, indicators)
- [ ] Alert notifications
- [ ] Mobile-responsive design
- [ ] Dark/Light theme toggle

## Support

For issues or questions:
1. Check the logs: `docker-compose logs`
2. Review API docs: http://localhost:8000/docs
3. Consult main README.md

## License

Proprietary - Peak Trade
