"""Load and validate Paper-Shadow Run-1 contract JSON (immutable bounds)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class RunContractError(ValueError):
    pass


@dataclass(frozen=True)
class PaperShadowRunContractV1:
    run_id: str
    run_type: str
    run_duration_seconds: int
    max_observation_count: int
    max_cycle_count: int
    max_simulated_execution_count: int
    max_simulated_open_position_count: int
    enter_required_for_success: bool
    fixpoint_sha: str
    fixpoint_tree: str
    settings_digest: str
    observation_source: str
    execution_sink: str
    ghv_control_fixpoint_sha: str
    raw: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "RUN_ID": self.run_id,
            "RUN_TYPE": self.run_type,
            "RUN_DURATION_SECONDS": self.run_duration_seconds,
            "MAX_OBSERVATION_COUNT": self.max_observation_count,
            "MAX_CYCLE_COUNT": self.max_cycle_count,
            "MAX_SIMULATED_EXECUTION_COUNT": self.max_simulated_execution_count,
            "MAX_SIMULATED_OPEN_POSITION_COUNT": self.max_simulated_open_position_count,
            "ENTER_REQUIRED_FOR_SUCCESS": self.enter_required_for_success,
            "FIXPOINT_SHA": self.fixpoint_sha,
            "FIXPOINT_TREE": self.fixpoint_tree,
            "SETTINGS_DIGEST": self.settings_digest,
            "OBSERVATION_SOURCE": self.observation_source,
            "EXECUTION_SINK": self.execution_sink,
            "GHV_CONTROL_FIXPOINT_SHA": self.ghv_control_fixpoint_sha,
        }


def _require_int(raw: dict[str, Any], key: str) -> int:
    if key not in raw:
        raise RunContractError(f"missing_contract_field:{key}")
    try:
        return int(raw[key])
    except (TypeError, ValueError) as exc:
        raise RunContractError(f"invalid_int:{key}") from exc


def load_paper_shadow_run_contract_v1(
    *,
    contract_path: Path,
    settings_digest_path: Path | None = None,
) -> PaperShadowRunContractV1:
    path = Path(contract_path).resolve()
    if not path.is_file():
        raise RunContractError(f"contract_not_found:{path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    digest = str(raw.get("SETTINGS_DIGEST") or "").strip()
    if not digest and settings_digest_path is not None:
        sp = Path(settings_digest_path).resolve()
        if sp.is_file():
            digest = str(json.loads(sp.read_text(encoding="utf-8")).get("SETTINGS_DIGEST") or "")
    if not digest:
        raise RunContractError("SETTINGS_DIGEST_REQUIRED")

    run_id = str(raw.get("RUN_ID") or "").strip()
    if run_id != "PAPER_SHADOW_RUN_001":
        raise RunContractError("RUN_ID_MUST_BE_PAPER_SHADOW_RUN_001")

    fixpoint = str(raw.get("FIXPOINT_SHA") or "").strip()
    tree = str(raw.get("FIXPOINT_TREE") or "").strip()
    if len(fixpoint) != 40 or len(tree) != 40:
        raise RunContractError("FIXPOINT_SHA_TREE_REQUIRED")

    return PaperShadowRunContractV1(
        run_id=run_id,
        run_type=str(raw.get("RUN_TYPE") or "BOUNDED_PAPER_SHADOW"),
        run_duration_seconds=_require_int(raw, "RUN_DURATION_SECONDS"),
        max_observation_count=_require_int(raw, "MAX_OBSERVATION_COUNT"),
        max_cycle_count=_require_int(raw, "MAX_CYCLE_COUNT"),
        max_simulated_execution_count=_require_int(raw, "MAX_SIMULATED_EXECUTION_COUNT"),
        max_simulated_open_position_count=_require_int(raw, "MAX_SIMULATED_OPEN_POSITION_COUNT"),
        enter_required_for_success=bool(raw.get("ENTER_REQUIRED_FOR_SUCCESS", False)),
        fixpoint_sha=fixpoint,
        fixpoint_tree=tree,
        settings_digest=digest,
        observation_source=str(raw.get("OBSERVATION_SOURCE") or "wallclock_public_md_observe_v1"),
        execution_sink=str(raw.get("EXECUTION_SINK") or "SIMULATED_ONLY"),
        ghv_control_fixpoint_sha=str(raw.get("GHV_CONTROL_FIXPOINT_SHA") or fixpoint),
        raw=raw,
    )
