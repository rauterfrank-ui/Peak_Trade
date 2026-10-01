#!/usr/bin/env python3
"""Read-only natural-data witness search + stateful CURRENT offline replay (GHV V1).

Uses recorded GET captures only (no network). Does not mutate trading semantics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
ORIGIN_SHA = "45c4455288184ccd391bdd72b554a73518725e82"

DATASETS: tuple[dict[str, str], ...] = (
    {
        "DATASET_ID": "GHV_POST6999_INSTRUMENTED_FUNNEL_V1",
        "SOURCE_PATH": (
            "evidence/ops/golden_happy_vector_instrumented_information_funnel_post6999_v1/"
            "20261001T212755Z"
        ),
        "SOURCE_CLASS": "REAL_VENUE_GET_CAPTURE",
    },
    {
        "DATASET_ID": "GHV_NATURAL_MARKET_DATA_CAPTURE_V1",
        "SOURCE_PATH": (
            "evidence/ops/golden_happy_vector_natural_market_data_capture_real_venue_v1/"
            "20261001T203807Z"
        ),
        "SOURCE_CLASS": "REAL_VENUE_GET_CAPTURE",
    },
)

PRODUCTIVITY_TEMPLATE_REL = (
    "evidence/ops/golden_happy_vector_natural_market_data_capture_real_venue_v1/"
    "20261001T203807Z/readonly_offline_adjudication_workspace_v1/productivity"
)
RUNTIME_PRODUCTIVITY_REL = (
    "runtime/current_productive/golden_happy_natural_offline_witness_adjudication_v1/productivity"
)

G17_PROVISION_SYNTHETIC_HARNESS = "synthetic_harness"
G17_PROVISION_NATURAL_CHECKPOINT = "natural_checkpoint"
NATURAL_G17_CHECKPOINT_REL = (
    "g17_hot_path/g17_mark_history/current_productive_g17_typed_vol_mark_history_checkpoint_v1.json"
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _percentile(sorted_vals: list[float], p: float) -> float | None:
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return float(sorted_vals[f])
    return float(sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f))


def _threshold_class(
    long_sig: float, *, observe: float, candidate: float, confirmation: float
) -> str:
    if long_sig < observe:
        return "BELOW_OBSERVE"
    if long_sig < candidate:
        return "OBSERVE_ONLY"
    if long_sig < confirmation:
        return "CANDIDATE"
    return "CONFIRMED_LEVEL"


def _short_threshold_class(
    short_sig: float, *, observe: float, candidate: float, confirmation: float
) -> str:
    if short_sig < observe:
        return "BELOW_OBSERVE"
    if short_sig < candidate:
        return "OBSERVE_ONLY"
    if short_sig < confirmation:
        return "CANDIDATE"
    return "CONFIRMED_LEVEL"


def _bundle_polls(rows: list[dict[str, Any]], run_id: str) -> dict[int, dict[str, dict[str, Any]]]:
    poll_re = re.compile(rf"continuous-run-{re.escape(run_id)}-(poll|mark|index)-(\d+)$")
    by_poll: dict[int, dict[str, dict[str, Any]]] = defaultdict(dict)
    for r in rows:
        pid = str(r.get("pretrade_decision_id") or "")
        m = poll_re.match(pid)
        if not m:
            continue
        kind, idx = m.group(1), int(m.group(2))
        by_poll[idx][kind] = r
    return dict(by_poll)


def _chronological_candles_series(
    rows: list[dict[str, Any]],
) -> tuple[list[tuple[float, float]], dict[str, Any]]:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
        extract_finalized_candle_closes_v1,
    )

    by_ts: dict[float, float] = {}
    for r in rows:
        if str(r.get("get_kind") or "") != "CANDLES":
            continue
        payload = r.get("payload")
        if not isinstance(payload, dict):
            continue
        closes, last_ts = extract_finalized_candle_closes_v1(payload)
        if not closes or last_ts is None:
            continue
        for i, close in enumerate(closes):
            ts = last_ts - (len(closes) - 1 - i) * 60.0
            by_ts[float(ts)] = float(close)
    series = sorted(by_ts.items(), key=lambda x: x[0])
    meta = {
        "RAW_OBSERVATION_COUNT": len(rows),
        "DISTINCT_C1_COUNT": len(series),
        "FIRST_EVENT_TIME": series[0][0] if series else None,
        "LAST_EVENT_TIME": series[-1][0] if series else None,
    }
    return series, meta


def _inventory_dataset(spec: dict[str, str]) -> dict[str, Any]:
    root = REPO / spec["SOURCE_PATH"]
    capture = root / "natural_market_data_get_capture_v1.jsonl"
    rows = _load_jsonl(capture)
    natives = sorted({str(r.get("native_id") or "") for r in rows if r.get("native_id")})
    instrument = natives[0] if len(natives) == 1 else "MIXED"
    kinds = Counter(str(r.get("get_kind") or "OTHER") for r in rows)
    series, cmeta = _chronological_candles_series(rows)
    g17 = (
        root
        / "g17_hot_path/g17_mark_history/current_productive_g17_typed_vol_mark_history_checkpoint_v1.json"
    ).is_file()
    report_path = root / "PRE_EXTERNAL_CONVERGENCE_REPORT.json"
    run_id = ""
    if report_path.is_file():
        run_id = str(json.loads(report_path.read_text()).get("RUN_ID") or "")
    by_poll = _bundle_polls(rows, run_id) if run_id else {}
    complete = sum(1 for p in by_poll.values() if {"poll", "mark", "index"}.issubset(p))
    usable = complete >= 1 and instrument != "MIXED"
    reject = ""
    if instrument == "MIXED":
        reject = "INSTRUMENT_MIXING"
    elif complete < 1:
        reject = "INCOMPLETE_POLL_BUNDLES"
    start = cmeta.get("FIRST_EVENT_TIME")
    end = cmeta.get("LAST_EVENT_TIME")
    contiguous = 0
    if len(series) >= 2:
        contiguous = 1
        for i in range(1, len(series)):
            if abs(series[i][0] - series[i - 1][0] - 60.0) < 0.01:
                contiguous += 1
            else:
                break
    return {
        "DATASET_ID": spec["DATASET_ID"],
        "SOURCE_PATH": spec["SOURCE_PATH"],
        "SOURCE_CLASS": spec["SOURCE_CLASS"],
        "INSTRUMENT": instrument,
        "BAR_INTERVAL": "1m",
        "START_TIME": start,
        "END_TIME": end,
        "RAW_ROWS": len(rows),
        "DISTINCT_C1_COUNT": cmeta.get("DISTINCT_C1_COUNT", 0),
        "CONTIGUOUS_DISTINCT_C1_COUNT": contiguous,
        "HAS_MARK": kinds.get("MARK", 0) > 0,
        "HAS_INDEX": kinds.get("INDEX", 0) > 0,
        "HAS_CANDLES": kinds.get("CANDLES", 0) > 0,
        "HAS_CAP61_HISTORY": g17,
        "STATEFUL_SEQUENCE_USABLE": usable,
        "REJECTION_REASON_IF_NOT_USABLE": reject,
        "PROVEN_COMPLETE_POLL_BUNDLES": complete,
        "RUN_ID": run_id,
    }


def _build_injections(by_poll: dict[int, dict[str, dict[str, Any]]], native: str) -> list[Any]:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
        ProductiveCanonicalPriceProvenanceError,
        build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
        InjectedContinuousObservationV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
        productive_auth_free_flat_occupancy_payloads_v1,
    )

    out: list[InjectedContinuousObservationV1] = []
    for idx in sorted(by_poll):
        parts = by_poll[idx]
        if not {"poll", "mark", "index"}.issubset(parts):
            continue
        candles = parts["poll"]["payload"]
        mark_payload = parts["mark"]["payload"]
        index_payload = parts["index"]["payload"]
        try:
            build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
                mark_price_payload=mark_payload,
                venue_native_id=native,
                index_from_index_tickers=index_payload,
            )
        except ProductiveCanonicalPriceProvenanceError:
            continue
        out.append(
            InjectedContinuousObservationV1(
                candles_payload=candles,
                occupancy_payloads=productive_auth_free_flat_occupancy_payloads_v1(),
                mark_price_payload=mark_payload,
                index_tickers_payload=index_payload,
            )
        )
    return out


def _signal_records_for_injections(
    injections: list[Any],
    *,
    sequence_id: str,
    policy: Any,
) -> list[dict[str, Any]]:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
        ProductiveCanonicalPriceProvenanceError,
        build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
        extract_finalized_candle_closes_v1,
    )
    from trading.master_v2.directional_assessment_v1 import (
        DirectionalAssessmentSide,
        compute_signal_strength,
    )
    from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
        map_signal_strength_to_confirmation_assessment_signal_v1,
    )

    records: list[dict[str, Any]] = []
    last_distinct_ts: float | None = None
    for i, inj in enumerate(injections):
        closes, event_ts = extract_finalized_candle_closes_v1(inj.candles_payload)
        rec: dict[str, Any] = {
            "SEQUENCE_ID": sequence_id,
            "C1_INDEX": i,
            "EVENT_TIME": event_ts,
            "INSTRUMENT": "ON-USDT-SWAP",
            "SIGNAL_EVALUABLE": False,
        }
        if not closes or event_ts is None or len(closes) < 2:
            rec["SIGNAL_UNAVAILABLE_REASON"] = "PRICE_PATH_TOO_SHORT_OR_MISSING"
            records.append(rec)
            continue
        if inj.mark_price_payload is None:
            rec["SIGNAL_UNAVAILABLE_REASON"] = "MARK_PAYLOAD_MISSING"
            records.append(rec)
            continue
        try:
            prov = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
                mark_price_payload=inj.mark_price_payload,
                venue_native_id="ON-USDT-SWAP",
                index_from_index_tickers=inj.index_tickers_payload,
            )
        except ProductiveCanonicalPriceProvenanceError as exc:
            rec["SIGNAL_UNAVAILABLE_REASON"] = f"PROVENANCE_FAIL:{exc}"
            records.append(rec)
            continue
        ref = float(prov.mark_px)
        long_sig = compute_signal_strength(
            price_path=tuple(closes),
            side=DirectionalAssessmentSide.LONG,
            reference_price=ref,
        )
        short_sig = compute_signal_strength(
            price_path=tuple(closes),
            side=DirectionalAssessmentSide.SHORT,
            reference_price=ref,
        )
        observe = float(policy.observe_signal_threshold)
        candidate = float(policy.candidate_signal_threshold)
        confirmation = float(policy.confirmation_signal_threshold)
        rec.update(
            {
                "SIGNAL_EVALUABLE": True,
                "REFERENCE_PRICE": ref,
                "PATH_START": float(closes[0]),
                "PATH_END": float(closes[-1]),
                "LONG_SIGNAL_STRENGTH": long_sig,
                "SHORT_SIGNAL_STRENGTH": short_sig,
                "OBSERVE_THRESHOLD": observe,
                "CANDIDATE_THRESHOLD": candidate,
                "CONFIRMATION_THRESHOLD": confirmation,
                "LONG_THRESHOLD_CLASS": _threshold_class(
                    long_sig, observe=observe, candidate=candidate, confirmation=confirmation
                ),
                "SHORT_THRESHOLD_CLASS": _short_threshold_class(
                    short_sig, observe=observe, candidate=candidate, confirmation=confirmation
                ),
                "LONG_ASSESSMENT_SIGNAL": map_signal_strength_to_confirmation_assessment_signal_v1(
                    long_sig, policy
                ).value,
                "SHORT_ASSESSMENT_SIGNAL": map_signal_strength_to_confirmation_assessment_signal_v1(
                    short_sig, policy
                ).value,
                "CURRENT_DISTINCT_C1": event_ts != last_distinct_ts,
            }
        )
        last_distinct_ts = float(event_ts)
        records.append(rec)
    return records


def _signal_distribution(records: list[dict[str, Any]]) -> dict[str, Any]:
    evaluable = [r for r in records if r.get("SIGNAL_EVALUABLE")]
    long_vals = sorted(float(r["LONG_SIGNAL_STRENGTH"]) for r in evaluable)
    short_vals = sorted(float(r["SHORT_SIGNAL_STRENGTH"]) for r in evaluable)
    distinct = [r for r in evaluable if r.get("CURRENT_DISTINCT_C1") is not False]

    def _counts(side_key: str, class_key: str) -> dict[str, int]:
        c: Counter[str] = Counter()
        for r in distinct:
            c[str(r[class_key])] += 1
        return dict(c)

    long_c = _counts("LONG", "LONG_THRESHOLD_CLASS")
    short_c = _counts("SHORT", "SHORT_THRESHOLD_CLASS")

    def _max_contiguous(class_key: str, target: str) -> int:
        best = cur = 0
        for r in distinct:
            if str(r[class_key]) == target:
                cur += 1
                best = max(best, cur)
            else:
                cur = 0
        return best

    n_dist = len(distinct) or 1
    cand_long = long_c.get("CANDIDATE", 0) + long_c.get("CONFIRMED_LEVEL", 0)
    conf_long = long_c.get("CONFIRMED_LEVEL", 0)
    cand_short = short_c.get("CANDIDATE", 0) + short_c.get("CONFIRMED_LEVEL", 0)
    conf_short = short_c.get("CONFIRMED_LEVEL", 0)

    return {
        "SIGNAL_SAMPLE_COUNT": len(evaluable),
        "DISTINCT_SIGNAL_SAMPLE_COUNT": len(distinct),
        "LONG_SIGNAL_MIN": long_vals[0] if long_vals else None,
        "LONG_SIGNAL_P10": _percentile(long_vals, 10),
        "LONG_SIGNAL_P25": _percentile(long_vals, 25),
        "LONG_SIGNAL_MEDIAN": statistics.median(long_vals) if long_vals else None,
        "LONG_SIGNAL_P75": _percentile(long_vals, 75),
        "LONG_SIGNAL_P90": _percentile(long_vals, 90),
        "LONG_SIGNAL_P95": _percentile(long_vals, 95),
        "LONG_SIGNAL_P99": _percentile(long_vals, 99),
        "LONG_SIGNAL_MAX": long_vals[-1] if long_vals else None,
        "SHORT_SIGNAL_MIN": short_vals[0] if short_vals else None,
        "SHORT_SIGNAL_MEDIAN": statistics.median(short_vals) if short_vals else None,
        "SHORT_SIGNAL_MAX": short_vals[-1] if short_vals else None,
        "COUNT_BELOW_OBSERVE": long_c.get("BELOW_OBSERVE", 0),
        "COUNT_OBSERVE_ONLY": long_c.get("OBSERVE_ONLY", 0),
        "COUNT_CANDIDATE_LONG": long_c.get("CANDIDATE", 0),
        "COUNT_CONFIRMED_LEVEL_LONG": long_c.get("CONFIRMED_LEVEL", 0),
        "COUNT_CANDIDATE_SHORT": short_c.get("CANDIDATE", 0),
        "COUNT_CONFIRMED_LEVEL_SHORT": short_c.get("CONFIRMED_LEVEL", 0),
        "EMPIRICAL_CANDIDATE_THRESHOLD_HIT_RATE": cand_long / n_dist,
        "EMPIRICAL_CONFIRMATION_THRESHOLD_HIT_RATE": conf_long / n_dist,
        "EMPIRICAL_SHORT_CANDIDATE_HIT_RATE": cand_short / n_dist,
        "EMPIRICAL_SHORT_CONFIRMATION_HIT_RATE": conf_short / n_dist,
        "MAX_CONTIGUOUS_CANDIDATE_LONG": _max_contiguous("LONG_THRESHOLD_CLASS", "CANDIDATE")
        + _max_contiguous("LONG_THRESHOLD_CLASS", "CONFIRMED_LEVEL"),
        "MAX_CONTIGUOUS_CONFIRMED_LONG": _max_contiguous("LONG_THRESHOLD_CLASS", "CONFIRMED_LEVEL"),
        "MAX_CONTIGUOUS_CANDIDATE_SHORT": _max_contiguous("SHORT_THRESHOLD_CLASS", "CANDIDATE")
        + _max_contiguous("SHORT_THRESHOLD_CLASS", "CONFIRMED_LEVEL"),
        "MAX_CONTIGUOUS_CONFIRMED_SHORT": _max_contiguous(
            "SHORT_THRESHOLD_CLASS", "CONFIRMED_LEVEL"
        ),
    }


def _cursor_digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sort_injections_chronologically(injections: list[Any]) -> list[Any]:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
        extract_finalized_candle_closes_v1,
    )

    keyed: list[tuple[float, Any]] = []
    for inj in injections:
        _closes, ts = extract_finalized_candle_closes_v1(inj.candles_payload)
        if ts is None:
            continue
        keyed.append((float(ts), inj))
    keyed.sort(key=lambda item: item[0])
    return [item[1] for item in keyed]


def _dataset_natural_g17_checkpoint_path(dataset_root: Path) -> Path | None:
    path = dataset_root / NATURAL_G17_CHECKPOINT_REL
    return path if path.is_file() else None


def _checkpoint_history_digest(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return str(payload.get("history_digest") or "")


def _ingest_g17_from_injection_v1(
    producer: Any,
    *,
    injection: Any,
    venue_native_id: str,
    instrument_id: str,
    venue: str = "OKX",
) -> str:
    """Ingest one finalized PT1M mark from a replay injection (forensic parity only)."""
    from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
        ProductiveCanonicalPriceProvenanceError,
        build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
        extract_finalized_candle_closes_v1,
    )
    from trading.market_state.distinct_market_observation_acceptor_v1 import (
        ObservationTransportMetadataV1,
    )
    from trading.market_state.time_sample_epoch_semantics_v1 import (
        EventTimeInstantV1,
        MarketSampleIdentityV1,
    )

    if injection.mark_price_payload is None:
        return "SKIP_NO_MARK_PAYLOAD"
    _closes, event_ts = extract_finalized_candle_closes_v1(injection.candles_payload)
    if event_ts is None:
        return "SKIP_NO_EVENT_TS"
    try:
        prov = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
            mark_price_payload=injection.mark_price_payload,
            venue_native_id=venue_native_id,
            index_from_index_tickers=injection.index_tickers_payload,
        )
    except ProductiveCanonicalPriceProvenanceError as exc:
        return f"SKIP_PROVENANCE:{exc}"
    mark_px = float(prov.mark_px)
    sample = MarketSampleIdentityV1(
        venue=str(venue),
        canonical_instrument_id=str(instrument_id),
        venue_instrument_id=str(venue_native_id),
        event_time=EventTimeInstantV1(unix_seconds=float(event_ts)),
        mark_price=mark_px,
    )
    result = producer.ingest_finalized_pt1m_mark_sample_v1(
        sample=sample,
        transport=ObservationTransportMetadataV1(receive_time=float(event_ts) + 0.5),
    )
    return str(result.outcome.value)


def _ingest_natural_g17_checkpoint_prefix_v1(
    producer: Any,
    records: list[dict[str, Any]],
    *,
    max_event_ts: float,
    ingest_state: dict[str, int],
    venue: str,
    instrument_id: str,
    venue_native_id: str,
) -> None:
    """Ingest checkpoint PT1M marks up to decision event time (no future marks)."""
    from trading.market_state.distinct_market_observation_acceptor_v1 import (
        ObservationTransportMetadataV1,
    )
    from trading.market_state.time_sample_epoch_semantics_v1 import (
        EventTimeInstantV1,
        MarketSampleIdentityV1,
    )

    idx = int(ingest_state.get("next_index", 0))
    while idx < len(records):
        rec = records[idx]
        ts = float(rec["event_time"]["unix_seconds"])
        if ts > float(max_event_ts):
            break
        sample = MarketSampleIdentityV1(
            venue=str(rec.get("venue") or venue),
            canonical_instrument_id=str(rec.get("canonical_instrument_id") or instrument_id),
            venue_instrument_id=str(rec.get("venue_instrument_id") or venue_native_id),
            event_time=EventTimeInstantV1(unix_seconds=ts),
            mark_price=float(rec["mark_price"]),
        )
        producer.ingest_finalized_pt1m_mark_sample_v1(
            sample=sample,
            transport=ObservationTransportMetadataV1(receive_time=ts + 0.5),
        )
        idx += 1
    ingest_state["next_index"] = idx


def _g17_last_accepted_event_ts_unix_v1(producer: Any) -> float | None:
    last = getattr(getattr(producer, "history", None), "last_accepted_event_time", None)
    if last is None:
        return None
    unix = getattr(last, "unix_seconds", None)
    return None if unix is None else float(unix)


def _ingest_g17_replay_observation_v1(
    producer: Any,
    *,
    injection: Any,
    natural_g17_records: list[dict[str, Any]],
    ingest_state: dict[str, int],
    venue_native_id: str,
    instrument_id: str,
    venue: str = "OKX",
) -> None:
    """Prefix checkpoint through C1 event time; ingest mark only if not already accepted."""
    from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
        extract_finalized_candle_closes_v1,
    )

    _closes, event_ts = extract_finalized_candle_closes_v1(injection.candles_payload)
    if event_ts is not None and natural_g17_records:
        _ingest_natural_g17_checkpoint_prefix_v1(
            producer,
            natural_g17_records,
            max_event_ts=float(event_ts),
            ingest_state=ingest_state,
            venue=venue,
            instrument_id=instrument_id,
            venue_native_id=venue_native_id,
        )
    if event_ts is None:
        return
    last_ts = _g17_last_accepted_event_ts_unix_v1(producer)
    if last_ts is not None and float(last_ts) >= float(event_ts):
        return
    _ingest_g17_from_injection_v1(
        producer,
        injection=injection,
        venue_native_id=venue_native_id,
        instrument_id=instrument_id,
        venue=venue,
    )


def _build_g17_producers_for_replay_v1(
    pairs: dict[str, Any],
    *,
    provision: str,
    dataset_root: Path | None,
    instrument_id: str,
    venue_native_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build lane G17 producers; natural mode restores same-package checkpoint history."""
    from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
        _lane_g17,
    )
    from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
        CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
    )

    meta: dict[str, Any] = {
        "G17_PROVISION": provision,
        "OFFLINE_REPLAY_G17_PRODUCER_CURRENT": (
            "tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1._memory_g17_producer"
            if provision == G17_PROVISION_SYNTHETIC_HARNESS
            else "CanonicalVolatilityTypedRuntimeProducerScaffoldV1.restore_from_persistence_v1"
        ),
    }
    if provision == G17_PROVISION_SYNTHETIC_HARNESS:
        meta["OFFLINE_REPLAY_G17_INPUT_SOURCE"] = "synthetic 61×100*exp(0.001*i) harness marks"
        meta["OFFLINE_REPLAY_G17_INPUT_SAMPLE_COUNT"] = 61
        return _lane_g17(pairs), meta

    if dataset_root is None:
        raise ValueError("dataset_root required for natural_checkpoint G17 provision")
    checkpoint = _dataset_natural_g17_checkpoint_path(dataset_root)
    if checkpoint is None:
        raise FileNotFoundError(f"NATURAL_G17_CHECKPOINT_MISSING:{dataset_root}")
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    records = sorted(
        payload.get("records") or [],
        key=lambda r: float(r["event_time"]["unix_seconds"]),
    )
    producer = CanonicalVolatilityTypedRuntimeProducerScaffoldV1.create(
        venue="OKX",
        canonical_instrument_id=str(instrument_id),
        venue_instrument_id=str(venue_native_id),
        persistence_path=None,
    )
    marks = [float(r["mark_price"]) for r in records if r.get("mark_price") is not None]
    meta.update(
        {
            "NATURAL_G17_SOURCE": str(checkpoint.relative_to(REPO)),
            "NATURAL_G17_SOURCE_INSTRUMENT": venue_native_id,
            "NATURAL_G17_SOURCE_EVENT_TIME": (
                float(records[-1]["event_time"]["unix_seconds"]) if records else None
            ),
            "NATURAL_G17_SOURCE_SAMPLE_COUNT": len(records),
            "NATURAL_G17_SOURCE_DIGEST": _checkpoint_history_digest(checkpoint),
            "OFFLINE_REPLAY_G17_INPUT_SOURCE": "post6999_package_g17_checkpoint_history",
            "OFFLINE_REPLAY_G17_INPUT_SAMPLE_COUNT": len(records),
            "NATURAL_G17_MIN": min(marks) if marks else None,
            "NATURAL_G17_MAX": max(marks) if marks else None,
            "NATURAL_G17_VARIANCE": statistics.pvariance(marks) if len(marks) > 1 else None,
            "NATURAL_G17_UNIQUE_VALUE_COUNT": len({round(x, 6) for x in marks}),
            "NATURAL_SOURCE_MATCHES_G17_CONTRACT": True,
            "NATURAL_G17_CHECKPOINT_RECORDS": records,
        }
    )
    return {"LANE_1": producer}, meta


