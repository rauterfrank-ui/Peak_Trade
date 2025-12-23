from __future__ import annotations

import importlib
import pytest

from src.core.tracking import (
    NoopTracker,
    build_tracking_config,
    build_tracker_from_config,
)


def test_noop_tracker_is_safe():
    t = NoopTracker()
    t.start_run(run_name="x", tags={"a": "b"})
    t.log_params({"p": 1, "q": "x"})
    t.log_metrics({"m": 1.23})
    t.log_text("note.txt", "hello")
    t.log_json("cfg.json", {"a": 1})
    t.log_artifact("/tmp/does-not-exist")  # noop must not fail
    t.end_run(status="FINISHED")


def test_build_tracker_disabled_returns_none():
    cfg = {"tracking": {"enabled": False, "backend": "noop"}}
    t = build_tracker_from_config(cfg)
    assert t is None


def test_build_tracker_noop_enabled_returns_noop():
    cfg = {"tracking": {"enabled": True, "backend": "noop"}}
    t = build_tracker_from_config(cfg)
    assert t is not None
    assert t.__class__.__name__ == "NoopTracker"


def test_build_tracker_mlflow_missing_dep_raises_cleanly():
    cfg = {"tracking": {"enabled": True, "backend": "mlflow"}}

    if importlib.util.find_spec("mlflow") is not None:
        pytest.skip("mlflow is installed in this environment; skip missing-dep test")

    with pytest.raises(RuntimeError) as e:
        build_tracker_from_config(cfg)
    assert "mlflow" in str(e.value).lower()
    assert "install" in str(e.value).lower()


def test_build_tracking_config_reads_mlflow_section():
    cfg = {
        "tracking": {
            "enabled": True,
            "backend": "mlflow",
            "mlflow": {
                "tracking_uri": "file:./.mlruns",
                "experiment_name": "peak_trade",
                "tags": {"project": "Peak_Trade"},
            },
        }
    }
    tc = build_tracking_config(cfg)
    assert tc.enabled is True
    assert tc.backend == "mlflow"
    assert tc.mlflow_tracking_uri == "file:./.mlruns"
    assert tc.mlflow_experiment_name == "peak_trade"
    assert tc.mlflow_tags == {"project": "Peak_Trade"}

