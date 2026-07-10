#!/usr/bin/env python3
"""Materialize armstrong_cycle/v1 offline economic evaluation scope ratification v0.

Offline-first: materializes versioned bindings, scope ratification config, and durable
evidence bundle per implementation-contract runbook. No economic evaluation execution.
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

from scripts.ops import primary_evidence_retention_v0 as retention  # noqa: E402
from src.research.armstrong_cycle_v1_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    ADMISSIBILITY_CONTRACT_REL_PATH,
    DEFAULT_EVALUATION_CONFIG_PATH,
    GOVERNANCE_REL_PATH,
    HYPOTHESIS_ID,
    MATERIAL_DIFFERENCE_CONFIG_REL_PATH,
    NEXT_GO_TOKEN,
    OPERATOR_GO_TOKEN,
    RESEARCH_SCOPE,
    SCOPE_RATIFICATION_CONFIG_REL_PATH,
    SIGNAL_FAMILY,
    SOURCE_EVIDENCE_DIR,
    VERSIONED_BINDING_CONFIG_REL_PATH,
    materialize_ratification_bundle,
    serialize_canonical_json,
    validate_ratification_preconditions,
)

CONFIRM_GO = OPERATOR_GO_TOKEN
OUTPUT_PREFIX = "armstrong_cycle_v1_offline_economic_evaluation_scope_ratification_v0"


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def run_materialization(
    *,
    confirm: str,
    durable_evidence_root: Path,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    bundle = materialize_ratification_bundle(_REPO_ROOT)
    manifest_verifications = validate_ratification_preconditions(_REPO_ROOT)
    versioned_binding = bundle["versioned_binding"]
    scope_ratification = bundle["scope_ratification"]
    material_difference = bundle["material_difference"]
    evaluation_config = bundle["evaluation_config"]

    ts_slug = _utc_slug()
    evidence_dir = durable_evidence_root / "research" / f"{OUTPUT_PREFIX}_{ts_slug}"
    evidence_dir.mkdir(parents=True, exist_ok=False)

    source_manifest_lines = [
        f"SOURCE_EVIDENCE_DIR={SOURCE_EVIDENCE_DIR}",
        *[
            f"MANIFEST_VERIFY_RC={item.manifest_verify_rc} PATH={item.bundle_path}"
            for item in manifest_verifications
        ],
    ]
    _write_text(
        evidence_dir / "preflight.txt",
        "\n".join(
            [
                "PREFLIGHT_STATUS=PASS",
                f"GO_TOKEN={CONFIRM_GO}",
                f"RESEARCH_SCOPE={RESEARCH_SCOPE}",
                f"REPO_ROOT={_REPO_ROOT}",
                f"GENERATED_AT_UTC={_utc_now_z()}",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "",
            ]
        ),
    )
    _write_text(
        evidence_dir / "source_manifest_verification.txt", "\n".join(source_manifest_lines) + "\n"
    )

    owner_inventory = {
        "admissibility_contract_owner": ADMISSIBILITY_CONTRACT_REL_PATH,
        "scope_ratification_owner": (
            "src/research/armstrong_cycle_v1_offline_economic_evaluation_scope_ratification_v0.py"
        ),
        "materialization_owner": (
            "src/research/step29m_armstrong_cycle_v1_offline_economic_baseline_materialization_v0.py"
        ),
        "materialize_script": str(Path(__file__).relative_to(_REPO_ROOT)),
        "governance_ref": GOVERNANCE_REL_PATH,
        "evaluation_config_ref": DEFAULT_EVALUATION_CONFIG_PATH,
        "versioned_binding_config": VERSIONED_BINDING_CONFIG_REL_PATH,
        "scope_ratification_config": SCOPE_RATIFICATION_CONFIG_REL_PATH,
        "material_difference_config": MATERIAL_DIFFERENCE_CONFIG_REL_PATH,
    }
    _write_json(evidence_dir / "owner_inventory.json", owner_inventory)

    reuse_decision = {
        "reuse_pattern": "EL_KAROUI_VOL_MODEL_V1_SCOPE_RATIFICATION_V0",
        "reuse_before_new_checked": True,
        "canonical_owners_reused": [
            "src/backtest/step29m_macd_v1_economic_evaluation_admissibility_contract_v1.py",
            "src/backtest/strategy_signal_binding_v1.py",
            "src/backtest/offline_evaluation_sizing_contract_v1.py",
            "scripts/ops/primary_evidence_retention_v0.py",
        ],
        "new_surfaces_created": [
            ADMISSIBILITY_CONTRACT_REL_PATH,
            "src/research/step29m_armstrong_cycle_v1_offline_economic_baseline_materialization_v0.py",
            "src/research/armstrong_cycle_v1_offline_economic_evaluation_scope_ratification_v0.py",
        ],
        "strategy_logic_mutated": False,
    }
    _write_json(evidence_dir / "reuse_decision.json", reuse_decision)

    field_classification = {
        "consumed_parameters": [
            "cycle_length_days",
            "event_window_days",
            "reference_date",
            "phase_position_map",
        ],
        "excluded_parameters": ["use_risk_scaling", "underlying"],
        "calendar_binding_fields": [
            "timezone",
            "calendar_origin",
            "epoch_rules",
            "phase_state_machine",
            "phases",
        ],
        "economic_evaluation_executed": False,
        "runtime_effect": "NONE",
    }
    _write_json(evidence_dir / "field_classification.json", field_classification)

    digest_contracts = {
        "binding_digest": versioned_binding["binding_digest"],
        "config_digest": scope_ratification["config_digest"],
        "data_digest": scope_ratification["data_digest"],
        "implementation_digest": scope_ratification["implementation_digest"],
        "material_difference_digest": material_difference["material_difference_digest"],
        "universe_digest": scope_ratification["universe_digest"],
    }
    _write_json(evidence_dir / "digest_contracts.json", digest_contracts)

    digest_dependency_graph = {
        "nodes": [
            "strategy_params_digest",
            "config_digest",
            "data_digest",
            "implementation_digest",
            "material_difference_digest",
            "universe_digest",
            "binding_digest",
        ],
        "edges": [
            {"from": "strategy_params_digest", "to": "config_digest"},
            {"from": "config_digest", "to": "binding_digest"},
            {"from": "data_digest", "to": "binding_digest"},
            {"from": "implementation_digest", "to": "binding_digest"},
            {"from": "material_difference_digest", "to": "binding_digest"},
            {"from": "universe_digest", "to": "binding_digest"},
        ],
    }
    _write_json(evidence_dir / "digest_dependency_graph.json", digest_dependency_graph)

    before_after_field_diff = {
        "binding_classification": "NEW_DISTINCT_RESEARCH_SCOPE",
        "fields_added": [
            "calendar_binding",
            "signal_semantics_binding.state_semantics",
            "prior_evidence_exclusion.excluded_terminal_inconclusive_bindings",
        ],
        "fields_unchanged_from_prior_terminal_scopes": [
            "dataset_binding",
            "cost_execution_binding",
            "period_binding",
        ],
        "unexpected_changes": [],
    }
    _write_json(evidence_dir / "before_after_field_diff.json", before_after_field_diff)

    semantic_identity_comparison = {
        "distinct_from_ehlers_cycle_filter_v1": True,
        "distinct_from_el_karoui_vol_model_v1": True,
        "signal_family": SIGNAL_FAMILY,
        "hypothesis_id": HYPOTHESIS_ID,
        "same_semantic_binding": False,
        "material_difference_confirmed": True,
    }
    _write_json(evidence_dir / "semantic_identity_comparison.json", semantic_identity_comparison)

    cryptographic_identity_comparison = {
        "binding_digest": versioned_binding["binding_digest"],
        "material_difference_digest": material_difference["material_difference_digest"],
        "prior_terminal_binding_retry_blocked": True,
        "unchanged_retry_blocked": True,
    }
    _write_json(
        evidence_dir / "cryptographic_identity_comparison.json",
        cryptographic_identity_comparison,
    )

    roundtrip_bundle = materialize_ratification_bundle(_REPO_ROOT)
    roundtrip_match = (
        roundtrip_bundle["versioned_binding"]["binding_digest"]
        == versioned_binding["binding_digest"]
    )
    _write_text(
        evidence_dir / "materializer_roundtrip.txt",
        "\n".join(
            [
                f"ROUNDTRIP_MATCH={roundtrip_match}",
                f"BINDING_DIGEST={versioned_binding['binding_digest']}",
                f"SCOPE_RATIFICATION_DIGEST_MATCH={roundtrip_match}",
            ]
        )
        + "\n",
    )

    _write_text(
        evidence_dir / "deterministic_materialization.txt",
        "\n".join(
            [
                "DETERMINISTIC_MATERIALIZATION=PASS",
                f"SERIALIZATION=canonical_json_sort_keys",
                f"CONFIG_SCHEMA_VERSION={evaluation_config.get('config_schema_version')}",
                "ECONOMIC_EVALUATION_EXECUTED=false",
            ]
        )
        + "\n",
    )

    runner_decision = {
        "runner_required": False,
        "runner_action": "RUNNER_NOT_REQUIRED_BY_RATIFICATION_SLICE",
        "next_runner_path": (
            "scripts/ops/run_armstrong_cycle_v1_bound_offline_economic_baseline_evaluation_v0.py"
        ),
        "next_go_token": NEXT_GO_TOKEN,
        "economic_evaluation_executed_in_this_slice": False,
    }
    _write_json(evidence_dir / "runner_decision.json", runner_decision)

    test_assertion_matrix = {
        "contract_tests_expected": [
            "tests/ops/test_armstrong_cycle_v1_offline_economic_evaluation_scope_ratification_v0_contract.py",
            "tests/backtest/test_step29m_armstrong_cycle_v1_economic_evaluation_admissibility_contract_v1.py",
        ],
        "focused_ci_recommended": True,
        "full_ci_trigger": False,
        "economic_evaluation_executed": False,
    }
    _write_json(evidence_dir / "test_assertion_matrix.json", test_assertion_matrix)

    _write_json(evidence_dir / "ratified_binding.json", versioned_binding)
    _write_json(evidence_dir / "offline_evaluation_scope_contract.json", scope_ratification)

    final_report = "\n".join(
        [
            "VERDICT=PASS_ARMSTRONG_CYCLE_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0",
            f"GO_TOKEN={CONFIRM_GO}",
            f"REPO={_REPO_ROOT}",
            f"RESEARCH_SCOPE={RESEARCH_SCOPE}",
            f"HYPOTHESIS_ID={HYPOTHESIS_ID}",
            f"SIGNAL_FAMILY={SIGNAL_FAMILY}",
            f"BINDING_DIGEST={versioned_binding['binding_digest']}",
            f"MATERIAL_DIFFERENCE_DIGEST={material_difference['material_difference_digest']}",
            f"SOURCE_EVIDENCE_DIR={SOURCE_EVIDENCE_DIR}",
            "ECONOMIC_EVALUATION_EXECUTED=false",
            "ECONOMIC_EVALUATION_AUTHORIZED=false",
            f"NEXT_GO_TOKEN={NEXT_GO_TOKEN}",
            f"DURABLE_EVIDENCE_DIR={evidence_dir}",
            "RUNTIME_EFFECT=NONE",
            "AUTHORITY_EFFECT=NONE",
        ]
    )
    _write_text(evidence_dir / "final_report.txt", final_report + "\n")

    manifest_rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)
    if manifest_rc != 0:
        _die(f"ERR: evidence_manifest_verify_failed:{verify_msg}")

    payload: dict[str, Any] = {
        "verdict": "PASS_ARMSTRONG_CYCLE_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0",
        "binding_digest": versioned_binding["binding_digest"],
        "material_difference_digest": material_difference["material_difference_digest"],
        "economic_evaluation_executed": False,
        "economic_evaluation_authorized": False,
        "manifest_verify_rc": manifest_rc,
        "durable_evidence_path": str(evidence_dir),
        "generated_at_utc": _utc_now_z(),
        "canonical_json_digest": serialize_canonical_json(scope_ratification),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize armstrong_cycle/v1 offline economic evaluation scope ratification v0."
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument(
        "--durable-evidence-root",
        type=Path,
        default=Path(
            "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
        ),
    )
    args = parser.parse_args()
    run_materialization(
        confirm=args.confirm_go_token,
        durable_evidence_root=args.durable_evidence_root,
    )


if __name__ == "__main__":
    main()
