"""Ranking-universe → Full-Core SSF handoff contract V1.

Assertion/validation only over existing Cap 2.2/2.3/2.4 and Master-V2
DTOs. Does not produce ranking, selection, binding, trading, or
execution objects. Does not create a second authority or a new runtime join.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, fields, is_dataclass
from typing import Any

from src.ops.productive_futures_ranking_producer_v1 import constants_v1 as cap22
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    CAPABILITY_ID as CAP23_CAPABILITY_ID,
)
from src.ops.single_selected_future_policy_v1.models_v1 import (
    SingleSelectedFutureSelectionV1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    SELECTION_AUTHORITY_OWNER as CAP24_SELECTION_AUTHORITY_OWNER,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import (
    BoundInstrumentV1,
)

OWNER = "ops.ranking_universe_to_full_core_ssf_handoff_contract_v1"
CONTRACT_ID = "RANKING_UNIVERSE_TO_FULL_CORE_SSF_HANDOFF_CONTRACT_V1"
SCHEMA_VERSION = "ranking_universe_to_full_core_ssf_handoff.v1"

AUTHORITY_EFFECT = "NONE"
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
VALIDATOR_AUTHORITY_EFFECT = "NONE"
SECOND_AUTHORITY_CREATED = False
NEW_RUNTIME_JOIN_CREATED = False
PRODUCTIVE_RUNTIME_SEMANTICS_CHANGED = False
MF_EGRESS_NOT_THIS_HANDOFF = True
C1_GATE_NATIVE_ID_JOINED = False

LAST_RANKING_UNIVERSE_AUTHORITY = CAP23_CAPABILITY_ID
HANDOFF_INPUT_OBJECT = "SingleSelectedFutureSelectionV1"
FIRST_EXTERNAL_RUNTIME_CONSUMER = "run_single_selected_future_runtime_binding_gate_v1"
CAP24_ARCHITECTURAL_CLASSIFICATION = "SHARED_BOUNDARY_SEAM"
CAP24_IS_FULL_CORE_PACKAGE_MEMBER = False
FULL_CORE_INGEST_OBJECT = "BoundInstrumentV1"
FIRST_TRADING_DECISION_CONSUMER = "run_current_productive_master_v2_runtime_cycle_v1"
REPLAY_CONSUMER = "run_integrated_offline_trading_logic_replay_v1"

CAP22_ROLE = "RANKING_CONTEXT_ONLY"
CAP23_ROLE = "SOLE_PRODUCTIVE_SELECTION_AUTHORITY"
CAP24_ROLE = "VALIDATE_AND_BIND_EXISTING_SELECTED_IDENTITY"
MASTER_V2_ROLE = "TRADING_DECISION_AUTHORITY_ON_BOUND_INSTRUMENT"

REPLAY_DROPPED_PROVENANCE_FIELDS = frozenset(
    {"selection_id", "ranking_snapshot_id", "universe_snapshot_id"}
)


class RankingUniverseToFullCoreSsfHandoffError(ValueError):
    """Fail-closed handoff invariant violation."""


@dataclass(frozen=True)
class RankingUniverseToFullCoreSsfHandoffDescriptorV1:
    """Minimal invariant descriptor. Not a producer DTO. Not a second authority."""

    contract_id: str
    last_ranking_universe_authority: str
    handoff_input_object: str
    first_external_runtime_consumer: str
    cap24_architectural_classification: str
    full_core_ingest_object: str
    first_trading_decision_consumer: str
    mf_egress_not_this_handoff: bool
    authority_effect: str
    validator_authority_effect: str
    second_authority_created: bool
    new_runtime_join_created: bool


def contract_descriptor_v1() -> RankingUniverseToFullCoreSsfHandoffDescriptorV1:
    return RankingUniverseToFullCoreSsfHandoffDescriptorV1(
        contract_id=CONTRACT_ID,
        last_ranking_universe_authority=LAST_RANKING_UNIVERSE_AUTHORITY,
        handoff_input_object=HANDOFF_INPUT_OBJECT,
        first_external_runtime_consumer=FIRST_EXTERNAL_RUNTIME_CONSUMER,
        cap24_architectural_classification=CAP24_ARCHITECTURAL_CLASSIFICATION,
        full_core_ingest_object=FULL_CORE_INGEST_OBJECT,
        first_trading_decision_consumer=FIRST_TRADING_DECISION_CONSUMER,
        mf_egress_not_this_handoff=MF_EGRESS_NOT_THIS_HANDOFF,
        authority_effect=AUTHORITY_EFFECT,
        validator_authority_effect=VALIDATOR_AUTHORITY_EFFECT,
        second_authority_created=SECOND_AUTHORITY_CREATED,
        new_runtime_join_created=NEW_RUNTIME_JOIN_CREATED,
    )


def _require_exact_identity(left: str, right: str, *, code: str) -> None:
    if left != right:
        if left.casefold() == right.casefold() or left.strip() != left or right.strip() != right:
            raise RankingUniverseToFullCoreSsfHandoffError(
                f"{code}:SILENT_IDENTITY_NORMALIZATION_FORBIDDEN"
            )
        raise RankingUniverseToFullCoreSsfHandoffError(code)


def _require_nonempty(value: str, *, code: str) -> str:
    text = str(value or "")
    if not text:
        raise RankingUniverseToFullCoreSsfHandoffError(code)
    if text != text.strip() or text != value:
        raise RankingUniverseToFullCoreSsfHandoffError(
            f"{code}:SILENT_IDENTITY_NORMALIZATION_FORBIDDEN"
        )
    return text


def validate_contract_creates_no_runtime_or_execution_authority_v1() -> None:
    if AUTHORITY_EFFECT != "NONE":
        raise RankingUniverseToFullCoreSsfHandoffError("AUTHORITY_EFFECT_NOT_NONE")
    if VALIDATOR_AUTHORITY_EFFECT != "NONE":
        raise RankingUniverseToFullCoreSsfHandoffError("VALIDATOR_AUTHORITY_EFFECT_NOT_NONE")
    if SECOND_AUTHORITY_CREATED is not False:
        raise RankingUniverseToFullCoreSsfHandoffError("SECOND_AUTHORITY_CREATED")
    if NEW_RUNTIME_JOIN_CREATED is not False:
        raise RankingUniverseToFullCoreSsfHandoffError("NEW_RUNTIME_JOIN_CREATED")
    if PRODUCTIVE_RUNTIME_SEMANTICS_CHANGED is not False:
        raise RankingUniverseToFullCoreSsfHandoffError("PRODUCTIVE_RUNTIME_SEMANTICS_CHANGED")


def validate_ranking_context_has_no_selection_trading_or_wire_authority_v1() -> None:
    if cap22.SELECTION_AUTHORITY_ADDED is not False:
        raise RankingUniverseToFullCoreSsfHandoffError("CAP22_SELECTION_AUTHORITY_FORBIDDEN")
    if cap22.ALPHA_AUTHORITY_ADDED is not False:
        raise RankingUniverseToFullCoreSsfHandoffError("CAP22_TRADING_AUTHORITY_FORBIDDEN")
    if cap22.EXECUTION_AUTHORITY_ADDED is not False:
        raise RankingUniverseToFullCoreSsfHandoffError("CAP22_WIRE_AUTHORITY_FORBIDDEN")
    if cap22.LIVE_AUTHORIZED is not False or cap22.ORDERS_AUTHORIZED is not False:
        raise RankingUniverseToFullCoreSsfHandoffError("CAP22_WIRE_AUTHORITY_FORBIDDEN")
    if CAP24_SELECTION_AUTHORITY_OWNER != LAST_RANKING_UNIVERSE_AUTHORITY:
        raise RankingUniverseToFullCoreSsfHandoffError("CAP24_SELECTION_OWNER_MISMATCH")


def validate_selection_identity_owner_is_cap23_v1(
    selection: SingleSelectedFutureSelectionV1,
) -> None:
    if not isinstance(selection, SingleSelectedFutureSelectionV1):
        raise RankingUniverseToFullCoreSsfHandoffError("HANDOFF_INPUT_OBJECT_TYPE_MISMATCH")
    if selection.capability_id != LAST_RANKING_UNIVERSE_AUTHORITY:
        raise RankingUniverseToFullCoreSsfHandoffError("SELECTION_IDENTITY_OWNER_NOT_CAP23")
    selection_fields = {item.name for item in fields(SingleSelectedFutureSelectionV1)}
    if "universe_snapshot_id" in selection_fields:
        raise RankingUniverseToFullCoreSsfHandoffError("UNIVERSE_SNAPSHOT_ID_PRESENT_ON_SSF_DTO")
    payload = selection.to_dict()
    if "universe_snapshot_id" in payload:
        raise RankingUniverseToFullCoreSsfHandoffError("UNIVERSE_SNAPSHOT_ID_PRESENT_ON_SSF_DTO")
    _require_nonempty(selection.instrument_id, code="INSTRUMENT_ID_MISSING")
    _require_nonempty(selection.venue_native_id, code="VENUE_NATIVE_ID_MISSING")
    _require_nonempty(selection.selection_id, code="SELECTION_ID_MISSING")
    _require_nonempty(selection.ranking_snapshot_id, code="RANKING_SNAPSHOT_ID_MISSING")


def validate_cap24_preserves_selected_identity_v1(
    selection: SingleSelectedFutureSelectionV1,
    bound: BoundInstrumentV1,
    *,
    ranking_snapshot_id: str,
    ranking_universe_snapshot_id: str,
    universe_snapshot_id: str,
) -> None:
    if not isinstance(bound, BoundInstrumentV1):
        raise RankingUniverseToFullCoreSsfHandoffError("FULL_CORE_INGEST_OBJECT_TYPE_MISMATCH")
    if type(bound).__name__ != FULL_CORE_INGEST_OBJECT:
        raise RankingUniverseToFullCoreSsfHandoffError("FULL_CORE_INGEST_OBJECT_TYPE_MISMATCH")
    validate_selection_identity_owner_is_cap23_v1(selection)
    expected_ranking = _require_nonempty(ranking_snapshot_id, code="RANKING_SNAPSHOT_ID_MISSING")
    expected_universe = _require_nonempty(universe_snapshot_id, code="UNIVERSE_SNAPSHOT_ID_MISSING")
    ranking_universe = _require_nonempty(
        ranking_universe_snapshot_id, code="UNIVERSE_SNAPSHOT_ID_MISSING"
    )
    _require_exact_identity(
        ranking_universe,
        expected_universe,
        code="UNIVERSE_SNAPSHOT_ID_RANKING_UNIVERSE_MISMATCH",
    )
    _require_exact_identity(
        bound.instrument_id,
        selection.instrument_id,
        code="INSTRUMENT_ID_NOT_PRESERVED",
    )
    _require_exact_identity(
        bound.venue_native_id,
        selection.venue_native_id,
        code="VENUE_NATIVE_ID_NOT_PRESERVED",
    )
    _require_exact_identity(
        bound.selection_id,
        selection.selection_id,
        code="SELECTION_ID_NOT_PRESERVED",
    )
    _require_exact_identity(
        bound.ranking_snapshot_id,
        selection.ranking_snapshot_id,
        code="RANKING_SNAPSHOT_ID_NOT_PRESERVED",
    )
    _require_exact_identity(
        bound.ranking_snapshot_id,
        expected_ranking,
        code="RANKING_SNAPSHOT_ID_MISMATCH",
    )
    _require_exact_identity(
        bound.universe_snapshot_id,
        expected_universe,
        code="UNIVERSE_SNAPSHOT_ID_NOT_REDERIVED",
    )
    _require_exact_identity(
        bound.universe_snapshot_id,
        ranking_universe,
        code="UNIVERSE_SNAPSHOT_ID_NOT_REDERIVED",
    )


def validate_master_v2_consumes_bound_identity_v1(
    bound: BoundInstrumentV1,
    *,
    consumed_instrument_id: str,
    consumed_venue_native_id: str,
) -> None:
    if not isinstance(bound, BoundInstrumentV1):
        raise RankingUniverseToFullCoreSsfHandoffError("FULL_CORE_INGEST_OBJECT_TYPE_MISMATCH")
    _require_nonempty(bound.instrument_id, code="INSTRUMENT_ID_MISSING")
    _require_nonempty(bound.venue_native_id, code="VENUE_NATIVE_ID_MISSING")
    _require_exact_identity(
        consumed_instrument_id,
        bound.instrument_id,
        code="MASTER_V2_INSTRUMENT_REIDENTIFICATION_FORBIDDEN",
    )
    _require_exact_identity(
        consumed_venue_native_id,
        bound.venue_native_id,
        code="MASTER_V2_INSTRUMENT_REIDENTIFICATION_FORBIDDEN",
    )


def validate_replay_drops_handoff_provenance_v1(replay_input: Any) -> None:
    if not is_dataclass(replay_input):
        raise RankingUniverseToFullCoreSsfHandoffError("REPLAY_INPUT_NOT_DATACLASS")
    replay_fields = {item.name for item in fields(replay_input)}
    leaked = REPLAY_DROPPED_PROVENANCE_FIELDS.intersection(replay_fields)
    if leaked:
        raise RankingUniverseToFullCoreSsfHandoffError(
            f"HANDOFF_PROVENANCE_LEAKED_INTO_REPLAY:{sorted(leaked)}"
        )
    if "instrument_id" not in replay_fields:
        raise RankingUniverseToFullCoreSsfHandoffError("REPLAY_INSTRUMENT_ID_MISSING")
    if inspect.isclass(replay_input):
        return
    instrument_id = str(getattr(replay_input, "instrument_id", "") or "")
    if not instrument_id:
        raise RankingUniverseToFullCoreSsfHandoffError("REPLAY_INSTRUMENT_ID_MISSING")


def assert_handoff_invariants_v1(
    selection: SingleSelectedFutureSelectionV1,
    bound: BoundInstrumentV1,
    *,
    ranking_snapshot_id: str,
    ranking_universe_snapshot_id: str,
    universe_snapshot_id: str,
) -> RankingUniverseToFullCoreSsfHandoffDescriptorV1:
    validate_contract_creates_no_runtime_or_execution_authority_v1()
    validate_ranking_context_has_no_selection_trading_or_wire_authority_v1()
    validate_cap24_preserves_selected_identity_v1(
        selection,
        bound,
        ranking_snapshot_id=ranking_snapshot_id,
        ranking_universe_snapshot_id=ranking_universe_snapshot_id,
        universe_snapshot_id=universe_snapshot_id,
    )
    return contract_descriptor_v1()
