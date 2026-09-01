"""Explicit owner-adjudicated nonproductive contract-change authorization."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from src.governance.economic_diagnostic_optimization_boundary_v0 import (
    REASON_IMPACT_UNKNOWN,
    RESTORATION_AUTH_VERSION,
    RESTORATION_MUTATION_PURPOSE,
    RESTORATION_SCOPE_CLASS,
    TECHNICAL_WIRING_AUTH_VERSION,
    TECHNICAL_WIRING_MUTATION_PURPOSE,
    TECHNICAL_WIRING_SCOPE_CLASS,
    build_boundary_report,
    load_contract,
    load_decommission_authorization,
    load_owner_adjudication_authorization,
    load_restoration_authorization,
    load_technical_wiring_authorization,
    validate_decommission_authorization,
    validate_owner_adjudication_authorization,
    validate_restoration_authorization,
    validate_technical_wiring_authorization,
)
from src.governance.explicit_owner_adjudicated_nonproductive_contract_change_authorization_v1 import (
    OWNER_ADJUDICATION_AUTH_VERSION,
    OWNER_ADJUDICATION_AUTHORIZATION_ID,
    OWNER_ADJUDICATION_CLASS_ATTESTATION_RELATIVE,
    OWNER_ADJUDICATION_MUTATION_PURPOSE,
    OWNER_ADJUDICATION_SCOPE_CLASS,
    REASON_OWNER_ADJUDICATION_AUTH_INVALID,
    REASON_OWNER_ADJUDICATION_AUTH_VALID,
    REASON_OWNER_ADJUDICATION_AUTHORIZED,
    REASON_OWNER_ADJUDICATION_BASE_MISMATCH,
    REASON_OWNER_ADJUDICATION_DIGEST_MALFORMED,
    REASON_OWNER_ADJUDICATION_DIGEST_MISSING,
    REASON_OWNER_ADJUDICATION_DIGEST_MISMATCH,
    REASON_OWNER_ADJUDICATION_PATH_UNAUTHORIZED,
    REASON_OWNER_ADJUDICATION_SEMANTIC_CHANGE,
    compute_owner_adjudication_evidence_digest,
)
from src.governance.semantics_neutral_decommission_authorization_v1 import (
    DECOMMISSION_AUTH_VERSION,
    DECOMMISSION_MUTATION_PURPOSE,
    DECOMMISSION_SCOPE_CLASS,
    EVIDENCE_DIGEST_ALGORITHM,
    EVIDENCE_DIGEST_CANONICALIZATION,
    REASON_DECOMMISSION_AUTHORIZED,
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
    / "config/governance/explicit_owner_adjudicated_nonproductive_contract_change_authorization_v1.json"
)

PROBE_PATH = "src/research/new_listings/collectors/owner_adjudication_probe_v1.py"
PROBE_TEST_PATH = "tests/research/new_listings/test_owner_adjudication_probe_v1.py"
GENERIC_RESEARCH_PATH = "src/research/new_listings/runner.py"
GENERIC_TEST_PATH = "tests/research/new_listings/test_p9_normalize_ccxt_tickers.py"

TEST_DIFF_BASE_SHA = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
OTHER_DIFF_BASE_SHA = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

COMMITTED_OWNER_PATHS = (
    "src/research/new_listings/collectors/ccxt_ticker.py",
    "tests/research/new_listings/test_p8_ccxt_replay.py",
)


def _load_auth() -> dict:
    payload = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _inactive_grant() -> dict:
    auth = copy.deepcopy(_load_auth())
    auth["grant_active"] = False
    auth["allowed_paths"] = []
    auth["allowed_surface_classes"] = []
    auth["authorized_evidence_digest"] = ""
    auth["bound_diff_base_sha"] = ""
    return auth


def _active_grant(
    allowed_paths: list[str],
    diffs: dict[str, str],
    *,
    diff_base_sha: str = TEST_DIFF_BASE_SHA,
) -> dict:
    auth = copy.deepcopy(_load_auth())
    auth["grant_active"] = True
    auth["allowed_paths"] = list(allowed_paths)
    auth["allowed_surface_classes"] = [OWNER_ADJUDICATION_SCOPE_CLASS]
    auth["bound_diff_base_sha"] = diff_base_sha
    auth["authorized_evidence_digest"] = compute_owner_adjudication_evidence_digest(
        file_diffs=diffs,
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


def _hardening_diff(path: str) -> str:
    return _unified_diff(
        path,
        ['    exchange = cfg.get("exchange", "kraken")'],
        [
            '    exchange = str(cfg.get("exchange") or "")',
            "    if not exchange:",
            '        raise ValueError("exchange is required")',
        ],
    )


def _report(
    changed: list[str],
    *,
    auth: dict | None = None,
    diffs: dict[str, str] | None = None,
    skip_decommission: bool = True,
    skip_owner: bool = False,
    diff_base_sha: str | None = TEST_DIFF_BASE_SHA,
) -> object:
    return build_boundary_report(
        changed,
        repo_root=REPO_ROOT,
        owner_adjudication_authorization=auth,
        skip_owner_adjudication_authorization=skip_owner,
        skip_decommission_authorization=skip_decommission,
        file_diffs=diffs,
        diff_base_sha=diff_base_sha,
    )


class TestOwnerAdjudicationAdmissionClassContractV1:
    def test_owner_grant_inactive_blocks(self) -> None:
        diffs = {PROBE_PATH: _hardening_diff(PROBE_PATH)}
        report = _report([PROBE_PATH], auth=_inactive_grant(), diffs=diffs)
        assert report.admissible is False
        assert report.owner_adjudicated_nonproductive_contract_change_authorization_applied is False
        assert REASON_IMPACT_UNKNOWN in report.reason_codes

    def test_active_exact_grant_digest_and_predicates_pass(self) -> None:
        diffs = {PROBE_PATH: _hardening_diff(PROBE_PATH)}
        auth = _active_grant([PROBE_PATH], diffs)
        report = _report([PROBE_PATH], auth=auth, diffs=diffs)
        assert report.admissible is True
        assert report.owner_adjudicated_nonproductive_contract_change_authorization_applied is True
        assert REASON_OWNER_ADJUDICATION_AUTHORIZED in report.reason_codes
        assert report.owner_adjudicated_nonproductive_change_count == 1
        assert report.unclassified_touch_count == 0

    def test_same_path_changed_line_blocks(self) -> None:
        original = {PROBE_PATH: _hardening_diff(PROBE_PATH)}
        changed = {
            PROBE_PATH: _unified_diff(
                PROBE_PATH,
                ['    exchange = cfg.get("exchange", "kraken")'],
                ['    exchange = str(cfg.get("exchange") or "okx")'],
            )
        }
        auth = _active_grant([PROBE_PATH], original)
        report = _report([PROBE_PATH], auth=auth, diffs=changed)
        assert report.admissible is False
        assert REASON_OWNER_ADJUDICATION_DIGEST_MISMATCH in report.reason_codes

    def test_additional_hunk_blocks(self) -> None:
        original = {PROBE_PATH: _hardening_diff(PROBE_PATH)}
        extra = {
            PROBE_PATH: original[PROBE_PATH]
            + "@@ -20,1 +20,2 @@\n"
            + " context\n"
            + "+    extra = True\n"
        }
        auth = _active_grant([PROBE_PATH], original)
        report = _report([PROBE_PATH], auth=auth, diffs=extra)
        assert report.admissible is False
        assert REASON_OWNER_ADJUDICATION_DIGEST_MISMATCH in report.reason_codes

    def test_removed_replaced_hunk_blocks(self) -> None:
        original = {PROBE_PATH: _hardening_diff(PROBE_PATH)}
        replaced = {
            PROBE_PATH: _unified_diff(
                PROBE_PATH,
                ['    exchange = cfg.get("exchange", "kraken")'],
                ['    exchange = str(cfg.get("exchange") or "")'],
            )
        }
        auth = _active_grant([PROBE_PATH], original)
        report = _report([PROBE_PATH], auth=auth, diffs=replaced)
        assert report.admissible is False
        assert REASON_OWNER_ADJUDICATION_DIGEST_MISMATCH in report.reason_codes

    def test_additional_path_blocks(self) -> None:
        diffs = {
            PROBE_PATH: _hardening_diff(PROBE_PATH),
            PROBE_TEST_PATH: _hardening_diff(PROBE_TEST_PATH),
        }
        auth = _active_grant([PROBE_PATH], {PROBE_PATH: diffs[PROBE_PATH]})
        report = _report([PROBE_PATH, PROBE_TEST_PATH], auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OWNER_ADJUDICATION_PATH_UNAUTHORIZED in report.reason_codes
        assert report.owner_adjudicated_nonproductive_contract_change_authorization_applied is False

    def test_different_base_blocks(self) -> None:
        diffs = {PROBE_PATH: _hardening_diff(PROBE_PATH)}
        auth = _active_grant([PROBE_PATH], diffs, diff_base_sha=TEST_DIFF_BASE_SHA)
        report = _report(
            [PROBE_PATH],
            auth=auth,
            diffs=diffs,
            diff_base_sha=OTHER_DIFF_BASE_SHA,
        )
        assert report.admissible is False
        assert REASON_OWNER_ADJUDICATION_BASE_MISMATCH in report.reason_codes

    def test_missing_digest_blocks(self) -> None:
        diffs = {PROBE_PATH: _hardening_diff(PROBE_PATH)}
        auth = _active_grant([PROBE_PATH], diffs)
        auth["authorized_evidence_digest"] = ""
        report = _report([PROBE_PATH], auth=auth, diffs=diffs)
        assert report.admissible is False
        assert report.owner_adjudicated_nonproductive_contract_change_authorization_applied is False
        assert REASON_OWNER_ADJUDICATION_AUTH_INVALID in report.reason_codes
        assert REASON_OWNER_ADJUDICATION_DIGEST_MISSING in report.reason_codes

    def test_malformed_digest_blocks(self) -> None:
        diffs = {PROBE_PATH: _hardening_diff(PROBE_PATH)}
        auth = _active_grant([PROBE_PATH], diffs)
        auth["authorized_evidence_digest"] = "not-a-digest"
        report = _report([PROBE_PATH], auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OWNER_ADJUDICATION_DIGEST_MALFORMED in report.reason_codes

    def test_owner_approved_true_alone_does_not_pass(self) -> None:
        diffs = {PROBE_PATH: _hardening_diff(PROBE_PATH)}
        auth = _inactive_grant()
        auth["OWNER_APPROVED"] = True
        report = _report([PROBE_PATH], auth=auth, diffs=diffs)
        assert report.admissible is False
        assert report.owner_adjudicated_nonproductive_contract_change_authorization_applied is False

    def test_productive_reachability_increase_blocks(self) -> None:
        diffs = {
            PROBE_PATH: _unified_diff(
                PROBE_PATH,
                ["    return events"],
                ["    LIVE_AUTHORIZED = True", "    return events"],
            )
        }
        auth = _active_grant([PROBE_PATH], diffs)
        report = _report([PROBE_PATH], auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OWNER_ADJUDICATION_SEMANTIC_CHANGE in report.reason_codes

    def test_trading_semantic_change_blocks(self) -> None:
        diffs = {
            PROBE_PATH: _unified_diff(
                PROBE_PATH,
                ["    return events"],
                [
                    "    from src.trading.master_v2.survival_assessment_v1 import x",
                    "    return events",
                ],
            )
        }
        auth = _active_grant([PROBE_PATH], diffs)
        report = _report([PROBE_PATH], auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OWNER_ADJUDICATION_SEMANTIC_CHANGE in report.reason_codes

    def test_economic_semantic_change_blocks(self) -> None:
        diffs = {
            PROBE_PATH: _unified_diff(
                PROBE_PATH,
                ["    return events"],
                [
                    "    ECONOMIC_RESULT_MAY_NOT_JUSTIFY_CANONICAL_LOGIC_CHANGE = False",
                    "    return events",
                ],
            )
        }
        auth = _active_grant([PROBE_PATH], diffs)
        report = _report([PROBE_PATH], auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OWNER_ADJUDICATION_SEMANTIC_CHANGE in report.reason_codes

    def test_selection_semantic_change_blocks(self) -> None:
        diffs = {
            PROBE_PATH: _unified_diff(
                PROBE_PATH,
                ["    return events"],
                ["    SELECTION_AUTHORITY = True", "    return events"],
            )
        }
        auth = _active_grant([PROBE_PATH], diffs)
        report = _report([PROBE_PATH], auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OWNER_ADJUDICATION_SEMANTIC_CHANGE in report.reason_codes

    def test_risk_semantic_change_blocks(self) -> None:
        diffs = {
            PROBE_PATH: _unified_diff(
                PROBE_PATH,
                ["    return events"],
                ["    from src.risk.killswitch import arm", "    return events"],
            )
        }
        auth = _active_grant([PROBE_PATH], diffs)
        report = _report([PROBE_PATH], auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OWNER_ADJUDICATION_SEMANTIC_CHANGE in report.reason_codes

    def test_planning_semantic_change_blocks(self) -> None:
        diffs = {
            PROBE_PATH: _unified_diff(
                PROBE_PATH,
                ["    return events"],
                ["    from src.planning.scheduler import plan", "    return events"],
            )
        }
        auth = _active_grant([PROBE_PATH], diffs)
        report = _report([PROBE_PATH], auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OWNER_ADJUDICATION_SEMANTIC_CHANGE in report.reason_codes

    def test_execution_semantic_change_blocks(self) -> None:
        diffs = {
            PROBE_PATH: _unified_diff(
                PROBE_PATH,
                ["    return events"],
                ["    from src.execution.live_session import start", "    return events"],
            )
        }
        auth = _active_grant([PROBE_PATH], diffs)
        report = _report([PROBE_PATH], auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OWNER_ADJUDICATION_SEMANTIC_CHANGE in report.reason_codes

    def test_fail_closed_weakening_blocks(self) -> None:
        diffs = {
            PROBE_PATH: _unified_diff(
                PROBE_PATH,
                ['        raise ValueError("exchange is required")'],
                ["        exchange = 'okx'"],
            )
        }
        auth = _active_grant([PROBE_PATH], diffs)
        report = _report([PROBE_PATH], auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_OWNER_ADJUDICATION_SEMANTIC_CHANGE in report.reason_codes

    def test_generic_src_research_without_exact_grant_blocks(self) -> None:
        diffs = {GENERIC_RESEARCH_PATH: _hardening_diff(GENERIC_RESEARCH_PATH)}
        auth = _active_grant([PROBE_PATH], {PROBE_PATH: _hardening_diff(PROBE_PATH)})
        report = _report([GENERIC_RESEARCH_PATH], auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_IMPACT_UNKNOWN in report.reason_codes
        assert report.owner_adjudicated_nonproductive_contract_change_authorization_applied is False

    def test_generic_tests_research_without_exact_grant_blocks(self) -> None:
        diffs = {GENERIC_TEST_PATH: _hardening_diff(GENERIC_TEST_PATH)}
        auth = _active_grant([PROBE_PATH], {PROBE_PATH: _hardening_diff(PROBE_PATH)})
        report = _report([GENERIC_TEST_PATH], auth=auth, diffs=diffs)
        assert report.admissible is False
        assert REASON_IMPACT_UNKNOWN in report.reason_codes

    def test_digest_reuse_predicates(self) -> None:
        original = {PROBE_PATH: _hardening_diff(PROBE_PATH)}
        digest = compute_owner_adjudication_evidence_digest(
            file_diffs=original,
            diff_base_sha=TEST_DIFF_BASE_SHA,
            paths=[PROBE_PATH],
        )
        changed_line = {
            PROBE_PATH: original[PROBE_PATH].replace("exchange is required", "exchange missing")
        }
        extra_hunk = {PROBE_PATH: original[PROBE_PATH] + "+extra = 1\n"}
        removed_hunk = {
            PROBE_PATH: _unified_diff(
                PROBE_PATH,
                ['    exchange = cfg.get("exchange", "kraken")'],
                ['    exchange = str(cfg.get("exchange") or "")'],
            )
        }
        extra_path = {
            PROBE_PATH: original[PROBE_PATH],
            PROBE_TEST_PATH: _hardening_diff(PROBE_TEST_PATH),
        }
        assert (
            compute_owner_adjudication_evidence_digest(
                file_diffs=changed_line,
                diff_base_sha=TEST_DIFF_BASE_SHA,
                paths=[PROBE_PATH],
            )
            != digest
        )
        assert (
            compute_owner_adjudication_evidence_digest(
                file_diffs=extra_hunk,
                diff_base_sha=TEST_DIFF_BASE_SHA,
                paths=[PROBE_PATH],
            )
            != digest
        )
        assert (
            compute_owner_adjudication_evidence_digest(
                file_diffs=removed_hunk,
                diff_base_sha=TEST_DIFF_BASE_SHA,
                paths=[PROBE_PATH],
            )
            != digest
        )
        assert (
            compute_owner_adjudication_evidence_digest(
                file_diffs=extra_path,
                diff_base_sha=TEST_DIFF_BASE_SHA,
                paths=[PROBE_PATH, PROBE_TEST_PATH],
            )
            != digest
        )
        assert (
            compute_owner_adjudication_evidence_digest(
                file_diffs=original,
                diff_base_sha=OTHER_DIFF_BASE_SHA,
                paths=[PROBE_PATH],
            )
            != digest
        )


class TestOwnerAdjudicationCommittedGrantV1:
    def test_committed_artifact_is_valid_exact_two_path_grant(self) -> None:
        auth = load_owner_adjudication_authorization(REPO_ROOT)
        assert auth is not None
        valid, reasons = validate_owner_adjudication_authorization(auth, repo_root=REPO_ROOT)
        assert valid is True
        assert reasons == (REASON_OWNER_ADJUDICATION_AUTH_VALID,)
        assert auth["contract_version"] == OWNER_ADJUDICATION_AUTH_VERSION
        assert auth["authorized_scope_class"] == OWNER_ADJUDICATION_SCOPE_CLASS
        assert auth["authorization_token"] == OWNER_ADJUDICATION_AUTHORIZATION_ID
        assert auth["mutation_purpose_class"] == OWNER_ADJUDICATION_MUTATION_PURPOSE
        assert auth["TOKEN_ALONE_IS_INSUFFICIENT"] is True
        assert auth["OWNER_APPROVED_ALONE_IS_INSUFFICIENT"] is True
        assert auth["grant_active"] is True
        assert auth["allowed_paths"] == list(COMMITTED_OWNER_PATHS)
        assert auth["allowed_surface_classes"] == [OWNER_ADJUDICATION_SCOPE_CLASS]
        assert auth["authorized_path_prefixes"] == []
        assert auth["pr_specific_exception"] is False
        assert auth["directory_grant"] is False
        assert auth["blanket_allowlist"] is False
        assert "pr_number" not in auth
        assert "branch_name" not in auth
        assert auth["evidence_digest_algorithm"] == EVIDENCE_DIGEST_ALGORITHM
        assert auth["evidence_digest_canonicalization"] == EVIDENCE_DIGEST_CANONICALIZATION
        assert auth["class_attestation"] == OWNER_ADJUDICATION_CLASS_ATTESTATION_RELATIVE
        assert (REPO_ROOT / OWNER_ADJUDICATION_CLASS_ATTESTATION_RELATIVE).is_file()
        assert len(auth["authorized_evidence_digest"]) == 64
        assert len(auth["bound_diff_base_sha"]) == 40

    def test_bound_from_boundary_contract(self) -> None:
        contract = load_contract(REPO_ROOT)
        assert contract[
            "explicit_owner_adjudicated_nonproductive_contract_change_authorization"
        ] == (
            "config/governance/"
            "explicit_owner_adjudicated_nonproductive_contract_change_authorization_v1.json"
        )
        assert contract["immutable_flags"]["MASTER_V2_MUTATION_ALLOWED"] is False


class TestExistingAuthorizationSemanticsUnchangedWithOwnerClassV1:
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
        assert "TECHNICAL_CANONICAL_WIRING_AUTHORIZED" in report.reason_codes
        assert REASON_OWNER_ADJUDICATION_AUTHORIZED not in report.reason_codes

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
        assert REASON_DECOMMISSION_AUTHORIZED not in report.reason_codes
        assert REASON_OWNER_ADJUDICATION_AUTHORIZED not in report.reason_codes

    def test_decommission_semantics_unchanged(self) -> None:
        auth = load_decommission_authorization(REPO_ROOT)
        assert auth is not None
        valid, reasons = validate_decommission_authorization(auth, repo_root=REPO_ROOT)
        assert valid is True
        assert auth["authorized_scope_class"] == DECOMMISSION_SCOPE_CLASS
        assert auth["mutation_purpose_class"] == DECOMMISSION_MUTATION_PURPOSE
        assert auth["contract_version"] == DECOMMISSION_AUTH_VERSION
        diffs = {
            PROBE_PATH: _unified_diff(
                PROBE_PATH,
                ['        "exchange": str(ccxt_cfg.get("exchange", "kraken")),'],
                [
                    "        from src.exchange.operative_venue_boundary_v1 import assert_operative_ccxt_venue_id",
                    "        exchange_id = assert_operative_ccxt_venue_id(exchange_id)",
                ],
            )
        }
        decommission_grant = copy.deepcopy(auth)
        decommission_grant["grant_active"] = True
        decommission_grant["allowed_paths"] = [PROBE_PATH]
        decommission_grant["allowed_surface_classes"] = []
        decommission_grant["authorized_evidence_digest"] = (
            compute_owner_adjudication_evidence_digest(
                file_diffs=diffs,
                diff_base_sha=TEST_DIFF_BASE_SHA,
                paths=[PROBE_PATH],
            )
        )
        report = build_boundary_report(
            [PROBE_PATH],
            repo_root=REPO_ROOT,
            decommission_authorization=decommission_grant,
            skip_owner_adjudication_authorization=True,
            file_diffs=diffs,
            diff_base_sha=TEST_DIFF_BASE_SHA,
        )
        assert report.admissible is False
        assert report.semantics_neutral_decommission_authorization_applied is False
        assert report.owner_adjudicated_nonproductive_contract_change_authorization_applied is False
