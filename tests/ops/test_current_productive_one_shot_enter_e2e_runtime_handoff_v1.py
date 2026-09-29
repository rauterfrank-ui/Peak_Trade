"""One-shot Enter E2E runtime handoff prepare tests (no POST)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1 import (
    K1_OPAQUE_SIGNING_OWNER_GO,
    POST_OWNER_GO,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
    OWNER_GO as PRE_EXTERNAL_OWNER_GO,
    CurrentProductiveFullCorePreExternalClosureResultV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_one_shot_enter_e2e_runtime_handoff_v1 import (
    HANDOFF_FILENAME,
    OWNER_GO,
    CurrentProductiveOneShotEnterE2ERuntimeHandoffError,
    prepare_current_productive_one_shot_enter_e2e_runtime_handoff_v1,
)
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_candles_payload_from_enter_closes_v1,
    prepare_layered_long_armed_seed_for_pre_external_invoke_v1,
)
from tests.ops._pre_external_cap21_inst_type_test_helpers_v1 import (
    write_cap21_productivity_root_for_inst_v1,
)
from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
    _TEST_INST,
    _bound,
    _origin_main_sha,
    _productive_transport,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_ONE_SHOT_ENTER_E2E_RUNTIME_HANDOFF_V1.md"
)


def _sample_envelope():
    plan = VenuePlanCandidateV1(
        instrument_id="cap24-ADA-USDT-SWAP",
        side="buy",
        quantity="1",
        order_type="market",
        td_mode="cross",
        reduce_only=False,
        clordid="pt-e2e-handoff-fixture",
        venue_native_payload={
            "instId": "ADA-USDT-SWAP",
            "ordType": "market",
            "side": "buy",
            "sz": "1",
            "tdMode": "cross",
        },
        quantity_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        side_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        instrument_source="DH_CAP24_BOUND_INSTRUMENT_ID",
        path_kind="FULL_CORE_CURRENT_PRODUCTIVE",
    )
    return bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref="adm-e2e-handoff",
        provenance_ref="prov-e2e-handoff",
        creation_epoch="2026-09-27T12:00:00Z",
    )


def _executable_closure(
    *, store_root: str, envelope
) -> CurrentProductiveFullCorePreExternalClosureResultV1:
    return CurrentProductiveFullCorePreExternalClosureResultV1(
        store_root=store_root,
        base_sha=_origin_main_sha(),
        head_sha=_origin_main_sha(),
        branch="main",
        wp1_status="PASS",
        wp2_status="PASS",
        common_epoch_status="PASS",
        common_epoch_id="epoch-e2e-handoff",
        u01_status="PASS",
        p01_status="DOES_NOT_APPLY",
        live_account_bound_status="PASS",
        equity_producer_status="MINTED",
        bound_value_29p_status="BOUND",
        admissibility_29p_status="true",
        instrument_metadata_status="TRUSTED_CURRENT",
        reference_price_status="GOVERNED_MV2_MARK",
        mv2_capital_context_rebind_status="PASS",
        portfolio_reservation_status="PASS",
        venue_plan_status="PASS",
        final_order_envelope_status="PASS",
        terminal_disposition=DISPOSITION_PRE_EXTERNAL_EFFECT,
        gets_actually_performed=1,
        private_get_auth_path="test",
        runtime_owner_gos_consumed=(),
        synthetic_contamination=False,
        fixture_contamination=False,
        manual_injection_contamination=False,
        post_count=0,
        permit_created=False,
        external_effect_occurred=False,
        blockers_closed=("E2E-B06",),
        earliest_remaining_blocker=(
            "OWNER_GO_REQUIRED_FOR_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT"
        ),
        manifest_verify_rc=0,
        current_productive_decision_result="EXECUTABLE_VENUE_PLAN_BOUND",
        decision_execution_eligible="true",
        envelope_readiness="true",
        pre_external_effect_boundary_reached="true",
        capital_context_bound="true",
        fresh_executable_enter_final_order_envelope=envelope,
    )


def test_spec_present() -> None:
    assert SPEC_PATH.is_file()
    assert OWNER_GO.startswith("OWNER_GO_")


def test_fail_closed_when_cap24_runtime_missing(tmp_path: Path) -> None:
    origin_sha = _origin_main_sha()
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=origin_sha,
        head=origin_sha,
    )
    with pytest.raises(CurrentProductiveOneShotEnterE2ERuntimeHandoffError) as exc:
        prepare_current_productive_one_shot_enter_e2e_runtime_handoff_v1(
            owner_go=OWNER_GO,
            pre_external_owner_go=PRE_EXTERNAL_OWNER_GO,
            post_owner_go=POST_OWNER_GO,
            k1_owner_go=K1_OPAQUE_SIGNING_OWNER_GO,
            productivity_root=tmp_path / "missing_cap24",
            lane_state_root=tmp_path / "lane",
            post_durable_store_root=tmp_path / "post",
            origin_main_sha=origin_sha,
            execution_integrity_backend=integrity,
        )
    assert "CAP24_RUNTIME_STATE_ROOT_MISSING" in str(exc.value)


def test_prepare_handoff_from_pre_external_closure_without_post(tmp_path: Path) -> None:
    origin_sha = _origin_main_sha()
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=origin_sha,
        head=origin_sha,
    )
    bound = _bound()
    envelope = _sample_envelope()
    closure_store = tmp_path / "closure"
    closure_store.mkdir()
    (closure_store / "FINAL_ORDER_ENVELOPE.json").write_text(
        json.dumps(envelope.to_runtime_json_v1(), sort_keys=True),
        encoding="utf-8",
    )
    closure = _executable_closure(store_root=str(closure_store), envelope=envelope)
    lanes_root = tmp_path / "lanes"
    lanes_root.mkdir()
    post_store = tmp_path / "post_durable"
    cap24_root = write_cap21_productivity_root_for_inst_v1(tmp_path, venue_native_id=_TEST_INST)

    with patch(
        "src.ops.governed_productive_account_equity_authority_producer_v1."
        "current_productive_one_shot_enter_e2e_runtime_handoff_v1."
        "execute_current_productive_full_core_pre_external_closure_v1",
        return_value=closure,
    ):
        result = prepare_current_productive_one_shot_enter_e2e_runtime_handoff_v1(
            owner_go=OWNER_GO,
            pre_external_owner_go=PRE_EXTERNAL_OWNER_GO,
            post_owner_go=POST_OWNER_GO,
            k1_owner_go=K1_OPAQUE_SIGNING_OWNER_GO,
            productivity_root=cap24_root,
            lane_state_root=lanes_root,
            post_durable_store_root=post_store,
            origin_main_sha=origin_sha,
            bound_instrument_override=bound,
            evidence_root=tmp_path / "handoff_evidence",
            execution_integrity_backend=integrity,
            prove_k1_pre_live=False,
        )
    assert result.terminal_disposition == DISPOSITION_PRE_EXTERNAL_EFFECT
    assert result.e2e_runtime_ready == "true"
    assert Path(result.envelope_json_path).is_file()
    handoff_path = Path(result.handoff_store_root) / HANDOFF_FILENAME
    payload = json.loads(handoff_path.read_text(encoding="utf-8"))
    assert payload["REAL_VENUE_POST_PERFORMED"] == "false"
    assert "--confirm-real-venue-post" in result.final_operator_command
    assert result.manifest_verify_rc == 0


def _run_layered_enter_e2e_handoff_once_v1(*, tmp_path: Path, cycle_id_prefix: str) -> None:
    """Full compose: WP-2 layered ENTER closure → one-shot handoff prepare (no POST)."""
    origin_sha = _origin_main_sha()
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=origin_sha,
        head=origin_sha,
    )
    bound = _bound()
    lanes_root = tmp_path / "lanes"
    _arm, enter_closes, mark_px, event_ts, g17 = (
        prepare_layered_long_armed_seed_for_pre_external_invoke_v1(
            bound=bound,
            g17_typed_vol_producer=object(),
            lane_state_root=lanes_root,
        )
    )
    del _arm
    candles = governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=enter_closes,
        last_event_ts_unix=event_ts,
    )
    cap24_root = write_cap21_productivity_root_for_inst_v1(tmp_path, venue_native_id=_TEST_INST)
    post_store = tmp_path / "post_durable"
    result = prepare_current_productive_one_shot_enter_e2e_runtime_handoff_v1(
        owner_go=OWNER_GO,
        pre_external_owner_go=PRE_EXTERNAL_OWNER_GO,
        post_owner_go=POST_OWNER_GO,
        k1_owner_go=K1_OPAQUE_SIGNING_OWNER_GO,
        productivity_root=cap24_root,
        lane_state_root=lanes_root,
        post_durable_store_root=post_store,
        origin_main_sha=origin_sha,
        bound_instrument_override=bound,
        execution_integrity_backend=integrity,
        fresh_get_transport=_productive_transport(),
        candles_payload=candles,
        market_kwargs={
            "cycle_id_prefix": cycle_id_prefix,
            "mark_px": mark_px,
            "index_px": mark_px,
            "bid_px": mark_px - 0.5,
            "ask_px": mark_px + 0.5,
            "finalized_closes": enter_closes,
            "last_finalized_event_ts_unix": event_ts,
            "observed_unix": event_ts + 100.0,
            "venue_flat": True,
            "existing_position_side": ExistingPositionSide.NONE,
            "volume": 10.0,
            "open_interest": 20.0,
            "funding_rate": 0.0001,
        },
        g17_typed_vol_producers={"LANE_1": g17},
        evidence_root=tmp_path / "handoff_evidence",
        prove_k1_pre_live=False,
    )
    assert result.terminal_disposition == DISPOSITION_PRE_EXTERNAL_EFFECT
    assert result.e2e_runtime_ready == "true"
    assert Path(result.envelope_json_path).is_file()
    handoff_path = Path(result.handoff_store_root) / HANDOFF_FILENAME
    payload = json.loads(handoff_path.read_text(encoding="utf-8"))
    assert payload["REAL_VENUE_POST_PERFORMED"] == "false"
    assert result.manifest_verify_rc == 0


def test_layered_enter_e2e_handoff_full_compose_without_closure_mock_v1(
    tmp_path: Path,
) -> None:
    """PRE_EXTERNAL closure executor composed into handoff prepare (transport-bound; no POST)."""
    _run_layered_enter_e2e_handoff_once_v1(
        tmp_path=tmp_path,
        cycle_id_prefix="e2e-handoff-compose-single",
    )


def test_layered_enter_e2e_handoff_first_same_process_batch_v1(tmp_path: Path) -> None:
    """Same-process batch step A (ops conftest PRE_EXTERNAL isolation before test)."""
    _run_layered_enter_e2e_handoff_once_v1(
        tmp_path=tmp_path,
        cycle_id_prefix="e2e-handoff-batch-a",
    )


def test_layered_enter_e2e_handoff_second_same_process_batch_v1(tmp_path: Path) -> None:
    """Same-process batch step B after step A (conftest isolation between tests)."""
    _run_layered_enter_e2e_handoff_once_v1(
        tmp_path=tmp_path,
        cycle_id_prefix="e2e-handoff-batch-b",
    )
