from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence

from .contract import (
    CANON_JSONL_RULE,
    CANON_JSON_RULE,
    CONTRACT_VERSION,
    ContractViolationError,
    EVENT_ORDERING_INVARIANT,
    SchemaValidationError,
)


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def assert_no_floats(x: Any, *, path: str = "$") -> None:
    """
    Hard error on any float anywhere (determinism).
    """
    if isinstance(x, float):
        raise ContractViolationError(f"float forbidden in deterministic artifacts at {path}")
    if isinstance(x, Mapping):
        for k, v in x.items():
            assert_no_floats(v, path=f"{path}.{k}")
        return
    if isinstance(x, (list, tuple)):
        for i, v in enumerate(x):
            assert_no_floats(v, path=f"{path}[{i}]")


def assert_lf_only_bytes(b: bytes, *, label: str) -> None:
    """
    Enforce LF-only newlines (reject CRLF) and require trailing LF.
    """
    if b"\r\n" in b:
        raise ContractViolationError(f"CRLF forbidden in deterministic artifacts: {label}")
    if not b.endswith(b"\n"):
        raise ContractViolationError(f"missing trailing LF in deterministic artifact: {label}")


def _require_non_empty_str(d: Mapping[str, Any], key: str) -> str:
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        raise SchemaValidationError(f"manifest field must be non-empty string: {key}")
    return v


