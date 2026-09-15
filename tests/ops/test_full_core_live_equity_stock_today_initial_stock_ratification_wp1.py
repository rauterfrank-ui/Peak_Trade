"""Today initial-stock Owner ratification tests.

Exact authorized candidate only. No Anchor. No KIND_SET mutation.
No GET. No POST. Sealed BT candidate is not rewritten.
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
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_declaration_governed_binding_contract_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BT_PACK_RELPATH,
    CANDIDATE_FILE,
    ECONOMIC_MEANING,
    EQUITY_UNIT,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_ratification_v1 import (
    AUTHORIZED_AS_OF_TIME,
    AUTHORIZED_DECLARATION_ID,
    AUTHORIZED_EQUITY_VALUE,
    AUTHORIZED_PROVENANCE_DIGEST,
    CANONICAL_PACK_RELPATH,
    EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_GO,
    REASON_FIXTURE_CANNOT_PROMOTE,
    TodayInitialStockRatificationError,
    execute_live_equity_stock_today_initial_stock_ratification_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_source_kind_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BS_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_RATIFICATION_WP1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
BT_HEADING = "11.2.1.BT FULL_CORE_LIVE_EQUITY_STOCK_TODAY_DECLARATION_GOVERNED_BINDING_CONTRACT"
BU_HEADING = "11.2.1.BU FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_RATIFICATION"
SEALED_BT = REPO_ROOT / CANONICAL_BT_PACK_RELPATH
SEALED_BS = REPO_ROOT / CANONICAL_BS_PACK_RELPATH
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH


def _copy_bt(tmp_path: Path) -> Path:
    dest = tmp_path / "bt_pack"
    shutil.copytree(SEALED_BT, dest)
    return dest


def _mutate_candidate(pack: Path, **fields: str) -> None:
    path = pack / CANDIDATE_FILE
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(fields)
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )


def _reseal(pack: Path) -> None:
    persist_manifest_sha256_v1(store_root=pack)


def _execute(*, evidence_root: Path, sealed_bt_pack: Path = SEALED_BT, **kwargs: str):
    return execute_live_equity_stock_today_initial_stock_ratification_v1(
        owner_go=kwargs.get("owner_go", OWNER_GO),
        origin_main_sha=kwargs.get("origin_main_sha", EXPECTED_ORIGIN_MAIN_SHA),
        repo_root=REPO_ROOT,
        evidence_root=evidence_root,
        sealed_bt_pack=sealed_bt_pack,
        persist_as_of=kwargs.get("persist_as_of", "2026-09-14T18:21:00Z"),
    )


def _bu_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BU_HEADING)
    return runbook[start : runbook.index("## 11.3 Autonomy state model", start)]


def test_authorized_candidate_ratified(tmp_path: Path) -> None:
    result = _execute(evidence_root=tmp_path)
    assert result.declaration_id == AUTHORIZED_DECLARATION_ID
    assert result.candidate_digest == AUTHORIZED_PROVENANCE_DIGEST
    assert result.candidate_status == "PRESENT"
    assert result.ratification_status == "RATIFIED"
    assert result.initial_stock_anchor_status == "ABSENT"
    assert result.live_equity_stock_kind_set == KIND_SET_EMPTY
    assert result.venue_eq_source_authority == "false"
    assert result.venue_get_count_added == "0"
    assert result.venue_post_count == "0"
    assert result.earliest_live_critical_path_blocker == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER
    store = Path(result.store_root)
    sealed = json.loads((SEALED_BT / CANDIDATE_FILE).read_text(encoding="utf-8"))
    assert sealed["declaration_id"] == AUTHORIZED_DECLARATION_ID
    assert sealed["ratification_status"] == "NOT_RATIFIED"
    assert sealed["equity_value"] == AUTHORIZED_EQUITY_VALUE
    assert sealed["as_of_time"] == AUTHORIZED_AS_OF_TIME
    ratification = json.loads(
        (store / "today_initial_stock_owner_ratification_v1.json").read_text(encoding="utf-8")
    )
    assert ratification["ratification_status"] == "RATIFIED"
    assert ratification["initial_stock_anchor_status"] == "ABSENT"
    assert ratification["live_equity_stock_kind_set"] == KIND_SET_EMPTY
    assert ratification["venue_eq_source_authority"] == "false"
    assert ratification["ratification_is_not_anchor"] == "true"
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    assert claims["VENUE_GET_COUNT_ADDED"] == "0"
    assert claims["VENUE_POST_COUNT"] == "0"
    assert claims["BT_CANDIDATE_REWRITTEN"] == "false"
    assert claims["MASTER_V2_UNCHANGED"] == "true"
    assert claims["STEP_29P_UNCHANGED"] == "true"
    assert verify_manifest_sha256_v1(store_root=store) == 0


def _recompute_digest(pack: Path) -> None:
    from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_declaration_governed_binding_contract_v1 import (
        semantic_candidate_digest_v1,
    )

    path = pack / CANDIDATE_FILE
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["provenance_digest"] = semantic_candidate_digest_v1(payload)
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )


def test_wrong_declaration_id_denied(tmp_path: Path) -> None:
    pack = _copy_bt(tmp_path)
    _mutate_candidate(pack, declaration_id="GOVERNED_TODAY_CANDIDATE_deadbeefdeadbeef")
    _recompute_digest(pack)
    _reseal(pack)
    with pytest.raises(TodayInitialStockRatificationError, match="DECLARATION_ID_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bt_pack=pack)


def test_wrong_candidate_digest_denied(tmp_path: Path) -> None:
    pack = _copy_bt(tmp_path)
    _mutate_candidate(pack, provenance_digest="0" * 64)
    _reseal(pack)
    with pytest.raises(TodayInitialStockRatificationError, match="CANDIDATE_DIGEST_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bt_pack=pack)


def test_modified_equity_value_denied(tmp_path: Path) -> None:
    pack = _copy_bt(tmp_path)
    _mutate_candidate(pack, equity_value="9.999")
    _recompute_digest(pack)
    _reseal(pack)
    with pytest.raises(TodayInitialStockRatificationError, match="EQUITY_VALUE_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bt_pack=pack)


def test_modified_as_of_time_denied(tmp_path: Path) -> None:
    pack = _copy_bt(tmp_path)
    _mutate_candidate(pack, as_of_time="2026-09-14T00:00:00Z")
    _recompute_digest(pack)
    _reseal(pack)
    with pytest.raises(TodayInitialStockRatificationError, match="AS_OF_TIME_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bt_pack=pack)


def test_candidate_substitution_denied(tmp_path: Path) -> None:
    pack = _copy_bt(tmp_path)
    payload = json.loads((pack / CANDIDATE_FILE).read_text(encoding="utf-8"))
    payload["declaration_id"] = "GOVERNED_TODAY_CANDIDATE_ffffffffffffffff"
    from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_declaration_governed_binding_contract_v1 import (
        semantic_candidate_digest_v1,
    )

    payload["provenance_digest"] = semantic_candidate_digest_v1(payload)
    (pack / CANDIDATE_FILE).write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    _reseal(pack)
    with pytest.raises(TodayInitialStockRatificationError, match="DECLARATION_ID_MISMATCH"):
        _execute(evidence_root=tmp_path / "out", sealed_bt_pack=pack)


def test_absent_candidate_denied(tmp_path: Path) -> None:
    pack = _copy_bt(tmp_path)
    (pack / CANDIDATE_FILE).unlink()
    _reseal(pack)
    with pytest.raises(TodayInitialStockRatificationError, match="CANDIDATE_ABSENT"):
        _execute(evidence_root=tmp_path / "out", sealed_bt_pack=pack)


def test_malformed_candidate_denied(tmp_path: Path) -> None:
    pack = _copy_bt(tmp_path)
    (pack / CANDIDATE_FILE).write_text("{not-json", encoding="utf-8")
    _reseal(pack)
    with pytest.raises(TodayInitialStockRatificationError, match="CANDIDATE_MALFORMED"):
        _execute(evidence_root=tmp_path / "out", sealed_bt_pack=pack)


def test_numeric_equity_coercion_denied(tmp_path: Path) -> None:
    pack = _copy_bt(tmp_path)
    payload = json.loads((pack / CANDIDATE_FILE).read_text(encoding="utf-8"))
    payload["equity_value"] = 2.29
    (pack / CANDIDATE_FILE).write_text(json.dumps(payload) + "\n", encoding="utf-8")
    _reseal(pack)
    with pytest.raises(
        TodayInitialStockRatificationError, match="NUMERIC_COERCION_FORBIDDEN:equity_value"
    ):
        _execute(evidence_root=tmp_path / "out", sealed_bt_pack=pack)


def test_fixture_candidate_denied(tmp_path: Path) -> None:
    pack = _copy_bt(tmp_path)
    payload = json.loads((pack / CANDIDATE_FILE).read_text(encoding="utf-8"))
    payload["declaration_id"] = "FIXTURE_TODAY_CANDIDATE"
    from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_declaration_governed_binding_contract_v1 import (
        semantic_candidate_digest_v1,
    )

    payload["provenance_digest"] = semantic_candidate_digest_v1(payload)
    (pack / CANDIDATE_FILE).write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    _reseal(pack)
    with pytest.raises(TodayInitialStockRatificationError, match=REASON_FIXTURE_CANNOT_PROMOTE):
        _execute(evidence_root=tmp_path / "out", sealed_bt_pack=pack)


def test_tampered_pack_without_reseal_denied(tmp_path: Path) -> None:
    pack = _copy_bt(tmp_path)
    _mutate_candidate(pack, declaration_id="GOVERNED_TODAY_CANDIDATE_deadbeefdeadbeef")
    with pytest.raises(TodayInitialStockRatificationError, match="BT_MANIFEST_VERIFY_FAILED"):
        _execute(evidence_root=tmp_path / "out", sealed_bt_pack=pack)


def test_owner_go_and_sha_mismatch(tmp_path: Path) -> None:
    with pytest.raises(TodayInitialStockRatificationError, match="OWNER_GO_MISMATCH"):
        _execute(evidence_root=tmp_path, owner_go="WRONG")
    with pytest.raises(TodayInitialStockRatificationError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        _execute(evidence_root=tmp_path, origin_main_sha="0" * 40)


def test_ratification_does_not_create_anchor_or_mutate_kind_set() -> None:
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["INITIAL_STOCK_ANCHOR_STATUS"] == "ABSENT"
    assert claims["LIVE_EQUITY_STOCK_KIND_SET"] == KIND_SET_EMPTY
    assert claims["KIND_SET"] == KIND_SET_EMPTY
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["VENUE_GET_COUNT_ADDED"] == "0"
    assert claims["VENUE_POST_COUNT"] == "0"
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True


def test_canonical_pack_and_bt_candidate_unrewritten() -> None:
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0
    assert verify_manifest_sha256_v1(store_root=SEALED_BT) == 0
    assert verify_manifest_sha256_v1(store_root=SEALED_BS) == 0
    candidate = json.loads((SEALED_BT / CANDIDATE_FILE).read_text(encoding="utf-8"))
    assert candidate["declaration_id"] == AUTHORIZED_DECLARATION_ID
    assert candidate["provenance_digest"] == AUTHORIZED_PROVENANCE_DIGEST
    assert candidate["equity_value"] == AUTHORIZED_EQUITY_VALUE
    assert candidate["equity_unit"] == EQUITY_UNIT
    assert candidate["equity_value"] != candidate.get("settlement_currency")
    ratification = json.loads(
        (CANONICAL_PACK / "today_initial_stock_owner_ratification_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert ratification["declaration_id"] == AUTHORIZED_DECLARATION_ID
    assert ratification["candidate_digest"] == AUTHORIZED_PROVENANCE_DIGEST
    assert ratification["ratification_status"] == "RATIFIED"
    assert ECONOMIC_MEANING in json.dumps(ratification)


def test_runbook_bu_and_navigation_persist() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    bu_section = _bu_section()
    assert OWNER_GO in bu_section
    assert AUTHORIZED_DECLARATION_ID in bu_section
    assert "RATIFICATION_STATUS=RATIFIED" in bu_section
    assert "CANDIDATE_STATUS=PRESENT" in bu_section
    assert "INITIAL_STOCK_ANCHOR_STATUS=ABSENT" in bu_section
    assert "LIVE_EQUITY_STOCK_KIND_SET=EMPTY_FAIL_CLOSED" in bu_section
    assert "VENUE_EQ_SOURCE_AUTHORITY=false" in bu_section
    assert "VENUE_GET_COUNT_ADDED=0" in bu_section
    assert "VENUE_POST_COUNT=0" in bu_section
    assert EARLIEST_LIVE_CRITICAL_PATH_BLOCKER in bu_section
    assert NEXT_OWNER_GO_REQUIRED in bu_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.BU" in bu_section
    assert BT_HEADING in RUNBOOK.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_RATIFICATION_WP1" in spec
    assert "FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_RATIFICATION_WP1.md" in mot
    assert BU_HEADING in mot
    assert "11.2.1.BU" in atlas
    assert "live_equity_stock_today_initial_stock_ratification_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
