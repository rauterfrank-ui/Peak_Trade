"""Static contract: AWS audit authority SSOT v1 + read-only audit doc markers.

Docs/config/tests-only. Does not call AWS, authorize live/orders, or mutate infra.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SSOT_JSON = REPO_ROOT / "config" / "governance" / "aws_audit_authority_ssot_v1.json"
AUDIT_DOC = REPO_ROOT / "docs" / "audits" / "AWS_INFRASTRUCTURE_READ_ONLY_AUDIT_2026-07-17.md"

EXPECTED_ACCOUNT = "511913187493"
EXPECTED_PROFILE = "peak-trade-prearm-v3-audit"
EXPECTED_ROLE = "peak-trade-operator-readonly-audit-role"
EXPECTED_REGION = "eu-central-1"
EXPECTED_BASE_SHA = "55388134cb424227449157b051b30a1812454564"

REQUIRED_DOC_MARKERS: tuple[str, ...] = (
    "AWS_INFRASTRUCTURE_READ_ONLY_AUDIT_2026-07-17=true",
    f"BASE_SHA={EXPECTED_BASE_SHA}",
    f"AWS_PROFILE={EXPECTED_PROFILE}",
    f"AWS_ACCOUNT_ID={EXPECTED_ACCOUNT}",
    f"AWS_REGION={EXPECTED_REGION}",
    "PROFILE_SELECTION_AUTHORITY=EXPLICIT_OPERATOR_DECISION",
    "PERMISSION_MODE=read_only",
    "SECRET_VALUES_READ=false",
    "AWS_MUTATIONS_PERFORMED=false",
    "AUDIT_CLAIMS_FULL_ACCOUNT_INVENTORY=false",
    "LIVE_AUTHORIZED=false",
    "ORDERS_ENABLED=false",
    "RUNTIME_BRIDGE_ACTIVATED=false",
)

FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "SECRET_VALUES_READ=true",
    "AWS_MUTATIONS_PERFORMED=true",
    "LIVE_AUTHORIZED=true",
    "ORDERS_ENABLED=true",
    "RUNTIME_BRIDGE_ACTIVATED=true",
    "full account inventory complete",
    "GetSecretValue",
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


def test_ssot_pins_operator_authority_and_safety() -> None:
    payload = _load()
    assert payload["schema_version"] == "aws_audit_authority_schema_v1"
    assert payload["account_id"] == EXPECTED_ACCOUNT
    assert payload["canonical_profile"] == EXPECTED_PROFILE
    assert payload["principal_role"] == EXPECTED_ROLE
    assert payload["region"] == EXPECTED_REGION
    assert payload["authority"] == "explicit_operator_decision"
    assert payload["permission_mode"] == "read_only"
    assert payload["fallback_profile"] == "peak-trade-operator-readonly-audit-user"
    assert payload["secret_value_access_allowed"] is False
    assert payload["mutation_allowed"] is False
    assert payload["generated_from_main_sha"] == EXPECTED_BASE_SHA
    assert payload["markers"]["AUDIT_CLAIMS_FULL_ACCOUNT_INVENTORY"] is False
    safety = payload["safety_status"]
    assert safety["secret_values_read"] is False
    assert safety["aws_mutations_performed"] is False
    assert safety["live_authorized"] is False
    assert safety["orders_enabled"] is False
    assert safety["runtime_bridge_activated"] is False
    # no raw session ARNs
    blob = json.dumps(payload)
    assert "botocore-session-" not in blob
    assert "<SESSION_REDACTED>" in payload["principal_arn_pattern"]


def test_classification_counts_agree_with_expected_resources() -> None:
    payload = _load()
    summary = payload["classification_summary"]
    expected = payload["expected_resources"]
    assert summary["repo_expected_resource_count"] == len(expected) == 6
    assert summary["live_matching_resource_count"] == sum(
        1 for e in expected if e["classification"] == "MATCH"
    )
    assert summary["live_drift_resource_count"] == sum(
        1 for e in expected if e["classification"] == "DRIFT"
    )
    assert summary["not_verifiable_count"] == sum(
        1 for e in expected if e["classification"] == "NOT_VERIFIABLE"
    )
    assert summary["access_denied_count"] == 16
    assert summary["active_trading_schedule_detected"] == "UNRESOLVED"
    assert summary["active_order_execution_detected"] == "UNRESOLVED"
    assert summary["public_s3_exposure_detected"] == "UNRESOLVED"
    assert summary["iam_oidc_trust_drift_detected"] == "UNRESOLVED"
    classes = {e["classification"] for e in expected}
    assert classes == {"MATCH", "DRIFT", "ACCESS_DENIED", "NOT_VERIFIABLE"}


def test_access_denied_surfaces_listed_and_nonempty() -> None:
    payload = _load()
    denied = payload["access_denied_surfaces"]
    assert len(denied) == 16
    assert "lambda.list-functions" in denied
    assert "events.list-rules" in denied
    assert "secretsmanager.list-secrets" in denied
    readable = payload["readable_surfaces"]
    assert "sts.get-caller-identity" in readable
    assert "iam.get-role" in readable


def test_governance_readme_points_to_aws_audit() -> None:
    readme = _read(REPO_ROOT / "docs" / "governance" / "README.md")
    assert "AWS_INFRASTRUCTURE_READ_ONLY_AUDIT_2026-07-17.md" in readme
