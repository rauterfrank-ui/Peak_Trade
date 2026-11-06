"""CURRENT_PRODUCTIVE U01 account-mode adapter and ratification tests.

Injected transport only. No productive network. No POST.
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
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_U01_CANONICAL_SEMANTIC_TOKEN,
    CURRENT_PRODUCTIVE_U01_GET_ENDPOINT,
    CURRENT_PRODUCTIVE_U01_OPEN_AUTHORITY_STATUS,
    CURRENT_PRODUCTIVE_U01_REQUIRED_RAW_TOKEN,
    P01_RUNTIME_INSTANCE_PRESENT,
    SEALED_LEGACY_CENSUS_REOPENED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    REQUIRED_ACCOUNT_MODE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u01_account_mode_adapter_v1 import (
    REQUIRED_RAW_TOKEN,
    adapt_current_productive_u01_account_mode_v1,
    build_current_productive_u01_eligibility_fact_v1,
    extract_raw_acct_lv_from_account_config_payload_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u01_account_mode_semantic_ratification_v1 import (
    ALLOWED_OWNER_GOS,
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    PIN_OWNER_GO,
    CurrentProductiveU01RatificationError,
    execute_current_productive_u01_account_mode_semantic_ratification_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_ACCOUNT_SCOPE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK_PATH = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "specs"
    / "FULL_CORE_CURRENT_PRODUCTIVE_U01_ACCOUNT_MODE_SEMANTIC_RATIFICATION_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
CW_HEADING = "### 11.2.1.CW FULL_CORE_CURRENT_PRODUCTIVE_U01_ACCOUNT_MODE_SEMANTIC_RATIFICATION"


def _payload(*, acct_lv: object = "2", uid: str | None = None, code: str = "0") -> bytes:
    row: dict[str, object] = {
        "uid": uid or REUSED_BINDING_ACCOUNT_SCOPE,
        "posMode": "net_mode",
    }
    if acct_lv is not None:
        row["acctLv"] = acct_lv
    return json.dumps({"code": code, "data": [row], "msg": ""}).encode("utf-8")


def _run(tmp_path: Path, *, body: bytes) -> object:
    transport = RecordingFakeCanaryTransportV1(body=body)
    return execute_current_productive_u01_account_mode_semantic_ratification_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "pack",
        transport=transport,
        execute_get=True,
    )


def test_standing_pins() -> None:
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert P01_RUNTIME_INSTANCE_PRESENT is False
    assert SEALED_LEGACY_CENSUS_REOPENED is False
    assert REQUIRED_ACCOUNT_MODE == "FUTURES_MODE"
    assert CURRENT_PRODUCTIVE_U01_CANONICAL_SEMANTIC_TOKEN == "FUTURES_MODE"
    assert CURRENT_PRODUCTIVE_U01_REQUIRED_RAW_TOKEN == "2"
    assert CURRENT_PRODUCTIVE_U01_OPEN_AUTHORITY_STATUS == (
        "RETIRED_NOT_CURRENT_PRODUCTIVE_AUTHORITY"
    )
    assert CURRENT_PRODUCTIVE_U01_GET_ENDPOINT == "/api/v5/account/config"
    assert OWNER_GO in ALLOWED_OWNER_GOS
    assert PIN_OWNER_GO in ALLOWED_OWNER_GOS


def test_raw_2_maps_to_futures_mode_and_mints_eligibility() -> None:
    adaptation = adapt_current_productive_u01_account_mode_v1("2")
    assert adaptation.status == "ELIGIBLE"
    assert adaptation.raw_token == "2"
    assert adaptation.semantic_token == "FUTURES_MODE"
    assert adaptation.eligible == "true"
    assert adaptation.raw_rewritten == "false"
    fact = build_current_productive_u01_eligibility_fact_v1(
        adaptation=adaptation,
        bound_account_identity="acct-1",
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch="2026-09-15T11:28:00Z",
        provenance_digest="a" * 64,
    )
    assert fact is not None
    assert fact.account_mode == "FUTURES_MODE"
    assert fact.fact_id == "CURRENT_PRODUCTIVE_U01_ACCOUNT_ELIGIBILITY"


def test_non_2_missing_unknown_and_open_fail_closed() -> None:
    for raw, expected in (
        ("1", "U01_RAW_ACCT_LV_NOT_REQUIRED_2"),
        ("3", "U01_RAW_ACCT_LV_NOT_REQUIRED_2"),
        ("4", "U01_RAW_ACCT_LV_NOT_REQUIRED_2"),
        ("9", "U01_RAW_ACCT_LV_UNMAPPED"),
        ("OPEN", "U01_OPEN_IS_NOT_CURRENT_PRODUCTIVE_AUTHORITY"),
        ("", "U01_RAW_ACCT_LV_EMPTY"),
        (None, "U01_RAW_ACCT_LV_MISSING"),
        (2, "U01_RAW_ACCT_LV_NOT_STRING"),
    ):
        adaptation = adapt_current_productive_u01_account_mode_v1(raw)
        assert adaptation.eligible == "false"
        assert expected in adaptation.reason_codes
        assert adaptation.raw_rewritten == "false"
        assert adaptation.semantic_token != REQUIRED_RAW_TOKEN or adaptation.eligible == "false"


def test_payload_extract_preserves_raw_2() -> None:
    payload = json.loads(_payload().decode("utf-8"))
    adaptation = extract_raw_acct_lv_from_account_config_payload_v1(payload)
    assert adaptation.raw_token == "2"
    assert adaptation.semantic_token == "FUTURES_MODE"
    assert payload["data"][0]["acctLv"] == "2"


def test_happy_path_mints_u01_and_stops_at_p01(tmp_path: Path) -> None:
    result = _run(tmp_path, body=_payload())
    assert result.fresh_get_executed == "true"
    assert result.raw_acct_lv == "2"
    assert result.semantic_account_mode == "FUTURES_MODE"
    assert result.u01_status == "ELIGIBLE"
    assert result.u01_runtime_fact_status == "MINTED_CURRENT_PRODUCTIVE_U01_ELIGIBILITY_FACT"
    assert result.p01_applicability == "UNKNOWN_FAIL_CLOSED"
    assert result.p01_status == "P01_DIRECTIVE_MISSING"
    assert result.fresh_usdc_availeq_status == "NOT_REACHED_P01_REAL_BLOCKER"
    assert result.risk_capital_mint_status == "NOT_REACHED_UNMINTED"
    assert result.step_29p_risk_admissible == "false"
    assert result.first_real_blocker == (
        "P01_DIRECTIVE_MISSING_OWNER_MUST_RATIFY_APPLIES_OR_DOES_NOT_APPLY"
    )
    assert result.post_count == "0"
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    assert claims["U01_RAW_REWRITTEN"] == "false"
    assert claims["P01_INFERRED_DOES_NOT_APPLY"] == "false"
    assert claims["OPEN_CURRENT_PRODUCTIVE_AUTHORITY_STATUS"] == (
        "RETIRED_NOT_CURRENT_PRODUCTIVE_AUTHORITY"
    )
    snapshot = json.loads(
        (tmp_path / "pack" / "GET_SNAPSHOT.sanitized.json").read_text(encoding="utf-8")
    )
    assert snapshot["RAW_ACCT_LV_PRESERVED"] == "2"
    assert snapshot["RAW_NOT_REWRITTEN"] is True
    p01 = json.loads((tmp_path / "pack" / "p01_resolution_v1.json").read_text(encoding="utf-8"))
    assert p01["decision_state"] == "UNKNOWN_FAIL_CLOSED"
    assert p01["normalized_to_does_not_apply"] == "false"
    assert verify_manifest_sha256_v1(store_root=tmp_path / "pack") == 0


def test_non_2_and_missing_fail_closed_without_mint(tmp_path: Path) -> None:
    non_two = _run(tmp_path / "a", body=_payload(acct_lv="1"))
    assert non_two.u01_status == "INELIGIBLE"
    assert non_two.u01_runtime_fact_status == ("MISSING_NO_CURRENT_PRODUCTIVE_U01_RUNTIME_INSTANCE")
    missing = _run(tmp_path / "b", body=_payload(acct_lv=None))
    assert missing.u01_runtime_fact_status == ("MISSING_NO_CURRENT_PRODUCTIVE_U01_RUNTIME_INSTANCE")
    assert missing.p01_applicability == "UNKNOWN_FAIL_CLOSED"


def test_owner_go_sha_and_flag_fail_closed(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(body=_payload())
    with pytest.raises(CurrentProductiveU01RatificationError, match="OWNER_GO_MISMATCH"):
        execute_current_productive_u01_account_mode_semantic_ratification_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "a",
            transport=transport,
            execute_get=True,
        )
    with pytest.raises(CurrentProductiveU01RatificationError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_current_productive_u01_account_mode_semantic_ratification_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            evidence_root=tmp_path / "b",
            transport=transport,
            execute_get=True,
        )
    with pytest.raises(CurrentProductiveU01RatificationError, match="EXECUTE_GET_FLAG_REQUIRED"):
        execute_current_productive_u01_account_mode_semantic_ratification_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "c",
            transport=transport,
            execute_get=False,
        )


def test_wrong_uid_fail_closed(tmp_path: Path) -> None:
    result = _run(tmp_path, body=_payload(uid="not-the-bound-account"))
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    assert "ACCOUNT_IDENTITY_SCOPE_MISMATCH" in claims["GET_FAILURE_REASONS"]
    assert result.u01_runtime_fact_status == ("MISSING_NO_CURRENT_PRODUCTIVE_U01_RUNTIME_INSTANCE")


def test_ssot_docs_once_present() -> None:
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    assert CW_HEADING in runbook
    assert SPEC_PATH.name in mot
    assert (
        "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_U01_ACCOUNT_MODE_SEMANTIC_RATIFICATION_V1" in spec
    )
    assert "11.2.1.CW" in atlas
    assert "current_productive_u01_account_mode_adapter_v1.py" in atlas
    pack = REPO_ROOT / CANONICAL_PACK_RELPATH
    claims = json.loads((pack / "claims.json").read_text(encoding="utf-8"))
    assert claims["U01_CANONICAL_RAW_TOKEN"] == "2"
    assert claims["U01_CANONICAL_SEMANTIC_TOKEN"] == "FUTURES_MODE"
    assert claims["P01_APPLICABILITY"] == "UNKNOWN_FAIL_CLOSED"
    assert claims["STEP_29P_RISK_ADMISSIBLE"] == "false"
    assert claims["POST_COUNT"] == "0"
    assert verify_manifest_sha256_v1(store_root=pack) == 0
