"""Append-only productive research evidence ledger with chain + crash safety."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    LEDGER_SCHEMA_VERSION,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    DuplicateStatusV1,
    ProductiveEvidenceAccumulationError,
    ProductiveLedgerEnvelopeV1,
    ProductiveResearchEvidenceRecordV1,
    ValidationStatusV1,
    digest_excluding_keys,
    sha256_hex,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.validation_v1 import (
    attach_validation_v1,
    productive_record_from_mapping_v1,
    should_quarantine_v1,
    validate_productive_evidence_record_v1,
)

GENESIS_CHAIN_DIGEST = "0" * 64
RECORD_KIND_EVIDENCE = "PRODUCTIVE_EVIDENCE"
RECORD_KIND_QUARANTINE = "QUARANTINE"


def _atomic_append_line_v1(path: Path, line: str) -> None:
    """Append one JSONL line with durable rename semantics for crash safety.

    Strategy: write full existing content + new line to a sibling temp file,
    fsync, then atomic replace. Prevents torn/partial valid ledger lines.
    """
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


def _envelope_digest_v1(payload: Mapping[str, Any]) -> str:
    return digest_excluding_keys(payload, exclude=("ledger_chain_digest",))


def _build_envelope_v1(
    *,
    sequence: int,
    prev_digest: str,
    record_kind: str,
    productive_evidence: Mapping[str, Any],
    research_join: Optional[Mapping[str, Any]],
    quarantine_reasons: Sequence[str],
) -> ProductiveLedgerEnvelopeV1:
    provisional = {
        "ledger_record_sequence": int(sequence),
        "ledger_schema_version": LEDGER_SCHEMA_VERSION,
        "prev_ledger_chain_digest": prev_digest,
        "productive_evidence": dict(productive_evidence),
        "quarantine_reasons": list(quarantine_reasons),
        "record_kind": record_kind,
        "research_join": None if research_join is None else dict(research_join),
    }
    chain = sha256_hex(
        {
            "ledger_schema_version": LEDGER_SCHEMA_VERSION,
            "prev_ledger_chain_digest": prev_digest,
            "productive_evidence_digest": sha256_hex(dict(productive_evidence)),
            "quarantine_reasons": list(quarantine_reasons),
            "record_kind": record_kind,
            "research_join_digest": (
                None if research_join is None else sha256_hex(dict(research_join))
            ),
            "sequence": int(sequence),
        }
    )
    return ProductiveLedgerEnvelopeV1(
        ledger_schema_version=LEDGER_SCHEMA_VERSION,
        ledger_record_sequence=int(sequence),
        prev_ledger_chain_digest=prev_digest,
        ledger_chain_digest=chain,
        record_kind=record_kind,
        productive_evidence=dict(productive_evidence),
        research_join=None if research_join is None else dict(research_join),
        quarantine_reasons=tuple(quarantine_reasons),
    )


def load_productive_evidence_ledger_v1(
    ledger_path: Path,
    *,
    fail_closed_on_corrupt_tail: bool = True,
) -> list[ProductiveLedgerEnvelopeV1]:
    path = Path(ledger_path)
    if not path.exists():
        return []
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ProductiveEvidenceAccumulationError(f"ledger_read_failed:{exc}") from exc

    envelopes: list[ProductiveLedgerEnvelopeV1] = []
    prev = GENESIS_CHAIN_DIGEST
    expected_seq = 1
    lines = raw_text.splitlines()
    for line_no, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            if fail_closed_on_corrupt_tail and line_no == len(lines):
                raise ProductiveEvidenceAccumulationError(
                    f"ledger_corrupt_tail:line={line_no}:{exc.msg}"
                ) from exc
            raise ProductiveEvidenceAccumulationError(
                f"ledger_corrupt_json:line={line_no}:{exc.msg}"
            ) from exc
        if not isinstance(payload, dict):
            raise ProductiveEvidenceAccumulationError(
                f"ledger_record_must_be_object:line={line_no}"
            )
        if payload.get("ledger_schema_version") != LEDGER_SCHEMA_VERSION:
            raise ProductiveEvidenceAccumulationError(
                f"ledger_schema_version_mismatch:line={line_no}"
            )
        seq = int(payload.get("ledger_record_sequence") or -1)
        if seq != expected_seq:
            raise ProductiveEvidenceAccumulationError(
                f"ledger_sequence_gap:line={line_no}:expected={expected_seq}:got={seq}"
            )
        if payload.get("prev_ledger_chain_digest") != prev:
            raise ProductiveEvidenceAccumulationError(f"ledger_chain_break:line={line_no}")
        envelope = _build_envelope_v1(
            sequence=seq,
            prev_digest=prev,
            record_kind=str(payload.get("record_kind")),
            productive_evidence=dict(payload.get("productive_evidence") or {}),
            research_join=(
                None
                if payload.get("research_join") is None
                else dict(payload.get("research_join") or {})
            ),
            quarantine_reasons=tuple(payload.get("quarantine_reasons") or ()),
        )
        if envelope.ledger_chain_digest != payload.get("ledger_chain_digest"):
            raise ProductiveEvidenceAccumulationError(
                f"ledger_chain_digest_mismatch:line={line_no}"
            )
        envelopes.append(envelope)
        prev = envelope.ledger_chain_digest
        expected_seq += 1
    return envelopes


def _find_duplicate_v1(
    existing: Sequence[ProductiveLedgerEnvelopeV1],
    candidate: ProductiveResearchEvidenceRecordV1,
) -> DuplicateStatusV1:
    for env in existing:
        if env.record_kind != RECORD_KIND_EVIDENCE:
            continue
        prior = productive_record_from_mapping_v1(env.productive_evidence)
        if prior.evidence_record_id == candidate.evidence_record_id:
            if prior.record_digest == candidate.record_digest:
                return DuplicateStatusV1.DUPLICATE_IDEMPOTENT
            return DuplicateStatusV1.DUPLICATE_CONFLICT
        if prior.semantic_identity_v1() == candidate.semantic_identity_v1():
            if prior.record_digest == candidate.record_digest:
                return DuplicateStatusV1.DUPLICATE_IDEMPOTENT
            return DuplicateStatusV1.DUPLICATE_CONFLICT
    return DuplicateStatusV1.UNIQUE


def append_productive_evidence_record_v1(
    *,
    ledger_path: Path,
    quarantine_ledger_path: Path | None,
    record: ProductiveResearchEvidenceRecordV1,
    research_join: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate, dedupe, and append (or quarantine) one productive evidence record."""
    validated = attach_validation_v1(record)
    status, reasons = validate_productive_evidence_record_v1(validated)
    existing = load_productive_evidence_ledger_v1(ledger_path)

    duplicate = _find_duplicate_v1(existing, validated)
    if duplicate == DuplicateStatusV1.DUPLICATE_CONFLICT:
        raise ProductiveEvidenceAccumulationError("unresolvable_duplicate_identity")
    if duplicate == DuplicateStatusV1.DUPLICATE_IDEMPOTENT:
        return {
            "action": "IDEMPOTENT_NOOP",
            "duplicate_status": duplicate.value,
            "evidence_record_id": validated.evidence_record_id,
            "ledger_path": str(ledger_path),
            "validation_status": status.value,
        }

    payload = validated.to_dict()
    payload["duplicate_status"] = duplicate.value
    payload["validation_status"] = status.value
    payload["rejection_reasons"] = list(reasons)
    payload["record_digest"] = digest_excluding_keys(payload, exclude=("record_digest",))
    final_record = productive_record_from_mapping_v1(payload)

    sequence = len(existing) + 1
    prev = existing[-1].ledger_chain_digest if existing else GENESIS_CHAIN_DIGEST

    if should_quarantine_v1(status, reasons):
        target = Path(quarantine_ledger_path or (Path(ledger_path).parent / "quarantine.jsonl"))
        q_existing = load_productive_evidence_ledger_v1(target) if target.exists() else []
        q_seq = len(q_existing) + 1
        q_prev = q_existing[-1].ledger_chain_digest if q_existing else GENESIS_CHAIN_DIGEST
        envelope = _build_envelope_v1(
            sequence=q_seq,
            prev_digest=q_prev,
            record_kind=RECORD_KIND_QUARANTINE,
            productive_evidence=final_record.to_dict(),
            research_join=None,
            quarantine_reasons=reasons,
        )
        _atomic_append_line_v1(
            target,
            json.dumps(envelope.to_dict(), sort_keys=True, separators=(",", ":"), default=str),
        )
        return {
            "action": "QUARANTINED",
            "duplicate_status": duplicate.value,
            "evidence_record_id": final_record.evidence_record_id,
            "ledger_path": str(target),
            "quarantine_reasons": list(reasons),
            "validation_status": ValidationStatusV1.QUARANTINED.value,
        }

    envelope = _build_envelope_v1(
        sequence=sequence,
        prev_digest=prev,
        record_kind=RECORD_KIND_EVIDENCE,
        productive_evidence=final_record.to_dict(),
        research_join=None if research_join is None else dict(research_join),
        quarantine_reasons=(),
    )
    _atomic_append_line_v1(
        Path(ledger_path),
        json.dumps(envelope.to_dict(), sort_keys=True, separators=(",", ":"), default=str),
    )
    return {
        "action": "APPENDED",
        "duplicate_status": duplicate.value,
        "evidence_record_id": final_record.evidence_record_id,
        "envelope": envelope.to_dict(),
        "ledger_path": str(ledger_path),
        "validation_status": status.value,
    }


def valid_productive_records_from_ledger_v1(
    ledger_path: Path,
) -> list[ProductiveResearchEvidenceRecordV1]:
    out: list[ProductiveResearchEvidenceRecordV1] = []
    for env in load_productive_evidence_ledger_v1(ledger_path):
        if env.record_kind != RECORD_KIND_EVIDENCE:
            continue
        record = productive_record_from_mapping_v1(env.productive_evidence)
        status, _ = validate_productive_evidence_record_v1(record)
        if status == ValidationStatusV1.VALID:
            out.append(record)
    return out


def ledger_digest_v1(ledger_path: Path) -> str:
    envelopes = load_productive_evidence_ledger_v1(ledger_path)
    if not envelopes:
        return GENESIS_CHAIN_DIGEST
    return envelopes[-1].ledger_chain_digest