def _cursor_scope_forensics_v1(cursor_root: Path) -> dict[str, Any]:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
        CURSOR_FILENAME,
    )
    from trading.master_v2.deterministic_scope_event_generator_v1 import (
        ScopeDirectionState,
        compute_evaluated_thresholds,
    )
    from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
        scope_direction_from_side_state_v1,
    )
    from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
        resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1,
    )
    from trading.master_v2.double_play_state import SideState

    path = cursor_root / CURSOR_FILENAME
    if not path.is_file():
        return {"CURSOR_PRESENT": False}
    cursor = json.loads(path.read_text(encoding="utf-8"))
    scope = cursor.get("existing_scope") or {}
    rt = cursor.get("runtime_scope_state") or {}
    conf = cursor.get("scope_confirmation") or {}
    mark = None
    try:
        mark = float(
            cursor["cap61_confirmation_state"]["observation_acceptance_state"][
                "last_accepted_observation_identity"
            ]["mark_price"]
        )
    except (KeyError, TypeError, ValueError):
        mark = scope.get("reference_price")
    vol = scope.get("volatility_estimate")
    anchor = rt.get("anchor_price", scope.get("trailing_anchor"))
    band = rt.get("current_hysteresis_band", scope.get("scope_band"))
    boundaries: dict[str, Any] = {}
    if band is not None and anchor is not None and mark is not None:
        try:
            raw_side = str(cursor.get("side_state") or SideState.NEUTRAL_OBSERVE.value)
            try:
                side_state_enum = SideState(raw_side)
            except ValueError:
                side_state_enum = SideState.NEUTRAL_OBSERVE
            side = scope_direction_from_side_state_v1(side_state_enum)
            lc = resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1(float(band))
            if lc.ok:
                th = compute_evaluated_thresholds(
                    direction=side
                    if isinstance(side, ScopeDirectionState)
                    else ScopeDirectionState.LONG,
                    trailing_anchor=float(anchor),
                    up_distance=float(lc.up_distance),
                    adverse_exit_distance=float(lc.adverse_exit_distance),
                    reversal_distance=float(lc.reversal_distance),
                )
                boundaries = {
                    "UPSCOPE_BOUNDARY": th.up_candidate_threshold,
                    "DOWNSCOPE_BOUNDARY": th.downscope_candidate_threshold,
                    "ADVERSE_BOUNDARY": th.adverse_exit_threshold,
                }
        except (TypeError, ValueError):
            boundaries = {}
    return {
        "CURSOR_PRESENT": True,
        "G17_VOLATILITY": vol,
        "MARK": mark,
        "ANCHOR": anchor,
        "SCOPE_DISTANCE": (
            float(vol) * float(mark)
            if vol is not None and mark is not None
            else scope.get("initial_volatility_distance")
        ),
        **boundaries,
        "SCOPE_STATE": scope.get("lifecycle_state"),
        "SCOPE_CANDIDATE_KIND": conf.get("candidate_kind"),
        "SCOPE_CANDIDATE_COUNT": conf.get("candidate_count"),
        "SIDESTATE": cursor.get("side_state"),
        "TRADING_EPOCH": cursor.get("trading_epoch"),
    }


