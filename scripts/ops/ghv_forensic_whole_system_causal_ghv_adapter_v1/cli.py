#!/usr/bin/env python3
"""Offline CLI for WP2-B-A1 graph inspection adapter (AUTHORITY=NONE)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _ensure_repo_on_path() -> None:
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def main() -> int:
    _ensure_repo_on_path()
    parser = argparse.ArgumentParser(description="GHV WP2-B-A1 offline graph inspection")
    parser.add_argument("--wp2a-output-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    from scripts.ops.ghv_forensic_whole_system_causal_ghv_adapter_v1.inspect_graph_v1 import (
        run_offline_graph_inspection_v1,
    )

    result = run_offline_graph_inspection_v1(
        wp2a_output_dir=args.wp2a_output_dir,
        output_dir=args.output_dir,
        repo_root=REPO_ROOT,
    )
    payload = {
        "ok": result.ok,
        "failure_semantic": result.failure_semantic,
        "errors": result.errors,
        "output_dir": str(result.output_dir) if result.output_dir else None,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
