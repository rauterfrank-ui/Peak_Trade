"""Explicit owner-adjudicated productive mapping-contract runtime-bind authorization."""

from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

from src.governance.economic_diagnostic_optimization_boundary_v0 import (
    RESTORATION_AUTH_VERSION,
    RESTORATION_MUTATION_PURPOSE,
    RESTORATION_SCOPE_CLASS,
    TECHNICAL_WIRING_AUTH_VERSION,
    TECHNICAL_WIRING_MUTATION_PURPOSE,
    TECHNICAL_WIRING_SCOPE_CLASS,
    build_boundary_report,
    load_contract,
    load_decommission_authorization,
    load_mapping_bind_authorization,
    load_owner_adjudication_authorization,
    load_restoration_authorization,
    load_technical_wiring_authorization,
    validate_decommission_authorization,
    validate_mapping_bind_authorization,
    validate_owner_adjudication_authorization,
    validate_restoration_authorization,
    validate_technical_wiring_authorization,
)
from src.governance.explicit_owner_adjudicated_productive_mapping_contract_runtime_bind_authorization_v1 import (
    MAPPING_BIND_AUTHORIZATION_ID,
    MAPPING_BIND_AUTH_VERSION,
    MAPPING_BIND_CLASS_ATTESTATION_RELATIVE,
    MAPPING_BIND_CONTRACT_SPEC,
    MAPPING_BIND_MUTATION_PURPOSE,
    MAPPING_BIND_SCOPE_CLASS,
    REASON_MAPPING_BIND_AUTH_INVALID,
    REASON_MAPPING_BIND_AUTH_VALID,
    REASON_MAPPING_BIND_AUTHORIZED,
    REASON_MAPPING_BIND_BASE_MISMATCH,
    REASON_MAPPING_BIND_DIGEST_MISMATCH,
    REASON_MAPPING_BIND_EXCLUDED_PATH,
    REASON_MAPPING_BIND_PATH_UNAUTHORIZED,
    REASON_MAPPING_BIND_REQUIRED_RUNTIME_MISSING,
    REASON_MAPPING_BIND_UNKNOWN_FIELD,
    compute_mapping_bind_evidence_digest,
)
from src.governance.semantics_neutral_decommission_authorization_v1 import (
    DECOMMISSION_AUTH_VERSION,
    DECOMMISSION_MUTATION_PURPOSE,
    DECOMMISSION_SCOPE_CLASS,
    EVIDENCE_DIGEST_ALGORITHM,
    EVIDENCE_DIGEST_CANONICALIZATION,
)
from tests.governance.test_historically_attested_current_system_semantic_restoration_authorization_v1 import (
    COMMITTED_SLICE_GRANT_PATHS,
)
from tests.governance.test_technical_canonical_wiring_authorization_bound_to_boundary_guard_v1 import (
    AUTHORIZED_TECHNICAL_WIRING_FIXTURE,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
AUTH_PATH = (
    REPO_ROOT
    / "config/governance/explicit_owner_adjudicated_productive_mapping_contract_runtime_bind_authorization_v1.json"
)

RUNTIME_PATH = "src/trading/master_v2/double_play_state.py"
SPEC_PATH = "docs/ops/specs/FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md"
EXTRA_RUNTIME_PATH = "src/trading/master_v2/evaluate_double_play_authority_boundary_v0.py"
EXCLUDED_PATH = "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
EXECUTION_PREFIX_PATH = "src/execution/mapping_bind_probe_v1.py"

TEST_DIFF_BASE_SHA = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
OTHER_DIFF_BASE_SHA = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
FIXTURE_SLICE_GRANT_ID = "PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_FIXTURE_SLICE_V1"
PR_6274_HEAD_SHA = "955a05b40cb53fc00b12bcd96cf71b3a524f40da"

REQUIRED_RUNTIME_PATHS = (
    "src/trading/master_v2/double_play_state.py",
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
)


def _load_auth() -> dict:
    payload = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _inactive_grant() -> dict:
    return copy.deepcopy(_load_auth())


def _unified_diff(path: str, removed: list[str], added: list[str]) -> str:
    lines = [
        f"--- a/{path}",
        f"+++ b/{path}",
        f"@@ -1,{len(removed) or 1} +1,{len(added) or 1} @@",
    ]
    lines.extend(f"-{line}" for line in removed)
    lines.extend(f"+{line}" for line in added)
    return "\n".join(lines) + "\n"


def _polarity_diff(path: str) -> str:
    return _unified_diff(
        path,
        ["            return ScopeDirection.UPSCOPE_CONFIRMED"],
        ["            return ScopeDirection.DOWNSCOPE_CONFIRMED"],
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
    auth["allowed_surface_classes"] = [MAPPING_BIND_SCOPE_CLASS]
    auth["bound_diff_base_sha"] = diff_base_sha
    auth["slice_grant_id"] = FIXTURE_SLICE_GRANT_ID
    auth["authorized_evidence_digest"] = compute_mapping_bind_evidence_digest(
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
    skip_mapping: bool = False,
    diff_base_sha: str | None = TEST_DIFF_BASE_SHA,
) -> object:
    return build_boundary_report(
        changed,
        repo_root=REPO_ROOT,
        mapping_bind_authorization=auth,
        skip_mapping_bind_authorization=skip_mapping,
        skip_technical_wiring_authorization=skip_wiring,
        skip_decommission_authorization=skip_decommission,
        skip_restoration_authorization=skip_restoration,
        skip_owner_adjudication_authorization=skip_owner,
        file_diffs=diffs,
        diff_base_sha=diff_base_sha,
    )


def _sha_exists(sha: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-t", sha],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "commit"


class TestMappingBindCommittedInactiveGrantV1:
    def test_committed_artifact_is_valid_inactive_grant(self) -> None:
        auth = load_mapping_bind_authorization(REPO_ROOT)
        assert auth is not None
        valid, reasons = validate_mapping_bind_authorization(auth, repo_root=REPO_ROOT)
        assert valid is True, reasons
        assert reasons == (REASON_MAPPING_BIND_AUTH_VALID,)
        assert auth["contract_version"] == MAPPING_BIND_AUTH_VERSION
        assert auth["authorized_scope_class"] == MAPPING_BIND_SCOPE_CLASS
        assert auth["authorization_token"] == MAPPING_BIND_AUTHORIZATION_ID
        assert auth["mutation_purpose_class"] == MAPPING_BIND_MUTATION_PURPOSE
        assert auth["grant_active"] is False
        assert auth["allowed_paths"] == []
        assert auth["required_runtime_paths"] == []
        assert auth["authorized_evidence_digest"] == ""
        assert auth["bound_diff_base_sha"] == ""
        assert auth["slice_grant_id"] == ""
        assert auth["authorized_path_prefixes"] == []
        assert auth["pr_specific_exception"] is False
        assert auth["directory_grant"] is False
        assert auth["blanket_allowlist"] is False
        assert "pr_number" not in auth
        assert "branch_name" not in auth
        assert auth["evidence_digest_algorithm"] == EVIDENCE_DIGEST_ALGORITHM
        assert auth["evidence_digest_canonicalization"] == EVIDENCE_DIGEST_CANONICALIZATION
        assert auth["class_attestation"] == MAPPING_BIND_CLASS_ATTESTATION_RELATIVE
        assert auth["mapping_contract_spec"] == MAPPING_BIND_CONTRACT_SPEC
        assert (REPO_ROOT / MAPPING_BIND_CLASS_ATTESTATION_RELATIVE).is_file()
        assert (REPO_ROOT / MAPPING_BIND_CONTRACT_SPEC).is_file()
        assert auth["required_semantic_invariants"]["TRADING_SEMANTICS_CHANGED"] is True
        assert auth["required_semantic_invariants"]["ENTRY_EXIT_RUNTIME_CHANGED"] is False
        assert (
            auth["human_adjudicated_slice_claims"]["CONTRACT_RUNTIME_BINDING_PROVEN_SCOPE"]
            == "OFFLINE_FIXTURE_PROOF_ONLY_NOT_LIVE"
        )

    def test_bound_from_boundary_contract(self) -> None:
        contract = load_contract(REPO_ROOT)
        assert contract[
            "explicit_owner_adjudicated_productive_mapping_contract_runtime_bind_authorization"
        ] == (
            "config/governance/"
            "explicit_owner_adjudicated_productive_mapping_contract_runtime_bind_authorization_v1.json"
        )
        assert contract["immutable_flags"]["MASTER_V2_MUTATION_ALLOWED"] is False
        assert contract["immutable_flags"]["CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED"] is False


class TestMappingBindAdmissionPositiveV1:
    def test_exact_authorized_fixture_and_digest_pass(self) -> None:
        changed = [RUNTIME_PATH, SPEC_PATH]
        diffs = {path: _polarity_diff(path) for path in changed}
        auth = _active_grant(changed, diffs)
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is True
        assert report.fail_closed is False
        assert report.canonical_trading_semantics_changed is True
        assert report.productive_mapping_contract_runtime_bind_authorization_applied is True
        assert REASON_MAPPING_BIND_AUTHORIZED in report.reason_codes
        assert report.technical_wiring_authorization_applied is False
        assert report.restoration_authorization_applied is False
        assert report.semantics_neutral_decommission_authorization_applied is False
        assert report.owner_adjudicated_nonproductive_contract_change_authorization_applied is False
        assert report.to_dict()["new_productive_mapping_bind_authorization_applied"] is True

    def test_wiring_listed_runtime_plus_non_wiring_forbidden_path_uses_mapping_class(
        self,
    ) -> None:
        changed = [RUNTIME_PATH, SPEC_PATH]
        diffs = {path: _polarity_diff(path) for path in changed}
        auth = _active_grant(changed, diffs)
        report = _report(changed, auth=auth, diffs=diffs, skip_wiring=False)
        assert report.admissible is True
        assert report.productive_mapping_contract_runtime_bind_authorization_applied is True
        assert report.technical_wiring_authorization_applied is False
        assert REASON_MAPPING_BIND_AUTHORIZED in report.reason_codes
        assert "TECHNICAL_CANONICAL_WIRING_AUTHORIZED" not in report.reason_codes


class TestMappingBindAdmissionNegativeV1:
    def test_inactive_grant_blocks(self) -> None:
        changed = [RUNTIME_PATH, SPEC_PATH]
        diffs = {path: _polarity_diff(path) for path in changed}
        report = _report(changed, auth=_inactive_grant(), diffs=diffs)
        assert report.admissible is False
        assert report.productive_mapping_contract_runtime_bind_authorization_applied is False
        assert REASON_MAPPING_BIND_AUTHORIZED not in report.reason_codes

    def test_additional_forbidden_runtime_path_blocks(self) -> None:
        allowed = [RUNTIME_PATH, SPEC_PATH]
        changed = [RUNTIME_PATH, SPEC_PATH, EXTRA_RUNTIME_PATH]
        diffs = {path: _polarity_diff(path) for path in changed}
        auth = _active_grant(allowed, diffs)
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_MAPPING_BIND_PATH_UNAUTHORIZED in report.reason_codes

    def test_additional_hunk_digest_mismatch_blocks(self) -> None:
        changed = [RUNTIME_PATH, SPEC_PATH]
        original = {path: _polarity_diff(path) for path in changed}
        extra = {
            RUNTIME_PATH: original[RUNTIME_PATH]
            + "@@ -20,1 +20,2 @@\n"
            + " context\n"
            + "+    extra = True\n",
            SPEC_PATH: original[SPEC_PATH],
        }
        auth = _active_grant(changed, original)
        report = _report(changed, auth=auth, diffs=extra)
        assert report.admissible is False
        assert REASON_MAPPING_BIND_DIGEST_MISMATCH in report.reason_codes

    def test_wrong_base_sha_blocks(self) -> None:
        changed = [RUNTIME_PATH, SPEC_PATH]
        diffs = {path: _polarity_diff(path) for path in changed}
        auth = _active_grant(changed, diffs)
        report = _report(changed, auth=auth, diffs=diffs, diff_base_sha=OTHER_DIFF_BASE_SHA)
        assert report.admissible is False
        assert REASON_MAPPING_BIND_BASE_MISMATCH in report.reason_codes

    def test_excluded_path_in_diff_blocks(self) -> None:
        allowed = [RUNTIME_PATH, SPEC_PATH, EXCLUDED_PATH]
        changed = allowed
        diffs = {path: _polarity_diff(path) for path in changed}
        auth = _active_grant(allowed, diffs, required_runtime_paths=[RUNTIME_PATH])
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_MAPPING_BIND_EXCLUDED_PATH in report.reason_codes

    def test_required_runtime_path_missing_from_diff_blocks(self) -> None:
        allowed = [RUNTIME_PATH, SPEC_PATH]
        changed = [SPEC_PATH]
        diffs = {SPEC_PATH: _polarity_diff(SPEC_PATH)}
        auth = _active_grant(allowed, diffs)
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_MAPPING_BIND_REQUIRED_RUNTIME_MISSING in report.reason_codes

    def test_required_runtime_path_not_in_allowed_paths_blocks(self) -> None:
        diffs = {SPEC_PATH: _polarity_diff(SPEC_PATH)}
        auth = _active_grant(
            [SPEC_PATH],
            diffs,
            required_runtime_paths=[RUNTIME_PATH],
        )
        valid, reasons = validate_mapping_bind_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_MAPPING_BIND_AUTH_INVALID in reasons
        assert "MAPPING_BIND_REQUIRED_RUNTIME_NOT_IN_ALLOWED_PATHS" in reasons
        report = _report([SPEC_PATH], auth=auth, diffs=diffs)
        assert report.admissible is False
        assert report.productive_mapping_contract_runtime_bind_authorization_applied is False

    def test_glob_in_path_blocks(self) -> None:
        diffs = {RUNTIME_PATH: _polarity_diff(RUNTIME_PATH)}
        auth = _active_grant([RUNTIME_PATH], diffs)
        auth["allowed_paths"] = ["src/trading/master_v2/*.py"]
        valid, reasons = validate_mapping_bind_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert "MAPPING_BIND_ALLOWED_PATHS_NOT_EXACT_FILES" in reasons

    def test_directory_grant_blocks(self) -> None:
        diffs = {RUNTIME_PATH: _polarity_diff(RUNTIME_PATH)}
        auth = _active_grant([RUNTIME_PATH], diffs)
        auth["allowed_paths"] = ["src/trading/master_v2/"]
        valid, reasons = validate_mapping_bind_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert "MAPPING_BIND_ALLOWED_PATHS_NOT_EXACT_FILES" in reasons

    def test_unknown_json_key_blocks(self) -> None:
        diffs = {RUNTIME_PATH: _polarity_diff(RUNTIME_PATH), SPEC_PATH: _polarity_diff(SPEC_PATH)}
        auth = _active_grant([RUNTIME_PATH, SPEC_PATH], diffs)
        auth["unexpected_owner_field"] = True
        valid, reasons = validate_mapping_bind_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_MAPPING_BIND_UNKNOWN_FIELD in reasons
        report = _report([RUNTIME_PATH, SPEC_PATH], auth=auth, diffs=diffs)
        assert report.admissible is False

    def test_wrong_purpose_blocks(self) -> None:
        diffs = {RUNTIME_PATH: _polarity_diff(RUNTIME_PATH), SPEC_PATH: _polarity_diff(SPEC_PATH)}
        auth = _active_grant([RUNTIME_PATH, SPEC_PATH], diffs)
        auth["mutation_purpose_class"] = "OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE"
        valid, reasons = validate_mapping_bind_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert "MAPPING_BIND_MUTATION_PURPOSE_MISMATCH" in reasons

    def test_wiring_purpose_in_new_class_blocks(self) -> None:
        diffs = {RUNTIME_PATH: _polarity_diff(RUNTIME_PATH), SPEC_PATH: _polarity_diff(SPEC_PATH)}
        auth = _active_grant([RUNTIME_PATH, SPEC_PATH], diffs)
        auth["mutation_purpose_class"] = "SEMANTICS_NEUTRAL_TECHNICAL_CANONICAL_WIRING"
        valid, reasons = validate_mapping_bind_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert "MAPPING_BIND_WIRING_PURPOSE_FORBIDDEN" in reasons
        assert "MAPPING_BIND_MUTATION_PURPOSE_MISMATCH" in reasons

    def test_pr_number_in_json_blocks(self) -> None:
        diffs = {RUNTIME_PATH: _polarity_diff(RUNTIME_PATH), SPEC_PATH: _polarity_diff(SPEC_PATH)}
        auth = _active_grant([RUNTIME_PATH, SPEC_PATH], diffs)
        auth["notes"] = list(auth["notes"]) + ["temporary exception for PR #9999"]
        valid, reasons = validate_mapping_bind_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert "MAPPING_BIND_PR_OR_BRANCH_HARDCODE" in reasons

    def test_branch_hardcode_blocks(self) -> None:
        diffs = {RUNTIME_PATH: _polarity_diff(RUNTIME_PATH), SPEC_PATH: _polarity_diff(SPEC_PATH)}
        auth = _active_grant([RUNTIME_PATH, SPEC_PATH], diffs)
        auth["notes"] = list(auth["notes"]) + ["cursor/feature-mapping-bind"]
        valid, reasons = validate_mapping_bind_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert "MAPPING_BIND_PR_OR_BRANCH_HARDCODE" in reasons

    def test_grant_active_true_with_empty_paths_blocks(self) -> None:
        auth = _inactive_grant()
        auth["grant_active"] = True
        auth["allowed_surface_classes"] = [MAPPING_BIND_SCOPE_CLASS]
        auth["slice_grant_id"] = FIXTURE_SLICE_GRANT_ID
        auth["bound_diff_base_sha"] = TEST_DIFF_BASE_SHA
        auth["authorized_evidence_digest"] = "a" * 64
        valid, reasons = validate_mapping_bind_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert "MAPPING_BIND_ALLOWED_PATHS_EMPTY_WHILE_ACTIVE" in reasons
        assert "MAPPING_BIND_REQUIRED_RUNTIME_PATHS_EMPTY_WHILE_ACTIVE" in reasons

    def test_grant_active_false_with_nonempty_paths_blocks(self) -> None:
        auth = _inactive_grant()
        auth["allowed_paths"] = [RUNTIME_PATH]
        valid, reasons = validate_mapping_bind_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert "MAPPING_BIND_ALLOWED_PATHS_NONEMPTY_WHILE_INACTIVE" in reasons

    def test_wrong_canonicalization_blocks(self) -> None:
        diffs = {RUNTIME_PATH: _polarity_diff(RUNTIME_PATH), SPEC_PATH: _polarity_diff(SPEC_PATH)}
        auth = _active_grant([RUNTIME_PATH, SPEC_PATH], diffs)
        auth["evidence_digest_canonicalization"] = "other_canonicalization_v1"
        valid, reasons = validate_mapping_bind_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert "MAPPING_BIND_DIGEST_CANONICALIZATION_INVALID" in reasons

    def test_wrong_digest_algorithm_blocks(self) -> None:
        diffs = {RUNTIME_PATH: _polarity_diff(RUNTIME_PATH), SPEC_PATH: _polarity_diff(SPEC_PATH)}
        auth = _active_grant([RUNTIME_PATH, SPEC_PATH], diffs)
        auth["evidence_digest_algorithm"] = "sha1"
        valid, reasons = validate_mapping_bind_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert "MAPPING_BIND_DIGEST_ALGORITHM_INVALID" in reasons

    def test_master_v2_mutation_allowed_true_blocks(self) -> None:
        diffs = {RUNTIME_PATH: _polarity_diff(RUNTIME_PATH), SPEC_PATH: _polarity_diff(SPEC_PATH)}
        auth = _active_grant([RUNTIME_PATH, SPEC_PATH], diffs)
        auth["MASTER_V2_MUTATION_ALLOWED"] = True
        valid, reasons = validate_mapping_bind_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_MAPPING_BIND_UNKNOWN_FIELD in reasons
        assert "MAPPING_BIND_IMMUTABLE_FLAG_TRUE:MASTER_V2_MUTATION_ALLOWED" in reasons

    def test_canonical_trading_logic_mutation_allowed_true_blocks(self) -> None:
        diffs = {RUNTIME_PATH: _polarity_diff(RUNTIME_PATH), SPEC_PATH: _polarity_diff(SPEC_PATH)}
        auth = _active_grant([RUNTIME_PATH, SPEC_PATH], diffs)
        auth["CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED"] = True
        valid, reasons = validate_mapping_bind_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_MAPPING_BIND_UNKNOWN_FIELD in reasons
        assert (
            "MAPPING_BIND_IMMUTABLE_FLAG_TRUE:CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED" in reasons
        )

    def test_does_not_consume_unclassified_nonproductive_paths(self) -> None:
        probe = "src/research/unknown_mapping_bind_probe_v1.py"
        changed = [RUNTIME_PATH, SPEC_PATH, probe]
        diffs = {path: _polarity_diff(path) for path in changed}
        auth = _active_grant([RUNTIME_PATH, SPEC_PATH], diffs)
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False
        assert report.impact_unknown is True
        assert report.productive_mapping_contract_runtime_bind_authorization_applied is False

    def test_forbidden_execution_prefix_blocks_even_if_listed(self) -> None:
        allowed = [RUNTIME_PATH, SPEC_PATH, EXECUTION_PREFIX_PATH]
        changed = allowed
        diffs = {path: _polarity_diff(path) for path in changed}
        auth = _active_grant(allowed, diffs, required_runtime_paths=[RUNTIME_PATH])
        report = _report(changed, auth=auth, diffs=diffs)
        assert report.admissible is False


class TestMappingBindGlobalMutationFlagsRemainFalseV1:
    def test_master_v2_mutation_allowed_is_false(self) -> None:
        contract = load_contract(REPO_ROOT)
        assert contract["immutable_flags"]["MASTER_V2_MUTATION_ALLOWED"] is False

    def test_canonical_trading_logic_mutation_allowed_is_false(self) -> None:
        contract = load_contract(REPO_ROOT)
        assert contract["immutable_flags"]["CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED"] is False


class TestExistingAuthorizationSemanticsUnchangedWithMappingBindClassV1:
    def test_technical_wiring_semantics_unchanged(self) -> None:
        auth = load_technical_wiring_authorization(REPO_ROOT)
        assert auth is not None
        valid, reasons = validate_technical_wiring_authorization(auth)
        assert valid is True
        assert reasons == ()
        assert auth["authorized_scope_class"] == TECHNICAL_WIRING_SCOPE_CLASS
        assert auth["mutation_purpose_class"] == TECHNICAL_WIRING_MUTATION_PURPOSE
        assert auth["contract_version"] == TECHNICAL_WIRING_AUTH_VERSION
        report = build_boundary_report(
            AUTHORIZED_TECHNICAL_WIRING_FIXTURE,
            repo_root=REPO_ROOT,
        )
        assert report.admissible is True
        assert report.technical_wiring_authorization_applied is True
        assert report.restoration_authorization_applied is False
        assert report.semantics_neutral_decommission_authorization_applied is False
        assert report.owner_adjudicated_nonproductive_contract_change_authorization_applied is False
        assert report.productive_mapping_contract_runtime_bind_authorization_applied is False
        assert "TECHNICAL_CANONICAL_WIRING_AUTHORIZED" in report.reason_codes
        assert REASON_MAPPING_BIND_AUTHORIZED not in report.reason_codes

    def test_restoration_semantics_unchanged(self) -> None:
        auth = load_restoration_authorization(REPO_ROOT)
        assert auth is not None
        valid, reasons = validate_restoration_authorization(auth, repo_root=REPO_ROOT)
        assert valid is True
        assert reasons == ()
        assert auth["authorized_scope_class"] == RESTORATION_SCOPE_CLASS
        assert auth["mutation_purpose_class"] == RESTORATION_MUTATION_PURPOSE
        assert auth["contract_version"] == RESTORATION_AUTH_VERSION
        report = build_boundary_report(
            COMMITTED_SLICE_GRANT_PATHS,
            repo_root=REPO_ROOT,
        )
        assert report.admissible is True
        assert report.restoration_authorization_applied is True
        assert report.technical_wiring_authorization_applied is False
        assert report.semantics_neutral_decommission_authorization_applied is False
        assert report.owner_adjudicated_nonproductive_contract_change_authorization_applied is False
        assert report.productive_mapping_contract_runtime_bind_authorization_applied is False
        assert REASON_MAPPING_BIND_AUTHORIZED not in report.reason_codes

    def test_decommission_and_owner_classes_remain_valid(self) -> None:
        decommission = load_decommission_authorization(REPO_ROOT)
        owner = load_owner_adjudication_authorization(REPO_ROOT)
        assert decommission is not None
        assert owner is not None
        decommission_valid, _ = validate_decommission_authorization(
            decommission, repo_root=REPO_ROOT
        )
        owner_valid, _ = validate_owner_adjudication_authorization(owner, repo_root=REPO_ROOT)
        assert decommission_valid is True
        assert owner_valid is True
        assert decommission["authorized_scope_class"] == DECOMMISSION_SCOPE_CLASS
        assert decommission["mutation_purpose_class"] == DECOMMISSION_MUTATION_PURPOSE
        assert decommission["contract_version"] == DECOMMISSION_AUTH_VERSION


class TestMappingBindLocalPr6274ProofOptionalV1:
    def test_in_memory_active_grant_against_bound_head_if_present(self) -> None:
        if not _sha_exists(PR_6274_HEAD_SHA):
            return
        base = subprocess.run(
            ["git", "merge-base", "origin/main", PR_6274_HEAD_SHA],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        names = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...{PR_6274_HEAD_SHA}"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        changed = [line.strip() for line in names if line.strip()]
        report_before = build_boundary_report(
            changed,
            repo_root=REPO_ROOT,
            skip_mapping_bind_authorization=True,
        )
        assert report_before.admissible is False
        diffs: dict[str, str] = {}
        for path in changed:
            result = subprocess.run(
                ["git", "diff", "-U20", f"{base}...{PR_6274_HEAD_SHA}", "--", path],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            diffs[path] = result.stdout if result.returncode == 0 else ""
        blocking = sorted({match.matched_path for match in report_before.forbidden_surface_matches})
        required = [path for path in REQUIRED_RUNTIME_PATHS if path in blocking]
        assert required == list(REQUIRED_RUNTIME_PATHS)
        auth = _active_grant(blocking, diffs, required_runtime_paths=required, diff_base_sha=base)
        report = build_boundary_report(
            changed,
            repo_root=REPO_ROOT,
            mapping_bind_authorization=auth,
            file_diffs=diffs,
            diff_base_sha=base,
        )
        assert report.admissible is True
        assert report.canonical_trading_semantics_changed is True
        assert report.productive_mapping_contract_runtime_bind_authorization_applied is True
        assert report.technical_wiring_authorization_applied is False
        assert report.restoration_authorization_applied is False
        assert report.semantics_neutral_decommission_authorization_applied is False
        assert REASON_MAPPING_BIND_AUTHORIZED in report.reason_codes
        assert load_contract(REPO_ROOT)["immutable_flags"]["MASTER_V2_MUTATION_ALLOWED"] is False
        assert (
            load_contract(REPO_ROOT)["immutable_flags"]["CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED"]
            is False
        )
