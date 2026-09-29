"""Regression: stale navigation must not contradict OD account-equity / normative pack."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.ops.law_map_v1.surface_census_v1 import (
    _SUPPRESSED_UNKNOWN_RELATION_IDS,
    expansion_payload,
)
from scripts.ops.law_map_v1.ucs_evidence_binding_v1 import (
    NAV_UCS0018_ACCOUNT_EQUITY_SIZING_SOURCE_V1,
    NAV_UCS0031_COMMON_EPOCH_NORMATIVE_V1,
    NAV_UCS0040_ACCOUNT_EQUITY_SIZING_SOURCE_V1,
    NAV_UCS0045_COMMON_EPOCH_NORMATIVE_V1,
    build_workset_artifact,
)

REPO = Path(__file__).resolve().parents[2]
OD_29P_NORMATIVE = REPO / "config/governance/od_29p_normative_pack_v1.json"
SOURCE = REPO / "config/governance/current_law_impact_map_v1/source_v1.json"


def test_ucs0018_navigation_does_not_claim_unresolved_unk_pin() -> None:
    artifact = build_workset_artifact()
    row = next(r for r in artifact["dispositions"] if r["workset_id"] == "UCS-0018")
    reason = str(row["unresolved_reason"] or "")
    assert "unk_account_equity_sizing_source" in reason
    assert "HISTORICAL_DISCOVERY" in reason
    assert "CURRENT_ADJUDICATED" in reason
    assert "RESOLVED_NORMATIVE" in reason
    assert reason == NAV_UCS0018_ACCOUNT_EQUITY_SIZING_SOURCE_V1
    assert "remains CSIA PARTIAL" not in reason


def test_ucs0040_not_obsolete_unk_carrier() -> None:
    artifact = build_workset_artifact()
    row = next(r for r in artifact["dispositions"] if r["workset_id"] == "UCS-0040")
    reason = str(row["unresolved_reason"] or "")
    assert row["bound_lref"] == "OD-ACCOUNT-EQUITY-SIZING-SOURCE-ADJUDICATION-V1"
    assert reason == NAV_UCS0040_ACCOUNT_EQUITY_SIZING_SOURCE_V1
    assert "maps to unk_account_equity_sizing_source" not in reason
    assert "RESOLVED_NORMATIVE" in reason


def test_surface_census_suppresses_resolved_unk_account_equity_sizing_source() -> None:
    payload = expansion_payload()
    ids = {u["id"] for u in payload["unknown_relations"]}
    assert "unk_account_equity_sizing_source" not in ids
    assert "unk_account_equity_sizing_source" in _SUPPRESSED_UNKNOWN_RELATION_IDS


def test_no_new_conflicting_relations_in_source() -> None:
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert doc.get("conflicting_relations", []) == []


def test_remaining_29_does_not_close_frozen_unknown_domain_laws() -> None:
    from scripts.ops.law_map_v1.remaining_29_evidence_exhaustion_v1 import _build_rows

    rows = {r.workset_id: r for r in _build_rows()}
    assert rows["UCS-0034"].domain_law_adjudication == "UNKNOWN_CURRENT"
    assert rows["UCS-0032"].domain_law_adjudication == "PROVEN_CURRENT"
    od_numeric = json.loads(
        (
            REPO
            / "config/governance/od_29p_fresh_trusted_numeric_venue_bind_canonical_adjudication_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert od_numeric.get("real_productive_get_executed_in_wp") is False


def test_ucs0031_and_ucs0045_common_epoch_nav_rebound() -> None:
    artifact = build_workset_artifact()
    r31 = next(r for r in artifact["dispositions"] if r["workset_id"] == "UCS-0031")
    r45 = next(r for r in artifact["dispositions"] if r["workset_id"] == "UCS-0045")
    assert r31["unresolved_reason"] == NAV_UCS0031_COMMON_EPOCH_NORMATIVE_V1
    assert r45["unresolved_reason"] == NAV_UCS0045_COMMON_EPOCH_NORMATIVE_V1
    assert "HISTORICAL_DISCOVERY" in r31["unresolved_reason"]
    assert "CURRENT_ADJUDICATED" in r45["unresolved_reason"]
    assert "sealed venue pin OPEN at UCS freeze" in r45["unresolved_reason"]


def test_source_no_stale_common_epoch_open_navigation() -> None:
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    reasons = " ".join(r["reason"] for r in doc["unclassified_current_surfaces"])
    assert "normative epoch semantics OPEN" not in reasons
    assert "sealed venue pin OPEN" not in reasons
    assert OD_29P_NORMATIVE.is_file()
    assert not any(u["id"] == "unk_account_equity_sizing_source" for u in doc["unknown_relations"])
