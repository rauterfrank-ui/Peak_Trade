from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from src.execution.beta_bridge.schema import normalize_beta_exec_v1_event, sort_key_beta_exec_v1

from .canonical import write_json_canonical, write_jsonl_canonical
from .contract import (
    BUNDLE_ROOT_DIRNAME,
    CANON_JSONL_RULE,
    CANON_JSON_RULE,
    CONTRACT_VERSION,
    EVENT_ORDERING_INVARIANT,
)
from .hashing import collect_files_for_hashing, sha256_file, write_sha256sums


@dataclass(frozen=True)
class BuildInputs:
    run_id: str
    events_jsonl_path: Path
    source_mode: str


def _repo_root_from_this_file() -> Path:
    # src/execution/replay_pack/builder.py -> repo root is 4 levels up
    return Path(__file__).resolve().parents[4]


def _discover_events_jsonl(run_dir: Path) -> Optional[Path]:
    # Preferred contract location (Slice 1): logs/execution/execution_events.jsonl
    candidates = [
        run_dir / "logs" / "execution" / "execution_events.jsonl",
        run_dir / "execution_events.jsonl",
        run_dir / "logs" / "execution_events.jsonl",
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            return p
    return None


def _detect_build_inputs(run_dir_or_run_id: Union[str, os.PathLike[str]]) -> BuildInputs:
    s = str(run_dir_or_run_id)
    p = Path(s)
    if p.exists() and p.is_dir():
        events = _discover_events_jsonl(p)
        if events is None:
            raise FileNotFoundError("could not find execution events jsonl under run_dir")
        run_id = _infer_run_id_from_events(events) or p.name
        return BuildInputs(run_id=run_id, events_jsonl_path=events, source_mode="run_dir")

    run_id = s
    repo_root = _repo_root_from_this_file()

    # Deterministic discovery order.
    candidate_dirs = [
        repo_root / "runs" / run_id,
        repo_root / "artifacts" / run_id,
        repo_root / "out" / run_id,
        repo_root / run_id,
        repo_root,
    ]
    for d in candidate_dirs:
        if not d.exists() or not d.is_dir():
            continue
        events = _discover_events_jsonl(d)
        if events is None:
            continue
        # If the events file contains multiple run_ids, filter at export time.
        return BuildInputs(run_id=run_id, events_jsonl_path=events, source_mode="run_id")

    raise FileNotFoundError("could not resolve run_id to an execution events jsonl file")


def _infer_run_id_from_events(events_jsonl: Path) -> Optional[str]:
    try:
        with open(events_jsonl, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                import json

                obj = json.loads(line)
                if isinstance(obj, Mapping) and isinstance(obj.get("run_id"), str):
                    return str(obj["run_id"])
                break
    except Exception:
        return None
    return None


def _git_info(repo_root: Path) -> Dict[str, Any]:
    # Best-effort; must not crash bundle build.
    import subprocess

    sha = "UNKNOWN"
    dirty: Optional[bool] = None
    try:
        sha = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(repo_root))
            .decode("utf-8")
            .strip()
        )
        status = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=str(repo_root)
        ).decode("utf-8")
        dirty = bool(status.strip())
    except Exception:
        sha = "UNKNOWN"
        dirty = None
    return {"commit_sha": sha, "dirty": dirty}


def _env_info() -> Dict[str, Any]:
    import platform

    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": sys.platform,
        "platform_release": platform.release(),
    }


def _event_time_utc_from_ts_sim(ts_sim: int) -> str:
    # Deterministic surrogate: epoch + ts_sim seconds.
    dt = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=int(ts_sim))
    return dt.isoformat()


