#!/usr/bin/env python3
"""Bounded productive OKX read-only GET validation (reconciliation allowlist). No POST."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _origin_main_sha() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "origin/main"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return str(proc.stdout or "").strip()


def _main() -> int:
    parser = argparse.ArgumentParser(
        description="GHV bounded OKX productive read-only reconciliation GET validation"
    )
    parser.add_argument("--instrument-id", default="0G-USDT-SWAP")
    parser.add_argument("--inst-type", default="SWAP")
    parser.add_argument("--pretrade-decision-id", default="ghv-okx-productive-get-validation-v1")
    parser.add_argument("--work-package-owner-go", default="GRANTED")
    parser.add_argument("--private-get-go", default="GRANTED_SCOPED_READ_ONLY")
    parser.add_argument("--offline-implementation-go", default="GRANTED")
    parser.add_argument(
        "--origin-main-sha",
        default="",
        help="Must match git origin/main (default: resolve locally)",
    )
    parser.add_argument(
        "--skip-network",
        action="store_true",
        help="Phase-7 gates only; no Keychain or HTTP",
    )
    args = parser.parse_args()

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    from src.ops.full_core_live_path_composition_root_v1.full_core_orchestrated_post_submit_lifecycle_reconciliation_v1 import (
        LifecycleReconciliationOrchestrationMode,
        PostSubmitLifecycleReconciliationOrchestrationRequestV1,
        RECONCILIATION_READ_ONLY_GET_ALLOWLIST,
    )
    from src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_productive_read_only_reconciliation_get_validation_v1 import (
        evaluate_productive_get_safety_gates_v1,
        run_bounded_productive_okx_read_only_validation_session_v1,
    )

    origin_sha = str(args.origin_main_sha or "").strip() or _origin_main_sha()
    gate_request = PostSubmitLifecycleReconciliationOrchestrationRequestV1(
        mode=LifecycleReconciliationOrchestrationMode.PRODUCTIVE_OKX_SCOPED_READ_ONLY,
        work_package_owner_go=str(args.work_package_owner_go),
        private_get_go=str(args.private_get_go),
        offline_implementation_go=str(args.offline_implementation_go),
        origin_main_sha=origin_sha,
        decision_outcome="VALIDATION_ONLY",
        venue_plan_identity="validation-vp",
        envelope_identity="validation-env",
        submit_attempt_id="validation-submit",
        local_durable_state_version="validation-v1",
        pretrade_decision_id=str(args.pretrade_decision_id),
    )
    gates = evaluate_productive_get_safety_gates_v1(
        offline_reproof_pass=True,
        adversarial_review_pass=True,
        orchestration_request=gate_request,
    )
    report: dict[str, object] = {
        "WORK_PACKAGE": "GHV_CURRENT_OKX_PRODUCTIVE_GET_ACTIVATION_READINESS_V1",
        "ORIGIN_MAIN_SHA": origin_sha,
        "PHASE_7_SAFETY_GATES": gates.to_dict(),
        "GET_ENDPOINT_ALLOWLIST": sorted(RECONCILIATION_READ_ONLY_GET_ALLOWLIST),
    }
    if gates.overall != "PASS":
        report["DISPOSITION"] = "STOP_BEFORE_NETWORK"
        print(json.dumps(report, sort_keys=True))
        return 2
    if args.skip_network:
        report["DISPOSITION"] = "PHASE_7_PASS_NETWORK_SKIPPED"
        print(json.dumps(report, sort_keys=True))
        return 0

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

    backend = resolve_macos_security_framework_k1_lookup_backend_v1(
        k1_owner_go=K1_OPAQUE_SIGNING_OWNER_GO
    )
    with open_current_productive_k1_opaque_signing_handle_session_v1(
        owner_go=K1_OPAQUE_SIGNING_OWNER_GO,
        backend=backend,
    ) as session:
        transport = FullCoreProductiveReadOnlyGetTransportV1(
            handle=session.signing_handle,
            max_request_count=8,
        )
        session_result = run_bounded_productive_okx_read_only_validation_session_v1(
            transport=transport,
            pretrade_decision_id=str(args.pretrade_decision_id),
            instrument_id=str(args.instrument_id),
            inst_type=str(args.inst_type),
        )
    report["PHASE_8_VALIDATION"] = session_result.to_dict()
    report["GET_REQUEST_COUNT"] = session_result.get_request_count
    report["DISPOSITION"] = session_result.disposition
    print(json.dumps(report, sort_keys=True))
    return 0 if session_result.disposition == "VALIDATION_PASS" else 3


if __name__ == "__main__":
    raise SystemExit(_main())
