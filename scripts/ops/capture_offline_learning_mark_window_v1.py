"""Capture one closed ETH mark window for the offline learning archive."""

import argparse
from contextlib import closing
from datetime import datetime, timezone
import fcntl
import hashlib
from http.client import HTTPSConnection
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from urllib.parse import urlencode

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    require_v1,
    seal_v1,
    strict_json_v1,
    validate_seal_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_recorded_market_replay_v1 import (
    RecordedMarkArchiveV1,
    RecordedMarkPageV1,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import (
    HTTP_MAX_RESPONSE_BYTES,
    HTTP_TIMEOUT_SECONDS,
    MARK_BAR,
    MARK_ENDPOINT_PATH,
    MARK_HISTORY_LIMIT,
    PUBLIC_HTTP_HOST,
    PT1M_STEP_MS,
)
from src.research.offline_recorded_mark_horizon_source_v1 import (
    aggregate_recorded_mark_minutes,
    read_bound_json,
    utc_seconds,
)

SCHEMA = "recorded_public_mark_window_v1"
NATIVE_INSTRUMENT = "ETH-USDT-SWAP"


def _utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _public_get(query):
    # A fixed host and path, with no redirects or proxy inheritance.
    with closing(HTTPSConnection(PUBLIC_HTTP_HOST, timeout=HTTP_TIMEOUT_SECONDS)) as connection:
        connection.request(
            "GET",
            f"{MARK_ENDPOINT_PATH}?{urlencode(query)}",
            headers={"Accept": "application/json"},
        )
        with connection.getresponse() as response:
            return response.status, response.read(HTTP_MAX_RESPONSE_BYTES + 1)


def _write(path, data):
    with path.open("xb") as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())


def _sync_directory(path):
    handle = os.open(path, os.O_RDONLY)
    try:
        os.fsync(handle)
    finally:
        os.close(handle)


def _read_manifest(root):
    return validate_seal_v1(strict_json_v1((root / "capture.json").read_bytes()), SCHEMA)


def _page_path(root, index):
    return root / f"page-{index:02d}.json"


def read_captured_mark_archive_v1(root: Path) -> RecordedMarkArchiveV1:
    """Reopen the published pins for the existing offline archive reader."""
    root = Path(root)
    manifest = _read_manifest(root)
    pages = tuple(
        RecordedMarkPageV1(_page_path(root, index), digest)
        for index, digest in enumerate(manifest["page_digests"])
    )
    require_v1(bool(pages), "CAPTURE_PAGES_REQUIRED")
    return RecordedMarkArchiveV1(
        pages[0].raw_path,
        pages[0].raw_sha256,
        root / "request_log.json",
        manifest["request_log_sha256"],
        root / "instrument_binding.json",
        manifest["plan"]["binding_sha256"],
        manifest["plan"]["repository_sha"],
        additional_pages=pages[1:],
    )


