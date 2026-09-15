"""NEW_CANONICAL today initial-stock source kind.

Forensic bootstrap supply is retired from the productive critical path.
Sealed BQ/BR evidence remains intact. No today declaration exists, so
KIND_SET stays empty. Candidate is not an anchor. No GET. No POST.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    WIRE_SEND_PERMITTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_remaining_unknown_kind_semantics_v1 import (
    DECISION_INCLUDE,
    KIND_SET_EMPTY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_owner_supplied_bootstrap_artifact_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BR_PACK_RELPATH,
    EARLIEST_LIVE_CRITICAL_PATH_BLOCKER as BR_LIVE_BLOCKER,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_source_kind_v1 import (
    CANONICAL_PACK_RELPATH,
    DECLARATION_FILENAME,
    DECLARATION_SURFACE_RELPATH,
    EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
    EXPECTED_ORIGIN_MAIN_SHA,
    FORENSIC_PATH_PRODUCTIVE_STATUS,
    HISTORICAL_ARTIFACT_EXISTENCE_CLAIM,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_GO,
    TODAY_SOURCE_KIND,
    TodayInitialStockSourceKindContractError,
    evaluate_today_declaration_candidate_v1,
    evaluate_today_initial_stock_source_kind_boundary_v1,
    execute_live_equity_stock_today_initial_stock_source_kind_v1,
    fixture_today_declaration_payload_v1,
    reject_forensic_path_as_productive_authority_v1,
    scan_today_declaration_surface_v1,
    semantic_declaration_digest_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_SOURCE_KIND_WP1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
BR_HEADING = "11.2.1.BR FULL_CORE_LIVE_EQUITY_STOCK_OWNER_SUPPLIED_BOOTSTRAP_ARTIFACT"
BS_HEADING = "11.2.1.BS FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_SOURCE_KIND"
BT_HEADING = "11.2.1.BT FULL_CORE_LIVE_EQUITY_STOCK_TODAY_DECLARATION_GOVERNED_BINDING_CONTRACT"
SEALED_BR = REPO_ROOT / CANONICAL_BR_PACK_RELPATH
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
_AS_OF = "2026-09-14T18:40:00Z"


def _bs_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BS_HEADING)
    return runbook[start : runbook.index(BT_HEADING, start)]


def _write_declaration(root: Path, payload: dict) -> Path:
    surface = root / DECLARATION_SURFACE_RELPATH
    surface.mkdir(parents=True, exist_ok=True)
    path = surface / DECLARATION_FILENAME
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    path.write_text(body, encoding="utf-8")
    return path


def _run(tmp_path: Path):
    return execute_live_equity_stock_today_initial_stock_source_kind_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        sealed_br_pack=SEALED_BR,
        repo_root=REPO_ROOT,
        evidence_root=tmp_path / "today_kind",
        persist_as_of=_AS_OF,
    )


def test_sealed_br_manifest_remains_intact() -> None:
    assert verify_manifest_sha256_v1(store_root=SEALED_BR) == 0
    claims = json.loads((SEALED_BR / "claims.json").read_text(encoding="utf-8"))
    assert claims["FORENSIC_ARTIFACT_PRESENT"] == "false"
    assert claims["EARLIEST_LIVE_CRITICAL_PATH_BLOCKER"] == BR_LIVE_BLOCKER


def test_owner_go_and_sha_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(TodayInitialStockSourceKindContractError, match="OWNER_GO_MISMATCH"):
        execute_live_equity_stock_today_initial_stock_source_kind_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_br_pack=SEALED_BR,
            repo_root=REPO_ROOT,
            evidence_root=tmp_path,
            persist_as_of=_AS_OF,
        )
    with pytest.raises(TodayInitialStockSourceKindContractError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_live_equity_stock_today_initial_stock_source_kind_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            sealed_br_pack=SEALED_BR,
            repo_root=REPO_ROOT,
            evidence_root=tmp_path,
            persist_as_of=_AS_OF,
        )


def test_forensic_path_cannot_become_productive_authority() -> None:
    with pytest.raises(TodayInitialStockSourceKindContractError):
        reject_forensic_path_as_productive_authority_v1(
            claimed_proof="PROMOTE_FORENSIC_ARTIFACT_TO_TODAY_SOURCE",
        )
    with pytest.raises(TodayInitialStockSourceKindContractError):
        reject_forensic_path_as_productive_authority_v1(claimed_proof=DECISION_INCLUDE)
    with pytest.raises(TodayInitialStockSourceKindContractError):
        reject_forensic_path_as_productive_authority_v1(claimed_proof="RESTORE_HISTORICAL_F12")


def test_production_surface_declaration_absent() -> None:
    scan = scan_today_declaration_surface_v1(repo_root=REPO_ROOT)
    assert scan.declaration_present == "false"
    assert scan.surface_status == "MISSING"
    boundary = evaluate_today_initial_stock_source_kind_boundary_v1(repo_root=REPO_ROOT)
    assert boundary.forensic_path_productive_status == FORENSIC_PATH_PRODUCTIVE_STATUS
    assert boundary.historical_artifact_existence_claim == HISTORICAL_ARTIFACT_EXISTENCE_CLAIM
    assert boundary.today_source_kind == TODAY_SOURCE_KIND
    assert boundary.today_observation_status == "ABSENT"
    assert boundary.candidate_status == "ABSENT"
    assert boundary.ratification_status == "RATIFICATION_AUTHORITY_ABSENT"
    assert boundary.initial_stock_anchor_status == "ABSENT"
    assert boundary.live_equity_stock_kind_set == KIND_SET_EMPTY
    assert boundary.checkpoint_status == "NON_SOURCE_NO_BOUND_STOCK"
    assert boundary.event_stream_binding_status == "FLOW_NOT_STOCK"
    assert boundary.running_equity_reconstruction_status == "BLOCKED_NO_RATIFIED_ANCHOR"
    assert boundary.venue_eq_source_authority == "false"
    assert boundary.checkpoint_mints_equity == "false"
    assert boundary.earliest_live_critical_path_blocker == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER
    assert boundary.next_owner_go_required == NEXT_OWNER_GO_REQUIRED


def test_absence_is_not_proof_of_historical_nonexistence() -> None:
    boundary = evaluate_today_initial_stock_source_kind_boundary_v1(repo_root=REPO_ROOT)
    assert boundary.historical_artifact_existence_claim != "ARTIFACT_NEVER_EXISTED"
    assert "AVAILABLE_LOCAL_SEARCH_SURFACES" in boundary.historical_artifact_existence_claim


def _eval_payload(tmp_path: Path, payload: dict) -> object:
    _write_declaration(tmp_path, payload)
    return evaluate_today_declaration_candidate_v1(
        repo_root=tmp_path,
        claimed_proof="TODAY_SOURCE_KIND_DEFINED_DECLARATION_ABSENT_FAIL_CLOSED",
    )


def test_malformed_json_fail_closed(tmp_path: Path) -> None:
    surface = tmp_path / DECLARATION_SURFACE_RELPATH
    surface.mkdir(parents=True)
    (surface / DECLARATION_FILENAME).write_text("{", encoding="utf-8")
    result = evaluate_today_declaration_candidate_v1(
        repo_root=tmp_path,
        claimed_proof="TODAY_SOURCE_KIND_DEFINED_DECLARATION_ABSENT_FAIL_CLOSED",
    )
    assert result.validation_status == "INVALID"
    assert result.initial_stock_anchor_status == "ABSENT"


def test_forensic_source_kind_cannot_be_today_source(tmp_path: Path) -> None:
    payload = fixture_today_declaration_payload_v1()
    payload["source_kind"] = "OWNER_SUPPLIED_FORENSIC_BOOTSTRAP_STOCK"
    result = _eval_payload(tmp_path, payload)
    assert result.reason_code == "FORENSIC_BOOTSTRAP_PATH_NOT_PRODUCTIVE_AUTHORITY"
    assert result.initial_stock_candidate_status == "ABSENT"


def test_venue_eq_cannot_source_today_stock(tmp_path: Path) -> None:
    payload = fixture_today_declaration_payload_v1()
    payload["source_type"] = "VENUE_EQ"
    result = _eval_payload(tmp_path, payload)
    assert result.reason_code == "VENUE_EQ_CANNOT_BE_SOURCE"


def test_checkpoint_cannot_mint_today_stock(tmp_path: Path) -> None:
    payload = fixture_today_declaration_payload_v1()
    payload["source_type"] = "CHECKPOINT_MINT"
    result = _eval_payload(tmp_path, payload)
    assert result.reason_code == "CHECKPOINT_CANNOT_MINT_EQUITY"


def test_fixture_cannot_promote(tmp_path: Path) -> None:
    payload = fixture_today_declaration_payload_v1()
    payload["declaration_id"] = "FIXTURE_TODAY_001"
    result = _eval_payload(tmp_path, payload)
    assert result.reason_code == "FIXTURE_CANNOT_PROMOTE"


def test_unknown_source_kind_fail_closed(tmp_path: Path) -> None:
    payload = fixture_today_declaration_payload_v1()
    payload["source_kind"] = "MADE_UP_KIND"
    result = _eval_payload(tmp_path, payload)
    assert result.reason_code == "UNKNOWN_SOURCE_KIND"


def test_account_mismatch_fail_closed(tmp_path: Path) -> None:
    payload = fixture_today_declaration_payload_v1()
    _write_declaration(tmp_path, payload)
    result = evaluate_today_declaration_candidate_v1(
        repo_root=tmp_path,
        claimed_proof="TODAY_SOURCE_KIND_DEFINED_DECLARATION_ABSENT_FAIL_CLOSED",
        expected_bindings={
            "account_identity": "OTHER_ACCOUNT",
            "instrument_identity": "ACCOUNT_LEVEL",
            "as_of_time": payload["as_of_time"],
        },
    )
    assert result.reason_code == "ACCOUNT_BINDING_MISMATCH"


def test_instrument_mismatch_fail_closed(tmp_path: Path) -> None:
    payload = fixture_today_declaration_payload_v1()
    _write_declaration(tmp_path, payload)
    result = evaluate_today_declaration_candidate_v1(
        repo_root=tmp_path,
        claimed_proof="TODAY_SOURCE_KIND_DEFINED_DECLARATION_ABSENT_FAIL_CLOSED",
        expected_bindings={
            "account_identity": payload["account_identity"],
            "instrument_identity": "OTHER_INSTRUMENT",
            "as_of_time": payload["as_of_time"],
        },
    )
    assert result.reason_code == "INSTRUMENT_BINDING_MISMATCH"


def test_temporal_mismatch_fail_closed(tmp_path: Path) -> None:
    payload = fixture_today_declaration_payload_v1()
    _write_declaration(tmp_path, payload)
    result = evaluate_today_declaration_candidate_v1(
        repo_root=tmp_path,
        claimed_proof="TODAY_SOURCE_KIND_DEFINED_DECLARATION_ABSENT_FAIL_CLOSED",
        expected_bindings={
            "account_identity": payload["account_identity"],
            "instrument_identity": payload["instrument_identity"],
            "as_of_time": "1999-01-01T00:00:00Z",
        },
    )
    assert result.reason_code == "TIME_BINDING_MISMATCH"


def test_implicit_numeric_coerce_fail_closed(tmp_path: Path) -> None:
    payload = fixture_today_declaration_payload_v1()
    payload["equity_value"] = 100.0
    result = _eval_payload(tmp_path, payload)
    assert result.reason_code == "IMPLICIT_NORMALIZATION_FORBIDDEN"
    assert result.initial_stock_anchor_status == "ABSENT"


def test_digest_mismatch_fail_closed(tmp_path: Path) -> None:
    payload = fixture_today_declaration_payload_v1()
    payload["provenance_digest"] = "0" * 64
    result = _eval_payload(tmp_path, payload)
    assert result.reason_code == "PROVENANCE_DIGEST_MISMATCH"


def test_flow_cannot_source_today_stock(tmp_path: Path) -> None:
    payload = fixture_today_declaration_payload_v1()
    payload["source_type"] = "HISTORICAL_FLOW"
    result = _eval_payload(tmp_path, payload)
    assert result.reason_code == "FLOW_CANNOT_BE_SOURCE"


def test_estimated_pnl_cannot_source_today_stock(tmp_path: Path) -> None:
    payload = fixture_today_declaration_payload_v1()
    payload["source_type"] = "ESTIMATED_PNL"
    result = _eval_payload(tmp_path, payload)
    assert result.reason_code == "ESTIMATED_PNL_CANNOT_BE_SOURCE"


def test_plausibility_cannot_source_today_stock(tmp_path: Path) -> None:
    payload = fixture_today_declaration_payload_v1()
    payload["source_type"] = "PLAUSIBILITY"
    result = _eval_payload(tmp_path, payload)
    assert result.reason_code == "PLAUSIBILITY_CANNOT_BE_SOURCE"


def test_unclassified_event_cannot_source_today_stock(tmp_path: Path) -> None:
    payload = fixture_today_declaration_payload_v1()
    payload["source_type"] = "UNCLASSIFIED_EVENT"
    result = _eval_payload(tmp_path, payload)
    assert result.reason_code == "UNCLASSIFIED_EVENT_CANNOT_BE_SOURCE"


def test_missing_field_fail_closed(tmp_path: Path) -> None:
    payload = fixture_today_declaration_payload_v1()
    del payload["equity_value"]
    payload["provenance_digest"] = semantic_declaration_digest_v1(payload)
    result = _eval_payload(tmp_path, payload)
    assert result.reason_code == "MISSING_FIELD"
    assert result.initial_stock_candidate_status == "ABSENT"


def test_contradictory_validity_window_fail_closed(tmp_path: Path) -> None:
    payload = fixture_today_declaration_payload_v1()
    payload["validity_window_end"] = "2099-01-01T00:00:00Z"
    payload["provenance_digest"] = semantic_declaration_digest_v1(payload)
    result = _eval_payload(tmp_path, payload)
    assert result.reason_code == "CONTRADICTORY_FIELD"


def test_valid_declaration_remains_non_anchor_without_ratification(tmp_path: Path) -> None:
    payload = fixture_today_declaration_payload_v1()
    payload["provenance_digest"] = semantic_declaration_digest_v1(payload)
    _write_declaration(tmp_path, payload)
    result = evaluate_today_declaration_candidate_v1(
        repo_root=tmp_path,
        claimed_proof="TODAY_SOURCE_KIND_DEFINED_DECLARATION_ABSENT_FAIL_CLOSED",
    )
    assert result.reason_code == "VALID_TODAY_CANDIDATE_NOT_RATIFIED"
    assert result.validation_status == "VALID"
    assert result.initial_stock_candidate_status == "PRESENT_UNRATIFIED"
    assert result.initial_stock_anchor_status == "ABSENT"
    assert result.ratification_status == "RATIFICATION_AUTHORITY_ABSENT"
    assert result.live_equity_stock_kind_set == KIND_SET_EMPTY
    assert result.membership_member == "false"


def test_empty_kind_set_without_valid_candidate() -> None:
    candidate = evaluate_today_declaration_candidate_v1(
        repo_root=REPO_ROOT,
        claimed_proof="TODAY_SOURCE_KIND_DEFINED_DECLARATION_ABSENT_FAIL_CLOSED",
    )
    assert candidate.live_equity_stock_kind_set == KIND_SET_EMPTY
    assert candidate.membership_member == "false"


def test_deterministic_replay_and_execute(tmp_path: Path) -> None:
    first = evaluate_today_initial_stock_source_kind_boundary_v1(repo_root=REPO_ROOT)
    second = evaluate_today_initial_stock_source_kind_boundary_v1(repo_root=REPO_ROOT)
    assert first == second
    result = _run(tmp_path)
    assert result.forensic_path_productive_status == FORENSIC_PATH_PRODUCTIVE_STATUS
    assert result.today_observation_status == "ABSENT"
    assert result.candidate_status == "ABSENT"
    assert result.ratification_status == "RATIFICATION_AUTHORITY_ABSENT"
    assert result.initial_stock_anchor_status == "ABSENT"
    assert result.live_equity_stock_kind_set == KIND_SET_EMPTY
    assert result.checkpoint_mints_equity == "false"
    assert result.venue_eq_source_authority == "false"
    assert result.kinds_invented_this_go == "false"
    assert result.legacy_semantics_reconstructed == "false"
    assert result.venue_get_count == "0"
    assert result.venue_post_count == "0"
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is False
    store = Path(result.store_root)
    assert verify_manifest_sha256_v1(store_root=store) == 0
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    assert claims["NEW_CANONICAL_SEMANTICS"] == "true"
    assert claims["FORENSIC_PATH_PRODUCTIVE_STATUS"] == FORENSIC_PATH_PRODUCTIVE_STATUS
    assert claims["HISTORICAL_ARTIFACT_EXISTENCE_CLAIM"] == HISTORICAL_ARTIFACT_EXISTENCE_CLAIM
    assert claims["INVENTED_VALUES"] == "false"
    assert claims["PROTECTED_SURFACES_UNCHANGED"] == "true"


def test_canonical_pack_matches_executor_and_manifest() -> None:
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["TODAY_OBSERVATION_STATUS"] == "ABSENT"
    assert claims["CANDIDATE_STATUS"] == "ABSENT"
    assert claims["INITIAL_STOCK_ANCHOR_STATUS"] == "ABSENT"
    assert claims["LIVE_EQUITY_STOCK_KIND_SET"] == KIND_SET_EMPTY
    assert claims["EARLIEST_LIVE_CRITICAL_PATH_BLOCKER"] == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER


def test_runbook_bs_and_navigation_persist() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    br_section = RUNBOOK.read_text(encoding="utf-8")
    bs_section = _bs_section()
    assert OWNER_GO in bs_section
    assert "NEW_CANONICAL_SEMANTICS=true" in bs_section
    assert FORENSIC_PATH_PRODUCTIVE_STATUS in bs_section
    assert TODAY_SOURCE_KIND in bs_section
    assert EARLIEST_LIVE_CRITICAL_PATH_BLOCKER in bs_section
    assert NEXT_OWNER_GO_REQUIRED in bs_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.BS" in bs_section
    assert BR_HEADING in br_section
    assert "DOCS_TOKEN_FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_SOURCE_KIND_WP1" in spec
    assert "FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_SOURCE_KIND_WP1.md" in mot
    assert BS_HEADING in mot
    assert "RETIRED_FROM_PRODUCTIVE_CRITICAL_PATH" in mot
    assert "11.2.1.BS" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
