# Peak Trade WebUI - Quick Start Guide

## 🚀 Getting Started

The Peak Trade WebUI provides a comprehensive web-based interface for monitoring, backtesting, and managing your trading system.

### Quick Start with Docker (Recommended)

```bash
# Start the complete WebUI stack
bash scripts/start_webui.sh

# Access the dashboard
# - Dashboard:   http://localhost:8501
# - API Docs:    http://localhost:8000/docs
# - API:         http://localhost:8000
```

### Stop Services

```bash
cd docker
docker-compose -f docker-compose.webui.yml down
```

## 📊 Features

### Dashboard Pages

1. **📊 Dashboard** - Real-time portfolio overview
   - Key metrics: Total Value, P&L, Win Rate, Sharpe Ratio
   - Interactive equity curve
   - Recent trades table

2. **🔬 Backtest** - Run strategy backtests
   - Configure strategy parameters
   - Multiple strategy support
   - Visual results with equity curves
   - Performance metrics

3. **💼 Portfolio** - Portfolio management
   - Current summary and positions
   - Portfolio allocation visualization
   - P&L tracking

4. **📡 Monitoring** - System monitoring
   - Performance metrics
   - Circuit breaker status
   - Operation statistics

5. **🏥 System Health** - Health & backups
   - Overall health status
   - Service health checks
   - Backup management

## 🔧 Local Development

### Start API Server

```bash
# Install dependencies
pip install -r requirements.txt

# Start API
uvicorn src.webui.api.app:app --reload --host 127.0.0.1 --port 8000
```

### Start Streamlit Dashboard

```bash
# In another terminal
streamlit run src/webui/streamlit_app.py
```

## 📚 Documentation

Full documentation: [docs/WEBUI_DASHBOARD.md](./WEBUI_DASHBOARD.md)

## 🧪 Testing

```bash
# Run WebUI tests
pytest tests/webui/

# All tests should pass
# ✓ 10 tests for API endpoints
```

## 🛠️ Technology Stack

- **Backend**: FastAPI + uvicorn
- **Frontend**: Streamlit
- **Visualization**: Plotly
- **Real-time**: WebSocket
- **Deployment**: Docker Compose

## 📝 API Endpoints

- `GET /health` - System health
- `GET /health/detailed` - Detailed health checks
- `POST /backtest/run` - Run backtest
- `GET /backtest/results` - List results
- `GET /portfolio/summary` - Portfolio summary
- `GET /portfolio/positions` - Open positions
- `GET /metrics/performance` - Performance metrics
- `GET /circuit-breakers` - Circuit breaker status
- `GET /backups/list` - List backups
- `POST /backups/create` - Create backup
- `WS /ws` - Real-time updates

Full API documentation: http://localhost:8000/docs

## 🔍 Troubleshooting

### Port already in use

```bash
# Change ports in docker-compose.webui.yml
# Or kill existing processes:
lsof -ti:8000 | xargs kill  # API
lsof -ti:8501 | xargs kill  # Streamlit
```

### API not accessible

```bash
# Check if containers are running
docker ps

# View logs
docker-compose -f docker/docker-compose.webui.yml logs -f
```

## 📦 Files Created

- `src/webui/api/app.py` - FastAPI backend application
- `src/webui/streamlit_app.py` - Streamlit dashboard
- `docker/Dockerfile.api` - API Docker image
- `docker/Dockerfile.streamlit` - Streamlit Docker image
- `docker/docker-compose.webui.yml` - Docker Compose configuration
- `scripts/start_webui.sh` - Startup script
- `tests/webui/test_api.py` - API tests
- `docs/WEBUI_DASHBOARD.md` - Full documentation

## ✅ Implementation Status

All acceptance criteria met:
- ✅ FastAPI backend with REST API
- ✅ Streamlit Dashboard (5 pages)
- ✅ Real-time WebSocket updates
- ✅ Plotly interactive charts
- ✅ Docker Compose setup
- ✅ Integration with Circuit Breaker, Performance Monitoring
- ✅ Backtest visualization
- ✅ Portfolio tracking
- ✅ System health dashboard
- ✅ Documentation complete
- ✅ 10 automated tests passing

## 🎯 Next Steps

Potential enhancements:
- Real data integration with exchanges
- User authentication
- Trade execution from dashboard
- Advanced charting with indicators
- Alert notifications
- Mobile-responsive design

## 📞 Support

For issues:
1. Check logs: `docker-compose logs`
2. Review API docs: http://localhost:8000/docs
3. Consult [WEBUI_DASHBOARD.md](./WEBUI_DASHBOARD.md)
