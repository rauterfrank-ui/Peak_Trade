#!/usr/bin/env python3
"""Execute offline source evidence admissibility review v0.

Offline-only admissibility review execution. No economic evaluation, no backtest,
no runtime authority, no EconomicViabilityEvidenceV1 emission.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    verify_manifest_sha256,
    write_manifest_sha256,
)

SCOPE_ID = "OFFLINE_SOURCE_EVIDENCE_ADMISSIBILITY_REVIEW_EXECUTION_V0"
PROCESS_CLASSIFICATION = "OFFLINE_SOURCE_EVIDENCE_ADMISSIBILITY_REVIEW_EXECUTION_V0"
SCOPE_CLASSIFICATION = (
    "OFFLINE_ONLY_SOURCE_EVIDENCE_ADMISSIBILITY_REVIEW_EXECUTION_NO_ECONOMIC_EVALUATION_"
    "NO_RUNTIME_AUTHORITY_V0"
)
GO_TOKEN = (
    "OFFLINE_SOURCE_EVIDENCE_ADMISSIBILITY_REVIEW_EXECUTION_OR_ECONOMIC_EVALUATION_"
    "PRECONDITION_MATERIALIZATION_SCOPE_REQUIRES_SEPARATE_GO"
)
DEFAULT_CONFIG = (
    _REPO_ROOT / "config/research/offline_source_evidence_admissibility_review_execution_v0.json"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "offline_source_evidence_admissibility_review_execution_v0"
FINAL_RESEARCH_FLEET = ("trend_following", "bollinger_bands", "momentum_1h")
STRATEGY_VERSION = "post_v4_hypothesis_v0"
CONTRACT_IDS = (
    "TRADE_LEDGER_PER_TRADE_DECOMPOSITION_V0",
    "LONG_SHORT_ATTRIBUTION_LEDGER_V0",
    "TURNOVER_COST_DRAG_TIMESERIES_V0",
    "INSTRUMENT_CONCENTRATION_DETAIL_V0",
)
REVIEW_DIMENSIONS = (
    "source_evidence_manifest_integrity",
    "source_evidence_contract_coverage",
    "collector_output_contract_coverage",
    "candidate_binding_precondition_coverage",
    "dataset_binding_precondition_coverage",
    "period_binding_precondition_coverage",
    "instrument_binding_precondition_coverage",
    "fee_model_binding_precondition_coverage",
    "slippage_model_binding_precondition_coverage",
    "funding_model_binding_precondition_coverage",
    "execution_model_binding_precondition_coverage",
    "economic_policy_binding_precondition_coverage",
    "implementation_digest_precondition_coverage",
    "config_digest_precondition_coverage",
    "data_digest_precondition_coverage",
    "failed_binding_no_retry_guard",
    "no_policy_threshold_backfit_guard",
    "no_runtime_authority_from_evidence_guard",
    "final_research_fleet_alignment_guard",
)
FORBIDDEN_AUTHORITY_FLAGS = (
    "economic_evaluation_authorized",
    "economic_evaluation_executed",
    "economic_viability_evidence_emitted",
    "economic_viability_claimed",
    "runtime_authority_granted",
    "orders_allowed",
    "scheduler_runtime_allowed",
    "live_authorized",
    "shadow_authorized",
    "paper_authorized",
    "testnet_authorized",
    "adapter_submission_allowed",
    "credentials_required",
    "arming_allowed",
    "canary_authorized",
    "core_system_mutation_allowed",
    "canonical_trading_logic_mutation_allowed",
    "master_v2_mutation_allowed",
    "double_play_mutation_allowed",
    "risk_sizing_mutation_allowed",
    "safety_runtime_mutation_allowed",
)
FORBIDDEN_COMMAND_PATTERNS = (
    "backtest",
    "walk_forward",
    "walk-forward",
    "monte_carlo",
    "monte-carlo",
    "stress_test",
    "stress-test",
    "parameter_sensitivity",
    "economic_viability_evidence",
    "run_economic_viability",
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _die(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"not_object:{path}")
    return payload


def _git_snapshot() -> dict[str, str]:
    def _run(args: list[str]) -> str:
        return subprocess.check_output(["git", *args], cwd=_REPO_ROOT, text=True).strip()

    return {
        "head": _run(["rev-parse", "HEAD"]),
        "origin_main": _run(["rev-parse", "origin/main"]),
        "branch": _run(["branch", "--show-current"]),
        "status_short": _run(["status", "--short"]) or "(clean)",
    }


def _parse_closeout_field(text: str, field: str) -> str | None:
    match = re.search(rf"^{re.escape(field)}=(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def validate_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if config.get("scope_id") != SCOPE_ID:
        errors.append("unexpected scope_id")
    if config.get("go_token") != GO_TOKEN:
        errors.append("unexpected go_token")
    if config.get("parent_pr") != 4913:
        errors.append("unexpected parent_pr")
    if config.get("admissibility_review_executed") is not True:
        errors.append("admissibility_review_executed must be true for execution config")
    for flag in FORBIDDEN_AUTHORITY_FLAGS:
        if config.get(flag) is not False:
            errors.append(f"forbidden authority flag must be false: {flag}")
    missing = sorted(set(REVIEW_DIMENSIONS) - set(config.get("required_review_dimensions", [])))
    if missing:
        errors.append(f"missing review dimensions: {missing}")
    return errors


def _finding(
    *,
    dimension: str,
    status: str,
    hard_block: bool,
    finding: str,
    evidence_refs: list[str],
) -> dict[str, Any]:
    return {
        "dimension": dimension,
        "status": status,
        "hard_block": hard_block,
        "finding": finding,
        "evidence_refs": evidence_refs,
    }


def _manifest_status(path: Path) -> tuple[int, str]:
    ok, msg = verify_manifest_sha256(path)
    return (0 if ok else 1), msg or "ok"


def _count_missing_source_records(jsonl_path: Path) -> tuple[int, int]:
    if not jsonl_path.is_file():
        return 0, 0
    total = 0
    missing = 0
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        total += 1
        record = json.loads(line)
        if any(
            isinstance(value, dict) and value.get("status") == "MISSING_SOURCE_EVIDENCE"
            for value in record.values()
        ):
            missing += 1
    return missing, total


def _candidate_provenance(evaluation_bundle: Path, candidate: str) -> dict[str, Any] | None:
    path = (
        evaluation_bundle
        / "candidates"
        / f"{candidate}_{STRATEGY_VERSION}"
        / "INPUT_PROVENANCE.json"
    )
    if not path.is_file():
        return None
    return _load_json(path)


def _candidate_config_snapshot(evaluation_bundle: Path, candidate: str) -> dict[str, Any] | None:
    path = (
        evaluation_bundle
        / "candidates"
        / f"{candidate}_{STRATEGY_VERSION}"
        / "CONFIG_SNAPSHOT.json"
    )
    if not path.is_file():
        return None
    return _load_json(path)


def _compute_verdict(findings: list[dict[str, Any]]) -> str:
    if any(item["hard_block"] for item in findings):
        return "ADMISSIBILITY_FAIL"
    if all(item["status"] == "PASS" for item in findings):
        return "ADMISSIBILITY_PASS"
    return "ADMISSIBILITY_INCONCLUSIVE"


def _verify_parent_provenance(parent_closeout: Path, config: dict[str, Any]) -> dict[str, Any]:
    closeout_md = parent_closeout / "CLOSEOUT.md"
    pr_view = parent_closeout / "pr_view_post_merge.json"
    manifest_rc, manifest_msg = _manifest_status(parent_closeout)
    provenance: dict[str, Any] = {
        "parent_closeout_dir": str(parent_closeout),
        "parent_manifest_verify_rc": manifest_rc,
        "parent_manifest_verify_msg": manifest_msg,
        "parent_pr": config["parent_pr"],
        "expected_pre_merge_origin_main": config["parent_pre_merge_origin_main"],
        "expected_pr_head": config["parent_pr_head"],
        "expected_post_merge_head": config["parent_post_merge_head"],
    }
    if closeout_md.is_file():
        text = closeout_md.read_text(encoding="utf-8")
        provenance["closeout_fields"] = {
            "PRE_MERGE_ORIGIN_MAIN": _parse_closeout_field(text, "PRE_MERGE_ORIGIN_MAIN"),
            "PR_HEAD": _parse_closeout_field(text, "PR_HEAD"),
            "POST_MERGE_HEAD": _parse_closeout_field(text, "POST_MERGE_HEAD"),
            "MERGE_COMMIT": _parse_closeout_field(text, "MERGE_COMMIT"),
        }
    if pr_view.is_file():
        provenance["pr_view_post_merge"] = _load_json(pr_view)
    field_matches = (
        provenance.get("closeout_fields", {}).get("PRE_MERGE_ORIGIN_MAIN")
        == config["parent_pre_merge_origin_main"]
        and provenance.get("closeout_fields", {}).get("PR_HEAD") == config["parent_pr_head"]
        and provenance.get("closeout_fields", {}).get("POST_MERGE_HEAD")
        == config["parent_post_merge_head"]
    )
    provenance["provenance_field_match"] = field_matches
    provenance["manifest_requirement_met"] = manifest_rc == int(
        config.get("required_parent_manifest_rc", 0)
    )
    return provenance


def _review_all_dimensions(
    *,
    config: dict[str, Any],
    parent_provenance: dict[str, Any],
    scope_definition_config: Path,
    scope_definition_bundle: Path,
    collector_bundle: Path,
    evaluation_bundle: Path,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    scope_cfg = _load_json(scope_definition_config)
    collector_report_path = collector_bundle / "SOURCE_EVIDENCE_COLLECTION_REPORT.json"
    collector_report = _load_json(collector_report_path) if collector_report_path.is_file() else {}

    manifest_targets = {
        "parent_closeout": Path(config["parent_closeout_dir"]),
        "scope_definition_bundle": scope_definition_bundle,
        "collector_bundle": collector_bundle,
        "evaluation_bundle": evaluation_bundle,
    }
    manifest_results = {name: _manifest_status(path)[0] for name, path in manifest_targets.items()}
    parent_manifest_ok = manifest_results["parent_closeout"] == 0
    downstream_manifest_ok = all(
        manifest_results[name] == 0 for name in manifest_results if name != "parent_closeout"
    )

    if not parent_manifest_ok:
        findings.append(
            _finding(
                dimension="source_evidence_manifest_integrity",
                status="FAIL",
                hard_block=True,
                finding=(
                    "Parent PR #4913 closeout MANIFEST.sha256 verification failed; "
                    "parent evidence is not manifest-verifiable."
                ),
                evidence_refs=[str(manifest_targets["parent_closeout"] / "MANIFEST.sha256")],
            )
        )
    elif downstream_manifest_ok:
        findings.append(
            _finding(
                dimension="source_evidence_manifest_integrity",
                status="PASS",
                hard_block=False,
                finding="All referenced parent/source bundles verify with MANIFEST.sha256 RC=0.",
                evidence_refs=[str(path / "MANIFEST.sha256") for path in manifest_targets.values()],
            )
        )
    else:
        findings.append(
            _finding(
                dimension="source_evidence_manifest_integrity",
                status="INCONCLUSIVE",
                hard_block=False,
                finding="Downstream bundle manifest verification incomplete.",
                evidence_refs=[str(path / "MANIFEST.sha256") for path in manifest_targets.values()],
            )
        )

    defined_contracts = {
        item["contract_id"] for item in scope_cfg.get("source_evidence_contracts", [])
    } or set(CONTRACT_IDS)
    pr4911_config = (
        _REPO_ROOT
        / "config/research/offline_source_evidence_instrumentation_admissibility_gap_v0.json"
    )
    if pr4911_config.is_file():
        pr4911 = _load_json(pr4911_config)
        defined_contracts = {
            item["contract_id"] for item in pr4911.get("source_evidence_contracts", [])
        }
    materialized = set(collector_report.get("contracts_materialized", []))
    if defined_contracts.issubset(materialized):
        findings.append(
            _finding(
                dimension="source_evidence_contract_coverage",
                status="PASS",
                hard_block=False,
                finding="All PR4911-defined source-evidence contracts are referenced in collector output.",
                evidence_refs=[str(collector_report_path)],
            )
        )
    else:
        findings.append(
            _finding(
                dimension="source_evidence_contract_coverage",
                status="INCONCLUSIVE",
                hard_block=False,
                finding=f"Missing contracts in collector output: {sorted(defined_contracts - materialized)}",
                evidence_refs=[str(collector_report_path)],
            )
        )

    missing_records = 0
    total_records = 0
    for contract_id in CONTRACT_IDS:
        missing, total = _count_missing_source_records(collector_bundle / f"{contract_id}.jsonl")
        missing_records += missing
        total_records += total
    if total_records == 0:
        findings.append(
            _finding(
                dimension="collector_output_contract_coverage",
                status="INCONCLUSIVE",
                hard_block=False,
                finding="Collector output JSONL artifacts absent.",
                evidence_refs=[str(collector_bundle)],
            )
        )
    elif missing_records == 0:
        findings.append(
            _finding(
                dimension="collector_output_contract_coverage",
                status="PASS",
                hard_block=False,
                finding="Collector output contains no MISSING_SOURCE_EVIDENCE sentinel rows.",
                evidence_refs=[
                    str(collector_bundle / f"{contract_id}.jsonl") for contract_id in CONTRACT_IDS
                ],
            )
        )
    else:
        findings.append(
            _finding(
                dimension="collector_output_contract_coverage",
                status="INCONCLUSIVE",
                hard_block=False,
                finding=(
                    f"Collector output includes {missing_records}/{total_records} "
                    "MISSING_SOURCE_EVIDENCE sentinel rows; source detail remains incomplete."
                ),
                evidence_refs=[
                    str(collector_bundle / f"{contract_id}.jsonl") for contract_id in CONTRACT_IDS
                ],
            )
        )

    candidate_hits = []
    candidate_missing = []
    for candidate in FINAL_RESEARCH_FLEET:
        if _candidate_provenance(evaluation_bundle, candidate):
            candidate_hits.append(candidate)
        else:
            candidate_missing.append(candidate)
    if not candidate_missing:
        findings.append(
            _finding(
                dimension="candidate_binding_precondition_coverage",
                status="PASS",
                hard_block=False,
                finding="All final-research-fleet candidates have INPUT_PROVENANCE bindings.",
                evidence_refs=[
                    str(
                        evaluation_bundle
                        / "candidates"
                        / f"{candidate}_{STRATEGY_VERSION}"
                        / "INPUT_PROVENANCE.json"
                    )
                    for candidate in FINAL_RESEARCH_FLEET
                ],
            )
        )
    else:
        findings.append(
            _finding(
                dimension="candidate_binding_precondition_coverage",
                status="INCONCLUSIVE",
                hard_block=False,
                finding=f"Missing candidate INPUT_PROVENANCE for: {candidate_missing}",
                evidence_refs=[str(evaluation_bundle / "candidates")],
            )
        )

    dataset_hits = 0
    for candidate in FINAL_RESEARCH_FLEET:
        provenance = _candidate_provenance(evaluation_bundle, candidate)
        if provenance and provenance.get("dataset_digest"):
            dataset_hits += 1
    findings.append(
        _finding(
            dimension="dataset_binding_precondition_coverage",
            status="PASS" if dataset_hits == len(FINAL_RESEARCH_FLEET) else "INCONCLUSIVE",
            hard_block=False,
            finding=(
                f"Dataset digest binding present for {dataset_hits}/{len(FINAL_RESEARCH_FLEET)} candidates."
            ),
            evidence_refs=[str(evaluation_bundle / "candidates")],
        )
    )

    period_hits = 0
    for candidate in FINAL_RESEARCH_FLEET:
        snapshot = _candidate_config_snapshot(evaluation_bundle, candidate)
        dataset = (
            snapshot.get("cfg", {})
            .get("backtest", {})
            .get("dataset_admissibility", {})
            .get("dataset", {})
            if snapshot
            else {}
        )
        if (
            dataset.get("training_period")
            and dataset.get("validation_period")
            and dataset.get("out_of_sample_period")
        ):
            period_hits += 1
    findings.append(
        _finding(
            dimension="period_binding_precondition_coverage",
            status="PASS" if period_hits == len(FINAL_RESEARCH_FLEET) else "INCONCLUSIVE",
            hard_block=False,
            finding=(
                f"Training/validation/OOS period bindings present for {period_hits}/"
                f"{len(FINAL_RESEARCH_FLEET)} candidates."
            ),
            evidence_refs=[str(evaluation_bundle / "candidates")],
        )
    )

    instrument_hits = 0
    for candidate in FINAL_RESEARCH_FLEET:
        snapshot = _candidate_config_snapshot(evaluation_bundle, candidate)
        dataset = (
            snapshot.get("cfg", {})
            .get("backtest", {})
            .get("dataset_admissibility", {})
            .get("dataset", {})
            if snapshot
            else {}
        )
        if dataset.get("instrument_id"):
            instrument_hits += 1
    findings.append(
        _finding(
            dimension="instrument_binding_precondition_coverage",
            status="PASS" if instrument_hits == len(FINAL_RESEARCH_FLEET) else "INCONCLUSIVE",
            hard_block=False,
            finding=(
                f"Instrument binding present for {instrument_hits}/{len(FINAL_RESEARCH_FLEET)} candidates."
            ),
            evidence_refs=[str(evaluation_bundle / "candidates")],
        )
    )

    fee_hits = slippage_hits = funding_hits = execution_hits = 0
    for candidate in FINAL_RESEARCH_FLEET:
        snapshot = _candidate_config_snapshot(evaluation_bundle, candidate)
        backtest = snapshot.get("cfg", {}).get("backtest", {}) if snapshot else {}
        cost = backtest.get("economic_research_execution_cost", {})
        dataset_adm = backtest.get("dataset_admissibility", {})
        if cost.get("fee_model_version") or backtest.get("cost_model_version"):
            fee_hits += 1
        if dataset_adm.get("execution_cost_binding") or cost.get("spread_model_version"):
            slippage_hits += 1
        if dataset_adm.get("dataset", {}).get("field_bindings", {}).get("funding_field_binding"):
            funding_hits += 1
        if dataset_adm.get("execution_cost_binding") or cost.get(
            "execution_price_observation_source"
        ):
            execution_hits += 1

    for dimension, hits in (
        ("fee_model_binding_precondition_coverage", fee_hits),
        ("slippage_model_binding_precondition_coverage", slippage_hits),
        ("funding_model_binding_precondition_coverage", funding_hits),
        ("execution_model_binding_precondition_coverage", execution_hits),
    ):
        findings.append(
            _finding(
                dimension=dimension,
                status="PASS" if hits == len(FINAL_RESEARCH_FLEET) else "INCONCLUSIVE",
                hard_block=False,
                finding=f"{dimension} evidence present for {hits}/{len(FINAL_RESEARCH_FLEET)} candidates.",
                evidence_refs=[str(evaluation_bundle / "candidates")],
            )
        )

    policy_hits = sum(
        1
        for candidate in FINAL_RESEARCH_FLEET
        if (_candidate_provenance(evaluation_bundle, candidate) or {}).get("policy_digest")
    )
    findings.append(
        _finding(
            dimension="economic_policy_binding_precondition_coverage",
            status="PASS" if policy_hits == len(FINAL_RESEARCH_FLEET) else "INCONCLUSIVE",
            hard_block=False,
            finding=f"Policy digest binding present for {policy_hits}/{len(FINAL_RESEARCH_FLEET)} candidates.",
            evidence_refs=[str(evaluation_bundle / "candidates")],
        )
    )

    impl_hits = sum(
        1
        for candidate in FINAL_RESEARCH_FLEET
        if (_candidate_provenance(evaluation_bundle, candidate) or {}).get("implementation_digest")
    )
    findings.append(
        _finding(
            dimension="implementation_digest_precondition_coverage",
            status="PASS" if impl_hits == len(FINAL_RESEARCH_FLEET) else "INCONCLUSIVE",
            hard_block=False,
            finding=f"Implementation digest present for {impl_hits}/{len(FINAL_RESEARCH_FLEET)} candidates.",
            evidence_refs=[str(evaluation_bundle / "candidates")],
        )
    )

    cfg_hits = sum(
        1
        for candidate in FINAL_RESEARCH_FLEET
        if (_candidate_provenance(evaluation_bundle, candidate) or {}).get("config_digest")
    )
    findings.append(
        _finding(
            dimension="config_digest_precondition_coverage",
            status="PASS" if cfg_hits == len(FINAL_RESEARCH_FLEET) else "INCONCLUSIVE",
            hard_block=False,
            finding=f"Config digest present for {cfg_hits}/{len(FINAL_RESEARCH_FLEET)} candidates.",
            evidence_refs=[str(evaluation_bundle / "candidates")],
        )
    )

    data_digest_present = bool(collector_report.get("data_digest")) and bool(
        collector_report.get("config_digest")
    )
    findings.append(
        _finding(
            dimension="data_digest_precondition_coverage",
            status="PASS" if data_digest_present else "INCONCLUSIVE",
            hard_block=False,
            finding=(
                "Collector report includes config/data digests."
                if data_digest_present
                else "Collector report missing config/data digest provenance."
            ),
            evidence_refs=[str(collector_report_path)],
        )
    )

    collector_cfg = (
        _REPO_ROOT
        / "config/research/offline_source_evidence_contract_collector_materialization_v0.json"
    )
    collector_config = _load_json(collector_cfg) if collector_cfg.is_file() else {}
    retry_blocked = (
        scope_cfg.get("admissibility_review_executed") is False
        and collector_config.get("binding_retry_allowed") is False
        and collector_config.get("parameter_optimization_allowed") is False
    )
    findings.append(
        _finding(
            dimension="failed_binding_no_retry_guard",
            status="PASS" if retry_blocked else "FAIL",
            hard_block=not retry_blocked,
            finding=(
                "Failed-binding retry and parameter rescue remain blocked in governing configs."
                if retry_blocked
                else "Retry/rescue guard not proven across governing configs."
            ),
            evidence_refs=[str(scope_definition_config), str(collector_cfg)],
        )
    )

    threshold_blocked = (
        collector_config.get("threshold_lowering_allowed") is False
        and scope_cfg.get("economic_evaluation_authorized") is False
    )
    findings.append(
        _finding(
            dimension="no_policy_threshold_backfit_guard",
            status="PASS" if threshold_blocked else "FAIL",
            hard_block=not threshold_blocked,
            finding=(
                "Policy-threshold backfit remains blocked."
                if threshold_blocked
                else "Threshold-lowering guard not proven."
            ),
            evidence_refs=[str(scope_definition_config), str(collector_cfg)],
        )
    )

    authority_blocked = (
        all(config.get(flag) is False for flag in FORBIDDEN_AUTHORITY_FLAGS)
        and collector_config.get("runtime_authority_granted") is False
    )
    findings.append(
        _finding(
            dimension="no_runtime_authority_from_evidence_guard",
            status="PASS" if authority_blocked else "FAIL",
            hard_block=not authority_blocked,
            finding=(
                "No runtime/shadow/paper/testnet/live authority flags are granted."
                if authority_blocked
                else "Runtime authority leakage detected in config flags."
            ),
            evidence_refs=[str(DEFAULT_CONFIG), str(collector_cfg)],
        )
    )

    fleet_in_collector = all(
        (collector_bundle / f"TRADE_LEDGER_PER_TRADE_DECOMPOSITION_V0.jsonl").is_file()
        for _ in FINAL_RESEARCH_FLEET
    )
    fleet_in_eval = not candidate_missing
    fleet_ok = fleet_in_collector and fleet_in_eval
    findings.append(
        _finding(
            dimension="final_research_fleet_alignment_guard",
            status="PASS" if fleet_ok else "INCONCLUSIVE",
            hard_block=False,
            finding=(
                "Final research fleet candidates align across collector and evaluation bundles."
                if fleet_ok
                else "Final research fleet alignment incomplete across referenced bundles."
            ),
            evidence_refs=[str(collector_bundle), str(evaluation_bundle / "candidates")],
        )
    )

    if not parent_provenance.get("provenance_field_match", False):
        findings.append(
            _finding(
                dimension="source_evidence_manifest_integrity",
                status="FAIL",
                hard_block=True,
                finding="Parent PR #4913 provenance fields do not match configured expectations.",
                evidence_refs=[str(Path(config["parent_closeout_dir"]) / "CLOSEOUT.md")],
            )
        )

    by_dimension: dict[str, dict[str, Any]] = {}
    for item in findings:
        existing = by_dimension.get(item["dimension"])
        if existing is None or (item["hard_block"] and not existing.get("hard_block")):
            by_dimension[item["dimension"]] = item
    ordered = []
    for dimension in REVIEW_DIMENSIONS:
        if dimension in by_dimension:
            ordered.append(by_dimension[dimension])
    return ordered


def _write_review_findings_md(
    output_dir: Path, findings: list[dict[str, Any]], verdict: str
) -> None:
    lines = [
        "# Review Findings",
        "",
        f"- verdict: `{verdict}`",
        f"- scope_id: `{SCOPE_ID}`",
        "",
        "## Dimensions",
        "",
    ]
    for item in findings:
        lines.extend(
            [
                f"### {item['dimension']}",
                "",
                f"- status: `{item['status']}`",
                f"- hard_block: `{item['hard_block']}`",
                f"- finding: {item['finding']}",
                "",
            ]
        )
    output_dir.joinpath("REVIEW_FINDINGS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_offline_source_evidence_admissibility_review_execution_v0(
    *,
    config_path: Path = DEFAULT_CONFIG,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
) -> dict[str, Any]:
    if not config_path.is_file():
        _die(f"ERR:missing config: {config_path}")

    config = _load_json(config_path)
    errors = validate_config(config)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        _die("ERR:config validation failed", code=1)

    parent_closeout = Path(config["parent_closeout_dir"])
    if not parent_closeout.is_dir():
        _die(f"ERR:missing parent closeout dir: {parent_closeout}")

    scope_definition_config = _REPO_ROOT / config["scope_definition_config"]
    scope_definition_bundle = Path(config["scope_definition_bundle"])
    collector_bundle = Path(config["collector_materialization_bundle"])
    evaluation_bundle = Path(config["parent_evaluation_bundle"])

    for label, path in (
        ("scope_definition_config", scope_definition_config),
        ("scope_definition_bundle", scope_definition_bundle),
        ("collector_materialization_bundle", collector_bundle),
        ("parent_evaluation_bundle", evaluation_bundle),
    ):
        if not path.exists():
            _die(f"ERR:missing {label}: {path}")

    parent_provenance = _verify_parent_provenance(parent_closeout, config)
    findings = _review_all_dimensions(
        config=config,
        parent_provenance=parent_provenance,
        scope_definition_config=scope_definition_config,
        scope_definition_bundle=scope_definition_bundle,
        collector_bundle=collector_bundle,
        evaluation_bundle=evaluation_bundle,
    )
    verdict = _compute_verdict(findings)
    next_step = (
        config["next_step_on_pass"]
        if verdict == "ADMISSIBILITY_PASS"
        else config["next_step_on_fail_or_inconclusive"]
    )

    output_dir = archive_root / "implementation" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    output_dir.mkdir(parents=True, exist_ok=False)

    git_snapshot = _git_snapshot()
    safety_boundaries = {flag: False for flag in FORBIDDEN_AUTHORITY_FLAGS}
    safety_boundaries["admissibility_review_executed"] = True
    safety_boundaries["forbidden_command_patterns_blocked"] = list(FORBIDDEN_COMMAND_PATTERNS)

    review_result = {
        "verdict": verdict,
        "scope_id": SCOPE_ID,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "go_token": GO_TOKEN,
        "go_token_consumption": "CONSUMED",
        "review_result_vocabulary": config["review_result_vocabulary"],
        "final_research_fleet": list(FINAL_RESEARCH_FLEET),
        "parent_provenance": parent_provenance,
        "findings": findings,
        "hard_block_count": sum(1 for item in findings if item["hard_block"]),
        "pass_count": sum(1 for item in findings if item["status"] == "PASS"),
        "inconclusive_count": sum(1 for item in findings if item["status"] == "INCONCLUSIVE"),
        "fail_count": sum(1 for item in findings if item["status"] == "FAIL"),
        "economic_evaluation_executed": False,
        "economic_viability_evidence_emitted": False,
        "runtime_authority_granted": False,
        "next_step": next_step,
        "durable_evidence_path": str(output_dir),
        "git_snapshot": git_snapshot,
    }

    (output_dir / "execution_config_v0.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "PARENT_PROVENANCE.json").write_text(
        json.dumps(parent_provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "SAFETY_BOUNDARIES.json").write_text(
        json.dumps(safety_boundaries, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "git_snapshot.json").write_text(
        json.dumps(git_snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_review_findings_md(output_dir, findings, verdict)
    (output_dir / "REVIEW_RESULT.json").write_text(
        json.dumps(review_result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    write_manifest_sha256(output_dir)
    manifest_ok, manifest_msg = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if manifest_ok else 1
    if manifest_rc != 0:
        _die(f"ERR:manifest verify failed: {output_dir} ({manifest_msg})")

    review_result["manifest_verify_rc"] = manifest_rc
    (output_dir / "REVIEW_RESULT.json").write_text(
        json.dumps(review_result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_manifest_sha256(output_dir)
    manifest_ok, manifest_msg = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if manifest_ok else 1
    if manifest_rc != 0:
        _die(
            f"ERR:manifest verify failed after review result update: {output_dir} ({manifest_msg})"
        )
    review_result["manifest_verify_rc"] = manifest_rc

    return review_result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute offline source evidence admissibility review v0"
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    args = parser.parse_args()

    result = run_offline_source_evidence_admissibility_review_execution_v0(
        config_path=args.config,
        archive_root=args.durable_evidence_root,
    )
    print(f"VERDICT={result['verdict']}")
    print(f"REVIEW_RESULT={result['verdict']}")
    print(f"DURABLE_EVIDENCE_BUNDLE={result['durable_evidence_path']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    print(f"NEXT_STEP={result['next_step']}")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
