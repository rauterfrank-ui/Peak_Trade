#!/usr/bin/env python3
"""OKX multi-window foundation launcher (local Safari slots, idempotent)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ops.okx_multi_window_foundation_v1.config_v1 import (  # noqa: E402
    load_config,
    save_config,
)
from src.ops.okx_multi_window_foundation_v1.launcher_v1 import (  # noqa: E402
    LauncherStop,
    run_launch,
)

DEFAULT_CONFIG = ROOT / "config/ops/okx_multi_window_foundation_v1/foundation_v1.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="OKX Safari multi-window slot launcher v1")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Path to foundation_v1.json",
    )
    parser.add_argument(
        "--no-create",
        action="store_true",
        help="Do not create missing slot windows (fail-closed)",
    )
    parser.add_argument(
        "--no-apply-urls",
        action="store_true",
        help="Skip navigating slot tabs from url_bindings",
    )
    args = parser.parse_args()

    config_path = args.config if args.config.is_absolute() else ROOT / args.config
    try:
        config = load_config(config_path)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "message": str(exc)}))
        return 1

    try:
        result = run_launch(
            config,
            allow_create=not args.no_create,
            apply_urls=not args.no_apply_urls,
        )
    except LauncherStop as exc:
        print(json.dumps({"status": "FAIL", "message": str(exc)}))
        return 1

    save_config(config_path, config)
    print(
        json.dumps(
            {
                "status": result.status,
                "workstation_window_id": result.workstation_window_id,
                "slot_window_ids": result.slot_window_ids,
                "windows_created": result.windows_created,
                "urls_applied": result.urls_applied,
                "message": result.message,
                "config_path": str(config_path),
            },
            ensure_ascii=False,
        )
    )
    return 0 if result.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
