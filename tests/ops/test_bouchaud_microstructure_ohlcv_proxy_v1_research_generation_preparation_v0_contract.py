"""Contract tests for bouchaud_microstructure_ohlcv_proxy/v1 research generation preparation v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from src.research.bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0 import (
    CONFIG_REL_PATH,
    DATASET_DIGEST,
    DATASET_ID,
    FEATURE_NAMES,
    GOVERNANCE_REL_PATH,
    HYPOTHESIS_ID,
    OPERATOR_GO_TOKEN,
    PREPARATION_ID,
    RESEARCH_SCOPE,
    TARGET_NAME,
    TARGET_SHIFT,
    build_hypothesis_contract,
    compute_preparation_digest,
    is_unsupported_microstructure_feature_rejected,
    load_fixture_bars_v0,
    materialize_and_validate_feature_matrix_v0,
    materialize_preparation_config,
    serialize_canonical_json,
    validate_no_lookahead_contract_v0,
    validate_source_evidence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / CONFIG_REL_PATH
GOVERNANCE_DOC = REPO_ROOT / GOVERNANCE_REL_PATH
FIXTURE_PATH = (
    REPO_ROOT
    / "tests/fixtures/bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0/"
    "truth_pack_bars.json"
)
OWNER_MODULE = (
    REPO_ROOT
    / "src/research/bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0.py"
)

FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
    "src.orders",
)


class TestResearchGenerationPreparationModule:
    def test_fixture_truth_pack_deterministic_digest(self) -> None:
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        bars = pd.DataFrame(payload["bars"])
        rows, binding, digest = materialize_and_validate_feature_matrix_v0(bars)
        assert len(rows) == payload["expected_row_count"]
        assert digest == payload["expected_feature_digest"]
        assert binding.feature_names == FEATURE_NAMES
        assert binding.target_name == TARGET_NAME

    def test_no_lookahead_contract(self) -> None:
        bars = load_fixture_bars_v0(REPO_ROOT)
        rows, _, _ = materialize_and_validate_feature_matrix_v0(bars)
        contract = validate_no_lookahead_contract_v0(rows)
        assert contract["no_lookahead"] is True
        assert contract["target_shift"] == TARGET_SHIFT
        assert contract["ohlcv_proxy_is_not_true_order_book_microstructure"] is True

    def test_unsupported_microstructure_features_rejected(self) -> None:
        assert is_unsupported_microstructure_feature_rejected("true_order_book_imbalance")
        assert is_unsupported_microstructure_feature_rejected("tick_level_trade_sign")
        assert not is_unsupported_microstructure_feature_rejected(FEATURE_NAMES[0])

    def test_source_evidence_manifest_verification(self) -> None:
        evidence = validate_source_evidence()
        assert evidence["source_manifest_verify_rc"] == 0

    def test_no_runtime_or_scheduler_imports(self) -> None:
        source = OWNER_MODULE.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source

    def test_preparation_config_deterministic(self) -> None:
        bars = load_fixture_bars_v0(REPO_ROOT)
        rows, _, digest = materialize_and_validate_feature_matrix_v0(bars)
        first = materialize_preparation_config(REPO_ROOT, rows=rows, feature_digest=digest)
        second = materialize_preparation_config(REPO_ROOT, rows=rows, feature_digest=digest)
        assert first == second
        assert first["preparation_digest"] == compute_preparation_digest(first)


class TestResearchGenerationPreparationConfig:
    def test_config_exists_when_materialized(self) -> None:
        if not CONFIG_PATH.is_file():
            bars = load_fixture_bars_v0(REPO_ROOT)
            rows, _, digest = materialize_and_validate_feature_matrix_v0(bars)
            envelope = materialize_preparation_config(REPO_ROOT, rows=rows, feature_digest=digest)
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(
                json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        assert payload["artifact_kind"] == PREPARATION_ID
        assert payload["go_token"] == OPERATOR_GO_TOKEN
        assert payload["research_scope"] == RESEARCH_SCOPE
        assert payload["hypothesis_id"] == HYPOTHESIS_ID
        assert payload["dataset_id"] == DATASET_ID
        assert payload["dataset_digest"] == DATASET_DIGEST
        assert payload["bitcoin_present"] is False
        assert payload["futures_only"] is True
        assert payload["feature_count"] == len(FEATURE_NAMES)
        assert payload["target_name"] == TARGET_NAME
        assert payload["target_shift"] == TARGET_SHIFT
        assert payload["ohlcv_proxy_is_not_true_order_book_microstructure"] is True
        assert payload["economic_evaluation_status"]["economic_evaluation_executed"] is False
        assert payload["runtime_effect"] == "NONE"
        assert payload["authority_effect"] == "NONE"
        assert payload["implementation_admissibility"]["implementation_admissible"] is True
        assert payload["preparation_digest"] == compute_preparation_digest(payload)

    def test_hypothesis_contract_fields(self) -> None:
        contract = build_hypothesis_contract()
        assert contract["research_scope"] == RESEARCH_SCOPE
        assert contract["proxy_semantics"] is True
        assert contract["true_tick_l2_microstructure"] is False
        assert contract["economic_evaluation_executed"] is False

    def test_canonical_serialization_stable(self) -> None:
        if CONFIG_PATH.is_file():
            payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            assert serialize_canonical_json(payload) == serialize_canonical_json(payload)


class TestResearchGenerationPreparationGovernance:
    def test_governance_doc_exists_and_states_non_claim(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert "OHLCV_PROXY_IS_NOT_TRUE_ORDER_BOOK_MICROSTRUCTURE" in body
        assert OPERATOR_GO_TOKEN in body
        assert "economic_evaluation_executed" in body.lower() or "No economic evaluation" in body

    def test_governance_doc_runtime_boundary(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert re.search(r"RUNTIME_EFFECT.*NONE", body)
        assert re.search(r"AUTHORITY_EFFECT.*NONE", body)
