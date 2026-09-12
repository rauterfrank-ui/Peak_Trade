"""Owner-bind and retroactive-synthesis-refusal tests for §11.14 Live restart."""

from __future__ import annotations

from pathlib import Path

from src.learning.deterministic_decision_outcome_v0.a1_durability_failure_policy_binding_v1 import (
    HOST_CRASH_DURABILITY,
)
from src.learning.mutation_critical_control_state_storage_v1.authority_v1 import (
    ADMISSION_TRUE,
    DEPENDENT_MUTATION_ALLOWED,
    PRODUCTIVE_HOST_BINDING,
    STORAGE_OWNER_NAME,
    SUPERVISOR_ACTIVATED,
)
from src.learning.mutation_critical_control_state_storage_v1.crash_reproof_v1 import (
    POWER_LOSS_DURABILITY,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY,
    SECTION_11_14_ACCOUNTING_IS_NOT_FULL_CORE_E2E,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    A1_WAL_AS_LIVE_HANDOFF_ALLOWED,
    ACCOUNTING_ONLY_IS_NOT_RESTART,
    CANARY_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY,
    FORBIDDEN_OWNER_REUSE,
    HISTORICAL_LIVE_RESTART_HANDOFF_STATUS,
    HISTORICAL_OWNER_BIND_OWNER_GO,
    HISTORICAL_OWNER_BIND_SHA,
    LIVE_RESTART_RECONSTRUCTED,
    HISTORICAL_HANDOFF_OWNER_BOUND,
    HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
    HISTORICAL_HANDOFF_PRODUCTIVE_BINDING,
    HISTORICAL_HANDOFF_WRITER_PRESENT,
    THIS_SLICE,
    TRACK_1,
    TRACK_2,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_historical_unprovability_v1 import (
    bind_historical_live_restart_unprovability_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_INSTID,
    BOUND_ORDID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_bind_execute_v1 import (
    execute_live_restart_handoff_owner_bind_and_retroactive_synthesis_refusal_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_bind_v1 import (
    bind_section_11_14_live_handoff_owner_contract_v1,
    classify_forbidden_owner_reuse_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_census_matrix_v1 import (
    bind_section_11_14_live_handoff_owner_census_matrix_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_predicate_v1 import (
    ADMISSIBLE_SOURCE_KIND,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_validators_v1 import (
    evaluate_handoff_proof_bundle_v1,
    refuse_retroactive_handoff_synthesis_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _identity_handoff() -> dict[str, str]:
    return {
        "clOrdId": BOUND_CLORDID,
        "ordId": BOUND_ORDID,
        "instId": BOUND_INSTID,
        "posSide": "net",
        "pos": "1",
    }


def test_current_handoff_owner_is_none() -> None:
    contract = bind_section_11_14_live_handoff_owner_contract_v1()
    assert HISTORICAL_HANDOFF_OWNER_CURRENT_NONE == "NONE"
    assert contract["SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT"] == "NONE"
    assert HISTORICAL_HANDOFF_OWNER_BOUND is False
    assert HISTORICAL_HANDOFF_WRITER_PRESENT is False
    assert HISTORICAL_HANDOFF_PRODUCTIVE_BINDING is False
    assert contract["NEW_STORAGE_OWNER_CREATED"] is False
    assert contract["PLACEHOLDER_WRITER_CREATED"] is False


def test_live_restart_reconstructed_remains_false() -> None:
    assert LIVE_RESTART_RECONSTRUCTED is False
    result = execute_live_restart_handoff_owner_bind_and_retroactive_synthesis_refusal_v1(
        owner_go=HISTORICAL_OWNER_BIND_OWNER_GO,
        origin_main_sha=HISTORICAL_OWNER_BIND_SHA,
        repo_root=REPO_ROOT,
        run_id="20260906T201500Z-test",
    )
    assert result["adjudication"]["LIVE_RESTART_RECONSTRUCTED"] is False
    assert result["summary"]["LIVE_RESTART_RECONSTRUCTED"] is False
    assert result["raw_exchanges"] == []


def test_venue_get_alone_cannot_set_field_true() -> None:
    result = evaluate_handoff_proof_bundle_v1(
        handoff=_identity_handoff(),
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path=(
            "evidence/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            "20260904T181817Z/GET_POSITIONS.raw.json"
        ),
        synthetic_from_venue_get=True,
    )
    assert result["claim_value"] is False
    assert result["REASON"] == "ACCOUNTING_ONLY_IS_NOT_RESTART"


def test_accounting_evidence_alone_cannot_set_field_true() -> None:
    result = evaluate_handoff_proof_bundle_v1(
        handoff=_identity_handoff(),
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path=(
            "evidence/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            "20260904T185000Z/ACCOUNTING_RECONSTRUCTED_ADJUDICATION.json"
        ),
        accounting_only=True,
    )
    assert result["claim_value"] is False
    assert result["REASON"] == "ACCOUNTING_ONLY_IS_NOT_RESTART"
    assert ACCOUNTING_ONLY_IS_NOT_RESTART is True


def test_ddo_ledger_cannot_set_field_true() -> None:
    result = evaluate_handoff_proof_bundle_v1(
        handoff=_identity_handoff(),
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path="src/learning/deterministic_decision_outcome_v0/ledger.json",
        claimed_owner="DDO_DURABLE_EVIDENCE_STORAGE_OWNER",
        contemporaneous_capture_proven=True,
        provenance_class="CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_CAPTURE",
    )
    assert result["claim_value"] is False
    row = classify_forbidden_owner_reuse_v1("DDO_DURABLE_EVIDENCE_STORAGE_OWNER")
    assert row["ALLOWED_AS_SECTION_11_14_LIVE_HANDOFF_OWNER"] is False


def test_a1_wal_cannot_set_field_true() -> None:
    result = evaluate_handoff_proof_bundle_v1(
        handoff=_identity_handoff(),
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path="src/learning/mutation_critical_control_state_storage_v1/wal_adapter_v1.py",
        claimed_owner="MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER",
        contemporaneous_capture_proven=True,
        provenance_class="CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_CAPTURE",
    )
    assert result["claim_value"] is False
    assert A1_WAL_AS_LIVE_HANDOFF_ALLOWED is False
    assert STORAGE_OWNER_NAME == "MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER"


def test_testnet_durable_state_cannot_set_field_true() -> None:
    result = evaluate_handoff_proof_bundle_v1(
        handoff=_identity_handoff(),
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path=(
            "evidence/ops/section_11_12_8_bounded_long_running_productive_testnet_campaign_now/"
            "20260808T181528Z/durable_state/actual_start_durable_state_v1.json"
        ),
        contemporaneous_capture_proven=True,
        provenance_class="CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_CAPTURE",
    )
    assert result["claim_value"] is False
    assert result["artifact_role"] == "TESTNET_DURABLE_STATE_NOT_THIS_FIELD"


def test_phase_9_2_durable_state_cannot_set_field_true() -> None:
    result = evaluate_handoff_proof_bundle_v1(
        handoff=_identity_handoff(),
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path="docs/evidence/capability_phase_9_2/durable_state/md.json",
        contemporaneous_capture_proven=True,
        provenance_class="CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_CAPTURE",
    )
    assert result["claim_value"] is False
    assert result["artifact_role"] == "PHASE_9_2_MD_OR_FIXTURE_NOT_THIS_FIELD"


def test_cap_72_sidestate_cannot_set_field_true() -> None:
    result = evaluate_handoff_proof_bundle_v1(
        handoff=_identity_handoff(),
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path=(
            "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
            "sidestate_restore_v1.py"
        ),
        claimed_owner="CAP_72_SIDESTATE_PERSIST",
        contemporaneous_capture_proven=True,
        provenance_class="CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_CAPTURE",
    )
    assert result["claim_value"] is False
    assert result["artifact_role"] == "CAP_72_SIDESTATE_NOT_THIS_FIELD"


def test_filegate_kill_switch_cannot_set_field_true() -> None:
    result = evaluate_handoff_proof_bundle_v1(
        handoff=_identity_handoff(),
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path="src/risk_layer/kill_switch/persistence.py",
        claimed_owner="FILEGATE_KILL_SWITCH",
        contemporaneous_capture_proven=True,
        provenance_class="CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_CAPTURE",
    )
    assert result["claim_value"] is False
    assert result["artifact_role"] == "FILEGATE_KILL_SWITCH_NOT_THIS_FIELD"


def test_synthetic_json_from_get_positions_is_rejected() -> None:
    refusal = refuse_retroactive_handoff_synthesis_v1(
        handoff=_identity_handoff(),
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path=(
            "evidence/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            "20260904T181817Z/GET_POSITIONS.raw.json"
        ),
        synthetic_from_venue_get=True,
        provenance_class="VENUE_GET_COPY",
    )
    assert refusal["SYNTHESIS_ALLOWED"] is False
    assert refusal["REASON"] == "VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF"
    assert refusal["RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED"] is False


def test_identical_identity_fields_without_contemporaneous_provenance_rejected() -> None:
    result = evaluate_handoff_proof_bundle_v1(
        handoff=_identity_handoff(),
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path="durable_state/pre_restart.json",
        contemporaneous_capture_proven=False,
    )
    assert result["claim_value"] is False
    assert result["REASON"] == "POST_HOC_IDENTITY_MATCH_DOES_NOT_PROVE_PRE_RESTART_CAPTURE"


def test_timestamp_backfill_and_retroactive_relabel_rejected() -> None:
    backfill = refuse_retroactive_handoff_synthesis_v1(
        handoff={**_identity_handoff(), "captured_at_utc": "2026-09-04T16:00:00Z"},
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path="durable_state/pre_restart.json",
        timestamp_backfill=True,
        provenance_class="TIMESTAMP_BACKFILL",
    )
    assert backfill["SYNTHESIS_ALLOWED"] is False
    assert backfill["REASON"] == "NO_TIMESTAMP_BACKFILL"
    relabel = refuse_retroactive_handoff_synthesis_v1(
        handoff=_identity_handoff(),
        source_kind=ADMISSIBLE_SOURCE_KIND,
        source_path="durable_state/pre_restart.json",
        provenance_class="RETROACTIVE_SYNTHESIS",
        contemporaneous_capture_proven=True,
    )
    assert relabel["SYNTHESIS_ALLOWED"] is False
    assert relabel["REASON"] == "NO_SYNTHETIC_PRE_RESTART_PROVENANCE"


def test_historical_bound_identity_remains_unprovable_without_contemporaneous_capture() -> None:
    bind = bind_historical_live_restart_unprovability_v1()
    assert bind["BOUND_ORDID"] == "3893505043080286208"
    assert bind["BOUND_CLORDID"] == "ptokxeprod1fec928b1fec928b00"
    assert bind["BOUND_INSTID"] == "SUI-USD_UM_XPERP-310404"
    assert bind["CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED"] is False
    assert bind["HISTORICAL_LIVE_RESTART_HANDOFF_STATUS"] == (
        "UNPROVABLE_WITHOUT_CONTEMPORANEOUS_CAPTURE"
    )
    assert HISTORICAL_LIVE_RESTART_HANDOFF_STATUS == ("UNPROVABLE_WITHOUT_CONTEMPORANEOUS_CAPTURE")
    assert bind["DOES_NOT_DENY_ORDER_WAS_REAL"] is True
    assert bind["DOES_NOT_DENY_ACK_WAS_OBSERVED"] is True
    assert bind["DOES_NOT_DENY_FILL_WAS_OBSERVED"] is True
    assert bind["DOES_NOT_DENY_POSITION_WAS_OBSERVED"] is True
    assert bind["DOES_NOT_DENY_ACCOUNTING_WAS_OBSERVED"] is True


def test_live_accounting_reconstructed_true_alone_is_not_restart() -> None:
    proof = adjudicate_live_restart_reconstructed_v1(
        restart_evidence={
            "source_kind": "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF_CENSUS",
            "POST_USED": False,
            "GET_PERFORMED": False,
            "PRIVATE_GET_USED": False,
            "CANCEL_USED": False,
            "AMEND_USED": False,
            "FLATTEN_EXECUTE_USED": False,
            "RESTART_EXECUTION": False,
            "LIVE_RESTART_RECONSTRUCTED": False,
            "durable_handoff": _identity_handoff(),
            "census": {
                "DURABLE_PRE_RESTART_HANDOFF_PRESENT": False,
                "HANDOFF_DISTINCT_FROM_ACCOUNTING_VENUE_GET_PATH": False,
                "NOT_FIXTURE_TESTNET_OR_SIMULATED": True,
            },
        }
    )
    assert proof["LIVE_ACCOUNTING_RECONSTRUCTED"] is True
    assert proof["LIVE_RESTART_RECONSTRUCTED"] is False


def test_a1_crash_durability_remains_unproven() -> None:
    assert HOST_CRASH_DURABILITY == "UNPROVEN"
    assert POWER_LOSS_DURABILITY == "UNPROVEN"
    assert DEPENDENT_MUTATION_ALLOWED is False
    assert PRODUCTIVE_HOST_BINDING is False
    assert ADMISSION_TRUE is False
    assert SUPERVISOR_ACTIVATED is False


def test_full_core_29p_authority_remains_unchanged() -> None:
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "ACCOUNT_EQUITY_SOURCE_SEMANTIC_MAPPING_OWNER_RATIFICATION_REQUIRED"
    )
    assert CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY is False
    assert CANARY_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY is False
    assert SECTION_11_14_ACCOUNTING_IS_NOT_FULL_CORE_E2E is True
    assert TRACK_1 == "SECTION_11_14_EVIDENCE_LADDER"
    assert TRACK_2 == "SECTION_11_2_1_FULL_CORE_PRODUCTIVE_LIVE_PATH"


def test_no_live_writer_or_transport_reachability_created() -> None:
    result = execute_live_restart_handoff_owner_bind_and_retroactive_synthesis_refusal_v1(
        owner_go=HISTORICAL_OWNER_BIND_OWNER_GO,
        origin_main_sha=HISTORICAL_OWNER_BIND_SHA,
        repo_root=REPO_ROOT,
        run_id="20260906T201500Z-test",
    )
    assert result["summary"]["GET_PERFORMED"] is False
    assert result["summary"]["POST_USED"] is False
    assert result["summary"]["CREDENTIAL_USE"] is False
    assert result["code_path_census"]["SECTION_11_14_LIVE_DURABLE_STATE_WRITER_EXISTS"] is False
    assert result["code_path_census"]["LIVE_CANARY_DURABLE_STATE_WRITER_EXISTS"] is False
    assert result["owner_bind"]["SECTION_11_14_LIVE_HANDOFF_WRITER_PRESENT"] is False


def test_no_second_restart_state_or_reconciliation_engine_owner_created() -> None:
    matrix = bind_section_11_14_live_handoff_owner_census_matrix_v1()
    assert matrix["LIVE_SCOPED_IDENTITY_BOUND_CONTEMPORANEOUS_HANDOFF_OWNER_FOUND"] is False
    assert matrix["NEW_STORAGE_OWNER_CREATED"] is False
    assert matrix["NEW_RECONCILIATION_ENGINE_CREATED"] is False
    assert matrix["NEW_EXECUTION_STATE_MACHINE_CREATED"] is False
    assert matrix["SECOND_RESTART_STATE_OWNER_CREATED"] is False
    assert matrix["ALLOWED_HANDOFF_OWNER_COUNT"] == 0
    assert set(FORBIDDEN_OWNER_REUSE) == {
        "DDO_DURABLE_EVIDENCE_STORAGE_OWNER",
        "MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER",
        "SECTION_11_14_EVIDENCE_PACKS",
        "TESTNET_CAMPAIGN_DURABLE_STATE",
        "PHASE_9_2_MD_DURABLE_STATE",
        "CAP_72_SIDESTATE_PERSIST",
        "FILEGATE_KILL_SWITCH",
        "VENUE_OKX_EEA",
    }
    assert THIS_SLICE != ("11.14.LIVE_RESTART_HANDOFF_OWNER_BIND_AND_RETROACTIVE_SYNTHESIS_REFUSAL")
    for name in FORBIDDEN_OWNER_REUSE:
        classified = classify_forbidden_owner_reuse_v1(name)
        assert classified["ALLOWED_AS_SECTION_11_14_LIVE_HANDOFF_OWNER"] is False
