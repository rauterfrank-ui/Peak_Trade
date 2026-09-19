"""Bounded tests for RANKING_UNIVERSE_TO_FULL_CORE_SSF_HANDOFF_CONTRACT_V1."""

from __future__ import annotations

import inspect
from dataclasses import fields
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (  # noqa: E501
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
    C1_GATE_NATIVE_ID,
)
from src.ops.mf_canonical_single_egress_authority_handoff_contract_v1 import (
    PRODUCTIVE_CAP22_CAP23_PATH_CLASS,
)
from src.ops.productive_futures_ranking_producer_v1 import constants_v1 as cap22
from src.ops.ranking_universe_to_full_core_ssf_handoff_contract_v1 import (
    AUTHORITY_EFFECT,
    CAP24_ARCHITECTURAL_CLASSIFICATION,
    CAP24_IS_FULL_CORE_PACKAGE_MEMBER,
    CONTRACT_ID,
    FIRST_EXTERNAL_RUNTIME_CONSUMER,
    FIRST_TRADING_DECISION_CONSUMER,
    FULL_CORE_INGEST_OBJECT,
    HANDOFF_INPUT_OBJECT,
    LAST_RANKING_UNIVERSE_AUTHORITY,
    MF_EGRESS_NOT_THIS_HANDOFF,
    NEW_RUNTIME_JOIN_CREATED,
    PRODUCTIVE_RUNTIME_SEMANTICS_CHANGED,
    SECOND_AUTHORITY_CREATED,
    VALIDATOR_AUTHORITY_EFFECT,
    RankingUniverseToFullCoreSsfHandoffError,
    assert_handoff_invariants_v1,
    contract_descriptor_v1,
    validate_master_v2_consumes_bound_identity_v1,
    validate_ranking_context_has_no_selection_trading_or_wire_authority_v1,
    validate_replay_drops_handoff_provenance_v1,
    validate_selection_identity_owner_is_cap23_v1,
)
from src.ops.single_selected_future_policy_v1.models_v1 import (
    SingleSelectedFutureSelectionV1,
)
from src.ops.single_selected_future_runtime_binding_v1.binding_gate_v1 import (
    run_single_selected_future_runtime_binding_gate_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    RUNTIME_ACTIVATION_ALLOWED as CAP24_RUNTIME_ACTIVATION_ALLOWED,
    SELECTION_AUTHORITY_OWNER,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import (
    BoundInstrumentV1,
)
from src.trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayInputV1,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_SOURCE = REPO_ROOT / "src/ops/ranking_universe_to_full_core_ssf_handoff_contract_v1.py"
BINDING_GATE_SOURCE = (
    REPO_ROOT / "src/ops/single_selected_future_runtime_binding_v1/binding_gate_v1.py"
)
MASTER_V2_SOURCE = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_master_v2_runtime_cycle_v1.py"
)
SPEC = REPO_ROOT / "docs/ops/specs/RANKING_UNIVERSE_TO_FULL_CORE_SSF_HANDOFF_CONTRACT_V1.md"
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"

INSTRUMENT_ID = "okx_eea:BTC-USDT-SWAP"
VENUE_NATIVE_ID = "BTC-USDT-SWAP"
SELECTION_ID = "sel_handoff_1"
RANKING_SNAPSHOT_ID = "rank_handoff_1"
UNIVERSE_SNAPSHOT_ID = "uni_handoff_1"


def _selection(**overrides: object) -> SingleSelectedFutureSelectionV1:
    payload: dict[str, object] = {
        "schema_version": "single_selected_future_selection.v1",
        "capability_id": LAST_RANKING_UNIVERSE_AUTHORITY,
        "producer_version": "single_selected_future_policy.v1",
        "selection_id": SELECTION_ID,
        "instrument_id": INSTRUMENT_ID,
        "venue_native_id": VENUE_NATIVE_ID,
        "ranking_snapshot_id": RANKING_SNAPSHOT_ID,
        "ranking_integrity_digest": "a" * 64,
        "ranking_event_time": "2026-09-16T00:00:00Z",
        "selected_at_event_time": "2026-09-16T00:00:00Z",
        "selected_at_wall_time": "2026-09-16T00:00:00Z",
        "valid_from": "2026-09-16T00:00:00Z",
        "valid_until": "2026-09-16T01:00:00Z",
        "policy_version": "v1",
        "policy_id": "single_selected_future_policy_v1",
        "config_digest": "b" * 64,
        "repository_sha": "c" * 40,
        "reason_codes": ("SELECTED",),
        "state": "SELECTED_ACTIVE",
        "integrity_digest": "",
    }
    payload.update(overrides)
    return SingleSelectedFutureSelectionV1.from_dict(payload).with_integrity_digest()


