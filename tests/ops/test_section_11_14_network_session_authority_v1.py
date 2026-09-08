"""Owner Network-Session authority tests. No live POST. No network."""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    AUTHORITY_TYPE_OWNER_NETWORK_SESSION,
    BOUND_FROZEN_ENVELOPE_ID,
    BOUND_ORIGIN_MAIN_SHA,
    FLATTEN_CONFIRM_TOKEN_EXPECTED,
    INSTRUMENT_ID,
    NETWORK_SESSION_CONFIRM_TOKEN_EXPECTED,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.issuance_v1 import (
    current_section_11_14_issuance_explicit_v1,
    issue_owner_flatten_authority_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.network_session_authority_v1 import (
    current_section_11_14_network_session_explicit_v1,
    issue_owner_network_session_authority_v1,
    network_session_owner_contract_schema_v1,
    verify_owner_network_session_authority_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

ISSUED_AT = "2026-09-08T02:50:00Z"
PRODUCER_PATH = (
    Path(__file__).resolve().parents[2]
    / "src/ops/section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1"
    / "network_session_authority_v1.py"
)


def test_schema_is_not_issued_authority() -> None:
    schema = network_session_owner_contract_schema_v1()
    assert schema["ISSUED"] is False
    assert schema["EVALUATOR_IS_NOT_ISSUER"] is True
    assert schema["kind"] == AUTHORITY_TYPE_OWNER_NETWORK_SESSION
    assert schema["confirm_token_expected"] == NETWORK_SESSION_CONFIRM_TOKEN_EXPECTED
    assert schema["confirm_token_expected"] != FLATTEN_CONFIRM_TOKEN_EXPECTED


def test_standing_live_flags_are_not_session_authority() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert CANARY_AUTHORIZED is False
    assert POST_ALLOWED is False


def test_missing_issued_at_does_not_mint() -> None:
    explicit = current_section_11_14_network_session_explicit_v1(issued_at="")
    produced = issue_owner_network_session_authority_v1(explicit=explicit)
    assert produced["issued"] is False
    assert produced["artifact"] is None
    assert "NETWORK_SESSION_ISSUED_AT_REQUIRED" in produced["reasons"]


def test_chat_source_forbidden() -> None:
    explicit = current_section_11_14_network_session_explicit_v1(issued_at=ISSUED_AT)
    explicit["authority_source"] = "CHAT_DECLARATION"
    produced = issue_owner_network_session_authority_v1(explicit=explicit)
    assert produced["issued"] is False
    assert "NETWORK_SESSION_AUTHORITY_SOURCE_FORBIDDEN" in produced["reasons"]


def test_flatten_confirm_token_cannot_authorize_session() -> None:
    explicit = current_section_11_14_network_session_explicit_v1(issued_at=ISSUED_AT)
    explicit["confirm_token"] = FLATTEN_CONFIRM_TOKEN_EXPECTED
    produced = issue_owner_network_session_authority_v1(explicit=explicit)
    assert produced["issued"] is False
    assert "FLATTEN_CONFIRM_TOKEN_CANNOT_AUTHORIZE_NETWORK_SESSION" in produced["reasons"]


def test_flatten_issuance_artifact_cannot_verify_as_session() -> None:
    flatten = issue_owner_flatten_authority_v1(
        explicit=current_section_11_14_issuance_explicit_v1(issued_at=ISSUED_AT)
    )["artifact"]
    assert flatten is not None
    verdict = verify_owner_network_session_authority_v1(
        issuance=flatten,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert verdict["issued"] is False
    assert "FLATTEN_GRANT_CANNOT_AUTHORIZE_NETWORK_SESSION" in verdict["reasons"]


def test_producer_mints_only_from_explicit_owner_input() -> None:
    explicit = current_section_11_14_network_session_explicit_v1(issued_at=ISSUED_AT)
    produced = issue_owner_network_session_authority_v1(explicit=explicit)
    assert produced["issued"] is True
    artifact = produced["artifact"]
    assert artifact is not None
    assert artifact["issued_at"] == ISSUED_AT
    assert artifact["WIRE_SEND_NOT_AUTHORIZED_BY_THIS_REPAIR"] is True
    verdict = verify_owner_network_session_authority_v1(
        issuance=artifact,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert verdict["accepted"] is True
    assert verdict["issued"] is True
    assert verdict["WIRE_SEND_NOT_AUTHORIZED_BY_THIS_REPAIR"] is True


def test_evaluator_does_not_mint_when_artifact_missing() -> None:
    verdict = verify_owner_network_session_authority_v1(
        issuance=None,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert verdict["issued"] is False
    assert verdict["EVALUATOR_IS_NOT_ISSUER"] is True
    assert "NETWORK_SESSION_OWNER_AUTHORITY_MISSING" in verdict["reasons"]


def test_env_cli_and_fixture_sources_are_forbidden() -> None:
    src = PRODUCER_PATH.read_text(encoding="utf-8")
    assert "os.environ" not in src
    assert "os.getenv" not in src
    assert "argparse" not in src
    for forbidden in ("ENV", "CLI_FLAG", "TEST_FIXTURE"):
        explicit = current_section_11_14_network_session_explicit_v1(issued_at=ISSUED_AT)
        explicit["authority_source"] = forbidden
        produced = issue_owner_network_session_authority_v1(explicit=explicit)
        assert produced["issued"] is False
        assert "NETWORK_SESSION_AUTHORITY_SOURCE_FORBIDDEN" in produced["reasons"]


def test_live_flags_cannot_authorize_this_required() -> None:
    explicit = current_section_11_14_network_session_explicit_v1(issued_at=ISSUED_AT)
    explicit["live_flags_cannot_authorize_this"] = False
    produced = issue_owner_network_session_authority_v1(explicit=explicit)
    assert produced["issued"] is False
    assert "NETWORK_SESSION_LIVE_FLAGS_SEPARATION_REQUIRED" in produced["reasons"]
