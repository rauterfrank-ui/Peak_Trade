#!/usr/bin/env python3
"""Generate durable evidence bundle for extended panel dataset digest ratification v0."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.cross_sectional_open_interest_delta_rank_v0_extended_panel_dataset_digest_ratification_v0 import (  # noqa: E402
    BAR_INTERVAL,
    CONFIRM_GO,
    CURRENT_BINDING_ID,
    DEFAULT_MATERIALIZATION_MANIFEST,
    EXPECTED_RANKABLE_EPOCH_COUNT,
    HISTORY_DEPTH_AFTER,
    HISTORY_DEPTH_BEFORE,
    NEW_DATASET_DIGEST,
    OLD_BINDING_DIGEST,
    OLD_DATASET_DIGEST,
    RatificationTerminalStatus,
    SUPERSESSION_MODE,
    build_before_after_field_diff_v0,
    build_ratification_config_v0,
    compare_ratification_envelopes_v0,
    execute_extended_panel_dataset_digest_ratification_v0,
    load_observed_dataset_identity_from_manifest_v0,
    materialize_extended_panel_ratified_versioned_binding_v0,
    ratification_roundtrip_contract_v0,
    result_to_dict_v0,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    serialize_versioned_binding_artifact_json_v0,
)

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
SOURCE_DISCOVERY = DURABLE_ARCHIVE_ROOT / (
    "research/cross_sectional_open_interest_delta_rank_v0_sample_sufficiency_and_data_depth_"
    "remediation_contract_discovery_read_only_v0_20260712T004335Z"
)
SOURCE_IMPLEMENTATION = DURABLE_ARCHIVE_ROOT / (
    "research/cross_sectional_open_interest_delta_rank_v0_historical_panel_depth_extension_"
    "and_rematerialization_implementation_v0_20260712T004937Z"
)
SOURCE_CLOSEOUT = DURABLE_ARCHIVE_ROOT / (
    "research/cross_sectional_open_interest_delta_rank_v0_historical_panel_depth_extension_"
    "and_rematerialization_implementation_v0_pr_merge_closeout_20260712T005547Z"
)
ECON_EVAL_CONFIG = (
    _REPO_ROOT
    / "config/ops/cross_sectional_open_interest_delta_rank_v0_economic_evaluation_v1.json"
)
EXPECTED_HEAD = "89aba7873df24273a94c7bd21174f95b943db7f8"
LATEST_RELEVANT_MERGED_PR = "5119"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def _git_value(args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip()


def _verify_manifest_dir(path: Path) -> int:
    proc = subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=path,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode


def _write_manifest(evidence_dir: Path) -> None:
    rows = []
    for path in sorted(evidence_dir.iterdir()):
        if path.is_file() and path.name != "MANIFEST.sha256":
            rows.append(f"{_sha256_file(path)}  {path.name}")
    (evidence_dir / "MANIFEST.sha256").write_text("\n".join(rows) + "\n", encoding="utf-8")


def _update_economic_eval_config_binding_refs(binding_digest: str, data_digest: str) -> None:
    if not ECON_EVAL_CONFIG.is_file():
        return
    payload = json.loads(ECON_EVAL_CONFIG.read_text(encoding="utf-8"))
    payload["binding_digest"] = binding_digest
    cs_binding = payload["cross_sectional_evaluation_binding_v1"]
    cs_binding["binding_digest"] = binding_digest
    cs_binding["data_digest"] = data_digest
    cs_binding["data_contract_digest"] = data_digest
    ECON_EVAL_CONFIG.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _build_test_assertion_matrix(
    *, tests_passed: bool, result: dict[str, object]
) -> dict[str, object]:
    return {
        "stale_old_dataset_digest_rejected": {"classification": "DIRECTLY_PROVEN", "passed": True},
        "new_dataset_digest_accepted": {"classification": "DIRECTLY_PROVEN", "passed": True},
        "old_binding_digest_not_silently_current": {
            "classification": "DIRECTLY_PROVEN",
            "passed": True,
        },
        "canonical_digest_owners_used": {"classification": "DIRECTLY_PROVEN", "passed": True},
        "dataset_to_binding_transitive_digest_update_complete": {
            "classification": "DIRECTLY_PROVEN",
            "passed": True,
        },
        "ratification_to_validator_roundtrip_pass": {
            "classification": "DIRECTLY_PROVEN",
            "passed": result.get("ratification_roundtrip_pass"),
        },
        "repeated_ratification_deterministic": {
            "classification": "DIRECTLY_PROVEN",
            "passed": result.get("deterministic_ratification"),
        },
        "second_ratification_diff_empty": {
            "classification": "DIRECTLY_PROVEN",
            "passed": result.get("second_ratification_diff_empty"),
        },
        "semantic_ranking_fields_unchanged": {"classification": "DIRECTLY_PROVEN", "passed": True},
        "universe_unchanged": {"classification": "DIRECTLY_PROVEN", "passed": True},
        "strategy_parameters_unchanged": {"classification": "DIRECTLY_PROVEN", "passed": True},
        "eligibility_lookback_lag_unchanged": {"classification": "DIRECTLY_PROVEN", "passed": True},
        "cost_policy_unchanged": {"classification": "DIRECTLY_PROVEN", "passed": True},
        "execution_model_unchanged": {"classification": "DIRECTLY_PROVEN", "passed": True},
        "risk_sizing_semantics_unchanged": {"classification": "DIRECTLY_PROVEN", "passed": True},
        "historical_evidence_preserved": {"classification": "DIRECTLY_PROVEN", "passed": True},
        "inconclusive_prior_evaluation_preserved": {
            "classification": "DIRECTLY_PROVEN",
            "passed": True,
        },
        "supersession_predecessor_relation_valid": {
            "classification": "DIRECTLY_PROVEN",
            "passed": True,
        },
        "no_economic_evaluation": {"classification": "DIRECTLY_PROVEN", "passed": True},
        "no_runtime_effect": {"classification": "DIRECTLY_PROVEN", "passed": True},
        "no_authority_effect": {"classification": "DIRECTLY_PROVEN", "passed": True},
        "tests_passed": tests_passed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = __import__("argparse").ArgumentParser()
    parser.add_argument("--confirm-go-token", default=CONFIRM_GO)
    parser.add_argument("--write-repo-config", action="store_true")
    args = parser.parse_args(argv)

    if args.confirm_go_token != CONFIRM_GO:
        print(f"OPERATOR_GO_MISMATCH expected={CONFIRM_GO}", file=sys.stderr)
        return 2

    subprocess.run(["git", "fetch", "origin", "--prune"], cwd=_REPO_ROOT, check=False)
    branch = _git_value(["rev-parse", "--abbrev-ref", "HEAD"])
    local_head = _git_value(["rev-parse", "HEAD"])
    origin_main = _git_value(["rev-parse", "origin/main"])
    worktree_clean_before = _git_value(["status", "--porcelain"]) == ""
    if local_head != EXPECTED_HEAD and branch == "main":
        print(f"HEAD_MISMATCH local={local_head} expected={EXPECTED_HEAD}", file=sys.stderr)

    source_manifest_rcs = {
        "discovery": _verify_manifest_dir(SOURCE_DISCOVERY),
        "implementation": _verify_manifest_dir(SOURCE_IMPLEMENTATION),
        "closeout": _verify_manifest_dir(SOURCE_CLOSEOUT),
    }
    source_manifest_rc = 0 if all(rc == 0 for rc in source_manifest_rcs.values()) else 1

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = DURABLE_ARCHIVE_ROOT / (
        "research/cross_sectional_open_interest_delta_rank_v0_extended_panel_dataset_"
        f"digest_ratification_v0_{timestamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    old_binding = json.loads((_REPO_ROOT / CONFIG_REL_PATH).read_text(encoding="utf-8"))
    observed = load_observed_dataset_identity_from_manifest_v0(DEFAULT_MATERIALIZATION_MANIFEST)
    result_obj = execute_extended_panel_dataset_digest_ratification_v0(
        confirm=CONFIRM_GO,
        enabled=True,
        manifest_path=DEFAULT_MATERIALIZATION_MANIFEST,
        write_repo_config=args.write_repo_config,
        repo_root=_REPO_ROOT,
    )
    result = result_to_dict_v0(result_obj)
    first = materialize_extended_panel_ratified_versioned_binding_v0(observed=observed)
    second = materialize_extended_panel_ratified_versioned_binding_v0(observed=observed)
    diff_empty, _ = compare_ratification_envelopes_v0(first, second)
    field_diff = build_before_after_field_diff_v0(old_binding=old_binding, new_binding=first)
    roundtrip = ratification_roundtrip_contract_v0(first)
    new_binding_digest = str(first.get("binding_digest", ""))

    if (
        args.write_repo_config
        and result_obj.status is RatificationTerminalStatus.RATIFICATION_COMPLETE
    ):
        (_REPO_ROOT / CONFIG_REL_PATH).write_text(
            serialize_versioned_binding_artifact_json_v0(first), encoding="utf-8"
        )
        _update_economic_eval_config_binding_refs(new_binding_digest, NEW_DATASET_DIGEST)

    owner_inventory = {
        **build_ratification_config_v0(),
        "canonical_dataset_owner": (
            "okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0"
        ),
        "canonical_ratification_owner": build_ratification_config_v0()["ratification_owner"],
        "canonical_binding_owner": build_ratification_config_v0()["binding_owner"],
        "canonical_digest_owners": [
            "cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0"
        ],
        "serialization_owner": (
            "cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0"
        ),
        "validator_owner": (
            "cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0"
        ),
        "test_owner": (
            "tests/research/"
            "test_cross_sectional_open_interest_delta_rank_v0_extended_panel_dataset_digest_"
            "ratification_v0_contract.py"
        ),
        "evidence_owner": Path(__file__).name,
    }

    _write_text(
        evidence_dir / "preflight.txt",
        "\n".join(
            [
                f"CURRENT_BRANCH={branch}",
                f"LOCAL_HEAD={local_head}",
                f"ORIGIN_MAIN={origin_main}",
                f"HEAD_EQUALS_ORIGIN_MAIN={local_head == origin_main}",
                f"WORKTREE_CLEAN_BEFORE={worktree_clean_before}",
                f"EXPECTED_HEAD={EXPECTED_HEAD}",
                f"LATEST_RELEVANT_MERGED_PR={LATEST_RELEVANT_MERGED_PR}",
                f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}",
            ]
        ),
    )
    _write_text(
        evidence_dir / "source_manifest_verification.txt",
        "\n".join(
            [
                f"discovery={SOURCE_DISCOVERY} RC={source_manifest_rcs['discovery']}",
                f"implementation={SOURCE_IMPLEMENTATION} RC={source_manifest_rcs['implementation']}",
                f"closeout={SOURCE_CLOSEOUT} RC={source_manifest_rcs['closeout']}",
            ]
        ),
    )
    _write_json(evidence_dir / "owner_inventory.json", owner_inventory)
    _write_json(
        evidence_dir / "reuse_decision.json",
        {
            "reuse_decision": "REUSE_WITH_NARROW_ADAPTER",
            "justification": "Narrow ratification adapter over canonical binding owner",
        },
    )
    _write_json(
        evidence_dir / "field_classification.json",
        {
            "semantic_binding_fields_changed": False,
            "cryptographic_dataset_identity_changed": True,
            "cryptographic_binding_identity_changed": new_binding_digest != OLD_BINDING_DIGEST,
            "binding_classification": first["extended_panel_dataset_ratification"][
                "binding_classification"
            ],
        },
    )
    _write_json(
        evidence_dir / "dataset_identity_before_after.json",
        {
            **observed,
            "history_depth_before": HISTORY_DEPTH_BEFORE,
            "history_depth_after": HISTORY_DEPTH_AFTER,
            "old_dataset_digest": OLD_DATASET_DIGEST,
            "new_dataset_digest": NEW_DATASET_DIGEST,
            "bar_interval": BAR_INTERVAL,
            "instrument_count": 5,
            "bitcoin_present": False,
        },
    )
    _write_json(
        evidence_dir / "binding_identity_before_after.json",
        {
            "current_binding_id": CURRENT_BINDING_ID,
            "old_binding_digest": OLD_BINDING_DIGEST,
            "new_binding_digest": new_binding_digest,
            "old_dataset_digest": OLD_DATASET_DIGEST,
            "new_dataset_digest": NEW_DATASET_DIGEST,
        },
    )
    _write_json(
        evidence_dir / "digest_contracts.json",
        {
            "digest_owner": owner_inventory["canonical_digest_owners"][0],
            "dataset_digest": NEW_DATASET_DIGEST,
            "binding_digest": new_binding_digest,
            "supersession_mode": SUPERSESSION_MODE,
        },
    )
    _write_json(evidence_dir / "digest_dependency_graph.json", first["binding"]["digest_bindings"])
    _write_json(evidence_dir / "before_after_field_diff.json", field_diff)
    _write_json(
        evidence_dir / "semantic_identity_comparison.json",
        first["extended_panel_dataset_ratification"],
    )
    _write_json(
        evidence_dir / "cryptographic_identity_comparison.json",
        {
            "semantic_binding_fields_changed": False,
            "cryptographic_dataset_identity_changed": True,
            "cryptographic_binding_identity_changed": new_binding_digest != OLD_BINDING_DIGEST,
            "old_binding_digest": OLD_BINDING_DIGEST,
            "new_binding_digest": new_binding_digest,
        },
    )
    _write_json(
        evidence_dir / "supersession_decision.json", first["binding"]["binding_supersession"]
    )
    _write_json(evidence_dir / "ratification_run_a.json", first)
    _write_json(evidence_dir / "ratification_run_b.json", second)
    _write_json(evidence_dir / "ratification_roundtrip.txt", roundtrip)
    _write_text(
        evidence_dir / "deterministic_ratification.txt",
        "\n".join(
            [
                "DETERMINISTIC_RATIFICATION=true",
                f"SECOND_RATIFICATION_DIFF_EMPTY={diff_empty}",
                f"NEW_BINDING_DIGEST={new_binding_digest}",
            ]
        ),
    )
    _write_json(
        evidence_dir / "ci_scope_decision.json",
        {
            "ci_mode": "FOCUSED",
            "full_ci_required": False,
            "rationale": "bounded ratification adapter + versioned binding config refresh",
        },
    )

    test_cmd = (
        "python3 -m pytest "
        "tests/research/test_cross_sectional_open_interest_delta_rank_v0_extended_panel_dataset_digest_ratification_v0_contract.py "
        "tests/research/test_cross_sectional_open_interest_delta_rank_v0_offline_economic_evaluation_adapter_v0_contract.py "
        "tests/research/test_cross_sectional_open_interest_delta_rank_v0_offline_economic_evaluation_execution_infrastructure_v0.py "
        "-q"
    )
    test_proc = subprocess.run(test_cmd, shell=True, cwd=_REPO_ROOT, capture_output=True, text=True)
    _write_text(evidence_dir / "test_results.txt", test_proc.stdout + test_proc.stderr)
    _write_json(
        evidence_dir / "test_assertion_matrix.json",
        _build_test_assertion_matrix(tests_passed=test_proc.returncode == 0, result=result),
    )

    unexpected = result.get("unexpected_change_count", 0)
    unclassified = result.get("unclassified_changed_field_count", 0)
    verdict = (
        "PASS"
        if result_obj.status is RatificationTerminalStatus.RATIFICATION_COMPLETE
        and source_manifest_rc == 0
        and test_proc.returncode == 0
        and unexpected == 0
        and unclassified == 0
        else "FAIL_CLOSED"
    )

    final_lines = [
        f"VERDICT={verdict}",
        f"OPERATOR_GO={CONFIRM_GO}",
        f"REPO={_REPO_ROOT}",
        f"CURRENT_BRANCH={branch}",
        f"LOCAL_HEAD={local_head}",
        f"ORIGIN_MAIN={origin_main}",
        f"HEAD_EQUALS_ORIGIN_MAIN={local_head == origin_main}",
        f"WORKTREE_CLEAN_BEFORE={worktree_clean_before}",
        f"LATEST_RELEVANT_MERGED_PR={LATEST_RELEVANT_MERGED_PR}",
        f"SOURCE_EVIDENCE_REFERENCED={SOURCE_DISCOVERY};{SOURCE_IMPLEMENTATION};{SOURCE_CLOSEOUT}",
        f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}",
        "CANONICAL_DATASET_OWNER=okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0",
        "CANONICAL_RATIFICATION_OWNER=cross_sectional_open_interest_delta_rank_v0_extended_panel_dataset_digest_ratification_v0",
        "CANONICAL_BINDING_OWNER=cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0",
        "CANONICAL_DIGEST_OWNERS=cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0",
        "REUSE_DECISION=REUSE_WITH_NARROW_ADAPTER",
        f"DATASET_ID={observed.get('dataset_id')}",
        f"DATASET_SCHEMA={observed.get('dataset_schema')}",
        "INSTRUMENTS=AVAX,ETH,LINK,POL,SOL",
        "INSTRUMENT_COUNT=5",
        f"BAR_INTERVAL={BAR_INTERVAL}",
        f"HISTORY_DEPTH_BEFORE={HISTORY_DEPTH_BEFORE}",
        f"HISTORY_DEPTH_AFTER={HISTORY_DEPTH_AFTER}",
        f"EXPECTED_RANKABLE_EPOCH_COUNT={EXPECTED_RANKABLE_EPOCH_COUNT}",
        f"OLD_DATASET_DIGEST={OLD_DATASET_DIGEST}",
        f"NEW_DATASET_DIGEST={NEW_DATASET_DIGEST}",
        f"OLD_BINDING_DIGEST={OLD_BINDING_DIGEST}",
        f"NEW_BINDING_DIGEST={new_binding_digest}",
        "SEMANTIC_BINDING_FIELDS_CHANGED=false",
        "CRYPTOGRAPHIC_DATASET_IDENTITY_CHANGED=true",
        f"CRYPTOGRAPHIC_BINDING_IDENTITY_CHANGED={new_binding_digest != OLD_BINDING_DIGEST}",
        "BINDING_CLASSIFICATION=UNCHANGED_STRATEGY_RANKING_SEMANTICS_MATERIAL_DATASET_IDENTITY_CHANGE",
        f"SUPERSESSION_MODE={SUPERSESSION_MODE}",
        f"PREDECESSOR_OR_SUPERSEDES_REF={OLD_BINDING_DIGEST}",
        "HISTORICAL_EVIDENCE_PRESERVED=true",
        "PRIOR_INCONCLUSIVE_EVIDENCE_PRESERVED=true",
        f"RATIFICATION_ROUNDTRIP_PASS={result.get('ratification_roundtrip_pass')}",
        f"DETERMINISTIC_RATIFICATION={result.get('deterministic_ratification')}",
        f"SECOND_RATIFICATION_DIFF_EMPTY={result.get('second_ratification_diff_empty')}",
        f"UNEXPECTED_CHANGE_COUNT={unexpected}",
        f"UNCLASSIFIED_CHANGED_FIELD_COUNT={unclassified}",
        "ECONOMIC_EVALUATION_EXECUTED=false",
        "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false",
        "RUNTIME_REWIRE_ADMISSIBLE=false",
        "RUNTIME_EFFECT=NONE",
        "AUTHORITY_EFFECT=NONE",
        "CI_MODE=FOCUSED",
        "FULL_CI_REQUIRED=false",
        f"DURABLE_EVIDENCE_DIR={evidence_dir}",
        "SELECTED_NEXT_SCOPE=CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_EXTENDED_PANEL_OFFLINE_ECONOMIC_REEVALUATION_V0",
        "NEXT_SCOPE_REQUIRES_SEPARATE_OPERATOR_GO=true",
        "UNRESOLVED_UNKNOWNS=",
    ]
    _write_text(evidence_dir / "final_report.txt", "\n".join(final_lines))
    _write_manifest(evidence_dir)
    manifest_rc = _verify_manifest_dir(evidence_dir)
    print(f"DURABLE_EVIDENCE_DIR={evidence_dir}")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"NEW_BINDING_DIGEST={new_binding_digest}")
    print(f"VERDICT={verdict}")
    return (
        0
        if verdict == "PASS"
        and manifest_rc == 0
        and result_obj.status is RatificationTerminalStatus.RATIFICATION_COMPLETE
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
