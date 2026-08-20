"""§11.13.5.Z2V bind of completed negative independent account-runtime probe.

Docs/governance invariants only. Distinguishes the executed read-only
probe from Rule-C proof, operative contract value, Face-Value
reconciliation, and Cover USDC. Does not authorize Live, Testnet,
orders, funding, conversion, transfer, Canary execute, or a productive
HTTP GET.
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
    / "section_11_13_5_z2v_negative_account_runtime_probe_v1"
    / "20260820T125156Z"
)

Z2V_HEADING = (
    "### 11.13.5.Z2V Independent account-runtime IM &#47; notionalUsd &#47; UPL probe bind"
)
Z2U_HEADING = "### 11.13.5.Z2U Operative algebra triangulation bind"
Z2W_HEADING = "### 11.13.5.Z2W Evidence boundary reached bind"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_ANY_NEW_RUNTIME_STATE_SUCH_AS_POSITION_OR_ORDER_"
    "DERIVED_IM_NOTIONALUSD_OR_UPL_REPEAT_ZERO_EQUITY_NO_POSITION_GET_HAS_NO_"
    "DISCRIMINATORY_VALUE_FACE_VALUE_AND_COVER_USDC_REMAIN_UNRESOLVED_SUPPORT_"
    "CONTACT_NOT_AUTHORIZED_CANARY_NOT_AUTHORIZED"
)
OWNER_GO = "OWNER_GO_Z2U_NEGATIVE_RUNTIME_PROBE_CANONICAL_BIND_PLUS_DUAL_NOTION_MIRROR_SYNC_ONLY"
BASELINE_SHA = "16ed9ddae96e61c073f4857256e329a3b75e3cec"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2v_section(text: str) -> str:
    start = text.find(Z2V_HEADING)
    assert start >= 0, "missing §11.13.5.Z2V heading"
    end = text.find(Z2W_HEADING, start)
    assert end > start, "missing §11.13.5.Z2W boundary after Z2V"
    return text[start:end]


def test_z2v_heading_is_unique_and_follows_z2u() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2V_HEADING) == 1
    z2u = text.find(Z2U_HEADING)
    z2v = text.find(Z2V_HEADING)
    z2w = text.find(Z2W_HEADING)
    ladder = text.find("## 11.14 Live order and economic evidence ladder")
    assert 0 <= z2u < z2v < z2w < ladder


def test_z2v_docs_bind_negative_probe_without_proving_contract_value() -> None:
    section = _z2v_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=Z2U_NEGATIVE_INDEPENDENT_ACCOUNT_RUNTIME_PROBE_BIND_DOCS_EVIDENCE_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "TARGET_INSTRUMENT=BTC-USD_UM_XPERP-310404",
        "GET_EXECUTED_THIS_PERSIST_STEP=false",
        "GET_ALREADY_EXECUTED_PRIOR_GO=true",
        "GET_REQUEST_COUNT=6",
        "TARGET_RUNTIME_RECORD_FOUND=false",
        "RULE_C_INDEPENDENT_RUNTIME_IM_SATISFIED=false",
        "OPERATIVE_RUNTIME_VALUE=UNPROVEN",
        "OPERATIVE_CONTRACT_VALUE_PROVEN=false",
        "OPERATIVE_CONTRACT_VALUE=UNPROVEN",
        "FACE_VALUE_DOCUMENT_CONFLICT_RECONCILED=false",
        "CANDIDATE_A_0_0001_BTC_COMPATIBLE=INCONCLUSIVE_ZERO_EQUITY_NOT_DISCRIMINATING",
        "CANDIDATE_B_0_01_BTC_COMPATIBLE=INCONCLUSIVE_ZERO_EQUITY_NOT_DISCRIMINATING",
        "INDEPENDENCE_FROM_PUBLIC_CTVAL_FORMULA=true_SURFACES_CHECKED_BUT_NO_DISCRIMINATING_VALUE",
        "NO_USD_EQUALS_USDC=true",
        "COVER_USDC_INSTANTIATED=false",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "API_WRITE_PERFORMED=false",
        "ORDER_SUBMITTED=false",
        "FUNDING_PERFORMED=false",
        "SUPPORT_CONTACT_PERFORMED=false",
        "LIVE_ACTION_PERFORMED=false",
        "TESTNET_ACTION_PERFORMED=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_EXECUTE_AUTHORIZED=false",
        "NO_DISCRIMINATING_ACCOUNT_RUNTIME_VALUE_EXISTS_UNDER_THE_OBSERVED_ZERO_EQUITY_NO_POSITION_STATE=true",
        "22F_INDEPENDENT_ACCOUNT_RUNTIME_PROBE_CONSUMED_NEGATIVE_NO_TARGET_RECORD_ZERO_EQUITY_NON_DISCRIMINATING_RULE_C_UNSATISFIED",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "NO_FUNDING",
        "NO_ORDER",
        "NO_CANARY",
        "NO_EXECUTE",
    )
    for marker in required:
        assert marker in section, f"missing Z2V marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nOPERATIVE_CONTRACT_VALUE_PROVEN=true\n",
        "\nRULE_C_INDEPENDENT_RUNTIME_IM_SATISFIED=true\n",
        "\nFACE_VALUE_DOCUMENT_CONFLICT_RECONCILED=true\n",
        "\nCOVER_USDC_INSTANTIATED=true\n",
        "\nCOVER_USDC_STATUS=INSTANTIATED\n",
        "\nORDER_SUBMITTED=true\n",
        "\nCANARY_EXECUTE_AUTHORIZED=true\n",
        "\nNO_USD_EQUALS_USDC=false\n",
        "\nOPERATIVE_RUNTIME_VALUE=0.0001_BTC\n",
        "\nOPERATIVE_RUNTIME_VALUE=0.01_BTC\n",
        "\nTARGET_RUNTIME_RECORD_FOUND=true\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2V marker present: {marker!r}"


def test_z2v_map_of_truth_navigation_pointer_matches_runbook() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "§11.13.5.Z2V |" in mot
    assert "historical next pointer superseded by §11.13.5.Z2V" in mot
    assert "historical next pointer superseded by §11.13.5.Z2W" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}\n" not in mot
    assert (
        "NEXT_CANONICAL_STEP_POINTER=OWNER_GO_REQUIRED_FOR_INDEPENDENT_OKX_ACCOUNT_RUNTIME_"
        "IM_NOTIONALUSD_OR_UPL_ON_BTC_USD_UM_XPERP_310404_AND_OEM_METADATA_FACE_VALUE_"
        "RECONCILIATION_SUPPORT_CONTACT_NOT_AUTHORIZED\n" not in mot
    )


def test_z2v_evidence_manifest_verifies_without_secrets_or_writes() -> None:
    result = verify_manifest_v1(EVIDENCE_ROOT)
    assert result["MANIFEST_VERIFY_RC"] == 0
    claims = json_load(EVIDENCE_ROOT / "claims.json")
    assert claims["OPERATIVE_CONTRACT_VALUE_PROVEN"] is False
    assert claims["RULE_C_INDEPENDENT_RUNTIME_IM_SATISFIED"] is False
    assert claims["TARGET_RUNTIME_RECORD_FOUND"] is False
    assert claims["NO_USD_EQUALS_USDC"] is True
    redaction = json_load(EVIDENCE_ROOT / "redaction_check.json")
    assert redaction["REDACTION_CHECK_PASS"] is True
    assert redaction["SECRET_VALUE_PERSISTED"] is False
    zero = json_load(EVIDENCE_ROOT / "zero_write_assertions.json")
    assert zero["POST_COUNT"] == 0
    assert zero["ORDER_EXECUTED"] is False
    assert zero["GET_COUNT"] == 6
    blob = (EVIDENCE_ROOT / "GET_SNAPSHOT.sanitized.json").read_text(encoding="utf-8")
    for needle in ('"api_secret"', '"passphrase"', '"OK-ACCESS-SIGN":', '"OK-ACCESS-KEY":'):
        assert needle not in blob


def json_load(path: Path) -> dict:
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload
