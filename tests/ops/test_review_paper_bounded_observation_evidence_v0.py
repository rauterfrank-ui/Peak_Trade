"""Behavioral tests for paper bounded closeout evidence review v0."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REVIEW_SCRIPT = ROOT / "scripts" / "ops" / "review_paper_bounded_observation_evidence_v0.py"
CANONICAL_GIT_SHA_PREFIX = "0123456789ab"
REPO_HEAD_SHA_PREFIX_MACHINE_LINE_KEY = "REPO_HEAD_SHA_PREFIX"


def _load_review():
    spec = importlib.util.spec_from_file_location(
        "review_paper_bounded_observation_evidence_v0",
        REVIEW_SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_closeout_bundle(
    staging: Path,
    *,
    git_sha_prefix: str | None = CANONICAL_GIT_SHA_PREFIX,
    include_run_metadata: bool = True,
    include_final_machine_lines: bool = True,
    include_closeout: bool = True,
    run_metadata_overrides: dict[str, object] | None = None,
    machine_line_overrides: dict[str, str] | None = None,
) -> None:
    staging.mkdir(parents=True, exist_ok=True)
    if include_closeout:
        (staging / "CLOSEOUT.md").write_text(
            "\n".join(
                [
                    "# Paper Bounded Observation Adapter Closeout",
                    "live_authority=false",
                    "testnet_authority=false",
                    "broker_authority=false",
                    "LIVE_ALLOWED=false",
                    "PREFLIGHT_BLOCKED=true",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    if include_run_metadata:
        metadata: dict[str, object] = {"repo_head_sha_prefix": git_sha_prefix}
        if run_metadata_overrides:
            metadata.update(run_metadata_overrides)
        (staging / "RUN_METADATA.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if include_final_machine_lines:
        machine_lines = {REPO_HEAD_SHA_PREFIX_MACHINE_LINE_KEY: git_sha_prefix}
        if machine_line_overrides:
            machine_lines.update(machine_line_overrides)
        ordered = sorted(machine_lines.items())
        (staging / "FINAL_MACHINE_LINES.txt").write_text(
            "\n".join(f"{key}={value}" for key, value in ordered) + "\n",
            encoding="utf-8",
        )


def test_review_script_exists() -> None:
    assert REVIEW_SCRIPT.is_file()


def test_review_passes_consistent_runtime_git_provenance(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_closeout_bundle(staging, git_sha_prefix=CANONICAL_GIT_SHA_PREFIX)
    result = review.review_evidence(staging)
    assert result["verdict"] == review.PASS
    assert result["checks"]["run_metadata_repo_head_sha_prefix_valid"] is True
    assert result["checks"]["final_machine_lines_repo_head_sha_prefix_valid"] is True
    assert result["checks"]["git_provenance_consistent"] is True


def test_review_fails_missing_run_metadata(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_closeout_bundle(staging, include_run_metadata=False)
    result = review.review_evidence(staging)
    assert result["verdict"] == review.REVIEW_REQUIRED
    assert result["checks"]["run_metadata_present"] is False
    assert any(review.GIT_PROVENANCE_MISSING in issue for issue in result["issues"])


def test_review_fails_missing_repo_head_sha_prefix_field(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_closeout_bundle(staging)
    (staging / "RUN_METADATA.json").write_text('{"run_id": "fixture"}\n', encoding="utf-8")
    result = review.review_evidence(staging)
    assert result["verdict"] == review.REVIEW_REQUIRED
    assert result["checks"]["run_metadata_repo_head_sha_prefix_valid"] is False
    assert any(review.GIT_PROVENANCE_MISSING in issue for issue in result["issues"])


def test_review_fails_missing_final_machine_lines(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_closeout_bundle(staging, include_final_machine_lines=False)
    result = review.review_evidence(staging)
    assert result["verdict"] == review.REVIEW_REQUIRED
    assert result["checks"]["final_machine_lines_present"] is False
    assert any(review.GIT_PROVENANCE_MISSING in issue for issue in result["issues"])


def test_review_fails_missing_final_machine_lines_repo_head_sha_prefix(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_closeout_bundle(staging)
    (staging / "FINAL_MACHINE_LINES.txt").write_text("REVIEW_VERDICT=PASS\n", encoding="utf-8")
    result = review.review_evidence(staging)
    assert result["verdict"] == review.REVIEW_REQUIRED
    assert result["checks"]["final_machine_lines_repo_head_sha_prefix_valid"] is False
    assert any(review.GIT_PROVENANCE_MISSING in issue for issue in result["issues"])


@pytest.mark.parametrize(
    "bad_prefix",
    [
        "",
        "   ",
        None,
        "UNKNOWN",
        "UNKNOWN_HEAD_MISSING",
        "UNKNOWN_REF_MISSING",
        "NOT_AVAILABLE",
        "MISSING",
        "not-hex-prefix",
        "0x0123456789ab",
        "0123456789abc",
        "0123456789a",
        "0123456789 ab",
    ],
)
def test_review_fails_invalid_run_metadata_git_sha_prefix(
    tmp_path: Path, bad_prefix: str | None
) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_closeout_bundle(
        staging,
        run_metadata_overrides={"repo_head_sha_prefix": bad_prefix},
    )
    result = review.review_evidence(staging)
    assert result["verdict"] == review.REVIEW_REQUIRED
    assert result["checks"]["run_metadata_repo_head_sha_prefix_valid"] is False


@pytest.mark.parametrize(
    "bad_prefix",
    [
        "",
        "   ",
        "UNKNOWN",
        "UNKNOWN_HEAD_MISSING",
        "NOT_AVAILABLE",
        "not-hex-prefix",
        "0x0123456789ab",
        "0123456789abc",
    ],
)
def test_review_fails_invalid_final_machine_lines_git_sha_prefix(
    tmp_path: Path, bad_prefix: str
) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_closeout_bundle(
        staging,
        machine_line_overrides={REPO_HEAD_SHA_PREFIX_MACHINE_LINE_KEY: bad_prefix},
    )
    result = review.review_evidence(staging)
    assert result["verdict"] == review.REVIEW_REQUIRED
    assert result["checks"]["final_machine_lines_repo_head_sha_prefix_valid"] is False


def test_review_fails_mismatched_runtime_git_provenance(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_closeout_bundle(
        staging,
        git_sha_prefix=CANONICAL_GIT_SHA_PREFIX,
        machine_line_overrides={REPO_HEAD_SHA_PREFIX_MACHINE_LINE_KEY: "111122223333"},
    )
    result = review.review_evidence(staging)
    assert result["verdict"] == review.REVIEW_REQUIRED
    assert result["checks"]["git_provenance_consistent"] is False
    assert any(review.GIT_PROVENANCE_MISMATCH in issue for issue in result["issues"])


def test_review_fails_similar_prefix_mismatch_not_normalized(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_closeout_bundle(
        staging,
        git_sha_prefix="0123456789ab",
        machine_line_overrides={REPO_HEAD_SHA_PREFIX_MACHINE_LINE_KEY: "0123456789a0"},
    )
    result = review.review_evidence(staging)
    assert result["verdict"] == review.REVIEW_REQUIRED
    assert any(review.GIT_PROVENANCE_MISMATCH in issue for issue in result["issues"])


def test_review_no_plan_level_sha_fallback_when_runtime_provenance_missing(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_closeout_bundle(
        staging, git_sha_prefix=None, run_metadata_overrides={"repo_head_sha_prefix": None}
    )
    (staging / "PLAN_LEVEL_ORIGIN_MAIN_HEAD.txt").write_text("3702fc944962\n", encoding="utf-8")
    result = review.review_evidence(staging)
    assert result["verdict"] == review.REVIEW_REQUIRED
    assert any(review.GIT_PROVENANCE_MISSING in issue for issue in result["issues"])


def test_review_git_provenance_is_deterministic(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_closeout_bundle(staging)
    first = review.review_evidence(staging)
    second = review.review_evidence(staging)
    assert first == second


def test_review_does_not_claim_gate_clearance(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_closeout_bundle(staging)
    result = review.review_evidence(staging)
    blob = json.dumps(result)
    assert "PAPER_RUNTIME_APPROVAL_GRANTED" not in blob
    assert result["non_authorizing"] is True


def test_review_fails_closeout_gate_claims(tmp_path: Path) -> None:
    review = _load_review()
    staging = tmp_path / "staging"
    _write_closeout_bundle(staging)
    (staging / "CLOSEOUT.md").write_text("PAPER_RUNTIME_APPROVAL_GRANTED=true\n", encoding="utf-8")
    result = review.review_evidence(staging)
    assert result["verdict"] == review.REVIEW_REQUIRED
    assert result["checks"]["closeout_no_gate_claims"] is False
