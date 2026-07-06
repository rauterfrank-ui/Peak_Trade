"""Contract tests for offline source evidence admissibility review scope definition v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256, write_manifest_sha256
from scripts.research.offline_source_evidence_admissibility_review_scope_v0 import (
    FORBIDDEN_AUTHORITY_FLAGS,
    GO_TOKEN,
    PROCESS_CLASSIFICATION,
    REQUIRED_REVIEW_DIMENSIONS,
    SCOPE_CLASSIFICATION,
    SCOPE_ID,
    run_offline_source_evidence_admissibility_review_scope_v0,
    validate_config,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT / "config/research/offline_source_evidence_admissibility_review_scope_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/OFFLINE_SOURCE_EVIDENCE_ADMISSIBILITY_REVIEW_SCOPE_V0.md"
)
PARENT_CLOSEOUT_SUFFIX = (
    "offline_source_evidence_contract_collector_materialization_merge_closeout_20260706T055534ZZ"
)
NEXT_STEP = (
    "OFFLINE_SOURCE_EVIDENCE_ADMISSIBILITY_REVIEW_EXECUTION_OR_"
    "ECONOMIC_EVALUATION_PRECONDITION_MATERIALIZATION_SCOPE_REQUIRES_SEPARATE_GO"
)
PARENT_PRE_MERGE = "0b307dc027a274d0d5f0df07b96d6c593c761331"
PARENT_PR_HEAD = "18af85cd079c87ef360a8403dede92fd300ce578"
PARENT_POST_MERGE = "399cbcbc8b9d9dbd15ef7ed22da0f31e72e91081"


def _load_config() -> dict:
    return json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))


@pytest.fixture
def synthetic_archive(tmp_path: Path) -> Path:
    archive_root = tmp_path / "archive"
    parent_closeout = archive_root / "implementation" / PARENT_CLOSEOUT_SUFFIX
    parent_closeout.mkdir(parents=True)
    (parent_closeout / "CLOSEOUT.md").write_text("VERDICT=TEST\n", encoding="utf-8")
    write_manifest_sha256(parent_closeout)
    return archive_root


@pytest.fixture
def synthetic_config(tmp_path: Path, synthetic_archive: Path) -> Path:
    config = _load_config()
    config["parent_closeout_dir"] = str(
        synthetic_archive / "implementation" / PARENT_CLOSEOUT_SUFFIX
    )
    config_path = tmp_path / "scope_config.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return config_path


def test_config_flags_enforce_no_runtime_or_economic_execution() -> None:
    cfg = _load_config()
    assert cfg["admissibility_review_defined"] is True
    assert cfg["admissibility_review_executed"] is False
    assert cfg["economic_evaluation_authorized"] is False
    assert cfg["economic_evaluation_executed"] is False
    assert cfg["economic_viability_evidence_emitted"] is False
    assert cfg["runtime_authority_granted"] is False
    for flag in FORBIDDEN_AUTHORITY_FLAGS:
        assert cfg[flag] is False


def test_required_review_dimensions_present() -> None:
    cfg = _load_config()
    assert cfg["required_review_dimensions"] == list(REQUIRED_REVIEW_DIMENSIONS)


def test_parent_provenance_fields_match_exactly() -> None:
    cfg = _load_config()
    assert cfg["parent_pr"] == 4912
    assert cfg["parent_pre_merge_origin_main"] == PARENT_PRE_MERGE
    assert cfg["parent_pr_head"] == PARENT_PR_HEAD
    assert cfg["parent_post_merge_head"] == PARENT_POST_MERGE
    assert cfg["parent_closeout_dir"].endswith(PARENT_CLOSEOUT_SUFFIX)
    assert cfg["required_parent_manifest_rc"] == 0


def test_scope_classification_and_go_token() -> None:
    cfg = _load_config()
    assert cfg["scope_id"] == SCOPE_ID
    assert cfg["go_token"] == GO_TOKEN
    assert cfg["process_classification"] == PROCESS_CLASSIFICATION
    assert cfg["scope_classification"] == SCOPE_CLASSIFICATION


def test_script_creates_durable_bundle(
    synthetic_archive: Path,
    synthetic_config: Path,
) -> None:
    result = run_offline_source_evidence_admissibility_review_scope_v0(
        config_path=synthetic_config,
        archive_root=synthetic_archive,
    )
    output_dir = Path(result["durable_evidence_path"])
    assert output_dir.is_dir()
    assert (output_dir / "SUMMARY.json").is_file()
    assert (output_dir / "SCOPE_DEFINITION.md").is_file()
    assert (output_dir / "MANIFEST.sha256").is_file()
    assert result["verdict"] == "SCOPE_DEFINED_NOT_EXECUTED"


def test_script_writes_and_verifies_manifest(
    synthetic_archive: Path,
    synthetic_config: Path,
) -> None:
    result = run_offline_source_evidence_admissibility_review_scope_v0(
        config_path=synthetic_config,
        archive_root=synthetic_archive,
    )
    output_dir = Path(result["durable_evidence_path"])
    ok, msg = verify_manifest_sha256(output_dir)
    assert ok, msg
    assert result["manifest_verify_rc"] == 0


def test_script_fails_closed_on_forbidden_authority_flags(
    synthetic_archive: Path,
    synthetic_config: Path,
) -> None:
    cfg = json.loads(synthetic_config.read_text(encoding="utf-8"))
    cfg["runtime_authority_granted"] = True
    bad_config = synthetic_config.parent / "bad_config.json"
    bad_config.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        run_offline_source_evidence_admissibility_review_scope_v0(
            config_path=bad_config,
            archive_root=synthetic_archive,
        )
    assert exc.value.code != 0


def test_script_fails_closed_on_economic_evaluation_executed(
    synthetic_archive: Path,
    synthetic_config: Path,
) -> None:
    cfg = json.loads(synthetic_config.read_text(encoding="utf-8"))
    cfg["economic_evaluation_executed"] = True
    bad_config = synthetic_config.parent / "bad_eval_config.json"
    bad_config.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        run_offline_source_evidence_admissibility_review_scope_v0(
            config_path=bad_config,
            archive_root=synthetic_archive,
        )
    assert exc.value.code != 0


def test_script_fails_closed_on_economic_viability_evidence_emitted(
    synthetic_archive: Path,
    synthetic_config: Path,
) -> None:
    cfg = json.loads(synthetic_config.read_text(encoding="utf-8"))
    cfg["economic_viability_evidence_emitted"] = True
    bad_config = synthetic_config.parent / "bad_evidence_config.json"
    bad_config.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        run_offline_source_evidence_admissibility_review_scope_v0(
            config_path=bad_config,
            archive_root=synthetic_archive,
        )
    assert exc.value.code != 0


def test_validate_config_catches_missing_review_dimensions() -> None:
    cfg = _load_config()
    cfg["required_review_dimensions"] = ["source_evidence_manifest_integrity"]
    errors = validate_config(cfg)
    assert any("missing required review dimensions" in error for error in errors)


def test_docs_contain_non_authorizing_language() -> None:
    text = GOVERNANCE_DOC.read_text(encoding="utf-8")
    assert "SCOPE_DEFINED_NOT_EXECUTED" in text
    assert "scope-definition-only" in text.lower()
    assert "not** an admissibility review execution" in text
    assert "not** an economic evaluation" in text
    assert "does **not** emit `EconomicViabilityEvidenceV1`" in text
    assert (
        "No strategy, parameter, dataset, period, fee, slippage, funding, execution, "
        "or policy binding is changed"
    ) in text
    assert (
        "No runtime, shadow, paper, testnet, scheduler, adapter, credential, arming, "
        "canary, or live authority is granted"
    ) in text
    assert "4912" in text


def test_docs_include_review_outcome_vocabulary_without_emitting_outcome() -> None:
    text = GOVERNANCE_DOC.read_text(encoding="utf-8")
    assert "`PASS`" in text
    assert "`FAIL`" in text
    assert "`INCONCLUSIVE`" in text
    assert "emits **no** such outcome" in text


def test_next_step_requires_separate_go() -> None:
    cfg = _load_config()
    assert cfg["next_step_after_this_scope"] == NEXT_STEP
    text = GOVERNANCE_DOC.read_text(encoding="utf-8")
    assert NEXT_STEP in text
    assert "separate operator GO" in text
