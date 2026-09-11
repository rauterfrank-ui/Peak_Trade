"""MACD-v1 ETH bars bind to PEAK_TRADE_DATA_ARCHIVE_ROOT — no Documents fallback."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from src.backtest import step29m_macd_v1_economic_evaluation_admissibility_contract_v1 as contract
from src.research.longer_chronological_pit_acquisition_v1 import ENV_ARCHIVE_ROOT
from src.research.longer_chronological_pit_acquisition_v1.archive_root import (
    RUNTIME_EVIDENCE_20260520_REL,
    ArchiveRootError,
    resolve_archive_root,
)

ROOT = Path(__file__).resolve().parents[2]
MACD_CONFIGS = (
    "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v1.json",
    "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v2.json",
    "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v3.json",
)
LEGACY_DOCUMENTS_PREFIX = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)


def test_macd_reuses_existing_archive_root_resolver() -> None:
    assert contract.resolve_archive_root is resolve_archive_root
    assert contract.DATASET_ROOT_CONTRACT == ENV_ARCHIVE_ROOT
    assert contract.DATASET_ROOT_CONTRACT == "PEAK_TRADE_DATA_ARCHIVE_ROOT"
    assert (
        contract.MACD_V1_DATASET_RELPATH
        == "datasets/admissible_futures/inst-eth-usdt-perp/v1/bars.parquet"
    )


def test_configs_and_contract_share_root_semantics() -> None:
    for rel in MACD_CONFIGS:
        cfg = contract.load_macd_v1_evaluation_config_v1(ROOT, rel)
        reasons = contract.verify_macd_v1_dataset_root_contract_binding_v1(cfg)
        assert reasons == ()
        binding = cfg["real_admissible_futures_evaluation_binding_v1"]
        assert binding["dataset_root_contract"] == contract.DATASET_ROOT_CONTRACT
        assert binding["dataset_relpath"] == contract.MACD_V1_DATASET_RELPATH
        assert "dataset_path" not in binding
        assert LEGACY_DOCUMENTS_PREFIX not in str(binding)


def test_env_unset_does_not_open_legacy_documents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    assert contract.resolve_macd_v1_data_archive_root() is None
    with patch.object(pd, "read_parquet") as read_parquet:
        with pytest.raises(FileNotFoundError, match="dataset_archive_root_unset"):
            contract.load_admissible_okx_eth_bars_v1()
        read_parquet.assert_not_called()
    with pytest.raises(FileNotFoundError, match="dataset_archive_root_unset"):
        contract.resolve_macd_v1_dataset_bars_path()


def test_env_valid_temp_root_relative_join(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(tmp_path))
    expected = (
        tmp_path / RUNTIME_EVIDENCE_20260520_REL / contract.MACD_V1_DATASET_RELPATH
    ).resolve()
    assert contract.resolve_macd_v1_dataset_bars_path() == expected
    cfg = contract.load_macd_v1_evaluation_config_v1(ROOT, MACD_CONFIGS[0])
    assert contract.resolve_macd_v1_dataset_bars_path_from_config(cfg) == expected
    with patch.object(pd, "read_parquet") as read_parquet:
        with pytest.raises(FileNotFoundError, match="dataset_bars_missing"):
            contract.load_admissible_okx_eth_bars_v1()
        read_parquet.assert_not_called()
        err = None
        try:
            contract.load_admissible_okx_eth_bars_v1()
        except FileNotFoundError as exc:
            err = str(exc)
        assert err is not None
        assert LEGACY_DOCUMENTS_PREFIX not in err
        assert str(expected) in err


def test_temp_root_existing_file_opens_joined_path_not_legacy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(tmp_path))
    bars_path = tmp_path / RUNTIME_EVIDENCE_20260520_REL / contract.MACD_V1_DATASET_RELPATH
    bars_path.parent.mkdir(parents=True)
    bars_path.write_bytes(b"not-a-parquet")
    opened: list[str] = []

    def _capture(path: object, *args: object, **kwargs: object) -> pd.DataFrame:
        opened.append(str(path))
        raise AssertionError("read_parquet_probe_only")

    with patch.object(pd, "read_parquet", side_effect=_capture):
        with pytest.raises(AssertionError, match="read_parquet_probe_only"):
            contract.load_admissible_okx_eth_bars_v1()
    assert opened == [str(bars_path.resolve())]
    assert all(LEGACY_DOCUMENTS_PREFIX not in path for path in opened)


def test_repo_inner_root_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(ROOT))
    with pytest.raises(ArchiveRootError, match="INSIDE_GIT_REPO"):
        contract.resolve_macd_v1_data_archive_root()
    with pytest.raises(FileNotFoundError, match="dataset_archive_root_invalid"):
        contract.load_admissible_okx_eth_bars_v1()
