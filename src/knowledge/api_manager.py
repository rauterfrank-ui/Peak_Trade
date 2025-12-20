"""
API Manager for Knowledge Database APIs

Handles:
- API key management (loading from environment)
- Key rotation tracking
- Network monitoring hooks
- Security best practices

Usage:
    from src.knowledge.api_manager import APIManager
    
    manager = APIManager()
    
    # Get API key securely
    pinecone_key = manager.get_api_key("PINECONE_API_KEY")
    
    # Track API usage
    manager.track_request("pinecone", endpoint="/query")
    
    # Check if key rotation is needed
    if manager.should_rotate_key("OPENAI_API_KEY"):
        print("Consider rotating API key")
"""

import os
from typing import Any, Dict, Optional
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class APIManager:
    """Manager for API keys and security for knowledge databases."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize API manager.

        Args:
            config_path: Optional path to API config file (not for secrets!)
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.usage_log: Dict[str, Any] = {}
        self.key_rotation_log = self._load_rotation_log()

        logger.info("API Manager initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load API configuration (not secrets)."""
        if self.config_path and Path(self.config_path).exists():
            with open(self.config_path) as f:
                config = json.load(f)
            logger.info(f"Loaded API config from {self.config_path}")
            return config

        # Default configuration
        return {
            "rotation_interval_days": 90,
            "request_limit_per_hour": 1000,
            "monitored_apis": ["pinecone", "openai", "influxdb"],
        }

    def _load_rotation_log(self) -> Dict[str, datetime]:
        """Load key rotation log."""
        log_path = Path("data/api_rotation_log.json")
        if log_path.exists():
            with open(log_path) as f:
                data = json.load(f)
                return {
                    k: datetime.fromisoformat(v) for k, v in data.items()
                }

        return {}

    def _save_rotation_log(self) -> None:
        """Save key rotation log."""
        log_path = Path("data/api_rotation_log.json")
        log_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            k: v.isoformat() for k, v in self.key_rotation_log.items()
        }
        with open(log_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_api_key(self, key_name: str, required: bool = True) -> Optional[str]:
        """
        Get API key from environment.

        SECURITY: Keys should ONLY be stored in environment variables or
        secure secret management systems, NEVER in code or config files.

        Args:
            key_name: Environment variable name for the API key
            required: Whether the key is required (raises error if missing)

        Returns:
            API key value or None if not found and not required
        """
        key_value = os.environ.get(key_name)

        if key_value is None and required:
            raise ValueError(
                f"API key {key_name} not found in environment. "
                f"Set it with: export {key_name}=your_key"
            )

        if key_value:
            logger.info(f"Retrieved API key: {key_name}")
            # Track when key was last retrieved
            self.key_rotation_log[key_name] = datetime.now()
            self._save_rotation_log()

        return key_value

    def should_rotate_key(self, key_name: str) -> bool:
        """
        Check if an API key should be rotated.

        Args:
            key_name: Environment variable name for the API key

        Returns:
            True if key should be rotated
        """
        if key_name not in self.key_rotation_log:
            return False

        last_rotation = self.key_rotation_log[key_name]
        rotation_interval = timedelta(
            days=self.config.get("rotation_interval_days", 90)
        )

        should_rotate = datetime.now() - last_rotation > rotation_interval

        if should_rotate:
            logger.warning(
                f"API key {key_name} should be rotated "
                f"(last rotation: {last_rotation.strftime('%Y-%m-%d')})"
            )

        return should_rotate

    def track_request(
        self, api_name: str, endpoint: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track API request for monitoring.

        Args:
            api_name: Name of the API (e.g., "pinecone", "openai")
            endpoint: API endpoint being called
            metadata: Optional metadata about the request
        """
        if api_name not in self.usage_log:
            self.usage_log[api_name] = []

        self.usage_log[api_name].append(
            {
                "timestamp": datetime.now().isoformat(),
                "endpoint": endpoint,
                "metadata": metadata or {},
            }
        )

        logger.debug(f"Tracked request: {api_name}/{endpoint}")

    def get_usage_stats(self, api_name: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get usage statistics for an API.

        Args:
            api_name: Name of the API
            hours: Time window in hours

        Returns:
            Dict with usage statistics
        """
        if api_name not in self.usage_log:
            return {"api_name": api_name, "request_count": 0}

        cutoff = datetime.now() - timedelta(hours=hours)
        recent_requests = [
            req
            for req in self.usage_log[api_name]
            if datetime.fromisoformat(req["timestamp"]) > cutoff
        ]

        return {
            "api_name": api_name,
            "time_window_hours": hours,
            "request_count": len(recent_requests),
            "requests": recent_requests,
        }

    def check_rate_limit(self, api_name: str, hours: int = 1) -> bool:
        """
        Check if API is within rate limits.

        Args:
            api_name: Name of the API
            hours: Time window in hours

        Returns:
            True if within limits, False if limit exceeded
        """
        stats = self.get_usage_stats(api_name, hours=hours)
        request_limit = self.config.get("request_limit_per_hour", 1000)

        if stats["request_count"] >= request_limit:
            logger.warning(
                f"Rate limit exceeded for {api_name}: "
                f"{stats['request_count']}/{request_limit} requests in {hours}h"
            )
            return False

        return True

    def get_db_config(
        self, db_type: str, include_secrets: bool = False
    ) -> Dict[str, Any]:
        """
        Get database configuration.

        Args:
            db_type: Type of database (e.g., "chroma", "pinecone", "influxdb")
            include_secrets: Whether to include API keys (default: False)

        Returns:
            Configuration dict for the database
        """
        configs = {
            "chroma": {
                "persist_directory": os.environ.get(
                    "CHROMA_PERSIST_DIR", "./data/chroma_db"
                ),
                "collection_name": os.environ.get(
                    "CHROMA_COLLECTION", "peak_trade"
                ),
            },
            "pinecone": {
                "environment": os.environ.get(
                    "PINECONE_ENV", "us-west1-gcp"
                ),
                "index_name": os.environ.get(
                    "PINECONE_INDEX", "peak-trade"
                ),
            },
            "qdrant": {
                "url": os.environ.get(
                    "QDRANT_URL", ":memory:"
                ),
                "collection_name": os.environ.get(
                    "QDRANT_COLLECTION", "peak_trade"
                ),
            },
            "influxdb": {
                "url": os.environ.get(
                    "INFLUXDB_URL", "http://localhost:8086"
                ),
                "org": os.environ.get("INFLUXDB_ORG", "peak_trade"),
                "bucket": os.environ.get(
                    "INFLUXDB_BUCKET", "market_data"
                ),
            },
        }

        config = configs.get(db_type, {})

        # Add API keys if requested (use cautiously!)
        if include_secrets:
            if db_type == "pinecone":
                config["api_key"] = self.get_api_key(
                    "PINECONE_API_KEY", required=False
                )
            elif db_type == "qdrant":
                config["api_key"] = self.get_api_key(
                    "QDRANT_API_KEY", required=False
                )
            elif db_type == "influxdb":
                config["token"] = self.get_api_key(
                    "INFLUXDB_TOKEN", required=False
                )

        return config

    def validate_environment(self) -> Dict[str, bool]:
        """
        Validate that required environment variables are set.

        Returns:
            Dict mapping API names to availability status
        """
        required_keys = {
            "chroma": [],  # No API key needed for local
            "pinecone": ["PINECONE_API_KEY"],
            "qdrant": [],  # Optional for local
            "influxdb": ["INFLUXDB_TOKEN"],
        }

        validation = {}
        for api_name, keys in required_keys.items():
            if not keys:
                validation[api_name] = True
            else:
                validation[api_name] = all(
                    os.environ.get(key) is not None for key in keys
                )

        return validation

    def get_security_report(self) -> Dict[str, Any]:
        """
        Generate security report for API keys and usage.

        Returns:
            Dict with security status and recommendations
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "environment_validation": self.validate_environment(),
            "rotation_needed": {},
            "usage_summary": {},
        }

        # Check key rotation
        for key_name in self.key_rotation_log:
            report["rotation_needed"][key_name] = self.should_rotate_key(key_name)

        # Usage summary
        for api_name in self.config.get("monitored_apis", []):
            report["usage_summary"][api_name] = self.get_usage_stats(api_name)

        return report
