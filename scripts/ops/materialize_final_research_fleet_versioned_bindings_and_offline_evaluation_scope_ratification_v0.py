#!/usr/bin/env python3
"""Materialize final research fleet versioned bindings and offline evaluation scope ratification v0.

Offline-first: validates fleet binding completion, emits repo config artifacts,
scope ratification contract, and fleet ratification record. No economic evaluation
execution, no runtime or order effect.
Operator GO: GO_BOUNDED_FINAL_RESEARCH_FLEET_VERSIONED_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_RATIFICATION_V0
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

CONFIRM_GO = "GO_BOUNDED_FINAL_RESEARCH_FLEET_VERSIONED_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_RATIFICATION_V0"

from src.research.final_research_fleet_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    CONFIG_REL_PATH as SCOPE_CONFIG_REL_PATH,
    ECONOMIC_EVALUATION_AUTHORIZED,
    ECONOMIC_EVALUATION_SCOPE_RATIFIED,
    FINAL_RESEARCH_FLEET_BINDING_READY,
    NEW_CANDIDATES_RATIFIED,
    OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED,
    materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0,
    validate_final_research_fleet_offline_economic_evaluation_scope_ratification_v0,
    ValidationVerdict as ScopeValidationVerdict,
    write_scope_ratification_artifact_v0,
)
from src.research.final_research_fleet_v0_fleet_ratification_v0 import (  # noqa: E402
    CONFIG_REL_PATH as FLEET_CONFIG_REL_PATH,
    NEXT_CANONICAL_STEP,
    materialize_final_research_fleet_v0_fleet_ratification_v0,
    validate_final_research_fleet_v0_fleet_ratification_v0,
    ValidationVerdict as FleetValidationVerdict,
    write_fleet_ratification_artifact_v0,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (  # noqa: E402
    CONFIG_REL_PATH as BINDING_CONFIG_REL_PATH,
    ValidationVerdict as BindingValidationVerdict,
    validate_final_research_fleet_versioned_binding_completion_v0,
    write_binding_completion_artifact_v0,
)
from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (  # noqa: E402
    load_panel_series_from_staging,
)
from src.research.pit_futures_universe_manifest_dataset_period_binding_v0 import (  # noqa: E402
    envelope_from_dict,
    manifest_from_dict,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (  # noqa: E402
    materialize_final_research_fleet_versioned_binding_completion_v0,
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
    panel_series, _panel_ref = load_panel_series_from_staging(staging_root)
    source_ref, source_digest = _load_source_registration(staging_root)

    completion = materialize_final_research_fleet_versioned_binding_completion_v0(
        repo_root=_REPO_ROOT,
        production_manifest=production_manifest,
        production_envelope=production_envelope,
        panel_series=panel_series,
        source_registration_ref=source_ref,
        source_registration_digest=source_digest,
    )
    binding_validation = validate_final_research_fleet_versioned_binding_completion_v0(
        completion,
        repo_root=_REPO_ROOT,
        require_ready_for_eval=True,
    )
    if binding_validation.verdict != BindingValidationVerdict.ACCEPTED:
        _die(f"ERR: binding_completion_validation_failed:{binding_validation.fail_reasons}")

    binding_path = write_binding_completion_artifact_v0(_REPO_ROOT, completion=completion)
    scope_path = write_scope_ratification_artifact_v0(
        _REPO_ROOT,
        fleet_binding_completion=completion,
    )
    fleet_path = write_fleet_ratification_artifact_v0(
        _REPO_ROOT,
        fleet_binding_completion=completion,
    )

    scope_ratification = (
        materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
            repo_root=_REPO_ROOT,
            fleet_binding_completion=completion,
        )
    )
    scope_validation = (
        validate_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
            scope_ratification,
            repo_root=_REPO_ROOT,
            expected_fleet_binding_completion=completion,
        )
    )
    if scope_validation.verdict != ScopeValidationVerdict.ACCEPTED:
        _die(f"ERR: scope_ratification_validation_failed:{scope_validation.fail_reasons}")

    fleet_record = materialize_final_research_fleet_v0_fleet_ratification_v0(
        repo_root=_REPO_ROOT,
        fleet_binding_completion=completion,
    )
    fleet_validation = validate_final_research_fleet_v0_fleet_ratification_v0(
        fleet_record,
        fleet_binding_completion=completion,
        scope_ratification=scope_ratification,
    )
    if fleet_validation.verdict != FleetValidationVerdict.ACCEPTED:
        _die(f"ERR: fleet_ratification_validation_failed:{fleet_validation.fail_reasons}")

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = (
        durable_evidence_root
        / "implementation"
        / f"bounded_final_research_fleet_versioned_bindings_and_offline_evaluation_scope_ratification_v0_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    for src in (binding_path, scope_path, fleet_path):
        dst = evidence_dir / src.name
        dst.write_bytes(src.read_bytes())

    governance_snapshot = {
        "origin_main_head": "0a073336c4ccca6fd7c5c5f80bfe28ccc98a7f40",
        "no_new_candidate_hold": "REVOKED",
        "operator_policy_decision": "AUTHORIZE_BOUNDED_MULTI_CANDIDATE_FUTURES_RESEARCH_FLEET_V0",
        "final_research_fleet": "trend_following,bollinger_bands,momentum_1h",
        "final_research_fleet_binding_ready": FINAL_RESEARCH_FLEET_BINDING_READY,
        "new_candidates_ratified": NEW_CANDIDATES_RATIFIED,
        "economic_evaluation_scope_ratified": ECONOMIC_EVALUATION_SCOPE_RATIFIED,
        "offline_economic_evaluation_scope_ratified": OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_validity_offline_gate_pass": False,
        "promotion_eligible": False,
        "runtime_rewire_admissible": False,
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "economic_evaluation_executed": False,
    }
    (evidence_dir / "GOVERNANCE_START_STATE_SNAPSHOT.json").write_text(
        json.dumps(governance_snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)

    payload = {
        "verdict": "FINAL_RESEARCH_FLEET_VERSIONED_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_RATIFICATION_PASS",
        "binding_config_path": str(binding_path.relative_to(_REPO_ROOT)),
        "scope_config_path": str(scope_path.relative_to(_REPO_ROOT)),
        "fleet_config_path": str(fleet_path.relative_to(_REPO_ROOT)),
        "completion_digest": completion["completion_digest"],
        "scope_ratification_digest": scope_ratification["ratification_digest"],
        "fleet_ratification_digest": fleet_record["fleet_ratification_digest"],
        "candidate_count": len(completion["candidates"]),
        "final_research_fleet_binding_ready": FINAL_RESEARCH_FLEET_BINDING_READY,
        "new_candidates_ratified": NEW_CANDIDATES_RATIFIED,
        "economic_evaluation_scope_ratified": ECONOMIC_EVALUATION_SCOPE_RATIFIED,
        "offline_economic_evaluation_scope_ratified": OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": False,
        "economic_validity_offline_gate_pass": False,
        "runtime_rewire_admissible": False,
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "durable_evidence_path": str(evidence_dir),
        "manifest_verify_rc": rc,
        "manifest_verify_msg": verify_msg,
        "generated_at_utc": _utc_now_z(),
    }
    (evidence_dir / "RATIFICATION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _emit_machine_lines(payload)
    return payload


def _emit_machine_lines(result: Mapping[str, Any]) -> None:
    for key in (
        "verdict",
        "completion_digest",
        "scope_ratification_digest",
        "fleet_ratification_digest",
        "candidate_count",
        "final_research_fleet_binding_ready",
        "new_candidates_ratified",
        "economic_evaluation_scope_ratified",
        "economic_evaluation_authorized",
        "economic_evaluation_executed",
        "economic_validity_offline_gate_pass",
        "runtime_rewire_admissible",
        "next_canonical_step",
        "manifest_verify_rc",
    ):
        print(f"{key.upper()}={result.get(key)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize final research fleet versioned bindings and offline "
            "evaluation scope ratification v0."
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
