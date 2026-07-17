"""Static contract: monitoring topology audit SSOT v1 (Grafana not expected).

Docs/config/tests-only. Does not probe Grafana, send alerts, or mutate infra.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SSOT_JSON = REPO_ROOT / "config" / "governance" / "monitoring_topology_audit_ssot_v1.json"
AUDIT_DOC = REPO_ROOT / "docs" / "audits" / "MONITORING_TOPOLOGY_READ_ONLY_AUDIT_2026-07-17.md"

EXPECTED_BASE_SHA = "f5114401f6a76171840040f0c44d0de05df61bf5"

REQUIRED_DOC_MARKERS: tuple[str, ...] = (
    "MONITORING_TOPOLOGY_READ_ONLY_AUDIT_2026-07-17=true",
    f"BASE_SHA={EXPECTED_BASE_SHA}",
    "PERMISSION_MODE=read_only",
    "SECRET_VALUES_READ=false",
    "MONITORING_MUTATIONS_PERFORMED=false",
    "NOTIFICATIONS_SENT=false",
    "GRAFANA_EXPECTED=false",
    "GRAFANA_AUDITED=false",
    "LIVE_AUTHORIZED=false",
    "ORDERS_ENABLED=false",
    "RUNTIME_BRIDGE_ACTIVATED=false",
)

FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "GRAFANA_EXPECTED=true",
    "GRAFANA_AUDITED=true",
    "SECRET_VALUES_READ=true",
    "MONITORING_MUTATIONS_PERFORMED=true",
    "NOTIFICATIONS_SENT=true",
    "LIVE_AUTHORIZED=true",
    "ORDERS_ENABLED=true",
    "RUNTIME_BRIDGE_ACTIVATED=true",
)

ACTIVE_CLASSIFICATIONS: frozenset[str] = frozenset(
    {
        "VERIFIED_LIVE_MATCH",
        "VERIFIED_REPO_ONLY",
        "DRIFT",
        "ACCESS_DENIED",
        "NOT_VERIFIABLE",
    }
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing: {path}"
    return path.read_text(encoding="utf-8")


def _load() -> dict:
    return json.loads(_read(SSOT_JSON))


def test_audit_doc_markers_forbid_grafana_expected() -> None:
    text = _read(AUDIT_DOC)
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, f"missing marker: {marker}"
    lowered = text.lower()
    for claim in FORBIDDEN_CLAIMS:
        assert claim.lower() not in lowered, f"forbidden claim: {claim}"
    # Grafana must not appear as an expected active component
    assert "Grafana | **Yes**" not in text
    assert 'grafana_expected": true' not in _read(SSOT_JSON).lower()


def test_ssot_topology_excludes_grafana_alertmanager_cloudwatch() -> None:
    payload = _load()
    topo = payload["canonical_topology"]
    assert topo["grafana_expected"] is False
    assert topo["alertmanager_expected"] is False
    assert topo["cloudwatch_expected"] is False
    assert topo["prometheus_expected"] is True
    assert topo["alert_routing_expected"] is True
    assert payload["markers"]["GRAFANA_EXPECTED"] is False
    assert payload["markers"]["GRAFANA_AUDITED"] is False
    assert payload["surface_status"]["grafana"] == "REMOVED_AS_DESIGNED"
    assert payload["surface_status"]["alertmanager"] == "REMOVED_AS_DESIGNED"
    assert payload["surface_status"]["cloudwatch"] == "REMOVED_AS_DESIGNED"
    assert payload["surface_status"]["prometheus"] == "VERIFIED_REPO_ONLY"
    assert payload["surface_status"]["alert_routing"] == "VERIFIED_REPO_ONLY"


def test_active_components_only_allowed_classifications() -> None:
    payload = _load()
    expected = payload["expected_active_components"]
    summary = payload["classification_summary"]
    assert summary["expected_active_component_count"] == len(expected) == 2
    assert summary["repo_only_component_count"] == 2
    assert summary["live_matching_component_count"] == 0
    assert summary["drift_component_count"] == 0
    assert summary["access_denied_count"] == 0
    assert summary["not_verifiable_count"] == 0
    for e in expected:
        assert e["classification"] in ACTIVE_CLASSIFICATIONS
        assert e["id"] != "grafana"
    ids = {e["id"] for e in expected}
    assert ids == {"prometheus_metrics_surface", "in_app_alert_routing"}


def test_stale_reference_counts_pinned() -> None:
    payload = _load()
    stale = payload["stale_references"]
    assert stale["grafana_class"] == "STALE_REFERENCE_FOUND"
    assert stale["market_dashboard_class"] == "STALE_REFERENCE_FOUND"
    assert stale["grafana_match_count"] == 432
    assert stale["market_dashboard_match_count"] == 334


def test_safety_and_secret_names_only() -> None:
    payload = _load()
    safety = payload["safety_status"]
    assert safety["secret_values_read"] is False
    assert safety["notifications_sent"] is False
    assert safety["grafana_audited"] is False
    assert safety["okx_audit_reopened"] is False
    blob = json.dumps(payload)
    assert "hooks.slack.com/services/" not in blob
    assert "BEGIN " not in blob
    assert "PAGERDUTY_ROUTING_KEY" in payload["secret_env_var_names"]


def test_governance_readme_points_to_topology_audit() -> None:
    readme = _read(REPO_ROOT / "docs" / "governance" / "README.md")
    assert "MONITORING_TOPOLOGY_READ_ONLY_AUDIT_2026-07-17.md" in readme