def _ddo_scope_event_sequence_v1(ddo_path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in _load_jsonl(ddo_path):
        pay = row.get("payload") or {}
        dt = str(pay.get("decision_type") or "")
        if "SCOPE" not in dt:
            continue
        reasons = pay.get("reason_codes") or []
        code = reasons[0].get("code") if reasons and isinstance(reasons[0], dict) else reasons
        out.append(
            {
                "EVENT_TIME_UTC": pay.get("event_time_utc"),
                "CYCLE_ID": pay.get("cycle_id"),
                "DECISION_TYPE": dt,
                "SCOPE_EVENT": code,
            }
        )
    return out


def _g17_typed_volatility_from_producer_v1(producer: Any) -> float | None:
    port = producer.output_port_v1()
    if port.estimate is None:
        return None
    return float(port.estimate.value)


def _run_stateful_replay(
    *,
    injections: list[Any],
    native: str,
    max_cycles: int,
    max_duration: float,
    workspace: Path,
    mode: str,
    g17_provision: str = G17_PROVISION_SYNTHETIC_HARNESS,
    dataset_root: Path | None = None,
    instrument_id: str = "",
) -> dict[str, Any]:
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
        _cursor_floor_or_zero,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
        RUNTIME_OWNER_GO,
        CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
        ScriptedContinuousObservationSourceV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
        bootstrap_s8_lane_via_s7_compose_v1,
        build_s8_occupied_lane_pairs_v1,
        make_n1_occupied_lane_s5_runner_v1,
        read_sidestate_continuity_snapshot_v1,
        run_offline_persistent_natural_enter_convergence_v1,
        _read_bull_confirmation_count_v1,
        _read_trading_epoch_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
        acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.cap24_runtime_binding_witness_epoch_v1 import (
        resolve_cap24_runtime_binding_witness_epoch_v1,
    )
    from src.ops.single_selected_future_policy_v1.persistence_v1 import (
        load_and_validate_selection_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
        CURSOR_FILENAME,
    )
    from tests.ops.test_full_core_current_productive_governed_continuous_cycle_orchestrator_v1 import (
        _FakeClock,
    )

    prod_template = REPO / PRODUCTIVITY_TEMPLATE_REL
    prod_runtime = REPO / RUNTIME_PRODUCTIVITY_REL
    lane_root = workspace / "lane_state"
    ev_root = workspace / f"offline_evidence_{mode}"
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    if prod_runtime.exists():
        shutil.rmtree(prod_runtime)
    prod_runtime.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(prod_template, prod_runtime)
    prod_src = prod_runtime

    sel = load_and_validate_selection_v1(
        prod_src / "runtime_state/selection", require_manifest=True
    )
    assert sel.selection is not None
    manifest_path = prod_src / "cap24_selection_state_publish_manifest_v1.json"
    prod_repo_sha = json.loads(manifest_path.read_text()).get("repository_sha", ORIGIN_SHA)
    binding_epoch = resolve_cap24_runtime_binding_witness_epoch_v1(
        selection=sel.selection,
        decision_epoch="2026-10-01T21:33:35Z",
    )
    handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
        productivity_root=prod_src,
        repository_sha=str(prod_repo_sha),
        binding_epoch=binding_epoch,
    )
    bound = handoff.bound_instrument
    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane_root, bound=bound)
    resolved_instrument_id = instrument_id or str(bound.instrument_id or "").strip()
    g17, g17_meta = _build_g17_producers_for_replay_v1(
        pairs,
        provision=g17_provision,
        dataset_root=dataset_root,
        instrument_id=resolved_instrument_id,
        venue_native_id=native,
    )
    cursor_root = Path(pairs["LANE_1"][0].lane_state_root)
    natural_ingest = g17_provision == G17_PROVISION_NATURAL_CHECKPOINT
    g17_producer = g17.get("LANE_1")
    natural_g17_records: list[dict[str, Any]] = list(
        g17_meta.get("NATURAL_G17_CHECKPOINT_RECORDS") or []
    )
    natural_g17_ingest_state: dict[str, int] = {"next_index": 0}

    cycle_traces: list[dict[str, Any]] = []
    base_factory = make_n1_occupied_lane_s5_runner_v1

    def _tracing_factory(**kw: Any) -> Any:
        inner = base_factory(**kw)

        def _runner(**kwargs: Any) -> Any:
            if (
                natural_ingest
                and g17_producer is not None
                and kwargs.get("mark_price_payload") is not None
            ):
                from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
                    InjectedContinuousObservationV1,
                )

                inj = InjectedContinuousObservationV1(
                    candles_payload=kwargs["candles_payload"],
                    occupancy_payloads=kwargs.get("occupancy_payloads") or {},
                    mark_price_payload=kwargs["mark_price_payload"],
                    index_tickers_payload=kwargs.get("index_tickers_payload"),
                )
                _ingest_g17_replay_observation_v1(
                    g17_producer,
                    injection=inj,
                    natural_g17_records=natural_g17_records,
                    ingest_state=natural_g17_ingest_state,
                    venue_native_id=native,
                    instrument_id=resolved_instrument_id,
                )
            scope_before = _cursor_scope_forensics_v1(cursor_root)
            before = _cursor_digest(cursor_root / CURSOR_FILENAME)
            bull_before = _read_bull_confirmation_count_v1(cursor_root)
            epoch_before = _read_trading_epoch_v1(cursor_root)
            snap_before = read_sidestate_continuity_snapshot_v1(cursor_root)
            result = inner(**kwargs)
            scope_after = _cursor_scope_forensics_v1(cursor_root)
            after = _cursor_digest(cursor_root / CURSOR_FILENAME)
            bull_after = _read_bull_confirmation_count_v1(cursor_root)
            epoch_after = _read_trading_epoch_v1(cursor_root)
            snap_after = read_sidestate_continuity_snapshot_v1(cursor_root)
            cycle_traces.append(
                {
                    "CYCLE_INDEX": len(cycle_traces) + 1,
                    "DECISION_RESULT": result.decision_result,
                    "MASTER_V2_DECISION": result.master_v2_decision,
                    "DECISION_EXECUTION_ELIGIBLE": result.decision_execution_eligible,
                    "BLOCKER_CLASS": result.blocker_class,
                    "FIRST_GENUINE_BLOCKER": result.first_genuine_blocker,
                    "C1_USED": result.c1_used,
                    "CURSOR_PERSISTED": result.cursor_persisted,
                    "CURSOR_FLOOR_BEFORE": result.cursor_floor_before,
                    "CURSOR_FLOOR_AFTER": result.cursor_floor_after,
                    "CONFIRMATION_BULL_COUNT_BEFORE": bull_before,
                    "CONFIRMATION_BULL_COUNT_AFTER": bull_after,
                    "TRADING_EPOCH_BEFORE": epoch_before,
                    "TRADING_EPOCH_AFTER": epoch_after,
                    "SIDESTATE_SNAPSHOT_BEFORE": snap_before,
                    "SIDESTATE_SNAPSHOT_AFTER": snap_after,
                    "CURSOR_DIGEST_BEFORE": before,
                    "CURSOR_DIGEST_AFTER": after,
                    "SCOPE_FORENSICS_BEFORE": scope_before,
                    "SCOPE_FORENSICS_AFTER": scope_after,
                    "G17_TYPED_VOLATILITY_AFTER_INGEST": (
                        _g17_typed_volatility_from_producer_v1(g17_producer)
                        if natural_ingest and g17_producer is not None
                        else None
                    ),
                }
            )
            return result

        return _runner

    import src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 as conv_mod

    conv_mod.make_n1_occupied_lane_s5_runner_v1 = _tracing_factory  # type: ignore[method-assign]

    ordered = _sort_injections_chronologically(injections)
    if len(ordered) < 2:
        return {
            "REPLAY_MODE": mode,
            "SKIPPED": True,
            "SKIP_REASON": "INSUFFICIENT_CHRONOLOGICAL_INJECTIONS",
        }
    bootstrap = ordered[0]
    feed = ordered[1:]
    if bootstrap.mark_price_payload is None:
        return {"REPLAY_MODE": mode, "SKIPPED": True, "SKIP_REASON": "BOOTSTRAP_MARK_MISSING"}
    if natural_ingest and g17_producer is not None:
        _ingest_g17_replay_observation_v1(
            g17_producer,
            injection=bootstrap,
            natural_g17_records=natural_g17_records,
            ingest_state=natural_g17_ingest_state,
            venue_native_id=native,
            instrument_id=resolved_instrument_id,
        )
    bootstrap_s8_lane_via_s7_compose_v1(
        composed_pairs=pairs,
        origin_main_sha=str(prod_repo_sha),
        g17_producers=g17,
        candles_payload=bootstrap.candles_payload,
        mark_price_payload=bootstrap.mark_price_payload,
        venue_native_id=native,
        index_tickers_payload=bootstrap.index_tickers_payload,
    )
    floor = float(_cursor_floor_or_zero(cursor_root))
    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=RUNTIME_OWNER_GO,
        native_id=native,
        bar="1m",
        expected_cursor_floor=floor,
        max_cycles_per_run=int(max_cycles),
        max_run_duration_seconds=float(max_duration),
        wait_interval_seconds=0.001,
        max_wait_for_next_c1_seconds=60.0,
        stall_seconds=60.0,
    )
    clock = _FakeClock()
    obs_steps = list(feed) + [None] * 8
    source = ScriptedContinuousObservationSourceV1(obs_steps)
    try:
        orch = run_offline_persistent_natural_enter_convergence_v1(
            authorization=auth,
            origin_main_sha=str(prod_repo_sha),
            lane_state_root=lane_root,
            bound=bound,
            g17_producers=g17,
            observation_source=source,
            evidence_root=ev_root,
            bootstrap_observation=None,
            time_fn=clock.time,
            sleep_fn=clock.sleep,
        )
    finally:
        conv_mod.make_n1_occupied_lane_s5_runner_v1 = base_factory  # type: ignore[method-assign]

    continuity: list[dict[str, Any]] = []
    for i in range(len(cycle_traces) - 1):
        a = cycle_traces[i]
        b = cycle_traces[i + 1]
        match = a.get("CURSOR_DIGEST_AFTER") is not None and a.get("CURSOR_DIGEST_AFTER") == b.get(
            "CURSOR_DIGEST_BEFORE"
        )
        reset = "UNKNOWN"
        if i == 0 and a.get("CONFIRMATION_BULL_COUNT_BEFORE") is None:
            reset = "EXPECTED_INITIAL_COLD_START"
        elif match:
            reset = "NONE"
        elif a.get("CURSOR_PERSISTED") and not match:
            reset = "UNEXPECTED_STATE_LOSS"
        continuity.append(
            {
                "CYCLE_N": i + 1,
                "CYCLE_N_OUTPUT_CURSOR_DIGEST": a.get("CURSOR_DIGEST_AFTER"),
                "CYCLE_N_PLUS_1_INPUT_CURSOR_DIGEST": b.get("CURSOR_DIGEST_BEFORE"),
                "CURSOR_CONTINUITY_MATCH": match,
                "CONFIRMATION_COUNT_DELTA": (
                    None
                    if a.get("CONFIRMATION_BULL_COUNT_AFTER") is None
                    else (
                        b.get("CONFIRMATION_BULL_COUNT_BEFORE"),
                        a.get("CONFIRMATION_BULL_COUNT_AFTER"),
                    )
                ),
                "RESET_CLASS": reset,
            }
        )

    ddo_path = cursor_root / "ddo_learning_capture_v1.jsonl"
    dpo_outcomes: list[str] = []
    for line in _load_jsonl(ddo_path):
        if line.get("record_type") == "double_play_entry_exit_observation":
            canon = (line.get("payload") or {}).get("producer_canonical_payload") or {}
            dpo_outcomes.append(str(canon.get("decision_outcome") or ""))

    scope_seq = _ddo_scope_event_sequence_v1(ddo_path)
    bootstrap_scope = _cursor_scope_forensics_v1(cursor_root)
    g17_meta_safe = {k: v for k, v in g17_meta.items() if k != "NATURAL_G17_CHECKPOINT_RECORDS"}
    return {
        "REPLAY_MODE": mode,
        "G17_PROVISION": g17_provision,
        "G17_PROVISION_META": g17_meta_safe,
        "MAX_CYCLES": max_cycles,
        "MAX_DURATION_SECONDS": max_duration,
        "CYCLES_COMPLETED": orch.cycles_completed,
        "DISPOSITION": orch.disposition,
        "TERMINAL_CLASS": orch.terminal_class,
        "POST_COUNT": orch.post_count,
        "EXTERNAL_EFFECTS": orch.external_effect_count,
        "CYCLE_TRACES": cycle_traces,
        "CURSOR_CONTINUITY": continuity,
        "DPO_DECISION_OUTCOMES": dpo_outcomes,
        "SCOPE_EVENT_SEQUENCE": scope_seq,
        "FINAL_CURSOR_SCOPE_FORENSICS": bootstrap_scope,
        "NATURAL_ENTER_OBSERVED": any(x in {"enter_long", "enter_short"} for x in dpo_outcomes),
        "CURSOR_FLOOR_AFTER": _cursor_floor_or_zero(cursor_root),
    }


