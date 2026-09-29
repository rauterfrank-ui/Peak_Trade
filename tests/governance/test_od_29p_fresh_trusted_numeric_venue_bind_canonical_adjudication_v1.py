"""OD 29P fresh-trusted numeric venue bind adjudication contracts."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.od_29p_fresh_trusted_numeric_venue_bind_canonical_adjudication_v1 import (
    ADJUDICATION_CONFIG,
    DL_NUMERIC_KEYS,
    build_adjudication_report_v1,
    load_adjudication_v1,
    validate_adjudication_against_repo_v1,
)
from src.governance.od_account_equity_sizing_source_canonical_adjudication_v1 import (
    ADJUDICATION_CONFIG as SIZING_ADJ,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    NUMERIC_EQUITY_TTL_SECONDS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    OBSERVATION_SURFACE,
)

REPO = Path(__file__).resolve().parents[2]


def test_numeric_bind_adjudication_loads_and_validates() -> None:
    adj = load_adjudication_v1(REPO)
    ok, reasons = validate_adjudication_against_repo_v1(repo_root=REPO, adjudication=adj)
    assert ok, reasons
    report = build_adjudication_report_v1(repo_root=REPO)
    assert report["VALIDATION_OK"] is True
    assert report["DECISION_CASE"] == "D"
    assert report["NUMERIC_VENUE_BIND_RESOLVED"] is True


def test_aligns_with_6960_sizing_source_without_reopening() -> None:
    numeric = json.loads((REPO / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))
    sizing = json.loads((REPO / SIZING_ADJ).read_text(encoding="utf-8"))
    assert numeric["raw_field"] == sizing["available_for_sizing"]["observation_surface"]
    assert numeric["transform_id"] == sizing["available_for_sizing"]["transformation_id"]
    assert numeric["output_semantic_id"] == "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"
    assert sizing["decision_case"] == "A"
    assert numeric["unk_sealed_venue_number_29p_status"] != "UNKNOWN_CURRENT"
    assert numeric["successor_owner_ratification"] == "OD-29P-NORMATIVE-PACK-V1"


def test_observation_surface_matches_risk_capital_model() -> None:
    payload = json.loads((REPO / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))
    assert payload["raw_field"] == OBSERVATION_SURFACE
    assert payload["freshness_clock"] is not None
    assert NUMERIC_EQUITY_TTL_SECONDS > 0


def test_all_dl_numeric_proven() -> None:
    laws = json.loads((REPO / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))["domain_laws"]
    assert set(laws) == set(DL_NUMERIC_KEYS)
    assert all(v == "PROVEN_CURRENT" for v in laws.values())
