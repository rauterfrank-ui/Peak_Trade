from __future__ import annotations

import hashlib
import json
from typing import Mapping

from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
    run_integrated_offline_trading_logic_replay_v1,
)


def _canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def replay_semantic_digest_v1(result: IntegratedOfflineReplayResultV1) -> str:
    ev = result.evidence
    material = {
        "decision_outcome": ev.decision_outcome,
        "selected_side": ev.selected_side,
        "execution_eligible": ev.execution_eligible,
        "reason_codes": tuple(ev.reason_codes),
        "scope_event_ref": ev.scope_event_ref,
        "entry_exit_policy_ref": ev.entry_exit_policy_ref,
        "authority_effect": ev.authority_effect,
        "runtime_effect": ev.runtime_effect,
        "order_effect": ev.order_effect,
        "risk_sizing_effect": ev.risk_sizing_effect,
        "quantity_status": ev.quantity_status,
        "semantic_digest": ev.semantic_digest,
    }
    return hashlib.sha256(_canonical_json(material).encode("utf-8")).hexdigest()


def run_trading_logic_reference_replay_v1(
    replay_input,
) -> tuple[IntegratedOfflineReplayResultV1, str]:
    result = run_integrated_offline_trading_logic_replay_v1(replay_input)
    return result, replay_semantic_digest_v1(result)


def compare_trading_logic_preservation_v1(
    reference_digest: str,
    lab_digest: str,
) -> Mapping[str, object]:
    ok = reference_digest == lab_digest
    return {
        "TRADING_LOGIC_REFERENCE_DIGEST": reference_digest,
        "LAB_DIGEST": lab_digest,
        "TRADING_LOGIC_PRESERVATION_PASS": ok,
    }
