from __future__ import annotations

from pathlib import Path

import pytest


def test_metricsd_build_registry_no_crash(tmp_path: Path) -> None:
    """
    With prometheus_client installed, building a multiprocess registry should not crash.
    """
    try:
        import prometheus_client  # noqa: F401
    except Exception:
        pytest.skip("prometheus_client not installed")

    from src.obs import metricsd

    mp = tmp_path / "prom_multiproc"
    mp.mkdir(parents=True, exist_ok=True)

    # Ensure env is set; registry build should succeed.
    metricsd._maybe_set_multiproc_env(mp)  # noqa: SLF001 (test-only)
    reg = metricsd.build_multiprocess_registry(multiproc_dir=mp)
    assert reg is not None


def test_metricsd_fail_open_when_prometheus_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from src.obs import metricsd

    def _boom(name: str):
        raise ImportError("no prometheus_client")

    monkeypatch.setattr(metricsd.importlib, "import_module", _boom)
    ok = metricsd.start_metricsd(
        port=9111, multiproc_dir=str(tmp_path / "prom_multiproc"), fail_open=True
    )
    assert ok is False
