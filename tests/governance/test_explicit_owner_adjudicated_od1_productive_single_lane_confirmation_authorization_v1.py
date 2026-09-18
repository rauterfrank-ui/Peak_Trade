"""Eighth Economic Guard class: OD1 productive single-lane confirmation."""

from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

from src.governance.economic_diagnostic_optimization_boundary_v0 import (
    build_boundary_report,
    load_armed_identity_split_authorization,
    load_contract,
    load_generator_fallback_authorization,
    load_mapping_bind_authorization,
    load_od1_single_lane_confirmation_authorization,
)
from src.governance.explicit_owner_adjudicated_od1_productive_single_lane_confirmation_authorization_v1 import (
    FORBIDDEN_RESEARCH_PATH,
    OD1_SINGLE_LANE_CONFIRMATION_AUTHORIZATION_ID,
    OD1_SINGLE_LANE_CONFIRMATION_AUTH_VERSION,
    OD1_SINGLE_LANE_CONFIRMATION_BOUND_AUTHORITY_SPEC,
    OD1_SINGLE_LANE_CONFIRMATION_CLASS_ATTESTATION_RELATIVE,
    OD1_SINGLE_LANE_CONFIRMATION_MUTATION_PURPOSE,
    OD1_SINGLE_LANE_CONFIRMATION_SCOPE_CLASS,
    REASON_OD1_SINGLE_LANE_CONFIRMATION_AUTH_VALID,
    REASON_OD1_SINGLE_LANE_CONFIRMATION_AUTHORIZED,
    REASON_OD1_SINGLE_LANE_CONFIRMATION_BASE_MISMATCH,
    REASON_OD1_SINGLE_LANE_CONFIRMATION_DIGEST_MISMATCH,
    REASON_OD1_SINGLE_LANE_CONFIRMATION_EXCLUDED_PATH,
    REASON_OD1_SINGLE_LANE_CONFIRMATION_FORBIDDEN_PREFIX,
    REASON_OD1_SINGLE_LANE_CONFIRMATION_PATH_UNAUTHORIZED,
    REASON_OD1_SINGLE_LANE_CONFIRMATION_REQUIRED_RUNTIME_MISSING,
    REASON_OD1_SINGLE_LANE_CONFIRMATION_UNKNOWN_FIELD,
    compute_od1_single_lane_confirmation_evidence_digest,
    validate_od1_single_lane_confirmation_authorization,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
AUTH_PATH = (
    REPO_ROOT
    / "config/governance/"
    / "explicit_owner_adjudicated_od1_productive_single_lane_confirmation_authorization_v1.json"
)

COMMITTED_ALLOWED_PATHS = [
    "src/trading/master_v2/single_lane_confirmation_activation_v1.py",
    "src/trading/master_v2/post_confirmation_survival_suitability_composition_binding_v1.py",
    "src/trading/master_v2/double_play_composition_matrix_v1.py",
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    "tests/trading/master_v2/test_single_lane_confirmation_activation_v1.py",
    "tests/trading/master_v2/test_single_lane_composition_matrix_v1.py",
    "tests/trading/master_v2/test_od1_single_lane_confirmation_regression_v1.py",
    "tests/trading/master_v2/test_directional_assessment_confirmation_integration_v1.py",
    "tests/trading/master_v2/test_post_confirmation_survival_suitability_composition_binding_v1.py",
    "tests/trading/master_v2/test_integrated_offline_trading_logic_replay_v1.py",
]
COMMITTED_REQUIRED_RUNTIME_PATHS = [
    "src/trading/master_v2/single_lane_confirmation_activation_v1.py",
    "src/trading/master_v2/post_confirmation_survival_suitability_composition_binding_v1.py",
    "src/trading/master_v2/double_play_composition_matrix_v1.py",
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
]
COMMITTED_DIFF_BASE_SHA = "255450145660c68a98b1dbfd29952308d12932e2"
COMMITTED_EVIDENCE_DIGEST = "f7da8710edd4de1dfceabd9ef3c54fb49b731aa747fed20abcab3ffa104714e6"
COMMITTED_SLICE_GRANT_ID = "OD1_PRODUCTIVE_SINGLE_LANE_CONFIRMATION_BOUNDED_SLICE_V1"
FOREIGN_MASTER_V2_PATH = "src/trading/master_v2/survival_assessment_v1.py"
FOREIGN_MASTER_V2_TEST_PATH = "tests/trading/master_v2/test_survival_assessment_v1.py"
ENTRY_EXIT_PATH = "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
SIDE_STATE_PATH = "src/trading/master_v2/double_play_state.py"
SWITCH_PATH = "src/trading/master_v2/bull_bear_state_switch_scenario_binding_adapter_v0.py"
SCOPE_EVENT_PATH = "src/trading/master_v2/scope_event_generator_scenario_binding_adapter_v0.py"
EXECUTION_PREFIX_PATH = "src/execution/od1_single_lane_probe_v1.py"
RISK_PREFIX_PATH = "src/risk/od1_single_lane_probe_v1.py"
LIVE_ROOT_PATH = "src/ops/full_core_live_path_composition_root_v1/od1_probe_v1.py"
TEST_DIFF_BASE_SHA = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
OTHER_DIFF_BASE_SHA = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
FIXTURE_SLICE_GRANT_ID = "OD1_PRODUCTIVE_SINGLE_LANE_CONFIRMATION_FIXTURE_SLICE_V1"


def _load_auth() -> dict:
    payload = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _unified_diff(path: str, removed: list[str], added: list[str]) -> str:
    lines = [
        f"--- a/{path}",
        f"+++ b/{path}",
        f"@@ -1,{len(removed) or 1} +1,{len(added) or 1} @@",
    ]
    lines.extend(f"-{line}" for line in removed)
    lines.extend(f"+{line}" for line in added)
    return "\n".join(lines) + "\n"


def _od1_diff(path: str) -> str:
    return _unified_diff(
        path,
        ["    evaluate_confirmation_both_lanes(state)"],
        ["    evaluate_selected_lane_confirmation(state)"],
    )


def _active_grant(
    allowed_paths: list[str],
    diffs: dict[str, str],
    *,
    required_runtime_paths: list[str] | None = None,
    diff_base_sha: str = TEST_DIFF_BASE_SHA,
) -> dict:
    auth = copy.deepcopy(_load_auth())
    auth["grant_active"] = True
    auth["allowed_paths"] = list(allowed_paths)
    auth["required_runtime_paths"] = list(
        required_runtime_paths
        if required_runtime_paths is not None
        else [COMMITTED_REQUIRED_RUNTIME_PATHS[0]]
    )
    auth["allowed_surface_classes"] = [OD1_SINGLE_LANE_CONFIRMATION_SCOPE_CLASS]
    auth["bound_diff_base_sha"] = diff_base_sha
    auth["slice_grant_id"] = FIXTURE_SLICE_GRANT_ID
    auth["authorized_evidence_digest"] = compute_od1_single_lane_confirmation_evidence_digest(
        file_diffs=diffs,
        diff_base_sha=diff_base_sha,
        paths=allowed_paths,
    )
    return auth


def _report(
    changed: list[str],
    *,
    auth: dict | None = None,
    diffs: dict[str, str] | None = None,
    skip_wiring: bool = True,
    skip_decommission: bool = True,
    skip_restoration: bool = True,
    skip_owner: bool = True,
    skip_mapping: bool = True,
    skip_generator: bool = True,
    skip_armed: bool = True,
    skip_od1: bool = False,
    diff_base_sha: str | None = TEST_DIFF_BASE_SHA,
) -> object:
    return build_boundary_report(
        changed,
        repo_root=REPO_ROOT,
        od1_single_lane_confirmation_authorization=auth,
        skip_od1_single_lane_confirmation_authorization=skip_od1,
        skip_armed_identity_split_authorization=skip_armed,
        skip_generator_fallback_authorization=skip_generator,
        skip_mapping_bind_authorization=skip_mapping,
        skip_technical_wiring_authorization=skip_wiring,
        skip_decommission_authorization=skip_decommission,
        skip_restoration_authorization=skip_restoration,
        skip_owner_adjudication_authorization=skip_owner,
        file_diffs=diffs,
        diff_base_sha=diff_base_sha,
    )


def _committed_file_diffs() -> dict[str, str]:
    diffs: dict[str, str] = {}
    for path in COMMITTED_ALLOWED_PATHS:
        result = subprocess.run(
            ["git", "diff", "-U20", "origin/main...HEAD", "--", path],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        diffs[path] = result.stdout if result.returncode == 0 else ""
    return diffs


class TestOd1SingleLaneConfirmationCommittedActiveGrantV1:
    def test_committed_artifact_is_valid_active_exact_file_grant(self) -> None:
        auth = load_od1_single_lane_confirmation_authorization(REPO_ROOT)
        assert auth is not None
        valid, reasons = validate_od1_single_lane_confirmation_authorization(
            auth, repo_root=REPO_ROOT
        )
        assert valid is True, reasons
        assert reasons == (REASON_OD1_SINGLE_LANE_CONFIRMATION_AUTH_VALID,)
        assert auth["contract_version"] == OD1_SINGLE_LANE_CONFIRMATION_AUTH_VERSION
        assert auth["authorized_scope_class"] == OD1_SINGLE_LANE_CONFIRMATION_SCOPE_CLASS
        assert auth["authorization_token"] == OD1_SINGLE_LANE_CONFIRMATION_AUTHORIZATION_ID
        assert auth["mutation_purpose_class"] == OD1_SINGLE_LANE_CONFIRMATION_MUTATION_PURPOSE
        assert auth["grant_active"] is True
        assert auth["allowed_paths"] == COMMITTED_ALLOWED_PATHS
        assert auth["required_runtime_paths"] == COMMITTED_REQUIRED_RUNTIME_PATHS
        assert auth["allowed_surface_classes"] == [OD1_SINGLE_LANE_CONFIRMATION_SCOPE_CLASS]
        assert auth["slice_grant_id"] == COMMITTED_SLICE_GRANT_ID
        assert auth["authorized_evidence_digest"] == COMMITTED_EVIDENCE_DIGEST
        assert auth["bound_diff_base_sha"] == COMMITTED_DIFF_BASE_SHA
        assert auth["authorized_path_prefixes"] == []
        assert auth["pr_specific_exception"] is False
        assert auth["directory_grant"] is False
        assert auth["blanket_allowlist"] is False
        assert FORBIDDEN_RESEARCH_PATH not in auth["allowed_paths"]
        assert "pr_number" not in auth
        assert "branch_name" not in auth
        assert "MASTER_V2_MUTATION_ALLOWED" not in auth
        assert "CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED" not in auth
        assert auth["class_attestation"] == OD1_SINGLE_LANE_CONFIRMATION_CLASS_ATTESTATION_RELATIVE
        assert auth["bound_authority_spec"] == OD1_SINGLE_LANE_CONFIRMATION_BOUND_AUTHORITY_SPEC
        assert (REPO_ROOT / OD1_SINGLE_LANE_CONFIRMATION_CLASS_ATTESTATION_RELATIVE).is_file()
        invariants = auth["required_semantic_invariants"]
        assert invariants["TRADING_SEMANTICS_CHANGED"] is True
        assert invariants["ENTRY_EXIT_RUNTIME_CHANGED"] is False
        assert invariants["ARMED_LAST_ACTIVE_SIDE_CHANGED"] is False
        assert invariants["BULL_BEAR_ASSESSMENT_RUNTIME_CHANGED"] is False
        assert invariants["ACTIVE_SIDE_TO_SCOPE_DIRECTION_CHANGED"] is False
        assert invariants["EXECUTION_SEMANTICS_CHANGED"] is False
        assert invariants["EXECUTION_AUTHORIZATION_CHANGED"] is False
        assert invariants["RISK_SEMANTICS_CHANGED"] is False
        assert invariants["AUTHORITY_EFFECT"] == "NONE"
        assert invariants["RUNTIME_EFFECT"] == "NONE"
        assert invariants["ORDER_EFFECT"] == "NONE"
        assert invariants["FIFTH_CLASS_GRANT_REOPENED"] is False
        assert invariants["SIXTH_CLASS_GRANT_REOPENED"] is False
        assert invariants["SEVENTH_CLASS_GRANT_REOPENED"] is False
        claims = auth["human_adjudicated_slice_claims"]
        assert claims["ELEMENTARY_DIRECTION_SOLE_PRODUCTIVE_IDENTITY"] is True
        assert claims["PRODUCTIVE_C3_SELECTED_LANE_ONLY"] is True
        assert claims["INACTIVE_LANE_IS_ABSENCE"] is True
        assert claims["NO_SYNTHETIC_DA_FOR_INACTIVE_OR_NEUTRAL"] is True
        assert claims["C4_CANDIDATE_CARDINALITY_LE_1"] is True
        assert claims["C4_SOLE_SELECTED_SIDE_PRODUCER"] is True
        assert claims["ENTRY_EXIT_SEMANTICS_UNCHANGED"] is True
        assert claims["SIDESTATE_ARMED_UNCHANGED"] is True
        assert claims["SCOPE_EVENT_SWITCH_UNCHANGED"] is True
        assert claims["EXECUTION_RISK_INTENT_UNCHANGED"] is True
        assert claims["NO_PARALLEL_PRODUCTIVE_DIRECTION_AUTHORITY"] is True
        mapping = load_mapping_bind_authorization(REPO_ROOT)
        assert mapping is not None
        assert mapping["grant_active"] is False
        sixth = load_generator_fallback_authorization(REPO_ROOT)
        assert sixth is not None
        assert sixth["grant_active"] is False
        seventh = load_armed_identity_split_authorization(REPO_ROOT)
        assert seventh is not None
        assert seventh["grant_active"] is False
        assert load_contract(REPO_ROOT)["immutable_flags"]["MASTER_V2_MUTATION_ALLOWED"] is False
        assert (
            load_contract(REPO_ROOT)["immutable_flags"]["CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED"]
            is False
        )

    def test_committed_digest_matches_locked_ten_file_diffs(self) -> None:
        diffs = _committed_file_diffs()
        actual = compute_od1_single_lane_confirmation_evidence_digest(
            file_diffs=diffs,
            diff_base_sha=COMMITTED_DIFF_BASE_SHA,
            paths=COMMITTED_ALLOWED_PATHS,
        )
        assert actual == COMMITTED_EVIDENCE_DIGEST

    def test_committed_ten_file_forbidden_surface_is_admissible(self) -> None:
        diffs = _committed_file_diffs()
        report = build_boundary_report(
            COMMITTED_ALLOWED_PATHS + [FORBIDDEN_RESEARCH_PATH],
            repo_root=REPO_ROOT,
            file_diffs=diffs,
            diff_base_sha=COMMITTED_DIFF_BASE_SHA,
            skip_technical_wiring_authorization=True,
            skip_decommission_authorization=True,
            skip_restoration_authorization=True,
            skip_owner_adjudication_authorization=True,
            skip_mapping_bind_authorization=True,
            skip_generator_fallback_authorization=True,
            skip_armed_identity_split_authorization=True,
        )
        assert report.admissible is True
        assert report.fail_closed is False
        assert report.od1_single_lane_confirmation_authorization_applied is True
        assert REASON_OD1_SINGLE_LANE_CONFIRMATION_AUTHORIZED in report.reason_codes
        assert report.unclassified_touch_count == 0
        assert report.impact_unknown is False
        assert FORBIDDEN_RESEARCH_PATH not in {
            match.matched_path for match in report.forbidden_surface_matches
        }
        unique_forbidden = {match.matched_path for match in report.forbidden_surface_matches}
        assert unique_forbidden == set(COMMITTED_ALLOWED_PATHS)
        assert (
            "OFFLINE_ECONOMIC_EVALUATION_EXECUTION_INFRASTRUCTURE_WITHOUT_TRADING_SEMANTIC_EFFECT"
            in report.allowed_surface_classification
        )
        assert load_contract(REPO_ROOT)["immutable_flags"]["MASTER_V2_MUTATION_ALLOWED"] is False


class TestOd1SingleLaneConfirmationAdmissionNegativeV1:
    def test_without_class_master_v2_diff_blocks(self) -> None:
        changed = list(COMMITTED_REQUIRED_RUNTIME_PATHS)
        diffs = {path: _od1_diff(path) for path in changed}
        auth = _active_grant(changed, diffs, required_runtime_paths=changed)
        auth["grant_active"] = False
        auth["allowed_paths"] = []
        auth["required_runtime_paths"] = []
        auth["allowed_surface_classes"] = []
        auth["authorized_evidence_digest"] = ""
        auth["bound_diff_base_sha"] = ""
        auth["slice_grant_id"] = ""
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert report.od1_single_lane_confirmation_authorization_applied is False
        assert REASON_OD1_SINGLE_LANE_CONFIRMATION_AUTHORIZED not in report.reason_codes

    def test_additional_src_master_v2_file_blocks(self) -> None:
        allowed = list(COMMITTED_REQUIRED_RUNTIME_PATHS)
        changed = allowed + [FOREIGN_MASTER_V2_PATH]
        diffs = {path: _od1_diff(path) for path in changed}
        auth = _active_grant(allowed, diffs, required_runtime_paths=allowed)
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OD1_SINGLE_LANE_CONFIRMATION_PATH_UNAUTHORIZED in report.reason_codes

    def test_additional_master_v2_test_file_blocks(self) -> None:
        allowed = list(COMMITTED_REQUIRED_RUNTIME_PATHS)
        changed = allowed + [FOREIGN_MASTER_V2_TEST_PATH]
        diffs = {path: _od1_diff(path) for path in changed}
        auth = _active_grant(allowed, diffs, required_runtime_paths=allowed)
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OD1_SINGLE_LANE_CONFIRMATION_PATH_UNAUTHORIZED in report.reason_codes

    def test_entry_exit_policy_mutation_blocks(self) -> None:
        allowed = [COMMITTED_REQUIRED_RUNTIME_PATHS[0], ENTRY_EXIT_PATH]
        changed = allowed
        diffs = {path: _od1_diff(path) for path in changed}
        auth = _active_grant(
            allowed, diffs, required_runtime_paths=[COMMITTED_REQUIRED_RUNTIME_PATHS[0]]
        )
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OD1_SINGLE_LANE_CONFIRMATION_EXCLUDED_PATH in report.reason_codes

    def test_double_play_state_mutation_blocks(self) -> None:
        allowed = [COMMITTED_REQUIRED_RUNTIME_PATHS[0], SIDE_STATE_PATH]
        changed = allowed
        diffs = {path: _od1_diff(path) for path in changed}
        auth = _active_grant(
            allowed, diffs, required_runtime_paths=[COMMITTED_REQUIRED_RUNTIME_PATHS[0]]
        )
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OD1_SINGLE_LANE_CONFIRMATION_EXCLUDED_PATH in report.reason_codes

    def test_switch_adapter_mutation_blocks(self) -> None:
        allowed = [COMMITTED_REQUIRED_RUNTIME_PATHS[0], SWITCH_PATH]
        changed = allowed
        diffs = {path: _od1_diff(path) for path in changed}
        auth = _active_grant(
            allowed, diffs, required_runtime_paths=[COMMITTED_REQUIRED_RUNTIME_PATHS[0]]
        )
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OD1_SINGLE_LANE_CONFIRMATION_EXCLUDED_PATH in report.reason_codes

    def test_scope_event_generator_mutation_blocks(self) -> None:
        allowed = [COMMITTED_REQUIRED_RUNTIME_PATHS[0], SCOPE_EVENT_PATH]
        changed = allowed
        diffs = {path: _od1_diff(path) for path in changed}
        auth = _active_grant(
            allowed, diffs, required_runtime_paths=[COMMITTED_REQUIRED_RUNTIME_PATHS[0]]
        )
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OD1_SINGLE_LANE_CONFIRMATION_EXCLUDED_PATH in report.reason_codes

    def test_execution_prefix_blocks(self) -> None:
        allowed = [COMMITTED_REQUIRED_RUNTIME_PATHS[0], EXECUTION_PREFIX_PATH]
        changed = allowed
        diffs = {path: _od1_diff(path) for path in changed}
        auth = _active_grant(
            allowed, diffs, required_runtime_paths=[COMMITTED_REQUIRED_RUNTIME_PATHS[0]]
        )
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OD1_SINGLE_LANE_CONFIRMATION_FORBIDDEN_PREFIX in report.reason_codes

    def test_risk_prefix_blocks(self) -> None:
        allowed = [COMMITTED_REQUIRED_RUNTIME_PATHS[0], RISK_PREFIX_PATH]
        changed = allowed
        diffs = {path: _od1_diff(path) for path in changed}
        auth = _active_grant(
            allowed, diffs, required_runtime_paths=[COMMITTED_REQUIRED_RUNTIME_PATHS[0]]
        )
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OD1_SINGLE_LANE_CONFIRMATION_FORBIDDEN_PREFIX in report.reason_codes

    def test_full_core_live_composition_root_blocks(self) -> None:
        allowed = [COMMITTED_REQUIRED_RUNTIME_PATHS[0], LIVE_ROOT_PATH]
        changed = allowed
        diffs = {path: _od1_diff(path) for path in changed}
        auth = _active_grant(
            allowed, diffs, required_runtime_paths=[COMMITTED_REQUIRED_RUNTIME_PATHS[0]]
        )
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OD1_SINGLE_LANE_CONFIRMATION_FORBIDDEN_PREFIX in report.reason_codes

    def test_missing_required_runtime_path_blocks(self) -> None:
        allowed = list(COMMITTED_REQUIRED_RUNTIME_PATHS)
        changed = allowed[1:]
        diffs = {path: _od1_diff(path) for path in changed}
        auth = _active_grant(allowed, diffs, required_runtime_paths=allowed)
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OD1_SINGLE_LANE_CONFIRMATION_REQUIRED_RUNTIME_MISSING in report.reason_codes

    def test_wrong_base_sha_blocks(self) -> None:
        changed = list(COMMITTED_REQUIRED_RUNTIME_PATHS)
        diffs = {path: _od1_diff(path) for path in changed}
        auth = _active_grant(changed, diffs, required_runtime_paths=changed)
        report = _report(changed, auth=auth, diffs=diffs, diff_base_sha=OTHER_DIFF_BASE_SHA)
        assert report.admissible is False
        assert REASON_OD1_SINGLE_LANE_CONFIRMATION_BASE_MISMATCH in report.reason_codes

    def test_digest_mismatch_blocks(self) -> None:
        changed = list(COMMITTED_REQUIRED_RUNTIME_PATHS)
        original = {path: _od1_diff(path) for path in changed}
        extra = dict(original)
        extra[changed[0]] = (
            original[changed[0]] + "@@ -20,1 +20,2 @@\n context\n+    extra = True\n"
        )
        auth = _active_grant(changed, original, required_runtime_paths=changed)
        report = _report(changed, auth=auth, diffs=extra)
        assert report.admissible is False
        assert REASON_OD1_SINGLE_LANE_CONFIRMATION_DIGEST_MISMATCH in report.reason_codes

    def test_wildcard_grant_blocks(self) -> None:
        diffs = {
            COMMITTED_REQUIRED_RUNTIME_PATHS[0]: _od1_diff(COMMITTED_REQUIRED_RUNTIME_PATHS[0])
        }
        auth = _active_grant([COMMITTED_REQUIRED_RUNTIME_PATHS[0]], diffs)
        auth["allowed_paths"] = ["src/trading/master_v2/*.py"]
        valid, reasons = validate_od1_single_lane_confirmation_authorization(
            auth, repo_root=REPO_ROOT
        )
        assert valid is False
        assert "OD1_SINGLE_LANE_CONFIRMATION_ALLOWED_PATHS_NOT_EXACT_FILES" in reasons

    def test_directory_grant_blocks(self) -> None:
        diffs = {
            COMMITTED_REQUIRED_RUNTIME_PATHS[0]: _od1_diff(COMMITTED_REQUIRED_RUNTIME_PATHS[0])
        }
        auth = _active_grant([COMMITTED_REQUIRED_RUNTIME_PATHS[0]], diffs)
        auth["allowed_paths"] = ["src/trading/master_v2/"]
        valid, reasons = validate_od1_single_lane_confirmation_authorization(
            auth, repo_root=REPO_ROOT
        )
        assert valid is False
        assert "OD1_SINGLE_LANE_CONFIRMATION_ALLOWED_PATHS_NOT_EXACT_FILES" in reasons

    def test_research_funnel_in_od1_allowed_paths_blocks(self) -> None:
        diffs = {
            COMMITTED_REQUIRED_RUNTIME_PATHS[0]: _od1_diff(COMMITTED_REQUIRED_RUNTIME_PATHS[0])
        }
        auth = _active_grant([COMMITTED_REQUIRED_RUNTIME_PATHS[0]], diffs)
        auth["allowed_paths"] = [COMMITTED_REQUIRED_RUNTIME_PATHS[0], FORBIDDEN_RESEARCH_PATH]
        valid, reasons = validate_od1_single_lane_confirmation_authorization(
            auth, repo_root=REPO_ROOT
        )
        assert valid is False
        assert "OD1_SINGLE_LANE_CONFIRMATION_RESEARCH_PATH_IN_PRODUCTIVE_GRANT" in reasons

    def test_technical_wiring_substitution_blocks(self) -> None:
        diffs = {
            COMMITTED_REQUIRED_RUNTIME_PATHS[0]: _od1_diff(COMMITTED_REQUIRED_RUNTIME_PATHS[0])
        }
        auth = _active_grant([COMMITTED_REQUIRED_RUNTIME_PATHS[0]], diffs)
        auth["mutation_purpose_class"] = "SEMANTICS_NEUTRAL_TECHNICAL_CANONICAL_WIRING"
        valid, reasons = validate_od1_single_lane_confirmation_authorization(
            auth, repo_root=REPO_ROOT
        )
        assert valid is False
        assert "OD1_SINGLE_LANE_CONFIRMATION_WIRING_PURPOSE_FORBIDDEN" in reasons

    def test_mapping_bind_substitution_blocks(self) -> None:
        diffs = {
            COMMITTED_REQUIRED_RUNTIME_PATHS[0]: _od1_diff(COMMITTED_REQUIRED_RUNTIME_PATHS[0])
        }
        auth = _active_grant([COMMITTED_REQUIRED_RUNTIME_PATHS[0]], diffs)
        auth["mutation_purpose_class"] = "PRODUCTIVE_CANONICAL_MAPPING_CONTRACT_RUNTIME_BIND"
        valid, reasons = validate_od1_single_lane_confirmation_authorization(
            auth, repo_root=REPO_ROOT
        )
        assert valid is False
        assert "OD1_SINGLE_LANE_CONFIRMATION_FIFTH_CLASS_PURPOSE_FORBIDDEN" in reasons

    def test_restoration_substitution_blocks(self) -> None:
        diffs = {
            COMMITTED_REQUIRED_RUNTIME_PATHS[0]: _od1_diff(COMMITTED_REQUIRED_RUNTIME_PATHS[0])
        }
        auth = _active_grant([COMMITTED_REQUIRED_RUNTIME_PATHS[0]], diffs)
        auth["mutation_purpose_class"] = "HISTORICALLY_ATTESTED_CANONICAL_SEMANTIC_RESTORATION"
        valid, reasons = validate_od1_single_lane_confirmation_authorization(
            auth, repo_root=REPO_ROOT
        )
        assert valid is False
        assert "OD1_SINGLE_LANE_CONFIRMATION_RESTORATION_PURPOSE_FORBIDDEN" in reasons

    def test_generator_fallback_substitution_blocks(self) -> None:
        diffs = {
            COMMITTED_REQUIRED_RUNTIME_PATHS[0]: _od1_diff(COMMITTED_REQUIRED_RUNTIME_PATHS[0])
        }
        auth = _active_grant([COMMITTED_REQUIRED_RUNTIME_PATHS[0]], diffs)
        auth["mutation_purpose_class"] = "SCOPE_DIRECTION_GENERATOR_FALLBACK_REPAIR"
        valid, reasons = validate_od1_single_lane_confirmation_authorization(
            auth, repo_root=REPO_ROOT
        )
        assert valid is False
        assert "OD1_SINGLE_LANE_CONFIRMATION_SIXTH_CLASS_PURPOSE_FORBIDDEN" in reasons

    def test_sidestate_armed_substitution_blocks(self) -> None:
        diffs = {
            COMMITTED_REQUIRED_RUNTIME_PATHS[0]: _od1_diff(COMMITTED_REQUIRED_RUNTIME_PATHS[0])
        }
        auth = _active_grant([COMMITTED_REQUIRED_RUNTIME_PATHS[0]], diffs)
        auth["mutation_purpose_class"] = "SIDESTATE_ARMED_IDENTITY_SPLIT_REPAIR"
        valid, reasons = validate_od1_single_lane_confirmation_authorization(
            auth, repo_root=REPO_ROOT
        )
        assert valid is False
        assert "OD1_SINGLE_LANE_CONFIRMATION_SEVENTH_CLASS_PURPOSE_FORBIDDEN" in reasons

    def test_master_v2_mutation_allowed_true_blocks(self) -> None:
        diffs = {
            COMMITTED_REQUIRED_RUNTIME_PATHS[0]: _od1_diff(COMMITTED_REQUIRED_RUNTIME_PATHS[0])
        }
        auth = _active_grant([COMMITTED_REQUIRED_RUNTIME_PATHS[0]], diffs)
        auth["MASTER_V2_MUTATION_ALLOWED"] = True
        valid, reasons = validate_od1_single_lane_confirmation_authorization(
            auth, repo_root=REPO_ROOT
        )
        assert valid is False
        assert (
            "OD1_SINGLE_LANE_CONFIRMATION_IMMUTABLE_FLAG_TRUE:MASTER_V2_MUTATION_ALLOWED" in reasons
        )
        assert REASON_OD1_SINGLE_LANE_CONFIRMATION_UNKNOWN_FIELD in reasons

    def test_reopening_class_five_six_or_seven_blocks(self) -> None:
        diffs = {
            COMMITTED_REQUIRED_RUNTIME_PATHS[0]: _od1_diff(COMMITTED_REQUIRED_RUNTIME_PATHS[0])
        }
        auth = _active_grant([COMMITTED_REQUIRED_RUNTIME_PATHS[0]], diffs)
        for key in (
            "FIFTH_CLASS_GRANT_REOPENED",
            "SIXTH_CLASS_GRANT_REOPENED",
            "SEVENTH_CLASS_GRANT_REOPENED",
        ):
            mutated = copy.deepcopy(auth)
            mutated["required_semantic_invariants"][key] = True
            mutated["human_adjudicated_slice_claims"][key] = True
            valid, reasons = validate_od1_single_lane_confirmation_authorization(
                mutated, repo_root=REPO_ROOT
            )
            assert valid is False, key
            assert "OD1_SINGLE_LANE_CONFIRMATION_SEMANTIC_INVARIANT_NOT_FALSE" in reasons
