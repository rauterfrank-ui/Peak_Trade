"""Today initial-stock KIND_SET membership V1 tests.

Exact authorized Anchor plus defined kind only. Singleton KIND_SET.
No GET. No POST. Sealed BT/BU/BV artifacts are not rewritten.
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
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_anchor_v1 import (
    ANCHOR_FILE,
    AUTHORIZED_ANCHOR_ID,
    CANONICAL_PACK_RELPATH as CANONICAL_BV_PACK_RELPATH,
    anchor_digest_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_kind_set_membership_v1 import (
    AUTHORIZED_MEMBERSHIP_ID,
    CANONICAL_PACK_RELPATH,
    EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
    EXPECTED_ORIGIN_MAIN_SHA,
    MEMBERSHIP_STATUS_PRESENT,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_GO,
    SOURCE_KIND_DEFINED_MEMBER,
    TodayInitialStockKindSetMembershipError,
    assert_defined_today_kind_identity_v1,
    assert_exclusive_today_kind_set_members_v1,
    execute_live_equity_stock_today_initial_stock_kind_set_membership_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_ratification_v1 import (
    AUTHORIZED_AS_OF_TIME,
    AUTHORIZED_DECLARATION_ID,
    AUTHORIZED_EQUITY_VALUE,
    AUTHORIZED_PROVENANCE_DIGEST,
    CANONICAL_PACK_RELPATH as CANONICAL_BU_PACK_RELPATH,
    IDENTITY_FILE,
    RATIFICATION_FILE,
    TODAY_SOURCE_KIND,
    ratification_digest_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_source_kind_v1 import (
    SOURCE_KIND_DEFINED_NOT_MEMBER,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_KIND_SET_MEMBERSHIP_WP1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
MEMBERSHIP_MODULE = (
    REPO_ROOT
    / "src/ops/governed_productive_account_equity_authority_producer_v1/"
    / "live_equity_stock_today_initial_stock_kind_set_membership_v1.py"
)
BV_HEADING = "11.2.1.BV FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_ANCHOR"
BW_HEADING = "11.2.1.BW FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_KIND_SET_MEMBERSHIP"
SEALED_BT = REPO_ROOT / CANONICAL_BT_PACK_RELPATH
SEALED_BU = REPO_ROOT / CANONICAL_BU_PACK_RELPATH
SEALED_BV = REPO_ROOT / CANONICAL_BV_PACK_RELPATH
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


def _mutate_anchor(pack: Path, **fields: str) -> None:
    path = pack / ANCHOR_FILE
    payload = _load_json(path)
    payload.update(fields)
    payload["anchor_digest"] = anchor_digest_v1(payload)
    _write_json(path, payload)


def _execute(
    *,
    evidence_root: Path,
    sealed_bv_pack: Path = SEALED_BV,
    sealed_bu_pack: Path = SEALED_BU,
    sealed_bt_pack: Path = SEALED_BT,
    **kwargs: str,
):
    return execute_live_equity_stock_today_initial_stock_kind_set_membership_v1(
        owner_go=kwargs.get("owner_go", OWNER_GO),
        origin_main_sha=kwargs.get("origin_main_sha", EXPECTED_ORIGIN_MAIN_SHA),
        repo_root=REPO_ROOT,
        evidence_root=evidence_root,
        sealed_bv_pack=sealed_bv_pack,
        sealed_bu_pack=sealed_bu_pack,
        sealed_bt_pack=sealed_bt_pack,
        persist_as_of=kwargs.get("persist_as_of", "2026-09-14T21:25:00Z"),
    )


def _bw_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BW_HEADING)
    return runbook[start : runbook.index("## 11.3 Autonomy state model", start)]


def test_authorized_anchor_and_defined_kind_bind_membership(tmp_path: Path) -> None:
    result = _execute(evidence_root=tmp_path)
    assert result.declaration_id == AUTHORIZED_DECLARATION_ID
    assert result.candidate_digest == AUTHORIZED_PROVENANCE_DIGEST
    assert result.anchor_id == AUTHORIZED_ANCHOR_ID
    assert result.membership_id == AUTHORIZED_MEMBERSHIP_ID
    assert result.source_kind_id == TODAY_SOURCE_KIND
    assert result.source_kind_status == SOURCE_KIND_DEFINED_MEMBER
    assert result.membership_status == MEMBERSHIP_STATUS_PRESENT
    assert result.live_equity_stock_kind_set == TODAY_SOURCE_KIND
    assert result.kind_set_members == TODAY_SOURCE_KIND
    assert result.membership_owner_ratification_required == "false"
    assert result.venue_eq_source_authority == "false"
    assert result.venue_get_count_added == "0"
    assert result.venue_post_count == "0"
    assert result.candidate_ratification_anchor_membership_lineage_valid == "true"
    assert result.earliest_live_critical_path_blocker == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER
    assert result.next_owner_go_required == NEXT_OWNER_GO_REQUIRED
    store = Path(result.store_root)
    membership = _load_json(store / "today_initial_stock_kind_set_membership_v1.json")
    assert membership["equity_value"] == AUTHORIZED_EQUITY_VALUE
    assert membership["equity_unit"] == EQUITY_UNIT
    assert membership["settlement_currency"] == "USDC"
    assert membership["equity_precision"] == "15"
    assert membership["economic_meaning"] == ECONOMIC_MEANING
    assert membership["as_of_time"] == AUTHORIZED_AS_OF_TIME
    assert membership["source_kind"] == TODAY_SOURCE_KIND
    assert membership["live_equity_stock_kind_set"] == TODAY_SOURCE_KIND
    lineage = _load_json(store / "candidate_ratification_anchor_membership_lineage_v1.json")
    assert lineage["lineage"] == "CANDIDATE->RATIFICATION->ANCHOR->MEMBERSHIP"
    assert lineage["lineage_valid"] == "true"
    claims = _load_json(store / "claims.json")
    assert claims["KIND_SET_MEMBERS"] == TODAY_SOURCE_KIND
    assert claims["MEMBERSHIP_OWNER_RATIFICATION_REQUIRED"] == "false"
    assert claims["VENUE_GET_COUNT_ADDED"] == "0"
    assert claims["VENUE_POST_COUNT"] == "0"
    assert claims["BT_CANDIDATE_REWRITTEN"] == "false"
    assert claims["BU_RATIFICATION_REWRITTEN"] == "false"
    assert claims["BV_ANCHOR_REWRITTEN"] == "false"
    assert claims["MASTER_V2_UNCHANGED"] == "true"
    assert claims["STEP_29P_UNCHANGED"] == "true"
    before_after = _load_json(store / "kind_set_membership_before_after_v1.json")
    assert before_after["live_equity_stock_kind_set_before"] == "EMPTY_FAIL_CLOSED"
    assert before_after["kind_set_members_before"] == "NONE"
    assert before_after["kind_set_members_after"] == TODAY_SOURCE_KIND
    kind_identity = _load_json(store / "exact_kind_identity_v1.json")
    assert kind_identity["source_kind_status_before"] == SOURCE_KIND_DEFINED_NOT_MEMBER
    assert kind_identity["source_kind_status_after"] == SOURCE_KIND_DEFINED_MEMBER
    assert verify_manifest_sha256_v1(store_root=store) == 0


def test_missing_anchor_denied(tmp_path: Path) -> None:
    bv = _copy_pack(SEALED_BV, tmp_path / "bv")
    (bv / ANCHOR_FILE).unlink()
    _reseal(bv)
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="ANCHOR_ABSENT"):
        _execute(evidence_root=tmp_path / "out", sealed_bv_pack=bv)


def test_missing_ratification_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    (bu / RATIFICATION_FILE).unlink()
    _reseal(bu)
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="RATIFICATION_ABSENT"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_wrong_candidate_id_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    _mutate_ratification(bu, declaration_id="GOVERNED_TODAY_CANDIDATE_deadbeefdeadbeef")
    _mutate_identity(bu, declaration_id="GOVERNED_TODAY_CANDIDATE_deadbeefdeadbeef")
    _reseal(bu)
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="DECLARATION_ID_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_wrong_anchor_id_denied(tmp_path: Path) -> None:
    bv = _copy_pack(SEALED_BV, tmp_path / "bv")
    _mutate_anchor(bv, anchor_id="GOVERNED_TODAY_INITIAL_STOCK_ANCHOR_deadbeefdeadbeef")
    _reseal(bv)
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="ANCHOR_ID_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bv_pack=bv)


def test_wrong_candidate_digest_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    _mutate_ratification(bu, candidate_digest="0" * 64)
    _reseal(bu)
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="CANDIDATE_DIGEST_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_wrong_ratification_digest_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    payload = _load_json(bu / RATIFICATION_FILE)
    payload["ratification_digest"] = "0" * 64
    _write_json(bu / RATIFICATION_FILE, payload)
    _reseal(bu)
    with pytest.raises(
        TodayInitialStockKindSetMembershipError, match="RATIFICATION_DIGEST_MISMATCH"
    ):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_wrong_anchor_digest_denied(tmp_path: Path) -> None:
    bv = _copy_pack(SEALED_BV, tmp_path / "bv")
    payload = _load_json(bv / ANCHOR_FILE)
    payload["anchor_digest"] = "0" * 64
    _write_json(bv / ANCHOR_FILE, payload)
    _reseal(bv)
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="ANCHOR_DIGEST_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bv_pack=bv)


def test_unknown_kind_denied() -> None:
    with pytest.raises(
        TodayInitialStockKindSetMembershipError, match="UNKNOWN_OR_ALIAS_STOCK_KIND"
    ):
        assert_defined_today_kind_identity_v1("SOME_OTHER_STOCK_KIND")


def test_kind_alias_substitution_denied() -> None:
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="KIND_ALIAS_OR_SUBSTITUTION"):
        assert_defined_today_kind_identity_v1("TODAY_INITIAL_STOCK")
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="KIND_ALIAS_OR_SUBSTITUTION"):
        assert_defined_today_kind_identity_v1("eq")


def test_wrong_kind_on_anchor_denied(tmp_path: Path) -> None:
    bv = _copy_pack(SEALED_BV, tmp_path / "bv")
    _mutate_anchor(bv, source_kind="TODAY_INITIAL_STOCK")
    _reseal(bv)
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="KIND_ALIAS_OR_SUBSTITUTION"):
        _execute(evidence_root=tmp_path / "out", sealed_bv_pack=bv)


def test_extra_kind_set_member_denied() -> None:
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="EXTRA_KIND_SET_MEMBER"):
        assert_exclusive_today_kind_set_members_v1((TODAY_SOURCE_KIND, "VENUE_EQ"))
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="EXTRA_KIND_SET_MEMBER"):
        assert_exclusive_today_kind_set_members_v1(f"{TODAY_SOURCE_KIND},U04")


def test_equity_value_mismatch_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    _mutate_ratification(bu, equity_value="9.999")
    _mutate_identity(bu, equity_value="9.999")
    _reseal(bu)
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="EQUITY_VALUE_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_equity_unit_mismatch_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    _mutate_ratification(bu, equity_unit="USDC")
    _mutate_identity(bu, equity_unit="USDC")
    _reseal(bu)
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="EQUITY_UNIT_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_settlement_currency_mismatch_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    _mutate_ratification(bu, settlement_currency="USD")
    _mutate_identity(bu, settlement_currency="USD")
    _reseal(bu)
    with pytest.raises(
        TodayInitialStockKindSetMembershipError, match="SETTLEMENT_CURRENCY_MISMATCH"
    ):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_equity_scale_mismatch_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    _mutate_identity(bu, equity_precision="2")
    _reseal(bu)
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="EQUITY_PRECISION_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_as_of_time_mismatch_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    _mutate_ratification(bu, as_of_time="2026-09-14T00:00:00Z")
    _mutate_identity(bu, as_of_time="2026-09-14T00:00:00Z")
    _reseal(bu)
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="AS_OF_TIME_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_economic_meaning_mismatch_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    _mutate_ratification(bu, economic_meaning="SOMETHING_ELSE")
    _mutate_identity(bu, economic_meaning="SOMETHING_ELSE")
    _reseal(bu)
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="ECONOMIC_MEANING_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_candidate_substitution_denied(tmp_path: Path) -> None:
    bt = _copy_pack(SEALED_BT, tmp_path / "bt")
    _mutate_candidate(bt, declaration_id="GOVERNED_TODAY_CANDIDATE_ffffffffffffffff")
    _reseal(bt)
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="DECLARATION_ID_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bt_pack=bt)


def test_numeric_equity_coercion_denied(tmp_path: Path) -> None:
    bu = _copy_pack(SEALED_BU, tmp_path / "bu")
    payload = json.loads((bu / RATIFICATION_FILE).read_text(encoding="utf-8"))
    payload["equity_value"] = 2.29
    (bu / RATIFICATION_FILE).write_text(json.dumps(payload) + "\n", encoding="utf-8")
    _reseal(bu)
    with pytest.raises(
        TodayInitialStockKindSetMembershipError, match="NUMERIC_COERCION_FORBIDDEN:equity_value"
    ):
        _execute(evidence_root=tmp_path / "out", sealed_bu_pack=bu)


def test_venue_eq_cannot_become_source_authority(tmp_path: Path) -> None:
    bv = _copy_pack(SEALED_BV, tmp_path / "bv")
    _mutate_anchor(bv, venue_eq_source_authority="true")
    _reseal(bv)
    with pytest.raises(
        TodayInitialStockKindSetMembershipError, match="VENUE_EQ_SOURCE_AUTHORITY_DRIFT"
    ):
        _execute(evidence_root=tmp_path / "out", sealed_bv_pack=bv)


def test_venue_eq_field_as_source_denied(tmp_path: Path) -> None:
    bv = _copy_pack(SEALED_BV, tmp_path / "bv")
    payload = _load_json(bv / ANCHOR_FILE)
    payload["eq"] = AUTHORIZED_EQUITY_VALUE
    payload["anchor_digest"] = anchor_digest_v1(payload)
    _write_json(bv / ANCHOR_FILE, payload)
    _reseal(bv)
    with pytest.raises(
        TodayInitialStockKindSetMembershipError, match="VENUE_FIELD_AS_SOURCE_FORBIDDEN:eq"
    ):
        _execute(evidence_root=tmp_path / "out", sealed_bv_pack=bv)


def test_no_venue_io_in_membership_module() -> None:
    source = MEMBERSHIP_MODULE.read_text(encoding="utf-8")
    assert "import urllib" not in source
    assert "from urllib" not in source
    assert "import requests" not in source
    assert "import http.client" not in source
    assert "from http" not in source
    assert "LiveCanaryHttpClient" not in source
    assert "ENDPOINT_ACCOUNT_BALANCE" not in source
    assert "eea.okx.com" not in source


def test_owner_go_and_sha_mismatch(tmp_path: Path) -> None:
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="OWNER_GO_MISMATCH"):
        _execute(evidence_root=tmp_path, owner_go="WRONG")
    with pytest.raises(TodayInitialStockKindSetMembershipError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        _execute(evidence_root=tmp_path, origin_main_sha="0" * 40)


def test_membership_does_not_rewrite_parents() -> None:
    claims = _load_json(CANONICAL_PACK / "claims.json")
    assert claims["INITIAL_STOCK_ANCHOR_STATUS"] == "PRESENT"
    assert claims["LIVE_EQUITY_STOCK_KIND_SET"] == TODAY_SOURCE_KIND
    assert claims["KIND_SET"] == "EMPTY_FAIL_CLOSED"
    assert claims["KIND_SET_MEMBERS"] == TODAY_SOURCE_KIND
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["VENUE_GET_COUNT_ADDED"] == "0"
    assert claims["VENUE_POST_COUNT"] == "0"
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    bv_anchor = _load_json(SEALED_BV / ANCHOR_FILE)
    assert bv_anchor["kind_set_members"] == "NONE"
    assert bv_anchor["live_equity_stock_kind_set"] == "EMPTY_FAIL_CLOSED"
    assert bv_anchor["membership_owner_ratification_required"] == "true"
    bu_ratification = _load_json(SEALED_BU / RATIFICATION_FILE)
    assert bu_ratification["initial_stock_anchor_status"] == "ABSENT"
    candidate = _load_json(SEALED_BT / CANDIDATE_FILE)
    assert candidate["declaration_id"] == AUTHORIZED_DECLARATION_ID


def test_canonical_pack_and_parents_unrewritten() -> None:
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0
    assert verify_manifest_sha256_v1(store_root=SEALED_BT) == 0
    assert verify_manifest_sha256_v1(store_root=SEALED_BU) == 0
    assert verify_manifest_sha256_v1(store_root=SEALED_BV) == 0
    membership = _load_json(CANONICAL_PACK / "today_initial_stock_kind_set_membership_v1.json")
    assert membership["membership_id"] == AUTHORIZED_MEMBERSHIP_ID
    assert membership["declaration_id"] == AUTHORIZED_DECLARATION_ID
    assert membership["candidate_digest"] == AUTHORIZED_PROVENANCE_DIGEST
    assert membership["anchor_id"] == AUTHORIZED_ANCHOR_ID
    assert membership["equity_value"] == AUTHORIZED_EQUITY_VALUE
    assert membership["source_kind"] == TODAY_SOURCE_KIND
    claims = _load_json(CANONICAL_PACK / "claims.json")
    assert claims["CANDIDATE_RATIFICATION_ANCHOR_MEMBERSHIP_LINEAGE_VALID"] == "true"
    assert claims["PROTECTED_SURFACES_UNCHANGED"] == "true"


def test_runbook_bw_and_navigation_persist() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    bw_section = _bw_section()
    assert OWNER_GO in bw_section
    assert AUTHORIZED_DECLARATION_ID in bw_section
    assert AUTHORIZED_ANCHOR_ID in bw_section
    assert AUTHORIZED_MEMBERSHIP_ID in bw_section
    assert "RATIFICATION_STATUS=RATIFIED" in bw_section
    assert "INITIAL_STOCK_ANCHOR_STATUS=PRESENT" in bw_section
    assert f"LIVE_EQUITY_STOCK_KIND_SET={TODAY_SOURCE_KIND}" in bw_section
    assert f"KIND_SET_MEMBERS={TODAY_SOURCE_KIND}" in bw_section
    assert "SOURCE_KIND_STATUS=DEFINED_KIND_SET_MEMBER" in bw_section
    assert "MEMBERSHIP_OWNER_RATIFICATION_REQUIRED=false" in bw_section
    assert "VENUE_EQ_SOURCE_AUTHORITY=false" in bw_section
    assert "VENUE_GET_COUNT_ADDED=0" in bw_section
    assert "VENUE_POST_COUNT=0" in bw_section
    assert EARLIEST_LIVE_CRITICAL_PATH_BLOCKER in bw_section
    assert NEXT_OWNER_GO_REQUIRED in bw_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.BW" in bw_section
    assert BV_HEADING in RUNBOOK.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_KIND_SET_MEMBERSHIP_WP1" in spec
    )
    assert "FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_KIND_SET_MEMBERSHIP_WP1.md" in mot
    assert BW_HEADING in mot
    assert "11.2.1.BW" in atlas
    assert "live_equity_stock_today_initial_stock_kind_set_membership_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
