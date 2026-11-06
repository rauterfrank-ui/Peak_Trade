"""Read-only Cap2.3 eligibility gate on Top20 residency completion evidence.

Does not select, rank, bind, or invoke MV2/Double Play. Fail-closed when the
gate is productively enabled and residency completion cannot be proven for the
selected identity context.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.single_selected_future_policy_v1.constants_v1 import (
    CAP23_RESIDENCY_ELIGIBILITY_GATE_ENABLED,
    STATE_NO_SELECTION,
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_policy_v1.models_v1 import (
    SelectionProduceResultV1,
    SingleSelectedFutureSelectionV1,
)
from src.ops.single_selected_future_policy_v1.reason_codes_v1 import SelectionFailureCodeV1
from src.ops.single_selected_future_policy_v1.selection_v1 import _failure_selection
from src.ops.top20_opportunity_evaluation_residency_v1.constants_v1 import (
    EVENTS_FILENAME,
    STATE_COMPLETED,
    TOP20_EVALUATION_RESIDENCY_ENABLED,
)
from src.ops.top20_opportunity_evaluation_residency_v1.models_v1 import (
    EvaluationCompletionWitnessV1,
    ResidencyRuntimeConfigV1,
    residency_identity_key,
)
from src.ops.top20_opportunity_evaluation_residency_v1.persistence_v1 import load_store_v1
from src.ops.top20_opportunity_evaluation_residency_v1.residency_engine_v1 import (
    is_canonical_evaluation_complete_v1,
)


@dataclass(frozen=True)
class Cap23ResidencyEligibilityGateConfigV1:
    """Scoped activation for the read-only residency eligibility gate."""

    enabled: bool = CAP23_RESIDENCY_ELIGIBILITY_GATE_ENABLED
    residency_state_root: Path | None = None
    max_witness_age_seconds: float = 86_400.0
    scoped_productive_activation: bool = False


@dataclass(frozen=True)
class ResidencyCompletionRefV1:
    residency_epoch_id: str
    canonical_instrument_id: str
    universe_snapshot_id: str
    residency_completion_state: str
    governed_cycle_disposition: str

    def to_dict(self) -> dict[str, str]:
        return {
            "residency_epoch_id": self.residency_epoch_id,
            "canonical_instrument_id": self.canonical_instrument_id,
            "universe_snapshot_id": self.universe_snapshot_id,
            "residency_completion_state": self.residency_completion_state,
            "governed_cycle_disposition": str(self.governed_cycle_disposition),
        }


def is_cap23_residency_eligibility_gate_enabled_v1(
    *,
    gate: Cap23ResidencyEligibilityGateConfigV1,
    residency_config: ResidencyRuntimeConfigV1,
) -> bool:
    if not bool(gate.enabled):
        return False
    if not bool(residency_config.enabled):
        return False
    if gate.scoped_productive_activation:
        return True
    return bool(TOP20_EVALUATION_RESIDENCY_ENABLED)


def _load_witnesses_from_events_v1(state_root: Path) -> tuple[EvaluationCompletionWitnessV1, ...]:
    path = state_root / EVENTS_FILENAME
    if not path.is_file():
        return ()
    witnesses: list[EvaluationCompletionWitnessV1] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(row.get("event_type") or "") != "EVALUATION_OBSERVED":
            continue
        payload = row
        if "canonical_instrument_id" not in payload:
            continue
        witnesses.append(
            EvaluationCompletionWitnessV1(
                canonical_instrument_id=str(payload.get("canonical_instrument_id") or ""),
                residency_epoch_id=str(payload.get("residency_epoch_id") or ""),
                integrated_offline_replay_executed=bool(
                    payload.get("integrated_offline_replay_executed")
                ),
                governed_cycle_disposition=str(payload.get("governed_cycle_disposition") or ""),
            )
        )
    return tuple(witnesses)


def _find_completed_residency_record_v1(
    *,
    state_root: Path,
    canonical_instrument_id: str,
    universe_snapshot_id: str,
) -> Any | None:
    store = load_store_v1(state_root)
    key = residency_identity_key(
        universe_snapshot_id=universe_snapshot_id,
        canonical_instrument_id=canonical_instrument_id,
    )
    for row in store.records:
        if row.state != STATE_COMPLETED:
            continue
        row_key = residency_identity_key(
            universe_snapshot_id=row.universe_snapshot_id,
            canonical_instrument_id=row.canonical_instrument_id,
        )
        if row_key == key:
            return row
    return None


def verify_cap23_residency_eligibility_v1(
    *,
    selection: SingleSelectedFutureSelectionV1,
    ranking_snapshot: Mapping[str, Any],
    gate: Cap23ResidencyEligibilityGateConfigV1,
    producer_observed_at_unix: float,
    residency_config: ResidencyRuntimeConfigV1,
) -> tuple[bool, tuple[str, ...], ResidencyCompletionRefV1 | None]:
    if not is_cap23_residency_eligibility_gate_enabled_v1(
        gate=gate, residency_config=residency_config
    ):
        return True, (), None
    if selection.state != STATE_SELECTED_ACTIVE:
        return True, (), None
    if gate.residency_state_root is None:
        return False, (SelectionFailureCodeV1.RESIDENCY_ELIGIBILITY_WITNESS_MISSING.value,), None

    universe_snapshot_id = str(ranking_snapshot.get("universe_snapshot_id") or "").strip()
    if not universe_snapshot_id:
        return False, (SelectionFailureCodeV1.RESIDENCY_ELIGIBILITY_WITNESS_MISSING.value,), None

    state_root = Path(gate.residency_state_root)
    record = _find_completed_residency_record_v1(
        state_root=state_root,
        canonical_instrument_id=str(selection.instrument_id or "").strip(),
        universe_snapshot_id=universe_snapshot_id,
    )
    if record is None:
        return (
            False,
            (SelectionFailureCodeV1.RESIDENCY_ELIGIBILITY_RESIDENCY_INCOMPLETE.value,),
            None,
        )

    witnesses = _load_witnesses_from_events_v1(state_root)
    matching = [
        w
        for w in witnesses
        if w.residency_epoch_id == record.residency_epoch_id
        and is_canonical_evaluation_complete_v1(w)
    ]
    if not matching:
        return False, (SelectionFailureCodeV1.RESIDENCY_ELIGIBILITY_WITNESS_MISSING.value,), None

    witness = matching[-1]
    if (
        str(witness.canonical_instrument_id or "").strip()
        != str(selection.instrument_id or "").strip()
    ):
        return (
            False,
            (SelectionFailureCodeV1.RESIDENCY_ELIGIBILITY_IDENTITY_MISMATCH.value,),
            None,
        )

    age = float(producer_observed_at_unix) - float(record.residency_started_at_unix)
    if age < 0 or age > float(gate.max_witness_age_seconds):
        return False, (SelectionFailureCodeV1.RESIDENCY_ELIGIBILITY_WITNESS_STALE.value,), None

    ref = ResidencyCompletionRefV1(
        residency_epoch_id=record.residency_epoch_id,
        canonical_instrument_id=record.canonical_instrument_id,
        universe_snapshot_id=record.universe_snapshot_id,
        residency_completion_state=record.state,
        governed_cycle_disposition=witness.governed_cycle_disposition,
    )
    return True, (), ref


def apply_cap23_residency_eligibility_gate_v1(
    *,
    produced: SelectionProduceResultV1,
    ranking_snapshot: Mapping[str, Any],
    gate: Cap23ResidencyEligibilityGateConfigV1,
    residency_config: ResidencyRuntimeConfigV1,
    producer_observed_at_unix: float,
) -> tuple[SelectionProduceResultV1, ResidencyCompletionRefV1 | None]:
    ok, codes, ref = verify_cap23_residency_eligibility_v1(
        selection=produced.selection,
        ranking_snapshot=ranking_snapshot,
        gate=gate,
        producer_observed_at_unix=producer_observed_at_unix,
        residency_config=residency_config,
    )
    if ok:
        return produced, ref

    sel = produced.selection
    failed = _failure_selection(
        repository_sha=sel.repository_sha,
        config_digest=sel.config_digest,
        wall_rfc=sel.selected_at_wall_time,
        event_time=sel.ranking_event_time,
        failure_codes=tuple(dict.fromkeys(produced.failure_codes + codes)),
        ranking_snapshot_id=sel.ranking_snapshot_id,
        ranking_integrity_digest=sel.ranking_integrity_digest,
        ranking_event_time=sel.ranking_event_time,
        ranking_policy_id=sel.ranking_policy_id,
        ranking_policy_version=sel.ranking_policy_version,
        ranking_config_digest=sel.ranking_config_digest,
        upstream_rank_order_witness=sel.upstream_rank_order_witness,
        selection_input_digest=sel.selection_input_digest,
        previous=None,
        state=STATE_NO_SELECTION,
    )
    return (
        SelectionProduceResultV1(
            selection=failed,
            ok=False,
            hard_stop=True,
            failure_codes=tuple(dict.fromkeys(produced.failure_codes + codes)),
            alpha_blocked=True,
        ),
        None,
    )
