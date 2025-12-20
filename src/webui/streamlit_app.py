"""
Peak Trade Streamlit Dashboard
==============================
Interactive dashboard for Peak Trade with real-time monitoring,
backtest visualization, portfolio tracking, and system health.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import logging

# Configuration
API_BASE_URL = "http://localhost:8000"
st.set_page_config(
    page_title="Peak Trade Dashboard",
    page_icon="📊",
    layout="wide"
)

logger = logging.getLogger(__name__)

# ==================== Helper Functions ====================

def fetch_api(endpoint: str):
    """Fetch data from API."""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, requests.Timeout) as e:
        st.error(f"API Error: {e}")
        return None

def post_api(endpoint: str, data: dict):
    """Post data to API."""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, requests.Timeout) as e:
        st.error(f"API Error: {e}")
        return None

# ==================== Sidebar ====================

st.sidebar.title("🚀 Peak Trade")
page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "🔬 Backtest", "💼 Portfolio", "📡 Monitoring", "🏥 System Health"]
)

# ==================== Page: Dashboard ====================

if page == "📊 Dashboard":
    st.title("📊 Trading Dashboard")
    
    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    # Fetch portfolio summary
    summary = fetch_api("/portfolio/summary")
    
    if summary:
        with col1:
            st.metric("Total Value", f"${summary['total_value']:,.2f}", 
                     f"{summary['pnl_percent']:.2%}")
        
        with col2:
            st.metric("Daily P&L", f"${summary['pnl']:,.2f}", 
                     f"{summary['pnl_percent']:.2%}")
    else:
        with col1:
            st.metric("Total Value", "$12,345", "+5.2%")
        
        with col2:
            st.metric("Daily P&L", "$234", "+1.9%")
    
    with col3:
        st.metric("Win Rate", "62%", "+2%")
    
    with col4:
        st.metric("Sharpe Ratio", "1.85", "+0.1")
    
    # Equity Curve
    st.subheader("Equity Curve")
    
    # Mock data (replace with real data)
    dates = pd.date_range(start="2023-01-01", end=datetime.now(), freq="D")
    equity = 10000 * (1 + 0.001 * range(len(dates)))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=equity,
        mode='lines',
        name='Equity',
        line=dict(color='#00ff00', width=2)
    ))
    fig.update_layout(
        title="Portfolio Equity Over Time",
        xaxis_title="Date",
        yaxis_title="Equity ($)",
        template="plotly_dark",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent Trades
    st.subheader("Recent Trades")
    
    trades_data = {
        "Time": ["10:30:15", "11:45:22", "14:20:10"],
        "Symbol": ["BTC/USD", "ETH/USD", "BTC/USD"],
        "Side": ["BUY", "SELL", "BUY"],
        "Price": [42000, 2800, 42150],
        "Quantity": [0.5, 2.0, 0.3],
        "P&L": ["+$150", "-$50", "+$75"]
    }
    
    st.dataframe(pd.DataFrame(trades_data), use_container_width=True)

# ==================== Page: Backtest ====================

elif page == "🔬 Backtest":
    st.title("🔬 Backtest Engine")
    
    with st.form("backtest_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            strategy = st.selectbox(
                "Strategy",
                ["momentum_1h", "ma_crossover", "rsi_strategy", "trend_following", "mean_reversion"]
            )
            symbol = st.text_input("Symbol", "BTC/USD")
            initial_capital = st.number_input("Initial Capital", value=10000.0, min_value=1000.0)
        
        with col2:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365))
            end_date = st.date_input("End Date", datetime.now())
        
        st.subheader("Strategy Parameters")
        lookback_period = st.slider("Lookback Period", 5, 50, 20)
        threshold = st.slider("Threshold", 0.01, 0.1, 0.02, 0.01)
        
        submitted = st.form_submit_button("Run Backtest")
        
        if submitted:
            with st.spinner("Running backtest..."):
                config = {
                    "strategy": strategy,
                    "symbol": symbol,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "initial_capital": initial_capital,
                    "parameters": {
                        "lookback_period": lookback_period,
                        "threshold": threshold
                    }
                }
                
                result = post_api("/backtest/run", config)
                
                if result:
                    st.success(f"Backtest completed! Run ID: {result['run_id']}")
                    
                    # Display results
                    col1, col2, col3, col4 = st.columns(4)
                    
                    col1.metric("Total Return", f"{result['total_return']:.2%}")
                    col2.metric("Sharpe Ratio", f"{result['sharpe_ratio']:.2f}")
                    col3.metric("Max Drawdown", f"{result['max_drawdown']:.2%}")
                    col4.metric("Win Rate", f"{result['win_rate']:.2%}")
                    
                    # Equity curve
                    if result.get('equity_curve'):
                        equity_df = pd.DataFrame(result['equity_curve'])
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=equity_df['timestamp'],
                            y=equity_df['equity'],
                            mode='lines',
                            name='Equity',
                            line=dict(color='#00ff00', width=2)
                        ))
                        fig.update_layout(
                            title="Backtest Equity Curve",
                            xaxis_title="Time",
                            yaxis_title="Equity ($)",
                            template="plotly_dark",
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)

# ==================== Page: Portfolio ====================

elif page == "💼 Portfolio":
    st.title("💼 Portfolio Management")
    
    # Portfolio Summary
    summary = fetch_api("/portfolio/summary")
    
    if summary:
        col1, col2, col3 = st.columns(3)
        
        col1.metric("Total Value", f"${summary['total_value']:,.2f}")
        col2.metric("Cash", f"${summary['cash']:,.2f}")
        col3.metric("P&L", f"${summary['pnl']:,.2f}", f"{summary['pnl_percent']:.2%}")
    
    # Positions
    st.subheader("Open Positions")
    
    positions = fetch_api("/portfolio/positions")
    
    if positions and positions.get("positions"):
        positions_df = pd.DataFrame(positions["positions"])
        st.dataframe(positions_df, use_container_width=True)
    else:
        st.info("No open positions")
    
    # Allocation Chart
    st.subheader("Portfolio Allocation")
    
    # Mock data
    allocation = {"BTC": 40, "ETH": 30, "Cash": 30}
    
    fig = go.Figure(data=[go.Pie(
        labels=list(allocation.keys()),
        values=list(allocation.values()),
        hole=0.3
    )])
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

# ==================== Page: Monitoring ====================

elif page == "📡 Monitoring":
    st.title("📡 System Monitoring")
    
    # Performance Metrics
    st.subheader("Performance Metrics")
    
    metrics = fetch_api("/metrics/performance")
    
    if metrics and metrics.get("operations"):
        metrics_df = pd.DataFrame(metrics["operations"])
        st.dataframe(metrics_df, use_container_width=True)
    else:
        st.info("No performance metrics available")
    
    # Circuit Breakers
    st.subheader("Circuit Breakers")
    
    breakers = fetch_api("/circuit-breakers")
    
    if breakers and breakers.get("circuit_breakers"):
        for breaker in breakers["circuit_breakers"]:
            status = "🟢 CLOSED" if breaker["state"] == "closed" else "🔴 OPEN"
            st.write(f"{breaker['name']}: {status}")
    else:
        st.info("No circuit breakers configured")

# ==================== Page: System Health ====================

elif page == "🏥 System Health":
    st.title("🏥 System Health")
    
    # Overall Health
    health = fetch_api("/health")
    
    if health:
        if health["status"] == "healthy":
            st.success("✅ System Healthy")
        else:
            st.error("❌ System Unhealthy")
    
    # Detailed Health Checks
    st.subheader("Service Health Checks")
    
    detailed = fetch_api("/health/detailed")
    
    if detailed:
        for service in detailed:
            status_icon = "✅" if service["healthy"] else "❌"
            with st.expander(f"{status_icon} {service['service']}"):
                st.write(service.get("details", "No details available"))
    
    # Backups
    st.subheader("Backups")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        backups = fetch_api("/backups/list")
        
        if backups and backups.get("backups"):
            backups_df = pd.DataFrame(backups["backups"])
            st.dataframe(backups_df, use_container_width=True)
        else:
            st.info("No backups available")
    
    with col2:
        if st.button("Create Backup"):
            with st.spinner("Creating backup..."):
                result = post_api("/backups/create", {
                    "tags": ["manual"],
                    "description": "Manual backup from dashboard"
                })
                
                if result:
                    st.success(f"Backup created: {result['backup_id']}")

# ==================== Footer ====================

st.sidebar.markdown("---")
st.sidebar.markdown("Peak Trade v1.0.0")
st.sidebar.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
