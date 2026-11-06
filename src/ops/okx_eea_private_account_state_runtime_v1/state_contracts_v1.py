"""Normalized private-state contracts (V1)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def body_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PrivateStateProvenanceV1:
    observation_source_class: str
    transport: str
    endpoint_or_channel: str
    venue_host_family: str
    instrument: Optional[str]
    venue_timestamp_ms: Optional[int]
    captured_at: str
    session_identity: str
    body_digest: str
    credential_class: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PrivateStateQualityV1:
    state: str
    stale_reason: Optional[str] = None
    reconciliation_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AccountConfigStateV1:
    acct_lv: Optional[str]
    pos_mode: Optional[str]
    quality: PrivateStateQualityV1
    provenance: PrivateStateProvenanceV1

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_kind": "AccountConfigStateV1",
            "acct_lv": self.acct_lv,
            "pos_mode": self.pos_mode,
            "quality": self.quality.to_dict(),
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True)
class BalanceSnapshotV1:
    total_eq: Optional[str]
    avail_eq: Optional[str]
    ccy: Optional[str]
    quality: PrivateStateQualityV1
    provenance: PrivateStateProvenanceV1

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_kind": "BalanceSnapshotV1",
            "total_eq": self.total_eq,
            "avail_eq": self.avail_eq,
            "ccy": self.ccy,
            "quality": self.quality.to_dict(),
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True)
class PositionStateV1:
    inst_id: str
    pos_side: Optional[str]
    pos: str
    avg_px: Optional[str]
    quality: PrivateStateQualityV1
    provenance: PrivateStateProvenanceV1

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_kind": "PositionStateV1",
            "instId": self.inst_id,
            "posSide": self.pos_side,
            "pos": self.pos,
            "avgPx": self.avg_px,
            "quality": self.quality.to_dict(),
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True)
class OrderSnapshotV1:
    inst_id: str
    cl_ord_id: Optional[str]
    ord_id: Optional[str]
    state: str
    quality: PrivateStateQualityV1
    provenance: PrivateStateProvenanceV1

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_kind": "OrderSnapshotV1",
            "instId": self.inst_id,
            "clOrdId": self.cl_ord_id,
            "ordId": self.ord_id,
            "state": self.state,
            "quality": self.quality.to_dict(),
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True)
class FillFactV1:
    inst_id: str
    trade_id: str
    ord_id: Optional[str]
    cl_ord_id: Optional[str]
    fill_sz: str
    fill_px: str
    quality: PrivateStateQualityV1
    provenance: PrivateStateProvenanceV1

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_kind": "FillFactV1",
            "instId": self.inst_id,
            "tradeId": self.trade_id,
            "ordId": self.ord_id,
            "clOrdId": self.cl_ord_id,
            "fillSz": self.fill_sz,
            "fillPx": self.fill_px,
            "quality": self.quality.to_dict(),
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True)
class ReconciliationSnapshotV1:
    reconciliation_id: str
    rest_ws_disagreement: str
    safe_adopt_exchange_truth: bool
    trusted_boundary_established: bool
    notes: tuple[str, ...]
    quality: PrivateStateQualityV1

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_kind": "ReconciliationSnapshotV1",
            "reconciliation_id": self.reconciliation_id,
            "rest_ws_disagreement": self.rest_ws_disagreement,
            "safe_adopt_exchange_truth": self.safe_adopt_exchange_truth,
            "trusted_boundary_established": self.trusted_boundary_established,
            "notes": list(self.notes),
            "quality": self.quality.to_dict(),
        }


@dataclass(frozen=True)
class PrivateStateRecordV1:
    schema_version: str
    state_digest: str
    payload: dict[str, Any]
    persisted_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
