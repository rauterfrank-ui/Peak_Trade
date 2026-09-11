"""Ehlers-v1 ETH bars bind to PEAK_TRADE_DATA_ARCHIVE_ROOT — no Documents fallback."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from src.backtest import (
    step29m_ehlers_cycle_filter_v1_economic_evaluation_admissibility_contract_v1 as contract,
)
from src.research.longer_chronological_pit_acquisition_v1 import ENV_ARCHIVE_ROOT
from src.research.longer_chronological_pit_acquisition_v1.archive_root import (
    RUNTIME_EVIDENCE_20260520_REL,
    ArchiveRootError,
    resolve_archive_root,
)

ROOT = Path(__file__).resolve().parents[2]
EHLERS_OPS_CONFIG = contract.DEFAULT_EVALUATION_CONFIG_PATH
EHLERS_RESEARCH_CONFIGS = (
    "config/research/ehlers_cycle_filter_v1_offline_economic_evaluation_scope_ratification_v0.json",
    "config/research/ehlers_cycle_filter_v1_versioned_research_binding_v0.json",
)
RUNNER_PATH = (
    ROOT / "scripts/ops/run_ehlers_cycle_filter_v1_bound_offline_economic_baseline_evaluation_v0.py"
)
LEGACY_DOCUMENTS_PREFIX = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)


def _research_dataset_binding(rel: str) -> dict:
    payload = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    if "dataset_binding" in payload:
        return payload["dataset_binding"]
    return payload["binding"]["dataset_binding"]


def test_ehlers_reuses_existing_archive_root_resolver() -> None:
    assert contract.resolve_archive_root is resolve_archive_root
    assert contract.DATASET_ROOT_CONTRACT == ENV_ARCHIVE_ROOT
    assert contract.DATASET_ROOT_CONTRACT == "PEAK_TRADE_DATA_ARCHIVE_ROOT"
    assert (
        contract.EHLERS_V1_DATASET_RELPATH
        == "datasets/admissible_futures/inst-eth-usdt-perp/v1/bars.parquet"
    )
    assert (
        contract.EHLERS_V1_DATASET_MANIFEST_RELPATH
        == "datasets/admissible_futures/inst-eth-usdt-perp/v1/dataset_manifest.json"
    )


def test_ops_config_and_contract_share_root_semantics() -> None:
    cfg = contract.load_ehlers_cycle_filter_v1_evaluation_config_v1(ROOT, EHLERS_OPS_CONFIG)
    reasons = contract.verify_ehlers_v1_dataset_root_contract_binding_v1(cfg)
    assert reasons == ()
    binding = cfg["real_admissible_futures_evaluation_binding_v1"]
    assert binding["dataset_root_contract"] == contract.DATASET_ROOT_CONTRACT
    assert binding["dataset_relpath"] == contract.EHLERS_V1_DATASET_RELPATH
    assert "dataset_path" not in binding
    assert LEGACY_DOCUMENTS_PREFIX not in str(binding)
    assert binding["expected_dataset_digest"] == (
        "39286384bb5baca27c93cae04716de9d8638ac62ab7d01a64c0a74c535e8d087"
    )
    assert binding["expected_manifest_digest"] == (
        "f250627c19f59b1c3245b0a5da69a646671210a1717609367f22b94d3a2a7059"
    )


def test_research_configs_rebind_dataset_path_only() -> None:
    for rel in EHLERS_RESEARCH_CONFIGS:
        binding = _research_dataset_binding(rel)
        assert binding["dataset_root_contract"] == contract.DATASET_ROOT_CONTRACT
        assert binding["dataset_relpath"] == contract.EHLERS_V1_DATASET_RELPATH
        assert binding["dataset_version"] == "v1"
        assert "dataset_path" not in binding
        assert LEGACY_DOCUMENTS_PREFIX not in str(binding)


def test_research_evidence_refs_use_archive_relative_locators() -> None:
    payload = json.loads((ROOT / EHLERS_RESEARCH_CONFIGS[1]).read_text(encoding="utf-8"))
    assert payload["canonical_evaluation_bundle"].startswith(RUNTIME_EVIDENCE_20260520_REL)
    assert payload["classification_evidence_ref"].startswith(RUNTIME_EVIDENCE_20260520_REL)
    assert payload["durable_evidence_refs"].startswith(RUNTIME_EVIDENCE_20260520_REL)
    assert LEGACY_DOCUMENTS_PREFIX not in payload["canonical_evaluation_bundle"]
    assert LEGACY_DOCUMENTS_PREFIX not in payload["classification_evidence_ref"]
    assert LEGACY_DOCUMENTS_PREFIX not in payload["durable_evidence_refs"]


def test_env_unset_does_not_open_legacy_documents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    cfg = contract.load_ehlers_cycle_filter_v1_evaluation_config_v1(ROOT, EHLERS_OPS_CONFIG)
    assert contract.resolve_ehlers_v1_data_archive_root() is None
    with patch.object(pd, "read_parquet") as read_parquet:
        with patch.object(Path, "read_text") as read_text:
            with patch.object(Path, "is_file") as is_file:
                reasons = contract.verify_ehlers_v1_dataset_manifest_availability_v1(cfg)
                assert reasons == ("dataset_archive_root_unset",)
                read_parquet.assert_not_called()
                read_text.assert_not_called()
                is_file.assert_not_called()
    with pytest.raises(FileNotFoundError, match="dataset_archive_root_unset"):
        contract.resolve_ehlers_v1_dataset_bars_path()
    with pytest.raises(FileNotFoundError, match="dataset_archive_root_unset"):
        contract.resolve_ehlers_v1_dataset_manifest_path()
    with pytest.raises(FileNotFoundError, match="dataset_archive_root_unset"):
        contract.resolve_ehlers_v1_dataset_bars_path_from_config(cfg)


def test_env_valid_temp_root_relative_join(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(tmp_path))
    expected_bars = (
        tmp_path / RUNTIME_EVIDENCE_20260520_REL / contract.EHLERS_V1_DATASET_RELPATH
    ).resolve()
    expected_manifest = (
        tmp_path / RUNTIME_EVIDENCE_20260520_REL / contract.EHLERS_V1_DATASET_MANIFEST_RELPATH
    ).resolve()
    assert contract.resolve_ehlers_v1_dataset_bars_path() == expected_bars
    assert contract.resolve_ehlers_v1_dataset_manifest_path() == expected_manifest
    cfg = contract.load_ehlers_cycle_filter_v1_evaluation_config_v1(ROOT, EHLERS_OPS_CONFIG)
    assert contract.resolve_ehlers_v1_dataset_bars_path_from_config(cfg) == expected_bars
    reasons = contract.verify_ehlers_v1_dataset_manifest_availability_v1(cfg)
    assert reasons == ("dataset_manifest_missing",)
    assert LEGACY_DOCUMENTS_PREFIX not in "".join(reasons)


def test_temp_root_existing_manifest_opens_joined_path_not_legacy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(tmp_path))
    manifest_path = (
        tmp_path / RUNTIME_EVIDENCE_20260520_REL / contract.EHLERS_V1_DATASET_MANIFEST_RELPATH
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("{}", encoding="utf-8")
    cfg = contract.load_ehlers_cycle_filter_v1_evaluation_config_v1(ROOT, EHLERS_OPS_CONFIG)
    reasons = contract.verify_ehlers_v1_dataset_manifest_availability_v1(cfg)
    assert reasons == ()
    with patch.object(pd, "read_parquet") as read_parquet:
        read_parquet.assert_not_called()
    assert LEGACY_DOCUMENTS_PREFIX not in str(contract.resolve_ehlers_v1_dataset_manifest_path())


def test_repo_inner_root_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(ROOT))
    cfg = contract.load_ehlers_cycle_filter_v1_evaluation_config_v1(ROOT, EHLERS_OPS_CONFIG)
    with pytest.raises(ArchiveRootError, match="INSIDE_GIT_REPO"):
        contract.resolve_ehlers_v1_data_archive_root()
    with pytest.raises(ArchiveRootError, match="INSIDE_GIT_REPO"):
        contract.resolve_ehlers_v1_dataset_bars_path()
    reasons = contract.verify_ehlers_v1_dataset_manifest_availability_v1(cfg)
    assert reasons == ("dataset_archive_root_invalid",)
    assert LEGACY_DOCUMENTS_PREFIX not in "".join(reasons)


@pytest.mark.parametrize(
    ("raw_root", "match"),
    (
        ("/", "ARCHIVE_ROOT_IS_FILESYSTEM_ROOT"),
        (str(Path.home()), "ARCHIVE_ROOT_IS_HOME_DIRECTORY"),
        ("relative-not-absolute", "ARCHIVE_ROOT_INSIDE_GIT_REPO"),
    ),
)
def test_invalid_archive_roots_rejected(
    monkeypatch: pytest.MonkeyPatch,
    raw_root: str,
    match: str,
) -> None:
    monkeypatch.chdir(ROOT)
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, raw_root)
    cfg = contract.load_ehlers_cycle_filter_v1_evaluation_config_v1(ROOT, EHLERS_OPS_CONFIG)
    with pytest.raises(ArchiveRootError, match=match):
        contract.resolve_ehlers_v1_data_archive_root()
    reasons = contract.verify_ehlers_v1_dataset_manifest_availability_v1(cfg)
    assert reasons == ("dataset_archive_root_invalid",)
    assert LEGACY_DOCUMENTS_PREFIX not in "".join(reasons)


def test_runner_resolves_via_contract_and_keeps_durable_evidence_default() -> None:
    source = RUNNER_PATH.read_text(encoding="utf-8")
    assert 'eval_binding["dataset_path"]' not in source
    assert "resolve_ehlers_v1_dataset_bars_path_from_config" in source
    assert "resolve_ehlers_v1_dataset_manifest_path" in source
    assert "pd.read_parquet(dataset_path)" in source
    assert "--durable-evidence-root" in source
    default_block = source.split("--durable-evidence-root", 1)[1]
    assert "located_runtime_evidence_20260520" in default_block
    assert LEGACY_DOCUMENTS_PREFIX not in default_block.split("parser.add_argument", 1)[0]
