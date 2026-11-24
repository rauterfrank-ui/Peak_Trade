"""Bind original BTC Demo GETs to the original TESTNET budget writer.

This adapter performs no GET and sends no order. Its caller owns the Core lock
and acquires the decision-bound batch through the scoped Demo reader.
"""

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from urllib.parse import urlencode

from src.ops import btc_demo_lane3_v2 as demo
from src.ops.btc_demo_budget_owner_v3 import BtcDemoBudgetOwnerV3
from src.ops.btc_demo_entry_financial_inputs_v1 import (
    build_btc_demo_capital_inputs_v1,
    build_btc_demo_sizing_inputs_v1,
)
from src.ops.full_core_live_path_composition_root_v1 import pretrade_acquisition_v1 as acquisition
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    immutable_json_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as cost
from src.ops.portfolio_capital_reservation_budget_v1.absolute_movement_cost_v1 import (
    AbsoluteMovementCostObservationV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.native_initial_margin_v1 import (
    NativeInitialMarginObservationV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    ReserveDispositionV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import PortfolioTruthSnapshotV1
from src.ops.productive_reconciliation_runtime_binding_v1.startup_gate_v1 import (
    run_productive_reconciliation_startup_gate_v1,
)


def _need(condition, reason):
    if not condition:
        raise ValueError(reason)


def _validate_sources(batch, *, budget, cycle, now):
    queries = demo.BTC_DEMO_PRETRADE_QUERIES_V1
    rows = deepcopy(batch["sources"])
    originals = batch["original_bodies_hex"]
    _need(rows.keys() == originals.keys() == queries.keys(), "BTC_DEMO_ORIGINAL_BATCH_REQUIRED")
    epoch = cycle.replay.intermediate.market_context.decision_time
    context = cost.canonical(dict(decision_epoch=epoch, cycle_id=cycle.cycle_id))
    _need(
        batch["execution_environment"] == "TESTNET"
        and batch["lane_id"] == demo._LANE
        and batch["authority"] == "NONE"
        and batch["instrument_id"] == budget.bound.instrument_id
        and batch["decision_id"] == cycle.replay.evidence.decision_id
        and batch["decision_epoch"] == epoch
        and batch["cycle_id"] == cycle.cycle_id,
        "BTC_DEMO_ORIGINAL_ENTRY_BATCH_MISMATCH",
    )
    for name, (path, query) in queries.items():
        source = rows[name]
        body = bytes.fromhex(originals[name])
        _need(
            type(source) is cost.FreshPretradeGetTransportResultV1
            and source.endpoint == path + ("?" + urlencode(query) if query else "")
            and source.get_performed is True
            and source.method == "GET"
            and source.http_status == 200
            and source.auth_header_sent is (name not in {"book", "funding"})
            and source.transport_class == "OKX_EEA_DEMO_READ_ONLY_GET"
            and source.venue_live_contact is True
            and source.historical_reuse is False
            and not source.error_class
            and source.data_safety_source_kind is None
            and source.pretrade_decision_id == context
            and source.body_sha256 == sha256(body).hexdigest()
            and source.payload == json.loads(body),
            "BTC_DEMO_ORIGINAL_SOURCE_MISMATCH:" + name,
        )
        acquisition.acquisition_age_seconds_v1(
            acquired_at_utc=epoch, now_utc=source.acquired_at_utc
        )
        acquisition.acquisition_age_seconds_v1(acquired_at_utc=source.acquired_at_utc, now_utc=now)
        cost._rows(source.payload)
    account = demo._only(rows["account"].payload)
    _need(account.get("uid") == budget.account, "BTC_DEMO_ACCOUNT_MISMATCH")
    _need(account.get("posMode") == "net_mode", "BTC_DEMO_NET_POSITION_MODE_REQUIRED")
    _need(
        demo._only(rows["balance"].payload).get("uid", budget.account) == budget.account,
        "BTC_DEMO_BALANCE_ACCOUNT_MISMATCH",
    )
    instrument = demo._only(rows["instruments"].payload)
    _need(
        instrument.get("instId") == budget.bound.venue_native_id
        and instrument.get("state") == "live",
        "BTC_DEMO_ACCOUNT_INSTRUMENT_UNAVAILABLE",
    )
    # Reuse the cost owner's account-specific USDC contract admission.
    cost._instrument_source_path_v1(rows["instruments"], instrument, account)
    for name in ("positions", "pending"):
        _need(
            rows[name].payload["data"] == [],
            "BTC_DEMO_FIRST_ENTRY_REQUIRES_FLAT_INVENTORY",
        )
    return rows, account


def reserve_btc_demo_entry_v1(host, *, cycle, batch, movement_input, clock):
    budget = host.budget
    owner, bound = budget.owner, budget.bound
    _need(
        type(owner) is BtcDemoBudgetOwnerV3 and owner.execution_environment_v1() == "TESTNET",
        "BTC_DEMO_TESTNET_JOURNAL_REQUIRED",
    )
    _need(
        budget.budget_revision_ref_v1() == batch["budget_revision"]
        and owner.stored_reservation_count_v1() == 0,
        "BTC_DEMO_FRESH_FIRST_ENTRY_REQUIRED",
    )
    policy = owner.entry_budget_policy_v1()
    _need(
        policy is not None
        and policy.allowed_slot_ids == (demo._LANE,)
        and policy.aggregate_reserved_notional_limit
        == policy.per_slot_reserved_notional_limit
        == policy.per_entry_notional_limit
        == demo._BUDGET_USDC
        and policy.require_usdc_settlement
        and policy.require_native_initial_margin
        and policy.require_opening_execution_costs
        and policy.require_closing_execution_costs
        and policy.require_next_funding_costs
        and policy.require_absolute_movement_cost_cover,
        "BTC_DEMO_BOUNDED_COST_POLICY_REQUIRED",
    )
    declaration = owner.risk_snapshot_v1()["state"].get("slot_capital_allocation")
    _need(
        declaration is not None
        and declaration["schema"] == "slot_capital_allocation.v1"
        and declaration["declaration"]["account_identity"] == budget.account
        and declaration["declaration"]["initial_usdc_by_slot"]
        == {demo._LANE: str(demo._BUDGET_USDC)},
        "BTC_DEMO_ONCE_FUNDED_SLOT_REQUIRED",
    )
    epoch = cycle.replay.intermediate.market_context.decision_time
    now = datetime.fromtimestamp(clock(), timezone.utc).isoformat()
    rows, account = _validate_sources(batch, budget=budget, cycle=cycle, now=now)
    margin, output, _, _ = build_btc_demo_capital_inputs_v1(
        rows, account=budget.account, epoch=epoch, now=now, config=account
    )
    lane = demo._demo_lane_root(budget.root)
    stamp = datetime.fromisoformat(rows["positions"].acquired_at_utc).timestamp()
    observed = PortfolioTruthSnapshotV1(
        source_id="OKX_EEA_DEMO_READ_ONLY_GET",
        event_time_unix=stamp,
        wall_time_unix=stamp,
        max_age_seconds=acquisition.NUMERIC_EQUITY_TTL_SECONDS,
    )
    reconciliation = run_productive_reconciliation_startup_gate_v1(
        state_root=lane.parent / "budget-owner" / "reconciliation",
        # Only this empty first-entry journal may establish its initial baseline.
        require_persisted_present=False,
        observed=observed,
        session_id=host.writer_session_id,
        repository_sha=host.repository_sha,
        now_unix=datetime.fromisoformat(now).timestamp(),
    )
    _need(reconciliation.ok, "BTC_DEMO_FIRST_ENTRY_RECONCILIATION_REQUIRED")
    base = dict(
        bound_instrument=bound,
        decision_epoch=epoch,
        cycle_id=cycle.cycle_id,
        evaluated_at_utc=now,
    )
    opening = cost.EntryExecutionCostObservationV1.capture_v1(
        **base,
        account_identity=budget.account,
        sources={key: rows[key] for key in ("account", "instruments", "fees", "book")},
    )
    native = NativeInitialMarginObservationV1.capture_v1(
        sources={key: rows[key] for key in ("balance", "leverage")},
        opening_observation=opening,
        evaluated_at_utc=now,
    )
    funding = cost.FundingCostObservationV1.capture_v1(**base, source=rows["funding"])
    movement = AbsoluteMovementCostObservationV1.capture_v1(
        instrument_raw_input=movement_input,
        opening_observation=opening,
        evaluated_at_utc=now,
    )
    capture = dict(
        schema="btc_demo_entry_sources.v1",
        execution_environment="TESTNET",
        native_price_currency="USD",
        contract_settlement_sources_json=cost.canonical(
            {key: asdict(rows[key]) for key in ("account", "instruments")}
        ),
        capital_risk_mode="TESTNET_ACCOUNT_BOUND",
        decision_id=cycle.replay.evidence.decision_id,
        cycle_id=cycle.cycle_id,
        account_identity=budget.account,
        bound=bound.to_dict(),
        decision_epoch=epoch,
        budget_parent_revision=list(batch["budget_revision"]),
        policy_digest=policy.digest_v1(),
        evaluated_at_utc=now,
        sources={key: asdict(value) for key, value in rows.items()},
        original_bodies_hex=deepcopy(batch["original_bodies_hex"]),
    )
    checksum = cost.digest(capture)
    sizing, monetary = build_btc_demo_sizing_inputs_v1(
        cycle,
        bound,
        rows["instruments"].payload,
        Decimal(output.value),
        margin.observed_at_as_of,
        policy,
        checksum,
        capital_risk_mode="TESTNET_ACCOUNT_BOUND",
        native_price_currency="USD",
        contract_settlement_sources_json=capture["contract_settlement_sources_json"],
    )
    finished = datetime.fromtimestamp(clock(), timezone.utc).isoformat()
    acquisition.acquisition_age_seconds_v1(acquired_at_utc=now, now_utc=finished)
    acquisition.acquisition_age_seconds_v1(acquired_at_utc=epoch, now_utc=finished)
    for source in rows.values():
        acquisition.acquisition_age_seconds_v1(
            acquired_at_utc=source.acquired_at_utc,
            now_utc=finished,
        )
    folder = lane / "entry-reservation-sources"
    _need(folder.resolve() == folder, "BTC_DEMO_SOURCE_PATH_INVALID")
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    immutable_json_v1(folder / (checksum + ".json"), capture)
    _need(
        budget.budget_revision_ref_v1() == batch["budget_revision"],
        "BTC_DEMO_ENTRY_BUDGET_HEAD_CHANGED",
    )
    recovered = owner.recover_automatically_v1(
        output=output,
        observed=observed,
        reconciliation=reconciliation,
        lane_bindings={demo._LANE: bound},
        now_unix=datetime.fromisoformat(finished).timestamp(),
        capital_max_age_seconds=acquisition.NUMERIC_EQUITY_TTL_SECONDS,
    )
    _need(recovered.disposition is ReserveDispositionV1.ADMITTED, ",".join(recovered.reason_codes))
    result = owner.reserve_demo_entry_v3(
        output=output,
        observation=margin,
        slot_id=demo._LANE,
        decision_id=cycle.replay.evidence.decision_id,
        cycle_id=cycle.cycle_id,
        account_identity=budget.account,
        sizing_input=sizing,
        monetary_source=monetary,
        opening_cost_observation=opening,
        funding_cost_observation=funding,
        native_initial_margin_observation=native,
        absolute_movement_cost_observation=movement,
        expected_durable_head=budget.budget_revision_ref_v1()[1],
        local_generation=owner.local_commitment_readback_v1().generation_digest,
        source_checksum=checksum,
        evaluated_at_utc=finished,
    )
    _need(result.disposition is ReserveDispositionV1.ADMITTED, ",".join(result.reason_codes))
    return result, checksum
