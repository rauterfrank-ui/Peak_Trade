"""Static contract: OKX audit authority SSOT v1 + read-only audit doc markers.

Docs/config/tests-only. Does not call OKX, authorize live/orders, or mutate venues.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SSOT_JSON = REPO_ROOT / "config" / "governance" / "okx_audit_authority_ssot_v1.json"
AUDIT_DOC = REPO_ROOT / "docs" / "audits" / "OKX_INTEGRATION_READ_ONLY_AUDIT_2026-07-17.md"

EXPECTED_BASE_SHA = "0f36c93f76a08ae306a49b294ef300aa3e8dcc5c"

REQUIRED_DOC_MARKERS: tuple[str, ...] = (
    "OKX_INTEGRATION_READ_ONLY_AUDIT_2026-07-17=true",
    f"BASE_SHA={EXPECTED_BASE_SHA}",
    "PERMISSION_MODE=read_only",
    "SECRET_VALUES_READ=false",
    "CREDENTIAL_VALUES_READ=false",
    "OKX_MUTATIONS_PERFORMED=false",
    "LIVE_AUTHORIZED=false",
    "ORDERS_ENABLED=false",
    "RUNTIME_BRIDGE_ACTIVATED=false",
)

FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "SECRET_VALUES_READ=true",
    "CREDENTIAL_VALUES_READ=true",
    "OKX_MUTATIONS_PERFORMED=true",
    "LIVE_AUTHORIZED=true",
    "ORDERS_ENABLED=true",
    "RUNTIME_BRIDGE_ACTIVATED=true",
)

REQUIRED_CREDENTIAL_NAMES: tuple[str, ...] = (
    "OKX_EEA_PUBLIC_API_KEY",
    "OKX_EEA_READONLY_API_KEY",
    "OKX_EEA_READONLY_API_SECRET",
    "OKX_EEA_READONLY_API_PASSPHRASE",
    "OKX_EEA_TRADE_API_KEY",
    "OKX_EEA_TRADE_API_SECRET",
    "OKX_EEA_TRADE_API_PASSPHRASE",
    "OKX_API_KEY",
    "OKX_API_SECRET",
)

FORBIDDEN_MUTATIONS: tuple[str, ...] = (
    "order_place",
    "order_amend",
    "order_cancel",
    "transfer",
    "leverage_set",
    "position_mode_change",
    "runtime_bridge_activation",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing: {path}"
    return path.read_text(encoding="utf-8")


def _load() -> dict:
    return json.loads(_read(SSOT_JSON))


def test_audit_doc_markers_and_forbidden_claims() -> None:
    text = _read(AUDIT_DOC)
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, f"missing marker: {marker}"
    lowered = text.lower()
    for claim in FORBIDDEN_CLAIMS:
        assert claim.lower() not in lowered, f"forbidden claim: {claim}"


def test_ssot_pins_authority_safety_and_base_sha() -> None:
    payload = _load()
    assert payload["schema_version"] == "okx_audit_authority_schema_v1"
    assert payload["authority"] == "explicit_operator_decision"
    assert payload["permission_mode"] == "read_only"
    assert payload["generated_from_main_sha"] == EXPECTED_BASE_SHA
    assert payload["markers"]["LIVE_AUTHORIZED"] is False
    assert payload["markers"]["ORDERS_ENABLED"] is False
    assert payload["markers"]["RUNTIME_BRIDGE_ACTIVATED"] is False
    assert payload["markers"]["CREDENTIAL_VALUE_ACCESS_ALLOWED"] is False
    assert payload["markers"]["MUTATION_ALLOWED"] is False
    safety = payload["safety_status"]
    assert safety["credential_values_read"] is False
    assert safety["okx_mutations_performed"] is False
    assert safety["live_authorized"] is False
    assert safety["orders_enabled"] is False
    assert safety["runtime_bridge_activated"] is False


def test_credential_names_presence_only_no_secret_values() -> None:
    payload = _load()
    names = payload["credential_env_var_names"]
    presence = payload["credential_presence"]
    assert list(names) == list(REQUIRED_CREDENTIAL_NAMES)
    assert set(presence) == set(REQUIRED_CREDENTIAL_NAMES)
    for name, status in presence.items():
        assert status in {"PRESENT", "ABSENT", "NOT_VERIFIABLE"}, name
    blob = json.dumps(payload)
    # No secret-looking long opaque values persisted in SSOT
    assert "OK-ACCESS-" not in blob
    assert "BEGIN " not in blob
    for status in presence.values():
        assert status in {"PRESENT", "ABSENT", "NOT_VERIFIABLE"}


def test_allowed_probes_and_forbidden_mutations() -> None:
    payload = _load()
    probes = payload["allowed_read_only_probes"]
    assert any("public/time" in p for p in probes)
    assert any("public/instruments" in p for p in probes)
    assert any("public_ws" in p for p in probes)
    forbidden = set(payload["forbidden_mutations"])
    for item in FORBIDDEN_MUTATIONS:
        assert item in forbidden
    # private mutating trade paths must not appear as allowed probes
    joined = " ".join(probes).lower()
    assert "/api/v5/trade/order" not in joined
    assert "order_place" not in joined


def test_probe_results_and_classification_counts() -> None:
    payload = _load()
    probes = payload["probe_results"]
    assert probes["rest_public_reachable"] is True
    assert probes["rest_private_authenticated"] is False
    assert probes["websocket_public_reachable"] is True
    assert probes["websocket_private_authenticated"] is False
    assert probes["fail_closed_verified"] is True
    assert probes["futures_only_match"] is True
    assert probes["btc_exclusion_match"] is True
    assert probes["spot_exposure_detected"] is False
    assert probes["open_orders_detected"] == "NOT_VERIFIABLE"
    assert probes["open_algo_orders_detected"] == "NOT_VERIFIABLE"
    assert probes["open_positions_detected"] == "NOT_VERIFIABLE"

    summary = payload["classification_summary"]
    expected = payload["expected_components"]
    assert summary["repo_expected_component_count"] == len(expected) == 14
    assert summary["live_matching_component_count"] == sum(
        1 for e in expected if e["classification"] == "MATCH"
    )
    assert summary["live_drift_component_count"] == sum(
        1 for e in expected if e["classification"] == "DRIFT"
    )
    assert summary["missing_component_count"] == sum(
        1 for e in expected if e["classification"] == "MISSING"
    )
    assert summary["not_verifiable_count"] == sum(
        1 for e in expected if e["classification"] == "NOT_VERIFIABLE"
    )
    assert summary["access_denied_count"] == 0
    classes = {e["classification"] for e in expected}
    assert classes == {"MATCH", "DRIFT", "NOT_VERIFIABLE"}


def test_canonical_owners_listed() -> None:
    payload = _load()
    owners = {o["id"]: o["path"] for o in payload["canonical_owners"]}
    assert "venue_binding" in owners
    assert "adapter_lifecycle_reconciliation" in owners
    assert "public_market_data_ingest" in owners
    assert owners["config_exchange_profile"].endswith("config.toml")


def test_governance_readme_points_to_okx_audit() -> None:
    readme = _read(REPO_ROOT / "docs" / "governance" / "README.md")
    assert "OKX_INTEGRATION_READ_ONLY_AUDIT_2026-07-17.md" in readme