def _bound(
    selection: SingleSelectedFutureSelectionV1,
    *,
    universe_snapshot_id: str = UNIVERSE_SNAPSHOT_ID,
    **overrides: object,
) -> BoundInstrumentV1:
    payload = {
        "instrument_id": selection.instrument_id,
        "venue_native_id": selection.venue_native_id,
        "ranking_snapshot_id": selection.ranking_snapshot_id,
        "ranking_integrity_digest": selection.ranking_integrity_digest,
        "universe_snapshot_id": universe_snapshot_id,
        "selection_id": selection.selection_id,
        "selection_integrity_digest": selection.integrity_digest,
        "selection_state": selection.state,
    }
    payload.update(overrides)
    return BoundInstrumentV1(**payload)


def test_contract_descriptor_and_safety_invariants() -> None:
    descriptor = contract_descriptor_v1()
    assert descriptor.contract_id == CONTRACT_ID
    assert descriptor.last_ranking_universe_authority == (
        "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"
    )
    assert descriptor.handoff_input_object == "SingleSelectedFutureSelectionV1"
    assert descriptor.first_external_runtime_consumer == (
        "run_single_selected_future_runtime_binding_gate_v1"
    )
    assert descriptor.cap24_architectural_classification == "SHARED_BOUNDARY_SEAM"
    assert CAP24_IS_FULL_CORE_PACKAGE_MEMBER is False
    assert descriptor.full_core_ingest_object == "BoundInstrumentV1"
    assert descriptor.first_trading_decision_consumer == (
        "run_current_productive_master_v2_runtime_cycle_v1"
    )
    assert descriptor.mf_egress_not_this_handoff is True
    assert descriptor.authority_effect == "NONE"
    assert descriptor.validator_authority_effect == "NONE"
    assert descriptor.second_authority_created is False
    assert descriptor.new_runtime_join_created is False
    assert AUTHORITY_EFFECT == "NONE"
    assert VALIDATOR_AUTHORITY_EFFECT == "NONE"
    assert SECOND_AUTHORITY_CREATED is False
    assert NEW_RUNTIME_JOIN_CREATED is False
    assert PRODUCTIVE_RUNTIME_SEMANTICS_CHANGED is False
    assert MF_EGRESS_NOT_THIS_HANDOFF is True
    assert PRODUCTIVE_CAP22_CAP23_PATH_CLASS == "NOT_MF_EGRESS"
    assert C1_GATE_NATIVE_ID == "0G-USDT-SWAP"
    assert CAP24_RUNTIME_ACTIVATION_ALLOWED is False
    assert cap22.RUNTIME_ACTIVATION_ALLOWED is False
    assert (
        FIRST_EXTERNAL_RUNTIME_CONSUMER
        == run_single_selected_future_runtime_binding_gate_v1.__name__
    )
    assert (
        FIRST_TRADING_DECISION_CONSUMER
        == run_current_productive_master_v2_runtime_cycle_v1.__name__
    )
    assert HANDOFF_INPUT_OBJECT == SingleSelectedFutureSelectionV1.__name__
    assert FULL_CORE_INGEST_OBJECT == BoundInstrumentV1.__name__
    assert CAP24_ARCHITECTURAL_CLASSIFICATION == "SHARED_BOUNDARY_SEAM"


def test_canonical_docs_persist_current_contract() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    nav = MAP_OF_TRUTH.read_text(encoding="utf-8")
    owner = (
        REPO_ROOT / "src/ops/ranking_universe_to_full_core_ssf_handoff_contract_v1.py"
    ).read_text(encoding="utf-8")
    assert "CONTRACT_ID=RANKING_UNIVERSE_TO_FULL_CORE_SSF_HANDOFF_CONTRACT_V1" in spec
    assert "LAST_RANKING_UNIVERSE_AUTHORITY=CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1" in spec
    assert "HANDOFF_INPUT_OBJECT=SingleSelectedFutureSelectionV1" in spec
    assert (
        "FIRST_EXTERNAL_RUNTIME_CONSUMER=run_single_selected_future_runtime_binding_gate_v1" in spec
    )
    assert "CAP24_ARCHITECTURAL_CLASSIFICATION=SHARED_BOUNDARY_SEAM" in spec
    assert "FULL_CORE_INGEST_OBJECT=BoundInstrumentV1" in spec
    assert (
        "FIRST_TRADING_DECISION_CONSUMER=run_current_productive_master_v2_runtime_cycle_v1" in spec
    )
    assert "MF_EGRESS_NOT_THIS_HANDOFF=true" in spec
    assert "LAST_RANKING_UNIVERSE_AUTHORITY" in owner
    assert "AUTHORITY_EFFECT=NONE" in spec
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in nav