def capture_public_mark_window_v1(
    *,
    output: Path,
    start_utc: str,
    hours: int,
    binding_path: Path,
    binding_sha256: str,
    repository_sha: str,
    fetch_page=_public_get,
):
    """Publish one complete archive or replay an identical existing capture."""
    require_v1(type(hours) is int and 1 <= hours <= 24, "EXPLICIT_BOUNDED_BAR_COUNT_REQUIRED")
    require_v1(re.fullmatch(r"[0-9a-f]{40}", repository_sha) is not None, "REPOSITORY_SHA_REQUIRED")
    start = utc_seconds(start_utc)
    require_v1(start % 3600 == 0, "EXPLICIT_HOURLY_GRID_REQUIRED")
    end = start + hours * 3600
    require_v1(end <= utc_seconds(_utc_now()), "CAPTURE_WINDOW_NOT_CLOSED")
    binding_bytes = binding_path.read_bytes()
    require_v1(_sha(binding_bytes) == binding_sha256, "SOURCE_SHA256_MISMATCH")
    binding = strict_json_v1(binding_bytes)
    require_v1(
        isinstance(binding, dict) and binding.get("native_instrument_id") == NATIVE_INSTRUMENT,
        "CAPTURE_MARKET_MISMATCH",
    )
    plan = {
        "start_utc": start_utc,
        "hours": hours,
        "binding_sha256": binding_sha256,
        "repository_sha": repository_sha,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with (output.parent / f".{output.name}.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if output.exists():
            saved = _read_manifest(output)
            require_v1(saved["plan"] == plan, "CAPTURE_WINDOW_CONFLICT")
            archive = read_captured_mark_archive_v1(output)
            read_bound_json(archive.request_log_path, archive.request_log_sha256)
            read_bound_json(archive.binding_path, archive.binding_sha256)
            read_bound_json(archive.raw_path, archive.raw_sha256)
            for page in archive.additional_pages:
                read_bound_json(page.raw_path, page.raw_sha256)
            return saved

        with TemporaryDirectory(prefix=".mark-capture-", dir=output.parent) as temporary:
            stage = Path(temporary) / "archive"
            stage.mkdir()
            pages, logs = [], []
            page_size = int(MARK_HISTORY_LIMIT)
            minute_count = hours * 60
            for index, offset in enumerate(range(0, minute_count, page_size)):
                query = {
                    "instId": NATIVE_INSTRUMENT,
                    "bar": MARK_BAR,
                    "after": str(int(end * 1000) - offset * PT1M_STEP_MS),
                    "limit": str(min(page_size, minute_count - offset)),
                }
                requested = _utc_now()
                status, raw = fetch_page(query)
                received = _utc_now()
                require_v1(status == 200, f"PUBLIC_MARK_HTTP_{status}")
                require_v1(len(raw) <= HTTP_MAX_RESPONSE_BYTES, "PUBLIC_MARK_RESPONSE_TOO_LARGE")
                payload = strict_json_v1(raw)
                require_v1(
                    isinstance(payload, dict) and payload.get("code") == "0",
                    "PUBLIC_MARK_VENUE_FAILURE",
                )
                digest = _sha(raw)
                record = {
                    "endpoint": MARK_ENDPOINT_PATH,
                    "request_host": PUBLIC_HTTP_HOST,
                    "query_params": query,
                    "request_time_utc": requested,
                    "response_time_utc": received,
                    "http_status": status,
                    "okx_code": payload["code"],
                    "raw_response_sha256": digest,
                }
                logs.append(record)
                pages.append({"payload": payload, "raw_sha256": digest, "request_record": record})
                _write(_page_path(stage, index), raw)

            aggregate_recorded_mark_minutes(
                pages=pages,
                instrument_binding=binding,
                canonical_instrument_id=binding["canonical_instrument_id"],
                native_instrument_id=NATIVE_INSTRUMENT,
                horizon_start_utc=start_utc,
                n_bars=hours,
                repository_sha=repository_sha,
            )
            log_bytes = bytes_v1(logs)
            manifest = seal_v1(
                {
                    "schema_version": SCHEMA,
                    "authority": "NONE",
                    "plan": plan,
                    "available_at_utc": max(row["response_time_utc"] for row in logs),
                    "request_log_sha256": _sha(log_bytes),
                    "page_digests": [page["raw_sha256"] for page in pages],
                }
            )
            _write(stage / "request_log.json", log_bytes)
            _write(stage / "instrument_binding.json", binding_bytes)
            _write(stage / "capture.json", bytes_v1(manifest))
            _sync_directory(stage)
            os.rename(stage, output)
            _sync_directory(output.parent)
            return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--start-utc", required=True)
    parser.add_argument("--hours", required=True, type=int)
    parser.add_argument("--binding-path", required=True, type=Path)
    parser.add_argument("--binding-sha256", required=True)
    parser.add_argument("--repository-sha", required=True)
    args = parser.parse_args()
    manifest = capture_public_mark_window_v1(**vars(args))
    print(bytes_v1(manifest).decode("utf-8"))


if __name__ == "__main__":
    main()
