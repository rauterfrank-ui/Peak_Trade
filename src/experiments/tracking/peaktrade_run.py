"""
Peak Trade Run Context Manager
===============================

Context manager for experiment runs with optional MLflow tracking.
Generates run summary JSON for local comparison and reporting.

Configuration precedence: CLI args > ENV vars > defaults
"""

from __future__ import annotations

import logging
import os
import socket
import subprocess
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .run_summary import RunSummary

logger = logging.getLogger(__name__)


class PeakTradeRun:
    """
    Context manager for Peak Trade experiment runs.

    Supports optional MLflow tracking with graceful fallback.
    Always generates a run_summary.json for local comparison.

    Example:
        >>> with PeakTradeRun(
        ...     experiment_name="strategy_sweep",
        ...     run_name="rsi_10_20",
        ...     mlflow_uri="http://localhost:5000",
        ... ) as run:
        ...     run.log_param("fast_period", 10)
        ...     run.log_metric("sharpe", 1.5)
        ...     # Summary JSON written automatically on exit
    """

    def __init__(
        self,
        experiment_name: Optional[str] = None,
        run_name: Optional[str] = None,
        mlflow_uri: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        results_dir: Union[str, Path] = "results",
        enable_mlflow: Optional[bool] = None,
    ):
        """
        Initialize run context.

        Args:
            experiment_name: Name of experiment (overrides MLFLOW_EXPERIMENT_NAME env)
            run_name: Name for this run (optional)
            mlflow_uri: MLflow tracking URI (overrides MLFLOW_TRACKING_URI env)
            tags: Initial tags to apply
            results_dir: Directory for run_summary.json (default: results/)
            enable_mlflow: Explicitly enable/disable MLflow (overrides env)
        """
        self.experiment_name = experiment_name or os.getenv(
            "MLFLOW_EXPERIMENT_NAME", "peak_trade_default"
        )
        self.run_name = run_name
        self.results_dir = Path(results_dir)

        # Configuration precedence: explicit arg > env > default (False)
        if enable_mlflow is not None:
            self.enable_mlflow = enable_mlflow
        else:
            self.enable_mlflow = os.getenv("PEAK_TRADE_MLFLOW_ENABLE", "").lower() in (
                "true",
                "1",
                "yes",
            )

        self.mlflow_uri = mlflow_uri or os.getenv("MLFLOW_TRACKING_URI")

        # Run state
        self.run_id: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.finished_at: Optional[datetime] = None
        self.status: str = "RUNNING"
        self.tags: Dict[str, str] = tags.copy() if tags else {}
        self.params: Dict[str, Union[str, int, float, bool]] = {}
        self.metrics: Dict[str, float] = {}
        self.artifacts: List[str] = []

        # MLflow state
        self.mlflow_available = False
        self.mlflow_run = None

        # Try to import mlflow if enabled
        if self.enable_mlflow:
            try:
                import mlflow

                self.mlflow = mlflow
                self.mlflow_available = True
                logger.info("MLflow available for tracking")
            except ImportError:
                logger.warning(
                    "MLflow tracking requested but not installed. Falling back to null backend."
                )

    def __enter__(self) -> PeakTradeRun:
        """Start run context."""
        self.started_at = datetime.now(timezone.utc)
        self.run_id = str(uuid.uuid4())

        # Start MLflow run if available
        if self.mlflow_available and self.mlflow_uri:
            try:
                self.mlflow.set_tracking_uri(self.mlflow_uri)
                self.mlflow.set_experiment(self.experiment_name)

                self.mlflow_run = self.mlflow.start_run(run_name=self.run_name)
                self.run_id = self.mlflow_run.info.run_id

                # Log initial tags
                if self.tags:
                    self.mlflow.set_tags(self.tags)

                logger.info(f"Started MLflow run: {self.run_id}")
            except Exception as e:
                logger.warning(f"Failed to start MLflow run: {e}. Using null backend.")
                self.mlflow_available = False

        logger.info(f"Started run: {self.run_id}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End run context and write summary."""
        self.finished_at = datetime.now(timezone.utc)

        # Determine final status
        if exc_type is not None:
            self.status = "FAILED"
        else:
            self.status = "FINISHED"

        # End MLflow run if active
        if self.mlflow_available and self.mlflow_run:
            try:
                self.mlflow.end_run(status=self.status)
                logger.info(f"Ended MLflow run: {self.run_id}")
            except Exception as e:
                logger.warning(f"Failed to end MLflow run: {e}")

        # Always write local summary
        self._write_summary()

        logger.info(f"Run {self.run_id} finished with status: {self.status}")

    def log_param(self, key: str, value: Union[str, int, float, bool]) -> None:
        """
        Log a parameter.

        Args:
            key: Parameter name
            value: Parameter value
        """
        self.params[key] = value

        if self.mlflow_available and self.mlflow_run:
            try:
                self.mlflow.log_param(key, value)
            except Exception as e:
                logger.warning(f"Failed to log param to MLflow: {e}")

    def log_params(self, params: Dict[str, Union[str, int, float, bool]]) -> None:
        """
        Log multiple parameters.

        Args:
            params: Dictionary of parameter key-value pairs
        """
        self.params.update(params)

        if self.mlflow_available and self.mlflow_run:
            try:
                self.mlflow.log_params(params)
            except Exception as e:
                logger.warning(f"Failed to log params to MLflow: {e}")

    def log_metric(self, key: str, value: float, step: Optional[int] = None) -> None:
        """
        Log a metric.

        Args:
            key: Metric name
            value: Metric value
            step: Optional step number for time-series metrics
        """
        # Store only the latest value locally
        self.metrics[key] = value

        if self.mlflow_available and self.mlflow_run:
            try:
                self.mlflow.log_metric(key, value, step=step)
            except Exception as e:
                logger.warning(f"Failed to log metric to MLflow: {e}")

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        """
        Log multiple metrics.

        Args:
            metrics: Dictionary of metric key-value pairs
            step: Optional step number for time-series metrics
        """
        self.metrics.update(metrics)

        if self.mlflow_available and self.mlflow_run:
            try:
                self.mlflow.log_metrics(metrics, step=step)
            except Exception as e:
                logger.warning(f"Failed to log metrics to MLflow: {e}")

    def set_tag(self, key: str, value: str) -> None:
        """
        Set a tag.

        Args:
            key: Tag name
            value: Tag value (must be string)
        """
        self.tags[key] = str(value)

        if self.mlflow_available and self.mlflow_run:
            try:
                self.mlflow.set_tag(key, value)
            except Exception as e:
                logger.warning(f"Failed to set tag in MLflow: {e}")

    def set_tags(self, tags: Dict[str, str]) -> None:
        """
        Set multiple tags.

        Args:
            tags: Dictionary of tag key-value pairs
        """
        self.tags.update({k: str(v) for k, v in tags.items()})

        if self.mlflow_available and self.mlflow_run:
            try:
                self.mlflow.set_tags(tags)
            except Exception as e:
                logger.warning(f"Failed to set tags in MLflow: {e}")

    def log_artifact(self, local_path: Union[str, Path]) -> None:
        """
        Log an artifact file.

        Args:
            local_path: Path to artifact file
        """
        local_path = Path(local_path)
        if local_path.exists():
            # Store relative path
            try:
                rel_path = local_path.relative_to(Path.cwd())
            except ValueError:
                rel_path = local_path

            self.artifacts.append(str(rel_path))

            if self.mlflow_available and self.mlflow_run:
                try:
                    self.mlflow.log_artifact(str(local_path))
                except Exception as e:
                    logger.warning(f"Failed to log artifact to MLflow: {e}")
        else:
            logger.warning(f"Artifact not found: {local_path}")

    def _write_summary(self) -> None:
        """Write run summary JSON to results directory."""
        if not self.started_at or not self.finished_at:
            logger.warning("Run timestamps not set, cannot write summary")
            return

        # Collect git context
        git_sha = self._get_git_sha()
        worktree = self._get_worktree_name()
        hostname = socket.gethostname()

        # Determine tracking backend
        tracking_backend = "mlflow" if (self.mlflow_available and self.mlflow_run) else "null"

        # Build summary
        summary = RunSummary(
            run_id=self.run_id,
            started_at_utc=self.started_at.isoformat(),
            finished_at_utc=self.finished_at.isoformat(),
            status=self.status,
            tags=self.tags,
            params=self.params,
            metrics=self.metrics,
            artifacts=self.artifacts,
            git_sha=git_sha,
            worktree=worktree,
            hostname=hostname,
            tracking_backend=tracking_backend,
        )

        # Write to results/run_summary_{run_id}.json
        summary_path = self.results_dir / f"run_summary_{self.run_id}.json"
        summary.write_json(summary_path)

        # Also log as artifact if MLflow is active
        if self.mlflow_available and self.mlflow_run and summary_path.exists():
            try:
                self.mlflow.log_artifact(str(summary_path))
            except Exception as e:
                logger.warning(f"Failed to log summary to MLflow: {e}")

    @staticmethod
    def _get_git_sha() -> Optional[str]:
        """Get current git commit SHA."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return None

    @staticmethod
    def _get_worktree_name() -> Optional[str]:
        """Get git worktree name if in worktree."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            worktree_path = Path(result.stdout.strip())
            return worktree_path.name
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return None
