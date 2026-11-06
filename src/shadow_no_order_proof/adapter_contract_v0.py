# Declarative bounded Shadow adapter proof contract (v0).
# This module MUST NOT perform I/O, network, broker, exchange, or order submission.
# Not a runtime entrypoint; not an executable command surface.

BOUNDED_SHADOW_ADAPTER_PROOF_V0 = "bounded_shadow_adapter_proof_v0"
ADAPTER_KIND = "declarative_no_order_shadow_adapter_proof"

# This declarative package remains non-executable. The proven operator entrypoint
# lives outside this package (ops orchestration CLI); flags stay False here.
PROVEN_SHADOW_NO_ORDER_ENTRYPOINT_FOUND = False
EXECUTABLE_COMMAND_CREATED = False
EXTERNAL_PROVEN_EXECUTABLE_SHADOW_NO_ORDER_ENTRYPOINT_RELPATH = (
    "scripts/ops/run_okx_futures_shadow_no_order_v0.py"
)
EXTERNAL_PROVEN_EXECUTABLE_SHADOW_NO_ORDER_ENTRYPOINT_MODULE = (
    "src.ops.okx_futures_shadow_no_order_entrypoint_v0"
)

SHADOW_MODE_ALLOWED = False
ORDER_SUBMISSION_ALLOWED = False

BROKER_ALLOWED = False
EXCHANGE_ALLOWED = False

RUNTIME_ALLOWED = False
SCHEDULER_ALLOWED = False

LIVE_ALLOWED = False
TESTNET_ALLOWED = False
PAPER_ALLOWED = False
