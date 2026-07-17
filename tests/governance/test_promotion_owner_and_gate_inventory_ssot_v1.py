"""Static contract: pin canonical promotion gate owner SSOT v1.

Docs/config/tests-only. Does not authorize live, orders, runtime bridge,
deployment, or economic-gate semantic changes.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.governance.promotion_loop import promotion_economic_gate_v1 as gate
from src.research.cross_sectional_lead_lag_v0_promotion_economic_gate_precheck_v0 import (
    CANONICAL_PROMOTION_GATE_OWNER as LEAD_LAG_CANONICAL_OWNER,
)
from src.research.linear_evidence.offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0 import (
    CANONICAL_PROMOTION_GATE_OWNER as LINEAR_DIAG_CANONICAL_OWNER,
)
from src.trading.master_v2.promotion_gate_boundary_offline_replay_binding_adapter_v0 import (
    PROMOTION_GATE_CANONICAL_OWNER as BOUNDARY_CANONICAL_OWNER,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SSOT_DOC = REPO_ROOT / "docs" / "governance" / "PROMOTION_OWNER_AND_GATE_INVENTORY_SSOT_V1.md"
SSOT_JSON = REPO_ROOT / "config" / "governance" / "promotion_owner_and_gate_inventory_ssot_v1.json"
GATE_MODULE = REPO_ROOT / "src" / "governance" / "promotion_loop" / "promotion_economic_gate_v1.py"

EXPECTED_OWNER = "governance.promotion_loop.promotion_economic_gate_v1"
EXPECTED_VERSION = "promotion_economic_gate_v1"

REQUIRED_DOC_MARKERS: tuple[str, ...] = (
    "PROMOTION_OWNER_AND_GATE_INVENTORY_SSOT_V1=true",
    f"CANONICAL_PROMOTION_GATE_OWNER={EXPECTED_OWNER}",
    "CANONICAL_PROMOTION_GATE_MODULE=src/governance/promotion_loop/promotion_economic_gate_v1.py",
    "CANONICAL_PROMOTION_GATE_CALLABLE=evaluate_promotion_economic_gate_v1",
    "PRODUCTIVE_PROMOTION_DECISION_OWNER_COUNT=1",
    "DUPLICATE_PRODUCTIVE_PROMOTION_DECISION_OWNERS=false",
    "SECOND_PRODUCTIVE_PROMOTION_DECISION_OWNER_FORBIDDEN=true",
    "THIS_DOCUMENT_IS_INVENTORY_SSOT_NOT_RUNTIME_AUTHORITY=true",
    "NO_RUNTIME_REWIRE_IN_THIS_SLICE=true",
    "ECONOMIC_GATE_REMAINS_FAIL_CLOSED=true",
    "ELIGIBLE_FOR_LIVE_DEFAULT=false",
    "LIVE_AUTHORIZED=false",
    "ORDERS_ENABLED=false",
    "AUTHORITY_EFFECT=NONE",
    "CANONICAL_DECISION_OWNER",
)

FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "eligible_for_live=true",
    "LIVE_AUTHORIZED=true",
    "ORDERS_ENABLED=true",
    "runtime bridge activated",
    "approved for live trading",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def test_ssot_doc_exists_with_required_markers() -> None:
    text = _read(SSOT_DOC)
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, f"missing SSOT marker: {marker}"
    lowered = text.lower()
    for claim in FORBIDDEN_CLAIMS:
        assert claim.lower() not in lowered, f"forbidden claim leaked: {claim}"


def test_ssot_json_pins_canonical_owner_and_count() -> None:
    payload = json.loads(_read(SSOT_JSON))
    markers = payload["markers"]
    owner = payload["canonical_decision_owner"]
    assert markers["CANONICAL_PROMOTION_GATE_OWNER"] == EXPECTED_OWNER
    assert markers["PRODUCTIVE_PROMOTION_DECISION_OWNER_COUNT"] == 1
    assert markers["DUPLICATE_PRODUCTIVE_PROMOTION_DECISION_OWNERS"] is False
    assert markers["SECOND_PRODUCTIVE_PROMOTION_DECISION_OWNER_FORBIDDEN"] is True
    assert markers["ECONOMIC_GATE_REMAINS_FAIL_CLOSED"] is True
    assert markers["ELIGIBLE_FOR_LIVE_DEFAULT"] is False
    assert owner["owner_id"] == EXPECTED_OWNER
    assert owner["module_path"] == "src/governance/promotion_loop/promotion_economic_gate_v1.py"
    assert owner["primary_callable"] == "evaluate_promotion_economic_gate_v1"
    assert payload["risk_sizing_claimed_consolidated"] is False
    assert payload["risk_sizing_inventory_status"] == "DONE"
    assert payload["next_plan_item"] == "P2_LEGACY_ORDER_INTENT"


def test_gate_module_is_sole_owner_string_definition() -> None:
    assert gate.PROMOTION_ECONOMIC_GATE_POLICY_OWNER == EXPECTED_OWNER
    assert gate.PROMOTION_ECONOMIC_GATE_POLICY_VERSION == EXPECTED_VERSION
    assert GATE_MODULE.is_file()

    redefine = re.compile(
        r"^\s*PROMOTION_ECONOMIC_GATE_POLICY_OWNER\s*=",
        re.MULTILINE,
    )
    offenders: list[str] = []
    for path in (REPO_ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if not redefine.search(text):
            continue
        if path.resolve() == GATE_MODULE.resolve():
            continue
        offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == [], f"second owner definition(s): {offenders}"


def test_productive_consumer_aliases_point_at_canonical_owner() -> None:
    assert LEAD_LAG_CANONICAL_OWNER == EXPECTED_OWNER
    assert LINEAR_DIAG_CANONICAL_OWNER == EXPECTED_OWNER
    assert BOUNDARY_CANONICAL_OWNER == EXPECTED_OWNER
    assert LEAD_LAG_CANONICAL_OWNER == gate.PROMOTION_ECONOMIC_GATE_POLICY_OWNER


def test_inventory_paths_exist_and_classified() -> None:
    payload = json.loads(_read(SSOT_JSON))
    for key in (
        "adapters_consumers",
        "reporting_observability",
        "legacy_or_domain_scoped_not_canonical_gate",
    ):
        paths = payload[key]
        assert paths, f"empty classification list: {key}"
        for rel in paths:
            assert (REPO_ROOT / rel).is_file(), f"missing inventoried path: {rel}"


def test_current_repo_gate_remains_fail_closed() -> None:
    result = gate.evaluate_current_repo_promotion_gate_v1()
    payload = result.to_dict()
    assert payload["promotion_eligible"] is False
    assert payload["deployment_eligible"] is False
    assert payload["runtime_eligible"] is False
    assert payload["promotion_candidate_status"] == "BLOCKED"
    assert payload.get("economic_validity_pass") is False


def test_governance_readme_points_to_promotion_owner_ssot() -> None:
    readme = _read(REPO_ROOT / "docs" / "governance" / "README.md")
    assert "PROMOTION_OWNER_AND_GATE_INVENTORY_SSOT_V1.md" in readme
