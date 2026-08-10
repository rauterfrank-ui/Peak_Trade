"""Unknown-submit fail-closed helpers for productive §11.12.8 campaign path.

Reuses Cap 11.5 refuse_unknown_submit_blind_retry semantics. Never performs
network I/O. Never invents exchange ACK/state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.unknown_submit_reconnect_recovery_contract_v1 import (
    refuse_unknown_submit_blind_retry_v1,
)


class ActualStartUnknownSubmitError(RuntimeError):
    """Fail-closed unknown-submit / unparsed transport violation."""


_UNKNOWN_CLASSIFICATIONS: frozenset[str] = frozenset(
    {
        "TRANSPORT_RESPONSE_UNPARSED",
        "UNKNOWN",
        "UNKNOWN_SUBMIT",
        "TIMEOUT_UNKNOWN",
    }
)


@dataclass(frozen=True)
class UnknownSubmitDecisionV1:
    hard_stop: bool
    blind_resubmit_forbidden: bool
    classification: str
    client_order_id: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "hard_stop": self.hard_stop,
            "blind_resubmit_forbidden": self.blind_resubmit_forbidden,
            "classification": self.classification,
            "client_order_id": self.client_order_id,
            "reason": self.reason,
        }


def classify_unknown_or_unproven_submit_v1(
    *,
    effect: Mapping[str, Any] | None,
    client_order_id: str,
) -> UnknownSubmitDecisionV1 | None:
    """Return a hard-stop decision when exchange state is not provable.

    Returns None when the effect is a normal ACK/REJECT/stub/no-op.
    """
    if not effect:
        return None
    classification = str(
        effect.get("response_classification") or effect.get("classification") or ""
    ).strip()
    wire_sent = bool(effect.get("wire_sent"))
    ack = bool(effect.get("order_acknowledged") or effect.get("exchange_accepted"))
    rejected = bool(effect.get("exchange_rejected"))
    stubbed = bool(effect.get("stubbed"))
    if stubbed or (not wire_sent):
        return None
    if ack or rejected:
        return None
    if classification in _UNKNOWN_CLASSIFICATIONS or (wire_sent and not ack and not rejected):
        return UnknownSubmitDecisionV1(
            hard_stop=True,
            blind_resubmit_forbidden=True,
            classification=classification or "UNPROVEN_EXCHANGE_STATE",
            client_order_id=str(client_order_id),
            reason="UNKNOWN_OR_UNPROVEN_SUBMIT_STATE_HARD_STOP",
        )
    return None


def enforce_unknown_submit_fail_closed_v1(
    *,
    effect: Mapping[str, Any] | None,
    client_order_id: str,
) -> UnknownSubmitDecisionV1 | None:
    """Hard-stop unknown/unproven submits; never allow blind resubmit."""
    decision = classify_unknown_or_unproven_submit_v1(
        effect=effect, client_order_id=client_order_id
    )
    if decision is None:
        return None
    # Reuse Cap 11.5 blind-retry refuse semantics (raises).
    try:
        refuse_unknown_submit_blind_retry_v1(client_order_id=client_order_id)
    except Exception as exc:  # noqa: BLE001 — convert to local fail-closed error
        raise ActualStartUnknownSubmitError(
            f"{decision.reason}:{decision.classification}:{exc}"
        ) from exc
    raise ActualStartUnknownSubmitError(
        f"{decision.reason}:{decision.classification}:{client_order_id}"
    )