def _normalize_and_filter_events(
    *,
    events_jsonl_path: Path,
    run_id: str,
    source_mode: str,
) -> List[Dict[str, Any]]:
    import json

    raw: List[Mapping[str, Any]] = []
    with open(events_jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if not isinstance(obj, Mapping):
                continue
            if obj.get("schema_version") != "BETA_EXEC_V1":
                # Replay pack v1 is scoped to Slice-1 deterministic beta events.
                continue
            if source_mode == "run_id":
                if str(obj.get("run_id") or "") != run_id:
                    continue
            raw.append(obj)

    normalized = [normalize_beta_exec_v1_event(e) for e in raw]
    normalized = sorted(normalized, key=sort_key_beta_exec_v1)

    # Add deterministic ordering fields used by replay pack contract.
    out: List[Dict[str, Any]] = []
    for seq, e in enumerate(normalized):
        d = dict(e)
        d["event_time_utc"] = _event_time_utc_from_ts_sim(int(d["ts_sim"]))
        d["seq"] = seq
        out.append(d)
    return out


def _media_type_for_path(relpath: str) -> str:
    if relpath.endswith(".jsonl"):
        return "application/jsonl"
    if relpath.endswith(".json"):
        return "application/json"
    if relpath.endswith(".toml"):
        return "application/toml"
    if relpath.endswith(".txt"):
        return "text/plain"
    return "application/octet-stream"


def build_replay_pack(
    run_dir_or_run_id: Union[str, os.PathLike[str]],
    out_dir: Union[str, os.PathLike[str]],
    *,
    created_at_utc_override: Optional[str] = None,
    include_outputs: bool = False,
) -> Path:
    """
    Export a deterministic replay bundle.

    Args:
        run_dir_or_run_id: either a run directory OR a run_id to discover deterministically
        out_dir: directory that will contain the bundle root directory
        created_at_utc_override: fixed ISO8601 timestamp for deterministic tests
        include_outputs: include expected outputs for invariant checks

    Returns:
        Path to the bundle root directory (named 'replay_pack')
    """
    inputs = _detect_build_inputs(run_dir_or_run_id)
    bundle_root = Path(out_dir) / BUNDLE_ROOT_DIRNAME
    bundle_root.mkdir(parents=True, exist_ok=True)

    # Always write minimal deterministic inputs snapshot (even if we do not have a real config).
    write_json_canonical(
        bundle_root / "inputs" / "config_snapshot.json",
        {"run_id": inputs.run_id, "source_mode": inputs.source_mode},
    )

    # Meta is optional but useful for operator forensics.
    repo_root = _repo_root_from_this_file()
    git = _git_info(repo_root)
    env = _env_info()
    write_json_canonical(bundle_root / "meta" / "git.json", git)
    write_json_canonical(bundle_root / "meta" / "env.json", env)

    events = _normalize_and_filter_events(
        events_jsonl_path=inputs.events_jsonl_path,
        run_id=inputs.run_id,
        source_mode=inputs.source_mode,
    )
    if not events:
        raise ValueError("no BETA_EXEC_V1 events found for run")

    write_jsonl_canonical(bundle_root / "events" / "execution_events.jsonl", events)

    # Optional expected outputs (for --check-outputs).
    if include_outputs:
        from src.execution.ledger.engine import LedgerEngine
        from src.execution.ledger.quantization import parse_symbol

        first_symbol = str(events[0].get("symbol") or "")
        _, quote = parse_symbol(first_symbol)
        eng = LedgerEngine(quote_currency=quote)
        for e in events:
            eng.apply(e)

        fills = [e for e in events if str(e.get("event_type")) == "FILL"]
        write_jsonl_canonical(bundle_root / "outputs" / "expected_fills.jsonl", fills)

        # Positions: stable dict keyed by symbol, values are JSON-safe strings.
        positions = {}
        for sym in sorted(eng.state.positions.keys()):
            pos = eng.state.positions[sym]
            positions[sym] = {
                "quantity": str(pos.quantity),
                "avg_cost": str(pos.avg_cost),
                "fees": str(pos.fees),
                "realized_pnl": str(pos.realized_pnl),
            }
        write_json_canonical(bundle_root / "outputs" / "expected_positions.json", positions)

    # Build manifest contents list (excludes manifest.json and hashes/sha256sums.txt).
    content_relpaths = []
    for p in bundle_root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(bundle_root).as_posix()
        if rel in {"manifest.json", "hashes/sha256sums.txt"}:
            continue
        content_relpaths.append(rel)
    content_relpaths = sorted(content_relpaths)

    contents: List[Dict[str, Any]] = []
    for rel in content_relpaths:
        abs_p = bundle_root / rel
        b = abs_p.stat().st_size
        digest = sha256_file(abs_p)
        contents.append(
            {
                "path": rel,
                "sha256": digest,
                "bytes": int(b),
                "media_type": _media_type_for_path(rel),
            }
        )

    # Deterministic bundle id: sha256 over (run_id + contract + content hashes).
    from .canonical import dumps_canonical
    from .hashing import sha256_bytes

    bundle_id_material = dumps_canonical(
        {
            "contract_version": CONTRACT_VERSION,
            "run_id": inputs.run_id,
            "contents": [{"path": c["path"], "sha256": c["sha256"]} for c in contents],
        }
    ).encode("utf-8")
    bundle_id = sha256_bytes(bundle_id_material)

    # Deterministic created_at_utc:
    created_at_utc = created_at_utc_override or str(events[0]["event_time_utc"])

    manifest = {
        "contract_version": CONTRACT_VERSION,
        "bundle_id": bundle_id,
        "run_id": inputs.run_id,
        "created_at_utc": created_at_utc,
        "peak_trade_git_sha": str(git.get("commit_sha") or "UNKNOWN"),
        "producer": {"tool": "pt_replay_pack", "version": "1.0"},
        "contents": contents,
        "canonicalization": {"json": CANON_JSON_RULE, "jsonl": CANON_JSONL_RULE},
        "invariants": {
            "has_execution_events": True,
            "ordering": EVENT_ORDERING_INVARIANT,
        },
    }
    write_json_canonical(bundle_root / "manifest.json", manifest)

    # hashes/sha256sums.txt covers all files except itself (includes manifest.json).
    relpaths_for_hashing = collect_files_for_hashing(bundle_root)
    write_sha256sums(bundle_root, relpaths_for_hashing)

    return bundle_root
