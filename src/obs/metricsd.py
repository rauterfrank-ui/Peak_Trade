from __future__ import annotations

import importlib
import logging
import os
from pathlib import Path
from typing import Optional

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
    Prometheus metricsd (CURRENT runtime detached).

    Never binds a listener. Explicit CLI invocation exits without opening a port.
    """
    del port, multiproc_dir, fail_open
    logging.basicConfig(level=getattr(logging, log_level.upper(), logging.INFO))
    logger.info("metricsd runtime inactive (Prometheus detached); no listener started.")
    return False


def run_forever(
    *,
    port: int = DEFAULT_PORT,
    multiproc_dir: str = DEFAULT_MULTIPROC_DIR,
    fail_open: bool = True,
    log_level: str = "INFO",
) -> int:
    """
    CLI-friendly runner (CURRENT runtime detached): no listener, clean exit.
    """
    del port, multiproc_dir, fail_open
    start_metricsd(log_level=log_level)
    return 0
