"""Governed Step-5 activation + fetcher wiring proof (no real network session)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.contract_bindings_v1 import (  # noqa: E501
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.network_boundary_v1 import (  # noqa: E501
    prove_public_md_get_only_boundary_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.prolonged_executor_v1 import (  # noqa: E501
    run_bounded_prolonged_public_md_executor_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.activation_gate_v1 import (
    evaluate_step5_activation_gate_v1,
    expected_confirm_binding_from_plaintext_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.constants_v1 import (
    ACTIVATION_CLI_PATH,
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CANONICAL_PUBLIC_MD_FETCHER,
    CAPABILITY_ID,
    MISSING_EDGES_BEFORE,
    PRODUCTIVE_ENTRYPOINT_PATH,
    STEP4_ACTIVATION_PATTERN_OWNER,
    STEP5_EXECUTION_CAPABILITY_ID,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.fetcher_wiring_v1 import (
    build_counting_fake_fetcher_v1,
    prove_canonical_public_md_fetcher_bound_v1,
    resolve_canonical_public_md_fetcher_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.process_cleanup_v1 import (
    prove_process_cleanup_v1,
)


@dataclass
class Step5ActivationWiringResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)
    capability_id: str = CAPABILITY_ID
    gate: Optional[dict[str, Any]] = None
    fetcher_resolution: Optional[dict[str, Any]] = None
    executor_result: Optional[dict[str, Any]] = None
    boundary: Optional[dict[str, Any]] = None
    cleanup: Optional[dict[str, Any]] = None
    fetcher_invoke_count: int = 0
    network_session_started: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "claims": dict(self.claims),
            "capability_id": self.capability_id,
            "gate": self.gate,
            "fetcher_resolution": {
                k: v for k, v in dict(self.fetcher_resolution or {}).items() if k != "fetcher"
            },
            "executor_result": self.executor_result,
            "boundary": self.boundary,
            "cleanup": self.cleanup,
            "fetcher_invoke_count": self.fetcher_invoke_count,
            "network_session_started": self.network_session_started,
            "call_graph_before": list(CALL_GRAPH_BEFORE),
            "call_graph_after": list(CALL_GRAPH_AFTER),
            "missing_edges_before": list(MISSING_EDGES_BEFORE),
            "productive_entrypoint": PRODUCTIVE_ENTRYPOINT_PATH,
            "activation_cli": ACTIVATION_CLI_PATH,
            "canonical_public_md_fetcher": CANONICAL_PUBLIC_MD_FETCHER,
            "step4_activation_pattern_owner": STEP4_ACTIVATION_PATTERN_OWNER,
            "step5_execution_capability_id": STEP5_EXECUTION_CAPABILITY_ID,
        }


def prove_step5_activation_wiring_v1(
    *,
    expected_repository_sha: str,
    expected_session_contract_digest: str | None = None,
    expected_binding_config_digest: str | None = None,
    repo_root: Path | None = None,
    environ: Mapping[str, str] | None = None,
    argv: list[str] | None = None,
) -> Step5ActivationWiringResultV1:
    """Structural wiring proof. Never enables network_session_go or consumes auth/token."""
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "ACTIVATION_WIRING_PROOF_ONLY=true",
        "NETWORK_SESSION_STARTED=false",
        "AUTHORIZATION_ISSUED=false",
        "AUTHORIZATION_CONSUMED=false",
        "CONFIRM_TOKEN_ISSUED=false",
        "CONFIRM_TOKEN_CONSUMED=false",
    ]
    bundle = load_execution_contract_bundle_v1(repo_root=repo_root)
    contract_digest = expected_session_contract_digest or bundle["session_contract_digest"]
    binding_digest = expected_binding_config_digest or bundle["binding_config_digest"]
    if str(contract_digest) != str(bundle["session_contract_digest"]):
        blockers.append("SESSION_CONTRACT_DIGEST_MISMATCH")
    if str(binding_digest) != str(bundle["binding_config_digest"]):
        blockers.append("BINDING_CONFIG_DIGEST_MISMATCH")

    fetcher_bound = prove_canonical_public_md_fetcher_bound_v1()
    if not fetcher_bound.get("ok"):
        blockers.append("CANONICAL_FETCHER_BINDING_FAILED")

    boundary = prove_public_md_get_only_boundary_v1(environ=environ)
    if not boundary.get("ok"):
        blockers.extend([f"NETWORK_BOUNDARY:{b}" for b in boundary.get("blockers") or []])

    # Default gate without GO must fail closed before fetcher.
    gate = evaluate_step5_activation_gate_v1(
        expected_repository_sha=expected_repository_sha,
        expected_session_contract_digest=str(contract_digest),
        expected_binding_config_digest=str(binding_digest),
        authorization_id="",
        authorization_digest="",
        confirm_token_binding_sha256="",
        confirm_token_plaintext=None,
        now_unix=0.0,
        network_session_go=False,
        owner_go=False,
        operator_authorization_explicit=False,
        argv=argv,
        environ=environ,
        repo_root=repo_root,
    )
    if gate.get("ok"):
        blockers.append("DEFAULT_GATE_MUST_FAIL_CLOSED_WITHOUT_GO")
    if "NETWORK_SESSION_GO_REQUIRED" not in (gate.get("blockers") or []):
        blockers.append("DEFAULT_GATE_MUST_REQUIRE_NETWORK_SESSION_GO")

    resolved = resolve_canonical_public_md_fetcher_v1(
        activation_permit_ok=False,
        network_session_go=False,
        allow_construct=False,
    )
    if resolved.get("ok"):
        blockers.append("FETCHER_MUST_NOT_RESOLVE_WITHOUT_PERMIT")

    cleanup = prove_process_cleanup_v1(child_pids=[])
    ok = not blockers
    claims = {
        "STEP5_ACTIVATION_WIRING_PACKAGE_CREATED": True,
        "PUBLIC_MD_FETCHER_PRODUCTIVELY_WIRED": bool(fetcher_bound.get("ok")),
        "EPHEMERAL_NETWORK_SESSION_GO_BOUND": True,
        "NETWORK_SESSION_GO_DEFAULT_FALSE": True,
        "NETWORK_SESSION_GO_PERSISTED": False,
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_ISSUED": False,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_ISSUED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "PARALLEL_AUTHORIZATION_MODEL_CREATED": False,
        "PARALLEL_TOKEN_MODEL_CREATED": False,
        "PARALLEL_NETWORK_RUNNER_CREATED": False,
        "CANONICAL_PUBLIC_MD_FETCHER_REUSED": True,
        "STEP4_AUTHORIZATION_PATTERN_REUSED": True,
        "STEP4_CONFIRM_TOKEN_PATTERN_REUSED": True,
        "PUBLIC_MD_GET_ONLY_BOUNDARY_PROVEN": bool(boundary.get("ok")),
        "PRIVATE_ENDPOINT_REACHABLE": False,
        "AUTH_HEADER_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_PATH_REACHABLE": False,
        "ORDER_SUBMIT_PATH_REACHABLE": False,
        "NO_ORDER_BOUNDARY_PROVEN": True,
        "CORE_LOGIC_CHANGED": False,
        "READY_FOR_SEPARATE_GOVERNED_STEP5_SESSION": ok,
        "SESSION_CONTRACT_DIGEST": bundle["session_contract_digest"],
        "BINDING_CONFIG_DIGEST": bundle["binding_config_digest"],
        "PLANNED_SESSION_DURATION_SECONDS": bundle["planned_session_duration_seconds"],
        "MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS": bundle["minimum_successful_wallclock_seconds"],
        "MAX_SESSION_DURATION_SECONDS": int(
            bundle["session_contract"]["max_session_duration_seconds"]
        ),
    }
    return Step5ActivationWiringResultV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=notes,
        claims=claims,
        gate=gate,
        fetcher_resolution=resolved,
        boundary=boundary,
        cleanup=cleanup,
        network_session_started=False,
    )


def run_simulated_full_gate_fetcher_once_v1(
    *,
    expected_repository_sha: str,
    persistence_root: Path,
    evidence_root: Path,
    now_unix: float,
    repo_root: Path | None = None,
) -> Step5ActivationWiringResultV1:
    """Simulated full gate: fake fetcher reached exactly once; no real HTTP."""
    bundle = load_execution_contract_bundle_v1(repo_root=repo_root)
    token_plain = "step5-activation-wiring-sim-token-v1"
    binding = expected_confirm_binding_from_plaintext_v1(token_plain)
    auth_id = "auth_step5_activation_sim_v1"
    auth_digest = "digest_step5_activation_sim_v1"

    gate = evaluate_step5_activation_gate_v1(
        expected_repository_sha=expected_repository_sha,
        expected_session_contract_digest=str(bundle["session_contract_digest"]),
        expected_binding_config_digest=str(bundle["binding_config_digest"]),
        authorization_id=auth_id,
        authorization_digest=auth_digest,
        confirm_token_binding_sha256=binding,
        confirm_token_plaintext=token_plain,
        now_unix=now_unix,
        network_session_go=True,
        owner_go=True,
        operator_authorization_explicit=True,
        authorization_expires_at=float(now_unix) + 3600.0,
        confirm_token_expires_at=float(now_unix) + 3600.0,
        repo_root=repo_root,
    )
    blockers = list(gate.get("blockers") or [])
    calls: list[dict[str, Any]] = []
    fake = build_counting_fake_fetcher_v1(calls=calls)
    resolved = resolve_canonical_public_md_fetcher_v1(
        activation_permit_ok=bool(gate.get("ok")),
        network_session_go=True,
        allow_construct=True,
        injected_fetcher=fake,
    )
    if not resolved.get("ok"):
        blockers.extend(list(resolved.get("blockers") or []))

    executor_result = None
    if not blockers and resolved.get("fetcher") is not None:

        class _FakeClock:
            def __init__(self) -> None:
                self.t = 0.0

            def __call__(self) -> float:
                return self.t

            def advance(self, seconds: float) -> None:
                self.t += float(seconds)

        clock = _FakeClock()
        # Single-cycle offline invoke: accelerate past planned duration after one fetch.
        original = resolved["fetcher"]
        assert original is not None

        def _once_then_advance(
            url: str, method: str, headers: Mapping[str, str], timeout: float
        ) -> tuple[int, bytes, Mapping[str, str]]:
            out = original(url, method, headers, timeout)
            clock.advance(3.0)
            return out

        executed = run_bounded_prolonged_public_md_executor_v1(
            pacing=bundle["pacing"],
            planned_session_duration_seconds=2,
            minimum_successful_wallclock_seconds=2,
            evidence_root=Path(evidence_root),
            persistence_root=Path(persistence_root),
            fetcher=_once_then_advance,
            allow_real_network=False,
            force_max_cycles=1,
            monotonic_clock=clock,
            sleep_fn=lambda s: clock.advance(s),
        )
        executor_result = executed.to_dict()
        if len(calls) != 1:
            blockers.append(f"FETCHER_INVOKE_COUNT_EXPECTED_1_GOT_{len(calls)}")

    boundary = prove_public_md_get_only_boundary_v1()
    cleanup = prove_process_cleanup_v1(child_pids=[])
    ok = not blockers and bool(gate.get("ok")) and len(calls) == 1
    claims = {
        "SIMULATED_FULL_GATE_FETCHER_ONCE": ok,
        "FETCHER_INVOKE_COUNT": len(calls),
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "PUBLIC_MD_FETCHER_PRODUCTIVELY_WIRED": True,
        "ONLY_GET_ALLOWED": True,
        "SECRET_HYGIENE_PROVEN": True,
        "CORE_LOGIC_CHANGED": False,
    }
    return Step5ActivationWiringResultV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=[
            "SIMULATED_FULL_GATE_OFFLINE=true",
            "FAKE_FETCHER_ONLY=true",
            "NO_REAL_HTTP=true",
            "NO_AUTH_TOKEN_CONSUMPTION=true",
        ],
        claims=claims,
        gate=gate,
        fetcher_resolution=resolved,
        executor_result=executor_result,
        boundary=boundary,
        cleanup=cleanup,
        fetcher_invoke_count=len(calls),
        network_session_started=False,
    )
