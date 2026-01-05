"""
Run Summary Contract
====================

Stable JSON contract for run metadata and results.
Enables local comparison and reporting without MLflow dependency.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class RunSummary:
    """
    Stable contract for run metadata and results.

    This provides a standard, version-controlled format for tracking
    experiment runs. Can be serialized to JSON for local storage and
    comparison without requiring MLflow or network access.

    Attributes:
        run_id: Unique identifier for this run
        started_at_utc: ISO 8601 timestamp when run started
        finished_at_utc: ISO 8601 timestamp when run finished
        status: Run status (FINISHED, FAILED, RUNNING, KILLED)
        tags: String key-value pairs for categorization
        params: Run parameters (strategy config, hyperparams, etc.)
        metrics: Numeric metrics (returns, sharpe, max_dd, etc.)
        artifacts: List of relative paths to saved artifacts
        git_sha: Git commit SHA if available
        worktree: Git worktree name if applicable
        hostname: Machine hostname where run executed
        tracking_backend: Which backend was used ("null" or "mlflow")
    """

    run_id: str
    started_at_utc: str
    finished_at_utc: str
    status: str
    tags: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Union[str, int, float, bool]] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    git_sha: Optional[str] = None
    worktree: Optional[str] = None
    hostname: Optional[str] = None
    tracking_backend: str = "null"

    def to_json_dict(self) -> Dict[str, Any]:
        """
        Convert to JSON-serializable dictionary.

        Returns:
            Dictionary ready for JSON serialization
        """
        return asdict(self)

    @classmethod
    def from_json_dict(cls, data: Dict[str, Any]) -> RunSummary:
        """
        Create RunSummary from JSON dictionary.

        Args:
            data: Dictionary loaded from JSON

        Returns:
            RunSummary instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Validate required fields
        required = ["run_id", "started_at_utc", "finished_at_utc", "status"]
        missing = [f for f in required if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        return cls(**data)

    def write_json(self, path: Union[str, Path]) -> None:
        """
        Write summary to JSON file.

        Creates parent directories if needed. Logs warning on failure
        but does not raise (graceful degradation).

        Args:
            path: Target file path
        """
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w") as f:
                json.dump(self.to_json_dict(), f, indent=2)

            logger.info(f"Wrote run summary to {path}")
        except Exception as e:
            logger.warning(f"Failed to write run summary to {path}: {e}")

    @classmethod
    def read_json(cls, path: Union[str, Path]) -> RunSummary:
        """
        Read summary from JSON file.

        Args:
            path: Source file path

        Returns:
            RunSummary instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is invalid or missing required fields
        """
        path = Path(path)

        with open(path) as f:
            data = json.load(f)

        return cls.from_json_dict(data)

    def validate_contract(self, strict: bool = True) -> List[str]:
        """
        Validate that this summary conforms to the contract.

        Args:
            strict: If True, enforce stricter validation rules

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check required fields are non-empty
        if not self.run_id:
            errors.append("run_id cannot be empty")

        if not self.started_at_utc:
            errors.append("started_at_utc cannot be empty")

        if not self.finished_at_utc:
            errors.append("finished_at_utc cannot be empty")

        if not self.status:
            errors.append("status cannot be empty")

        # Validate status values
        valid_statuses = {"FINISHED", "FAILED", "RUNNING", "KILLED"}
        if self.status not in valid_statuses:
            errors.append(f"status must be one of {valid_statuses}, got '{self.status}'")

        # Validate ISO 8601 timestamps
        for field_name in ["started_at_utc", "finished_at_utc"]:
            try:
                datetime.fromisoformat(getattr(self, field_name))
            except (ValueError, TypeError) as e:
                errors.append(f"{field_name} is not valid ISO 8601: {e}")

        # Validate tracking backend
        valid_backends = {"null", "mlflow"}
        if self.tracking_backend not in valid_backends:
            errors.append(
                f"tracking_backend must be one of {valid_backends}, got '{self.tracking_backend}'"
            )

        if strict:
            # Strict mode: enforce type contracts
            if not isinstance(self.tags, dict):
                errors.append("tags must be dict")
            elif not all(isinstance(k, str) and isinstance(v, str) for k, v in self.tags.items()):
                errors.append("all tags keys and values must be strings")

            if not isinstance(self.params, dict):
                errors.append("params must be dict")

            if not isinstance(self.metrics, dict):
                errors.append("metrics must be dict")
            elif not all(isinstance(v, (int, float)) for v in self.metrics.values()):
                errors.append("all metrics values must be numeric")

            if not isinstance(self.artifacts, list):
                errors.append("artifacts must be list")
            elif not all(isinstance(a, str) for a in self.artifacts):
                errors.append("all artifacts must be strings")

        return errors

    def is_valid(self, strict: bool = True) -> bool:
        """
        Check if summary is valid.

        Args:
            strict: If True, enforce stricter validation rules

        Returns:
            True if valid, False otherwise
        """
        return len(self.validate_contract(strict=strict)) == 0
