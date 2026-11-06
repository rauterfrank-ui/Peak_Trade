"""Adversarial tests for PL-TF-002 network evidence contract verifier."""

from __future__ import annotations

import time
from typing import Any

import pytest

from src.ops.pl_tf_002_network_evidence_contract_v1.constants_v1 import (
    F1_REQUIRED_GET_ITEM_IDS,
    NE_TF_001_ENDPOINT_PATH,
    NE_TF_001_HTTP_METHOD,
    PL_TF_002_STATUS_CLOSED,
    PL_TF_002_STATUS_STANDING,
)
from src.ops.pl_tf_002_network_evidence_contract_v1.errors_v1 import PlTf002NetworkEvidenceError
from src.ops.pl_tf_002_network_evidence_contract_v1.normalize_v1 import (
    normalize_okx_account_config_perm_v1,
)
from src.ops.pl_tf_002_network_evidence_contract_v1.verifier_v1 import (
    verify_pl_tf_002_network_evidence_v1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.constants_v1 import (
    PL_TF_002_STATUS as TREASURY_NAVIGATION_PL_TF_002_STATUS,
    VENUE_PERMISSION_GET_PERFORMED,
    VENUE_PERMISSION_UNKNOWN,
)


def _f1_items(**overrides: object) -> dict[str, Any]:
    items: dict[str, Any] = {}
    for item_id in F1_REQUIRED_GET_ITEM_IDS:
        items[item_id] = {
            "get_performed": True,
            "method": "GET",
            "venue_live_contact": True,
            "transport_class": "FULL_CORE_PRODUCTIVE_READ_ONLY_GET_V1",
        }
    items.update(overrides)  # type: ignore[arg-type]
    return items


def _raw_config(*, perm: str, uid: str = "acct-uid-1") -> dict[str, Any]:
    return {"code": "0", "msg": "", "data": [{"uid": uid, "perm": perm, "posMode": "net_mode"}]}


def _synthetic_bundle(*, perm: str = "read_only", uid: str = "acct-uid-1") -> dict[str, Any]:
    now_ms = int(time.time() * 1000)
    return {
        "EVIDENCE_PROVENANCE": {
            "evidence_class": "PRODUCTIVE_VENUE_EVIDENCE",
            "transport_class": "FULL_CORE_PRODUCTIVE_READ_ONLY_GET_V1",
            "venue_live_contact": True,
            "fixture_or_injected": False,
            "historical_reuse": False,
            "observed_at_unix_ms": now_ms,
            "freshness_max_age_ms": 300_000,
            "expected_credential_uid": uid,
        },
        "F1_PRODUCTIVE_VENUE_GET": {"items": _f1_items()},
        "F2_NE_TF_001": {
            "task_id": "NE-TF-001",
            "http_method": NE_TF_001_HTTP_METHOD,
            "endpoint_path": NE_TF_001_ENDPOINT_PATH,
            "get_performed": True,
            "raw_venue_response": _raw_config(perm=perm, uid=uid),
        },
    }


def test_standing_constants_remain_frozen_after_synthetic_pass() -> None:
    result = verify_pl_tf_002_network_evidence_v1(_synthetic_bundle())
    assert result["VERIFICATION_RESULT"] == "PASS"
    assert result["PL_TF_002_CLOSURE_RESULT"]["closed"] is True
    assert result["PL_TF_002_CLOSURE_RESULT"]["status_if_closed"] == PL_TF_002_STATUS_CLOSED
    assert (
        result["PL_TF_002_CLOSURE_RESULT"]["standing_status_unchanged"] == PL_TF_002_STATUS_STANDING
    )
    assert PL_TF_002_STATUS_STANDING == "FROZEN_PENDING_NETWORK_EVIDENCE"
    assert TREASURY_NAVIGATION_PL_TF_002_STATUS == PL_TF_002_STATUS_CLOSED
    assert VENUE_PERMISSION_UNKNOWN is False
    assert VENUE_PERMISSION_GET_PERFORMED is True
    assert result["LIVE_MINTED"] is False
    assert result["RISK_ADMISSIBLE_MINTED"] is False
    assert result["TREASURY_AUTHORITY_MINTED"] is False


def test_missing_f1_item_fail_closed() -> None:
    bundle = _synthetic_bundle()
    items = dict(bundle["F1_PRODUCTIVE_VENUE_GET"]["items"])
    del items["AVAILABLE_MARGIN"]
    bundle["F1_PRODUCTIVE_VENUE_GET"]["items"] = items
    result = verify_pl_tf_002_network_evidence_v1(bundle)
    assert result["VERIFICATION_RESULT"] == "FAIL_CLOSED"
    assert any("F1_MISSING_ITEM:AVAILABLE_MARGIN" in r for r in result["REASONS"])


def test_missing_f2_block_fail_closed() -> None:
    bundle = _synthetic_bundle()
    del bundle["F2_NE_TF_001"]
    result = verify_pl_tf_002_network_evidence_v1(bundle)
    assert result["VERIFICATION_RESULT"] == "FAIL_CLOSED"
    assert "F2_BLOCK_MISSING" in result["REASONS"]


def test_unknown_permission_token_fail_closed() -> None:
    with pytest.raises(PlTf002NetworkEvidenceError, match="UNKNOWN_PERM_TOKEN"):
        normalize_okx_account_config_perm_v1(_raw_config(perm="read_only,mystery"))


def test_wrong_credential_uid_fail_closed() -> None:
    bundle = _synthetic_bundle(uid="acct-uid-1")
    bundle["EVIDENCE_PROVENANCE"]["expected_credential_uid"] = "other-uid"
    result = verify_pl_tf_002_network_evidence_v1(bundle)
    assert "F2_CREDENTIAL_UID_MISMATCH" in result["REASONS"]


def test_stale_evidence_fail_closed() -> None:
    bundle = _synthetic_bundle()
    bundle["EVIDENCE_PROVENANCE"]["observed_at_unix_ms"] = int(time.time() * 1000) - 400_000
    result = verify_pl_tf_002_network_evidence_v1(bundle)
    assert "EVIDENCE_STALE" in result["REASONS"]


def test_fixture_evidence_class_fail_closed() -> None:
    bundle = _synthetic_bundle()
    bundle["EVIDENCE_PROVENANCE"]["evidence_class"] = "INJECTED_TEST_DOUBLE"
    result = verify_pl_tf_002_network_evidence_v1(bundle)
    assert "EVIDENCE_CLASS_NOT_PRODUCTIVE" in result["REASONS"]


def test_malformed_venue_response_fail_closed() -> None:
    bundle = _synthetic_bundle()
    bundle["F2_NE_TF_001"]["raw_venue_response"] = {"code": "1", "data": []}
    result = verify_pl_tf_002_network_evidence_v1(bundle)
    assert any(
        "VENUE_CODE_NOT_ZERO" in r or "VENUE_DATA_ROW_COUNT_NOT_ONE" in r for r in result["REASONS"]
    )


def test_conflicting_trade_permission_fail_closed() -> None:
    bundle = _synthetic_bundle(perm="read_only,trade")
    result = verify_pl_tf_002_network_evidence_v1(bundle)
    assert "F3_TRADE_REQUIREMENT_FAIL" in result["REASONS"]


def test_unexpected_treasury_withdraw_capability_fail_closed() -> None:
    bundle = _synthetic_bundle(perm="read_only,withdraw")
    result = verify_pl_tf_002_network_evidence_v1(bundle)
    assert "F3_WITHDRAW_REQUIREMENT_FAIL" in result["REASONS"]
    assert "F3_UNEXPECTED_TREASURY_WITHDRAW_CAPABILITY" in result["REASONS"]


def test_owner_attestation_not_ne_tf_001_authority() -> None:
    bundle = _synthetic_bundle()
    bundle["F2_NE_TF_001"]["owner_permission_attestation"] = {
        "READ": True,
        "TRADE": False,
        "WITHDRAW": False,
    }
    result = verify_pl_tf_002_network_evidence_v1(bundle)
    assert "F2_OWNER_ATTESTATION_NOT_NE_TF_001_AUTHORITY" in result["REASONS"]


def test_secret_redaction_invariant() -> None:
    bundle = _synthetic_bundle()
    bundle["audit"] = {"api_key": "must-not-appear"}
    result = verify_pl_tf_002_network_evidence_v1(bundle)
    assert "SECRET_FIELD_PRESENT" in result["REASONS"][0]


def test_normalize_read_only_only() -> None:
    normalized = normalize_okx_account_config_perm_v1(_raw_config(perm="read_only"))
    assert normalized == {
        "READ": True,
        "TRADE": False,
        "WITHDRAW": False,
        "uid": "acct-uid-1",
        "perm_raw": "read_only",
        "perm_tokens": ["read_only"],
        "normalization_contract": "OKX_ACCOUNT_CONFIG_PERM_COMMA_TOKENS_V1",
        "source_field": "data[0].perm",
        "identity_field": "data[0].uid",
    }