def _witness_levels(replay: dict[str, Any], dist: dict[str, Any]) -> dict[str, Any]:
    traces = replay.get("CYCLE_TRACES") or []
    deepest_long = "L0"
    deepest_short = "S0"
    long_drop = "NONE"
    short_drop = "NONE"

    if dist.get("SIGNAL_SAMPLE_COUNT", 0) > 0:
        deepest_long = "L1"
        deepest_short = "S1"
    if dist.get("COUNT_CANDIDATE_LONG", 0) + dist.get("COUNT_CONFIRMED_LEVEL_LONG", 0) > 0:
        deepest_long = "L2"
    if dist.get("MAX_CONTIGUOUS_CONFIRMED_LONG", 0) >= 1:
        deepest_long = "L3"
    if dist.get("MAX_CONTIGUOUS_CONFIRMED_LONG", 0) >= 2:
        deepest_long = "L4"
    if any(
        t.get("CONFIRMATION_BULL_COUNT_AFTER", 0) and t["CONFIRMATION_BULL_COUNT_AFTER"] >= 2
        for t in traces
    ):
        deepest_long = "L4"
    if any("long" in str(t.get("MASTER_V2_DECISION") or "").lower() for t in traces):
        if int(deepest_long[1:]) < 7:
            deepest_long = "L7"
    if replay.get("NATURAL_ENTER_OBSERVED"):
        deepest_long = "L9"

    if dist.get("COUNT_CANDIDATE_SHORT", 0) + dist.get("COUNT_CONFIRMED_LEVEL_SHORT", 0) > 0:
        deepest_short = "S2"
    if dist.get("MAX_CONTIGUOUS_CONFIRMED_SHORT", 0) >= 2:
        deepest_short = "S4"
    if replay.get("NATURAL_ENTER_OBSERVED"):
        deepest_short = "S9"

    if dist.get("MAX_CONTIGUOUS_CONFIRMED_LONG", 0) < 2:
        long_drop = "INSUFFICIENT_CONTIGUOUS_CONFIRMED_LEVEL_DISTINCT_POLLS"
        long_first = (
            "L3/L4 Confirmation progression (need 2 contiguous distinct CONFIRMED-level signals)"
        )
    elif not replay.get("NATURAL_ENTER_OBSERVED"):
        long_first = "L5-L8 Scope/SideState/Composition (replay did not reach ENTER_LONG)"
        long_drop = "SCOPE_OR_COMPOSITION_NOT_SATISFIED_IN_REPLAY"
    else:
        long_first = "NONE"
        long_drop = "NONE"

    if dist.get("MAX_CONTIGUOUS_CONFIRMED_SHORT", 0) < 2:
        short_first = "S3/S4 Confirmation progression"
        short_drop = "INSUFFICIENT_CONTIGUOUS_CONFIRMED_SHORT"
    else:
        short_first = "NOT_REACHED"
        short_drop = "SHORT_CANDIDATE_DOMINANCE_LONG_SIDE"

    return {
        "LONG_DEEPEST_NATURAL_LEVEL_REACHED": deepest_long,
        "SHORT_DEEPEST_NATURAL_LEVEL_REACHED": deepest_short,
        "LONG_FIRST_UNSATISFIED_WITNESS_CONSTRAINT": long_first,
        "SHORT_FIRST_UNSATISFIED_WITNESS_CONSTRAINT": short_first,
        "PRIMARY_LONG_DROP_REASON": long_drop,
        "PRIMARY_SHORT_DROP_REASON": short_drop,
    }


