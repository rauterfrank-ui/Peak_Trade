"""RSI-v1 ETH v2 bars bind to PEAK_TRADE_DATA_ARCHIVE_ROOT — no Documents fallback."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.backtest import (
    step30a_rsi_reversion_v1_economic_evaluation_admissibility_contract_v1 as contract,
)
from src.research.longer_chronological_pit_acquisition_v1 import ENV_ARCHIVE_ROOT
from src.research.longer_chronological_pit_acquisition_v1.archive_root import (
    RUNTIME_EVIDENCE_20260520_REL,
    ArchiveRootError,
    resolve_archive_root,
)

ROOT = Path(__file__).resolve().parents[2]
RSI_CONFIG = contract.DEFAULT_EVALUATION_CONFIG_PATH
LEGACY_DOCUMENTS_PREFIX = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)


def test_rsi_reuses_existing_archive_root_resolver() -> None:
    assert contract.resolve_archive_root is resolve_archive_root
    assert contract.DATASET_ROOT_CONTRACT == ENV_ARCHIVE_ROOT
    assert contract.DATASET_ROOT_CONTRACT == "PEAK_TRADE_DATA_ARCHIVE_ROOT"
    assert (
        contract.STEP30A_DATASET_V2_RELPATH
        == "datasets/admissible_futures/inst-eth-usdt-perp/v2/bars.parquet"
    )
    assert (
        contract.STEP30A_DATASET_V2_MANIFEST_RELPATH
        == "datasets/admissible_futures/inst-eth-usdt-perp/v2/dataset_manifest.json"
    )


def test_config_and_contract_share_root_semantics() -> None:
    cfg = contract.load_step30a_rsi_reversion_v1_evaluation_config_v1(ROOT, RSI_CONFIG)
    reasons = contract.verify_rsi_v2_dataset_root_contract_binding_v1(cfg)
    assert reasons == ()
    binding = cfg["real_admissible_futures_evaluation_binding_v1"]
    assert binding["dataset_root_contract"] == contract.DATASET_ROOT_CONTRACT
    assert binding["dataset_relpath"] == contract.STEP30A_DATASET_V2_RELPATH
    assert binding["dataset_version"] == "v2"
    assert "dataset_path" not in binding
    assert LEGACY_DOCUMENTS_PREFIX not in str(binding)
    assert binding["expected_dataset_digest"] == (
        "76b7e30b6153a8d273c63d771dbe2a232448369cd870ef3148031edd1187bc53"
    )
    assert binding["expected_manifest_digest"] == (
        "c5e9039a04521272c115e83158ba415e1b85d9fcad9658446bfb947abc77b44a"
    )


def test_env_unset_does_not_open_legacy_documents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    cfg = contract.load_step30a_rsi_reversion_v1_evaluation_config_v1(ROOT, RSI_CONFIG)
    assert contract.resolve_rsi_v2_data_archive_root() is None
    with patch.object(Path, "read_text") as read_text:
        with patch.object(Path, "is_file") as is_file:
            reasons = contract.verify_dataset_v2_digest_binding_v1(cfg)
            assert "dataset_archive_root_unset" in reasons
            read_text.assert_not_called()
            is_file.assert_not_called()
    with pytest.raises(FileNotFoundError, match="dataset_archive_root_unset"):
        contract.resolve_rsi_v2_dataset_bars_path()
    with pytest.raises(FileNotFoundError, match="dataset_archive_root_unset"):
        contract.resolve_rsi_v2_dataset_manifest_path()


def test_env_valid_temp_root_relative_join(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(tmp_path))
    expected_bars = (
        tmp_path / RUNTIME_EVIDENCE_20260520_REL / contract.STEP30A_DATASET_V2_RELPATH
    ).resolve()
    expected_manifest = (
        tmp_path / RUNTIME_EVIDENCE_20260520_REL / contract.STEP30A_DATASET_V2_MANIFEST_RELPATH
    ).resolve()
    assert contract.resolve_rsi_v2_dataset_bars_path() == expected_bars
    assert contract.resolve_rsi_v2_dataset_manifest_path() == expected_manifest
    cfg = contract.load_step30a_rsi_reversion_v1_evaluation_config_v1(ROOT, RSI_CONFIG)
    assert contract.resolve_rsi_v2_dataset_bars_path_from_config(cfg) == expected_bars
    reasons = contract.verify_dataset_v2_digest_binding_v1(cfg)
    assert reasons == ("dataset_v2_manifest_missing",)
    assert LEGACY_DOCUMENTS_PREFIX not in "".join(reasons)


def test_temp_root_existing_manifest_opens_joined_path_not_legacy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(tmp_path))
    manifest_path = (
        tmp_path / RUNTIME_EVIDENCE_20260520_REL / contract.STEP30A_DATASET_V2_MANIFEST_RELPATH
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("{}", encoding="utf-8")
    opened: list[str] = []

    def _capture(self: Path, *args: object, **kwargs: object) -> str:
        opened.append(str(self))
        raise AssertionError("read_text_probe_only")

    cfg = contract.load_step30a_rsi_reversion_v1_evaluation_config_v1(ROOT, RSI_CONFIG)
    with patch.object(Path, "read_text", _capture):
        with pytest.raises(AssertionError, match="read_text_probe_only"):
            contract.verify_dataset_v2_digest_binding_v1(cfg)
    assert opened == [str(manifest_path.resolve())]
    assert all(LEGACY_DOCUMENTS_PREFIX not in path for path in opened)


def test_repo_inner_root_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(ROOT))
    cfg = contract.load_step30a_rsi_reversion_v1_evaluation_config_v1(ROOT, RSI_CONFIG)
    with pytest.raises(ArchiveRootError, match="INSIDE_GIT_REPO"):
        contract.resolve_rsi_v2_data_archive_root()
    with pytest.raises(ArchiveRootError, match="INSIDE_GIT_REPO"):
        contract.resolve_rsi_v2_dataset_bars_path()
    reasons = contract.verify_dataset_v2_digest_binding_v1(cfg)
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
    cfg = contract.load_step30a_rsi_reversion_v1_evaluation_config_v1(ROOT, RSI_CONFIG)
    with pytest.raises(ArchiveRootError, match=match):
        contract.resolve_rsi_v2_data_archive_root()
    reasons = contract.verify_dataset_v2_digest_binding_v1(cfg)
    assert reasons == ("dataset_archive_root_invalid",)
    assert LEGACY_DOCUMENTS_PREFIX not in "".join(reasons)
