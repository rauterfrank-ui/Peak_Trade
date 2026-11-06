"""Single canonical execution/accounting writer boundary.

Multiple instrument intents funnel into exactly one existing writer pair.
No per-instrument execution writer. No second accounting writer.
"""

from __future__ import annotations

from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    CANONICAL_ACCOUNTING_WRITER_IDENTITY,
    CANONICAL_EXECUTION_WRITER_IDENTITY,
    SECOND_ACCOUNTING_AUTHORITY_CREATED,
    SECOND_EXECUTION_AUTHORITY_CREATED,
    SUBMIT_UNLOCKED,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    IntentV1,
    R6S3RuntimeArchitectureError,
    WriterBundleV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.constants_v1 import (
    SINGLE_WRITER_IDENTITY as ACCOUNTING_WRITER,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.constants_v1 import (
    SIMULATED_EXECUTION_PORT_OWNER,
)


def _reject(message: str) -> None:
    raise R6S3RuntimeArchitectureError(message)


def bind_single_writer_v1(
    intents: tuple[IntentV1, ...],
    *,
    authorized: bool,
) -> WriterBundleV1:
    if SECOND_EXECUTION_AUTHORITY_CREATED is not False:
        _reject("second_execution_authority_created")
    if SECOND_ACCOUNTING_AUTHORITY_CREATED is not False:
        _reject("second_accounting_authority_created")
    if CANONICAL_ACCOUNTING_WRITER_IDENTITY != ACCOUNTING_WRITER:
        _reject("accounting_writer_identity_drift")
    if SIMULATED_EXECUTION_PORT_OWNER not in CANONICAL_EXECUTION_WRITER_IDENTITY:
        _reject("execution_writer_identity_drift")
    if authorized is True:
        _reject("writer_cannot_honor_authorized_true")
    identities = {
        "execution": {CANONICAL_EXECUTION_WRITER_IDENTITY},
        "accounting": {CANONICAL_ACCOUNTING_WRITER_IDENTITY},
    }
    if len(identities["execution"]) != 1 or len(identities["accounting"]) != 1:
        _reject("writer_identity_not_unique")
    return WriterBundleV1(
        execution_writer_identity=CANONICAL_EXECUTION_WRITER_IDENTITY,
        accounting_writer_identity=CANONICAL_ACCOUNTING_WRITER_IDENTITY,
        intents=intents,
        durable_before_submit=True,
        submit_unlocked=bool(SUBMIT_UNLOCKED and authorized),
    )
