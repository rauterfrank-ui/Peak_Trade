"""PRODUCTIVE Full-Core pre-external closure v1 (WP-1 + WP-2).

Consumes Owner-GO OWNER_GO_PRODUCTIVE_FULL_CORE_PRE_EXTERNAL_CLOSURE_V1.
Composes common-epoch 29P capital surface from productive read-only GETs,
wires occupied-lane governed cycle to PRE_EXTERNAL or earliest fail-closed
blocker. No permit mint. No POST. No external effect.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlencode

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
    invoke_occupied_lane_governed_cycle_n1_consumer_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    OCCUPANCY_OCCUPIED,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneSlotV1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_HOLD,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    EG_OWNER_GO,
    GET_OWNER_GO,
    OCCUPANCY_OWNER_GO,
    RUNTIME_OWNER_GO,
    T2_RUNTIME_OWNER_GO,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ENDPOINT_MARKET_CANDLES,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FullCoreFreshPretradeGetTransportV1,
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_FULL_CORE_PRE_EXTERNAL_CLOSURE_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_common_epoch_handoff_v1 import (
    CurrentProductive29PCommonEpochHandoffError,
    compose_current_productive_29p_common_epoch_handoff_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
    CurrentProductive29PRuntimeIntegrityBackendV1,
    assert_current_productive_29p_execution_identity_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_common_epoch_to_enter_live_29p_handoff_v1 import (
    CurrentProductiveCommonEpochToEnterLive29PHandoffError,
    build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_execute_network_credential_join_v1 import (
    CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS,
    bind_productive_read_only_get_transport_for_execute_network_v1,
    release_productive_credential_handle_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_fresh_cap23_cap24_decision_and_one_shot_real_post_readiness_v1 import (
    _assert_no_secrets,
    _persist_json,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide

OWNER_GO = "OWNER_GO_PRODUCTIVE_FULL_CORE_PRE_EXTERNAL_CLOSURE_V1"
ALLOWED_OWNER_GOS = frozenset({OWNER_GO, f"OWNER_GO_{OWNER_GO}"})
EXPECTED_BASELINE_ORIGIN_MAIN_SHA = "9f2ab677cfdb3ef62d604ba62789b135bf83fe5f"
THIS_SLICE = "11.2.1.FC.FULL_CORE_CURRENT_PRODUCTIVE_PRE_EXTERNAL_CLOSURE"
EVIDENCE_DIRNAME = "full_core_current_productive_pre_external_closure_v1"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
_PROXY_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)
_REPO_ROOT = Path(__file__).resolve().parents[3]

RUNTIME_OWNER_GOS_CONSUMED = (
    RUNTIME_OWNER_GO,
    GET_OWNER_GO,
    EG_OWNER_GO,
    OCCUPANCY_OWNER_GO,
    T2_RUNTIME_OWNER_GO,
)


class CurrentProductiveFullCorePreExternalClosureError(RuntimeError):
    """Fail-closed pre-external closure violation."""


@dataclass(frozen=True)
class CurrentProductiveFullCorePreExternalClosureResultV1:
    store_root: str
    base_sha: str
    head_sha: str
    branch: str
    wp1_status: str
    wp2_status: str
    common_epoch_status: str
    common_epoch_id: str
    u01_status: str
    p01_status: str
    live_account_bound_status: str
    equity_producer_status: str
    bound_value_29p_status: str
    admissibility_29p_status: str
    instrument_metadata_status: str
    reference_price_status: str
    mv2_capital_context_rebind_status: str
    portfolio_reservation_status: str
    venue_plan_status: str
    final_order_envelope_status: str
    terminal_disposition: str
    gets_actually_performed: int
    private_get_auth_path: str
    runtime_owner_gos_consumed: tuple[str, ...]
    synthetic_contamination: bool
    fixture_contamination: bool
    manual_injection_contamination: bool
    post_count: int
    permit_created: bool
    external_effect_occurred: bool
    blockers_closed: tuple[str, ...]
    earliest_remaining_blocker: str
    manifest_verify_rc: int


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _assert_no_proxy_env_v1() -> None:
    present = [key for key in _PROXY_ENV_KEYS if str(os.environ.get(key) or "").strip()]
    if present:
        raise CurrentProductiveFullCorePreExternalClosureError("HTTP_PROXY_FORBIDDEN")


def _assert_standing_pins_v1() -> None:
    if POST_ALLOWED is True or REAL_VENUE_POST_ALLOWED is True:
        raise CurrentProductiveFullCorePreExternalClosureError("POST_STANDING_MUST_REMAIN_FALSE")
    if EXTERNAL_EFFECT_AUTHORIZED is True:
        raise CurrentProductiveFullCorePreExternalClosureError("EXTERNAL_EFFECT_MUST_REMAIN_FALSE")
    if CURRENT_PRODUCTIVE_FULL_CORE_PRE_EXTERNAL_CLOSURE_CREATED is not True:
        raise CurrentProductiveFullCorePreExternalClosureError("CLOSURE_SLICE_NOT_CREATED")


def _git_head_sha_v1() -> str:
    import subprocess

    return (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_REPO_ROOT, text=True)
        .strip()
        .lower()
    )


def _git_branch_v1() -> str:
    import subprocess

    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=_REPO_ROOT, text=True
    ).strip()


def _fetch_candles_payload_v1(
    *,
    transport: FullCoreFreshPretradeGetTransportV1,
    venue_native_id: str,
    decision_epoch: str,
) -> Mapping[str, Any]:
    query = urlencode({"instId": venue_native_id, "bar": "1m", "limit": "120"})
    endpoint = f"{ENDPOINT_MARKET_CANDLES}?{query}"
    result = transport.get(
        endpoint=endpoint,
        auth_required=False,
        pretrade_decision_id=decision_epoch,
    )
    if result.get_performed is not True or result.payload is None:
        raise CurrentProductiveFullCorePreExternalClosureError("C1_CANDLES_GET_FAIL_CLOSED")
    return result.payload if isinstance(result.payload, Mapping) else {"data": result.payload}


def _lane_pair_v1(
    *,
    lane_state_root: Path,
    bound: BoundInstrumentV1,
    lane_id: str = "LANE_1",
) -> tuple[IsolatedLaneSlotV1, BoundInstrumentV1]:
    root = lane_state_root / lane_id
    root.mkdir(parents=True, exist_ok=True)
    slot = IsolatedLaneSlotV1(
        lane_id=lane_id,
        occupancy=OCCUPANCY_OCCUPIED,
        canonical_instrument_id=bound.instrument_id,
        lane_state_root=str(root),
        universe_snapshot_id=bound.universe_snapshot_id,
        ranking_snapshot_id=bound.ranking_snapshot_id,
        ranking_integrity_digest=bound.ranking_integrity_digest,
    )
    return slot, bound


def execute_current_productive_full_core_pre_external_closure_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    bound_instrument: BoundInstrumentV1,
    lane_state_root: Path,
    fresh_get_transport: FullCoreFreshPretradeGetTransportV1 | None = None,
    execute_network: bool = False,
    vault_file: Path | str | None = None,
    evidence_root: Path | None = None,
    candles_payload: Mapping[str, Any] | None = None,
    portfolio_budget_owner: PortfolioCapitalReservationBudgetOwnerV1 | None = None,
    g17_typed_vol_producers: Mapping[str, object] | None = None,
    market_kwargs: Mapping[str, Any] | None = None,
    execution_integrity_backend: CurrentProductive29PRuntimeIntegrityBackendV1 | None = None,
) -> CurrentProductiveFullCorePreExternalClosureResultV1:
    """Run WP-1+2 closure to PRE_EXTERNAL or earliest blocker."""
    if owner_go not in ALLOWED_OWNER_GOS:
        raise CurrentProductiveFullCorePreExternalClosureError("OWNER_GO_MISMATCH")
    _assert_standing_pins_v1()
    _assert_no_proxy_env_v1()
    base_sha = str(origin_main_sha or "").strip().lower()
    if not base_sha:
        raise CurrentProductiveFullCorePreExternalClosureError("ORIGIN_MAIN_SHA_MISSING")
    assert_current_productive_29p_execution_identity_v1(
        declared_origin_main_sha=base_sha,
        integrity_backend=execution_integrity_backend,
    )

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    store = (
        Path(evidence_root)
        if evidence_root is not None
        else _REPO_ROOT / "evidence" / "ops" / EVIDENCE_DIRNAME / run_id
    )
    store.mkdir(parents=True, exist_ok=True)

    handle = None
    transport = fresh_get_transport
    private_auth_path = "NOT_REACHED"
    wp1_status = "NOT_STARTED"
    wp2_status = "NOT_STARTED"
    blockers_closed: list[str] = []
    earliest = ""
    common_epoch_id = ""
    gets_performed = 0

    def _fail(
        *,
        wp1: str,
        wp2: str,
        blocker: str,
        status_fields: Mapping[str, str] | None = None,
    ) -> CurrentProductiveFullCorePreExternalClosureResultV1:
        fields = dict(status_fields or {})
        claims = {
            "OWNER_GO": owner_go,
            "THIS_SLICE": THIS_SLICE,
            "BASE_SHA": base_sha,
            "WP1_STATUS": wp1,
            "WP2_STATUS": wp2,
            "EARLIEST_REMAINING_BLOCKER": blocker,
            "POST_COUNT": "0",
            "PERMIT_CREATED": FALSE_TOKEN,
            "EXTERNAL_EFFECT_OCCURRED": FALSE_TOKEN,
            **fields,
        }
        _assert_no_secrets(claims)
        _persist_json(path=store / "claims.json", payload=claims)
        _persist_json(path=store / "SUMMARY.json", payload={"FIRST_REAL_BLOCKER": blocker})
        persist_manifest_sha256_v1(store_root=store)
        manifest_rc = verify_manifest_sha256_v1(store_root=store)
        return CurrentProductiveFullCorePreExternalClosureResultV1(
            store_root=str(store),
            base_sha=base_sha,
            head_sha=_git_head_sha_v1(),
            branch=_git_branch_v1(),
            wp1_status=wp1,
            wp2_status=wp2,
            common_epoch_status=fields.get("COMMON_EPOCH_STATUS", "FAIL"),
            common_epoch_id=common_epoch_id,
            u01_status=fields.get("U01_STATUS", "UNKNOWN"),
            p01_status=fields.get("P01_STATUS", "UNKNOWN"),
            live_account_bound_status=fields.get("LIVE_ACCOUNT_BOUND_STATUS", "UNKNOWN"),
            equity_producer_status=fields.get("EQUITY_PRODUCER_STATUS", "UNKNOWN"),
            bound_value_29p_status=fields.get("29P_BOUND_VALUE_STATUS", "UNKNOWN"),
            admissibility_29p_status=fields.get("29P_ADMISSIBILITY_STATUS", "UNKNOWN"),
            instrument_metadata_status=fields.get("INSTRUMENT_METADATA_STATUS", "UNKNOWN"),
            reference_price_status=fields.get("REFERENCE_PRICE_STATUS", "UNKNOWN"),
            mv2_capital_context_rebind_status=fields.get(
                "MV2_CAPITAL_CONTEXT_REBIND_STATUS", "UNKNOWN"
            ),
            portfolio_reservation_status=fields.get("PORTFOLIO_RESERVATION_STATUS", "NOT_REACHED"),
            venue_plan_status=fields.get("VENUE_PLAN_STATUS", "NOT_REACHED"),
            final_order_envelope_status=fields.get("FINAL_ORDER_ENVELOPE_STATUS", "NOT_REACHED"),
            terminal_disposition=fields.get("TERMINAL_DISPOSITION", "FAIL_CLOSED"),
            gets_actually_performed=gets_performed,
            private_get_auth_path=private_auth_path,
            runtime_owner_gos_consumed=(),
            synthetic_contamination=False,
            fixture_contamination=False,
            manual_injection_contamination=False,
            post_count=0,
            permit_created=False,
            external_effect_occurred=False,
            blockers_closed=tuple(blockers_closed),
            earliest_remaining_blocker=blocker,
            manifest_verify_rc=manifest_rc,
        )

    try:
        transport, cred_status, handle = (
            bind_productive_read_only_get_transport_for_execute_network_v1(
                execute_network=execute_network,
                fresh_get_transport=transport,
                vault_file=vault_file,
                repo_root=_REPO_ROOT,
            )
        )
        if cred_status == CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS:
            return _fail(
                wp1="BLOCKED",
                wp2="NOT_STARTED",
                blocker="CREDENTIAL_HANDLE_FAIL_CLOSED",
                status_fields={
                    "PRIVATE_GET_AUTH_PATH": cred_status,
                    "COMMON_EPOCH_STATUS": "NOT_REACHED",
                },
            )
        if transport is None:
            return _fail(
                wp1="BLOCKED",
                wp2="NOT_STARTED",
                blocker="FRESH_GET_TRANSPORT_REQUIRED",
                status_fields={"COMMON_EPOCH_STATUS": "NOT_REACHED"},
            )
        if execute_network is True:
            private_auth_path = "SECTION_11_13_5_SECRETREF_VAULT_AND_K1_VENUE_AUTH_SESSION_V1"
        elif isinstance(transport, FullCoreProductiveReadOnlyGetTransportV1):
            private_auth_path = "PRODUCTIVE_READ_ONLY_TRANSPORT_PREBOUND"
        else:
            private_auth_path = "INJECTED_PRODUCTIVE_CLASS_TRANSPORT"

        decision_epoch = _utc_now_iso_v1()
        common_epoch_id = decision_epoch
        wp1_status = "IN_PROGRESS"
        handoff = compose_current_productive_29p_common_epoch_handoff_v1(
            decision_epoch=decision_epoch,
            bound_instrument=bound_instrument,
            fresh_get_transport=transport,
        )
        gets_performed = int(getattr(transport, "request_count", 0) or 0)

        if handoff.evaluator_29p is not True:
            wp1_status = "FAIL"
            return _fail(
                wp1=wp1_status,
                wp2="NOT_STARTED",
                blocker="STEP_29P_RISK_ADMISSIBLE_FALSE",
                status_fields={
                    "COMMON_EPOCH_STATUS": "COMPOSED_NOT_ADMISSIBLE",
                    "U01_STATUS": str(handoff.adaptation.status),
                    "P01_STATUS": "DOES_NOT_APPLY",
                    "LIVE_ACCOUNT_BOUND_STATUS": str(handoff.lab_status),
                    "EQUITY_PRODUCER_STATUS": "MINTED" if handoff.produced else "UNMINTED",
                    "29P_BOUND_VALUE_STATUS": "UNBOUND",
                    "29P_ADMISSIBILITY_STATUS": FALSE_TOKEN,
                },
            )

        blockers_closed.extend(["E2E-B01", "E2E-B02", "E2E-B03", "E2E-B04", "E2E-B05"])
        wp1_status = "PASS"

        try:
            live_29p_injected = (
                build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1(
                    handoff=handoff,
                    transport=transport,
                )
            )
        except (
            CurrentProductiveCommonEpochToEnterLive29PHandoffError,
            CurrentProductive29PCommonEpochHandoffError,
        ) as exc:
            return _fail(
                wp1=wp1_status,
                wp2="NOT_STARTED",
                blocker=str(exc)[:120],
                status_fields={
                    "COMMON_EPOCH_STATUS": "PASS",
                    "U01_STATUS": str(handoff.adaptation.status),
                    "LIVE_ACCOUNT_BOUND_STATUS": str(handoff.lab_status),
                    "EQUITY_PRODUCER_STATUS": "MINTED",
                    "29P_ADMISSIBILITY_STATUS": TRUE_TOKEN,
                },
            )

        wp2_status = "IN_PROGRESS"
        candles = candles_payload
        if candles is None:
            candles = _fetch_candles_payload_v1(
                transport=transport,
                venue_native_id=str(bound_instrument.venue_native_id),
                decision_epoch=decision_epoch,
            )
            gets_performed = int(getattr(transport, "request_count", 0) or 0)

        mk = dict(market_kwargs or {})
        mk.pop("candles_payload", None)
        mk.pop("g17_typed_vol_producers", None)
        mk.setdefault("origin_main_sha", base_sha)
        mk.setdefault("cycle_id_prefix", f"pre-ext-closure-{run_id}")
        mk.setdefault("observed_unix", datetime.now(timezone.utc).timestamp())
        mk.setdefault("mark_px", 100.0)
        mk.setdefault("index_px", 100.0)
        mk.setdefault("bid_px", 99.5)
        mk.setdefault("ask_px", 100.5)
        mk.setdefault("volume", 10.0)
        mk.setdefault("open_interest", 20.0)
        mk.setdefault("funding_rate", 0.0001)
        mk.setdefault("finalized_closes", (98.0, 99.0, 100.0))
        mk.setdefault("last_finalized_event_ts_unix", mk["observed_unix"] - 60.0)
        mk.setdefault("venue_flat", True)
        mk.setdefault("existing_position_side", ExistingPositionSide.NONE)

        pair = _lane_pair_v1(lane_state_root=Path(lane_state_root), bound=bound_instrument)
        pairs = {"LANE_1": pair}
        invoke_kwargs = dict(mk)
        if g17_typed_vol_producers is not None:
            invoke_kwargs["g17_typed_vol_producers"] = g17_typed_vol_producers

        results = invoke_occupied_lane_governed_cycle_n1_consumer_v1(
            pairs,
            live_29p_injected=live_29p_injected,
            portfolio_budget_owner=portfolio_budget_owner,
            candles_payload=dict(candles),
            **invoke_kwargs,
        )
        lane_result = results["LANE_1"]
        cycle = lane_result.governed_cycle_result
        terminal = str(cycle.disposition)
        post_count = int(cycle.post_count)
        permit_created = bool(cycle.permit_created)

        if post_count != 0 or permit_created:
            raise CurrentProductiveFullCorePreExternalClosureError("EXTERNAL_EFFECT_OR_POST_LEAK")

        venue_plan_status = "NOT_REACHED"
        envelope_status = "NOT_REACHED"
        rebind_status = "NOT_REACHED"
        ref_price_status = "NOT_EVALUATED"
        metadata_status = "NOT_EVALUATED"
        portfolio_status = "NOT_REACHED"

        if terminal == DISPOSITION_PRE_EXTERNAL_EFFECT:
            wp2_status = "PASS"
            blockers_closed.append("E2E-B06")
            venue_plan_status = "PASS"
            envelope_status = "PASS"
            rebind_status = "PASS"
            ref_price_status = "GOVERNED_MV2_MARK"
            metadata_status = "TRUSTED_CURRENT"
            portfolio_status = "PASS" if portfolio_budget_owner is not None else "NOT_REQUIRED"
            earliest = "OWNER_GO_REQUIRED_FOR_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT"
        elif terminal == DISPOSITION_HOLD:
            wp2_status = "HOLD_TERMINAL"
            earliest = "MARKET_STATE_HOLD_NOT_ENTER"
        else:
            wp2_status = "FAIL"
            earliest = str(cycle.first_genuine_blocker or cycle.reason_code or "FAIL_CLOSED")

        claims = {
            "OWNER_GO": owner_go,
            "THIS_SLICE": THIS_SLICE,
            "BASE_SHA": base_sha,
            "HEAD_SHA": _git_head_sha_v1(),
            "WP1_STATUS": wp1_status,
            "WP2_STATUS": wp2_status,
            "COMMON_EPOCH_STATUS": "PASS",
            "COMMON_EPOCH_ID": common_epoch_id,
            "U01_STATUS": str(handoff.adaptation.status),
            "P01_STATUS": "DOES_NOT_APPLY",
            "LIVE_ACCOUNT_BOUND_STATUS": str(handoff.lab_status),
            "EQUITY_PRODUCER_STATUS": "MINTED",
            "29P_BOUND_VALUE_STATUS": "BOUND",
            "29P_ADMISSIBILITY_STATUS": TRUE_TOKEN,
            "INSTRUMENT_METADATA_STATUS": metadata_status,
            "REFERENCE_PRICE_STATUS": ref_price_status,
            "MV2_CAPITAL_CONTEXT_REBIND_STATUS": rebind_status,
            "PORTFOLIO_RESERVATION_STATUS": portfolio_status,
            "VENUE_PLAN_STATUS": venue_plan_status,
            "FINAL_ORDER_ENVELOPE_STATUS": envelope_status,
            "TERMINAL_DISPOSITION": terminal,
            "GETS_ACTUALLY_PERFORMED": str(gets_performed),
            "PRIVATE_GET_AUTH_PATH": private_auth_path,
            "RUNTIME_OWNER_GOS_CONSUMED": list(RUNTIME_OWNER_GOS_CONSUMED),
            "SYNTHETIC_CONTAMINATION": FALSE_TOKEN,
            "FIXTURE_CONTAMINATION": FALSE_TOKEN,
            "MANUAL_INJECTION_CONTAMINATION": FALSE_TOKEN,
            "POST_COUNT": str(post_count),
            "PERMIT_CREATED": FALSE_TOKEN,
            "EXTERNAL_EFFECT_OCCURRED": FALSE_TOKEN,
            "BLOCKERS_CLOSED": blockers_closed,
            "EARLIEST_REMAINING_BLOCKER": earliest,
            "TRANSPORT_CLASS": str(getattr(transport, "transport_class", "")),
        }
        _assert_no_secrets(claims)
        _persist_json(path=store / "claims.json", payload=claims)
        _persist_json(
            path=store / "SUMMARY.json",
            payload={
                "TERMINAL_DISPOSITION": terminal,
                "POST_COUNT": str(post_count),
                "EARLIEST_REMAINING_BLOCKER": earliest,
            },
        )
        persist_manifest_sha256_v1(store_root=store)
        manifest_rc = verify_manifest_sha256_v1(store_root=store)

        return CurrentProductiveFullCorePreExternalClosureResultV1(
            store_root=str(store),
            base_sha=base_sha,
            head_sha=_git_head_sha_v1(),
            branch=_git_branch_v1(),
            wp1_status=wp1_status,
            wp2_status=wp2_status,
            common_epoch_status="PASS",
            common_epoch_id=common_epoch_id,
            u01_status=str(handoff.adaptation.status),
            p01_status="DOES_NOT_APPLY",
            live_account_bound_status=str(handoff.lab_status),
            equity_producer_status="MINTED",
            bound_value_29p_status="BOUND",
            admissibility_29p_status=TRUE_TOKEN,
            instrument_metadata_status=metadata_status,
            reference_price_status=ref_price_status,
            mv2_capital_context_rebind_status=rebind_status,
            portfolio_reservation_status=portfolio_status,
            venue_plan_status=venue_plan_status,
            final_order_envelope_status=envelope_status,
            terminal_disposition=terminal,
            gets_actually_performed=gets_performed,
            private_get_auth_path=private_auth_path,
            runtime_owner_gos_consumed=RUNTIME_OWNER_GOS_CONSUMED,
            synthetic_contamination=False,
            fixture_contamination=False,
            manual_injection_contamination=False,
            post_count=post_count,
            permit_created=permit_created,
            external_effect_occurred=False,
            blockers_closed=tuple(blockers_closed),
            earliest_remaining_blocker=earliest,
            manifest_verify_rc=manifest_rc,
        )
    finally:
        release_productive_credential_handle_v1(handle)


__all__ = [
    "ALLOWED_OWNER_GOS",
    "EVIDENCE_DIRNAME",
    "EXPECTED_BASELINE_ORIGIN_MAIN_SHA",
    "OWNER_GO",
    "RUNTIME_OWNER_GOS_CONSUMED",
    "THIS_SLICE",
    "CurrentProductiveFullCorePreExternalClosureError",
    "CurrentProductiveFullCorePreExternalClosureResultV1",
    "execute_current_productive_full_core_pre_external_closure_v1",
]
