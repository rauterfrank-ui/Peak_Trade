"""Fresh trusted USDC availEq GET + CU producer + 29P bind tests.

Injected transport only. No productive network. No POST.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    WIRE_SEND_PERMITTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_29P_FRESH_GET_AUTHORIZED_COUNT,
    CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT,
    CURRENT_PRODUCTIVE_29P_FRESH_GET_POST_COUNT,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_U04_APPLICATION,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY,
    P01_RUNTIME_INSTANCE_PRESENT,
    SEALED_LEGACY_CENSUS_REOPENED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_sizing_value_v1 import (
    ALLOWED_OWNER_GOS,
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    PIN_OWNER_GO,
    CurrentProductive29PFreshGetError,
    execute_current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    reject_direct_avail_eq_29p_claim_v1,
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
RUNBOOK_PATH = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs"
    / "FULL_CORE_CURRENT_PRODUCTIVE_29P_FRESH_TRUSTED_USDC_FREE_MARGIN_GET_AND_PRODUCE_SIZING_VALUE_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
CU_HEADING = "11.2.1.CU FULL_CORE_CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_MODEL"
CV_HEADING = (
    "11.2.1.CV FULL_CORE_CURRENT_PRODUCTIVE_29P_FRESH_TRUSTED_USDC_"
    "FREE_MARGIN_GET_AND_PRODUCE_SIZING_VALUE"
)


def _payload(
    *,
    uid: str | None = REUSED_BINDING_ACCOUNT_SCOPE,
    avail_eq: str = "123.45",
) -> bytes:
    account: dict[str, Any] = {
        "uTime": "1726400000000",
        "availEq": "999.00",
        "totalEq": "1000.00",
        "adjEq": "800.00",
        "details": [
            {
                "ccy": "USDC",
                "availEq": avail_eq,
                "availBal": "10.00",
                "cashBal": "11.00",
                "eq": "200.00",
                "uTime": "1726400000000",
            },
            {"ccy": "BTC", "availEq": "0.01", "uTime": "1726400000000"},
        ],
    }
    if uid is not None:
        account["uid"] = uid
    body = {"code": "0", "msg": "", "data": [account]}
    return json.dumps(body).encode("utf-8")


def _run(tmp_path: Path, *, body: bytes | None = None, owner_go: str = OWNER_GO):
    transport = RecordingFakeCanaryTransportV1(body=body or _payload())
    return execute_current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_v1(
        owner_go=owner_go,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "pack",
        transport=transport,
        execute_get=True,
    )


def test_standing_pins_remain_fail_closed() -> None:
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert SEALED_LEGACY_CENSUS_REOPENED is False
    assert P01_RUNTIME_INSTANCE_PRESENT is False
    assert CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT == "/api/v5/account/balance"
    assert CURRENT_PRODUCTIVE_29P_FRESH_GET_AUTHORIZED_COUNT == 1
    assert CURRENT_PRODUCTIVE_29P_FRESH_GET_POST_COUNT == 0
    assert PIN_OWNER_GO in ALLOWED_OWNER_GOS


def test_injected_get_observes_usdc_availeq_but_does_not_mint_without_p01(
    tmp_path: Path,
) -> None:
    result = _run(tmp_path, body=_payload(uid=None))
    assert result.fresh_get_executed == "true"
    assert result.http_status == "200"
    assert result.venue_code == "0"
    assert result.usdc_details_row_status == "EXACTLY_ONE_USDC_DETAILS_ROW_VALID"
    assert result.raw_usdc_availeq == "123.45"
    assert result.trusted_auth_status == "INJECTED_TEST_DOUBLE_NOT_PRODUCTIVE"
    assert result.p01_applicability == "UNKNOWN_FAIL_CLOSED"
    assert result.p01_status == "P01_DIRECTIVE_MISSING"
    assert result.producer_output_status == "FAIL_CLOSED"
    assert result.producer_output_value_usdc == ""
    assert result.u04_subtracted == "false"
    assert result.forbidden_fallback_used == "false"
    assert result.eq_used_as_source == "false"
    assert result.post_count == "0"
    assert result.step_29p_risk_admissible == "false"
    assert "CONSUMER_BOUND" in result.step_29p_value_binding_status
    assert "UNBOUND" in result.step_29p_value_binding_status
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    assert claims["PRODUCER_ALGEBRA"] == CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA
    assert claims["PRODUCER_IDENTITY"] == (
        CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY
    )
    assert claims["DOUBLE_COUNTING_GUARD"] == (CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_U04_APPLICATION)
    assert "ELIGIBILITY_FACT_MISSING" in claims["PRODUCER_REASON_CODES"] or (
        "P01_UNKNOWN_FAIL_CLOSED" in claims["PRODUCER_REASON_CODES"]
    )
    assert claims["LEGACY_CENSUS_REOPENED"] == "false"
    assert verify_manifest_sha256_v1(store_root=tmp_path / "pack") == 0
    gets = json.loads((tmp_path / "pack" / "GETS.json").read_text(encoding="utf-8"))
    assert gets["REQUESTS"][0]["ENDPOINT"] == "/api/v5/account/balance"
    assert gets["REQUESTS"][0]["OBSERVED_FIELD"] == "details[ccy=USDC].availEq"


def test_does_not_use_account_level_or_forbidden_fields_as_source(tmp_path: Path) -> None:
    result = _run(tmp_path)
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    assert result.raw_usdc_availeq == "123.45"
    assert result.raw_usdc_availeq != "999.00"
    assert claims["EQ_USED_AS_SOURCE"] == "false"
    assert claims["FORBIDDEN_FALLBACK_USED"] == "false"
    with pytest.raises(
        Exception,
        match="DIRECT_AVAILEQ_29P_CLAIM_FORBIDDEN_USE_PRODUCER",
    ):
        reject_direct_avail_eq_29p_claim_v1(claimed="availEq")


def test_ambiguous_usdc_row_fail_closed(tmp_path: Path) -> None:
    body = {
        "code": "0",
        "msg": "",
        "data": [
            {
                "uid": REUSED_BINDING_ACCOUNT_SCOPE,
                "details": [
                    {"ccy": "USDC", "availEq": "1.00", "uTime": "1"},
                    {"ccy": "USDC", "availEq": "2.00", "uTime": "1"},
                ],
            }
        ],
    }
    result = _run(tmp_path, body=json.dumps(body).encode("utf-8"))
    assert result.producer_output_status == "FAIL_CLOSED"
    assert "FAIL_CLOSED" in result.usdc_details_row_status
    assert result.raw_usdc_availeq == ""


def test_owner_go_and_sha_and_execute_flag_fail_closed(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(body=_payload())
    with pytest.raises(CurrentProductive29PFreshGetError, match="OWNER_GO_MISMATCH"):
        execute_current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "a",
            transport=transport,
            execute_get=True,
        )
    with pytest.raises(CurrentProductive29PFreshGetError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            evidence_root=tmp_path / "b",
            transport=transport,
            execute_get=True,
        )
    with pytest.raises(CurrentProductive29PFreshGetError, match="EXECUTE_GET_FLAG_REQUIRED"):
        execute_current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "c",
            transport=transport,
            execute_get=False,
        )


def test_wrong_payload_uid_fail_closed(tmp_path: Path) -> None:
    result = _run(tmp_path, body=_payload(uid="not-the-bound-account"))
    assert result.producer_output_status == "FAIL_CLOSED"
    assert "FAIL_CLOSED" in result.usdc_details_row_status
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    assert "ACCOUNT_IDENTITY_SCOPE_MISMATCH" in claims["GET_FAILURE_REASONS"]


def test_ssot_docs_once_present() -> None:
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    assert CU_HEADING in runbook
    assert CV_HEADING in runbook
    assert "DETAILS_USDC_AVAILEQ_MINUS_CONDITIONAL_P01_USDC_V1" in runbook
    assert SPEC_PATH.name in mot
    assert (
        "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_29P_FRESH_TRUSTED_USDC_"
        "FREE_MARGIN_GET_AND_PRODUCE_SIZING_VALUE_V1"
    ) in spec
    assert "11.2.1.CV" in atlas
    assert "current_productive_29p_fresh_trusted_usdc_free_margin_get" in atlas
    pack = REPO_ROOT / CANONICAL_PACK_RELPATH
    claims = json.loads((pack / "claims.json").read_text(encoding="utf-8"))
    assert claims["FRESH_GET_EXECUTED"] == "true"
    assert claims["POST_COUNT"] == "0"
    assert claims["STEP_29P_RISK_ADMISSIBLE"] == "false"
    assert claims["LEGACY_CENSUS_REOPENED"] == "false"
    assert verify_manifest_sha256_v1(store_root=pack) == 0
