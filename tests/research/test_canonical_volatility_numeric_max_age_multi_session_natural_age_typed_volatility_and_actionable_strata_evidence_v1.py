"""Focused tests for multi-session natural-age typed-vol + actionable strata v1."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.duration_v1 import (
    MonotonicDurationAuthorityV1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.independence_v1 import (
    assert_exit_precedence_preserved_v1,
    build_exit_risk_safety_independence_record_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    MarketSampleV1,
    S03ScopeBindingsV1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1 import (
    assert_architecture_guards_v1,
    build_campaign_aggregation_v1,
    build_typed_volatility_comparison_v1,
    derive_opportunity_stratum_v1,
    early_age_density_support_matrix_v1,
    evaluate_multi_session_typed_vol_readiness_v1,
    materialize_fresh_estimate_from_mark_prices_v1,
    plan_early_age_evidence_snapshots_v1,
    run_full_alpha_counterfactual_comparison_v1,
    verify_old_s03_evidence_digests_unchanged_v1,
    write_typed_s03_session_cycle_evidence_v1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.constants_v1 import (
    FORBIDDEN_SCAFFOLD_SUBSTRINGS,
    OPPORTUNITY_STRATA_V1,
    PACKAGE_MARKER,
    READY_FOR_POLICY_ENFORCEMENT,
    READY_FOR_POLICY_IMPLEMENTATION,
    READY_FOR_POLICY_SELECTION,
    S03_FROZEN_FILE_DIGESTS,
    S03_LEGACY_SESSION_REL,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.full_alpha_counterfactual_harness_v1 import (
    default_digest_alpha_evaluator_v1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.models_v1 import (
    AlphaComponentSnapshotV1,
    MultiSessionTypedVolEvidenceError,
    classify_first_divergence_v1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.opportunity_strata_v1 import (
    assert_long_short_mirror_support_v1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.s03_typed_evidence_cycle_v1 import (
    build_minimal_frozen_cmc_shell_v1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.typed_volatility_comparison_v1 import (
    _reject_synthetic_literals_v1,
    clone_aged_estimate_immutable_v1,
)
from trading.master_v2 import canonical_volatility_estimate_materializer_v1 as materializer
from trading.master_v2 import canonical_volatility_estimate_typed_consumption_contract_v1 as typed

ROOT = Path(__file__).resolve().parents[2]
S03_DIR = ROOT / S03_LEGACY_SESSION_REL


def _bindings() -> S03ScopeBindingsV1:
    return S03ScopeBindingsV1(
        campaign_id="camp_test",
        session_label="S99",
        session_id="camp_test_s99",
        preregistration_id="camp_test_s99",
        preregistration_digest="a" * 64,
        contract_digest="b" * 64,
        runbook_digest="c" * 64,
        authorization_id="auth_test",
        authorization_digest="d" * 64,
        repository_sha="e" * 40,
        venue="OKX",
        instrument="ETH-USD-SWAP",
        network_scope="PUBLIC_MD_ONLY",
        session_scope="ADDITIONAL_EVIDENCE",
        duration_seconds=10860,
    )


def _estimate(*, value: float = 0.001, source_digest: str | None = None):
    return typed.build_canonical_volatility_estimate_v1(
        value=value,
        observation_count=60,
        as_of_event_time=datetime(2026, 6, 1, 1, 0, tzinfo=timezone.utc),
        fallback_used=False,
        source_digest=source_digest,
    )


def _fixture_series():
    fixture = materializer.exact_known_61_price_fixture_v1()
    series = fixture["mark_price"]
    times = [t.to_pydatetime().replace(tzinfo=timezone.utc) for t in series.index]
    return [float(x) for x in series.tolist()], times


def test_01_synthetic_volatility_scaffold_rejected() -> None:
    with pytest.raises(MultiSessionTypedVolEvidenceError):
        _reject_synthetic_literals_v1(value=0.12, source="scaffold_default")


def test_02_hardcoded_age_probe_removed_from_orchestrator() -> None:
    orch = (
        ROOT / "src/research/canonical_volatility_numeric_max_age_additional_evidence_"
        "s03_productive_session_execution_owner_v1/orchestrator_v1.py"
    ).read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_SCAFFOLD_SUBSTRINGS:
        assert forbidden not in orch
    assert "write_typed_s03_session_cycle_evidence_v1" in orch
    assert "age < 3600" not in orch
    assert "BLOCK_ALPHA_AGE_ONLY" not in orch


def test_03_aged_estimate_immutable() -> None:
    aged = _estimate(value=0.002)
    before = aged.to_dict()
    clone_aged_estimate_immutable_v1(aged)
    assert aged.to_dict() == before
    build_typed_volatility_comparison_v1(
        session_id="s",
        market_sample_id="m",
        market_context_digest="ctx",
        aged_estimate=aged,
        fresh_estimate=_estimate(value=0.003, source_digest="f" * 64),
        age_seconds=120.0,
    )
    assert aged.to_dict() == before


def test_04_fresh_estimate_from_canonical_estimator() -> None:
    prices, times = _fixture_series()
    est = materialize_fresh_estimate_from_mark_prices_v1(
        prices,
        event_times_utc=times,
        as_of_event_time=times[-1],
    )
    assert est.estimator == typed.CANONICAL_ESTIMATOR
    assert est.estimator_version == typed.CANONICAL_ESTIMATOR_VERSION
    assert est.unit == typed.CANONICAL_UNIT


def test_05_unit_horizon_mismatch_not_comparable(monkeypatch: pytest.MonkeyPatch) -> None:
    aged = _estimate(value=0.001)
    fresh = _estimate(value=0.002, source_digest="9" * 64)

    def _boom(
        a: object,
        f: object,
    ) -> None:
        raise MultiSessionTypedVolEvidenceError("unit_mismatch_not_comparable")

    monkeypatch.setattr(
        "research.canonical_volatility_numeric_max_age_multi_session_natural_age_"
        "typed_volatility_and_actionable_strata_evidence_v1.full_alpha_counterfactual_harness_v1."
        "assert_estimates_contract_compatible_v1",
        _boom,
    )
    cf = run_full_alpha_counterfactual_comparison_v1(
        session_id="s",
        market_sample_id="m",
        market_context_digest="ctx",
        prior_state_digest="p",
        frozen_context=build_minimal_frozen_cmc_shell_v1(bindings=_bindings()),
        aged_estimate=aged,
        fresh_estimate=fresh,
        age_seconds=10.0,
        aged_volatility_record_id="a",
        fresh_volatility_record_id="f",
        non_volatility_input_digest="same",
        expected_non_volatility_input_digest="same",
    )
    assert cf["classification"] == "NOT_COMPARABLE"
    assert cf["FIRST_DIVERGENCE_COMPONENT"] == "CONTRACT_COMPATIBILITY"
    # Canonical builder reject incompatible unit (fail-closed before compare).
    with pytest.raises(Exception):
        typed.build_canonical_volatility_estimate_v1(
            value=0.002,
            observation_count=60,
            as_of_event_time=datetime(2026, 6, 1, 1, 0, tzinfo=timezone.utc),
            fallback_used=False,
            unit="WRONG_UNIT",
        )


def test_06_identical_market_context_enforced() -> None:
    aged = _estimate(value=0.001)
    fresh = _estimate(value=0.002, source_digest="f" * 64)
    shell = build_minimal_frozen_cmc_shell_v1(bindings=_bindings())
    cf = run_full_alpha_counterfactual_comparison_v1(
        session_id="s",
        market_sample_id="m",
        market_context_digest="ctx_digest",
        prior_state_digest="p",
        frozen_context=shell,
        aged_estimate=aged,
        fresh_estimate=fresh,
        age_seconds=30.0,
        aged_volatility_record_id="a",
        fresh_volatility_record_id="f",
        non_volatility_input_digest="digest_a",
        expected_non_volatility_input_digest="digest_a",
    )
    assert cf["MARKET_CONTEXT_DIGEST"] == "ctx_digest"
    assert cf["NON_PERSISTING_READ_ONLY"] is True


def test_07_confounder_non_volatility_input() -> None:
    aged = _estimate(value=0.001)
    fresh = _estimate(value=0.002, source_digest="f" * 64)
    cf = run_full_alpha_counterfactual_comparison_v1(
        session_id="s",
        market_sample_id="m",
        market_context_digest="ctx",
        prior_state_digest="p",
        frozen_context=build_minimal_frozen_cmc_shell_v1(bindings=_bindings()),
        aged_estimate=aged,
        fresh_estimate=fresh,
        age_seconds=30.0,
        aged_volatility_record_id="a",
        fresh_volatility_record_id="f",
        non_volatility_input_digest="left",
        expected_non_volatility_input_digest="right",
    )
    assert cf["classification"] == "NOT_COMPARABLE"
    assert "NON_VOLATILITY_INPUT_DIGEST_MISMATCH" in cf["CONFOUNDERS"]


def test_08_counterfactual_no_state_mutation() -> None:
    from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
        bind_typed_canonical_volatility_estimate_into_market_context_v1,
    )

    snap = default_digest_alpha_evaluator_v1(
        bind_typed_canonical_volatility_estimate_into_market_context_v1(
            build_minimal_frozen_cmc_shell_v1(bindings=_bindings()),
            _estimate(),
        )
    )
    assert snap.state_mutations == ()
    with pytest.raises(MultiSessionTypedVolEvidenceError, match="state_mutation"):
        from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.full_alpha_counterfactual_harness_v1 import (
            _assert_no_side_effects_v1,
        )

        _assert_no_side_effects_v1(
            AlphaComponentSnapshotV1(
                directional_assessment="d",
                survival="s",
                suitability="u",
                composition="c",
                switch_state="sw",
                entry_permission="e",
                entry_outcome="o",
                hold_reduce_exit="h",
                final_outcome="f",
                evaluation_digest="x",
                state_mutations=("persist",),
            )
        )


def test_09_counterfactual_no_order_intents() -> None:
    from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
        bind_typed_canonical_volatility_estimate_into_market_context_v1,
    )
    from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.full_alpha_counterfactual_harness_v1 import (
        _assert_no_side_effects_v1,
    )

    snap = default_digest_alpha_evaluator_v1(
        bind_typed_canonical_volatility_estimate_into_market_context_v1(
            build_minimal_frozen_cmc_shell_v1(bindings=_bindings()),
            _estimate(),
        )
    )
    assert snap.order_intents == ()
    with pytest.raises(MultiSessionTypedVolEvidenceError, match="order_activity"):
        _assert_no_side_effects_v1(
            AlphaComponentSnapshotV1(
                directional_assessment="d",
                survival="s",
                suitability="u",
                composition="c",
                switch_state="sw",
                entry_permission="e",
                entry_outcome="o",
                hold_reduce_exit="h",
                final_outcome="f",
                evaluation_digest="x",
                order_intents=("BUY",),
            )
        )


def test_10_first_divergence_component() -> None:
    base = dict(
        directional_assessment="d",
        survival="s",
        suitability="u",
        composition="c",
        switch_state="sw",
        entry_permission="e1",
        entry_outcome="o1",
        hold_reduce_exit="h",
        final_outcome="f1",
        evaluation_digest="x",
    )
    aged = AlphaComponentSnapshotV1(**base)
    fresh = AlphaComponentSnapshotV1(**{**base, "entry_permission": "e2", "final_outcome": "f2"})
    classification, first = classify_first_divergence_v1(aged, fresh)
    assert classification == "ENTRY_PERMISSION_CHANGE"
    assert first == "entry_permission"


def test_11_opportunity_strata_from_real_decision() -> None:
    rec = derive_opportunity_stratum_v1(
        productive_record={
            "decision_outcome": "entry",
            "selected_side": "long",
            "position_state": "flat",
            "entry_opportunity": True,
        }
    )
    assert rec["OPPORTUNITY_STRATUM"] in OPPORTUNITY_STRATA_V1
    assert rec["SYNTHETIC_ACTIONABLE_OUTCOME"] is False
    assert rec["OPPORTUNITY_STRATUM"] == "LONG_ENTRY_ELIGIBLE"


def test_12_long_short_strata_mirror() -> None:
    mirror = assert_long_short_mirror_support_v1()
    assert mirror["MIRROR_SUFFIXES_EQUAL"] is True
    assert mirror["LONG_STRATA_SUPPORTED"] is True
    assert mirror["SHORT_STRATA_SUPPORTED"] is True


def test_13_campaign_aggregation_append_only_reproducible(tmp_path: Path) -> None:
    s1 = tmp_path / "S01"
    s2 = tmp_path / "S02"
    for sdir, sid in ((s1, "s01"), (s2, "s02")):
        sdir.mkdir()
        (sdir / "terminal_verdict.json").write_text(
            json.dumps({"session_id": sid, "status": "PASS"}), encoding="utf-8"
        )
        (sdir / "market_samples.jsonl").write_text(
            json.dumps({"sample_identity": f"{sid}-1"}) + "\n", encoding="utf-8"
        )
        (sdir / "typed_volatility_comparisons.jsonl").write_text(
            json.dumps({"age_seconds": 30.0}) + "\n" + json.dumps({"age_seconds": 90.0}) + "\n",
            encoding="utf-8",
        )
        (sdir / "full_alpha_counterfactuals.jsonl").write_text(
            json.dumps(
                {
                    "classification": "ENTRY_PERMISSION_CHANGE",
                    "AGE_ONLY_CAUSALITY_SUPPORTED": True,
                    "FINAL_OUTCOME_CHANGED": True,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (sdir / "opportunity_strata.jsonl").write_text(
            json.dumps({"OPPORTUNITY_STRATUM": "LONG_ENTRY_ELIGIBLE"})
            + "\n"
            + json.dumps({"OPPORTUNITY_STRATUM": "SHORT_DIRECTIONAL_OPPORTUNITY"})
            + "\n",
            encoding="utf-8",
        )
    a = build_campaign_aggregation_v1(campaign_id="c1", session_dirs=[s1, s2])
    b = build_campaign_aggregation_v1(campaign_id="c1", session_dirs=[s1, s2])
    assert a["aggregation_digest"] == b["aggregation_digest"]
    assert a["CROSS_SESSION_REPLICATION_AVAILABLE"] is True
    assert a["SESSION_EVIDENCE_IMMUTABLE"] is True
    assert a["PRODUCTIVE_SESSION_COUNT"] == 2


@pytest.mark.skipif(not S03_DIR.is_dir(), reason="local S03 evidence not present")
def test_14_old_s03_digests_unchanged() -> None:
    result = verify_old_s03_evidence_digests_unchanged_v1(repo_root=ROOT)
    assert result["OLD_S03_EVIDENCE_DIGESTS_UNCHANGED"] is True
    for name, expected in S03_FROZEN_FILE_DIGESTS.items():
        actual = hashlib.sha256((S03_DIR / name).read_bytes()).hexdigest()
        assert actual == expected


@pytest.mark.skipif(not S03_DIR.is_dir(), reason="local S03 evidence not present")
def test_15_old_s03_backward_verification() -> None:
    result = verify_old_s03_evidence_digests_unchanged_v1(repo_root=ROOT)
    assert result["OLD_S03_BACKWARD_VERIFICATION_PASS"] is True


def test_15b_backward_verify_detects_drift(tmp_path: Path) -> None:
    session = tmp_path / "S03"
    session.mkdir()
    (session / "heartbeat.jsonl").write_text("drift\n", encoding="utf-8")
    with pytest.raises(MultiSessionTypedVolEvidenceError):
        verify_old_s03_evidence_digests_unchanged_v1(
            repo_root=ROOT,
            session_dir=session,
            frozen_digests={"heartbeat.jsonl": "0" * 64},
        )


def test_16_early_age_density_no_fabricated_samples() -> None:
    plan = plan_early_age_evidence_snapshots_v1(
        distinct_sample_identities=["a", "a", "b"],
        age_seconds_by_identity={"a": 30.0, "b": 90.0},
        minimum_network_interval_seconds=60.0,
        max_extra_snapshots_per_sample=1,
    )
    primary = [p for p in plan if p["snapshot_kind"] == "PRIMARY_ON_DISTINCT_SAMPLE"]
    assert len(primary) == 2  # duplicate identity skipped
    assert all(p["fabricates_market_sample"] is False for p in plan)
    assert all(p["fabricates_market_time"] is False for p in plan)
    with pytest.raises(MultiSessionTypedVolEvidenceError):
        plan_early_age_evidence_snapshots_v1(
            distinct_sample_identities=["x"],
            age_seconds_by_identity={"x": 10.0},
            minimum_network_interval_seconds=0.0,
        )


def test_17_duplicate_samples_do_not_advance_confirmation() -> None:
    matrix = early_age_density_support_matrix_v1()
    assert matrix["DUPLICATE_SAMPLES_DO_NOT_ADVANCE_CONFIRMATION"] is True


def test_18_19_20_exit_risk_safety_independence() -> None:
    bindings = _bindings()
    for blocked in (False, True):
        rec = build_exit_risk_safety_independence_record_v1(
            bindings=bindings,
            alpha_gate_blocked=blocked,
            monotonic_elapsed_seconds=1.0,
            receive_time_unix_seconds=1.0,
        )
        assert_exit_precedence_preserved_v1(rec)
        assert rec["mandatory_exit_available"] is True
        assert rec["hard_risk_reduce_available"] is True
        assert rec["safety_path_available"] is True
        assert rec["SAFETY_NOT_DEPENDENT_ON_ALPHA_TRIGGER"] is True
        assert rec["RISK_NOT_DEPENDENT_ON_ALPHA_TRIGGER"] is True
        assert rec["MANDATORY_EXIT_NOT_DEPENDENT_ON_ALPHA_TRIGGER"] is True


def test_21_no_bull_bear_double_play_core_diff() -> None:
    # Capability must not touch core strategy owners (empty git diff vs origin/main).
    import subprocess

    cores = [
        "src/trading/master_v2/directional_assessment_v1.py",
        "src/trading/master_v2/double_play_composition.py",
        "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
        "src/trading/master_v2/double_play_survival.py",
        "src/trading/master_v2/double_play_suitability.py",
    ]
    for path in cores:
        out = subprocess.check_output(
            ["git", "diff", "origin/main", "--", path],
            cwd=str(ROOT),
            text=True,
        )
        assert out.strip() == "", path


def test_22_readiness_policy_flags_remain_false() -> None:
    assert READY_FOR_POLICY_SELECTION is False
    assert READY_FOR_POLICY_IMPLEMENTATION is False
    assert READY_FOR_POLICY_ENFORCEMENT is False
    readiness = evaluate_multi_session_typed_vol_readiness_v1(repo_root=ROOT)
    assert readiness["READY_FOR_POLICY_SELECTION"] is False
    assert readiness["READY_FOR_POLICY_IMPLEMENTATION"] is False
    assert readiness["READY_FOR_POLICY_ENFORCEMENT"] is False
    assert readiness["NUMERIC_MAX_AGE_SELECTED"] is False


def test_architecture_guards_and_package_marker() -> None:
    guards = assert_architecture_guards_v1(repo_root=ROOT)
    assert guards["ok"] is True
    assert PACKAGE_MARKER.endswith("=true")
    assert guards["SYNTHETIC_VOLATILITY_SCAFFOLD_REMOVED"] is True


def test_typed_cycle_writer_offline(tmp_path: Path) -> None:
    prices, times = _fixture_series()
    # Extend with a few more natural ages for typed comparisons.
    samples = []
    t0 = times[0].timestamp()
    for i, (price, ts) in enumerate(zip(prices, times)):
        samples.append(
            MarketSampleV1(
                sample_identity=f"id-{i}",
                mark_price=float(price),
                event_time_unix_seconds=float(ts.timestamp()),
                receive_time_unix_seconds=float(ts.timestamp()) + 0.1,
                monotonic_elapsed_seconds=float(i),
            )
        )
    # Extra distinct sample beyond warmup for age progression.
    last = times[-1]
    for j in range(1, 4):
        ts = last + timedelta(seconds=60 * j)
        samples.append(
            MarketSampleV1(
                sample_identity=f"id-extra-{j}",
                mark_price=float(prices[-1]) * (1.0 + 0.0001 * j),
                event_time_unix_seconds=float(ts.timestamp()),
                receive_time_unix_seconds=float(ts.timestamp()) + 0.1,
                monotonic_elapsed_seconds=float(len(prices) + j),
            )
        )
    clock_state = {"t": 0.0}

    def _clock() -> float:
        return float(clock_state["t"])

    duration = MonotonicDurationAuthorityV1(monotonic_clock=_clock)
    duration.start()
    clock_state["t"] = 10860.0
    session_dir = tmp_path / "S99"
    session_dir.mkdir()
    out = write_typed_s03_session_cycle_evidence_v1(
        session_dir=session_dir,
        bindings=_bindings(),
        samples=samples,
        duration=duration,
    )
    assert out["SYNTHETIC_VOLATILITY_SCAFFOLD_USED"] is False
    assert out["HARDCODED_AGE_DECISION_PROBE_USED"] is False
    assert (session_dir / "typed_volatility_comparisons.jsonl").is_file()
    assert (session_dir / "full_alpha_counterfactuals.jsonl").is_file()
    assert (session_dir / "opportunity_strata.jsonl").is_file()
    # No scaffold literals in written vol records.
    vol_text = (session_dir / "volatility_records.jsonl").read_text(encoding="utf-8")
    assert "0.12" not in vol_text or 'old_volatility_value": 0.12' not in vol_text
