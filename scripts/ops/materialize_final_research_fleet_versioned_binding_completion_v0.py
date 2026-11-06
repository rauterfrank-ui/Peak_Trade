#!/usr/bin/env python3
"""Materialize final research fleet versioned binding completion v0.

Offline-first: reads production universe manifest, panel, and lifecycle staging
artifacts. Emits fleet binding completion manifest with full versioned bindings.
No network, no economic evaluation, no runtime effect.
Operator GO: GO_BOUNDED_FINAL_RESEARCH_FLEET_VERSIONED_BINDING_COMPLETION_V0
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

CONFIRM_GO = "GO_BOUNDED_FINAL_RESEARCH_FLEET_VERSIONED_BINDING_COMPLETION_V0"

from src.research.final_research_fleet_versioned_binding_completion_v0 import (  # noqa: E402
    BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
    SCHEMA_VERSION,
    ValidationVerdict,
    materialize_final_research_fleet_versioned_binding_completion_v0,
    serialize_completion_canonical_v0,
    validate_final_research_fleet_versioned_binding_completion_v0,
)
from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (  # noqa: E402
    load_panel_series_from_staging,
)
from src.research.pit_futures_universe_manifest_dataset_period_binding_v0 import (  # noqa: E402
    envelope_from_dict,
    manifest_from_dict,
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


def _load_source_registration(staging_root: Path) -> tuple[str, str]:
    source_reg_path = staging_root / "lifecycle" / "SOURCE_REGISTRATION.json"
    if not source_reg_path.is_file():
        _die(f"ERR: missing_source_registration:{source_reg_path}")
    payload = _load_json(source_reg_path)
    return str(payload["source_snapshot_ref"]), str(payload["source_snapshot_digest"])


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

    panel_series = None
    try:
        panel_series, _panel_ref = load_panel_series_from_staging(staging_root)
    except FileNotFoundError:
        panel_series = None

    source_ref, source_digest = _load_source_registration(staging_root)

    completion = materialize_final_research_fleet_versioned_binding_completion_v0(
        repo_root=_REPO_ROOT,
        production_manifest=production_manifest,
        production_envelope=production_envelope,
        panel_series=panel_series,
        source_registration_ref=source_ref,
        source_registration_digest=source_digest,
    )
    validation = validate_final_research_fleet_versioned_binding_completion_v0(
        completion,
        repo_root=_REPO_ROOT,
        require_ready_for_eval=True,
    )
    if validation.verdict != ValidationVerdict.ACCEPTED:
        _die(f"ERR: binding_completion_validation_failed:{validation.fail_reasons}")

    output_dir = staging_root / "research_materialization"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "final_research_fleet_versioned_binding_completion_v0.json").write_text(
        serialize_completion_canonical_v0(completion),
        encoding="utf-8",
    )

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = (
        durable_evidence_root
        / "planning"
        / f"bounded_final_research_fleet_versioned_binding_completion_v0_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for rel in (
        "universe/pit_futures_universe_manifest_v1.json",
        "universe/production_materialization_envelope_v1.json",
        "research_materialization/final_research_fleet_versioned_binding_completion_v0.json",
    ):
        src = staging_root / rel
        if src.is_file():
            dst = evidence_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)

    payload = {
        "verdict": "FINAL_RESEARCH_FLEET_VERSIONED_BINDING_COMPLETION_PASS",
        "schema_version": SCHEMA_VERSION,
        "binding_materialization_status": completion.get("binding_materialization_status"),
        "completion_digest": completion["completion_digest"],
        "candidate_count": len(completion["candidates"]),
        "binding_status_ready": completion.get("binding_materialization_status")
        == BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
        "economic_evaluation_authorized": completion.get("economic_evaluation_authorized"),
        "staging_root": str(staging_root),
        "durable_evidence_path": str(evidence_dir),
        "manifest_verify_rc": rc,
        "manifest_verify_msg": verify_msg,
        "generated_at_utc": _utc_now_z(),
    }
    (evidence_dir / "COMPLETION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _emit_machine_lines(payload)
    return payload


def _emit_machine_lines(result: Mapping[str, Any]) -> None:
    for key in (
        "verdict",
        "binding_materialization_status",
        "completion_digest",
        "candidate_count",
        "binding_status_ready",
        "economic_evaluation_authorized",
        "manifest_verify_rc",
    ):
        print(f"{key.upper()}={result.get(key)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize final research fleet versioned binding completion v0."
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
