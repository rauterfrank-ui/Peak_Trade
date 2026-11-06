"""P5.1 authority seam: durable L1–L10 episode step + immutable seal (infrastructure only)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Tuple

from src.ops.p4_l6_explicit_d_t_proposal_v1.models_v1 import (
    ExplicitDtProposalV1,
    P4ExplicitDtProposalIdentityContextV1,
)
from src.ops.p4_l6_explicit_d_t_proposal_v1.adapter_v1 import (
    validate_and_transport_explicit_dt_proposal_v1,
)
from src.ops.p5_productive_layered_core_authority_seam_v1.constants_v1 import (
    P4_PRODUCTIVE_BINDING,
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
    PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import ObservationCandidateV1
from trading.master_v2.layered_core_authority_seal_v1 import (
    LayeredCoreAuthoritySealV1,
    build_layered_core_authority_seal_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    SelectedFutureInputV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (
    NakedLayeredCoreDurableStateError,
    NakedLayeredCoreEpisodeV1,
    atomic_persist_episode_v1,
    execute_naked_layered_core_mechanical_step_v1,
    initialize_naked_layered_core_episode_v1,
    restore_episode_from_store_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l6_dynamic_scope_generator_v1 import (
    ExplicitPassthroughDynamicScopeGeneratorV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.orchestrator_v1 import (
    MechanicalStepSpecV1,
)
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1


class P5LayeredCoreAuthoritySeamError(ValueError):
    """Fail-closed P5 seam violation."""


@dataclass(frozen=True)
class P5LayeredCoreAuthoritySeamResultV1:
    ok: bool
    failure_codes: Tuple[str, ...]
    episode: Optional[NakedLayeredCoreEpisodeV1]
    seal: Optional[LayeredCoreAuthoritySealV1]
    store_manifest_digest: Optional[str]


def _resolve_mechanical_step_v1(
    *,
    mark_price_m_t: float,
    mechanical_step: Optional[MechanicalStepSpecV1],
    explicit_dt_proposal: Optional[ExplicitDtProposalV1],
    identity_context: Optional[P4ExplicitDtProposalIdentityContextV1],
) -> Tuple[Optional[MechanicalStepSpecV1], Tuple[str, ...]]:
    if mechanical_step is not None:
        if mechanical_step.proposed_d_t is None:
            return None, ("mechanical_step_missing_proposed_d_t",)
        return mechanical_step, ()
    if explicit_dt_proposal is None:
        return None, ("explicit_dt_proposal_required",)
    if identity_context is None:
        return None, ("p4_identity_context_required",)
    _validation, transport, step = validate_and_transport_explicit_dt_proposal_v1(
        explicit_dt_proposal,
        identity_context=identity_context,
        mark_price_m_t=float(mark_price_m_t),
    )
    if step is None or not transport.ok:
        codes = tuple(
            c.value if hasattr(c, "value") else str(c) for c in transport.failure_codes
        ) or ("p4_transport_failed",)
        return None, codes
    return step, ()


def run_p5_layered_core_authority_seam_v1(
    *,
    store_root: Path,
    selected: SelectedFutureInputV1,
    mark_price_m_t: float,
    mechanical_step: Optional[MechanicalStepSpecV1] = None,
    explicit_dt_proposal: Optional[ExplicitDtProposalV1] = None,
    p4_identity_context: Optional[P4ExplicitDtProposalIdentityContextV1] = None,
    initialization_observations: Optional[Sequence[ObservationCandidateV1]] = None,
    restore_existing: bool = True,
) -> P5LayeredCoreAuthoritySeamResultV1:
    """Run one mechanical L1–L10 step and emit seal. Does not activate productive cutover."""
    if P5_AUTHORITY_CUTOVER_AUTHORIZED or PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED:
        return P5LayeredCoreAuthoritySeamResultV1(
            ok=False,
            failure_codes=("productive_cutover_not_authorized",),
            episode=None,
            seal=None,
            store_manifest_digest=None,
        )
    if P4_PRODUCTIVE_BINDING:
        return P5LayeredCoreAuthoritySeamResultV1(
            ok=False,
            failure_codes=("p4_productive_binding_forbidden",),
            episode=None,
            seal=None,
            store_manifest_digest=None,
        )

    step, step_failures = _resolve_mechanical_step_v1(
        mark_price_m_t=mark_price_m_t,
        mechanical_step=mechanical_step,
        explicit_dt_proposal=explicit_dt_proposal,
        identity_context=p4_identity_context,
    )
    if step is None:
        return P5LayeredCoreAuthoritySeamResultV1(
            ok=False,
            failure_codes=step_failures,
            episode=None,
            seal=None,
            store_manifest_digest=None,
        )

    scope_generator = ExplicitPassthroughDynamicScopeGeneratorV1()
    try:
        if restore_existing:
            episode = restore_episode_from_store_v1(
                store_root,
                expected_instrument_id=selected.instrument_id,
            )
        else:
            if not initialization_observations:
                raise P5LayeredCoreAuthoritySeamError("initialization_observations_required")
            episode, init_failures = initialize_naked_layered_core_episode_v1(
                selected=selected,
                initialization_observations=initialization_observations,
                first_mechanical_step=None,
                scope_generator=scope_generator,
            )
            if init_failures:
                raise P5LayeredCoreAuthoritySeamError(
                    "initialization_fail_closed:" + ",".join(init_failures)
                )
        step_result = execute_naked_layered_core_mechanical_step_v1(
            episode=episode,
            step=step,
            scope_generator=scope_generator,
        )
    except (NakedLayeredCoreDurableStateError, P5LayeredCoreAuthoritySeamError) as exc:
        return P5LayeredCoreAuthoritySeamResultV1(
            ok=False,
            failure_codes=(f"seam_fail_closed:{type(exc).__name__}",),
            episode=None,
            seal=None,
            store_manifest_digest=None,
        )

    if step_result.fail_closed:
        return P5LayeredCoreAuthoritySeamResultV1(
            ok=False,
            failure_codes=step_result.fail_reasons or ("mechanical_step_fail_closed",),
            episode=step_result.episode,
            seal=None,
            store_manifest_digest=None,
        )

    manifest_digest = atomic_persist_episode_v1(store_root, step_result.episode)
    regime_pre = (
        episode.regime
        if isinstance(episode.regime, NakedRegimeV1)
        else NakedRegimeV1(str(episode.regime))
    )
    seal = build_layered_core_authority_seal_v1(
        seal_id=uuid.uuid4().hex,
        instrument_id=step_result.episode.instrument_id,
        episode_snapshot_id=step_result.episode.snapshot_id,
        store_manifest_digest=manifest_digest,
        regime_pre=regime_pre,
        regime_post=step_result.regime_post,
        nullline_price=float(step_result.episode.nullline.nullline_price),
        d_t=float(step_result.d_t),
        r_t=float(step_result.r_t_post),
        cm_t=float(step_result.cm_t),
        switch_condition_met=bool(step_result.switch_condition_met),
        mechanical_step_count=int(step_result.episode.mechanical_step_count),
        cz4_delegation_active=True,
    )
    return P5LayeredCoreAuthoritySeamResultV1(
        ok=True,
        failure_codes=(),
        episode=step_result.episode,
        seal=seal,
        store_manifest_digest=manifest_digest,
    )


__all__ = [
    "P5LayeredCoreAuthoritySeamError",
    "P5LayeredCoreAuthoritySeamResultV1",
    "run_p5_layered_core_authority_seam_v1",
]
