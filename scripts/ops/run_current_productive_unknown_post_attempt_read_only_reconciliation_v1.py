#!/usr/bin/env python3
"""Read-only reconciliation for UNKNOWN actual-venue POST attempts. No mutation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _main() -> int:
    parser = argparse.ArgumentParser(description="UNKNOWN POST read-only reconciliation")
    parser.add_argument("--client-order-id", required=True)
    parser.add_argument("--instrument-id", required=True)
    parser.add_argument("--inst-type", default="SWAP")
    parser.add_argument("--pretrade-decision-id", default="unknown-post-read-only-reconciliation-v1")
    args = parser.parse_args()

    from src.ops.full_core_live_path_composition_root_v1.current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1 import (
        K1_OPAQUE_SIGNING_OWNER_GO,
        resolve_macos_security_framework_k1_lookup_backend_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1 import (
        open_current_productive_k1_opaque_signing_handle_session_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
        FullCoreProductiveReadOnlyGetTransportV1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_unknown_post_attempt_read_only_reconciliation_v1 import (
        reconcile_unknown_post_attempt_read_only_v1,
    )

    backend = resolve_macos_security_framework_k1_lookup_backend_v1(
        k1_owner_go=K1_OPAQUE_SIGNING_OWNER_GO
    )
    with open_current_productive_k1_opaque_signing_handle_session_v1(
        owner_go=K1_OPAQUE_SIGNING_OWNER_GO,
        backend=backend,
    ) as session:
        transport = FullCoreProductiveReadOnlyGetTransportV1(
            handle=session.signing_handle,
            max_request_count=12,
        )
        result = reconcile_unknown_post_attempt_read_only_v1(
            client_order_id=args.client_order_id,
            instrument_id=args.instrument_id,
            inst_type=args.inst_type,
            read_only_get_transport=transport,
            pretrade_decision_id=args.pretrade_decision_id,
        )
    print(
        json.dumps(
            {
                "CLIENT_ORDER_ID": result.client_order_id,
                "READ_ONLY_REQUESTS_PERFORMED": result.read_only_requests_performed,
                "ORDER_FOUND": result.order_found,
                "RECONCILIATION_RESULT": result.reconciliation_result,
                "EXTERNAL_EFFECT_CONFIRMED": result.external_effect_confirmed,
                "EXACT_ORDER_LOOKUP_PERFORMED": result.exact_order_lookup_performed,
                "SURFACES": list(result.surfaces_summary),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
