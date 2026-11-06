"""Append-only revocation and consumption ledgers for campaign authorization."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.constants_v1 import (
    CONSUMPTION_REQUIRED_FIELDS,
    REVOCATION_REQUIRED_FIELDS,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.expiry_v1 import (
    format_aware_utc_datetime_v1,
    parse_aware_utc_datetime_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.models_v1 import (
    CampaignAuthorizationError,
    digest_excluding_keys,
)


def resolve_ledger_path_v1(*, evidence_root: Path, relative_or_absolute: str) -> Path:
    raw = Path(relative_or_absolute)
    if raw.is_absolute():
        return raw
    return (Path(evidence_root) / raw).resolve()


def _atomic_append_jsonl_line_v1(path: Path, line: str) -> None:
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        if existing and not existing.endswith("\n"):
            existing += "\n"
        new_body = existing + line + "\n"
        tmp = path.with_suffix(path.suffix + ".tmp")
        # Temporary files have no authority.
        with tmp.open("w", encoding="utf-8") as handle:
            handle.write(new_body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        try:
            dir_fd = os.open(str(path.parent), os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass
    except OSError as exc:
        raise CampaignAuthorizationError(f"ledger_persist_error:{exc}") from exc


def _load_jsonl_records_v1(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    if not path.is_file():
        raise CampaignAuthorizationError("ledger_not_file")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CampaignAuthorizationError(f"ledger_read_error:{exc}") from exc
    records: list[dict[str, Any]] = []
    for idx, line in enumerate(text.splitlines()):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CampaignAuthorizationError(f"ledger_corrupt_line:{idx}") from exc
        if not isinstance(raw, dict):
            raise CampaignAuthorizationError(f"ledger_corrupt_record:{idx}")
        records.append(raw)
    return records


def compute_revocation_record_digest_v1(payload: Mapping[str, Any]) -> str:
    return digest_excluding_keys(payload, exclude=("revocation_record_digest",))


def compute_consumption_record_digest_v1(payload: Mapping[str, Any]) -> str:
    return digest_excluding_keys(payload, exclude=("consumption_record_digest",))


def _validate_required_fields_v1(
    payload: Mapping[str, Any],
    required: Sequence[str],
    *,
    kind: str,
) -> None:
    missing = [f for f in required if f not in payload]
    if missing:
        raise CampaignAuthorizationError(f"{kind}_field_missing:" + ",".join(missing))
    unknown = sorted(set(payload.keys()) - set(required))
    if unknown:
        raise CampaignAuthorizationError(f"{kind}_unknown_field:" + ",".join(unknown))


def parse_revocation_record_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    _validate_required_fields_v1(payload, REVOCATION_REQUIRED_FIELDS, kind="revocation")
    parse_aware_utc_datetime_v1(payload["revoked_at"], field_name="revoked_at")
    expected = compute_revocation_record_digest_v1(payload)
    if str(payload["revocation_record_digest"]) != expected:
        raise CampaignAuthorizationError("revocation_record_digest_mismatch")
    return {
        "authorization_id": str(payload["authorization_id"]),
        "authorization_digest": str(payload["authorization_digest"]),
        "revoked_at": str(payload["revoked_at"]),
        "reason": str(payload["reason"]),
        "operator_reference": str(payload["operator_reference"]),
        "revocation_record_digest": str(payload["revocation_record_digest"]),
    }


def parse_consumption_record_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    _validate_required_fields_v1(payload, CONSUMPTION_REQUIRED_FIELDS, kind="consumption")
    parse_aware_utc_datetime_v1(payload["consumed_at"], field_name="consumed_at")
    expected = compute_consumption_record_digest_v1(payload)
    if str(payload["consumption_record_digest"]) != expected:
        raise CampaignAuthorizationError("consumption_record_digest_mismatch")
    return {
        "authorization_id": str(payload["authorization_id"]),
        "authorization_digest": str(payload["authorization_digest"]),
        "session_id": str(payload["session_id"]),
        "consumed_at": str(payload["consumed_at"]),
        "consumption_index": int(payload["consumption_index"]),
        "repository_sha": str(payload["repository_sha"]),
        "campaign_id": str(payload["campaign_id"]),
        "consumption_record_digest": str(payload["consumption_record_digest"]),
    }


def load_revocation_records_v1(path: Path) -> list[dict[str, Any]]:
    return [parse_revocation_record_v1(r) for r in _load_jsonl_records_v1(path)]


def load_consumption_records_v1(path: Path) -> list[dict[str, Any]]:
    return [parse_consumption_record_v1(r) for r in _load_jsonl_records_v1(path)]


def assert_not_revoked_v1(
    *,
    revocation_ledger_path: Path,
    authorization_id: str,
    authorization_digest: str,
) -> None:
    try:
        records = load_revocation_records_v1(revocation_ledger_path)
    except CampaignAuthorizationError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise CampaignAuthorizationError("revocation_ledger_unreadable") from exc
    for record in records:
        if record["authorization_id"] == authorization_id:
            if record["authorization_digest"] != authorization_digest:
                raise CampaignAuthorizationError("revocation_digest_ambiguity")
            raise CampaignAuthorizationError("authorization_revoked")


def append_revocation_record_v1(
    *,
    revocation_ledger_path: Path,
    authorization_id: str,
    authorization_digest: str,
    reason: str,
    operator_reference: str,
    revoked_at: datetime | str,
) -> dict[str, Any]:
    """Append-only irreversible revocation. Does not mutate authorization artifacts."""
    if not str(reason or "").strip():
        raise CampaignAuthorizationError("revocation_reason_required")
    if not str(operator_reference or "").strip():
        raise CampaignAuthorizationError("revocation_operator_reference_required")
    revoked_s = format_aware_utc_datetime_v1(
        parse_aware_utc_datetime_v1(revoked_at, field_name="revoked_at")
    )
    provisional = {
        "authorization_id": str(authorization_id),
        "authorization_digest": str(authorization_digest),
        "revoked_at": revoked_s,
        "reason": str(reason).strip(),
        "operator_reference": str(operator_reference).strip(),
    }
    provisional["revocation_record_digest"] = compute_revocation_record_digest_v1(provisional)
    record = parse_revocation_record_v1(provisional)
    line = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    _atomic_append_jsonl_line_v1(Path(revocation_ledger_path), line)
    records = load_revocation_records_v1(Path(revocation_ledger_path))
    matches = [
        r
        for r in records
        if r["authorization_id"] == authorization_id
        and r["authorization_digest"] == authorization_digest
    ]
    if not matches:
        raise CampaignAuthorizationError("revocation_persist_verify_failed")
    if record["revocation_record_digest"] not in {r["revocation_record_digest"] for r in matches}:
        raise CampaignAuthorizationError("revocation_persist_verify_failed")
    return record


def append_consumption_record_v1(
    *,
    consumption_ledger_path: Path,
    authorization_id: str,
    authorization_digest: str,
    session_id: str,
    repository_sha: str,
    campaign_id: str,
    consumption_index: int,
    consumed_at: datetime | str,
) -> dict[str, Any]:
    consumed_s = format_aware_utc_datetime_v1(
        parse_aware_utc_datetime_v1(consumed_at, field_name="consumed_at")
    )
    provisional = {
        "authorization_id": str(authorization_id),
        "authorization_digest": str(authorization_digest),
        "session_id": str(session_id),
        "consumed_at": consumed_s,
        "consumption_index": int(consumption_index),
        "repository_sha": str(repository_sha),
        "campaign_id": str(campaign_id),
    }
    provisional["consumption_record_digest"] = compute_consumption_record_digest_v1(provisional)
    record = parse_consumption_record_v1(provisional)
    line = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    _atomic_append_jsonl_line_v1(Path(consumption_ledger_path), line)
    return record


def find_session_consumption_v1(
    records: Sequence[Mapping[str, Any]],
    *,
    authorization_id: str,
    session_id: str,
) -> Optional[dict[str, Any]]:
    for record in records:
        if (
            str(record.get("authorization_id")) == authorization_id
            and str(record.get("session_id")) == session_id
        ):
            return dict(record)
    return None
