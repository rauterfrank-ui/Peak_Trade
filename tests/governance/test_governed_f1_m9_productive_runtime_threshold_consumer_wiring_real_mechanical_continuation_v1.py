"""F1/M9 productive runtime threshold consumer wiring tests."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from pathlib import Path

from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    initialize_empty_revocation_ledger_v1,
)
from src.governance.current_productive_activation_policy_v1 import (
    RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
    standing_productive_activation_authorized_v1,
)
from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
    DECISION_CONFIG,
    FORBIDDEN_UNGOVERNED_NUMERIC_DEFAULTS,
    RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS,
    REAL_P4_TO_F1_M9_JOIN_STATUS,
    STATUS_WIRED,
    consumer_wiring_authorized_v1,
    evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1,
)
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
    initialize_empty_threshold_revocation_ledger_v1,
)
from src.governance.governed_f1_m9_productive_runtime_threshold_consumer_wiring_closure_v1 import (
    prove_governed_f1_m9_productive_runtime_threshold_consumer_wiring_v1,
)
from src.governance.governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1 import (
    GovernedF1M9ThresholdConsumerWiringRequestV1,
    resolve_runtime_applied_seam_for_consumer_wiring_v1,
    run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    EXTERNAL_EFFECT,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    ENFORCEMENT_ENABLED,
    NUMERIC_MAX_AGE_DECIDED,
    VolatilityMaxAgeReasonCodeV1,
)
from tests.trading.master_v2.test_double_play_runtime_typed_volatility_presence_gate_v1 import (
    _context,
    _valid_estimate,
)
from trading.master_v2.canonical_market_context_v1 import with_computed_input_digest
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
    evaluate_typed_volatility_binding_eligibility_v1,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    build_canonical_volatility_estimate_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

REPO_ROOT = Path(__file__).resolve().parents[2]
BOUND_THRESHOLD = "e556ea63f68df3651cf38ef4d49d675f94a0e20f67c5b72f9044f9492b9bf109"


def _apply_ledger_paths(tmp_path: Path) -> F1M9ProductiveApplyLedgerPathsV1:
    rev = tmp_path / "apply_revocation.jsonl"
    initialize_empty_revocation_ledger_v1(rev)
    return F1M9ProductiveApplyLedgerPathsV1(
        apply_ledger_path=tmp_path / "apply.jsonl",
        revocation_ledger_path=rev,
    )


def _threshold_ledger_paths(tmp_path: Path) -> F1M9ThresholdValueAuthorizationLedgerPathsV1:
    rev = tmp_path / "threshold_revocation.jsonl"
    initialize_empty_threshold_revocation_ledger_v1(rev)
    return F1M9ThresholdValueAuthorizationLedgerPathsV1(
        threshold_ledger_path=tmp_path / "threshold.jsonl",
        threshold_revocation_ledger_path=rev,
    )


def _bound_context(estimate: object):
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        with_computed_input_digest(_context(volatility_estimate=0.0)),
        estimate,
    )
    return ctx, evaluate_typed_volatility_binding_eligibility_v1(ctx)


def _re_digest_seam(seam: dict) -> dict:
    body = {key: value for key, value in seam.items() if key != "seam_digest"}
    out = dict(seam)
    out["seam_digest"] = compute_content_sha256(body)
    return out


def _canonical_seam(tmp_path: Path) -> dict:
    continuation = run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1(
        GovernedF1M9ThresholdConsumerWiringRequestV1(
            apply_ledger_paths=_apply_ledger_paths(tmp_path),
            threshold_ledger_paths=_threshold_ledger_paths(tmp_path),
            repo_root=REPO_ROOT,
        )
    )
    assert continuation.status == "CONTINUATION_COMPLETE", continuation.blocking_reasons
    assert continuation.bound_seam_record is not None
    return dict(continuation.bound_seam_record)


def test_decision_and_global_invariants() -> None:
    assert consumer_wiring_authorized_v1(repo_root=REPO_ROOT) is True
    assert standing_productive_activation_authorized_v1(repo_root=REPO_ROOT) is True
    assert REAL_P4_TO_F1_M9_JOIN_STATUS == "REAL_P4_F1_M9_JOIN_NOT_CANONICAL"
    assert EXTERNAL_EFFECT is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert PRODUCTIVE_NUMERIC_VALUES_SET == 0
    assert NUMERIC_MAX_AGE_DECIDED is False
    assert ENFORCEMENT_ENABLED is False
    assert prove_governed_f1_m9_productive_runtime_threshold_consumer_wiring_v1(repo_root=REPO_ROOT)


def test_resolve_runtime_applied_seam_idempotent_after_durable_apply(tmp_path: Path) -> None:
    ledger_root = tmp_path / "durable"
    ledger_root.mkdir()
    request = GovernedF1M9ThresholdConsumerWiringRequestV1(
        apply_ledger_paths=_apply_ledger_paths(ledger_root),
        threshold_ledger_paths=_threshold_ledger_paths(ledger_root),
        repo_root=REPO_ROOT,
    )
    first = resolve_runtime_applied_seam_for_consumer_wiring_v1(request)
    second = resolve_runtime_applied_seam_for_consumer_wiring_v1(request)
    assert first is not None
    assert second is not None
    assert first.get("seam_digest") == second.get("seam_digest")


def test_canonical_600s_happy_path_and_lineage(tmp_path: Path) -> None:
    seam = _canonical_seam(tmp_path)
    assert float(seam["numeric_max_age_seconds"]) == float(
        RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS
    )
    assert seam["runtime_applied"] is True
    assert str(seam["threshold_value_authorization_digest"]) == BOUND_THRESHOLD

    ctx, elig = _bound_context(_valid_estimate())
    path = evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(
        market_context=ctx,
        eligibility=elig,
        governed_seam_record=seam,
        require_governed_seam=True,
        runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
        repo_root=REPO_ROOT,
    )
    assert path.wiring_status == STATUS_WIRED
    assert path.threshold_numeric_max_age_seconds == 600.0
    assert path.configuration_runtime_applied is True
    assert path.enforcement_applied is True
    assert path.alpha_scope_entry_authority_allowed is True
    assert path.productive_runtime_admission is True
    assert path.productive_activation_authorized is True


def test_stale_rejection_and_boundary_600_inclusive(tmp_path: Path) -> None:
    seam = _canonical_seam(tmp_path)
    stale_estimate = build_canonical_volatility_estimate_v1(
        value=0.004321,
        observation_count=61,
        as_of_event_time=datetime(2026, 6, 30, 10, 0, tzinfo=timezone.utc),
        fallback_used=False,
        source_digest="b" * 64,
    )
    stale_ctx, stale_elig = _bound_context(stale_estimate)
    stale_path = evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(
        market_context=stale_ctx,
        eligibility=stale_elig,
        governed_seam_record=seam,
        require_governed_seam=True,
        runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
        repo_root=REPO_ROOT,
    )
    assert stale_path.wiring_status == STATUS_WIRED
    assert stale_path.alpha_scope_entry_authority_allowed is False
    assert stale_path.enforcement_applied is True

    boundary_estimate = build_canonical_volatility_estimate_v1(
        value=0.004321,
        observation_count=61,
        as_of_event_time=datetime(2026, 6, 30, 11, 50, tzinfo=timezone.utc),
        fallback_used=False,
        source_digest="c" * 64,
    )
    boundary_ctx, boundary_elig = _bound_context(boundary_estimate)
    boundary_path = evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(
        market_context=boundary_ctx,
        eligibility=boundary_elig,
        governed_seam_record=seam,
        require_governed_seam=True,
        runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
        repo_root=REPO_ROOT,
    )
    assert boundary_path.wiring_status == STATUS_WIRED
    assert boundary_path.alpha_scope_entry_authority_allowed is True

    over_boundary = build_canonical_volatility_estimate_v1(
        value=0.004321,
        observation_count=61,
        as_of_event_time=datetime(2026, 6, 30, 11, 49, 59, tzinfo=timezone.utc),
        fallback_used=False,
        source_digest="d" * 64,
    )
    over_ctx, over_elig = _bound_context(over_boundary)
    over_path = evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(
        market_context=over_ctx,
        eligibility=over_elig,
        governed_seam_record=seam,
        require_governed_seam=True,
        runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
        repo_root=REPO_ROOT,
    )
    assert over_path.alpha_scope_entry_authority_allowed is False


def test_fail_closed_missing_and_mismatched_seam(tmp_path: Path) -> None:
    ctx, elig = _bound_context(_valid_estimate())
    missing = evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(
        market_context=ctx,
        eligibility=elig,
        governed_seam_record=None,
        require_governed_seam=True,
        runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
        repo_root=REPO_ROOT,
    )
    assert "GOVERNED_SEAM_RECORD_REQUIRED" in missing.reason_codes

    seam = _canonical_seam(tmp_path)
    bad_digest = copy.deepcopy(seam)
    bad_digest["seam_digest"] = "0" * 64
    mismatched = evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(
        market_context=ctx,
        eligibility=elig,
        governed_seam_record=bad_digest,
        require_governed_seam=True,
        runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
        repo_root=REPO_ROOT,
    )
    assert "SEAM_DIGEST_INVALID" in mismatched.reason_codes

    no_runtime = _re_digest_seam({**copy.deepcopy(seam), "runtime_applied": False})
    not_applied = evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(
        market_context=ctx,
        eligibility=elig,
        governed_seam_record=no_runtime,
        require_governed_seam=True,
        runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
        repo_root=REPO_ROOT,
    )
    assert "CONFIGURATION_RUNTIME_APPLIED_REQUIRED" in not_applied.reason_codes


def test_forbidden_historical_numeric_defaults_rejected(tmp_path: Path) -> None:
    seam = _canonical_seam(tmp_path)
    ctx, elig = _bound_context(_valid_estimate())
    for forbidden in FORBIDDEN_UNGOVERNED_NUMERIC_DEFAULTS:
        bad = _re_digest_seam(
            {
                **copy.deepcopy(seam),
                "numeric_max_age_seconds": forbidden,
                "authorized_candidate_max_age_seconds": forbidden,
            }
        )
        path = evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(
            market_context=ctx,
            eligibility=elig,
            governed_seam_record=bad,
            require_governed_seam=True,
            runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
            repo_root=REPO_ROOT,
        )
        assert "FORBIDDEN_UNGOVERNED_NUMERIC_DEFAULT" in path.reason_codes


def test_stale_reason_code_from_bounded_enforcement(tmp_path: Path) -> None:
    seam = _canonical_seam(tmp_path)
    stale_estimate = build_canonical_volatility_estimate_v1(
        value=0.004321,
        observation_count=61,
        as_of_event_time=datetime(2026, 6, 30, 10, 0, tzinfo=timezone.utc),
        fallback_used=False,
        source_digest="b" * 64,
    )
    stale_ctx, stale_elig = _bound_context(stale_estimate)
    stale_path = evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(
        market_context=stale_ctx,
        eligibility=stale_elig,
        governed_seam_record=seam,
        require_governed_seam=True,
        runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
        repo_root=REPO_ROOT,
    )
    assert stale_path.presence_gate is not None
    assert stale_path.presence_gate.max_age_policy_evidence is not None
    assert (
        VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_STALE.value
        in (stale_path.presence_gate.max_age_policy_evidence.reason_code,)
        or stale_path.alpha_scope_entry_authority_allowed is False
    )
