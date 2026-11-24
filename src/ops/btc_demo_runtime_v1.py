"""Concrete Slot-3 Demo ports: original Core, writer, POST and GET consumers."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import time
from urllib.parse import urlencode
from uuid import uuid4

from src.ops import btc_demo_lane3_v2 as demo
from src.ops.btc_demo_bounded_host_v1 import validate_btc_demo_host_config_v1
from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_baseline_v1 import (
    EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
)
from src.ops.btc_demo_budget_owner_v3 import BtcDemoBudgetOwnerV3, CONTRACT
from src.ops.btc_demo_budget_reconciliation_host_v1 import BtcDemoBudgetReconciliationHostV1
from src.ops.btc_demo_offline_trading_host_v1 import (
    BtcDemoOfflineTradingHostV1,
    BtcDemoMarketObservationV1,
)
from src.ops.btc_demo_entry_submit_v1 import (
    BtcDemoEntryPostContextV1,
    btc_demo_entry_reader_v1,
    capture_btc_demo_entry_quantity_v1,
    execute_btc_demo_entry_post_v1,
)
from src.ops.btc_demo_bounded_post_owner_v1 import BtcDemoBoundedPostOwnerV1
from src.ops.btc_demo_session_control_v1 import (
    BoundedDemoSessionRegistrationV1,
    validate_session_control_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    FullCoreK1BoundVenueAuthHandleV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_pending_observation_v1 import (
    capture_current_post_pending_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    extract_ticker_fields_v1,
    extract_open_interest_v1,
    extract_funding_rate_v1,
    extract_finalized_candle_closes_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
    prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_reconciliation_admission_v1 import (
    build_explicit_non_productive_bounded_harness_master_v2_reconciliation_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    immutable_json_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    K1AccountObservationSourceV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.absolute_movement_cost_v1 import (
    EntryPublicMarkSourceV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
    PortfolioBudgetHostV1,
    AuthenticatedEntryEpisodeRequestV1,
    collect_host_account_observation_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.slot_loss_budget_v1 import (
    SlotCapitalAllocationV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
    require_btc_testnet_slot_scope_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


def fixed_demo_pin_v1(pin):
    """Explicit user pin, with no invented economic rank or Cap23 receipt."""
    if (
        type(pin) is not dict
        or set(pin)
        != {
            "kind",
            "instrument_source",
            "instrument_source_sha256",
            "canonical_instrument_id",
            "native_instrument_id",
        }
        or pin["kind"] != "USER_FIXED_TESTNET_INSTRUMENT"
        or pin["native_instrument_id"] != demo._NATIVE
    ):
        raise ValueError("BTC_DEMO_ORIGINAL_FIXED_PIN_REQUIRED")
    source = Path(pin["instrument_source"])
    if (
        not source.is_absolute()
        or source.resolve() != source
        or sha256(source.read_bytes()).hexdigest() != pin["instrument_source_sha256"]
    ):
        raise ValueError("BTC_DEMO_FIXED_PIN_SOURCE_CHANGED")
    original = json.loads(source.read_bytes())
    row = original["instrument"]
    if (
        original["environment"] != "TESTNET"
        or original["purpose"] != "INSTRUMENT_IDENTITY"
        or row["canonical_instrument_id"] != pin["canonical_instrument_id"]
        or row["venue_native_inst_id"] != demo._NATIVE
    ):
        raise ValueError("BTC_DEMO_FIXED_PIN_IDENTITY_MISMATCH")
    evidence = digest(pin)
    return BoundInstrumentV1(
        instrument_id=pin["canonical_instrument_id"],
        venue_native_id=demo._NATIVE,
        ranking_snapshot_id="USER_PIN_NO_ECONOMIC_RANKING",
        ranking_integrity_digest=evidence,
        universe_snapshot_id=pin["instrument_source_sha256"],
        selection_id="USER_FIXED_TESTNET:" + evidence,
        selection_integrity_digest=evidence,
        selection_state="SELECTED",
        ranking_policy_id="USER_PIN_NO_CAP23_RANKING_CLAIM",
        ranking_policy_version="1",
    )


class BtcDemoRuntimeV1:
    """One process around the original Slot-3 contracts. No work in __init__."""

    def __init__(
        self,
        *,
        config,
        signing_handle,
        clock=time.time,
        execution_integrity_backend=None,
        opener_factory=None,
    ):
        self.config = deepcopy(validate_btc_demo_host_config_v1(config))
        if (
            type(signing_handle) is not FullCoreK1BoundVenueAuthHandleV1
            or signing_handle.execution_environment != "TESTNET"
        ):
            raise ValueError("BTC_DEMO_RUNTIME_TESTNET_SIGNER_REQUIRED")
        self.handle, self.clock = signing_handle, clock
        self.integrity, self.post_opener = execution_integrity_backend, opener_factory
        self.root = Path(config["testnet_root"])
        self.first = self.portfolio = self.post_owner = None
        self.registration = None
        self.reads = None
        self.transport = None
        self.inventory = None
        self._g17_final_window = None

    @property
    def owner(self):
        return self.portfolio.owner if self.portfolio is not None else self.first.budget.owner

    def start_or_recover_v1(self, *, operator_start):
        from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_baseline_v1 import (
            resolve_and_assert_live_post_execution_baseline_v1,
        )
        from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
            FROZEN_PROFIT_PROTECTION_DISTANCE,
        )
        from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
            layer_c_derived_exit_policy_adverse_config_digest_v1,
        )

        self.bound = fixed_demo_pin_v1(self.config["fixed_pin"])
        sha = resolve_and_assert_live_post_execution_baseline_v1(
            declared_baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            integrity_backend=self.integrity,
        )
        if sha != self.config["repository_sha"]:
            raise ValueError("BTC_DEMO_RUNTIME_SOURCE_REVISION_MISMATCH")
        if self.registration is not None:
            operator_start.validate_v1(
                config=self.config, now_unix=self.clock(), existing_registration=self.registration
            )
            return self.registration
        policy_path = Path(self.config["entry_budget_policy_path"])
        if (
            not policy_path.is_absolute()
            or sha256(policy_path.read_bytes()).hexdigest()
            != self.config["entry_budget_policy_sha256"]
        ):
            raise ValueError("BTC_DEMO_RUNTIME_ORIGINAL_POLICY_CHANGED")
        policy = load_slot_entry_budget_v1(policy_path)
        if policy.require_xperp_liquidation_projection:
            raise ValueError(
                "BTC_DEMO_ADDITIONAL_LIQUIDATION_POLICY_REQUIRES_ITS_ORIGINAL_CUSTODY_BINDING"
            )
        self.policy = replace(
            policy, allowed_slot_ids=("LANE_3",), aggregate_reserved_notional_limit=Decimal(25)
        )
        require_btc_testnet_slot_scope_v1(self.policy, {"LANE_3": self.bound})
        recover = (self.root / "testnet-state/budget-owner/owner/reservations.sqlite3").is_file()
        if not recover:
            operator_start.validate_v1(config=self.config, now_unix=self.clock())
            self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
            lane = self.root / "testnet-state/LANE_3"
            lane.mkdir(mode=0o700, parents=True, exist_ok=True)
            immutable_json_v1(
                self.root / "btc-lane3-testnet.json",
                dict(
                    lane="LANE_3",
                    instrument=demo._NATIVE,
                    environment="TESTNET",
                    roots={"lane": str(lane)},
                ),
            )
        lane = demo._demo_lane_root(self.root)
        self.cursor = lane / "cursor/LANE_3"
        self.proof_root = lane / "authenticated-execution-proofs"
        self.proof_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.exit_config = layer_c_derived_exit_policy_adverse_config_digest_v1(
            profit_protection_distance=FROZEN_PROFIT_PROTECTION_DISTANCE
        )
        kwargs = dict(
            durable_root=lane.parent / "budget-owner/owner",
            durable_account_identity=self.config["account_identity"],
            durable_mode="recover" if recover else "create",
            durable_lane_bindings={"LANE_3": self.bound},
            entry_budget_policy=self.policy,
        )
        if not recover:
            kwargs["slot_capital_allocation"] = SlotCapitalAllocationV1(
                self.config["account_identity"],
                "explicit-bounded-demo-start:" + operator_start.digest_v1(),
                (("LANE_3", Decimal(25)),),
            )
        owner = BtcDemoBudgetOwnerV3(**kwargs)
        if recover:
            registration = validate_session_control_v1(owner, owner._bounded_demo_session_control)
            if registration is None:
                owner.close()
                raise ValueError("BTC_DEMO_RUNTIME_ORIGINAL_SESSION_REQUIRED")
            operator_start.validate_v1(
                config=self.config, now_unix=self.clock(), existing_registration=registration
            )
        else:
            now = datetime.fromtimestamp(self.clock(), timezone.utc).isoformat()
            registration = BoundedDemoSessionRegistrationV1(
                session_id=self.config["session_id"],
                account_identity=self.config["account_identity"],
                instrument_id=self.bound.instrument_id,
                started_at_utc=now,
                operator_start_digest=operator_start.digest_v1(),
            )
            owner.register_bounded_demo_session_v1(
                registration, expected_head=owner._store.head, now_utc=now
            )
        self.registration = registration
        budget = BtcDemoBudgetReconciliationHostV1(
            owner=owner,
            bound=self.bound,
            account=self.config["account_identity"],
            testnet_root=self.root,
        )
        self.first = BtcDemoOfflineTradingHostV1(
            budget_host=budget,
            g17_producer=None,
            repository_sha=sha,
            config_digest=self.exit_config,
            writer_session_id=self.config["session_id"],
        )
        self.reads = btc_demo_entry_reader_v1(signing_handle=self.handle)
        self.transport = FullCoreProductiveReadOnlyGetTransportV1(
            handle=self.handle, execution_environment="TESTNET", max_request_count=250000
        )
        self.inventory = K1AccountObservationSourceV1(
            credential=self.handle,
            transport=self.transport,
            expected_account_identity=self.config["account_identity"],
            session_id=self.config["session_id"],
            clock=self.clock,
            account_inventory_guard=True,
            inventory_inst_type="FUTURES",
        )
        self.movement = EntryPublicMarkSourceV1(lane / "public-entry-movement", self.transport)
        self.post_owner = BtcDemoBoundedPostOwnerV1(
            root=lane / "bounded-post-owner", registration=registration, recover=recover
        )
        return registration

    def _market_v1(self):
        from concurrent.futures import ThreadPoolExecutor

        acquisition = self.config["session_id"] + ":market:" + uuid4().hex
        queries = dict(
            candles=("/api/v5/market/candles", dict(instId=demo._NATIVE, bar="1m", limit="100")),
            g17=(
                "/api/v5/market/history-mark-price-candles",
                dict(instId=demo._NATIVE, bar="1m", limit="100"),
            ),
            mark=("/api/v5/public/mark-price", dict(instType="FUTURES", instId=demo._NATIVE)),
            index=("/api/v5/market/index-tickers", dict(instId="BTC-USD")),
            ticker=("/api/v5/market/ticker", dict(instId=demo._NATIVE)),
            interest=(
                "/api/v5/public/open-interest",
                dict(instType="FUTURES", instId=demo._NATIVE),
            ),
            funding=("/api/v5/public/funding-rate", dict(instId=demo._NATIVE)),
        )

        def read(item):
            name, (path, query) = item
            row = self.transport.get(
                endpoint=path + "?" + urlencode(query),
                auth_required=False,
                pretrade_decision_id=acquisition,
                get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
            )
            if (
                not row.get_performed
                or row.http_status != 200
                or row.error_class
                or row.payload.get("code") != "0"
            ):
                raise ValueError("BTC_DEMO_MARKET_GET_UNPROVEN:" + name)
            return name, row

        with ThreadPoolExecutor(max_workers=7, thread_name_prefix="btc-demo-market") as worker:
            rows = dict(worker.map(read, queries.items()))
        now = self.clock()
        bid, ask, volume, _ = extract_ticker_fields_v1(
            rows["ticker"].payload, native_id=demo._NATIVE
        )
        oi = extract_open_interest_v1(rows["interest"].payload, native_id=demo._NATIVE)
        funding = extract_funding_rate_v1(rows["funding"].payload, native_id=demo._NATIVE)
        if any(value is None for value in (bid, ask, volume, oi, funding)):
            raise ValueError("BTC_DEMO_MARKET_ORIGINAL_METRICS_REQUIRED")
        final_window = digest(
            [row for row in rows["g17"].payload["data"] if len(row) >= 6 and row[5] == "1"]
        )
        if final_window != self._g17_final_window:
            g17 = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
                evidence_store_root=self.root / "g17",
                bound_instrument=self.bound,
                mark_candles_payload=rows["g17"].payload,
                receive_or_capture_timestamp=rows["g17"].acquired_at_utc,
            )
            if g17.fail_closed or g17.producer is None or not g17.estimate_present:
                raise ValueError("BTC_DEMO_G17_UNAVAILABLE:" + g17.reason_code)
            self.first.g17 = g17.producer
            self._g17_final_window = final_window
        obs = BtcDemoMarketObservationV1(
            "USD",
            acquisition,
            now,
            rows["candles"].payload,
            rows["mark"].payload,
            rows["mark"].acquired_at_utc,
            bid,
            ask,
            volume,
            oi,
            funding,
            self.portfolio is None,
            index_tickers_payload=rows["index"].payload,
        )
        return obs, rows

    def _ensure_portfolio_v1(self):
        from src.ops.gates.risk_gate import canonical_kill_switch_state_path

        if self.portfolio is None:
            self.first.budget.owner.close()
            self.portfolio = PortfolioBudgetHostV1(
                root=demo._demo_lane_root(self.root).parent / "budget-owner",
                private_rest_fetch=self.inventory,
                repository_sha=self.config["repository_sha"],
                session_id=self.config["session_id"],
                expected_account_identity=self.config["account_identity"],
                durable_mode="recover",
                clock=self.clock,
                execution_environment="TESTNET",
                entry_budget_policy=self.policy,
                reconciliation_transport=self.transport,
                execution_incident_state_path=canonical_kill_switch_state_path(),
                testnet_owner_contract=CONTRACT,
            )
            self.portfolio.recover_owner_for_occupied_execution_v1(
                {"LANE_3": self.bound}, operation="BOUNDED_DEMO_SESSION_RECOVERY"
            )
        return self.portfolio

    def _pair_v1(self):
        from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
            IsolatedLaneSlotV1,
        )

        return IsolatedLaneSlotV1(
            "LANE_3",
            "OCCUPIED",
            self.bound.instrument_id,
            str(self.cursor),
            self.bound.universe_snapshot_id,
            self.bound.ranking_snapshot_id,
            self.bound.ranking_integrity_digest,
        ), self.bound

    def _recovery_v1(self):
        from src.ops.full_core_live_path_composition_root_v1.current_productive_double_play_reversal_v1 import (
            recover_submitted_net_reversal_v1,
        )

        host = self._ensure_portfolio_v1()
        recovered = recover_submitted_net_reversal_v1(
            lane_pair=self._pair_v1(), get_budget_host=lambda: host, proof_root=self.proof_root
        )
        if (
            recovered is not None
            and recovered.transport_phase == "MAY_HAVE_SENT"
            and not recovered.booking_digest
        ):
            raise ValueError(
                "BTC_DEMO_NET_RECONCILIATION_REQUIRED:" + str(recovered.reconciliation_blocker)
            )
        # LIVE's global incident writer cannot consume Demo identities. The
        # original Demo proof still fences every unmatched/incident read.
        recovery, proofs = host.observe_authenticated_execution_reconciliation_v1(
            {"LANE_3": self.bound},
            proof_root=self.proof_root,
            deliver_authenticated_incidents=False,
        )
        links = host.owner.execution_links_v1(active_only=True)
        if len(links) != 1:
            raise ValueError("BTC_DEMO_ONE_ORIGINAL_ACTIVE_HOLD_REQUIRED")
        rid = next(iter(links))
        proof = proofs.get(rid)
        if proof is None or not recovery.execution_reconciliation.get(rid, {}).get("matched"):
            raise ValueError("BTC_DEMO_ENTRY_RECONCILIATION_REQUIRED")
        if proof.quantity_incident is not None:
            raise ValueError("BTC_DEMO_QUANTITY_INCIDENT_REQUIRES_SCOPED_RECONCILIATION")
        request = AuthenticatedEntryEpisodeRequestV1(self.proof_root, proof)
        recovery.inspect_current_authenticated_entry_v1(lane_id="LANE_3", proof=proof)
        if host.owner.read_authenticated_net_reversal_v1(rid) is None:
            from src.ops.btc_demo_entry_c1_source_v1 import read_original_entry_g17_for_c1_v1

            episode = recovery.bind_current_authenticated_entry_episode_v1(
                lane_id="LANE_3",
                proof_root=self.proof_root,
                proof=proof,
                config_digest=self.exit_config,
            )
            recovery.publish_authenticated_testnet_entry_c1_v1(
                lane_id="LANE_3",
                proof=proof,
                episode=episode,
                cursor_root=self.cursor,
                g17_producer=read_original_entry_g17_for_c1_v1(self, rid),
            )
        return recovery, request

    def step_v1(self):
        self.owner.require_bounded_demo_risk_window_v1()
        links = self.owner.execution_links_v1(active_only=True)
        if any(link["phase"] == "SUBMIT_MAY_HAVE_OCCURRED" for link in links.values()):
            return self._occupied_v1()
        if self.owner.stored_reservation_count_v1():
            raise ValueError("BTC_DEMO_UNSENT_HOLD_REQUIRES_ORIGINAL_RECOVERY")
        observation, _ = self._market_v1()
        inventory = collect_host_account_observation_v1(
            private_rest_fetch=self.inventory,
            instrument_ids_by_native_id={demo._NATIVE: self.bound.instrument_id},
            session_id=self.config["session_id"],
            clock=self.clock,
            expected_account=self.config["account_identity"],
        )
        if inventory.observed.positions or inventory.pending_orders:
            raise ValueError("BTC_DEMO_FRESH_FIRST_ENTRY_REQUIRES_FLAT_ACCOUNT")
        from src.ops.first_entry_mark_clock_v2 import FirstEntryBudgetBindingV2

        admission = (
            build_explicit_non_productive_bounded_harness_master_v2_reconciliation_admission_v1(
                bound_instrument_id=self.bound.instrument_id,
                session_id=self.config["session_id"],
                repository_sha=self.config["repository_sha"],
            )
        )
        entry = self.first.prepare_entry_v1(
            observation=observation,
            reconciliation=admission,
            budget_binding=FirstEntryBudgetBindingV2(
                str(self.owner._store.root),
                self.config["account_identity"],
                self.config["session_id"],
                False,
            ),
        )
        if entry.status != "ENTRY_DECIDED":
            return dict(
                status="WAITING_FOR_VALID_ENTRY",
                core_status=entry.status,
                core_blocker=None if entry.cycle is None else entry.cycle.input_blocker,
                core_fail_reasons=[] if entry.cycle is None else list(entry.cycle.fail_reasons),
            )
        result, _ = self.first.reserve_testnet_entry_v1(
            entry=entry, reads=self.reads, movement_input=self.movement, clock=self.clock
        )
        rid = result.reservation.reservation_id
        envelope, plan = self.first.plan_testnet_entry_v1(
            entry=entry,
            reservation_id=rid,
            expected_revision=self.first.budget.budget_revision_ref_v1(),
            clock=self.clock,
        )
        from src.ops.btc_demo_entry_c1_source_v1 import retain_original_entry_g17_for_c1_v1

        retain_original_entry_g17_for_c1_v1(self, rid)
        collect_host_account_observation_v1(
            private_rest_fetch=self.inventory,
            instrument_ids_by_native_id={demo._NATIVE: self.bound.instrument_id},
            session_id=self.config["session_id"],
            clock=self.clock,
            expected_account=self.config["account_identity"],
        )
        pending = capture_current_post_pending_v1(
            envelope=envelope, source=self.inventory, execution_environment="TESTNET"
        )
        context = BtcDemoEntryPostContextV1(self.first, entry, rid, envelope, plan, pending)
        quantity = capture_btc_demo_entry_quantity_v1(context=context, reads=self.reads)
        auth = self.post_owner.authorization_v1(envelope, action="ENTER", owner=self.owner)
        execute_btc_demo_entry_post_v1(
            context=context,
            authorization=auth,
            signing_handle=self.handle,
            quantity_context=quantity,
            baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            perform_real_venue_post=True,
            execution_integrity_backend=self.integrity,
            opener_factory=self.post_opener,
        )
        return dict(
            status="AWAITING_CONFIRMED_ENTRY",
            reservation_id=rid,
            envelope_digest=envelope.envelope_digest,
        )

    def _occupied_v1(self):
        from src.ops.btc_demo_net_reversal_pretrade_v1 import BtcDemoNetReversalPretradeV1
        from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
            invoke_occupied_lane_governed_cycle_n1_consumer_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
            CurrentProductiveEnterLive29PInjectedGetV1,
        )
        from src.ops.full_core_live_path_composition_root_v1.current_productive_double_play_reversal_v1 import (
            read_retained_net_reversal_post_context_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
            execute_authenticated_net_reversal_post_v1,
        )
        from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide

        recovery, request = self._recovery_v1()
        observation, _ = self._market_v1()
        self._admit_occupied_budget_v1(recovery)
        episode = recovery.bind_current_authenticated_entry_episode_v1(
            lane_id="LANE_3",
            proof_root=self.proof_root,
            proof=request.proof,
            config_digest=self.exit_config,
        )
        closes, c1 = extract_finalized_candle_closes_v1(observation.candles_payload)
        price = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
            mark_price_payload=observation.mark_price_payload,
            venue_native_id=demo._NATIVE,
            index_from_index_tickers=observation.index_tickers_payload,
            mark_acquired_at_utc=observation.mark_acquired_at_utc,
        )
        instruments, instrument_acquired = self.reads.read(
            "/api/v5/account/instruments", instType="FUTURES", instId=demo._NATIVE
        )
        injected = CurrentProductiveEnterLive29PInjectedGetV1(
            instruments_payload=instruments,
            observed_at=datetime.fromtimestamp(self.clock(), timezone.utc).isoformat(),
            testnet_reversal_pretrade_provider=BtcDemoNetReversalPretradeV1(
                self.reads, self.bound, self.config["account_identity"], self.clock, self.movement
            ),
        )
        pair = self._pair_v1()
        result = invoke_occupied_lane_governed_cycle_n1_consumer_v1(
            {"LANE_3": pair},
            origin_main_sha=self.config["repository_sha"],
            cycle_id_prefix=observation.cycle_id,
            observed_unix=self.clock(),
            mark_px=price.mark_px,
            index_px=price.index_px,
            bid_px=observation.bid_px,
            ask_px=observation.ask_px,
            volume=observation.volume,
            open_interest=observation.open_interest,
            funding_rate=observation.funding_rate,
            finalized_closes=closes,
            last_finalized_event_ts_unix=c1,
            venue_flat=False,
            existing_position_side=ExistingPositionSide(episode.identity.position_side),
            candles_payload=observation.candles_payload,
            g17_typed_vol_producers={"LANE_3": self.first.g17},
            canonical_price_provenance=price,
            portfolio_budget_owner=self.owner,
            host_budget_recovery=recovery,
            authenticated_entry=request,
            occupied_scope_mark_lane_id="LANE_3",
            live_29p_injected_by_lane={"LANE_3": injected},
        )["LANE_3"].governed_cycle_result
        if result.position_management_reversal is None:
            return dict(status="OCCUPIED", blocker=result.first_genuine_blocker)
        context = read_retained_net_reversal_post_context_v1(
            lane_pair=pair, recovery=recovery, authenticated_entry=request
        )
        auth = self.post_owner.authorization_v1(
            context.envelope, action="DIRECT_DOUBLE_PLAY_REVERSAL", owner=self.owner
        )
        execute_authenticated_net_reversal_post_v1(
            lane_pair=pair,
            recovery=recovery,
            authenticated_entry=request,
            authorization=auth,
            baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            perform_real_venue_post=True,
            testnet_signing_handle=self.handle,
            execution_integrity_backend=self.integrity,
            opener_factory=self.post_opener,
        )
        return dict(
            status="AWAITING_CONFIRMED_NET_REVERSAL",
            envelope_digest=context.envelope.envelope_digest,
        )

    def _admit_occupied_budget_v1(self, recovery):
        from dataclasses import asdict
        from src.ops.btc_demo_entry_financial_inputs_v1 import build_btc_demo_capital_inputs_v1
        from src.ops.portfolio_capital_reservation_budget_v1.entry_execution_cost_v1 import (
            FreshPretradeGetTransportResultV1,
        )

        epoch = datetime.fromtimestamp(self.clock(), timezone.utc).isoformat()
        acquisition = digest(
            dict(session=self.config["session_id"], purpose="OCCUPIED_BUDGET_RECOVERY", epoch=epoch)
        )
        sources = {}
        for name, path in (
            ("account", "/api/v5/account/config"),
            ("balance", "/api/v5/account/balance"),
        ):
            payload, acquired, body = self.reads.read_original_v1(path)
            sources[name] = FreshPretradeGetTransportResultV1(
                get_performed=True,
                method="GET",
                endpoint=path,
                http_status=200,
                payload=payload,
                auth_header_sent=True,
                transport_class="OKX_EEA_DEMO_READ_ONLY_GET",
                venue_live_contact=True,
                historical_reuse=False,
                error_class="",
                body_sha256=sha256(body).hexdigest(),
                pretrade_decision_id=acquisition,
                acquired_at_utc=acquired.isoformat(),
            )
        _, capital, _, _ = build_btc_demo_capital_inputs_v1(
            sources,
            account=self.config["account_identity"],
            epoch=epoch,
            now=datetime.fromtimestamp(self.clock(), timezone.utc).isoformat(),
            config=demo._only(sources["account"].payload),
            minimum_available=Decimal(0),
        )
        immutable_json_v1(
            self.root / "occupied-capital" / (acquisition + ".json"),
            dict(
                sources={k: asdict(v) for k, v in sources.items()},
                capital_recovery_only=True,
                no_additional_slot_funding=True,
            ),
        )
        recovery.recover_v1(self.owner, capital)

    def finish_v1(self):
        from src.ops.btc_demo_session_close_v1 import prepare_btc_demo_session_close_v1
        from src.ops.btc_demo_session_close_submit_v1 import execute_btc_demo_session_close_v1
        from src.ops.btc_demo_session_close_reconciliation_v1 import (
            reconcile_btc_demo_session_close_v1,
        )

        if not self.owner.stored_reservation_count_v1():
            from src.ops.btc_demo_runtime_no_entry_v1 import confirm_no_entry_v1

            return confirm_no_entry_v1(runtime=self)
        control = self.owner._bounded_demo_session_control
        if control["phase"] == "CLOSED":
            return dict(
                status="CONFIRMED_CLOSED",
                session_result=self.owner.bounded_demo_session_result_v1(),
            )
        if control["phase"] != "CLOSING":
            recovery, request = self._recovery_v1()
            context = prepare_btc_demo_session_close_v1(
                recovery=recovery, entry_request=request, reads=self.reads
            )
            auth = self.post_owner.authorization_v1(
                context.envelope, action="BOUNDED_SESSION_CLOSE", owner=self.owner
            )
            execute_btc_demo_session_close_v1(
                context=context,
                authorization=auth,
                signing_handle=self.handle,
                baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                perform_real_venue_post=True,
                execution_integrity_backend=self.integrity,
                opener_factory=self.post_opener,
            )
        self._ensure_portfolio_v1()
        reconcile_btc_demo_session_close_v1(host=self.portfolio)
        return dict(
            status="CONFIRMED_CLOSED", session_result=self.owner.bounded_demo_session_result_v1()
        )

    def close(self):
        if self.portfolio is not None:
            self.portfolio.close()
        elif self.first is not None:
            self.first.budget.owner.close()
        if self.inventory is not None:
            self.inventory.close()
