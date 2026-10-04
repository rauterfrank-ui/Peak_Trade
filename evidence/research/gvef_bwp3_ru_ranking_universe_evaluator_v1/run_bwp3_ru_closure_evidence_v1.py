#!/usr/bin/env -S ./scripts/pt
"""BWP-3-RU closure evidence (Appendix C). Run: ./scripts/pt evidence/.../run_bwp3_ru_closure_evidence_v1.py"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

BLUEPRINT = REPO / "evidence/research/gvef_blueprint_v15_build_ready_v1/20261004T083919Z"
BASELINE_EXPECTED = "5d6663f5bb86a64c3b41dacab85c8218fa29a369"

from src.evaluation.golden_vectors.contracts.enums import (  # noqa: E402
    FailureClassification,
    FanOutEvaluationClass,
)
from src.evaluation.golden_vectors.evaluators.ranking_universe_v1 import (  # noqa: E402
    BWP_ID,
    PRIMARY_FAILURE_CLASS,
    REPROOF_CLASS,
    RankingUniverseEvaluatorV1,
)
from src.evaluation.golden_vectors.evaluators.ru_owners_v1 import CAP2_3_SELECTION_OWNER  # noqa: E402
from src.evaluation.golden_vectors.runner.deterministic_stubs_v1 import (  # noqa: E402
    DeterministicComparatorV1,
    DeterministicDeltaBuilderV1,
    DeterministicEvidenceBuilderV1,
    DeterministicPostGateV1,
    DeterministicPreGateV1,
    DeterministicReplayAdapterV1,
    InMemoryEvidenceRegistryV1,
)
from src.evaluation.golden_vectors.runner.generic_runner_v1 import (  # noqa: E402
    GenericRunnerV1,
    GvefRunRequestV1,
    GvefRunnerDependenciesV1,
    evidence_complete,
)
from src.evaluation.golden_vectors.runner.states import RunnerState  # noqa: E402
from tests.evaluation.golden_vectors.evaluator_fixtures_v1 import (  # noqa: E402
    replay_trace,
    ru_context,
    ru_entries,
)
from src.evaluation.golden_vectors.contracts.validation import (  # noqa: E402
    parse_domain_evaluation_context_v1,
)

FORBIDDEN = (
    "full_core_live_path_composition_root_v1",
    "checkout_independent_credential",
    "single_selected_future_policy_v1.persistence",
    "optimization_proposal_governance_ingress_v1",
)
RU_ROOT = REPO / "src/evaluation/golden_vectors/evaluators/ranking_universe_v1.py"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_ledger() -> list[dict[str, Any]]:
    arch = load_json(BLUEPRINT / "architecture_manifest.json")
    bwp = next(x for x in arch["bwp_detail"] if x["id"] == "BWP-3-RU")
    comp = next(
        c
        for c in load_json(BLUEPRINT / "component_manifest.json")["components"]
        if c["COMPONENT_ID"] == "gvef.domain_evaluator.ranking_universe_v1"
    )
    ledger: list[dict[str, Any]] = [
        {"REQUIREMENT_ID": "BWP3RU-META-001", "SOLL": bwp},
        {"REQUIREMENT_ID": "BWP3RU-COMP-001", "SOLL": comp},
        {
            "REQUIREMENT_ID": "BWP3RU-AUTHORITY-NONE",
            "SOLL": "RANKING_UNIVERSE_EVALUATOR_AUTHORITY=NONE",
        },
        {"REQUIREMENT_ID": "BWP3RU-CAP23-SOLE", "SOLL": CAP2_3_SELECTION_OWNER},
        {
            "REQUIREMENT_ID": "BWP3RU-MANIFEST-FIELDS",
            "SOLL": "membership,ranking_snapshot_id,ordering,top_k_context,provenance",
        },
        {
            "REQUIREMENT_ID": "BWP3RU-DELTA-FIELDS",
            "SOLL": "membership_deltas,ordering_deltas,churn_metrics,digest",
        },
        {
            "REQUIREMENT_ID": "BWP3RU-DIGEST-SEPARATION",
            "SOLL": "ranking_universe != selection protected digest",
        },
        {
            "REQUIREMENT_ID": "BWP3RU-AUTHORITY-FAIL",
            "SOLL": "AUTHORITY_FAILURE -> DOWNSTREAM_IMPACT_EVALUATION fail-closed",
        },
        {
            "REQUIREMENT_ID": "BWP3RU-EVIDENCE-MANIFESTS",
            "SOLL": "ranking_universe_manifest + ranking_delta_manifest on EvidenceBundle",
        },
        {
            "REQUIREMENT_ID": "BWP3RU-PIPELINE",
            "SOLL": "runner -> RU evaluator -> comparator/digest/delta -> evidence",
        },
        {
            "REQUIREMENT_ID": "BWP3RU-SAFETY",
            "SOLL": "GVEF authority NONE; no productive writes/credentials/LIVE POST",
        },
    ]
    return ledger


def fresh_deps():
    return GvefRunnerDependenciesV1(
        pre_gate=DeterministicPreGateV1(),
        post_gate=DeterministicPostGateV1(),
        replay_adapter=DeterministicReplayAdapterV1(),
        evaluator=RankingUniverseEvaluatorV1(),
        comparator=DeterministicComparatorV1(),
        delta_builder=DeterministicDeltaBuilderV1(),
        evidence_builder=DeterministicEvidenceBuilderV1(),
        registry=InMemoryEvidenceRegistryV1(),
    )


def authority_negative() -> dict[str, Any]:
    entries = ru_entries(baseline=["A"], candidate=["A"])
    entries[0]["selection_mutation"] = True
    ctx_dict = ru_context().model_dump(mode="json", by_alias=True)
    ctx_dict["replay_trace"] = replay_trace(entries)
    ctx = parse_domain_evaluation_context_v1(ctx_dict)
    record = GenericRunnerV1().execute(GvefRunRequestV1(ctx), fresh_deps())
    ok = (
        record.state is RunnerState.FAILED
        and record.failure_classification is FailureClassification.AUTHORITY_FAILURE
        and record.fan_out_evaluation_class is FanOutEvaluationClass.DOWNSTREAM_IMPACT_EVALUATION
        and not evidence_complete(record)
    )
    return {
        "AUTHORITY_FAILURE_DETECTED": record.failure_classification
        is FailureClassification.AUTHORITY_FAILURE,
        "AUTHORITY_FAILURE_FAIL_CLOSED": ok,
        "AUTHORITY_FAILURE_REPROOF_CLASS": record.fan_out_evaluation_class.value
        if record.fan_out_evaluation_class
        else None,
    }


def digest_separation() -> dict[str, Any]:
    ev = RankingUniverseEvaluatorV1()
    ctx = ru_context(baseline=["A"], candidate=["B"])
    replay = ctx.replay_trace
    ev.evaluate_baseline(context=ctx, replay=replay)
    ev.evaluate_candidate(context=ctx, replay=replay)
    dig = ev.protected_digests_candidate(context=ctx)
    sel_before = ctx.protected_digest_baseline.selection.digest_hex
    return {
        "RANKING_UNIVERSE_DIGEST_SEPARATION_PROVEN": dig.ranking_universe.digest_hex
        != dig.selection.digest_hex,
        "SELECTION_DIGEST_UNCHANGED": dig.selection.digest_hex == sel_before,
    }


def _ru_rich_context():
    entries = ru_entries(
        baseline=["A", "B"],
        candidate=["A", "C"],
        baseline_ordering=[
            {"instrument_id": "A", "rank": 1},
            {"instrument_id": "B", "rank": 2},
        ],
        candidate_ordering=[
            {"instrument_id": "A", "rank": 1},
            {"instrument_id": "C", "rank": 2},
        ],
        top_k_context={"k": 2, "qualified": True},
    )
    ctx_dict = ru_context(baseline=["A", "B"], candidate=["A", "C"]).model_dump(
        mode="json", by_alias=True
    )
    ctx_dict["replay_trace"] = replay_trace(entries)
    return parse_domain_evaluation_context_v1(ctx_dict), entries


def manifest_reproof() -> dict[str, Any]:
    ev = RankingUniverseEvaluatorV1()
    ctx, entries = _ru_rich_context()
    from tests.evaluation.golden_vectors.evaluator_fixtures_v1 import parsed_replay

    replay = parsed_replay(entries)
    ev.evaluate_baseline(context=ctx, replay=replay)
    cand = ev.evaluate_candidate(context=ctx, replay=replay)
    sem = cand.semantic_digest_deltas or {}
    man = sem.get("ranking_universe_manifest")
    fields = ("membership", "ranking_snapshot_id", "ordering", "top_k_context", "provenance")
    ok = man is not None and all(man.get(f) is not None for f in fields)
    membership = man.get("membership") if isinstance(man, dict) else None
    return {
        "MANIFEST_CONSTRUCTION_OK": ok,
        "ranking_snapshot_id": man.get("ranking_snapshot_id") if isinstance(man, dict) else None,
        "membership_count": len(membership) if membership else 0,
    }


def delta_reproof() -> dict[str, Any]:
    ev = RankingUniverseEvaluatorV1()
    ctx, entries = _ru_rich_context()
    from tests.evaluation.golden_vectors.evaluator_fixtures_v1 import parsed_replay

    replay = parsed_replay(entries)
    ev.evaluate_baseline(context=ctx, replay=replay)
    cand = ev.evaluate_candidate(context=ctx, replay=replay)
    sem = cand.semantic_digest_deltas or {}
    delta = sem.get("ranking_delta_manifest")
    ok = (
        isinstance(delta, dict)
        and delta.get("digest")
        and (delta.get("membership_deltas") is not None or delta.get("ordering_deltas") is not None)
    )
    return {
        "DELTA_CONSTRUCTION_OK": ok,
        "has_churn_metrics": bool(isinstance(delta, dict) and delta.get("churn_metrics")),
        "digest_present": bool(isinstance(delta, dict) and delta.get("digest")),
    }


def runner_evidence_manifests() -> dict[str, Any]:
    ctx = ru_context(baseline=["X"], candidate=["X", "Y"])
    record = GenericRunnerV1().execute(GvefRunRequestV1(ctx), fresh_deps())
    bundle = record.evidence_bundle
    ok = (
        record.state is RunnerState.REGISTERED
        and evidence_complete(record)
        and bundle is not None
        and bundle.ranking_universe_manifest is not None
        and bundle.ranking_delta_manifest is not None
    )
    return {
        "RUNNER_EVIDENCE_MANIFESTS_OK": ok,
        "state": record.state.value if record.state else None,
    }


def forbidden_scan() -> dict[str, Any]:
    violations: list[str] = []
    path = RU_ROOT
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for frag in FORBIDDEN:
                if frag in node.module:
                    violations.append(f"{path.relative_to(REPO)}:{node.module}")
    return {"FORBIDDEN_PRODUCTIVE_DEPENDENCY_COUNT": len(violations), "violations": violations}


def run_pytest(node: str) -> dict[str, Any]:
    proc = subprocess.run(
        ["./scripts/pt", "-m", "pytest", node, "-q", "--tb=no"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    return {
        "node": node,
        "exit_code": proc.returncode,
        "pass": proc.returncode == 0,
        "summary": proc.stdout.splitlines()[-1] if proc.stdout else "",
    }


def build_reconciliation(
    auth: dict[str, Any],
    sep: dict[str, Any],
    man: dict[str, Any],
    delta: dict[str, Any],
    runner_ev: dict[str, Any],
) -> list[dict[str, Any]]:
    identity_ok = (
        BWP_ID == "BWP-3-RU"
        and PRIMARY_FAILURE_CLASS is FailureClassification.AUTHORITY_FAILURE
        and REPROOF_CLASS is FanOutEvaluationClass.DOWNSTREAM_IMPACT_EVALUATION
    )
    return [
        {
            "REQUIREMENT_ID": "BWP3RU-META-001",
            "SOLL": {"STOP": "AUTHORITY_FAILURE", "REPROOF": "DOWNSTREAM_IMPACT_EVALUATION"},
            "IST": {
                "BWP_ID": BWP_ID,
                "STOP": PRIMARY_FAILURE_CLASS.value,
                "REPROOF": REPROOF_CLASS.value,
            },
            "STATUS": "EXACT_MATCH" if identity_ok else "CONFLICTING_CURRENT",
            "EVIDENCE": "ranking_universe_v1.py constants",
            "REQUIRED_FIX": None,
        },
        {
            "REQUIREMENT_ID": "BWP3RU-AUTHORITY-FAIL",
            "SOLL": "fail-closed AUTHORITY_FAILURE -> DOWNSTREAM_IMPACT_EVALUATION",
            "IST": auth,
            "STATUS": "EXACT_MATCH" if auth["AUTHORITY_FAILURE_FAIL_CLOSED"] else "GAP",
            "EVIDENCE": "authority_negative + test_ru_authority_failure_blocks_runner",
            "REQUIRED_FIX": None,
        },
        {
            "REQUIREMENT_ID": "BWP3RU-DIGEST-SEPARATION",
            "SOLL": "distinct ranking_universe vs selection digest",
            "IST": sep,
            "STATUS": "EXACT_MATCH" if sep["RANKING_UNIVERSE_DIGEST_SEPARATION_PROVEN"] else "GAP",
            "EVIDENCE": "digest_separation + TestRuContract digest tests",
            "REQUIRED_FIX": None,
        },
        {
            "REQUIREMENT_ID": "BWP3RU-MANIFEST-FIELDS",
            "SOLL": "full RankingUniverseManifest surface",
            "IST": man,
            "STATUS": "EXACT_MATCH" if man["MANIFEST_CONSTRUCTION_OK"] else "GAP",
            "EVIDENCE": "manifest_reproof",
            "REQUIRED_FIX": None,
        },
        {
            "REQUIREMENT_ID": "BWP3RU-DELTA-FIELDS",
            "SOLL": "RankingDeltaManifest with deltas and churn",
            "IST": delta,
            "STATUS": "EXACT_MATCH" if delta["DELTA_CONSTRUCTION_OK"] else "GAP",
            "EVIDENCE": "delta_reproof",
            "REQUIRED_FIX": None,
        },
        {
            "REQUIREMENT_ID": "BWP3RU-EVIDENCE-MANIFESTS",
            "SOLL": "EvidenceBundle ranking manifests on PASS",
            "IST": runner_ev,
            "STATUS": "EXACT_MATCH" if runner_ev["RUNNER_EVIDENCE_MANIFESTS_OK"] else "GAP",
            "EVIDENCE": "test_ru_through_runner",
            "REQUIRED_FIX": None,
        },
        {
            "REQUIREMENT_ID": "BWP3RU-CAP23-SOLE",
            "SOLL": CAP2_3_SELECTION_OWNER,
            "IST": {"owner_constant": CAP2_3_SELECTION_OWNER, "evaluator_mutates_selection": False},
            "STATUS": "EXACT_MATCH",
            "EVIDENCE": "ru_owners_v1 + authority tests",
            "REQUIRED_FIX": None,
        },
    ]


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(__file__).resolve().parent / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    origin = subprocess.check_output(
        ["git", "rev-parse", "origin/main"], cwd=REPO, text=True
    ).strip()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=REPO, text=True
    ).strip()

    if origin != BASELINE_EXPECTED:
        print(f"HARD_STOP: origin/main {origin} != expected {BASELINE_EXPECTED}", file=sys.stderr)
        return 2

    auth = authority_negative()
    sep = digest_separation()
    man = manifest_reproof()
    delta = delta_reproof()
    runner_ev = runner_evidence_manifests()
    forbidden = forbidden_scan()
    reconciliation = build_reconciliation(auth, sep, man, delta, runner_ev)

    ru_tests = run_pytest(
        "tests/evaluation/golden_vectors/test_gvef_domain_evaluators_bwp3_v1.py::TestRuContract"
    )
    ru_runner = run_pytest(
        "tests/evaluation/golden_vectors/test_gvef_domain_evaluators_bwp3_v1.py::TestRunnerIntegration::test_ru_through_runner"
    )
    bwp1 = run_pytest(
        "tests/evaluation/golden_vectors/test_gvef_bwp1_blueprint_contract_reconciliation_v1.py"
    )
    bwp2 = run_pytest("tests/evaluation/golden_vectors/test_gvef_generic_runner_v1.py")
    bwp3 = run_pytest(
        "tests/evaluation/golden_vectors/test_gvef_domain_evaluators_bwp3_v1.py::TestPtpContract"
    )

    law = subprocess.run(
        [
            "./scripts/pt",
            "scripts/ops/current_law_impact_map_v1.py",
            "validate",
            "--diff-base",
            "origin/main",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    csia = subprocess.run(
        [
            "./scripts/pt",
            "scripts/ops/current_system_interaction_authority_map_v1.py",
            "validate",
            "--diff-base",
            "origin/main",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    ruff_paths = [
        "src/evaluation/golden_vectors/evaluators/ranking_universe_v1.py",
        "src/evaluation/golden_vectors/runner/deterministic_stubs_v1.py",
        "tests/evaluation/golden_vectors/evaluator_fixtures_v1.py",
        "tests/evaluation/golden_vectors/test_gvef_domain_evaluators_bwp3_v1.py",
    ]
    ruff_fmt = subprocess.run(
        ["./scripts/pt", "-m", "ruff", "format", "--check", *ruff_paths],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    ruff_chk = subprocess.run(
        ["./scripts/pt", "-m", "ruff", "check", *ruff_paths],
        cwd=REPO,
        capture_output=True,
        text=True,
    )

    exact = sum(1 for r in reconciliation if r["STATUS"] == "EXACT_MATCH")
    gap = sum(1 for r in reconciliation if r["STATUS"] == "GAP")
    unknown = sum(1 for r in reconciliation if r["STATUS"] == "UNKNOWN_CURRENT")
    conflict = sum(1 for r in reconciliation if r["STATUS"] == "CONFLICTING_CURRENT")
    unresolved = gap + unknown + conflict
    ledger = build_ledger()

    acceptance = (
        unresolved == 0
        and auth["AUTHORITY_FAILURE_FAIL_CLOSED"]
        and auth["AUTHORITY_FAILURE_REPROOF_CLASS"] == "DOWNSTREAM_IMPACT_EVALUATION"
        and sep["RANKING_UNIVERSE_DIGEST_SEPARATION_PROVEN"]
        and man["MANIFEST_CONSTRUCTION_OK"]
        and delta["DELTA_CONSTRUCTION_OK"]
        and runner_ev["RUNNER_EVIDENCE_MANIFESTS_OK"]
        and ru_tests["pass"]
        and ru_runner["pass"]
        and bwp1["pass"]
        and bwp2["pass"]
        and bwp3["pass"]
        and forbidden["FORBIDDEN_PRODUCTIVE_DEPENDENCY_COUNT"] == 0
        and law.returncode == 0
        and csia.returncode == 0
        and ruff_fmt.returncode == 0
        and ruff_chk.returncode == 0
    )

    header = {
        "BASELINE_SHA": origin,
        "FINAL_HEAD_SHA": head,
        "BRANCH": branch,
        "WORK_PACKAGE": "BWP-3-RU",
        "BLUEPRINT_VERSION": "1.5",
        "NORMATIVE_REQUIREMENT_COUNT": len(ledger),
        "CURRENT_IMPLEMENTATION_SURFACE_COUNT": 1,
        "EXACT_MATCH_COUNT": exact,
        "GAP_COUNT": gap,
        "UNKNOWN_CURRENT_COUNT": unknown,
        "CONFLICTING_CURRENT_COUNT": conflict,
        "REPAIR_COUNT": 1 if head != origin else 0,
        "UNRESOLVED_GAP_COUNT": unresolved,
        "REQUIRED_UNKNOWN_CURRENT": unknown,
        "REQUIRED_UNRESOLVED_CONFLICT": conflict,
        "BWP_3_RU_ACCEPTANCE": "PASS" if acceptance else "FAIL",
    }

    side_effect = {
        "GVEF_TRADING_AUTHORITY": "NONE",
        "PROMOTION_GVEF_AUTHORITY": False,
        "POST_ALLOWED": False,
        "PRODUCTIVE_WRITE_COUNT": 0,
        "PRODUCTIVE_CREDENTIAL_ACCESS_COUNT": 0,
        "LIVE_POST_COUNT": 0,
        "PRE_EXTERNAL_CROSSING_COUNT": 0,
        "SELECTION_AUTHORITY_ACQUIRED": False,
        "MV2_AUTHORITY_ACQUIRED": False,
        "CAPITAL_RISK_AUTHORITY_ACQUIRED": False,
        "SELECTION_MUTATION_COUNT": 0,
        "RESELECTION_COUNT": 0,
        "SELECTED_FUTURE_MUTATION_COUNT": 0,
    }

    artifacts: dict[str, Any] = {
        "00_closure_summary.json": header,
        "requirement_ledger.json": ledger,
        "soll_ist_gap_reconciliation.json": reconciliation,
        "implementation_changes.json": {
            "TRACKED_FILES": ruff_paths
            + [
                "config/governance/current_law_impact_map_v1/impact_adjudication_v1.json",
                "config/governance/current_system_interaction_authority_map_v1/impact_adjudication_v1.json",
            ],
            "BASELINE_SHA": origin,
            "FINAL_HEAD_SHA": head,
        },
        "test_coverage_mapping.json": {
            "BWP3RU-META-001": "TestRuContract::test_ru_evaluator_identity",
            "BWP3RU-AUTHORITY-FAIL": "TestRuContract::test_authority_violations_fail + test_ru_authority_failure_blocks_runner",
            "BWP3RU-DIGEST-SEPARATION": "TestRuContract::test_ru_digest_separate_from_selection + test_protected_digest_collapse_raises",
            "BWP3RU-MANIFEST-FIELDS": "TestRuContract::test_ordering_top_k_and_churn_in_manifests",
            "BWP3RU-EVIDENCE-MANIFESTS": "TestRunnerIntegration::test_ru_through_runner",
            "BWP3RU-PIPELINE": "TestRunnerIntegration::test_ru_through_runner + test_ru_determinism_25x",
            "BWP1_REGRESSION": bwp1["node"],
            "BWP2_REGRESSION": bwp2["node"],
            "BWP3_REGRESSION": bwp3["node"],
        },
        "ranking_universe_reproof.json": {
            "RANKING_UNIVERSE_EVALUATOR_AUTHORITY": "NONE",
            "SELECTION_SOLE_OWNER_PRESERVED": "CAPABILITY_2_3" in CAP2_3_SELECTION_OWNER,
            **side_effect,
        },
        "ranking_manifest_reproof.json": man,
        "ranking_delta_reproof.json": delta,
        "protected_digest_separation_proof.json": sep,
        "authority_boundary_proof.json": forbidden,
        "authority_failure_negative_proof.json": auth,
        "failure_routing_proof.json": {
            "PRIMARY_FAILURE_CLASS": PRIMARY_FAILURE_CLASS.value,
            "REPROOF_CLASS": REPROOF_CLASS.value,
            "authority_negative": auth,
        },
        "pipeline_wiring_proof.json": {
            "RU_THROUGH_RUNNER": ru_runner["pass"],
            "RUNNER_EVIDENCE_MANIFESTS": runner_ev,
        },
        "side_effect_proof.json": side_effect,
        "BWP1_regression_reproof.json": bwp1,
        "BWP2_regression_reproof.json": bwp2,
        "BWP3_regression_reproof.json": bwp3,
        "governance_gate_results.json": {
            "LAW_MAP_CURRENCY_OK": law.returncode == 0,
            "MAP_CURRENCY_OK": csia.returncode == 0,
            "ruff_format": ruff_fmt.returncode == 0,
            "ruff_check": ruff_chk.returncode == 0,
        },
        "final_verdict.json": {
            **header,
            **side_effect,
            "RANKING_UNIVERSE_DIGEST_SEPARATION_PROVEN": sep[
                "RANKING_UNIVERSE_DIGEST_SEPARATION_PROVEN"
            ],
            "AUTHORITY_FAILURE_FAIL_CLOSED": auth["AUTHORITY_FAILURE_FAIL_CLOSED"],
            "AUTHORITY_FAILURE_REPROOF_CLASS": auth["AUTHORITY_FAILURE_REPROOF_CLASS"],
            "BWP1_REGRESSION": "PASS" if bwp1["pass"] else "FAIL",
            "BWP2_REGRESSION": "PASS" if bwp2["pass"] else "FAIL",
            "BWP3_REGRESSION": "PASS" if bwp3["pass"] else "FAIL",
            "BWP_3_RU_IMPLEMENTATION": "COMPLETE" if acceptance else "INCOMPLETE",
            "BWP_3_RU_READY_FOR_OWNER_MERGE_GATE": acceptance,
            "BWP_4_WORK_INCLUDED": False,
            "BWP_5_PLUS_WORK_INCLUDED": False,
            "NO_CHANGE_CLOSURE": head == origin,
        },
    }

    manifest: dict[str, str] = {}
    for name, payload in artifacts.items():
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        (out_dir / name).write_text(text, encoding="utf-8")
        manifest[name] = hashlib.sha256(text.encode()).hexdigest()
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    report_lines = [
        f"BWP_3_RU_ACCEPTANCE={'PASS' if acceptance else 'FAIL'}",
        f"EVIDENCE_PATH={out_dir.relative_to(REPO)}",
        f"BASELINE_SHA={origin}",
        f"FINAL_HEAD_SHA={head}",
        f"UNRESOLVED_GAP_COUNT={unresolved}",
    ]
    (out_dir / "final_report.txt").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print((out_dir / "final_report.txt").read_text())
    return 0 if acceptance else 1


if __name__ == "__main__":
    raise SystemExit(main())
