"""
Ingress CLI (Runbook A6): module entrypoint for run_ingress.
Prints absolute paths (feature_view, capsule) one per line; exit 0 on success, nonzero on error.
Pointer-only: no payload/raw/transcript in outputs.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.ingress.orchestrator.ingress_orchestrator import OrchestratorConfig, run_ingress


def _default_run_id() -> str:
    return f"{int(time.time())}-{os.getpid()}"


def _parse_labels(label_args: List[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for s in label_args:
        if "=" in s:
            k, _, v = s.partition("=")
            out[k.strip()] = v.strip()
    return out


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run ingress pipeline (A2→A4).")
    parser.add_argument(
        "--run-id",
        default=_default_run_id(),
        help="Run identifier (default: timestamp-pid).",
    )
    parser.add_argument(
        "--input-jsonl",
        default="",
        metavar="PATH",
        help="Path to input JSONL (optional; empty ok).",
    )
    parser.add_argument(
        "--base-dir",
        default="out/ops",
        metavar="PATH",
        help="Base directory for views and capsules (default: out/ops).",
    )
    parser.add_argument(
        "--label",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Repeatable label (e.g. --label env=prod).",
    )
    args = parser.parse_args(argv)

    config = OrchestratorConfig(
        base_dir=Path(args.base_dir),
        run_id=args.run_id,
        input_jsonl_path=args.input_jsonl or "",
    )
    labels = _parse_labels(args.label) if args.label else None

    try:
        feature_view_path, capsule_path = run_ingress(config, labels=labels)
        print(feature_view_path.resolve())
        print(capsule_path.resolve())
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    sys.exit(main())
