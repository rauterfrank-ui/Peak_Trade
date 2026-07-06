"""Contract tests for offline source evidence admissibility review execution v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256, write_manifest_sha256
from scripts.research.offline_source_evidence_admissibility_review_execution_v0 import (
    FINAL_RESEARCH_FLEET,
    FORBIDDEN_AUTHORITY_FLAGS,
    GO_TOKEN,
    PROCESS_CLASSIFICATION,
    REVIEW_DIMENSIONS,
    SCOPE_CLASSIFICATION,
    SCOPE_ID,
    _compute_verdict,
    run_offline_source_evidence_admissibility_review_execution_v0,
    validate_config,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTION_CONFIG = (
    REPO_ROOT / "config/research/offline_source_evidence_admissibility_review_execution_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/OFFLINE_SOURCE_EVIDENCE_ADMISSIBILITY_REVIEW_EXECUTION_V0.md"
)
PARENT_CLOSEOUT_SUFFIX = (
    "offline_source_evidence_admissibility_review_scope_merge_closeout_20260706T060519Z"
)
PARENT_PRE_MERGE = "399cbcbc8b9d9dbd15ef7ed22da0f31e72e91081"
PARENT_PR_HEAD = "f391b7e4d3b9a334cc4541e6b2b89016e75039c9"
PARENT_POST_MERGE = "923915da6d60c18b7fc96d1fc4f38632bc225330"
NEXT_STEP_FAIL = "RATIFY_NARROW_PRECONDITION_GAP_FIX_OR_SCOPE_DEFINITION_REQUIRES_SEPARATE_GO"
NEXT_STEP_PASS = "RATIFY_OFFLINE_ECONOMIC_EVALUATION_PRECONDITION_MATERIALIZATION_OR_EVALUATION_SCOPE_REQUIRES_SEPARATE_GO"


def _load_config() -> dict:
    return json.loads(EXECUTION_CONFIG.read_text(encoding="utf-8"))


def _finding(dimension: str, status: str, hard_block: bool = False) -> dict:
    return {
        "dimension": dimension,
        "status": status,
        "hard_block": hard_block,
        "finding": "test",
        "evidence_refs": [],
    }


@pytest.fixture
def synthetic_archive(tmp_path: Path) -> Path:
    archive_root = tmp_path / "archive"
    parent_closeout = archive_root / "implementation" / PARENT_CLOSEOUT_SUFFIX
    scope_bundle = archive_root / "implementation" / "scope_definition_bundle"
    collector_bundle = archive_root / "implementation" / "collector_bundle"
    evaluation_bundle = archive_root / "implementation" / "evaluation_bundle"

    for directory in (parent_closeout, scope_bundle, collector_bundle, evaluation_bundle):
        directory.mkdir(parents=True)

    (parent_closeout / "CLOSEOUT.md").write_text(
        "\n".join(
            [
                f"PRE_MERGE_ORIGIN_MAIN={PARENT_PRE_MERGE}",
                f"PR_HEAD={PARENT_PR_HEAD}",
                f"POST_MERGE_HEAD={PARENT_POST_MERGE}",
                f"MERGE_COMMIT={PARENT_POST_MERGE}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (parent_closeout / "pr_view_post_merge.json").write_text(
        json.dumps({"headRefOid": PARENT_PR_HEAD, "mergeCommit": {"oid": PARENT_POST_MERGE}})
        + "\n",
        encoding="utf-8",
    )
    write_manifest_sha256(parent_closeout)

    (scope_bundle / "SUMMARY.json").write_text("{}\n", encoding="utf-8")
    write_manifest_sha256(scope_bundle)

    (collector_bundle / "SOURCE_EVIDENCE_COLLECTION_REPORT.json").write_text(
        json.dumps(
            {
                "contracts_materialized": [
                    "TRADE_LEDGER_PER_TRADE_DECOMPOSITION_V0",
                    "LONG_SHORT_ATTRIBUTION_LEDGER_V0",
                    "TURNOVER_COST_DRAG_TIMESERIES_V0",
                    "INSTRUMENT_CONCENTRATION_DETAIL_V0",
                ],
                "config_digest": "abc",
                "data_digest": "def",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    for contract_id in (
        "TRADE_LEDGER_PER_TRADE_DECOMPOSITION_V0",
        "LONG_SHORT_ATTRIBUTION_LEDGER_V0",
        "TURNOVER_COST_DRAG_TIMESERIES_V0",
        "INSTRUMENT_CONCENTRATION_DETAIL_V0",
    ):
        (collector_bundle / f"{contract_id}.jsonl").write_text(
            json.dumps({"strategy_id": "trend_following", "manifest_ref": "x"}) + "\n",
            encoding="utf-8",
        )
    write_manifest_sha256(collector_bundle)

    for candidate in FINAL_RESEARCH_FLEET:
        candidate_dir = evaluation_bundle / "candidates" / f"{candidate}_post_v4_hypothesis_v0"
        candidate_dir.mkdir(parents=True)
        (candidate_dir / "INPUT_PROVENANCE.json").write_text(
            json.dumps(
                {
                    "config_digest": "cfg",
                    "dataset_digest": "data",
                    "implementation_digest": "impl",
                    "policy_digest": "pol",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (candidate_dir / "CONFIG_SNAPSHOT.json").write_text(
            json.dumps(
                {
                    "cfg": {
                        "backtest": {
                            "cost_model_version": "backtest_cost_v0",
                            "dataset_admissibility": {
                                "dataset": {
                                    "field_bindings": {"funding_field_binding": "funding_rate"},
                                    "instrument_id": "inst-eth-usdt-perp",
                                    "out_of_sample_period": "a..b",
                                    "training_period": "a..b",
                                    "validation_period": "a..b",
                                },
                                "execution_cost_binding": {
                                    "execution_price_observation_source": "MODELLED_NOT_OBSERVED"
                                },
                            },
                            "economic_research_execution_cost": {
                                "fee_model_version": "fee_v0",
                                "spread_model_version": "spread_v0",
                                "execution_price_observation_source": "MODELLED_NOT_OBSERVED",
                            },
                        }
                    }
                }
            )
            + "\n",
            encoding="utf-8",
        )
    write_manifest_sha256(evaluation_bundle)

    return archive_root


@pytest.fixture
def synthetic_config(tmp_path: Path, synthetic_archive: Path) -> Path:
    config = _load_config()
    config["parent_closeout_dir"] = str(
        synthetic_archive / "implementation" / PARENT_CLOSEOUT_SUFFIX
    )
    config["scope_definition_bundle"] = str(
        synthetic_archive / "implementation" / "scope_definition_bundle"
    )
    config["collector_materialization_bundle"] = str(
        synthetic_archive / "implementation" / "collector_bundle"
    )
    config["parent_evaluation_bundle"] = str(
        synthetic_archive / "implementation" / "evaluation_bundle"
    )
    config_path = tmp_path / "execution_config.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return config_path


def test_parent_provenance_exact_match() -> None:
    cfg = _load_config()
    assert cfg["parent_pr"] == 4913
    assert cfg["parent_pre_merge_origin_main"] == PARENT_PRE_MERGE
    assert cfg["parent_pr_head"] == PARENT_PR_HEAD
    assert cfg["parent_post_merge_head"] == PARENT_POST_MERGE
    assert cfg["parent_closeout_dir"].endswith(PARENT_CLOSEOUT_SUFFIX)


def test_forbidden_authority_flags_all_false() -> None:
    cfg = _load_config()
    for flag in FORBIDDEN_AUTHORITY_FLAGS:
        assert cfg[flag] is False


def test_no_economic_evaluation_execution_in_config() -> None:
    cfg = _load_config()
    assert cfg["economic_evaluation_authorized"] is False
    assert cfg["economic_evaluation_executed"] is False
    assert cfg["economic_viability_evidence_emitted"] is False
    assert cfg["admissibility_review_executed"] is True


def test_all_review_dimensions_present() -> None:
    cfg = _load_config()
    assert cfg["required_review_dimensions"] == list(REVIEW_DIMENSIONS)


def test_pass_fail_inconclusive_vocabulary() -> None:
    cfg = _load_config()
    assert cfg["review_result_vocabulary"] == [
        "ADMISSIBILITY_PASS",
        "ADMISSIBILITY_FAIL",
        "ADMISSIBILITY_INCONCLUSIVE",
    ]


def test_hard_block_verdict_rules() -> None:
    assert _compute_verdict([_finding("x", "PASS")]) == "ADMISSIBILITY_PASS"
    assert (
        _compute_verdict([_finding("x", "INCONCLUSIVE"), _finding("y", "PASS")])
        == "ADMISSIBILITY_INCONCLUSIVE"
    )
    assert (
        _compute_verdict([_finding("x", "PASS"), _finding("y", "FAIL", hard_block=True)])
        == "ADMISSIBILITY_FAIL"
    )


def test_script_creates_durable_bundle(
    synthetic_archive: Path,
    synthetic_config: Path,
) -> None:
    result = run_offline_source_evidence_admissibility_review_execution_v0(
        config_path=synthetic_config,
        archive_root=synthetic_archive,
    )
    output_dir = Path(result["durable_evidence_path"])
    assert output_dir.is_dir()
    assert (output_dir / "REVIEW_RESULT.json").is_file()
    assert (output_dir / "REVIEW_FINDINGS.md").is_file()
    assert (output_dir / "PARENT_PROVENANCE.json").is_file()
    assert (output_dir / "SAFETY_BOUNDARIES.json").is_file()
    assert (output_dir / "MANIFEST.sha256").is_file()
    assert result["verdict"] in _load_config()["review_result_vocabulary"]


def test_manifest_sha256_verification(
    synthetic_archive: Path,
    synthetic_config: Path,
) -> None:
    result = run_offline_source_evidence_admissibility_review_execution_v0(
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
        run_offline_source_evidence_admissibility_review_execution_v0(
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
    bad_config = synthetic_config.parent / "bad_eval.json"
    bad_config.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        run_offline_source_evidence_admissibility_review_execution_v0(
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
    bad_config = synthetic_config.parent / "bad_evidence.json"
    bad_config.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        run_offline_source_evidence_admissibility_review_execution_v0(
            config_path=bad_config,
            archive_root=synthetic_archive,
        )
    assert exc.value.code != 0


def test_validate_config_rejects_missing_dimensions() -> None:
    cfg = _load_config()
    cfg["required_review_dimensions"] = ["source_evidence_manifest_integrity"]
    errors = validate_config(cfg)
    assert any("missing review dimensions" in error for error in errors)


def test_docs_non_authorizing_language() -> None:
    text = GOVERNANCE_DOC.read_text(encoding="utf-8")
    assert "offline-only admissibility review execution" in text
    assert "not** an economic evaluation" in text
    assert "does **not** authorize any later economic evaluation" in text
    assert "does **not** create `EconomicViabilityEvidenceV1`" in text
    assert "does **not** run backtest" in text
    assert "4913" in text
    assert "`ADMISSIBILITY_PASS`" in text
    assert "`ADMISSIBILITY_FAIL`" in text
    assert "`ADMISSIBILITY_INCONCLUSIVE`" in text


def test_final_fleet_alignment_guard_in_config() -> None:
    cfg = _load_config()
    assert cfg["final_research_fleet"] == list(FINAL_RESEARCH_FLEET)
    text = GOVERNANCE_DOC.read_text(encoding="utf-8")
    for candidate in FINAL_RESEARCH_FLEET:
        assert candidate in text
    assert "not** evaluated as new candidates" in text


def test_scope_classification_and_go_token() -> None:
    cfg = _load_config()
    assert cfg["scope_id"] == SCOPE_ID
    assert cfg["go_token"] == GO_TOKEN
    assert cfg["process_classification"] == PROCESS_CLASSIFICATION
    assert cfg["scope_classification"] == SCOPE_CLASSIFICATION


def test_next_step_mapping_on_verdict() -> None:
    cfg = _load_config()
    assert cfg["next_step_on_pass"] == NEXT_STEP_PASS
    assert cfg["next_step_on_fail_or_inconclusive"] == NEXT_STEP_FAIL
