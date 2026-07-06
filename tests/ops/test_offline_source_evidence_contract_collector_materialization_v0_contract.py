"""Contract and collector tests for offline source evidence contract materialization v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256, write_manifest_sha256
from scripts.research.offline_source_evidence_contract_collector_materialization_v0 import (
    CONTRACT_IDS,
    OPERATOR_GO,
    PARENT_EVALUATION_SUFFIX,
    PARENT_PR4909_MATERIALIZATION_SUFFIX,
    PARENT_PR4911_CLOSEOUT_SUFFIX,
    run_offline_source_evidence_contract_collector_materialization_v0,
)
from src.research.offline_source_evidence_contract_collector_materialization_v0 import (
    EXECUTION_ID,
    EXECUTION_STATUS,
    FORBIDDEN_RUNTIME_IMPORTS,
    PROCESS_CLASSIFICATION,
    REQUIRED_FIELDS_BY_CONTRACT,
    SCOPE_CLASSIFICATION,
    SCOPE_ID,
    collect_all_contracts,
    deterministic_collection_digest,
    missing_value,
    validate_record_fields,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTION_CONFIG = (
    REPO_ROOT / "config/research/offline_source_evidence_contract_collector_materialization_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/OFFLINE_SOURCE_EVIDENCE_CONTRACT_COLLECTOR_MATERIALIZATION_V0.md"
)
COLLECTOR_OWNER = (
    REPO_ROOT / "src/research/offline_source_evidence_contract_collector_materialization_v0.py"
)
RUNNER_SCRIPT = (
    REPO_ROOT / "scripts/research/offline_source_evidence_contract_collector_materialization_v0.py"
)
PR4911_CONFIG = (
    REPO_ROOT / "config/research/offline_source_evidence_instrumentation_admissibility_gap_v0.json"
)
BASELINE_HEAD = "0b307dc027a274d0d5f0df07b96d6c593c761331"
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
PARENT_PR4911_CLOSEOUT_DIR = ARCHIVE_ROOT / "implementation" / PARENT_PR4911_CLOSEOUT_SUFFIX
PARENT_PR4909_MATERIALIZATION_BUNDLE = (
    ARCHIVE_ROOT / "implementation" / PARENT_PR4909_MATERIALIZATION_SUFFIX
)
PARENT_EVALUATION_BUNDLE = ARCHIVE_ROOT / "implementation" / PARENT_EVALUATION_SUFFIX
REQUIRED_OUTPUTS = (
    "SOURCE_EVIDENCE_COLLECTION_REPORT.json",
    "parent_manifest_verification.json",
    "execution_summary.json",
    "AUTHORITY_BOUNDARY.txt",
    "MANIFEST.sha256",
    *[f"{contract_id}.json" for contract_id in CONTRACT_IDS],
    *[f"{contract_id}.jsonl" for contract_id in CONTRACT_IDS],
)
FORBIDDEN_RUNTIME_ACTIONS = (
    "RUNTIME",
    "SHADOW",
    "PAPER",
    "TESTNET",
    "SCHEDULER",
    "ORDERS",
    "CREDENTIALS",
    "ARMING",
    "LIVE",
)
BOUNDARY_PHRASES = (
    "Keine neue Economic Evaluation",
    "SOURCE_EVIDENCE_ONLY",
    "NO_ECONOMIC_CLAIM",
    "NO_RUNTIME_AUTHORITY",
    "FAILED_EVIDENCE_IS_TERMINAL=true",
    "MISSING_SOURCE_EVIDENCE",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


@pytest.fixture
def synthetic_parent_bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / "parent_evaluation"
    bundle.mkdir()
    for candidate in ("trend_following", "bollinger_bands", "momentum_1h"):
        (bundle / f"CANDIDATE_RESULT_{candidate}.json").write_text(
            json.dumps(
                {
                    "canonical_candidate_identifier": f"{candidate}/post_v4_hypothesis_v0",
                    "evidence_status": "ROBUSTNESS_FAILED",
                    "gross_return": 0.01,
                    "net_return": -0.02,
                    "evaluation_timestamp": "2026-07-06T04:00:00Z",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (bundle / f"ECONOMIC_VIABILITY_EVIDENCE_{candidate}.json").write_text(
            json.dumps(
                {
                    "instrument_id_or_universe": "ETH-USDT-SWAP",
                    "turnover": {
                        "semantic": "NOT_COMPUTED",
                        "reason_code": "turnover_not_computed",
                    },
                    "fee_drag": {
                        "semantic": "NOT_COMPUTED",
                        "reason_code": "fee_drag_not_computed",
                    },
                    "long_contribution": {
                        "semantic": "NOT_COMPUTED",
                        "reason_code": "long_contribution_not_computed",
                    },
                    "short_contribution": {
                        "semantic": "NOT_COMPUTED",
                        "reason_code": "short_contribution_not_computed",
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
    write_manifest_sha256(bundle)
    return bundle


class TestOfflineSourceEvidenceContractCollectorMaterializationV0Contract:
    def test_scope_config_core_fields(self) -> None:
        config = json.loads(EXECUTION_CONFIG.read_text(encoding="utf-8"))
        assert config["scope_id"] == SCOPE_ID
        assert config["execution_id"] == EXECUTION_ID
        assert config["verdict"] == EXECUTION_STATUS
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["scope_classification"] == SCOPE_CLASSIFICATION
        assert config["go_token"] == OPERATOR_GO
        assert config["baseline_head"] == BASELINE_HEAD
        assert config["source_evidence_only"] is True
        assert config["no_economic_claim"] is True
        assert config["no_runtime_authority"] is True
        assert config["failed_evidence_is_terminal"] is True
        assert config["economic_evaluation_executed"] is False
        assert config["runtime_authority_granted"] is False
        assert config["orders_allowed"] is False
        assert config["contracts_targeted"] == list(CONTRACT_IDS)

    def test_governance_doc_exists_with_docs_token(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_OFFLINE_SOURCE_EVIDENCE_CONTRACT_COLLECTOR_MATERIALIZATION_V0"
            )
            in body
        )
        assert f"`GO_TOKEN` | `{OPERATOR_GO}`" in body
        assert "`FAILED_EVIDENCE_IS_TERMINAL` | `true`" in body
        assert "`ECONOMIC_EVALUATION_EXECUTED` | `false`" in body

    def test_governance_doc_boundary_phrases(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body

    def test_governance_doc_forbidden_runtime_actions(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        for action in FORBIDDEN_RUNTIME_ACTIONS:
            assert action in body

    def test_pr4911_contract_fields_are_subset_of_collector_owner(self) -> None:
        pr4911 = json.loads(PR4911_CONFIG.read_text(encoding="utf-8"))
        for contract in pr4911["source_evidence_contracts"]:
            contract_id = contract["contract_id"]
            owner_fields = set(REQUIRED_FIELDS_BY_CONTRACT[contract_id])
            for field in contract["required_fields"]:
                assert field in owner_fields, f"{contract_id}.{field}"

    def test_collector_owner_has_no_forbidden_runtime_imports(self) -> None:
        owner_source = COLLECTOR_OWNER.read_text(encoding="utf-8")
        runner_source = RUNNER_SCRIPT.read_text(encoding="utf-8")
        for token in FORBIDDEN_RUNTIME_IMPORTS:
            assert token not in owner_source
            assert token not in runner_source

    def test_validate_record_fields_detects_missing(self) -> None:
        errors = validate_record_fields({"strategy_id": "x"}, ("strategy_id", "manifest_ref"))
        assert errors == ["missing_field:manifest_ref"]

    def test_collect_all_contracts_on_synthetic_parent(self, synthetic_parent_bundle: Path) -> None:
        digest = "abc123"
        result = collect_all_contracts(
            parent_evaluation_ref=synthetic_parent_bundle,
            parent_manifest_digest=digest,
        )
        assert not result["validation_errors"]
        for contract_id in CONTRACT_IDS:
            records = result["contracts"][contract_id]["records"]
            assert records, contract_id
            for record in records:
                assert record["manifest_ref"] == digest
                assert not validate_record_fields(record, REQUIRED_FIELDS_BY_CONTRACT[contract_id])

    def test_deterministic_collection_digest_is_stable(self, synthetic_parent_bundle: Path) -> None:
        collection = collect_all_contracts(
            parent_evaluation_ref=synthetic_parent_bundle,
            parent_manifest_digest="stable",
        )
        first = deterministic_collection_digest(collection["contracts"])
        second = deterministic_collection_digest(collection["contracts"])
        assert first == second

    @pytest.mark.skipif(
        not PARENT_EVALUATION_BUNDLE.is_dir(),
        reason="durable archive parent bundle unavailable",
    )
    def test_end_to_end_collector_materialization_against_archive(self, tmp_path: Path) -> None:
        result = run_offline_source_evidence_contract_collector_materialization_v0(
            go_token=OPERATOR_GO,
            parent_pr4911_closeout_dir=PARENT_PR4911_CLOSEOUT_DIR,
            parent_pr4909_materialization_bundle=PARENT_PR4909_MATERIALIZATION_BUNDLE,
            parent_evaluation_bundle=PARENT_EVALUATION_BUNDLE,
            durable_archive_root=tmp_path,
        )
        output_dir = Path(result["durable_evidence_path"])
        assert result["verdict"] == EXECUTION_STATUS
        assert result["manifest_verify_rc"] == 0
        for name in REQUIRED_OUTPUTS:
            assert (output_dir / name).is_file(), name
        ok, _ = verify_manifest_sha256(output_dir)
        assert ok
        report = json.loads((output_dir / "SOURCE_EVIDENCE_COLLECTION_REPORT.json").read_text())
        assert report["source_evidence_only"] is True
        assert report["no_economic_claim"] is True
        assert report["authority_boundary"]["economic_evaluation_executed"] is False
        assert report["authority_boundary"]["runtime_authority_granted"] is False

    def test_invalid_go_token_rejected(self, synthetic_parent_bundle: Path, tmp_path: Path) -> None:
        closeout = tmp_path / "closeout"
        closeout.mkdir()
        mat = tmp_path / "mat"
        mat.mkdir()
        write_manifest_sha256(closeout)
        write_manifest_sha256(mat)
        with pytest.raises(SystemExit):
            run_offline_source_evidence_contract_collector_materialization_v0(
                go_token="INVALID",
                parent_pr4911_closeout_dir=closeout,
                parent_pr4909_materialization_bundle=mat,
                parent_evaluation_bundle=synthetic_parent_bundle,
                durable_archive_root=tmp_path / "out_root",
            )

    def test_missing_manifest_blocks_collection(
        self, synthetic_parent_bundle: Path, tmp_path: Path
    ) -> None:
        closeout = tmp_path / "closeout"
        closeout.mkdir()
        mat = tmp_path / "mat"
        mat.mkdir()
        (closeout / "MANIFEST.sha256").write_text("deadbeef  tampered.txt\n", encoding="utf-8")
        write_manifest_sha256(mat)
        with pytest.raises(SystemExit):
            run_offline_source_evidence_contract_collector_materialization_v0(
                go_token=OPERATOR_GO,
                parent_pr4911_closeout_dir=closeout,
                parent_pr4909_materialization_bundle=mat,
                parent_evaluation_bundle=synthetic_parent_bundle,
                durable_archive_root=tmp_path / "out_root2",
            )

    def test_long_short_records_include_missing_source_sentinel(
        self, synthetic_parent_bundle: Path
    ) -> None:
        result = collect_all_contracts(
            parent_evaluation_ref=synthetic_parent_bundle,
            parent_manifest_digest="digest",
        )
        record = result["contracts"]["LONG_SHORT_ATTRIBUTION_LEDGER_V0"]["records"][0]
        assert record["turnover"]["status"] == "MISSING_SOURCE_EVIDENCE"

    def test_missing_value_helper(self) -> None:
        value = missing_value(reason_code="example")
        assert value["status"] == "MISSING_SOURCE_EVIDENCE"
        assert value["reason_code"] == "example"
