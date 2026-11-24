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
    execution_environment: str = "LIVE"

    def inspect_v1(self, *, envelope, stage, expected_account=None, execution_environment="LIVE"):
        try:
            assert_envelope_unmodified_v1(envelope)
            if self.envelope != envelope or not is_original_account_observation_source_v1(
                self.source
            ):
                raise ValueError("ORIGINAL_SOURCE_OR_ENVELOPE_MISMATCH")
            if self.execution_environment != execution_environment or execution_environment not in {
                "LIVE",
                "TESTNET",
            }:
                raise ValueError("PENDING_EXECUTION_ENVIRONMENT_MISMATCH")
            demo = execution_environment == "TESTNET"
            from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
                K1AccountObservationSourceV1,
            )

            if type(self.source) is K1AccountObservationSourceV1 and (
                self.source.credential.execution_environment != execution_environment
                or self.source.transport._transport.execution_environment != execution_environment
            ):
                raise ValueError("PENDING_SIGNER_ENVIRONMENT_MISMATCH")
            if demo:
                if (
                    type(self.source) is not K1AccountObservationSourceV1
                    or not self.source.account_inventory_guard
                    or self.source.inventory_inst_type != "FUTURES"
                    or self.source.credential.execution_environment != "TESTNET"
                    or self.source.transport._transport.execution_environment != "TESTNET"
                    or envelope.instrument_id != "BTC-USD_UM_XPERP-310328"
                ):
                    raise ValueError("BTC_DEMO_PENDING_ORIGINAL_FUTURES_SCOPE_REQUIRED")
            if envelope.reduce_only is not False or (
                not demo and not envelope.instrument_id.endswith("-SWAP")
            ):
                raise ValueError("SUPPORTED_NEW_ENTRY_SWAP_SCOPE_REQUIRED")
            proof = self.source.inspect_pending_observation_v1(self.observation)
            if expected_account is not None and proof["account"] != expected_account:
                raise ValueError("ORIGINAL_BUDGET_ACCOUNT_MISMATCH")
            return {**proof, "envelope_digest": envelope.envelope_digest}
        except (ValueError, TypeError, AttributeError, KeyError) as exc:
            raise CurrentPostPendingObservationError(f"POST_PENDING_DENIED:{stage}:{exc}") from exc


def capture_current_post_pending_v1(*, envelope, source, execution_environment="LIVE"):
    if not is_original_account_observation_source_v1(source):
        raise CurrentPostPendingObservationError("POST_PENDING_ORIGINAL_OBSERVER_REQUIRED")
    return CurrentPostPendingContextV1(
        envelope, source, source.pending_observation_v1(), execution_environment
    )


def inspect_current_post_pending_v1(
    context, *, envelope, stage, expected_account=None, execution_environment="LIVE"
):
    if type(context) is not CurrentPostPendingContextV1:
        raise CurrentPostPendingObservationError(f"POST_PENDING_CONTEXT_REQUIRED:{stage}")
    return context.inspect_v1(
        envelope=envelope,
        stage=stage,
        expected_account=expected_account,
        execution_environment=execution_environment,
    )
