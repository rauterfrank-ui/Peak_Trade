from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.update_officer_consumer import (  # noqa: E402
    load_notifier_payload,
    render_notifier_text_summary,
)
from src.ops.update_officer_schema import UpdateOfficerSchemaError  # noqa: E402


def _resolve_payload_path(payload: str | None, run_dir: str | None) -> Path:
    if payload and run_dir:
        raise ValueError("Use either --payload or --run-dir, not both.")
    if payload:
        return Path(payload)
    if run_dir:
        return Path(run_dir) / "notifier_payload.json"
    raise ValueError("Missing required input: provide --payload or --run-dir.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render a deterministic Update Officer notifier summary (read-only). "
            "Use explicit --payload or --run-dir only — same resolution semantics as the "
            "WebUI operator trace (no latest-run scan)."
        )
    )
    parser.add_argument(
        "--payload",
        help="Path to notifier_payload.json",
    )
    parser.add_argument(
        "--run-dir",
        help="Path to an Update Officer run directory containing notifier_payload.json",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        payload_path = _resolve_payload_path(args.payload, args.run_dir)
        payload = load_notifier_payload(payload_path)
        summary = render_notifier_text_summary(payload)
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON: {exc}", file=sys.stderr)
        return 2
    except (ValueError, FileNotFoundError, OSError, UpdateOfficerSchemaError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
