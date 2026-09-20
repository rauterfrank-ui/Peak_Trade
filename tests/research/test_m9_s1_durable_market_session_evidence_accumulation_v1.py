"""Tests for M9-S1 durable market session evidence accumulation v1."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from research.m9_s1_durable_market_session_evidence_accumulation_v1.architecture_guards_v1 import (
    assert_architecture_guards_v1,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.constants_v1 import (
    COUNTERFACTUAL_CANDIDATE_MAX_AGE_SECONDS,
    ENFORCEMENT_ENABLED,
    EXTERNAL_EFFECT_AUTHORIZED,
    NUMERIC_MAX_AGE_DECIDED,
    PRODUCTIVE_PARAMETER_MUTATED,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.counterfactual_replay_v1 import (
    run_counterfactual_replay_v1,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.models_v1 import (
    ObservationSourceClassV1,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.observation_ledger_v1 import (
    load_m9_s1_observation_ledger_v1,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.passive_accumulation_v1 import (
    passive_accumulate_from_bridge_cycle_v1,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.runner_v1 import (
    run_offline_replay_and_owner_review_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.runtime_v1 import (
    bind_accumulation_state_v1,
)
from tests.research.test_canonical_volatility_max_age_productive_research_evidence_accumulation_v1 import (
    T0,
    _cycle,
)

ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = "d801828dc3c1f8c4efd3c1fb50c05dfb9d79179c"


def _fixture_state(tmp_path: Path):
    return bind_accumulation_state_v1(
        session_id="m9s1-sess",
        session_start_event_time=T0.isoformat().replace("+00:00", "Z"),
        repository_sha=BASE_SHA,
        venue="OKX",
        canonical_instrument_id="ETH-USD_UM_XPERP-310404",
        venue_instrument_id="ETH-USD-SWAP",
        repo_root=tmp_path,
        productive_ledger_path=tmp_path / "prod.jsonl",
        join_ledger_path=tmp_path / "join.jsonl",
        quarantine_ledger_path=tmp_path / "q.jsonl",
    )


def test_architecture_guards_pass() -> None:
    guards = assert_architecture_guards_v1(repo_root=ROOT)
    assert guards["guards_pass"] is True
    assert guards["numeric_max_age_decided"] is False
    assert guards["enforcement_enabled"] is False


def test_passive_accumulation_fixture_and_replay_deterministic(tmp_path: Path) -> None:
    state = _fixture_state(tmp_path)
    obs_ledger = tmp_path / "m9_obs.jsonl"
    cycles = []
    for idx, age in enumerate([30.0, 90.0, 400.0, 900.0, 2000.0]):
        cycle = _cycle(
            session_id="m9s1-sess",
            cycle_id=f"c{idx}",
            age_seconds=age,
            event_offset=idx * 120,
        )
        cycles.append(cycle)
        result = passive_accumulate_from_bridge_cycle_v1(
            cycle,
            state=state,
            source_class=ObservationSourceClassV1.SHADOW_OBSERVED,
            m9_s1_observation_ledger_path=obs_ledger,
        )
        assert result["trading_behavior_mutated"] is False
        assert result["presence_gate_semantics_unchanged"] is True
        assert result["alpha_gate_semantics_unchanged"] is True

    assert state.join_ledger_path.exists()

    replay1 = run_counterfactual_replay_v1(join_ledger_path=state.join_ledger_path)
    replay2 = run_counterfactual_replay_v1(join_ledger_path=state.join_ledger_path)
    assert replay1["artifact_digest"] == replay2["artifact_digest"]
    assert len(replay1["per_candidate"]) == len(COUNTERFACTUAL_CANDIDATE_MAX_AGE_SECONDS)

    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"
    pkg1 = run_offline_replay_and_owner_review_v1(
        repo_root=tmp_path,
        join_ledger_path=state.join_ledger_path,
        m9_s1_observation_ledger_path=obs_ledger,
        output_dir=out1,
        repository_sha=BASE_SHA,
    )
    pkg2 = run_offline_replay_and_owner_review_v1(
        repo_root=tmp_path,
        join_ledger_path=state.join_ledger_path,
        m9_s1_observation_ledger_path=obs_ledger,
        output_dir=out2,
        repository_sha=BASE_SHA,
    )
    assert pkg1["replay_artifact_digest"] == pkg2["replay_artifact_digest"]
    assert pkg1["owner_review_digest"] == pkg2["owner_review_digest"]

    obs_rows = load_m9_s1_observation_ledger_v1(obs_ledger)
    assert all(row["evidence_source_class"] == "SHADOW_OBSERVED" for row in obs_rows)
    assert len(obs_rows) >= 1


def test_invariants_module_constants() -> None:
    assert NUMERIC_MAX_AGE_DECIDED is False
    assert ENFORCEMENT_ENABLED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert PRODUCTIVE_PARAMETER_MUTATED is False


def test_observation_ledger_dedup_idempotent(tmp_path: Path) -> None:
    state = _fixture_state(tmp_path)
    obs_ledger = tmp_path / "m9_obs.jsonl"
    cycle = _cycle(session_id="m9s1-sess", cycle_id="c-dup", age_seconds=60.0)
    first = passive_accumulate_from_bridge_cycle_v1(
        cycle,
        state=state,
        source_class=ObservationSourceClassV1.SHADOW_OBSERVED,
        m9_s1_observation_ledger_path=obs_ledger,
    )
    second = passive_accumulate_from_bridge_cycle_v1(
        cycle,
        state=state,
        source_class=ObservationSourceClassV1.SHADOW_OBSERVED,
        m9_s1_observation_ledger_path=obs_ledger,
    )
    assert first["m9_s1_observation_append"]["action"] == "APPENDED"
    assert second["m9_s1_observation_append"]["action"] == "DUPLICATE_IDEMPOTENT"
    assert len(load_m9_s1_observation_ledger_v1(obs_ledger)) == 1


def test_synthetic_fixture_source_class_observation_only(tmp_path: Path) -> None:
    state = _fixture_state(tmp_path)
    obs_ledger = tmp_path / "m9_obs.jsonl"
    cycle = _cycle(session_id="m9s1-sess", cycle_id="c-fix", age_seconds=45.0)
    cycle["fixture"] = True
    result = passive_accumulate_from_bridge_cycle_v1(
        cycle,
        state=state,
        source_class=ObservationSourceClassV1.SYNTHETIC_FIXTURE,
        m9_s1_observation_ledger_path=obs_ledger,
    )
    assert result["append_result"]["action"] == "QUARANTINED"
    assert result["m9_s1_observation_append"]["action"] == "APPENDED"
    row = load_m9_s1_observation_ledger_v1(obs_ledger)[0]
    assert row["evidence_source_class"] == "SYNTHETIC_FIXTURE"
