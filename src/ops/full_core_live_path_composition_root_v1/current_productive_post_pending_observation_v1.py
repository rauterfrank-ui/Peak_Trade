"""Original account-observer session at actual new-entry POST; no new GET/grant."""

from dataclasses import dataclass
from .final_order_envelope_v1 import FinalOrderEnvelopeV1, assert_envelope_unmodified_v1
from src.ops.okx_eea_private_account_state_runtime_v1.startup_source_v1 import (
    AccountObservationSourceV1,
    PendingOrdersReadbackV1,
    is_original_account_observation_source_v1,
)


class CurrentPostPendingObservationError(ValueError):
    pass


@dataclass(frozen=True)
class CurrentPostPendingContextV1:
    envelope: FinalOrderEnvelopeV1
    source: AccountObservationSourceV1
    observation: PendingOrdersReadbackV1 | None

    def inspect_v1(self, *, envelope, stage, expected_account=None):
        try:
            assert_envelope_unmodified_v1(envelope)
            if self.envelope != envelope or not is_original_account_observation_source_v1(
                self.source
            ):
                raise ValueError("ORIGINAL_SOURCE_OR_ENVELOPE_MISMATCH")
            if envelope.reduce_only is not False or not envelope.instrument_id.endswith("-SWAP"):
                raise ValueError("SUPPORTED_NEW_ENTRY_SWAP_SCOPE_REQUIRED")
            proof = self.source.inspect_pending_observation_v1(self.observation)
            if expected_account is not None and proof["account"] != expected_account:
                raise ValueError("ORIGINAL_BUDGET_ACCOUNT_MISMATCH")
            return {**proof, "envelope_digest": envelope.envelope_digest}
        except (ValueError, TypeError, AttributeError, KeyError) as exc:
            raise CurrentPostPendingObservationError(f"POST_PENDING_DENIED:{stage}:{exc}") from exc


def capture_current_post_pending_v1(*, envelope, source):
    if not is_original_account_observation_source_v1(source):
        raise CurrentPostPendingObservationError("POST_PENDING_ORIGINAL_OBSERVER_REQUIRED")
    return CurrentPostPendingContextV1(envelope, source, source.pending_observation_v1())


def inspect_current_post_pending_v1(context, *, envelope, stage, expected_account=None):
    if type(context) is not CurrentPostPendingContextV1:
        raise CurrentPostPendingObservationError(f"POST_PENDING_CONTEXT_REQUIRED:{stage}")
    return context.inspect_v1(envelope=envelope, stage=stage, expected_account=expected_account)
