"""Durable L1–L10-native episode state (P3): atomic persist + fail-closed restore.

Does not bind productive hosts, integrated replay, SideState, or legacy scope semantics.
RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Tuple

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceStateV1,
    ObservationAcceptanceResultV1,
    ObservationCandidateV1,
    ObservationClassification,
)
from trading.market_state.elementary_direction_v1 import ElementaryDirectionV1
from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    BullBearSwitchInputV1,
    CounterMoveInputV1,
    DynamicScopeGeneratorInputV1,
    DynamicScopeGeneratorV1,
    InitialDirectionInputV1,
    InitialStateInitializationInputV1,
    MarketObservationInputV1,
    MarketObservationStateV1,
    NullLineInputV1,
    NullLineStateV1,
    RunningReferenceStateV1,
    RunningReferenceStepInputV1,
    ScopeStateMaterializationInputV1,
    ScopeStateV1,
    SelectedFutureInputV1,
    SelectedFutureStateV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l1_selected_future_v1 import (
    apply_l1_selected_future_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l2_market_observation_v1 import (
    apply_l2_market_observation_v1,
    initial_market_observation_state_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l3_initial_direction_v1 import (
    apply_l3_initial_direction_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l4_initial_state_v1 import (
    apply_l4_initial_state_initialization_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l5_nullline_v1 import (
    apply_l5_nullline_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l6_dynamic_scope_generator_v1 import (
    apply_l6_dynamic_scope_generator_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l7_scope_state_v1 import (
    apply_l7_scope_state_materialization_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l8_running_reference_v1 import (
    apply_l8_running_reference_step_v1,
    initial_running_reference_state_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l9_counter_move_v1 import (
    apply_l9_counter_move_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l10_bull_bear_switch_v1 import (
    apply_l10_bull_bear_switch_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.layer_catalog_v1 import (
    EXPLICIT_LAYERED_CORE_VERSION,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.orchestrator_v1 import (
    MechanicalStepSpecV1,
)
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1

DURABLE_STATE_OWNER = "trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1"
SNAPSHOT_SCHEMA_NAME = "naked_mv2_dp_explicit_layered_core_durable_state.v1"
SNAPSHOT_SCHEMA_VERSION = "v1"
SNAPSHOT_FILENAME = "naked_layered_core_episode_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"

PRODUCTIVE_BINDING_AUTHORIZED = False
AUTHORITY_CUTOVER_OCCURRED = False
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
EXTERNAL_EFFECT_AUTHORIZED = False
LEGACY_SEMANTIC_FALLBACK_AUTHORIZED = False

_FORBIDDEN_LEGACY_TOP_LEVEL_KEYS = frozenset(
    {
        "side_state",
        "runtime_scope_state",
        "existing_scope",
        "canonical_scope",
        "scope_confirmation",
        "trailing_anchor",
        "reference_price",
        "anchor_price",
        "transition_state",
        "composition_result",
        "decision_outcome",
    }
)

_REQUIRED_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_name",
        "schema_version",
        "core_version",
        "snapshot_id",
        "instrument_id",
        "instrument_key",
        "initialization_complete",
        "regime",
        "nullline",
        "running_reference",
        "observation_state",
        "mechanical_step_count",
    }
)


class NakedLayeredCoreDurableStateError(ValueError):
    """Fail-closed durable snapshot or restore violation."""


@dataclass(frozen=True)
class NakedLayeredCoreEpisodeV1:
    instrument_id: str
    instrument_key: InstrumentObservationKeyV1
    initialization_complete: bool
    regime: NakedRegimeV1
    nullline: NullLineStateV1
    scope: Optional[ScopeStateV1]
    running_reference: RunningReferenceStateV1
    observation_state: MarketObservationStateV1
    last_acceptance_provenance: Optional[Mapping[str, Any]]
    mechanical_step_count: int
    snapshot_id: str

    def __post_init__(self) -> None:
        if not self.initialization_complete:
            raise NakedLayeredCoreDurableStateError("EPISODE_NOT_INITIALIZED")
        if self.nullline.instrument_id != self.instrument_id:
            raise NakedLayeredCoreDurableStateError("NULLLINE_INSTRUMENT_MISMATCH")
        if self.running_reference.instrument_id != self.instrument_id:
            raise NakedLayeredCoreDurableStateError("RUNNING_REFERENCE_INSTRUMENT_MISMATCH")


@dataclass(frozen=True)
class MechanicalStepExecutionResultV1:
    episode: NakedLayeredCoreEpisodeV1
    fail_closed: bool
    fail_reasons: Tuple[str, ...]
    switch_condition_met: bool
    cm_t: float
    d_t: float
    regime_post: NakedRegimeV1
    r_t_post: float


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _snapshot_digest(payload: Mapping[str, Any]) -> str:
    material = {k: v for k, v in payload.items() if k != "snapshot_id"}
    return hashlib.sha256(_canonical_json(material).encode("utf-8")).hexdigest()


def _parse_regime(raw: object) -> NakedRegimeV1:
    if isinstance(raw, NakedRegimeV1):
        return raw
    text = str(raw or "").strip().lower()
    if text == NakedRegimeV1.BULL.value:
        return NakedRegimeV1.BULL
    if text == NakedRegimeV1.BEAR.value:
        return NakedRegimeV1.BEAR
    raise NakedLayeredCoreDurableStateError(f"REGIME_INVALID:{text}")


def _null_line_from_dict(payload: Mapping[str, Any]) -> NullLineStateV1:
    return NullLineStateV1(
        instrument_id=str(payload["instrument_id"]),
        nullline_price=float(payload["nullline_price"]),
        provenance_mark_epoch=int(payload["provenance_mark_epoch"]),
    )


def _null_line_to_dict(nullline: NullLineStateV1) -> dict[str, Any]:
    return {
        "instrument_id": nullline.instrument_id,
        "nullline_price": float(nullline.nullline_price),
        "provenance_mark_epoch": int(nullline.provenance_mark_epoch),
    }


def _scope_from_dict(payload: Mapping[str, Any]) -> ScopeStateV1:
    d_t = float(payload["d_t"])
    if not (d_t > 0.0 and d_t == d_t):
        raise NakedLayeredCoreDurableStateError("D_T_INVALID")
    return ScopeStateV1(
        instrument_id=str(payload["instrument_id"]),
        d_t=d_t,
        nullline_price=float(payload["nullline_price"]),
        nullline_provenance_epoch=int(payload["nullline_provenance_epoch"]),
        generator_id=str(payload["generator_id"]),
        valid=bool(payload.get("valid", True)),
    )


def _scope_to_dict(scope: ScopeStateV1) -> dict[str, Any]:
    return {
        "instrument_id": scope.instrument_id,
        "d_t": float(scope.d_t),
        "nullline_price": float(scope.nullline_price),
        "nullline_provenance_epoch": int(scope.nullline_provenance_epoch),
        "generator_id": scope.generator_id,
        "valid": bool(scope.valid),
    }


def _running_from_dict(payload: Mapping[str, Any]) -> RunningReferenceStateV1:
    r_t = float(payload["reference_price_r_t"])
    if not (r_t > 0.0 and r_t == r_t):
        raise NakedLayeredCoreDurableStateError("R_T_INVALID")
    return RunningReferenceStateV1(
        instrument_id=str(payload["instrument_id"]),
        reference_price_r_t=r_t,
    )


def _observation_state_from_dict(payload: Mapping[str, Any]) -> MarketObservationStateV1:
    selected_raw = payload.get("selected")
    acceptance_raw = payload.get("acceptance_state")
    if not isinstance(selected_raw, Mapping) or not isinstance(acceptance_raw, Mapping):
        raise NakedLayeredCoreDurableStateError("OBSERVATION_STATE_INCOMPLETE")
    key = InstrumentObservationKeyV1.from_dict(selected_raw["instrument_key"])
    selected = SelectedFutureStateV1(
        instrument_id=str(selected_raw["instrument_id"]),
        instrument_key=key,
    )
    acceptance = ObservationAcceptanceStateV1.from_dict(acceptance_raw)
    return MarketObservationStateV1(selected=selected, acceptance_state=acceptance)


def _observation_state_to_dict(state: MarketObservationStateV1) -> dict[str, Any]:
    return {
        "selected": {
            "instrument_id": state.selected.instrument_id,
            "instrument_key": state.selected.instrument_key.to_dict(),
        },
        "acceptance_state": state.acceptance_state.to_dict(),
    }


def assert_no_legacy_semantic_fields_v1(payload: Mapping[str, Any]) -> None:
    overlap = _FORBIDDEN_LEGACY_TOP_LEVEL_KEYS.intersection(payload.keys())
    if overlap:
        raise NakedLayeredCoreDurableStateError(
            "LEGACY_SEMANTIC_FIELD_FORBIDDEN:" + ",".join(sorted(overlap))
        )


def episode_to_snapshot_v1(episode: NakedLayeredCoreEpisodeV1) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_name": SNAPSHOT_SCHEMA_NAME,
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "core_version": EXPLICIT_LAYERED_CORE_VERSION,
        "instrument_id": episode.instrument_id,
        "instrument_key": episode.instrument_key.to_dict(),
        "initialization_complete": bool(episode.initialization_complete),
        "regime": episode.regime.value,
        "nullline": _null_line_to_dict(episode.nullline),
        "running_reference": {
            "instrument_id": episode.running_reference.instrument_id,
            "reference_price_r_t": float(episode.running_reference.reference_price_r_t),
        },
        "observation_state": _observation_state_to_dict(episode.observation_state),
        "last_acceptance_provenance": (
            None
            if episode.last_acceptance_provenance is None
            else dict(episode.last_acceptance_provenance)
        ),
        "mechanical_step_count": int(episode.mechanical_step_count),
        "scope": None if episode.scope is None else _scope_to_dict(episode.scope),
        "productive_binding_authorized": False,
        "authority_cutover_occurred": False,
    }
    body["snapshot_id"] = _snapshot_digest(body)
    if body["snapshot_id"] != episode.snapshot_id:
        raise NakedLayeredCoreDurableStateError("EPISODE_SNAPSHOT_ID_DRIFT")
    return body


def episode_from_snapshot_v1(
    payload: Mapping[str, Any],
    *,
    expected_instrument_id: Optional[str] = None,
    expected_core_version: str = EXPLICIT_LAYERED_CORE_VERSION,
) -> NakedLayeredCoreEpisodeV1:
    if not isinstance(payload, Mapping):
        raise NakedLayeredCoreDurableStateError("SNAPSHOT_NOT_OBJECT")
    assert_no_legacy_semantic_fields_v1(payload)
    missing = _REQUIRED_TOP_LEVEL_KEYS - set(payload.keys())
    if missing:
        raise NakedLayeredCoreDurableStateError(
            "SNAPSHOT_MISSING_FIELDS:" + ",".join(sorted(missing))
        )
    if str(payload.get("schema_name")) != SNAPSHOT_SCHEMA_NAME:
        raise NakedLayeredCoreDurableStateError("SCHEMA_NAME_MISMATCH")
    if str(payload.get("schema_version")) != SNAPSHOT_SCHEMA_VERSION:
        raise NakedLayeredCoreDurableStateError("SCHEMA_VERSION_UNKNOWN")
    if str(payload.get("core_version")) != expected_core_version:
        raise NakedLayeredCoreDurableStateError("CORE_VERSION_MISMATCH")
    instrument_id = str(payload.get("instrument_id") or "").strip()
    if not instrument_id:
        raise NakedLayeredCoreDurableStateError("INSTRUMENT_ID_MISSING")
    if expected_instrument_id is not None and instrument_id != expected_instrument_id:
        raise NakedLayeredCoreDurableStateError("SELECTED_FUTURE_MISMATCH")
    key_raw = payload.get("instrument_key")
    if not isinstance(key_raw, Mapping):
        raise NakedLayeredCoreDurableStateError("INSTRUMENT_KEY_MISSING")
    instrument_key = InstrumentObservationKeyV1.from_dict(key_raw)
    if instrument_key.canonical_instrument_id != instrument_id:
        raise NakedLayeredCoreDurableStateError("L1_BINDING_PROVENANCE_MISMATCH")
    if payload.get("initialization_complete") is not True:
        raise NakedLayeredCoreDurableStateError("INITIALIZATION_NOT_EXPLICIT")
    nullline = _null_line_from_dict(payload["nullline"])  # type: ignore[arg-type]
    if nullline.instrument_id != instrument_id:
        raise NakedLayeredCoreDurableStateError("NULLLINE_INSTRUMENT_MISMATCH")
    scope_raw = payload.get("scope")
    scope = None if scope_raw is None else _scope_from_dict(scope_raw)  # type: ignore[arg-type]
    if scope is not None and scope.nullline_price != nullline.nullline_price:
        raise NakedLayeredCoreDurableStateError("NULLLINE_SCOPE_DRIFT")
    if scope is not None and scope.nullline_provenance_epoch != nullline.provenance_mark_epoch:
        raise NakedLayeredCoreDurableStateError("NULLLINE_PROVENANCE_DRIFT")
    running = _running_from_dict(payload["running_reference"])  # type: ignore[arg-type]
    observation_state = _observation_state_from_dict(payload["observation_state"])  # type: ignore[arg-type]
    if observation_state.selected.instrument_id != instrument_id:
        raise NakedLayeredCoreDurableStateError("L2_SELECTED_MISMATCH")
    provenance = payload.get("last_acceptance_provenance")
    if provenance is not None and not isinstance(provenance, Mapping):
        raise NakedLayeredCoreDurableStateError("LAST_ACCEPTANCE_PROVENANCE_INVALID")
    digest = _snapshot_digest(dict(payload))
    snapshot_id = str(payload.get("snapshot_id") or "")
    if snapshot_id != digest:
        raise NakedLayeredCoreDurableStateError("SNAPSHOT_DIGEST_MISMATCH")
    return NakedLayeredCoreEpisodeV1(
        instrument_id=instrument_id,
        instrument_key=instrument_key,
        initialization_complete=True,
        regime=_parse_regime(payload.get("regime")),
        nullline=nullline,
        scope=scope,
        running_reference=running,
        observation_state=observation_state,
        last_acceptance_provenance=None if provenance is None else dict(provenance),
        mechanical_step_count=int(payload.get("mechanical_step_count") or 0),
        snapshot_id=snapshot_id,
    )


def _build_episode(
    *,
    selected: SelectedFutureStateV1,
    regime: NakedRegimeV1,
    nullline: NullLineStateV1,
    scope: Optional[ScopeStateV1],
    running: RunningReferenceStateV1,
    observation_state: MarketObservationStateV1,
    last_acceptance: Optional[ObservationAcceptanceResultV1],
    mechanical_step_count: int,
) -> NakedLayeredCoreEpisodeV1:
    provisional: dict[str, Any] = {
        "schema_name": SNAPSHOT_SCHEMA_NAME,
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "core_version": EXPLICIT_LAYERED_CORE_VERSION,
        "instrument_id": selected.instrument_id,
        "instrument_key": selected.instrument_key.to_dict(),
        "initialization_complete": True,
        "regime": regime.value,
        "nullline": _null_line_to_dict(nullline),
        "running_reference": {
            "instrument_id": running.instrument_id,
            "reference_price_r_t": float(running.reference_price_r_t),
        },
        "observation_state": _observation_state_to_dict(observation_state),
        "last_acceptance_provenance": (
            None if last_acceptance is None else last_acceptance.to_dict()
        ),
        "mechanical_step_count": int(mechanical_step_count),
        "scope": None if scope is None else _scope_to_dict(scope),
        "productive_binding_authorized": False,
        "authority_cutover_occurred": False,
    }
    snapshot_id = _snapshot_digest(provisional)
    return NakedLayeredCoreEpisodeV1(
        instrument_id=selected.instrument_id,
        instrument_key=selected.instrument_key,
        initialization_complete=True,
        regime=regime,
        nullline=nullline,
        scope=scope,
        running_reference=running,
        observation_state=observation_state,
        last_acceptance_provenance=(None if last_acceptance is None else last_acceptance.to_dict()),
        mechanical_step_count=mechanical_step_count,
        snapshot_id=snapshot_id,
    )


def initialize_naked_layered_core_episode_v1(
    *,
    selected: SelectedFutureInputV1,
    initialization_observations: Sequence[ObservationCandidateV1],
    first_mechanical_step: Optional[MechanicalStepSpecV1] = None,
    scope_generator: DynamicScopeGeneratorV1,
) -> Tuple[NakedLayeredCoreEpisodeV1, Tuple[str, ...]]:
    """Run L1–L5 initialization (explicit). Optional first L6–L10 mechanical step."""
    l1 = apply_l1_selected_future_v1(selected)
    obs_state = initial_market_observation_state_v1(l1.state)
    nullline: Optional[NullLineStateV1] = None
    regime_state = None
    last_acceptance: Optional[ObservationAcceptanceResultV1] = None

    for candidate in initialization_observations:
        l2 = apply_l2_market_observation_v1(
            MarketObservationInputV1(observation_state=obs_state, candidate=candidate)
        )
        obs_state = l2.observation_state
        last_acceptance = l2.acceptance_result
        if l2.acceptance_result.classification is not ObservationClassification.DISTINCT:
            continue
        mark = float(candidate.mark_price)  # type: ignore[arg-type]
        l3 = apply_l3_initial_direction_v1(
            InitialDirectionInputV1(
                acceptance_result=l2.acceptance_result,
                bound_instrument_key=l1.state.instrument_key,
                current_mark=mark,
            )
        )
        if l3.direction_result.direction not in (
            ElementaryDirectionV1.BULL,
            ElementaryDirectionV1.BEAR,
        ):
            continue
        l4 = apply_l4_initial_state_initialization_v1(
            InitialStateInitializationInputV1(
                selected=l1.state,
                direction=l3,
                initialization_mark=mark,
            )
        )
        if l4.fail_closed:
            raise NakedLayeredCoreDurableStateError("L4_FAIL_CLOSED:" + ",".join(l4.fail_reasons))
        regime_state = l4.regime_state
        epoch = int(l2.acceptance_result.state_after.market_observation_epoch.value)
        l5 = apply_l5_nullline_v1(
            NullLineInputV1(
                regime_state=l4.regime_state,
                initialization_mark=mark,
                market_observation_epoch=epoch,
            )
        )
        nullline = l5.nullline
        break

    if nullline is None or regime_state is None:
        raise NakedLayeredCoreDurableStateError("INITIALIZATION_INCOMPLETE")

    regime = regime_state.regime
    running = initial_running_reference_state_v1(
        instrument_id=nullline.instrument_id,
        reference_price_r_t=nullline.nullline_price,
    )
    episode = _build_episode(
        selected=l1.state,
        regime=regime,
        nullline=nullline,
        scope=None,
        running=running,
        observation_state=obs_state,
        last_acceptance=last_acceptance,
        mechanical_step_count=0,
    )
    if first_mechanical_step is None:
        return episode, ()
    result = execute_naked_layered_core_mechanical_step_v1(
        episode=episode,
        step=first_mechanical_step,
        scope_generator=scope_generator,
    )
    if result.fail_closed:
        return result.episode, result.fail_reasons
    return result.episode, ()


def execute_naked_layered_core_mechanical_step_v1(
    *,
    episode: NakedLayeredCoreEpisodeV1,
    step: MechanicalStepSpecV1,
    scope_generator: DynamicScopeGeneratorV1,
) -> MechanicalStepExecutionResultV1:
    """One L6–L10 mechanical step from an initialized episode (no legacy inputs)."""
    if not episode.initialization_complete:
        raise NakedLayeredCoreDurableStateError("EPISODE_NOT_INITIALIZED")
    nullline = episode.nullline
    regime = episode.regime
    running = episode.running_reference

    l6 = apply_l6_dynamic_scope_generator_v1(
        scope_generator,
        DynamicScopeGeneratorInputV1(nullline=nullline, proposed_d_t=step.proposed_d_t),
    )
    if l6.fail_closed or l6.d_t is None:
        return MechanicalStepExecutionResultV1(
            episode=episode,
            fail_closed=True,
            fail_reasons=l6.fail_reasons or ("l6_fail_closed",),
            switch_condition_met=False,
            cm_t=0.0,
            d_t=0.0,
            regime_post=regime,
            r_t_post=running.reference_price_r_t,
        )

    l7 = apply_l7_scope_state_materialization_v1(
        ScopeStateMaterializationInputV1(nullline=nullline, generator_output=l6)
    )
    if l7.fail_closed or l7.scope is None:
        return MechanicalStepExecutionResultV1(
            episode=episode,
            fail_closed=True,
            fail_reasons=l7.fail_reasons or ("l7_fail_closed",),
            switch_condition_met=False,
            cm_t=0.0,
            d_t=float(l6.d_t),
            regime_post=regime,
            r_t_post=running.reference_price_r_t,
        )

    scope = l7.scope
    l8 = apply_l8_running_reference_step_v1(
        RunningReferenceStepInputV1(
            regime=regime,
            mark_price_m_t=step.mark_price_m_t,
            previous=running,
        )
    )
    l9 = apply_l9_counter_move_v1(
        CounterMoveInputV1(
            regime=regime,
            mark_price_m_t=step.mark_price_m_t,
            running_reference=l8.state,
        )
    )
    l10 = apply_l10_bull_bear_switch_v1(
        BullBearSwitchInputV1(
            regime_pre=regime,
            cm_t=l9.counter_move.cm_t,
            d_t=scope.d_t,
            mark_price_m_t=step.mark_price_m_t,
            running_reference_post=l8.state,
        )
    )
    regime_post = l10.regime_post
    running_post = initial_running_reference_state_v1(
        instrument_id=running.instrument_id,
        reference_price_r_t=l10.persisted_r_t,
    )
    next_episode = _build_episode(
        selected=episode.observation_state.selected,
        regime=regime_post,
        nullline=nullline,
        scope=scope,
        running=running_post,
        observation_state=episode.observation_state,
        last_acceptance=None,
        mechanical_step_count=episode.mechanical_step_count + 1,
    )
    return MechanicalStepExecutionResultV1(
        episode=next_episode,
        fail_closed=False,
        fail_reasons=(),
        switch_condition_met=l10.switch_condition_met,
        cm_t=l9.counter_move.cm_t,
        d_t=scope.d_t,
        regime_post=regime_post,
        r_t_post=running_post.reference_price_r_t,
    )


def atomic_persist_episode_v1(
    store_root: Path,
    episode: NakedLayeredCoreEpisodeV1,
) -> str:
    """Atomic write episode JSON + MANIFEST.sha256 under store_root."""
    store_root.mkdir(parents=True, exist_ok=True)
    snapshot = episode_to_snapshot_v1(episode)
    body = _canonical_json(snapshot)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    snapshot_path = store_root / SNAPSHOT_FILENAME
    manifest_path = store_root / MANIFEST_FILENAME
    tmp_snapshot = snapshot_path.with_suffix(".json.tmp")
    tmp_manifest = manifest_path.with_suffix(".sha256.tmp")
    tmp_snapshot.write_text(body, encoding="utf-8")
    tmp_manifest.write_text(f"{digest}  {SNAPSHOT_FILENAME}\n", encoding="utf-8")
    os.replace(tmp_snapshot, snapshot_path)
    os.replace(tmp_manifest, manifest_path)
    return digest


def restore_episode_from_store_v1(
    store_root: Path,
    *,
    expected_instrument_id: Optional[str] = None,
) -> NakedLayeredCoreEpisodeV1:
    snapshot_path = store_root / SNAPSHOT_FILENAME
    manifest_path = store_root / MANIFEST_FILENAME
    if not snapshot_path.is_file() or not manifest_path.is_file():
        raise NakedLayeredCoreDurableStateError("SNAPSHOT_STORE_INCOMPLETE")
    body = snapshot_path.read_text(encoding="utf-8")
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    manifest_line = manifest_path.read_text(encoding="utf-8").strip().split()
    if not manifest_line or manifest_line[0] != digest:
        raise NakedLayeredCoreDurableStateError("MANIFEST_DIGEST_MISMATCH")
    payload = json.loads(body)
    return episode_from_snapshot_v1(
        payload,
        expected_instrument_id=expected_instrument_id,
    )


def roundtrip_episode_v1(episode: NakedLayeredCoreEpisodeV1) -> NakedLayeredCoreEpisodeV1:
    """Memory roundtrip (codec parity)."""
    snap = episode_to_snapshot_v1(episode)
    return episode_from_snapshot_v1(snap, expected_instrument_id=episode.instrument_id)


def new_episode_store_id_v1() -> str:
    return uuid.uuid4().hex


__all__ = [
    "AUTHORITY_CUTOVER_OCCURRED",
    "DURABLE_STATE_OWNER",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "LEGACY_SEMANTIC_FALLBACK_AUTHORIZED",
    "MANIFEST_FILENAME",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "MechanicalStepExecutionResultV1",
    "NakedLayeredCoreDurableStateError",
    "NakedLayeredCoreEpisodeV1",
    "PRODUCTIVE_BINDING_AUTHORIZED",
    "SNAPSHOT_FILENAME",
    "SNAPSHOT_SCHEMA_NAME",
    "SNAPSHOT_SCHEMA_VERSION",
    "assert_no_legacy_semantic_fields_v1",
    "atomic_persist_episode_v1",
    "episode_from_snapshot_v1",
    "episode_to_snapshot_v1",
    "execute_naked_layered_core_mechanical_step_v1",
    "initialize_naked_layered_core_episode_v1",
    "new_episode_store_id_v1",
    "restore_episode_from_store_v1",
    "roundtrip_episode_v1",
]
