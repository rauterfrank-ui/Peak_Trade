"""Offline first-entry reservation using the original Slot 3 TESTNET journal.

The input consists of synthetic, decision-bound GET receipts. No transport,
credential or execution port is available here. The separate signed Demo
inspection is not an input to this fixture.
"""

from copy import deepcopy
from dataclasses import asdict
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
    _reserve_from_admitted_capital_v1,
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
        scope_capital_limit=amount,
        per_trade_risk_limit=amount,
        total_capital_limit=amount,
        daily_loss_remaining_budget=amount,
        instrument=meta.constraints,
        config_digest=source_digest,
        capital_risk_mode="OFFLINE_TESTNET_ACCOUNT_BOUND",
    )
    sizing, reasons = build_capital_risk_sizing_input_from_decision_v0(
        decision=replay.evidence, capital_context=policy.constrain_offline_testnet_entry_v1(context)
    )
    _need(sizing is not None, "BTC_TESTNET_SIZING_INPUT_REQUIRED:" + ",".join(reasons))
    return sizing, source


def require_fixture_journal_source_v1(owner, *, checksum, slot, decision, cycle):
    """Verify the fixture journal and its original input before honoring a replay clock."""
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
        and capture["schema"] == "btc_testnet_offline_entry_sources.v1"
        and capture["source"] == SOURCE
        and capture["execution_environment"] == "TESTNET"
        and capture["account"] == scope["account"]
        and capture["lane"] == slot
        and capture["decision"] == decision
        and capture["cycle"] == cycle,
        "BTC_TESTNET_ORIGINAL_SOURCE_MISMATCH",
    )
    return capture


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
    capture = dict(
        schema="btc_testnet_offline_entry_sources.v1",
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
    recovered = owner.recover_automatically_v1(
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
    folder = lane / "entry-reservation-sources"
    _need(folder.resolve() == folder, "BTC_TESTNET_FIXTURE_SOURCE_PATH_INVALID")
    path = folder / (checksum + ".json")
    _need(path.resolve() == path, "BTC_TESTNET_FIXTURE_SOURCE_PATH_INVALID")
    immutable_json_v1(path, capture)
    local = owner.local_commitment_readback_v1()
    generation = owner.require_local_commitment_readback_v1(local, account_identity=account)
    result = _reserve_from_admitted_capital_v1(
        owner,
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