def test_cap22_has_no_selection_trading_or_wire_authority() -> None:
    validate_ranking_context_has_no_selection_trading_or_wire_authority_v1()
    assert cap22.SELECTION_AUTHORITY_ADDED is False
    assert cap22.ALPHA_AUTHORITY_ADDED is False
    assert cap22.EXECUTION_AUTHORITY_ADDED is False
    assert SELECTION_AUTHORITY_OWNER == LAST_RANKING_UNIVERSE_AUTHORITY


def test_ssf_field_lineage_and_universe_snapshot_absent_on_dto() -> None:
    selection = _selection()
    names = {item.name for item in fields(SingleSelectedFutureSelectionV1)}
    assert "instrument_id" in names
    assert "venue_native_id" in names
    assert "selection_id" in names
    assert "ranking_snapshot_id" in names
    assert "universe_snapshot_id" not in names
    assert "universe_snapshot_id" not in selection.to_dict()
    validate_selection_identity_owner_is_cap23_v1(selection)


def test_cap24_preserves_selected_identity_and_rederives_universe() -> None:
    selection = _selection()
    bound = _bound(selection)
    descriptor = assert_handoff_invariants_v1(
        selection,
        bound,
        ranking_snapshot_id=RANKING_SNAPSHOT_ID,
        ranking_universe_snapshot_id=UNIVERSE_SNAPSHOT_ID,
        universe_snapshot_id=UNIVERSE_SNAPSHOT_ID,
    )
    assert bound.instrument_id == selection.instrument_id
    assert bound.venue_native_id == selection.venue_native_id
    assert bound.selection_id == selection.selection_id
    assert bound.ranking_snapshot_id == selection.ranking_snapshot_id
    assert bound.universe_snapshot_id == UNIVERSE_SNAPSHOT_ID
    assert descriptor.full_core_ingest_object == "BoundInstrumentV1"


@pytest.mark.parametrize(
    ("override", "code"),
    [
        ({"instrument_id": "okx_eea:ETH-USDT-SWAP"}, "INSTRUMENT_ID_NOT_PRESERVED"),
        ({"instrument_id": INSTRUMENT_ID.lower()}, "INSTRUMENT_ID_NOT_PRESERVED"),
        ({"venue_native_id": "ETH-USDT-SWAP"}, "VENUE_NATIVE_ID_NOT_PRESERVED"),
        ({"venue_native_id": VENUE_NATIVE_ID.lower()}, "VENUE_NATIVE_ID_NOT_PRESERVED"),
        ({"selection_id": "sel_other"}, "SELECTION_ID_NOT_PRESERVED"),
        ({"ranking_snapshot_id": "rank_other"}, "RANKING_SNAPSHOT_ID_NOT_PRESERVED"),
        ({"universe_snapshot_id": "uni_other"}, "UNIVERSE_SNAPSHOT_ID_NOT_REDERIVED"),
    ],
)
def test_identity_or_provenance_mismatch_fails_closed(override: dict[str, str], code: str) -> None:
    selection = _selection()
    bound = _bound(selection, **override)
    with pytest.raises(RankingUniverseToFullCoreSsfHandoffError, match=code):
        assert_handoff_invariants_v1(
            selection,
            bound,
            ranking_snapshot_id=RANKING_SNAPSHOT_ID,
            ranking_universe_snapshot_id=UNIVERSE_SNAPSHOT_ID,
            universe_snapshot_id=UNIVERSE_SNAPSHOT_ID,
        )


