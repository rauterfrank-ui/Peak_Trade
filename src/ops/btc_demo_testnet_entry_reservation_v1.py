"""Offline first-entry reservation using the original Slot 3 TESTNET journal.

The input consists of synthetic, decision-bound GET receipts. No transport,
credential or execution port is available here. The separate signed Demo
inspection is not an input to this fixture.
"""

from copy import deepcopy
from dataclasses import asdict, replace
from threading import RLock
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path

from src.ops import btc_demo_lane3_v2 as demo
from src.ops.full_core_live_path_composition_root_v1 import pretrade_acquisition_v1 as acquisition
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    resolve_current_productive_live_29p_adverse_exit_distance_v1,
    resolve_protective_stop_sizing_side_for_live_29p_join_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    immutable_json_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    OBSERVATION_FACT_ID,
    OBSERVATION_SURFACE,
    CurrentProductiveUsdcFreeMarginObservationV1,
    produce_current_productive_29p_risk_capital_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u01_account_mode_adapter_v1 import (
    adapt_current_productive_u01_account_mode_v1,
    build_current_productive_u01_eligibility_fact_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_v1 import (
    bind_current_productive_p01_fact_for_ct_sizing_produce_v1,
)
from src.ops.governed_productive_instrument_metadata_authority_producer_v1.current_productive_okx_instruments_row_producer_v1 import (
    produce_current_productive_instrument_quantity_constraints_from_okx_row_v1,
)
from src.ops.governed_productive_monetary_normalization_v1.normalize_v1 import (
    build_capital_risk_sizing_monetary_context_v1,
    crs_operands_from_monetary_context_v1,
)
from src.ops.governed_productive_monetary_normalization_v1.sizing_source_v1 import (
    build_sizing_monetary_source_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as cost
from src.ops.portfolio_capital_reservation_budget_v1.absolute_movement_cost_v1 import (
    AbsoluteMovementCostObservationV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.native_initial_margin_v1 import (
    NativeInitialMarginObservationV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
    capital_context_facts_v1,
    apply_capital_context_facts_v1,
    evaluate_capital_risk_sizing_v1,
    CapitalRiskSizingOutcome,
    CapitalReservationV1,
    ReservationId,
    SlotId,
    ReservationStateV1,
    _reservation_key,
    observation_identity_v1,
    ReserveDispositionV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    PORTFOLIO_STATE_FILENAME,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import PortfolioTruthSnapshotV1
from src.ops.productive_reconciliation_runtime_binding_v1.startup_gate_v1 import (
    run_productive_reconciliation_startup_gate_v1,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    derive_protective_stop_price_from_adverse_exit_v0,
    default_offline_replay_capital_context_v0,
)
from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
    build_capital_risk_sizing_input_from_decision_v0,
)

SOURCE = "OKX_EEA_TESTNET_OFFLINE_FIXTURE"
_ENDPOINTS = {
    "account": demo._CONFIG,
    "instruments": f"{demo._INSTRUMENTS}?instType=FUTURES&instId={demo._NATIVE}",
    "fees": f"{demo._FEE}?instType=FUTURES&instFamily={demo._FAMILY}",
    "book": f"/api/v5/market/books?instId={demo._NATIVE}&sz=20",
    "balance": demo._BALANCE,
    "leverage": f"/api/v5/account/leverage-info?instId={demo._NATIVE}&mgnMode=cross",
    "funding": f"/api/v5/public/funding-rate?instId={demo._NATIVE}",
    "positions": demo._POSITIONS,
    "pending": demo._PENDING,
}


def _need(condition, reason):
    if not condition:
        raise ValueError(reason)


def _current_sources(rows, *, account, epoch, cycle_id, now):
    _need(
        type(rows) is dict and rows.keys() == _ENDPOINTS.keys(),
        "BTC_TESTNET_COMPLETE_BATCH_REQUIRED",
    )
    expected = cost.canonical(dict(decision_epoch=epoch, cycle_id=cycle_id))
    for key, endpoint in _ENDPOINTS.items():
        row = rows[key]
        private = key not in {"book", "funding"}
        _need(
            type(row) is cost.FreshPretradeGetTransportResultV1
            and row.transport_class == (f"{SOURCE}:{account}" if private else SOURCE)
            and row.venue_live_contact is False
            and row.data_safety_source_kind == "SYNTHETIC"
            and row.method == "GET"
            and row.get_performed is True
            and row.http_status == 200
            and row.auth_header_sent is private
            and not row.error_class
            and row.historical_reuse is False
            and row.endpoint == endpoint
            and row.pretrade_decision_id == expected
            and row.body_sha256 == cost.digest(row.payload),
            "BTC_TESTNET_WRONG_SOURCE:" + key,
        )
        acquisition.acquisition_age_seconds_v1(acquired_at_utc=epoch, now_utc=row.acquired_at_utc)
        acquisition.acquisition_age_seconds_v1(acquired_at_utc=row.acquired_at_utc, now_utc=now)
        cost._rows(row.payload)
    config = demo._only(rows["account"].payload)
    _need(config.get("uid") == account, "BTC_TESTNET_WRONG_ACCOUNT")
    _need(config.get("posMode") == "net_mode", "BTC_TESTNET_NET_POSITION_MODE_REQUIRED")
    _need(
        demo._only(rows["balance"].payload).get("uid", account) == account,
        "BTC_TESTNET_WRONG_ACCOUNT",
    )
    instrument = demo._only(rows["instruments"].payload)
    _need(
        instrument.get("instId") == demo._NATIVE and instrument.get("state") == "live",
        "BTC_TESTNET_WRONG_INSTRUMENT",
    )
    cost._instrument_source_path_v1(rows["instruments"], instrument, config)
    for key in ("positions", "pending"):
        _need(
            rows[key].payload == {"code": "0", "data": []},
            "BTC_TESTNET_COMPLETE_FLAT_INVENTORY_REQUIRED",
        )
    return config


def _capital(rows, *, account, epoch, now, config):
    balance = rows["balance"]
    detail = cost._one(demo._only(balance.payload)["details"], "ccy", "USDC")
    value = cost._money(detail.get("availEq"), positive=True)
    _need(value >= demo._BUDGET_USDC, "BTC_TESTNET_DECLARED_BUDGET_UNCOVERED")
    age = acquisition.acquisition_age_seconds_v1(
        acquired_at_utc=balance.acquired_at_utc, now_utc=now
    )
    scope = dict(
        bound_account_identity=account,
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=epoch,
    )
    margin = CurrentProductiveUsdcFreeMarginObservationV1(
        **scope,
        fact_id=OBSERVATION_FACT_ID,
        surface=OBSERVATION_SURFACE,
        value=detail["availEq"],
        settlement_currency="USDC",
        selected_ccy="USDC",
        observed_at_as_of=balance.acquired_at_utc,
        age_seconds=age,
        freshness_max_age=str(acquisition.NUMERIC_EQUITY_TTL_SECONDS),
        provenance_digest=balance.body_sha256,
        already_net_of_in_use="true",
        account_level_avail_eq_used="false",
        fallback_chain_used="false",
    )
    p01 = bind_current_productive_p01_fact_for_ct_sizing_produce_v1(
        base=margin, age_seconds=age, freshness_max_age=margin.freshness_max_age
    )
    eligibility = build_current_productive_u01_eligibility_fact_v1(
        **scope,
        adaptation=adapt_current_productive_u01_account_mode_v1(config["acctLv"]),
        provenance_digest=rows["account"].body_sha256,
    )
    output = produce_current_productive_29p_risk_capital_v1(
        observation=margin, p01=p01, eligibility=eligibility
    )
    _need(
        output.produced == "true" and Decimal(output.value) >= demo._BUDGET_USDC,
        "BTC_TESTNET_CAPITAL_NOT_ADMISSIBLE",
    )
    return margin, output


def _sizing(cycle, bound, instruments, equity, observed_at, policy, source_digest):
    replay = cycle.replay
    reference = Decimal(str(replay.intermediate.market_context.mark_price))
    distance, _ = resolve_current_productive_live_29p_adverse_exit_distance_v1(replay)
    stop = derive_protective_stop_price_from_adverse_exit_v0(
        selected_side=resolve_protective_stop_sizing_side_for_live_29p_join_v1(replay),
        reference_price=reference,
        adverse_exit_distance=distance,
    )
    _need(stop is not None, "BTC_TESTNET_ORIGINAL_STOP_REQUIRED")
    meta = produce_current_productive_instrument_quantity_constraints_from_okx_row_v1(
        venue_native_id=bound.venue_native_id,
        instruments_payload=instruments,
        observed_at_as_of=observed_at,
        bound_instrument_id=bound.instrument_id,
    )
    _need(meta.produced and meta.constraints is not None, "BTC_TESTNET_NATIVE_METADATA_REQUIRED")
    money_args = dict(
        decision_epoch=replay.intermediate.market_context.decision_time,
        observed_at=observed_at,
        fresh_pretrade_get_status="TRUSTED_PRESENT",
        native_reference_price=reference,
        native_protective_stop_price=stop,
        instruments_payload=instruments,
        venue_native_id=bound.venue_native_id,
        index_tickers_payload=None,
        conversion_pair_instruments_payload=None,
    )
    money = build_capital_risk_sizing_monetary_context_v1(
        **money_args, account_equity_amount=equity, account_equity_currency="USDC"
    )
    source = build_sizing_monetary_source_v1(
        **money_args,
        canonical_instrument_id=bound.instrument_id,
        account_equity_usdc=equity,
        normalization_digest=money.normalization_digest,
    )
    amount, price, protection = crs_operands_from_monetary_context_v1(money)
    context = default_offline_replay_capital_context_v0(
        instrument_id=bound.instrument_id,
        reference_price=price,
        protective_stop_price=protection,
        account_equity=amount,
        scope_capital_limit=min(amount, policy.per_entry_notional_limit),
        per_trade_risk_limit=amount,
        total_capital_limit=min(amount, policy.aggregate_reserved_notional_limit),
        daily_loss_remaining_budget=amount,
        instrument=meta.constraints,
        config_digest=source_digest,
        capital_risk_mode="OFFLINE_TESTNET_ACCOUNT_BOUND",
    )
    sizing, reasons = build_capital_risk_sizing_input_from_decision_v0(
        decision=replay.evidence, capital_context=context
    )
    _need(sizing is not None, "BTC_TESTNET_SIZING_INPUT_REQUIRED:" + ",".join(reasons))
    return sizing, source


def require_fixture_journal_source_v1(owner, *, checksum, slot, decision, cycle, evaluated_at):
    """Verify the fixture journal and its original input before honoring a replay clock."""
    capture = _read_fixture_capture(owner, checksum, slot, decision, cycle)
    _need(capture["evaluated_at_utc"] == evaluated_at, "BTC_TESTNET_ORIGINAL_SOURCE_MISMATCH")
    return capture


def _read_fixture_capture(owner, checksum, slot, decision, cycle):
    scope = owner.durable_scope_identity_v1()
    root = Path(scope["root"])
    _need(len(root.parents) >= 3, "BTC_TESTNET_ORIGINAL_OWNER_REQUIRED")
    root_dir = root.parents[2]
    lane = demo._demo_lane_root(root_dir)
    profile = root_dir / "btc-lane3-testnet.json"
    _need(
        profile.resolve() == profile
        and json.loads(profile.read_bytes()).get("reservation_fixture") == SOURCE
        and root == lane.parent / "budget-owner" / "owner"
        and slot == demo._LANE,
        "BTC_TESTNET_ISOLATED_FIXTURE_REQUIRED",
    )
    _need(
        isinstance(checksum, str)
        and len(checksum) == 64
        and all(x in "0123456789abcdef" for x in checksum),
        "OFFLINE_TESTNET_SOURCE_DIGEST_INVALID",
    )
    path = lane / "entry-reservation-sources" / (checksum + ".json")
    _need(path.resolve() == path, "BTC_TESTNET_FIXTURE_SOURCE_PATH_INVALID")
    capture = json.loads(path.read_bytes())
    _need(
        cost.digest(capture) == checksum
        and capture["schema"] == "btc_testnet_offline_entry_sources.v2"
        and capture["source"] == SOURCE
        and capture["execution_environment"] == "TESTNET"
        and capture["account"] == scope["account"]
        and capture["lane"] == slot
        and capture["decision"] == decision
        and capture["cycle"] == cycle,
        "BTC_TESTNET_ORIGINAL_SOURCE_MISMATCH",
    )
    return capture


class BtcDemoBudgetOwnerV2(PortfolioCapitalReservationBudgetOwnerV1):
    """Isolated TESTNET owner using the existing journal format, writer and restore."""

    def __init__(
        self,
        *,
        durable_root,
        durable_account_identity,
        durable_mode,
        durable_lane_bindings,
        entry_budget_policy=None,
    ):
        root = Path(durable_root)
        lane = demo._demo_lane_root(root.parents[2])
        _need(
            root == lane.parent / "budget-owner" / "owner"
            and root.resolve() == root
            and set(durable_lane_bindings) == {demo._LANE}
            and durable_lane_bindings[demo._LANE].venue_native_id == demo._NATIVE,
            "BTC_TESTNET_ORIGINAL_OWNER_REQUIRED",
        )
        super().__init__(
            durable_root=root,
            durable_account_identity=durable_account_identity,
            durable_mode=durable_mode,
            durable_lane_bindings=durable_lane_bindings,
            entry_budget_policy=entry_budget_policy,
        )
        # V2 composes original locked recovery and sizing reads in one critical section.
        self._lock = RLock()

    def try_reserve_v1(self, **kwargs):
        return self._closed(("BTC_TESTNET_V2_FIXTURE_RESERVATION_REQUIRED",))

    def recover_at_head_v2(self, *, expected_durable_head, **inputs):
        with self._lock:
            if self._store.head != expected_durable_head:
                return self._closed(("DURABLE_RECOVERY_HEAD_CHANGED",))
            return super().recover_automatically_v1(**inputs)

    def reserve_fixture_v2(
        self,
        *,
        output,
        observation,
        slot_id,
        decision_id,
        cycle_id,
        account_identity,
        sizing_input,
        local_generation,
        monetary_source,
        opening_cost_observation,
        funding_cost_observation,
        native_initial_margin_observation,
        absolute_movement_cost_observation,
        expected_durable_head,
        offline_testnet_source_digest,
        offline_testnet_evaluated_at,
    ):
        from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import (
            ReservationSizingBindingV1,
            request_digest_v1,
        )
        from src.ops.portfolio_capital_reservation_budget_v1.native_initial_margin_v1 import (
            bind_native_initial_margin_v1,
            require_native_margin_locked_v1,
        )
        from src.ops.portfolio_capital_reservation_budget_v1.absolute_movement_cost_v1 import (
            bind_absolute_movement_cost_v1,
        )
        from src.ops.portfolio_capital_reservation_budget_v1.slot_loss_budget_v1 import (
            remaining_loss,
        )

        with self._lock:
            _need(self._store.head == expected_durable_head, "RESERVATION_DURABLE_HEAD_CHANGED")
            _need(
                self._admitted
                and not self._by_key
                and not self._recovery_required
                and not self._storage_failed
                and not self._closed_owner,
                "BTC_TESTNET_FRESH_FIRST_ENTRY_REQUIRED",
            )
            observed = observation_identity_v1(output)
            _need(
                observed == self._observation_id and account_identity == self._account_identity,
                "BTC_TESTNET_WRONG_ACCOUNT",
            )
            try:
                capture = require_fixture_journal_source_v1(
                    self,
                    checksum=offline_testnet_source_digest,
                    slot=slot_id,
                    decision=decision_id,
                    cycle=cycle_id,
                    evaluated_at=offline_testnet_evaluated_at,
                )
            except (KeyError, OSError, ValueError, TypeError) as exc:
                raise ValueError("BTC_TESTNET_ORIGINAL_JOURNAL_SOURCE_REQUIRED") from exc
            _need(
                capture["bound"] == self._lane_bindings[slot_id]["bound"]
                and capture["policy_digest"] == self._entry_budget_policy.digest_v1()
                and capture["decision_outcome"] == sizing_input.decision_outcome
                and capture["bound"]["instrument_id"] == sizing_input.instrument_id
                and decision_id == sizing_input.decision_id
                and capture["sources"]["funding"]
                == json.loads(funding_cost_observation.source_json)
                and json.loads(native_initial_margin_observation.sources_json)
                == {key: capture["sources"][key] for key in ("balance", "leverage")}
                and json.loads(opening_cost_observation.sources_json)
                == {
                    key: capture["sources"][key]
                    for key in ("account", "fees", "book", "instruments")
                },
                "BTC_TESTNET_ORIGINAL_SOURCE_MISMATCH",
            )
            _need(
                self.local_commitment_readback_v1().generation_digest == local_generation,
                "LOCAL_COMMITMENT_GENERATION_CHANGED_BEFORE_RESERVE",
            )
            applied = apply_capital_context_facts_v1(
                sizing_input, capital_context_facts_v1(self, slot_id=slot_id)
            )
            decision = evaluate_capital_risk_sizing_v1(applied)
            _need(decision.outcome is CapitalRiskSizingOutcome.PASS, "BTC_TESTNET_SIZING_DENIED")
            args = dict(
                applied_input=applied,
                decision=decision,
                monetary_source=monetary_source,
                evaluated_at_utc=offline_testnet_evaluated_at,
            )
            opening = cost.bind_entry_execution_cost_v1(
                opening_cost_observation,
                account_identity=account_identity,
                slot_id=slot_id,
                cycle_id=cycle_id,
                **args,
            )
            close = cost.bind_closing_execution_cost_v1(opening, **args)
            funding = cost.bind_next_funding_cost_v1(
                funding_cost_observation, entry_binding=opening, close_binding=close, **args
            )
            native = bind_native_initial_margin_v1(
                native_initial_margin_observation,
                original_margin=observation,
                entry_binding=opening,
                **args,
            )
            sizing = ReservationSizingBindingV1(
                request_digest=request_digest_v1(sizing_input),
                applied_input=applied,
                decision=decision,
                monetary_source=monetary_source,
                entry_cost_binding=opening,
                close_cost_binding=close,
                funding_cost_binding=funding,
                native_initial_margin_binding=native,
                offline_testnet_source_digest=offline_testnet_source_digest,
            )
            movement = bind_absolute_movement_cost_v1(
                absolute_movement_cost_observation,
                sizing=sizing,
                evaluated_at_utc=offline_testnet_evaluated_at,
            )
            sizing = ReservationSizingBindingV1.from_dict_v1(
                replace(sizing, absolute_movement_cost_binding=movement).to_dict_v1()
            )
            amount = decision.canonical_position_sizing.resulting_notional
            sizing.validate_v1(amount=amount, decision_id=decision_id)
            require_native_margin_locked_v1(
                self, sizing, evaluated_at_utc=offline_testnet_evaluated_at
            )
            closing_and_funding = cost.reserved_closing_cost_v1(
                sizing
            ) + cost.reserved_funding_cost_v1(sizing)
            opening_cost = Decimal(json.loads(opening.receipt_json)["total_opening_cost_usdc"])
            denial = self._entry_budget_denial_locked(slot_id, amount)
            _need(not denial, denial)
            _need(
                decision.post_sizing_risk.resulting_max_loss + opening_cost + closing_and_funding
                <= remaining_loss(self, slot_id),
                "TEST_SLOT_REMAINING_LOSS_BUDGET_EXCEEDED",
            )
            _need(
                amount + cost.reserved_opening_fee_v1(sizing) + closing_and_funding
                <= min(self._budget, applied.total_capital_limit, demo._BUDGET_USDC),
                "ENTRY_COST_CAPITAL_WITH_FEES_EXCEEDED",
            )
            key = _reservation_key(
                slot_id=slot_id, decision_id=decision_id, cycle_id=cycle_id, observation_id=observed
            )
            hold = CapitalReservationV1(
                ReservationId(key),
                SlotId(slot_id),
                decision_id,
                cycle_id,
                observed,
                amount,
                ReservationStateV1.RESERVED,
                ("REQUESTED", "RESERVED"),
                "",
            )
            self._by_key[key] = hold
            self._by_id[key] = key
            self._reservation_bindings[key] = dict(self._lane_bindings[slot_id])
            self._sizing_bindings[key] = sizing
            return self._result_locked(
                disposition=ReserveDispositionV1.ADMITTED,
                reservation=hold,
                reason_codes=("BTC_TESTNET_OFFLINE_RESERVED",),
                mutated=True,
            )


def _reserve_fixture_entry_v1(host, cycle, *, sources, movement_input, expected_revision, clock):
    """Called under the original Core entry lock. All nine GETs are in-memory fixtures."""
    budget = host.budget
    lane = demo._demo_lane_root(budget.root)
    profile_path = budget.root / "btc-lane3-testnet.json"
    reconciliation_root = lane.parent / "budget-owner" / "reconciliation"
    _need(
        profile_path.resolve() == profile_path
        and reconciliation_root.resolve() == reconciliation_root,
        "BTC_TESTNET_FIXTURE_SOURCE_PATH_INVALID",
    )
    profile = json.loads(profile_path.read_bytes())
    _need(profile.get("reservation_fixture") == SOURCE, "BTC_TESTNET_ISOLATED_FIXTURE_REQUIRED")
    owner, bound, account = budget.owner, budget.bound, budget.account
    _need(
        owner.durable_scope_identity_v1()
        == {"root": str(lane.parent / "budget-owner" / "owner"), "account": account}
        and owner.slot_account_binding_matches_v1(
            slot_id=demo._LANE, instrument_id=bound.instrument_id, account_identity=account
        ),
        "BTC_TESTNET_ORIGINAL_OWNER_REQUIRED",
    )
    _need(type(owner) is BtcDemoBudgetOwnerV2, "BTC_TESTNET_V2_OWNER_REQUIRED")
    policy = owner.entry_budget_policy_v1()
    _need(
        policy is not None
        and policy.allowed_slot_ids == (demo._LANE,)
        and policy.require_usdc_settlement
        and policy.require_native_initial_margin
        and policy.require_opening_execution_costs
        and policy.require_closing_execution_costs
        and policy.require_next_funding_costs
        and policy.require_absolute_movement_cost_cover
        and not policy.require_original_public_movement_facts
        and not getattr(policy, "require_xperp_liquidation_projection", False)
        and policy.aggregate_reserved_notional_limit
        == policy.per_slot_reserved_notional_limit
        == policy.per_entry_notional_limit
        == demo._BUDGET_USDC,
        "BTC_TESTNET_ORIGINAL_SLOT_POLICY_REQUIRED",
    )
    _need(
        budget.budget_revision_ref_v1() == expected_revision
        and owner.stored_reservation_count_v1() == 0,
        "BTC_TESTNET_FRESH_FIRST_ENTRY_REQUIRED",
    )
    epoch = cycle.replay.intermediate.market_context.decision_time
    now = clock()
    # Detach mutable caller-owned payloads before validating, hashing or storing.
    rows = deepcopy(sources)
    config = _current_sources(rows, account=account, epoch=epoch, cycle_id=cycle.cycle_id, now=now)
    margin, output = _capital(rows, account=account, epoch=epoch, now=now, config=config)
    stamp = datetime.fromisoformat(rows["positions"].acquired_at_utc).timestamp()
    observed = PortfolioTruthSnapshotV1(
        source_id=SOURCE,
        event_time_unix=stamp,
        wall_time_unix=stamp,
        max_age_seconds=acquisition.NUMERIC_EQUITY_TTL_SECONDS,
    )
    persisted = reconciliation_root / PORTFOLIO_STATE_FILENAME
    _need(
        persisted.resolve() == persisted and persisted.is_file(),
        "BTC_TESTNET_ORIGINAL_RECONCILIATION_STATE_REQUIRED",
    )
    gate = run_productive_reconciliation_startup_gate_v1(
        state_root=reconciliation_root,
        require_persisted_present=True,
        observed=observed,
        session_id=host.writer_session_id,
        repository_sha=host.repository_sha,
        now_unix=datetime.fromisoformat(now).timestamp(),
    )
    _need(
        gate.ok and gate.classification.value == "MATCH",
        "BTC_TESTNET_ORIGINAL_RECONCILIATION_MATCH_REQUIRED",
    )
    base = dict(
        bound_instrument=bound, decision_epoch=epoch, cycle_id=cycle.cycle_id, evaluated_at_utc=now
    )
    opening = cost.EntryExecutionCostObservationV1.capture_v1(
        **base,
        account_identity=account,
        sources={k: rows[k] for k in ("account", "instruments", "fees", "book")},
    )
    native = NativeInitialMarginObservationV1.capture_v1(
        sources={k: rows[k] for k in ("balance", "leverage")},
        opening_observation=opening,
        evaluated_at_utc=now,
    )
    funding = cost.FundingCostObservationV1.capture_v1(**base, source=rows["funding"])
    movement = AbsoluteMovementCostObservationV1.capture_v1(
        instrument_raw_input=movement_input, opening_observation=opening, evaluated_at_utc=now
    )
    finished = clock()
    acquisition.acquisition_age_seconds_v1(acquired_at_utc=now, now_utc=finished)
    acquisition.acquisition_age_seconds_v1(acquired_at_utc=epoch, now_utc=finished)
    capture = dict(
        schema="btc_testnet_offline_entry_sources.v2",
        evaluated_at_utc=finished,
        execution_environment="TESTNET",
        source=SOURCE,
        account=account,
        lane=demo._LANE,
        bound=bound.to_dict(),
        decision=cycle.replay.evidence.decision_id,
        cycle=cycle.cycle_id,
        decision_epoch=epoch,
        decision_outcome=cycle.decision_outcome,
        parent_revision=list(expected_revision),
        policy_digest=policy.digest_v1(),
        sources={k: asdict(v) for k, v in rows.items()},
        inventory_digest=observed.digest(),
        reconciliation_evidence=gate.evidence.to_dict(),
    )
    checksum = cost.digest(capture)
    sizing, monetary = _sizing(
        cycle,
        bound,
        rows["instruments"].payload,
        Decimal(output.value),
        margin.observed_at_as_of,
        policy,
        checksum,
    )
    folder = lane / "entry-reservation-sources"
    _need(folder.resolve() == folder, "BTC_TESTNET_FIXTURE_SOURCE_PATH_INVALID")
    path = folder / (checksum + ".json")
    _need(path.resolve() == path, "BTC_TESTNET_FIXTURE_SOURCE_PATH_INVALID")
    immutable_json_v1(path, capture)
    recovered = owner.recover_at_head_v2(
        output=output,
        reconciliation=gate,
        observed=observed,
        lane_bindings={demo._LANE: bound},
        now_unix=datetime.fromisoformat(finished).timestamp(),
        capital_max_age_seconds=acquisition.NUMERIC_EQUITY_TTL_SECONDS,
        expected_durable_head=expected_revision[1],
    )
    _need(recovered.disposition is ReserveDispositionV1.ADMITTED, ",".join(recovered.reason_codes))
    seq, head = budget.budget_revision_ref_v1()
    _need(seq == expected_revision[0] + 1, "BTC_TESTNET_RECOVERY_REVISION_CHANGED")
    local = owner.local_commitment_readback_v1()
    generation = owner.require_local_commitment_readback_v1(local, account_identity=account)
    result = owner.reserve_fixture_v2(
        output=output,
        observation=margin,
        slot_id=demo._LANE,
        decision_id=capture["decision"],
        cycle_id=cycle.cycle_id,
        account_identity=account,
        sizing_input=sizing,
        local_generation=generation,
        monetary_source=monetary,
        opening_cost_observation=opening,
        funding_cost_observation=funding,
        native_initial_margin_observation=native,
        absolute_movement_cost_observation=movement,
        expected_durable_head=head,
        offline_testnet_source_digest=checksum,
        offline_testnet_evaluated_at=finished,
    )
    _need(result.disposition is ReserveDispositionV1.ADMITTED, ",".join(result.reason_codes))
    return result.reservation.reservation_id, checksum


def _book_fixture_entry_v1(budget, cycle, rid, revision):
    """Replay the reserved market entry at its archived book and signed taker rate."""
    from src.execution.paper.futures_accounting import notional_value
    from src.governance.canonical_order_intent_v1 import (
        CanonicalOrderIntentBuildInputV1,
        build_canonical_order_intent_v1,
    )

    owner = budget.owner
    _need(type(owner) is BtcDemoBudgetOwnerV2, "BTC_TESTNET_V2_OWNER_REQUIRED")
    with owner._lock:
        _need(budget.budget_revision_ref_v1() == revision, "BTC_DEMO_BUDGET_HEAD_CHANGED")
        key = owner._by_id.get(rid)
        _need(key is not None, "BTC_TESTNET_ORIGINAL_RESERVATION_REQUIRED")
        hold = owner._by_key[key]
        sizing = owner._sizing_bindings[key]
        receipt = sizing.entry_cost_binding.validate_v1(
            monetary_source=sizing.monetary_source,
            applied_input=sizing.applied_input,
            decision=sizing.decision,
        )
        _need(
            hold.state.value == "RESERVED"
            and rid not in owner.execution_links_v1()
            and hold.decision_id == cycle.replay.evidence.decision_id
            and hold.cycle_id == cycle.cycle_id
            and receipt["native_id"] == budget.bound.venue_native_id
            and receipt["quote_currency"] == "USDC",
            "BTC_TESTNET_ORIGINAL_USDC_FIXTURE_HOLD_REQUIRED",
        )
        capture = _read_fixture_capture(
            owner,
            sizing.offline_testnet_source_digest,
            str(hold.slot_id),
            hold.decision_id,
            hold.cycle_id,
        )
        _need(
            revision[0] == capture["parent_revision"][0] + 2,
            "BTC_TESTNET_ORIGINAL_RESERVATION_REVISION_REQUIRED",
        )
        side = receipt["side"]
        intent = build_canonical_order_intent_v1(
            CanonicalOrderIntentBuildInputV1(
                sizing_input=sizing.applied_input,
                sizing_decision=sizing.decision,
                intent_id="btc-offline-entry:" + rid,
                trading_epoch=capture["decision_epoch"],
                canonical_trading_logic_version="integrated_offline_trading_logic_replay_v1",
                intent_action=cycle.decision_outcome.upper(),
                policy_digest=capture["policy_digest"],
                order_type_policy="MARKET_ONLY",
                price_policy="EXPLICIT_NONE",
                time_in_force_policy="GTC",
                max_slippage_policy="ARCHIVED_BOOK_DEPTH_ONLY",
                expected_position_side=side,
                current_reconciled_exposure=Decimal(0),
            )
        ).intent
        _need(
            intent is not None and intent.side == side and not intent.submission_authorized,
            "BTC_FIXTURE_INTENT_REQUIRED",
        )
        book = capture["sources"]["book"]["payload"]["data"][0]
        remaining = intent.quantity
        notional = Decimal(0)
        fills = []
        rate = Decimal(receipt["taker_rate"])
        multiplier = sizing.applied_input.instrument.contract_multiplier
        for price, size, *_ in book["asks" if side == "LONG" else "bids"]:
            quantity = min(remaining, Decimal(size))
            value = notional_value(
                mark_price=Decimal(price), qty=quantity, contract_size=multiplier
            )
            fills.append(
                dict(price=price, contracts=str(quantity), signed_fee_usdc=str(value * rate))
            )
            notional += value
            remaining -= quantity
            if remaining == 0:
                break
        _need(
            remaining == 0
            and notional / multiplier / intent.quantity == Decimal(receipt["book_vwap"]),
            "BTC_FIXTURE_DEPTH_MISMATCH",
        )
        fee = sum(Decimal(fill["signed_fee_usdc"]) for fill in fills)
        record = dict(
            schema="btc_offline_reserved_entry_fill.v1",
            source=SOURCE,
            authority="NONE",
            execution_model="ARCHIVED_BOOK_REPLAY",
            account=budget.account,
            lane=demo._LANE,
            native_id=receipt["native_id"],
            instrument_id=intent.instrument_id,
            reservation_id=rid,
            revision=list(revision),
            replay_as_of=capture["evaluated_at_utc"],
            book_observed_at=capture["sources"]["book"]["acquired_at_utc"],
            source_digest=sizing.offline_testnet_source_digest,
            decision_id=intent.decision_id,
            cycle=hold.cycle_id,
            intent_digest=intent.semantic_digest,
            side=side,
            contracts=str(intent.quantity),
            average_price=receipt["book_vwap"],
            fills=fills,
            signed_opening_fee_usdc=str(fee),
            fixture_budget_after_fee_usdc=str(demo._BUDGET_USDC + fee),
        )
        lane = demo._demo_lane_root(budget.root)
        path = lane / "simulated-reserved-entries" / (cost.digest(rid) + ".json")
        _need(path.resolve() == path, "BTC_TESTNET_FIXTURE_SOURCE_PATH_INVALID")
        immutable_json_v1(path, record)
        return json.loads(path.read_bytes())
