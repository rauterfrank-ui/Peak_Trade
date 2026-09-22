"""D6 eq-identity and F12/F13/U05 liability-stock kind-ratification tests.

Sealed BH raw plus S1-S6 plus #6452/#6453/#6454 only. No new GET.
NONE and REMAIN_UNKNOWN are valid fail-closed outcomes.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    KIND_SET_RESOLVED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MS2_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_and_complete_event_stream_acquisition_v1 import (
    CANONICAL_MAPPING_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_ratification_v1 import (
    CANONICAL_S6_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.eq_identity_and_f12_f13_liability_stock_kind_ratification_v1 import (
    CANONICAL_BG_PACK_RELPATH,
    CANONICAL_BH_PACK_RELPATH,
    CANONICAL_PACK_RELPATH,
    EARLIEST_REMAINING_D6_BLOCKER,
    EXPECTED_ORIGIN_MAIN_SHA,
    IDENTITY_NONE,
    OWNER_GO,
    EqIdentityAndF12F13LiabilityStockKindRatificationError,
    execute_eq_identity_and_f12_f13_liability_stock_kind_ratification_v1,
    reject_claimed_eq_identity_or_kind_proof_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_f16_f17_f18_necessary_equity_stock_kind_resolution_v1 import (
    CANONICAL_ACQUISITION_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    CANONICAL_SEALED_OBSERVATION_PACK_RELPATH,
    verify_manifest_sha256_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_D6_EQ_IDENTITY_AND_F12_F13_LIABILITY_STOCK_KIND_RATIFICATION_V1.md"
)
BI_HEADING = "11.2.1.BI FULL_CORE_D6_EQ_IDENTITY_AND_F12_F13_LIABILITY_STOCK_KIND_RATIFICATION"
SEALED_BH = REPO_ROOT / CANONICAL_BH_PACK_RELPATH
SEALED_PACK = REPO_ROOT / CANONICAL_SEALED_OBSERVATION_PACK_RELPATH
CANONICAL_S6_PACK = REPO_ROOT / CANONICAL_S6_PACK_RELPATH
CANONICAL_MAPPING_PACK = REPO_ROOT / CANONICAL_MAPPING_PACK_RELPATH
CANONICAL_ACQUISITION_PACK = REPO_ROOT / CANONICAL_ACQUISITION_PACK_RELPATH
CANONICAL_BG_PACK = REPO_ROOT / CANONICAL_BG_PACK_RELPATH
CANONICAL_RATIFICATION_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
_AS_OF = "2026-09-13T23:00:00Z"


def _bi_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BI_HEADING)
    return runbook[
        start : runbook.index(
            "11.2.1.BJ FULL_CORE_D6_F12_F13_KIND_SET_REMAINING_UNKNOWN_PIN_AND_REOPEN_GATE",
            start,
        )
    ]


def _run(tmp_path: Path):
    return execute_eq_identity_and_f12_f13_liability_stock_kind_ratification_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        sealed_bh_pack=SEALED_BH,
        sealed_observation_pack=SEALED_PACK,
        sealed_s6_pack=CANONICAL_S6_PACK,
        sealed_mapping_pack=CANONICAL_MAPPING_PACK,
        sealed_acquisition_pack=CANONICAL_ACQUISITION_PACK,
        sealed_bg_pack=CANONICAL_BG_PACK,
        evidence_root=tmp_path / "rat",
        ratification_as_of=_AS_OF,
    )


def test_sealed_input_manifests_verify() -> None:
    assert verify_manifest_sha256_v1(store_root=SEALED_BH) == 0
    assert verify_manifest_sha256_v1(store_root=SEALED_PACK) == 0
    assert verify_manifest_sha256_v1(store_root=CANONICAL_S6_PACK) == 0
    assert verify_manifest_sha256_v1(store_root=CANONICAL_MAPPING_PACK) == 0
    assert verify_manifest_sha256_v1(store_root=CANONICAL_ACQUISITION_PACK) == 0
    assert verify_manifest_sha256_v1(store_root=CANONICAL_BG_PACK) == 0


def test_wrong_owner_go_fail_closes_without_writing(tmp_path: Path) -> None:
    with pytest.raises(
        EqIdentityAndF12F13LiabilityStockKindRatificationError,
        match="OWNER_GO_MISMATCH",
    ):
        execute_eq_identity_and_f12_f13_liability_stock_kind_ratification_v1(
            owner_go="WRONG_GO",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bh_pack=SEALED_BH,
            sealed_observation_pack=SEALED_PACK,
            sealed_s6_pack=CANONICAL_S6_PACK,
            sealed_mapping_pack=CANONICAL_MAPPING_PACK,
            sealed_acquisition_pack=CANONICAL_ACQUISITION_PACK,
            sealed_bg_pack=CANONICAL_BG_PACK,
            evidence_root=tmp_path / "rat",
            ratification_as_of=_AS_OF,
        )
    assert not (tmp_path / "rat" / "2026-09-13T230000Z").exists()


def test_claimed_include_algebra_or_legacy_restore_fail_closes() -> None:
    with pytest.raises(
        EqIdentityAndF12F13LiabilityStockKindRatificationError,
        match="EQ_IDENTITY_CANNOT_ALGEBRAIC_EQ_IDENTITY",
    ):
        reject_claimed_eq_identity_or_kind_proof_v1(
            claimed_proof="ALGEBRAIC_EQ_IDENTITY",
            fact_id="F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ",
        )
    with pytest.raises(
        EqIdentityAndF12F13LiabilityStockKindRatificationError,
        match="EQ_IDENTITY_CANNOT_RESTORE_LEGACY_EQUITY_LOGIC",
    ):
        reject_claimed_eq_identity_or_kind_proof_v1(
            claimed_proof="RESTORE_LEGACY_EQUITY_LOGIC",
            fact_id="F12_LIABILITY_AFFECTS_EQUITY_STOCK",
        )
    with pytest.raises(
        EqIdentityAndF12F13LiabilityStockKindRatificationError,
        match="EQ_IDENTITY_CANNOT_INCLUDES_LIABILITY",
    ):
        reject_claimed_eq_identity_or_kind_proof_v1(
            claimed_proof="INCLUDES_LIABILITY",
            fact_id="F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ",
        )
    reject_claimed_eq_identity_or_kind_proof_v1(
        claimed_proof="REMAIN_UNKNOWN_NO_UNIQUE_EQ_IDENTITY_PROOF",
        fact_id="F12_LIABILITY_AFFECTS_EQUITY_STOCK",
    )


def test_ratification_is_none_and_facts_remain_unknown(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.genesis_id == EXPECTED_GENESIS_ID
    assert result.genesis_as_of == EXPECTED_GENESIS_AS_OF
    assert result.ratified_eq_identity == IDENTITY_NONE
    assert result.f12_decision == "REMAIN_UNKNOWN"
    assert result.f13_decision == "REMAIN_UNKNOWN"
    assert result.u05_kind_decision == "REMAIN_UNKNOWN"
    assert result.f16_decision == "REMAIN_UNKNOWN"
    assert result.f17_decision == "REMAIN_UNKNOWN"
    assert result.f18_decision == "REMAIN_UNKNOWN"
    assert result.ratified_source_kinds == "NONE"
    assert result.kind_set == "EMPTY_FAIL_CLOSED"
    assert result.kind_set_resolved == "false"
    assert result.raw_eq_source_authority == "false"
    assert result.eq_reconciliation_target_only == "true"
    assert result.earliest_remaining_d6_blocker == EARLIEST_REMAINING_D6_BLOCKER
    assert result.new_network_get_count == "0"
    assert result.network_post_performed == "false"
    assert result.ms2_authorized == "false"
    assert result.d6_fully_closed == "false"
    assert result.d7_authorized == "false"
    assert result.legacy_structure_restored == "false"
    assert result.semantic_salvage_rule_applied == "true"
    pack = Path(result.store_root)
    forensic = json.loads((pack / "forensic_eq_identity_tokens_v1.json").read_text())
    assert forensic["layer"] == "FORENSIC_RAW"
    assert forensic["algebraic_eq_identity"] == "FORBIDDEN"
    assert forensic["numeric_composition_derived"] == "false"
    usdc = next(item for item in forensic["details"] if item["ccy_raw_token"] == "USDC")
    eq_token = next(item for item in usdc["tokens"] if item["field"] == "eq")
    assert eq_token["presence"] == "STRING"
    assert eq_token["empty_zero_null_missing_not_normalized"] == "true"
    liab = next(item for item in usdc["tokens"] if item["field"] == "liab")
    assert liab["exact_empty_string"] == "true"
    identity = json.loads((pack / "eq_identity_ratification_v1.json").read_text())
    assert identity["ratified_eq_identity"] == "NONE"
    assert identity["legacy_equity_logic_restored"] == "false"
    claims = json.loads((pack / "claims.json").read_text())
    assert claims["LEGACY_STRUCTURE_RESTORED"] == "false"
    assert claims["SEMANTIC_SALVAGE_RULE_APPLIED"] == "true"
    assert claims["BH_RAW_BODY_REWRITTEN"] == "false"
    raw_bh = SEALED_BH / "raw_account_balance_response_body.json"
    assert claims["BH_RAW_PAYLOAD_SHA256"] == hashlib.sha256(raw_bh.read_bytes()).hexdigest()
    assert verify_manifest_sha256_v1(store_root=pack) == 0
    assert KIND_SET_RESOLVED is False
    assert MS2_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert (
        EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY
        == "CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SURFACE_BOUND_VALUE_REQUIRES_FRESH_TRUSTED_GET"
    )


def test_canonical_pack_matches_executor() -> None:
    claims = json.loads((CANONICAL_RATIFICATION_PACK / "claims.json").read_text())
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["GENESIS_ID"] == EXPECTED_GENESIS_ID
    assert claims["RATIFIED_EQ_IDENTITY"] == "NONE"
    assert claims["F12_DECISION"] == "REMAIN_UNKNOWN"
    assert claims["F13_DECISION"] == "REMAIN_UNKNOWN"
    assert claims["U05_KIND_DECISION"] == "REMAIN_UNKNOWN"
    assert claims["F16_DECISION"] == "REMAIN_UNKNOWN"
    assert claims["RATIFIED_SOURCE_KINDS"] == "NONE"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["EARLIEST_REMAINING_D6_BLOCKER"] == EARLIEST_REMAINING_D6_BLOCKER
    assert claims["VENUE_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["LEGACY_STRUCTURE_RESTORED"] == "false"
    assert claims["SEMANTIC_SALVAGE_RULE_APPLIED"] == "true"
    assert verify_manifest_sha256_v1(store_root=CANONICAL_RATIFICATION_PACK) == 0
    expected: dict[str, str] = {}
    for line in (
        (CANONICAL_RATIFICATION_PACK / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
    ):
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        expected[name] = digest
    actual = {
        path.name
        for path in CANONICAL_RATIFICATION_PACK.iterdir()
        if path.is_file() and path.name != "MANIFEST.sha256"
    }
    assert set(expected) == actual
    for name, digest in expected.items():
        assert (
            hashlib.sha256((CANONICAL_RATIFICATION_PACK / name).read_bytes()).hexdigest() == digest
        )


def test_runbook_bi_persists_typed_fail_closed_ratification() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    bi_section = _bi_section()
    assert OWNER_GO in bi_section
    assert (
        "THIS_SLICE=11.2.1.BI.FULL_CORE_D6_EQ_IDENTITY_AND_F12_F13_LIABILITY_STOCK_KIND_RATIFICATION"
        in bi_section
    )
    assert "RATIFIED_EQ_IDENTITY=NONE" in bi_section
    assert "F12_DECISION=REMAIN_UNKNOWN" in bi_section
    assert "F13_DECISION=REMAIN_UNKNOWN" in bi_section
    assert "U05_KIND_DECISION=REMAIN_UNKNOWN" in bi_section
    assert "F16_DECISION=REMAIN_UNKNOWN" in bi_section
    assert "RATIFIED_SOURCE_KINDS=NONE" in bi_section
    assert "KIND_SET_RESOLVED=false" in bi_section
    assert f"EARLIEST_REMAINING_D6_BLOCKER={EARLIEST_REMAINING_D6_BLOCKER}" in bi_section
    assert "RAW_EQ_SOURCE_AUTHORITY=false" in bi_section
    assert "LEGACY_STRUCTURE_RESTORED=false" in bi_section
    assert "SEMANTIC_SALVAGE_RULE_APPLIED=true" in bi_section
    assert "VENUE_GET_COUNT=0" in bi_section
    assert "MS2_AUTHORIZED=false" in bi_section
    assert "D6_FULLY_CLOSED=false" in bi_section
    assert "D7_AUTHORIZED=false" in bi_section
    assert (
        "DOCS_TOKEN_FULL_CORE_D6_EQ_IDENTITY_AND_F12_F13_LIABILITY_STOCK_KIND_RATIFICATION_V1"
        in spec
    )
