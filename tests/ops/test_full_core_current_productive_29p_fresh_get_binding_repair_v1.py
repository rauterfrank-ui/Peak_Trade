"""Fresh GET binding repair v1 — mapping gate, K1 path, P01 policy, U01 fail-closed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 as equity_constants
import src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_p01_policy_v1 as p01_policy
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_sizing_value_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    CurrentProductive29PFreshGetError,
    execute_current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REQUIRED_SECRETREF_URI,
    REUSED_BINDING_ACCOUNT_SCOPE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)

assert CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is True
assert EXPECTED_ORIGIN_MAIN_SHA == "389cc5f91da08d30c9ae65af05b6d9f914e8ac45"


def _payload(
    *,
    uid: str | None = REUSED_BINDING_ACCOUNT_SCOPE,
    avail_eq: str = "123.45",
    acct_lv: str | None = None,
) -> bytes:
    account: dict[str, Any] = {
        "uTime": "1726400000000",
        "availEq": "999.00",
        "details": [
            {
                "ccy": "USDC",
                "availEq": avail_eq,
                "uTime": "1726400000000",
            },
        ],
    }
    if uid is not None:
        account["uid"] = uid
    if acct_lv is not None:
        account["acctLv"] = acct_lv
    body = {"code": "0", "msg": "", "data": [account]}
    return json.dumps(body).encode("utf-8")


def _vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "vault.json"
    material = {
        "api_key": "test-key-not-real",
        "api_secret": "test-secret-not-real",
        "passphrase": "test-pass-not-real",
    }
    path.write_text(
        json.dumps({REQUIRED_SECRETREF_URI: material}),
        encoding="utf-8",
    )
    return path


def test_mapping_false_blocks_before_network(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    transport = RecordingFakeCanaryTransportV1(body=_payload())
    monkeypatch.setattr(
        equity_constants,
        "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING",
        False,
    )
    with pytest.raises(
        CurrentProductive29PFreshGetError,
        match="CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING_FALSE",
    ):
        execute_current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
            transport=transport,
            execute_get=True,
        )
    assert transport.calls == []


def test_productive_path_requires_vault_file(tmp_path: Path) -> None:
    with pytest.raises(CurrentProductive29PFreshGetError, match="VAULT_FILE_REQUIRED"):
        execute_current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
            vault_file=None,
            transport=None,
            execute_get=True,
        )


def test_invalid_vault_fail_closed_before_get(tmp_path: Path) -> None:
    bad_vault = tmp_path / "bad.json"
    bad_vault.write_text("{}", encoding="utf-8")
    with pytest.raises(CurrentProductive29PFreshGetError, match="SECRETREF_URI_UNBOUND"):
        execute_current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
            vault_file=bad_vault,
            transport=None,
            execute_get=True,
        )


def test_k1_credential_path_reaches_read_only_get_boundary_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_sizing_value_v1 as fresh_get_mod

    recorded_calls: list[RecordingFakeCanaryTransportV1] = []

    class FakeUrllibTransport:
        wire_send_enabled = True

        def __init__(self, **_kwargs: object) -> None:
            self._rec = RecordingFakeCanaryTransportV1(body=_payload())
            recorded_calls.append(self._rec)

        def send(self, request: object) -> object:
            return self._rec.send(request)  # type: ignore[arg-type]

    monkeypatch.setattr(fresh_get_mod, "UrllibLiveCanaryTransportV1", FakeUrllibTransport)
    vault = _vault_file(tmp_path)
    result = execute_current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "pack",
        vault_file=vault,
        transport=None,
        execute_get=True,
    )
    assert len(recorded_calls) == 1
    recorded = recorded_calls[0]
    assert len(recorded.calls) == 1
    assert recorded.calls[0].method == "GET"
    assert recorded.calls[0].endpoint == "/api/v5/account/balance"
    assert result.post_count == "0"
    headers = {k.upper(): v for k, v in recorded.calls[0].headers.items()}
    assert "OK-ACCESS-KEY" in headers
    assert "test-key-not-real" not in json.dumps(
        json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    )


def test_p01_policy_does_not_apply_consumed_without_u01(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(body=_payload(uid=None))
    result = execute_current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "pack",
        transport=transport,
        execute_get=True,
    )
    assert result.p01_applicability == "DOES_NOT_APPLY"
    assert result.producer_output_status == "FAIL_CLOSED"
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    assert claims["P01_DIRECTIVE_SOURCE"] == "CURRENT_PRODUCTIVE_P01_POLICY_DOES_NOT_APPLY_V1"
    assert "ELIGIBILITY_FACT_MISSING" in claims["PRODUCER_REASON_CODES"]
    assert claims["ELIGIBILITY_STATUS"] == "ACCT_LV_ABSENT_FROM_AUTHORIZED_BALANCE_RESPONSE"
    assert result.u04_subtracted == "false"


def test_p01_policy_authority_ambiguous_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    transport = RecordingFakeCanaryTransportV1(body=_payload())
    monkeypatch.setattr(p01_policy, "CURRENT_PRODUCTIVE_P01_POLICY_DECISION", "APPLIES")
    with pytest.raises(
        CurrentProductive29PFreshGetError,
        match="P01_POLICY_AUTHORITY_UNREACHABLE",
    ):
        execute_current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
            transport=transport,
            execute_get=True,
        )
    assert transport.calls == []


def test_u01_minted_only_when_acct_lv_in_same_balance_response(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(body=_payload(acct_lv="2"))
    result = execute_current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "pack",
        transport=transport,
        execute_get=True,
    )
    assert result.p01_applicability == "DOES_NOT_APPLY"
    assert result.producer_output_status == "PRODUCED"
    assert result.producer_output_value_usdc == "123.45"
    assert result.u04_subtracted == "false"
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    assert claims["ELIGIBILITY_STATUS"] == "ELIGIBILITY_FROM_SAME_AUTHORIZED_BALANCE_RESPONSE"


def test_stale_origin_main_sha_rejected(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(body=_payload())
    with pytest.raises(CurrentProductive29PFreshGetError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_v1(
            owner_go=OWNER_GO,
            origin_main_sha="62ac12d8167757aeaa145af03d0e972772385195",
            evidence_root=tmp_path / "pack",
            transport=transport,
            execute_get=True,
        )
