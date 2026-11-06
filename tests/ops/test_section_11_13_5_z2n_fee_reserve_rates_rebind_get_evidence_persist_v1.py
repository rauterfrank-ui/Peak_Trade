"""§11.13.5.Z2N SSOT bind of already persisted fee-reserve rates rebind GET evidence.

Docs/governance invariants only. Does not authorize Live, Testnet,
orders, funding, conversion, transfer, Canary execute, or a productive
HTTP GET. Does not instantiate COVER_USDC or numeric FEE_RESERVE.
"""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
EVIDENCE_ROOT = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_z2m_fee_reserve_rates_rebind_get_v1"
    / "20260819T102325Z"
)

Z2N_HEADING = "### 11.13.5.Z2N Fresh authenticated fee-reserve rates rebind GET evidence persist"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2n_section(text: str) -> str:
    start = text.find(Z2N_HEADING)
    assert start >= 0, "missing §11.13.5.Z2N heading"
    end = text.find("## 11.14 Live order and economic evidence ladder", start)
    assert end > start, "missing §11.14 boundary after Z2N"
    return text[start:end]


def test_z2n_docs_bind_persisted_get_evidence_without_network_or_cover_usdc() -> None:
    section = _z2n_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=PERSIST_FRESH_FEE_RESERVE_RATES_REBIND_GET_EVIDENCE_TO_ORIGIN_MAIN_SSOT_ONLY",
        "FEE_RESERVE_RATES_REBIND_GET_EVIDENCE_BOUND=true",
        "EVIDENCE_SOURCE=ORIGIN_MAIN_PERSISTED_EVIDENCE_FROM_PR_5966",
        "NETWORK_CALL_REQUIRED_FOR_BINDING=false",
        "NETWORK_CALL_EXECUTED_DURING_BINDING=false",
        "PRODUCTION_NETWORK_CALL_EXECUTED=false",
        "GET_EXECUTED_THIS_PERSIST_STEP=false",
        "REQUEST_INST_TYPE=FUTURES",
        "REQUEST_INST_FAMILY=BTC-USD_UM_XPERP",
        "REQUEST_GRAMMAR_MATCH=true",
        "MARKET_DASHBOARD_FAMILY_TAXONOMY_USED=false",
        "MARKET_DASHBOARD_FAMILY_REQUIRED=false",
        "HTTP_STATUS=200",
        "OKX_CODE=0",
        "OKX_MSG=",
        "TAKER_USDC_RAW=-0.0005",
        "MAKER_USDC_RAW=-0.0002",
        "TAKER_RATE=-0.0005",
        "MAKER_RATE=-0.0002",
        "RESPONSE_RULETYPE=normal",
        "DELIVERY_RAW=0.0003",
        "DELIVERY_ENTERS_FEE_RESERVE=false",
        "BODY_SHA256=c700c5b9cef16e5a88b6d92ea81561c66f6de32d60b446b1c0e7ae99018dd8bc",
        "COLLECTED_UTC=2026-08-19T10:23:25.619850Z",
        "RUN_ID=20260819T102325Z",
        "FEE_RESERVE_RATES_ADJUDICATION=PROVEN",
        "NUMERIC_FEE_RESERVE_STATUS=UNINSTANTIATED",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "LIVE_AUTHORIZED=false",
        "NO_FUNDING",
        "NO_TRANSFER",
        "NO_CONVERSION",
        "NO_ORDER",
        "NO_CANARY",
        "OWNER_GO=OWNER_GO_TO_PERSIST_FRESH_FEE_RESERVE_RATES_REBIND_GET_EVIDENCE",
        "OWNER_GO_STATUS=CONSUMED",
        "CANONICAL_NEXT_STEP=OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_COVER_USDC_TERMS_AFTER_FEE_RESERVE_RATES_REBIND_BEFORE_FUNDING",
        "EARLIEST_UNRESOLVED_DEPENDENCY=COVER_USDC_UNINSTANTIATED_REMAINING_UNPROVEN_TERMS_AFTER_FEE_RESERVE_RATES_REBIND",
        "NAMED_REMAINING_COVER_USDC_TERM=FINITE_PHYSICAL_USDC_COVER_AMOUNT_ABSENT",
    )
    for token in required:
        assert token in section, f"missing runbook token: {token}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCOVER_USDC_STATUS=PROVEN\n",
        "\nCOVER_USDC_STATUS=INSTANTIATED\n",
        "\nNUMERIC_FEE_RESERVE_STATUS=INSTANTIATED\n",
        "\nGET_EXECUTED_THIS_PERSIST_STEP=true\n",
        "\nNETWORK_CALL_EXECUTED_DURING_BINDING=true\n",
        "\nMARKET_DASHBOARD_FAMILY_TAXONOMY_USED=true\n",
        "\nFUNDING_EXECUTED=true\n",
        "\nFX_STATUS=PROVEN\n",
        "\nROUNDING_STATUS=PROVEN\n",
    )
    for assignment in forbidden:
        assert assignment not in section, f"forbidden assignment present: {assignment!r}"