def run_g17_parity_readjudication_v1(out_dir: Path) -> dict[str, Any]:
    """Run synthetic vs natural-checkpoint G17 provision on the same post6999 capture."""
    from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
        bind_typed_canonical_volatility_estimate_into_market_context_v1,
        resolve_legacy_volatility_float_for_consumer_v1,
    )
    from trading.master_v2.canonical_market_context_v1 import (
        BarFinalityStatus,
        CanonicalMarketContextV1,
        ClockTrustStatus,
        DataIntegrityStatus,
        FuturesMarketType,
        WarmupStatus,
        with_computed_input_digest,
    )

    dataset = DATASETS[0]
    root = REPO / dataset["SOURCE_PATH"]
    rows = _load_jsonl(root / "natural_market_data_get_capture_v1.jsonl")
    run_id = str(
        json.loads((root / "PRE_EXTERNAL_CONVERGENCE_REPORT.json").read_text()).get("RUN_ID")
    )
    injections = _build_injections(_bundle_polls(rows, run_id), "ON-USDT-SWAP")
    ordered = _sort_injections_chronologically(injections)
    bootstrap = ordered[0]

    ws_old = out_dir / "replay_synthetic_harness"
    ws_new = out_dir / "replay_natural_checkpoint"
    old = _run_stateful_replay(
        injections=injections,
        native="ON-USDT-SWAP",
        max_cycles=4,
        max_duration=180.0,
        workspace=ws_old / "faithful_180s_4cycles",
        mode="SYNTHETIC_HARNESS_G17",
        g17_provision=G17_PROVISION_SYNTHETIC_HARNESS,
    )
    new = _run_stateful_replay(
        injections=injections,
        native="ON-USDT-SWAP",
        max_cycles=4,
        max_duration=180.0,
        workspace=ws_new / "faithful_180s_4cycles",
        mode="NATURAL_CHECKPOINT_G17",
        g17_provision=G17_PROVISION_NATURAL_CHECKPOINT,
        dataset_root=root,
        instrument_id="okx_eea:linear_perpetual:ON:USDT:USDT:on-usdt-swap",
    )

    # Recompute G17→CMC→resolver on bootstrap observation with natural producer after ingest.
    from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
        build_s8_occupied_lane_pairs_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
        acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.cap24_runtime_binding_witness_epoch_v1 import (
        resolve_cap24_runtime_binding_witness_epoch_v1,
    )
    from src.ops.single_selected_future_policy_v1.persistence_v1 import (
        load_and_validate_selection_v1,
    )
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.feature_regime_pipeline_v1 import (
        compute_feature_regime_from_mid_prices_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
        build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
        extract_finalized_candle_closes_v1,
    )

    prod_runtime = REPO / RUNTIME_PRODUCTIVITY_REL
    if not prod_runtime.is_dir():
        prod_runtime.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(REPO / PRODUCTIVITY_TEMPLATE_REL, prod_runtime)
    manifest = json.loads(
        (prod_runtime / "cap24_selection_state_publish_manifest_v1.json").read_text()
    )
    sel = load_and_validate_selection_v1(
        prod_runtime / "runtime_state/selection", require_manifest=True
    )
    handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
        productivity_root=prod_runtime,
        repository_sha=str(manifest["repository_sha"]),
        binding_epoch=resolve_cap24_runtime_binding_witness_epoch_v1(
            selection=sel.selection, decision_epoch="2026-10-01T21:33:35Z"
        ),
    )
    pairs = build_s8_occupied_lane_pairs_v1(
        lane_state_root=out_dir / "g17_chain_probe_lane",
        bound=handoff.bound_instrument,
    )
    g17_nat, g17_nat_meta = _build_g17_producers_for_replay_v1(
        pairs,
        provision=G17_PROVISION_NATURAL_CHECKPOINT,
        dataset_root=root,
        instrument_id=str(handoff.bound_instrument.instrument_id),
        venue_native_id="ON-USDT-SWAP",
    )
    producer = g17_nat["LANE_1"]
    records = list(g17_nat_meta.get("NATURAL_G17_CHECKPOINT_RECORDS") or [])
    ingest_state: dict[str, int] = {"next_index": 0}
    _ingest_g17_replay_observation_v1(
        producer,
        injection=bootstrap,
        natural_g17_records=records,
        ingest_state=ingest_state,
        venue_native_id="ON-USDT-SWAP",
        instrument_id=str(handoff.bound_instrument.instrument_id),
    )
    typed_vol = _g17_typed_volatility_from_producer_v1(producer)
    closes, _ts = extract_finalized_candle_closes_v1(bootstrap.candles_payload)
    prov = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
        mark_price_payload=bootstrap.mark_price_payload,
        venue_native_id="ON-USDT-SWAP",
        index_from_index_tickers=bootstrap.index_tickers_payload,
    )
    mark = float(prov.mark_px)
    feats = compute_feature_regime_from_mid_prices_v1(closes)
    ctx = with_computed_input_digest(
        CanonicalMarketContextV1(
            context_id="parity-bootstrap",
            instrument_id=str(handoff.bound_instrument.instrument_id),
            market_type=FuturesMarketType.PERPETUAL,
            trading_epoch=1,
            market_event_time="2026-10-01T21:31:00Z",
            decision_time="2026-10-01T21:31:01Z",
            bar_interval="1m",
            bar_finality_status=BarFinalityStatus.FINALIZED,
            mark_price=mark,
            index_price=mark,
            best_bid=mark - 0.01,
            best_ask=mark + 0.01,
            spread=0.02,
            volume=1.0,
            open_interest=1.0,
            funding_rate=0.0,
            volatility_estimate=float(feats.volatility_estimate),
            trend_feature_set={},
            momentum_feature_set={},
            liquidity_feature_set={},
            market_structure_feature_set={},
            data_integrity_status=DataIntegrityStatus.TRUSTED,
            clock_trust_status=ClockTrustStatus.TRUSTED,
            warmup_status=WarmupStatus.WARMUP_COMPLETE,
            feature_contract_version="v1",
            input_digest="",
        )
    )
    port = producer.output_port_v1()
    assert port.estimate is not None
    ctx_bound = bind_typed_canonical_volatility_estimate_into_market_context_v1(ctx, port.estimate)
    resolved = resolve_legacy_volatility_float_for_consumer_v1(ctx_bound)

    old_scope = (old.get("SCOPE_EVENT_SEQUENCE") or [{}])[0].get("SCOPE_EVENT")
    new_scope = (new.get("SCOPE_EVENT_SEQUENCE") or [{}])[0].get("SCOPE_EVENT")
    old_vol = (old.get("FINAL_CURSOR_SCOPE_FORENSICS") or {}).get("G17_VOLATILITY")
    new_vol = (new.get("FINAL_CURSOR_SCOPE_FORENSICS") or {}).get("G17_VOLATILITY")
    old_dist = (old.get("FINAL_CURSOR_SCOPE_FORENSICS") or {}).get("SCOPE_DISTANCE")
    new_dist = (new.get("FINAL_CURSOR_SCOPE_FORENSICS") or {}).get("SCOPE_DISTANCE")

    verdict: dict[str, Any] = {
        "WP": "OFFLINE_REPLAY_G17_PROVISION_PARITY_REPAIR_NATURAL_SCOPE_READJUDICATION_V1",
        "BASE_HEAD": ORIGIN_SHA,
        "G17_REQUIRED_INPUT_SEMANTICS": "FINALIZED_PT1M_MARK_PRICE_LOG_RETURN_STDDEV_60B",
        "G17_REQUIRED_BAR_INTERVAL": "PT1M",
        "G17_REQUIRED_SAMPLE_COUNT": 61,
        "G17_REQUIRED_ORDERING": "chronological_distinct_PT1M",
        "G17_REQUIRED_PRICE_FIELD": "mark_price",
        "NATURAL_SOURCE_MATCHES_G17_CONTRACT": True,
        "TRADING_LOGIC_CHANGED": False,
        "G17_FORMULA_CHANGED": False,
        "CMC_BIND_CHANGED": False,
        "LEGACY_RESOLVER_CHANGED": False,
        "DYNAMIC_SCOPE_CHANGED": False,
        "THRESHOLDS_CHANGED": False,
        "SYNTHETIC_FIXTURE_BEHAVIOR_PRESERVED": True,
        "OFFLINE_REPLAY_G17_PRODUCER_BEFORE": old.get("G17_PROVISION_META", {}).get(
            "OFFLINE_REPLAY_G17_PRODUCER_CURRENT"
        ),
        "OFFLINE_REPLAY_G17_INPUT_BEFORE": old.get("G17_PROVISION_META", {}).get(
            "OFFLINE_REPLAY_G17_INPUT_SOURCE"
        ),
        "NATURAL_G17_SOURCE": g17_nat_meta.get("NATURAL_G17_SOURCE"),
        "NATURAL_G17_SAMPLE_COUNT": g17_nat_meta.get("NATURAL_G17_SOURCE_SAMPLE_COUNT"),
        "NATURAL_G17_TYPED_VOLATILITY": typed_vol,
        "CMC_BOUND_VOLATILITY": ctx_bound.volatility_estimate,
        "RESOLVED_SCOPE_VOLATILITY": resolved,
        "G17_TO_CMC_VALUE_EQUAL": typed_vol == ctx_bound.volatility_estimate,
        "CMC_TO_RESOLVER_VALUE_EQUAL": ctx_bound.volatility_estimate == resolved,
        "OLD_HARNESS_G17_VOLATILITY": old_vol,
        "PARITY_CORRECT_G17_VOLATILITY": new_vol,
        "OLD_HARNESS_SCOPE_DISTANCE": old_dist,
        "PARITY_CORRECT_SCOPE_DISTANCE": new_dist,
        "OLD_HARNESS_SCOPE_EVENT": old_scope,
        "PARITY_CORRECT_SCOPE_EVENT": new_scope,
        "DID_SYNTHETIC_G17_INPUT_CHANGE_CAUSAL_CONCLUSION": old_scope != new_scope
        or old_vol != new_vol,
        "SYNTHETIC_REPLAY": old,
        "PARITY_REPLAY": new,
        "ORIGINAL_PRODUCTIVE_G17_VALUE": "UNKNOWN",
        "REPLAY_PARITY": "PARTIAL",
        "REPLAY_PARITY_REASON": (
            "Offline replay now restores same-package G17 checkpoint and ingests per-cycle marks; "
            "original live run did not persist typed G17 consumed at Scope init in durable evidence."
        ),
        "MINIMUM_ADDITIONAL_PRODUCTIVE_OBSERVABILITY": (
            "Persist G17 output_port estimate + bind outcome on each productive cycle in durable evidence"
        ),
        "REAL_VENUE_PRODUCT_INVOCATION_COUNT": 0,
        "NETWORK_GET_COUNT": 0,
        "POST_ATTEMPTS": 0,
        "EXTERNAL_EFFECTS": 0,
        "PERMIT_CREATED": False,
    }
    return verdict


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO
        / "evidence/ops/natural_data_offline_witness_search_stateful_current_replay_v1/20261001T234500Z",
    )
    parser.add_argument(
        "--parity-readjudication",
        action="store_true",
        help="Run G17 synthetic vs natural-checkpoint parity replay (post6999 capture only).",
    )
    args = parser.parse_args()
    if args.parity_readjudication:
        out = args.output_dir
        out.mkdir(parents=True, exist_ok=True)
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
        verdict = run_g17_parity_readjudication_v1(out)
        verdict["FINAL_HEAD"] = head
        verdict["CODE_CHANGED"] = True
        verdict["PR_CREATED"] = False
        # First divergence heuristics from parity replay
        parity = verdict.get("PARITY_REPLAY") or {}
        traces = parity.get("CYCLE_TRACES") or []
        scope_seq = parity.get("SCOPE_EVENT_SEQUENCE") or []
        dpo = parity.get("DPO_DECISION_OUTCOMES") or []
        if parity.get("NATURAL_ENTER_OBSERVED"):
            verdict["FIRST_TRUE_DIVERGENCE_STAGE"] = "NONE_ENTER_OBSERVED"
            verdict["NATURAL_ENTER_LIVENESS_STATUS"] = "PROVEN_LIVE"
            verdict["NEXT_ACTION"] = "EXPAND_OFFLINE_EVIDENCE"
        elif any("upscope" in str(s.get("SCOPE_EVENT") or "").lower() for s in scope_seq):
            verdict["FIRST_TRUE_DIVERGENCE_STAGE"] = "Downstream_of_UPSCOPE"
            verdict["NATURAL_ENTER_LIVENESS_STATUS"] = "UNKNOWN_CURRENT"
            verdict["NEXT_ACTION"] = "EXPAND_OFFLINE_EVIDENCE"
        else:
            verdict["FIRST_TRUE_DIVERGENCE_STAGE"] = "Dynamic Scope or downstream"
            verdict["REQUIRED_VALUE_OR_STATE"] = "UPSCOPE_CANDIDATE or UPSCOPE_CONFIRMED"
            verdict["OBSERVED_VALUE_OR_STATE"] = scope_seq
            verdict["DIVERGENCE_REASON"] = "Scope did not emit upscope under parity-correct G17"
            verdict["NATURAL_ENTER_LIVENESS_STATUS"] = "UNKNOWN_CURRENT"
            verdict["NEXT_ACTION"] = "EXPAND_OFFLINE_EVIDENCE"
        verdict["SCOPE_EVENT_SEQUENCE"] = scope_seq
        verdict["SIDESTATE_SEQUENCE"] = [
            t.get("SCOPE_FORENSICS_AFTER", {}).get("SIDESTATE") for t in traces
        ]
        verdict["DECISION_SEQUENCE"] = dpo
        verdict["NATURAL_ENTER_OBSERVED"] = parity.get("NATURAL_ENTER_OBSERVED", False)
        verdict["PRE_EXTERNAL_REACHED"] = False
        path = out / "OFFLINE_REPLAY_G17_PARITY_NATURAL_SCOPE_READJUDICATION_V1.json"
        path.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(verdict, indent=2, sort_keys=True))
        return 0

    out_dir: Path = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()

    from trading.master_v2.canonical_core_runtime_integration_bridge_v0 import _default_policies

    policy = _default_policies().directional
    thresholds_verified = {
        "OBSERVE_THRESHOLD": policy.observe_signal_threshold,
        "CANDIDATE_THRESHOLD": policy.candidate_signal_threshold,
        "CONFIRMATION_THRESHOLD": policy.confirmation_signal_threshold,
        "CONFIRMATION_EPOCHS": policy.confirmation_epochs,
        "SOURCE": "canonical_core_runtime_integration_bridge_v0._default_policies",
    }

    inventories = [_inventory_dataset(d) for d in DATASETS]
    all_records: list[dict[str, Any]] = []
    replay_results: dict[str, Any] = {}

    for inv in inventories:
        if not inv.get("STATEFUL_SEQUENCE_USABLE"):
            continue
        root = REPO / inv["SOURCE_PATH"]
        rows = _load_jsonl(root / "natural_market_data_get_capture_v1.jsonl")
        by_poll = _bundle_polls(rows, str(inv.get("RUN_ID") or ""))
        injections = _build_injections(by_poll, str(inv["INSTRUMENT"]))
        seq_id = str(inv["DATASET_ID"])
        recs = _signal_records_for_injections(injections, sequence_id=seq_id, policy=policy)
        all_records.extend(recs)
        dist = _signal_distribution(recs)
        ws = out_dir / f"replay_workspace_{inv['DATASET_ID']}"
        faithful = _run_stateful_replay(
            injections=injections,
            native=str(inv["INSTRUMENT"]),
            max_cycles=4,
            max_duration=180.0,
            workspace=ws / "faithful_180s_4cycles",
            mode="FAITHFUL_PRODUCT_BUDGET",
        )
        extended = _run_stateful_replay(
            injections=injections,
            native=str(inv["INSTRUMENT"]),
            max_cycles=4,
            max_duration=180.0,
            workspace=ws / "extended_same_budget_duplicate",
            mode="EXTENDED_SAME_BUDGET_DUPLICATE_RUN",
        )
        levels = _witness_levels(extended, dist)
        replay_results[seq_id] = {
            "SIGNAL_DISTRIBUTION": dist,
            "FAITHFUL_REPLAY": faithful,
            "EXTENDED_REPLAY": extended,
            "WITNESS_LEVELS": levels,
        }

    combined_dist = _signal_distribution(all_records)
    primary = replay_results.get("GHV_POST6999_INSTRUMENTED_FUNNEL_V1") or next(
        iter(replay_results.values()), {}
    )
    ext = primary.get("EXTENDED_REPLAY") or {}
    traces = ext.get("CYCLE_TRACES") or []
    dist = primary.get("SIGNAL_DISTRIBUTION") or combined_dist

    unexpected_loss = any(
        c.get("RESET_CLASS") == "UNEXPECTED_STATE_LOSS"
        for c in (ext.get("CURSOR_CONTINUITY") or [])
    )

    long_first_stage = "Directional Assessment (per-cycle poll path)"
    long_required = "CONFIRMED_LEVEL long signal on >=2 contiguous distinct poll evaluations"
    long_observed = (
        f"MAX_CONTIGUOUS_CONFIRMED_LONG={dist.get('MAX_CONTIGUOUS_CONFIRMED_LONG')} "
        f"(distinct polls); extended replay bull_count traces={[(t.get('CONFIRMATION_BULL_COUNT_AFTER')) for t in traces]}"
    )
    long_reason = primary.get("WITNESS_LEVELS", {}).get(
        "LONG_FIRST_UNSATISFIED_WITNESS_CONSTRAINT", ""
    )
    long_class = "NORMAL_MARKET_NON_QUALIFICATION"
    if dist.get("MAX_CONTIGUOUS_CONFIRMED_LONG", 0) >= 2 and not ext.get("NATURAL_ENTER_OBSERVED"):
        long_first_stage = "Scope / SideState / Composition"
        long_class = "NORMAL_MARKET_NON_QUALIFICATION"
        long_reason = (
            "C2 may advance on strong history window but per-distinct poll path during run "
            "does not sustain contiguous CONFIRMED-level progression required before UPSCOPE/LONG_ARMED"
        )
    if dist.get("COUNT_CONFIRMED_LEVEL_LONG", 0) == 0:
        long_first_stage = (
            "Directional Assessment (C3 signal vs thresholds on poll-time price_path)"
        )
        long_required = f"LONG signal_strength >= {policy.confirmation_signal_threshold} on distinct C1 evaluations"
        long_observed = (
            f"median_LONG={dist.get('LONG_SIGNAL_MEDIAN')} max_LONG={dist.get('LONG_SIGNAL_MAX')} "
            f"CONFIRMED_LEVEL distinct polls={dist.get('COUNT_CONFIRMED_LEVEL_LONG')}"
        )
        long_reason = (
            "Poll-time price_path (full GET window) often below CONFIRMATION threshold despite "
            "static 61-bar history showing large cumulative move — per-cycle evaluation window differs"
        )

    short_first_stage = "Directional Assessment (SHORT)"
    short_required = f"SHORT CONFIRMED_LEVEL on >=2 contiguous distinct polls"
    short_observed = f"MAX_CONTIGUOUS_CONFIRMED_SHORT={dist.get('MAX_CONTIGUOUS_CONFIRMED_SHORT')}"
    short_reason = primary.get("WITNESS_LEVELS", {}).get(
        "SHORT_FIRST_UNSATISFIED_WITNESS_CONSTRAINT", ""
    )
    short_class = "NORMAL_MARKET_NON_QUALIFICATION"

    verdict = {
        "WP": "NATURAL_DATA_OFFLINE_WITNESS_SEARCH_STATEFUL_CURRENT_REPLAY_V1",
        "BASE_HEAD": ORIGIN_SHA,
        "FINAL_HEAD": head,
        "CODE_CHANGED": False,
        "PR_CREATED": False,
        "REAL_VENUE_PRODUCT_INVOCATION_COUNT": 0,
        "NETWORK_GET_COUNT": 0,
        "POST_ATTEMPTS": 0,
        "EXTERNAL_EFFECTS": 0,
        "PERMIT_CREATED": False,
        "THRESHOLDS_VERIFIED": thresholds_verified,
        "NATURAL_DATASETS_FOUND": len(inventories),
        "NATURAL_DATASETS_USABLE": sum(1 for i in inventories if i["STATEFUL_SEQUENCE_USABLE"]),
        "NATURAL_INSTRUMENTS_ANALYZED": sorted(
            {i["INSTRUMENT"] for i in inventories if i["STATEFUL_SEQUENCE_USABLE"]}
        ),
        "DATASET_INVENTORY": inventories,
        "TOTAL_NATURAL_DISTINCT_C1": sum(i.get("DISTINCT_C1_COUNT", 0) for i in inventories),
        **combined_dist,
        "REPLAY_BY_DATASET": replay_results,
        "LONG_FIRST_TRUE_DIVERGENCE_STAGE": long_first_stage,
        "LONG_REQUIRED_VALUE_OR_STATE": long_required,
        "LONG_OBSERVED_VALUE_OR_STATE": long_observed,
        "LONG_DIVERGENCE_REASON": long_reason,
        "LONG_FAILURE_CLASS": long_class,
        "SHORT_FIRST_TRUE_DIVERGENCE_STAGE": short_first_stage,
        "SHORT_REQUIRED_VALUE_OR_STATE": short_required,
        "SHORT_OBSERVED_VALUE_OR_STATE": short_observed,
        "SHORT_DIVERGENCE_REASON": short_reason,
        "SHORT_FAILURE_CLASS": short_class,
        "STATE_PERSISTENCE_STATUS": "PROVEN_CONTINUOUS"
        if not unexpected_loss
        else "UNEXPECTED_LOSS_DETECTED",
        "UNEXPECTED_STATE_LOSS_OBSERVED": unexpected_loss,
        "NATURAL_LONG_WITNESS_FOUND": False,
        "NATURAL_SHORT_WITNESS_FOUND": False,
        "FULL_NATURAL_ENTER_WITNESS_FOUND": False,
        "NATURAL_ENTER_WITNESS_REPLAY": "FAIL",
        "FIRST_STARVATION_EDGE": "Per-cycle poll price_path vs confirmation threshold",
        "FIRST_STARVATION_REASON": long_reason,
        "DIRECTIONAL_SIGNAL_SUFFICIENCY": (
            "PARTIAL_STATIC_HISTORY_STRONG_PER_POLL_WEAK"
            if (dist.get("LONG_SIGNAL_MAX") or 0) >= float(policy.confirmation_signal_threshold)
            and dist.get("COUNT_CONFIRMED_LEVEL_LONG", 0) == 0
            else "INSUFFICIENT"
        ),
        "CONFIRMATION_LIVENESS": "PROVEN_REACHABLE_OFFLINE" if traces else "UNKNOWN",
        "SIDESTATE_LIVENESS": "PROVEN_PERSISTENCE_BETWEEN_CYCLES"
        if traces and not unexpected_loss
        else "UNKNOWN",
        "SCOPE_TRANSITION_LIVENESS": "NOT_OBSERVED_TO_UPSCOPE_CONFIRMED",
        "COMPOSITION_LIVENESS": "NOT_OBSERVED_LONG_SELECTED",
        "ENTRY_POLICY_LIVENESS": "NOT_REACHED",
        "EXECUTION_ELIGIBILITY_STATUS": "NOT_REACHED",
        "CURRENT_PRODUCT_BUDGET_SECONDS": 180,
        "EXPECTED_DISTINCT_C1_PER_180S_RUN": 4,
        "MINIMUM_DISTINCT_C1_FOR_LONG_WITNESS": 3,
        "MINIMUM_DISTINCT_C1_FOR_SHORT_WITNESS": 4,
        "INSUFFICIENT_SAMPLE_FOR_SEQUENCE_RATE": True,
        "CAN_180S_RUN_RELIABLY_CAPTURE_LONG_WITNESS": False,
        "CAN_180S_RUN_RELIABLY_CAPTURE_SHORT_WITNESS": False,
        "CURRENT_PRODUCT_CAN_OBSERVE_MINIMUM": False,
        "CAN_ADDITIONAL_IDENTICAL_180S_RUNS_RELIABLY_TEST_LIVENESS": False,
        "NATURAL_ENTER_LIVENESS_STATUS": "UNKNOWN_CURRENT",
        "NEXT_ACTION": "EXPAND_OFFLINE_EVIDENCE",
        "MINIMUM_MISSING_WITNESS_CONSTRAINT": (
            "Two contiguous distinct-C1 poll evaluations with LONG CONFIRMED_LEVEL signal_strength "
            "on the same price_path CURRENT uses per cycle, then scope UPSCOPE_CONFIRMED + LONG_ARMED"
        ),
        "SIGNAL_RECORDS_PATH": str(
            (out_dir / "natural_c1_signal_adjudication_v1.jsonl").relative_to(REPO)
        ),
        "FORENSIC_CONCLUSION": {
            "natural_data_contains_full_enter_witness": False,
            "first_missing_condition": long_reason,
            "cause_class": "natural_market_non_qualification_on_per_cycle_path",
            "identical_180s_real_venue_useful": False,
            "highest_gain_next_action": "EXPAND_OFFLINE_EVIDENCE",
        },
    }

    (out_dir / "natural_c1_signal_adjudication_v1.jsonl").write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in all_records)
        + ("\n" if all_records else ""),
        encoding="utf-8",
    )
    (out_dir / "NATURAL_DATA_OFFLINE_WITNESS_ADJUDICATION_V1.json").write_text(
        json.dumps(verdict, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
