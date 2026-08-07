"""Materialize offline implementation evidence for Step-6 continuation binding."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.constants_v1 import (
    ADVERSE_DATA_CLASSIFIER,
    BINDING_MANIFEST_FILENAME,
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    FAILURE_INJECTION_SURFACE,
    OWNER,
    PRODUCER_VERSION,
    PRODUCTIVE_ENTRYPOINT_PATH,
    PRODUCTIVE_STEP6_EXECUTOR,
    SCHEMA_VERSION,
    STALE_DATA_CLASSIFIER,
    TARGET_SESSION_ID,
    VERIFIER_PATH,
    repo_root_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.fault_path_v1 import (
    prove_governed_adverse_stale_fault_path_offline_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.network_boundary_v1 import (
    prove_public_md_network_boundary_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.parity_v1 import (
    assert_no_parallel_productive_authority_v1,
    prove_phase92_step6_adverse_stale_continuation_parity_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.productive_executor_v1 import (
    exact_productive_caller_path_v1,
    run_step6_productive_executor_wiring_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.session_contract_v1 import (
    load_and_validate_session_contract_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.session_evidence_schema_v1 import (
    build_session_evidence_template_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.verifier_v1 import (
    verify_binding_manifest_v1,
    verify_productive_session_evidence_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)


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

    parity = prove_phase92_step6_adverse_stale_continuation_parity_v1()
    authority = assert_no_parallel_productive_authority_v1()
    contract = load_and_validate_session_contract_v1(repo_root=root)
    write_json_atomic_v1(fixtures / "session_contract_v1.json", contract)

    boundary = prove_public_md_network_boundary_v1()
    write_json_atomic_v1(fixtures / "network_boundary_v1.json", boundary)

    fault = prove_governed_adverse_stale_fault_path_offline_v1()
    write_json_atomic_v1(fixtures / "adverse_stale_fault_path_v1.json", fault)

    executor = run_step6_productive_executor_wiring_v1(
        repository_sha=repository_sha,
        config_digest=cfg,
        request_real_network=False,
        owner_go=True,
    )
    write_json_atomic_v1(fixtures / "productive_executor_wiring_v1.json", executor.to_dict())

    template = build_session_evidence_template_v1(repository_sha=repository_sha, config_digest=cfg)
    write_json_atomic_v1(fixtures / "session_evidence_template_v1.json", template)

    # Positive productive-session fixture (synthetic observed session shape).
    positive = {
        **template,
        "distinct_observation_count": 3,
        "duplicate_observation_count": 1,
        "stale_observation_count": 2,
        "confirmation_advance_count": 2,
        "stale_confirmation_advance_count": 0,
        "duplicate_confirmation_advance_count": 0,
        "fill_count": 0,
        "fabricated_observation_count": 0,
        "retry_count": 1,
        "backoff_timeline": [1.0, 2.0],
        "minimum_request_interval_seconds": 2.0,
        "telemetry": {
            "STALE_OBSERVATION_COUNT": 2,
            "DISTINCT_OBSERVATION_COUNT": 3,
            "DUPLICATE_OBSERVATION_COUNT": 1,
            "fabricated_observation_count": 0,
            "stale_confirmation_advance_count": 0,
            "duplicate_confirmation_advance_count": 0,
            "minimum_request_interval_seconds": 2.0,
            "BOUNDED_RETRY_OBSERVED": True,
            "BOUNDED_BACKOFF_OBSERVED": True,
        },
        "claims": {
            "OBSERVED_SESSION": True,
            "STALE_CONDITION_OBSERVED": True,
            "ADVERSE_CONDITION_OBSERVED": True,
            "STALE_OBSERVATION_COUNT": 2,
            "DISTINCT_OBSERVATION_COUNT": 3,
            "DUPLICATE_OBSERVATION_COUNT": 1,
            "DUPLICATE_CONFIRMATION_ADVANCE": False,
            "STALE_CONFIRMATION_ADVANCE": False,
            "DUPLICATE_FILL": False,
            "ZERO_INTERVAL_RETRY_BURST": False,
            "BOUNDED_RETRY_OBSERVED": True,
            "BOUNDED_BACKOFF_OBSERVED": True,
            "PRIVATE_ENDPOINT_REACHED": False,
            "EXCHANGE_CREDENTIAL_PATH_REACHED": False,
            "ORDER_SIDE_EFFECT_OCCURRED": False,
            "ADVERSE_STALE_DATA_LADDER_STEP_CLOSED": False,
        },
    }
    write_json_atomic_v1(fixtures / "productive_session_positive_fixture_v1.json", positive)
    positive_verify = verify_productive_session_evidence_v1(positive)
    write_json_atomic_v1(fixtures / "productive_session_positive_verifier_v1.json", positive_verify)

    # Negative fixture: stale confirmation advance present.
    negative = {
        **positive,
        "stale_confirmation_advance_count": 1,
        "claims": {
            **dict(positive["claims"]),
            "STALE_CONFIRMATION_ADVANCE": True,
        },
        "telemetry": {
            **dict(positive["telemetry"]),
            "stale_confirmation_advance_count": 1,
        },
    }
    write_json_atomic_v1(fixtures / "productive_session_negative_fixture_v1.json", negative)
    negative_verify = verify_productive_session_evidence_v1(negative)
    write_json_atomic_v1(fixtures / "productive_session_negative_verifier_v1.json", negative_verify)

    claims = {
        **dict(executor.claims),
        "CORE_LOGIC_CHANGE": False,
        "EFFECTIVE_TRADING_NUMERIC_VALUES_UNCHANGED": True,
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "CLAIMS_MATCH_IMPLEMENTATION": bool(executor.ok and fault["ok"] and boundary["ok"]),
        "PRODUCTIVE_ENTRYPOINT": PRODUCTIVE_ENTRYPOINT_PATH,
        "PRODUCTIVE_STEP6_EXECUTOR": PRODUCTIVE_STEP6_EXECUTOR,
        "STALE_DATA_CLASSIFIER": STALE_DATA_CLASSIFIER,
        "ADVERSE_DATA_CLASSIFIER": ADVERSE_DATA_CLASSIFIER,
        "FAILURE_INJECTION_SURFACE": FAILURE_INJECTION_SURFACE,
        "VERIFIER_PATH": VERIFIER_PATH,
        "CALL_GRAPH_AFTER": list(executor.call_graph_after),
        "EXACT_PRODUCTIVE_CALLER": exact_productive_caller_path_v1(),
        "POSITIVE_SESSION_VERIFIER_OK": bool(positive_verify.get("ok")),
        "NEGATIVE_SESSION_VERIFIER_REJECTS": not bool(negative_verify.get("ok")),
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "capability_id": CAPABILITY_ID,
        "owner": OWNER,
        "producer_version": PRODUCER_VERSION,
        "repository_sha": repository_sha,
        "config_digest": cfg,
        "target_session_id": TARGET_SESSION_ID,
        "claims": claims,
        "parity": parity,
        "authority": authority,
        "boundary_ok": bool(boundary.get("ok")),
        "fault_path_ok": bool(fault.get("ok")),
        "executor_ok": bool(executor.ok),
    }
    binding_verify = verify_binding_manifest_v1(manifest)
    write_json_atomic_v1(fixtures / "binding_verifier_v1.json", binding_verify)
    write_json_atomic_v1(out / BINDING_MANIFEST_FILENAME, manifest)

    summary = {
        "ok": bool(
            executor.ok
            and fault["ok"]
            and boundary["ok"]
            and binding_verify["ok"]
            and positive_verify["ok"]
            and (not negative_verify["ok"])
        ),
        "capability_id": CAPABILITY_ID,
        "claims": claims,
        "manifest_digest": sha256_canonical_v1(manifest),
        "evidence_root": str(out),
    }
    write_json_atomic_v1(out / "SUMMARY.json", summary)

    lines = []
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            rel = path.relative_to(out).as_posix()
            digest = sha256_canonical_v1(path.read_text(encoding="utf-8"))
            lines.append(f"{digest}  {rel}")
    (out / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary
