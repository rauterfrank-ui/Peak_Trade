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
    parser.add_argument(
        "--work-package-owner-go",
        default=None,
        help="Required explicit Owner-GO (no GRANTED default)",
    )
    parser.add_argument(
        "--private-get-go",
        default=None,
        help="Required explicit scoped private-GET Owner-GO",
    )
    parser.add_argument(
        "--offline-implementation-go",
        default=None,
        help="Required explicit offline-implementation Owner-GO",
    )
    parser.add_argument(
        "--k1-session-owner-go",
        default=None,
        help="Required for network path; must match K1_SESSION_OWNER_GO",
    )
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
    from src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_phase7_readiness_adjudication_v1 import (
        WORK_PACKAGE_ID as PHASE7_WORK_PACKAGE_ID,
    )
    from src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_productive_read_only_reconciliation_get_validation_v1 import (
        DISPOSITION_SESSION_WALLCLOCK_EXCEEDED,
        DISPOSITION_STOP_BEFORE_KEYCHAIN_AND_NETWORK,
        DISPOSITION_STOP_BEFORE_NETWORK,
        GhvOkxProductiveReadOnlyValidationError,
        Phase8CliOwnerAuthorizationV1,
        ProductiveOkxReadOnlyValidationSessionDeadlineV1,
        VALIDATION_SESSION_MONOTONIC_WALLCLOCK_SECONDS,
        evaluate_phase8_k1_network_owner_authorization_v1,
        evaluate_phase8_pre_network_owner_authorization_v1,
        evaluate_productive_get_safety_gates_v1,
        run_bounded_productive_okx_read_only_validation_session_v1,
    )

    cli_auth = Phase8CliOwnerAuthorizationV1(
        work_package_owner_go=args.work_package_owner_go,
        private_get_go=args.private_get_go,
        offline_implementation_go=args.offline_implementation_go,
        k1_session_owner_go=args.k1_session_owner_go,
    )
    pre_auth = evaluate_phase8_pre_network_owner_authorization_v1(cli_auth)
    origin_sha = str(args.origin_main_sha or "").strip() or _origin_main_sha()
    report: dict[str, object] = {
        "WORK_PACKAGE": PHASE7_WORK_PACKAGE_ID,
        "ORIGIN_MAIN_SHA": origin_sha,
        "OWNER_AUTHORIZATION": pre_auth.to_dict(),
        "GET_ENDPOINT_ALLOWLIST": sorted(RECONCILIATION_READ_ONLY_GET_ALLOWLIST),
        "PHASE_7_EVIDENCE_BOUND": True,
    }
    if pre_auth.disposition != "OWNER_AUTHORIZATION_OK":
        report["DISPOSITION"] = pre_auth.disposition
        print(json.dumps(report, sort_keys=True))
        return 2

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
        orchestration_request=gate_request,
        repo_root=REPO_ROOT,
    )
    report["PHASE_7_SAFETY_GATES"] = gates.to_dict()
    if gates.overall != "PASS":
        report["DISPOSITION"] = DISPOSITION_STOP_BEFORE_NETWORK
        print(json.dumps(report, sort_keys=True))
        return 2
    if args.skip_network:
        report["DISPOSITION"] = "PHASE_7_PASS_NETWORK_SKIPPED"
        report["NETWORK_REQUEST_COUNT"] = 0
        report["PRIVATE_GET_COUNT"] = 0
        report["KEYCHAIN_ACCESS_COUNT"] = 0
        report["POST_COUNT"] = 0
        print(json.dumps(report, sort_keys=True))
        return 0

    network_auth = evaluate_phase8_k1_network_owner_authorization_v1(cli_auth)
    report["K1_NETWORK_OWNER_AUTHORIZATION"] = network_auth.to_dict()
    if network_auth.disposition != "OWNER_AUTHORIZATION_OK":
        report["DISPOSITION"] = DISPOSITION_STOP_BEFORE_KEYCHAIN_AND_NETWORK
        print(json.dumps(report, sort_keys=True))
        return 2

    session_deadline = ProductiveOkxReadOnlyValidationSessionDeadlineV1.start(
        budget_seconds=VALIDATION_SESSION_MONOTONIC_WALLCLOCK_SECONDS
    )
    report["SESSION_DEADLINE"] = session_deadline.to_evidence_dict_v1()

    try:
        session_deadline.assert_within_budget_v1()
    except GhvOkxProductiveReadOnlyValidationError:
        report["DISPOSITION"] = DISPOSITION_SESSION_WALLCLOCK_EXCEEDED
        report["SESSION_DEADLINE"] = session_deadline.to_evidence_dict_v1()
        print(json.dumps(report, sort_keys=True))
        return 4

    from src.ops.full_core_live_path_composition_root_v1.current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1 import (
        resolve_macos_security_framework_k1_lookup_backend_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1 import (
        open_current_productive_k1_opaque_signing_handle_session_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
        FullCoreProductiveReadOnlyGetTransportV1,
    )

    try:
        session_deadline.assert_within_budget_v1()
        backend = resolve_macos_security_framework_k1_lookup_backend_v1(
            k1_owner_go=str(args.k1_session_owner_go)
        )
        session_deadline.assert_within_budget_v1()
        with open_current_productive_k1_opaque_signing_handle_session_v1(
            owner_go=str(args.k1_session_owner_go),
            backend=backend,
        ) as session:
            session_deadline.assert_within_budget_v1()
            transport = FullCoreProductiveReadOnlyGetTransportV1(
                handle=session.signing_handle,
                max_request_count=8,
            )
            session_result = run_bounded_productive_okx_read_only_validation_session_v1(
                transport=transport,
                pretrade_decision_id=str(args.pretrade_decision_id),
                instrument_id=str(args.instrument_id),
                inst_type=str(args.inst_type),
                session_deadline=session_deadline,
            )
    except GhvOkxProductiveReadOnlyValidationError as exc:
        report["DISPOSITION"] = (
            DISPOSITION_SESSION_WALLCLOCK_EXCEEDED
            if str(exc) == "SESSION_WALLCLOCK_EXCEEDED"
            else "VALIDATION_FAIL_CLOSED"
        )
        report["VALIDATION_ABORT_DETAIL"] = str(exc)[:200]
        report["SESSION_DEADLINE"] = session_deadline.to_evidence_dict_v1()
        print(json.dumps(report, sort_keys=True))
        return 4 if report["DISPOSITION"] == DISPOSITION_SESSION_WALLCLOCK_EXCEEDED else 3

    report["PHASE_8_VALIDATION"] = session_result.to_dict()
    report["GET_REQUEST_COUNT"] = session_result.get_request_count
    report["SESSION_DEADLINE"] = session_deadline.to_evidence_dict_v1()
    report["DISPOSITION"] = session_result.disposition
    print(json.dumps(report, sort_keys=True))
    return 0 if session_result.disposition == "VALIDATION_PASS" else 3


if __name__ == "__main__":
    raise SystemExit(_main())
