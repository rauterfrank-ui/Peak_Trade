"""Contract tests for parent closeout manifest precondition gap fix v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256, write_manifest_sha256
from scripts.research.offline_source_evidence_parent_closeout_manifest_precondition_gap_fix_v0 import (
    FAILURE_CLASS,
    FORBIDDEN_AUTHORITY_FLAGS,
    GO_TOKEN,
    PROCESS_CLASSIFICATION,
    SCOPE_CLASSIFICATION,
    SCOPE_ID,
    VERDICT_TARGET,
    _normalize_rel_path,
    classify_invalid_parent_manifest,
    run_offline_source_evidence_parent_closeout_manifest_precondition_gap_fix_v0,
    validate_config,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIX_CONFIG = (
    REPO_ROOT
    / "config/research/offline_source_evidence_parent_closeout_manifest_precondition_gap_fix_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/OFFLINE_SOURCE_EVIDENCE_PARENT_CLOSEOUT_MANIFEST_PRECONDITION_GAP_FIX_V0.md"
)
INVALID_PARENT_SUFFIX = (
    "offline_source_evidence_admissibility_review_scope_merge_closeout_20260706T060519Z"
)
NEXT_STEP = "RERUN_OR_UPDATE_ADMISSIBILITY_REVIEW_AFTER_PRECONDITION_FIX_REQUIRES_SEPARATE_GO"
PARENT_PRE_MERGE = "399cbcbc8b9d9dbd15ef7ed22da0f31e72e91081"
PARENT_PR_HEAD = "f391b7e4d3b9a334cc4541e6b2b89016e75039c9"
PARENT_POST_MERGE = "923915da6d60c18b7fc96d1fc4f38632bc225330"


def _load_config() -> dict:
    return json.loads(FIX_CONFIG.read_text(encoding="utf-8"))


def _write_invalid_parent_closeout(parent_closeout: Path) -> None:
    closeout_body = (
        "\n".join(
            [
                "# Parent Closeout",
                "",
                f"PRE_MERGE_ORIGIN_MAIN={PARENT_PRE_MERGE}",
                f"PR_HEAD={PARENT_PR_HEAD}",
                f"POST_MERGE_HEAD={PARENT_POST_MERGE}",
                f"MERGE_COMMIT={PARENT_POST_MERGE}",
                "NEXT_STEP=TEST",
            ]
        )
        + "\n"
    )
    (parent_closeout / "CLOSEOUT.md").write_text(closeout_body, encoding="utf-8")
    (parent_closeout / "pr_view_post_merge.json").write_text("{}\n", encoding="utf-8")
    write_manifest_sha256(parent_closeout)
    appended = closeout_body + "\nMANIFEST_VERIFY_RC=0\n"
    (parent_closeout / "CLOSEOUT.md").write_text(appended, encoding="utf-8")


@pytest.fixture
def synthetic_archive(tmp_path: Path) -> Path:
    archive_root = tmp_path / "archive"
    invalid_parent = archive_root / "implementation" / INVALID_PARENT_SUFFIX
    admissibility_bundle = archive_root / "implementation" / "admissibility_review_execution_bundle"
    invalid_parent.mkdir(parents=True)
    admissibility_bundle.mkdir(parents=True)

    _write_invalid_parent_closeout(invalid_parent)
    (admissibility_bundle / "REVIEW_RESULT.json").write_text(
        json.dumps({"verdict": "ADMISSIBILITY_FAIL"}) + "\n",
        encoding="utf-8",
    )
    write_manifest_sha256(admissibility_bundle)
    return archive_root


@pytest.fixture
def synthetic_config(tmp_path: Path, synthetic_archive: Path) -> Path:
    config = _load_config()
    config["invalid_parent_closeout_dir"] = str(
        synthetic_archive / "implementation" / INVALID_PARENT_SUFFIX
    )
    config["admissibility_review_bundle"] = str(
        synthetic_archive / "implementation" / "admissibility_review_execution_bundle"
    )
    config_path = tmp_path / "fix_config.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return config_path


def test_config_scope_and_go_token() -> None:
    cfg = _load_config()
    assert cfg["scope_id"] == SCOPE_ID
    assert cfg["verdict_target"] == VERDICT_TARGET
    assert cfg["go_token"] == GO_TOKEN
    assert cfg["process_classification"] == PROCESS_CLASSIFICATION
    assert cfg["scope_classification"] == SCOPE_CLASSIFICATION


def test_forbidden_authority_flags_all_false() -> None:
    cfg = _load_config()
    for flag in FORBIDDEN_AUTHORITY_FLAGS:
        assert cfg[flag] is False


def test_parent_and_admissibility_linkage() -> None:
    cfg = _load_config()
    assert cfg["parent_pr"] == 4913
    assert cfg["admissibility_review_pr"] == 4914
    assert cfg["admissibility_review_verdict"] == "ADMISSIBILITY_FAIL"
    assert cfg["expected_failure_class"] == FAILURE_CLASS
    assert cfg["expected_invalid_parent_manifest_rc"] == 1
    assert cfg["historical_bundle_mutation_allowed"] is False
    assert cfg["next_step"] == NEXT_STEP


def test_classify_invalid_parent_detects_closeout_md_modified(
    synthetic_archive: Path,
) -> None:
    invalid_parent = synthetic_archive / "implementation" / INVALID_PARENT_SUFFIX
    provenance = classify_invalid_parent_manifest(invalid_parent)
    assert provenance["parent_closeout_manifest_verify_rc"] == 1
    assert provenance["failure_class"] == FAILURE_CLASS
    assert {_normalize_rel_path(path) for path in provenance["mismatched_files"]} == {"CLOSEOUT.md"}
    assert provenance["historical_bundle_mutated"] is False


def test_script_creates_corrective_bundle(
    synthetic_archive: Path,
    synthetic_config: Path,
) -> None:
    result = run_offline_source_evidence_parent_closeout_manifest_precondition_gap_fix_v0(
        config_path=synthetic_config,
        archive_root=synthetic_archive,
    )
    output_dir = Path(result["durable_evidence_path"])
    assert output_dir.is_dir()
    assert (output_dir / "PRECONDITION_FIX_RESULT.json").is_file()
    assert (output_dir / "PRECONDITION_FIX_FINDINGS.md").is_file()
    assert (output_dir / "INVALID_PARENT_MANIFEST_PROVENANCE.json").is_file()
    assert (output_dir / "SUPERSEDING_PARENT_CLOSEOUT_MANIFEST.sha256").is_file()
    assert (output_dir / "SAFETY_BOUNDARIES.json").is_file()
    assert (output_dir / "MANIFEST.sha256").is_file()
    assert (output_dir / "MANIFEST_VERIFY.log").is_file()
    assert result["verdict"] == VERDICT_TARGET


def test_corrective_bundle_manifest_verifies_rc0(
    synthetic_archive: Path,
    synthetic_config: Path,
) -> None:
    result = run_offline_source_evidence_parent_closeout_manifest_precondition_gap_fix_v0(
        config_path=synthetic_config,
        archive_root=synthetic_archive,
    )
    output_dir = Path(result["durable_evidence_path"])
    ok, msg = verify_manifest_sha256(output_dir)
    assert ok, msg
    assert result["manifest_verify_rc"] == 0
    assert result["superseding_parent_manifest_verify_rc"] == 0


def test_superseding_parent_closeout_manifest_verifies_rc0(
    synthetic_archive: Path,
    synthetic_config: Path,
) -> None:
    result = run_offline_source_evidence_parent_closeout_manifest_precondition_gap_fix_v0(
        config_path=synthetic_config,
        archive_root=synthetic_archive,
    )
    superseding_dir = Path(result["superseding_parent_closeout_dir"])
    ok, msg = verify_manifest_sha256(superseding_dir)
    assert ok, msg


def test_historical_invalid_parent_bundle_not_mutated(
    synthetic_archive: Path,
    synthetic_config: Path,
) -> None:
    invalid_parent = synthetic_archive / "implementation" / INVALID_PARENT_SUFFIX
    before = (invalid_parent / "CLOSEOUT.md").read_text(encoding="utf-8")
    result = run_offline_source_evidence_parent_closeout_manifest_precondition_gap_fix_v0(
        config_path=synthetic_config,
        archive_root=synthetic_archive,
    )
    after = (invalid_parent / "CLOSEOUT.md").read_text(encoding="utf-8")
    assert before == after
    assert result["historical_bundle_mutated"] is False
    ok, _ = verify_manifest_sha256(invalid_parent)
    assert ok is False


def test_safety_boundaries_all_false(
    synthetic_archive: Path,
    synthetic_config: Path,
) -> None:
    result = run_offline_source_evidence_parent_closeout_manifest_precondition_gap_fix_v0(
        config_path=synthetic_config,
        archive_root=synthetic_archive,
    )
    output_dir = Path(result["durable_evidence_path"])
    safety = json.loads((output_dir / "SAFETY_BOUNDARIES.json").read_text(encoding="utf-8"))
    for flag in FORBIDDEN_AUTHORITY_FLAGS:
        assert safety[flag] is False
    assert safety["is_economic_viability_evidence_v1"] is False
    assert safety["is_economic_evaluation"] is False
    assert safety["grants_runtime_authority"] is False
    assert safety["mutates_historical_negative_evidence"] is False
    assert safety["missing_source_evidence_sentinel_rows"] == 0


def test_script_fails_closed_on_forbidden_authority_flag(
    synthetic_archive: Path,
    synthetic_config: Path,
) -> None:
    cfg = json.loads(synthetic_config.read_text(encoding="utf-8"))
    cfg["runtime_authority_granted"] = True
    bad_config = synthetic_config.parent / "bad_config.json"
    bad_config.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        run_offline_source_evidence_parent_closeout_manifest_precondition_gap_fix_v0(
            config_path=bad_config,
            archive_root=synthetic_archive,
        )
    assert exc.value.code != 0


def test_validate_config_rejects_wrong_failure_class() -> None:
    cfg = _load_config()
    cfg["expected_failure_class"] = "WRONG"
    errors = validate_config(cfg)
    assert any("unexpected expected_failure_class" in error for error in errors)


def test_docs_non_authorizing_language() -> None:
    text = GOVERNANCE_DOC.read_text(encoding="utf-8")
    assert "not** `EconomicViabilityEvidenceV1`" in text
    assert "not** an economic evaluation" in text
    assert "grants **no** runtime authority" in text
    assert "does **not** mutate historical negative" in text
    assert "4913" in text
    assert "4914" in text
    assert "`CLOSEOUT_MD_MODIFIED_AFTER_MANIFEST_WRITE`" in text
    assert "`PRECONDITION_GAP_FIX_COMPLETE`" in text
    assert NEXT_STEP in text
