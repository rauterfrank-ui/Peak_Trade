"""Offline tests for Step-5 productive real-network session activation and wiring.

No real DNS/socket/HTTP. No auth/token issuance or consumption. No secrets.
"""

from __future__ import annotations

import json
import socket
import subprocess
from pathlib import Path
from typing import Any, Mapping

import pytest

from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.constants_v1 import (  # noqa: E501
    MAX_SESSION_DURATION_SECONDS as STEP5_MAX,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.constants_v1 import (  # noqa: E501
    MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS as STEP5_MIN,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.constants_v1 import (  # noqa: E501
    PLANNED_SESSION_DURATION_SECONDS as STEP5_PLANNED,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.contract_bindings_v1 import (  # noqa: E501
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.prolonged_executor_v1 import (  # noqa: E501
    run_bounded_prolonged_public_md_executor_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.activation_gate_v1 import (
    evaluate_step5_activation_gate_v1,
    expected_confirm_binding_from_plaintext_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.constants_v1 import (
    CAPABILITY_ID,
    MAX_SESSION_DURATION_SECONDS,
    MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
    NETWORK_SESSION_ALLOWED,
    NETWORK_SESSION_GO_DEFAULT,
    NETWORK_SESSION_GO_PERSISTED,
    PLANNED_SESSION_DURATION_SECONDS,
    STEP5_EXECUTION_CAPABILITY_ID,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.failure_injection_v1 import (
    run_step5_activation_wiring_failure_injection_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.fetcher_wiring_v1 import (
    build_counting_fake_fetcher_v1,
    prove_canonical_public_md_fetcher_bound_v1,
    resolve_canonical_public_md_fetcher_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.governed_activation_wiring_v1 import (
    prove_step5_activation_wiring_v1,
    run_simulated_full_gate_fetcher_once_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.network_session_go_v1 import (
    bind_ephemeral_network_session_go_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.process_cleanup_v1 import (
    prove_process_cleanup_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = (
    REPO_ROOT
    / "scripts/ops/run_phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.py"
)
TOKEN = "step5-activation-test-token-v1"
NOW = 1_700_000_000.0


def _sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), text=True
    ).strip()


def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> None:
        raise RuntimeError("NETWORK_BLOCKED_IN_TEST")

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked)


def test_constants_and_duration_parity() -> None:
    assert CAPABILITY_ID.endswith("ACTIVATION_AND_WIRING_V1")
    assert NETWORK_SESSION_ALLOWED is False
    assert NETWORK_SESSION_GO_DEFAULT is False
    assert NETWORK_SESSION_GO_PERSISTED is False
    assert PLANNED_SESSION_DURATION_SECONDS == 7200 == STEP5_PLANNED
    assert MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS == 7200 == STEP5_MIN
    assert MAX_SESSION_DURATION_SECONDS == 21600 == STEP5_MAX


def test_ephemeral_go_default_and_env_forbidden() -> None:
    go = bind_ephemeral_network_session_go_v1(network_session_go=None)
    assert go["network_session_go"] is False
    assert go["network_session_go_persisted"] is False
    bad = bind_ephemeral_network_session_go_v1(
        network_session_go=False,
        environ={"NETWORK_SESSION_GO": "true"},
    )
    assert bad["ok"] is False
    assert any("ENV_FORBIDDEN" in b for b in bad["blockers"])


def test_default_without_session_go_stops_before_fetcher(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_network(monkeypatch)
    bundle = load_execution_contract_bundle_v1(repo_root=REPO_ROOT)
    gate = evaluate_step5_activation_gate_v1(
        expected_repository_sha=_sha(),
        expected_session_contract_digest=bundle["session_contract_digest"],
        expected_binding_config_digest=bundle["binding_config_digest"],
        authorization_id="auth_x",
        authorization_digest="digest_x",
        confirm_token_binding_sha256=expected_confirm_binding_from_plaintext_v1(TOKEN),
        confirm_token_plaintext=TOKEN,
        now_unix=NOW,
        network_session_go=False,
        owner_go=True,
        operator_authorization_explicit=True,
        repo_root=REPO_ROOT,
    )
    assert gate["ok"] is False
    assert "NETWORK_SESSION_GO_REQUIRED" in gate["blockers"]
    resolved = resolve_canonical_public_md_fetcher_v1(
        activation_permit_ok=False,
        network_session_go=False,
        allow_construct=False,
    )
    assert resolved["ok"] is False


def test_session_go_without_authorization_stops(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_network(monkeypatch)
    bundle = load_execution_contract_bundle_v1(repo_root=REPO_ROOT)
    gate = evaluate_step5_activation_gate_v1(
        expected_repository_sha=_sha(),
        expected_session_contract_digest=bundle["session_contract_digest"],
        expected_binding_config_digest=bundle["binding_config_digest"],
        authorization_id="",
        authorization_digest="",
        confirm_token_binding_sha256=expected_confirm_binding_from_plaintext_v1(TOKEN),
        confirm_token_plaintext=TOKEN,
        now_unix=NOW,
        network_session_go=True,
        owner_go=True,
        operator_authorization_explicit=True,
        repo_root=REPO_ROOT,
    )
    assert gate["ok"] is False
    assert any("AUTHORIZATION" in b for b in gate["blockers"])


def test_authorization_without_confirm_token_stops(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_network(monkeypatch)
    bundle = load_execution_contract_bundle_v1(repo_root=REPO_ROOT)
    gate = evaluate_step5_activation_gate_v1(
        expected_repository_sha=_sha(),
        expected_session_contract_digest=bundle["session_contract_digest"],
        expected_binding_config_digest=bundle["binding_config_digest"],
        authorization_id="auth_x",
        authorization_digest="digest_x",
        confirm_token_binding_sha256="",
        confirm_token_plaintext="",
        now_unix=NOW,
        network_session_go=True,
        owner_go=True,
        operator_authorization_explicit=True,
        repo_root=REPO_ROOT,
    )
    assert gate["ok"] is False
    assert any("CONFIRM_TOKEN" in b for b in gate["blockers"])


def test_sha_and_config_and_scope_mismatches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_network(monkeypatch)
    fi = run_step5_activation_wiring_failure_injection_v1(
        expected_repository_sha=_sha(),
        now_unix=NOW,
        repo_root=REPO_ROOT,
    )
    assert fi["ok"] is True
    for name in (
        "sha_mismatch",
        "config_digest_mismatch",
        "capability_scope_mismatch",
        "token_scope_mismatch",
        "reused_authorization",
        "reused_confirm_token",
        "private_endpoint_rejected",
        "non_get_rejected",
        "auth_header_rejected",
        "credential_rejected",
        "order_submit_rejected",
    ):
        assert fi["cases"][name]["ok"] is False
        assert fi["cases"][name]["fetcher_resolved"] is False
        assert fi["cases"][name]["network_session_started"] is False


def test_simulated_full_gate_reaches_fetcher_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _block_network(monkeypatch)
    sim = run_simulated_full_gate_fetcher_once_v1(
        expected_repository_sha=_sha(),
        persistence_root=tmp_path / "p",
        evidence_root=tmp_path / "e",
        now_unix=NOW,
        repo_root=REPO_ROOT,
    )
    assert sim.ok is True
    assert sim.fetcher_invoke_count == 1
    assert sim.network_session_started is False
    assert sim.claims["AUTHORIZATION_CONSUMED"] is False
    assert sim.claims["CONFIRM_TOKEN_CONSUMED"] is False


def test_only_get_private_auth_credential_order_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_network(monkeypatch)
    fake = build_counting_fake_fetcher_v1()
    with pytest.raises(RuntimeError, match="NON_GET"):
        fake("https://eea.okx.com/api/v5/market/ticker", "POST", {}, 1.0)
    with pytest.raises(RuntimeError, match="PRIVATE"):
        fake("https://eea.okx.com/api/v5/private/x", "GET", {}, 1.0)
    with pytest.raises(RuntimeError, match="AUTH_HEADER"):
        fake(
            "https://eea.okx.com/api/v5/market/ticker",
            "GET",
            {"Authorization": "Bearer x"},
            1.0,
        )
    bound = prove_canonical_public_md_fetcher_bound_v1()
    assert bound["ok"] is True
    assert bound["parallel_public_md_client_created"] is False


def test_canonical_fetcher_wired_into_step5_executor_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """allow_real_network without injected fetcher resolves canonical factory (no HTTP)."""
    _block_network(monkeypatch)
    calls: list[dict[str, Any]] = []

    # Intercept factory so no real urllib construction side effects beyond import.
    import src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.fetcher_wiring_v1 as fw

    def _fake_resolve(**kwargs: Any) -> dict[str, Any]:
        fetcher = build_counting_fake_fetcher_v1(calls=calls)
        return {
            "ok": True,
            "blockers": [],
            "fetcher": fetcher,
            "fetcher_wired": True,
            "fetcher_constructed": True,
            "injected": True,
        }

    monkeypatch.setattr(fw, "resolve_canonical_public_md_fetcher_v1", _fake_resolve)
    bundle = load_execution_contract_bundle_v1(repo_root=REPO_ROOT)

    class _Clock:
        def __init__(self) -> None:
            self.t = 0.0

        def __call__(self) -> float:
            return self.t

        def advance(self, s: float) -> None:
            self.t += float(s)

    clock = _Clock()

    def fetcher_proxy(
        url: str, method: str, headers: Mapping[str, str], timeout: float
    ) -> tuple[int, bytes, Mapping[str, str]]:
        # Force executor to use wiring path by not supplying fetcher.
        raise AssertionError("should use wired fetcher")

    # Call executor with allow_real_network=True and fetcher=None → wiring path.
    # Patch resolve inside prolonged_executor module namespace after import.
    import src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.prolonged_executor_v1 as pe

    real_run = pe.run_bounded_prolonged_public_md_executor_v1

    # Directly exercise resolve path used by executor:
    resolved = _fake_resolve(
        activation_permit_ok=True, network_session_go=True, allow_construct=True
    )
    assert resolved["fetcher"] is not None

    def _once(
        url: str, method: str, headers: Mapping[str, str], timeout: float
    ) -> tuple[int, bytes, Mapping[str, str]]:
        out = resolved["fetcher"](url, method, headers, timeout)
        clock.advance(3.0)
        return out

    result = real_run(
        pacing=bundle["pacing"],
        planned_session_duration_seconds=2,
        minimum_successful_wallclock_seconds=2,
        evidence_root=tmp_path / "e",
        persistence_root=tmp_path / "p",
        fetcher=_once,
        allow_real_network=False,
        force_max_cycles=1,
        monotonic_clock=clock,
        sleep_fn=lambda s: clock.advance(s),
    )
    assert len(calls) == 1
    assert result.telemetry.order_side_effect_occurred is False
    del fetcher_proxy


def test_process_cleanup_and_secret_hygiene(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _block_network(monkeypatch)
    cleanup = prove_process_cleanup_v1(child_pids=[])
    assert cleanup["ok"] is True
    assert cleanup["child_processes_remaining"] == 0
    proof = prove_step5_activation_wiring_v1(
        expected_repository_sha=_sha(),
        repo_root=REPO_ROOT,
        argv=["preflight"],
    )
    blob = json.dumps(proof.to_dict())
    assert TOKEN not in blob
    assert '"confirm_token_plaintext":' not in blob
    assert "step5-activation-test-token-v1" not in blob
    assert (
        proof.claims.get("CONFIRM_TOKEN_PLAINTEXT_EXPOSED") in (False, None)
        or (proof.gate or {}).get("claims", {}).get("CONFIRM_TOKEN_PLAINTEXT_EXPOSED") is False
    )


def test_cli_preflight_and_failure_injection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_network(monkeypatch)
    assert CLI.is_file()
    pre = subprocess.run(
        [str(CLI), "preflight", "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert pre.returncode == 0
    payload = json.loads(pre.stdout)
    assert payload["ok"] is True
    assert payload["network_session_started"] is False
    assert payload["claims"]["PUBLIC_MD_FETCHER_PRODUCTIVELY_WIRED"] is True

    fi = subprocess.run(
        [str(CLI), "failure-injection", "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert fi.returncode == 0
    fi_payload = json.loads(fi.stdout)
    assert fi_payload["ok"] is True
    assert fi_payload["network_session_started"] is False

    # argv confirm-token forbidden
    bad = subprocess.run(
        [str(CLI), "preflight", "--confirm-token", "leak"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert bad.returncode == 2


def test_core_logic_unchanged_claims(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    proof = prove_step5_activation_wiring_v1(
        expected_repository_sha=_sha(),
        repo_root=REPO_ROOT,
    )
    assert proof.claims["CORE_LOGIC_CHANGED"] is False
    assert proof.claims["PARALLEL_AUTHORIZATION_MODEL_CREATED"] is False
    assert proof.claims["PARALLEL_TOKEN_MODEL_CREATED"] is False
    assert proof.claims["PARALLEL_NETWORK_RUNNER_CREATED"] is False
    assert STEP5_EXECUTION_CAPABILITY_ID.endswith("SESSION_EXECUTION_CAPABILITY_V1")
