"""F2 Step29M config authority tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.backtest.okx_eth_perp_research_cost_grid_v1_constants import SOURCE_STEP29M_CONFIG
from src.experiments.f2_step29m_config_authority_v1 import (
    F2Step29mConfigAuthorityError,
    IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY,
    resolve_f2_step29m_config_authority_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_f2_config_authority_is_unique_and_matches_ssot() -> None:
    authority = resolve_f2_step29m_config_authority_v1(repo_root=REPO_ROOT)
    assert authority.authoritative_config_rel_path == SOURCE_STEP29M_CONFIG
    assert authority.strategy_id == "ma_crossover"
    assert len(authority.dataset_digest) == 64
    assert authority.instrument_id == "inst-eth-usdt-perp"


def test_f2_config_authority_fail_closed_on_divergent_template(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.experiments.f2_step29m_config_authority_v1 as authority_mod

    real_load = authority_mod._load_json_mapping

    def _patched_load(root: Path, rel: str) -> dict:
        payload = dict(real_load(root, rel))
        if rel.endswith("step29m_current_single_selected_future_dynamic_binding_v1.json"):
            payload["evaluation_config_template_path"] = "config/ops/other.json"
        return payload

    monkeypatch.setattr(authority_mod, "_load_json_mapping", _patched_load)
    with pytest.raises(
        F2Step29mConfigAuthorityError, match=IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY
    ):
        resolve_f2_step29m_config_authority_v1(repo_root=REPO_ROOT)
