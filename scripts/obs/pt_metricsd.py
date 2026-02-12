#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.obs.metricsd import DEFAULT_MULTIPROC_DIR, DEFAULT_PORT, run_forever


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Peak_Trade metricsd (Prometheus multiprocess exporter)"
    )
    p.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind (default: 9111)")
    p.add_argument(
        "--multiproc-dir",
        default=DEFAULT_MULTIPROC_DIR,
        help="Multiprocess directory for prometheus_client (default: .ops_local/prom_multiproc)",
    )
    p.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)",
    )
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    return run_forever(
        port=int(args.port),
        multiproc_dir=str(args.multiproc_dir),
        log_level=str(args.log_level),
        fail_open=True,
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
