"""F2 Step29M evaluation config authority v1 — fail-closed single-path binding proof.

Resolves the owner-authoritative Step29M config for F2 research execution only.
Does not authorize selection, promotion, or alternate strategy configs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.backtest.okx_eth_perp_research_cost_grid_v1_constants import (
    BASELINE_FEE_BPS,
    BASELINE_SLIPPAGE_BPS,
    GRID_ID,
    OPERATOR_BOUND_FEE_BPS,
    OPERATOR_BOUND_SLIPPAGE_BPS,
    SOURCE_STEP29M_CONFIG,
)
from src.backtest.step29m_current_single_selected_future_dynamic_binding_v1 import (
    CONTRACT_CONFIG_REL_PATH,
    DEFAULT_EVALUATION_CONFIG_TEMPLATE_REL,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "f2_step29m_config_authority_v1"
IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY: Final[str] = "IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY"
ALLOWED_POLICY_DOMAIN_REF: Final[str] = (
    "config/governance/optimizable_envelope/"
    "research_backtest_cost_grid_allowed_policy_domain_v1.json"
)


class F2Step29mConfigAuthorityError(ValueError):
    """Fail-closed F2 Step29M config authority error."""


@dataclass(frozen=True, slots=True)
class F2Step29mConfigAuthorityV1:
    schema_version: str
    authoritative_config_rel_path: str
    config_content_digest: str
    strategy_id: str
    strategy_version: str
    dataset_digest: str
    instrument_id: str
    authority_evidence_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "authoritative_config_rel_path": self.authoritative_config_rel_path,
            "config_content_digest": self.config_content_digest,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "dataset_digest": self.dataset_digest,
            "instrument_id": self.instrument_id,
            "authority_evidence_refs": list(self.authority_evidence_refs),
        }


def _repo_root(repo_root: Path | None) -> Path:
    return repo_root or Path(__file__).resolve().parents[2]


def _load_json_mapping(root: Path, rel_path: str) -> dict[str, Any]:
    path = root / rel_path
    if not path.is_file():
        raise F2Step29mConfigAuthorityError(
            f"{IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY}:missing_authority_ref:{rel_path}"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise F2Step29mConfigAuthorityError(
            f"{IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY}:authority_ref_not_mapping:{rel_path}"
        )
    return payload


def _validate_grid_matches_f2_domain(cfg: Mapping[str, Any]) -> None:
    backtest = cfg.get("backtest")
    if not isinstance(backtest, Mapping):
        raise F2Step29mConfigAuthorityError(
            f"{IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY}:missing_backtest_section"
        )
    section = backtest.get("parameter_sensitivity")
    if not isinstance(section, Mapping) or section.get("bind") is not True:
        raise F2Step29mConfigAuthorityError(
            f"{IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY}:parameter_sensitivity_not_bound"
        )
    grid = section.get("grid")
    if not isinstance(grid, Mapping):
        raise F2Step29mConfigAuthorityError(
            f"{IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY}:missing_parameter_grid"
        )
    if grid.get("grid_id") != GRID_ID:
        raise F2Step29mConfigAuthorityError(
            f"{IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY}:grid_id_mismatch"
        )
    fee = tuple(float(v) for v in grid.get("parameter_values", ())[0])
    slip = tuple(float(v) for v in grid.get("parameter_values", ())[1])
    if fee != OPERATOR_BOUND_FEE_BPS or slip != OPERATOR_BOUND_SLIPPAGE_BPS:
        raise F2Step29mConfigAuthorityError(
            f"{IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY}:grid_values_not_operator_bound"
        )
    if float(backtest.get("fee_bps", -1)) != BASELINE_FEE_BPS:
        raise F2Step29mConfigAuthorityError(
            f"{IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY}:baseline_fee_mismatch"
        )
    if float(backtest.get("slippage_bps", -1)) != BASELINE_SLIPPAGE_BPS:
        raise F2Step29mConfigAuthorityError(
            f"{IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY}:baseline_slippage_mismatch"
        )


def resolve_f2_step29m_config_authority_v1(
    *, repo_root: Path | None = None
) -> F2Step29mConfigAuthorityV1:
    """Prove a single owner-authoritative Step29M config path for F2 (fail-closed)."""
    root = _repo_root(repo_root)
    candidate_paths: set[str] = {
        SOURCE_STEP29M_CONFIG,
        DEFAULT_EVALUATION_CONFIG_TEMPLATE_REL,
    }
    binding_cfg = _load_json_mapping(root, CONTRACT_CONFIG_REL_PATH)
    template_path = str(binding_cfg.get("evaluation_config_template_path") or "")
    if template_path:
        candidate_paths.add(template_path)
    domain_cfg = _load_json_mapping(root, ALLOWED_POLICY_DOMAIN_REF)
    source_module = str(domain_cfg.get("source_constant_module") or "")
    if source_module != "src/backtest/okx_eth_perp_research_cost_grid_v1_constants.py":
        raise F2Step29mConfigAuthorityError(
            f"{IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY}:allowed_domain_source_module_mismatch"
        )
    if len(candidate_paths) != 1:
        raise F2Step29mConfigAuthorityError(
            f"{IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY}:ambiguous_config_paths:"
            f"{sorted(candidate_paths)}"
        )
    authoritative = SOURCE_STEP29M_CONFIG
    if candidate_paths != {authoritative}:
        raise F2Step29mConfigAuthorityError(
            f"{IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY}:authority_refs_diverge:"
            f"{sorted(candidate_paths)}"
        )

    cfg = _load_json_mapping(root, authoritative)
    _validate_grid_matches_f2_domain(cfg)
    eval_section = cfg.get("economic_evaluation_v1")
    if not isinstance(eval_section, Mapping):
        raise F2Step29mConfigAuthorityError(
            f"{IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY}:missing_economic_evaluation_v1"
        )
    strategy_id = str(eval_section.get("strategy_id") or "")
    if not strategy_id:
        raise F2Step29mConfigAuthorityError(
            f"{IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY}:strategy_id_missing"
        )
    real_binding = cfg.get("real_admissible_futures_evaluation_binding_v1")
    if not isinstance(real_binding, Mapping):
        raise F2Step29mConfigAuthorityError(
            f"{IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY}:missing_real_admissible_binding"
        )
    dataset_digest = str(real_binding.get("expected_dataset_digest") or "")
    if not is_valid_sha256_hex(dataset_digest):
        raise F2Step29mConfigAuthorityError(
            f"{IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY}:invalid_expected_dataset_digest"
        )
    instrument_id = str(real_binding.get("canonical_instrument_id") or "")
    if not instrument_id:
        raise F2Step29mConfigAuthorityError(
            f"{IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY}:canonical_instrument_id_missing"
        )

    return F2Step29mConfigAuthorityV1(
        schema_version=SCHEMA_VERSION,
        authoritative_config_rel_path=authoritative,
        config_content_digest=compute_content_sha256(cfg),
        strategy_id=strategy_id,
        strategy_version="v1",
        dataset_digest=dataset_digest,
        instrument_id=instrument_id,
        authority_evidence_refs=(
            "src/backtest/okx_eth_perp_research_cost_grid_v1_constants.py#SOURCE_STEP29M_CONFIG",
            CONTRACT_CONFIG_REL_PATH,
            ALLOWED_POLICY_DOMAIN_REF,
        ),
    )


def load_f2_authoritative_step29m_config_v1(
    *, repo_root: Path | None = None
) -> MappingProxyType[str, Any]:
    authority = resolve_f2_step29m_config_authority_v1(repo_root=repo_root)
    root = _repo_root(repo_root)
    cfg = _load_json_mapping(root, authority.authoritative_config_rel_path)
    return MappingProxyType(dict(cfg))
