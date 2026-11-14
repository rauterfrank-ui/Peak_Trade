"""One-shot Enter E2E runtime handoff prepare tests (no POST)."""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from shlex import split
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
from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
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
POST_CLI = (
    REPO_ROOT
    / "scripts/ops/run_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1.py"
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


@pytest.mark.parametrize("extra_flags", [[], ["--pre-live-only"]])
def test_legacy_submit_flag_stops_before_envelope_or_k1(
    tmp_path: Path, monkeypatch, capsys, extra_flags
) -> None:
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1 as k1,
    )

    def unexpected_backend(**_kwargs):
        pytest.fail("The legacy submit mode must stop before resolving K1")

    monkeypatch.setattr(
        k1, "resolve_macos_security_framework_k1_lookup_backend_v1", unexpected_backend
    )
    store = tmp_path / "send"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(POST_CLI),
            "--store-root",
            str(store),
            "--envelope-json",
            str(tmp_path / "missing.json"),
            "--k1-backend",
            "macos",
            "--confirm-real-venue-post",
            *extra_flags,
        ],
    )
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(POST_CLI), run_name="__main__")
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert captured.err.strip() == "FAIL_CLOSED:POST_PENDING_CONTEXT_REQUIRED:OPERATOR_CLI"
    assert not captured.out
    assert not store.exists()


def test_fail_closed_when_cap24_runtime_missing(tmp_path: Path) -> None:
    from tests.ops.test_single_selected_future_runtime_binding_v1 import _empty_portfolio

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
            observed_portfolio=_empty_portfolio(),
            lane_state_root=tmp_path / "lane",
            post_durable_store_root=tmp_path / "post",
            origin_main_sha=origin_sha,
            execution_integrity_backend=integrity,
        )
    assert "CAP24_RUNTIME_STATE_ROOT_MISSING" in str(exc.value)


def test_prepare_handoff_from_pre_external_closure_without_post(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    origin_sha = _origin_main_sha()
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=origin_sha,
        head=origin_sha,
    )
    bound = _bound()
    envelope = _sample_envelope()
    closure_store = tmp_path / "closure with spaces"
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
    assert result.e2e_runtime_ready == "false"
    assert Path(result.envelope_json_path).is_file()
    handoff_path = Path(result.handoff_store_root) / HANDOFF_FILENAME
    payload = json.loads(handoff_path.read_text(encoding="utf-8"))
    assert payload["REAL_VENUE_POST_PERFORMED"] == "false"
    assert payload["E2E_RUNTIME_READY"] == "false"
    assert payload["POST_HANDOFF_BLOCKER"] == result.post_handoff_blocker
    assert result.post_handoff_blocker == "POST_PENDING_CONTEXT_REQUIRED:OPERATOR_CLI"
    assert payload["FINAL_OPERATOR_COMMAND"] == result.final_operator_command == ""
    pre_live_args = split(result.final_pre_live_command)[2:]
    assert pre_live_args == [
        "--store-root",
        str(post_store),
        "--envelope-json",
        result.envelope_json_path,
        "--k1-backend",
        "macos",
        "--pre-live-only",
    ]
    assert result.manifest_verify_rc == 0
    from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
        MacosSecurityFrameworkLookupBackendV1,
    )

    def unexpected_lookup(*_args, **_kwargs):
        pytest.fail("The pre-live CLI checklist must not read the Keychain")

    monkeypatch.setattr(
        MacosSecurityFrameworkLookupBackendV1,
        "copy_matching_generic_password_value_data_v1",
        unexpected_lookup,
    )
    monkeypatch.setattr(sys, "argv", [str(POST_CLI), *pre_live_args])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(POST_CLI), run_name="__main__")
    assert exc.value.code == 0
    proof = json.loads(capsys.readouterr().out)
    assert proof["PRE_LIVE_PROOF_COMPLETE"] == "true"
    assert proof["POST_ADMISSION_GRANTED"] == "false"
    assert not list(post_store.iterdir())


def _run_layered_enter_e2e_handoff_once_v1(
    *, tmp_path: Path, cycle_id_prefix: str, provide_budget_owner: bool = True
) -> None:
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
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1,
    )

    # Explicit temporary test owner. The prepare path must forward this same
    # owner and must not construct a replacement when none was supplied.
    budget_owner = PortfolioCapitalReservationBudgetOwnerV1() if provide_budget_owner else None
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
        portfolio_budget_owner=budget_owner,
        evidence_root=tmp_path / "handoff_evidence",
        prove_k1_pre_live=False,
    )
    assert result.terminal_disposition == DISPOSITION_PRE_EXTERNAL_EFFECT
    assert result.e2e_runtime_ready == "false"
    assert Path(result.envelope_json_path).is_file()
    handoff_path = Path(result.handoff_store_root) / HANDOFF_FILENAME
    payload = json.loads(handoff_path.read_text(encoding="utf-8"))
    assert payload["REAL_VENUE_POST_PERFORMED"] == "false"
    assert result.manifest_verify_rc == 0
    assert budget_owner.active_sum_v1() > 0
    assert budget_owner.active_sum_v1() <= 25
    budget_owner.close()


def test_natural_enter_without_shared_owner_reports_capital_blocker(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveOneShotEnterE2ERuntimeHandoffError,
        match="ENTRY_BUDGET_REQUIRES_SHARED_RESERVATION_OWNER",
    ):
        _run_layered_enter_e2e_handoff_once_v1(
            tmp_path=tmp_path,
            cycle_id_prefix="e2e-missing-budget-owner",
            provide_budget_owner=False,
        )


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
