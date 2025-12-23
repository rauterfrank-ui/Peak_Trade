from __future__ import annotations

from dataclasses import dataclass
import importlib
import json
from typing import Any, Dict, Mapping, Optional, Protocol


class Tracker(Protocol):
    """
    Minimal Tracking Interface for Peak_Trade vNext.

    Design goals:
    - Safe-by-default: when tracking is disabled, caller passes tracker=None.
    - No behavior change: tracking must not mutate trading results.
    - Optional deps: concrete backends (e.g., MLflow) are imported lazily.
    """

    def start_run(self, run_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None) -> None: ...
    def log_params(self, params: Mapping[str, Any]) -> None: ...
    def log_metrics(self, metrics: Mapping[str, float]) -> None: ...
    def log_text(self, name: str, text: str) -> None: ...
    def log_json(self, name: str, payload: Any) -> None: ...
    def log_artifact(self, path: str, artifact_path: Optional[str] = None) -> None: ...
    def end_run(self, status: str = "FINISHED") -> None: ...


@dataclass(frozen=True)
class TrackingConfig:
    enabled: bool = False
    backend: str = "noop"  # "noop" | "mlflow"
    # MLflow settings (only used when backend == "mlflow")
    mlflow_tracking_uri: Optional[str] = None
    mlflow_experiment_name: Optional[str] = None
    mlflow_tags: Optional[Dict[str, str]] = None


class NoopTracker:
    def start_run(self, run_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None) -> None:
        return

    def log_params(self, params: Mapping[str, Any]) -> None:
        return

    def log_metrics(self, metrics: Mapping[str, float]) -> None:
        return

    def log_text(self, name: str, text: str) -> None:
        return

    def log_json(self, name: str, payload: Any) -> None:
        return

    def log_artifact(self, path: str, artifact_path: Optional[str] = None) -> None:
        return

    def end_run(self, status: str = "FINISHED") -> None:
        return


class MLflowTracker:
    """
    Optional MLflow backend.
    Import is lazy; raise clean error if MLflow not installed.
    """

    def __init__(self, cfg: TrackingConfig):
        self._cfg = cfg
        self._mlflow = _import_mlflow_or_raise()
        self._active = False

        if cfg.mlflow_tracking_uri:
            self._mlflow.set_tracking_uri(cfg.mlflow_tracking_uri)

        if cfg.mlflow_experiment_name:
            self._mlflow.set_experiment(cfg.mlflow_experiment_name)

    def start_run(self, run_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None) -> None:
        if self._active:
            return
        all_tags: Dict[str, str] = {}
        if self._cfg.mlflow_tags:
            all_tags.update(self._cfg.mlflow_tags)
        if tags:
            all_tags.update(tags)
        self._mlflow.start_run(run_name=run_name)
        if all_tags:
            self._mlflow.set_tags(all_tags)
        self._active = True

    def log_params(self, params: Mapping[str, Any]) -> None:
        if not self._active:
            return
        # mlflow expects values to be str/int/float/bool
        safe = {k: _stringify_param(v) for k, v in params.items()}
        self._mlflow.log_params(safe)

    def log_metrics(self, metrics: Mapping[str, float]) -> None:
        if not self._active:
            return
        safe = {k: float(v) for k, v in metrics.items()}
        self._mlflow.log_metrics(safe)

    def log_text(self, name: str, text: str) -> None:
        if not self._active:
            return
        # mlflow supports logging text via artifacts (>=2.x), but keep simple and robust:
        import tempfile
        from pathlib import Path

        tmpdir = Path(tempfile.mkdtemp(prefix="peak_trade_mlflow_text_"))
        p = tmpdir / name
        p.write_text(text, encoding="utf-8")
        self._mlflow.log_artifact(str(p))

    def log_json(self, name: str, payload: Any) -> None:
        if not self._active:
            return
        text = json.dumps(_to_jsonable(payload), indent=2, sort_keys=True)
        self.log_text(name, text)

    def log_artifact(self, path: str, artifact_path: Optional[str] = None) -> None:
        if not self._active:
            return
        if artifact_path:
            self._mlflow.log_artifact(path, artifact_path=artifact_path)
        else:
            self._mlflow.log_artifact(path)

    def end_run(self, status: str = "FINISHED") -> None:
        if not self._active:
            return
        # mlflow.end_run accepts status in recent versions; if older, it will ignore.
        try:
            self._mlflow.end_run(status=status)
        except TypeError:
            self._mlflow.end_run()
        self._active = False


