"""Shared offline doubles for mandatory NEW-RISK Enter POST tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.ops.full_core_live_path_composition_root_v1.current_full_core_capital_guard_v1 import (
    ratified_offline_full_core_guard_config_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_pilot_capital_guard_post_bind_v1 import (
    OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cover_usdc_current_public_tier_mmr_productive_evidence_v1 import (
    encode_fixture_position_tiers_payload_v1,
)

PILOT_TEST_INST = "0G-USDT-SWAP"
PILOT_TEST_INST_FAMILY = "0G-USDT"
PILOT_TEST_ACCOUNT_UID = "acct-pilot-bind-1"


class PilotGuardReadTransport:
    def __init__(
        self,
        *,
        avail_eq: str = "5000",
        open_orders: bool = False,
        balance_ccy: str = "USDC",
    ) -> None:
        self._avail_eq = avail_eq
        self._open_orders = open_orders
        self._balance_ccy = balance_ccy
        tiers_raw = encode_fixture_position_tiers_payload_v1(
            inst_family=PILOT_TEST_INST_FAMILY,
            qty_one_imr="0.05",
            qty_one_mmr="0.004",
            qty_one_tier="1",
            qty_one_min_sz="1",
            qty_one_max_sz="100",
        )
        self._tiers_payload = json.loads(tiers_raw.decode("utf-8"))

    def get(self, *, endpoint: str, auth_required: bool, pretrade_decision_id: str):
        del auth_required, pretrade_decision_id
        path = str(endpoint).split("?", 1)[0]
        from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
            FreshPretradeGetTransportResultV1,
            TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
        )

        if "balance" in path:
            payload = {
                "code": "0",
                "data": [
                    {
                        "details": [
                            {"ccy": self._balance_ccy, "availEq": self._avail_eq},
                        ]
                    }
                ],
            }
        elif "config" in path:
            payload = {"code": "0", "data": [{"uid": PILOT_TEST_ACCOUNT_UID}]}
        elif "leverage-info" in path:
            payload = {"code": "0", "data": [{"instId": PILOT_TEST_INST, "lever": "5"}]}
        elif "position-tiers" in path:
            payload = self._tiers_payload
        elif "orders-pending" in path:
            rows = (
                [{"instId": PILOT_TEST_INST, "clOrdId": "pending-1"}] if self._open_orders else []
            )
            payload = {"code": "0", "data": rows}
        elif "positions" in path:
            payload = {"code": "0", "data": []}
        elif "instruments" in path or "price-limit" in path:
            payload = {
                "code": "0",
                "data": [
                    {
                        "instId": PILOT_TEST_INST,
                        "instType": "SWAP",
                        "instFamily": PILOT_TEST_INST_FAMILY,
                        "state": "live",
                        "ctVal": "1",
                        "minSz": "1",
                        "lotSz": "1",
                    }
                ],
            }
        elif "max-size" in path:
            payload = {
                "code": "0",
                "data": [{"instId": PILOT_TEST_INST, "maxBuy": "100", "maxSell": "100"}],
            }
        elif "index-tickers" in path:
            inst = PILOT_TEST_INST if PILOT_TEST_INST in endpoint else "USDT-USDC"
            payload = {"code": "0", "data": [{"instId": inst, "idxPx": "10.0"}]}
        else:
            payload = {"code": "0", "data": [{"instId": PILOT_TEST_INST, "tdMode": "cross"}]}

        if "instruments" in path and "USDC-USDT-SWAP" in endpoint:
            payload = {
                "code": "0",
                "data": [
                    {
                        "instId": "USDC-USDT-SWAP",
                        "instType": "SWAP",
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


def ratified_pilot_guard_config_for_tests():
    return ratified_offline_full_core_guard_config_v1()


def mandatory_new_risk_execute_kwargs(tmp_path: Path) -> dict[str, Any]:
    return {
        "pilot_capital_guard_bind_go": OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1,
        "pilot_capital_guard_config": ratified_pilot_guard_config_for_tests(),
        "pilot_native_instrument_id": PILOT_TEST_INST,
        "pilot_atomic_state_dir": tmp_path / "full_core_enter_post_guard_atomic_v1",
    }


def bind_authorized_exact_object_flatten_envelope_for_tests_v1(
    *,
    clordid: str = "pt-exact-flatten-one-shot-v1",
) -> Any:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_exact_object_flatten_plan_v1 import (
        INSTRUMENT_SOURCE as EXACT_OBJECT_FLATTEN_INSTRUMENT_SOURCE,
        PATH_KIND_EXACT_OBJECT_FLATTEN,
        QUANTITY_SOURCE as EXACT_OBJECT_FLATTEN_QUANTITY_SOURCE,
        SIDE_SOURCE as EXACT_OBJECT_FLATTEN_SIDE_SOURCE,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_risk_reducing_envelope_provenance_v1 import (
        EXACT_OBJECT_FLATTEN_ADMISSION_REF,
        EXACT_OBJECT_FLATTEN_PROVENANCE_REF,
    )
    from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
        bind_final_order_envelope_from_venue_plan_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1

    plan = VenuePlanCandidateV1(
        instrument_id="okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
        side="sell",
        quantity="1",
        order_type="limit",
        td_mode="cross",
        reduce_only=True,
        clordid=clordid,
        venue_native_payload={
            "instId": PILOT_TEST_INST,
            "ordType": "limit",
            "side": "sell",
            "sz": "1",
            "tdMode": "cross",
            "reduceOnly": True,
            "px": "10.0",
        },
        quantity_source=EXACT_OBJECT_FLATTEN_QUANTITY_SOURCE,
        side_source=EXACT_OBJECT_FLATTEN_SIDE_SOURCE,
        instrument_source=EXACT_OBJECT_FLATTEN_INSTRUMENT_SOURCE,
        path_kind=PATH_KIND_EXACT_OBJECT_FLATTEN,
    )
    return bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref=EXACT_OBJECT_FLATTEN_ADMISSION_REF,
        provenance_ref=EXACT_OBJECT_FLATTEN_PROVENANCE_REF,
        creation_epoch="2026-10-14T00:00:00Z",
    )


def establish_new_risk_one_shot_admission_seal_for_tests_v1(
    *,
    store_root: Path,
    envelope: Any,
    atomic_state_dir: Path | None = None,
    pretrade_decision_id: str = "one-shot-admission-seal-test",
) -> None:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_mandatory_new_risk_enter_post_admission_v1 import (
        persist_enter_post_lifecycle_correlation_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_pilot_capital_guard_post_bind_v1 import (
        enforce_pilot_capital_guard_before_enter_post_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
    )

    atomic = atomic_state_dir or (store_root / "full_core_enter_post_guard_atomic_v1")
    pilot_bind = enforce_pilot_capital_guard_before_enter_post_v1(
        pilot_capital_guard_bind_go=OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1,
        envelope=envelope,
        read_only_get_transport=PilotGuardReadTransport(avail_eq="10000"),
        pretrade_decision_id=pretrade_decision_id,
        native_instrument_id=PILOT_TEST_INST,
        canonical_decision_id=pretrade_decision_id,
        account_identity=PILOT_TEST_ACCOUNT_UID,
        origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        guard_config=ratified_pilot_guard_config_for_tests(),
        atomic_state_dir=atomic,
    )
    if pilot_bind.blocked:
        raise RuntimeError(f"PILOT_GUARD_BLOCKED:{','.join(pilot_bind.reasons)}")
    persist_enter_post_lifecycle_correlation_v1(
        store_root=store_root,
        envelope=envelope,
        authorization_binding=pilot_bind.authorization_binding,
        pretrade_decision_id=pretrade_decision_id,
        submit_attempt_id=f"enter-post:{envelope.client_order_id}",
        atomic_state_dir=atomic,
    )
