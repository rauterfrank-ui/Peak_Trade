#!/usr/bin/env python3
"""Replay the I17 decision bridge on one sealed mark sequence for both GVEF profiles."""

from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter, deque
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from io import BytesIO
from math import isfinite
import json
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256  # noqa: E402
from scripts.ops.run_research_candidate_shadow_v1 import (  # noqa: E402
    _absolute,
    _clock,
    _head,
    _pair,
    _public_get,
    _raw_rows,
    _reality_gap_policy_window,
)
from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import (  # noqa: E402
    EvaluationReceiptArchiveV1,
)
from src.execution.paper.futures_accounting import (  # noqa: E402
    funding_payment_quote,
    notional_value,
)
from src.experiments.canonical_research_prepared_execution_v1 import (  # noqa: E402
    digest_v1,
    publish_v1,
    read_v1,
)
from src.experiments.offline_ddo_research_cycle_v1 import ResearchGapDimensionV1  # noqa: E402
from src.governance.canonical_order_intent_v1 import (  # noqa: E402
    canonical_order_intent_from_dict,
    validate_canonical_order_intent_v1,
)
from src.ops.bounded_peaktrade_system_composition_v1.paper_episode_outcome_v1 import (  # noqa: E402
    PAPER_PROFILE,
    SIMULATION,
)
from src.ops.integrated_paper_shadow_observation_session_v1.market_data_policy_v1 import (  # noqa: E402
    ObservationMarketTickV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1 import (  # noqa: E402
    verify_wallclock_evidence_bundle_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.candidate_observation_v1 import (  # noqa: E402
    HOUR as HOUR,
    I17CandidatePairV1,
    LAST_ENDPOINT,
    PLAN_SCHEMA,
    PUBLIC_HTTP_HOST as PUBLIC_HTTP_HOST,
    _assert_capture_journal_separate,
    _capture_journal_paths,
    _capture_last_response,
    _capture_scope_path,
    _decision_time_window,
    _last_query,
    _parse_last,
    _read_capture_journal,
    _strategy_binding,
    _utc,
    _validated_last_snapshots,
    candidate_plan_component_v1,
    capture_decision_time_last_v1 as capture_decision_time_last_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (  # noqa: E402
    EXECUTION_CLASS_ANALYTICAL,
    MARKET_TYPE_FUTURES,
    VENUE_OKX,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (  # noqa: E402
    parse_preregistration_contract_v1,
)

from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (  # noqa: E402
    AccountingEngineError,
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.fill_model_v1 import (  # noqa: E402
    build_simulated_fill_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import (  # noqa: E402
    ContractMetadataV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (  # noqa: E402
    _fill_to_dict,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.idempotent_portfolio_v2 import (  # noqa: E402
    IdempotentPortfolioV2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.provenance_v2 import (  # noqa: E402
    make_scoped_id,
    portfolio_state_hash,
)

DECISION_TIME_LAST_SCHEMA = "i17_decision_time_last_captures.v1"


def _i17_manifest_pins(manifest):
    return dict(line.split("  ", 1)[::-1] for line in manifest.decode().splitlines() if line)


def _pinned_i17_file(root, manifest, name):
    pins = _i17_manifest_pins(manifest)
    path = root / name
    if path.is_symlink():
        raise ValueError("I17_COMPARISON_UNSAFE_ORIGINAL_FILE")
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != pins.get(name):
        raise ValueError("I17_COMPARISON_ORIGINAL_LEDGER_CHANGED")
    return raw


def _read_i17_archive(root, instrument, *, require_typed_ddo):
    manifest = (root / "evidence_manifest.sha256").read_bytes()
    check = verify_wallclock_evidence_bundle_v1(evidence_root=root)
    if require_typed_ddo and not check.typed_ddo_requirement_met:
        raise ValueError("I17_COMPARISON_REQUIRES_VERIFIED_TYPED_ARCHIVE")
    if not check.verified or check.incomplete or check.verdict != "PASS":
        raise ValueError("I17_COMPARISON_REQUIRES_COMPLETE_VERIFIED_ARCHIVE")

    def read_rows(name):
        return (
            json.loads(line)
            for line in BytesIO(_pinned_i17_file(root, manifest, name))
            if line.rstrip(b"\r\n")
        )

    def paired_rows():
        previous_decision = None
        ticks = read_rows("market_data_sequence.jsonl")
        cycles = read_rows("bridge_cycle_ledger.jsonl")
        for tick, cycle in zip(ticks, cycles, strict=True):
            timing = cycle["shadow_decision_timing"]
            decided = timing["decision_cycle_ts_unix"]
            if (
                tick["canonical_instrument_id"] != instrument
                or tick["venue_instrument_id"] != instrument
                or cycle["instrument_id"] != instrument
                or timing["market_sequence"] != tick["sequence"]
                or timing["mark_event_ts_unix"] != tick["event_ts_unix"]
                or tick["event_ts_unix"] > tick["receive_ts_unix"]
                or tick["receive_ts_unix"] > decided
                or (previous_decision is not None and decided <= previous_decision)
            ):
                raise ValueError("I17_COMPARISON_TICK_DECISION_MISMATCH")
            previous_decision = decided
            yield decided, tick, cycle

    return manifest, paired_rows()


def _read_i17(root, instrument):
    manifest, rows = _read_i17_archive(root, instrument, require_typed_ddo=True)
    return sha256(manifest).hexdigest(), [
        (decided, tick, cycle["decision_id"]) for decided, tick, cycle in rows
    ]


def _read_i17_scope(root, manifest_sha):
    manifest = (root / "evidence_manifest.sha256").read_bytes()
    if sha256(manifest).hexdigest() != manifest_sha:
        raise ValueError("I17_COMPARISON_ORIGINAL_MANIFEST_CHANGED")
    prereg = parse_preregistration_contract_v1(
        json.loads(_pinned_i17_file(root, manifest, "prereg.json"))
    )
    scope = _pinned_i17_file(root, manifest, "scope_digest.txt").decode().strip()
    if scope != prereg.scope_digest():
        raise ValueError("I17_DECISION_TIME_ORIGINAL_SCOPE_MISMATCH")
    return scope


def _last_source(workspace, query, *, capture_last, fetch=_public_get):
    path = workspace.safe_path_v1("last-candles.json")
    if path.exists() or not capture_last:
        record = read_v1(path)
        return record, _parse_last(record, query)
    record = _capture_last_response(query, fetch=fetch, clock=_clock, requested=_clock())
    frame = _parse_last(record, query)
    publish_v1(path, record)
    return record, frame


def seal_decision_time_last_v1(journal, *, plan, evidence_root):
    """Join the pre-bound capture receipts to their sealed I17 session archive."""
    _assert_capture_journal_separate(journal, evidence_root.resolve())
    manifest_sha, rows = _read_i17(evidence_root, plan["instrument_id"])
    scope = _read_i17_scope(evidence_root, manifest_sha)
    namespace = _capture_scope_path(plan, scope)
    binding = {"plan_digest": namespace.parts[0], "original_i17_scope_digest": scope}
    with journal.lease_v1():
        captures = _read_capture_journal(
            journal, _capture_journal_paths(journal, namespace), binding
        )
        archive = {
            "schema_version": DECISION_TIME_LAST_SCHEMA,
            "original_i17_manifest_sha256": manifest_sha,
            **binding,
            "captures": captures,
        }
        snapshots = _decision_time_last_snapshots(plan, rows, archive, manifest_sha=manifest_sha)
        if snapshots[0][0].timestamp() > rows[0][0]:
            raise ValueError("I17_DECISION_TIME_LAST_NOT_YET_AVAILABLE")
        target = journal.safe_path_v1(namespace / "captures.json")
        publish_v1(target, archive)
        return target


def _decision_time_last_snapshots(plan, rows, archive, *, manifest_sha):
    registered, start, end = _decision_time_window(plan)
    if (
        archive["schema_version"] != DECISION_TIME_LAST_SCHEMA
        or archive["plan_digest"] != digest_v1(plan)
        or archive["original_i17_manifest_sha256"] != manifest_sha
        or not rows
        or not start.timestamp() <= rows[0][0] <= rows[-1][0] < end.timestamp()
    ):
        raise ValueError("I17_DECISION_TIME_WINDOW_OR_PLAN_MISMATCH")

    return _validated_last_snapshots(plan, archive["captures"], registered=registered, end=end)


def _compared_cycles(
    plan, rows, candles, *, identifier, decision_time_last=None, record_simulated_economics=False
):
    pair = I17CandidatePairV1(
        plan,
        session_prefix=f"i17-offline-{identifier[:20]}",
        record_simulated_economics=record_simulated_economics,
    )
    first_received = rows[0][1]["receive_ts_unix"]
    receipt_times = [] if decision_time_last is None else [row[0] for row in decision_time_last]
    for decided, original, decision_id in rows:
        decision_time = datetime.fromtimestamp(decided, timezone.utc)
        close_time = decision_time.replace(minute=0, second=0, microsecond=0)
        candle_input = {}
        if decision_time_last is not None:
            available_index = bisect_right(receipt_times, decision_time) - 1
            if available_index < 0:
                raise ValueError("I17_DECISION_TIME_LAST_NOT_YET_AVAILABLE")
            _, candles, trace = decision_time_last[available_index]
            close_time = candles.index[-1]
            candle_input = {"last_candle_input": trace}
        tick = ObservationMarketTickV1(
            instrument_id=pair.instrument,
            venue=VENUE_OKX,
            market_type=MARKET_TYPE_FUTURES,
            sequence=original["sequence"],
            event_ts_unix=original["event_ts_unix"],
            receive_ts_unix=original["receive_ts_unix"],
            mono_ts=original["receive_ts_unix"] - first_received,
            mid_price=original["mid_price"],
            source="caller_supplied_offline",
        )
        arms = pair.evaluate(tick, decided=decided, close_time=close_time, candles=candles)
        yield {
            "observed_mark_sequence": tick.sequence,
            "historical_decision_id": decision_id,
            "decision_time_utc": decision_time.isoformat(),
            "last_candle_close_utc": close_time.isoformat(),
            **candle_input,
            "arms": arms,
        }


def _compare(plan, rows, candles, *, identifier, decision_time_last=None):
    return list(
        _compared_cycles(
            plan, rows, candles, identifier=identifier, decision_time_last=decision_time_last
        )
    )


def compare_v1(
    workspace,
    *,
    plan,
    evidence_root,
    code_sha,
    capture_last=False,
    verify=False,
    decision_time_archive=None,
):
    manifest_sha, rows = _read_i17(evidence_root, plan["instrument_id"])
    output = workspace.safe_path_v1("result.json")
    with workspace.lease_v1():
        scope = "HISTORICAL_I17_COMPARISON"
        snapshots = None
        if decision_time_archive is None:
            query = _last_query(plan["instrument_id"], rows[-1][0])
            source, candles = _last_source(
                workspace, query, capture_last=capture_last and not verify
            )
            last_received = source["received_at_utc"]
        else:
            if capture_last:
                raise ValueError("I17_DECISION_TIME_PREFLIGHT_REQUIRES_OFFLINE_INPUT")
            scope = "I17_DECISION_TIME_OFFLINE_PREFLIGHT"
            source, candles = decision_time_archive, None
            if "original_i17_scope_digest" in source and source[
                "original_i17_scope_digest"
            ] != _read_i17_scope(evidence_root, manifest_sha):
                raise ValueError("I17_DECISION_TIME_ORIGINAL_SCOPE_MISMATCH")
            snapshots = _decision_time_last_snapshots(plan, rows, source, manifest_sha=manifest_sha)
            last_received = snapshots[-1][0].isoformat()
        binding = {
            "plan_digest": digest_v1(plan),
            "original_i17_manifest_sha256": manifest_sha,
            "last_candle_archive_digest": digest_v1(source),
            "code_sha": code_sha,
        }
        if decision_time_archive is not None and "original_i17_scope_digest" in source:
            binding["original_i17_scope_digest"] = source["original_i17_scope_digest"]
        if output.exists() and not verify:
            saved = read_v1(output)
            if any(saved[key] != value for key, value in binding.items()):
                raise ValueError("I17_COMPARISON_ORIGINAL_BINDING_CHANGED")
            return saved
        cycles = _compare(
            plan, rows, candles, identifier=digest_v1(binding), decision_time_last=snapshots
        )
        results = [(row["arms"]["reference"], row["arms"]["candidate"]) for row in cycles]
        result = {
            "schema_version": "i17_offline_candidate_comparison.v1",
            "authority": "NONE",
            "scope": scope,
            "last_inputs_captured_at_utc": last_received,
            "strategy_id": plan["strategy_id"],
            "strategy_version": plan["strategy_version"],
            "parameters": {
                role: profile["parameters"] for role, profile in plan["profiles"].items()
            },
            **binding,
            "cycle_count": len(cycles),
            "market_observation_classifications": dict(
                Counter(a["market_observation_classification"] for a, _ in results)
            ),
            "typed_volatility_cycles": sum(a["typed_volatility_present"] for a, _ in results),
            "directional_confirmation_cycles": {
                role: sum(
                    row["arms"][role]["directional_confirmation_progress"] is not None
                    for row in cycles
                )
                for role in plan["profiles"]
            },
            "suitability_cycles": {
                "reference": sum(bool(a["suitability"]) for a, _ in results),
                "candidate": sum(bool(b["suitability"]) for _, b in results),
            },
            "different_strategy_states": sum(
                a["material"]["cycle_signal_value"] != b["material"]["cycle_signal_value"]
                for a, b in results
            ),
            "different_suitability_cycles": sum(
                a["suitability"] != b["suitability"] for a, b in results
            ),
            "different_decision_cycles": sum(
                (a["decision_outcome"], a["selected_side"], a["intended_action"])
                != (b["decision_outcome"], b["selected_side"], b["intended_action"])
                for a, b in results
            ),
            "cycles": cycles,
        }
        if verify:
            if digest_v1(read_v1(output)) != digest_v1(result):
                raise ValueError("I17_COMPARISON_READBACK_MISMATCH")
        else:
            publish_v1(output, result)
        return read_v1(output)


def _replay_simulated_arm(portfolio, *, arm, packet, session, index, instrument, mark):
    if "simulated_economics" not in arm:
        raise ValueError("I17_HOST_SIMULATED_ECONOMICS_NOT_RECORDED")
    recorded = arm["simulated_economics"]
    action = recorded["intended_action"]
    snapshot = portfolio.model.snapshot()
    cycle_id = make_scoped_id("cycle", session, index)
    decision_id = make_scoped_id("decision", session, cycle_id, index)
    risk_id = make_scoped_id("risk", decision_id, arm["safety_result"])
    intent_id = make_scoped_id("intent", risk_id, action["feature_digest"])
    if (
        arm["artifact_digest"] != packet
        or arm["material"]["instrument_id"] != instrument
        or arm["material"]["trading_epoch"] != index
        or recorded["execution_class"] != EXECUTION_CLASS_ANALYTICAL
        or recorded["cycle_id"] != cycle_id
        or action["session_id"] != session
        or action["cycle_id"] != cycle_id
        or action["decision_id"] != decision_id
        or action["risk_decision_id"] != risk_id
        or action["intent_id"] != intent_id
        or action["intent_action"] != arm["intended_action"]
        or any(
            recorded["portfolio_model"][key] != snapshot[key]
            for key in ("model_id", "model_version", "model_digest", "params")
        )
        or recorded["portfolio_state_before_hash"] != portfolio_state_hash(snapshot)
    ):
        raise ValueError("I17_HOST_SIMULATED_DECISION_OR_MODEL_MISMATCH")

    side = action["intended_side"]
    quantity = Decimal(action["intended_quantity"])
    if not quantity.is_finite() or (side not in {"BUY", "SELL"} and quantity != 0):
        raise ValueError("I17_HOST_INVALID_SIMULATED_QUANTITY")
    fill_id = (
        make_scoped_id("fill", intent_id, mark, quantity, side) if side in {"BUY", "SELL"} else None
    )
    fill = portfolio.apply_intended_action(
        instrument_id=instrument,
        side=side,
        quantity=quantity,
        mark_price=Decimal(str(mark)),
        intent_id=intent_id,
        fill_id=fill_id,
    )
    after = portfolio.model.snapshot()
    after_hash = portfolio_state_hash(after)
    saved_fill = recorded["fill"]
    if fill is None:
        if saved_fill is not None:
            raise ValueError("I17_HOST_SIMULATED_FILL_MISMATCH")
    else:
        expected_fill = {
            **_fill_to_dict(fill),
            "session_id": session,
            "cycle_id": cycle_id,
            "decision_id": decision_id,
            "risk_decision_id": risk_id,
            "intent_id": intent_id,
            "fill_id": fill_id,
            "cycle_index": index,
            "trading_epoch": index,
            "portfolio_state_before_hash": recorded["portfolio_state_before_hash"],
            "portfolio_state_after_hash": after_hash,
        }
        if saved_fill is None or any(
            saved_fill[key] != value for key, value in expected_fill.items()
        ):
            raise ValueError("I17_HOST_SIMULATED_FILL_MISMATCH")
    if (
        recorded["portfolio_after"] != after["state"]
        or recorded["portfolio_state_after_hash"] != after_hash
        or arm["analytical_equity"] != after["state"]["equity"]
    ):
        raise ValueError("I17_HOST_SIMULATED_PORTFOLIO_MISMATCH")


def _paper_contract(root, plan):
    manifest = _pinned_paper_manifest(root)
    profile = json.loads(_pinned_i17_file(root, manifest, "paper-profile.json"))
    contract_fields = profile["contract"]
    decimal_fields = {
        "contract_size",
        "tick_size",
        "min_qty",
        "initial_margin_rate",
        "maintenance_margin_rate",
        "max_leverage",
    }
    if set(contract_fields) != set(ContractMetadataV1.__dataclass_fields__):
        raise ValueError("I17_PAPER_CONTRACT_FIELDS_MISMATCH")
    contract = ContractMetadataV1(
        **{
            key: Decimal(value) if key in decimal_fields else value
            for key, value in contract_fields.items()
        }
    )
    native = plan["instrument_binding"]["instrument_metadata"]
    instrument = plan["instrument_id"]
    binding = profile["instrument_binding"]
    if (
        profile["schema"] != PAPER_PROFILE
        or profile["execution_environment"] != SIMULATION
        or profile["venue_order_transport"] is not False
        or binding["instrument_id"] != instrument
        or binding["venue_native_id"] != instrument
        or contract.symbol != instrument
        or native["instId"] != instrument
        or contract.contract_type != native["ctType"]
        or contract.quote_currency != native["settleCcy"]
        or contract.contract_size != Decimal(native["ctVal"]) * Decimal(native["ctMult"])
        or contract.tick_size != Decimal(native["tickSz"])
        or contract.min_qty != Decimal(native["lotSz"])
        or contract.min_qty < Decimal(native["minSz"])
        or contract.max_leverage != Decimal(native["lever"])
    ):
        raise ValueError("I17_PAPER_CONTRACT_OR_SCOPE_MISMATCH")
    return contract, sha256(manifest).hexdigest()


def _pinned_paper_manifest(root):
    manifest = root / "MANIFEST.sha256"
    original = manifest.read_bytes()
    valid, reason = verify_manifest_sha256(root, required_rel_paths=("paper-profile.json",))
    if not valid or manifest.read_bytes() != original:
        raise ValueError(f"I17_PAPER_TERMS_MANIFEST_INVALID:{reason}")
    return original


def _apply_futures_cycle(account, record, observed_at, mark):
    """Book one replayed action in the canonical native-contract accounting."""
    saved_fill = record["fill"]
    if saved_fill is None:
        account.mark_to_market(mark)
        return
    side, quantity = saved_fill["side"], Decimal(saved_fill["quantity"])
    action = record["intended_action"]
    payload = record.get("canonical_order_intent")
    if payload is None:
        # The original analytical exit mapper takes its quantity from the open
        # position. The futures owner checks that it only reduces exposure.
        if action.get("quantity_source") != "exit_or_reduce" or account.position is None:
            raise ValueError("I17_FUTURES_CONTRACT_QUANTITY_PROOF_REQUIRED")
        reduce_only = True
    else:
        intent = canonical_order_intent_from_dict(payload)
        valid = validate_canonical_order_intent_v1(intent)
        derived_side = "BUY" if (intent.side == "LONG") != intent.reduce_only else "SELL"
        if (
            payload.get("semantic_digest") != intent.semantic_digest
            or valid.validation_status != "VALID"
            or intent.instrument_id != account.contract.symbol
            or intent.quantity_unit != "CONTRACTS"
            or side != derived_side
            or action["intent_action"] != intent.intent_action
            or (quantity > intent.quantity if intent.reduce_only else quantity != intent.quantity)
        ):
            raise ValueError("I17_FUTURES_CONTRACT_QUANTITY_MISMATCH")
        reduce_only = intent.reduce_only

    params = record["portfolio_model"]["params"]
    fill = build_simulated_fill_v1(
        fill_id=saved_fill["fill_id"],
        instrument_id=account.contract.symbol,
        side=side,
        quantity=quantity,
        mark_price=mark,
        contract=account.contract,
        fee_rate_bps=params["fee_rate_bps"],
        slippage_bps=params["slippage_bps"],
        reduce_only=reduce_only,
        event_time_unix=observed_at.timestamp(),
    )
    account.apply_fill(fill)


def _archived_funding_source(plan, archive):
    market_rows = dict(_raw_rows(plan, archive))
    start, end = (_utc(plan[key]) for key in ("start_utc", "end_utc"))
    rates = {}
    end_ms = int(end.timestamp() * 1000)
    for row in market_rows["funding"]:
        time = row["fundingTime"]
        if not isinstance(time, str) or not time.isascii() or not time.isdecimal():
            raise ValueError("I17_FUNDING_EVENT_TIME_INVALID")
        event_ms = int(time)
        if not 0 < event_ms < end_ms:
            raise ValueError("I17_FUNDING_EVENT_TIME_INVALID")
        event_time = datetime.fromtimestamp(event_ms / 1000, timezone.utc)
        rate = Decimal(row["realizedRate"])
        if (
            row["instId"] != plan["instrument_id"]
            or row["instType"] != "FUTURES"
            or not rate.is_finite()
            or event_time in rates
        ):
            raise ValueError("I17_FUNDING_HISTORY_EVENT_INVALID")
        rates[event_time] = rate
    if (
        not 0 < len(rates) <= int(archive["records"]["funding"]["query"]["limit"])
        or list(rates) != sorted(rates, reverse=True)
        or min(rates) > start
    ):
        raise ValueError("I17_FUNDING_HISTORY_DOES_NOT_COVER_WINDOW")

    event_by_candle_open_ms = {
        int((event - HOUR).timestamp() * 1000): event for event in rates if start <= event < end
    }
    marks = {}
    for row in market_rows["mark"]:
        if not isinstance(row, list) or len(row) != 6:
            raise ValueError("I17_FUNDING_MARK_CANDLE_SHAPE_INVALID")
        event = event_by_candle_open_ms.get(int(row[0]))
        if event is None:
            continue
        close = Decimal(row[4])
        if (
            event in marks
            or event != event.replace(minute=0, second=0, microsecond=0)
            or row[-1] != "1"
            or not close.is_finite()
            or close <= 0
        ):
            raise ValueError("I17_FUNDING_MARK_CANDLE_INVALID")
        marks[event] = (event - HOUR, close)
    return deque((event, rates[event]) for event in sorted(event_by_candle_open_ms.values())), marks


def _book_archived_funding(account, *, event, rate, mark_open, mark):
    position = account.position
    quantity = Decimal("0") if position is None else position.qty
    notional = Decimal("0")
    amount = Decimal("0")
    if position is not None:
        notional = notional_value(
            mark_price=mark, qty=quantity, contract_size=account.contract.contract_size
        )
        amount = funding_payment_quote(side=position.side, notional=notional, funding_rate=rate)
    event_id = make_scoped_id("funding", account.contract.symbol, event.isoformat())
    account.apply_funding_observation_v1(
        event_id=event_id,
        amount=str(amount),
        currency=account.contract.quote_currency,
        instrument_id=account.contract.symbol,
        event_time_unix=event.timestamp(),
    )
    return {
        **account.funding_events[event_id],
        "event_id": event_id,
        "funding_time_utc": event.isoformat(),
        "realized_rate": str(rate),
        "mark_candle_open_utc": mark_open.isoformat(),
        "mark_close": str(mark),
        "position_side": None if position is None else position.side.value,
        "position_contracts": str(quantity),
        "notional": str(notional),
        "last_applied_fill_id": account.fill_order[-1] if account.fill_order else None,
    }


class _FuturesReadback:
    """Use the same native valuation and funding for observed and replayed actions."""

    def __init__(self, workspace, *, plan, initial_equity, paper_terms_evidence, funding_evidence):
        _assert_capture_journal_separate(workspace, _absolute(paper_terms_evidence))
        self.contract, self.paper_manifest = _paper_contract(paper_terms_evidence, plan)
        self.accounts = {
            role: ProductiveFuturesAccountingSessionV1(
                contract=self.contract, initial_equity=Decimal(equity)
            )
            for role, equity in initial_equity.items()
        }
        self.first_at = None
        self.settlements = deque()
        self.funding_archive = None
        self.bookings = {role: [] for role in self.accounts}
        self.models = {role: set() for role in self.accounts}
        self.decision_configs = {role: set() for role in self.accounts}
        self.governed_seams = {role: set() for role in self.accounts}
        if funding_evidence is not None:
            _assert_capture_journal_separate(workspace, _absolute(funding_evidence))
            self.funding_archive = read_v1(funding_evidence)
            self.settlements, self.settlement_marks = _archived_funding_source(
                plan, self.funding_archive
            )

    def book_cycle(self, *, observed_at, mark, arms):
        if self.first_at is None:
            self.first_at = observed_at
        while self.settlements and self.settlements[0][0] <= observed_at:
            event, rate = self.settlements.popleft()
            if event < self.first_at:
                continue
            if event not in self.settlement_marks:
                raise ValueError("I17_FUNDING_FINAL_SETTLEMENT_MARK_MISSING")
            mark_open, settlement_mark = self.settlement_marks[event]
            # Funding uses the position carried into the event, before a same-time fill.
            for role, account in self.accounts.items():
                self.bookings[role].append(
                    _book_archived_funding(
                        account, event=event, rate=rate, mark_open=mark_open, mark=settlement_mark
                    )
                )
        for role, arm in arms.items():
            record = arm["simulated_economics"]
            _apply_futures_cycle(self.accounts[role], record, observed_at, mark)
            self.models[role].add(record["portfolio_model"]["model_digest"])
            self.decision_configs[role].add(record["intended_action"]["config_digest"])
            self.governed_seams[role].add(arm["governed_seam_digest"])

    def result_fields(self):
        portfolios = {
            role: account.portfolio_state().to_dict() for role, account in self.accounts.items()
        }
        result = {
            "paper_contract_manifest_sha256": self.paper_manifest,
            "futures_contract": self.contract.to_dict(),
            "futures_contract_digest": self.contract.digest(),
            "futures_accounting_owner": next(iter(self.accounts.values())).kernel_owner,
            "futures_portfolios": portfolios,
            "futures_funding_semantics": "EXCHANGE_EVENTS_NOT_APPLIED",
            "futures_measurement": {
                "definition": "NET_RETURN_ON_BEGINNING_EQUITY_V1",
                "currency": self.contract.quote_currency,
                "initial_position": "FLAT",
                "terminal_valuation": "MARK_TO_MARKET_WITHOUT_FORCED_CLOSE",
                "profiles": {
                    role: {
                        "net_return_fraction": str(
                            (Decimal(portfolio["equity"]) - Decimal(portfolio["initial_equity"]))
                            / Decimal(portfolio["initial_equity"])
                        ),
                        "execution_model_digests": sorted(self.models[role]),
                        "decision_config_digests": sorted(self.decision_configs[role]),
                        "governed_parameter_seam_digests": sorted(self.governed_seams[role]),
                    }
                    for role, portfolio in portfolios.items()
                },
            },
        }
        if self.funding_archive is not None:
            sources = self.funding_archive["records"]
            result.update(
                futures_funding_semantics="OKX_HISTORY_RATE_AND_FINAL_MARK_CLOSE_APPLIED_IN_SIMULATION",
                funding_source_digest=digest_v1(self.funding_archive),
                funding_source_known_at_utc=max(
                    _utc(sources[role]["received_at_utc"]) for role in ("funding", "mark")
                ).isoformat(),
                funding_rate_response_sha256=sources["funding"]["raw_sha256"],
                funding_mark_response_sha256=sources["mark"]["raw_sha256"],
                funding_bookings=self.bookings,
            )
        return result


def measure_host_economics_v1(
    workspace,
    *,
    plan,
    evidence_root,
    code_sha,
    verify=False,
    paper_terms_evidence=None,
    funding_evidence=None,
):
    """Reconcile archived I17 simulations under their original model."""
    _assert_capture_journal_separate(workspace, evidence_root, REPO)
    instrument = plan["instrument_id"]
    manifest, rows = _read_i17_archive(evidence_root, instrument, require_typed_ddo=False)
    prereg = parse_preregistration_contract_v1(
        json.loads(_pinned_i17_file(evidence_root, manifest, "prereg.json"))
    )
    scope = _pinned_i17_file(evidence_root, manifest, "scope_digest.txt").decode().strip()
    plan_digest = digest_v1(plan)
    _, start, end = _decision_time_window(plan)
    profiles = plan["profiles"]
    if (
        set(profiles) != {"reference", "candidate"}
        or prereg.scope_digest() != scope
        or candidate_plan_component_v1(plan) not in prereg.strategy_component_identities
    ):
        raise ValueError("I17_HOST_SIMULATED_SCOPE_MISMATCH")

    portfolios = {role: IdempotentPortfolioV2() for role in profiles}
    initial_equity = {
        role: portfolio.model.snapshot()["state"]["equity"]
        for role, portfolio in portfolios.items()
    }
    futures = None
    if paper_terms_evidence is not None:
        futures = _FuturesReadback(
            workspace,
            plan=plan,
            initial_equity=initial_equity,
            paper_terms_evidence=paper_terms_evidence,
            funding_evidence=funding_evidence,
        )
    elif funding_evidence is not None:
        raise ValueError("I17_FUNDING_REQUIRES_FUTURES_ACCOUNTING")

    window_start = window_end = None
    cycle_count = 0
    for cycle_count, (decided, tick, parent) in enumerate(rows, start=1):
        pair = parent.get("i17_candidate_comparison") or {}
        if pair.get("status") != "COMPARED":
            raise ValueError("I17_HOST_PAIRED_OBSERVATION_INCOMPLETE")
        observed_at = _utc(pair["decision_time_utc"])
        if (
            pair["authority"] != "NONE"
            or pair["parent_decision_id"] != parent["decision_id"]
            or parent["session_id"] != prereg.session_id
            or pair["plan_digest"] != plan_digest
            or pair["original_i17_scope_digest"] != scope
            or pair["mark_sequence"] != tick["sequence"]
            or pair["mark_event_ts_unix"] != tick["event_ts_unix"]
            or pair["mark_receive_ts_unix"] != tick["receive_ts_unix"]
            or observed_at < datetime.fromtimestamp(decided, timezone.utc)
            or not start <= observed_at < end
            or (window_end is not None and observed_at <= window_end)
            or not _utc(pair["last_candle_close_utc"])
            <= _utc(pair["last_candle_input"]["received_at_utc"])
            <= observed_at
            or set(pair["arms"]) != set(profiles)
        ):
            raise ValueError("I17_HOST_PAIRED_OBSERVATION_BINDING_MISMATCH")
        mark = float(tick["mid_price"])
        if not Decimal(str(mark)).is_finite() or mark <= 0:
            raise ValueError("I17_HOST_INVALID_MARK")
        if window_start is None:
            window_start = observed_at
        for role, portfolio in portfolios.items():
            _replay_simulated_arm(
                portfolio,
                arm=pair["arms"][role],
                packet=profiles[role]["packet"],
                session=f"{prereg.session_id}-i17-candidate-{role}",
                index=cycle_count,
                instrument=instrument,
                mark=mark,
            )
        if futures is not None:
            futures.book_cycle(observed_at=observed_at, mark=Decimal(str(mark)), arms=pair["arms"])
        window_end = observed_at
    if window_start is None or window_end is None:
        raise ValueError("I17_HOST_PAIRED_OBSERVATION_INCOMPLETE")

    result = {
        "schema_version": "i17_host_simulated_economics_readback.v1",
        "authority": "NONE",
        "execution_class": EXECUTION_CLASS_ANALYTICAL,
        "code_sha": code_sha,
        "observation_code_sha": _pinned_i17_file(evidence_root, manifest, "repo_sha.txt")
        .decode()
        .strip(),
        "plan_digest": plan_digest,
        "original_i17_scope_digest": scope,
        "original_i17_manifest_sha256": sha256(manifest).hexdigest(),
        "instrument_id": instrument,
        "first_decision_utc": window_start.isoformat(),
        "last_decision_utc": window_end.isoformat(),
        "cycle_count": cycle_count,
        "profiles": {
            role: {
                "packet": profiles[role]["packet"],
                "parameters": profiles[role]["parameters"],
                "initial_equity": initial_equity[role],
                "portfolio_snapshot": portfolio.model.snapshot(),
            }
            for role, portfolio in portfolios.items()
        },
        "funding_semantics": "MODELLED_FUNDING_ONLY",
        "economic_qualification_status": "BLOCKED",
        "reality_gap_status": "INCOMPLETE",
    }
    if (evidence_root / "evidence_manifest.sha256").read_bytes() != manifest:
        raise ValueError("I17_HOST_ORIGINAL_MANIFEST_CHANGED")
    output_name = "host-economics.json"
    if futures is not None:
        output_name = (
            "host-futures-funding.json" if funding_evidence else "host-futures-accounting.json"
        )
        result.update(
            measurement_surface="SHADOW_ARCHIVE_SIMULATION_READBACK",
            original_market_sequence_sha256=_i17_manifest_pins(manifest)[
                "market_data_sequence.jsonl"
            ],
            schema_version=(
                "i17_host_futures_funding_readback.v1"
                if funding_evidence
                else "i17_host_futures_accounting_readback.v1"
            ),
            **futures.result_fields(),
        )
    output = workspace.safe_path_v1(output_name)
    with workspace.lease_v1():
        if verify:
            if read_v1(output) != result:
                raise ValueError("I17_HOST_SIMULATED_READBACK_MISMATCH")
        else:
            publish_v1(output, result)
        return read_v1(output)


def measure_backtest_economics_v1(
    workspace,
    *,
    plan,
    evidence_root,
    code_sha,
    decision_time_archive,
    paper_terms_evidence,
    funding_evidence,
    verify=False,
):
    """Recompute I17 decisions on a sealed market tape, then value their simulated fills."""
    if (
        funding_evidence is None
        or paper_terms_evidence is None
        or set(plan["profiles"]) != {"reference", "candidate"}
    ):
        raise ValueError("I17_BACKTEST_REQUIRES_PAIRED_FUTURES_AND_FUNDING_EVIDENCE")
    _assert_capture_journal_separate(workspace, evidence_root)
    manifest_sha, rows = _read_i17(evidence_root, plan["instrument_id"])
    scope = _read_i17_scope(evidence_root, manifest_sha)
    if decision_time_archive.get("original_i17_scope_digest") != scope:
        raise ValueError("I17_DECISION_TIME_ORIGINAL_SCOPE_MISMATCH")
    snapshots = _decision_time_last_snapshots(
        plan, rows, decision_time_archive, manifest_sha=manifest_sha
    )
    plan_digest = digest_v1(plan)
    binding = {
        "plan_digest": plan_digest,
        "original_i17_manifest_sha256": manifest_sha,
        "original_i17_scope_digest": scope,
        "last_candle_archive_digest": digest_v1(decision_time_archive),
        "code_sha": code_sha,
    }
    initial = IdempotentPortfolioV2().model.params.initial_equity
    futures = _FuturesReadback(
        workspace,
        plan=plan,
        initial_equity={role: initial for role in plan["profiles"]},
        paper_terms_evidence=paper_terms_evidence,
        funding_evidence=funding_evidence,
    )
    replayed = _compared_cycles(
        plan,
        rows,
        None,
        identifier=digest_v1(binding),
        decision_time_last=snapshots,
        record_simulated_economics=True,
    )
    decisions = []
    for (_, tick, _), cycle in zip(rows, replayed, strict=True):
        decide_at = _utc(cycle["decision_time_utc"])
        futures.book_cycle(
            observed_at=decide_at, mark=Decimal(str(float(tick["mid_price"]))), arms=cycle["arms"]
        )
        decisions.append(
            {
                "mark_sequence": tick["sequence"],
                "decision_time_utc": cycle["decision_time_utc"],
                "last_candle_input": cycle["last_candle_input"],
                "arms": {
                    role: {
                        "decision_id": arm["simulated_economics"]["intended_action"]["decision_id"],
                        "action": arm["intended_action"],
                        "fill_id": None
                        if arm["simulated_economics"]["fill"] is None
                        else arm["simulated_economics"]["fill"]["fill_id"],
                    }
                    for role, arm in cycle["arms"].items()
                },
            }
        )
    result = {
        "schema_version": "i17_backtest_futures_funding_readback.v1",
        "authority": "NONE",
        "measurement_surface": "BACKTEST_REPLAY_FROM_MARKET_TAPE",
        "instrument_id": plan["instrument_id"],
        "profiles": {
            role: {"packet": profile["packet"], "parameters": profile["parameters"]}
            for role, profile in plan["profiles"].items()
        },
        "first_decision_utc": decisions[0]["decision_time_utc"],
        "last_decision_utc": decisions[-1]["decision_time_utc"],
        "cycle_count": len(decisions),
        "replayed_decisions": decisions,
        "economic_qualification_status": "BLOCKED",
        "reality_gap_status": "INCOMPLETE",
        **binding,
        **futures.result_fields(),
    }
    manifest = (evidence_root / "evidence_manifest.sha256").read_bytes()
    if sha256(manifest).hexdigest() != manifest_sha:
        raise ValueError("I17_HOST_ORIGINAL_MANIFEST_CHANGED")
    result["original_market_sequence_sha256"] = _i17_manifest_pins(manifest)[
        "market_data_sequence.jsonl"
    ]
    output = workspace.safe_path_v1("backtest-futures-funding.json")
    with workspace.lease_v1():
        if verify:
            if read_v1(output) != result:
                raise ValueError("I17_BACKTEST_ECONOMICS_READBACK_MISMATCH")
        else:
            publish_v1(output, result)
        return read_v1(output)


def _verify_gap_measurement(receipt, *, plan, window, minimum_cycles, tolerance):
    first, last = (_utc(receipt[key]) for key in ("first_decision_utc", "last_decision_utc"))
    _, start, end = _decision_time_window(plan)
    if (
        not start <= window[0] < window[1] <= end
        or not start <= first < last < end
        or any(
            abs(Decimal(str((actual - scheduled).total_seconds()))) > tolerance
            for actual, scheduled in zip((first, last), window, strict=True)
        )
        or type(receipt["cycle_count"]) is not int
        or receipt["cycle_count"] < minimum_cycles
        or _utc(receipt["funding_source_known_at_utc"]) < end
    ):
        raise ValueError("I17_REALITY_GAP_WINDOW_OR_SAMPLE_MISMATCH")
    return last - first


def _measured_net_return(receipt, role, *, minimum_fills):
    portfolio = receipt["futures_portfolios"][role]
    initial = Decimal(portfolio["initial_equity"])
    final = Decimal(portfolio["equity"])
    if (
        not initial.is_finite()
        or initial <= 0
        or not final.is_finite()
        or type(portfolio["fill_count"]) is not int
        or portfolio["fill_count"] < minimum_fills
    ):
        raise ValueError("I17_REALITY_GAP_EQUITY_OR_SAMPLE_INVALID")
    value = (final - initial) / initial
    if Decimal(receipt["futures_measurement"]["profiles"][role]["net_return_fraction"]) != value:
        raise ValueError("I17_REALITY_GAP_RETURN_READBACK_MISMATCH")
    return initial, value


def prepare_i17_reality_gap_input_v1(
    workspace,
    *,
    expected_plan,
    observed_plan,
    expected_path,
    observed_path,
    policy_path,
    verify=False,
):
    """Admit a paired measurement and prepare existing Phase 7 dimension inputs."""
    expected_path, observed_path, policy_path = (
        _absolute(path) for path in (expected_path, observed_path, policy_path)
    )
    _assert_capture_journal_separate(workspace, REPO, expected_path, observed_path, policy_path)
    expected, observed = read_v1(expected_path), read_v1(observed_path)
    policy = json.loads(policy_path.read_bytes())
    registered, start, end = _decision_time_window(observed_plan)
    expected_window, observed_window, tolerance, threshold = _reality_gap_policy_window(
        policy, registered=registered, start=start, end=end
    )
    expected_plan_digest = digest_v1(expected_plan)
    observed_plan_digest = digest_v1(observed_plan)
    policy_digest = digest_v1(policy)
    if (
        observed_plan.get("reality_gap_policy_digest") != policy_digest
        or expected_plan_digest != policy["expected_plan_digest"]
        or digest_v1(expected) != policy["expected_receipt_digest"]
        or _utc(expected["funding_source_known_at_utc"]) > _utc(policy["registered_at_utc"])
        or _utc(expected_plan["end_utc"]) > _utc(policy["registered_at_utc"])
    ):
        raise ValueError("I17_REALITY_GAP_PREDECLARED_POLICY_REQUIRED")
    funded = "OKX_HISTORY_RATE_AND_FINAL_MARK_CLOSE_APPLIED_IN_SIMULATION"
    if (
        expected["schema_version"] != "i17_backtest_futures_funding_readback.v1"
        or expected["measurement_surface"] != "BACKTEST_REPLAY_FROM_MARKET_TAPE"
        or observed["schema_version"] != "i17_host_futures_funding_readback.v1"
        or observed["measurement_surface"] != "SHADOW_ARCHIVE_SIMULATION_READBACK"
        or not expected["authority"] == observed["authority"] == "NONE"
        or expected["plan_digest"] != expected_plan_digest
        or observed["plan_digest"] != observed_plan_digest
        or not expected["instrument_id"]
        == observed["instrument_id"]
        == observed_plan["instrument_id"]
        or not expected["futures_funding_semantics"]
        == observed["futures_funding_semantics"]
        == funded
    ):
        raise ValueError("I17_REALITY_GAP_SURFACE_OR_SCOPE_MISMATCH")
    if any(
        expected[key] == observed[key]
        or any(not re.fullmatch(r"[0-9a-f]{64}", receipt[key]) for receipt in (expected, observed))
        for key in (
            "original_i17_scope_digest",
            "original_i17_manifest_sha256",
            "original_market_sequence_sha256",
            "funding_source_digest",
        )
    ):
        raise ValueError("I17_REALITY_GAP_INDEPENDENT_OBSERVATION_REQUIRED")

    if any(
        expected[key] != observed[key]
        for key in (
            "code_sha",
            "futures_contract_digest",
            "futures_contract",
            "futures_accounting_owner",
        )
    ):
        raise ValueError("I17_REALITY_GAP_MEASUREMENT_BASIS_MISMATCH")
    expected_duration, observed_duration = (
        _verify_gap_measurement(
            receipt,
            plan=plan,
            window=window,
            minimum_cycles=policy["minimum_cycles"],
            tolerance=tolerance,
        )
        for receipt, plan, window in (
            (expected, expected_plan, expected_window),
            (observed, observed_plan, observed_window),
        )
    )
    if abs(Decimal(str((expected_duration - observed_duration).total_seconds()))) > tolerance:
        raise ValueError("I17_REALITY_GAP_WINDOW_OR_SAMPLE_MISMATCH")

    before, after = (item["futures_measurement"] for item in (expected, observed))
    definition = "NET_RETURN_ON_BEGINNING_EQUITY_V1"
    if (
        not before["definition"] == after["definition"] == definition
        or not before["currency"]
        == after["currency"]
        == expected["futures_contract"]["quote_currency"]
        or not before["initial_position"] == after["initial_position"] == "FLAT"
        or not before["terminal_valuation"]
        == after["terminal_valuation"]
        == "MARK_TO_MARKET_WITHOUT_FORCED_CLOSE"
        or any(
            set(item["profiles"]) != {"reference", "candidate"}
            for item in (expected, observed, before, after)
        )
    ):
        raise ValueError("I17_REALITY_GAP_METRIC_DEFINITION_MISMATCH")
    profiles = {}
    for role, profile in observed_plan["profiles"].items():
        if any(
            receipt["profiles"][role][key] != profile[key]
            for receipt in (expected, observed, expected_plan)
            for key in ("packet", "parameters")
        ):
            raise ValueError("I17_REALITY_GAP_PROFILE_MISMATCH")
        if any(
            before["profiles"][role][key] != after["profiles"][role][key]
            or len(before["profiles"][role][key]) != 1
            or not re.fullmatch(r"[0-9a-f]{64}", before["profiles"][role][key][0])
            for key in (
                "execution_model_digests",
                "decision_config_digests",
                "governed_parameter_seam_digests",
            )
        ):
            raise ValueError("I17_REALITY_GAP_RISK_OR_EXECUTION_MODEL_MISMATCH")
        initial_expected, net_expected = _measured_net_return(
            expected, role, minimum_fills=policy["minimum_fills_per_profile"]
        )
        initial_observed, net_observed = _measured_net_return(
            observed, role, minimum_fills=policy["minimum_fills_per_profile"]
        )
        if initial_expected != initial_observed:
            raise ValueError("I17_REALITY_GAP_START_EQUITY_MISMATCH")
        values = (net_expected, net_observed, threshold)
        numeric = tuple(float(value) for value in values)
        if any(
            not isfinite(scalar) or (value and not scalar)
            for value, scalar in zip(values, numeric, strict=True)
        ):
            raise ValueError("I17_REALITY_GAP_FLOAT_REPRESENTATION_INVALID")
        dimension = ResearchGapDimensionV1(
            name="pnl", expected=numeric[0], observed=numeric[1], threshold=numeric[2], unit="ratio"
        )
        profiles[role] = {"packet": profile["packet"], "gap_dimensions": [dimension.model_dump()]}

    result = {
        "schema_version": "i17_reality_gap_inputs.v1",
        "authority": "NONE",
        "expected_plan_digest": expected_plan_digest,
        "observed_plan_digest": observed_plan_digest,
        "metric_definitions": definition,
        "observed_surface": "SHADOW",
        "threshold_policy_digest": policy_digest,
        "expected_receipt_digest": digest_v1(expected),
        "observed_receipt_digest": digest_v1(observed),
        "expected_market_sequence_sha256": expected["original_market_sequence_sha256"],
        "observed_market_sequence_sha256": observed["original_market_sequence_sha256"],
        "source_data_known_at_utc": max(
            _utc(receipt["funding_source_known_at_utc"]) for receipt in (expected, observed)
        ).isoformat(),
        "profiles": profiles,
    }
    output = workspace.safe_path_v1("i17-reality-gap-inputs.json")
    with workspace.lease_v1():
        if verify:
            if read_v1(output) != result:
                raise ValueError("I17_REALITY_GAP_INPUT_READBACK_MISMATCH")
        else:
            publish_v1(output, result)
        return read_v1(output)


def _gap_main(argv):
    parser = argparse.ArgumentParser(description="Prepare paired I17 Phase 7 measurement inputs.")
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--pair-plan", type=Path, required=True)
    parser.add_argument("--expected-plan", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--observed", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    try:
        workspace = EvaluationReceiptArchiveV1(_absolute(args.state))
        plan_paths = tuple(_absolute(path) for path in (args.expected_plan, args.pair_plan))
        _assert_capture_journal_separate(workspace, *plan_paths)
        expected_plan, observed_plan = (read_v1(path) for path in plan_paths)
        result = prepare_i17_reality_gap_input_v1(
            workspace,
            expected_plan=expected_plan,
            observed_plan=observed_plan,
            expected_path=args.expected,
            observed_path=args.observed,
            policy_path=args.policy,
            verify=args.verify,
        )
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, InvalidOperation) as exc:
        parser.exit(2, f"I17 Reality Gap input stopped: {exc}\n")


def main(argv=None):
    args_list = sys.argv[1:] if argv is None else argv
    if args_list[:1] == ["reality-gap"]:
        return _gap_main(args_list[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--pair-plan", type=Path, required=True)
    parser.add_argument("--campaign-state", type=Path, required=True)
    parser.add_argument("--base-config", type=Path, required=True)
    parser.add_argument("--i17-evidence", type=Path, required=True)
    parser.add_argument("--decision-time-last-captures", type=Path)
    economics = parser.add_mutually_exclusive_group()
    economics.add_argument("--host-economics", action="store_true")
    economics.add_argument("--backtest-economics", action="store_true")
    parser.add_argument("--paper-terms-evidence", type=Path)
    parser.add_argument("--funding-evidence", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--capture-public-last", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args(args_list)
    try:
        state = _absolute(args.state)
        source_paths = [
            REPO,
            _absolute(args.pair_plan).parent,
            _absolute(args.campaign_state),
            _absolute(args.base_config),
            _absolute(args.i17_evidence),
        ]
        if args.paper_terms_evidence is not None:
            if not (args.host_economics or args.backtest_economics):
                raise ValueError("I17_PAPER_TERMS_REQUIRE_ECONOMICS_MODE")
            source_paths.append(_absolute(args.paper_terms_evidence))
        if args.funding_evidence is not None:
            if args.paper_terms_evidence is None:
                raise ValueError("I17_FUNDING_REQUIRES_FUTURES_ACCOUNTING")
            source_paths.append(_absolute(args.funding_evidence))
        if args.decision_time_last_captures is not None:
            if args.host_economics:
                raise ValueError("I17_HOST_ECONOMICS_USES_ORIGINAL_HOST_RECORDS")
            if args.capture_public_last:
                raise ValueError("I17_DECISION_TIME_PREFLIGHT_REQUIRES_OFFLINE_INPUT")
            source_paths.append(_absolute(args.decision_time_last_captures))
        if any(state.is_relative_to(path) or path.is_relative_to(state) for path in source_paths):
            raise ValueError("I17_COMPARISON_STATE_MUST_BE_SEPARATE")
        plan = read_v1(args.pair_plan)
        pair = _pair(
            args.campaign_state, plan["learning_digest"], json.loads(args.base_config.read_bytes())
        )
        if (
            plan["schema_version"] != PLAN_SCHEMA
            or plan["authority"] != "NONE"
            or any(plan[key] != value for key, value in pair.items())
            or plan["strategy_id"] != "ma_crossover"
        ):
            raise ValueError("I17_COMPARISON_GVEF_PLAN_MISMATCH")
        if args.backtest_economics:
            if not all(
                (args.decision_time_last_captures, args.paper_terms_evidence, args.funding_evidence)
            ):
                raise ValueError("I17_BACKTEST_REQUIRES_LAST_PAPER_TERMS_AND_FUNDING_EVIDENCE")
            result = measure_backtest_economics_v1(
                EvaluationReceiptArchiveV1(state),
                plan=plan,
                evidence_root=args.i17_evidence,
                code_sha=_head(),
                verify=args.verify,
                decision_time_archive=read_v1(args.decision_time_last_captures),
                paper_terms_evidence=args.paper_terms_evidence,
                funding_evidence=args.funding_evidence,
            )
            print(
                json.dumps(
                    {key: value for key, value in result.items() if key != "replayed_decisions"},
                    sort_keys=True,
                )
            )
            return 0
        if args.host_economics:
            if args.capture_public_last:
                raise ValueError("I17_HOST_ECONOMICS_REQUIRES_OFFLINE_INPUT")
            result = measure_host_economics_v1(
                EvaluationReceiptArchiveV1(state),
                plan=plan,
                evidence_root=args.i17_evidence,
                code_sha=_head(),
                verify=args.verify,
                paper_terms_evidence=args.paper_terms_evidence,
                funding_evidence=args.funding_evidence,
            )
            print(json.dumps(result, sort_keys=True))
            return 0
        result = compare_v1(
            EvaluationReceiptArchiveV1(state),
            plan=plan,
            evidence_root=args.i17_evidence,
            code_sha=_head(),
            capture_last=args.capture_public_last,
            verify=args.verify,
            decision_time_archive=(
                None
                if args.decision_time_last_captures is None
                else read_v1(args.decision_time_last_captures)
            ),
        )
        print(
            json.dumps(
                {key: value for key, value in result.items() if key != "cycles"}, sort_keys=True
            )
        )
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        InvalidOperation,
        AccountingEngineError,
    ) as exc:
        parser.exit(2, f"I17 candidate comparison stopped: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
