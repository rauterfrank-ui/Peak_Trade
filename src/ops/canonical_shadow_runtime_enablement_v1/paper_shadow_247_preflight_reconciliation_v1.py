"""Reconcile PAPER_SHADOW_247 preflight vs canonical Shadow activatable state."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PREFLIGHT_CONFIG_RELPATH = "config/ops/paper_shadow_247_preflight.toml"


@dataclass(frozen=True)
class PaperShadow247PreflightReconciliationV1:
    preflight_contract_status: str
    technical_readiness: bool
    operator_authorization: bool
    runtime_activation: bool
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "PREFLIGHT_CONTRACT_STATUS": self.preflight_contract_status,
            "TECHNICAL_READINESS": self.technical_readiness,
            "OPERATOR_AUTHORIZATION": self.operator_authorization,
            "RUNTIME_ACTIVATION": self.runtime_activation,
            "blockers": list(self.blockers),
        }


def _load_preflight_flags(repo_root: Path) -> dict[str, Any]:
    path = repo_root / PREFLIGHT_CONFIG_RELPATH
    if not path.is_file():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def evaluate_paper_shadow_247_preflight_reconciliation_v1(
    *,
    repo_root: Path | None = None,
    shadow_implemented: bool,
    shadow_activatable: bool,
    shadow_authorized: bool,
) -> PaperShadow247PreflightReconciliationV1:
    """Distinguish BLOCKED vs READY_BUT_NOT_AUTHORIZED without lifting preflight contract."""
    root = (repo_root or Path(__file__).resolve().parents[3]).resolve()
    flags = _load_preflight_flags(root)
    blockers: list[str] = []
    if not flags:
        blockers.append("PREFLIGHT_CONFIG_MISSING")

    runtime_auth = bool(flags.get("shadow_runtime_authorized", False))
    daemon_auth = bool(flags.get("daemon_activation_authorized", False))
    operator_authorization = runtime_auth or daemon_auth

    technical = shadow_implemented and shadow_activatable
    runtime_activation = shadow_authorized and operator_authorization

    if not technical:
        status = "BLOCKED_TECHNICAL"
        if not shadow_implemented:
            blockers.append("SHADOW_NOT_IMPLEMENTED")
        if not shadow_activatable:
            blockers.append("SHADOW_NOT_ACTIVATABLE")
    elif not operator_authorization:
        status = "READY_BUT_NOT_AUTHORIZED"
        blockers.append("PREFLIGHT_OPERATOR_AUTHORIZATION_ABSENT")
    elif not shadow_authorized:
        status = "READY_BUT_NOT_AUTHORIZED"
        blockers.append("SHADOW_RUNTIME_GO_NOT_CONSUMED")
    else:
        status = "AUTHORIZED_PENDING_BOUNDED_RUN"
        blockers.append("OPERATIONAL_RUN_OUT_OF_SCOPE_FOR_THIS_WP")

    return PaperShadow247PreflightReconciliationV1(
        preflight_contract_status=status,
        technical_readiness=technical,
        operator_authorization=operator_authorization,
        runtime_activation=runtime_activation,
        blockers=tuple(blockers),
    )