def _require_mapping(d: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    v = d.get(key)
    if not isinstance(v, Mapping):
        raise SchemaValidationError(f"manifest {key} must be an object")
    return v


def _validate_relpath(path: str) -> None:
    if not path or path.strip() != path:
        raise SchemaValidationError("manifest contents.path must be non-empty and trimmed")
    if path.startswith("/") or path.startswith("\\"):
        raise SchemaValidationError("manifest contents.path must be relative (no leading slash)")
    if "\\" in path:
        raise SchemaValidationError("manifest contents.path must use forward slashes only")
    if ".." in path.split("/"):
        raise SchemaValidationError("manifest contents.path must not contain '..' segments")


def validate_manifest_v1_strict(d: Mapping[str, Any]) -> None:
    """
    Strict schema validation for manifest v1.x (still contract_version='1').

    Backwards compatibility:
    - unknown extra top-level keys are allowed
    - optional known keys are validated if present
    """
    required = (
        "contract_version",
        "bundle_id",
        "run_id",
        "created_at_utc",
        "peak_trade_git_sha",
        "producer",
        "contents",
        "canonicalization",
        "invariants",
    )
    missing = [k for k in required if k not in d]
    if missing:
        raise SchemaValidationError(f"manifest missing required keys: {missing}")

    if str(d.get("contract_version")) != CONTRACT_VERSION:
        raise SchemaValidationError("manifest contract_version must be '1'")

    _require_non_empty_str(d, "bundle_id")
    _require_non_empty_str(d, "run_id")
    created_at = _require_non_empty_str(d, "created_at_utc")
    # Must be parseable ISO8601 to avoid locale/format drift.
    try:
        datetime.fromisoformat(created_at)
    except Exception as ex:  # noqa: BLE001
        raise SchemaValidationError("manifest created_at_utc must be ISO8601") from ex

    _require_non_empty_str(d, "peak_trade_git_sha")

    producer = _require_mapping(d, "producer")
    if producer.get("tool") != "pt_replay_pack":
        raise SchemaValidationError("manifest producer.tool must be 'pt_replay_pack'")
    if not isinstance(producer.get("version"), str) or not str(producer.get("version")).strip():
        raise SchemaValidationError("manifest producer.version must be non-empty string")

    canon = _require_mapping(d, "canonicalization")
    if canon.get("json") != CANON_JSON_RULE:
        raise SchemaValidationError(f"manifest canonicalization.json must be {CANON_JSON_RULE!r}")
    if canon.get("jsonl") != CANON_JSONL_RULE:
        raise SchemaValidationError(f"manifest canonicalization.jsonl must be {CANON_JSONL_RULE!r}")

    inv = _require_mapping(d, "invariants")
    if inv.get("has_execution_events") is not True:
        raise SchemaValidationError("manifest invariants.has_execution_events must be true")
    if inv.get("ordering") != EVENT_ORDERING_INVARIANT:
        raise SchemaValidationError(
            f"manifest invariants.ordering must be {EVENT_ORDERING_INVARIANT!r}"
        )

    contents = d.get("contents")
    if not isinstance(contents, list) or not contents:
        raise SchemaValidationError("manifest contents must be a non-empty list")

    paths: list[str] = []
    for i, item in enumerate(contents):
        if not isinstance(item, Mapping):
            raise SchemaValidationError(f"manifest contents[{i}] must be an object")
        for req in ("path", "sha256", "bytes", "media_type"):
            if req not in item:
                raise SchemaValidationError(f"manifest contents[{i}] missing key: {req}")

        p = item.get("path")
        if not isinstance(p, str):
            raise SchemaValidationError(f"manifest contents[{i}].path must be string")
        _validate_relpath(p)
        paths.append(p)

        sha = item.get("sha256")
        if not isinstance(sha, str) or _SHA256_RE.fullmatch(sha) is None:
            raise SchemaValidationError(f"manifest contents[{i}].sha256 must be 64-hex lowercase")

        b = item.get("bytes")
        if not isinstance(b, int) or b < 0:
            raise SchemaValidationError(f"manifest contents[{i}].bytes must be int >= 0")

        mt = item.get("media_type")
        if not isinstance(mt, str) or not mt.strip():
            raise SchemaValidationError(
                f"manifest contents[{i}].media_type must be non-empty string"
            )

    # Strict list constraints
    if paths != sorted(paths):
        raise SchemaValidationError("manifest.contents must be sorted by path")
    if len(set(paths)) != len(paths):
        raise SchemaValidationError("manifest.contents paths must be unique")

    # Known optional keys
    if "instruments" in d and d["instruments"] is not None:
        inst = d["instruments"]
        if not isinstance(inst, list) or any(not isinstance(x, str) for x in inst):
            raise SchemaValidationError("manifest instruments must be a list of strings")

    if "notes" in d and d["notes"] is not None and not isinstance(d["notes"], str):
        raise SchemaValidationError("manifest notes must be string if present")

    if "timerange" in d and d["timerange"] is not None and not isinstance(d["timerange"], Mapping):
        raise SchemaValidationError("manifest timerange must be object if present")

    if "data_refs" in d and d["data_refs"] is not None and not isinstance(d["data_refs"], Mapping):
        raise SchemaValidationError("manifest data_refs must be object if present")


def validate_execution_event_object_strict(ev: Mapping[str, Any], *, line_no: int) -> None:
    """
    Strict event-object validation for events/execution_events.jsonl.
    """
    assert_no_floats(ev, path=f"$.events[{line_no}]")

    # Required replay-pack fields
    if ev.get("schema_version") != "BETA_EXEC_V1":
        raise ContractViolationError("execution event schema_version must be 'BETA_EXEC_V1'")
    for k in ("event_id", "run_id", "session_id", "intent_id", "symbol", "event_type"):
        v = ev.get(k)
        if not isinstance(v, str) or not v.strip():
            raise ContractViolationError(f"execution event missing/invalid required string: {k}")
    ts_sim = ev.get("ts_sim")
    if not isinstance(ts_sim, int) or ts_sim < 0:
        raise ContractViolationError("execution event ts_sim must be int >= 0")

    payload = ev.get("payload")
    if payload is None:
        raise ContractViolationError("execution event payload must be object (not null)")
    if not isinstance(payload, Mapping):
        raise ContractViolationError("execution event payload must be object")

    # Ordering invariant fields
    if not isinstance(ev.get("event_time_utc"), str):
        raise ContractViolationError("events must include event_time_utc (str)")
    if not isinstance(ev.get("seq"), int):
        raise ContractViolationError("events must include seq (int)")


# -----------------------------------------------------------------------------
# Market data refs (optional) — v1.x additive
# -----------------------------------------------------------------------------

MARKET_DATA_REFS_SCHEMA_VERSION: str = "MARKET_DATA_REFS_V1"

_MARKET_DATA_KIND_ALLOWED = {"bars", "ticks", "quotes"}


def validate_market_data_ref_object_strict(x: Mapping[str, Any]) -> None:
    """
    Strict schema validation for one market data ref object.
    """
    assert_no_floats(x, path="$.market_data_ref")

    def req_str(key: str) -> str:
        v = x.get(key)
        if not isinstance(v, str) or not v.strip():
            raise SchemaValidationError(f"market_data_ref.{key} must be non-empty string")
        return v

    def opt_str(key: str) -> None:
        v = x.get(key)
        if v is None:
            return
        if not isinstance(v, str):
            raise SchemaValidationError(f"market_data_ref.{key} must be string or null")

    req_str("ref_id")
    kind = req_str("kind")
    if kind not in _MARKET_DATA_KIND_ALLOWED:
        raise SchemaValidationError(
            f"market_data_ref.kind must be one of {sorted(_MARKET_DATA_KIND_ALLOWED)!r}"
        )
    req_str("symbol")
    opt_str("venue")
    opt_str("timeframe")
    req_str("start_utc")
    req_str("end_utc")
    source = req_str("source")
    if source != "local_cache":
        raise SchemaValidationError("market_data_ref.source must be 'local_cache'")

    locator = x.get("locator")
    if not isinstance(locator, Mapping):
        raise SchemaValidationError("market_data_ref.locator must be object")
    assert_no_floats(locator, path="$.market_data_ref.locator")
    for k in ("namespace", "dataset"):
        v = locator.get(k)
        if not isinstance(v, str) or not v.strip():
            raise SchemaValidationError(f"market_data_ref.locator.{k} must be non-empty string")
    part = locator.get("partition")
    if part is not None and not isinstance(part, str):
        raise SchemaValidationError("market_data_ref.locator.partition must be string or null")

    hint = x.get("sha256_hint")
    if hint is not None:
        if not isinstance(hint, str) or _SHA256_RE.fullmatch(hint) is None:
            raise SchemaValidationError("market_data_ref.sha256_hint must be 64-hex lowercase")

    req = x.get("required")
    if req is not None and not isinstance(req, bool):
        raise SchemaValidationError("market_data_ref.required must be bool if present")


def validate_market_data_refs_document_strict(doc: Mapping[str, Any] | Sequence[Any]) -> None:
    """
    Validate the optional market data refs document.

    Accepted top-level shapes:
    - list[ref]
    - { "schema_version": "MARKET_DATA_REFS_V1", "refs": [ref, ...] }
    - { "market_data_refs": [ref, ...] }  (preferred human-friendly wrapper)
    """
    if isinstance(doc, list):
        items = doc
    elif isinstance(doc, Mapping):
        if "market_data_refs" in doc:
            refs = doc.get("market_data_refs")
            if not isinstance(refs, list):
                raise SchemaValidationError("market_data_refs.market_data_refs must be a list")
            items = refs
        else:
            sv = doc.get("schema_version")
            if sv != MARKET_DATA_REFS_SCHEMA_VERSION:
                raise SchemaValidationError(
                    f"market_data_refs.schema_version must be {MARKET_DATA_REFS_SCHEMA_VERSION!r}"
                )
            refs = doc.get("refs")
            if not isinstance(refs, list):
                raise SchemaValidationError("market_data_refs.refs must be a list")
            items = refs
    else:
        raise SchemaValidationError("market_data_refs document must be object or list")

    for i, it in enumerate(items):
        if not isinstance(it, Mapping):
            raise SchemaValidationError(f"market_data_refs[{i}] must be object")
        validate_market_data_ref_object_strict(it)
