"""Phase-8.2 graph orchestrator. Offline, unauthorized, fail-closed."""

from __future__ import annotations

from types import MappingProxyType

from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.active_set_v1 import (
    resolve_active_set_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.arbitration_v1 import (
    arbitrate_intents_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.authority_gate_v1 import (
    resolve_authority_flags_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    ACCOUNT_MUTATION_EFFECT,
    CANARY_AUTHORIZED,
    CURRENT_EFFECTIVE_RUNTIME_MODE,
    ECONOMIC_EVIDENCE_CANNOT_CREATE_RUNTIME_AUTHORITY,
    G13_UNCHANGED,
    LIVE_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    NETWORK_EFFECT,
    ORDER_EFFECT,
    PHASE_8_2_GRAPH,
    PORTFOLIO_RISK_BEFORE_GLOBAL_SAFETY,
    RESEARCH_CANNOT_CREATE_RUNTIME_AUTHORITY,
    TESTNET_AUTHORIZED,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.global_safety_v1 import (
    apply_global_safety_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.instrument_context_v1 import (
    isolate_instrument_contexts_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    InstrumentContextV1,
    Phase82GraphRequestV1,
    Phase82GraphResultV1,
    R6S3RuntimeArchitectureError,
    RankingCandidateV1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.per_instrument_pipeline_v1 import (
    evaluate_per_instrument_pipeline_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.portfolio_risk_binding_v1 import (
    apply_portfolio_risk_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.reconciliation_v1 import (
    apply_per_instrument_reconciliation_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.restart_v1 import (
    reconstruct_contexts_v1,
    snapshot_contexts_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.single_writer_boundary_v1 import (
    bind_single_writer_v1,
)


def _reject(message: str) -> None:
    raise R6S3RuntimeArchitectureError(message)


def evaluate_phase_82_graph_v1(
    request: Phase82GraphRequestV1,
    *,
    portfolio_reduce_entry_qty_to: str | None = None,
) -> Phase82GraphResultV1:
    if PORTFOLIO_RISK_BEFORE_GLOBAL_SAFETY is not True:
        _reject("portfolio_risk_must_precede_global_safety")
    if request.economic_evidence_pass and ECONOMIC_EVIDENCE_CANNOT_CREATE_RUNTIME_AUTHORITY is True:
        pass
    if request.research_signal_pass and RESEARCH_CANNOT_CREATE_RUNTIME_AUTHORITY is True:
        pass
    flags = resolve_authority_flags_v1(request)
    authorized = bool(flags["authorized"])
    implemented = bool(flags["implemented"])
    active = resolve_active_set_v1(request, authorized=authorized)
    contexts = request.instrument_contexts
    if request.restart_snapshot is not None:
        contexts = reconstruct_contexts_v1(
            request.restart_snapshot,
            authorized_after_restart=authorized,
        )
    isolated = isolate_instrument_contexts_v1(contexts)
    isolated_tuple = tuple(isolated[key] for key in sorted(isolated))
    pipeline = evaluate_per_instrument_pipeline_v1(isolated_tuple)
    reconciled = apply_per_instrument_reconciliation_v1(pipeline, isolated_tuple)
    portfolio = apply_portfolio_risk_v1(
        reconciled,
        authorized=authorized,
        reduce_entry_qty_to=portfolio_reduce_entry_qty_to,
    )
    safety = apply_global_safety_v1(
        portfolio,
        global_kill_switch=bool(request.global_kill_switch),
    )
    arbitrated = arbitrate_intents_v1(safety)
    writer = bind_single_writer_v1(arbitrated, authorized=authorized)
    if writer.submit_unlocked is True:
        _reject("submit_unlocked_must_remain_false")
    if len(active["effective_active_ids"]) > MAX_POSITIONS_EFFECTIVE:
        _reject("effective_active_count_exceeds_max")
    claims = MappingProxyType(
        {
            "MULTI_FUTURE_RUNTIME_IMPLEMENTED": implemented,
            "MULTI_FUTURE_RUNTIME_AUTHORIZED": False,
            "G13_UNCHANGED": G13_UNCHANGED,
            "CURRENT_EFFECTIVE_RUNTIME_MODE": CURRENT_EFFECTIVE_RUNTIME_MODE,
            "MAX_POSITIONS_EFFECTIVE": MAX_POSITIONS_EFFECTIVE,
            "SUBMIT_UNLOCKED": False,
            "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
            "TESTNET_AUTHORIZED": TESTNET_AUTHORIZED,
            "CANARY_AUTHORIZED": CANARY_AUTHORIZED,
            "NETWORK_EFFECT": NETWORK_EFFECT,
            "ORDER_EFFECT": ORDER_EFFECT,
            "ACCOUNT_MUTATION_EFFECT": ACCOUNT_MUTATION_EFFECT,
            "ECONOMIC_EVIDENCE_CREATED_RUNTIME_AUTHORITY": False,
            "RESEARCH_CREATED_RUNTIME_AUTHORITY": False,
            "RANKING_CREATED_RUNTIME_AUTHORITY": False,
            "PORTFOLIO_CREATED_ORDER_AUTHORITY": False,
            "STAGE_ORDER": list(PHASE_8_2_GRAPH),
            "RESTART_SNAPSHOT": dict(snapshot_contexts_v1(isolated_tuple)),
        }
    )
    return Phase82GraphResultV1(
        implemented=implemented,
        authorized=False,
        effective_runtime_mode=CURRENT_EFFECTIVE_RUNTIME_MODE,
        max_positions_effective=MAX_POSITIONS_EFFECTIVE,
        effective_active_ids=tuple(active["effective_active_ids"]),
        candidate_ids=tuple(active["candidate_ids"]),
        isolated_contexts=MappingProxyType(
            {key: dict(value.to_mapping()) for key, value in isolated.items()}
        ),
        pipeline_intents=pipeline,
        portfolio_intents=portfolio,
        safety_intents=safety,
        arbitrated_intents=arbitrated,
        writer_bundle=writer,
        stage_order=PHASE_8_2_GRAPH,
        submit_unlocked=False,
        live_authorized=False,
        testnet_authorized=False,
        canary_authorized=False,
        order_effect=ORDER_EFFECT,
        claims=claims,
    )


def default_single_future_request_v1(
    selected_future_id: str,
    *,
    extra_candidates: tuple[str, ...] = (),
) -> Phase82GraphRequestV1:
    candidates = [(selected_future_id, 1)]
    candidates.extend(
        (instrument_id, index + 2) for index, instrument_id in enumerate(extra_candidates)
    )

    return Phase82GraphRequestV1(
        selected_future_id=selected_future_id,
        ranking_candidates=tuple(
            RankingCandidateV1(instrument_id=item[0], rank=item[1], eligible=True)
            for item in candidates
        ),
        instrument_contexts=(
            InstrumentContextV1(
                instrument_id=selected_future_id,
                directional_side="FLAT",
                intended_action="HOLD",
                intended_side="FLAT",
                intended_qty="0",
                reconciliation_status="RECONCILED",
            ),
        ),
    )
