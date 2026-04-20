#!/usr/bin/env python3
"""
Bounded-pilot operator preflight packet (read-only orchestration).

Orchestrates existing entrypoints only:
- ``scripts/ops/check_bounded_pilot_readiness.run_bounded_pilot_readiness``
- ``scripts/ops/snapshot_operator_stop_signals.build_stop_signal_snapshot``

Emits one fixed JSON object for operators. No new gate semantics, no state writes,
no live authorization.

Exit codes:
  0 — readiness GREEN and stop-signal snapshot has no hard read/parse errors
  1 — blocked (readiness not GREEN and/or stop-signal artifact/KS file in error)
  2 — orchestration / unexpected failure building the packet
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONTRACT_ID = "bounded_pilot_operator_preflight_packet_v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _try_git_head(repo_root: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if out.returncode != 0:
            return None
        line = (out.stdout or "").strip()
        return line or None
    except (OSError, subprocess.SubprocessError):
        return None


def _stop_snapshot_hard_ok(snapshot: dict[str, Any]) -> tuple[bool, list[str]]:
    """True when no read/parse ``error`` status on wired stop-signal sources."""
    blocked: list[str] = []
    art = snapshot.get("incident_stop_artifact") or {}
    if art.get("status") == "error":
        blocked.append(
            "stop_signal_snapshot.incident_stop_artifact: error "
            f"({art.get('error') or 'read/parse failure'})"
        )
    ks = snapshot.get("kill_switch_file") or {}
    if ks.get("status") == "error":
        blocked.append(
            "stop_signal_snapshot.kill_switch_file: error "
            f"({ks.get('error') or 'read/parse failure'})"
        )
    return (len(blocked) == 0, blocked)


def build_operator_preflight_packet(
    repo_root: Path,
    config_path: Path,
    *,
    run_tests: bool = False,
) -> tuple[dict[str, Any], int]:
    """
    Build the packet dict and intended exit code (0/1/2).

    Always runs readiness and stop snapshot when possible so partial failures stay visible.
    """
    from scripts.ops.check_bounded_pilot_readiness import run_bounded_pilot_readiness
    from scripts.ops.snapshot_operator_stop_signals import build_stop_signal_snapshot

    meta: dict[str, Any] = {
        "generated_at_utc": _utc_now_iso(),
        "repo_root": str(repo_root.resolve()),
        "git_head": _try_git_head(repo_root),
    }

    readiness_bundle: dict[str, Any]
    readiness_ok: bool
    try:
        readiness_ok, readiness_bundle = run_bounded_pilot_readiness(
            repo_root,
            config_path,
            run_tests=run_tests,
        )
    except Exception as e:
        packet = {
            "contract": CONTRACT_ID,
            "metadata": meta,
            "bounded_pilot_readiness": {
                "contract": "bounded_pilot_readiness_v1",
                "ok": False,
                "orchestrator_error": str(e),
            },
            "stop_signal_snapshot": None,
            "summary": {
                "readiness_ok": False,
                "stop_snapshot_ok": False,
                "packet_ok": False,
                "blocked": [f"bounded_pilot_readiness: exception ({e})"],
                "notes": [],
            },
        }
        return packet, 2

    stop_snapshot: dict[str, Any] | None = None
    stop_ok = False
    stop_blocked: list[str] = []
    notes: list[str] = []
    stop_build_exc: str | None = None
    try:
        stop_snapshot = build_stop_signal_snapshot(repo_root)
        stop_ok, stop_blocked = _stop_snapshot_hard_ok(stop_snapshot)
        snap_notes = stop_snapshot.get("consistency_notes") or []
        if isinstance(snap_notes, list):
            notes.extend(str(x) for x in snap_notes)
    except Exception as e:
        stop_build_exc = str(e)
        stop_snapshot = {
            "contract": "operator_stop_signal_snapshot_v1",
            "orchestrator_error": stop_build_exc,
        }
        stop_ok = False
        stop_blocked = [f"stop_signal_snapshot: exception ({stop_build_exc})"]

    blocked: list[str] = []
    if not readiness_ok:
        rb = readiness_bundle.get("blocked_at")
        msg = readiness_bundle.get("message") or "readiness not GREEN"
        blocked.append(f"bounded_pilot_readiness: {msg}" + (f" (at={rb})" if rb else ""))
    blocked.extend(stop_blocked)

    packet_ok = bool(readiness_ok and stop_ok and stop_build_exc is None)

    packet = {
        "contract": CONTRACT_ID,
        "metadata": meta,
        "bounded_pilot_readiness": readiness_bundle,
        "stop_signal_snapshot": stop_snapshot,
        "summary": {
            "readiness_ok": readiness_ok,
            "stop_snapshot_ok": stop_ok,
            "packet_ok": packet_ok,
            "blocked": blocked,
            "notes": notes,
        },
    }

    if stop_build_exc is not None:
        return packet, 2
    if not readiness_ok:
        return packet, 1
    if not stop_ok:
        return packet, 1
    return packet, 0


def _print_text(packet: dict[str, Any], *, exit_code: int) -> None:
    s = packet.get("summary") or {}
    print(
        f"packet_ok={s.get('packet_ok')} readiness_ok={s.get('readiness_ok')} "
        f"stop_snapshot_ok={s.get('stop_snapshot_ok')} exit={exit_code}"
    )
    for b in s.get("blocked") or []:
        print(f"  BLOCKED: {b}", file=sys.stderr)
    notes = s.get("notes") or []
    if notes:
        print("--- notes ---")
        for n in notes:
            print(f"  - {n}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Emit a single bounded-pilot operator preflight JSON packet "
            "(read-only; orchestrates readiness + stop-signal snapshot)."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit full packet as JSON on stdout",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repo root (default: inferred from script location)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Config path (default: PEAK_TRADE_CONFIG_PATH or config/config.toml)",
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Pass through to bounded pilot readiness: run baseline pytest (slow)",
    )
    args = parser.parse_args()

    from scripts.ops.check_bounded_pilot_readiness import resolve_bounded_pilot_config_path

    repo_root = args.repo_root or (_REPO_ROOT if _REPO_ROOT.is_dir() else Path.cwd())
    if not repo_root.is_dir():
        err = {
            "contract": CONTRACT_ID,
            "error": f"repo root not a directory: {repo_root}",
        }
        print(json.dumps(err, indent=2))
        return 2

    config_path = resolve_bounded_pilot_config_path(repo_root, args.config)

    try:
        packet, code = build_operator_preflight_packet(
            repo_root,
            config_path,
            run_tests=args.run_tests,
        )
    except Exception as e:
        fallback = {
            "contract": CONTRACT_ID,
            "error": str(e),
        }
        print(json.dumps(fallback, indent=2))
        return 2

    if args.json:
        print(json.dumps(packet, indent=2))
    else:
        _print_text(packet, exit_code=code)

    return code


if __name__ == "__main__":
    raise SystemExit(main())
