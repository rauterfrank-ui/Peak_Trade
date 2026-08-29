"""Historically attested current-system semantic restoration authorization v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.governance.economic_diagnostic_optimization_boundary_v0 import (
    REASON_RESTORATION_ATTESTATION_BINDING_INVALID,
    REASON_RESTORATION_AUTHORIZED,
    REASON_RESTORATION_BROAD_SCOPE_FORBIDDEN,
    REASON_RESTORATION_INVALID,
    REASON_RESTORATION_PATH_UNAUTHORIZED,
    REASON_RESTORATION_REFERENCE_BINDING_INVALID,
    REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID,
    REASON_RESTORATION_TARGET_BINDING_INVALID,
    RESTORATION_AUTH_VERSION,
    RESTORATION_AUTHORIZATION_ID,
    RESTORATION_CLASS_ATTESTATION_RELATIVE,
    RESTORATION_HISTORICAL_REFERENCE_SHA256,
    RESTORATION_MUTATION_PURPOSE,
    RESTORATION_SCOPE_CLASS,
    RESTORATION_TARGET_ID,
    TECHNICAL_WIRING_AUTH_VERSION,
    TECHNICAL_WIRING_MUTATION_PURPOSE,
    TECHNICAL_WIRING_SCOPE_CLASS,
    build_boundary_report,
    forbidden_surface_changed_count,
    load_contract,
    load_restoration_authorization,
    load_technical_wiring_authorization,
    validate_restoration_authorization,
    validate_technical_wiring_authorization,
)
from tests.governance.test_technical_canonical_wiring_authorization_bound_to_boundary_guard_v1 import (
    AUTHORIZED_TECHNICAL_WIRING_FIXTURE,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
AUTH_PATH = (
    REPO_ROOT
    / "config/governance/historically_attested_current_system_semantic_restoration_authorization_v1.json"
)

CANDIDATE_RESTORE_PATHS_WITHOUT_GRANT = [
    "src/governance/capital_risk_sizing_v1.py",
    "src/trading/master_v2/capital_risk_sizing_intent_restore_v1.py",
    "tests/trading/master_v2/test_master_v2_a06_capital_risk_sizing_intent_restore_contract_v1.py",
]

FIXTURE_GRANTED_PATH = "src/trading/master_v2/survival_assessment_v1.py"


def _load_restoration() -> dict:
    payload = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _grant_fixture(allowed_paths: list[str]) -> dict:
    auth = copy.deepcopy(_load_restoration())
    auth["grant_active"] = True
    auth["allowed_paths"] = list(allowed_paths)
    auth["allowed_surface_classes"] = ["MASTER_V2"]
    auth["slice_grant_id"] = "GOVERNANCE_FIXTURE_EXACT_FILE_GRANT_V1"
    auth["RESTORATION_TARGET_CONFORMANCE"] = True
    return auth


class TestRestorationAdmissionClassContractV1:
    def test_committed_artifact_is_valid_empty_grant(self) -> None:
        auth = load_restoration_authorization(REPO_ROOT)
        assert auth is not None
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is True
        assert reasons == ()
        assert auth["contract_version"] == RESTORATION_AUTH_VERSION
        assert auth["authorized_scope_class"] == RESTORATION_SCOPE_CLASS
        assert auth["authorization_token"] == RESTORATION_AUTHORIZATION_ID
        assert auth["mutation_purpose_class"] == RESTORATION_MUTATION_PURPOSE
        assert auth["restoration_target_id"] == RESTORATION_TARGET_ID
        assert auth["grant_active"] is False
        assert auth["allowed_paths"] == []
        assert auth["CURRENT_SYSTEM_SEMANTIC_DELTA"] is True
        assert auth["binds_to_restoration_target"] is True
        assert auth["binds_to_current_a06_code"] is False
        assert auth["historical_reference_sha256"] == RESTORATION_HISTORICAL_REFERENCE_SHA256
        assert auth["historical_reference_authority"] == "NONE"
        assert auth["restoration_attestation_id"] == RESTORATION_CLASS_ATTESTATION_RELATIVE
        assert "RISK_SIZING_SEMANTICS_CHANGED" not in auth.get("restoration_invariants", {})
        assert "RISK_SIZING_SEMANTICS_CHANGED" not in auth

    def test_bound_from_boundary_contract(self) -> None:
        contract = load_contract(REPO_ROOT)
        assert (
            contract["historically_attested_current_system_semantic_restoration_authorization"]
            == "config/governance/historically_attested_current_system_semantic_restoration_authorization_v1.json"
        )
        assert (
            contract["technical_canonical_wiring_authorization"]
            == "config/governance/technical_canonical_wiring_authorization_v1.json"
        )

    def test_committed_artifact_does_not_grant_candidate_restore_paths(self) -> None:
        auth = _load_restoration()
        allowed = set(auth["allowed_paths"])
        for path in CANDIDATE_RESTORE_PATHS_WITHOUT_GRANT:
            assert path not in allowed
        serialized = json.dumps(auth)
        assert "capital_risk_sizing_intent_restore_v1.py" not in serialized
        assert "A06RestoreError" not in serialized

    def test_token_alone_is_insufficient(self) -> None:
        token_only = {
            "authorization_token": RESTORATION_AUTHORIZATION_ID,
            "contract_version": RESTORATION_AUTH_VERSION,
        }
        valid, reasons = validate_restoration_authorization(token_only, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_RESTORATION_INVALID in reasons


class TestTechnicalWiringRegressionUnchangedV1:
    def test_wiring_contract_remains_valid_and_semantics_neutral(self) -> None:
        auth = load_technical_wiring_authorization(REPO_ROOT)
        assert auth is not None
        valid, reasons = validate_technical_wiring_authorization(auth)
        assert valid is True
        assert reasons == ()
        assert auth["authorized_scope_class"] == TECHNICAL_WIRING_SCOPE_CLASS
        assert auth["mutation_purpose_class"] == TECHNICAL_WIRING_MUTATION_PURPOSE
        assert auth["contract_version"] == TECHNICAL_WIRING_AUTH_VERSION
        assert auth["required_semantic_invariants"]["RISK_SIZING_SEMANTICS_CHANGED"] is False

    def test_authorized_technical_wiring_fixture_still_passes(self) -> None:
        report = build_boundary_report(
            AUTHORIZED_TECHNICAL_WIRING_FIXTURE,
            repo_root=REPO_ROOT,
        )
        assert report.admissible is True
        assert report.technical_wiring_authorization_applied is True
        assert report.restoration_authorization_applied is False
        assert "TECHNICAL_CANONICAL_WIRING_AUTHORIZED" in report.reason_codes
        assert REASON_RESTORATION_AUTHORIZED not in report.reason_codes
        assert forbidden_surface_changed_count(report) == 0
        assert report.canonical_trading_semantics_changed is False
        assert report.risk_sizing_changed is False

    def test_unauthorized_master_v2_still_fails(self) -> None:
        report = build_boundary_report(
            [FIXTURE_GRANTED_PATH],
            repo_root=REPO_ROOT,
        )
        assert report.admissible is False
        assert report.fail_closed is True
        assert report.restoration_authorization_applied is False
        assert "FORBIDDEN_MUTATION_SURFACE_MATCH" in report.reason_codes
        assert REASON_RESTORATION_PATH_UNAUTHORIZED in report.reason_codes


class TestRestorationAdmissionNegativeV1:
    def test_candidate_restore_paths_without_grant_fail(self) -> None:
        report = build_boundary_report(
            CANDIDATE_RESTORE_PATHS_WITHOUT_GRANT,
            repo_root=REPO_ROOT,
        )
        assert report.admissible is False
        assert report.fail_closed is True
        assert report.restoration_authorization_applied is False
        assert report.technical_wiring_authorization_applied is False
        assert "FORBIDDEN_MUTATION_SURFACE_MATCH" in report.reason_codes
        assert REASON_RESTORATION_PATH_UNAUTHORIZED in report.reason_codes
        assert forbidden_surface_changed_count(report) >= 1

    def test_wrong_contract_version_fails(self) -> None:
        auth = _load_restoration()
        auth["contract_version"] = "wrong_version"
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_RESTORATION_INVALID in reasons
        assert "RESTORATION_AUTH_VERSION_MISMATCH" in reasons

    def test_wrong_token_fails(self) -> None:
        auth = _load_restoration()
        auth["authorization_token"] = "WRONG_TOKEN"
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert "RESTORATION_TOKEN_MISMATCH" in reasons

    def test_semantics_neutral_purpose_class_fails(self) -> None:
        auth = _load_restoration()
        auth["mutation_purpose_class"] = TECHNICAL_WIRING_MUTATION_PURPOSE
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert "RESTORATION_MUTATION_PURPOSE_MISMATCH" in reasons
        assert REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID in reasons

    def test_missing_restoration_target_id_fails(self) -> None:
        auth = _load_restoration()
        auth["restoration_target_id"] = ""
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_RESTORATION_TARGET_BINDING_INVALID in reasons

    def test_a06_identifier_as_restoration_target_fails(self) -> None:
        auth = _load_restoration()
        auth["restoration_target_id"] = "A06_CAPITAL_RISK_SIZING_INTENT"
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_RESTORATION_TARGET_BINDING_INVALID in reasons

    def test_missing_attestation_id_fails(self) -> None:
        auth = _load_restoration()
        auth["restoration_attestation_id"] = ""
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_RESTORATION_ATTESTATION_BINDING_INVALID in reasons

    def test_wrong_attestation_path_fails(self) -> None:
        auth = _load_restoration()
        auth["restoration_attestation_id"] = "docs/ops/specs/DOES_NOT_EXIST_V1.md"
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_RESTORATION_ATTESTATION_BINDING_INVALID in reasons

    def test_wrong_historical_sha_fails(self) -> None:
        auth = _load_restoration()
        auth["historical_reference_sha256"] = "0" * 64
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_RESTORATION_REFERENCE_BINDING_INVALID in reasons

    def test_historical_authority_not_none_fails(self) -> None:
        auth = _load_restoration()
        auth["historical_reference_authority"] = "CANONICAL"
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_RESTORATION_REFERENCE_BINDING_INVALID in reasons

    def test_grant_claimed_with_empty_paths_fails(self) -> None:
        auth = _grant_fixture([])
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_RESTORATION_PATH_UNAUTHORIZED in reasons

    def test_directory_grant_fails(self) -> None:
        auth = _grant_fixture(["src/trading/master_v2/"])
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_RESTORATION_BROAD_SCOPE_FORBIDDEN in reasons

    def test_glob_grant_fails(self) -> None:
        auth = _grant_fixture(["src/trading/master_v2/*.py"])
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_RESTORATION_BROAD_SCOPE_FORBIDDEN in reasons

    def test_broad_master_v2_grant_fails(self) -> None:
        auth = _grant_fixture(["src/trading/master_v2/**"])
        auth["BROAD_MASTER_V2_GRANT"] = True
        auth["restoration_invariants"]["BROAD_MASTER_V2_GRANT"] = True
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_RESTORATION_BROAD_SCOPE_FORBIDDEN in reasons or (
            REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID in reasons
        )

    @pytest.mark.parametrize(
        "flag",
        [
            "NEW_POLICY_INTRODUCED",
            "UNATTESTED_FORMULA_CHANGE",
            "CANONICAL_COMPUTE_OWNER_CHANGED",
            "EXECUTION_AUTHORITY_CHANGED",
            "LIVE_AUTHORITY_CHANGED",
            "SAFETY_AUTHORITY_CHANGED",
            "TRADING_AUTHORITY_CHANGED",
            "REQUIRED_CHECK_WAIVER",
            "BRANCH_PROTECTION_BYPASS",
        ],
    )
    def test_forbidden_true_invariants_fail(self, flag: str) -> None:
        auth = _load_restoration()
        auth[flag] = True
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID in reasons

    def test_current_system_semantic_delta_false_fails(self) -> None:
        auth = _load_restoration()
        auth["CURRENT_SYSTEM_SEMANTIC_DELTA"] = False
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID in reasons

    def test_token_alone_insufficient_missing_fails(self) -> None:
        auth = _load_restoration()
        auth["TOKEN_ALONE_IS_INSUFFICIENT"] = False
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID in reasons

    def test_semantics_neutral_risk_sizing_false_claim_fails(self) -> None:
        auth = _load_restoration()
        auth["restoration_invariants"]["RISK_SIZING_SEMANTICS_CHANGED"] = False
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID in reasons

    def test_binds_to_current_a06_code_true_fails(self) -> None:
        auth = _load_restoration()
        auth["binds_to_current_a06_code"] = True
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID in reasons

    def test_invalid_target_binding_does_not_admit_forbidden_path(self) -> None:
        auth = _grant_fixture([FIXTURE_GRANTED_PATH])
        auth["restoration_target_id"] = ""
        report = build_boundary_report(
            [FIXTURE_GRANTED_PATH],
            repo_root=REPO_ROOT,
            restoration_authorization=auth,
        )
        assert report.admissible is False
        assert REASON_RESTORATION_INVALID in report.reason_codes
        assert REASON_RESTORATION_TARGET_BINDING_INVALID in report.reason_codes


class TestRestorationAdmissionPositiveFixtureV1:
    def test_exact_file_grant_admits_and_keeps_semantic_delta(self) -> None:
        auth = _grant_fixture([FIXTURE_GRANTED_PATH])
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is True, reasons
        report = build_boundary_report(
            [FIXTURE_GRANTED_PATH],
            repo_root=REPO_ROOT,
            restoration_authorization=auth,
        )
        assert report.admissible is True
        assert report.fail_closed is False
        assert report.restoration_authorization_applied is True
        assert report.technical_wiring_authorization_applied is False
        assert report.restoration_mutation_purpose_class == RESTORATION_MUTATION_PURPOSE
        assert REASON_RESTORATION_AUTHORIZED in report.reason_codes
        assert report.canonical_trading_semantics_changed is True
        assert report.master_v2_changed is True
        assert forbidden_surface_changed_count(report) == 0

    def test_grant_does_not_cover_ungranted_forbidden_file(self) -> None:
        auth = _grant_fixture([FIXTURE_GRANTED_PATH])
        report = build_boundary_report(
            [FIXTURE_GRANTED_PATH, "src/governance/capital_risk_sizing_v1.py"],
            repo_root=REPO_ROOT,
            restoration_authorization=auth,
        )
        assert report.admissible is False
        assert REASON_RESTORATION_PATH_UNAUTHORIZED in report.reason_codes
        assert report.restoration_authorization_applied is False