def test_z2n_map_of_truth_binds_pr_5966_pack_without_cover_usdc() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "§11.13.5.Z2N" in mot
    assert "FEE_RESERVE_RATES_REBIND_GET_EVIDENCE_BOUND=true" in mot
    assert "EVIDENCE_SOURCE=ORIGIN_MAIN_PERSISTED_EVIDENCE_FROM_PR_5966" in mot
    assert "REQUEST_INST_TYPE=FUTURES" in mot
    assert "REQUEST_INST_FAMILY=BTC-USD_UM_XPERP" in mot
    assert "MARKET_DASHBOARD_FAMILY_TAXONOMY_USED=false" in mot
    assert "FEE_RESERVE_RATES_ADJUDICATION=PROVEN" in mot
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in mot
    assert (
        "EARLIEST_UNRESOLVED_DEPENDENCY="
        "COVER_USDC_UNINSTANTIATED_REMAINING_UNPROVEN_TERMS_AFTER_FEE_RESERVE_RATES_REBIND"
    ) in mot
    assert (
        "FEE_RESERVE_RATES_REBIND_GET_USING_SEALED_GRAMMAR_AND_SEALED_EXECUTION_PATH_NOT_EXECUTED"
        in mot
    )


def test_z2n_origin_main_pr_5966_evidence_pack_verifies_without_network() -> None:
    verify = verify_manifest_v1(EVIDENCE_ROOT)
    assert verify["MANIFEST_VERIFY_RC"] == 0
    snapshot = _read(EVIDENCE_ROOT / "GET_SNAPSHOT.sanitized.json")
    assert '"HTTP_STATUS": 200' in snapshot
    assert '"OKX_CODE": "0"' in snapshot
    assert '"takerUSDC": "-0.0005"' in snapshot
    assert '"makerUSDC": "-0.0002"' in snapshot
    assert '"delivery": "0.0003"' in snapshot
    assert '"ruleType": "normal"' in snapshot
    assert '"instType": "FUTURES"' in snapshot
    assert (
        '"BODY_SHA256": "c700c5b9cef16e5a88b6d92ea81561c66f6de32d60b446b1c0e7ae99018dd8bc"'
    ) in snapshot
    claims = _read(EVIDENCE_ROOT / "claims.json")
    assert '"GET_EXECUTED": true' in claims
    assert '"COVER_USDC_STATUS": "UNINSTANTIATED"' in claims
    assert '"NUMERIC_FEE_RESERVE_INSTANTIATED": false' in claims
    zero = _read(EVIDENCE_ROOT / "zero_write_assertions.json")
    assert '"ORDER_EXECUTED": false' in zero
    assert '"POST_COUNT": 0' in zero
    assert '"GET_COUNT": 1' in zero
    redaction = _read(EVIDENCE_ROOT / "redaction_check.json")
    assert '"SECRET_VALUE_PERSISTED": false' in redaction
    assert '"REDACTION_CHECK_PASS": true' in redaction
