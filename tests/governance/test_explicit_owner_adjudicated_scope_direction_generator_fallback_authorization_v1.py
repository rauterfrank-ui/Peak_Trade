"""Sixth Economic Guard class: ScopeDirection generator-fallback authorization."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from src.governance.economic_diagnostic_optimization_boundary_v0 import (
    build_boundary_report,
    load_contract,
    load_generator_fallback_authorization,
    load_mapping_bind_authorization,
)
from src.governance.explicit_owner_adjudicated_scope_direction_generator_fallback_authorization_v1 import (
    GENERATOR_FALLBACK_AUTHORIZATION_ID,
    GENERATOR_FALLBACK_AUTH_VERSION,
    GENERATOR_FALLBACK_BOUND_AUTHORITY_SPEC,
    GENERATOR_FALLBACK_CLASS_ATTESTATION_RELATIVE,
    GENERATOR_FALLBACK_MUTATION_PURPOSE,
    GENERATOR_FALLBACK_SCOPE_CLASS,
    REASON_GENERATOR_FALLBACK_AUTH_INVALID,
    REASON_GENERATOR_FALLBACK_AUTH_VALID,
    REASON_GENERATOR_FALLBACK_AUTHORIZED,
    REASON_GENERATOR_FALLBACK_BASE_MISMATCH,
    REASON_GENERATOR_FALLBACK_DIGEST_MISMATCH,
    REASON_GENERATOR_FALLBACK_EXCLUDED_PATH,
    REASON_GENERATOR_FALLBACK_PATH_UNAUTHORIZED,
    REASON_GENERATOR_FALLBACK_REQUIRED_RUNTIME_MISSING,
    REASON_GENERATOR_FALLBACK_UNKNOWN_FIELD,
    compute_generator_fallback_evidence_digest,
    validate_generator_fallback_authorization,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
AUTH_PATH = (
    REPO_ROOT
    / "config/governance/"
    / "explicit_owner_adjudicated_scope_direction_generator_fallback_authorization_v1.json"
)

RUNTIME_PATH = "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
FOREIGN_MASTER_V2_PATH = "src/trading/master_v2/double_play_state.py"
EXCLUDED_PATH = "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
EXECUTION_PREFIX_PATH = "src/execution/generator_fallback_probe_v1.py"
TEST_DIFF_BASE_SHA = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
OTHER_DIFF_BASE_SHA = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
FIXTURE_SLICE_GRANT_ID = "SCOPE_DIRECTION_GENERATOR_FALLBACK_FIXTURE_SLICE_V1"
COMMITTED_SLICE_GRANT_ID = "SCOPE_DIRECTION_GENERATOR_FALLBACK_BOUNDED_SLICE_V1"


def _load_auth() -> dict:
    payload = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _inactive_grant() -> dict:
    auth = copy.deepcopy(_load_auth())
    auth["grant_active"] = False
    auth["allowed_paths"] = []
    auth["required_runtime_paths"] = []
    auth["allowed_surface_classes"] = []
    auth["authorized_evidence_digest"] = ""
    auth["bound_diff_base_sha"] = ""
    auth["slice_grant_id"] = ""
    return auth


def _unified_diff(path: str, removed: list[str], added: list[str]) -> str:
    lines = [
        f"--- a/{path}",
        f"+++ b/{path}",
        f"@@ -1,{len(removed) or 1} +1,{len(added) or 1} @@",
    ]
    lines.extend(f"-{line}" for line in removed)
    lines.extend(f"+{line}" for line in added)
    return "\n".join(lines) + "\n"


def _fallback_diff(path: str) -> str:
    return _unified_diff(
        path,
        [
            "    effective_scope_direction = scope_direction_from_side_state_v1(",
            "        inp.side_state,",
            "        fallback=inp.scope_direction_state,",
            "    )",
        ],
        [
            "    effective_scope_direction = scope_direction_from_side_state_v1(inp.side_state)",
        ],
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
        required_runtime_paths if required_runtime_paths is not None else [RUNTIME_PATH]
    )
    auth["allowed_surface_classes"] = [GENERATOR_FALLBACK_SCOPE_CLASS]
    auth["bound_diff_base_sha"] = diff_base_sha
    auth["slice_grant_id"] = FIXTURE_SLICE_GRANT_ID
    auth["authorized_evidence_digest"] = compute_generator_fallback_evidence_digest(
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
    skip_generator: bool = False,
    diff_base_sha: str | None = TEST_DIFF_BASE_SHA,
) -> object:
    return build_boundary_report(
        changed,
        repo_root=REPO_ROOT,
        generator_fallback_authorization=auth,
        skip_generator_fallback_authorization=skip_generator,
        skip_mapping_bind_authorization=skip_mapping,
        skip_technical_wiring_authorization=skip_wiring,
        skip_decommission_authorization=skip_decommission,
        skip_restoration_authorization=skip_restoration,
        skip_owner_adjudication_authorization=skip_owner,
        file_diffs=diffs,
        diff_base_sha=diff_base_sha,
    )


class TestGeneratorFallbackCommittedActiveGrantV1:
    def test_committed_artifact_is_valid_active_exact_slice(self) -> None:
        auth = load_generator_fallback_authorization(REPO_ROOT)
        assert auth is not None
        valid, reasons = validate_generator_fallback_authorization(auth, repo_root=REPO_ROOT)
        assert valid is True, reasons
        assert reasons == (REASON_GENERATOR_FALLBACK_AUTH_VALID,)
        assert auth["contract_version"] == GENERATOR_FALLBACK_AUTH_VERSION
        assert auth["authorized_scope_class"] == GENERATOR_FALLBACK_SCOPE_CLASS
        assert auth["authorization_token"] == GENERATOR_FALLBACK_AUTHORIZATION_ID
        assert auth["mutation_purpose_class"] == GENERATOR_FALLBACK_MUTATION_PURPOSE
        assert auth["grant_active"] is True
        assert auth["allowed_paths"] == [RUNTIME_PATH]
        assert auth["required_runtime_paths"] == [RUNTIME_PATH]
        assert auth["allowed_surface_classes"] == [GENERATOR_FALLBACK_SCOPE_CLASS]
        assert auth["slice_grant_id"] == COMMITTED_SLICE_GRANT_ID
        assert auth["authorized_path_prefixes"] == []
        assert auth["pr_specific_exception"] is False
        assert auth["directory_grant"] is False
        assert auth["blanket_allowlist"] is False
        assert "pr_number" not in auth
        assert "branch_name" not in auth
        assert "MASTER_V2_MUTATION_ALLOWED" not in auth
        assert auth["class_attestation"] == GENERATOR_FALLBACK_CLASS_ATTESTATION_RELATIVE
        assert auth["bound_authority_spec"] == GENERATOR_FALLBACK_BOUND_AUTHORITY_SPEC
        assert (REPO_ROOT / GENERATOR_FALLBACK_CLASS_ATTESTATION_RELATIVE).is_file()
        assert auth["required_semantic_invariants"]["TRADING_SEMANTICS_CHANGED"] is True
        assert auth["required_semantic_invariants"]["ENTRY_EXIT_RUNTIME_CHANGED"] is False
        assert auth["required_semantic_invariants"]["FIFTH_CLASS_GRANT_REOPENED"] is False
        assert (
            auth["human_adjudicated_slice_claims"][
                "COMPOSITION_SELECTED_SIDE_MAY_WRITE_SCOPE_DIRECTION_STATE"
            ]
            is False
        )
        mapping = load_mapping_bind_authorization(REPO_ROOT)
        assert mapping is not None
        assert mapping["grant_active"] is False
        assert load_contract(REPO_ROOT)["immutable_flags"]["MASTER_V2_MUTATION_ALLOWED"] is False


class TestGeneratorFallbackAdmissionPositiveV1:
    def test_exact_authorized_fixture_and_digest_pass(self) -> None:
        changed = [RUNTIME_PATH]
        diffs = {RUNTIME_PATH: _fallback_diff(RUNTIME_PATH)}
        auth = _active_grant(changed, diffs)
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is True
        assert report.fail_closed is False
        assert report.scope_direction_generator_fallback_authorization_applied is True
        assert REASON_GENERATOR_FALLBACK_AUTHORIZED in report.reason_codes
        assert report.productive_mapping_contract_runtime_bind_authorization_applied is False
        assert report.to_dict()["new_scope_direction_generator_fallback_authorization_applied"] is (
            True
        )

    def test_exact_slice_claims_admission_over_standing_wiring_subset(self) -> None:
        changed = [RUNTIME_PATH]
        diffs = {RUNTIME_PATH: _fallback_diff(RUNTIME_PATH)}
        auth = _active_grant(changed, diffs)
        report = _report(changed, auth=auth, diffs=diffs, skip_wiring=False)
        assert report.admissible is True
        assert report.scope_direction_generator_fallback_authorization_applied is True
        assert report.technical_wiring_authorization_applied is False
        assert REASON_GENERATOR_FALLBACK_AUTHORIZED in report.reason_codes


class TestGeneratorFallbackAdmissionNegativeV1:
    def test_without_class_master_v2_diff_blocks(self) -> None:
        changed = [RUNTIME_PATH]
        diffs = {RUNTIME_PATH: _fallback_diff(RUNTIME_PATH)}
        report = _report(changed, auth=_inactive_grant(), diffs=diffs)
        assert report.admissible is False
        assert report.scope_direction_generator_fallback_authorization_applied is False
        assert REASON_GENERATOR_FALLBACK_AUTHORIZED not in report.reason_codes

    def test_skip_class_blocks_authorized_runtime_path(self) -> None:
        changed = [RUNTIME_PATH]
        diffs = {RUNTIME_PATH: _fallback_diff(RUNTIME_PATH)}
        report = _report(changed, diffs=diffs, skip_generator=True)
        assert report.admissible is False
        assert report.scope_direction_generator_fallback_authorization_applied is False

    def test_foreign_master_v2_file_blocks(self) -> None:
        allowed = [RUNTIME_PATH]
        changed = [RUNTIME_PATH, FOREIGN_MASTER_V2_PATH]
        diffs = {path: _fallback_diff(path) for path in changed}
        auth = _active_grant(allowed, diffs)
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_GENERATOR_FALLBACK_PATH_UNAUTHORIZED in report.reason_codes

    def test_additional_unauthorized_path_in_same_diff_blocks(self) -> None:
        allowed = [RUNTIME_PATH]
        changed = [RUNTIME_PATH, "src/trading/master_v2/double_play_composition_matrix_v1.py"]
        diffs = {path: _fallback_diff(path) for path in changed}
        auth = _active_grant(allowed, diffs)
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_GENERATOR_FALLBACK_PATH_UNAUTHORIZED in report.reason_codes

    def test_additional_hunk_digest_mismatch_blocks(self) -> None:
        changed = [RUNTIME_PATH]
        original = {RUNTIME_PATH: _fallback_diff(RUNTIME_PATH)}
        extra = {
            RUNTIME_PATH: original[RUNTIME_PATH]
            + "@@ -20,1 +20,2 @@\n"
            + " context\n"
            + "+    extra = True\n",
        }
        auth = _active_grant(changed, original)
        report = _report(changed, auth=auth, diffs=extra)
        assert report.admissible is False
        assert REASON_GENERATOR_FALLBACK_DIGEST_MISMATCH in report.reason_codes

    def test_wrong_base_sha_blocks(self) -> None:
        changed = [RUNTIME_PATH]
        diffs = {RUNTIME_PATH: _fallback_diff(RUNTIME_PATH)}
        auth = _active_grant(changed, diffs)
        report = _report(changed, auth=auth, diffs=diffs, diff_base_sha=OTHER_DIFF_BASE_SHA)
        assert report.admissible is False
        assert REASON_GENERATOR_FALLBACK_BASE_MISMATCH in report.reason_codes

    def test_excluded_path_in_diff_blocks(self) -> None:
        allowed = [RUNTIME_PATH, EXCLUDED_PATH]
        changed = allowed
        diffs = {path: _fallback_diff(path) for path in changed}
        auth = _active_grant(allowed, diffs, required_runtime_paths=[RUNTIME_PATH])
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_GENERATOR_FALLBACK_EXCLUDED_PATH in report.reason_codes

    def test_required_runtime_path_missing_from_diff_blocks(self) -> None:
        other = "src/trading/master_v2/survival_assessment_v1.py"
        allowed = [RUNTIME_PATH, other]
        changed = [other]
        diffs = {other: _fallback_diff(other)}
        auth = _active_grant(allowed, diffs, required_runtime_paths=[RUNTIME_PATH])
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_GENERATOR_FALLBACK_REQUIRED_RUNTIME_MISSING in report.reason_codes

    def test_glob_in_path_blocks(self) -> None:
        diffs = {RUNTIME_PATH: _fallback_diff(RUNTIME_PATH)}
        auth = _active_grant([RUNTIME_PATH], diffs)
        auth["allowed_paths"] = ["src/trading/master_v2/*.py"]
        valid, reasons = validate_generator_fallback_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert "GENERATOR_FALLBACK_ALLOWED_PATHS_NOT_EXACT_FILES" in reasons

    def test_directory_grant_blocks(self) -> None:
        diffs = {RUNTIME_PATH: _fallback_diff(RUNTIME_PATH)}
        auth = _active_grant([RUNTIME_PATH], diffs)
        auth["allowed_paths"] = ["src/trading/master_v2/"]
        valid, reasons = validate_generator_fallback_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert "GENERATOR_FALLBACK_ALLOWED_PATHS_NOT_EXACT_FILES" in reasons

    def test_unknown_json_key_blocks(self) -> None:
        diffs = {RUNTIME_PATH: _fallback_diff(RUNTIME_PATH)}
        auth = _active_grant([RUNTIME_PATH], diffs)
        auth["unexpected_owner_field"] = True
        valid, reasons = validate_generator_fallback_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_GENERATOR_FALLBACK_UNKNOWN_FIELD in reasons
        report = _report([RUNTIME_PATH], auth=auth, diffs=diffs)
        assert report.admissible is False

    def test_fifth_class_purpose_in_sixth_class_blocks(self) -> None:
        diffs = {RUNTIME_PATH: _fallback_diff(RUNTIME_PATH)}
        auth = _active_grant([RUNTIME_PATH], diffs)
        auth["mutation_purpose_class"] = "PRODUCTIVE_CANONICAL_MAPPING_CONTRACT_RUNTIME_BIND"
        valid, reasons = validate_generator_fallback_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert "GENERATOR_FALLBACK_FIFTH_CLASS_PURPOSE_FORBIDDEN" in reasons

    def test_forbidden_execution_prefix_blocks_even_if_listed(self) -> None:
        allowed = [RUNTIME_PATH, EXECUTION_PREFIX_PATH]
        changed = allowed
        diffs = {path: _fallback_diff(path) for path in changed}
        auth = _active_grant(allowed, diffs, required_runtime_paths=[RUNTIME_PATH])
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
