"""Evidence + failure injection for Step-5 final generic consume/start binding."""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping

from src.ops.phase_9_2_step_5_final_generic_session_authorization_consume_and_network_start_binding_v1.binding_v1 import (  # noqa: E501
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    build_step5_final_generic_side_effect_grant_v1,
    prove_step5_final_generic_consume_start_binding_complete_v1,
    run_step5_final_generic_consume_and_network_start_binding_v1,
    verify_step5_final_generic_binding_manifest_v1,
)
from src.ops.phase_9_2_step_5_final_generic_session_authorization_consume_and_network_start_binding_v1.constants_v1 import (  # noqa: E501
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    MAX_SESSION_DURATION_SECONDS,
    MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
    PLANNED_SESSION_DURATION_SECONDS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    STEP5_EXECUTION_CAPABILITY_ID,
    TARGET_SESSION_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.contract_bindings_v1 import (  # noqa: E501
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.digest_v1 import (  # noqa: E501
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

NOW = 1_700_000_000.0
FIXTURE_TOKEN = "step5-final-generic-fixture-token-v1"
# Historical shared path (must NOT be used by evidence materialization).
LEGACY_SHARED_FAILURE_INJECTION_PERSISTENCE_RELPATH = (
    "var/tmp/step5_final_generic_failure_injection"
)


def _token_binding(token: str = FIXTURE_TOKEN) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def run_step5_final_generic_failure_injection_v1(
    *,
    repository_sha: str,
    config_digest: str,
    persistence_root: Path,
    now_unix: float = NOW,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = Path(persistence_root)
    root.mkdir(parents=True, exist_ok=True)
    bundle = load_execution_contract_bundle_v1(repo_root=repo_root)
    contract_digest = str(bundle["session_contract_digest"])
    binding_digest = str(bundle["binding_config_digest"])
    token_binding = _token_binding()
    results: dict[str, Any] = {}

    def _grant(**overrides: Any) -> dict[str, Any]:
        base = build_step5_final_generic_side_effect_grant_v1(
            authorization_id=str(overrides.pop("authorization_id", "auth_step5_fi_v1")),
            authorization_digest=str(overrides.pop("authorization_digest", "digest_step5_fi_v1")),
            repository_sha=repository_sha,
            config_digest=config_digest,
            session_contract_digest=contract_digest,
            binding_config_digest=binding_digest,
            confirm_token_digest=str(overrides.pop("confirm_token_digest", token_binding)),
            issued_at=now_unix,
            not_before=now_unix,
            expires_at=now_unix + 3600.0,
            owner_go=True,
            operator_authorization_explicit=True,
            network_session_go=True,
        )
        base.update(overrides)
        body = {k: v for k, v in base.items() if k != "grant_digest"}
        base["grant_digest"] = sha256_canonical_v1(body)
        return base

    def _case(name: str, fn: Callable[[], Mapping[str, Any]]) -> None:
        payload = dict(fn())
        results[name] = {
            "ok": bool(payload.get("expected_pass")) or (payload.get("ok") is False),
            "blockers": list(payload.get("blockers") or []),
            "claims": dict(payload.get("claims") or {}),
            "authorization_consumed": bool(payload.get("authorization_consumed")),
            "confirm_token_consumed": bool(payload.get("confirm_token_consumed")),
            "executor_invoked": bool(payload.get("executor_invoked")),
            "network_session_started": bool(payload.get("network_session_started")),
            "expected_fail_closed": not bool(payload.get("expected_pass")),
        }

    def _run(**kwargs: Any) -> dict[str, Any]:
        case_root = root / kwargs.pop("case_name", "case")
        result = run_step5_final_generic_consume_and_network_start_binding_v1(
            expected_repository_sha=repository_sha,
            expected_config_digest=config_digest,
            grant=kwargs.pop("grant"),
            confirm_token_plaintext=kwargs.pop("confirm_token_plaintext", FIXTURE_TOKEN),
            confirm_token_binding_sha256=kwargs.pop("confirm_token_binding_sha256", token_binding),
            confirm_token_expires_at=now_unix + 3600.0,
            owner_go=kwargs.pop("owner_go", True),
            operator_authorization_explicit=kwargs.pop("operator_authorization_explicit", True),
            network_session_go=kwargs.pop("network_session_go", True),
            now_unix=now_unix,
            persistence_root=case_root / "persistence",
            evidence_root=case_root / "evidence",
            repo_root=repo_root,
            **kwargs,
        )
        return result.to_dict()

    _case(
        "missing_network_session_go",
        lambda: _run(grant=_grant(), network_session_go=False, case_name="no_go"),
    )
    _case(
        "wrong_sha",
        lambda: _run(
            grant=_grant(repository_sha="0" * 40),
            case_name="wrong_sha",
        ),
    )
    _case(
        "wrong_config",
        lambda: _run(grant=_grant(config_digest="1" * 64), case_name="wrong_cfg"),
    )
    _case(
        "wrong_contract",
        lambda: _run(
            grant=_grant(session_contract_digest="2" * 64),
            case_name="wrong_contract",
        ),
    )
    _case(
        "wrong_binding",
        lambda: _run(
            grant=_grant(binding_config_digest="3" * 64),
            case_name="wrong_binding",
        ),
    )
    _case(
        "wrong_scope",
        lambda: _run(grant=_grant(session_scope="WRONG_SCOPE"), case_name="wrong_scope"),
    )
    _case(
        "expired_authorization",
        lambda: _run(
            grant=_grant(
                expires_at=now_unix - 10.0, not_before=now_unix - 100.0, issued_at=now_unix - 200.0
            ),
            case_name="expired",
        ),
    )
    _case(
        "invalid_token",
        lambda: _run(
            grant=_grant(),
            confirm_token_plaintext="not-the-bound-token",
            case_name="bad_token",
        ),
    )
    _case(
        "crash_before_reserve",
        lambda: _run(
            grant=_grant(authorization_id="auth_crash_before"),
            crash_before_reserve=True,
            case_name="crash_before",
        ),
    )
    _case(
        "crash_after_reserve",
        lambda: _run(
            grant=_grant(authorization_id="auth_crash_after"),
            crash_after_reserve=True,
            case_name="crash_after",
        ),
    )
    _case(
        "crash_after_consume_before_executor",
        lambda: _run(
            grant=_grant(authorization_id="auth_crash_post_consume"),
            crash_after_consume_before_executor=True,
            case_name="crash_post_consume",
        ),
    )
    _case(
        "auth_consume_fail",
        lambda: _run(
            grant=_grant(authorization_id="auth_consume_fail"),
            crash_during_auth_consume=True,
            case_name="auth_consume_fail",
        ),
    )
    _case(
        "token_consume_fail",
        lambda: _run(
            grant=_grant(authorization_id="auth_token_fail"),
            force_token_consume_fail=True,
            case_name="token_consume_fail",
        ),
    )

    # Happy path then reuse on the SAME persistence root.
    happy = _run(grant=_grant(authorization_id="auth_happy_reuse"), case_name="happy_reuse")
    results["happy_path_once"] = {
        "ok": bool(happy.get("ok")),
        "blockers": list(happy.get("blockers") or []),
        "authorization_consumed": bool(happy.get("authorization_consumed")),
        "confirm_token_consumed": bool(happy.get("confirm_token_consumed")),
        "executor_invoked": bool(happy.get("executor_invoked")),
        "network_session_started": bool(happy.get("network_session_started")),
        "expected_fail_closed": False,
        "expected_pass": True,
    }
    reuse = _run(grant=_grant(authorization_id="auth_happy_reuse"), case_name="happy_reuse")
    results["authorization_reuse_blocked"] = {
        "ok": reuse.get("ok") is False,
        "blockers": list(reuse.get("blockers") or []),
        "authorization_consumed": bool(reuse.get("authorization_consumed")),
        "executor_invoked": bool(reuse.get("executor_invoked")),
        "expected_fail_closed": True,
    }

    all_ok = all(bool(v.get("ok")) for v in results.values())
    return {
        "ok": all_ok,
        "capability_id": CAPABILITY_ID,
        "cases": results,
        "network_session_started": False,
        "authorization_issued": False,
        "confirm_token_issued": False,
    }


def materialize_step5_final_generic_binding_evidence_v1(
    *,
    repository_sha: str,
    evidence_root: Path | None = None,
    repo_root: Path | None = None,
    failure_injection_persistence_root: Path | None = None,
) -> dict[str, Any]:
    """Materialize binding evidence with per-call isolated FI persistence.

    Failure-injection consumption ledgers are written only under an exclusive
    persistence root for this invocation. By default that root is created inside
    a TemporaryDirectory and removed on success or exception. Callers may inject
    an explicit root for tests; the legacy shared ``var/tmp/...`` path is never
    selected by this materializer.
    """
    root = repo_root_v1() if repo_root is None else Path(repo_root)
    cfg = str(
        load_activation_config_v1(
            config_path=root
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )
    out_root = (
        Path(evidence_root)
        if evidence_root is not None
        else root / "docs" / "evidence" / EVIDENCE_DIRNAME
    )
    fixtures = out_root / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)

    proof = prove_step5_final_generic_consume_start_binding_complete_v1(
        expected_repository_sha=repository_sha,
        expected_config_digest=cfg,
        repo_root=root,
    )

    owned_tmpdir: tempfile.TemporaryDirectory | None = None
    isolation_mode = "explicit_injected"
    fi_root: Path
    try:
        if failure_injection_persistence_root is not None:
            fi_root = Path(failure_injection_persistence_root)
            fi_root.mkdir(parents=True, exist_ok=True)
            isolation_mode = "explicit_injected"
        else:
            owned_tmpdir = tempfile.TemporaryDirectory(prefix="step5_final_generic_fi_ephemeral_")
            fi_root = Path(owned_tmpdir.name) / "failure_injection"
            fi_root.mkdir(parents=True, exist_ok=True)
            isolation_mode = "ephemeral_temporary_directory"

        legacy_shared = (root / LEGACY_SHARED_FAILURE_INJECTION_PERSISTENCE_RELPATH).resolve()
        if fi_root.resolve() == legacy_shared:
            raise ValueError("SHARED_FAILURE_INJECTION_PERSISTENCE_ROOT_FORBIDDEN_FOR_MATERIALIZE")

        # Redacted uniqueness: parent temp-dir basename (ephemeral) or leaf name (injected).
        # Never embed absolute filesystem paths into evidence.
        uniqueness_label = (
            fi_root.parent.name
            if isolation_mode == "ephemeral_temporary_directory"
            else fi_root.name
        )
        fi_root_token = sha256_canonical_v1({"kind": isolation_mode, "label": uniqueness_label})
        fi = run_step5_final_generic_failure_injection_v1(
            repository_sha=repository_sha,
            config_digest=cfg,
            persistence_root=fi_root,
            repo_root=root,
        )
        happy = dict((fi.get("cases") or {}).get("happy_path_once") or {})
        reuse = dict((fi.get("cases") or {}).get("authorization_reuse_blocked") or {})
        bundle = load_execution_contract_bundle_v1(repo_root=root)
        claims = dict(proof.get("claims") or {})
        claims.update(
            {
                "FAILURE_INJECTION_OK": bool(fi.get("ok")),
                "PLANNED_SESSION_DURATION_SECONDS": PLANNED_SESSION_DURATION_SECONDS,
                "MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS": MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
                "MAX_SESSION_DURATION_SECONDS": MAX_SESSION_DURATION_SECONDS,
                "SESSION_CONTRACT_DIGEST": bundle["session_contract_digest"],
                "BINDING_CONFIG_DIGEST": bundle["binding_config_digest"],
                "CONFIG_DIGEST": cfg,
            }
        )
        manifest = {
            "schema_version": "phase_9_2_step_5_final_generic_consume_start_binding_evidence.v1",
            "capability_id": CAPABILITY_ID,
            "runtime_capability_id": STEP5_EXECUTION_CAPABILITY_ID,
            "repository_sha": repository_sha,
            "claims": claims,
            "call_graph_before": list(CALL_GRAPH_BEFORE),
            "call_graph_after": list(CALL_GRAPH_AFTER),
            "productive_entrypoint": PRODUCTIVE_ENTRYPOINT_PATH,
            "target_session_id": TARGET_SESSION_ID,
            "network_session_started": False,
            "authorization_issued": False,
            "authorization_consumed": False,
            "confirm_token_issued": False,
            "confirm_token_consumed": False,
        }
        verifier = verify_step5_final_generic_binding_manifest_v1(manifest)
        write_json_atomic_v1(fixtures / "structural_proof_v1.json", proof)
        write_json_atomic_v1(fixtures / "failure_injection_v1.json", fi)
        write_json_atomic_v1(fixtures / "manifest_v1.json", manifest)
        write_json_atomic_v1(fixtures / "verifier_result_v1.json", verifier)

        isolation = {
            "mode": isolation_mode,
            "shared_var_tmp_path_used": False,
            "legacy_shared_relpath": LEGACY_SHARED_FAILURE_INJECTION_PERSISTENCE_RELPATH,
            "persistence_root_name_redacted": True,
            "persistence_root_token": fi_root_token,
            "happy_path_once_ok": bool(happy.get("ok")),
            "intra_run_reuse_blocked": bool(reuse.get("ok")),
            "owned_ephemeral_cleanup_scheduled": owned_tmpdir is not None,
        }
        summary = {
            "ok": bool(proof.get("ok")) and bool(fi.get("ok")) and bool(verifier.get("ok")),
            "capability_id": CAPABILITY_ID,
            "repository_sha": repository_sha,
            "config_digest": cfg,
            "session_contract_digest": bundle["session_contract_digest"],
            "binding_config_digest": bundle["binding_config_digest"],
            "claims": claims,
            "verifier": verifier,
            "evidence_root": str(out_root),
            "network_session_started": False,
            "authorization_issued": False,
            "authorization_consumed": False,
            "confirm_token_issued": False,
            "confirm_token_consumed": False,
            "manifest_digest": sha256_canonical_v1(manifest),
            "claims_match_evidence": bool(verifier.get("ok")),
            "failure_injection_persistence_isolation": isolation,
        }
        write_json_atomic_v1(out_root / "SUMMARY.json", summary)
        (out_root / "MANIFEST.sha256").write_text(
            summary["manifest_digest"] + "  fixtures/manifest_v1.json\n", encoding="utf-8"
        )
        return summary
    finally:
        if owned_tmpdir is not None:
            owned_tmpdir.cleanup()
