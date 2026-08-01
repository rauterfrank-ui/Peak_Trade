"""Tests for non-enforcing max-age parameter research execution v1."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.architecture_guards_v1 import (
    assert_architecture_guards_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    EXPECTED_PREREGISTRATION_DIGEST,
    OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS,
    SPEC_REL_PATH,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.contracts_v1 import (
    MaxAgeResearchExecutionError,
    assert_candidate_domain_immutable_v1,
    assert_candidates_not_config_authority_v1,
    bind_candidate_domain_v1,
    bind_hypothesis_contract_v1,
    bind_robustness_execution_contract_v1,
    bind_split_and_embargo_contract_v1,
    verify_preregistration_digest_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.evidence_loader_v1 import (
    assert_restore_does_not_invent_estimate_evidence_v1,
    load_research_evidence_from_payloads_v1,
    load_research_evidence_records_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.runner_v1 import (
    run_max_age_parameter_research_execution_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.serialization_v1 import (
    build_execution_id_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.split_engine_v1 import (
    access_final_holdout_v1,
    build_purged_chronological_splits_v1,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    JOIN_CONTRACT_VERSION,
    append_max_age_research_evidence_ledger_record_v1,
    build_max_age_research_evidence_join_v1,
    build_ratified_max_age_research_design_contract_v1,
)

ROOT = Path(__file__).resolve().parents[2]
T0 = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)


def _join(
    *,
    session_id: str,
    cycle_id: str,
    regime_id: str,
    age_seconds: float,
    event_offset_seconds: int,
    instrument_id: str = "ETH-USD_UM_XPERP-310404",
):
    ref = T0 + timedelta(seconds=event_offset_seconds)
    as_of = ref - timedelta(seconds=age_seconds)
    return build_max_age_research_evidence_join_v1(
        session_id=session_id,
        cycle_id=cycle_id,
        instrument_id=instrument_id,
        regime_id=regime_id,
        max_age_policy_evidence={
            "estimate_as_of_event_time": as_of.isoformat().replace("+00:00", "Z"),
            "reference_event_time": ref.isoformat().replace("+00:00", "Z"),
            "computed_age_seconds": float(age_seconds),
            "max_age_status": "AGE_COMPUTED_THRESHOLD_UNRESOLVED",
            "threshold_status": "UNRESOLVED_MAX_AGE",
            "presence_status": "PRESENT",
            "clock_trust_status": "TRUSTED",
            "data_integrity_status": "TRUSTED",
            "reuse_status": "FRESHLY_PRODUCED",
            "restart_status": "NOT_APPLICABLE",
            "source_digest": "abc123",
            "decision": "AGE_COMPUTED",
            "reason_code": "VOLATILITY_ESTIMATE_AGE_UNRESOLVED",
            "enforcement_applied": False,
            "numeric_threshold_selected": False,
            "session_id": session_id,
            "cycle_id": cycle_id,
            "instrument_id": instrument_id,
            "regime_id": regime_id,
        },
        producer_outcome="PRODUCED",
        reuse_status="FRESHLY_PRODUCED",
        restart_status="NOT_APPLICABLE",
        restart_without_estimate=False,
        estimate_present=True,
        observation_count=60,
        source_digest="abc123",
        trading_epoch=1,
        cycle_index=0,
        alpha_scope_entry_authority_allowed=True,
        decision_outcome="HOLD",
        selected_side="none",
        economic_metrics={"net_pnl_after_fees_and_slippage": 0.0, "trade_count": 0},
    )


def _fixture_records():
    ages = [30, 90, 250, 500, 800, 1200, 2000, 4000, 100, 400, 700, 1500]
    sessions = [
        "sess-a",
        "sess-a",
        "sess-a",
        "sess-a",
        "sess-a",
        "sess-a",
        "sess-b",
        "sess-b",
        "sess-b",
        "sess-b",
        "sess-b",
        "sess-b",
    ]
    regimes = [
        "trending",
        "trending",
        "trending",
        "choppy",
        "choppy",
        "choppy",
        "trending",
        "trending",
        "choppy",
        "choppy",
        "trending",
        "choppy",
    ]
    joins = []
    for i, age in enumerate(ages):
        joins.append(
            _join(
                session_id=sessions[i],
                cycle_id=f"{sessions[i]}-c{i}",
                regime_id=regimes[i],
                age_seconds=float(age),
                event_offset_seconds=i * 7200,
            )
        )
    from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.evidence_loader_v1 import (
        load_research_evidence_from_payloads_v1,
    )

    return load_research_evidence_from_payloads_v1([j.to_dict() for j in joins])


def test_01_preregistration_digest_mismatch_fail_closed() -> None:
    with pytest.raises(MaxAgeResearchExecutionError, match="preregistration_digest_mismatch"):
        verify_preregistration_digest_v1("0" * 64)
    design = build_ratified_max_age_research_design_contract_v1()
    assert design.preregistration_digest == EXPECTED_PREREGISTRATION_DIGEST
    verify_preregistration_digest_v1(design.preregistration_digest)


def test_02_candidate_domain_immutable_after_start() -> None:
    domain = bind_candidate_domain_v1(
        repository_sha="e03426f0250fbc55f95c044c6a904e059746125c",
        preregistration_digest=EXPECTED_PREREGISTRATION_DIGEST,
        execution_id="exec-test",
        created_at_utc="2026-08-01T00:00:00Z",
    )
    assert_candidate_domain_immutable_v1(
        domain, attempted_candidates=domain.candidate_max_age_seconds
    )
    with pytest.raises(MaxAgeResearchExecutionError, match="immutable"):
        assert_candidate_domain_immutable_v1(domain, attempted_candidates=(1, 2, 3))


def test_03_candidate_values_not_config_policy_authority() -> None:
    domain = bind_candidate_domain_v1(
        repository_sha="e03426f0250fbc55f95c044c6a904e059746125c",
        preregistration_digest=EXPECTED_PREREGISTRATION_DIGEST,
        execution_id="exec-test",
        created_at_utc="2026-08-01T00:00:00Z",
    )
    payload = domain.to_dict()
    assert_candidates_not_config_authority_v1(payload)
    assert "NOT_CONFIG" in payload["candidate_authority"]
    assert domain.candidate_max_age_seconds == OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS


def test_04_missing_join_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(MaxAgeResearchExecutionError, match="missing_join_ledger"):
        load_research_evidence_records_v1(tmp_path / "absent.jsonl")


def test_05_join_digest_mismatch_fail_closed(tmp_path: Path) -> None:
    join = _join(
        session_id="s1",
        cycle_id="s1-c0",
        regime_id="trending",
        age_seconds=10.0,
        event_offset_seconds=0,
    )
    path = tmp_path / "ledger.jsonl"
    append_max_age_research_evidence_ledger_record_v1(ledger_path=path, record=join)
    text = path.read_text(encoding="utf-8")
    row = json.loads(text)
    row["join_digest"] = "0" * 64
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(MaxAgeResearchExecutionError, match="join_digest_mismatch"):
        load_research_evidence_records_v1(path)


def test_06_unknown_schema_fail_closed() -> None:
    with pytest.raises(MaxAgeResearchExecutionError, match="unknown_schema_version"):
        load_research_evidence_from_payloads_v1(
            [
                {
                    "session_id": "s",
                    "cycle_id": "c",
                    "instrument_id": "i",
                    "regime_id": "r",
                    "join_contract_version": "unknown/v9",
                    "join_digest": "x",
                    "threshold_status": "UNRESOLVED_MAX_AGE",
                    "enforcement_applied": False,
                    "numeric_threshold_selected": False,
                }
            ]
        )


def test_07_resolved_threshold_in_input_fail_closed() -> None:
    with pytest.raises(MaxAgeResearchExecutionError, match="resolved_threshold"):
        load_research_evidence_from_payloads_v1(
            [
                {
                    "session_id": "s",
                    "cycle_id": "c",
                    "instrument_id": "i",
                    "regime_id": "r",
                    "join_contract_version": JOIN_CONTRACT_VERSION,
                    "join_digest": "x",
                    "threshold_status": "RESOLVED_MAX_AGE",
                    "enforcement_applied": False,
                    "numeric_threshold_selected": False,
                }
            ]
        )


def test_08_enforcement_in_input_fail_closed() -> None:
    with pytest.raises(MaxAgeResearchExecutionError, match="enforcement_applied"):
        load_research_evidence_from_payloads_v1(
            [
                {
                    "session_id": "s",
                    "cycle_id": "c",
                    "instrument_id": "i",
                    "regime_id": "r",
                    "join_contract_version": JOIN_CONTRACT_VERSION,
                    "join_digest": "x",
                    "threshold_status": "UNRESOLVED_MAX_AGE",
                    "enforcement_applied": True,
                    "numeric_threshold_selected": False,
                }
            ]
        )


def test_09_duplicate_identity_divergent_digest_fail_closed(tmp_path: Path) -> None:
    j1 = _join(
        session_id="s1",
        cycle_id="s1-c0",
        regime_id="trending",
        age_seconds=10.0,
        event_offset_seconds=0,
    )
    j2 = _join(
        session_id="s1",
        cycle_id="s1-c0",
        regime_id="trending",
        age_seconds=99.0,
        event_offset_seconds=0,
    )
    path = tmp_path / "ledger.jsonl"
    append_max_age_research_evidence_ledger_record_v1(ledger_path=path, record=j1)
    with pytest.raises(Exception):
        append_max_age_research_evidence_ledger_record_v1(ledger_path=path, record=j2)


def test_10_restore_does_not_invent_estimate_evidence() -> None:
    records = _fixture_records()
    assert_restore_does_not_invent_estimate_evidence_v1(before=records, after=records)
    invented = list(records) + list(records[:1])
    # Same digests already present — inventing a new identity should fail.
    from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.evidence_loader_v1 import (
        ResearchEvidenceRecordV1,
    )

    extra = ResearchEvidenceRecordV1(
        session_id="invented",
        cycle_id="invented-c0",
        instrument_id="X",
        regime_id="r",
        join_contract_version=JOIN_CONTRACT_VERSION,
        join_digest="inventeddigest",
        volatility_source_digest=None,
        market_event_time=None,
        volatility_as_of_event_time=None,
        computed_age_seconds=1.0,
        reuse_status=None,
        restart_status=None,
        estimate_present=True,
        decision_outcome=None,
        selected_side=None,
        economic_metrics=None,
        event_time_epoch_seconds=1.0,
        raw={},
    )
    with pytest.raises(MaxAgeResearchExecutionError, match="restore_invented"):
        assert_restore_does_not_invent_estimate_evidence_v1(
            before=records, after=tuple(list(records) + [extra])
        )
    _ = invented


def test_11_12_split_chronological_purged_and_embargo() -> None:
    records = _fixture_records()
    split_contract = bind_split_and_embargo_contract_v1(
        repository_sha="e03426f0250fbc55f95c044c6a904e059746125c",
        preregistration_digest=EXPECTED_PREREGISTRATION_DIGEST,
        execution_id="exec-test",
        created_at_utc="2026-08-01T00:00:00Z",
    )
    sealed = build_purged_chronological_splits_v1(
        records, split_contract=split_contract, access_holdout=False
    )
    assert sealed.embargo_seconds == split_contract.embargo_seconds
    assert sealed.holdout_accessed is False
    for rows in (sealed.train, sealed.validation):
        times = [float(r.event_time_epoch_seconds or 0.0) for r in rows]
        assert times == sorted(times)


def test_13_holdout_untouched_until_final() -> None:
    records = _fixture_records()
    split_contract = bind_split_and_embargo_contract_v1(
        repository_sha="e03426f0250fbc55f95c044c6a904e059746125c",
        preregistration_digest=EXPECTED_PREREGISTRATION_DIGEST,
        execution_id="exec-test",
        created_at_utc="2026-08-01T00:00:00Z",
    )
    sealed = build_purged_chronological_splits_v1(
        records, split_contract=split_contract, access_holdout=False
    )
    assert sealed.holdout_accessed is False
    opened = access_final_holdout_v1(sealed)
    assert opened.holdout_accessed is True


def test_14_15_16_17_18_19_20_full_runner_no_alpha_enforcement_deterministic(
    tmp_path: Path,
) -> None:
    records = _fixture_records()
    out1 = tmp_path / "run1"
    result1 = run_max_age_parameter_research_execution_v1(
        repo_root=ROOT,
        output_root=out1,
        repository_sha="e03426f0250fbc55f95c044c6a904e059746125c",
        records=records,
        created_at_utc="2026-08-01T00:00:00Z",
    )
    assert result1["preregistration_digest_match"] is True
    assert result1["numeric_threshold_selected"] is False
    assert result1["parameter_promoted"] is False
    assert result1["enforcement_applied"] is False
    assert result1["threshold_status"] == "UNRESOLVED_MAX_AGE"
    assert result1["hard_stop"] is True
    assert result1["deterministic_reexecution_pass"] is True
    assert result1["ledger_resume_equivalence_pass"] is True
    assert result1["conclusion"]["recommended_single_threshold"] is None
    assert result1["conclusion"]["numeric_threshold_selected"] is False

    for row in result1["candidate_results"]:
        assert row["alpha_decision_mutated"] is False
        assert row["enforcement_applied"] is False
        assert row["evaluation_mode"] == "DIAGNOSTIC_COUNTERFACTUAL_NO_ENFORCEMENT"

    out2 = tmp_path / "run2"
    result2 = run_max_age_parameter_research_execution_v1(
        repo_root=ROOT,
        output_root=out2,
        repository_sha="e03426f0250fbc55f95c044c6a904e059746125c",
        records=records,
        created_at_utc="2026-08-01T00:00:00Z",
    )
    assert result1["execution_id"] == result2["execution_id"]
    assert result1["candidate_domain_digest"] == result2["candidate_domain_digest"]
    assert result1["candidate_results"] == result2["candidate_results"]

    required = [
        "research_execution_manifest.json",
        "candidate_domain.json",
        "hypothesis_contract.json",
        "split_and_embargo_contract.json",
        "robustness_execution_contract.json",
        "input_evidence_manifest.json",
        "candidate_results.jsonl",
        "walk_forward_results.json",
        "holdout_results.json",
        "regime_results.json",
        "session_results.json",
        "robustness_results.json",
        "research_conclusion.json",
        "integrity_manifest.json",
    ]
    for name in required:
        assert (out1 / name).exists(), name


def test_16_deterministic_execution_id() -> None:
    a = build_execution_id_v1(
        repository_sha="e03426f0250fbc55f95c044c6a904e059746125c",
        preregistration_digest=EXPECTED_PREREGISTRATION_DIGEST,
        candidate_domain_digest="a" * 64,
        hypothesis_contract_digest="b" * 64,
        split_contract_digest="c" * 64,
        robustness_contract_digest="d" * 64,
        input_evidence_manifest_digest="e" * 64,
    )
    b = build_execution_id_v1(
        repository_sha="e03426f0250fbc55f95c044c6a904e059746125c",
        preregistration_digest=EXPECTED_PREREGISTRATION_DIGEST,
        candidate_domain_digest="a" * 64,
        hypothesis_contract_digest="b" * 64,
        split_contract_digest="c" * 64,
        robustness_contract_digest="d" * 64,
        input_evidence_manifest_digest="e" * 64,
    )
    assert a == b
    assert a.startswith("maxage_research_exec_")


def test_21_architecture_guard_against_trading_authority_import() -> None:
    guards = assert_architecture_guards_v1(repo_root=ROOT)
    assert guards["guards_pass"] is True
    assert guards["trading_authority_imports_absent"] is True
    assert guards["numeric_threshold_selected"] is False


def test_22_docs_and_reference_gates() -> None:
    spec = ROOT / SPEC_REL_PATH
    assert spec.exists()
    text = spec.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PARAMETER_RESEARCH_EXECUTION_V1"
        in text
    )
    assert "NUMERIC_THRESHOLD_SELECTED: false" in text
    assert "ENFORCEMENT_APPLIED: false" in text
    assert "HARD_STOP: true" in text
    # Docs token policy: inline code paths must use &#47;
    assert "src&#47;research&#47;" in text or "scripts&#47;ops&#47;" in text


def test_hypothesis_and_split_bindings_before_eval() -> None:
    hyp = bind_hypothesis_contract_v1(
        repository_sha="e03426f0250fbc55f95c044c6a904e059746125c",
        preregistration_digest=EXPECTED_PREREGISTRATION_DIGEST,
        execution_id="exec-test",
        created_at_utc="2026-08-01T00:00:00Z",
    )
    assert hyp.enforcement_during_research is False
    assert hyp.counterfactual_only is True
    assert hyp.alpha_decision_mutation_allowed is False
    split = bind_split_and_embargo_contract_v1(
        repository_sha="e03426f0250fbc55f95c044c6a904e059746125c",
        preregistration_digest=EXPECTED_PREREGISTRATION_DIGEST,
        execution_id="exec-test",
        created_at_utc="2026-08-01T00:00:00Z",
    )
    assert split.embargo_seconds > 0
    assert split.holdout_untouched_until_final_evaluation is True
    rob = bind_robustness_execution_contract_v1(
        repository_sha="e03426f0250fbc55f95c044c6a904e059746125c",
        preregistration_digest=EXPECTED_PREREGISTRATION_DIGEST,
        execution_id="exec-test",
        created_at_utc="2026-08-01T00:00:00Z",
    )
    assert "BLOCK_BOOTSTRAP_CONFIDENCE_INTERVALS" in rob.methods


def test_insufficient_productive_ledger_blocks_without_extrapolation(tmp_path: Path) -> None:
    result = run_max_age_parameter_research_execution_v1(
        repo_root=ROOT,
        ledger_path=tmp_path / "missing.jsonl",
        output_root=tmp_path / "blocked",
        repository_sha="e03426f0250fbc55f95c044c6a904e059746125c",
        created_at_utc="2026-08-01T00:00:00Z",
    )
    assert result["status"] == "BLOCKED"
    assert result["insufficient_research_evidence"] is True
    assert result["numeric_threshold_selected"] is False
    assert result["parameter_promoted"] is False
    assert (tmp_path / "blocked" / "research_conclusion.json").exists()
