"""Thin offline economic evaluation adapter for cross_sectional_open_interest_delta_rank/v0.

Loads the ratified versioned binding and five-instrument self-accumulated panel, validates
digests fail-closed, and delegates to the canonical evaluation precheck owner. Does not
execute economic evaluation. Research-only; no runtime or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.research.cross_sectional_open_interest_delta_rank_v0_offline_economic_evaluation_execution_v0 import (
    ADAPTER_GO_TOKEN,
    AUTHORITY_EFFECT,
    CANONICAL_EVALUATION_CALLABLE,
    RUNTIME_EFFECT,
    OfflineEvaluationAdapterPrecheckResultV0,
    precheck_result_to_dict,
    run_offline_evaluation_adapter_precheck_v0,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0 import (
    CONFIG_REL_PATH as BINDING_CONFIG_REL_PATH,
    STRATEGY_ID,
    STRATEGY_VERSION,
    load_versioned_research_binding_v0,
    materialize_versioned_research_binding_v0,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_OFFLINE_ECONOMIC_EVALUATION_ADAPTER_V0=true"
)

SCHEMA_VERSION = (
    "cross_sectional_open_interest_delta_rank_v0_offline_economic_evaluation_adapter.v0"
)
ADAPTER_ID = "cross_sectional_open_interest_delta_rank_v0_offline_economic_evaluation_adapter_v0"
ADAPTER_VERSION = "v0"
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_open_interest_delta_rank_v0_offline_economic_evaluation_adapter_v0.json"
)

GO_TOKEN = ADAPTER_GO_TOKEN
EXECUTION_OWNER = (
    "src.research.cross_sectional_open_interest_delta_rank_v0_offline_economic_evaluation_"
    "execution_v0"
)


class AdapterTerminalStatus(str, Enum):
    ADAPTER_BINDING_COMPLETE = "ADAPTER_BINDING_COMPLETE"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class OfflineEvaluationAdapterResultV0:
    status: AdapterTerminalStatus
    adapter_binding_complete: bool
    precheck: OfflineEvaluationAdapterPrecheckResultV0
    evidence_root: str
    adapter_digest: str
    authority_effect: str
    runtime_effect: str
    economic_evaluation_executed: bool


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_adapter_config_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH
    if not path.is_file():
        return {
            "schema_version": SCHEMA_VERSION,
            "adapter_id": ADAPTER_ID,
            "adapter_version": ADAPTER_VERSION,
            "strategy_id": STRATEGY_ID,
            "strategy_version": STRATEGY_VERSION,
            "go_token": GO_TOKEN,
            "offline_only": True,
            "economic_evaluation_executed": False,
            "authority_effect": AUTHORITY_EFFECT,
            "runtime_effect": RUNTIME_EFFECT,
        }
    return json.loads(path.read_text(encoding="utf-8"))


def materialize_adapter_contract_v0() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "adapter_id": ADAPTER_ID,
        "adapter_version": ADAPTER_VERSION,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "go_token": GO_TOKEN,
        "execution_owner": EXECUTION_OWNER,
        "canonical_evaluation_callable": CANONICAL_EVALUATION_CALLABLE,
        "versioned_binding_config": BINDING_CONFIG_REL_PATH,
        "adapter_config": CONFIG_REL_PATH,
        "offline_only": True,
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def run_cross_sectional_open_interest_delta_rank_v0_offline_economic_evaluation_adapter_v0(
    *,
    repo_root: Path,
    materialization_root: Path,
    evidence_root: Path,
    go_token: str,
    versioned_binding: Mapping[str, Any] | None = None,
) -> OfflineEvaluationAdapterResultV0:
    """Thin adapter entrypoint: binding load, panel load, digest checks, precheck delegate."""
    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))
    precheck = run_offline_evaluation_adapter_precheck_v0(
        repo_root=repo_root,
        materialization_root=materialization_root,
        go_token=go_token,
        versioned_binding=envelope,
        offline_only=True,
    )

    evidence_root.mkdir(parents=True, exist_ok=True)
    adapter_payload = {
        "adapter_contract": materialize_adapter_contract_v0(),
        "versioned_binding_digest": _stable_digest(
            {
                "data_digest": envelope.get("data_digest"),
                "instrument_universe_digest": envelope.get("instrument_universe_digest"),
            }
        ),
        "precheck": precheck_result_to_dict(precheck),
        "materialization_root": str(materialization_root),
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }
    adapter_digest = _stable_digest(adapter_payload)
    (evidence_root / "adapter_binding_result.json").write_text(
        json.dumps({**adapter_payload, "adapter_digest": adapter_digest}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    adapter_binding_complete = precheck.precheck_passed
    return OfflineEvaluationAdapterResultV0(
        status=(
            AdapterTerminalStatus.ADAPTER_BINDING_COMPLETE
            if adapter_binding_complete
            else AdapterTerminalStatus.FAIL_CLOSED
        ),
        adapter_binding_complete=adapter_binding_complete,
        precheck=precheck,
        evidence_root=str(evidence_root),
        adapter_digest=adapter_digest,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
        economic_evaluation_executed=False,
    )


def adapter_result_to_dict(result: OfflineEvaluationAdapterResultV0) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "adapter_id": ADAPTER_ID,
        "adapter_version": ADAPTER_VERSION,
        "status": result.status.value,
        "adapter_binding_complete": result.adapter_binding_complete,
        "precheck": precheck_result_to_dict(result.precheck),
        "evidence_root": result.evidence_root,
        "adapter_digest": result.adapter_digest,
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "economic_evaluation_executed": result.economic_evaluation_executed,
    }
