"""Forensic closure tests for exact fee, restart, durability, and readiness.

No GET. No POST. No restart. No crash.
"""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
)
from src.ops.section_11_14_live_handoff_exact_fee_restart_durability_and_pre_execution_readiness_closure_v1.adjudication_v1 import (
    adjudicate_exact_fee_restart_durability_and_pre_execution_readiness_v1,
    historical_fill_hypothesis_algebra_v1,
)
from src.ops.section_11_14_live_handoff_exact_fee_restart_durability_and_pre_execution_readiness_closure_v1.constants_v1 import (
    BOUNDED_FEE_ENVELOPE_PROVEN,
    CANARY_AUTHORIZED_EXACT_FIELD,
    CODE_GAP_FOUND,
    EXACT_OKX_FEE_FORMULA_UNPROVEN,
    HOST_CRASH_DURABILITY_UNPROVEN,
    LIVE_RESTART_EMPIRICAL_RECONSTRUCTION_PROVEN,
    LIVE_RESTART_RECONSTRUCTED,
    LIVE_RESTART_STATIC_RECONSTRUCTION_PROVEN,
    OWNER_EXECUTION_AUTHORIZED,
    POST_ALLOWED_EXACT_FIELD,
    TECHNICAL_PRE_EXECUTION_READINESS,
)
from src.ops.section_11_14_live_handoff_exact_fee_restart_durability_and_pre_execution_readiness_closure_v1.persist_evidence_v1 import (
    persist_evidence_pack_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)


def test_standing_flags_and_unproven_predicates_remain_closed() -> None:
    result = adjudicate_exact_fee_restart_durability_and_pre_execution_readiness_v1()
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    assert result["EXACT_OKX_FEE_FORMULA_UNPROVEN"] is True
    assert result["BOUNDED_FEE_ENVELOPE_PROVEN"] is False
    assert result["LIVE_RESTART_STATIC_RECONSTRUCTION_PROVEN"] is True
    assert result["LIVE_RESTART_EMPIRICAL_RECONSTRUCTION_PROVEN"] is False
    assert result["LIVE_RESTART_RECONSTRUCTED"] is False
    assert result["HOST_CRASH_DURABILITY_UNPROVEN"] is True
    assert result["CODE_GAP_FOUND"] is False
    assert result["TECHNICAL_PRE_EXECUTION_READINESS"] is False
    assert result["TECHNICAL_EXECUTION_READY"] is False
    assert result["OWNER_EXECUTION_AUTHORIZED"] is False
    assert result["CANARY_AUTHORIZED_EXACT_FIELD"] == "INDETERMINATE_ABSENT"
    assert result["POST_ALLOWED_EXACT_FIELD"] == "INDETERMINATE_ABSENT"
    assert result["GET_PERFORMED"] is False
    assert result["POST_PERFORMED"] is False
    assert result["RESTART_EXECUTED"] is False
    assert result["CRASH_TEST_EXECUTED"] is False
    assert EXACT_OKX_FEE_FORMULA_UNPROVEN is True
    assert BOUNDED_FEE_ENVELOPE_PROVEN is False
    assert LIVE_RESTART_STATIC_RECONSTRUCTION_PROVEN is True
    assert LIVE_RESTART_EMPIRICAL_RECONSTRUCTION_PROVEN is False
    assert LIVE_RESTART_RECONSTRUCTED is False
    assert HOST_CRASH_DURABILITY_UNPROVEN is True
    assert CODE_GAP_FOUND is False
    assert TECHNICAL_PRE_EXECUTION_READINESS is False
    assert OWNER_EXECUTION_AUTHORIZED is False
    assert CANARY_AUTHORIZED_EXACT_FIELD == "INDETERMINATE_ABSENT"
    assert POST_ALLOWED_EXACT_FIELD == "INDETERMINATE_ABSENT"


def test_historical_fill_algebra_is_hypothesis_not_oem_formula() -> None:
    hypo = historical_fill_hypothesis_algebra_v1()
    assert hypo["MATCHES_FILL_PX_TIMES_HYPOTHESIZED_0_0005"] is True
    assert hypo["MARK_PX_EXACT_MATCH"] is False
    assert hypo["IDX_PX_EXACT_MATCH"] is False
    assert hypo["CONTEMPORANEOUS_SUI_TRADE_FEE_GET"] is False
    assert hypo["DOES_NOT_CLOSE_EXACT_OKX_FEE_FORMULA"] is True
    assert hypo["AUTHORITY_CLASS"] == "HYPOTHESIS_NOT_OEM_FORMULA"
    assert hypo["N_FILLS"] == 1


def test_fee_classes_are_not_equated() -> None:
    result = adjudicate_exact_fee_restart_durability_and_pre_execution_readiness_v1()
    names = {row["PREDICATE"] for row in result["FEE_PROVENANCE"]}
    assert "EXPECTED_FEE_PRETRADE" in names
    assert "VENUE_REPORTED_FEE_POST_FILL" in names
    assert "LOCAL_FEE_ESTIMATE" in names
    assert "EXACT_SETTLED_FEE" in names
    assert "EXACT_OKX_FEE_FORMULA" in names
    assert result["EXPECTED_FEE_PRETRADE_STATUS"] != result["VENUE_REPORTED_FEE_POST_FILL_STATUS"]
    assert result["LOCAL_FEE_ESTIMATE_STATUS"] != result["EXACT_SETTLED_FEE_STATUS"]


