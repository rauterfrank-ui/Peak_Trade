"""Read existing DDO owner records before admitting context-bound Pending work."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    SEAM_DOUBLE_PLAY_ENTRY_EXIT, SEAM_SPECS_V0,
)
from src.learning.deterministic_decision_outcome_v0.double_play_observation_projection_v1 import (
    generic_decision_result_for_producer_outcome_v1,
    generic_decision_type_for_producer_outcome_v1,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoError
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.ops.full_core_live_path_composition_root_v1.current_productive_pending_decision_context_v1 import (
    PendingDecisionContextV1, canonical_payload_json_v1,
)


@dataclass(frozen=True)
class PendingBoundDecisionIdentityV1:
    correlation_id: str
    policy_decision_id: str


def load_bound_pending_decision_identity_v1(
    *, ledger_path: Path, context: PendingDecisionContextV1, dpo: Mapping[str, str],
) -> PendingBoundDecisionIdentityV1 | None:
    """Validate stored DPO and its DecisionEvent using the existing ledger reader.

    Generic event enums follow the capture mapping; they cannot replace exact DP.
    This verifies present fields, not absent DecisionEvent policy/input snapshots.
    """
    try:
        records = AppendOnlyDdoLedgerV0(ledger_path.resolve()).read_all()
    except (DdoError, OSError, ValueError, TypeError):
        return None
    by_id = {record["record_id"]: record for record in records}
    observation = by_id.get(dpo.get("dpo_ref", ""))
    parent = by_id.get(dpo.get("decision_event_ref", ""))
    if observation is None or parent is None:
        return None
    if observation["schema_name"] != "double_play_entry_exit_observation":
        return None
    if parent["schema_name"] != "decision_event":
        return None
    producer = observation["producer_canonical_payload"]
    if canonical_payload_json_v1(producer) != context.producer_payload_json:
        return None
    for key in ("decision_outcome", "selected_side", "execution_eligible", "trading_epoch"):
        if str(producer[key]).lower() != str(dpo.get(key, "")).lower():
            return None
    if observation["decision_event_ref"] != parent["record_id"]:
        return None
    if observation["cycle_id"] != context.cycle_id or parent["cycle_id"] != context.cycle_id:
        return None
    for key in ("correlation_id", "event_time_utc"):
        if observation[key] != parent[key]:
            return None
    spec = SEAM_SPECS_V0[SEAM_DOUBLE_PLAY_ENTRY_EXIT]
    if parent["producer_id"] != spec.producer_id or parent["authority_owner"] != spec.authority_owner:
        return None
    expected_codes = list(producer["reason_codes"]) or ["UNKNOWN"]
    if [item["code"] for item in parent["reason_codes"]] != expected_codes:
        return None
    if any(item["source_taxonomy_ref"] != spec.source_taxonomy_ref for item in parent["reason_codes"]):
        # The existing capture uses no source ref for its explicit empty-code UNKNOWN.
        if producer["reason_codes"] or any(item["source_taxonomy_ref"] is not None for item in parent["reason_codes"]):
            return None
    if parent["hard_block_reasons"]:
        return None
    outcome = str(producer["decision_outcome"])
    if parent["decision_type"] != generic_decision_type_for_producer_outcome_v1(outcome):
        return None
    if parent["decision_result"] != generic_decision_result_for_producer_outcome_v1(outcome):
        return None
    return PendingBoundDecisionIdentityV1(
        correlation_id=str(parent["correlation_id"]),
        policy_decision_id=str(producer["policy_decision_id"]),
    )


def pending_decision_lineage_is_bound_v1(
    *, ledger_path: Path, context: PendingDecisionContextV1, dpo: Mapping[str, str],
) -> bool:
    return load_bound_pending_decision_identity_v1(
        ledger_path=ledger_path, context=context, dpo=dpo,
    ) is not None
