"""Shared offline full-system E2E proof fixtures (no productive network)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_owner_go_durable_consume_v1 import (
    persist_durable_post_owner_go_consume_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    POST_OWNER_GO,
)
from src.ops.full_core_live_path_composition_root_v1.current_full_system_offline_e2e_integration_proof_v1 import (
    OFFLINE_E2E_FAKE_EXCHANGE_ORD_ID_V1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_fresh_executable_enter_final_order_envelope_runtime_reach_to_one_shot_post_join_boundary_v1 import (
    resolve_fresh_executable_enter_final_order_envelope_from_pre_external_closure_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_gap_true_01_executable_envelope_pre_external_evidence_v1 import (
    OWNER_GO as GAP_TRUE_01_OWNER_GO,
    CurrentProductiveGapTrue01EvidenceResultV1,
    execute_current_productive_gap_true_01_executable_envelope_pre_external_evidence_v1,
)
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_candles_payload_from_enter_closes_v1,
    prepare_layered_long_armed_seed_for_pre_external_invoke_v1,
)
from tests.ops._pilot_guard_enter_post_test_helpers_v1 import (
    PILOT_TEST_ACCOUNT_UID,
    PilotGuardReadTransport,
)
from tests.ops._pre_external_cap21_inst_type_test_helpers_v1 import (
    write_cap21_productivity_root_for_inst_v1,
)
from tests.ops.test_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    _FakeKeychainBackend,
)
from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
    _TEST_INST,
    _bound,
    _origin_main_sha,
    _productive_transport,
)
from tests.ops.test_full_core_exchange_reconciliation_v1 import _order_row
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide


def run_gap_true_01_natural_enter_pre_external_v1(
    tmp_path: Path,
) -> tuple[Any, CurrentProductiveGapTrue01EvidenceResultV1, str, Any, float]:
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
    result = execute_current_productive_gap_true_01_executable_envelope_pre_external_evidence_v1(
        owner_go=GAP_TRUE_01_OWNER_GO,
        origin_main_sha=origin_sha,
        bound_instrument=bound,
        fresh_get_transport=_productive_transport(),
        lane_state_root=lanes_root,
        cap24_productivity_root=cap24_root,
        candles_payload=candles,
        market_kwargs={
            "cycle_id_prefix": "full-system-offline-e2e-v1",
            "mark_px": mark_px,
            "index_px": mark_px,
            "bid_px": mark_px - 0.5,
            "ask_px": mark_px + 0.5,
            "finalized_closes": enter_closes,
            "last_finalized_event_ts_unix": event_ts,
            "observed_unix": event_ts + 100.0,
            "venue_flat": True,
            "volume": 10.0,
            "open_interest": 20.0,
            "funding_rate": 0.0001,
            "existing_position_side": ExistingPositionSide.NONE,
        },
        g17_typed_vol_producers={"LANE_1": g17},
        evidence_root=tmp_path / "gap_true_01_evidence",
        execution_integrity_backend=integrity,
    )
    assert result.gap_true_01_verdict == "CLOSED"
    return bound, result, origin_sha, _productive_transport(), float(mark_px)


def prepare_offline_owner_authorization_for_one_shot_v1(
    *,
    state_root: Path,
    closure: Any,
    origin_main_sha: str,
    bound: Any,
) -> Any:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_mandatory_new_risk_enter_post_admission_v1 import (
        persist_enter_post_lifecycle_correlation_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_pilot_capital_guard_post_bind_v1 import (
        OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1,
        enforce_pilot_capital_guard_before_enter_post_v1,
    )
    from tests.ops._pilot_guard_enter_post_test_helpers_v1 import (
        ratified_pilot_guard_config_for_tests,
    )

    envelope = resolve_fresh_executable_enter_final_order_envelope_from_pre_external_closure_v1(
        closure
    )
    one_shot_root = state_root / "one_shot_durable"
    one_shot_root.mkdir(parents=True, exist_ok=True)
    persist_durable_post_owner_go_consume_v1(
        store_root=one_shot_root,
        owner_go_token=POST_OWNER_GO,
        baseline_origin_main_sha=origin_main_sha,
    )
    pretrade_id = str(closure.common_epoch_id or "offline-e2e")
    native_id = str(bound.venue_native_id or _TEST_INST)
    atomic = state_root / "atomic" / "pilot_guard"
    pilot_bind = enforce_pilot_capital_guard_before_enter_post_v1(
        pilot_capital_guard_bind_go=OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1,
        envelope=envelope,
        read_only_get_transport=_InstrumentAwarePilotReadTransport(
            native_inst_id=native_id,
            avail_eq="10000",
        ),
        pretrade_decision_id=pretrade_id,
        native_instrument_id=native_id,
        canonical_decision_id=pretrade_id,
        account_identity=PILOT_TEST_ACCOUNT_UID,
        origin_main_sha=origin_main_sha,
        guard_config=ratified_pilot_guard_config_for_tests(),
        atomic_state_dir=atomic,
    )
    if pilot_bind.blocked:
        raise RuntimeError(f"PILOT_GUARD_BLOCKED:{','.join(pilot_bind.reasons)}")
    persist_enter_post_lifecycle_correlation_v1(
        store_root=one_shot_root,
        envelope=envelope,
        authorization_binding=pilot_bind.authorization_binding,
        pretrade_decision_id=pretrade_id,
        submit_attempt_id=f"enter-post:{envelope.client_order_id}",
        atomic_state_dir=atomic,
    )
    return pilot_bind.authorization_binding


def offline_recon_fixture_for_envelope_v1(
    closure: Any,
) -> OfflineExchangeFixtureV1:
    envelope = resolve_fresh_executable_enter_final_order_envelope_from_pre_external_closure_v1(
        closure
    )
    cl = str(envelope.client_order_id or "cl-offline-e2e")
    inst = str(envelope.instrument_id or _TEST_INST)
    qty = str(envelope.quantity or "1")
    row = _order_row(state="live", sz=qty, acc="0")
    row["clOrdId"] = cl
    row["instId"] = inst
    row["ordId"] = OFFLINE_E2E_FAKE_EXCHANGE_ORD_ID_V1
    return OfflineExchangeFixtureV1(pending_orders={"data": [row]})


def fake_k1_backend_v1() -> _FakeKeychainBackend:
    return _FakeKeychainBackend()


class _InstrumentAwarePilotReadTransport(PilotGuardReadTransport):
    def __init__(self, *, native_inst_id: str, avail_eq: str = "10000") -> None:
        import json

        from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cover_usdc_current_public_tier_mmr_productive_evidence_v1 import (
            encode_fixture_position_tiers_payload_v1,
        )

        self._avail_eq = avail_eq
        self._open_orders = False
        self._balance_ccy = "USDC"
        self._inst_family = str(native_inst_id).split("-")[0] + "-USDT"
        tiers_raw = encode_fixture_position_tiers_payload_v1(
            inst_family=self._inst_family,
            qty_one_imr="0.05",
            qty_one_mmr="0.004",
            qty_one_tier="1",
            qty_one_min_sz="0",
            qty_one_max_sz="100",
        )
        self._tiers_payload = json.loads(tiers_raw.decode("utf-8"))
        self._native_inst_id = native_inst_id

    def get(self, *, endpoint: str, auth_required: bool, pretrade_decision_id: str):
        from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
            FreshPretradeGetTransportResultV1,
            TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
        )

        path = str(endpoint).split("?", 1)[0]
        if "leverage-info" in path:
            from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
                FreshPretradeGetTransportResultV1,
                TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
            )

            payload = {
                "code": "0",
                "data": [{"instId": self._native_inst_id, "lever": "5"}],
            }
            return FreshPretradeGetTransportResultV1(
                get_performed=True,
                method="GET",
                endpoint=endpoint,
                http_status=200,
                payload=payload,
                auth_header_sent=True,
                transport_class=TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
                venue_live_contact=True,
                historical_reuse=False,
                error_class="",
                data_safety_source_kind="REAL",
            )
        if "position-tiers" in path:
            from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
                FreshPretradeGetTransportResultV1,
                TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
            )

            return FreshPretradeGetTransportResultV1(
                get_performed=True,
                method="GET",
                endpoint=endpoint,
                http_status=200,
                payload=self._tiers_payload,
                auth_header_sent=True,
                transport_class=TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
                venue_live_contact=True,
                historical_reuse=False,
                error_class="",
                data_safety_source_kind="REAL",
            )
        if "instruments" in path:
            payload = {
                "code": "0",
                "data": [
                    {
                        "instId": self._native_inst_id,
                        "instType": "SWAP",
                        "instFamily": self._inst_family,
                        "state": "live",
                        "ctVal": "1",
                        "minSz": "1",
                        "lotSz": "1",
                    }
                ],
            }
            return FreshPretradeGetTransportResultV1(
                get_performed=True,
                method="GET",
                endpoint=endpoint,
                http_status=200,
                payload=payload,
                auth_header_sent=True,
                transport_class=TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
                venue_live_contact=True,
                historical_reuse=False,
                error_class="",
                data_safety_source_kind="REAL",
            )
        return super().get(
            endpoint=endpoint,
            auth_required=auth_required,
            pretrade_decision_id=pretrade_decision_id,
        )


def pilot_get_transport_v1(*, native_inst_id: str = _TEST_INST) -> PilotGuardReadTransport:
    return _InstrumentAwarePilotReadTransport(native_inst_id=native_inst_id)
