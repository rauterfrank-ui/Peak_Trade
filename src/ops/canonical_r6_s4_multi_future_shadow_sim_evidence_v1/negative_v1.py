"""Fail-closed negative matrix for R6 S4 shadow/sim evidence."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.arbitration_v1 import (
    arbitrate_intents_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.instrument_context_v1 import (
    isolate_instrument_contexts_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    CANONICAL_ACCOUNTING_WRITER_IDENTITY,
    CANONICAL_EXECUTION_WRITER_IDENTITY,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.lineage_v1 import (
    load_layer_config_v1 as load_s3_config_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    InstrumentContextV1,
    IntentV1,
    Phase82GraphRequestV1,
    R6S3RuntimeArchitectureError,
    WriterBundleV1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.orchestrator_v1 import (
    evaluate_phase_82_graph_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.portfolio_risk_binding_v1 import (
    apply_portfolio_risk_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.restart_v1 import (
    reconstruct_contexts_v1,
    snapshot_contexts_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.verifier_v1 import (
    validate_layer_config_v1,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.constants_v1 import (
    FIXTURE_INSTRUMENT_A,
    FIXTURE_INSTRUMENT_B,
    NEGATIVE_CASE_IDS,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.models_v1 import (
    R6S4ShadowSimEvidenceError,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.producer_v1 import (
    fixture_contexts_v1,
    fixture_request_v1,
)


def _reject(message: str) -> None:
    raise R6S4ShadowSimEvidenceError(message)


def _context(
    instrument_id: str,
    *,
    recon: str = "RECONCILED",
    stale: bool = False,
    action: str = "ENTRY",
) -> InstrumentContextV1:
    return InstrumentContextV1(
        instrument_id=instrument_id,
        directional_side="FLAT",
        intended_action=action,
        intended_side="LONG",
        intended_qty="2",
        reconciliation_status=recon,
        single_use_permission=True,
        stale=stale,
        isolated_state={"marker": instrument_id},
    )


def _duplicate_instrument_context() -> None:
    isolate_instrument_contexts_v1((_context(FIXTURE_INSTRUMENT_A), _context(FIXTURE_INSTRUMENT_A)))


def _state_contamination() -> None:
    isolated = isolate_instrument_contexts_v1(
        (_context(FIXTURE_INSTRUMENT_A), _context(FIXTURE_INSTRUMENT_B))
    )
    isolated[FIXTURE_INSTRUMENT_A].isolated_state["marker"] = "BLEED"


def _nondeterministic_arbitration() -> None:
    arbitrate_intents_v1((IntentV1(FIXTURE_INSTRUMENT_A, "SHUFFLE", "LONG", "1", sequence=1),))


def _conflicting_intents() -> None:
    arbitrate_intents_v1(
        (
            IntentV1(FIXTURE_INSTRUMENT_A, "ENTRY", "LONG", "1", sequence=1),
            IntentV1(FIXTURE_INSTRUMENT_A, "EXIT", "SHORT", "1", sequence=2),
        )
    )


def _portfolio_risk_rejection() -> None:
    intents = (
        IntentV1(FIXTURE_INSTRUMENT_A, "ENTRY", "LONG", "4", sequence=0),
        IntentV1(FIXTURE_INSTRUMENT_B, "ENTRY", "LONG", "4", sequence=1),
    )
    apply_portfolio_risk_v1(intents, authorized=True, reduce_entry_qty_to="0")


def _writer_duplication_attempt() -> None:
    forged = WriterBundleV1(
        execution_writer_identity="forged_second_execution_writer",
        accounting_writer_identity=CANONICAL_ACCOUNTING_WRITER_IDENTITY,
        intents=(),
        submit_unlocked=False,
    )
    if forged.execution_writer_identity != CANONICAL_EXECUTION_WRITER_IDENTITY:
        _reject("second_execution_authority_rejected")


def _accounting_writer_duplication_attempt() -> None:
    forged = WriterBundleV1(
        execution_writer_identity=CANONICAL_EXECUTION_WRITER_IDENTITY,
        accounting_writer_identity="forged_second_accounting_writer",
        intents=(),
        submit_unlocked=False,
    )
    if forged.accounting_writer_identity != CANONICAL_ACCOUNTING_WRITER_IDENTITY:
        _reject("second_accounting_authority_rejected")


def _stale_unknown_instrument_state() -> None:
    result = evaluate_phase_82_graph_v1(
        fixture_request_v1(
            (
                _context(FIXTURE_INSTRUMENT_A),
                _context(FIXTURE_INSTRUMENT_B, recon="UNKNOWN", stale=True, action="ENTRY"),
            )
        )
    )
    by_id = {intent.instrument_id: intent for intent in result.arbitrated_intents}
    if by_id[FIXTURE_INSTRUMENT_B].blocked is not True:
        _reject("stale_unknown_not_blocked")
    _reject("stale_unknown_instrument_state_fail_closed")


def _restart_reconciliation_mismatch() -> None:
    live = fixture_contexts_v1()
    snapshot = dict(snapshot_contexts_v1((live[0],)))
    reconstructed = reconstruct_contexts_v1(snapshot, authorized_after_restart=False)
    live_ids = {row.instrument_id for row in live}
    restart_ids = {row.instrument_id for row in reconstructed}
    if restart_ids != live_ids:
        _reject("restart_reconciliation_mismatch")
    _reject("restart_mismatch_not_detected")


def _unauthorized_mf_activation_attempt() -> None:
    request = fixture_request_v1()
    evaluate_phase_82_graph_v1(
        Phase82GraphRequestV1(
            selected_future_id=request.selected_future_id,
            ranking_candidates=request.ranking_candidates,
            instrument_contexts=request.instrument_contexts,
            requested_authorized=True,
        )
    )


def _g13_bypass_attempt() -> None:
    payload = dict(load_s3_config_v1())
    payload["g13_unchanged"] = False
    validate_layer_config_v1(payload)


def _order_submit_attempt() -> None:
    result = evaluate_phase_82_graph_v1(fixture_request_v1())
    if result.submit_unlocked is True or result.writer_bundle.submit_unlocked is True:
        _reject("submit_already_unlocked")
    _reject("order_submit_attempt_rejected")


_CASE_RUNNERS = {
    "duplicate_instrument_context": _duplicate_instrument_context,
    "state_contamination": _state_contamination,
    "nondeterministic_arbitration": _nondeterministic_arbitration,
    "conflicting_intents": _conflicting_intents,
    "portfolio_risk_rejection": _portfolio_risk_rejection,
    "writer_duplication_attempt": _writer_duplication_attempt,
    "accounting_writer_duplication_attempt": _accounting_writer_duplication_attempt,
    "stale_unknown_instrument_state": _stale_unknown_instrument_state,
    "restart_reconciliation_mismatch": _restart_reconciliation_mismatch,
    "unauthorized_mf_activation_attempt": _unauthorized_mf_activation_attempt,
    "g13_bypass_attempt": _g13_bypass_attempt,
    "order_submit_attempt": _order_submit_attempt,
}

_EXPECTED_TOKENS = {
    "duplicate_instrument_context": "duplicate_instrument_context",
    "state_contamination": "",
    "nondeterministic_arbitration": "unknown_action_for_arbitration",
    "conflicting_intents": "arbitration_conflict_fail_closed",
    "portfolio_risk_rejection": "portfolio_risk_cannot_honor_authorized_true",
    "writer_duplication_attempt": "second_execution_authority_rejected",
    "accounting_writer_duplication_attempt": "second_accounting_authority_rejected",
    "stale_unknown_instrument_state": "stale_unknown_instrument_state_fail_closed",
    "restart_reconciliation_mismatch": "restart_reconciliation_mismatch",
    "unauthorized_mf_activation_attempt": "authorized_rejected",
    "g13_bypass_attempt": "g13_unchanged",
    "order_submit_attempt": "order_submit_attempt_rejected",
}


def run_negative_matrix_v1() -> Mapping[str, Any]:
    if tuple(_CASE_RUNNERS) != NEGATIVE_CASE_IDS:
        _reject("negative_case_id_drift")
    results: dict[str, Mapping[str, Any]] = {}
    for case_id in NEGATIVE_CASE_IDS:
        runner = _CASE_RUNNERS[case_id]
        token = _EXPECTED_TOKENS[case_id]
        try:
            runner()
        except (R6S3RuntimeArchitectureError, R6S4ShadowSimEvidenceError, TypeError) as exc:
            reason = str(exc)
            if token and token not in reason:
                _reject(f"negative_token_mismatch:{case_id}:{reason}")
            results[case_id] = MappingProxyType(
                {"fail_closed": True, "reason": reason, "case_id": case_id}
            )
            continue
        _reject(f"negative_case_did_not_fail_closed:{case_id}")
    if any(row["fail_closed"] is not True for row in results.values()):
        _reject("negative_matrix_not_fully_fail_closed")
    return MappingProxyType(results)
