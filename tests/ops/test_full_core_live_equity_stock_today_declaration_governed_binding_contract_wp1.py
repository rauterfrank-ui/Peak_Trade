"""Today declaration governed-binding contract tests.

System-bound candidate from D4 + fresh config/balance GET pair.
eq is not totalEq/eqUsd. Candidate is not ratification or anchor.
KIND_SET stays empty. No POST.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    WIRE_SEND_PERMITTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_remaining_unknown_kind_semantics_v1 import (
    KIND_SET_EMPTY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_declaration_governed_binding_contract_v1 import (
    ACCOUNT_IDENTITY_BINDING,
    AS_OF_TIME_SEMANTIC,
    CONTRACT_VERSION,
    EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
    ECONOMIC_MEANING,
    EQUITY_PRECISION_SEMANTIC,
    EQUITY_UNIT,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_GO,
    SETTLEMENT_CURRENCY_BINDING,
    TODAY_SOURCE_TYPE,
    TodayDeclarationGovernedBindingContractError,
    build_system_bound_today_candidate_v1,
    derive_declaration_id_v1,
    execute_live_equity_stock_today_declaration_governed_binding_contract_v1,
    extract_account_config_join_facts_v1,
    extract_settlement_eq_row_v1,
    join_fresh_acquisition_to_d4_v1,
    lexical_decimal_scale_of_exact_equity_value_string_v1,
    semantic_candidate_digest_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_source_kind_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BS_PACK_RELPATH,
    TODAY_SOURCE_KIND,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_CONFIG,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_LIVE_EQUITY_STOCK_TODAY_DECLARATION_GOVERNED_BINDING_CONTRACT_WP1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
BS_HEADING = "11.2.1.BS FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_SOURCE_KIND"
BT_HEADING = "11.2.1.BT FULL_CORE_LIVE_EQUITY_STOCK_TODAY_DECLARATION_GOVERNED_BINDING_CONTRACT"
SEALED_BS = REPO_ROOT / CANONICAL_BS_PACK_RELPATH
D4_UID = "856964404452495999"
D4_CCY = "USDC"
BALANCE_REQUEST_UTC = "2026-09-14T17:31:00Z"
CONFIG_REQUEST_UTC = "2026-09-14T17:30:59Z"
VENUE_ACCOUNT_UTIME = "1757872260000"
VENUE_ROW_UTIME = "1757872260123"
EQ_VALUE = "123.450000"


def _config_payload(
    *, uid: str = D4_UID, settle: str = D4_CCY, acct: str = "2", pos: str = "net_mode"
) -> dict:
    return {
        "code": "0",
        "data": [
            {
                "uid": uid,
                "mainUid": uid,
                "settleCcy": settle,
                "acctLv": acct,
                "posMode": pos,
            }
        ],
    }


def _balance_payload(
    *,
    eq: str = EQ_VALUE,
    extra_rows: list[dict] | None = None,
    include_usdc: bool = True,
    total_eq: str = "999.00",
    account_utime: str = VENUE_ACCOUNT_UTIME,
    row_utime: str = VENUE_ROW_UTIME,
    eq_as_number: bool = False,
) -> dict:
    details: list[dict] = []
    if include_usdc:
        details.append(
            {
                "ccy": D4_CCY,
                "eq": 123.45 if eq_as_number else eq,
                "cashBal": "10.00",
                "availEq": "5.00",
                "eqUsd": "123.45",
                "adjEq": "1.00",
                "uTime": row_utime,
            }
        )
    details.append({"ccy": "BTC", "eq": "0.01", "uTime": row_utime})
    if extra_rows:
        details.extend(extra_rows)
    return {
        "code": "0",
        "data": [
            {
                "totalEq": total_eq,
                "eqUsd": "999.00",
                "adjEq": "1.00",
                "cashBal": "10.00",
                "uTime": account_utime,
                "details": details,
            }
        ],
    }


def _bodies(*, config: dict | None = None, balance: dict | None = None) -> dict[str, bytes]:
    return {
        ENDPOINT_ACCOUNT_CONFIG: json.dumps(
            config if config is not None else _config_payload(),
            separators=(",", ":"),
        ).encode("utf-8"),
        ENDPOINT_ACCOUNT_BALANCE: json.dumps(
            balance if balance is not None else _balance_payload(),
            separators=(",", ":"),
        ).encode("utf-8"),
    }


def _run(tmp_path: Path, *, config: dict | None = None, balance: dict | None = None):
    transport = RecordingFakeCanaryTransportV1(
        bodies_by_endpoint=_bodies(config=config, balance=balance)
    )
    return execute_live_equity_stock_today_declaration_governed_binding_contract_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        repo_root=REPO_ROOT,
        evidence_root=tmp_path / "bt_pack",
        sealed_bs_pack=SEALED_BS,
        transport=transport,
    )


def _bt_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BT_HEADING)
    return runbook[start : runbook.index("## 11.3 Autonomy state model", start)]


def test_owner_go_and_sha_mismatch_fail_closed(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(bodies_by_endpoint=_bodies())
    with pytest.raises(TodayDeclarationGovernedBindingContractError, match="OWNER_GO_MISMATCH"):
        execute_live_equity_stock_today_declaration_governed_binding_contract_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            repo_root=REPO_ROOT,
            evidence_root=tmp_path,
            sealed_bs_pack=SEALED_BS,
            transport=transport,
        )
    with pytest.raises(
        TodayDeclarationGovernedBindingContractError, match="ORIGIN_MAIN_SHA_MISMATCH"
    ):
        execute_live_equity_stock_today_declaration_governed_binding_contract_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            repo_root=REPO_ROOT,
            evidence_root=tmp_path,
            sealed_bs_pack=SEALED_BS,
            transport=transport,
        )


def test_eq_not_collapsed_into_totaleq_or_equsd(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.equity_value == EQ_VALUE
    assert result.equity_value != "999.00"
    assert result.equity_value != "123.45"
    candidate = json.loads(
        (Path(result.store_root) / "system_bound_today_initial_stock_candidate_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert candidate["equity_value_field"] == "eq"
    assert candidate["equity_value"] == EQ_VALUE
    assert "totalEq" not in candidate["equity_value"]
    assert candidate["venue_eq_source_authority"] == "false"


def test_config_uid_mismatch_fail_closed() -> None:
    facts = extract_account_config_join_facts_v1(_config_payload(uid="999"))
    with pytest.raises(
        TodayDeclarationGovernedBindingContractError, match="CONFIG_UID_D4_MISMATCH"
    ):
        join_fresh_acquisition_to_d4_v1(
            config=facts,
            d4_bound_account_identity=D4_UID,
            d4_settlement_currency=D4_CCY,
        )


def test_settle_ccy_mismatch_fail_closed() -> None:
    facts = extract_account_config_join_facts_v1(_config_payload(settle="USDT"))
    with pytest.raises(
        TodayDeclarationGovernedBindingContractError, match="CONFIG_SETTLE_CCY_D4_MISMATCH"
    ):
        join_fresh_acquisition_to_d4_v1(
            config=facts,
            d4_bound_account_identity=D4_UID,
            d4_settlement_currency=D4_CCY,
        )


def test_acctlv_and_posmode_mismatch_fail_closed() -> None:
    facts = extract_account_config_join_facts_v1(_config_payload(acct="1"))
    with pytest.raises(
        TodayDeclarationGovernedBindingContractError, match="CONFIG_ACCTLV_MISMATCH"
    ):
        join_fresh_acquisition_to_d4_v1(
            config=facts,
            d4_bound_account_identity=D4_UID,
            d4_settlement_currency=D4_CCY,
        )
    facts = extract_account_config_join_facts_v1(_config_payload(pos="long_short_mode"))
    with pytest.raises(
        TodayDeclarationGovernedBindingContractError, match="CONFIG_POSMODE_MISMATCH"
    ):
        join_fresh_acquisition_to_d4_v1(
            config=facts,
            d4_bound_account_identity=D4_UID,
            d4_settlement_currency=D4_CCY,
        )


def test_missing_and_multiple_detail_rows_fail_closed() -> None:
    with pytest.raises(
        TodayDeclarationGovernedBindingContractError, match="MATCHING_BALANCE_ROW_COUNT_NOT_ONE:0"
    ):
        extract_settlement_eq_row_v1(
            payload=_balance_payload(include_usdc=False),
            settlement_currency=D4_CCY,
        )
    extra = [{"ccy": D4_CCY, "eq": "1.00", "uTime": VENUE_ROW_UTIME}]
    with pytest.raises(
        TodayDeclarationGovernedBindingContractError, match="MATCHING_BALANCE_ROW_COUNT_NOT_ONE:2"
    ):
        extract_settlement_eq_row_v1(
            payload=_balance_payload(extra_rows=extra),
            settlement_currency=D4_CCY,
        )


def test_float_coercion_and_numeric_eq_fail_closed() -> None:
    with pytest.raises(
        TodayDeclarationGovernedBindingContractError, match="NUMERIC_COERCION_FORBIDDEN:eq"
    ):
        extract_settlement_eq_row_v1(
            payload=_balance_payload(eq_as_number=True),
            settlement_currency=D4_CCY,
        )
    with pytest.raises(
        TodayDeclarationGovernedBindingContractError, match="EQUITY_VALUE_NOT_STRING"
    ):
        lexical_decimal_scale_of_exact_equity_value_string_v1(123.45)  # type: ignore[arg-type]


def test_exact_lexical_equity_preservation_and_precision() -> None:
    row = extract_settlement_eq_row_v1(
        payload=_balance_payload(eq="123.450000"),
        settlement_currency=D4_CCY,
    )
    assert row.eq == "123.450000"
    assert row.eq != "123.45"
    assert lexical_decimal_scale_of_exact_equity_value_string_v1(row.eq) == "6"
    assert lexical_decimal_scale_of_exact_equity_value_string_v1("100") == "0"
    with pytest.raises(
        TodayDeclarationGovernedBindingContractError, match="EQUITY_VALUE_MALFORMED"
    ):
        lexical_decimal_scale_of_exact_equity_value_string_v1("1e2")
    with pytest.raises(
        TodayDeclarationGovernedBindingContractError, match="EQUITY_VALUE_MALFORMED"
    ):
        lexical_decimal_scale_of_exact_equity_value_string_v1("123.45.6")


def test_equity_unit_token_is_settlement_currency_units_not_usdc(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.equity_unit == "SETTLEMENT_CURRENCY_UNITS"
    assert result.equity_unit != D4_CCY
    candidate = json.loads(
        (Path(result.store_root) / "system_bound_today_initial_stock_candidate_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert candidate["equity_unit"] == "SETTLEMENT_CURRENCY_UNITS"
    assert candidate["settlement_currency"] == D4_CCY
    assert candidate["equity_unit"] != candidate["settlement_currency"]


def test_request_utc_separated_from_venue_utime(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.as_of_time_semantic == AS_OF_TIME_SEMANTIC
    assert result.venue_account_utime_raw == VENUE_ACCOUNT_UTIME
    assert result.venue_settlement_row_utime_raw == VENUE_ROW_UTIME
    assert result.as_of_time != result.venue_account_utime_raw
    assert result.as_of_time != result.venue_settlement_row_utime_raw
    candidate = json.loads(
        (Path(result.store_root) / "system_bound_today_initial_stock_candidate_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert candidate["as_of_time"] == candidate["validity_window_start"]
    assert candidate["as_of_time"] == candidate["validity_window_end"]
    assert candidate["as_of_time"] == candidate["acquisition_balance_request_utc"]


def test_candidate_is_not_ratification_or_anchor(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.candidate_status == "PRESENT_UNRATIFIED"
    assert result.ratification_status == "NOT_RATIFIED"
    assert result.initial_stock_anchor_status == "ABSENT"
    assert result.live_equity_stock_kind_set == KIND_SET_EMPTY
    assert result.venue_eq_source_authority == "false"
    assert result.owner_ratification_required == "true"
    assert result.venue_get_count == "2"
    assert result.venue_post_count == "0"
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    claims = json.loads((Path(result.store_root) / "claims.json").read_text(encoding="utf-8"))
    assert claims["CANDIDATE_STATUS"] != claims["RATIFICATION_STATUS"]
    assert claims["INITIAL_STOCK_ANCHOR_STATUS"] == "ABSENT"
    assert claims["LIVE_EQUITY_STOCK_KIND_SET"] == KIND_SET_EMPTY
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["KIND_SET"] == KIND_SET_EMPTY


def test_declaration_id_is_deterministic_and_not_fixture() -> None:
    first = build_system_bound_today_candidate_v1(
        account_identity=D4_UID,
        settlement_currency=D4_CCY,
        equity_value=EQ_VALUE,
        as_of_time=BALANCE_REQUEST_UTC,
        venue_account_utime_raw=VENUE_ACCOUNT_UTIME,
        venue_settlement_row_utime_raw=VENUE_ROW_UTIME,
        raw_config_sha256="a" * 64,
        raw_balance_sha256="b" * 64,
        config_request_utc=CONFIG_REQUEST_UTC,
        balance_request_utc=BALANCE_REQUEST_UTC,
    )
    second = build_system_bound_today_candidate_v1(
        account_identity=D4_UID,
        settlement_currency=D4_CCY,
        equity_value=EQ_VALUE,
        as_of_time=BALANCE_REQUEST_UTC,
        venue_account_utime_raw=VENUE_ACCOUNT_UTIME,
        venue_settlement_row_utime_raw=VENUE_ROW_UTIME,
        raw_config_sha256="a" * 64,
        raw_balance_sha256="b" * 64,
        config_request_utc=CONFIG_REQUEST_UTC,
        balance_request_utc=BALANCE_REQUEST_UTC,
    )
    assert first.declaration_id == second.declaration_id
    assert not first.declaration_id.startswith("FIXTURE")
    assert first.declaration_id.startswith("GOVERNED_TODAY_CANDIDATE_")
    assert first.payload["provenance_digest"] == semantic_candidate_digest_v1(first.payload)
    bound = {
        k: v for k, v in first.payload.items() if k not in {"declaration_id", "provenance_digest"}
    }
    assert derive_declaration_id_v1(bound) == first.declaration_id


def test_execute_mismatch_does_not_promote_candidate(tmp_path: Path) -> None:
    with pytest.raises(
        TodayDeclarationGovernedBindingContractError, match="CONFIG_UID_D4_MISMATCH"
    ):
        _run(tmp_path, config=_config_payload(uid="000"))
    stores = list((tmp_path / "bt_pack").glob("*"))
    if stores:
        store = stores[0]
        assert not (store / "system_bound_today_initial_stock_candidate_v1.json").exists()


def test_raw_bytes_preserved_and_hashed(tmp_path: Path) -> None:
    result = _run(tmp_path)
    store = Path(result.store_root)
    raw_config = (store / "raw_account_config_response_body.json").read_bytes()
    raw_balance = (store / "raw_account_balance_response_body.json").read_bytes()
    assert json.dumps(_config_payload(), separators=(",", ":")).encode("utf-8") == raw_config
    assert json.dumps(_balance_payload(), separators=(",", ":")).encode("utf-8") == raw_balance
    assert result.raw_config_evidence_sha256 == hashlib.sha256(raw_config).hexdigest()
    assert result.raw_balance_evidence_sha256 == hashlib.sha256(raw_balance).hexdigest()
    assert verify_manifest_sha256_v1(store_root=store) == 0
    assert result.genesis_id == EXPECTED_GENESIS_ID


def test_binding_tokens_and_semantics(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.contract_version == CONTRACT_VERSION
    assert result.target_stock_semantic == ECONOMIC_MEANING
    assert result.account_identity_binding == ACCOUNT_IDENTITY_BINDING
    assert result.settlement_currency_binding == SETTLEMENT_CURRENCY_BINDING
    assert result.equity_precision_semantic == EQUITY_PRECISION_SEMANTIC
    assert result.as_of_time_semantic == AS_OF_TIME_SEMANTIC
    assert result.equity_precision == "6"
    candidate = json.loads(
        (Path(result.store_root) / "system_bound_today_initial_stock_candidate_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert candidate["source_kind"] == TODAY_SOURCE_KIND
    assert candidate["source_type"] == TODAY_SOURCE_TYPE
    assert candidate["source_type"] != "VENUE_EQ"
    assert candidate["economic_meaning"] == ECONOMIC_MEANING


def test_canonical_pack_matches_executor_and_manifest() -> None:
    from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_declaration_governed_binding_contract_v1 import (
        CANONICAL_PACK_RELPATH,
    )

    pack = REPO_ROOT / CANONICAL_PACK_RELPATH
    assert verify_manifest_sha256_v1(store_root=pack) == 0
    claims = json.loads((pack / "claims.json").read_text(encoding="utf-8"))
    candidate = json.loads(
        (pack / "system_bound_today_initial_stock_candidate_v1.json").read_text(encoding="utf-8")
    )
    assert claims["CANDIDATE_STATUS"] == "PRESENT_UNRATIFIED"
    assert claims["RATIFICATION_STATUS"] == "NOT_RATIFIED"
    assert claims["INITIAL_STOCK_ANCHOR_STATUS"] == "ABSENT"
    assert claims["LIVE_EQUITY_STOCK_KIND_SET"] == KIND_SET_EMPTY
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["VENUE_GET_COUNT"] == "2"
    assert claims["VENUE_POST_COUNT"] == "0"
    assert claims["OWNER_RATIFICATION_REQUIRED"] == "true"
    assert claims["EQUITY_UNIT"] == "SETTLEMENT_CURRENCY_UNITS"
    assert claims["EQUITY_VALUE_FIELD"] == "eq"
    assert candidate["equity_value"] == "2.290727894593913"
    assert candidate["equity_unit"] == "SETTLEMENT_CURRENCY_UNITS"
    assert candidate["declaration_id"].startswith("GOVERNED_TODAY_CANDIDATE_")
    assert not candidate["declaration_id"].startswith("FIXTURE")
    assert candidate["as_of_time"] != candidate["venue_account_utime_raw"]
    assert candidate["equity_precision"] == "15"
    raw_balance = json.loads(
        (pack / "raw_account_balance_response_body.json").read_text(encoding="utf-8")
    )
    account = raw_balance["data"][0]
    usdc_rows = [row for row in account["details"] if row.get("ccy") == "USDC"]
    assert len(usdc_rows) == 1
    assert usdc_rows[0]["eq"] == candidate["equity_value"]
    assert usdc_rows[0]["eq"] != account.get("totalEq")
    assert isinstance(usdc_rows[0]["eq"], str)


def test_runbook_bt_and_navigation_persist() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    bt_section = _bt_section()
    assert OWNER_GO in bt_section
    assert "CONTRACT_VERSION=v2" in bt_section
    assert ECONOMIC_MEANING in bt_section
    assert "SETTLEMENT_CURRENCY_UNITS" in bt_section
    assert EQUITY_PRECISION_SEMANTIC in bt_section
    assert AS_OF_TIME_SEMANTIC in bt_section
    assert "VENUE_EQ_SOURCE_AUTHORITY=false" in bt_section
    assert "LIVE_EQUITY_STOCK_KIND_SET=EMPTY_FAIL_CLOSED" in bt_section
    assert "VENUE_POST_COUNT=0" in bt_section
    assert EARLIEST_LIVE_CRITICAL_PATH_BLOCKER in bt_section
    assert NEXT_OWNER_GO_REQUIRED in bt_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.BT" in bt_section
    assert BS_HEADING in RUNBOOK.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_FULL_CORE_LIVE_EQUITY_STOCK_TODAY_DECLARATION_GOVERNED_BINDING_CONTRACT_WP1"
        in spec
    )
    assert "FULL_CORE_LIVE_EQUITY_STOCK_TODAY_DECLARATION_GOVERNED_BINDING_CONTRACT_WP1.md" in mot
    assert BT_HEADING in mot
    assert "11.2.1.BT" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
