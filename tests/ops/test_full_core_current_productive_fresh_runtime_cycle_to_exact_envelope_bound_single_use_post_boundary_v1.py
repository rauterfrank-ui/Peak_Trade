"""CURRENT_PRODUCTIVE fresh Cap-23/24 + Master-V2 cycle to envelope-bound POST boundary.

Injected acquisition/GET only. No venue POST. REAL_POST_COUNT=0.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_DEFAULT_INSTRUMENT_ID,
    ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM,
    EXTERNAL_EFFECT_AUTHORIZED,
    FULL_CORE_ACTUAL_HTTP_POST_SEAM_IMPLEMENTED,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
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
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    CYCLE_OWNER,
    ENDPOINT_MARKET_CANDLES,
    ENDPOINT_MARKET_TICKER,
    ENDPOINT_PUBLIC_FUNDING_RATE,
    ENDPOINT_PUBLIC_OPEN_INTEREST,
    extract_finalized_candle_closes_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    DurableKillSwitchEvidenceStatusV1,
    FreshPretradeGetStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_POSITIONS,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    ONE_SHOT_REAL_POST_AUTHORITY_REFS,
    issue_external_effect_permit_v1,
    permit_authorizes_one_shot_real_post_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreProductiveHttpPostError,
    FullCoreProductiveHttpTradeOrderTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_FRESH_RUNTIME_CYCLE_TO_EXACT_ENVELOPE_BOUND_SINGLE_USE_POST_BOUNDARY_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_fresh_runtime_cycle_to_exact_envelope_bound_single_use_post_boundary_v1 import (
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    THIS_SLICE,
    CurrentProductiveFreshRuntimeCycleError,
    execute_current_productive_fresh_runtime_cycle_to_exact_envelope_bound_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from tests.ops.test_full_core_current_productive_eea_universe_inventory_to_cap24_and_29p_v1 import (
    InjectedPayloadsFreshGetTransportV1,
    _eligible_transport,
    _EXPECTED_SELECTED,
    _identity_payloads,
)
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _envelope,
    _handle,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_FRESH_RUNTIME_CYCLE_"
    "TO_EXACT_ENVELOPE_BOUND_SINGLE_USE_POST_BOUNDARY_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
DK_HEADING = (
    "### 11.2.1.DK FULL_CORE_CURRENT_PRODUCTIVE_FRESH_RUNTIME_CYCLE_TO_EXACT_"
    "ENVELOPE_BOUND_SINGLE_USE_POST_BOUNDARY"
)
NEXT_BLOCKER = "OWNER_GO_REQUIRED_FOR_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT"
LATER_POST_GO = (
    "OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1"
)
PROTECTED_ALGORITHM_FILES = (
    "src/ops/governed_futures_universe_producer_v1/eligibility_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/policy_v1.py",
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
)


def _finalized_candles(count: int = 8) -> list[list[str]]:
    rows: list[list[str]] = []
    base = 1_700_000_000_000
    close = 100.0
    for index in range(count):
        ts = str(base + index * 60_000)
        close_px = f"{close + index * 0.01:.4f}"
        rows.append([ts, close_px, close_px, close_px, close_px, "10", "100", "USDT", "1"])
    return rows


def _market_payloads(*, instrument_id: str = _EXPECTED_SELECTED) -> dict[str, object]:
    return {
        ENDPOINT_MARKET_TICKER: {
            "code": "0",
            "data": [
                {
                    "instId": instrument_id,
                    "bidPx": "100.4",
                    "askPx": "100.6",
                    "vol24h": "12345",
                    "idxPx": "100.45",
                }
            ],
        },
        ENDPOINT_MARKET_CANDLES: {"code": "0", "data": _finalized_candles()},
        ENDPOINT_PUBLIC_OPEN_INTEREST: {
            "code": "0",
            "data": [{"instId": instrument_id, "oi": "1000"}],
        },
        ENDPOINT_PUBLIC_FUNDING_RATE: {
            "code": "0",
            "data": [{"instId": instrument_id, "fundingRate": "0.0001"}],
        },
    }


def _fresh_get_transport(*, include_market: bool = True):
    payloads = dict(_identity_payloads())
    if include_market:
        payloads.update(_market_payloads())
    return InjectedPayloadsFreshGetTransportV1(payloads=payloads)


def _run(tmp_path: Path, **overrides):
    payload = {
        "owner_go": OWNER_GO,
        "origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
        "evidence_root": tmp_path / "store",
        "acquisition_transport": _eligible_transport(),
        "fresh_get_transport": _fresh_get_transport(),
        "execute_network": False,
        "producer_observed_at_unix": 1_700_000_100.0,
        "replay": None,
    }
    payload.update(overrides)
    return execute_current_productive_fresh_runtime_cycle_to_exact_envelope_bound_v1(**payload)


def test_standing_flags_keep_real_post_fail_closed() -> None:
    assert (
        CURRENT_PRODUCTIVE_FRESH_RUNTIME_CYCLE_TO_EXACT_ENVELOPE_BOUND_SINGLE_USE_POST_BOUNDARY_CREATED
        is True
    )
    assert ONE_SHOT_REAL_POST_TRANSPORT_IMPLEMENTED is True
    assert ONE_SHOT_REAL_POST_REQUIRES_EXACT_ENVELOPE_BOUND_PERMIT is True
    assert ONE_SHOT_REAL_POST_STANDING_EXTERNAL_EFFECT_FORBIDDEN is True
    assert ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM is True
    assert FULL_CORE_ACTUAL_HTTP_POST_SEAM_IMPLEMENTED is True
    assert int(MAX_EXTERNAL_EFFECT_POST_COUNT) == 1
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert SUBMISSION_AUTHORIZED is True
    assert LIVE_AUTHORIZED is True
    assert PRODUCTIVE_WIRE_SEND_REACHABLE is True
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert POST_ALLOWED is False
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert EXPECTED_ORIGIN_MAIN_SHA == "be9d79e95725e92e96dfdc84bf4afd3886185f24"
    assert current_productive_first_real_blocker_v1() == NEXT_BLOCKER
    assert LATER_POST_GO in ONE_SHOT_REAL_POST_AUTHORITY_REFS
    assert OWNER_GO not in ONE_SHOT_REAL_POST_AUTHORITY_REFS


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
        authority_ref=LATER_POST_GO,
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
    assert transport.venue_live_contact is False


def test_owner_go_and_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(CurrentProductiveFreshRuntimeCycleError, match="OWNER_GO_MISMATCH"):
        _run(tmp_path / "a", owner_go="WRONG")
    with pytest.raises(
        CurrentProductiveFreshRuntimeCycleError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        _run(tmp_path / "b", origin_main_sha="0" * 40)


def test_finalized_candles_keep_observed_order() -> None:
    closes, last_ts = extract_finalized_candle_closes_v1(
        {"code": "0", "data": _finalized_candles(3)}
    )
    assert len(closes) == 3
    assert last_ts is not None
    assert closes[0] < closes[-1]


def test_injected_path_runs_cycle_without_fabricating_enter(tmp_path: Path) -> None:
    result = _run(tmp_path)
    claims = json.loads((Path(result.store_root) / "claims.json").read_text(encoding="utf-8"))
    assert result.cap23_selected_instrument_id == _EXPECTED_SELECTED
    assert result.cap23_selected_instrument_id != CANARY_DEFAULT_INSTRUMENT_ID
    assert result.cap23_selected_instrument_id != DEFAULT_INSTRUMENT_ID
    assert result.cap24_bound_instrument_id
    assert result.master_v2_runtime_cycle_id
    assert CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT not in result.master_v2_runtime_cycle_id
    assert claims["MASTER_V2_RUNTIME_CYCLE_PROVENANCE"] == CYCLE_OWNER
    assert result.permit_created == "false"
    assert result.real_external_effect_authorized == "false"
    assert result.post_count == "0"
    assert result.decision_result == "NO_EXECUTABLE_DECISION"
    assert result.decision_execution_eligible == "false"
    assert result.envelope_readiness == "false"
    assert result.final_envelope_id == ""
    assert claims["POST_COUNT"] == "0"
    assert claims["TRANSPORT_ATTEMPTED"] == "false"
    assert claims["VENUE_MUTATION_PERFORMED"] == "false"
    assert claims["PERMIT_CREATED"] == "false"
    assert claims["PERMIT_CONSUMED_DURABLY"] == "false"
    assert claims["STEP_29Q_STATUS"] == STEP_29Q_PLAN_ONLY
    assert claims["EXTERNAL_EFFECT_AUTHORIZED"] == "false"
    assert claims["CANARY_INSTRUMENT_AUTHORITY_IMPORTED"] == "false"
    assert claims["FRESH_PRE_SUBMIT_EVIDENCE"] == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    assert claims["PROTECTED_SURFACES_CHANGED"] == "false"
    assert result.first_real_blocker != CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT
    assert verify_manifest_sha256_v1(store_root=Path(result.store_root)) == 0


def test_foreign_open_position_denies_without_second_instrument_cycle(tmp_path: Path) -> None:
    payloads = dict(_identity_payloads())
    payloads.update(_market_payloads())
    payloads[ENDPOINT_ACCOUNT_POSITIONS] = {
        "code": "0",
        "data": [{"instId": "BTC-USDT-SWAP", "pos": "1", "posSide": "long"}],
    }
    result = _run(
        tmp_path,
        fresh_get_transport=InjectedPayloadsFreshGetTransportV1(payloads=payloads),
    )
    assert result.first_real_blocker == "FOREIGN_OPEN_POSITION_MAX_POSITIONS_1"
    assert result.master_v2_runtime_cycle_id == ""
    assert result.decision_result == "NO_EXECUTABLE_DECISION"
    assert result.decision_provenance == "FOREIGN_OPEN_POSITION_MAX_POSITIONS_1"
    assert result.permit_created == "false"
    assert result.post_count == "0"
    assert result.envelope_readiness == "false"


def test_missing_market_get_is_truthful_incomplete(tmp_path: Path) -> None:
    result = _run(tmp_path, fresh_get_transport=_fresh_get_transport(include_market=False))
    claims = json.loads((Path(result.store_root) / "claims.json").read_text(encoding="utf-8"))
    assert result.decision_result == "NO_EXECUTABLE_DECISION"
    assert result.permit_created == "false"
    assert result.post_count == "0"
    assert "MASTER_V2_REQUIRED_GET_INCOMPLETE" in result.first_real_blocker
    assert claims["MASTER_V2_RUNTIME_CYCLE_ID"] == ""
    assert result.envelope_readiness == "false"


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
    assert DK_HEADING in runbook
    assert THIS_SLICE in runbook
    dk_section = runbook[
        runbook.index(
            "11.2.1.DK FULL_CORE_CURRENT_PRODUCTIVE_FRESH_RUNTIME_CYCLE_TO_EXACT_"
            "ENVELOPE_BOUND_SINGLE_USE_POST_BOUNDARY"
        ) : runbook.index("## 11.3 Autonomy state model")
    ]
    assert "ONE_SHOT_REAL_POST_SEAM_IMPLEMENTED=true" in dk_section
    assert "EXTERNAL_EFFECT_AUTHORIZED=false" in dk_section
    assert "REAL_EXTERNAL_EFFECT_AUTHORIZED=false" in dk_section
    assert "STEP_29Q_STATUS=PLAN_ONLY" in dk_section
    assert "POST_COUNT=0" in dk_section
    assert "PERMIT_CREATED=false" in dk_section
    assert SPEC_PATH.name in mot
    assert (
        "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_FRESH_RUNTIME_CYCLE_TO_EXACT_"
        "ENVELOPE_BOUND_SINGLE_USE_POST_BOUNDARY_V1"
    ) in spec
    assert "11.2.1.DK" in atlas
    assert (
        "current_productive_fresh_runtime_cycle_to_exact_envelope_bound_single_use_"
        "post_boundary_v1.py" in atlas
    )
    pack = REPO_ROOT / CANONICAL_PACK_RELPATH
    claims = json.loads((pack / "claims.json").read_text(encoding="utf-8"))
    assert claims["ONE_SHOT_REAL_POST_SEAM_IMPLEMENTED"] == "true"
    assert claims["EXTERNAL_EFFECT_AUTHORIZED"] == "false"
    assert claims["REAL_EXTERNAL_EFFECT_AUTHORIZED"] == "false"
    assert claims["POST_COUNT"] == "0"
    assert claims["STEP_29Q_STATUS"] == "PLAN_ONLY"
    assert claims["PERMIT_CREATED"] == "false"
    assert claims["PERMIT_CONSUMED_DURABLY"] == "false"
    assert claims["CANARY_INSTRUMENT_AUTHORITY_IMPORTED"] == "false"
    assert claims["CAP23_SELECTED_INSTRUMENT_ID"] != CANARY_DEFAULT_INSTRUMENT_ID
    assert claims["CAP23_SELECTED_INSTRUMENT_ID"] != DEFAULT_INSTRUMENT_ID
    assert claims["TRANSPORT_ATTEMPTED"] == "false"
    assert claims["VENUE_MUTATION_PERFORMED"] == "false"
    assert verify_manifest_sha256_v1(store_root=pack) == 0
