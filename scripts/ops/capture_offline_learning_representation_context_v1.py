"""Capture or replay one bounded ETH market context for Phase 22 B0/B1 research."""

import argparse
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import fcntl
from http.client import HTTPSConnection
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from urllib.parse import urlencode

from scripts.ops.capture_offline_learning_mark_window_v1 import (
    _read_manifest as _read_mark_manifest,
    _sha,
    _sync_directory,
    _utc_now,
    _write,
    read_captured_mark_archive_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.context_admission_v1 import (
    ContextAdmissionPolicyV1,
    FactAdmissionReceiptV1,
    compose_admitted_market_context_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    MarketIdentityV1,
    assert_offline_v1,
    bytes_v1,
    digest_v1,
    instant_v1,
    require_v1,
    seal_v1,
    strict_json_v1,
    validate_seal_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_existing_fact_materialization_v1 import (
    ExistingFactMaterializationRequestV1,
    GovernedCanonicalFactV1,
    WP_A_PRODUCER,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_recorded_market_replay_v1 import (
    compose_recorded_market_context_v1,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import (
    HTTP_MAX_RESPONSE_BYTES,
    HTTP_TIMEOUT_SECONDS,
    PUBLIC_HTTP_HOST,
    PT1M_STEP_MS,
)
from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import TRADES_REST_PATH
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import (
    DataQualityStateV1,
    InstrumentRefV1,
    MarketFactProvenanceV1,
    MarketTimestampV1,
    OhlcvIntervalFactV1,
    TradeFactV1,
    fact_digest,
)
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0 import (
    REQUIRED_WARMUP_ROWS,
)
from src.research.offline_recorded_mark_horizon_source_v1 import (
    LEGACY_NATIVE_INSTRUMENT as NATIVE_INSTRUMENT,
)
from src.research.offline_recorded_mark_horizon_source_v1 import read_bound_json

SCHEMA = "recorded_b0_b1_market_context_v1"
INSTRUMENT = "inst-eth-usdt-perp"
PRICE_UNIT = "USDT per ETH"
INSTRUMENTS_PATH = "/api/v5/public/instruments"
CANDLES_PATH = "/api/v5/market/history-candles"
_QUALITY = DataQualityStateV1(True, False, False, False, False, False, False, False)
_AGE_ROLES = {"price_o4", "flow", "microstructure"}


def _utc_from_ms(value):
    return datetime.fromtimestamp(value / 1000, timezone.utc).isoformat().replace("+00:00", "Z")


def _requests(plan):
    instrument = {"instId": NATIVE_INSTRUMENT}
    return {
        "instrument": (INSTRUMENTS_PATH, {**instrument, "instType": "SWAP"}),
        "ohlcv": (
            CANDLES_PATH,
            {
                **instrument,
                "bar": "1m",
                "after": str(plan["ohlcv_end_ms"]),
                "limit": str(REQUIRED_WARMUP_ROWS),
            },
        ),
        "trades": (TRADES_REST_PATH, {**instrument, "limit": str(plan["trade_count"])}),
    }


def _public_get(path, query):
    require_v1(path in {INSTRUMENTS_PATH, CANDLES_PATH, TRADES_REST_PATH}, "PUBLIC_PATH_REQUIRED")
    with closing(HTTPSConnection(PUBLIC_HTTP_HOST, timeout=HTTP_TIMEOUT_SECONDS)) as connection:
        connection.request(
            "GET", f"{path}?{urlencode(query)}", headers={"Accept": "application/json"}
        )
        with connection.getresponse() as response:
            return response.status, response.read(HTTP_MAX_RESPONSE_BYTES + 1)


def _number(value, *, allow_zero=False):
    require_v1(
        isinstance(value, str)
        and re.fullmatch(r"[0-9]{1,24}(?:\.[0-9]{1,24})?", value) is not None,
        "OKX_DECIMAL_REQUIRED",
    )
    result = Decimal(value)
    require_v1(allow_zero or result > 0, "OKX_POSITIVE_DECIMAL_REQUIRED")
    return result


def _epoch_ms(value):
    require_v1(
        isinstance(value, str) and re.fullmatch(r"[0-9]{13}", value) is not None,
        "OKX_TIMESTAMP_REQUIRED",
    )
    return int(value)


def _rows(payload):
    require_v1(
        isinstance(payload, dict)
        and payload.get("code") == "0"
        and isinstance(payload.get("data"), list),
        "OKX_PUBLIC_RESPONSE_INVALID",
    )
    return payload["data"]


def _instrument(rows, mark_binding):
    require_v1(len(rows) == 1 and isinstance(rows[0], dict), "EXACT_OKX_INSTRUMENT_REQUIRED")
    instrument = rows[0]
    expected = {
        "instId": NATIVE_INSTRUMENT,
        "instType": "SWAP",
        "uly": "ETH-USDT",
        "instFamily": "ETH-USDT",
        "ctType": "linear",
        "ctValCcy": "ETH",
        "settleCcy": "USDT",
        "state": "live",
    }
    require_v1(
        all(instrument.get(key) == value for key, value in expected.items()),
        "OKX_LINEAR_ETH_SWAP_REQUIRED",
    )
    face_value = _number(instrument.get("ctVal"))
    require_v1(
        _number(instrument.get("ctMult")) == 1
        and face_value == _number(mark_binding["instrument_metadata"].get("ctVal"))
        and mark_binding["instrument_metadata"].get("ctValCcy") == "ETH",
        "OKX_CONTRACT_VALUE_MISMATCH",
    )
    return face_value


def _fact_provenance(record):
    return MarketFactProvenanceV1(
        "rest", record["path"], record["raw_sha256"], record["raw_sha256"], PUBLIC_HTTP_HOST
    )


def _trade_facts(rows, *, plan, instrument, face_value, record, observed_at):
    require_v1(len(rows) == plan["trade_count"], "OKX_TRADE_COUNT_MISMATCH")
    provenance = _fact_provenance(record)
    received = record["received_at_utc"]
    max_age = plan["max_age_seconds_by_role"]["flow"]
    trades = []
    ids = set()
    for row in rows:
        require_v1(
            isinstance(row, dict) and row.get("instId") == NATIVE_INSTRUMENT,
            "OKX_TRADE_INSTRUMENT_MISMATCH",
        )
        trade_id = row.get("tradeId")
        require_v1(
            isinstance(trade_id, str)
            and re.fullmatch(r"[1-9][0-9]*", trade_id) is not None
            and trade_id not in ids
            and row.get("side") in {"buy", "sell"},
            "OKX_TRADE_ID_OR_SIDE_INVALID",
        )
        ids.add(trade_id)
        event_ms = _epoch_ms(row.get("ts"))
        event_utc = _utc_from_ms(event_ms)
        event = instant_v1(event_utc)
        require_v1(
            event <= instant_v1(received)
            and (instant_v1(observed_at) - event).total_seconds() <= max_age,
            "OKX_TRADE_OUTSIDE_KNOWLEDGE_WINDOW",
        )
        _number(row.get("px"))
        # The reported SWAP size is contracts. Both decimal operands have at most 48 digits.
        with localcontext() as precision:
            precision.prec = 96
            base_size = format(_number(row.get("sz")) * face_value, "f")
        trades.append(
            TradeFactV1(
                instrument,
                trade_id,
                row["px"],
                base_size,
                row["side"],
                MarketTimestampV1(event_ms, received, event_utc, "venue_event_ms"),
                provenance,
                _QUALITY,
            )
        )
    return sorted(
        trades, key=lambda fact: (fact.timestamps.venue_event_time_ms, int(fact.trade_id))
    )


def _candle_facts(rows, *, plan, instrument, record):
    provenance = _fact_provenance(record)
    received = record["received_at_utc"]
    end = plan["ohlcv_end_ms"]
    require_v1(
        instant_v1(_utc_from_ms(end)) <= instant_v1(record["requested_at_utc"]),
        "OHLCV_REQUEST_BEFORE_WINDOW_CLOSE",
    )
    expected = set(range(end - REQUIRED_WARMUP_ROWS * PT1M_STEP_MS, end, PT1M_STEP_MS))
    bars = {}
    for row in rows:
        require_v1(
            isinstance(row, list) and len(row) == 9 and row[8] == "1",
            "OKX_FINAL_OHLCV_ROW_REQUIRED",
        )
        opened, open_px, high_px, low_px, close_px, _, base_volume, _, confirm = row
        start = _epoch_ms(opened)
        low, high = _number(low_px), _number(high_px)
        require_v1(
            start in expected
            and start not in bars
            and low <= _number(open_px) <= high
            and low <= _number(close_px) <= high
            and instant_v1(_utc_from_ms(start + PT1M_STEP_MS)) <= instant_v1(received),
            "OKX_OHLCV_GRID_OR_PRICES_INVALID",
        )
        _number(base_volume, allow_zero=True)
        bars[start] = OhlcvIntervalFactV1(
            instrument,
            "PT1M",
            open_px,
            high_px,
            low_px,
            close_px,
            base_volume,
            "base",
            "last_trade",
            start,
            confirm,
            MarketTimestampV1(start, received, _utc_from_ms(start), "venue_interval_open_ms"),
            provenance,
            _QUALITY,
        )
    require_v1(set(bars) == expected, "OKX_OHLCV_WINDOW_INCOMPLETE")
    return [bars[start] for start in sorted(bars)]


def _read_capture(root):
    return validate_seal_v1(strict_json_v1((root / "context_capture.json").read_bytes()), SCHEMA)


def read_recorded_representation_context_v1(root, *, cutoff_utc):
    """Recompose the same context from original bytes at its recorded knowledge time."""
    assert_offline_v1()
    root = Path(root)
    manifest = _read_capture(root)
    plan = manifest["plan"]
    records = manifest["records"]
    observed_at = manifest["available_at_utc"]
    require_v1(
        instant_v1(observed_at) <= instant_v1(cutoff_utc),
        "REPRESENTATION_CAPTURE_NOT_YET_AVAILABLE",
    )
    expected = _requests(plan)
    require_v1(set(records) == set(expected), "EXACT_REPRESENTATION_RESPONSES_REQUIRED")
    original = {}
    for name, (path, query) in expected.items():
        record = records[name]
        require_v1(
            record["path"] == path
            and record["query"] == query
            and record["host"] == PUBLIC_HTTP_HOST
            and record["http_status"] == 200
            and instant_v1(record["requested_at_utc"])
            <= instant_v1(record["received_at_utc"])
            <= instant_v1(observed_at),
            "REPRESENTATION_RESPONSE_PROVENANCE_MISMATCH",
        )
        raw = (root / f"{name}.json").read_bytes()
        require_v1(_sha(raw) == record["raw_sha256"], "SOURCE_SHA256_MISMATCH")
        original[name] = _rows(strict_json_v1(raw))
    mark_root = Path(plan["mark_archive"])
    mark_manifest = _read_mark_manifest(mark_root)
    require_v1(
        mark_manifest["exact_content_digest"] == plan["mark_manifest_digest"],
        "REPRESENTATION_MARK_ARCHIVE_MISMATCH",
    )
    require_v1(
        instant_v1(observed_at)
        == max(
            instant_v1(mark_manifest["available_at_utc"]),
            *(instant_v1(record["received_at_utc"]) for record in records.values()),
        ),
        "REPRESENTATION_KNOWLEDGE_CLOCK_MISMATCH",
    )
    archive = read_captured_mark_archive_v1(mark_root)
    binding = read_bound_json(archive.binding_path, archive.binding_sha256)
    face_value = _instrument(original["instrument"], binding)
    generation = digest_v1(
        {
            "trade_count": plan["trade_count"],
            "max_age_seconds_by_role": plan["max_age_seconds_by_role"],
            "contract_face_value_eth": str(face_value.normalize()),
        }
    )
    identity = MarketIdentityV1(
        "offline-okx-eea-b0-b1-v1." + generation, "OKX", INSTRUMENT, NATIVE_INSTRUMENT
    )
    market_instrument = InstrumentRefV1(
        INSTRUMENT, NATIVE_INSTRUMENT, "OKX", "SWAP", "USDT", archive.binding_sha256
    )
    policy = ContextAdmissionPolicyV1(
        "explicit-public-b0-b1-v1",
        plan["max_age_seconds_by_role"],
        ("price_state_ref", "flow_state_ref", "liquidity_microstructure_state_ref"),
    )
    price = compose_recorded_market_context_v1(
        archive=archive,
        identity=identity,
        bar_open_utc=_utc_from_ms(plan["ohlcv_end_ms"] // 3_600_000 * 3_600_000 - 3_600_000),
        observed_at=observed_at,
        policy=ContextAdmissionPolicyV1(
            policy.policy_ref, policy.max_age_seconds_by_role, ("price_state_ref",)
        ),
    )["source_bindings"][0]
    mark = GovernedCanonicalFactV1(
        price["fact_kind"], price["fact_digest"], price["payload"], price["producer_owner"]
    )
    receipts = {
        mark.fact_digest: FactAdmissionReceiptV1(
            price["source_ref"],
            identity.dataset_generation,
            price["original_payload_json"].encode("utf-8"),
            price["known_at"],
            price["available_at"],
            price["units"],
        )
    }
    capture_ref = "archive.sha256:" + manifest["exact_content_digest"]

    def admit(facts, role, units):
        admitted = []
        received = records[role]["received_at_utc"]
        for fact in facts:
            payload = fact.to_dict()
            digest = fact_digest(payload)
            receipts[digest] = FactAdmissionReceiptV1(
                capture_ref + ":" + role,
                identity.dataset_generation,
                bytes_v1(payload),
                received,
                received,
                units,
            )
            admitted.append(GovernedCanonicalFactV1(fact.fact_kind, digest, payload, WP_A_PRODUCER))
        return admitted

    trades = _trade_facts(
        original["trades"],
        plan=plan,
        instrument=market_instrument,
        face_value=face_value,
        record=records["trades"],
        observed_at=observed_at,
    )
    bars = _candle_facts(
        original["ohlcv"], plan=plan, instrument=market_instrument, record=records["ohlcv"]
    )
    context = compose_admitted_market_context_v1(
        identity=identity,
        request=ExistingFactMaterializationRequestV1(
            observed_at,
            INSTRUMENT,
            (price["source_ref"], capture_ref),
            price_o4_bar_fact=mark,
            trade_facts=admit(trades, "trades", {"price": PRICE_UNIT, "size": "BASE"}),
            ohlcv_facts=admit(bars, "ohlcv", {"price": PRICE_UNIT, "volume": "BASE"}),
        ),
        receipts_by_digest=receipts,
        policy=policy,
    )
    require_v1(context["context_status"] == "VALID", "B0_B1_CONTEXT_INCOMPLETE")
    return context


def capture_representation_context_v1(
    *, output, mark_archive, ohlcv_end_utc, trade_count, max_age_seconds_by_role, fetch=_public_get
):
    """Publish only an admitted three-family context with all response bytes."""
    assert_offline_v1()
    end = instant_v1(ohlcv_end_utc)
    require_v1(not (end.second or end.microsecond), "OHLCV_MINUTE_BOUNDARY_REQUIRED")
    require_v1(
        type(trade_count) is int and 1 <= trade_count <= 500, "EXPLICIT_TRADE_COUNT_REQUIRED"
    )
    require_v1(
        set(max_age_seconds_by_role) == _AGE_ROLES
        and all(type(age) is int and age > 0 for age in max_age_seconds_by_role.values()),
        "EXPLICIT_CONTEXT_FRESHNESS_REQUIRED",
    )
    mark_archive = Path(mark_archive).resolve()
    mark_manifest = _read_mark_manifest(mark_archive)
    plan = {
        "mark_archive": str(mark_archive),
        "mark_manifest_digest": mark_manifest["exact_content_digest"],
        "ohlcv_end_ms": int(end.timestamp()) * 1000,
        "trade_count": trade_count,
        "max_age_seconds_by_role": dict(max_age_seconds_by_role),
    }
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with (output.parent / f".{output.name}.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if output.exists():
            saved = _read_capture(output)
            require_v1(saved["plan"] == plan, "REPRESENTATION_CAPTURE_PLAN_CONFLICT")
            return read_recorded_representation_context_v1(output, cutoff_utc=_utc_now())
        require_v1(end <= instant_v1(_utc_now()), "OHLCV_WINDOW_NOT_CLOSED")
        with TemporaryDirectory(prefix=".representation-capture-", dir=output.parent) as temporary:
            stage = Path(temporary) / "archive"
            stage.mkdir()
            records = {}
            for name, (path, query) in _requests(plan).items():
                requested = _utc_now()
                status, raw = fetch(path, query)
                received = _utc_now()
                require_v1(
                    status == 200 and len(raw) <= HTTP_MAX_RESPONSE_BYTES,
                    "OKX_PUBLIC_CAPTURE_FAILED",
                )
                records[name] = {
                    "path": path,
                    "query": query,
                    "host": PUBLIC_HTTP_HOST,
                    "http_status": status,
                    "requested_at_utc": requested,
                    "received_at_utc": received,
                    "raw_sha256": _sha(raw),
                }
                _write(stage / f"{name}.json", raw)
            observed_at = max(
                mark_manifest["available_at_utc"],
                *(record["received_at_utc"] for record in records.values()),
                key=instant_v1,
            )
            manifest = seal_v1(
                {
                    "schema_version": SCHEMA,
                    "authority": "NONE",
                    "available_at_utc": observed_at,
                    "plan": plan,
                    "records": records,
                }
            )
            _write(stage / "context_capture.json", bytes_v1(manifest))
            context = read_recorded_representation_context_v1(stage, cutoff_utc=_utc_now())
            _sync_directory(stage)
            os.rename(stage, output)
            _sync_directory(output.parent)
            return context


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture")
    capture.add_argument("--output", required=True, type=Path)
    capture.add_argument("--mark-archive", required=True, type=Path)
    capture.add_argument("--ohlcv-end-utc", required=True)
    capture.add_argument("--trade-count", required=True, type=int)
    capture.add_argument("--mark-max-age-seconds", required=True, type=int)
    capture.add_argument("--trade-max-age-seconds", required=True, type=int)
    capture.add_argument("--ohlcv-max-age-seconds", required=True, type=int)
    replay = commands.add_parser("read")
    replay.add_argument("--root", required=True, type=Path)
    replay.add_argument("--cutoff-utc", required=True)
    args = vars(parser.parse_args())
    if args.pop("command") == "read":
        context = read_recorded_representation_context_v1(**args)
    else:
        args["max_age_seconds_by_role"] = {
            "price_o4": args.pop("mark_max_age_seconds"),
            "flow": args.pop("trade_max_age_seconds"),
            "microstructure": args.pop("ohlcv_max_age_seconds"),
        }
        context = capture_representation_context_v1(**args)
    print(bytes_v1(context).decode())


if __name__ == "__main__":
    main()