def build_tracking_config(cfg: Any) -> TrackingConfig:
    """
    Build TrackingConfig from a config object/dict.
    Works with nested dicts or objects exposing attributes.

    Expected TOML shape:

    [tracking]
    enabled = false
    backend = "noop"

    [tracking.mlflow]
    tracking_uri = "file:./.mlruns"
    experiment_name = "peak_trade"
    tags = { project="Peak_Trade" }
    """
    enabled = bool(_cfg_get(cfg, "tracking.enabled", False))
    backend = str(_cfg_get(cfg, "tracking.backend", "noop")).strip().lower()

    mlflow_tracking_uri = _cfg_get(cfg, "tracking.mlflow.tracking_uri", None)
    mlflow_experiment_name = _cfg_get(cfg, "tracking.mlflow.experiment_name", None)
    mlflow_tags = _cfg_get(cfg, "tracking.mlflow.tags", None)

    if isinstance(mlflow_tags, Mapping):
        mlflow_tags = {str(k): str(v) for k, v in mlflow_tags.items()}
    else:
        mlflow_tags = None

    return TrackingConfig(
        enabled=enabled,
        backend=backend,
        mlflow_tracking_uri=str(mlflow_tracking_uri) if mlflow_tracking_uri else None,
        mlflow_experiment_name=str(mlflow_experiment_name) if mlflow_experiment_name else None,
        mlflow_tags=mlflow_tags,
    )


def build_tracker_from_config(cfg: Any) -> Optional[Tracker]:
    """
    Factory:
    - enabled=false -> None
    - enabled=true, backend=noop -> NoopTracker
    - enabled=true, backend=mlflow -> MLflowTracker (optional dep)
    """
    tc = build_tracking_config(cfg)
    if not tc.enabled:
        return None

    if tc.backend == "noop":
        return NoopTracker()

    if tc.backend == "mlflow":
        return MLflowTracker(tc)

    raise ValueError(f"Unknown tracking.backend={tc.backend!r}. Expected 'noop' or 'mlflow'.")


# -------------------------
# helpers
# -------------------------

def _import_mlflow_or_raise():
    if importlib.util.find_spec("mlflow") is None:
        raise RuntimeError(
            "MLflow backend requested but 'mlflow' is not installed. "
            "Install optional extras (e.g. pip install -e '.[mlflow]') and retry."
        )
    return importlib.import_module("mlflow")


def _stringify_param(v: Any) -> Any:
    if v is None:
        return "null"
    if isinstance(v, (str, int, float, bool)):
        return v
    return str(v)


def _to_jsonable(obj: Any) -> Any:
    # best-effort conversion for config snapshots
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Mapping):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_jsonable(x) for x in obj]
    # dataclasses / objects with dict
    d = getattr(obj, "__dict__", None)
    if isinstance(d, dict):
        return {str(k): _to_jsonable(v) for k, v in d.items()}
    return str(obj)


def _cfg_get(cfg: Any, path: str, default: Any) -> Any:
    """
    Robust getter for nested config:
    - dict style: cfg["tracking"]["enabled"]
    - attribute style: cfg.tracking.enabled
    - mixed is okay

    path uses dot-notation, e.g. "tracking.mlflow.tags"
    """
    parts = path.split(".")
    cur: Any = cfg
    for p in parts:
        if cur is None:
            return default

        if isinstance(cur, Mapping):
            if p in cur:
                cur = cur[p]
                continue
            return default

        # attribute style
        if hasattr(cur, p):
            cur = getattr(cur, p)
            continue

        return default

    return cur
