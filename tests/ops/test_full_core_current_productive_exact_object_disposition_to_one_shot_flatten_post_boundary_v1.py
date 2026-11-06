"""CURRENT_PRODUCTIVE exact-object disposition to flatten POST boundary tests.

Injected GET only. No venue POST. PERMIT_CREATED=false. POST_COUNT=0.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM,
    EXTERNAL_EFFECT_AUTHORIZED,
    FULL_CORE_ACTUAL_HTTP_POST_SEAM_IMPLEMENTED,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    MAX_EXTERNAL_EFFECT_POST_COUNT,
    ONE_SHOT_REAL_POST_REQUIRES_EXACT_ENVELOPE_BOUND_PERMIT,
    ONE_SHOT_REAL_POST_STANDING_EXTERNAL_EFFECT_FORBIDDEN,
    ONE_SHOT_REAL_POST_TRANSPORT_IMPLEMENTED,
    POST_ALLOWED,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    REAL_EXTERNAL_EFFECT_AUTHORIZED,
    REAL_VENUE_POST_ALLOWED,
    SUBMISSION_AUTHORIZED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_exact_object_flatten_plan_v1 import (
    ALREADY_FLAT,
    OBJECT_MISMATCH,
    flatten_side_from_net_pos_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ENDPOINT_MARKET_TICKER,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    DurableKillSwitchEvidenceStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    ONE_SHOT_REAL_POST_AUTHORITY_REFS,
    issue_external_effect_permit_v1,
    permit_authorizes_one_shot_real_post_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_PUBLIC_INSTRUMENTS,
    ENDPOINT_PUBLIC_PRICE_LIMIT,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreProductiveHttpPostError,
    FullCoreProductiveHttpTradeOrderTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_EXACT_OBJECT_DISPOSITION_TO_ONE_SHOT_FLATTEN_POST_BOUNDARY_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_exact_object_disposition_to_one_shot_flatten_post_boundary_v1 import (
    CANONICAL_PACK_RELPATH,
    ENDPOINT_ORDERS_PENDING,
    EXPECTED_ORIGIN_MAIN_SHA,
    GRANTED_INST_ID,
    GRANTED_POS_ID,
    NEXT_OWNER_GO,
    OWNER_GO,
    THIS_SLICE,
    CurrentProductiveExactObjectDispositionError,
    execute_current_productive_exact_object_disposition_to_one_shot_flatten_post_boundary_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _envelope,
    _handle,
)
from tests.ops.test_full_core_current_productive_eea_universe_inventory_to_cap24_and_29p_v1 import (
    InjectedPayloadsFreshGetTransportV1,
)
from decimal import Decimal

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_EXACT_OBJECT_DISPOSITION_"
    "TO_ONE_SHOT_FLATTEN_POST_BOUNDARY_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
DL_HEADING = (
    "### 11.2.1.DL FULL_CORE_CURRENT_PRODUCTIVE_EXACT_OBJECT_DISPOSITION_TO_"
    "ONE_SHOT_FLATTEN_POST_BOUNDARY"
)
PROTECTED_ALGORITHM_FILES = (
    "src/ops/governed_futures_universe_producer_v1/eligibility_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/policy_v1.py",
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
)


def _position_row(*, pos: str = "1", pos_id: str = GRANTED_POS_ID) -> dict[str, str]:
    return {
        "instId": GRANTED_INST_ID,
        "instType": "FUTURES",
        "pos": pos,
        "posSide": "net",
        "mgnMode": "cross",
        "lever": "3",
        "avgPx": "0.748",
        "ccy": "USDC",
        "posId": pos_id,
        "tradeId": "1055244",
    }


def _payloads(*, pos: str = "1", pending: list | None = None) -> dict[str, object]:
    return {
        ENDPOINT_ACCOUNT_CONFIG: {
            "code": "0",
            "data": [{"uid": "1", "acctLv": "2", "posMode": "net_mode"}],
        },
        ENDPOINT_ACCOUNT_POSITIONS: {"code": "0", "data": [_position_row(pos=pos)]},
        ENDPOINT_ORDERS_PENDING: {"code": "0", "data": list(pending or [])},
        ENDPOINT_PUBLIC_INSTRUMENTS: {
            "code": "0",
            "data": [
                {
                    "instId": GRANTED_INST_ID,
                    "state": "live",
                    "tickSz": "0.0001",
                    "lotSz": "1",
                    "minSz": "1",
                }
            ],
        },
        ENDPOINT_PUBLIC_PRICE_LIMIT: {
            "code": "0",
            "data": [
                {
                    "instId": GRANTED_INST_ID,
                    "buyLmt": "0.7200",
                    "sellLmt": "0.6800",
                }
            ],
        },
        ENDPOINT_MARKET_TICKER: {
            "code": "0",
            "data": [
                {
                    "instId": GRANTED_INST_ID,
                    "bidPx": "0.6860",
                    "askPx": "0.6862",
                    "last": "0.6861",
                }
            ],
        },
    }


def _run(tmp_path: Path, **overrides):
    payload = {
        "owner_go": OWNER_GO,
        "origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
        "evidence_root": tmp_path / "store",
        "fresh_get_transport": InjectedPayloadsFreshGetTransportV1(payloads=_payloads()),
        "execute_network": False,
    }
    payload.update(overrides)
    return execute_current_productive_exact_object_disposition_to_one_shot_flatten_post_boundary_v1(
        **payload
    )


def test_standing_flags_and_authority_wiring() -> None:
    assert (
        CURRENT_PRODUCTIVE_EXACT_OBJECT_DISPOSITION_TO_ONE_SHOT_FLATTEN_POST_BOUNDARY_CREATED
        is True
    )
    assert ONE_SHOT_REAL_POST_TRANSPORT_IMPLEMENTED is True
    assert ONE_SHOT_REAL_POST_REQUIRES_EXACT_ENVELOPE_BOUND_PERMIT is True
    assert ONE_SHOT_REAL_POST_STANDING_EXTERNAL_EFFECT_FORBIDDEN is True
    assert ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM is True
    assert FULL_CORE_ACTUAL_HTTP_POST_SEAM_IMPLEMENTED is True
    assert int(MAX_EXTERNAL_EFFECT_POST_COUNT) == 1
    assert LIVE_ARMED is True
    assert LIVE_AUTHORIZED is True
    assert WIRE_SEND_PERMITTED is True
    assert SUBMISSION_AUTHORIZED is True
    assert PRODUCTIVE_WIRE_SEND_REACHABLE is True
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert POST_ALLOWED is False
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert EXPECTED_ORIGIN_MAIN_SHA == "7360cb0c6fc229de2835aa68399cc8271ad5c8d0"
    assert OWNER_GO not in ONE_SHOT_REAL_POST_AUTHORITY_REFS
    assert NEXT_OWNER_GO in ONE_SHOT_REAL_POST_AUTHORITY_REFS
    assert flatten_side_from_net_pos_v1(Decimal("1")) == "sell"


def test_this_go_does_not_authorize_one_shot_real_post() -> None:
    envelope = _envelope()
    readiness_permit = issue_external_effect_permit_v1(
        envelope,
        authority_ref=OWNER_GO,
        kill_switch_blocked=False,
        durable_kill_switch_evidence_status=(
            DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
        ),
        filegate_denied=False,
        step_29q_status=STEP_29Q_PLAN_ONLY,
    )
    later_permit = issue_external_effect_permit_v1(
        envelope,
        authority_ref=NEXT_OWNER_GO,
        kill_switch_blocked=False,
        durable_kill_switch_evidence_status=(
            DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
        ),
        filegate_denied=False,
        step_29q_status=STEP_29Q_PLAN_ONLY,
    )
    assert permit_authorizes_one_shot_real_post_v1(readiness_permit) is False
    assert permit_authorizes_one_shot_real_post_v1(later_permit) is True


def test_default_http_transport_still_forbids_socket() -> None:
    transport = FullCoreProductiveHttpTradeOrderTransportV1(handle=_handle())
    with pytest.raises(FullCoreProductiveHttpPostError, match="REAL_VENUE_POST_FORBIDDEN"):
        transport.post_trade_order(
            payload={"instId": "MUST_NOT_POST"},
            permit_id="eep-fixture",
            envelope_id="env-fixture",
            envelope_digest="0" * 64,
        )
    assert transport.post_count == 0


def test_owner_go_and_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(CurrentProductiveExactObjectDispositionError, match="OWNER_GO_MISMATCH"):
        _run(tmp_path / "a", owner_go="WRONG")
    with pytest.raises(
        CurrentProductiveExactObjectDispositionError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        _run(tmp_path / "b", origin_main_sha="0" * 40)


def test_injected_path_builds_reduce_only_sell_envelope(tmp_path: Path) -> None:
    result = _run(tmp_path)
    claims = json.loads((Path(result.store_root) / "claims.json").read_text(encoding="utf-8"))
    assert result.authorized_object_match == "true"
    assert result.flatten_plan_created == "true"
    assert result.flatten_side == "sell"
    assert result.flatten_quantity == "1"
    assert result.reduce_only == "true"
    assert result.order_type == "limit"
    assert result.limit_price
    assert result.final_envelope_id.startswith("env-")
    assert len(result.final_envelope_digest) == 64
    assert result.envelope_readiness == "true"
    assert result.permit_created == "false"
    assert result.post_count == "0"
    assert result.real_external_effect_authorized == "false"
    assert claims["HISTORICAL_POSITION_OWNERSHIP"] == "UNKNOWN_NOT_PROVEN"
    assert claims["CURRENT_DISPOSITION_MANAGEMENT_AUTHORITY"] == ("OWNER_GRANTED_EXACT_OBJECT_ONLY")
    assert claims["FLATTEN_POST_AUTHORIZED"] == "false"
    assert claims["PERMIT_CONSUMED_DURABLY"] == "false"
    assert claims["TRANSPORT_ATTEMPTED"] == "false"
    assert claims["VENUE_MUTATION_PERFORMED"] == "false"
    assert claims["CANARY_OR_SECTION_11_14_IMPORTED_AS_OWNERSHIP"] == "false"
    assert claims["ENVELOPE_EXECUTION_FIELDS"]["reduceOnly"] is True
    assert claims["ENVELOPE_EXECUTION_FIELDS"]["side"] == "sell"
    assert result.first_real_blocker == NEXT_OWNER_GO
    assert verify_manifest_sha256_v1(store_root=Path(result.store_root)) == 0


def test_object_mismatch_hard_stops(tmp_path: Path) -> None:
    payloads = _payloads()
    payloads[ENDPOINT_ACCOUNT_POSITIONS] = {
        "code": "0",
        "data": [_position_row(pos_id="999")],
    }
    result = _run(
        tmp_path,
        fresh_get_transport=InjectedPayloadsFreshGetTransportV1(payloads=payloads),
    )
    assert result.authorized_object_match == "false"
    assert result.flatten_plan_created == "false"
    assert result.final_envelope_id == ""
    assert result.permit_created == "false"
    assert result.post_count == "0"
    assert OBJECT_MISMATCH in result.first_real_blocker


def test_already_flat_hard_stops_without_post(tmp_path: Path) -> None:
    payloads = _payloads()
    payloads[ENDPOINT_ACCOUNT_POSITIONS] = {"code": "0", "data": []}
    result = _run(
        tmp_path,
        fresh_get_transport=InjectedPayloadsFreshGetTransportV1(payloads=payloads),
    )
    assert result.first_real_blocker == ALREADY_FLAT
    assert result.flatten_plan_created == "false"
    assert result.post_count == "0"
    assert result.permit_created == "false"


def test_protected_algorithm_files_unchanged_vs_origin_main() -> None:
    import subprocess

    diff = subprocess.run(
        ["git", "diff", "--name-only", "origin/main", "--", *PROTECTED_ALGORITHM_FILES],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert diff.stdout.strip() == ""


def test_ssot_docs_once_present() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    assert DL_HEADING in runbook
    assert THIS_SLICE in runbook
    assert "UNKNOWN_NOT_PROVEN" in runbook
    assert "OWNER_GRANTED_EXACT_OBJECT_ONLY" in runbook
    assert "FLATTEN_POST_AUTHORIZED=false" in runbook
    assert "11.2.1.DL" in mot
    assert OWNER_GO in spec
    assert (
        "current_productive_exact_object_disposition_to_one_shot_flatten_post_boundary_v1.py"
        in atlas
    )
    assert CANONICAL_PACK_RELPATH in runbook or "20260915T212400Z" in runbook