def test_restart_distinctions_remain_separate() -> None:
    restart = adjudicate_exact_fee_restart_durability_and_pre_execution_readiness_v1()["RESTART"]
    assert restart["CODE_PATH_EXISTS"] is True
    assert restart["PRODUCTIVE_BINDING_EXISTS"] is True
    assert restart["OFFLINE_RECONSTRUCTION_PROOF_EXISTS"] is True
    assert restart["LIVE_RESTART_OBSERVATION_EXISTS"] is False
    assert restart["POST_RESTART_RECONCILIATION_PROOF_EXISTS"] is False
    assert restart["AUTHORIZATION_INTENTIONALLY_MUST_NOT_SURVIVE_RESTART"] is True
    assert restart["STATIC_FAIL_CLOSED_RECONSTRUCTION_PROVEN"] is True
    assert restart["STATIC_SUCCESSFUL_IDENTITY_RECONSTRUCTION_PROVEN"] is False
    assert restart["DOES_NOT_CLOSE_LIVE_RESTART_RECONSTRUCTED"] is True


def test_durability_classes_remain_separate() -> None:
    durability = adjudicate_exact_fee_restart_durability_and_pre_execution_readiness_v1()[
        "DURABILITY"
    ]
    assert durability["FSYNC_FILE"] is True
    assert durability["FSYNC_DIRECTORY"] is True
    assert durability["SYSCALL_SUCCESS_IS_HOST_CRASH_PROOF"] is False
    assert durability["PROCESS_KILL_IS_HOST_CRASH_PROOF"] is False
    assert durability["DDO_A1_PROOF_IS_NOT_THIS_OWNER"] is True
    assert durability["HOST_CRASH_DURABILITY_UNPROVEN"] is True
    assert durability["POWER_LOSS_DURABILITY_STATUS"] == "UNPROVEN"
    assert durability["CODE_GAP_FOUND"] is False


def test_predicate_table_covers_required_names() -> None:
    rows = adjudicate_exact_fee_restart_durability_and_pre_execution_readiness_v1()[
        "PREDICATE_TABLE"
    ]
    names = {row["PREDICATE"] for row in rows}
    required = {
        "ORIGIN_MAIN_BOUND",
        "TRACKED_TREE_CLEAN",
        "CURRENT_PHASE",
        "CURRENT_INSTRUMENT_BOUND",
        "CURRENT_ACCOUNT_BOUND",
        "NETWORK_READINESS",
        "PRIVATE_GET_READINESS",
        "INSTRUMENT_STATE",
        "ACCOUNT_MODE",
        "POSITION_MODE",
        "MARGIN_MODE",
        "LEVERAGE",
        "PRICE_BAND",
        "MAX_SIZE",
        "MAX_AVAILABLE",
        "AVAILABLE_MARGIN",
        "EXPECTED_FEE_MODEL",
        "EXACT_OKX_FEE_FORMULA",
        "FEE_ENVELOPE",
        "SLIPPAGE_BOUND",
        "LIVE_RESTART_STATIC_RECONSTRUCTION",
        "LIVE_RESTART_EMPIRICAL_RECONSTRUCTION",
        "PROCESS_CRASH_DURABILITY",
        "HOST_CRASH_DURABILITY",
        "CAPTURE_PROVENANCE",
        "POST_FILL_RECONCILIATION",
        "LIVE_ENABLED",
        "LIVE_ARMED",
        "CANARY_EXECUTE_AUTHORIZED",
        "OWNER_EXECUTION_AUTHORIZED",
        "SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED",
        "ORDER_SUBMIT_AUTHORIZED",
        "SUBMIT_UNLOCKED",
        "POST_ALLOWED_EXACT_FIELD",
        "CANARY_AUTHORIZED_EXACT_FIELD",
    }
    assert required <= names
    for row in rows:
        assert row["STATUS"] in {"PROVEN", "UNPROVEN", "INDETERMINATE", "NOT_APPLICABLE"}


def test_persist_evidence_pack_roundtrip(tmp_path: Path) -> None:
    persisted = persist_evidence_pack_v1(repo_root=tmp_path)
    assert int(persisted["MANIFEST_VERIFY_RC"]) == 0
    verified = verify_manifest_v1(Path(persisted["EVIDENCE_ROOT"]))
    assert int(verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    summary = (Path(persisted["EVIDENCE_ROOT"]) / "SUMMARY.json").read_text(encoding="utf-8")
    assert '"EXACT_OKX_FEE_FORMULA_UNPROVEN": true' in summary
    assert '"BOUNDED_FEE_ENVELOPE_PROVEN": false' in summary
    assert '"LIVE_RESTART_RECONSTRUCTED": false' in summary
    assert '"HOST_CRASH_DURABILITY_UNPROVEN": true' in summary
    assert '"OWNER_EXECUTION_AUTHORIZED": false' in summary
    assert '"GET_PERFORMED": false' in summary
    assert '"POST_PERFORMED": false' in summary
