"""Private original-response journal for the existing equity owner.

Explicit native K1 GET acquisition, no order/capital/sizing interface. Raw
account data stays outside Git; callbacks receive responses, never auth headers.
Sealed records can be replayed offline without credentials or another GET.
"""

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import time

from src.ops.okx_eea_private_account_state_runtime_v1.bills_observation_v1 import (
    audit_bill_pages_v1,
    canonical_digest_v1,
)


class RealEquityJournalError(ValueError):
    pass


def utc_now_v1():
    return datetime.now(timezone.utc).isoformat()


def unique_json_v1(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise RealEquityJournalError("JOURNAL_DUPLICATE_JSON_FIELD")
            result[key] = value
        return result

    return json.loads(data, object_pairs_hook=unique)


def write_private_json_v1(path, value):
    data = json.dumps(value, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    return sha256(data).hexdigest()


class PrivateEquityJournalV1:
    def __init__(self, root, *, expected_account_identity, source_commit):
        root = Path(root)
        if not root.is_absolute() or root.parent.is_symlink() or not root.parent.is_dir():
            raise RealEquityJournalError("JOURNAL_NEW_PRIVATE_ABSOLUTE_DIRECTORY_REQUIRED")
        if stat.S_IMODE(root.parent.stat().st_mode) & 0o077:
            raise RealEquityJournalError("JOURNAL_PARENT_NOT_PRIVATE")
        if root.parent.stat().st_uid != os.getuid():
            raise RealEquityJournalError("JOURNAL_PARENT_WRONG_OWNER")
        if not isinstance(expected_account_identity, str) or not expected_account_identity.strip():
            raise RealEquityJournalError("JOURNAL_EXPECTED_ACCOUNT_REQUIRED")
        root.mkdir(mode=0o700, exist_ok=False)
        self.root = root
        self.expected_account_identity = expected_account_identity
        self.source_commit = source_commit
        self.entries = []
        self.started_at = utc_now_v1()
        self.sealed = False

    def record_v1(self, *, result, body):
        if self.sealed:
            raise RealEquityJournalError("JOURNAL_ALREADY_SEALED")
        if not isinstance(body, bytes) or (
            sha256(body).hexdigest() != result.body_sha256
            and not (body == b"" and result.body_sha256 == "")
        ):
            raise RealEquityJournalError("JOURNAL_RAW_BODY_HASH_MISMATCH")
        if result.method != "GET":
            raise RealEquityJournalError("JOURNAL_NON_GET_FORBIDDEN")
        value = {
            "schema": "peaktrade.private_equity_raw_response.v1",
            "index": len(self.entries),
            "captured_at": utc_now_v1(),
            "endpoint": result.endpoint,
            "method": result.method,
            "http_status": result.http_status,
            "auth_header_sent": result.auth_header_sent,
            "venue_live_contact": result.venue_live_contact,
            "historical_reuse": result.historical_reuse,
            "error_class": result.error_class,
            "body_utf8_exact": body.decode("utf-8"),
            "body_sha256": sha256(body).hexdigest(),
            "previous_record_sha256": self.entries[-1]["sha256"] if self.entries else None,
        }
        name = f"response_{len(self.entries):03d}.json"
        digest = write_private_json_v1(self.root / name, value)
        self.entries.append({"file": name, "sha256": digest, "endpoint": result.endpoint})

    def seal_v1(self, *, status, labels, error_type=None, request_attempt_count=None):
        if self.sealed:
            raise RealEquityJournalError("JOURNAL_ALREADY_SEALED")
        manifest = {
            "schema": "peaktrade.private_equity_journal.v1",
            "account_identity": self.expected_account_identity,
            "source_commit": self.source_commit,
            "started_at": self.started_at,
            "completed_at": utc_now_v1(),
            "status": status,
            "labels": labels,
            "entries": self.entries,
            "error_type": error_type,
            "request_attempt_count": request_attempt_count,
            "orders_or_transfers": 0,
            "authority_effect": "NONE",
        }
        binding = self.root / "source_bindings.json"
        if binding.is_file():
            manifest["source_bindings_sha256"] = sha256(binding.read_bytes()).hexdigest()
        write_private_json_v1(self.root / "manifest.json", manifest)
        self.sealed = True
        return manifest


def collect_real_equity_journal_v1(source, journal):
    """At most ten unfiltered GETs; save even a failed attempt's raw response.

    Fixed page budgets intentionally fail closed when insufficient. Snapshot
    rows bracket both independent bill endpoints; no short-page assumption.
    """
    if source.closed or source.transport.read_count != 0:
        raise RealEquityJournalError("JOURNAL_FRESH_K1_SESSION_REQUIRED")
    native = source.transport._transport
    if native.raw_response_sink_v1 is not None:
        raise RealEquityJournalError("JOURNAL_RESPONSE_SINK_ALREADY_BOUND")
    labels = {}

    def get(label, path, params):
        index = len(journal.entries)
        result = source._verified_get_v1(path, params)
        if len(journal.entries) != index + 1:
            raise RealEquityJournalError("JOURNAL_CAPTURE_NOT_BOUND_TO_GET")
        labels[label] = index
        return result["data"]

    binding = canonical_digest_v1(
        {"account_identity": source.expected_account_identity, "venue_host": "eea.okx.com"}
    )
    native.raw_response_sink_v1 = journal.record_v1
    try:
        config = get("config_before", "/api/v5/account/config", {})
        if len(config) != 1 or config[0].get("uid") != journal.expected_account_identity:
            raise RealEquityJournalError("JOURNAL_ACCOUNT_MISMATCH")
        get("balance_before", "/api/v5/account/balance", {})
        get("positions_before", "/api/v5/account/positions", {})
        for family, budget in (("archive", 2), ("recent", 1)):
            path = (
                "/api/v5/account/bills-archive" if family == "archive" else "/api/v5/account/bills"
            )
            cursor = None
            for page_number in range(budget):
                params = {"limit": "100"}
                if cursor is not None:
                    params["after"] = str(cursor)
                rows = get(f"{family}_{page_number}", path, params)
                audit_bill_pages_v1(
                    [{"account_binding_digest": binding, "endpoint_path": path, "rows": rows}],
                    account_binding_digest=binding,
                )
                ids = [int(r["billId"]) for r in rows]
                if any(a <= b for a, b in zip(ids, ids[1:])) or (
                    cursor is not None and any(bid >= cursor for bid in ids)
                ):
                    raise RealEquityJournalError("JOURNAL_CURSOR_NOT_PROGRESSING")
                if not rows:
                    break
                cursor = ids[-1]
        get("funding_balance", "/api/v5/asset/balances", {})
        get("positions_after", "/api/v5/account/positions", {})
        get("balance_after", "/api/v5/account/balance", {})
        config = get("config_after", "/api/v5/account/config", {})
        if len(config) != 1 or config[0].get("uid") != journal.expected_account_identity:
            raise RealEquityJournalError("JOURNAL_ACCOUNT_MISMATCH")
        return journal.seal_v1(
            status="ACQUIRED", labels=labels, request_attempt_count=source.transport.read_count
        )
    except Exception as exc:
        journal.seal_v1(
            status="FAILED",
            labels=labels,
            error_type=type(exc).__name__,
            request_attempt_count=source.transport.read_count,
        )
        raise
    finally:
        native.raw_response_sink_v1 = None


def collect_equity_funding_supplement_v1(source, journal, *, pace=time.sleep):
    """Native bill taxonomy plus complete observed funding history, <=9 GETs.

    Funding cursors are timestamps, unlike Trading bill-ID cursors. A full
    100-row timestamp page remains ambiguous at ties and is not promoted.
    Never silently reuse the Trading cursor rule for the Funding endpoint.
    """
    if source.closed or source.transport.read_count != 0:
        raise RealEquityJournalError("JOURNAL_FRESH_K1_SESSION_REQUIRED")
    native = source.transport._transport
    if native.raw_response_sink_v1 is not None:
        raise RealEquityJournalError("JOURNAL_RESPONSE_SINK_ALREADY_BOUND")
    labels = {}

    def get(label, path, params):
        index = len(journal.entries)
        payload = source._verified_get_v1(path, params)
        if len(journal.entries) != index + 1:
            raise RealEquityJournalError("JOURNAL_CAPTURE_NOT_BOUND_TO_GET")
        labels[label] = index
        return payload["data"]

    native.raw_response_sink_v1 = journal.record_v1
    try:
        for label in ("config_before",):
            config = get(label, "/api/v5/account/config", {})
            if len(config) != 1 or config[0].get("uid") != journal.expected_account_identity:
                raise RealEquityJournalError("JOURNAL_ACCOUNT_MISMATCH")
        get("funding_before", "/api/v5/asset/balances", {})
        get("bill_taxonomy", "/api/v5/account/subtypes", {})
        cursor = None
        for page_number in range(4):
            if page_number:
                pace(1.1)  # documented history rate limit: one request/second
            params = {"limit": "100"}
            if cursor is not None:
                params["after"] = str(cursor)
            rows = get(f"funding_history_{page_number}", "/api/v5/asset/bills-history", params)
            if not rows:
                break
            timestamps = [int(r["ts"]) for r in rows]
            if any(a < b for a, b in zip(timestamps, timestamps[1:])) or (
                cursor is not None and any(ts >= cursor for ts in timestamps)
            ):
                raise RealEquityJournalError("FUNDING_TIMESTAMP_CURSOR_NOT_PROGRESSING")
            if len(rows) >= 100:
                raise RealEquityJournalError("FUNDING_TIMESTAMP_PAGE_BOUNDARY_AMBIGUOUS")
            cursor = timestamps[-1]
        get("funding_after", "/api/v5/asset/balances", {})
        config = get("config_after", "/api/v5/account/config", {})
        if len(config) != 1 or config[0].get("uid") != journal.expected_account_identity:
            raise RealEquityJournalError("JOURNAL_ACCOUNT_MISMATCH")
        return journal.seal_v1(
            status="ACQUIRED", labels=labels, request_attempt_count=source.transport.read_count
        )
    except Exception as exc:
        journal.seal_v1(
            status="FAILED",
            labels=labels,
            error_type=type(exc).__name__,
            request_attempt_count=source.transport.read_count,
        )
        raise
    finally:
        native.raw_response_sink_v1 = None


def load_real_equity_journal_v1(root, *, expected_manifest_sha256):
    """Verify an independently bound manifest and its exact original bodies."""
    root = Path(root)
    data = (root / "manifest.json").read_bytes()
    if sha256(data).hexdigest() != expected_manifest_sha256:
        raise RealEquityJournalError("JOURNAL_MANIFEST_HASH_MISMATCH")
    manifest = unique_json_v1(data)
    if (
        manifest.get("schema") != "peaktrade.private_equity_journal.v1"
        or manifest.get("status") != "ACQUIRED"
    ):
        raise RealEquityJournalError("JOURNAL_NOT_ACQUIRED")
    if "source_bindings_sha256" in manifest:
        if (
            sha256((root / "source_bindings.json").read_bytes()).hexdigest()
            != manifest["source_bindings_sha256"]
        ):
            raise RealEquityJournalError("JOURNAL_SOURCE_BINDING_HASH_MISMATCH")
    records = []
    previous = None
    for index, item in enumerate(manifest["entries"]):
        if item["file"] != f"response_{index:03d}.json":
            raise RealEquityJournalError("JOURNAL_RECORD_NAME_INVALID")
        data = (root / item["file"]).read_bytes()
        if sha256(data).hexdigest() != item["sha256"]:
            raise RealEquityJournalError("JOURNAL_RECORD_HASH_MISMATCH")
        record = unique_json_v1(data)
        if record["index"] != index or record["previous_record_sha256"] != previous:
            raise RealEquityJournalError("JOURNAL_HASH_CHAIN_INVALID")
        if record["endpoint"] != item["endpoint"]:
            raise RealEquityJournalError("JOURNAL_ENDPOINT_BINDING_MISMATCH")
        if sha256(record["body_utf8_exact"].encode()).hexdigest() != record["body_sha256"]:
            raise RealEquityJournalError("JOURNAL_BODY_HASH_MISMATCH")
        if not (
            record["http_status"] == 200
            and record["method"] == "GET"
            and record["auth_header_sent"] is True
            and record["venue_live_contact"] is True
            and record["historical_reuse"] is False
            and not record["error_class"]
        ):
            raise RealEquityJournalError("JOURNAL_GET_PROVENANCE_INVALID")
        payload = unique_json_v1(record["body_utf8_exact"])
        if (
            not isinstance(payload, dict)
            or str(payload.get("code")) != "0"
            or set(payload) - {"code", "msg", "data"}
            or not isinstance(payload.get("data"), list)
            or any(not isinstance(r, dict) for r in payload["data"])
        ):
            raise RealEquityJournalError("JOURNAL_RESPONSE_SCHEMA_INVALID")
        records.append({**record, "rows": payload["data"]})
        previous = item["sha256"]
    labels = manifest["labels"]
    if (
        not isinstance(labels, dict)
        or sorted(labels.values()) != list(range(len(records)))
        or any(type(i) is not int for i in labels.values())
    ):
        raise RealEquityJournalError("JOURNAL_LABEL_BINDING_INVALID")
    return manifest, {label: records[index] for label, index in labels.items()}