def test_universe_snapshot_ranking_universe_mismatch_fails_closed() -> None:
    selection = _selection()
    bound = _bound(selection)
    with pytest.raises(
        RankingUniverseToFullCoreSsfHandoffError,
        match="UNIVERSE_SNAPSHOT_ID_RANKING_UNIVERSE_MISMATCH",
    ):
        assert_handoff_invariants_v1(
            selection,
            bound,
            ranking_snapshot_id=RANKING_SNAPSHOT_ID,
            ranking_universe_snapshot_id="uni_from_ranking_other",
            universe_snapshot_id=UNIVERSE_SNAPSHOT_ID,
        )


def test_missing_required_provenance_fails_closed() -> None:
    selection = _selection(selection_id="")
    with pytest.raises(RankingUniverseToFullCoreSsfHandoffError, match="SELECTION_ID_MISSING"):
        validate_selection_identity_owner_is_cap23_v1(selection)
    foreign = _selection(capability_id="CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1")
    with pytest.raises(
        RankingUniverseToFullCoreSsfHandoffError, match="SELECTION_IDENTITY_OWNER_NOT_CAP23"
    ):
        validate_selection_identity_owner_is_cap23_v1(foreign)


def test_master_v2_consumes_bound_identity_and_must_not_reidentify() -> None:
    selection = _selection()
    bound = _bound(selection)
    validate_master_v2_consumes_bound_identity_v1(
        bound,
        consumed_instrument_id=bound.instrument_id,
        consumed_venue_native_id=bound.venue_native_id,
    )
    with pytest.raises(
        RankingUniverseToFullCoreSsfHandoffError,
        match="MASTER_V2_INSTRUMENT_REIDENTIFICATION_FORBIDDEN",
    ):
        validate_master_v2_consumes_bound_identity_v1(
            bound,
            consumed_instrument_id="okx_eea:ETH-USDT-SWAP",
            consumed_venue_native_id=bound.venue_native_id,
        )
    with pytest.raises(
        RankingUniverseToFullCoreSsfHandoffError,
        match="MASTER_V2_INSTRUMENT_REIDENTIFICATION_FORBIDDEN",
    ):
        validate_master_v2_consumes_bound_identity_v1(
            bound,
            consumed_instrument_id=bound.instrument_id.lower(),
            consumed_venue_native_id=bound.venue_native_id,
        )
    signature = inspect.signature(run_current_productive_master_v2_runtime_cycle_v1)
    bound_param = signature.parameters["bound_instrument"]
    assert bound_param.annotation in {BoundInstrumentV1, "BoundInstrumentV1"}
    source = MASTER_V2_SOURCE.read_text(encoding="utf-8")
    assert "bound_instrument.instrument_id" in source
    assert "bound_instrument.venue_native_id" in source
    assert "run_single_selected_future_policy_v1" not in source
    assert "produce_productive_futures_ranking_v1" not in source


def test_replay_drops_selection_ranking_and_universe_provenance() -> None:
    names = {item.name for item in fields(IntegratedOfflineReplayInputV1)}
    assert "instrument_id" in names
    assert "selection_id" not in names
    assert "ranking_snapshot_id" not in names
    assert "universe_snapshot_id" not in names
    validate_replay_drops_handoff_provenance_v1(IntegratedOfflineReplayInputV1)


def test_cap24_gate_does_not_rerank_or_reselect() -> None:
    source = BINDING_GATE_SOURCE.read_text(encoding="utf-8")
    assert "BoundInstrumentV1(" in source
    assert "instrument_id=selection.instrument_id" in source
    assert "venue_native_id=selection.venue_native_id" in source
    assert "selection_id=selection.selection_id" in source
    assert "universe_snapshot_id=universe.snapshot_id" in source
    assert "produce_productive_futures_ranking_v1" not in source
    assert "run_single_selected_future_policy_v1" not in source
    assert "run_productive_futures_ranking_producer_v1" not in source


def test_contract_creates_no_runtime_or_execution_authority() -> None:
    source = CONTRACT_SOURCE.read_text(encoding="utf-8")
    assert 'VALIDATOR_AUTHORITY_EFFECT = "NONE"' in source
    assert "SECOND_AUTHORITY_CREATED = False" in source
    assert "NEW_RUNTIME_JOIN_CREATED = False" in source
    assert "run_single_selected_future_runtime_binding_gate_v1(" not in source
    assert "run_current_productive_master_v2_runtime_cycle_v1(" not in source
    assert "LiveExecutionPort" not in source
    assert "send_order" not in source
    assert "permit" not in source.lower()
