"""Semantics-neutral decommission authorization bound to the economic boundary guard."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from src.governance.economic_diagnostic_optimization_boundary_v0 import (
    REASON_IMPACT_UNKNOWN,
    REASON_RESTORATION_AUTHORIZED,
    RESTORATION_AUTH_VERSION,
    RESTORATION_MUTATION_PURPOSE,
    RESTORATION_SCOPE_CLASS,
    TECHNICAL_WIRING_AUTH_VERSION,
    TECHNICAL_WIRING_MUTATION_PURPOSE,
    TECHNICAL_WIRING_SCOPE_CLASS,
    build_boundary_report,
    forbidden_surface_changed_count,
    load_contract,
    load_decommission_authorization,
    load_restoration_authorization,
    load_technical_wiring_authorization,
    validate_decommission_authorization,
    validate_restoration_authorization,
    validate_technical_wiring_authorization,
)
from src.governance.semantics_neutral_decommission_authorization_v1 import (
    DECOMMISSION_AUTH_VERSION,
    DECOMMISSION_AUTHORIZATION_ID,
    DECOMMISSION_CLASS_ATTESTATION_RELATIVE,
    DECOMMISSION_MUTATION_PURPOSE,
    DECOMMISSION_SCOPE_CLASS,
    EVIDENCE_DIGEST_ALGORITHM,
    EVIDENCE_DIGEST_CANONICALIZATION,
    REASON_DECOMMISSION_AUTH_INVALID,
    REASON_DECOMMISSION_AUTH_VALID,
    REASON_DECOMMISSION_AUTHORIZED,
    REASON_DECOMMISSION_DIGEST_MALFORMED,
    REASON_DECOMMISSION_DIGEST_MISSING,
    REASON_DECOMMISSION_DIGEST_MISMATCH,
    REASON_DECOMMISSION_EVIDENCE_INSUFFICIENT,
    REASON_DECOMMISSION_PATH_UNAUTHORIZED,
    REASON_DECOMMISSION_SEMANTIC_CHANGE,
    classify_decommission_diff,
    compute_decommission_evidence_digest,
)
from tests.governance.test_historically_attested_current_system_semantic_restoration_authorization_v1 import (
    COMMITTED_SLICE_GRANT_PATHS,
)
from tests.governance.test_technical_canonical_wiring_authorization_bound_to_boundary_guard_v1 import (
    AUTHORIZED_TECHNICAL_WIRING_FIXTURE,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
AUTH_PATH = REPO_ROOT / "config/governance/semantics_neutral_decommission_authorization_v1.json"

PROTECTED_PROMOTION_PATH = "src/governance/promotion_loop/safety.py"
PROTECTED_PROMOTION_TEST_PATH = "tests/governance/promotion_loop/test_safety_manifest_era_v1.py"
PROTECTED_MASTER_V2_PATH = (
    "src/trading/master_v2/pr4985_runtime_activation_materiality_classifier_v0.py"
)
PROTECTED_MASTER_V2_TEST_PATH = (
    "tests/trading/master_v2/test_pr4985_runtime_activation_materiality_classifier_v0.py"
)
PROTECTED_VOLATILITY_TEST_PATH = (
    "tests/trading/master_v2/test_canonical_volatility_typed_runtime_producer_scaffold_v1.py"
)
UNGRANTED_MASTER_V2_PATH = "src/trading/master_v2/survival_assessment_v1.py"
DELETED_COMPONENT_PATH = "src/exchange/deleted_component_absent_v0.py"

MASTER_V2_SURFACE = "MASTER_V2"
PROMOTION_SURFACE = "PROMOTION_RUNTIME_ORDER_CREDENTIAL_SCHEDULER_AUTHORITY"

REPLAY_TOUCHES = (
    PROTECTED_MASTER_V2_PATH,
    PROTECTED_MASTER_V2_TEST_PATH,
    PROTECTED_VOLATILITY_TEST_PATH,
    PROTECTED_PROMOTION_PATH,
    PROTECTED_PROMOTION_TEST_PATH,
)


def _load_auth() -> dict:
    payload = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


TEST_DIFF_BASE_SHA = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
OTHER_DIFF_BASE_SHA = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def _active_grant(
    allowed_paths: list[str],
    surface_classes: list[str],
    diffs: dict[str, str] | None = None,
    *,
    diff_base_sha: str = TEST_DIFF_BASE_SHA,
) -> dict:
    auth = copy.deepcopy(_load_auth())
    auth["grant_active"] = True
    auth["allowed_paths"] = list(allowed_paths)
    auth["allowed_surface_classes"] = list(surface_classes)
    auth["authorized_evidence_digest"] = compute_decommission_evidence_digest(
        file_diffs=diffs or {},
        diff_base_sha=diff_base_sha,
        paths=allowed_paths,
    )
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


def _report(
    changed: list[str],
    *,
    auth: dict | None = None,
    diffs: dict[str, str] | None = None,
    evidence_repo_root: Path | None = None,
    skip_decommission: bool = False,
    diff_base_sha: str | None = TEST_DIFF_BASE_SHA,
) -> object:
    return build_boundary_report(
        changed,
        repo_root=REPO_ROOT,
        decommission_authorization=auth,
        skip_decommission_authorization=skip_decommission,
        file_diffs=diffs,
        evidence_repo_root=evidence_repo_root,
        diff_base_sha=diff_base_sha,
    )


class TestDecommissionAdmissionClassContractV1:
    def test_committed_artifact_is_valid_digest_bound_grant(self) -> None:
        auth = load_decommission_authorization(REPO_ROOT)
        assert auth is not None
        valid, reasons = validate_decommission_authorization(auth, repo_root=REPO_ROOT)
        assert valid is True
        assert reasons == (REASON_DECOMMISSION_AUTH_VALID,)
        assert auth["contract_version"] == DECOMMISSION_AUTH_VERSION
        assert auth["authorized_scope_class"] == DECOMMISSION_SCOPE_CLASS
        assert auth["authorization_token"] == DECOMMISSION_AUTHORIZATION_ID
        assert auth["mutation_purpose_class"] == DECOMMISSION_MUTATION_PURPOSE
        assert auth["pr_specific_exception"] is False
        assert auth["branch_specific_exception"] is False
        assert auth["blanket_allowlist"] is False
        assert auth["directory_grant"] is False
        assert auth["broad_master_v2_grant"] is False
        assert auth["evidence_digest_algorithm"] == EVIDENCE_DIGEST_ALGORITHM
        assert auth["evidence_digest_canonicalization"] == EVIDENCE_DIGEST_CANONICALIZATION
        assert "pr_number" not in auth
        assert "branch_name" not in auth
        assert auth["class_attestation"] == DECOMMISSION_CLASS_ATTESTATION_RELATIVE
        assert (REPO_ROOT / DECOMMISSION_CLASS_ATTESTATION_RELATIVE).is_file()
        if auth["grant_active"] is False:
            assert auth["allowed_paths"] == []
            assert auth["allowed_surface_classes"] == []
            assert auth["authorized_evidence_digest"] == ""
        else:
            assert auth["allowed_paths"]
            assert all("/" in path and "*" not in path for path in auth["allowed_paths"])
            assert len(auth["authorized_evidence_digest"]) == 64

    def test_bound_from_boundary_contract(self) -> None:
        contract = load_contract(REPO_ROOT)
        assert (
            contract["semantics_neutral_decommission_authorization"]
            == "config/governance/semantics_neutral_decommission_authorization_v1.json"
        )
        assert contract["immutable_flags"]["MASTER_V2_MUTATION_ALLOWED"] is False

    def test_token_alone_is_insufficient(self) -> None:
        token_only = {
            "authorization_token": DECOMMISSION_AUTHORIZATION_ID,
            "contract_version": DECOMMISSION_AUTH_VERSION,
        }
        valid, reasons = validate_decommission_authorization(token_only, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_DECOMMISSION_AUTH_INVALID in reasons


class TestDecommissionGuardMatrixV1:
    def test_protected_surface_without_authorization_blocks(self) -> None:
        report = _report([PROTECTED_PROMOTION_PATH])
        assert report.admissible is False
        assert report.fail_closed is True
        assert report.semantics_neutral_decommission_authorization_applied is False
        assert "FORBIDDEN_MUTATION_SURFACE_MATCH" in report.reason_codes
        assert forbidden_surface_changed_count(report) >= 1

    def test_wrong_authorization_class_blocks(self) -> None:
        wiring = load_technical_wiring_authorization(REPO_ROOT)
        assert wiring is not None
        report = _report(
            [PROTECTED_PROMOTION_PATH],
            auth=copy.deepcopy(wiring),
            diffs={
                PROTECTED_PROMOTION_PATH: _unified_diff(
                    PROTECTED_PROMOTION_PATH,
                    ['    "src/exchange/deleted_component_absent_v0.py",'],
                    [],
                )
            },
        )
        assert report.admissible is False
        assert report.semantics_neutral_decommission_authorization_applied is False
        assert REASON_DECOMMISSION_AUTH_INVALID in report.reason_codes

    def test_malformed_decommission_authorization_blocks(self) -> None:
        auth = _active_grant([PROTECTED_PROMOTION_PATH], [PROMOTION_SURFACE])
        auth["contract_version"] = "wrong_version"
        report = _report(
            [PROTECTED_PROMOTION_PATH],
            auth=auth,
            diffs={
                PROTECTED_PROMOTION_PATH: _unified_diff(
                    PROTECTED_PROMOTION_PATH,
                    ['    "src/exchange/deleted_component_absent_v0.py",'],
                    [],
                )
            },
        )
        assert report.admissible is False
        assert REASON_DECOMMISSION_AUTH_INVALID in report.reason_codes
        assert report.semantics_neutral_decommission_authorization_applied is False

    def test_semantics_neutral_claim_with_trading_behavior_change_blocks(
        self, tmp_path: Path
    ) -> None:
        diffs = {
            PROTECTED_MASTER_V2_PATH: _unified_diff(
                PROTECTED_MASTER_V2_PATH,
                ["    return False"],
                ["    return True"],
            )
        }
        auth = _active_grant([PROTECTED_MASTER_V2_PATH], [MASTER_V2_SURFACE], diffs)
        report = _report(
            [PROTECTED_MASTER_V2_PATH],
            auth=auth,
            diffs=diffs,
            evidence_repo_root=tmp_path,
        )
        assert report.admissible is False
        assert REASON_DECOMMISSION_SEMANTIC_CHANGE in report.reason_codes
        assert report.semantics_neutral_decommission_authorization_applied is False

    def test_productive_reachability_increase_blocks(self, tmp_path: Path) -> None:
        diffs = {
            PROTECTED_PROMOTION_PATH: _unified_diff(
                PROTECTED_PROMOTION_PATH,
                ["    mode = 'manual_only'"],
                ["    LIVE_AUTHORIZED = True"],
            )
        }
        auth = _active_grant([PROTECTED_PROMOTION_PATH], [PROMOTION_SURFACE], diffs)
        report = _report(
            [PROTECTED_PROMOTION_PATH],
            auth=auth,
            diffs=diffs,
            evidence_repo_root=tmp_path,
        )
        assert report.admissible is False
        assert REASON_DECOMMISSION_SEMANTIC_CHANGE in report.reason_codes

    def test_fail_closed_weakening_blocks(self, tmp_path: Path) -> None:
        diffs = {
            PROTECTED_PROMOTION_PATH: _unified_diff(
                PROTECTED_PROMOTION_PATH,
                ['    raise RuntimeError("denied")'],
                ["    pass"],
            )
        }
        auth = _active_grant([PROTECTED_PROMOTION_PATH], [PROMOTION_SURFACE], diffs)
        report = _report(
            [PROTECTED_PROMOTION_PATH],
            auth=auth,
            diffs=diffs,
            evidence_repo_root=tmp_path,
        )
        assert report.admissible is False
        assert REASON_DECOMMISSION_SEMANTIC_CHANGE in report.reason_codes

    def test_assert_identifier_retokenization_is_not_fail_closed_weakening(self) -> None:
        diffs = {
            PROTECTED_PROMOTION_TEST_PATH: _unified_diff(
                PROTECTED_PROMOTION_TEST_PATH,
                ["    assert okx.instrument_id != binance.instrument_id"],
                ["    assert okx.instrument_id != other.instrument_id"],
            )
        }
        auth = _active_grant([PROTECTED_PROMOTION_TEST_PATH], [PROMOTION_SURFACE], diffs)
        report = _report([PROTECTED_PROMOTION_TEST_PATH], auth=auth, diffs=diffs)
        assert report.admissible is True
        assert report.semantics_neutral_decommission_authorization_applied is True
        assert "NEGATIVE_TEST_TOKEN_NEUTRALIZED" in (
            report.semantics_neutral_decommission_proven_predicates
        )

    def test_assert_true_substitution_still_blocks(self) -> None:
        diffs = {
            PROTECTED_PROMOTION_TEST_PATH: _unified_diff(
                PROTECTED_PROMOTION_TEST_PATH,
                ["    assert not live_authorized"],
                ["    assert True"],
            )
        }
        auth = _active_grant([PROTECTED_PROMOTION_TEST_PATH], [PROMOTION_SURFACE], diffs)
        report = _report([PROTECTED_PROMOTION_TEST_PATH], auth=auth, diffs=diffs)
        assert report.admissible is False
        assert report.semantics_neutral_decommission_authorization_applied is False

    def test_deleted_obsolete_reference_with_valid_evidence_passes(self, tmp_path: Path) -> None:
        diffs = {
            PROTECTED_MASTER_V2_PATH: _unified_diff(
                PROTECTED_MASTER_V2_PATH,
                [f'    "{DELETED_COMPONENT_PATH}",'],
                [],
            )
        }
        auth = _active_grant([PROTECTED_MASTER_V2_PATH], [MASTER_V2_SURFACE], diffs)
        report = _report(
            [PROTECTED_MASTER_V2_PATH],
            auth=auth,
            diffs=diffs,
            evidence_repo_root=tmp_path,
        )
        assert report.admissible is True
        assert report.fail_closed is False
        assert report.semantics_neutral_decommission_authorization_applied is True
        assert REASON_DECOMMISSION_AUTHORIZED in report.reason_codes
        assert report.canonical_trading_semantics_changed is False
        assert forbidden_surface_changed_count(report) == 0
        assert "REMOVED_TARGET_NO_LONGER_EXISTS" in (
            report.semantics_neutral_decommission_proven_predicates
        )

    def test_negative_test_token_neutralized_still_fail_closed_passes(self) -> None:
        diffs = {
            PROTECTED_PROMOTION_TEST_PATH: _unified_diff(
                PROTECTED_PROMOTION_TEST_PATH,
                ['    candidate = _candidate(target="foreign_literal")'],
                ['    candidate = _candidate(target="other_venue")'],
            )
        }
        auth = _active_grant([PROTECTED_PROMOTION_TEST_PATH], [PROMOTION_SURFACE], diffs)
        report = _report(
            [PROTECTED_PROMOTION_TEST_PATH],
            auth=auth,
            diffs=diffs,
        )
        assert report.admissible is True
        assert report.semantics_neutral_decommission_authorization_applied is True
        assert "NEGATIVE_TEST_TOKEN_NEUTRALIZED" in (
            report.semantics_neutral_decommission_proven_predicates
        )
        remaining = (REPO_ROOT / PROTECTED_PROMOTION_TEST_PATH).read_text(encoding="utf-8")
        assert "assert" in remaining

    def test_reference_removed_for_absent_target_passes(self, tmp_path: Path) -> None:
        diffs = {
            PROTECTED_MASTER_V2_TEST_PATH: _unified_diff(
                PROTECTED_MASTER_V2_TEST_PATH,
                [f'        "{DELETED_COMPONENT_PATH}",'],
                [],
            )
        }
        auth = _active_grant([PROTECTED_MASTER_V2_TEST_PATH], [MASTER_V2_SURFACE], diffs)
        report = _report(
            [PROTECTED_MASTER_V2_TEST_PATH],
            auth=auth,
            diffs=diffs,
            evidence_repo_root=tmp_path,
        )
        assert report.admissible is True
        proven = report.semantics_neutral_decommission_proven_predicates
        assert "DELETED_COMPONENT_REFERENCE_REMOVED" in proven
        assert "REMOVED_TARGET_NO_LONGER_EXISTS" in proven

    def test_blanket_directory_grant_blocks(self) -> None:
        auth = _active_grant(["src/trading/master_v2/**"], [MASTER_V2_SURFACE])
        valid, reasons = validate_decommission_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert "DECOMMISSION_BROAD_MASTER_V2_GRANT" in reasons
        report = _report([PROTECTED_MASTER_V2_PATH], auth=auth)
        assert report.admissible is False
        assert REASON_DECOMMISSION_AUTH_INVALID in report.reason_codes

    def test_pr_specific_exception_field_blocks(self) -> None:
        auth = _active_grant([PROTECTED_PROMOTION_PATH], [PROMOTION_SURFACE])
        auth["pr_specific_exception"] = True
        valid, reasons = validate_decommission_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert any("pr_specific_exception" in item for item in reasons)
        report = _report([PROTECTED_PROMOTION_PATH], auth=auth)
        assert report.admissible is False
        assert REASON_DECOMMISSION_AUTH_INVALID in report.reason_codes

    def test_branch_specific_exception_field_blocks(self) -> None:
        auth = _active_grant([PROTECTED_PROMOTION_PATH], [PROMOTION_SURFACE])
        auth["branch_specific_exception"] = True
        valid, reasons = validate_decommission_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        report = _report([PROTECTED_PROMOTION_PATH], auth=auth)
        assert report.admissible is False
        assert REASON_DECOMMISSION_AUTH_INVALID in report.reason_codes

    def test_branch_name_hardcode_blocks(self) -> None:
        auth = _active_grant([PROTECTED_PROMOTION_PATH], [PROMOTION_SURFACE])
        auth["branch_name"] = "cursor/example-decommission"
        valid, reasons = validate_decommission_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert "DECOMMISSION_PR_OR_BRANCH_HARDCODE" in reasons

    def test_active_grant_without_diffs_is_evidence_insufficient(self) -> None:
        auth = _active_grant([PROTECTED_PROMOTION_PATH], [PROMOTION_SURFACE])
        report = _report([PROTECTED_PROMOTION_PATH], auth=auth)
        assert report.admissible is False
        assert REASON_DECOMMISSION_EVIDENCE_INSUFFICIENT in report.reason_codes

    def test_path_outside_exact_allowlist_blocks(self, tmp_path: Path) -> None:
        diffs = {
            UNGRANTED_MASTER_V2_PATH: _unified_diff(
                UNGRANTED_MASTER_V2_PATH,
                [f'    "{DELETED_COMPONENT_PATH}",'],
                [],
            )
        }
        auth = _active_grant([PROTECTED_PROMOTION_PATH], [PROMOTION_SURFACE], diffs)
        report = _report(
            [UNGRANTED_MASTER_V2_PATH],
            auth=auth,
            diffs=diffs,
            evidence_repo_root=tmp_path,
        )
        assert report.admissible is False
        assert REASON_DECOMMISSION_PATH_UNAUTHORIZED in report.reason_codes

    def test_whole_file_delete_does_not_auto_pass(self, tmp_path: Path) -> None:
        diffs = {
            PROTECTED_MASTER_V2_PATH: _unified_diff(
                PROTECTED_MASTER_V2_PATH,
                ["def classify_runtime_activation_materiality_v0():", "    return 1"],
                [],
            )
        }
        auth = _active_grant([PROTECTED_MASTER_V2_PATH], [MASTER_V2_SURFACE], diffs)
        report = _report(
            [PROTECTED_MASTER_V2_PATH],
            auth=auth,
            diffs=diffs,
            evidence_repo_root=tmp_path,
        )
        assert report.admissible is False
        assert report.semantics_neutral_decommission_authorization_applied is False

    def test_unrelated_active_grant_does_not_admit_ungranted_protected_path(self) -> None:
        changed = [UNGRANTED_MASTER_V2_PATH]
        report = _report(changed)
        skipped = _report(changed, skip_decommission=True)
        assert report.admissible is False
        assert skipped.admissible is False
        assert report.restoration_authorization_applied is False
        assert skipped.restoration_authorization_applied is False
        assert report.semantics_neutral_decommission_authorization_applied is False


class TestExistingAuthorizationSemanticsUnchangedV1:
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
        assert "TECHNICAL_CANONICAL_WIRING_AUTHORIZED" in report.reason_codes
        assert REASON_DECOMMISSION_AUTHORIZED not in report.reason_codes

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
        assert report.semantics_neutral_decommission_authorization_applied is False
        assert REASON_RESTORATION_AUTHORIZED in report.reason_codes
        assert report.canonical_trading_semantics_changed is True
        assert REASON_DECOMMISSION_AUTHORIZED not in report.reason_codes


class TestGenericDecommissionReplayShapesV1:
    def test_five_cleanup_shapes_qualify_when_removed_targets_absent(self, tmp_path: Path) -> None:
        diffs = {
            PROTECTED_MASTER_V2_PATH: _unified_diff(
                PROTECTED_MASTER_V2_PATH,
                ['    "src/exchange/kraken_live.py",'],
                [],
            ),
            PROTECTED_MASTER_V2_TEST_PATH: _unified_diff(
                PROTECTED_MASTER_V2_TEST_PATH,
                ['        "src/exchange/kraken_live.py",'],
                [],
            ),
            PROTECTED_VOLATILITY_TEST_PATH: _unified_diff(
                PROTECTED_VOLATILITY_TEST_PATH,
                ['    bad = _sample(3, venue="binance")'],
                ['    bad = _sample(3, venue="other_venue")'],
            ),
            PROTECTED_PROMOTION_PATH: _unified_diff(
                PROTECTED_PROMOTION_PATH,
                [
                    '        # Support prefix matching (e.g., "live.api_keys" matches "live.api_keys.binance")'
                ],
                ["        # Support prefix matching (e.g., nested-key example)"],
            ),
            PROTECTED_PROMOTION_TEST_PATH: _unified_diff(
                PROTECTED_PROMOTION_TEST_PATH,
                ['    candidate = _candidate(target="live.api_keys.binance")'],
                ['    candidate = _candidate(target="foreign_venue")'],
            ),
        }
        auth = _active_grant(
            list(REPLAY_TOUCHES),
            [MASTER_V2_SURFACE, PROMOTION_SURFACE],
            diffs,
        )
        report = _report(
            list(REPLAY_TOUCHES),
            auth=auth,
            diffs=diffs,
            evidence_repo_root=tmp_path,
        )
        assert len(REPLAY_TOUCHES) == 5
        assert report.admissible is True
        assert report.semantics_neutral_decommission_authorization_applied is True
        assert report.canonical_trading_semantics_changed is False
        assert report.master_v2_changed is False
        assert report.double_play_changed is False
        assert forbidden_surface_changed_count(report) == 0
        proven = set(report.semantics_neutral_decommission_proven_predicates)
        assert proven.intersection(
            {
                "DELETED_COMPONENT_REFERENCE_REMOVED",
                "REMOVED_TARGET_NO_LONGER_EXISTS",
                "NEGATIVE_TEST_TOKEN_NEUTRALIZED",
                "NONCANONICAL_LITERAL_NEUTRALIZED",
                "OBSOLETE_REFERENCE_REMOVED",
            }
        )

    def test_same_cleanup_shapes_block_when_removed_target_still_exists(self) -> None:
        diffs = {
            PROTECTED_MASTER_V2_PATH: _unified_diff(
                PROTECTED_MASTER_V2_PATH,
                ['    "src/exchange/operative_venue_boundary_v1.py",'],
                [],
            )
        }
        auth = _active_grant([PROTECTED_MASTER_V2_PATH], [MASTER_V2_SURFACE], diffs)
        report = _report(
            [PROTECTED_MASTER_V2_PATH],
            auth=auth,
            diffs=diffs,
            evidence_repo_root=REPO_ROOT,
        )
        assert report.admissible is False
        evidence = classify_decommission_diff(
            path=PROTECTED_MASTER_V2_PATH,
            diff_text=diffs[PROTECTED_MASTER_V2_PATH],
            repo_root=REPO_ROOT,
        )
        assert evidence.insufficient is True
        assert "REMOVED_PATH_STILL_EXISTS" in evidence.notes


class TestDecommissionEvidenceDigestBindingV1:
    def test_active_grant_missing_digest_blocks(self) -> None:
        auth = _active_grant([PROTECTED_PROMOTION_PATH], [PROMOTION_SURFACE])
        auth["authorized_evidence_digest"] = ""
        valid, reasons = validate_decommission_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_DECOMMISSION_DIGEST_MISSING in reasons
        report = _report([PROTECTED_PROMOTION_PATH], auth=auth)
        assert report.admissible is False
        assert REASON_DECOMMISSION_AUTH_INVALID in report.reason_codes

    def test_active_grant_malformed_digest_blocks(self) -> None:
        auth = _active_grant([PROTECTED_PROMOTION_PATH], [PROMOTION_SURFACE])
        auth["authorized_evidence_digest"] = "not-a-sha256"
        valid, reasons = validate_decommission_authorization(auth, repo_root=REPO_ROOT)
        assert valid is False
        assert REASON_DECOMMISSION_DIGEST_MALFORMED in reasons

    def test_same_path_different_diff_cannot_reuse_digest(self, tmp_path: Path) -> None:
        original = {
            PROTECTED_MASTER_V2_PATH: _unified_diff(
                PROTECTED_MASTER_V2_PATH,
                [f'    "{DELETED_COMPONENT_PATH}",'],
                [],
            )
        }
        auth = _active_grant([PROTECTED_MASTER_V2_PATH], [MASTER_V2_SURFACE], original)
        mutated = {
            PROTECTED_MASTER_V2_PATH: _unified_diff(
                PROTECTED_MASTER_V2_PATH,
                [f'    "{DELETED_COMPONENT_PATH}",'],
                ["    leftover = 1"],
            )
        }
        report = _report(
            [PROTECTED_MASTER_V2_PATH],
            auth=auth,
            diffs=mutated,
            evidence_repo_root=tmp_path,
        )
        assert report.admissible is False
        assert REASON_DECOMMISSION_DIGEST_MISMATCH in report.reason_codes
        assert report.semantics_neutral_decommission_authorization_applied is False

    def test_additional_hunk_cannot_reuse_digest(self, tmp_path: Path) -> None:
        original = {
            PROTECTED_MASTER_V2_PATH: _unified_diff(
                PROTECTED_MASTER_V2_PATH,
                [f'    "{DELETED_COMPONENT_PATH}",'],
                [],
            )
        }
        auth = _active_grant([PROTECTED_MASTER_V2_PATH], [MASTER_V2_SURFACE], original)
        extra = original[PROTECTED_MASTER_V2_PATH] + "+    extra_hunk_line = True\n"
        report = _report(
            [PROTECTED_MASTER_V2_PATH],
            auth=auth,
            diffs={PROTECTED_MASTER_V2_PATH: extra},
            evidence_repo_root=tmp_path,
        )
        assert report.admissible is False
        assert REASON_DECOMMISSION_DIGEST_MISMATCH in report.reason_codes

    def test_removed_hunk_cannot_reuse_digest(self, tmp_path: Path) -> None:
        two_hunks = (
            f"--- a/{PROTECTED_MASTER_V2_PATH}\n"
            f"+++ b/{PROTECTED_MASTER_V2_PATH}\n"
            "@@ -1,1 +1,0 @@\n"
            f'-    "{DELETED_COMPONENT_PATH}",\n'
            "@@ -10,1 +10,0 @@\n"
            '-    "src/exchange/also_deleted.py",\n'
        )
        one_hunk = _unified_diff(
            PROTECTED_MASTER_V2_PATH,
            [f'    "{DELETED_COMPONENT_PATH}",'],
            [],
        )
        auth = _active_grant(
            [PROTECTED_MASTER_V2_PATH],
            [MASTER_V2_SURFACE],
            {PROTECTED_MASTER_V2_PATH: two_hunks},
        )
        report = _report(
            [PROTECTED_MASTER_V2_PATH],
            auth=auth,
            diffs={PROTECTED_MASTER_V2_PATH: one_hunk},
            evidence_repo_root=tmp_path,
        )
        assert report.admissible is False
        assert REASON_DECOMMISSION_DIGEST_MISMATCH in report.reason_codes

    def test_additional_protected_path_cannot_reuse_grant(self, tmp_path: Path) -> None:
        diffs = {
            PROTECTED_MASTER_V2_PATH: _unified_diff(
                PROTECTED_MASTER_V2_PATH,
                [f'    "{DELETED_COMPONENT_PATH}",'],
                [],
            ),
            UNGRANTED_MASTER_V2_PATH: _unified_diff(
                UNGRANTED_MASTER_V2_PATH,
                [f'    "{DELETED_COMPONENT_PATH}",'],
                [],
            ),
        }
        auth = _active_grant([PROTECTED_MASTER_V2_PATH], [MASTER_V2_SURFACE], diffs)
        report = _report(
            [PROTECTED_MASTER_V2_PATH, UNGRANTED_MASTER_V2_PATH],
            auth=auth,
            diffs=diffs,
            evidence_repo_root=tmp_path,
        )
        assert report.admissible is False
        assert REASON_DECOMMISSION_PATH_UNAUTHORIZED in report.reason_codes

    def test_different_diff_base_cannot_reuse_digest(self, tmp_path: Path) -> None:
        diffs = {
            PROTECTED_MASTER_V2_PATH: _unified_diff(
                PROTECTED_MASTER_V2_PATH,
                [f'    "{DELETED_COMPONENT_PATH}",'],
                [],
            )
        }
        auth = _active_grant([PROTECTED_MASTER_V2_PATH], [MASTER_V2_SURFACE], diffs)
        report = _report(
            [PROTECTED_MASTER_V2_PATH],
            auth=auth,
            diffs=diffs,
            evidence_repo_root=tmp_path,
            diff_base_sha=OTHER_DIFF_BASE_SHA,
        )
        assert report.admissible is False
        assert REASON_DECOMMISSION_DIGEST_MISMATCH in report.reason_codes

    def test_path_order_and_crlf_do_not_change_digest(self) -> None:
        lf_diffs = {
            PROTECTED_MASTER_V2_PATH: _unified_diff(
                PROTECTED_MASTER_V2_PATH,
                [f'    "{DELETED_COMPONENT_PATH}",'],
                [],
            ),
            PROTECTED_PROMOTION_PATH: _unified_diff(
                PROTECTED_PROMOTION_PATH,
                ['    "src/exchange/deleted_component_absent_v0.py",'],
                [],
            ),
        }
        crlf_diffs = {path: text.replace("\n", "\r\n") for path, text in lf_diffs.items()}
        paths = [PROTECTED_PROMOTION_PATH, PROTECTED_MASTER_V2_PATH]
        first = compute_decommission_evidence_digest(
            file_diffs=lf_diffs,
            diff_base_sha=TEST_DIFF_BASE_SHA,
            paths=paths,
        )
        second = compute_decommission_evidence_digest(
            file_diffs=crlf_diffs,
            diff_base_sha=TEST_DIFF_BASE_SHA,
            paths=list(reversed(paths)),
        )
        assert first == second
        assert len(first) == 64

    def test_semantic_change_blocks_even_when_digest_matches(self, tmp_path: Path) -> None:
        diffs = {
            PROTECTED_MASTER_V2_PATH: _unified_diff(
                PROTECTED_MASTER_V2_PATH,
                ["    return False"],
                ["    return True"],
            )
        }
        auth = _active_grant([PROTECTED_MASTER_V2_PATH], [MASTER_V2_SURFACE], diffs)
        report = _report(
            [PROTECTED_MASTER_V2_PATH],
            auth=auth,
            diffs=diffs,
            evidence_repo_root=tmp_path,
        )
        assert report.admissible is False
        assert REASON_DECOMMISSION_SEMANTIC_CHANGE in report.reason_codes

    def test_json_fixture_token_neutralization_is_admissible(self, tmp_path: Path) -> None:
        fixture_path = (
            "tests/research/fixtures/pit_futures_universe_manifest_v1/valid_single_epoch.json"
        )
        remaining = tmp_path / fixture_path
        remaining.parent.mkdir(parents=True, exist_ok=True)
        remaining.write_text(
            '{"venue_id":"other_venue","research_binding_only":true}',
            encoding="utf-8",
        )
        diffs = {
            fixture_path: _unified_diff(
                fixture_path,
                ['{"venue_id":"binance_usdm","research_binding_only":true}'],
                ['{"venue_id":"other_venue","research_binding_only":true}'],
            )
        }
        auth = _active_grant([fixture_path], [], diffs)
        report = _report(
            [fixture_path],
            auth=auth,
            diffs=diffs,
            evidence_repo_root=tmp_path,
        )
        assert report.admissible is True
        assert report.semantics_neutral_decommission_authorization_applied is True
        assert "NEGATIVE_TEST_TOKEN_NEUTRALIZED" in (
            report.semantics_neutral_decommission_proven_predicates
        )

    def test_research_helper_literal_swap_is_admissible(self) -> None:
        helper = "tests/research/fixtures/pit_futures_universe_manifest_v1/fixture_builder.py"
        diffs = {
            helper: _unified_diff(
                helper,
                ['        ("binance_usdm:linear_perpetual:ADA:USDT:USDT:perp", "binance_usdm")'],
                ['        ("other_venue:linear_perpetual:ADA:USDT:USDT:perp", "other_venue")'],
            )
        }
        auth = _active_grant([helper], [], diffs)
        report = _report([helper], auth=auth, diffs=diffs, evidence_repo_root=REPO_ROOT)
        assert report.admissible is True
        assert report.semantics_neutral_decommission_authorization_applied is True

    def test_unknown_research_behavior_change_blocks_even_with_digest(self, tmp_path: Path) -> None:
        research_path = "src/research/new_listings/collectors/ccxt_ticker.py"
        diffs = {
            research_path: _unified_diff(
                research_path,
                ['        "exchange": str(ccxt_cfg.get("exchange", "kraken")),'],
                [
                    "        from src.exchange.operative_venue_boundary_v1 import assert_operative_ccxt_venue_id",
                    "        exchange_id = assert_operative_ccxt_venue_id(exchange_id)",
                ],
            )
        }
        auth = _active_grant([research_path], [], diffs)
        report = _report(
            [research_path],
            auth=auth,
            diffs=diffs,
            evidence_repo_root=tmp_path,
        )
        assert report.admissible is False
        assert report.semantics_neutral_decommission_authorization_applied is False
        assert (
            REASON_DECOMMISSION_SEMANTIC_CHANGE in report.reason_codes
            or REASON_DECOMMISSION_EVIDENCE_INSUFFICIENT in report.reason_codes
        )

    def test_ungranted_research_path_remains_impact_unknown(self, tmp_path: Path) -> None:
        fixture_path = (
            "tests/research/fixtures/pit_futures_universe_manifest_v1/valid_single_epoch.json"
        )
        research_path = "src/research/new_listings/collectors/ccxt_ticker.py"
        diffs = {
            fixture_path: _unified_diff(
                fixture_path,
                ['{"venue_id":"binance_usdm"}'],
                ['{"venue_id":"other_venue"}'],
            ),
            research_path: _unified_diff(
                research_path,
                ['        "exchange": str(ccxt_cfg.get("exchange", "kraken")),'],
                [
                    "        from src.exchange.operative_venue_boundary_v1 import assert_operative_ccxt_venue_id",
                ],
            ),
        }
        auth = _active_grant([fixture_path], [], diffs)
        report = _report(
            [fixture_path, research_path],
            auth=auth,
            diffs=diffs,
            evidence_repo_root=tmp_path,
        )
        assert report.admissible is False
        assert REASON_IMPACT_UNKNOWN in report.reason_codes
        assert report.semantics_neutral_decommission_authorization_applied is False

    def test_active_grant_for_other_files_does_not_mask_restoration(self) -> None:
        diffs = {
            PROTECTED_PROMOTION_PATH: _unified_diff(
                PROTECTED_PROMOTION_PATH,
                ['    "src/exchange/deleted_component_absent_v0.py",'],
                [],
            )
        }
        auth = _active_grant([PROTECTED_PROMOTION_PATH], [PROMOTION_SURFACE], diffs)
        report = build_boundary_report(
            COMMITTED_SLICE_GRANT_PATHS,
            repo_root=REPO_ROOT,
            decommission_authorization=auth,
            diff_base_sha=TEST_DIFF_BASE_SHA,
            file_diffs=diffs,
        )
        assert report.admissible is True
        assert report.restoration_authorization_applied is True
        assert report.semantics_neutral_decommission_authorization_applied is False
        assert REASON_RESTORATION_AUTHORIZED in report.reason_codes
