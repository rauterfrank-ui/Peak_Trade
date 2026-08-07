"""Materialize offline implementation evidence for Step-7 campaign binding."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_bundle_v1 import (
    build_campaign_bundle_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_harness_v1 import (
    exact_campaign_owner_path_v1,
    run_step7_campaign_harness_binding_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_state_contract_v1 import (
    load_and_validate_campaign_state_contract_v1,
    seal_campaign_state_contract_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_verifier_v1 import (
    verify_binding_manifest_v1,
    verify_campaign_bundle_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.constants_v1 import (
    BINDING_MANIFEST_FILENAME,
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    MULTI_SESSION_REQUIREMENT_EXPRESSION,
    OWNER,
    PACKAGE_MARKER,
    PHASE_9_2_SESSION_LADDER_COMPLETE,
    PHASE_9_2_STEP_6_STATUS,
    PHASE_9_2_STEP_7_STATUS,
    PRODUCER_VERSION,
    PRODUCTIVE_ENTRYPOINT_PATH,
    READY_FOR_SEPARATE_OWNER_GO_CAMPAIGN_EXECUTION,
    SCHEMA_VERSION,
    STEP3_RESTART_OWNER,
    STEP4_RECONNECT_OWNER,
    STEP6_STALE_ADVERSE_OWNER,
    STEP7_BINDING_IMPLEMENTED,
    STEP7_CAMPAIGN_BUNDLE_OWNER_PRESENT,
    STEP7_CAMPAIGN_HARNESS_BOUND,
    STEP7_CAMPAIGN_OWNER_PRESENT,
    STEP7_CAMPAIGN_VERIFIER_PRESENT,
    STEP7_PER_SESSION_EVIDENCE_CONTRACT_PRESENT,
    STEP7_PRODUCTIVE_ENTRYPOINT_PRESENT,
    TARGET_CAMPAIGN_CAPABILITY_ID,
    TARGET_SESSION_ID_PREFIX,
    repo_root_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.parity_v1 import (
    assert_no_parallel_campaign_authority_v1,
    prove_phase92_step7_campaign_binding_parity_v1,
    prove_step7_reuse_bindings_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.per_session_evidence_contract_v1 import (
    build_per_session_evidence_template_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)


def _pass_session_v1(
    *,
    session_id: str,
    ordinal: int,
    repository_sha: str,
    config_digest: str,
    state_before: str,
    state_after: str,
    authorization_id: str,
    confirm_fp: str,
) -> dict[str, Any]:
    template = build_per_session_evidence_template_v1(
        session_id=session_id,
        repository_sha=repository_sha,
        config_digest=config_digest,
        session_ordinal=ordinal,
    )
    template.update(
        {
            "authorization_id": authorization_id,
            "authorization_digest": sha256_canonical_v1({"authorization_id": authorization_id}),
            "confirm_token_fingerprint": confirm_fp,
            "session_result": {"ok": True, "status": "PASS", "observed_session": True},
            "restart_recovery_result": {
                "ok": True,
                "status": "PASS",
                "reused_owner": STEP3_RESTART_OWNER,
            },
            "reconnect_result": {
                "ok": True,
                "status": "PASS",
                "reused_owner": STEP4_RECONNECT_OWNER,
            },
            "stale_adverse_result": {
                "ok": True,
                "status": "PASS",
                "reused_owner": STEP6_STALE_ADVERSE_OWNER,
            },
            "state_root_before": state_before,
            "state_root_after": state_after,
            "confirmation_advance_count": 1,
            "duplicate_confirmation_advance_count": 0,
            "fill_count": 0,
            "duplicate_fill_count": 0,
            "private_endpoint_reachable": False,
            "credential_access_reachable": False,
            "order_side_effect_occurred": False,
            "telemetry": {
                "duplicate_confirmation_advance_count": 0,
                "duplicate_fill_count": 0,
                "private_endpoint_reachable": False,
                "credential_access_reachable": False,
                "order_side_effect_occurred": False,
            },
            "verifier_result": {"ok": True, "status": "PASS", "blockers": []},
            "claims": {
                "OBSERVED_SESSION": True,
                "PER_SESSION_AUTHORIZATION_USED": True,
                "AUTHORIZATION_REUSED": False,
                "CONFIRM_TOKEN_REUSED": False,
                "RESTART_RECOVERY_PROVED": True,
                "BOUNDED_RECONNECT_PROVED": True,
                "STALE_ADVERSE_PROVED": True,
                "DUPLICATE_CONFIRMATION_ADVANCE": False,
                "DUPLICATE_FILL": False,
                "PRIVATE_ENDPOINT_REACHED": False,
                "EXCHANGE_CREDENTIAL_PATH_REACHED": False,
                "ORDER_SIDE_EFFECT_OCCURRED": False,
                "CLAIMS_MATCH_TELEMETRY": True,
            },
        }
    )
    template["evidence_digest"] = sha256_canonical_v1(
        {k: v for k, v in template.items() if k != "evidence_digest"}
    )
    return template


def materialize_capability_evidence_v1(
    *,
    repository_sha: str,
    evidence_root: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    out = (
        Path(evidence_root)
        if evidence_root is not None
        else root / "docs" / "evidence" / EVIDENCE_DIRNAME
    )
    fixtures = out / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)

    cfg = str(
        load_activation_config_v1(
            config_path=root
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )

    parity = prove_phase92_step7_campaign_binding_parity_v1()
    reuse = prove_step7_reuse_bindings_v1()
    authority = assert_no_parallel_campaign_authority_v1()
    contract = load_and_validate_campaign_state_contract_v1(repo_root=root)
    sealed_contract = seal_campaign_state_contract_v1(contract)
    write_json_atomic_v1(fixtures / "campaign_state_contract_v1.json", sealed_contract)

    harness = run_step7_campaign_harness_binding_v1(
        repository_sha=repository_sha,
        config_digest=cfg,
        owner_go=True,
        request_real_network=False,
        repo_root=root,
    )
    write_json_atomic_v1(fixtures / "campaign_harness_binding_v1.json", harness)

    template = build_per_session_evidence_template_v1(
        session_id=f"{TARGET_SESSION_ID_PREFIX}_001",
        repository_sha=repository_sha,
        config_digest=cfg,
        session_ordinal=1,
    )
    write_json_atomic_v1(fixtures / "per_session_evidence_template_v1.json", template)

    s1 = _pass_session_v1(
        session_id=f"{TARGET_SESSION_ID_PREFIX}_001",
        ordinal=1,
        repository_sha=repository_sha,
        config_digest=cfg,
        state_before="state_root_A",
        state_after="state_root_B",
        authorization_id="auth_session_1",
        confirm_fp="confirm_fp_1",
    )
    s2 = _pass_session_v1(
        session_id=f"{TARGET_SESSION_ID_PREFIX}_002",
        ordinal=2,
        repository_sha=repository_sha,
        config_digest=cfg,
        state_before="state_root_B",
        state_after="state_root_C",
        authorization_id="auth_session_2",
        confirm_fp="confirm_fp_2",
    )
    write_json_atomic_v1(fixtures / "multi_session_pass_session_001_v1.json", s1)
    write_json_atomic_v1(fixtures / "multi_session_pass_session_002_v1.json", s2)

    multi_pass_bundle = build_campaign_bundle_v1(
        sessions=[s1, s2],
        expected_repository_sha=repository_sha,
        expected_config_digest=cfg,
    )
    multi_pass_verdict = verify_campaign_bundle_v1(multi_pass_bundle)
    write_json_atomic_v1(fixtures / "multi_session_pass_bundle_v1.json", multi_pass_bundle)
    write_json_atomic_v1(
        fixtures / "multi_session_pass_verifier_result_v1.json", multi_pass_verdict
    )

    one_session_bundle = build_campaign_bundle_v1(
        sessions=[s1],
        expected_repository_sha=repository_sha,
        expected_config_digest=cfg,
    )
    one_session_verdict = verify_campaign_bundle_v1(one_session_bundle)
    write_json_atomic_v1(fixtures / "one_session_fail_bundle_v1.json", one_session_bundle)
    write_json_atomic_v1(fixtures / "one_session_fail_verifier_result_v1.json", one_session_verdict)

    claims = {
        "STEP7_BINDING_IMPLEMENTED": STEP7_BINDING_IMPLEMENTED,
        "STEP7_CAMPAIGN_OWNER_PRESENT": STEP7_CAMPAIGN_OWNER_PRESENT,
        "STEP7_PRODUCTIVE_ENTRYPOINT_PRESENT": STEP7_PRODUCTIVE_ENTRYPOINT_PRESENT,
        "STEP7_CAMPAIGN_HARNESS_BOUND": STEP7_CAMPAIGN_HARNESS_BOUND,
        "STEP7_PER_SESSION_EVIDENCE_CONTRACT_PRESENT": (
            STEP7_PER_SESSION_EVIDENCE_CONTRACT_PRESENT
        ),
        "STEP7_CAMPAIGN_BUNDLE_OWNER_PRESENT": STEP7_CAMPAIGN_BUNDLE_OWNER_PRESENT,
        "STEP7_CAMPAIGN_VERIFIER_PRESENT": STEP7_CAMPAIGN_VERIFIER_PRESENT,
        "STEP7_MULTI_SESSION_REQUIREMENT_EXPRESSED_WITHOUT_INVENTED_NUMERIC_POLICY": True,
        "MULTI_SESSION_REQUIREMENT_EXPRESSION": MULTI_SESSION_REQUIREMENT_EXPRESSION,
        "STEP3_RESTART_SEMANTICS_REUSED": True,
        "STEP4_RECONNECT_SEMANTICS_REUSED": True,
        "STEP6_STALE_ADVERSE_SEMANTICS_REUSED": True,
        "READY_FOR_SEPARATE_OWNER_GO_CAMPAIGN_EXECUTION": (
            READY_FOR_SEPARATE_OWNER_GO_CAMPAIGN_EXECUTION
        ),
        "PHASE_9_2_STEP_6_STATUS": PHASE_9_2_STEP_6_STATUS,
        "PHASE_9_2_STEP_7_STATUS": PHASE_9_2_STEP_7_STATUS,
        "PHASE_9_2_SESSION_LADDER_COMPLETE": PHASE_9_2_SESSION_LADDER_COMPLETE,
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_MINTED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "CAMPAIGN_EXECUTED": False,
        "STEP7_STARTED": False,
        "MULTI_SESSION_CONTINUITY_LADDER_STEP_CLOSED": False,
        "CAPABILITY_CLOSED": False,
        "PACKAGE_MARKER": PACKAGE_MARKER,
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "producer_version": PRODUCER_VERSION,
        "capability_id": CAPABILITY_ID,
        "target_campaign_capability_id": TARGET_CAMPAIGN_CAPABILITY_ID,
        "owner": OWNER,
        "repository_sha": repository_sha,
        "config_digest": cfg,
        "productive_entrypoint_path": PRODUCTIVE_ENTRYPOINT_PATH,
        "exact_campaign_owner_path": exact_campaign_owner_path_v1(),
        "parity": parity,
        "reuse": reuse,
        "authority": authority,
        "harness": harness,
        "multi_session_pass_verifier": multi_pass_verdict,
        "one_session_fail_verifier": one_session_verdict,
        "claims": claims,
        "manifest_digest": "",
    }
    manifest["manifest_digest"] = sha256_canonical_v1(
        {k: v for k, v in manifest.items() if k != "manifest_digest"}
    )
    write_json_atomic_v1(out / BINDING_MANIFEST_FILENAME, manifest)

    binding_verdict = verify_binding_manifest_v1(manifest)
    write_json_atomic_v1(out / "binding_verifier_result_v1.json", binding_verdict)

    summary = {
        "ok": bool(
            parity["ok"]
            and reuse["ok"]
            and authority["ok"]
            and harness["ok"]
            and binding_verdict["ok"]
            and multi_pass_verdict["ok"]
            and not one_session_verdict["ok"]
        ),
        "capability_id": CAPABILITY_ID,
        "target_campaign_capability_id": TARGET_CAMPAIGN_CAPABILITY_ID,
        "evidence_root": str(out),
        "binding_manifest": BINDING_MANIFEST_FILENAME,
        "binding_verifier": binding_verdict,
        "multi_session_pass_ok": multi_pass_verdict["ok"],
        "one_session_fail_ok": one_session_verdict["ok"],
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_MINTED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "PHASE_9_2_STEP_7_STATUS": "OPEN",
        "PHASE_9_2_SESSION_LADDER_COMPLETE": False,
        "claims": claims,
    }
    write_json_atomic_v1(out / "SUMMARY.json", summary)
    return summary
