"""Evidence separation: Demo private account observation != O4 REAL_PUBLIC outcome."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.constants_v1 import (
    ACCOUNT_OBSERVATION_EVIDENCE_CLASS,
    OUTCOME_EVIDENCE_CLASS_UNCHANGED,
)

EVIDENCE_BASENAME = "ghv_testnet_demo_private_account_observation_v1.json"


def write_demo_account_observation_evidence_v1(
    *,
    evidence_root: Path,
    observation_summary: Mapping[str, Any],
) -> Path:
    payload = {
        "evidence_class": ACCOUNT_OBSERVATION_EVIDENCE_CLASS,
        "strategy_outcome_evidence_class": OUTCOME_EVIDENCE_CLASS_UNCHANGED,
        "demo_account_observation_is_strategy_pnl": False,
        "demo_account_observation_is_o4_outcome_truth": False,
        "observation_summary": dict(observation_summary),
    }
    path = Path(evidence_root) / EVIDENCE_BASENAME
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def prove_outcome_closure_evidence_separation_v1() -> dict[str, str]:
    return {
        "O4_EVIDENCE_CLASS": OUTCOME_EVIDENCE_CLASS_UNCHANGED,
        "DEMO_ACCOUNT_OBSERVATION_EVIDENCE_CLASS": ACCOUNT_OBSERVATION_EVIDENCE_CLASS,
        "DEMO_ACCOUNT_OBSERVATION_EQ_O4_OUTCOME": "false",
    }
