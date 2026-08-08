"""Execution evidence + seal for ACTUAL productive start path."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    CAPABILITY_ID,
    MANIFEST_FILENAME,
    OWNER,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.secretref_credential_v1 import (
    assert_no_plaintext_in_payload_v1,
)


class ActualStartEvidenceError(RuntimeError):
    """Fail-closed evidence violation."""


@dataclass(frozen=True)
class EvidenceSealV1:
    sealed: bool
    evidence_dir: str
    manifest_path: str
    entry_count: int
    independently_verifiable: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "sealed": self.sealed,
            "evidence_dir": self.evidence_dir,
            "manifest_path": self.manifest_path,
            "entry_count": self.entry_count,
            "independently_verifiable": self.independently_verifiable,
        }


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_productive_execution_evidence_v1(
    evidence_dir: Path,
    *,
    payload: Mapping[str, Any],
    filename: str = "productive_execution_evidence_v1.json",
    stubbed_acceptance: bool | None = None,
    network_effect: str | None = None,
    order_effect: str | None = None,
    live_order_effect: str = "NONE",
    productive_testnet_campaign_started: bool | None = None,
) -> Path:
    assert_no_plaintext_in_payload_v1(payload)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    path = evidence_dir / filename

    mode = str(payload.get("mode") or "")
    lifecycle = payload.get("lifecycle") if isinstance(payload.get("lifecycle"), dict) else {}
    inferred_stubbed = stubbed_acceptance
    if inferred_stubbed is None:
        inferred_stubbed = mode != "PRODUCTIVE_REAL_NETWORK"
    inferred_network = network_effect
    if inferred_network is None:
        inferred_network = str(
            payload.get("NETWORK_EFFECT")
            or ("TESTNET" if payload.get("allow_wire_send") else "NONE")
        )
    inferred_order = order_effect
    if inferred_order is None:
        inferred_order = str(
            payload.get("ORDER_EFFECT") or ("TESTNET" if payload.get("allow_wire_send") else "NONE")
        )
    inferred_started = productive_testnet_campaign_started
    if inferred_started is None:
        inferred_started = bool(lifecycle.get("started")) and not inferred_stubbed

    body = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "OWNER": OWNER,
        "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": bool(inferred_started),
        "NETWORK_EFFECT": inferred_network,
        "ORDER_EFFECT": inferred_order,
        "LIVE_ORDER_EFFECT": live_order_effect,
        "SECTION_11_13_STARTED": False,
        "STUBBED_ACCEPTANCE": bool(inferred_stubbed),
        "LONG_RUNNING_CAMPAIGN": True,
        "execution_class": (
            "PRODUCTIVE_REAL_TESTNET_CAMPAIGN"
            if not inferred_stubbed
            else "STUBBED_ACCEPTANCE_CAMPAIGN"
        ),
        "campaign_id": lifecycle.get("campaign_id"),
        "execution_start_utc": lifecycle.get("execution_start_utc"),
        "execution_end_utc": lifecycle.get("execution_end_utc"),
        "execution_duration_seconds": lifecycle.get("execution_duration_seconds"),
        "duration_bound_seconds": lifecycle.get("duration_bound_seconds"),
        "cycle_bound": lifecycle.get("cycle_bound"),
        "cycles_started": lifecycle.get("cycles_started"),
        "cycles_completed": lifecycle.get("cycles_completed"),
        "network_request_count": lifecycle.get("network_request_count"),
        "order_attempt_count": lifecycle.get("order_attempt_count"),
        "testnet_order_sent_count": lifecycle.get("testnet_order_sent_count"),
        "transport_response_count": lifecycle.get("transport_response_count"),
        "exchange_ack_count": lifecycle.get("exchange_ack_count"),
        "exchange_reject_count": lifecycle.get("exchange_reject_count"),
        "fill_count": lifecycle.get("fill_count"),
        "partial_fill_count": lifecycle.get("partial_fill_count"),
        "client_order_ids": lifecycle.get("client_order_ids"),
        "exchange_order_ids": lifecycle.get("exchange_order_ids"),
        "bound_reached_reason": lifecycle.get("bound_reached_reason"),
        "campaign_terminal_status": (
            "ABORTED"
            if lifecycle.get("aborted")
            else ("COMPLETED" if lifecycle.get("completed") else "UNKNOWN")
        ),
        "payload": dict(payload),
    }
    assert_no_plaintext_in_payload_v1(body)
    path.write_text(
        json.dumps(body, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return path


def seal_evidence_dir_v1(evidence_dir: Path) -> EvidenceSealV1:
    if not evidence_dir.is_dir():
        raise ActualStartEvidenceError("EVIDENCE_DIR_MISSING")
    manifest_lines: list[str] = []
    for path in sorted(evidence_dir.rglob("*")):
        if not path.is_file() or path.name == MANIFEST_FILENAME:
            continue
        rel = path.relative_to(evidence_dir).as_posix()
        digest = _sha256_bytes(path.read_bytes())
        manifest_lines.append(f"{digest}  {rel}")
    if not manifest_lines:
        raise ActualStartEvidenceError("EVIDENCE_DIR_EMPTY")
    manifest_path = evidence_dir / MANIFEST_FILENAME
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    for line in manifest_lines:
        digest, _, rel = line.partition("  ")
        actual = _sha256_bytes((evidence_dir / rel).read_bytes())
        if actual != digest:
            raise ActualStartEvidenceError(f"EVIDENCE_SEAL_VERIFY_MISMATCH:{rel}")
    return EvidenceSealV1(
        sealed=True,
        evidence_dir=str(evidence_dir),
        manifest_path=str(manifest_path),
        entry_count=len(manifest_lines),
        independently_verifiable=True,
    )


def verify_evidence_seal_v1(evidence_dir: Path) -> int:
    manifest = evidence_dir / MANIFEST_FILENAME
    if not manifest.is_file():
        return 2
    lines = [ln.strip() for ln in manifest.read_text(encoding="utf-8").splitlines() if ln.strip()]
    for line in lines:
        digest, _, rel = line.partition("  ")
        path = evidence_dir / rel
        if not path.is_file():
            return 2
        if _sha256_bytes(path.read_bytes()) != digest:
            return 2
    return 0
