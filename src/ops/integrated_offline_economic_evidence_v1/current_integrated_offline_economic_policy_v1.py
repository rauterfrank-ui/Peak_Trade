"""Authoritative CURRENT integrated-offline economic sample-count policy v1 (AUTHORITY=NONE)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

CURRENT_INTEGRATED_OFFLINE_ECONOMIC_POLICY_ID = "ops.current_integrated_offline_economic_policy_v1"
CURRENT_INTEGRATED_OFFLINE_ECONOMIC_POLICY_VERSION = "v1"
CURRENT_INTEGRATED_OFFLINE_ECONOMIC_POLICY_CONFIG_RELPATH = (
    "config/ops/current_integrated_offline_economic_policy_v1.toml"
)
TRADE_COUNT_SEMANTIC_COMPLETED_POSITION_ROUND_TRIP = "COMPLETED_POSITION_ROUND_TRIP"


class CurrentIntegratedOfflineEconomicPolicyError(ValueError):
    """Fail-closed CURRENT integrated-offline economic policy error."""


@dataclass(frozen=True)
class CurrentIntegratedOfflineEconomicPolicyV1:
    policy_id: str
    policy_version: str
    minimum_trade_count: int
    trade_count_semantic: str
    trade_start_state: str
    trade_active_state: str
    trade_completion_state: str
    partial_reduce_counts_as_trade: bool
    entry_counts_as_trade: bool
    fill_counts_as_trade: bool
    closed_leg_counts_as_trade: bool
    minimum_trade_count_source_class: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "minimum_trade_count": self.minimum_trade_count,
            "trade_count_semantic": self.trade_count_semantic,
            "trade_start_state": self.trade_start_state,
            "trade_active_state": self.trade_active_state,
            "trade_completion_state": self.trade_completion_state,
            "partial_reduce_counts_as_trade": self.partial_reduce_counts_as_trade,
            "entry_counts_as_trade": self.entry_counts_as_trade,
            "fill_counts_as_trade": self.fill_counts_as_trade,
            "closed_leg_counts_as_trade": self.closed_leg_counts_as_trade,
            "minimum_trade_count_source_class": self.minimum_trade_count_source_class,
        }

    def policy_digest_sha256(self) -> str:
        payload = json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def economic_policy_reference_v1(self) -> dict[str, str]:
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "policy_digest_sha256": self.policy_digest_sha256(),
            "trade_count_semantic": self.trade_count_semantic,
        }


def _load_toml(path: Path) -> dict[str, Any]:
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover
        import tomli as tomllib  # type: ignore[no-redef]
    return tomllib.loads(path.read_text(encoding="utf-8"))


def load_current_integrated_offline_economic_policy_v1(
    *,
    repo_root: Path,
) -> CurrentIntegratedOfflineEconomicPolicyV1:
    """Load and validate authoritative CURRENT policy from config (fail-closed)."""
    path = repo_root.resolve() / CURRENT_INTEGRATED_OFFLINE_ECONOMIC_POLICY_CONFIG_RELPATH
    if not path.is_file():
        raise CurrentIntegratedOfflineEconomicPolicyError("CURRENT_POLICY_CONFIG_MISSING")
    cfg = _load_toml(path)
    policy_id = str(cfg.get("policy_id") or "")
    policy_version = str(cfg.get("policy_version") or "")
    sample = cfg.get("sample_count") if isinstance(cfg.get("sample_count"), dict) else {}
    provenance = cfg.get("provenance") if isinstance(cfg.get("provenance"), dict) else {}
    if policy_id != CURRENT_INTEGRATED_OFFLINE_ECONOMIC_POLICY_ID:
        raise CurrentIntegratedOfflineEconomicPolicyError("CURRENT_POLICY_ID_MISMATCH")
    if policy_version != CURRENT_INTEGRATED_OFFLINE_ECONOMIC_POLICY_VERSION:
        raise CurrentIntegratedOfflineEconomicPolicyError("CURRENT_POLICY_VERSION_MISMATCH")
    minimum = int(sample.get("minimum_trade_count") or 0)
    if minimum != 50:
        raise CurrentIntegratedOfflineEconomicPolicyError(
            "CURRENT_POLICY_MINIMUM_TRADE_COUNT_NOT_RATIFIED"
        )
    semantic = str(sample.get("trade_count_semantic") or "")
    if semantic != TRADE_COUNT_SEMANTIC_COMPLETED_POSITION_ROUND_TRIP:
        raise CurrentIntegratedOfflineEconomicPolicyError(
            "CURRENT_POLICY_TRADE_COUNT_SEMANTIC_MISMATCH"
        )
    for key, expected in (
        ("trade_start_state", "FLAT"),
        ("trade_active_state", "NONZERO_EXPOSURE"),
        ("trade_completion_state", "FLAT"),
    ):
        if str(sample.get(key) or "") != expected:
            raise CurrentIntegratedOfflineEconomicPolicyError(
                f"CURRENT_POLICY_{key.upper()}_MISMATCH"
            )
    for flag in (
        "partial_reduce_counts_as_trade",
        "entry_counts_as_trade",
        "fill_counts_as_trade",
        "closed_leg_counts_as_trade",
    ):
        if bool(sample.get(flag)):
            raise CurrentIntegratedOfflineEconomicPolicyError(
                f"CURRENT_POLICY_{flag.upper()}_MUST_BE_FALSE"
            )
    source_class = str(provenance.get("minimum_trade_count_source_class") or "")
    return CurrentIntegratedOfflineEconomicPolicyV1(
        policy_id=policy_id,
        policy_version=policy_version,
        minimum_trade_count=minimum,
        trade_count_semantic=semantic,
        trade_start_state=str(sample.get("trade_start_state") or ""),
        trade_active_state=str(sample.get("trade_active_state") or ""),
        trade_completion_state=str(sample.get("trade_completion_state") or ""),
        partial_reduce_counts_as_trade=False,
        entry_counts_as_trade=False,
        fill_counts_as_trade=False,
        closed_leg_counts_as_trade=False,
        minimum_trade_count_source_class=source_class,
    )


def verify_economic_policy_reference_v1(
    *,
    repo_root: Path,
    policy_ref: Mapping[str, Any] | None,
) -> tuple[CurrentIntegratedOfflineEconomicPolicyV1 | None, list[str]]:
    """Verify integrated index policy reference against authoritative CURRENT policy."""
    blockers: list[str] = []
    if not isinstance(policy_ref, dict):
        return None, ["ECONOMIC_POLICY_REFERENCE_V1_MISSING"]
    canonical = load_current_integrated_offline_economic_policy_v1(repo_root=repo_root)
    for key in ("policy_id", "policy_version", "policy_digest_sha256"):
        if not str(policy_ref.get(key) or ""):
            blockers.append(f"POLICY:{key.upper()}_MISSING")
    if blockers:
        return None, blockers
    if str(policy_ref.get("policy_id") or "") != canonical.policy_id:
        blockers.append("POLICY:POLICY_ID_MISMATCH")
    if str(policy_ref.get("policy_version") or "") != canonical.policy_version:
        blockers.append("POLICY:POLICY_VERSION_MISMATCH")
    if str(policy_ref.get("policy_digest_sha256") or "") != canonical.policy_digest_sha256():
        blockers.append("POLICY:POLICY_DIGEST_MISMATCH")
    ref_semantic = str(policy_ref.get("trade_count_semantic") or "")
    if ref_semantic and ref_semantic != canonical.trade_count_semantic:
        blockers.append("POLICY:TRADE_COUNT_SEMANTIC_MISMATCH")
    if blockers:
        return None, blockers
    return canonical, []


def resolve_productive_current_minimum_trade_count_v1(
    *,
    repo_root: Path,
    index_doc: Mapping[str, Any],
) -> tuple[int | None, list[str]]:
    """Resolve minimum_trade_count for PRODUCTIVE_CURRENT adjudication (fail-closed)."""
    binding = index_doc.get("canonical_identity_binding_v1")
    if not isinstance(binding, dict):
        return None, ["CANONICAL_IDENTITY_BINDING_V1_MISSING"]
    policy_ref = binding.get("economic_policy_reference_v1")
    policy, blockers = verify_economic_policy_reference_v1(
        repo_root=repo_root,
        policy_ref=policy_ref if isinstance(policy_ref, dict) else None,
    )
    if blockers or policy is None:
        return None, blockers
    return policy.minimum_trade_count, []
