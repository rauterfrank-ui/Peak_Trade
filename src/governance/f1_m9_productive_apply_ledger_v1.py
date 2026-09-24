"""Durable apply and revocation ledgers for F1/M9 scoped Owner Apply authority."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping, Sequence

from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    format_aware_utc_datetime_v1,
    parse_aware_utc_datetime_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "f1_m9_productive_apply_ledger/v1"

APPLY_LEDGER_ENTRY_KEYS: Final[tuple[str, ...]] = (
    "schema_version",
    "owner_apply_authorization_record_digest",
    "configuration_digest",
    "authorization_digest",
    "ingress_digest",
    "applied_at",
    "apply_ledger_entry_digest",
)

REVOCATION_LEDGER_ENTRY_KEYS: Final[tuple[str, ...]] = (
    "schema_version",
    "owner_apply_authorization_record_digest",
    "configuration_digest",
    "revoked_at",
    "reason",
    "operator_reference",
    "revocation_ledger_entry_digest",
)


class ProductiveApplyLedgerError(ValueError):
    """Fail-closed apply/revocation ledger error."""


@dataclass(frozen=True, slots=True)
class F1M9ProductiveApplyLedgerPathsV1:
    apply_ledger_path: Path
    revocation_ledger_path: Path


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
        raise ProductiveApplyLedgerError(f"ledger_persist_error:{exc}") from exc


def _load_jsonl_records_v1(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    if not path.is_file():
        raise ProductiveApplyLedgerError("ledger_not_file")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ProductiveApplyLedgerError("ledger_unavailable") from exc
    records: list[dict[str, Any]] = []
    for idx, line in enumerate(text.splitlines()):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ProductiveApplyLedgerError(f"ledger_corrupt_line:{idx}") from exc
        if not isinstance(raw, dict):
            raise ProductiveApplyLedgerError(f"ledger_corrupt_record:{idx}")
        records.append(raw)
    return records


def _validate_keys_v1(payload: Mapping[str, Any], required: Sequence[str], *, kind: str) -> None:
    missing = [key for key in required if key not in payload]
    if missing:
        raise ProductiveApplyLedgerError(f"{kind}_field_missing:" + ",".join(missing))


def compute_apply_ledger_entry_digest_v1(body: Mapping[str, Any]) -> str:
    sealed = {
        key: body[key]
        for key in APPLY_LEDGER_ENTRY_KEYS
        if key != "apply_ledger_entry_digest" and key in body
    }
    return compute_content_sha256(sealed)


def compute_revocation_ledger_entry_digest_v1(body: Mapping[str, Any]) -> str:
    sealed = {
        key: body[key]
        for key in REVOCATION_LEDGER_ENTRY_KEYS
        if key != "revocation_ledger_entry_digest" and key in body
    }
    return compute_content_sha256(sealed)


def parse_apply_ledger_entry_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    _validate_keys_v1(payload, APPLY_LEDGER_ENTRY_KEYS, kind="apply_ledger")
    parse_aware_utc_datetime_v1(payload["applied_at"], field_name="applied_at")
    expected = compute_apply_ledger_entry_digest_v1(payload)
    if str(payload["apply_ledger_entry_digest"]) != expected:
        raise ProductiveApplyLedgerError("apply_ledger_entry_digest_mismatch")
    return dict(payload)


def parse_revocation_ledger_entry_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    _validate_keys_v1(payload, REVOCATION_LEDGER_ENTRY_KEYS, kind="revocation_ledger")
    parse_aware_utc_datetime_v1(payload["revoked_at"], field_name="revoked_at")
    expected = compute_revocation_ledger_entry_digest_v1(payload)
    if str(payload["revocation_ledger_entry_digest"]) != expected:
        raise ProductiveApplyLedgerError("revocation_ledger_entry_digest_mismatch")
    return dict(payload)


def load_apply_ledger_entries_v1(path: Path) -> list[dict[str, Any]]:
    return [parse_apply_ledger_entry_v1(row) for row in _load_jsonl_records_v1(path)]


def load_revocation_ledger_entries_v1(path: Path) -> list[dict[str, Any]]:
    return [parse_revocation_ledger_entry_v1(row) for row in _load_jsonl_records_v1(path)]


def assert_revocation_state_available_v1(revocation_ledger_path: Path) -> None:
    """Fail-closed when revocation ledger path is missing or unreadable."""
    path = Path(revocation_ledger_path)
    if not path.exists():
        raise ProductiveApplyLedgerError("revocation_ledger_unavailable")
    if not path.is_file():
        raise ProductiveApplyLedgerError("revocation_ledger_unavailable")
    _ = load_revocation_ledger_entries_v1(path)


def assert_not_revoked_v1(
    *,
    revocation_ledger_path: Path,
    owner_apply_authorization_record_digest: str,
    configuration_digest: str,
) -> None:
    assert_revocation_state_available_v1(revocation_ledger_path)
    records = load_revocation_ledger_entries_v1(revocation_ledger_path)
    for record in records:
        if (
            record["owner_apply_authorization_record_digest"]
            != owner_apply_authorization_record_digest
        ):
            continue
        if record["configuration_digest"] != configuration_digest:
            raise ProductiveApplyLedgerError("revocation_configuration_digest_ambiguity")
        raise ProductiveApplyLedgerError("owner_apply_authorization_revoked")


def find_apply_ledger_entry_v1(
    *,
    apply_ledger_path: Path,
    owner_apply_authorization_record_digest: str,
) -> dict[str, Any] | None:
    if not Path(apply_ledger_path).exists():
        return None
    for entry in load_apply_ledger_entries_v1(apply_ledger_path):
        if (
            entry["owner_apply_authorization_record_digest"]
            == owner_apply_authorization_record_digest
        ):
            return entry
    return None


def append_apply_ledger_entry_v1(
    *,
    apply_ledger_path: Path,
    owner_apply_authorization_record_digest: str,
    configuration_digest: str,
    authorization_digest: str,
    ingress_digest: str,
    applied_at: str,
) -> dict[str, Any]:
    if not is_valid_sha256_hex(owner_apply_authorization_record_digest):
        raise ProductiveApplyLedgerError("apply_digest_invalid")
    existing = find_apply_ledger_entry_v1(
        apply_ledger_path=apply_ledger_path,
        owner_apply_authorization_record_digest=owner_apply_authorization_record_digest,
    )
    if existing is not None:
        if existing["configuration_digest"] != configuration_digest:
            raise ProductiveApplyLedgerError("apply_ledger_idempotency_configuration_mismatch")
        return existing

    parse_aware_utc_datetime_v1(applied_at, field_name="applied_at")
    body = {
        "schema_version": SCHEMA_VERSION,
        "owner_apply_authorization_record_digest": owner_apply_authorization_record_digest,
        "configuration_digest": configuration_digest,
        "authorization_digest": authorization_digest,
        "ingress_digest": ingress_digest,
        "applied_at": format_aware_utc_datetime_v1(
            parse_aware_utc_datetime_v1(applied_at, field_name="applied_at")
        ),
    }
    body["apply_ledger_entry_digest"] = compute_apply_ledger_entry_digest_v1(body)
    entry = parse_apply_ledger_entry_v1(body)
    line = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    _atomic_append_jsonl_line_v1(Path(apply_ledger_path), line)
    return entry


def append_revocation_ledger_entry_v1(
    *,
    revocation_ledger_path: Path,
    owner_apply_authorization_record_digest: str,
    configuration_digest: str,
    reason: str,
    operator_reference: str,
    revoked_at: str,
) -> dict[str, Any]:
    if not str(reason or "").strip():
        raise ProductiveApplyLedgerError("revocation_reason_required")
    if not str(operator_reference or "").strip():
        raise ProductiveApplyLedgerError("revocation_operator_reference_required")
    body = {
        "schema_version": SCHEMA_VERSION,
        "owner_apply_authorization_record_digest": owner_apply_authorization_record_digest,
        "configuration_digest": configuration_digest,
        "revoked_at": format_aware_utc_datetime_v1(
            parse_aware_utc_datetime_v1(revoked_at, field_name="revoked_at")
        ),
        "reason": str(reason).strip(),
        "operator_reference": str(operator_reference).strip(),
    }
    body["revocation_ledger_entry_digest"] = compute_revocation_ledger_entry_digest_v1(body)
    entry = parse_revocation_ledger_entry_v1(body)
    line = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    _atomic_append_jsonl_line_v1(Path(revocation_ledger_path), line)
    return entry


def initialize_empty_revocation_ledger_v1(revocation_ledger_path: Path) -> None:
    path = Path(revocation_ledger_path)
    if path.exists():
        assert_revocation_state_available_v1(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


__all__ = [
    "APPLY_LEDGER_ENTRY_KEYS",
    "F1M9ProductiveApplyLedgerPathsV1",
    "ProductiveApplyLedgerError",
    "REVOCATION_LEDGER_ENTRY_KEYS",
    "SCHEMA_VERSION",
    "append_apply_ledger_entry_v1",
    "append_revocation_ledger_entry_v1",
    "assert_not_revoked_v1",
    "assert_revocation_state_available_v1",
    "find_apply_ledger_entry_v1",
    "initialize_empty_revocation_ledger_v1",
    "load_apply_ledger_entries_v1",
    "load_revocation_ledger_entries_v1",
]
