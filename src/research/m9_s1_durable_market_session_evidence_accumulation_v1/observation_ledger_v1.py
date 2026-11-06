"""Append-only M9-S1 market session observation ledger."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from research.m9_s1_durable_market_session_evidence_accumulation_v1.constants_v1 import (
    OBSERVATION_LEDGER_SCHEMA_VERSION,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.models_v1 import (
    M9S1EvidenceAccumulationError,
    M9S1MarketSessionObservationV1,
    digest_excluding_keys,
    sha256_hex,
)


def _atomic_append_line_v1(path: Path, line: str) -> None:
    path = Path(path)
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


def load_m9_s1_observation_ledger_v1(path: Path) -> list[dict[str, Any]]:
    ledger_path = Path(path)
    if not ledger_path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_no, raw in enumerate(ledger_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise M9S1EvidenceAccumulationError(
                f"observation_ledger_corrupt_json:line={line_no}:{exc.msg}"
            ) from exc
        if not isinstance(payload, dict):
            raise M9S1EvidenceAccumulationError(
                f"observation_ledger_record_must_be_object:line={line_no}"
            )
        if payload.get("ledger_schema_version") != OBSERVATION_LEDGER_SCHEMA_VERSION:
            raise M9S1EvidenceAccumulationError("observation_ledger_schema_version_mismatch")
        expected = digest_excluding_keys(
            payload,
            exclude=frozenset(
                {
                    "record_digest",
                    "ledger_schema_version",
                    "ledger_sequence",
                    "ledger_chain_digest",
                }
            ),
        )
        if payload.get("record_digest") != expected:
            raise M9S1EvidenceAccumulationError(
                f"observation_ledger_digest_mismatch:line={line_no}"
            )
        records.append(payload)
    return records


def append_m9_s1_observation_v1(
    *,
    ledger_path: Path,
    observation: M9S1MarketSessionObservationV1,
) -> dict[str, Any]:
    existing = load_m9_s1_observation_ledger_v1(ledger_path)
    for row in existing:
        if row.get("dedup_identity") == observation.dedup_identity:
            return {
                "action": "DUPLICATE_IDEMPOTENT",
                "observation_id": row.get("observation_id") or observation.observation_id,
            }

    envelope = dict(observation.to_dict())
    envelope["ledger_schema_version"] = OBSERVATION_LEDGER_SCHEMA_VERSION
    envelope["ledger_sequence"] = len(existing) + 1
    envelope["ledger_chain_digest"] = sha256_hex(
        {
            "ledger_schema_version": OBSERVATION_LEDGER_SCHEMA_VERSION,
            "ledger_sequence": envelope["ledger_sequence"],
            "prev_digest": existing[-1]["ledger_chain_digest"] if existing else "0" * 64,
            "record_digest": observation.record_digest,
        }
    )
    line = json.dumps(envelope, sort_keys=True, separators=(",", ":"), default=str)
    _atomic_append_line_v1(ledger_path, line)
    return {"action": "APPENDED", "observation_id": observation.observation_id}
