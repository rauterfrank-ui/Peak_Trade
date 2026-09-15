"""CURRENT_PRODUCTIVE P01 policy replacement and 29P continuation tests.

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
    CURRENT_PRODUCTIVE_P01_INDEPENDENT_SAFETY_FUNCTION,
    CURRENT_PRODUCTIVE_P01_POLICY_BINDING_PRESENT,
    CURRENT_PRODUCTIVE_P01_POLICY_CREATED,
    CURRENT_PRODUCTIVE_P01_POLICY_DECISION,
    CURRENT_PRODUCTIVE_P01_POLICY_DECISION_BASIS,
    CURRENT_PRODUCTIVE_P01_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT,
    P01_RUNTIME_INSTANCE_PRESENT,
    SEALED_LEGACY_CENSUS_REOPENED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_p01_policy_v1 import (
    evaluate_current_productive_p01_policy_v1,
    mint_current_productive_p01_does_not_apply_directive_v1,
    reject_missing_as_does_not_apply_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_p01_policy_replacement_and_29p_continuation_v1 import (
    ALLOWED_OWNER_GOS,
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    PIN_OWNER_GO,
    CurrentProductiveP01PolicyContinuationError,
    execute_current_productive_p01_policy_replacement_and_29p_continuation_v1,
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
    / "FULL_CORE_CURRENT_PRODUCTIVE_P01_POLICY_REPLACEMENT_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
CX_HEADING = "### 11.2.1.CX FULL_CORE_CURRENT_PRODUCTIVE_P01_POLICY_REPLACEMENT"


def _config(*, acct_lv: object = "2", uid: str | None = None, code: str = "0") -> bytes:
    row: dict[str, object] = {
        "uid": uid or REUSED_BINDING_ACCOUNT_SCOPE,
        "posMode": "net_mode",
    }
    if acct_lv is not None:
        row["acctLv"] = acct_lv
    return json.dumps({"code": code, "data": [row], "msg": ""}).encode("utf-8")


def _balance(*, uid: str | None = None, avail_eq: str = "123.45") -> bytes:
    account: dict[str, object] = {
        "uTime": "1726400000000",
        "availEq": "999.00",
        "totalEq": "1000.00",
        "adjEq": "800.00",
        "uid": uid or REUSED_BINDING_ACCOUNT_SCOPE,
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
    return json.dumps({"code": "0", "msg": "", "data": [account]}).encode("utf-8")


def _run(
    tmp_path: Path,
    *,
    config: bytes | None = None,
    balance: bytes | None = None,
    owner_go: str = OWNER_GO,
) -> object:
    transport = RecordingFakeCanaryTransportV1(
        bodies_by_endpoint={
            "/api/v5/account/config": config if config is not None else _config(),
            "/api/v5/account/balance": balance if balance is not None else _balance(),
        }
    )
    return execute_current_productive_p01_policy_replacement_and_29p_continuation_v1(
        owner_go=owner_go,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "pack",
        transport=transport,
        execute_get=True,
    )


def test_standing_pins_and_missing_remain_unknown() -> None:
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert SEALED_LEGACY_CENSUS_REOPENED is False
    assert P01_RUNTIME_INSTANCE_PRESENT is False
    assert CURRENT_PRODUCTIVE_P01_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT is False
    assert CURRENT_PRODUCTIVE_P01_POLICY_CREATED is True
    assert CURRENT_PRODUCTIVE_P01_POLICY_DECISION == "DOES_NOT_APPLY"
    assert CURRENT_PRODUCTIVE_P01_POLICY_DECISION_BASIS == (
        "ARCHITECTURAL_REDUNDANCY_NOT_HISTORICAL_ABSENCE"
    )
    assert CURRENT_PRODUCTIVE_P01_INDEPENDENT_SAFETY_FUNCTION is False
    assert CURRENT_PRODUCTIVE_P01_POLICY_BINDING_PRESENT is True
    missing = reject_missing_as_does_not_apply_v1()
    assert missing.decision_state == "UNKNOWN_FAIL_CLOSED"
    assert missing.reason_code == "P01_DIRECTIVE_MISSING"
    decision = evaluate_current_productive_p01_policy_v1()
    assert decision.decision_state == "DOES_NOT_APPLY"
    assert decision.ready == "true"
    directive = mint_current_productive_p01_does_not_apply_directive_v1()
    assert directive.applicability_state == "DOES_NOT_APPLY"
    assert PIN_OWNER_GO in ALLOWED_OWNER_GOS


def test_injected_happy_path_mints_without_u04_or_29p_admit(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.p01_applicability == "DOES_NOT_APPLY"
    assert result.p01_directive_status == "RATIFIED_CURRENT_PRODUCTIVE_DOES_NOT_APPLY"
    assert result.u01_status == "ELIGIBLE"
    assert result.fresh_usdc_availeq_status == "OBSERVED_THIS_EPOCH"
    assert result.raw_usdc_availeq == "123.45"
    assert result.risk_capital_mint_status == "MINTED"
    assert result.producer_output_value_usdc == "123.45"
    assert result.step_29p_risk_admissible == "false"
    assert result.post_count == "0"
    assert "LIVE_ACCOUNT_BOUND" in result.first_real_blocker
    assert "INSTRUMENT_SCOPE" in result.first_real_blocker
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    assert claims["U04_SUBTRACTED"] == "false"
    assert claims["P01_LEGACY_RECONSTRUCTION_PERFORMED"] == "false"
    assert claims["P01_RUNTIME_INSTANCE_PRESENT"] == "false"
    assert claims["P01_DECISION_BASIS"] == "ARCHITECTURAL_REDUNDANCY_NOT_HISTORICAL_ABSENCE"
    assert claims["29P_PREDICATE_MATRIX"]["U04_NOT_SUBTRACTED"] is True
    assert claims["29P_PREDICATE_MATRIX"]["P01_DOES_NOT_APPLY"] is True
    p01 = json.loads((tmp_path / "pack" / "p01_resolution_v1.json").read_text(encoding="utf-8"))
    assert p01["decision_state"] == "DOES_NOT_APPLY"
    assert p01["normalized_from_missing"] == "false"
    coverage = json.loads(
        (tmp_path / "pack" / "coverage_matrix_v1.json").read_text(encoding="utf-8")
    )
    assert all(row["P01_NEEDED"] == "false" for row in coverage["COVERAGE"])
    protected = json.loads(
        (tmp_path / "pack" / "protected_surfaces_v1.json").read_text(encoding="utf-8")
    )
    assert protected["MASTER_V2_UNCHANGED"] == "true"
    assert protected["MAX_POSITIONS_ONE_UNCHANGED"] == "true"
    assert verify_manifest_sha256_v1(store_root=tmp_path / "pack") == 0
    assert result.manifest_verify_rc == 0


def test_empty_evaluator_is_not_does_not_apply() -> None:
    missing = evaluate_current_productive_p01_policy_v1(directives=())
    assert missing.decision_state == "UNKNOWN_FAIL_CLOSED"
    assert missing.reason_code == "P01_DIRECTIVE_MISSING"


def test_u01_ineligible_does_not_mint(tmp_path: Path) -> None:
    result = _run(tmp_path, config=_config(acct_lv="1"))
    assert result.u01_status == "INELIGIBLE"
    assert result.risk_capital_mint_status == "UNMINTED"
    assert result.p01_applicability == "DOES_NOT_APPLY"
    assert result.first_real_blocker == "CURRENT_PRODUCTIVE_U01_ELIGIBILITY_NOT_MINTED"


def test_owner_go_sha_and_flag_fail_closed(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(body=_config())
    with pytest.raises(CurrentProductiveP01PolicyContinuationError, match="OWNER_GO_MISMATCH"):
        execute_current_productive_p01_policy_replacement_and_29p_continuation_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "a",
            transport=transport,
            execute_get=True,
        )
    with pytest.raises(
        CurrentProductiveP01PolicyContinuationError, match="ORIGIN_MAIN_SHA_MISMATCH"
    ):
        execute_current_productive_p01_policy_replacement_and_29p_continuation_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            evidence_root=tmp_path / "b",
            transport=transport,
            execute_get=True,
        )
    with pytest.raises(
        CurrentProductiveP01PolicyContinuationError, match="EXECUTE_GET_FLAG_REQUIRED"
    ):
        execute_current_productive_p01_policy_replacement_and_29p_continuation_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "c",
            transport=transport,
            execute_get=False,
        )


def test_ssot_docs_once_present() -> None:
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    assert CX_HEADING in runbook
    assert SPEC_PATH.name in mot
    assert "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_P01_POLICY_REPLACEMENT_V1" in spec
    assert "11.2.1.CX" in atlas
    assert "current_productive_p01_policy_v1.py" in atlas
    assert "current_productive_p01_policy_replacement_and_29p_continuation_v1.py" in atlas
    pack = REPO_ROOT / CANONICAL_PACK_RELPATH
    claims = json.loads((pack / "claims.json").read_text(encoding="utf-8"))
    assert claims["P01_POLICY_DECISION"] == "DOES_NOT_APPLY"
    assert claims["P01_LEGACY_RECONSTRUCTION_PERFORMED"] == "false"
    assert claims["STEP_29P_RISK_ADMISSIBLE"] == "false"
    assert claims["POST_COUNT"] == "0"
    assert claims["P01_RUNTIME_INSTANCE_PRESENT"] == "false"
    assert verify_manifest_sha256_v1(store_root=pack) == 0
