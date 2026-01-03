"""
Tracking Abstraction (Noop + optional MLflow)

Ziel:
- Repo muss importierbar bleiben, auch wenn MLflow NICHT installiert ist.
- Tests erwarten: core.tracking.{NoopTracker, MLflowTracker, build_tracker_from_config,
  log_backtest_metadata, log_backtest_artifacts}
"""

from __future__ import annotations

import json
import os
import warnings
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Union


JsonLike = Union[Mapping[str, Any], Dict[str, Any]]


def _as_dict(obj: Any) -> Dict[str, Any]:
    """Best-effort: extrahiert eine raw/config dict View aus PeakConfig oder Mapping."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, Mapping):
        return dict(obj)
    # PeakConfig(raw=...) Pattern
    raw = getattr(obj, "raw", None)
    if isinstance(raw, Mapping):
        return dict(raw)
    # Fallback: __dict__
    d = getattr(obj, "__dict__", None)
    if isinstance(d, Mapping):
        return dict(d)
    return {}


def _flatten(prefix: str, value: Any, out: Dict[str, str]) -> None:
    """Flatten nested dicts into dot-keys and cast values to string (MLflow params need str)."""
    if isinstance(value, Mapping):
        for k, v in value.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            _flatten(key, v, out)
        return
    if isinstance(value, (list, tuple)):
        # stable-ish representation
        out[prefix] = json.dumps(value, ensure_ascii=False)
        return
    if value is None:
        out[prefix] = "null"
        return
    out[prefix] = str(value)


class NoopTracker:
    """No-op Tracker: akzeptiert Calls, macht nichts, wirft keine Exceptions."""

    def __init__(self) -> None:
        self._run_started: bool = False
        self._run_id: Optional[str] = None

    @property
    def tracking_uri(self) -> Optional[str]:
        return None

    @property
    def experiment_name(self) -> Optional[str]:
        return None

    def start_run(self, run_name: str = "run") -> None:
        self._run_started = True
        # deterministisch genug für noop
        self._run_id = "noop"

    def end_run(self) -> None:
        self._run_started = False
        self._run_id = None

    def log_params(self, params: Mapping[str, Any]) -> None:
        return None

    def log_metrics(self, metrics: Mapping[str, Any], step: Optional[int] = None) -> None:
        return None

    def set_tags(self, tags: Mapping[str, Any]) -> None:
        return None

    def log_artifact(self, path: str, artifact_path: Optional[str] = None) -> None:
        return None


class MLflowTracker:
    """
    MLflow Tracker (optional dependency).

    Importiert mlflow erst bei Instanziierung, damit 'core.tracking' ohne mlflow importierbar bleibt.
    """

    def __init__(
        self,
        tracking_uri: str,
        experiment_name: str = "Peak_Trade",
        auto_start_run: bool = False,
        run_name: str = "run",
    ) -> None:
        try:
            import mlflow  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("MLflowTracker erfordert 'mlflow'(pip install mlflow).") from e

        self._mlflow = mlflow
        self.tracking_uri = tracking_uri
        self.experiment_name = experiment_name
        self.auto_start_run = auto_start_run
        self.run_name = run_name

        self._mlflow.set_tracking_uri(self.tracking_uri)
        self._mlflow.set_experiment(self.experiment_name)

        self._active_run = None
        if self.auto_start_run:
            self.start_run(self.run_name)

    def start_run(self, run_name: str | None = None) -> None:
        rn = run_name or self.run_name
        self._active_run = self._mlflow.start_run(run_name=rn)

    def end_run(self) -> None:
        try:
            self._mlflow.end_run()
        finally:
            self._active_run = None

    def log_params(self, params):
        if params:
            self._mlflow.log_params(dict(params))

    def log_metrics(self, metrics, step=None):
        if metrics:
            self._mlflow.log_metrics(dict(metrics), step=step)

    def set_tags(self, tags):
        if tags:
            self._mlflow.set_tags(dict(tags))

    def log_artifact(self, path: str, artifact_path: str | None = None) -> None:
        self._mlflow.log_artifact(path, artifact_path=artifact_path)


def build_tracker_from_config(cfg):
    """
    Factory für Tracker aus einer (toleranten) Config-Mapping.

    Erwartungen aus Tests:
      - muss ohne mlflow importierbar sein (default -> NoopTracker)
      - mlflow erst bei Instanziierung verwenden (MLflowTracker importiert mlflow lazy)

    Unterstützte Patterns (alles optional):
      - type / tracker / tracker_type / backend: "noop" (default) | "mlflow"
      - enabled / disabled: bool
      - mlflow: {tracking_uri, experiment_name, auto_start_run, run_name}
        oder top-level keys: tracking_uri, experiment_name, auto_start_run, run_name
    """
    if cfg is None:
        return NoopTracker()

    # tolerant: akzeptiere auch Objekte mit dict()-ähnlichem Interface
    try:
        cfg_map = dict(cfg)
    except Exception:
        return NoopTracker()

    enabled = cfg_map.get("enabled", None)
    disabled = cfg_map.get("disabled", None)
    if enabled is False or disabled is True:
        return NoopTracker()

    t = (
        cfg_map.get("type")
        or cfg_map.get("tracker")
        or cfg_map.get("tracker_type")
        or cfg_map.get("backend")
        or "noop"
    )
    if isinstance(t, str):
        t_norm = t.strip().lower()
    else:
        t_norm = "noop"

    if t_norm in ("noop", "none", "null", "", "off", "disabled"):
        return NoopTracker()

    if t_norm in ("mlflow", "ml-flow"):
        mlcfg = cfg_map.get("mlflow", None)
        if isinstance(mlcfg, dict):
            tracking_uri = (
                mlcfg.get("tracking_uri") or mlcfg.get("uri") or mlcfg.get("trackingUrl") or ""
            )
            experiment_name = (
                mlcfg.get("experiment_name") or mlcfg.get("experiment") or "Peak_Trade"
            )
            auto_start_run = bool(mlcfg.get("auto_start_run", False))
            run_name = mlcfg.get("run_name") or mlcfg.get("run") or "run"
        else:
            tracking_uri = (
                cfg_map.get("tracking_uri")
                or cfg_map.get("uri")
                or cfg_map.get("trackingUrl")
                or ""
            )
            experiment_name = (
                cfg_map.get("experiment_name") or cfg_map.get("experiment") or "Peak_Trade"
            )
            auto_start_run = bool(cfg_map.get("auto_start_run", False))
            run_name = cfg_map.get("run_name") or cfg_map.get("run") or "run"

        # MLflowTracker importiert mlflow erst in __init__ (lazy). Ohne mlflow -> RuntimeError (ok; Tests skippen dann).
        return MLflowTracker(
            tracking_uri=str(tracking_uri),
            experiment_name=str(experiment_name),
            auto_start_run=bool(auto_start_run),
            run_name=str(run_name),
        )

    # unknown -> safe default
    return NoopTracker()


def log_backtest_metadata(tracker, *, config=None, result=None, tags=None, **kwargs) -> None:
    """
    Toleranter Helper: schreibt Metadaten (params/metrics/tags) an einen Tracker.
    Darf NIE crashen (Noop-safe). Keine harten Abhängigkeiten.
    """
    if tracker is None:
        return

    try:
        # params aus config (nur wenn Mapping-ähnlich)
        params = None
        if config is not None:
            try:
                cfg_map = dict(config)
                params = {str(k): v for k, v in cfg_map.items()}
            except Exception:
                params = None

        if params and hasattr(tracker, "log_params"):
            try:
                tracker.log_params(params)
            except Exception:
                pass

        # metrics aus result.stats (nur numerische)
        if result is not None and hasattr(tracker, "log_metrics"):
            try:
                stats = getattr(result, "stats", None)
                if isinstance(stats, dict):
                    metrics = {}
                    for k, v in stats.items():
                        if isinstance(v, (int, float)) and not isinstance(v, bool):
                            metrics[str(k)] = v
                    if metrics:
                        tracker.log_metrics(metrics, step=None)
            except Exception:
                pass

        # tags
        if tags and hasattr(tracker, "set_tags"):
            try:
                tracker.set_tags(dict(tags))
            except Exception:
                pass

    except Exception:
        # hard guarantee: never crash
        return


def log_backtest_artifacts(tracker, *, result=None, artifacts_dir=None) -> None:
    """
    Toleranter Helper: schreibt Stats/Equity als Dateien und loggt sie als Artifacts.
    Darf NIE crashen. Layout ist absichtlich tolerant, weil `result` projektweit variieren kann.
    """
    if tracker is None or result is None:
        return

    try:
        from pathlib import Path as _Path
        import json as _json
    except Exception:
        return

    base = _Path(artifacts_dir) if artifacts_dir is not None else _Path(".tmp_backtest_artifacts")
    try:
        base.mkdir(parents=True, exist_ok=True)
    except Exception:
        return

    # stats.json
    try:
        stats = getattr(result, "stats", None)
        if isinstance(stats, dict):
            fp = base / "stats.json"
            fp.write_text(_json.dumps(dict(stats), ensure_ascii=False, indent=2), encoding="utf-8")
            if hasattr(tracker, "log_artifact"):
                try:
                    tracker.log_artifact(str(fp))
                except Exception:
                    pass
    except Exception:
        pass

    # equity_curve.csv
    try:
        eq = getattr(result, "equity_curve", None)
        if eq is not None and hasattr(eq, "to_csv"):
            fp = base / "equity_curve.csv"
            try:
                eq.to_csv(fp)  # pandas Series/DataFrame
            except Exception:
                # fallback: string dump
                fp.write_text(str(eq), encoding="utf-8")
            if hasattr(tracker, "log_artifact"):
                try:
                    tracker.log_artifact(str(fp))
                except Exception:
                    pass
    except Exception:
        pass
