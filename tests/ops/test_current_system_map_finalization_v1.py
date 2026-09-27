"""CURRENT system interaction map finalization proof (representation only; AUTHORITY=NONE)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "config/governance/current_system_interaction_authority_map_v1/source_v1.json"
REPRESENTATION_CLOSURE_BASELINE_SHA = "528246fc0463bbc99494439ea1b0b265cb64802a"


def _load_source() -> dict:
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def _domains_by_id(doc: dict) -> dict[str, dict]:
    return {d["id"]: d for d in doc["domains"]}


def test_map_baseline_sha_matches_origin_main() -> None:
    doc = _load_source()
    origin_main = (
        subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=REPO, text=True)
        .strip()
        .lower()
    )
    head = (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip().lower()
    )
    assert doc["baseline_sha"] == REPRESENTATION_CLOSURE_BASELINE_SHA
    if head == origin_main:
        assert doc["baseline_sha"] == origin_main
    assert doc["baseline_sha"] != "9ab34786b13c26f1be5cb9b523975f265014e1cb"


def test_confirmed_first_class_universe_count_20() -> None:
    doc = _load_source()
    first_class = [d for d in doc["domains"] if d["tier"] == "FIRST_CLASS"]
    assert len(first_class) == 20


def test_subdomain_and_gate_representation() -> None:
    domains = _domains_by_id(_load_source())
    for domain_id in ("dynamic_scope", "bull_bear_sidestate"):
        d = domains[domain_id]
        assert d["tier"] == "INTERMEDIATE"
        assert "REPRESENTATION=SUBDOMAIN" in d["role"]
        assert "parent_domain=mv2_double_play" in d["role"]
    for domain_id in ("governance_promotion", "venue_plan_td_mode"):
        d = domains[domain_id]
        assert d["tier"] == "INTERMEDIATE"
        assert "REPRESENTATION=GATE" in d["role"]


def test_survival_owner_reference_and_treasury_subdomain() -> None:
    domains = _domains_by_id(_load_source())
    ssc = domains["survival_suitability_composition"]
    assert ssc["canonical_owner_ref"] == (
        "trading.master_v2.post_confirmation_survival_suitability_composition_binding_v1"
    )
    assert ssc["status"] == "PARTIAL"
    treasury = domains["treasury_29p"]
    assert treasury["status"] == "PARTIAL"
    assert "TREASURY_LIFECYCLE_SUBDOMAIN" in treasury["role"]
    assert treasury["canonical_owner_ref"] == "TREASURY_PHASE_BINDINGS_NAVIGATION_ONLY"


def test_gap_true_03_map_impact_representation_partial() -> None:
    doc = _load_source()
    rec = {r["id"]: r for r in doc["open_epistemic_records"]}["docs_ops_specs_map_impact"]
    assert rec["epistemic_class"] == "PARTIAL"
    assert "GAP-TRUE-03" in rec["statement"]


def test_open_epistemic_records_have_closure_adjudication() -> None:
    doc = _load_source()
    allowed = {
        "PROVEN_CURRENT",
        "CURRENT_SUPPORT",
        "EXPLICITLY_NOT_CURRENT",
        "OPEN_EVIDENCE",
        "CONFLICTING",
        "REPRESENTATION_ONLY",
        "SUPERSEDED_NONCURRENT",
    }
    for record in doc["open_epistemic_records"]:
        assert record.get("closure_adjudication_class") in allowed
        assert record.get("closure_note")


def test_b05_first_class_producer_domains_present() -> None:
    domains = _domains_by_id(_load_source())
    for domain_id in (
        "governed_productive_account_equity_authority_v1",
        "governed_productive_reference_price_authority_v1",
        "governed_productive_instrument_metadata_authority_v1",
    ):
        assert domains[domain_id]["tier"] == "FIRST_CLASS"
        assert domains[domain_id]["status"] == "PROVEN_CURRENT"


def test_b05_epistemic_records_reflect_merged_closure() -> None:
    doc = _load_source()
    records = {r["id"]: r for r in doc["open_epistemic_records"]}
    assert (
        "ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED=true"
        in records["account_equity_blocks"]["statement"]
    )
    assert (
        "REFERENCE_PRICE_AUTHORITY_CHAIN_CLOSED=true"
        in records["reference_price_authority_owner"]["statement"]
    )
    assert records["runbook_freshness_stamp"]["epistemic_class"] == "PARTIAL"
    assert "528246fc" in records["runbook_freshness_stamp"]["statement"]
    assert records["runbook_freshness_stamp"].get("closure_adjudication_class") == (
        "REPRESENTATION_ONLY"
    )
