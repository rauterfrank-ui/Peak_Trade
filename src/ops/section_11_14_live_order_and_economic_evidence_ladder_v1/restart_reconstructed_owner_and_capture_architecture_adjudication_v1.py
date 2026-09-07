"""Architecture adjudication for a first §11.14 Live durable pre-restart handoff owner.

Consumes the architecture/forensic Owner-GO. Does not mint a storage owner.
Does not join a productive writer or reader. Does not prove pos semantics.
Does not invent a complete capture seam. Does not GET. Does not POST.
Does not execute a restart. Does not activate admission or supervisor.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    A1_WAL_AS_LIVE_HANDOFF_ALLOWED,
    FORBIDDEN_OWNER_REUSE,
    FULL_CORE_29P_REQUIRED_FOR_THIS_FIELD,
    HOST_CRASH_DURABILITY_REQUIRED_FOR_THIS_FIELD,
    LIVE_RESTART_RECONSTRUCTED,
    NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
    NO_TIMESTAMP_BACKFILL,
    RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
    SECTION_11_14_IS_NOT_SECOND_PRODUCTIVE_LIVE_AUTHORITY,
    HISTORICAL_HANDOFF_OWNER_BOUND,
    HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
    HISTORICAL_HANDOFF_PRODUCTIVE_BINDING,
    HISTORICAL_HANDOFF_READER_PRESENT,
    HISTORICAL_HANDOFF_WRITER_PRESENT,
    TRACK_1,
    TRACK_2,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    HANDOFF_DOCUMENT_CLASS,
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    BOUND_FILL_SZ,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_census_matrix_v1 import (
    bind_section_11_14_live_handoff_owner_census_matrix_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_vacancy_contract_v1 import (
    OWNER_DOMAIN,
    OWNER_VACANCY_CONTRACT_STATUS,
    PROPOSED_FIRST_OWNER_ID,
    bind_section_11_14_live_handoff_owner_vacancy_contract_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_derivation_refusal_v1 import (
    bind_pos_derivation_adjudication_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_census_v1 import (
    bind_pos_producer_census_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_predicate_v1 import (
    RESTART_FIELD_CONSTITUENTS,
    RESTART_IDENTITY_EQUATION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_required_field_contract_v1 import (
    COMPLETE_CAPTURE_SEAM,
    EARLIEST_COMPLETE_HANDOFF_CAPTURE_MOMENT,
    EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN,
    EARLIEST_COMPLETE_HANDOFF_CAPTURE_SEAM,
    POS_SEMANTICS,
    POST_RESTART_READ_SEAM,
    bind_live_order_timeline_capture_v1,
    bind_required_field_contract_v1,
)

PROPOSED_FIRST_OWNER_ADJUDICATION = "ELIGIBLE_AS_FIRST_LOGICAL_OWNER_ID_NOT_PRODUCTIVELY_BOUND"
FIRST_OWNER_CONTRACT_DECLARED = True
FIRST_OWNER_PRODUCTIVELY_BOUND = False
MINIMAL_SAFE_ARCHITECTURE = "BOUND_FAIL_CLOSED_DEPENDENCY_DAG_POS_AND_SEAM_REMAIN_UNPROVEN"
ARCHITECTURE_ADJUDICATION_COMPLETE = True
IMPLEMENTATION_AUTHORIZED = False
BOUND_POS_FIELD_PRESENT = False
POS_CANONICAL_MEANING = "UNPROVEN"
POS_UNIT = "UNPROVEN"
POS_SIGN_SEMANTICS = "UNPROVEN"
POS_INSTRUMENT_BINDING = "MUST_EQUAL_BOUND_INSTID;UNIT_DIMENSION_UNPROVEN"
STEP_29P_EQUITY_DIMENSION_BINDING_STATUS = "MISSING"
STEP_29P_HANDOFF_RELATION = "ORTHOGONAL_TO_SECTION_11_14_LIVE_CANARY_HANDOFF"
PROPOSED_NEXT_SLICE = "SECTION_11_14_LIVE_HANDOFF_POS_SEMANTICS_CANONICAL_BINDING_V1"
HOST_CRASH_DURABILITY = "UNPROVEN"
POWER_LOSS_DURABILITY = "UNPROVEN"
DURABILITY_PROVEN_EFFECTIVE = False

_REQUIRED_DURABILITY_PRIMITIVES: tuple[str, ...] = (
    "IDENTITY_BOUND_SCHEMA_AND_VERSION",
    "CONTEMPORANEOUS_CAPTURE_TIMESTAMP_NO_BACKFILL",
    "WRITE_ACKNOWLEDGEMENT_BEFORE_CLAIM",
    "TORN_WRITE_AND_CORRUPTION_FAIL_CLOSED",
    "DISTINCT_FROM_VENUE_GET_ACCOUNTING_PATH",
    "NO_SYNTHETIC_RECONSTRUCTION_ON_READ",
    "PROCESS_RESTART_READABLE_HANDOFF_RECORD",
)
_CURRENTLY_PROVEN_PRIMITIVES_FOR_THIS_OWNER: tuple[str, ...] = ()
_NEVER_HEURISTIC_RECOVERY: tuple[str, ...] = (
    "MISSING_HANDOFF",
    "INCOMPLETE_REQUIRED_FIELDS",
    "STALE_OR_WRONG_ATTEMPT_IDENTITY",
    "CORRUPT_OR_TORN_RECORD",
    "SCHEMA_OR_VERSION_MISMATCH",
    "OWNER_MISMATCH",
    "INSTRUMENT_MISMATCH",
    "POS_SEMANTICS_UNPROVEN",
    "VENUE_GET_SUBSTITUTION",
    "FILL_SZ_SUBSTITUTION",
    "SUBMITTED_SZ_SUBSTITUTION",
    "ACCOUNTING_SUBSTITUTION",
    "A1_WAL_SUBSTITUTION",
    "TIMESTAMP_BACKFILL",
    "RETROACTIVE_SYNTHESIS",
    "CONTRADICTORY_IDENTITY",
)


def _seam(
    *,
    seam_id: str,
    location: str,
    upstream_producers: tuple[str, ...],
    available_fields: tuple[str, ...],
    missing_fields: tuple[str, ...],
    before_or_after_mutation: str,
    before_or_after_external_effect: str,
    crash_window: str,
    power_loss_window: str,
    retroactive_synthesis_required: bool,
    acceptable: str,
    reason: str,
) -> dict[str, Any]:
    if acceptable not in {"true", "false", "unproven"}:
        raise Section1114OfflineSurfaceError("SEAM_ACCEPTABLE_VALUE_INVALID")
    if acceptable == "true":
        raise Section1114OfflineSurfaceError("COMPLETE_CAPTURE_SEAM_MUST_NOT_BE_INVENTED")
    return {
        "SEAM_ID": seam_id,
        "LOCATION": location,
        "UPSTREAM_PRODUCERS": list(upstream_producers),
        "AVAILABLE_FIELDS": list(available_fields),
        "MISSING_FIELDS": list(missing_fields),
        "BEFORE_OR_AFTER_MUTATION": before_or_after_mutation,
        "BEFORE_OR_AFTER_EXTERNAL_EFFECT": before_or_after_external_effect,
        "CRASH_WINDOW": crash_window,
        "POWER_LOSS_WINDOW": power_loss_window,
        "RETROACTIVE_SYNTHESIS_REQUIRED": retroactive_synthesis_required,
        "ACCEPTABLE": acceptable,
        "REASON": reason,
    }


def bind_owner_contract_adjudication_v1() -> dict[str, Any]:
    census = bind_section_11_14_live_handoff_owner_census_matrix_v1()
    vacancy = bind_section_11_14_live_handoff_owner_vacancy_contract_v1()
    if census["ALLOWED_HANDOFF_OWNER_COUNT"] != 0:
        raise Section1114OfflineSurfaceError("COMPETING_HANDOFF_OWNER_MUST_REMAIN_ABSENT")
    if HISTORICAL_HANDOFF_OWNER_CURRENT_NONE != "NONE":
        raise Section1114OfflineSurfaceError("CURRENT_OWNER_MUST_REMAIN_NONE")
    if vacancy["PROPOSED_FIRST_OWNER_ID"] != PROPOSED_FIRST_OWNER_ID:
        raise Section1114OfflineSurfaceError("PROPOSED_FIRST_OWNER_ID_DRIFT")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_OWNER_CONTRACT_ADJUDICATION_V1",
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
        "SECTION_11_14_LIVE_HANDOFF_OWNER_BOUND": HISTORICAL_HANDOFF_OWNER_BOUND,
        "PROPOSED_FIRST_OWNER_ID": PROPOSED_FIRST_OWNER_ID,
        "PROPOSED_FIRST_OWNER_ADJUDICATION": PROPOSED_FIRST_OWNER_ADJUDICATION,
        "FIRST_OWNER_CONTRACT_DECLARED": FIRST_OWNER_CONTRACT_DECLARED,
        "FIRST_OWNER_PRODUCTIVELY_BOUND": FIRST_OWNER_PRODUCTIVELY_BOUND,
        "NAME_OR_DECLARATION_IS_NOT_PRODUCTIVE_BIND": True,
        "COMPETING_PRODUCTIVE_OWNER_COUNT": census["ALLOWED_HANDOFF_OWNER_COUNT"],
        "FORBIDDEN_OWNER_REUSE": list(FORBIDDEN_OWNER_REUSE),
        "OWNER_DOMAIN": OWNER_DOMAIN,
        "RESPONSIBILITY_BOUNDARY": (
            "Own contemporaneous Peak_Trade capture and storage of the identity-"
            "bound durable pre-restart handoff {clOrdId, ordId, instId, posSide, pos} "
            "distinct from venue-GET/accounting/fill/fee artifacts. Not transport, "
            "strategy, venue, supervisor, admission, or accounting ownership."
        ),
        "LIFECYCLE": (
            "Owner ID is durable and permanent. Records are bound Live "
            "submit/attempt/session specific. Restart does not mint a second owner."
        ),
        "EVIDENCE_OWNERSHIP": HANDOFF_DOCUMENT_CLASS,
        "ALLOWED_PRODUCERS": [],
        "ALLOWED_CONSUMERS": [POST_RESTART_READ_SEAM],
        "OWNER_IDENTITY_PERMANENCE": "DURABLE_OWNER_ID;ATTEMPT_SPECIFIC_RECORDS",
        "DATA_NOT_OWNED": list(vacancy["FORBIDDEN_INPUT_SOURCE_KINDS"]),
        "NEW_OWNER_REQUIRED": True,
        "OWNER_VACANCY_CONTRACT_STATUS": OWNER_VACANCY_CONTRACT_STATUS,
        "STORAGE_OWNER_MINTED": False,
        "WRITER_BOUND": False,
        "READER_BOUND": False,
        "CAPTURE_SEAM_BOUND": False,
        "PRODUCTIVE_BINDING_PRESENT": HISTORICAL_HANDOFF_PRODUCTIVE_BINDING,
        "PRODUCTIVE_WRITER_PRESENT": HISTORICAL_HANDOFF_WRITER_PRESENT,
        "PRODUCTIVE_READER_PRESENT": HISTORICAL_HANDOFF_READER_PRESENT,
        "WRITE_PRECONDITIONS": vacancy["WRITE_PRECONDITIONS"],
        "LIVE_SCOPED_IDENTITY_BOUND_CONTEMPORANEOUS_HANDOFF_OWNER_FOUND": census[
            "LIVE_SCOPED_IDENTITY_BOUND_CONTEMPORANEOUS_HANDOFF_OWNER_FOUND"
        ],
    }


def bind_pos_semantics_adjudication_v1() -> dict[str, Any]:
    producers = bind_pos_producer_census_v1()
    derivations = bind_pos_derivation_adjudication_v1()
    field_contract = bind_required_field_contract_v1()
    if producers["POS_ACCEPTABLE_PRODUCER_COUNT"] != 0:
        raise Section1114OfflineSurfaceError("POS_ACCEPTABLE_PRODUCER_COUNT_MUST_REMAIN_ZERO")
    if POS_SEMANTICS != "UNPROVEN":
        raise Section1114OfflineSurfaceError("POS_SEMANTICS_MUST_REMAIN_UNPROVEN")
    rejected = [
        {
            "PRODUCER_ID": row["PRODUCER_ID"],
            "PATH": row["PATH"],
            "VALUE_SEMANTICS": row["VALUE_SEMANTICS"],
            "REASON": row["WHY"],
            "DISPOSITION": row["DISPOSITION"],
        }
        for row in producers["rows"]
        if row["DISPOSITION"] != "POS_DERIVATION_UNPROVEN"
    ]
    unproven = [
        {
            "PRODUCER_ID": row["PRODUCER_ID"],
            "PATH": row["PATH"],
            "VALUE_SEMANTICS": row["VALUE_SEMANTICS"],
            "REASON": row["WHY"],
            "DISPOSITION": row["DISPOSITION"],
        }
        for row in producers["rows"]
        if row["DISPOSITION"] == "POS_DERIVATION_UNPROVEN"
    ]
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_POS_SEMANTICS_ARCHITECTURE_ADJUDICATION_V1",
        "POS_SEMANTICS_STATUS": POS_SEMANTICS,
        "POS_SEMANTICS": POS_SEMANTICS,
        "POS_CANONICAL_MEANING": POS_CANONICAL_MEANING,
        "POS_UNIT": POS_UNIT,
        "POS_SIGN_SEMANTICS": POS_SIGN_SEMANTICS,
        "POS_INSTRUMENT_BINDING": POS_INSTRUMENT_BINDING,
        "POS_TYPE": field_contract["POS_TYPE"],
        "POS_ACCEPTABLE_PRODUCER_COUNT": producers["POS_ACCEPTABLE_PRODUCER_COUNT"],
        "POS_ACCEPTABLE_PRODUCERS": [],
        "POS_REJECTED_PRODUCERS_WITH_REASON": rejected,
        "POS_UNPROVEN_PRODUCERS_WITH_REASON": unproven,
        "BOUND_POS_FIELD_PRESENT": BOUND_POS_FIELD_PRESENT,
        "BOUND_IDENTITY_HAS_FILL_SZ_NOT_POS": True,
        "BOUND_FILL_SZ": BOUND_FILL_SZ,
        "POS_EQUALS_BOUND_FILL_SZ_IS_LIVE_POSITION_RECONCILED_ONLY": True,
        "VENUE_RAW_POS_IS_NOT_THIS_HANDOFF_FIELD": True,
        "SIGNED_POSITION_UNPROVEN": True,
        "ABSOLUTE_QUANTITY_UNPROVEN": True,
        "CONTRACT_COUNT_UNPROVEN": True,
        "NORMALIZED_BASE_QUANTITY_UNPROVEN": True,
        "NET_MODE_SEMANTICS_UNPROVEN_FOR_HANDOFF_POS": True,
        "POSSIDE_NET_IS_BOUND_FILL_IDENTITY_NOT_HANDOFF_POS": True,
        "SETTLEMENT_UNIT_DIMENSION_UNPROVEN": True,
        "RESTART_IDENTITY_EQUATION": RESTART_IDENTITY_EQUATION,
        "NO_UNIQUE_CANONICAL_MEANING_FROM_AUTHORITY": True,
        "NORMALIZATION_FROM_PLAUSIBILITY_FORBIDDEN": True,
        "derivation_adjudication": {
            "ALLOWED_COUNT": derivations["ALLOWED_COUNT"],
            "REJECTED_COUNT": derivations["REJECTED_COUNT"],
            "UNPROVEN_COUNT": derivations["UNPROVEN_COUNT"],
        },
    }


def bind_capture_seam_graph_census_v1() -> dict[str, Any]:
    timeline = bind_live_order_timeline_capture_v1()
    required = list(REQUIRED_HANDOFF_FIELDS)
    seams = (
        _seam(
            seam_id="S01_CANARY_ORDER_PLAN",
            location=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"),
            upstream_producers=("LiveCanaryOrderPlanV1",),
            available_fields=("clOrdId", "instId"),
            missing_fields=("ordId", "posSide", "pos"),
            before_or_after_mutation="BEFORE",
            before_or_after_external_effect="BEFORE",
            crash_window="in-memory plan lost; no durable handoff writer",
            power_loss_window="in-memory plan lost; no durable handoff writer",
            retroactive_synthesis_required=True,
            acceptable="false",
            reason="Plan sz is not handoff pos. posSide omitted. ordId absent.",
        ),
        _seam(
            seam_id="S02_PRE_SUBMIT_GATES",
            location=(
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
                "submit_gates_v1.py::evaluate_canary_submit_gates_v1"
            ),
            upstream_producers=("order_plan_v1", "refuse_submit_unless_gates_pass_v1"),
            available_fields=("clOrdId", "instId"),
            missing_fields=("ordId", "posSide", "pos"),
            before_or_after_mutation="BEFORE",
            before_or_after_external_effect="BEFORE",
            crash_window="gate evaluation is ephemeral",
            power_loss_window="gate evaluation is ephemeral",
            retroactive_synthesis_required=True,
            acceptable="false",
            reason="Pre-submit gates do not produce ordId, posSide, or pos.",
        ),
        _seam(
            seam_id="S03_WIRE_SEND",
            location=(
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
                "submit_transport_v1.py::run_canary_submit_transport_v1 / "
                "UrllibLiveCanaryTransportV1.send"
            ),
            upstream_producers=("LiveCanaryHttpClientV1.post_entry_order",),
            available_fields=("clOrdId", "instId"),
            missing_fields=("ordId", "posSide", "pos"),
            before_or_after_mutation="AT_MUTATION",
            before_or_after_external_effect="AT_EXTERNAL_EFFECT",
            crash_window="unknown-submit window; joining would touch Live transport",
            power_loss_window="unknown-submit window; joining would touch Live transport",
            retroactive_synthesis_required=True,
            acceptable="false",
            reason="Request sz is not pos. posSide omitted. ordId absent. Live-transport join forbidden here.",
        ),
        _seam(
            seam_id="S04_HTTP_ACK_PARSE",
            location=(
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
                "http_client_v1.py::OKX_ORDER_DATA_ENTRY_FIELDS_V1"
            ),
            upstream_producers=("synchronous venue ACK data-entry allowlist",),
            available_fields=("clOrdId", "ordId"),
            missing_fields=("posSide", "pos"),
            before_or_after_mutation="AFTER",
            before_or_after_external_effect="AFTER",
            crash_window="ACK in memory only; no Live durable_state writer",
            power_loss_window="ACK in memory only; no Live durable_state writer",
            retroactive_synthesis_required=True,
            acceptable="false",
            reason="Allowlist is sCode,sMsg,ordId,clOrdId,tag. pos and posSide omitted. instId is request-owned, not ACK data.",
        ),
        _seam(
            seam_id="S05_CANARY_ACK_RETURN",
            location=(
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
                "submit_transport_v1.py::_entry_submit_returned_payload_v1"
            ),
            upstream_producers=("S04_HTTP_ACK_PARSE", "S01_CANARY_ORDER_PLAN"),
            available_fields=("clOrdId", "ordId", "instId"),
            missing_fields=("posSide", "pos"),
            before_or_after_mutation="AFTER",
            before_or_after_external_effect="AFTER",
            crash_window="return payload is process-local; CONTEMPORANEOUS_PERSIST_RELIABLE=false",
            power_loss_window="return payload is process-local; CONTEMPORANEOUS_PERSIST_RELIABLE=false",
            retroactive_synthesis_required=True,
            acceptable="false",
            reason="PRE_RESTART_CAPTURE_SEAM is partial identity only. Complete identity including pos is unproven.",
        ),
        _seam(
            seam_id="S06_FILL_GET",
            location=(
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
                "fill_observed_predicate_v1.py"
            ),
            upstream_producers=("GOVERNED_CURRENT_PRIVATE_GET fills",),
            available_fields=("clOrdId", "ordId", "instId", "posSide"),
            missing_fields=("pos",),
            before_or_after_mutation="AFTER",
            before_or_after_external_effect="AFTER",
            crash_window="venue GET artifact; not Peak_Trade contemporaneous handoff",
            power_loss_window="venue GET artifact; not Peak_Trade contemporaneous handoff",
            retroactive_synthesis_required=True,
            acceptable="false",
            reason="fillSz is not position proof. Venue GET is not contemporaneous Peak_Trade handoff.",
        ),
        _seam(
            seam_id="S07_POSITION_GET",
            location=(
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
                "position_reconciled_predicate_v1.py::ADMISSIBLE_POS_FIELD"
            ),
            upstream_producers=("GET /api/v5/account/positions",),
            available_fields=("instId", "posSide"),
            missing_fields=("clOrdId", "ordId", "pos"),
            before_or_after_mutation="AFTER",
            before_or_after_external_effect="AFTER",
            crash_window="venue-owned position row; Peak_Trade ownership false",
            power_loss_window="venue-owned position row; Peak_Trade ownership false",
            retroactive_synthesis_required=True,
            acceptable="false",
            reason="Venue-native pos is LIVE_POSITION_RECONCILED, not handoff pos.",
        ),
        _seam(
            seam_id="S08_ACCOUNTING_RECONSTRUCTION",
            location=(
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
                "accounting_reconstructed_adjudication_v1.py"
            ),
            upstream_producers=("S06_FILL_GET", "S07_POSITION_GET"),
            available_fields=("clOrdId", "ordId", "instId", "posSide"),
            missing_fields=("pos",),
            before_or_after_mutation="AFTER",
            before_or_after_external_effect="AFTER",
            crash_window="accounting path is predecessor, not restart handoff",
            power_loss_window="accounting path is predecessor, not restart handoff",
            retroactive_synthesis_required=True,
            acceptable="false",
            reason="ACCOUNTING_ONLY_IS_NOT_RESTART.",
        ),
        _seam(
            seam_id="S09_EVIDENCE_PACK_PERSIST",
            location=(
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/persist_v1.py"
            ),
            upstream_producers=("SECTION_11_14_EVIDENCE_PACKS",),
            available_fields=(),
            missing_fields=tuple(required),
            before_or_after_mutation="AFTER",
            before_or_after_external_effect="AFTER",
            crash_window="forensic pack is not control-state durability",
            power_loss_window="forensic pack is not control-state durability",
            retroactive_synthesis_required=True,
            acceptable="false",
            reason="Evidence packs must not be reclassified as control handoff.",
        ),
        _seam(
            seam_id="S10_DDO_LEDGER",
            location="src/learning/deterministic_decision_outcome_v0/",
            upstream_producers=("DDO_DURABLE_EVIDENCE_STORAGE_OWNER",),
            available_fields=(),
            missing_fields=tuple(required),
            before_or_after_mutation="NOT_THIS_PATH",
            before_or_after_external_effect="NOT_THIS_PATH",
            crash_window="observation ledger only; forbidden owner reuse",
            power_loss_window="observation ledger only; forbidden owner reuse",
            retroactive_synthesis_required=True,
            acceptable="false",
            reason="FORBIDDEN_OWNER_REUSE DDO_DURABLE_EVIDENCE_STORAGE_OWNER.",
        ),
        _seam(
            seam_id="S11_A1_WAL",
            location="src/learning/mutation_critical_control_state_storage_v1/wal_adapter_v1.py",
            upstream_producers=("MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER",),
            available_fields=(),
            missing_fields=tuple(required),
            before_or_after_mutation="NOT_THIS_PATH",
            before_or_after_external_effect="NOT_THIS_PATH",
            crash_window="A1 host-crash remains UNPROVEN and is not this owner",
            power_loss_window="A1 power-loss remains UNPROVEN and is not this owner",
            retroactive_synthesis_required=True,
            acceptable="false",
            reason="A1_WAL_AS_LIVE_HANDOFF_ALLOWED=false. Process-kill proof is not inherited.",
        ),
        _seam(
            seam_id="S12_FILEGATE",
            location="src/risk_layer/kill_switch/persistence.py",
            upstream_producers=("FILEGATE_KILL_SWITCH",),
            available_fields=(),
            missing_fields=tuple(required),
            before_or_after_mutation="NOT_THIS_PATH",
            before_or_after_external_effect="NOT_THIS_PATH",
            crash_window="safety-gate state is not Live handoff",
            power_loss_window="safety-gate state is not Live handoff",
            retroactive_synthesis_required=True,
            acceptable="false",
            reason="FILEGATE is safety-gate persistence, not Live pre-restart handoff.",
        ),
        _seam(
            seam_id="S13_CAP72_SIDESTATE",
            location=(
                "src/ops/wallclock_full_canonical_decision_to_simulated_economics_"
                "runtime_bridge_v1/sidestate_restore_v1.py"
            ),
            upstream_producers=("CAP_72_SIDESTATE_PERSIST",),
            available_fields=(),
            missing_fields=tuple(required),
            before_or_after_mutation="NOT_THIS_PATH",
            before_or_after_external_effect="NOT_THIS_PATH",
            crash_window="strategy lifecycle, not Live submit-identity handoff",
            power_loss_window="strategy lifecycle, not Live submit-identity handoff",
            retroactive_synthesis_required=True,
            acceptable="false",
            reason="Cap 7.2 SideState is not the Live handoff owner.",
        ),
        _seam(
            seam_id="S14_TESTNET_DURABLE_STATE",
            location="evidence/ops/section_11_12_testnet_restart_proven_v1/",
            upstream_producers=("TESTNET_CAMPAIGN_DURABLE_STATE",),
            available_fields=(),
            missing_fields=tuple(required),
            before_or_after_mutation="NOT_THIS_PATH",
            before_or_after_external_effect="NOT_THIS_PATH",
            crash_window="Testnet restart is not this Live field",
            power_loss_window="Testnet restart is not this Live field",
            retroactive_synthesis_required=True,
            acceptable="false",
            reason="No Testnet, fixture or simulated result may satisfy a Live evidence field.",
        ),
        _seam(
            seam_id="S15_SUPERVISOR",
            location="NONE_FOR_SECTION_11_14_LIVE_HANDOFF",
            upstream_producers=(),
            available_fields=(),
            missing_fields=tuple(required),
            before_or_after_mutation="NOT_THIS_PATH",
            before_or_after_external_effect="NOT_THIS_PATH",
            crash_window="supervisor not activated; no handoff capture join",
            power_loss_window="supervisor not activated; no handoff capture join",
            retroactive_synthesis_required=True,
            acceptable="false",
            reason="SUPERVISOR_ACTIVATED=false. No productive supervisor capture seam exists.",
        ),
        _seam(
            seam_id="S16_HOST_PROCESS_SUPERVISION",
            location="src/ops/canonical_local_launcher_and_process_supervision_v1/",
            upstream_producers=("single_writer_v1",),
            available_fields=(),
            missing_fields=tuple(required),
            before_or_after_mutation="NOT_THIS_PATH",
            before_or_after_external_effect="NOT_THIS_PATH",
            crash_window="launcher/single-writer is not Live identity-bound handoff",
            power_loss_window="launcher/single-writer is not Live identity-bound handoff",
            retroactive_synthesis_required=True,
            acceptable="false",
            reason="Process supervision is not the Peak_Trade Live pre-restart handoff owner.",
        ),
    )
    acceptable_true = [row for row in seams if row["ACCEPTABLE"] == "true"]
    if acceptable_true:
        raise Section1114OfflineSurfaceError("COMPLETE_CAPTURE_SEAM_MUST_NOT_BE_INVENTED")
    if EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN is True:
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_MUST_REMAIN_UNPROVEN")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_CAPTURE_SEAM_GRAPH_CENSUS_V1",
        "seams": [dict(row) for row in seams],
        "SEAM_CANDIDATE_COUNT": len(seams),
        "ACCEPTABLE_COMPLETE_SEAM_COUNT": 0,
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_MOMENT": EARLIEST_COMPLETE_HANDOFF_CAPTURE_MOMENT,
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_SEAM": EARLIEST_COMPLETE_HANDOFF_CAPTURE_SEAM,
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN": EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN,
        "COMPLETE_CAPTURE_SEAM": COMPLETE_CAPTURE_SEAM,
        "NO_INVENTED_SEAM": True,
        "NO_MOMENT_HAS_ALL_FIVE_PEAK_TRADE_OWNED_CONTEMPORANEOUS_FIELDS": True,
        "T4_ACK_MISSING_POSSIDE_AND_POS": True,
        "T6_FILL_POS_SIDE_IS_VENUE_OWNED": True,
        "POST_HOC_ASSEMBLY_ACROSS_MOMENTS_IS_RETROACTIVE_SYNTHESIS": True,
        "timeline": {
            "PRE_RESTART_CAPTURE_SEAM": timeline["PRE_RESTART_CAPTURE_SEAM"],
            "POST_RESTART_READ_SEAM": timeline["POST_RESTART_READ_SEAM"],
            "CANARY_ACK_OMITS_POS": timeline["CANARY_ACK_OMITS_POS"],
            "CANARY_ACK_OMITS_POSSIDE": timeline["CANARY_ACK_OMITS_POSSIDE"],
        },
    }


def bind_durability_contract_adjudication_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_DURABILITY_CONTRACT_ADJUDICATION_V1",
        "HOST_CRASH_DURABILITY": HOST_CRASH_DURABILITY,
        "POWER_LOSS_DURABILITY": POWER_LOSS_DURABILITY,
        "DURABILITY_PROVEN_EFFECTIVE": DURABILITY_PROVEN_EFFECTIVE,
        "HOST_CRASH_DURABILITY_REQUIRED_FOR_THIS_FIELD": (
            HOST_CRASH_DURABILITY_REQUIRED_FOR_THIS_FIELD
        ),
        "A1_WAL_AS_LIVE_HANDOFF_ALLOWED": A1_WAL_AS_LIVE_HANDOFF_ALLOWED,
        "REQUIRED_DURABILITY_PRIMITIVES": list(_REQUIRED_DURABILITY_PRIMITIVES),
        "CURRENTLY_PROVEN_PRIMITIVES": list(_CURRENTLY_PROVEN_PRIMITIVES_FOR_THIS_OWNER),
        "MISSING_PRIMITIVES": list(_REQUIRED_DURABILITY_PRIMITIVES),
        "API_OR_FUNCTION_NAME_IS_NOT_DURABILITY_PROOF": True,
        "A1_PROCESS_KILL_PROOF_IS_NOT_INHERITED": True,
        "A1_ATOMIC_REPLACE_PROVEN": False,
        "A1_HOST_CRASH_PROVEN": False,
        "A1_POWER_LOSS_PROVEN": False,
        "A1_DIRECTORY_ENTRY_DURABILITY_PROVEN": False,
        "FIELD_DOES_NOT_REQUIRE_HOST_CRASH_TO_BECOME_TRUE": True,
        "OWNER_NAME_DURABLE_DOES_NOT_PROVE_HOST_CRASH": True,
        "ACKNOWLEDGEMENT_POINT": "UNPROVEN_NO_WRITER",
        "READ_AFTER_WRITE": "UNPROVEN_NO_WRITER",
        "ATOMIC_REPLACE": "UNPROVEN_NO_WRITER",
        "FSYNC_FILE": "UNPROVEN_NO_WRITER",
        "FSYNC_DIRECTORY": "UNPROVEN_NO_WRITER",
        "TEMP_FILE_RENAME": "UNPROVEN_NO_WRITER",
        "CORRUPTION_TRUNCATION_HANDLING": "UNPROVEN_NO_WRITER",
        "VERSION_SCHEMA_IDENTITY": "SCHEMA_NAMED_NOT_PRODUCTIVELY_BOUND",
        "ATTEMPT_SESSION_IDENTITY": "REQUIRED_NOT_PRODUCTIVELY_BOUND",
        "DUPLICATE_STALE_HANDLING": "FAIL_CLOSED_REQUIRED_NOT_BOUND",
    }


def bind_writer_reader_contract_adjudication_v1() -> dict[str, Any]:
    vacancy = bind_section_11_14_live_handoff_owner_vacancy_contract_v1()
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_WRITER_READER_CONTRACT_ADJUDICATION_V1",
        "WRITER_BOUND": False,
        "READER_BOUND": False,
        "writer": {
            "INPUTS": list(REQUIRED_HANDOFF_FIELDS)
            + ["provenance_class", "owner_id", "schema_version", "attempt_identity"],
            "VALIDATION": vacancy["VALIDATION_RULES"],
            "IDENTITY": (
                "Bound Live submit/fill/position identity; owner_id must equal "
                "the later minted first owner, not NONE and not forbidden reuse."
            ),
            "EXACT_WRITE_POINT": "UNPROVEN_COMPLETE_CAPTURE_SEAM_REQUIRED_FIRST",
            "DURABILITY_ACKNOWLEDGEMENT": "REQUIRED_BEFORE_CLAIM_WRITTEN;CURRENTLY_ABSENT",
            "FAILURE_BEHAVIOR": "FAIL_CLOSED_NO_PARTIAL_VISIBLE_HANDOFF",
            "DUPLICATE_RETRY_BEHAVIOR": "IDEMPOTENT_REJECT_OR_EXACT_SAME_RECORD;NO_SECOND_IDENTITY",
            "PROHIBITION_OF_SYNTHETIC_RECONSTRUCTION": True,
            "WRITE_PRECONDITIONS": vacancy["WRITE_PRECONDITIONS"],
        },
        "reader": {
            "STARTUP_RESTART_POINT": POST_RESTART_READ_SEAM,
            "EXACT_ELIGIBLE_RECORDS": (
                "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF with contemporaneous "
                "provenance and complete required fields"
            ),
            "SCHEMA_VERSION_VALIDATION": "REQUIRED_FAIL_CLOSED",
            "FRESHNESS_SESSION_ATTEMPT_VALIDATION": "REQUIRED_FAIL_CLOSED",
            "CORRUPT_INCOMPLETE_STALE_HANDLING": "FAIL_CLOSED",
            "MISSING_EVIDENCE_HANDLING": "FAIL_CLOSED",
            "MULTIPLE_RECORD_HANDLING": "FAIL_CLOSED_UNLESS_EXACT_SAME_IDENTITY",
            "FAIL_CLOSED_BEHAVIOR": True,
        },
        "NEVER_HEURISTIC_RECOVERY": list(_NEVER_HEURISTIC_RECOVERY),
        "PRODUCTIVE_WRITER_JOIN_CREATED": False,
        "PRODUCTIVE_READER_JOIN_CREATED": False,
        "LATER_WRITER_CLAIMED_POSSIBLE": False,
    }


def bind_restart_admission_predicate_v1() -> dict[str, Any]:
    conjuncts = {
        "LIVE_ACCOUNTING_RECONSTRUCTED": True,
        "owner_bound": HISTORICAL_HANDOFF_OWNER_BOUND,
        "capture_seam_bound": EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN,
        "complete_required_fields": False,
        "provenance_valid": False,
        "durability_ack_present": False,
        "pos_semantics_proven": POS_SEMANTICS != "UNPROVEN",
        "pos_acceptable_producer_present": False,
        "DURABLE_PRE_RESTART_HANDOFF_PRESENT": False,
        "HANDOFF_DISTINCT_FROM_ACCOUNTING_VENUE_GET_PATH": False,
        "POST_RESTART_IDENTITY_RECONSTRUCTABLE": False,
        "IDENTITY_BOUND_HANDOFF_MATCHES_LIVE_SUBMIT": False,
        "NO_RESUBMIT": True,
        "NO_SILENT_REINITIALIZATION": True,
        "ADMISSIBLE_PERSISTED_LIVE_RESTART_HANDOFF_SOURCE": False,
        "NOT_FIXTURE_TESTNET_OR_SIMULATED": True,
        "ACCOUNTING_CLOSURE_IS_NOT_RESTART": True,
        "owner_match": False,
        "schema_version_match": False,
        "instrument_match": False,
        "session_attempt_match": False,
        "no_contradiction": True,
        "no_retroactive_synthesis": not RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
        "no_timestamp_backfill": NO_TIMESTAMP_BACKFILL,
        "no_synthetic_pre_restart_provenance": NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
    }
    false_required = [name for name, value in conjuncts.items() if value is not True]
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_RESTART_ADMISSION_PREDICATE_V1",
        "PREDICATE_NAME": "RESTART_HANDOFF_ELIGIBLE",
        "RESTART_FIELD_CONSTITUENTS": list(RESTART_FIELD_CONSTITUENTS),
        "conjuncts": conjuncts,
        "false_required": false_required,
        "RESTART_HANDOFF_ELIGIBLE": False,
        "ADMISSION_TRUE": False,
        "SUPERVISOR_ACTIVATED": False,
        "LIVE_RESTART_RECONSTRUCTED": LIVE_RESTART_RECONSTRUCTED,
        "MISSING_DATA_BEHAVIOR": "FAIL_CLOSED",
        "STALE_DATA_BEHAVIOR": "FAIL_CLOSED",
        "CONTRADICTION_BEHAVIOR": "FAIL_CLOSED",
        "HEURISTIC_RECOVERY_FORBIDDEN": list(_NEVER_HEURISTIC_RECOVERY),
        "THIS_PREDICATE_IS_NOT_FULL_CORE_LIVE_ENABLED_ADMISSION": True,
        "THIS_PREDICATE_DOES_NOT_AUTHORIZE_RESTART_EXECUTION": True,
    }


def bind_step_29p_handoff_relation_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_STEP_29P_HANDOFF_RELATION_ADJUDICATION_V1",
        "STEP_29P_EQUITY_DIMENSION_BINDING_STATUS": STEP_29P_EQUITY_DIMENSION_BINDING_STATUS,
        "STEP_29P_HANDOFF_RELATION": STEP_29P_HANDOFF_RELATION,
        "FULL_CORE_29P_REQUIRED_FOR_THIS_FIELD": FULL_CORE_29P_REQUIRED_FOR_THIS_FIELD,
        "TRACK_1": TRACK_1,
        "TRACK_2": TRACK_2,
        "SECTION_11_14_IS_NOT_SECOND_PRODUCTIVE_LIVE_AUTHORITY": (
            SECTION_11_14_IS_NOT_SECOND_PRODUCTIVE_LIVE_AUTHORITY
        ),
        "REQUIRED_FOR_HANDOFF_OWNER": False,
        "REQUIRED_FOR_CAPTURE_SEAM": False,
        "REQUIRED_FOR_WRITER": False,
        "REQUIRED_FOR_READER": False,
        "REQUIRED_FOR_RESTART_RECONSTRUCTION_OF_THIS_FIELD": False,
        "DOWNSTREAM_ONLY_FOR_THIS_FIELD": False,
        "ORTHOGONAL_TO_THIS_FIELD": True,
        "REMAINS_FULL_CORE_TRACK_2_DEPENDENCY": True,
        "NO_IMPLICIT_COUPLING_CREATED": True,
    }


def bind_proposed_slice_sequence_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_ARCHITECTURE_SLICE_SEQUENCE_V1",
        "SEQUENCE_AUTO_EXECUTED": False,
        "IMPLEMENTATION_AUTHORIZED": IMPLEMENTATION_AUTHORIZED,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "WHY_THIS_IS_EARLIEST": (
            "No acceptable pos producer exists and authority does not uniquely "
            "define handoff pos. A complete capture seam cannot be proven until "
            "pos meaning is uniquely bound. Owner mint, writer, reader, and "
            "restart admission all fail closed while POS_SEMANTICS=UNPROVEN."
        ),
        "PRECONDITIONS": (
            "Architecture adjudication consumed; POS_SEMANTICS remains UNPROVEN; "
            "no rejected derivation A-I reused; no venue GET/fillSz/sz substitution; "
            "no writer/reader/storage mint; no Live/Testnet/wire."
        ),
        "ALLOWED_PATHS_OR_SURFACES": (
            "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md §11.14; "
            "docs/ops/specs/; src/ops/section_11_14_live_order_and_economic_"
            "evidence_ladder_v1/; tests/ops/test_section_11_14_*"
        ),
        "FORBIDDEN_SURFACES": (
            "src/execution/**; credentials; Live/Testnet transport; supervisor; "
            "admission; A1 WAL reuse; DDO reuse; productive host binding; "
            "canary submit_transport join; Full-Core 29P runtime; Master V2; "
            "Double Play"
        ),
        "SUCCESS_CRITERIA": (
            "POS_SEMANTICS uniquely bound from remaining non-rejected authority, "
            "or explicit fail-closed that no remaining definition exists without "
            "a new Peak_Trade contemporaneous producer. POS_ACCEPTABLE_PRODUCER_COUNT "
            "may remain 0. LIVE_RESTART_RECONSTRUCTED remains false."
        ),
        "FAIL_CLOSED_CRITERIA": (
            "Any promotion of rejected derivations A-I; any BOUND_POS invented "
            "from fillSz or venue GET; any writer join; any capture-seam invention."
        ),
        "CLAIMS_NOT_GRANTED": (
            "FIRST_OWNER_PRODUCTIVELY_BOUND; WRITER_BOUND; READER_BOUND; "
            "CAPTURE_SEAM_BOUND; POS_SEMANTICS!=UNPROVEN unless that later GO "
            "uniquely binds it; ADMISSION_TRUE; LIVE_RESTART_RECONSTRUCTED; "
            "OWNER_MERGE_GO"
        ),
        "slices": (
            {
                "SLICE_ID": "SLICE_1",
                "SLICE": PROPOSED_NEXT_SLICE,
                "SLICE_1_PRECONDITIONS": "This architecture adjudication consumed; owner remains NONE.",
                "SLICE_1_CLOSES": "POS_SEMANTICS uniquely bound or explicit remaining-gap bind; still no writer.",
            },
            {
                "SLICE_ID": "SLICE_2",
                "SLICE": "SECTION_11_14_LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_PROOF_V1",
                "SLICE_2_PRECONDITIONS": "POS_SEMANTICS proven and not a rejected derivation.",
                "SLICE_2_CLOSES": "COMPLETE_CAPTURE_SEAM proven or remains UNPROVEN/absent without invention.",
            },
            {
                "SLICE_ID": "SLICE_3",
                "SLICE": "SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_MINT_V1",
                "SLICE_3_PRECONDITIONS": "POS_SEMANTICS proven AND complete capture seam proven.",
                "SLICE_3_CLOSES": "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT becomes the first owner ID without writer join unless that later GO also authorizes writer.",
            },
            {
                "SLICE_ID": "SLICE_4",
                "SLICE": "SECTION_11_14_LIVE_HANDOFF_WRITER_READER_PRODUCTIVE_BIND_V1",
                "SLICE_4_PRECONDITIONS": "Owner minted; seam proven; pos proven; separate explicit Owner-GO.",
                "SLICE_4_CLOSES": "Writer/reader contracts productively bound; still no restart execution.",
            },
            {
                "SLICE_ID": "SLICE_5",
                "SLICE": "SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_FROM_CONTEMPORANEOUS_HANDOFF_V1",
                "SLICE_5_PRECONDITIONS": "Durable contemporaneous handoff present; RESTART_HANDOFF_ELIGIBLE true.",
                "SLICE_5_CLOSES": "LIVE_RESTART_RECONSTRUCTED adjudication from GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF.",
            },
        ),
    }


def bind_owner_and_capture_architecture_adjudication_v1() -> dict[str, Any]:
    owner = bind_owner_contract_adjudication_v1()
    pos = bind_pos_semantics_adjudication_v1()
    seams = bind_capture_seam_graph_census_v1()
    durability = bind_durability_contract_adjudication_v1()
    writer_reader = bind_writer_reader_contract_adjudication_v1()
    admission = bind_restart_admission_predicate_v1()
    step_29p = bind_step_29p_handoff_relation_v1()
    sequence = bind_proposed_slice_sequence_v1()
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if admission["ADMISSION_TRUE"] is True:
        raise Section1114OfflineSurfaceError("ADMISSION_TRUE_MUST_REMAIN_FALSE")
    if IMPLEMENTATION_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("IMPLEMENTATION_MUST_REMAIN_UNAUTHORIZED")
    return {
        "DOCUMENT_CLASS": (
            "SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_AND_CAPTURE_"
            "ARCHITECTURE_ADJUDICATION_V1"
        ),
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT_ARCHITECTURE_ADJUDICATION_NOT_OWNER_MINT",
        "ARCHITECTURE_ADJUDICATION_COMPLETE": ARCHITECTURE_ADJUDICATION_COMPLETE,
        "IMPLEMENTATION_AUTHORIZED": IMPLEMENTATION_AUTHORIZED,
        "MINIMAL_SAFE_ARCHITECTURE": MINIMAL_SAFE_ARCHITECTURE,
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": owner[
            "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT"
        ],
        "PROPOSED_FIRST_OWNER_ID": owner["PROPOSED_FIRST_OWNER_ID"],
        "PROPOSED_FIRST_OWNER_ADJUDICATION": owner["PROPOSED_FIRST_OWNER_ADJUDICATION"],
        "FIRST_OWNER_CONTRACT_DECLARED": owner["FIRST_OWNER_CONTRACT_DECLARED"],
        "FIRST_OWNER_PRODUCTIVELY_BOUND": owner["FIRST_OWNER_PRODUCTIVELY_BOUND"],
        "POS_SEMANTICS": pos["POS_SEMANTICS"],
        "POS_ACCEPTABLE_PRODUCER_COUNT": pos["POS_ACCEPTABLE_PRODUCER_COUNT"],
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_MOMENT": seams[
            "EARLIEST_COMPLETE_HANDOFF_CAPTURE_MOMENT"
        ],
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_SEAM": seams["EARLIEST_COMPLETE_HANDOFF_CAPTURE_SEAM"],
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN": seams[
            "EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN"
        ],
        "COMPLETE_CAPTURE_SEAM": seams["COMPLETE_CAPTURE_SEAM"],
        "HOST_CRASH_DURABILITY": durability["HOST_CRASH_DURABILITY"],
        "POWER_LOSS_DURABILITY": durability["POWER_LOSS_DURABILITY"],
        "DURABILITY_PROVEN_EFFECTIVE": durability["DURABILITY_PROVEN_EFFECTIVE"],
        "STORAGE_OWNER_MINTED": False,
        "WRITER_BOUND": False,
        "READER_BOUND": False,
        "CAPTURE_SEAM_BOUND": False,
        "PRODUCTIVE_BINDING_PRESENT": False,
        "LIVE_RESTART_RECONSTRUCTED": LIVE_RESTART_RECONSTRUCTED,
        "STEP_29P_EQUITY_DIMENSION_BINDING_STATUS": step_29p[
            "STEP_29P_EQUITY_DIMENSION_BINDING_STATUS"
        ],
        "STEP_29P_HANDOFF_RELATION": step_29p["STEP_29P_HANDOFF_RELATION"],
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
        "NO_TIMESTAMP_BACKFILL": NO_TIMESTAMP_BACKFILL,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
        "DEPENDENT_MUTATION_ALLOWED": False,
        "PRODUCTIVE_HOST_BINDING": False,
        "ADMISSION_TRUE": False,
        "SUPERVISOR_ACTIVATED": False,
        "PROPOSED_NEXT_SLICE": sequence["PROPOSED_NEXT_SLICE"],
        "ACCEPTABLE_COMPLETE_SEAM_COUNT": seams["ACCEPTABLE_COMPLETE_SEAM_COUNT"],
        "SEAM_CANDIDATE_COUNT": seams["SEAM_CANDIDATE_COUNT"],
        "RESTART_HANDOFF_ELIGIBLE": admission["RESTART_HANDOFF_ELIGIBLE"],
        "REQUIRED_DURABILITY_PRIMITIVES": durability["REQUIRED_DURABILITY_PRIMITIVES"],
        "CURRENTLY_PROVEN_PRIMITIVES": durability["CURRENTLY_PROVEN_PRIMITIVES"],
        "MISSING_PRIMITIVES": durability["MISSING_PRIMITIVES"],
    }
