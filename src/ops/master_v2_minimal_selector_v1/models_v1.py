"""Typed DTOs for Master V2 minimal selector V1.

OWNER_POLICY_VERSION=V1
HISTORICAL_CLAIM=false
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from src.ops.master_v2_minimal_selector_v1.constants_v1 import (
    ALLOWLIST_SELECTION_AUTHORITY,
    AUTHORITY_OWNER,
    CAP22_ROLE,
    CAP22_SELECTION_AUTHORITY,
    CAPABILITY_ID,
    CURRENT_GFU_SEMANTIC_IMPORT_ALLOWED,
    D1_CLASS,
    D1_HISTORICAL_CLAIM,
    D1_INSTRUMENT_CLASS,
    D2_BTC_OR_BASE_EXCLUSION,
    D2_CLASS,
    D2_HISTORICAL_CLAIM,
    D3_CLASS,
    D3_HISTORICAL_CLAIM,
    D3_MULTI_ELIGIBLE_RESOLUTION,
    D4_CLASS,
    D4_HISTORICAL_CLAIM,
    D4_SELECTION_REFRESH_MODE,
    DASHBOARD_AUTHORITY,
    HISTORICAL_CLAIM,
    LIVE_AUTHORIZED,
    MANUAL_OVERRIDE_ALLOWED,
    NO_CANDIDATE_POLICY,
    NO_HOT_PATH_RESCAN,
    NO_IMPLICIT_FALLBACK_INSTRUMENT,
    ORDERS_AUTHORIZED,
    OWNER,
    OWNER_SELECTOR_POLICY_VERSION,
    POLICY_ID,
    PRODUCER_VERSION,
    RANKING_POLICY_REQUIRED_NOW,
    RUNTIME_ACTIVATION_ALLOWED,
    SCHEMA_VERSION,
    SELECTED_COUNT,
    SELECTOR_HAS_DOUBLE_PLAY_SIDE_AUTHORITY,
    SELECTOR_HAS_LEVERAGE_AUTHORITY,
    SELECTOR_HAS_POSITION_SIZING_AUTHORITY,
    SELECTOR_HAS_TRADING_AUTHORITY,
    STALE_SELECTION_POLICY,
    STATUS_NO_SELECTION,
    VENUE,
)


def canonical_json_dumps(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compute_policy_digest_v1() -> str:
    payload = {
        "OWNER_SELECTOR_POLICY_VERSION": OWNER_SELECTOR_POLICY_VERSION,
        "HISTORICAL_CLAIM": HISTORICAL_CLAIM,
        "VENUE": VENUE,
        "D1_INSTRUMENT_CLASS": D1_INSTRUMENT_CLASS,
        "D1_CLASS": D1_CLASS,
        "D1_HISTORICAL_CLAIM": D1_HISTORICAL_CLAIM,
        "D2_BTC_OR_BASE_EXCLUSION": D2_BTC_OR_BASE_EXCLUSION,
        "D2_CLASS": D2_CLASS,
        "D2_HISTORICAL_CLAIM": D2_HISTORICAL_CLAIM,
        "D3_MULTI_ELIGIBLE_RESOLUTION": D3_MULTI_ELIGIBLE_RESOLUTION,
        "D3_CLASS": D3_CLASS,
        "D3_HISTORICAL_CLAIM": D3_HISTORICAL_CLAIM,
        "D4_SELECTION_REFRESH_MODE": D4_SELECTION_REFRESH_MODE,
        "D4_CLASS": D4_CLASS,
        "D4_HISTORICAL_CLAIM": D4_HISTORICAL_CLAIM,
        "SELECTED_COUNT": SELECTED_COUNT,
        "NO_CANDIDATE_POLICY": NO_CANDIDATE_POLICY,
        "STALE_SELECTION_POLICY": STALE_SELECTION_POLICY,
        "NO_IMPLICIT_FALLBACK_INSTRUMENT": NO_IMPLICIT_FALLBACK_INSTRUMENT,
        "NO_HOT_PATH_RESCAN": NO_HOT_PATH_RESCAN,
        "RANKING_POLICY_REQUIRED_NOW": RANKING_POLICY_REQUIRED_NOW,
        "CAP22_SELECTION_AUTHORITY_ALLOWED": CAP22_SELECTION_AUTHORITY,
        "CURRENT_GFU_SEMANTIC_IMPORT_ALLOWED": CURRENT_GFU_SEMANTIC_IMPORT_ALLOWED,
        "POLICY_ID": POLICY_ID,
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "PRODUCER_VERSION": PRODUCER_VERSION,
    }
    return sha256_hex(canonical_json_dumps(payload))


def authority_block() -> dict[str, Any]:
    return {
        "AUTHORITY_OWNER": AUTHORITY_OWNER,
        "OWNER": OWNER,
        "OWNER_SELECTOR_POLICY_VERSION": OWNER_SELECTOR_POLICY_VERSION,
        "HISTORICAL_CLAIM": HISTORICAL_CLAIM,
        "SELECTOR_HAS_TRADING_AUTHORITY": SELECTOR_HAS_TRADING_AUTHORITY,
        "SELECTOR_HAS_POSITION_SIZING_AUTHORITY": SELECTOR_HAS_POSITION_SIZING_AUTHORITY,
        "SELECTOR_HAS_LEVERAGE_AUTHORITY": SELECTOR_HAS_LEVERAGE_AUTHORITY,
        "SELECTOR_HAS_DOUBLE_PLAY_SIDE_AUTHORITY": SELECTOR_HAS_DOUBLE_PLAY_SIDE_AUTHORITY,
        "CAP22_ROLE": CAP22_ROLE,
        "CAP22_SELECTION_AUTHORITY": CAP22_SELECTION_AUTHORITY,
        "DASHBOARD_AUTHORITY": DASHBOARD_AUTHORITY,
        "ALLOWLIST_SELECTION_AUTHORITY": ALLOWLIST_SELECTION_AUTHORITY,
        "MANUAL_OVERRIDE_ALLOWED": MANUAL_OVERRIDE_ALLOWED,
        "RUNTIME_ACTIVATION_ALLOWED": RUNTIME_ACTIVATION_ALLOWED,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "ORDERS_AUTHORIZED": ORDERS_AUTHORIZED,
        "RANKING_POLICY_REQUIRED_NOW": RANKING_POLICY_REQUIRED_NOW,
        "NO_IMPLICIT_FALLBACK_INSTRUMENT": NO_IMPLICIT_FALLBACK_INSTRUMENT,
        "NO_HOT_PATH_RESCAN": NO_HOT_PATH_RESCAN,
    }


@dataclass(frozen=True)
class StructuralEligibilityRowV1:
    venue_native_inst_id: str
    instrument_type: str
    eligible: bool
    exclusion_reason_codes: tuple[str, ...]
    mark_price_present: bool
    exp_time_empty: bool
    base_currency: str = ""
    quote_currency: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "venue_native_inst_id": self.venue_native_inst_id,
            "instrument_type": self.instrument_type,
            "eligible": self.eligible,
            "exclusion_reason_codes": list(self.exclusion_reason_codes),
            "mark_price_present": self.mark_price_present,
            "exp_time_empty": self.exp_time_empty,
            "base_currency": self.base_currency,
            "quote_currency": self.quote_currency,
        }


@dataclass(frozen=True)
class MasterV2SelectionDecisionV1:
    """Durable selection decision. No trading or sizing fields."""

    schema_version: str
    capability_id: str
    producer_version: str
    policy_version: str
    policy_id: str
    historical_claim: bool
    venue: str
    source_snapshot_digest: str
    source_event_time: str
    decision_status: str
    eligible_count: int
    selected_native_instrument_id: Optional[str]
    decision_reason: str
    policy_digest: str
    identity_digest: str
    eligible_native_instrument_ids: tuple[str, ...] = ()
    ranking_input_ignored: bool = True
    cap22_role: str = CAP22_ROLE
    cap22_selection_authority: bool = CAP22_SELECTION_AUTHORITY
    authority: Mapping[str, Any] = field(default_factory=dict)
    call_graph: tuple[str, ...] = ()
    classified_rows: tuple[StructuralEligibilityRowV1, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "capability_id": self.capability_id,
            "producer_version": self.producer_version,
            "policy_version": self.policy_version,
            "policy_id": self.policy_id,
            "historical_claim": bool(self.historical_claim),
            "venue": self.venue,
            "source_snapshot_digest": self.source_snapshot_digest,
            "source_event_time": self.source_event_time,
            "decision_status": self.decision_status,
            "eligible_count": int(self.eligible_count),
            "selected_native_instrument_id": self.selected_native_instrument_id,
            "decision_reason": self.decision_reason,
            "policy_digest": self.policy_digest,
            "identity_digest": self.identity_digest,
            "eligible_native_instrument_ids": list(self.eligible_native_instrument_ids),
            "ranking_input_ignored": bool(self.ranking_input_ignored),
            "cap22_role": self.cap22_role,
            "cap22_selection_authority": bool(self.cap22_selection_authority),
            "authority": dict(self.authority),
            "call_graph": list(self.call_graph),
            "classified_rows": [row.to_dict() for row in self.classified_rows],
        }

    def identity_payload(self) -> dict[str, Any]:
        """Identity excludes classified row order beyond sorted eligible native ids."""
        return {
            "schema_version": self.schema_version,
            "capability_id": self.capability_id,
            "producer_version": self.producer_version,
            "policy_version": self.policy_version,
            "policy_id": self.policy_id,
            "historical_claim": bool(self.historical_claim),
            "venue": self.venue,
            "source_snapshot_digest": self.source_snapshot_digest,
            "source_event_time": self.source_event_time,
            "decision_status": self.decision_status,
            "eligible_count": int(self.eligible_count),
            "selected_native_instrument_id": self.selected_native_instrument_id,
            "decision_reason": self.decision_reason,
            "policy_digest": self.policy_digest,
            "eligible_native_instrument_ids": list(self.eligible_native_instrument_ids),
            "ranking_input_ignored": True,
            "cap22_role": self.cap22_role,
            "cap22_selection_authority": False,
        }

    def compute_identity_digest(self) -> str:
        return sha256_hex(canonical_json_dumps(self.identity_payload()))

    def with_identity_digest(self) -> "MasterV2SelectionDecisionV1":
        digest = self.compute_identity_digest()
        return MasterV2SelectionDecisionV1(
            schema_version=self.schema_version,
            capability_id=self.capability_id,
            producer_version=self.producer_version,
            policy_version=self.policy_version,
            policy_id=self.policy_id,
            historical_claim=self.historical_claim,
            venue=self.venue,
            source_snapshot_digest=self.source_snapshot_digest,
            source_event_time=self.source_event_time,
            decision_status=self.decision_status,
            eligible_count=self.eligible_count,
            selected_native_instrument_id=self.selected_native_instrument_id,
            decision_reason=self.decision_reason,
            policy_digest=self.policy_digest,
            identity_digest=digest,
            eligible_native_instrument_ids=self.eligible_native_instrument_ids,
            ranking_input_ignored=self.ranking_input_ignored,
            cap22_role=self.cap22_role,
            cap22_selection_authority=self.cap22_selection_authority,
            authority=dict(self.authority),
            call_graph=self.call_graph,
            classified_rows=self.classified_rows,
        )

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "MasterV2SelectionDecisionV1":
        selected = payload.get("selected_native_instrument_id")
        rows = tuple(
            StructuralEligibilityRowV1(
                venue_native_inst_id=str(row.get("venue_native_inst_id") or ""),
                instrument_type=str(row.get("instrument_type") or ""),
                eligible=bool(row.get("eligible", False)),
                exclusion_reason_codes=tuple(
                    str(x) for x in (row.get("exclusion_reason_codes") or ())
                ),
                mark_price_present=bool(row.get("mark_price_present", False)),
                exp_time_empty=bool(row.get("exp_time_empty", False)),
                base_currency=str(row.get("base_currency") or ""),
                quote_currency=str(row.get("quote_currency") or ""),
            )
            for row in (payload.get("classified_rows") or [])
        )
        return MasterV2SelectionDecisionV1(
            schema_version=str(payload.get("schema_version") or SCHEMA_VERSION),
            capability_id=str(payload.get("capability_id") or CAPABILITY_ID),
            producer_version=str(payload.get("producer_version") or PRODUCER_VERSION),
            policy_version=str(payload.get("policy_version") or OWNER_SELECTOR_POLICY_VERSION),
            policy_id=str(payload.get("policy_id") or POLICY_ID),
            historical_claim=bool(payload.get("historical_claim", HISTORICAL_CLAIM)),
            venue=str(payload.get("venue") or VENUE),
            source_snapshot_digest=str(payload.get("source_snapshot_digest") or ""),
            source_event_time=str(payload.get("source_event_time") or ""),
            decision_status=str(payload.get("decision_status") or STATUS_NO_SELECTION),
            eligible_count=int(payload.get("eligible_count") or 0),
            selected_native_instrument_id=None if selected in (None, "") else str(selected),
            decision_reason=str(payload.get("decision_reason") or ""),
            policy_digest=str(payload.get("policy_digest") or ""),
            identity_digest=str(payload.get("identity_digest") or ""),
            eligible_native_instrument_ids=tuple(
                str(x) for x in (payload.get("eligible_native_instrument_ids") or ())
            ),
            ranking_input_ignored=bool(payload.get("ranking_input_ignored", True)),
            cap22_role=str(payload.get("cap22_role") or CAP22_ROLE),
            cap22_selection_authority=bool(payload.get("cap22_selection_authority", False)),
            authority=dict(payload.get("authority") or {}),
            call_graph=tuple(str(x) for x in (payload.get("call_graph") or ())),
            classified_rows=rows,
        )


def empty_no_selection(
    *,
    reason: str,
    source_snapshot_digest: str = "",
    source_event_time: str = "",
    classified_rows: Sequence[StructuralEligibilityRowV1] = (),
    eligible_native_instrument_ids: Sequence[str] = (),
    eligible_count: int = 0,
) -> MasterV2SelectionDecisionV1:
    return MasterV2SelectionDecisionV1(
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        producer_version=PRODUCER_VERSION,
        policy_version=OWNER_SELECTOR_POLICY_VERSION,
        policy_id=POLICY_ID,
        historical_claim=HISTORICAL_CLAIM,
        venue=VENUE,
        source_snapshot_digest=source_snapshot_digest,
        source_event_time=source_event_time,
        decision_status=STATUS_NO_SELECTION,
        eligible_count=int(eligible_count),
        selected_native_instrument_id=None,
        decision_reason=reason,
        policy_digest=compute_policy_digest_v1(),
        identity_digest="",
        eligible_native_instrument_ids=tuple(eligible_native_instrument_ids),
        ranking_input_ignored=True,
        cap22_role=CAP22_ROLE,
        cap22_selection_authority=CAP22_SELECTION_AUTHORITY,
        authority=authority_block(),
        call_graph=(),
        classified_rows=tuple(classified_rows),
    ).with_identity_digest()
