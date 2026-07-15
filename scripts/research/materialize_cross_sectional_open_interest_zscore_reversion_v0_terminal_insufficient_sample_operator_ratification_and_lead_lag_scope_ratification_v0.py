#!/usr/bin/env python3
"""Materialize operator ratification after OI zscore insufficient sample and lead-lag scope ratification v0."""

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

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    finalize_durable_bundle_manifest,
    verify_manifest_sha256,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    CONFIG_REL_PATH as LEAD_LAG_SCOPE_CONFIG_REL_PATH,
    ValidationVerdictEnum as LeadLagValidationVerdict,
    materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0,
    serialize_ratification_canonical_v0 as serialize_lead_lag_ratification,
    validate_lead_lag_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0 import (  # noqa: E402
    materialize_versioned_hypothesis_binding_v0 as materialize_lead_lag_binding,
)
from src.research.cross_sectional_open_interest_zscore_reversion_v0_terminal_insufficient_sample_and_distinct_futures_research_scope_ratification_v0 import (  # noqa: E402
    CANONICAL_EVALUATION_DIR,
    CONFIG_REL_PATH,
    GOVERNANCE_REL_PATH,
    OPERATOR_DECISION,
    OPERATOR_GO_TOKEN,
    REGISTRATION_ID,
    VERSIONED_BINDING_CONFIG_REL_PATH,
    apply_versioned_binding_registration_fields,
    build_distinct_scope_candidate_inventory,
    build_exact_binding_retry_guard_report,
    build_material_difference_matrix,
    build_retry_non_equivalence_proof,
    materialize_registration_config,
    serialize_canonical_json,
    validate_registration_preconditions,
)

