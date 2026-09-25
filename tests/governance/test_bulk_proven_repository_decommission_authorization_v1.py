"""Bulk proven repository decommission authorization v1 contracts."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.bulk_proven_repository_decommission_authorization_v1 import (
    REASON_BULK_AUTHORIZED,
    REASON_BULK_BASE_SHA_MISMATCH,
    REASON_BULK_MISSING_AUTHORIZED_DELETE,
    REASON_BULK_PATH_COUNT_MISMATCH,
    REASON_BULK_SET_SHA256_MISMATCH,
    REASON_BULK_UNAUTHORIZED_DELETE,
    compute_final_static_removal_proven_set_sha256,
    evaluate_bulk_proven_repository_decommission_authorization,
)
from src.governance.economic_diagnostic_optimization_boundary_v0 import (
    build_boundary_report,
    forbidden_surface_changed_count,
    load_decommission_authorization,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BULK_AUTH_PATH = REPO_ROOT / "config/governance/bulk_proven_repository_decommission_authorization_v1.json"
EVIDENCE_PATH = (
    REPO_ROOT
    / "evidence/ops/final_repository_residual_census_and_frozen_outside_cut_probe_v1/"
    "20260925T214500Z/FINAL_STATIC_REMOVAL_PROVEN_SET_V1.json"
)
BASE_SHA = "9911495cb95776be55d32f2628cbd1c8dd702b59"


def _load_bulk_auth() -> dict:
    return json.loads(BULK_AUTH_PATH.read_text(encoding="utf-8"))


def _deleted_diff(path: str) -> str:
    return (
        f"diff --git a/{path} b/{path}\n"
        "deleted file mode 100644\n"
        f"--- a/{path}\n"
        "+++ /dev/null\n"
        "@@ -1 +0,0 @@\n"
        "-x\n"
    )


def test_removal_set_sha256_matches_evidence() -> None:
    payload = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    digest = compute_final_static_removal_proven_set_sha256(payload["paths"])
    assert digest == payload["final_static_removal_proven_set_sha256"]


def test_wrong_base_sha_denies() -> None:
    auth = _load_bulk_auth()
    decision = evaluate_bulk_proven_repository_decommission_authorization(
        ["docs/example_removed.md"],
        auth=auth,
        repo_root=REPO_ROOT,
        file_diffs={"docs/example_removed.md": _deleted_diff("docs/example_removed.md")},
        diff_base_sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    )
    assert decision.applied is False
    assert REASON_BULK_BASE_SHA_MISMATCH in decision.reason_codes


def test_wrong_path_count_denies() -> None:
    auth = _load_bulk_auth()
    auth = dict(auth)
    auth["authorized_removal_path_count"] = 1
    decision = evaluate_bulk_proven_repository_decommission_authorization(
        [],
        auth=auth,
        repo_root=REPO_ROOT,
        file_diffs={},
        diff_base_sha=BASE_SHA,
    )
    assert decision.applied is False
    assert REASON_BULK_PATH_COUNT_MISMATCH in decision.reason_codes


def test_wrong_set_sha256_denies() -> None:
    auth = _load_bulk_auth()
    auth = dict(auth)
    auth["authorized_removal_set_sha256"] = "a" * 64
    decision = evaluate_bulk_proven_repository_decommission_authorization(
        [],
        auth=auth,
        repo_root=REPO_ROOT,
        file_diffs={},
        diff_base_sha=BASE_SHA,
    )
    assert decision.applied is False
    assert REASON_BULK_SET_SHA256_MISMATCH in decision.reason_codes


def test_unauthorized_extra_delete_denies() -> None:
    auth = _load_bulk_auth()
    extra = "src/ops/definitely_not_in_proven_set_v9999.py"
    decision = evaluate_bulk_proven_repository_decommission_authorization(
        [extra],
        auth=auth,
        repo_root=REPO_ROOT,
        file_diffs={extra: _deleted_diff(extra)},
        diff_base_sha=BASE_SHA,
    )
    assert decision.applied is False
    assert REASON_BULK_UNAUTHORIZED_DELETE in decision.reason_codes


def test_missing_evidence_file_denies(tmp_path: Path) -> None:
    auth = _load_bulk_auth()
    auth = dict(auth)
    auth["authorized_removal_evidence_path"] = "evidence/does_not_exist.json"
    decision = evaluate_bulk_proven_repository_decommission_authorization(
        [],
        auth=auth,
        repo_root=tmp_path,
        file_diffs={},
        diff_base_sha=BASE_SHA,
    )
    assert decision.applied is False


def test_runtime_addition_not_bulk_authorized() -> None:
    auth = _load_bulk_auth()
    added = "src/trading/master_v2/survival_assessment_v1.py"
    decision = evaluate_bulk_proven_repository_decommission_authorization(
        [added],
        auth=auth,
        repo_root=REPO_ROOT,
        file_diffs={added: f"diff --git a/{added} b/{added}\n+new\n"},
        diff_base_sha=BASE_SHA,
    )
    assert decision.applied is False
    assert decision.convergence_cut_diff is False


def test_repository_exact_file_grant_json_absent() -> None:
    grant_path = (
        REPO_ROOT / "config/governance/semantics_neutral_decommission_authorization_v1.json"
    )
    assert not grant_path.is_file()
    assert load_decommission_authorization(REPO_ROOT) is None


def test_bulk_grant_not_reused_for_unrelated_diff() -> None:
    auth = _load_bulk_auth()
    decision = evaluate_bulk_proven_repository_decommission_authorization(
        ["README.md"],
        auth=auth,
        repo_root=REPO_ROOT,
        file_diffs={"README.md": "diff --git a/README.md b/README.md\n+unrelated\n"},
        diff_base_sha=BASE_SHA,
    )
    assert decision.applied is False


def test_proven_set_subset_delete_only_still_denies_without_full_set() -> None:
    payload = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    one = payload["paths"][0]
    auth = _load_bulk_auth()
    decision = evaluate_bulk_proven_repository_decommission_authorization(
        [one],
        auth=auth,
        repo_root=REPO_ROOT,
        file_diffs={one: _deleted_diff(one)},
        diff_base_sha=BASE_SHA,
    )
    assert decision.applied is False
    assert REASON_BULK_MISSING_AUTHORIZED_DELETE in decision.reason_codes


def test_decommission_loader_still_independent() -> None:
    assert load_decommission_authorization(REPO_ROOT) is None


def test_forbidden_surface_cleared_when_bulk_and_stale_apply() -> None:
    """Integration-shaped: bulk + stale reference cleanup on repo cut diff."""
    import subprocess

    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{BASE_SHA}...HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    changed = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    if len(changed) < 5000:
        return
    diffs: dict[str, str] = {}
    for path in changed:
        diff_proc = subprocess.run(
            ["git", "diff", "-U20", f"{BASE_SHA}...HEAD", "--", path],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        diffs[path] = diff_proc.stdout
    md = "docs/ops/specs/MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md"
    if md in changed:
        wt = subprocess.run(
            ["git", "diff", "-U20", BASE_SHA, "--", md],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if wt.stdout.strip():
            diffs[md] = wt.stdout
    report = build_boundary_report(
        changed,
        repo_root=REPO_ROOT,
        file_diffs=diffs,
        diff_base_sha=BASE_SHA,
    )
    assert report.bulk_proven_repository_decommission_authorization_applied is True
    assert report.bound_stale_reference_cleanup_applied is True
    assert forbidden_surface_changed_count(report) == 0
    assert report.admissible is True
