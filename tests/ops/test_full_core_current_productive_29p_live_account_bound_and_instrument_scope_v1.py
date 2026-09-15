"""CURRENT_PRODUCTIVE LAB + STEP-29P instrument-scope tests.

Injected transport only. No productive network. No POST.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_DEFAULT_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_ENABLED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    LiveAccountBoundStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_LEVERAGE_INFO,
    ENDPOINT_ACCOUNT_MAX_SIZE,
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_PUBLIC_INSTRUMENTS,
    ENDPOINT_PUBLIC_PRICE_LIMIT,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_29P_CANARY_INSTRUMENT_AUTHORITY_IMPORTED,
    CURRENT_PRODUCTIVE_29P_LAB_AND_INSTRUMENT_SCOPE_ADAPTER_CREATED,
    P01_RUNTIME_INSTANCE_PRESENT,
    SEALED_LEGACY_CENSUS_REOPENED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_live_account_bound_and_instrument_scope_v1 import (
    ALLOWED_OWNER_GOS,
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    PIN_OWNER_GO,
    CurrentProductiveLabInstrumentScopeError,
    execute_current_productive_lab_and_instrument_scope_for_29p_v1,
    require_current_productive_29p_bound_instrument_v1,
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
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops.test_full_core_fresh_pretrade_runtime_get_seam_v1 import (
    InjectedFreshGetTransportV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK_PATH = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "specs"
    / "FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_FOR_29P_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
CY_HEADING = (
    "### 11.2.1.CY FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_FOR_29P"
)
_TEST_INST = "SOL-USD_UM_XPERP-310410"
_TEST_TD = "cross"


def _bound(*, instrument_id: str = _TEST_INST) -> BoundInstrumentV1:
    return BoundInstrumentV1(
        instrument_id=instrument_id,
        venue_native_id=instrument_id,
        ranking_snapshot_id="rank-cy-1",
        ranking_integrity_digest="rank-digest-cy-1",
        universe_snapshot_id="uni-cy-1",
        selection_id="sel-cy-1",
        selection_integrity_digest="sel-digest-cy-1",
        selection_state=STATE_SELECTED_ACTIVE,
        selected_future_count=1,
        max_positions_effective=MAX_POSITIONS_EFFECTIVE,
    )


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


def _identity_payloads(*, instrument_id: str = _TEST_INST, uid: str | None = None):
    uid_value = uid or REUSED_BINDING_ACCOUNT_SCOPE
    inst_row = {"instId": instrument_id, "tdMode": _TEST_TD, "mgnMode": _TEST_TD}
    return {
        ENDPOINT_PUBLIC_INSTRUMENTS: {"code": "0", "data": [dict(inst_row)]},
        ENDPOINT_PUBLIC_PRICE_LIMIT: {"code": "0", "data": [{"instId": instrument_id}]},
        ENDPOINT_ACCOUNT_MAX_SIZE: {"code": "0", "data": [dict(inst_row)]},
        ENDPOINT_ACCOUNT_LEVERAGE_INFO: {"code": "0", "data": [dict(inst_row)]},
        ENDPOINT_ACCOUNT_CONFIG: {
            "code": "0",
            "data": [{"uid": uid_value, "acctLv": "2", "posMode": "net_mode"}],
        },
        ENDPOINT_ACCOUNT_POSITIONS: {"code": "0", "data": [{"mgnMode": _TEST_TD}]},
        ENDPOINT_ACCOUNT_BALANCE: json.loads(_balance(uid=uid_value).decode("utf-8")),
    }


def _run(
    tmp_path: Path,
    *,
    bound: BoundInstrumentV1 | None = None,
    config: bytes | None = None,
    balance: bytes | None = None,
    fresh: bool = True,
    owner_go: str = OWNER_GO,
) -> object:
    transport = RecordingFakeCanaryTransportV1(
        bodies_by_endpoint={
            "/api/v5/account/config": config if config is not None else _config(),
            "/api/v5/account/balance": balance if balance is not None else _balance(),
        }
    )
    fresh_transport = None
    if fresh is True and bound is not None:
        fresh_transport = InjectedFreshGetTransportV1(
            payloads=_identity_payloads(instrument_id=bound.venue_native_id)
        )
    return execute_current_productive_lab_and_instrument_scope_for_29p_v1(
        owner_go=owner_go,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        bound_instrument=bound,
        evidence_root=tmp_path / "pack",
        transport=transport,
        fresh_get_transport=fresh_transport,
        execute_get=True,
    )


def test_standing_pins_and_canary_not_imported() -> None:
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is False
    assert SEALED_LEGACY_CENSUS_REOPENED is False
    assert P01_RUNTIME_INSTANCE_PRESENT is False
    assert CURRENT_PRODUCTIVE_29P_LAB_AND_INSTRUMENT_SCOPE_ADAPTER_CREATED is True
    assert CURRENT_PRODUCTIVE_29P_CANARY_INSTRUMENT_AUTHORITY_IMPORTED is False
    assert PIN_OWNER_GO in ALLOWED_OWNER_GOS
    bound = _bound()
    required = require_current_productive_29p_bound_instrument_v1(bound)
    assert required.venue_native_id == _TEST_INST
    assert required.venue_native_id != CANARY_DEFAULT_INSTRUMENT_ID
    with pytest.raises(CurrentProductiveLabInstrumentScopeError, match="BOUND_INSTRUMENT_MISSING"):
        require_current_productive_29p_bound_instrument_v1(None)


def test_missing_bound_instrument_is_first_real_blocker(tmp_path: Path) -> None:
    result = _run(tmp_path, bound=None, fresh=False)
    assert result.instrument_scope_status.startswith("FAIL_CLOSED:")
    assert result.live_account_bound_status == LiveAccountBoundStatusV1.MISSING.value
    assert result.selected_instrument_id == ""
    assert result.p01_status == "DOES_NOT_APPLY"
    assert result.u01_status == "ELIGIBLE"
    assert result.first_real_blocker == (
        "CURRENT_PRODUCTIVE_CAP24_BOUND_INSTRUMENT_INSTANCE_MISSING"
    )
    assert result.blocker_class == "B"
    assert result.step_29p_risk_admissible == "false"
    assert result.post_count == "0"
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    assert claims["CANARY_INSTRUMENT_AUTHORITY_IMPORTED"] == "false"
    assert claims["SECRET_MATERIAL_PERSISTED"] is False
    assert claims["MAX_POSITIONS_EFFECTIVE"] == "1"
    assert verify_manifest_sha256_v1(store_root=tmp_path / "pack") == 0


def test_injected_bound_instrument_closes_lab_and_scope_without_productive_29p(
    tmp_path: Path,
) -> None:
    result = _run(tmp_path, bound=_bound())
    assert result.selected_instrument_id == _TEST_INST
    assert result.selected_instrument_id != CANARY_DEFAULT_INSTRUMENT_ID
    assert result.instrument_scope_status == "BOUND_TO_CAP24_SINGLE_SELECTED_FUTURE"
    assert result.live_account_bound_status == LiveAccountBoundStatusV1.TRUSTED_PRESENT.value
    assert result.single_selected_future_proven == "true"
    assert result.max_positions_effective == "1"
    assert result.u01_status == "ELIGIBLE"
    assert result.p01_status == "DOES_NOT_APPLY"
    assert result.fresh_usdc_availeq_status == "OBSERVED_THIS_EPOCH"
    assert result.risk_capital_mint_status == "MINTED"
    assert result.step_29p_risk_admissible == "false"
    assert result.first_real_blocker == (
        "CURRENT_PRODUCTIVE_29P_REQUIRES_PRODUCTIVE_TRUSTED_GET_AND_CAP24_BOUND_INSTRUMENT"
    )
    assert result.blocker_class == "C"
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    assert claims["STEP_29P_RISK_ADMISSIBLE_EVALUATOR"] == "true"
    assert claims["U04_SUBTRACTED"] == "false"
    matrix = claims["29P_PREDICATE_MATRIX"]["PREDICATE"]
    names = {row["PREDICATE"]: row for row in matrix}
    assert names["LIVE_ACCOUNT_BOUND_TRUSTED"]["BLOCKING"] is False
    assert names["INSTRUMENT_SCOPE_BOUND"]["BLOCKING"] is False
    assert names["CURRENT_PRODUCTIVE_STEP_29P_RISK_ADMISSIBLE"]["BLOCKING"] is True
    assert verify_manifest_sha256_v1(store_root=tmp_path / "pack") == 0


def test_canary_default_is_not_required_for_bound_instrument() -> None:
    bound = _bound(instrument_id=_TEST_INST)
    assert bound.venue_native_id != CANARY_DEFAULT_INSTRUMENT_ID
    require_current_productive_29p_bound_instrument_v1(bound)


def test_owner_go_sha_and_flag_fail_closed(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(body=_config())
    with pytest.raises(CurrentProductiveLabInstrumentScopeError, match="OWNER_GO_MISMATCH"):
        execute_current_productive_lab_and_instrument_scope_for_29p_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            bound_instrument=_bound(),
            evidence_root=tmp_path / "a",
            transport=transport,
            execute_get=True,
        )
    with pytest.raises(CurrentProductiveLabInstrumentScopeError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_current_productive_lab_and_instrument_scope_for_29p_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            bound_instrument=_bound(),
            evidence_root=tmp_path / "b",
            transport=transport,
            execute_get=True,
        )
    with pytest.raises(CurrentProductiveLabInstrumentScopeError, match="EXECUTE_GET_FLAG_REQUIRED"):
        execute_current_productive_lab_and_instrument_scope_for_29p_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            bound_instrument=_bound(),
            evidence_root=tmp_path / "c",
            transport=transport,
            execute_get=False,
        )


def test_ssot_docs_once_present() -> None:
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    assert CY_HEADING in runbook
    assert SPEC_PATH.name in mot
    assert (
        "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_FOR_29P_V1"
        in spec
    )
    assert "11.2.1.CY" in atlas
    assert "current_productive_29p_live_account_bound_and_instrument_scope_v1.py" in atlas
    pack = REPO_ROOT / CANONICAL_PACK_RELPATH
    claims = json.loads((pack / "claims.json").read_text(encoding="utf-8"))
    assert claims["CANARY_INSTRUMENT_AUTHORITY_IMPORTED"] == "false"
    assert claims["STEP_29P_RISK_ADMISSIBLE"] == "false"
    assert claims["POST_COUNT"] == "0"
    assert claims["P01_POLICY_DECISION"] == "DOES_NOT_APPLY"
    assert claims["FIRST_REAL_BLOCKER"] == (
        "CURRENT_PRODUCTIVE_CAP24_BOUND_INSTRUMENT_INSTANCE_MISSING"
    )
    assert verify_manifest_sha256_v1(store_root=pack) == 0
