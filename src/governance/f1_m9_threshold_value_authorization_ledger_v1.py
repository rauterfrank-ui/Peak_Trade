"""Durable threshold authorization and revocation ledgers for F1/M9 scoped authority."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping, Sequence

from src.governance.f1_m9_owner_threshold_value_authorization_record_v1 import (
    format_aware_utc_datetime_v1,
    parse_aware_utc_datetime_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "f1_m9_threshold_value_authorization_ledger/v1"

THRESHOLD_LEDGER_ENTRY_KEYS: Final[tuple[str, ...]] = (
    "schema_version",
    "threshold_value_authorization_record_digest",
    "configuration_digest",
    "owner_apply_authorization_record_digest",
    "authorized_at",
    "threshold_ledger_entry_digest",
)

THRESHOLD_REVOCATION_LEDGER_ENTRY_KEYS: Final[tuple[str, ...]] = (
    "schema_version",
    "threshold_value_authorization_record_digest",
    "configuration_digest",
    "revoked_at",
    "reason",
    "operator_reference",
    "threshold_revocation_ledger_entry_digest",
)


class ThresholdValueAuthorizationLedgerError(ValueError):
    """Fail-closed threshold authorization ledger error."""


@dataclass(frozen=True, slots=True)
class F1M9ThresholdValueAuthorizationLedgerPathsV1:
    threshold_ledger_path: Path
    threshold_revocation_ledger_path: Path


def _atomic_append_jsonl_line_v1(path: Path, line: str) -> None:
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        if existing and not existing.endswith("\n"):
            existing += "\n"
        new_body = existing + line + "\n"
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            handle.write(new_body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except OSError as exc:
        raise ThresholdValueAuthorizationLedgerError(f"ledger_persist_error:{exc}") from exc


def _load_jsonl_records_v1(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    if not path.is_file():
        raise ThresholdValueAuthorizationLedgerError("ledger_not_file")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ThresholdValueAuthorizationLedgerError("ledger_unavailable") from exc
    records: list[dict[str, Any]] = []
    for idx, line in enumerate(text.splitlines()):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ThresholdValueAuthorizationLedgerError(f"ledger_corrupt_line:{idx}") from exc
        if not isinstance(raw, dict):
            raise ThresholdValueAuthorizationLedgerError(f"ledger_corrupt_record:{idx}")
        records.append(raw)
    return records


def _validate_keys_v1(payload: Mapping[str, Any], required: Sequence[str], *, kind: str) -> None:
    missing = [key for key in required if key not in payload]
    if missing:
        raise ThresholdValueAuthorizationLedgerError(f"{kind}_field_missing:" + ",".join(missing))


def compute_threshold_ledger_entry_digest_v1(body: Mapping[str, Any]) -> str:
    sealed = {
        key: body[key]
        for key in THRESHOLD_LEDGER_ENTRY_KEYS
        if key != "threshold_ledger_entry_digest" and key in body
    }
    return compute_content_sha256(sealed)


def compute_threshold_revocation_ledger_entry_digest_v1(body: Mapping[str, Any]) -> str:
    sealed = {
        key: body[key]
        for key in THRESHOLD_REVOCATION_LEDGER_ENTRY_KEYS
        if key != "threshold_revocation_ledger_entry_digest" and key in body
    }
    return compute_content_sha256(sealed)


def parse_threshold_ledger_entry_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    _validate_keys_v1(payload, THRESHOLD_LEDGER_ENTRY_KEYS, kind="threshold_ledger")
    parse_aware_utc_datetime_v1(payload["authorized_at"], field_name="authorized_at")
    expected = compute_threshold_ledger_entry_digest_v1(payload)
    if str(payload["threshold_ledger_entry_digest"]) != expected:
        raise ThresholdValueAuthorizationLedgerError("threshold_ledger_entry_digest_mismatch")
    return dict(payload)


def parse_threshold_revocation_ledger_entry_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    _validate_keys_v1(payload, THRESHOLD_REVOCATION_LEDGER_ENTRY_KEYS, kind="threshold_revocation")
    parse_aware_utc_datetime_v1(payload["revoked_at"], field_name="revoked_at")
    expected = compute_threshold_revocation_ledger_entry_digest_v1(payload)
    if str(payload["threshold_revocation_ledger_entry_digest"]) != expected:
        raise ThresholdValueAuthorizationLedgerError(
            "threshold_revocation_ledger_entry_digest_mismatch"
        )
    return dict(payload)


def load_threshold_ledger_entries_v1(path: Path) -> list[dict[str, Any]]:
    return [parse_threshold_ledger_entry_v1(row) for row in _load_jsonl_records_v1(path)]


def load_threshold_revocation_ledger_entries_v1(path: Path) -> list[dict[str, Any]]:
    return [parse_threshold_revocation_ledger_entry_v1(row) for row in _load_jsonl_records_v1(path)]


def assert_threshold_revocation_state_available_v1(revocation_ledger_path: Path) -> None:
    path = Path(revocation_ledger_path)
    if not path.exists():
        raise ThresholdValueAuthorizationLedgerError("threshold_revocation_ledger_unavailable")
    if not path.is_file():
        raise ThresholdValueAuthorizationLedgerError("threshold_revocation_ledger_unavailable")
    _ = load_threshold_revocation_ledger_entries_v1(path)


def assert_threshold_not_revoked_v1(
    *,
    revocation_ledger_path: Path,
    threshold_value_authorization_record_digest: str,
    configuration_digest: str,
) -> None:
    assert_threshold_revocation_state_available_v1(revocation_ledger_path)
    records = load_threshold_revocation_ledger_entries_v1(revocation_ledger_path)
    for record in records:
        if (
            record["threshold_value_authorization_record_digest"]
            != threshold_value_authorization_record_digest
        ):
            continue
        if record["configuration_digest"] != configuration_digest:
            raise ThresholdValueAuthorizationLedgerError(
                "threshold_revocation_configuration_digest_ambiguity"
            )
        raise ThresholdValueAuthorizationLedgerError("threshold_value_authorization_revoked")


def find_threshold_ledger_entry_v1(
    *,
    threshold_ledger_path: Path,
    threshold_value_authorization_record_digest: str,
) -> dict[str, Any] | None:
    if not Path(threshold_ledger_path).exists():
        return None
    for entry in load_threshold_ledger_entries_v1(threshold_ledger_path):
        if (
            entry["threshold_value_authorization_record_digest"]
            == threshold_value_authorization_record_digest
        ):
            return entry
    return None


def append_threshold_ledger_entry_v1(
    *,
    threshold_ledger_path: Path,
    threshold_value_authorization_record_digest: str,
    configuration_digest: str,
    owner_apply_authorization_record_digest: str,
    authorized_at: str,
) -> dict[str, Any]:
    if not is_valid_sha256_hex(threshold_value_authorization_record_digest):
        raise ThresholdValueAuthorizationLedgerError("threshold_digest_invalid")
    existing = find_threshold_ledger_entry_v1(
        threshold_ledger_path=threshold_ledger_path,
        threshold_value_authorization_record_digest=threshold_value_authorization_record_digest,
    )
    if existing is not None:
        if existing["configuration_digest"] != configuration_digest:
            raise ThresholdValueAuthorizationLedgerError(
                "threshold_ledger_idempotency_configuration_mismatch"
            )
        return existing

    parse_aware_utc_datetime_v1(authorized_at, field_name="authorized_at")
    body = {
        "schema_version": SCHEMA_VERSION,
        "threshold_value_authorization_record_digest": threshold_value_authorization_record_digest,
        "configuration_digest": configuration_digest,
        "owner_apply_authorization_record_digest": owner_apply_authorization_record_digest,
        "authorized_at": format_aware_utc_datetime_v1(
            parse_aware_utc_datetime_v1(authorized_at, field_name="authorized_at")
        ),
    }
    body["threshold_ledger_entry_digest"] = compute_threshold_ledger_entry_digest_v1(body)
    entry = parse_threshold_ledger_entry_v1(body)
    line = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    _atomic_append_jsonl_line_v1(Path(threshold_ledger_path), line)
    return entry


def append_threshold_revocation_ledger_entry_v1(
    *,
    revocation_ledger_path: Path,
    threshold_value_authorization_record_digest: str,
    configuration_digest: str,
    reason: str,
    operator_reference: str,
    revoked_at: str,
) -> dict[str, Any]:
    if not str(reason or "").strip():
        raise ThresholdValueAuthorizationLedgerError("threshold_revocation_reason_required")
    if not str(operator_reference or "").strip():
        raise ThresholdValueAuthorizationLedgerError(
            "threshold_revocation_operator_reference_required"
        )
    body = {
        "schema_version": SCHEMA_VERSION,
        "threshold_value_authorization_record_digest": threshold_value_authorization_record_digest,
        "configuration_digest": configuration_digest,
        "revoked_at": format_aware_utc_datetime_v1(
            parse_aware_utc_datetime_v1(revoked_at, field_name="revoked_at")
        ),
        "reason": str(reason).strip(),
        "operator_reference": str(operator_reference).strip(),
    }
    body["threshold_revocation_ledger_entry_digest"] = (
        compute_threshold_revocation_ledger_entry_digest_v1(body)
    )
    entry = parse_threshold_revocation_ledger_entry_v1(body)
    line = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    _atomic_append_jsonl_line_v1(Path(revocation_ledger_path), line)
    return entry


def initialize_empty_threshold_revocation_ledger_v1(revocation_ledger_path: Path) -> None:
    path = Path(revocation_ledger_path)
    if path.exists():
        assert_threshold_revocation_state_available_v1(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


__all__ = [
    "F1M9ThresholdValueAuthorizationLedgerPathsV1",
    "SCHEMA_VERSION",
    "THRESHOLD_LEDGER_ENTRY_KEYS",
    "THRESHOLD_REVOCATION_LEDGER_ENTRY_KEYS",
    "ThresholdValueAuthorizationLedgerError",
    "append_threshold_ledger_entry_v1",
    "append_threshold_revocation_ledger_entry_v1",
    "assert_threshold_not_revoked_v1",
    "assert_threshold_revocation_state_available_v1",
    "find_threshold_ledger_entry_v1",
    "initialize_empty_threshold_revocation_ledger_v1",
    "load_threshold_ledger_entries_v1",
    "load_threshold_revocation_ledger_entries_v1",
]
