"""Explicit public acquisition for a later fixed-slot entry; never started by prepare."""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, replace
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from threading import Lock
import time
from urllib.parse import urlsplit

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.acquire_v1 import (
    acquire_eea_universe_inventory_v1,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.transport_v1 import (
    UrllibEeaPublicUniverseGetTransportV1,
)
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (
    MARK_ENDPOINT_PATH,
    TICKER_ENDPOINT_PATH,
    OkxPublicEconomicMdReadAdapterV1,
    _default_public_get,
)
from src.ops.economic_md_input_producer_v1.universe_gate_v1 import (
    load_cap21_eligible_instruments_v1,
)
from src.ops.governed_futures_universe_producer_v1 import run_governed_futures_universe_producer_v1
from src.experiments.canonical_experiment_identity_v1 import inspect_code_provenance_v1

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output-dir", required=True, type=Path)
parser.add_argument("--expected-repository-sha", required=True)
args = parser.parse_args()
repo = Path(__file__).resolve().parents[2]
code = inspect_code_provenance_v1(repo)
revision = code.git_sha
if revision != args.expected_repository_sha or code.working_tree_status != "CLEAN":
    raise ValueError("FIVE_SLOT_CURRENT_CLEAN_CAPTURE_SOURCE_REQUIRED")
out = args.output_dir
if not out.is_absolute() or out.resolve() != out or out.exists():
    raise ValueError("FIVE_SLOT_NEW_CAPTURE_DIRECTORY_REQUIRED")
out.mkdir(mode=0o700, parents=True)
allowed = {
    "/api/v5/public/instruments",
    "/api/v5/public/mark-price",
    MARK_ENDPOINT_PATH,
    TICKER_ENDPOINT_PATH,
}
stats = Counter()
response_outcomes = Counter()
lock = Lock()
rate_locks = {route: Lock() for route in (MARK_ENDPOINT_PATH, TICKER_ENDPOINT_PATH)}
next_allowed = dict.fromkeys(rate_locks, 0.0)


def audit(event, args):
    if event != "urllib.Request":
        return
    url, body, headers, method = args
    parsed = urlsplit(url)
    if (parsed.scheme, parsed.netloc, method, body) != (
        "https",
        "eea.okx.com",
        "GET",
        None,
    ) or parsed.path not in allowed:
        raise AssertionError("PUBLIC_MARKET_GETS_ONLY")
    if any(name.lower().startswith(("authorization", "cookie", "ok-access")) for name in headers):
        raise AssertionError("NO_CREDENTIALS_IN_PUBLIC_MARKET_RUN")
    with lock:
        stats[parsed.path] += 1


sys.addaudithook(audit)


def utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write(path, value):
    with (out / path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=True, sort_keys=True, allow_nan=False)
        stream.write("\n")


with gzip.open(
    out / "public-get-receipts.jsonl.gz", "xt", encoding="utf-8", compresslevel=3
) as archive:

    def receipt(row):
        with lock:
            archive.write(
                json.dumps(row, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n"
            )

    class UniverseTransport(UrllibEeaPublicUniverseGetTransportV1):
        def get(self, *, path, query):
            started = utc()
            result = super().get(path=path, query=query)
            receipt(
                {
                    "kind": "universe",
                    "request_started_at": started,
                    "received_at": utc(),
                    "response": asdict(result),
                }
            )
            return result

    def universe(round_no):
        acquisition = acquire_eea_universe_inventory_v1(transport=UniverseTransport())
        observed = time.time()
        write(f"universe-acquisition-{round_no}.json", asdict(acquisition))
        if (
            not acquisition.ok
            or acquisition.provenance.get("SOFT_FAILURE_CODES")
            or not acquisition.venue_live_contact
        ):
            raise ValueError(
                f"PUBLIC_UNIVERSE_UNPROVEN:{acquisition.failure_codes}:{acquisition.provenance.get('SOFT_FAILURE_CODES')}"
            )
        production = run_governed_futures_universe_producer_v1(
            state_root=out / f"cap21-{round_no}",
            source_payload=acquisition.instruments_payload,
            mark_price_payload=acquisition.mark_price_payload,
            repository_sha=revision,
            producer_observed_at_unix=observed,
            source_event_time=acquisition.source_event_time,
            source_kind=acquisition.source_kind,
            session_id=f"broad-selection-public-{round_no}",
        )
        assert production["ok"], production.get("failure_codes")
        accepted = load_cap21_eligible_instruments_v1(production["snapshot"])
        assert accepted.ok, accepted.failure_codes
        return acquisition, {row.venue_native_id for row in accepted.eligible}, observed

    def collect(native):
        received = {}

        def trace(url, timeout, limit):
            route = urlsplit(url).path
            # Pace each documented public route below 20 requests per two seconds.
            with rate_locks[route]:
                time.sleep(max(0, next_allowed[route] - time.monotonic()))
                next_allowed[route] = time.monotonic() + 0.14
            start = utc()
            try:
                status, body, headers = _default_public_get(url, timeout, limit)
            except (OSError, ValueError) as exc:
                receipt(
                    {
                        "kind": "economic",
                        "native_id": native,
                        "route": route,
                        "started": start,
                        "error": type(exc).__name__,
                    }
                )
                with lock:
                    response_outcomes[f"{route}:{type(exc).__name__}"] += 1
                raise
            seen_at = utc()
            received[route] = seen_at
            receipt(
                {
                    "kind": "economic",
                    "native_id": native,
                    "route": route,
                    "method": "GET",
                    "started": start,
                    "received": seen_at,
                    "status": status,
                    "sha256": sha256(body).hexdigest(),
                    "body": body.decode("utf-8", errors="replace"),
                }
            )
            with lock:
                response_outcomes[f"{route}:{status}"] += 1
            return status, body, headers

        md = OkxPublicEconomicMdReadAdapterV1(capture_timestamp=utc(), fetcher=trace)
        bundle = md.collect_instrument_raw_input_v1(venue_native_id=native)
        marks = tuple(
            replace(mark, receive_or_capture_timestamp=received[MARK_ENDPOINT_PATH])
            for mark in bundle.marks
        )
        ticker = (
            replace(bundle.ticker, capture_or_receive_timestamp=received[TICKER_ENDPOINT_PATH])
            if bundle.ticker is not None
            else None
        )
        return replace(bundle, marks=marks, ticker=ticker)

    started = utc()
    start_acq, initially, _ = universe(1)
    print(f"CAP21 initial {len(initially)} eligible", flush=True)
    bundles = {}
    for index in range(2, 5):
        targets = initially if index == 2 else final_ids - bundles.keys()
        with ThreadPoolExecutor(max_workers=10) as pool:
            pending = {pool.submit(collect, native): native for native in sorted(targets)}
            for future in as_completed(pending):
                native = pending[future]
                bundles[native] = asdict(future.result())
                if len(bundles) % 100 == 0:
                    print(f"Captured {len(bundles)} instruments", flush=True)
        final_acq, final_ids, final_seen = universe(index)
        if final_ids <= bundles.keys():
            break
    missing = sorted(final_ids - bundles.keys())

with gzip.open(
    out / "economic-md-bundles.json.gz", "xt", encoding="utf-8", compresslevel=3
) as data:
    json.dump(bundles, data, ensure_ascii=True, sort_keys=True, allow_nan=False)
write(
    "market-capture.json",
    {
        "revision": revision,
        "started_at_utc": started,
        "completed_at_utc": utc(),
        "source": "PUBLIC_OKX_EEA_FUTURES_AND_SWAP",
        "initial_cap21_eligible": len(initially),
        "final_cap21_eligible": len(final_ids),
        "final_cap21_round": index,
        "final_observed_unix": final_seen,
        "initial_event_time": start_acq.source_event_time,
        "final_event_time": final_acq.source_event_time,
        "final_cap21_native_ids": sorted(final_ids),
        "missing_collections": missing,
        "public_gets": dict(stats),
        "response_outcomes": dict(response_outcomes),
        "private_gets": 0,
        "orders_sent": 0,
        "permits_created": 0,
    },
)
print(
    f"Collected {len(bundles)} instruments; final admissible cohort {len(final_ids)}; {len(missing)} missing collections",
    flush=True,
)
