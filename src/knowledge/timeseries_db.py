"""
Time-Series Database Integration

Support for storing and querying time-series data:
- Ticks and OHLCV data
- Portfolio histories
- Performance metrics over time

Backends:
- InfluxDB (recommended for time-series)
- TimescaleDB (PostgreSQL extension)
- Local Parquet files (simple fallback)

Usage:
    from src.knowledge.timeseries_db import TimeSeriesDBFactory

    db = TimeSeriesDBFactory.create("influxdb", config={
        "url": "http://localhost:8086",
        "token": "your-token",
        "org": "peak_trade",
        "bucket": "market_data"
    })

    # Write tick data
    db.write_ticks("BTC/USD", ticks_df)

    # Query portfolio history
    history = db.query_portfolio_history(
        start_time="2024-01-01",
        end_time="2024-12-31"
    )
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)


class TimeSeriesDBInterface(ABC):
    """Abstract interface for time-series databases."""

    @abstractmethod
    def write_ticks(
        self, symbol: str, data: pd.DataFrame, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Write tick data to the database."""
        pass

    @abstractmethod
    def write_portfolio_history(
        self, data: pd.DataFrame, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Write portfolio history to the database."""
        pass

    @abstractmethod
    def query_ticks(
        self,
        symbol: str,
        start_time: str,
        end_time: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """Query tick data from the database."""
        pass

    @abstractmethod
    def query_portfolio_history(
        self, start_time: str, end_time: str, filters: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """Query portfolio history from the database."""
        pass


class InfluxDBAdapter(TimeSeriesDBInterface):
    """InfluxDB adapter for time-series data."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize InfluxDB adapter.

        Args:
            config: Configuration dict with keys:
                - url: InfluxDB server URL
                - token: Authentication token
                - org: Organization name
                - bucket: Bucket name
        """
        try:
            from influxdb_client import InfluxDBClient, Point
            from influxdb_client.client.write_api import SYNCHRONOUS
        except ImportError:
            raise ImportError(
                "influxdb-client not installed. Install with: pip install influxdb-client"
            )

        self.url = config.get("url", "http://localhost:8086")
        self.token = config.get("token")
        self.org = config.get("org", "peak_trade")
        self.bucket = config.get("bucket", "market_data")

        if not self.token:
            raise ValueError("InfluxDB token is required")

        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()

        logger.info(f"InfluxDB initialized: {self.bucket} at {self.url} (org: {self.org})")

    def write_ticks(
        self, symbol: str, data: pd.DataFrame, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Write tick data to InfluxDB."""
        from influxdb_client import Point

        points = []
        for _, row in data.iterrows():
            point = (
                Point("tick")
                .tag("symbol", symbol)
                .field("price", float(row.get("price", 0)))
                .field("volume", float(row.get("volume", 0)))
                .time(row.get("timestamp"))
            )

            if tags:
                for key, value in tags.items():
                    point.tag(key, value)

            points.append(point)

        self.write_api.write(bucket=self.bucket, org=self.org, record=points)
        logger.info(f"Written {len(points)} tick records for {symbol}")

    def write_portfolio_history(
        self, data: pd.DataFrame, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Write portfolio history to InfluxDB."""
        from influxdb_client import Point

        points = []
        for _, row in data.iterrows():
            point = (
                Point("portfolio")
                .field("equity", float(row.get("equity", 0)))
                .field("cash", float(row.get("cash", 0)))
                .field("positions_value", float(row.get("positions_value", 0)))
                .time(row.get("timestamp"))
            )

            if tags:
                for key, value in tags.items():
                    point.tag(key, value)

            points.append(point)

        self.write_api.write(bucket=self.bucket, org=self.org, record=points)
        logger.info(f"Written {len(points)} portfolio history records")

    def query_ticks(
        self,
        symbol: str,
        start_time: str,
        end_time: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """Query tick data from InfluxDB."""
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: {start_time}, stop: {end_time})
            |> filter(fn: (r) => r["_measurement"] == "tick")
            |> filter(fn: (r) => r["symbol"] == "{symbol}")
        '''

        result = self.query_api.query_data_frame(query, org=self.org)
        logger.info(f"Queried {len(result)} tick records for {symbol}")
        return result

    def query_portfolio_history(
        self, start_time: str, end_time: str, filters: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """Query portfolio history from InfluxDB."""
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: {start_time}, stop: {end_time})
            |> filter(fn: (r) => r["_measurement"] == "portfolio")
        '''

        result = self.query_api.query_data_frame(query, org=self.org)
        logger.info(f"Queried {len(result)} portfolio history records")
        return result


class ParquetAdapter(TimeSeriesDBInterface):
    """Simple Parquet-based adapter for time-series data (fallback)."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Parquet adapter.

        Args:
            config: Configuration dict with keys:
                - base_path: Base directory for Parquet files
        """
        self.base_path = Path(config.get("base_path", "./data/timeseries"))
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.ticks_path = self.base_path / "ticks"
        self.ticks_path.mkdir(exist_ok=True)

        self.portfolio_path = self.base_path / "portfolio"
        self.portfolio_path.mkdir(exist_ok=True)

        logger.info(f"Parquet adapter initialized at {self.base_path}")

    def write_ticks(
        self, symbol: str, data: pd.DataFrame, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Write tick data to Parquet."""
        safe_symbol = symbol.replace("/", "_")
        file_path = self.ticks_path / f"{safe_symbol}.parquet"

        # Copy data to avoid mutating the original DataFrame
        data = data.copy()

        # Add tags as columns if provided
        if tags:
            for key, value in tags.items():
                data[f"tag_{key}"] = value

        data.to_parquet(file_path, index=False)
        logger.info(f"Written {len(data)} tick records for {symbol} to {file_path}")

    def write_portfolio_history(
        self, data: pd.DataFrame, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Write portfolio history to Parquet."""
        file_path = self.portfolio_path / "history.parquet"

        # Copy data to avoid mutating the original DataFrame
        data = data.copy()

        # Add tags as columns if provided
        if tags:
            for key, value in tags.items():
                data[f"tag_{key}"] = value

        # Append mode: read existing, concat, write
        if file_path.exists():
            existing = pd.read_parquet(file_path)
            data = pd.concat([existing, data], ignore_index=True)

        data.to_parquet(file_path, index=False)
        logger.info(f"Written {len(data)} portfolio history records to {file_path}")

    def query_ticks(
        self,
        symbol: str,
        start_time: str,
        end_time: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """Query tick data from Parquet."""
        safe_symbol = symbol.replace("/", "_")
        file_path = self.ticks_path / f"{safe_symbol}.parquet"

        if not file_path.exists():
            logger.warning(f"No tick data found for {symbol}")
            return pd.DataFrame()

        data = pd.read_parquet(file_path)

        # Filter by time
        if "timestamp" in data.columns:
            data["timestamp"] = pd.to_datetime(data["timestamp"])
            data = data[(data["timestamp"] >= start_time) & (data["timestamp"] <= end_time)]

        logger.info(f"Queried {len(data)} tick records for {symbol}")
        return data

    def query_portfolio_history(
        self, start_time: str, end_time: str, filters: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """Query portfolio history from Parquet."""
        file_path = self.portfolio_path / "history.parquet"

        if not file_path.exists():
            logger.warning("No portfolio history found")
            return pd.DataFrame()

        data = pd.read_parquet(file_path)

        # Filter by time
        if "timestamp" in data.columns:
            data["timestamp"] = pd.to_datetime(data["timestamp"])
            data = data[(data["timestamp"] >= start_time) & (data["timestamp"] <= end_time)]

        logger.info(f"Queried {len(data)} portfolio history records")
        return data


class TimeSeriesDBFactory:
    """Factory for creating time-series database instances."""

    _adapters = {
        "influxdb": InfluxDBAdapter,
        "parquet": ParquetAdapter,
    }

    @classmethod
    def create(cls, db_type: str, config: Dict[str, Any]) -> TimeSeriesDBInterface:
        """
        Create a time-series database instance.

        Args:
            db_type: Type of database ("influxdb", "parquet")
            config: Configuration dict for the database

        Returns:
            TimeSeriesDBInterface instance
        """
        if db_type not in cls._adapters:
            raise ValueError(
                f"Unknown database type: {db_type}. Available: {list(cls._adapters.keys())}"
            )

        adapter_class = cls._adapters[db_type]
        return adapter_class(config)

    @classmethod
    def register_adapter(cls, name: str, adapter_class: type) -> None:
        """Register a custom time-series database adapter."""
        cls._adapters[name] = adapter_class
        logger.info(f"Registered custom adapter: {name}")
