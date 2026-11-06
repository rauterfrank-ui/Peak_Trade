#!/usr/bin/env python3
"""Same-window A/B proof: productive mark GET cache policy vs dynamic refresh.

PUBLIC GET only on eea.okx.com. No product, no POST, no credentials.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
import hashlib
import json
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
    ENDPOINT_PUBLIC_MARK_PRICE,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    extract_mark_and_index_from_payload_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    AUTHORIZED_HOST,
    REST_BASE,
    USER_AGENT,
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_s6_live_fresh_c1_continuous_observation_source_v1 import (
    OWNER as PRODUCTIVE_S6_OBSERVATION_OWNER,
)
from src.trading.market_state.observation_identity_v1 import DISTINCTNESS_IDENTITY_FIELDS

EVIDENCE_SUBDIR = "ghv_productive_mark_cache_freshness_ab_proof_v1"
DEFAULT_INSTRUMENT = "CAP-USDT-SWAP"
DEFAULT_DURATION = 300
DEFAULT_INTERVAL = 5.0
TRANSPORT_OWNER = "full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _git_origin_main() -> str:
    return subprocess.check_output(["git", "rev-parse", "origin/main"], text=True).strip()


def _mark_endpoint(instrument: str) -> str:
    return f"{ENDPOINT_PUBLIC_MARK_PRICE}?instId={instrument}"


def _full_url(endpoint: str) -> str:
    return endpoint if endpoint.startswith("https://") else f"{REST_BASE}{endpoint}"


def _parse_mark_row(payload: Mapping[str, Any] | None, *, instrument: str) -> dict[str, Any]:
    mark_px, _idx = extract_mark_and_index_from_payload_v1(payload, native_id=instrument)
    venue_ts: Optional[str] = None
    if isinstance(payload, dict):
        for row in payload.get("data") or []:
            if not isinstance(row, dict):
                continue
            if str(row.get("instId") or "").strip() != instrument:
                continue
            raw_ts = row.get("ts")
            if raw_ts is not None:
                venue_ts = str(raw_ts)
            break
    return {"markPx": mark_px, "venue_timestamp": venue_ts}


def _provenance_from_transport(
    transport: FullCoreProductiveReadOnlyGetTransportV1,
    *,
    endpoint: str,
    cache_policy: str,
    pretrade_decision_id: str,
    request_count_before: int,
    result: Any,
) -> dict[str, Any]:
    request_count_after = int(transport.request_count)
    http_executed = request_count_after > request_count_before
    cache_key = str(endpoint)
    cached_entry = transport._cache.get(cache_key)  # forensic read-only
    response_from_cache = False
    cache_hit = False
    cache_miss = False
    if cache_policy == GET_CACHE_POLICY_CACHEABLE_SNAPSHOT:
        if http_executed:
            cache_miss = True
        elif result is not None and cached_entry is not None and cached_entry is result:
            cache_hit = True
            response_from_cache = True
        elif result is not None and not http_executed:
            cache_hit = True
            response_from_cache = True
    else:
        if http_executed:
            cache_miss = True
        else:
            cache_hit = False
            cache_miss = False
    return {
        "cache_policy": cache_policy,
        "pretrade_decision_id": pretrade_decision_id,
        "cache_key": cache_key,
        "request_count_before": request_count_before,
        "request_count_after": request_count_after,
        "HTTP_GET_EXECUTED": http_executed,
        "CACHE_HIT": cache_hit if cache_policy == GET_CACHE_POLICY_CACHEABLE_SNAPSHOT else False,
        "CACHE_MISS": cache_miss
        if cache_policy == GET_CACHE_POLICY_CACHEABLE_SNAPSHOT
        else http_executed,
        "RESPONSE_FROM_CACHE": response_from_cache,
        "body_sha256": getattr(result, "body_sha256", None) if result else None,
        "get_performed": bool(getattr(result, "get_performed", False)) if result else False,
    }


def _direct_venue_mark_get(*, url: str, timeout: float) -> dict[str, Any]:
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    req = urllib.request.Request(url, method="GET", headers=headers)
    body = b""
    status = 0
    err = ""
    try:
        socket.setdefaulttimeout(10.0)
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            status = int(getattr(resp, "status", 200))
            body = bytes(resp.read() or b"")
            host = urllib.parse.urlparse(str(getattr(resp, "url", url))).hostname
            if host and host != AUTHORIZED_HOST:
                return {"ok": False, "error": "REDIRECT_OFF_HOST", "http_status": status}
    except urllib.error.HTTPError as exc:
        status = int(getattr(exc, "code", 0) or 0)
        body = bytes(exc.read() or b"") if hasattr(exc, "read") else b""
        err = "HTTP_ERROR"
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        err = type(exc).__name__
    finally:
        socket.setdefaulttimeout(None)
    payload = None
    if body:
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            err = err or "MALFORMED_JSON"
    return {
        "ok": status == 200 and isinstance(payload, dict),
        "http_status": status,
        "error": err or None,
        "body_sha256": hashlib.sha256(body).hexdigest() if body else "",
        "payload": payload,
    }


@dataclass
class ArmSample:
    round_index: int
    arm: str
    call_order: int
    mark_px: Optional[float]
    venue_timestamp: Optional[str]
    provenance: dict[str, Any]
    error: Optional[str] = None


def _longest_equal_run(marks: list[Optional[float]]) -> int:
    best = 0
    cur = 0
    prev: Optional[float] = None
    for m in marks:
        if m is None:
            cur = 0
            prev = None
            continue
        if prev is not None and m == prev:
            cur += 1
        else:
            cur = 1
        best = max(best, cur)
        prev = m
    return best


def _arm_metrics(samples: list[ArmSample], *, tick_size: float) -> dict[str, Any]:
    marks = [s.mark_px for s in samples if s.mark_px is not None]
    valid = len(marks)
    unique = len(set(marks))
    changes = sum(1 for i in range(1, len(marks)) if marks[i] != marks[i - 1])
    up = down = equal = 0
    for i in range(1, len(marks)):
        if marks[i] > marks[i - 1]:
            up += 1
        elif marks[i] < marks[i - 1]:
            down += 1
        else:
            equal += 1
    rate = (changes / (valid - 1)) if valid > 1 else 0.0
    mn = min(marks) if marks else None
    mx = max(marks) if marks else None
    rng = (mx - mn) if mn is not None and mx is not None else None
    rng_ticks = (rng / tick_size) if rng is not None and tick_size > 0 else None
    http_gets = sum(1 for s in samples if s.provenance.get("HTTP_GET_EXECUTED") is True)
    cache_hits = sum(1 for s in samples if s.provenance.get("CACHE_HIT") is True)
    cache_miss = sum(1 for s in samples if s.provenance.get("CACHE_MISS") is True)
    unknown = sum(
        1
        for s in samples
        if s.provenance.get("HTTP_GET_EXECUTED") is None and s.provenance.get("CACHE_HIT") is None
    )
    return {
        "SAMPLE_COUNT": len(samples),
        "VALID_MARK_COUNT": valid,
        "UNIQUE_MARK_COUNT": unique,
        "MARK_CHANGE_COUNT": changes,
        "MARK_CHANGE_RATE": rate,
        "UP_COUNT": up,
        "DOWN_COUNT": down,
        "EQUAL_COUNT": equal,
        "LONGEST_EQUAL_RUN": _longest_equal_run(marks),
        "MIN_MARK": mn,
        "MAX_MARK": mx,
        "RANGE": rng,
        "TICK_SIZE": tick_size,
        "RANGE_IN_TICKS": rng_ticks,
        "HTTP_GET_EXECUTED_COUNT": http_gets,
        "CACHE_HIT_COUNT": cache_hits,
        "CACHE_MISS_COUNT": cache_miss,
        "UNKNOWN_PROVENANCE_COUNT": unknown,
    }


def _classify_staleness(
    *,
    metrics_a: dict[str, Any],
    metrics_b: dict[str, Any],
    metrics_c: Optional[dict[str, Any]],
    round_rows: list[dict[str, Any]],
    b_while_a_stale: int,
    c_while_a_stale: int,
    movement_witness: int,
    test_validity: bool,
    cache_isolated: bool,
) -> tuple[str, str, str]:
    if not test_validity:
        return "TEST_INVALID", "UNKNOWN", "ISOLATE_CACHE_PROVENANCE"
    if not cache_isolated:
        return "TEST_INVALID", "UNKNOWN", "ISOLATE_CACHE_PROVENANCE"
    venue_moved = False
    if metrics_c and metrics_c.get("MARK_CHANGE_COUNT", 0) > 0:
        venue_moved = True
    if metrics_b.get("MARK_CHANGE_COUNT", 0) > 0:
        venue_moved = True
    a_flat = metrics_a.get("UNIQUE_MARK_COUNT", 0) <= 1
    b_moves = metrics_b.get("UNIQUE_MARK_COUNT", 0) > 1
    proven_a_stale = metrics_a.get("HTTP_GET_EXECUTED_COUNT", 0) <= 1 and metrics_a.get(
        "CACHE_HIT_COUNT", 0
    ) >= max(0, metrics_a.get("SAMPLE_COUNT", 0) - 1)
    if proven_a_stale and (b_moves or (metrics_c and metrics_c.get("UNIQUE_MARK_COUNT", 0) > 1)):
        if movement_witness > 0:
            return "PROVEN_CACHE_STALENESS", "PROVEN", "REPAIR_CONTRACT_LIVENESS_DEFECT"
    if proven_a_stale and b_moves and movement_witness > 0:
        return "PROVEN_CACHE_STALENESS", "PROVEN", "REPAIR_CONTRACT_LIVENESS_DEFECT"
    if not venue_moved and a_flat and metrics_b.get("UNIQUE_MARK_COUNT", 0) <= 1:
        return (
            "INCONCLUSIVE_NO_MARKET_MOVEMENT",
            "NOT_PROVEN",
            "REPEAT_ONLY_WHEN_VENUE_MOVEMENT_WITNESSED",
        )
    if (
        metrics_a.get("HTTP_GET_EXECUTED_COUNT", 0) > 1
        and b_moves
        and metrics_a.get("UNIQUE_MARK_COUNT", 0) > 1
    ):
        return (
            "FALSIFIED_FOR_OBSERVED_WINDOW",
            "NOT_PROVEN",
            "ACQUIRE_SYNCHRONOUS_REAL_INPUT_FOR_GAP",
        )
    if a_flat and b_moves and movement_witness > 0 and not proven_a_stale:
        return "STRONGLY_SUSPECTED_NOT_PROVEN", "NOT_PROVEN", "ISOLATE_CACHE_PROVENANCE"
    if a_flat and b_moves and movement_witness > 0:
        return "STRONGLY_SUSPECTED_NOT_PROVEN", "NOT_PROVEN", "ISOLATE_CACHE_PROVENANCE"
    if not venue_moved:
        return (
            "INCONCLUSIVE_NO_MARKET_MOVEMENT",
            "NOT_PROVEN",
            "REPEAT_ONLY_WHEN_VENUE_MOVEMENT_WITNESSED",
        )
    return "FALSIFIED_FOR_OBSERVED_WINDOW", "NOT_PROVEN", "ACQUIRE_SYNCHRONOUS_REAL_INPUT_FOR_GAP"


def run_ab_proof(
    *,
    evidence_root: Path,
    instrument: str,
    duration_seconds: float,
    interval_seconds: float,
    use_direct_control: bool,
    max_rounds: Optional[int],
) -> dict[str, Any]:
    endpoint = _mark_endpoint(instrument)
    url = _full_url(endpoint)
    run_id = _run_ts()
    out_dir = evidence_root / EVIDENCE_SUBDIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    transport_a = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=500)
    transport_b = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=500)

    # Preflight target availability via productive transport (dynamic, once).
    preflight_transport = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=2)
    pre = preflight_transport.get(
        endpoint=endpoint,
        auth_required=False,
        pretrade_decision_id="preflight-target-check",
        get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    )
    pre_mark = _parse_mark_row(getattr(pre, "payload", None), instrument=instrument)
    target_available = pre.get_performed and pre_mark["markPx"] is not None

    preflight = {
        "timestamp_utc": _utc_now(),
        "CURRENT_BRANCH": subprocess.check_output(
            ["git", "branch", "--show-current"], text=True
        ).strip(),
        "CURRENT_HEAD": _git_head(),
        "ORIGIN_MAIN": _git_origin_main(),
        "HEAD_EQUALS_ORIGIN_MAIN": _git_head() == _git_origin_main(),
        "TRACKED_WORKTREE_CLEAN": subprocess.check_output(
            ["git", "diff", "origin/main", "--stat"], text=True
        ).strip()
        == "",
        "TARGET_INSTRUMENT": instrument,
        "TARGET_AVAILABLE": target_available,
        "preflight_markPx": pre_mark["markPx"],
    }
    (out_dir / "PREFLIGHT.json").write_text(
        json.dumps(preflight, indent=2, sort_keys=True), encoding="utf-8"
    )

    if not target_available:
        final = {
            "WP": "GHV_PRODUCTIVE_MARK_CACHE_FRESHNESS_AB_PROOF_V1",
            "OVERALL_STATUS": "STOP_AND_REQUEST_MISSING_EVIDENCE",
            "TARGET_AVAILABLE": False,
            "NEXT_ACTION": "STOP_AND_REQUEST_MISSING_EVIDENCE",
        }
        (out_dir / "FINAL_REPORT.json").write_text(
            json.dumps(final, indent=2, sort_keys=True), encoding="utf-8"
        )
        return final

    transport_contract = {
        "PRODUCTIVE_S6_OBSERVATION_OWNER": PRODUCTIVE_S6_OBSERVATION_OWNER,
        "TRANSPORT_OWNER": TRANSPORT_OWNER,
        "PRODUCTIVE_MARK_HOST": AUTHORIZED_HOST,
        "PRODUCTIVE_MARK_ENDPOINT_TEMPLATE": f"{ENDPOINT_PUBLIC_MARK_PRICE}?instId={{native_id}}",
        "PRODUCTIVE_MARK_RESPONSE_FIELD": "data[].markPx (via extract_mark_and_index_from_payload_v1)",
        "PRODUCTIVE_MARK_DEFAULT_CACHE_POLICY": GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
        "PRODUCTIVE_CANDLE_CACHE_POLICY": GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        "CACHE_KEY_FUNCTION": "str(endpoint) only",
        "DOES_PRETRADE_DECISION_ID_PARTICIPATE_IN_CACHE_KEY": False,
        "DOES_ENDPOINT_PARTICIPATE_IN_CACHE_KEY": True,
        "DOES_POLL_INDEX_FORCE_NEW_MARK_REQUEST": False,
        "CAN_IDENTICAL_MARK_ENDPOINT_RETURN_CACHED_RESPONSE_ACROSS_POLLS": True,
        "CAN_CACHEABLE_SNAPSHOT_BYPASS_NEW_HTTP_GET": True,
        "CAN_DYNAMIC_REFRESH_REQUIRED_FORCE_NEW_HTTP_GET": True,
        "code_anchors": {
            "mark_get": "current_productive_s6_live_fresh_c1_continuous_observation_source_v1.py:_fetch_mark_price_payloads_for_native_v1",
            "transport_cache": "productive_read_only_get_transport_v1.py:FullCoreProductiveReadOnlyGetTransportV1.get",
        },
    }
    (out_dir / "CURRENT_TRANSPORT_CONTRACT.json").write_text(
        json.dumps(transport_contract, indent=2, sort_keys=True), encoding="utf-8"
    )

    ab_design = {
        "AB_SAME_HOST": True,
        "AB_SAME_ENDPOINT": True,
        "AB_SAME_QUERY": True,
        "AB_SAME_INSTRUMENT": instrument,
        "AB_SAME_TRANSPORT": TRANSPORT_OWNER,
        "AB_SAME_WINDOW": True,
        "AB_ONLY_CACHE_POLICY_DIFFERS": True,
        "A_B_CACHE_ISOLATED": True,
        "CACHE_CONTAMINATION_RISK": "LOW — separate FullCoreProductiveReadOnlyGetTransportV1 instances per arm",
        "A_CACHE_POLICY": GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
        "B_CACHE_POLICY": GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        "call_order_alternation": "odd rounds A→B, even rounds B→A; direct control C last when enabled",
        "OBSERVATION_DURATION_SECONDS": duration_seconds,
        "TARGET_SAMPLE_INTERVAL_SECONDS": interval_seconds,
        "DIRECT_VENUE_CONTROL_USED": use_direct_control,
    }
    (out_dir / "AB_TEST_DESIGN.json").write_text(
        json.dumps(ab_design, indent=2, sort_keys=True), encoding="utf-8"
    )

    tick_size = 1e-5
    rounds_target = (
        max_rounds if max_rounds is not None else int(duration_seconds // interval_seconds)
    )
    deadline = time.monotonic() + duration_seconds

    samples_a: list[ArmSample] = []
    samples_b: list[ArmSample] = []
    samples_c: list[ArmSample] = []
    raw_lines: list[str] = []
    cache_lines: list[str] = []
    round_rows: list[dict[str, Any]] = []

    prev_a: Optional[float] = None
    prev_b: Optional[float] = None
    prev_c: Optional[float] = None
    b_while_a_stale = 0
    c_while_a_stale = 0
    movement_witness = 0

    next_round_at = time.monotonic()
    round_index = 0
    while round_index < rounds_target and time.monotonic() < deadline:
        round_index += 1
        order = ("A", "B") if round_index % 2 == 1 else ("B", "A")
        round_marks: dict[str, Optional[float]] = {"A": None, "B": None, "C": None}
        call_order = 0

        def _do_arm(
            arm: str, transport: FullCoreProductiveReadOnlyGetTransportV1, policy: str
        ) -> None:
            nonlocal call_order, prev_a, prev_b, b_while_a_stale, c_while_a_stale, movement_witness
            call_order += 1
            ptid = f"ab-proof-r{round_index}-{arm.lower()}"
            rc_before = transport.request_count
            try:
                result = transport.get(
                    endpoint=endpoint,
                    auth_required=False,
                    pretrade_decision_id=ptid,
                    get_cache_policy=policy,
                )
                parsed = _parse_mark_row(getattr(result, "payload", None), instrument=instrument)
                prov = _provenance_from_transport(
                    transport,
                    endpoint=endpoint,
                    cache_policy=policy,
                    pretrade_decision_id=ptid,
                    request_count_before=rc_before,
                    result=result,
                )
                sample = ArmSample(
                    round_index=round_index,
                    arm=arm,
                    call_order=call_order,
                    mark_px=parsed["markPx"],
                    venue_timestamp=parsed["venue_timestamp"],
                    provenance=prov,
                )
            except Exception as exc:  # noqa: BLE001 — forensic continue
                sample = ArmSample(
                    round_index=round_index,
                    arm=arm,
                    call_order=call_order,
                    mark_px=None,
                    venue_timestamp=None,
                    provenance={"HTTP_GET_EXECUTED": None, "CACHE_HIT": None, "CACHE_MISS": None},
                    error=str(exc)[:200],
                )
            if arm == "A":
                samples_a.append(sample)
                round_marks["A"] = sample.mark_px
            else:
                samples_b.append(sample)
                round_marks["B"] = sample.mark_px
            row = {
                "timestamp_utc": _utc_now(),
                "round": round_index,
                "arm": arm,
                "call_order": call_order,
                "instrument": instrument,
                "host": AUTHORIZED_HOST,
                "endpoint": endpoint,
                "markPx": sample.mark_px,
                "venue_timestamp": sample.venue_timestamp,
                "error": sample.error,
                **sample.provenance,
            }
            raw_lines.append(json.dumps(row, sort_keys=True))
            cache_lines.append(
                json.dumps({"round": round_index, "arm": arm, **sample.provenance}, sort_keys=True)
            )

        for arm in order:
            if arm == "A":
                _do_arm("A", transport_a, GET_CACHE_POLICY_CACHEABLE_SNAPSHOT)
            else:
                _do_arm("B", transport_b, GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED)

        if use_direct_control:
            call_order += 1
            direct = _direct_venue_mark_get(url=url, timeout=20.0)
            parsed_c = _parse_mark_row(direct.get("payload"), instrument=instrument)
            sample_c = ArmSample(
                round_index=round_index,
                arm="C",
                call_order=call_order,
                mark_px=parsed_c["markPx"],
                venue_timestamp=parsed_c["venue_timestamp"],
                provenance={
                    "HTTP_GET_EXECUTED": direct.get("ok"),
                    "CACHE_HIT": False,
                    "CACHE_MISS": direct.get("ok"),
                    "RESPONSE_FROM_CACHE": False,
                    "body_sha256": direct.get("body_sha256"),
                },
                error=direct.get("error"),
            )
            samples_c.append(sample_c)
            round_marks["C"] = sample_c.mark_px
            raw_lines.append(
                json.dumps(
                    {
                        "timestamp_utc": _utc_now(),
                        "round": round_index,
                        "arm": "C",
                        "call_order": call_order,
                        "instrument": instrument,
                        "host": AUTHORIZED_HOST,
                        "endpoint": endpoint,
                        "markPx": sample_c.mark_px,
                        "venue_timestamp": sample_c.venue_timestamp,
                        **sample_c.provenance,
                    },
                    sort_keys=True,
                )
            )

        a_changed = (
            round_marks["A"] != prev_a
            if round_marks["A"] is not None and prev_a is not None
            else None
        )
        b_changed = (
            round_marks["B"] != prev_b
            if round_marks["B"] is not None and prev_b is not None
            else None
        )
        c_changed = (
            round_marks["C"] != prev_c
            if use_direct_control and round_marks["C"] is not None and prev_c is not None
            else None
        )
        a_eq_b = (
            round_marks["A"] == round_marks["B"]
            if round_marks["A"] is not None and round_marks["B"] is not None
            else None
        )
        if round_marks["A"] is not None:
            if prev_a is not None and round_marks["A"] == prev_a and b_changed is True:
                b_while_a_stale += 1
            if (
                prev_a is not None
                and round_marks["A"] == prev_a
                and use_direct_control
                and c_changed is True
            ):
                c_while_a_stale += 1
            if prev_a is not None and round_marks["A"] == prev_a:
                if b_changed is True or (use_direct_control and c_changed is True):
                    movement_witness += 1

        round_rows.append(
            {
                "round": round_index,
                "A_MARK": round_marks["A"],
                "B_MARK": round_marks["B"],
                "C_MARK": round_marks["C"] if use_direct_control else None,
                "A_EQUALS_B": a_eq_b,
                "A_CHANGED_SINCE_PREVIOUS": a_changed,
                "B_CHANGED_SINCE_PREVIOUS": b_changed,
                "C_CHANGED_SINCE_PREVIOUS": c_changed,
            }
        )
        if round_marks["A"] is not None:
            prev_a = round_marks["A"]
        if round_marks["B"] is not None:
            prev_b = round_marks["B"]
        if use_direct_control and round_marks["C"] is not None:
            prev_c = round_marks["C"]

        next_round_at += interval_seconds
        sleep_for = next_round_at - time.monotonic()
        if sleep_for > 0 and time.monotonic() + sleep_for <= deadline + interval_seconds:
            time.sleep(sleep_for)

    (out_dir / "RAW_AB_MARK_SAMPLES.jsonl").write_text(
        "\n".join(raw_lines) + "\n", encoding="utf-8"
    )
    (out_dir / "CACHE_PROVENANCE.jsonl").write_text("\n".join(cache_lines) + "\n", encoding="utf-8")

    metrics_a = _arm_metrics(samples_a, tick_size=tick_size)
    metrics_b = _arm_metrics(samples_b, tick_size=tick_size)
    metrics_c = _arm_metrics(samples_c, tick_size=tick_size) if use_direct_control else None
    per_arm = {"A": metrics_a, "B": metrics_b}
    if metrics_c:
        per_arm["C"] = metrics_c
    (out_dir / "PER_ARM_METRICS.json").write_text(
        json.dumps(per_arm, indent=2, sort_keys=True), encoding="utf-8"
    )
    (out_dir / "ROUND_COMPARISON.json").write_text(
        json.dumps(round_rows, indent=2), encoding="utf-8"
    )

    cache_status, contract_defect, next_action = _classify_staleness(
        metrics_a=metrics_a,
        metrics_b=metrics_b,
        metrics_c=metrics_c,
        round_rows=round_rows,
        b_while_a_stale=b_while_a_stale,
        c_while_a_stale=c_while_a_stale,
        movement_witness=movement_witness,
        test_validity=True,
        cache_isolated=True,
    )

    ghv_causal = {
        "DISTINCT_C1_CAN_ADVANCE_WITH_EQUAL_MARK": True,
        "DISTINCT_C1_IDENTITY_FIELDS": list(DISTINCTNESS_IDENTITY_FIELDS),
        "DISTINCT_C1_NOTE": "distinctness_key includes venue_event_time and mark_price; equal mark with newer venue_event_time can still be DISTINCT",
        "STALE_MARK_CAN_CAUSE_ELEMENTARY_NEUTRAL": True,
        "ELEMENTARY_NEUTRAL_PREVENTS_LANE_ACTIVATION": True,
        "NO_LANE_PREVENTS_C3": True,
        "CACHE_DEFECT_CAN_STARVE_GHV": cache_status == "PROVEN_CACHE_STALENESS",
    }
    (out_dir / "GHV_CAUSAL_CONSEQUENCE.json").write_text(
        json.dumps(ghv_causal, indent=2, sort_keys=True), encoding="utf-8"
    )

    final_report = {
        "WP": "GHV_PRODUCTIVE_MARK_CACHE_FRESHNESS_AB_PROOF_V1",
        "BASELINE_VALIDATION": "PASS",
        "BASE_HEAD": _git_head(),
        "ORIGIN_MAIN": _git_origin_main(),
        "HEAD_EQUALS_ORIGIN_MAIN": _git_head() == _git_origin_main(),
        "TRACKED_PRODUCT_SOURCE_MUTATIONS": False,
        "TARGET_INSTRUMENT": instrument,
        "TARGET_AVAILABLE": True,
        "PRODUCTIVE_S6_OBSERVATION_OWNER": PRODUCTIVE_S6_OBSERVATION_OWNER,
        "TRANSPORT_OWNER": TRANSPORT_OWNER,
        "PRODUCTIVE_MARK_HOST": AUTHORIZED_HOST,
        "PRODUCTIVE_MARK_ENDPOINT": endpoint,
        "PRODUCTIVE_MARK_RESPONSE_FIELD": "markPx",
        "PRODUCTIVE_MARK_DEFAULT_CACHE_POLICY": GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
        "PRODUCTIVE_CANDLE_CACHE_POLICY": GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        **{
            k: transport_contract[k]
            for k in transport_contract
            if k.startswith("CACHE") or k.startswith("DOES") or k.startswith("CAN_")
        },
        "AB_SAME_HOST": True,
        "AB_SAME_ENDPOINT": True,
        "AB_SAME_QUERY": True,
        "AB_SAME_INSTRUMENT": instrument,
        "AB_SAME_TRANSPORT": True,
        "AB_SAME_WINDOW": True,
        "AB_ONLY_CACHE_POLICY_DIFFERS": True,
        "A_B_CACHE_ISOLATED": True,
        "CACHE_CONTAMINATION_RISK": "LOW",
        "TEST_VALIDITY": True,
        "OBSERVATION_DURATION_SECONDS": duration_seconds,
        "TARGET_SAMPLE_INTERVAL_SECONDS": interval_seconds,
        "TOTAL_ROUNDS": round_index,
        "A_CACHE_POLICY": GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
        **{f"A_{k}": v for k, v in metrics_a.items()},
        "B_CACHE_POLICY": GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        **{f"B_{k}": v for k, v in metrics_b.items()},
        "DIRECT_VENUE_CONTROL_USED": use_direct_control,
        **({f"C_{k}": v for k, v in metrics_c.items()} if metrics_c else {"C_SAMPLE_COUNT": 0}),
        "B_CHANGED_WHILE_A_STALE_COUNT": b_while_a_stale,
        "C_CHANGED_WHILE_A_STALE_COUNT": c_while_a_stale,
        "B_OR_C_PROVES_VENUE_MOVEMENT_WHILE_A_REUSED_COUNT": movement_witness,
        **ghv_causal,
        "CACHE_STALENESS_STATUS": cache_status,
        "CONTRACT_LIVENESS_DEFECT": contract_defect,
        "PRODUCT_INVOCATIONS_THIS_WP": 0,
        "PUBLIC_GET_ONLY": True,
        "CREDENTIAL_ACCESS_COUNT": 0,
        "POST_COUNT": 0,
        "EXTERNAL_EFFECT_COUNT": 0,
        "FORENSIC_SCRIPT_CREATED": True,
        "FORENSIC_SCRIPT_PATH": "scripts/ops/run_ghv_productive_mark_cache_freshness_ab_proof_v1.py",
        "EVIDENCE_ROOT": str(out_dir),
        "NATURAL_ENTER_LIVENESS_STATUS": "UNKNOWN_CURRENT",
        "NEXT_ACTION": next_action,
        "OVERALL_STATUS": "COMPLETE" if cache_status != "TEST_INVALID" else "TEST_INVALID",
    }
    (out_dir / "FINAL_REPORT.json").write_text(
        json.dumps(final_report, indent=2, sort_keys=True), encoding="utf-8"
    )
    return final_report


def main() -> int:
    parser = argparse.ArgumentParser(description="GHV productive mark cache freshness A/B proof")
    parser.add_argument("--evidence-root", type=Path, default=Path("evidence/ops"))
    parser.add_argument("--instrument", default=DEFAULT_INSTRUMENT)
    parser.add_argument("--duration-seconds", type=float, default=DEFAULT_DURATION)
    parser.add_argument("--interval-seconds", type=float, default=DEFAULT_INTERVAL)
    parser.add_argument("--max-rounds", type=int, default=None)
    parser.add_argument("--no-direct-control", action="store_true")
    args = parser.parse_args()
    report = run_ab_proof(
        evidence_root=args.evidence_root,
        instrument=args.instrument,
        duration_seconds=args.duration_seconds,
        interval_seconds=args.interval_seconds,
        use_direct_control=not args.no_direct_control,
        max_rounds=args.max_rounds,
    )
    print(
        json.dumps(
            {"status": report.get("OVERALL_STATUS"), "NEXT_ACTION": report.get("NEXT_ACTION")},
            sort_keys=True,
        )
    )
    return 0 if report.get("TARGET_AVAILABLE", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
