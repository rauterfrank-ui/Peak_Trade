from __future__ import annotations

import importlib
import logging
import os
import time
from pathlib import Path
from typing import Optional

from src.obs.metrics_config import get_metrics_port
from src.ops.net.ports import ensure_tcp_port_free

logger = logging.getLogger(__name__)


DEFAULT_PORT = 9111
DEFAULT_MULTIPROC_DIR = ".ops_local/prom_multiproc"


def _safe_clear_multiproc_dir(multiproc_dir: Path) -> None:
    """
    Clear multiprocess metrics files.

    Only the daemon should do this (workers must not). This is a best-effort helper
    and will never raise.
    """
    try:
        mp = multiproc_dir.resolve()
        # Safety guard: refuse to delete in suspicious locations.
        if str(mp) in {"/", str(Path.home())}:
            logger.warning("Refusing to clear unsafe multiproc dir: %s", mp)
            return
        if mp.name not in {"prom_multiproc", "prometheus_multiproc"}:
            logger.warning("Refusing to clear unexpected multiproc dir name: %s", mp)
            return
        if not mp.exists():
            return
        if not mp.is_dir():
            logger.warning("Multiproc path is not a directory: %s", mp)
            return

        for p in mp.iterdir():
            if p.is_file():
                try:
                    p.unlink()
                except Exception:
                    logger.debug("Failed to unlink multiproc file: %s", p, exc_info=True)
    except Exception:
        logger.debug("Failed to clear multiproc dir (ignored).", exc_info=True)


def _maybe_set_multiproc_env(multiproc_dir: Path) -> None:
    # PROMETHEUS_MULTIPROC_DIR must be set for multiprocess mode.
    os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", str(multiproc_dir))


def build_multiprocess_registry(*, multiproc_dir: Path):
    """
    Build a CollectorRegistry backed by MultiProcessCollector.

    This helper is testable without binding a port.
    """
    prom = importlib.import_module("prometheus_client")
    multiproc = importlib.import_module("prometheus_client.multiprocess")

    registry = prom.CollectorRegistry()
    multiproc.MultiProcessCollector(registry)  # type: ignore[attr-defined]
    return registry


def start_metricsd(
    *,
    port: int = DEFAULT_PORT,
    multiproc_dir: str = DEFAULT_MULTIPROC_DIR,
    fail_open: bool = True,
    log_level: str = "INFO",
) -> bool:
    """
    Start the Always-on Prometheus exporter daemon (Mode B).

    - Exposes /metrics on port (default: 9111)
    - Uses prometheus_client multiprocess mode (PROMETHEUS_MULTIPROC_DIR)
    - Clears the multiproc dir on daemon start (best-effort; daemon only)
    - Fail-open when prometheus_client is unavailable
    """
    try:
        logging.basicConfig(level=getattr(logging, log_level.upper(), logging.INFO))
        mp = Path(multiproc_dir)
        mp.mkdir(parents=True, exist_ok=True)
        _safe_clear_multiproc_dir(mp)
        _maybe_set_multiproc_env(mp)

        prom = importlib.import_module("prometheus_client")
        registry = build_multiprocess_registry(multiproc_dir=mp)

        # start_http_server runs in a background thread.
        prom.start_http_server(int(port), registry=registry)  # type: ignore[attr-defined]
        logger.info("metricsd started: port=%s multiproc_dir=%s", port, str(mp))
        return True
    except Exception:
        if not fail_open:
            raise
        logger.warning("metricsd failed to start (ignored).", exc_info=True)
        return False


def run_forever(
    *,
    port: int = DEFAULT_PORT,
    multiproc_dir: str = DEFAULT_MULTIPROC_DIR,
    fail_open: bool = True,
    log_level: str = "INFO",
) -> int:
    """
    CLI-friendly runner: start metricsd and block forever.
    """
    port = get_metrics_port(port)
    ensure_tcp_port_free(port, context="metricsd")
    ok = start_metricsd(
        port=port,
        multiproc_dir=multiproc_dir,
        fail_open=fail_open,
        log_level=log_level,
    )
    if not ok:
        return 2
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        return 0
