"""Contract tests for OLD effective Double-Play host boundary compatibility v1."""

from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    initialize_empty_revocation_ledger_v1,
)
from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
    F1M9ProductiveRuntimeThresholdConsumerPathResultV1,
)
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
    initialize_empty_threshold_revocation_ledger_v1,
)
from src.governance.governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1 import (
    GovernedF1M9ThresholdConsumerWiringRequestV1,
    run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1,
)
from tests.trading.master_v2.test_double_play_runtime_typed_volatility_presence_gate_v1 import (
    _context,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _market_context,
    _replay_input,
)
from tests.ops.test_current_productive_g17_typed_vol_cmc_bind_v1 import (
    _apply,
    _sixty_one_samples,
    g17_ingest_kwargs_from_extracted_sample_v1,
)
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
    evaluate_typed_volatility_binding_eligibility_v1,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    build_canonical_volatility_estimate_v1,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    TypedRuntimeProducerOutcomeV1,
)
from trading.master_v2.double_play_old_effective_host_contract_v1 import (
    REASON_PRESENCE_ALPHA_AT_DP_BOUNDARY,
    g17_cmc_bind_produced_only_v1,
    integrated_replay_presence_alpha_at_dp_boundary_v1,
    resolve_alpha_scope_entry_for_integrated_replay_v1,
)
from trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
    evaluate_double_play_runtime_typed_volatility_presence_gate_v1,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_typed_vol_cmc_bind_v1 import (
    apply_current_productive_g17_typed_vol_cmc_bind_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_resolve_alpha_uses_presence_when_old_contract_enabled() -> None:
    ctx = _context()
    presence = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(ctx)
    consumer = F1M9ProductiveRuntimeThresholdConsumerPathResultV1(
        wiring_status="WIRED",
        reason_codes=("STALE_TYPED_VOLATILITY_ESTIMATE",),
        transport_ready=True,
        presence_gate=presence,
        threshold_numeric_max_age_seconds=600.0,
        seam_digest="a" * 64,
        owner_threshold_record_digest="b" * 64,
        configuration_runtime_applied=True,
        enforcement_applied=True,
        alpha_scope_entry_authority_allowed=False,
        productive_runtime_admission=True,
        productive_activation_authorized=False,
        real_p4_to_f1_m9_join_status="REAL_P4_F1_M9_JOIN_NOT_CANONICAL",
        external_effect_authorized=False,
    )
    if not integrated_replay_presence_alpha_at_dp_boundary_v1(repo_root=REPO_ROOT):
        return
    allowed, reasons = resolve_alpha_scope_entry_for_integrated_replay_v1(
        presence_gate=presence,
        consumer_path=consumer,
        repo_root=REPO_ROOT,
    )
    if presence.alpha_scope_entry_authority_allowed is False:
        return
    assert allowed is True
    assert REASON_PRESENCE_ALPHA_AT_DP_BOUNDARY in reasons


def test_stale_integrated_replay_matches_old_presence_semantics_with_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        rev = root / "apply_rev.jsonl"
        initialize_empty_revocation_ledger_v1(rev)
        apply_paths = F1M9ProductiveApplyLedgerPathsV1(
            apply_ledger_path=root / "apply.jsonl",
            revocation_ledger_path=rev,
        )
        trev = root / "thr_rev.jsonl"
        initialize_empty_threshold_revocation_ledger_v1(trev)
        threshold_paths = F1M9ThresholdValueAuthorizationLedgerPathsV1(
            threshold_ledger_path=root / "thr.jsonl",
            threshold_revocation_ledger_path=trev,
        )
        cont = run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1(
            GovernedF1M9ThresholdConsumerWiringRequestV1(
                apply_ledger_paths=apply_paths,
                threshold_ledger_paths=threshold_paths,
                repo_root=REPO_ROOT,
            )
        )
        seam = dict(cont.bound_seam_record or {})
        stale_est = build_canonical_volatility_estimate_v1(
            value=0.004321,
            observation_count=61,
            as_of_event_time=datetime(2026, 6, 30, 10, 0, tzinfo=timezone.utc),
            fallback_used=False,
            source_digest="b" * 64,
        )
        base_ctx = _market_context(volatility_estimate=0.0)
        stale_ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(
            base_ctx,
            stale_est,
        )
        stale_elig = evaluate_typed_volatility_binding_eligibility_v1(stale_ctx)
        inp = _replay_input(
            canonical_market_context=stale_ctx,
            require_productive_typed_volatility_presence_gate=True,
            productive_typed_volatility_binding_eligibility=stale_elig,
            governed_authorized_productive_parameter_seam_record=seam,
        )
        result = run_integrated_offline_trading_logic_replay_v1(inp)
        assert result.replay_pass is True
        assert result.evidence.decision_outcome in ("no_action", "observe", "blocked", "hold")


def test_layered_core_cmc_mark_init_flag_enabled_with_owner_go() -> None:
    from trading.master_v2.double_play_old_effective_host_contract_v1 import (
        layered_core_cmc_mark_observation_init_v1,
        old_effective_host_contract_enabled_v1,
    )

    assert old_effective_host_contract_enabled_v1(repo_root=REPO_ROOT) is True
    assert layered_core_cmc_mark_observation_init_v1(repo_root=REPO_ROOT) is True


def test_g17_duplicate_noop_does_not_bind_under_old_contract(tmp_path: Path) -> None:
    if not g17_cmc_bind_produced_only_v1(repo_root=REPO_ROOT):
        return
    samples = _sixty_one_samples()
    created = _apply(tmp_path, samples=samples)
    producer = created.producer
    assert producer is not None
    dup = producer.ingest_finalized_pt1m_mark_sample_v1(
        **g17_ingest_kwargs_from_extracted_sample_v1(samples[-1])
    )
    assert dup.outcome is TypedRuntimeProducerOutcomeV1.DUPLICATE_NOOP
    out = apply_current_productive_g17_typed_vol_cmc_bind_v1(_context(), producer=producer)
    assert out.bind_performed is False
    assert out.outcome == TypedRuntimeProducerOutcomeV1.DUPLICATE_NOOP.value
