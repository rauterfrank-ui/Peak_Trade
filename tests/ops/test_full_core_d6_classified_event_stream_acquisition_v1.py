"""D6 classified event-stream acquisition and completeness fail-closed boundary."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    BOUND_ACCOUNT_CONCRETE_UID_OBSERVED,
    BOUND_ACCOUNT_IDENTITY_PROVEN,
    C01_C16_REJECTION_STILL_BINDING,
    C17_CREATED,
    C17_CREATION_FROZEN_UNTIL_D1_D9_PROVEN,
    CHECKPOINT_CAN_MINT_EQUITY,
    CHECKPOINT_OBSERVATION_PROVEN,
    COMPLETE_EVENT_STREAM_PROVEN,
    EARLIEST_OPTION_D_DEPENDENCY,
    EVENT_ACQUISITION_CREATED,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    EVENT_ACQUISITION_RUNTIME_INSTANCE_PRESENT,
    EVENT_ACQUISITION_SCHEMA_PRESENT,
    GOVERNED_PRODUCER_CREATED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ENGINE_CREATED,
    RESTART_PROVEN,
    SOURCE_SELECTED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    live_admission_gap_dag_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_contract_v1 import (
    BoundAccountIdentityContractV1,
    build_bound_account_identity_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_acquisition_contract_v1 import (
    FRESHNESS_EVIDENCE_STATUS,
    acquire_checkpoint_observation_v1,
    bind_checkpoint_observation_to_checkpoint_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.classified_event_stream_acquisition_contract_v1 import (
    COMPLETENESS_UNPROVEN,
    MISSING_COMPLETENESS_DEPENDENCY,
    SOURCE_STATUS_MISSING,
    ClassifiedEventAcquisitionResultV1,
    ClassifiedEventStreamAcquisitionContractError,
    acquire_classified_event_v1,
    bind_classified_event_stream_to_checkpoint_v1,
    compute_classified_event_stream_digest_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    C01_C16_NOT_ELEVATED,
    C01_C16_REVIVAL_ALLOWED,
    OWNER,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
    RATIFIED_CLASSIFIED_KIND_SET_RESOLVED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_stock_checkpoint_contract_v1 import (
    EQUITY_MINT_STATUS_NOT_MINTED,
    build_equity_stock_checkpoint_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.source_candidate_v1 import (
    C01_C16_IDS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION_V1.md"
)
AT_HEADING = "11.2.1.AT FULL_CORE_D5_CHECKPOINT_OBSERVATION_ACQUISITION"
AU_HEADING = "11.2.1.AU FULL_CORE_D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION"
AV_HEADING = "11.2.1.AV FULL_CORE_D6_CLASSIFIED_KIND_SET_AND_EVENT_SOURCE_SEAM"
_DIGEST = "a" * 64
_DIGEST_B = "b" * 64
_ISO = "2026-09-13T08:48:00Z"
_NEW_CONTRACT_FILES = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "classified_event_stream_acquisition_contract_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "equity_affecting_event_taxonomy_contract_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "checkpoint_observation_acquisition_contract_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "bound_account_identity_contract_v1.py",
)
_FORBIDDEN_ENGINE_MARKERS = (
    "reconstruct_equity_stock_from_events",
    "acquire_equity_events",
    "requests.",
    "httpx.",
    "urllib.request",
)


def _identity(*, identity_id: str, account: str) -> BoundAccountIdentityContractV1:
    return build_bound_account_identity_contract_v1(
        identity_id=identity_id,
        bound_account_identity=account,
        bound_venue_identity="SYNTHETIC_VENUE_OKX",
        bound_td_mode="cross",
        settlement_currency="USDC",
    )


def _identity_kwargs(identity: BoundAccountIdentityContractV1) -> dict[str, str]:
    return {
        "bound_account_identity_ref": identity.identity_id,
        "bound_account_identity_digest": identity.identity_digest,
        "expected_bound_account_identity_ref": identity.identity_id,
        "expected_bound_account_identity_digest": identity.identity_digest,
    }


def _checkpoint(identity: BoundAccountIdentityContractV1):
    return build_equity_stock_checkpoint_contract_v1(
        checkpoint_id="CKPT_EVENT_STREAM_A",
        schema_digest=_DIGEST,
        input_set_digest=_DIGEST_B,
        checkpoint_version="v1",
        bound_account_identity_ref=identity.identity_id,
        bound_account_identity_digest=identity.identity_digest,
    )


def _observation(identity: BoundAccountIdentityContractV1):
    return acquire_checkpoint_observation_v1(
        observation_id="CKPT_OBS_STREAM_A",
        source_observation_id="SRC_OBS_STREAM_A",
        observed_at_as_of=_ISO,
        acquired_at=_ISO,
        component_completeness="COMPLETE",
        freshness_policy_status=FRESHNESS_EVIDENCE_STATUS,
        **_identity_kwargs(identity),
    )


def _binding(identity: BoundAccountIdentityContractV1):
    observation = _observation(identity)
    checkpoint = _checkpoint(identity)
    binding = bind_checkpoint_observation_to_checkpoint_v1(
        binding_id="BIND_STREAM_OBS_A",
        checkpoint=checkpoint,
        acquisition=observation,
    )
    return checkpoint, observation, binding


def _au_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    au_start = runbook.index(AU_HEADING)
    return runbook[au_start : runbook.index(AV_HEADING, au_start)]


def test_d4_and_d5_prerequisites_and_exact_account_binding() -> None:
    identity = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    checkpoint, observation, binding = _binding(identity)
    stream = bind_classified_event_stream_to_checkpoint_v1(
        stream_id="EVT_STREAM_A",
        checkpoint=checkpoint,
        observation=observation,
        observation_binding=binding,
        events=(),
        completeness_status=COMPLETENESS_UNPROVEN,
        source_status=SOURCE_STATUS_MISSING,
    )
    assert BOUND_ACCOUNT_IDENTITY_PROVEN is True
    assert CHECKPOINT_OBSERVATION_PROVEN is True
    assert stream.bound_account_identity_ref == identity.identity_id
    assert stream.bound_account_identity_digest == identity.identity_digest
    assert stream.checkpoint_id == checkpoint.checkpoint_id
    assert stream.checkpoint_observation_ref == observation.observation_id
    assert stream.checkpoint_observation_digest == observation.provenance_digest
    assert stream.checkpoint_provenance_digest == checkpoint.provenance_digest
    assert stream.completeness_status == COMPLETENESS_UNPROVEN
    assert stream.complete_event_stream_proven == "false"
    assert stream.missing_completeness_dependency == MISSING_COMPLETENESS_DEPENDENCY
    assert stream.event_count == "0"
    assert stream.ordering_proven == "false"
    assert stream.gap_detected == "UNKNOWN"
    assert checkpoint.equity_mint_status == EQUITY_MINT_STATUS_NOT_MINTED
    assert stream.authority_effect == "NONE"
    assert len(stream.stream_replay_identity) == 64
    assert stream.provenance_digest == compute_classified_event_stream_digest_v1(
        {
            "stream_id": stream.stream_id,
            "stream_replay_identity": stream.stream_replay_identity,
            "checkpoint_id": stream.checkpoint_id,
            "checkpoint_provenance_digest": stream.checkpoint_provenance_digest,
            "checkpoint_observation_ref": stream.checkpoint_observation_ref,
            "checkpoint_observation_digest": stream.checkpoint_observation_digest,
            "bound_account_identity_ref": stream.bound_account_identity_ref,
            "bound_account_identity_digest": stream.bound_account_identity_digest,
            "coverage_boundary_class": stream.coverage_boundary_class,
            "completeness_status": stream.completeness_status,
            "source_status": stream.source_status,
            "event_count": stream.event_count,
            "ordering_proven": stream.ordering_proven,
            "gap_detected": stream.gap_detected,
            "complete_event_stream_proven": stream.complete_event_stream_proven,
            "missing_completeness_dependency": stream.missing_completeness_dependency,
            "reconstructed_equity_created": "false",
            "reconstruction_engine_created": "false",
            "eq_reconciliation_executed": "false",
            "raw_eq_source_authority": "false",
            "source_selected": "false",
            "mapping_proven": "false",
            "c17_created": "false",
            "network_method": "NONE",
            "authority_effect": "NONE",
        }
    )


def test_cross_account_mismatch_fail_closed() -> None:
    identity_a = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    identity_b = _identity(identity_id="SYNTHETIC_ACCOUNT_B", account="SYNTHETIC_ACCOUNT_B")
    checkpoint_a, observation_a, binding_a = _binding(identity_a)
    _checkpoint_b, observation_b, _binding_b = _binding(identity_b)
    with pytest.raises(ClassifiedEventStreamAcquisitionContractError) as mismatch:
        bind_classified_event_stream_to_checkpoint_v1(
            stream_id="EVT_STREAM_MIX",
            checkpoint=checkpoint_a,
            observation=observation_b,
            observation_binding=binding_a,
            events=(),
            completeness_status=COMPLETENESS_UNPROVEN,
        )
    assert "EVENT_STREAM_IDENTITY_MISMATCH_CROSS_ACCOUNT" in str(mismatch.value)


def test_unknown_unclassified_fail_closed() -> None:
    identity = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    kwargs = _identity_kwargs(identity)
    with pytest.raises(ClassifiedEventStreamAcquisitionContractError) as unknown_err:
        acquire_classified_event_v1(
            event_id="EVT_A",
            source_event_id="SRC_EVT_A",
            taxonomy_class="UNKNOWN",
            event_semantic_class="UNKNOWN",
            source_reference="SRC_REF_A",
            ordering_key="1",
            replay_identity=_DIGEST,
            event_digest=_DIGEST,
            **kwargs,
        )
    assert "UNKNOWN_FAIL_CLOSED" in str(unknown_err.value)
    with pytest.raises(ClassifiedEventStreamAcquisitionContractError) as unclassified_err:
        acquire_classified_event_v1(
            event_id="EVT_B",
            source_event_id="SRC_EVT_B",
            taxonomy_class="UNCLASSIFIED",
            event_semantic_class="UNCLASSIFIED",
            source_reference="SRC_REF_B",
            ordering_key="2",
            replay_identity=_DIGEST_B,
            event_digest=_DIGEST_B,
            **kwargs,
        )
    assert "UNCLASSIFIED_FAIL_CLOSED" in str(unclassified_err.value)


def test_missing_source_range_gap_and_duplicate_order_fail_closed() -> None:
    identity = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    checkpoint, observation, binding = _binding(identity)
    with pytest.raises(ClassifiedEventStreamAcquisitionContractError) as classified_err:
        acquire_classified_event_v1(
            event_id="EVT_CLASSIFIED",
            source_event_id="SRC_EVT_CLASSIFIED",
            taxonomy_class="CLASSIFIED",
            event_semantic_class="FILL",
            source_reference="SRC_REF_CLASSIFIED",
            ordering_key="1",
            replay_identity=_DIGEST,
            event_digest=_DIGEST,
            **_identity_kwargs(identity),
        )
    assert "CLASSIFIED_KIND_NOT_RATIFIED" in str(classified_err.value)
    with pytest.raises(ClassifiedEventStreamAcquisitionContractError) as missing_src_err:
        acquire_classified_event_v1(
            event_id="EVT_MISSING_SRC",
            source_event_id="SRC_EVT_MISSING",
            taxonomy_class="CLASSIFIED",
            event_semantic_class="FILL",
            source_reference="MISSING",
            ordering_key="1",
            replay_identity=_DIGEST,
            event_digest=_DIGEST,
            **_identity_kwargs(identity),
        )
    assert "MISSING_FAIL_CLOSED" in str(missing_src_err.value)
    with pytest.raises(ClassifiedEventStreamAcquisitionContractError) as source_err:
        bind_classified_event_stream_to_checkpoint_v1(
            stream_id="EVT_STREAM_SOURCE",
            checkpoint=checkpoint,
            observation=observation,
            observation_binding=binding,
            events=(),
            completeness_status=COMPLETENESS_UNPROVEN,
            source_status="PRESENT",
        )
    assert "EVENT_STREAM_SOURCE_PRESENT_NOT_PROVEN" in str(source_err.value)
    with pytest.raises(ClassifiedEventStreamAcquisitionContractError) as complete_err:
        bind_classified_event_stream_to_checkpoint_v1(
            stream_id="EVT_STREAM_COMPLETE",
            checkpoint=checkpoint,
            observation=observation,
            observation_binding=binding,
            events=(),
            completeness_status="COMPLETE",
        )
    assert "EVENT_STREAM_COMPLETENESS_COMPLETE_NOT_PROVEN" in str(complete_err.value)
    assert RATIFIED_CLASSIFIED_KIND_SET == ()
    assert RATIFIED_CLASSIFIED_KIND_SET_RESOLVED is False


def test_absence_is_not_zero_events() -> None:
    identity = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    checkpoint, observation, binding = _binding(identity)
    stream = bind_classified_event_stream_to_checkpoint_v1(
        stream_id="EVT_STREAM_ABSENCE",
        checkpoint=checkpoint,
        observation=observation,
        observation_binding=binding,
        events=(),
        completeness_status=COMPLETENESS_UNPROVEN,
    )
    assert stream.event_count == "0"
    assert stream.completeness_status != "COMPLETE"
    assert stream.complete_event_stream_proven == "false"
    assert COMPLETE_EVENT_STREAM_PROVEN is False


def test_duplicate_order_gap_and_equity_mutation_fail_closed() -> None:
    identity = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    checkpoint, observation, binding = _binding(identity)

    def _event(**overrides: str) -> ClassifiedEventAcquisitionResultV1:
        payload = {
            "event_id": "EVT_INJECTED",
            "source_event_id": "SRC_EVT_INJECTED",
            "taxonomy_class": "CLASSIFIED",
            "event_semantic_class": "UNRATIFIED",
            "source_reference": "SRC_REF_INJECTED",
            "ordering_key": "1",
            "replay_identity": _DIGEST,
            "event_digest": _DIGEST,
            "bound_account_identity_ref": identity.identity_id,
            "bound_account_identity_digest": identity.identity_digest,
            "equity_stock_mutation_status": "NOT_MUTATED",
            "claimed_equity_stock_value": "ABSENT",
            "reconstructed_equity_created": "false",
            "network_method": "NONE",
            "authority_effect": "NONE",
            "provenance_digest": _DIGEST,
        }
        payload.update(overrides)
        return ClassifiedEventAcquisitionResultV1(**payload)

    duplicate = _event()
    with pytest.raises(ClassifiedEventStreamAcquisitionContractError) as dup_err:
        bind_classified_event_stream_to_checkpoint_v1(
            stream_id="EVT_STREAM_DUP",
            checkpoint=checkpoint,
            observation=observation,
            observation_binding=binding,
            events=(duplicate, duplicate),
            completeness_status=COMPLETENESS_UNPROVEN,
        )
    assert "EVENT_STREAM_DUPLICATE_REPLAY_IDENTITY_FAIL_CLOSED" in str(dup_err.value)
    with pytest.raises(ClassifiedEventStreamAcquisitionContractError) as order_err:
        bind_classified_event_stream_to_checkpoint_v1(
            stream_id="EVT_STREAM_ORDER",
            checkpoint=checkpoint,
            observation=observation,
            observation_binding=binding,
            events=(
                _event(ordering_key="2", replay_identity=_DIGEST, event_id="EVT_2"),
                _event(ordering_key="1", replay_identity=_DIGEST_B, event_id="EVT_1"),
            ),
            completeness_status=COMPLETENESS_UNPROVEN,
        )
    assert "EVENT_STREAM_ORDERING_AMBIGUITY_FAIL_CLOSED" in str(order_err.value)
    with pytest.raises(ClassifiedEventStreamAcquisitionContractError) as mutate_err:
        bind_classified_event_stream_to_checkpoint_v1(
            stream_id="EVT_STREAM_MUTATE",
            checkpoint=checkpoint,
            observation=observation,
            observation_binding=binding,
            events=(_event(equity_stock_mutation_status="MUTATED"),),
            completeness_status=COMPLETENESS_UNPROVEN,
        )
    assert "EVENT_STREAM_CANNOT_MUTATE_EQUITY_STOCK" in str(mutate_err.value)


def test_no_event_can_mint_or_overwrite_equity() -> None:
    identity = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    with pytest.raises(ClassifiedEventStreamAcquisitionContractError) as mint_err:
        acquire_classified_event_v1(
            event_id="EVT_MINT",
            source_event_id="SRC_EVT_MINT",
            taxonomy_class="CLASSIFIED",
            event_semantic_class="FILL",
            source_reference="SRC_REF_MINT",
            ordering_key="1",
            replay_identity=_DIGEST,
            event_digest=_DIGEST,
            claimed_equity_stock_value="100.00",
            **_identity_kwargs(identity),
        )
    assert "CLASSIFIED_KIND_NOT_RATIFIED" in str(mint_err.value) or (
        "EVENT_STREAM_CANNOT_MINT_OR_OVERWRITE_EQUITY" in str(mint_err.value)
    )
    with pytest.raises(ClassifiedEventStreamAcquisitionContractError) as mutate_err:
        acquire_classified_event_v1(
            event_id="EVT_MUTATE",
            source_event_id="SRC_EVT_MUTATE",
            taxonomy_class="CLASSIFIED",
            event_semantic_class="FILL",
            source_reference="SRC_REF_MUTATE",
            ordering_key="1",
            replay_identity=_DIGEST,
            event_digest=_DIGEST,
            equity_stock_mutation_status="MUTATED",
            **_identity_kwargs(identity),
        )
    assert "CLASSIFIED_KIND_NOT_RATIFIED" in str(mutate_err.value) or (
        "EVENT_STREAM_CANNOT_MUTATE_EQUITY_STOCK" in str(mutate_err.value)
    )


def test_existing_owner_pins_and_non_regression() -> None:
    dag = live_admission_gap_dag_v1()
    assert OWNER == "ops.governed_productive_account_equity_authority_producer_v1"
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER == OWNER
    assert EVENT_ACQUISITION_SCHEMA_PRESENT is True
    assert EVENT_ACQUISITION_CREATED is True
    assert COMPLETE_EVENT_STREAM_PROVEN is False
    assert EVENT_ACQUISITION_RUNTIME_INSTANCE_PRESENT is False
    assert EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is False
    assert BOUND_ACCOUNT_CONCRETE_UID_OBSERVED is False
    assert C01_C16_REJECTION_STILL_BINDING is True
    assert C01_C16_REVIVAL_ALLOWED is False
    assert C01_C16_NOT_ELEVATED is True
    assert len(C01_C16_IDS) == 16
    assert C17_CREATED is False
    assert C17_CREATION_FROZEN_UNTIL_D1_D9_PROVEN is True
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert RECONSTRUCTION_ENGINE_CREATED is False
    assert RESTART_PROVEN is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert CHECKPOINT_CAN_MINT_EQUITY is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert dag["EVENT_ACQUISITION_CREATED"] is True
    assert dag["COMPLETE_EVENT_STREAM_PROVEN"] is False
    assert dag["EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED"] is False
    assert dag["RECONSTRUCTION_ENGINE_CREATED"] is False
    assert dag["EARLIEST_OPTION_D_DEPENDENCY"] == (
        "D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION"
    )
    assert EARLIEST_OPTION_D_DEPENDENCY == "D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION"
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "TRUSTED_29P_PRETRADE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_OWNER_GOS"
    )
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()
    for relative in _NEW_CONTRACT_FILES:
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in _FORBIDDEN_ENGINE_MARKERS:
            assert marker not in lowered
        assert "def reconstruct_equity_stock" not in text
        assert "def acquire_events" not in text


def test_runbook_au_consumes_owner_go_without_rewriting_at_or_protected_surfaces() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    au_section = _au_section()
    at_start = runbook.index(AT_HEADING)
    at_section = runbook[at_start : runbook.index(AU_HEADING, at_start)]
    assert "THIS_SLICE=11.2.1.AT" in at_section
    assert "THIS_SLICE=11.2.1.AU" not in at_section
    assert (
        "EARLIEST_OPTION_D_DEPENDENCY=D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION" in at_section
    )
    assert (
        "OWNER_GO=OWNER_GO_OPTION_D_D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION_WORKPACKAGE_V1"
        in au_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in au_section
    assert (
        "THIS_SLICE=11.2.1.AU.FULL_CORE_D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION"
        in au_section
    )
    assert "EVENT_ACQUISITION_CREATED=true" in au_section
    assert "COMPLETE_EVENT_STREAM_PROVEN=false" in au_section
    assert "EVENT_ACQUISITION_RUNTIME_INSTANCE_PRESENT=false" in au_section
    assert "EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED=false" in au_section
    assert "NETWORK_GET_PERFORMED=false" in au_section
    assert "NETWORK_POST_PERFORMED=false" in au_section
    assert "NEW_TRANSPORT_CREATED=false" in au_section
    assert (
        "D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION="
        "TYPED_ACQUISITION_CONTRACT_PRESENT_COMPLETENESS_UNPROVEN" in au_section
    )
    assert (
        "EARLIEST_OPTION_D_DEPENDENCY=D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION" in au_section
    )
    assert "D7_DETERMINISTIC_STOCK_RECONSTRUCTION=NOT_BUILT" in au_section
    assert "CHECKPOINT_CAN_MINT_EQUITY=false" in au_section
    assert "RECONSTRUCTED_EQUITY_CREATED=false" in au_section
    assert "RECONSTRUCTION_ENGINE_CREATED=false" in au_section
    assert "EQ_RECONCILIATION_EXECUTED=false" in au_section
    assert "RAW_EQ_SOURCE_AUTHORITY=false" in au_section
    assert "SOURCE_SELECTED=false" in au_section
    assert "MAPPING_PROVEN=false" in au_section
    assert "C17_CREATED=false" in au_section
    assert "UNCLASSIFIED_EVENT_FAIL_CLOSED=true" in au_section
    assert "ABSENCE_IS_NOT_ZERO_EVENTS=true" in au_section
    assert "EXISTING_AUTHORITY_OWNER_UNCHANGED=true" in au_section
    assert (
        "ACCOUNT_EQUITY_AUTHORITY_OWNER="
        "ops.governed_productive_account_equity_authority_producer_v1" in au_section
    )
    assert "LIVE_ENABLED=false" in au_section
    assert "LIVE_ARMED=false" in au_section
    assert "WIRE_SEND_PERMITTED=false" in au_section
    assert "MASTER_V2_UNCHANGED=true" in au_section
    assert "DOUBLE_PLAY_UNCHANGED=true" in au_section
    assert "BULL_BEAR_STATE_SWITCH_UNCHANGED=true" in au_section
    assert "TOP20_RANKING_UNIVERSE_UNCHANGED=true" in au_section
    assert "EVENT_ACQUISITION_CREATED=true" in spec
    assert "COMPLETE_EVENT_STREAM_PROVEN=false" in spec
    assert "D7_DETERMINISTIC_STOCK_RECONSTRUCTION=NOT_BUILT" in spec