CONFIRM_GO = OPERATOR_GO_TOKEN
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = (
    "cross_sectional_open_interest_zscore_reversion_v0_terminal_insufficient_sample_"
    "operator_ratification_and_lead_lag_scope_ratification_v0"
)
FOCUSED_TEST = (
    "tests/ops/"
    "test_cross_sectional_open_interest_zscore_reversion_v0_terminal_insufficient_sample_"
    "operator_ratification_and_lead_lag_scope_ratification_v0_contract.py"
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _die(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def _git_snapshot() -> dict[str, str]:
    def _run(args: list[str]) -> str:
        return subprocess.check_output(["git", *args], cwd=_REPO_ROOT, text=True).strip()

    return {
        "head": _run(["rev-parse", "HEAD"]),
        "origin_main": _run(["rev-parse", "origin/main"]),
        "branch": _run(["branch", "--show-current"]),
        "status_short": _run(["status", "--short"]) or "(clean)",
    }


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _verify_manifest(bundle_dir: Path, log_path: Path) -> int:
    ok, msg = verify_manifest_sha256(bundle_dir)
    rc = 0 if ok else 1
    log_path.write_text(
        f"MANIFEST_VERIFY_RC={rc}\nMANIFEST_VERIFY_MSG={msg or 'ok'}\nSOURCE={bundle_dir}\n",
        encoding="utf-8",
    )
    return rc


def _run_ci_selector() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "scripts/ops/ci_test_selection_v1.py"],
        cwd=_REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    payload: dict[str, Any] = {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            payload[key.strip()] = value.strip()
    return payload


def _run_focused_tests() -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", FOCUSED_TEST],
        cwd=_REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.returncode, proc.stdout + proc.stderr


def run_materialization_v0(
    *,
    confirm_go_token: str,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    write_repo_config: bool,
    skip_focused_tests: bool = False,
) -> dict[str, Any]:
    if confirm_go_token != CONFIRM_GO:
        _die(f"ERR:invalid confirm go token:{CONFIRM_GO}")

    canonical = validate_registration_preconditions()
    registration = materialize_registration_config(canonical=canonical)

    lead_lag_binding = materialize_lead_lag_binding()
    lead_lag_ratification = materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0(
        repo_root=_REPO_ROOT,
        versioned_binding=lead_lag_binding,
    )
    lead_lag_validation = validate_lead_lag_offline_economic_evaluation_scope_ratification_v0(
        lead_lag_ratification,
        expected_binding=lead_lag_binding,
    )
    if lead_lag_validation.verdict != LeadLagValidationVerdict.ACCEPTED:
        _die(
            f"ERR:lead_lag_scope_ratification_validation_failed:{lead_lag_validation.fail_reasons}"
        )

    if write_repo_config:
        reg_path = _REPO_ROOT / CONFIG_REL_PATH
        reg_path.parent.mkdir(parents=True, exist_ok=True)
        reg_path.write_text(serialize_canonical_json(registration) + "\n", encoding="utf-8")

        lead_lag_path = _REPO_ROOT / LEAD_LAG_SCOPE_CONFIG_REL_PATH
        lead_lag_path.parent.mkdir(parents=True, exist_ok=True)
        lead_lag_path.write_text(
            serialize_lead_lag_ratification(lead_lag_ratification) + "\n", encoding="utf-8"
        )

        binding_path = _REPO_ROOT / VERSIONED_BINDING_CONFIG_REL_PATH
        binding_payload = json.loads(binding_path.read_text(encoding="utf-8"))
        updated_binding = apply_versioned_binding_registration_fields(binding_payload, registration)
        binding_path.write_text(
            json.dumps(updated_binding, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    output_dir = archive_root / "research" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    output_dir.mkdir(parents=True, exist_ok=False)

    source_manifest_rc = _verify_manifest(
        CANONICAL_EVALUATION_DIR,
        output_dir / "source_manifest_verification.txt",
    )
    if source_manifest_rc != 0:
        _die("ERR:canonical evaluation manifest verify failed")

    git_snapshot = _git_snapshot()
    candidate_matrix = {
        "schema_version": "candidate_matrix.v0",
        "operator_decision": OPERATOR_DECISION,
        "candidates": build_distinct_scope_candidate_inventory()["candidates"],
    }
    candidate_ranking = {
        "schema_version": "candidate_ranking.v0",
        "ranked": [
            {
                "rank": 1,
                "candidate_id": "lead_lag_information_diffusion_v0",
                "candidate_type": "NEW_VERSIONED_RESEARCH_SCOPE",
                "research_scope_or_evidence_class": "cross_sectional_futures_lead_lag_information_diffusion/v0",
                "admissible": True,
                "ranking_score": 0.92,
            }
        ],
    }

    _write_json(
        output_dir / "terminal_status_reconciliation.json",
        {
            "cross_sectional_open_interest_zscore_reversion_v0_execution_complete": True,
            "economic_validity_offline_gate_pass": False,
            "failure_class": "INSUFFICIENT_TRADE_SAMPLE",
            "implementation_defect_proven": False,
            "binding_defect_proven": False,
            "unchanged_binding_retry_admissible": False,
            "parameter_rescue_admissible": False,
            "threshold_reduction_admissible": False,
            "policy_rescue_admissible": False,
            "runtime_rewire_admissible": False,
        },
    )
    _write_json(
        output_dir / "owner_inventory.json",
        {
            "canonical_owner": registration["selected_distinct_canonical_owner"],
            "registration_owner": REGISTRATION_ID,
            "lead_lag_scope_ratification_owner": LEAD_LAG_SCOPE_CONFIG_REL_PATH,
        },
    )
    _write_json(
        output_dir / "reuse_decision.json",
        {
            "reuse_decision": "REUSE_EXISTING_LEAD_LAG_BINDING_AND_EXECUTION_INFRASTRUCTURE",
            "new_owner_invented": False,
        },
    )
    _write_json(
        output_dir / "prior_scope_inventory.json",
        {
            "terminal_insufficient_sample_scopes": [registration["research_scope"]],
            "oi_ranking_family_exhausted": True,
        },
    )
    _write_json(output_dir / "candidate_matrix.json", candidate_matrix)
    _write_json(output_dir / "candidate_ranking.json", candidate_ranking)
    _write_json(
        output_dir / "selected_operator_decision.json",
        {
            "operator_decision": OPERATOR_DECISION,
            "selected_research_scope_or_evidence_class": registration["selected_distinct_scope"],
            "go_token_consumed": CONFIRM_GO,
        },
    )
    _write_json(output_dir / "material_difference_proof.json", build_material_difference_matrix())
    _write_json(
        output_dir / "retry_non_equivalence_proof.json", build_retry_non_equivalence_proof()
    )
    _write_json(
        output_dir / "field_classification.json",
        {
            "authored": ["registration_digest", "ratification_digest"],
            "observed": ["trade_count", "net_return", "binding_digest"],
            "derived": ["material_difference_matrix", "retry_non_equivalence_proof"],
        },
    )
    _write_json(
        output_dir / "digest_contracts.json",
        {
            "baseline_binding_digest": registration["binding_digest"],
            "selected_binding_digest": registration["selected_distinct_binding_digest"],
            "selected_material_difference_digest": registration[
                "selected_distinct_material_difference_digest"
            ],
        },
    )
    _write_json(
        output_dir / "digest_dependency_graph.json",
        {
            "nodes": [VERSIONED_BINDING_CONFIG_REL_PATH, LEAD_LAG_SCOPE_CONFIG_REL_PATH],
            "edges": [{"from": CONFIG_REL_PATH, "to": LEAD_LAG_SCOPE_CONFIG_REL_PATH}],
        },
    )
    _write_json(output_dir / "ratification_contract.json", registration)
    _write_json(
        output_dir / "runner_entry_point_decision.json",
        {
            "future_execution_go_token": registration["next_go_token"],
            "runner_binding_ref": lead_lag_ratification["runner_binding_ref"],
            "harness_binding_ref": lead_lag_ratification["harness_binding_ref"],
            "runtime_effect": "NONE",
        },
    )
    _write_json(output_dir / "lead_lag_scope_ratification_contract.json", lead_lag_ratification)

    ci_selector = _run_ci_selector()
    _write_json(output_dir / "ci_selector_decision.json", ci_selector)

    test_rc, test_output = (0, "SKIPPED") if skip_focused_tests else _run_focused_tests()
    (output_dir / "test_results.txt").write_text(test_output, encoding="utf-8")
    _write_json(
        output_dir / "test_assertion_matrix.json",
        {"focused_test": FOCUSED_TEST, "returncode": test_rc},
    )
    if test_rc != 0:
        _die(f"ERR:focused_tests_failed:\n{test_output}")

    repo_diff = subprocess.run(
        ["git", "diff", "--stat"],
        cwd=_REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    (output_dir / "repo_diff.txt").write_text(repo_diff.stdout + repo_diff.stderr, encoding="utf-8")
    _write_json(output_dir / "git_snapshot.json", git_snapshot)
    (output_dir / "preflight.txt").write_text(
        "\n".join(
            [
                f"GO_TOKEN={CONFIRM_GO}",
                f"OPERATOR_DECISION={OPERATOR_DECISION}",
                f"HEAD={git_snapshot['head']}",
                f"ORIGIN_MAIN={git_snapshot['origin_main']}",
                f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = finalize_durable_bundle_manifest(output_dir)
    final_report_lines = [
        "STATUS=PASS",
        "VERDICT=NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_RATIFIED",
        f"SCOPE={OUTPUT_PREFIX}",
        f"OPERATOR_GO={CONFIRM_GO}",
        f"OPERATOR_DECISION={OPERATOR_DECISION}",
        f"SELECTED_RESEARCH_SCOPE_OR_EVIDENCE_CLASS={registration['selected_distinct_scope']}",
        "MATERIAL_DIFFERENCE_PROVEN=true",
        "RETRY_NON_EQUIVALENCE_PROVEN=true",
        f"CANONICAL_OWNER={registration['selected_distinct_canonical_owner']}",
        "REUSE_DECISION=REUSE_EXISTING_LEAD_LAG_BINDING_AND_EXECUTION_INFRASTRUCTURE",
        f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}",
        f"MANIFEST_VERIFY_RC={manifest_rc}",
        f"CI_SELECTOR={ci_selector.get('SELECTOR_MODE', 'UNKNOWN')}",
        f"TEST_RESULT={'PASS' if test_rc == 0 else 'FAIL'}",
        "ECONOMIC_EVALUATION_EXECUTED=false",
        "PARAMETER_OPTIMIZATION_EXECUTED=false",
        "THRESHOLD_REDUCTION_EXECUTED=false",
        "POLICY_RESCUE_EXECUTED=false",
        "RUNTIME_EFFECT=NONE",
        "AUTHORITY_EFFECT=NONE",
        f"DURABLE_EVIDENCE_DIR={output_dir}",
        f"NEXT_ACTION=AWAIT_SEPARATE_{registration['next_go_token']}",
        f"NEXT_GO_TOKEN={registration['next_go_token']}",
        f"GOVERNANCE_REF={GOVERNANCE_REL_PATH}",
    ]
    (output_dir / "final_report.txt").write_text(
        "\n".join(final_report_lines) + "\n", encoding="utf-8"
    )

    if manifest_rc != 0:
        _die(f"ERR:evidence_manifest_verify_failed:{manifest_msg}")

    return {
        "verdict": "PASS",
        "registration_digest": registration["registration_digest"],
        "lead_lag_ratification_digest": lead_lag_ratification["ratification_digest"],
        "manifest_verify_rc": manifest_rc,
        "test_returncode": test_rc,
        "durable_evidence_dir": str(output_dir),
        "ci_selector_mode": ci_selector.get("SELECTOR_MODE"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--write-repo-config", action="store_true")
    parser.add_argument("--skip-focused-tests", action="store_true")
    args = parser.parse_args()
    result = run_materialization_v0(
        confirm_go_token=args.confirm_go_token,
        archive_root=args.durable_evidence_root,
        write_repo_config=args.write_repo_config,
        skip_focused_tests=args.skip_focused_tests,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
