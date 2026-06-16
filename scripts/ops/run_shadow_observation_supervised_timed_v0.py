#!/usr/bin/env python3
"""Supervised timed observer v0: explicit manifest → combined local Shadow Observation evidence (no runtime).

Finite operator-invoked batch only. Not a daemon, scheduler, or network client. Cadence fields are
metadata for the harness; no wall-clock timing or sleep is performed.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Set, Tuple, Union, cast

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.shadow_no_order_proof.observation_harness_v0 import (  # noqa: E402
    ShadowObservationInputSnapshot,
    _require_safe_run_id,
    run_shadow_observation_local_v0,
    write_shadow_observation_local_evidence_v0,
)

CONFIRMATION_TOKEN = "NO_RUNTIME_NO_SCHEDULER_NO_BROKER_NO_ORDERS"
CLOSEOUT_BASENAME = "SUPERVISED_TIMED_OBSERVER_V0_CLOSEOUT.md"
MANIFEST_SCHEMA_V0 = "supervised_timed_observer_input_manifest_v0"
MANIFEST_SOURCE_V0 = "operator_supplied_static_manifest"
HARNESS_SOURCE = "operator_supplied_static_manifest"
HARNESS_CADENCE_SOURCE = "operator_supplied_static_manifest"

BOUNDED_SCHEMA = "bounded_file_snapshot_observation_input_v0"
CAPTURED_SCHEMA = "captured_realistic_snapshot_observation_input_v0"

_load_snapshots_for_envelope: Union[Callable[..., Any], None] = None


def _file_snapshot_module() -> Any:
    global _load_snapshots_for_envelope
    if _load_snapshots_for_envelope is not None:
        return _load_snapshots_for_envelope
    path = _REPO_ROOT / "scripts" / "ops" / "run_shadow_observation_file_snapshot_v0.py"
    spec = importlib.util.spec_from_file_location("_shadow_obs_file_snap", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load file snapshot operator module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _load_snapshots_for_envelope = cast(
        Callable[..., Any], getattr(mod, "load_snapshots_for_envelope")
    )
    return _load_snapshots_for_envelope


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _glob_pattern_chars(s: str) -> bool:
    return any(ch in s for ch in "*?[")


def _read_git_context(repo_root: Path) -> str:
    head = repo_root / ".git" / "HEAD"
    if not head.is_file():
        return "git_head=unknown"
    line = head.read_text(encoding="utf-8").strip()
    if line.startswith("ref: "):
        ref = line[5:].strip()
        ref_file = repo_root / ".git" / ref
        if ref_file.is_file():
            sha = ref_file.read_text(encoding="utf-8").strip()[:12]
            return f"git_ref={ref} sha_prefix={sha}"
        return f"git_ref={ref}"
    return f"git_detached={line[:12]}"


def _validate_manifest_structure(raw: Mapping[str, Any]) -> Tuple[int, int, List[Dict[str, Any]]]:
    if raw.get("schema") != MANIFEST_SCHEMA_V0:
        _die(f"ERR: manifest schema must be {MANIFEST_SCHEMA_V0!r}")
    if raw.get("source") != MANIFEST_SOURCE_V0:
        _die(f"ERR: manifest source must be {MANIFEST_SOURCE_V0!r}")
    cad = raw.get("cadence_seconds")
    if not isinstance(cad, int) or cad < 0:
        _die("ERR: cadence_seconds must be int >= 0")
    mx = raw.get("max_observations")
    if not isinstance(mx, int) or mx < 1:
        _die("ERR: max_observations must be int >= 1")
    inputs = raw.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        _die("ERR: inputs must be a non-empty list")
    if len(inputs) > 10:
        _die("ERR: inputs length must be <= 10")
    out: List[Dict[str, Any]] = []
    seen_seq: Set[int] = set()
    for item in inputs:
        if not isinstance(item, Mapping):
            _die("ERR: each manifest input must be an object")
        seq = item.get("sequence")
        if not isinstance(seq, int):
            _die("ERR: sequence must be int")
        if seq in seen_seq:
            _die("ERR: duplicate sequence")
        seen_seq.add(seq)
        path_s = item.get("input_file")
        if not isinstance(path_s, str) or not path_s.strip():
            _die("ERR: input_file must be non-empty string path")
        if _glob_pattern_chars(path_s):
            _die("ERR: input_file must not contain glob wildcards")
        exp = item.get("expected_schema")
        if exp not in (BOUNDED_SCHEMA, CAPTURED_SCHEMA):
            _die(
                "ERR: expected_schema must be "
                f"{BOUNDED_SCHEMA!r} or {CAPTURED_SCHEMA!r}, got {exp!r}"
            )
        out.append(
            {
                "sequence": seq,
                "input_file": path_s,
                "expected_schema": exp,
            }
        )
    out.sort(key=lambda d: cast(int, d["sequence"]))
    return cad, mx, out


def _load_envelope_from_path(
    path: Path, expected_schema: str, load_snapshots: Callable[..., Any]
) -> Tuple[Tuple[ShadowObservationInputSnapshot, ...], str]:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as e:
        _die(f"ERR: failed to read input file {path}: {e}")
    try:
        loaded = json.loads(raw_text)
    except json.JSONDecodeError as e:
        _die(f"ERR: invalid JSON in {path}: {e}")
    if not isinstance(loaded, dict):
        _die(f"ERR: input JSON must be an object: {path}")
    actual = loaded.get("schema")
    if actual != expected_schema:
        _die(
            f"ERR: file {path} schema {actual!r} does not match manifest expected_schema "
            f"{expected_schema!r}"
        )
    return load_snapshots(loaded)


def main(argv: Union[List[str], None] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Supervised timed observer v0: manifest lists explicit local inputs → one evidence run."
        ),
    )
    parser.add_argument("--input-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--confirm-no-runtime",
        required=True,
        choices=[CONFIRMATION_TOKEN],
        help=f"Must be exactly {CONFIRMATION_TOKEN!r}.",
    )
    args = parser.parse_args(argv)

    manifest_path = args.input_manifest.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()

    if manifest_path.is_dir():
        _die(f"ERR: --input-manifest must be a file, not a directory: {manifest_path}")
    if not manifest_path.is_file():
        _die(f"ERR: manifest not found: {manifest_path}")

    try:
        _require_safe_run_id(args.run_id)
    except ValueError as e:
        _die(f"ERR: unsafe run_id: {e}")

    load_snapshots = _file_snapshot_module()

    try:
        m_raw_text = manifest_path.read_text(encoding="utf-8")
    except OSError as e:
        _die(f"ERR: failed to read manifest: {e}")
    m_sha256 = hashlib.sha256(m_raw_text.encode("utf-8")).hexdigest()

    try:
        manifest_obj = json.loads(m_raw_text)
    except json.JSONDecodeError as e:
        _die(f"ERR: invalid manifest JSON: {e}")
    if not isinstance(manifest_obj, dict):
        _die("ERR: manifest must be a JSON object")

    cadence_seconds, max_observations, entries = _validate_manifest_structure(manifest_obj)

    combined: List[ShadowObservationInputSnapshot] = []
    for ent in entries:
        p = Path(cast(str, ent["input_file"])).expanduser().resolve()
        if _glob_pattern_chars(str(p)):
            _die("ERR: resolved input_file must not contain glob wildcards")
        if p.is_dir():
            _die(f"ERR: listed input path is a directory: {p}")
        if not p.is_file():
            _die(f"ERR: listed input file not found: {p}")
        snaps, _src = _load_envelope_from_path(p, cast(str, ent["expected_schema"]), load_snapshots)
        combined.extend(snaps)

    total_n = len(combined)
    if total_n > max_observations:
        _die(
            f"ERR: total snapshot count {total_n} exceeds manifest max_observations {max_observations}"
        )

    if not combined:
        _die("ERR: no snapshots after loading inputs")

    ordered = tuple(combined)
    started = ordered[0].observed_at_utc
    ended = ordered[-1].observed_at_utc

    try:
        result = run_shadow_observation_local_v0(
            ordered,
            started_at_utc=started,
            ended_at_utc=ended,
            cadence_seconds=cadence_seconds,
            max_observations=max_observations,
            run_id=args.run_id,
            source=HARNESS_SOURCE,
            cadence_source=HARNESS_CADENCE_SOURCE,
        )
        write_shadow_observation_local_evidence_v0(
            result,
            output_dir=output_dir,
            overwrite=False,
        )
    except (ValueError, FileExistsError, OSError) as e:
        _die(f"ERR: harness or evidence write failed: {e}")

    run_dir = (output_dir / result.run_id).resolve()
    manifest_ev_path = run_dir / "manifest.json"
    manifest_ev_sha = hashlib.sha256(manifest_ev_path.read_bytes()).hexdigest()
    git_ctx = _read_git_context(_REPO_ROOT)

    lines = [
        "# Supervised Timed Observer v0 Closeout",
        "",
        "## Git / repo",
        "",
        f"- {git_ctx}",
        "",
        "## Paths",
        "",
        f"- input_manifest: `{manifest_path}`",
        f"- input_manifest_sha256: `{m_sha256}`",
        f"- output_dir: `{output_dir}`",
        f"- run_id: `{args.run_id}`",
        f"- run_dir: `{run_dir}`",
        "",
        "## Evidence",
        "",
        f"- record_count: {result.record_count}",
        f"- evidence_ids: {list(result.evidence_ids)}",
        f"- batch_hash: `{result.batch_hash}`",
        f"- timed_hash: `{result.timed_hash}`",
        f"- run_hash: `{result.run_hash}`",
        f"- manifest.json sha256 (written): `{manifest_ev_sha}`",
        "",
        "## Harness flags (non-approvals)",
        "",
        f"- local_observation_run_approved: {result.local_observation_run_approved}",
        f"- shadow_mode_allowed: {result.shadow_mode_allowed}",
        f"- runtime_allowed: {result.runtime_allowed}",
        f"- scheduler_allowed: {result.scheduler_allowed}",
        f"- order_submission_allowed: {result.order_submission_allowed}",
        "",
        "## Confirmation",
        "",
        f"- confirm_no_runtime: `{CONFIRMATION_TOKEN}`",
        "",
        "## Machine-readable final lines",
        "",
        "VERDICT=SUPERVISED_TIMED_OBSERVER_V0_PASSED",
        "DECISION=not_approved",
        "REPO_CHANGED=false",
        "SUPERVISED_TIMED_OBSERVER_EXECUTED=true",
        "SUPERVISED_TIMED_OBSERVER_RUNTIME_ADDED=false",
        "SUPERVISED_TIMED_OBSERVER_APPROVED=false",
        "SECOND_OPERATOR_RUN_EXECUTED=true",
        "SECOND_OPERATOR_RUN_PASSED=true",
        "CAPTURED_REALISTIC_INPUT_VALIDATION_IMPLEMENTED=true",
        "SHADOW_OBSERVATION_OPERATOR_ENTRYPOINT_IMPLEMENTED=true",
        "SHADOW_OBSERVATION_OPERATOR_ENTRYPOINT_APPROVED=false",
        "PROVEN_SHADOW_NO_ORDER_ENTRYPOINT_FOUND=false",
        "EXECUTABLE_COMMAND_CREATED=false",
        "OLD_DAEMON_EVIDENCE_IS_NOT_RUNTIME_APPROVAL=true",
        "LIVE_ALLOWED=false",
        "TESTNET_ALLOWED=false",
        "SHADOW_MODE_ALLOWED=false",
        "PAPER_ALLOWED=false",
        "SCHEDULER_ALLOWED=false",
        "RUNTIME_ALLOWED=false",
        "BROKER_ALLOWED=false",
        "EXCHANGE_ALLOWED=false",
        "ORDER_SUBMISSION_ALLOWED=false",
        "",
    ]
    closeout_path = run_dir / CLOSEOUT_BASENAME
    closeout_path.write_text("\n".join(lines), encoding="utf-8")

    in_machine = False
    for ml in lines:
        if ml.strip() == "## Machine-readable final lines":
            in_machine = True
            continue
        if in_machine and ml.strip() and not ml.startswith("#"):
            print(ml.strip())
    print(f"CLOSEOUT_WRITTEN={closeout_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
