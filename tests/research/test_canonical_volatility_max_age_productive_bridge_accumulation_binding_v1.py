"""Tests for productive bridge cycle input authorization and accumulation binding."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.architecture_guards_v1 import (
    assert_architecture_guards_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    AUTHORITATIVE_BRIDGE_CYCLE_OUTPUT_ID,
    DEFAULT_JOIN_LEDGER_RELATIVE_PATH,
    DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH,
    DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH,
    ENFORCEMENT_APPLIED,
    NUMERIC_THRESHOLD_SELECTED,
    PRODUCTIVE_BRIDGE_BINDING_CAPABILITY_ID,
    THRESHOLD_STATUS,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.ledger_v1 import (
    load_productive_evidence_ledger_v1,
    valid_productive_records_from_ledger_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveEvidenceAccumulationError,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.productive_bridge_binding_v1 import (
    authorize_productive_bridge_cycle_input_v1,
    bind_accumulation_state_to_hardened_bridge_session_v1,
    build_productive_bridge_cycle_authority_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.productive_bridge_runner_v1 import (
    assert_ledger_integrity_matrix_v1,
    deterministic_productive_mark_path_v1,
    run_productive_bridge_accumulation_session_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.evidence_loader_v1 import (
    load_research_evidence_records_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    build_ratified_max_age_research_design_contract_v1,
)

ROOT = Path(__file__).resolve().parents[2]
REPO_SHA = "51a3625b3666bc905b89ba9a8ad1bcfe84494430"
PREREG = build_ratified_max_age_research_design_contract_v1().preregistration_digest


def _paths(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    return (
        tmp_path / "prod.jsonl",
        tmp_path / "join.jsonl",
        tmp_path / "q.jsonl",
        tmp_path / "persist.json",
    )


def test_01_authoritative_bridge_cycle_produces_one_record_and_join(tmp_path: Path) -> None:
    prod, join, q, persist = _paths(tmp_path)
    report = run_productive_bridge_accumulation_session_v1(
        session_id="bind-s1",
        campaign_id="campaign_bind_v1",
        repository_sha=REPO_SHA,
        samples=deterministic_productive_mark_path_v1(count=62),
        repo_root=ROOT,
        productive_ledger_path=prod,
        join_ledger_path=join,
        quarantine_ledger_path=q,
        typed_volatility_persistence_path=persist,
    )
    assert report["status"] == "PASS"
    assert report["records_appended"] >= 1
    records = valid_productive_records_from_ledger_v1(prod)
    assert len(records) == report["records_appended"]
    joins = load_research_evidence_records_v1(join)
    assert len(joins) == len(records)
    rec = records[0]
    assert rec.source_is_authoritative_bridge_cycle is True
    assert rec.synthetic is False
    assert rec.fixture is False
    assert rec.test_data is False
    assert rec.campaign_id == "campaign_bind_v1"
    assert rec.market_sample_id
    assert rec.repository_sha == REPO_SHA
    assert rec.preregistration_digest == PREREG
    assert rec.productive_input_authority == AUTHORITATIVE_BRIDGE_CYCLE_OUTPUT_ID


def test_02_bijection_and_duplicate_cycle_idempotent(tmp_path: Path) -> None:
    prod, join, q, persist = _paths(tmp_path)
    samples = deterministic_productive_mark_path_v1(count=62)
    run_productive_bridge_accumulation_session_v1(
        session_id="bind-s1",
        campaign_id="campaign_bind_v1",
        repository_sha=REPO_SHA,
        samples=samples,
        repo_root=ROOT,
        productive_ledger_path=prod,
        join_ledger_path=join,
        quarantine_ledger_path=q,
        typed_volatility_persistence_path=persist,
    )
    before = len(valid_productive_records_from_ledger_v1(prod))
    # Replay exact same session samples against existing ledger → duplicate identities noop.
    run_productive_bridge_accumulation_session_v1(
        session_id="bind-s1",
        campaign_id="campaign_bind_v1",
        repository_sha=REPO_SHA,
        samples=samples,
        repo_root=ROOT,
        productive_ledger_path=prod,
        join_ledger_path=join,
        quarantine_ledger_path=q,
        typed_volatility_persistence_path=tmp_path / "persist2.json",
    )
    after = len(valid_productive_records_from_ledger_v1(prod))
    # Duplicate market samples cannot advance coverage.
    assert after == before
    integrity = assert_ledger_integrity_matrix_v1(
        productive_ledger_path=prod, join_ledger_path=join
    )
    assert integrity["productive_to_join_bijection_valid"] is True


def test_03_repository_sha_and_preregistration_rejected_before_mutation(tmp_path: Path) -> None:
    authority = build_productive_bridge_cycle_authority_v1(
        campaign_id="c",
        repository_sha=REPO_SHA,
        session_id="s",
        market_sample_id="msi_test",
    )
    cycle = {
        "session_id": "s",
        "cycle_id": "c1",
        "canonical_volatility_typed_binding": {"estimate_present": True},
        "double_play_typed_volatility_presence_gate": {
            "max_age_policy_evidence": {"estimate_as_of_event_time": "2023-01-01T00:00:00Z"}
        },
        "productive_bridge_cycle_authority": authority,
    }
    with pytest.raises(ProductiveEvidenceAccumulationError, match="repository_sha_mismatch"):
        authorize_productive_bridge_cycle_input_v1(
            cycle,
            expected_repository_sha="0" * 40,
            expected_preregistration_digest=PREREG,
        )
    bad = dict(authority)
    bad["preregistration_digest"] = "0" * 64
    cycle["productive_bridge_cycle_authority"] = bad
    with pytest.raises(
        ProductiveEvidenceAccumulationError, match="preregistration_digest_mismatch"
    ):
        authorize_productive_bridge_cycle_input_v1(
            cycle,
            expected_repository_sha=REPO_SHA,
            expected_preregistration_digest=PREREG,
        )
    assert not (tmp_path / "prod.jsonl").exists()


def test_04_synthetic_fixture_and_missing_fields_rejected(tmp_path: Path) -> None:
    authority = build_productive_bridge_cycle_authority_v1(
        campaign_id="c",
        repository_sha=REPO_SHA,
        session_id="s",
        market_sample_id="msi_test",
    )
    authority["synthetic"] = True
    cycle = {
        "session_id": "s",
        "cycle_id": "c1",
        "canonical_volatility_typed_binding": {"x": 1},
        "double_play_typed_volatility_presence_gate": {"max_age_policy_evidence": {"a": 1}},
        "productive_bridge_cycle_authority": authority,
    }
    with pytest.raises(ProductiveEvidenceAccumulationError, match="authority_flag_invalid"):
        authorize_productive_bridge_cycle_input_v1(
            cycle, expected_repository_sha=REPO_SHA, expected_preregistration_digest=PREREG
        )
    authority = build_productive_bridge_cycle_authority_v1(
        campaign_id="c",
        repository_sha=REPO_SHA,
        session_id="s",
        market_sample_id="msi_test",
    )
    cycle = {
        "session_id": "s",
        "cycle_id": "c1",
        "canonical_volatility_typed_binding": {},
        "double_play_typed_volatility_presence_gate": {"max_age_policy_evidence": {"a": 1}},
        "productive_bridge_cycle_authority": authority,
        "forced_wiring": True,
    }
    with pytest.raises(ProductiveEvidenceAccumulationError, match="fixture_input_rejected"):
        authorize_productive_bridge_cycle_input_v1(
            cycle, expected_repository_sha=REPO_SHA, expected_preregistration_digest=PREREG
        )
    cycle = {
        "session_id": "s",
        "cycle_id": "c1",
        "canonical_volatility_typed_binding": {},
        "double_play_typed_volatility_presence_gate": {},
        "productive_bridge_cycle_authority": build_productive_bridge_cycle_authority_v1(
            campaign_id="c",
            repository_sha=REPO_SHA,
            session_id="s",
            market_sample_id="msi_test",
        ),
    }
    with pytest.raises(
        ProductiveEvidenceAccumulationError, match="missing_canonical_volatility_typed_binding"
    ):
        authorize_productive_bridge_cycle_input_v1(
            cycle, expected_repository_sha=REPO_SHA, expected_preregistration_digest=PREREG
        )
    cycle["canonical_volatility_typed_binding"] = {"estimate_present": True}
    with pytest.raises(
        ProductiveEvidenceAccumulationError, match="missing_max_age_policy_evidence"
    ):
        authorize_productive_bridge_cycle_input_v1(
            cycle, expected_repository_sha=REPO_SHA, expected_preregistration_digest=PREREG
        )


def test_05_empty_input_creates_no_files(tmp_path: Path) -> None:
    prod, join, q, persist = _paths(tmp_path)
    report = run_productive_bridge_accumulation_session_v1(
        session_id="empty",
        campaign_id="campaign_empty",
        repository_sha=REPO_SHA,
        samples=[],
        repo_root=ROOT,
        productive_ledger_path=prod,
        join_ledger_path=join,
        quarantine_ledger_path=q,
        typed_volatility_persistence_path=persist,
    )
    assert report["status"] == "NO_ELIGIBLE_PRODUCTIVE_INPUT"
    assert report["ledgers_mutated"] is False
    assert not prod.exists()
    assert not join.exists()
    assert not q.exists()


def test_06_restart_separates_restored_history_from_new_estimates(tmp_path: Path) -> None:
    prod, join, q, persist = _paths(tmp_path)
    first = run_productive_bridge_accumulation_session_v1(
        session_id="restart-s1",
        campaign_id="campaign_restart",
        repository_sha=REPO_SHA,
        samples=deterministic_productive_mark_path_v1(count=62),
        repo_root=ROOT,
        productive_ledger_path=prod,
        join_ledger_path=join,
        quarantine_ledger_path=q,
        typed_volatility_persistence_path=persist,
        complete_session=False,
    )
    assert first["records_appended"] >= 1
    session = first["session"]
    second = run_productive_bridge_accumulation_session_v1(
        session_id="restart-s1",
        campaign_id="campaign_restart",
        repository_sha=REPO_SHA,
        samples=deterministic_productive_mark_path_v1(count=62, start_unix=1_700_100_000.0),
        repo_root=ROOT,
        productive_ledger_path=prod,
        join_ledger_path=join,
        quarantine_ledger_path=q,
        typed_volatility_persistence_path=persist,
        process_restart=True,
        existing_resume_token=session["resume_token"],
        existing_session_mapping=session,
        complete_session=True,
    )
    assert second["process_restart"] is True
    assert second["session"]["restart_generation"] >= 1
    assert second["restored_history_record_ids"]
    # Restored history ids are not re-counted as new estimates from this session.
    overlap = set(second["restored_history_record_ids"]) & set(second["new_estimate_record_ids"])
    assert not overlap


def test_07_bridge_state_binding_and_guards(tmp_path: Path) -> None:
    state = HardenedBridgeSessionStateV2()
    bound = bind_accumulation_state_to_hardened_bridge_session_v1(
        state,
        session_id="bind-api",
        session_start_event_time="2023-11-14T22:13:20Z",
        repository_sha=REPO_SHA,
        campaign_id="campaign_api",
        repo_root=ROOT,
        productive_ledger_path=tmp_path / "prod.jsonl",
        join_ledger_path=tmp_path / "join.jsonl",
        quarantine_ledger_path=tmp_path / "q.jsonl",
    )
    assert bound.productive_evidence_accumulation_state is not None
    assert bound.productive_evidence_accumulation_state.campaign_id == "campaign_api"
    assert bound.productive_evidence_accumulation_state.require_authoritative_bridge_cycle is True
    guards = assert_architecture_guards_v1(repo_root=ROOT)
    assert guards["guards_pass"] is True
    assert THRESHOLD_STATUS == "UNRESOLVED_MAX_AGE"
    assert ENFORCEMENT_APPLIED is False
    assert NUMERIC_THRESHOLD_SELECTED is False
    assert PRODUCTIVE_BRIDGE_BINDING_CAPABILITY_ID


def test_08_append_only_chain_and_default_paths_untouched(tmp_path: Path) -> None:
    prod, join, q, persist = _paths(tmp_path)
    run_productive_bridge_accumulation_session_v1(
        session_id="chain-s1",
        campaign_id="campaign_chain",
        repository_sha=REPO_SHA,
        samples=deterministic_productive_mark_path_v1(count=62),
        repo_root=ROOT,
        productive_ledger_path=prod,
        join_ledger_path=join,
        quarantine_ledger_path=q,
        typed_volatility_persistence_path=persist,
    )
    envelopes = load_productive_evidence_ledger_v1(prod)
    assert envelopes
    prev = envelopes[0].prev_ledger_chain_digest
    assert prev == "0" * 64
    for env in envelopes[1:]:
        assert env.prev_ledger_chain_digest
    default_prod = ROOT / DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH
    default_join = ROOT / DEFAULT_JOIN_LEDGER_RELATIVE_PATH
    default_q = ROOT / DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH
    assert not default_prod.exists()
    assert not default_join.exists()
    assert not default_q.exists()


def test_09_invalid_digest_and_enforcement_flags_remain_safe(tmp_path: Path) -> None:
    prod, join, q, persist = _paths(tmp_path)
    run_productive_bridge_accumulation_session_v1(
        session_id="safe-s1",
        campaign_id="campaign_safe",
        repository_sha=REPO_SHA,
        samples=deterministic_productive_mark_path_v1(count=62),
        repo_root=ROOT,
        productive_ledger_path=prod,
        join_ledger_path=join,
        quarantine_ledger_path=q,
        typed_volatility_persistence_path=persist,
    )
    text = prod.read_text(encoding="utf-8")
    lines = text.splitlines()
    payload = json.loads(lines[-1])
    payload["ledger_chain_digest"] = "deadbeef" * 8
    # Corrupt tail must fail closed on load.
    prod.write_text("\n".join(lines[:-1] + [json.dumps(payload)]) + "\n", encoding="utf-8")
    with pytest.raises(ProductiveEvidenceAccumulationError):
        load_productive_evidence_ledger_v1(prod)
    assert THRESHOLD_STATUS == "UNRESOLVED_MAX_AGE"
    assert ENFORCEMENT_APPLIED is False
