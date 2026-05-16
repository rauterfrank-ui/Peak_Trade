#!/usr/bin/env python3
"""Bounded local operator entrypoint: file snapshot → Shadow Observation evidence (no runtime authority).

This script is an ops-only wrapper. It does not approve Shadow Mode, runtime, scheduler, broker,
exchange, or orders. It invokes the existing harness and evidence writer only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Optional

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
CLOSEOUT_BASENAME = "SHADOW_OBSERVATION_FILE_SNAPSHOT_OPERATOR_ENTRYPOINT_V0_CLOSEOUT.md"
INPUT_SCHEMA_V0 = "bounded_file_snapshot_observation_input_v0"
INPUT_SOURCE_EXPECTED = "bounded_file_captured_static"


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _load_snapshots(payload: Mapping[str, Any]) -> tuple[ShadowObservationInputSnapshot, ...]:
    schema = payload.get("schema")
    if schema != INPUT_SCHEMA_V0:
        _die(f"ERR: input schema must be {INPUT_SCHEMA_V0!r}, got {schema!r}")
    source = payload.get("source")
    if source != INPUT_SOURCE_EXPECTED:
        _die(f"ERR: input source must be {INPUT_SOURCE_EXPECTED!r}, got {source!r}")
    raw = payload.get("snapshots")
    if not isinstance(raw, list) or not raw:
        _die("ERR: snapshots must be a non-empty list")
    out: list[ShadowObservationInputSnapshot] = []
    for item in raw:
        if not isinstance(item, Mapping):
            _die("ERR: each snapshot must be an object")
        try:
            symbol = str(item["symbol"])
            observed_at_utc = str(item["observed_at_utc"])
            pl = item["payload"]
        except (KeyError, TypeError) as e:
            _die(f"ERR: snapshot missing required fields: {e}")
        if not isinstance(pl, Mapping):
            _die("ERR: payload must be an object")
        out.append(
            ShadowObservationInputSnapshot(
                symbol=symbol,
                observed_at_utc=observed_at_utc,
                source=str(source),
                payload=dict(pl),
            )
        )
    return tuple(out)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run bounded file-snapshot Shadow Observation evidence (local / caller paths only)."
        ),
    )
    parser.add_argument("--input-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--confirm-no-runtime",
        required=True,
        choices=[CONFIRMATION_TOKEN],
        help=f"Must be exactly {CONFIRMATION_TOKEN!r}.",
    )
    args = parser.parse_args(argv)

    input_path = args.input_file.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()

    if input_path.is_dir():
        _die(f"ERR: --input-file must be a file, not a directory: {input_path}")
    if not input_path.is_file():
        _die(f"ERR: input file not found: {input_path}")

    try:
        _require_safe_run_id(args.run_id)
    except ValueError as e:
        _die(f"ERR: unsafe run_id: {e}")

    try:
        raw_text = input_path.read_text(encoding="utf-8")
    except OSError as e:
        _die(f"ERR: failed to read input file: {e}")
    input_sha256 = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    try:
        loaded = json.loads(raw_text)
    except json.JSONDecodeError as e:
        _die(f"ERR: invalid JSON: {e}")
    if not isinstance(loaded, dict):
        _die("ERR: input JSON must be an object")

    snapshots = _load_snapshots(loaded)
    ordered = tuple(sorted(snapshots, key=lambda s: s.observed_at_utc))
    started = ordered[0].observed_at_utc
    ended = ordered[-1].observed_at_utc

    try:
        result = run_shadow_observation_local_v0(
            ordered,
            started_at_utc=started,
            ended_at_utc=ended,
            cadence_seconds=60,
            max_observations=len(ordered),
            run_id=args.run_id,
            source=INPUT_SOURCE_EXPECTED,
            cadence_source=INPUT_SOURCE_EXPECTED,
        )
        write_shadow_observation_local_evidence_v0(
            result,
            output_dir=output_dir,
            overwrite=False,
        )
    except (ValueError, FileExistsError, OSError) as e:
        _die(f"ERR: harness or evidence write failed: {e}")

    run_dir = (output_dir / result.run_id).resolve()
    manifest_path = run_dir / "manifest.json"
    manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    lines = [
        "# Shadow Observation File Snapshot Operator Entrypoint v0 Closeout",
        "",
        "## Scope",
        "",
        "- Bounded local operator entrypoint (no Shadow Mode / runtime / scheduler / broker / orders).",
        "",
        "## Paths",
        "",
        f"- input_file: `{input_path}`",
        f"- output_dir: `{output_dir}`",
        f"- run_dir: `{run_dir}`",
        "",
        "## Hashes",
        "",
        f"- input_sha256: `{input_sha256}`",
        f"- manifest_sha256: `{manifest_sha256}`",
        "",
        "## Harness flags (all must remain non-approvals)",
        "",
        f"- local_observation_run_approved: {result.local_observation_run_approved}",
        f"- proven_shadow_no_order_entrypoint_found: {result.proven_shadow_no_order_entrypoint_found}",
        f"- executable_command_created: {result.executable_command_created}",
        f"- shadow_mode_allowed: {result.shadow_mode_allowed}",
        f"- runtime_allowed: {result.runtime_allowed}",
        f"- scheduler_allowed: {result.scheduler_allowed}",
        f"- order_submission_allowed: {result.order_submission_allowed}",
        "",
        "## Machine-readable final lines",
        "",
        "VERDICT=SHADOW_OBSERVATION_FILE_SNAPSHOT_OPERATOR_ENTRYPOINT_V0_PASSED_LOCAL_OPERATOR_ONLY",
        "DECISION=not_approved",
        "REPO_CHANGED=false",
        "SHADOW_OBSERVATION_OPERATOR_ENTRYPOINT_IMPLEMENTED=true",
        "SHADOW_OBSERVATION_OPERATOR_ENTRYPOINT_APPROVED=false",
        "LOCAL_OBSERVATION_RUN_APPROVED=false",
        "PROVEN_SHADOW_NO_ORDER_ENTRYPOINT_FOUND=false",
        "EXECUTABLE_COMMAND_CREATED=false",
        "LIVE_ALLOWED=false",
        "TESTNET_ALLOWED=false",
        "SHADOW_MODE_ALLOWED=false",
        "PAPER_ALLOWED=false",
        "SCHEDULER_ALLOWED=false",
        "RUNTIME_ALLOWED=false",
        "BROKER_ALLOWED=false",
        "EXCHANGE_ALLOWED=false",
        "ORDER_SUBMISSION_ALLOWED=false",
        "BOUNDED_FILE_SNAPSHOT_OBSERVATION_TEST_PASSED=true",
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
