"""Closure proof for F1/M9 real productive apply governed preparation v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.explicit_productive_authorization_v1 import AUTHORIZED_FOR_PRODUCTIVE_APPLY
from src.governance.f1_m9_canonical_productive_candidate_adjudication_v1 import (
    adjudicate_canonical_f1_m9_productive_candidate_v1,
)
from src.governance.f1_m9_productive_apply_durable_ledger_paths_v1 import (
    resolve_canonical_f1_m9_productive_apply_ledger_paths_v1,
)
from src.governance.f1_m9_productive_apply_execution_boundary_v1 import (
    DECISION_CONFIG,
    NEXT_TRUE_BLOCKER,
    PRODUCTIVE_APPLY_OCCURRED,
    load_execution_boundary_decision_v1,
)
from src.governance.f1_m9_productive_apply_execution_closure_v1 import (
    prove_f1_m9_productive_apply_execution_boundary_v1,
)
from src.governance.f1_m9_real_productive_apply_decision_binding_v1 import (
    prove_decision_binding_contract_v1,
)
from src.governance.governed_productive_configuration_v1 import runtime_apply_possible_v1
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

SCHEMA_VERSION: Final[str] = "f1_m9_real_productive_apply_preparation_closure/v1"
WORKPACKAGE_ID: Final[str] = "F1_M9_REAL_PRODUCTIVE_APPLY_GOVERNED_PREPARATION_V1"
PREPARATION_NORMATIVE: Final[str] = (
    "docs/ops/specs/F1_M9_REAL_PRODUCTIVE_APPLY_GOVERNED_PREPARATION_NORMATIVE_V1.md"
)


def prove_f1_m9_real_productive_apply_governed_preparation_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    required = (
        root / PREPARATION_NORMATIVE,
        root / "src/governance/f1_m9_real_productive_apply_decision_binding_v1.py",
        root / "src/governance/f1_m9_canonical_productive_candidate_adjudication_v1.py",
        root / "src/governance/f1_m9_productive_apply_durable_ledger_paths_v1.py",
        root / "src/governance/f1_m9_owner_apply_record_materialization_v1.py",
        root / "tests/governance/test_f1_m9_real_productive_apply_governed_preparation_v1.py",
    )
    if not all(path.is_file() for path in required):
        return False
    if not prove_f1_m9_productive_apply_execution_boundary_v1(repo_root=root):
        return False
    if not prove_decision_binding_contract_v1(repo_root=root):
        return False
    if PRODUCTIVE_APPLY_OCCURRED:
        return False
    if int(PRODUCTIVE_NUMERIC_VALUES_SET) != 0:
        return False
    if runtime_apply_possible_v1() is not False:
        return False
    if AUTHORIZED_FOR_PRODUCTIVE_APPLY is not False:
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    if decision.get("governed_preparation_implemented") is not True:
        return False
    handoff_decision_path = decision.get("post_real_campaign_handoff_decision")
    if isinstance(handoff_decision_path, str):
        handoff_path = root / handoff_decision_path
        if handoff_path.is_file():
            handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
            if handoff.get("bounded_handoff_complete") is True:
                if decision.get("real_productive_apply_authorized") is not True:
                    return False
                if decision.get("canonical_productive_candidate_resolved") is not True:
                    return False
                adjudication = adjudicate_canonical_f1_m9_productive_candidate_v1(repo_root=root)
                if not adjudication.resolved:
                    return False
                try:
                    _ = resolve_canonical_f1_m9_productive_apply_ledger_paths_v1(repo_root=root)
                except Exception:
                    return False
                return True
    if decision.get("real_productive_apply_authorized") is True:
        return False
    if decision.get("productive_apply_occurred") is True:
        return False
    if decision.get("next_true_blocker") != NEXT_TRUE_BLOCKER:
        return False
    if decision.get("canonical_productive_candidate_resolved") is True:
        return False
    adjudication = adjudicate_canonical_f1_m9_productive_candidate_v1(repo_root=root)
    if adjudication.resolved:
        return False
    try:
        _ = resolve_canonical_f1_m9_productive_apply_ledger_paths_v1(repo_root=root)
    except Exception:
        return False
    return True


__all__ = [
    "PREPARATION_NORMATIVE",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "prove_f1_m9_real_productive_apply_governed_preparation_v1",
]
