"""Today initial-stock Anchor V1 tests.

Exact authorized ratification only. KIND_SET remains EMPTY_FAIL_CLOSED.
No GET. No POST. Sealed BT/BU artifacts are not rewritten.
"""

from __future__ import annotations

import json
import shutil
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
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_declaration_governed_binding_contract_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BT_PACK_RELPATH,
    CANDIDATE_FILE,
    ECONOMIC_MEANING,
    EQUITY_UNIT,
    semantic_candidate_digest_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_ratification_v1 import (
    AUTHORIZED_AS_OF_TIME,
    AUTHORIZED_DECLARATION_ID,
    AUTHORIZED_EQUITY_VALUE,
    AUTHORIZED_PROVENANCE_DIGEST,
    CANONICAL_PACK_RELPATH as CANONICAL_BU_PACK_RELPATH,
    IDENTITY_FILE,
    RATIFICATION_FILE,
    ratification_digest_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_anchor_v1 import (
    AUTHORIZED_ANCHOR_ID,
    AUTHORIZED_RATIFICATION_DIGEST,
    CANONICAL_PACK_RELPATH,
    EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_GO,
    STATUS_PRESENT,
    TodayInitialStockAnchorError,
    execute_live_equity_stock_today_initial_stock_anchor_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_ANCHOR_WP1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
ANCHOR_MODULE = (
    REPO_ROOT
    / "src/ops/governed_productive_account_equity_authority_producer_v1/"
    / "live_equity_stock_today_initial_stock_anchor_v1.py"
)
BU_HEADING = "11.2.1.BU FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_RATIFICATION"
BV_HEADING = "11.2.1.BV FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_ANCHOR"
SEALED_BT = REPO_ROOT / CANONICAL_BT_PACK_RELPATH
SEALED_BU = REPO_ROOT / CANONICAL_BU_PACK_RELPATH
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH


def _copy_pack(src: Path, dest: Path) -> Path:
    shutil.copytree(src, dest)
    return dest


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )


def _load_json(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _reseal(pack: Path) -> None:
    persist_manifest_sha256_v1(store_root=pack)


def _mutate_ratification(pack: Path, **fields: str) -> None:
    path = pack / RATIFICATION_FILE
    payload = _load_json(path)
    payload.update(fields)
    payload["ratification_digest"] = ratification_digest_v1(payload)
    _write_json(path, payload)


def _mutate_identity(pack: Path, **fields: str) -> None:
    path = pack / IDENTITY_FILE
    payload = _load_json(path)
    payload.update(fields)
    _write_json(path, payload)


def _mutate_candidate(pack: Path, **fields: str) -> None:
    path = pack / CANDIDATE_FILE
    payload = _load_json(path)
    payload.update(fields)
    payload["provenance_digest"] = semantic_candidate_digest_v1(payload)
    _write_json(path, payload)


def _execute(
    *,
    evidence_root: Path,
    sealed_bu_pack: Path = SEALED_BU,
    sealed_bt_pack: Path = SEALED_BT,
    **kwargs: str,
):
    return execute_live_equity_stock_today_initial_stock_anchor_v1(
        owner_go=kwargs.get("owner_go", OWNER_GO),
        origin_main_sha=kwargs.get("origin_main_sha", EXPECTED_ORIGIN_MAIN_SHA),
        repo_root=REPO_ROOT,
        evidence_root=evidence_root,
        sealed_bu_pack=sealed_bu_pack,
        sealed_bt_pack=sealed_bt_pack,
        persist_as_of=kwargs.get("persist_as_of", "2026-09-14T20:55:00Z"),
    )


def _bv_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BV_HEADING)
    return runbook[start : runbook.index("## 11.3 Autonomy state model", start)]


def test_authorized_ratification_binds_anchor(tmp_path: Path) -> None:
    result = _execute(evidence_root=tmp_path)
    assert result.declaration_id == AUTHORIZED_DECLARATION_ID
    assert result.candidate_digest == AUTHORIZED_PROVENANCE_DIGEST
    assert result.ratification_digest == AUTHORIZED_RATIFICATION_DIGEST
    assert result.anchor_id == AUTHORIZED_ANCHOR_ID
    assert result.candidate_status == "PRESENT"
    assert result.ratification_status == "RATIFIED"
    assert result.initial_stock_anchor_status == STATUS_PRESENT
    assert result.live_equity_stock_kind_set == KIND_SET_EMPTY
    assert result.venue_eq_source_authority == "false"
    assert result.venue_get_count_added == "0"
    assert result.venue_post_count == "0"
    assert result.earliest_live_critical_path_blocker == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER
    assert result.next_owner_go_required == NEXT_OWNER_GO_REQUIRED
    store = Path(result.store_root)
    anchor = _load_json(store / "today_initial_stock_anchor_v1.json")
    assert anchor["equity_value"] == AUTHORIZED_EQUITY_VALUE
    assert anchor["equity_unit"] == EQUITY_UNIT
    assert anchor["settlement_currency"] == "USDC"
    assert anchor["equity_precision"] == "15"
    assert anchor["economic_meaning"] == ECONOMIC_MEANING
    assert anchor["as_of_time"] == AUTHORIZED_AS_OF_TIME
    assert anchor["candidate_digest"] == AUTHORIZED_PROVENANCE_DIGEST
    assert anchor["ratification_digest"] == AUTHORIZED_RATIFICATION_DIGEST
    assert anchor["anchor_is_not_kind_set_membership"] == "true"
    assert anchor["equity_copied_without_provenance"] == "false"
    assert anchor["venue_eq_source_authority"] == "false"
    lineage = _load_json(store / "candidate_ratification_anchor_lineage_v1.json")
    assert lineage["lineage"] == "CANDIDATE->RATIFICATION->ANCHOR"
    assert lineage["lineage_valid"] == "true"
    claims = _load_json(store / "claims.json")
    assert claims["KIND_SET_MEMBERS"] == "NONE"
    assert claims["MEMBERSHIP_OWNER_RATIFICATION_REQUIRED"] == "true"
    assert claims["VENUE_GET_COUNT_ADDED"] == "0"
    assert claims["VENUE_POST_COUNT"] == "0"
    assert claims["BT_CANDIDATE_REWRITTEN"] == "false"
    assert claims["BU_RATIFICATION_REWRITTEN"] == "false"
    assert claims["MASTER_V2_UNCHANGED"] == "true"
    assert claims["STEP_29P_UNCHANGED"] == "true"
    assert verify_manifest_sha256_v1(store_root=store) == 0


def test_wrong_candidate_id_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    _mutate_ratification(bu, declaration_id="GOVERNED_TODAY_CANDIDATE_deadbeefdeadbeef")
    _mutate_identity(bu, declaration_id="GOVERNED_TODAY_CANDIDATE_deadbeefdeadbeef")
    _reseal(bu)
    with pytest.raises(TodayInitialStockAnchorError, match="DECLARATION_ID_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_wrong_candidate_digest_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    _mutate_ratification(bu, candidate_digest="0" * 64)
    _reseal(bu)
    with pytest.raises(TodayInitialStockAnchorError, match="CANDIDATE_DIGEST_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_wrong_ratification_digest_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    payload = _load_json(bu / RATIFICATION_FILE)
    payload["ratification_digest"] = "0" * 64
    _write_json(bu / RATIFICATION_FILE, payload)
    _reseal(bu)
    with pytest.raises(TodayInitialStockAnchorError, match="RATIFICATION_DIGEST_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_wrong_ratification_id_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    payload = _load_json(bu / RATIFICATION_FILE)
    payload["ratification_id"] = "WRONG_RATIFICATION_ID"
    payload["ratification_digest"] = ratification_digest_v1(payload)
    _write_json(bu / RATIFICATION_FILE, payload)
    _reseal(bu)
    with pytest.raises(TodayInitialStockAnchorError, match="RATIFICATION_ID_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_equity_value_mismatch_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    _mutate_ratification(bu, equity_value="9.999")
    _mutate_identity(bu, equity_value="9.999")
    _reseal(bu)
    with pytest.raises(TodayInitialStockAnchorError, match="EQUITY_VALUE_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_equity_unit_mismatch_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    _mutate_ratification(bu, equity_unit="USDC")
    _mutate_identity(bu, equity_unit="USDC")
    _reseal(bu)
    with pytest.raises(TodayInitialStockAnchorError, match="EQUITY_UNIT_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_settlement_currency_mismatch_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    _mutate_ratification(bu, settlement_currency="USD")
    _mutate_identity(bu, settlement_currency="USD")
    _reseal(bu)
    with pytest.raises(TodayInitialStockAnchorError, match="SETTLEMENT_CURRENCY_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_equity_scale_mismatch_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    _mutate_identity(bu, equity_precision="2")
    _reseal(bu)
    with pytest.raises(TodayInitialStockAnchorError, match="EQUITY_PRECISION_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_as_of_time_mismatch_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    _mutate_ratification(bu, as_of_time="2026-09-14T00:00:00Z")
    _mutate_identity(bu, as_of_time="2026-09-14T00:00:00Z")
    _reseal(bu)
    with pytest.raises(TodayInitialStockAnchorError, match="AS_OF_TIME_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_economic_meaning_mismatch_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    _mutate_ratification(bu, economic_meaning="SOMETHING_ELSE")
    _mutate_identity(bu, economic_meaning="SOMETHING_ELSE")
    _reseal(bu)
    with pytest.raises(TodayInitialStockAnchorError, match="ECONOMIC_MEANING_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_missing_ratification_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    (bu / RATIFICATION_FILE).unlink()
    _reseal(bu)
    with pytest.raises(TodayInitialStockAnchorError, match="RATIFICATION_ABSENT"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_candidate_substitution_denied(tmp_path: Path) -> None:
    bt = _copy_pack(SEALED_BT, tmp_path / "bt")
    _mutate_candidate(bt, declaration_id="GOVERNED_TODAY_CANDIDATE_ffffffffffffffff")
    _reseal(bt)
    with pytest.raises(TodayInitialStockAnchorError, match="DECLARATION_ID_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bt_pack=bt)


def test_numeric_equity_coercion_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    payload = json.loads((bu / RATIFICATION_FILE).read_text(encoding="utf-8"))
    payload["equity_value"] = 2.29
    (bu / RATIFICATION_FILE).write_text(json.dumps(payload) + "\n", encoding="utf-8")
    _reseal(bu)
    with pytest.raises(
        TodayInitialStockAnchorError, match="NUMERIC_COERCION_FORBIDDEN:equity_value"
    ):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_unknown_or_extra_kind_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    _mutate_ratification(
        bu,
        live_equity_stock_kind_set="OWNER_DECLARED_TODAY_INITIAL_EQUITY_STOCK",
    )
    _reseal(bu)
    with pytest.raises(TodayInitialStockAnchorError, match="UNKNOWN_OR_EXTRA_STOCK_KIND_SEMANTIC"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_venue_eq_cannot_become_source_authority(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    _mutate_ratification(bu, venue_eq_source_authority="true")
    _reseal(bu)
    with pytest.raises(TodayInitialStockAnchorError, match="VENUE_EQ_SOURCE_AUTHORITY_DRIFT"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_venue_eq_field_as_source_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    payload = _load_json(bu / RATIFICATION_FILE)
    payload["eq"] = AUTHORIZED_EQUITY_VALUE
    payload["ratification_digest"] = ratification_digest_v1(payload)
    _write_json(bu / RATIFICATION_FILE, payload)
    _reseal(bu)
    with pytest.raises(TodayInitialStockAnchorError, match="VENUE_FIELD_AS_SOURCE_FORBIDDEN:eq"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_no_venue_io_in_anchor_module() -> None:
    source = ANCHOR_MODULE.read_text(encoding="utf-8")
    assert "import urllib" not in source
    assert "from urllib" not in source
    assert "import requests" not in source
    assert "import http.client" not in source
    assert "from http" not in source
    assert "LiveCanaryHttpClient" not in source
    assert "ENDPOINT_ACCOUNT_BALANCE" not in source
    assert "eea.okx.com" not in source


def test_owner_go_and_sha_mismatch(tmp_path: Path) -> None:
    with pytest.raises(TodayInitialStockAnchorError, match="OWNER_GO_MISMATCH"):
        _execute(evidence_root=tmp_path, owner_go="WRONG")
    with pytest.raises(TodayInitialStockAnchorError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        _execute(evidence_root=tmp_path, origin_main_sha="0" * 40)


def test_anchor_does_not_mutate_kind_set_or_rewrite_parents() -> None:
    claims = _load_json(CANONICAL_PACK / "claims.json")
    assert claims["INITIAL_STOCK_ANCHOR_STATUS"] == STATUS_PRESENT
    assert claims["LIVE_EQUITY_STOCK_KIND_SET"] == KIND_SET_EMPTY
    assert claims["KIND_SET"] == KIND_SET_EMPTY
    assert claims["KIND_SET_MEMBERS"] == "NONE"
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["VENUE_GET_COUNT_ADDED"] == "0"
    assert claims["VENUE_POST_COUNT"] == "0"
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is False
    bu_ratification = _load_json(SEALED_BU / RATIFICATION_FILE)
    assert bu_ratification["initial_stock_anchor_status"] == "ABSENT"
    assert bu_ratification["ratification_digest"] == AUTHORIZED_RATIFICATION_DIGEST
    candidate = _load_json(SEALED_BT / CANDIDATE_FILE)
    assert candidate["declaration_id"] == AUTHORIZED_DECLARATION_ID
    assert candidate["initial_stock_anchor_status"] == "ABSENT"


def test_canonical_pack_and_parents_unrewritten() -> None:
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0
    assert verify_manifest_sha256_v1(store_root=SEALED_BT) == 0
    assert verify_manifest_sha256_v1(store_root=SEALED_BU) == 0
    anchor = _load_json(CANONICAL_PACK / "today_initial_stock_anchor_v1.json")
    assert anchor["anchor_id"] == AUTHORIZED_ANCHOR_ID
    assert anchor["declaration_id"] == AUTHORIZED_DECLARATION_ID
    assert anchor["candidate_digest"] == AUTHORIZED_PROVENANCE_DIGEST
    assert anchor["ratification_digest"] == AUTHORIZED_RATIFICATION_DIGEST
    assert anchor["equity_value"] == AUTHORIZED_EQUITY_VALUE
    assert anchor["equity_unit"] == EQUITY_UNIT
    assert ECONOMIC_MEANING == anchor["economic_meaning"]
    claims = _load_json(CANONICAL_PACK / "claims.json")
    assert claims["CANDIDATE_RATIFICATION_ANCHOR_LINEAGE_VALID"] == "true"
    assert claims["PROTECTED_SURFACES_UNCHANGED"] == "true"


def test_runbook_bv_and_navigation_persist() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    bv_section = _bv_section()
    assert OWNER_GO in bv_section
    assert AUTHORIZED_DECLARATION_ID in bv_section
    assert AUTHORIZED_ANCHOR_ID in bv_section
    assert "RATIFICATION_STATUS=RATIFIED" in bv_section
    assert "INITIAL_STOCK_ANCHOR_STATUS=PRESENT" in bv_section
    assert "LIVE_EQUITY_STOCK_KIND_SET=EMPTY_FAIL_CLOSED" in bv_section
    assert "KIND_SET_MEMBERS=NONE" in bv_section
    assert "VENUE_EQ_SOURCE_AUTHORITY=false" in bv_section
    assert "VENUE_GET_COUNT_ADDED=0" in bv_section
    assert "VENUE_POST_COUNT=0" in bv_section
    assert EARLIEST_LIVE_CRITICAL_PATH_BLOCKER in bv_section
    assert NEXT_OWNER_GO_REQUIRED in bv_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.BV" in bv_section
    assert BU_HEADING in RUNBOOK.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_ANCHOR_WP1" in spec
    assert "FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_ANCHOR_WP1.md" in mot
    assert BV_HEADING in mot
    assert "11.2.1.BV" in atlas
    assert "live_equity_stock_today_initial_stock_anchor_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is False
