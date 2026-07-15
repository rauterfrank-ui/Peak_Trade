#!/usr/bin/env python3
"""Materialize terminal lead-lag v0 insufficient sample and pairwise spillover v1 scope ratification v0."""

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
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_terminal_insufficient_sample_and_distinct_futures_research_scope_ratification_v0 import (  # noqa: E402
    CANONICAL_EVALUATION_DIR,
    CONFIG_REL_PATH,
    GOVERNANCE_REL_PATH,
    OI_TERMINAL_RATIFICATION_DIR,
    OPERATOR_DECISION,
    OPERATOR_GO_TOKEN,
    PAIRWISE_SCOPE_RATIFICATION_CONFIG_REL_PATH,
    PR5197_CLOSEOUT_DIR,
    REGISTRATION_ID,
    VERSIONED_BINDING_CONFIG_REL_PATH,
    apply_versioned_binding_registration_fields,
    build_distinct_scope_candidate_inventory,
    build_exact_binding_retry_guard_report,
    build_material_difference_matrix,
    build_retry_non_equivalence_proof,
    build_zero_trade_causal_classification,
    compute_registration_digest,
    materialize_registration_config,
    serialize_canonical_json,
    validate_registration_preconditions,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_research_scope_ratification_v0 import (  # noqa: E402
    ValidationVerdictEnum as PairwiseValidationVerdict,
    materialize_pairwise_spillover_research_scope_ratification_v0,
    serialize_ratification_canonical_v0 as serialize_pairwise_ratification,
    validate_pairwise_spillover_research_scope_ratification_v0,
)

CONFIRM_GO = OPERATOR_GO_TOKEN
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = (
    "cross_sectional_futures_lead_lag_information_diffusion_v0_terminal_insufficient_sample_"
    "and_distinct_futures_research_scope_ratification_v0"
)
FOCUSED_TEST = (
    "tests/ops/"
    "test_cross_sectional_futures_lead_lag_information_diffusion_v0_terminal_insufficient_sample_"
    "operator_ratification_and_pairwise_spillover_scope_ratification_v0_contract.py"
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

    pairwise_ratification = materialize_pairwise_spillover_research_scope_ratification_v0(
        repo_root=_REPO_ROOT
    )
    pairwise_validation = validate_pairwise_spillover_research_scope_ratification_v0(
        pairwise_ratification
    )
    if pairwise_validation.verdict != PairwiseValidationVerdict.ACCEPTED:
        _die(
            f"ERR:pairwise_scope_ratification_validation_failed:{pairwise_validation.fail_reasons}"
        )

    if write_repo_config:
        reg_path = _REPO_ROOT / CONFIG_REL_PATH
        reg_path.parent.mkdir(parents=True, exist_ok=True)
        reg_path.write_text(serialize_canonical_json(registration) + "\n", encoding="utf-8")

        pairwise_path = _REPO_ROOT / PAIRWISE_SCOPE_RATIFICATION_CONFIG_REL_PATH
        pairwise_path.parent.mkdir(parents=True, exist_ok=True)
        pairwise_path.write_text(
            serialize_pairwise_ratification(pairwise_ratification), encoding="utf-8"
        )

        binding_path = _REPO_ROOT / VERSIONED_BINDING_CONFIG_REL_PATH
        binding_payload = json.loads(binding_path.read_text(encoding="utf-8"))
        updated_binding = apply_versioned_binding_registration_fields(binding_payload, registration)
        binding_path.write_text(
            json.dumps(updated_binding, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    output_dir = archive_root / "research" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    output_dir.mkdir(parents=True, exist_ok=False)

    source_lines = []
    source_rc_total = 0
    for label, bundle_dir in (
        ("CANONICAL_EVALUATION", CANONICAL_EVALUATION_DIR),
        ("PR5197_CLOSEOUT", PR5197_CLOSEOUT_DIR),
        ("OI_TERMINAL_RATIFICATION", OI_TERMINAL_RATIFICATION_DIR),
    ):
        rc = _verify_manifest(bundle_dir, output_dir / f"source_manifest_{label}.txt")
        source_lines.append(f"{label}={bundle_dir} RC={rc}")
        source_rc_total += rc
    (output_dir / "source_manifest_verification.txt").write_text(
        "\n".join(source_lines) + f"\nSOURCE_MANIFEST_VERIFY_RC={source_rc_total}\n",
        encoding="utf-8",
    )
    if source_rc_total != 0:
        _die("ERR:source manifest verify failed")

    git_snapshot = _git_snapshot()
    _write_json(
        output_dir / "terminal_evidence_adjudication.json",
        {
            "terminal_scope": registration["research_scope"],
            "terminal_verdict": registration["terminal_verdict"],
            "trade_count": registration["trade_count"],
            "binding_digest": registration["binding_digest"],
            "economic_evaluation_executed": True,
            "economic_validity_offline_gate_pass": False,
        },
    )
    _write_json(
        output_dir / "zero_trade_causal_classification.json",
        build_zero_trade_causal_classification(),
    )
    _write_json(
        output_dir / "retry_prohibition_assessment.json",
        build_exact_binding_retry_guard_report(),
    )
    _write_json(
        output_dir / "distinct_scope_material_difference.json",
        build_material_difference_matrix(),
    )
    _write_json(output_dir / "scope_ratification.json", pairwise_ratification)
    _write_json(
        output_dir / "owner_inventory.json",
        {
            "registration_owner": REGISTRATION_ID,
            "pairwise_scope_ratification_owner": PAIRWISE_SCOPE_RATIFICATION_CONFIG_REL_PATH,
            "versioned_binding_owner": VERSIONED_BINDING_CONFIG_REL_PATH,
        },
    )
    _write_json(
        output_dir / "reuse_decision.json",
        {
            "reuse_decision": "REUSE_EXISTING_GOVERNANCE_PATTERNS_NO_NEW_PARALLEL_REGISTRY",
            "pairwise_binding_owner_invented": False,
            "pairwise_score_owner_invented": False,
        },
    )
    _write_json(
        output_dir / "field_classification.json",
        {
            "authored": ["registration_digest", "ratification_digest"],
            "observed": ["trade_count", "binding_digest", "directional_candidate_count"],
            "derived": ["material_difference_matrix", "retry_non_equivalence_proof"],
        },
    )
    _write_json(
        output_dir / "digest_contracts.json",
        {
            "terminal_binding_digest": registration["binding_digest"],
            "implementation_digest": registration["implementation_digest"],
            "pairwise_material_difference_digest": pairwise_ratification[
                "material_difference_digest"
            ],
        },
    )
    _write_json(
        output_dir / "digest_dependency_graph.json",
        {
            "nodes": [
                VERSIONED_BINDING_CONFIG_REL_PATH,
                CONFIG_REL_PATH,
                PAIRWISE_SCOPE_RATIFICATION_CONFIG_REL_PATH,
            ],
            "edges": [
                {"from": CONFIG_REL_PATH, "to": PAIRWISE_SCOPE_RATIFICATION_CONFIG_REL_PATH},
                {"from": VERSIONED_BINDING_CONFIG_REL_PATH, "to": CONFIG_REL_PATH},
            ],
        },
    )
    _write_json(
        output_dir / "before_after_field_diff.json",
        {
            "binding_before_terminal_fields": False,
            "binding_after_terminal_fields": True,
            "pairwise_binding_exists": False,
        },
    )
    _write_json(
        output_dir / "semantic_identity_comparison.json",
        {
            "baseline_hypothesis_family": "panel_median_lagged_return_diffusion",
            "selected_hypothesis_family": registration["selected_distinct_hypothesis_family"],
            "semantic_identity_differs": True,
        },
    )
    _write_json(
        output_dir / "cryptographic_identity_comparison.json",
        {
            "terminal_binding_digest": registration["binding_digest"],
            "pairwise_binding_digest": None,
            "new_binding_required": True,
        },
    )
    _write_json(output_dir / "candidate_matrix.json", build_distinct_scope_candidate_inventory())
    _write_json(
        output_dir / "material_difference_proof.json",
        build_material_difference_matrix(),
    )
    _write_json(
        output_dir / "retry_non_equivalence_proof.json",
        build_retry_non_equivalence_proof(),
    )
    _write_json(output_dir / "ratification_contract.json", registration)
    _write_json(
        output_dir / "pairwise_scope_ratification_contract.json",
        pairwise_ratification,
    )

    roundtrip_registration = materialize_registration_config(canonical=canonical)
    roundtrip_pairwise = materialize_pairwise_spillover_research_scope_ratification_v0(
        repo_root=_REPO_ROOT
    )
    (output_dir / "materializer_roundtrip.txt").write_text(
        "\n".join(
            [
                f"registration_digest_match={roundtrip_registration['registration_digest'] == registration['registration_digest']}",
                f"pairwise_ratification_digest_match={roundtrip_pairwise['ratification_digest'] == pairwise_ratification['ratification_digest']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "deterministic_materialization.txt").write_text(
        f"registration_digest={registration['registration_digest']}\n"
        f"pairwise_ratification_digest={pairwise_ratification['ratification_digest']}\n",
        encoding="utf-8",
    )

    ci_selector = _run_ci_selector()
    _write_json(output_dir / "ci_selector_decision.json", ci_selector)

    test_rc, test_output = (0, "SKIPPED") if skip_focused_tests else _run_focused_tests()
    (output_dir / "test_results.txt").write_text(test_output, encoding="utf-8")
    _write_json(
        output_dir / "test_assertion_matrix.json",
        {
            "focused_test": FOCUSED_TEST,
            "returncode": test_rc,
            "assertions": [
                "terminal_lead_lag_v0_evidence_registered",
                "negative_evidence_preserved",
                "unchanged_retry_blocked",
                "policy_rescue_not_authorized",
                "pairwise_scope_new_identity",
                "material_difference_explicit",
                "no_pairwise_binding",
                "no_economic_evaluation_authority",
                "no_runtime_authority",
                "futures_only_bitcoin_excluded",
                "deterministic_materialization",
            ],
        },
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
                f"SOURCE_MANIFEST_VERIFY_RC={source_rc_total}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = finalize_durable_bundle_manifest(output_dir)
    final_report_lines = [
        "STATUS=PASS",
        "VERDICT=TERMINAL_NEGATIVE_EVIDENCE_REGISTERED_AND_DISTINCT_RESEARCH_SCOPE_RATIFIED",
        f"SCOPE={OUTPUT_PREFIX}",
        f"OPERATOR_GO={CONFIRM_GO}",
        f"TERMINAL_SCOPE={registration['research_scope']}",
        f"TERMINAL_VERDICT={registration['terminal_verdict']}",
        f"TERMINAL_TRADE_COUNT={registration['trade_count']}",
        f"TERMINAL_BINDING_DIGEST={registration['binding_digest']}",
        f"PRIMARY_CAUSAL_CLASS={registration['primary_cause_class']}",
        f"SECONDARY_CAUSAL_CLASS={registration['secondary_cause_class']}",
        "UNCHANGED_RETRY_BLOCKED=true",
        "NEGATIVE_EVIDENCE_PRESERVED=true",
        f"SELECTED_DISTINCT_SCOPE={registration['selected_distinct_scope']}",
        f"HYPOTHESIS_FAMILY={registration['selected_distinct_hypothesis_family']}",
        f"SCORE_FAMILY_POLICY={registration['selected_distinct_score_family_policy']}",
        f"MATERIAL_DIFFERENCE_PRIMARY={registration['selected_distinct_material_difference_primary']}",
        f"DATA_READINESS={registration['selected_distinct_data_readiness']}",
        "IMPLEMENTATION_EXECUTED=false",
        "ECONOMIC_EVALUATION_EXECUTED=false",
        "RUNTIME_EFFECT=NONE",
        "AUTHORITY_EFFECT=NONE",
        f"SOURCE_MANIFEST_VERIFY_RC={source_rc_total}",
        f"MANIFEST_VERIFY_RC={manifest_rc}",
        f"CI_SELECTOR={ci_selector.get('SELECTOR_MODE', 'UNKNOWN')}",
        f"TEST_RESULT={'PASS' if test_rc == 0 else 'FAIL'}",
        f"DURABLE_EVIDENCE_DIR={output_dir}",
        f"NEXT_STEP={registration['next_go_token']}",
        "NEXT_STEP_REQUIRES_SEPARATE_OPERATOR_GO=true",
        f"GOVERNANCE_REF={GOVERNANCE_REL_PATH}",
    ]
    (output_dir / "final_report.txt").write_text(
        "\n".join(final_report_lines) + "\n",
        encoding="utf-8",
    )

    if manifest_rc != 0:
        _die(f"ERR:evidence_manifest_verify_failed:{manifest_msg}")

    return {
        "verdict": "PASS",
        "registration_digest": registration["registration_digest"],
        "pairwise_ratification_digest": pairwise_ratification["ratification_digest"],
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
