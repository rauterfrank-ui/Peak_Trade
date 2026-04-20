#!/usr/bin/env python3
"""
Read-only operator snapshot of adjacent stop / abort signals.

Surfaces side-by-side (no runtime unification):
- process environment: PT_INCIDENT_STOP, PT_FORCE_NO_TRADE, PT_ENABLED, PT_ARMED
- latest ``out/ops/incident_stop_*/incident_stop_state.env`` artifact (if any)
- ``data/kill_switch/state.json`` (same active rule as ops cockpit: state in KILLED, RECOVERING)

Does not write state, does not change kill switch, does not authorize live trading.

Exit codes:
  0 — snapshot emitted
  2 — invalid arguments or unreadable repo root
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONTRACT_ID = "operator_stop_signal_snapshot_v1"

# Aligned with ``scripts/ops/incident_stop_now.sh`` and cockpit incident_state PT_* fields.
PT_STOP_KEYS = (
    "PT_INCIDENT_STOP",
    "PT_FORCE_NO_TRADE",
    "PT_ENABLED",
    "PT_ARMED",
)


def _truthy_env(val: Optional[str]) -> bool:
    if val is None:
        return False
    s = str(val).strip()
    return s not in ("", "0", "false", "False", "no", "NO")


def _snapshot_process_pt() -> Dict[str, Any]:
    return {k: os.environ.get(k) for k in PT_STOP_KEYS}


def _find_latest_incident_stop_state_file(repo_root: Path) -> Optional[Path]:
    """Mirror discovery order in ``ops_cockpit._detect_incident_stop`` (newest dir first)."""
    out_ops = repo_root / "out" / "ops"
    if not out_ops.is_dir():
        return None
    for d in sorted(out_ops.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if d.is_dir() and d.name.startswith("incident_stop_"):
            candidate = d / "incident_stop_state.env"
            if candidate.is_file():
                return candidate
    return None


def _parse_incident_stop_env_file(path: Path, repo_root: Path) -> Dict[str, Any]:
    rel = None
    try:
        rel = str(path.relative_to(repo_root.resolve()))
    except ValueError:
        rel = str(path)
    out: Dict[str, Any] = {
        "status": "ok",
        "path": rel,
        "parsed": None,
        "error": None,
    }
    try:
        parsed: Dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                parsed[k.strip()] = v.strip()
        out["parsed"] = parsed
    except OSError as e:
        out["status"] = "error"
        out["error"] = str(e)
    except UnicodeDecodeError as e:
        out["status"] = "error"
        out["error"] = str(e)
    return out


def _read_kill_switch(repo_root: Path) -> Dict[str, Any]:
    path = repo_root / "data" / "kill_switch" / "state.json"
    try:
        rel = str(path.relative_to(repo_root.resolve()))
    except ValueError:
        rel = "data/kill_switch/state.json"
    if not path.is_file():
        return {
            "status": "unavailable",
            "path": rel,
            "kill_switch_active": None,
            "state": None,
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        state_raw = data.get("state", "")
        state_u = str(state_raw).upper()
        active = state_u in ("KILLED", "RECOVERING")
        return {
            "status": "ok",
            "path": rel,
            "kill_switch_active": active,
            "state": state_raw,
        }
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        return {
            "status": "error",
            "path": rel,
            "kill_switch_active": None,
            "state": None,
            "error": str(e),
        }


def _build_consistency_notes(
    pt_env: Dict[str, Any],
    artifact: Dict[str, Any],
    ks: Dict[str, Any],
) -> List[str]:
    notes: List[str] = []
    env_fnt = _truthy_env(pt_env.get("PT_FORCE_NO_TRADE"))
    ks_active = ks.get("kill_switch_active")
    if ks_active is False and env_fnt:
        notes.append(
            "divergence: kill_switch_active is false but PT_FORCE_NO_TRADE is set in process env"
        )
    if ks_active is True and not env_fnt and not _truthy_env(pt_env.get("PT_INCIDENT_STOP")):
        notes.append(
            "divergence: kill_switch_active is true but PT_FORCE_NO_TRADE / PT_INCIDENT_STOP not set in process env"
        )

    if artifact.get("status") == "ok" and isinstance(artifact.get("parsed"), dict):
        ap = artifact["parsed"]
        art_fnt = _truthy_env(ap.get("PT_FORCE_NO_TRADE"))
        if art_fnt and not env_fnt:
            notes.append(
                "artifact_vs_process: latest incident_stop_state.env sets PT_FORCE_NO_TRADE "
                "but current process env does not (shell may not have sourced that file)"
            )

    if artifact.get("status") == "error":
        notes.append(f"incident_stop_artifact: {artifact.get('error', 'read/parse error')}")

    if ks.get("status") == "error":
        notes.append(f"kill_switch_file: {ks.get('error', 'read error')}")

    return notes


def build_stop_signal_snapshot(repo_root: Path) -> Dict[str, Any]:
    root = repo_root.resolve()
    pt_env = _snapshot_process_pt()
    latest_sf = _find_latest_incident_stop_state_file(root)
    if latest_sf is None:
        artifact: Dict[str, Any] = {
            "status": "none",
            "path": None,
            "parsed": None,
            "error": None,
        }
    else:
        artifact = _parse_incident_stop_env_file(latest_sf, root)
    ks = _read_kill_switch(root)
    notes = _build_consistency_notes(pt_env, artifact, ks)

    ks_a = ks.get("kill_switch_active")
    env_fnt = _truthy_env(pt_env.get("PT_FORCE_NO_TRADE"))
    summary_parts = [
        f"kill_switch_active={ks_a}",
        f"env_PT_FORCE_NO_TRADE={env_fnt}",
    ]
    if artifact.get("status") == "ok":
        summary_parts.append("incident_stop_artifact=present")
    elif artifact.get("status") == "none":
        summary_parts.append("incident_stop_artifact=none")
    else:
        summary_parts.append(f"incident_stop_artifact={artifact.get('status')}")
    if notes:
        summary_parts.append("consistency_notes=see_json")

    return {
        "contract": CONTRACT_ID,
        "repo_root": str(root),
        "process_environment_pt": pt_env,
        "incident_stop_artifact": artifact,
        "kill_switch_file": ks,
        "consistency_notes": notes,
        "summary": "; ".join(summary_parts),
    }


def _print_text(snapshot: Dict[str, Any]) -> None:
    print(snapshot.get("summary", ""))
    print("--- process PT_* ---")
    for k, v in snapshot["process_environment_pt"].items():
        print(f"  {k}={v!r}")
    art = snapshot["incident_stop_artifact"]
    print("--- incident_stop artifact ---")
    print(f"  status={art.get('status')} path={art.get('path')}")
    if art.get("parsed"):
        for k, v in art["parsed"].items():
            print(f"    {k}={v!r}")
    if art.get("error"):
        print(f"  error={art['error']}", file=sys.stderr)
    ks = snapshot["kill_switch_file"]
    print("--- kill_switch state.json ---")
    print(
        f"  status={ks.get('status')} kill_switch_active={ks.get('kill_switch_active')} "
        f"state={ks.get('state')!r}"
    )
    if ks.get("error"):
        print(f"  error={ks['error']}", file=sys.stderr)
    notes = snapshot.get("consistency_notes") or []
    if notes:
        print("--- consistency_notes ---")
        for n in notes:
            print(f"  - {n}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only snapshot of operator stop signals (PT_* env, incident_stop artifact, kill_switch JSON)."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: inferred from script location)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit full snapshot as JSON",
    )
    args = parser.parse_args()
    repo_root = args.repo_root or _REPO_ROOT
    if not repo_root.is_dir():
        print(f"ERR: repo root not a directory: {repo_root}", file=sys.stderr)
        return 2
    try:
        snapshot = build_stop_signal_snapshot(repo_root)
    except Exception as e:
        print(f"ERR: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(snapshot, indent=2))
    else:
        _print_text(snapshot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
