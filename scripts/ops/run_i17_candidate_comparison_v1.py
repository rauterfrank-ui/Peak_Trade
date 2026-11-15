#!/usr/bin/env python3
"""Replay the I17 decision bridge on one sealed mark sequence for both GVEF profiles."""

from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.ops.run_research_candidate_shadow_v1 import (  # noqa: E402
    _absolute,
    _clock,
    _head,
    _pair,
    _public_get,
)
from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import (  # noqa: E402
    EvaluationReceiptArchiveV1,
)
from src.experiments.canonical_research_prepared_execution_v1 import (  # noqa: E402
    digest_v1,
    publish_v1,
    read_v1,
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


def _pinned_i17_file(root, manifest, name):
    pins = dict(line.split("  ", 1)[::-1] for line in manifest.decode().splitlines() if line)
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


def _compare(plan, rows, candles, *, identifier, decision_time_last=None):
    pair = I17CandidatePairV1(plan, session_prefix=f"i17-offline-{identifier[:20]}")
    first_received = rows[0][1]["receive_ts_unix"]
    compared = []
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
        compared.append(
            {
                "observed_mark_sequence": tick.sequence,
                "historical_decision_id": decision_id,
                "decision_time_utc": decision_time.isoformat(),
                "last_candle_close_utc": close_time.isoformat(),
                **candle_input,
                "arms": arms,
            }
        )
    return compared


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


def measure_host_economics_v1(workspace, *, plan, evidence_root, code_sha, verify=False):
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
        if window_start is None:
            window_start = observed_at
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
    output = workspace.safe_path_v1("host-economics.json")
    with workspace.lease_v1():
        if verify:
            if read_v1(output) != result:
                raise ValueError("I17_HOST_SIMULATED_READBACK_MISMATCH")
        else:
            publish_v1(output, result)
        return read_v1(output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--pair-plan", type=Path, required=True)
    parser.add_argument("--campaign-state", type=Path, required=True)
    parser.add_argument("--base-config", type=Path, required=True)
    parser.add_argument("--i17-evidence", type=Path, required=True)
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--decision-time-last-captures", type=Path)
    inputs.add_argument("--host-economics", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--capture-public-last", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    try:
        state = _absolute(args.state)
        source_paths = [
            REPO,
            _absolute(args.pair_plan).parent,
            _absolute(args.campaign_state),
            _absolute(args.base_config),
            _absolute(args.i17_evidence),
        ]
        if args.decision_time_last_captures is not None:
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
        if args.host_economics:
            if args.capture_public_last:
                raise ValueError("I17_HOST_ECONOMICS_REQUIRES_OFFLINE_INPUT")
            result = measure_host_economics_v1(
                EvaluationReceiptArchiveV1(state),
                plan=plan,
                evidence_root=args.i17_evidence,
                code_sha=_head(),
                verify=args.verify,
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
    except (OSError, ValueError, KeyError, TypeError, IndexError, InvalidOperation) as exc:
        parser.exit(2, f"I17 candidate comparison stopped: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
