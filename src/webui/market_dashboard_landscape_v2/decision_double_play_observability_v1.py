"""S05/S06 consumer-only Decision and Double Play observability (display only).

Reads CanonicalDecisionSnapshotV1 and DoublePlaySnapshotV1 only.
Never composes decisions, never mirrors Double Play rules, never joins slots
without an explicit shared identifier contract.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .availability import Availability
from .contracts import CanonicalDecisionSnapshotV1, DoublePlaySnapshotV1
from .serialization import serialize_projection
from .source_health_projection_fidelity_v1 import format_freshness_display_v1

CAPABILITY_ID = "LANDSCAPE_DOUBLE_PLAY_AND_DECISION_OBSERVABILITY_FIDELITY_V1"
MULTI_DECISION_TIMELINE_STATUS = "MISSING_DASHBOARD_OBSERVABILITY"
JOIN_CONTRACT_PRESENT = False

_AVAILABILITY_LABELS: Mapping[Availability, str] = {
    Availability.AVAILABLE: "AVAILABLE",
    Availability.NOT_BOUND: "NOT_BOUND",
    Availability.MISSING_SOURCE: "MISSING_SOURCE",
    Availability.STALE: "STALE",
    Availability.INVALID: "INVALID",
}

_PANEL_SUMMARY_KEYS: tuple[str, ...] = ("name", "status", "summary", "blockers")


def _provenance_dict(snap: CanonicalDecisionSnapshotV1 | DoublePlaySnapshotV1) -> dict[str, Any]:
    payload = serialize_projection(snap)
    prov = payload.get("provenance")
    return dict(prov) if isinstance(prov, Mapping) else {}


def _freshness_dict(snap: CanonicalDecisionSnapshotV1 | DoublePlaySnapshotV1) -> dict[str, Any]:
    payload = serialize_projection(snap)
    fresh = payload.get("freshness")
    return dict(fresh) if isinstance(fresh, Mapping) else {}


def _scalar_display(raw: Any, availability: Availability) -> str | None:
    if availability in (Availability.AVAILABLE, Availability.STALE):
        if raw is None:
            return None
        text = str(raw).strip()
        return text if text else None
    return None


def _codes_display(codes: Sequence[str], availability: Availability) -> list[str]:
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        return list(codes)
    return [str(code) for code in codes]


def _codes_display_label(codes: Sequence[str], availability: Availability) -> str:
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        label = _AVAILABILITY_LABELS[availability]
        if codes:
            return f"{label} · {', '.join(str(c) for c in codes)}"
        return label
    if not codes:
        return "—"
    return ", ".join(str(c) for c in codes)


def build_canonical_decision_observability_v1(
    snap: CanonicalDecisionSnapshotV1,
) -> dict[str, Any]:
    """S05 panel from bound canonical_decision snapshot only."""
    availability = snap.availability
    freshness = _freshness_dict(snap)
    provenance = _provenance_dict(snap)
    return {
        "source_family": "S05",
        "slot": "canonical_decision",
        "schema_id": snap.schema_id,
        "availability": availability.value,
        "availability_label": _AVAILABILITY_LABELS[availability],
        "is_available": availability is Availability.AVAILABLE,
        "is_stale": availability is Availability.STALE,
        "decision_display": _scalar_display(snap.decision, availability)
        or _AVAILABILITY_LABELS[availability],
        "direction_display": _scalar_display(snap.direction, availability)
        or _AVAILABILITY_LABELS[availability],
        "instrument_id_display": _scalar_display(snap.instrument_id, availability)
        or _AVAILABILITY_LABELS[availability],
        "decision_id_display": _scalar_display(snap.decision_id, availability) or "—",
        "evidence_schema_version_display": _scalar_display(
            snap.evidence_schema_version, availability
        )
        or "—",
        "reason_codes": _codes_display(snap.reason_codes, availability),
        "reason_codes_display": _codes_display_label(snap.reason_codes, availability),
        "blockers": _codes_display(snap.blockers, availability),
        "blockers_display": _codes_display_label(snap.blockers, availability),
        "freshness": freshness,
        "freshness_display": format_freshness_display_v1(freshness),
        "is_stale_flag": freshness.get("is_stale") is True,
        "stale_reason": freshness.get("stale_reason"),
        "provenance": provenance,
        "source_kind": provenance.get("source_kind"),
        "source_reference": provenance.get("source_reference"),
        "producer_module": provenance.get("producer_module"),
        "provenance_generated_at": provenance.get("generated_at"),
        "provenance_effective_at": provenance.get("effective_at"),
        "evidence_digest": provenance.get("evidence_digest"),
    }


def _panel_row_display(row: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"raw_keys": sorted(str(k) for k in row.keys())}
    for key in _PANEL_SUMMARY_KEYS:
        if key not in row:
            out[key] = None
            out[f"{key}_display"] = "—"
            continue
        raw = row.get(key)
        if key == "blockers":
            if isinstance(raw, (list, tuple)):
                items = [str(x) for x in raw]
                out[key] = items
                out[f"{key}_display"] = ", ".join(items) if items else "—"
            else:
                out[key] = None
                out[f"{key}_display"] = "—"
            continue
        if raw is None or raw == "":
            out[key] = None
            out[f"{key}_display"] = "—"
        else:
            out[key] = raw
            out[f"{key}_display"] = str(raw)
    return out


def build_double_play_observability_v1(snap: DoublePlaySnapshotV1) -> dict[str, Any]:
    """S06 breakdown from bound double_play snapshot only."""
    availability = snap.availability
    freshness = _freshness_dict(snap)
    provenance = _provenance_dict(snap)
    panels: list[dict[str, Any]] = []
    if availability in (Availability.AVAILABLE, Availability.STALE):
        for index, row in enumerate(snap.panel_summaries):
            if not isinstance(row, Mapping):
                panels.append(
                    {
                        "panel_index": index,
                        "invalid_row": True,
                        "name_display": "—",
                        "status_display": "—",
                        "summary_display": "—",
                        "blockers_display": "—",
                    }
                )
                continue
            displayed = _panel_row_display(row)
            displayed["panel_index"] = index
            panels.append(displayed)
    return {
        "source_family": "S06",
        "slot": "double_play",
        "schema_id": snap.schema_id,
        "availability": availability.value,
        "availability_label": _AVAILABILITY_LABELS[availability],
        "is_available": availability is Availability.AVAILABLE,
        "is_stale": availability is Availability.STALE,
        "overall_status_display": _scalar_display(snap.overall_status, availability)
        or _AVAILABILITY_LABELS[availability],
        "display_only": snap.display_only
        if availability in (Availability.AVAILABLE, Availability.STALE)
        else None,
        "live_authorization": snap.live_authorization
        if availability in (Availability.AVAILABLE, Availability.STALE)
        else None,
        "blockers": _codes_display(snap.blockers, availability),
        "blockers_display": _codes_display_label(snap.blockers, availability),
        "panels": panels,
        "panel_count": len(panels),
        "freshness": freshness,
        "freshness_display": format_freshness_display_v1(freshness),
        "is_stale_flag": freshness.get("is_stale") is True,
        "stale_reason": freshness.get("stale_reason"),
        "provenance": provenance,
        "source_kind": provenance.get("source_kind"),
        "source_reference": provenance.get("source_reference"),
        "producer_module": provenance.get("producer_module"),
        "provenance_generated_at": provenance.get("generated_at"),
        "provenance_effective_at": provenance.get("effective_at"),
        "evidence_digest": provenance.get("evidence_digest"),
    }


def build_s05_s06_relationship_observability_v1(
    *,
    decision: CanonicalDecisionSnapshotV1,
    double_play: DoublePlaySnapshotV1,
) -> dict[str, Any]:
    """Relationship block — separate unless an explicit join field exists on both snapshots."""
    # Landscape contracts expose no shared decision_id / correlation_id on DoublePlaySnapshotV1.
    _ = decision
    _ = double_play
    return {
        "join_contract_present": JOIN_CONTRACT_PRESENT,
        "join_status": "SEPARATE_NO_SHARED_IDENTIFIER",
        "join_field": None,
        "message": (
            "S05 canonical_decision and S06 double_play bind independently; "
            "no belegter correlation contract — not joined in presentation."
        ),
    }


def build_decision_double_play_observability_v1(
    *,
    decision: CanonicalDecisionSnapshotV1,
    double_play: DoublePlaySnapshotV1,
) -> dict[str, Any]:
    s05 = build_canonical_decision_observability_v1(decision)
    s06 = build_double_play_observability_v1(double_play)
    relationship = build_s05_s06_relationship_observability_v1(
        decision=decision,
        double_play=double_play,
    )
    return {
        "capability_id": CAPABILITY_ID,
        "consumer_role": "read_only_consumer",
        "authority": "NONE",
        "canonical_decision": s05,
        "double_play": s06,
        "relationship": relationship,
        "multi_decision_timeline_status": MULTI_DECISION_TIMELINE_STATUS,
    }
