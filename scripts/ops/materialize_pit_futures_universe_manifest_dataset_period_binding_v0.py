#!/usr/bin/env python3
"""Materialize PIT futures universe manifest dataset/period/instrument binding v0.

Offline-first: reads production universe manifest + materialization envelope from an
explicit staging root produced by materialize_pit_futures_universe_manifest_production_v1.
No network, no orders, no runtime effect, no economic evaluation execution.
Operator GO: GO_BOUNDED_PIT_FUTURES_UNIVERSE_MANIFEST_DATASET_PERIOD_BINDING_V0
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONFIRM_GO = "GO_BOUNDED_PIT_FUTURES_UNIVERSE_MANIFEST_DATASET_PERIOD_BINDING_V0"

from src.research.pit_futures_universe_manifest_dataset_period_binding_v0 import (  # noqa: E402
    CONTRACT_ID,
    SCHEMA_VERSION,
    UNIVERSE_POLICY_ID,
    UNIVERSE_POLICY_VERSION,
    ValidationVerdict,
    envelope_from_dict,
    manifest_from_dict,
    materialize_pit_futures_universe_manifest_dataset_period_binding_v0,
    serialize_contract_canonical_v0,
    validate_pit_futures_universe_manifest_dataset_period_binding_v0,
)


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        _die(f"ERR: not_object:{path}")
    return payload


def run_materialization(
    *,
    confirm: str,
    staging_root: Path,
    durable_evidence_root: Path,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    manifest_path = staging_root / "universe" / "pit_futures_universe_manifest_v1.json"
    envelope_path = staging_root / "universe" / "production_materialization_envelope_v1.json"
    if not manifest_path.is_file():
        _die(f"ERR: missing_production_manifest:{manifest_path}")
    if not envelope_path.is_file():
        _die(f"ERR: missing_production_envelope:{envelope_path}")

    production_manifest = manifest_from_dict(_load_json(manifest_path))
    production_envelope = envelope_from_dict(_load_json(envelope_path))

    contract = materialize_pit_futures_universe_manifest_dataset_period_binding_v0(
        repo_root=_REPO_ROOT,
        production_manifest=production_manifest,
        production_envelope=production_envelope,
    )
    validation = validate_pit_futures_universe_manifest_dataset_period_binding_v0(
        contract,
        repo_root=_REPO_ROOT,
        expected_manifest=production_manifest,
        expected_envelope=production_envelope,
    )
    if validation.verdict != ValidationVerdict.ACCEPTED:
        _die(f"ERR: binding_contract_validation_failed:{validation.fail_reasons}")

    binding_dir = staging_root / "binding"
    binding_dir.mkdir(parents=True, exist_ok=True)
    contract_path = binding_dir / "pit_futures_universe_manifest_dataset_period_binding_v0.json"
    contract_path.write_text(serialize_contract_canonical_v0(contract), encoding="utf-8")

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = (
        durable_evidence_root
        / "planning"
        / f"bounded_pit_futures_universe_manifest_dataset_period_binding_v0_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for rel in (
        "universe/pit_futures_universe_manifest_v1.json",
        "universe/production_materialization_envelope_v1.json",
        "binding/pit_futures_universe_manifest_dataset_period_binding_v0.json",
    ):
        src = staging_root / rel
        if src.is_file():
            dst = evidence_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)

    payload = {
        "verdict": "PIT_FUTURES_UNIVERSE_MANIFEST_DATASET_PERIOD_BINDING_COMPLETE",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "universe_policy_id": UNIVERSE_POLICY_ID,
        "universe_policy_version": UNIVERSE_POLICY_VERSION,
        "production_universe_manifest_ref": contract["production_universe_manifest_ref"],
        "production_universe_manifest_digest": contract["production_universe_manifest_digest"],
        "contract_digest": contract["contract_digest"],
        "candidate_count": len(contract["candidates"]),
        "candidate_strategy_ids": [item["strategy_id"] for item in contract["candidates"]],
        "staging_root": str(staging_root),
        "durable_evidence_path": str(evidence_dir),
        "manifest_verify_rc": rc,
        "manifest_verify_msg": verify_msg,
    }
    (evidence_dir / "BINDING_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _emit_machine_lines(payload)
    return payload


def _emit_machine_lines(result: Mapping[str, Any]) -> None:
    for key in (
        "verdict",
        "universe_policy_id",
        "universe_policy_version",
        "production_universe_manifest_digest",
        "contract_digest",
        "manifest_verify_rc",
    ):
        print(f"{key.upper()}={result.get(key)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize PIT futures universe manifest dataset/period/instrument binding v0."
        )
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument("--durable-evidence-root", type=Path, required=True)
    args = parser.parse_args()
    run_materialization(
        confirm=args.confirm_go_token,
        staging_root=args.staging_root,
        durable_evidence_root=args.durable_evidence_root,
    )


if __name__ == "__main__":
    main()
