"""Tests for Step-4 governed real-network execution binding + Hidden-PTY handoff.

No real DNS/socket/HTTP. Runner always injected. Token plaintext never asserted in
captures beyond redaction checks.
"""

from __future__ import annotations

import json
import socket
import subprocess
from pathlib import Path
from typing import Any, Callable

import pytest

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    CONFIRM_TOKEN_PREFIX,
    compute_confirm_token_binding_sha256,
    fingerprint_confirm_token,
    sha256_text,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    parse_preregistration_contract_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    GOVERNED_EXECUTION_BINDING_CAPABILITY_ID,
    GOVERNED_EXECUTION_BINDING_REAL_NETWORK_SIDE_EFFECTS_AUTHORIZED,
    GOVERNED_PUBLIC_MD_NETWORK_SCOPE,
    HTTP_METHOD_ALLOWLIST,
    NETWORK_ALLOWLIST,
    NETWORK_ALLOWED_AUTHORITY_SOURCE,
    NETWORK_SESSION_ALLOWED,
    PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE,
    SESSION_SCOPE,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.digest_v1 import (
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.governed_execution_binding_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    execute_governed_step4_execution_binding_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.governed_network_authorization_v1 import (
    derive_network_allowed_from_issuance_authorization_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.hidden_pty_confirm_handoff_v1 import (
    acquire_confirm_token_via_canonical_hidden_pty_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.network_boundary_v1 import (
    prove_public_md_network_boundary_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.parity_v1 import (
    prove_phase92_rate_limit_reconnect_wallclock_binding_parity_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_request_cli_adapter_v1 import (
    build_canonical_session_request_from_issuance_artifacts_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    parse_operator_go_contract_v1,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1 import (
    FAMILY_PSO_GOVERNED_PUBLIC_MD,
    PURPOSE_PSO_WALLCLOCK_OBSERVE,
    SecureEphemeralConfirmTokenHandleV1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = (
    REPO_ROOT
    / "tests/fixtures/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1"
)
TOKEN = CONFIRM_TOKEN_PREFIX + ("GOVERNEDBINDTOKENV1" + "Y" * 22)
SESSION_ID = "phase_9_2_governed_binding_session_v1"
NOW = 1_700_000_000.0


def _sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), text=True
    ).strip()


def _cfg() -> str:
    return str(
        load_activation_config_v1(
            config_path=REPO_ROOT
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )


def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> None:
        raise AssertionError("REAL_NETWORK_FORBIDDEN_IN_TESTS")

    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked)


def _write_governed_issuance(
    tmp_path: Path,
    *,
    sha: str,
    network_authorized: bool = True,
    token: str = TOKEN,
) -> dict[str, Path]:
    evidence_root = tmp_path / "evidence_root"
    evidence_root.mkdir(parents=True, exist_ok=True)
    ledger = tmp_path / "fingerprint_ledger.txt"
    ledger.write_text("", encoding="utf-8")

    prereg_raw = json.loads(
        (FIXTURE_DIR / "preregistration_wallclock_valid_non_authoritative.json").read_text(
            encoding="utf-8"
        )
    )
    go_raw = json.loads(
        (FIXTURE_DIR / "operator_go_wallclock_valid_non_authoritative.json").read_text(
            encoding="utf-8"
        )
    )
    prereg_raw["session_id"] = SESSION_ID
    prereg_raw["expected_repository_sha"] = sha
    prereg_raw["evidence_root"] = str(evidence_root)
    prereg_raw["expires_at"] = NOW + 3600.0
    prereg_raw.pop("issued_at", None)
    prereg_raw.pop("not_before", None)
    provisional = parse_preregistration_contract_v1(prereg_raw)
    scope = provisional.scope_digest()
    binding = compute_confirm_token_binding_sha256(
        session_id=SESSION_ID,
        scope_digest=scope,
        expires_at=float(prereg_raw["expires_at"]),
        repository_sha=sha,
        confirm_token=token,
    )
    prereg_raw["confirm_token_binding_sha256"] = binding
    prereg_raw["confirm_token_hash_reference"] = "sha256:" + sha256_text(token)
    # Recompute scope after binding update.
    provisional = parse_preregistration_contract_v1(prereg_raw)
    scope = provisional.scope_digest()
    binding = compute_confirm_token_binding_sha256(
        session_id=SESSION_ID,
        scope_digest=scope,
        expires_at=float(prereg_raw["expires_at"]),
        repository_sha=sha,
        confirm_token=token,
    )
    prereg_raw["confirm_token_binding_sha256"] = binding

    go_raw["session_id"] = SESSION_ID
    go_raw["expected_repository_sha"] = sha
    go_raw["confirm_token_binding_sha256"] = binding
    go_raw["confirm_token_hash_reference"] = prereg_raw["confirm_token_hash_reference"]
    go_raw["scope_digest"] = scope
    go_raw["network_authorized"] = network_authorized
    go_raw["session_execution_authorized"] = network_authorized
    go_raw["network_scope"] = GOVERNED_PUBLIC_MD_NETWORK_SCOPE
    go_raw["session_execution_scope"] = "paper_shadow_observation_wallclock_v1"
    go_raw["orders_authorized"] = False
    go_raw["live_authorized"] = False
    go_raw["testnet_authorized"] = False
    go_raw["paper_execution_authorized"] = False
    go_raw["credentials_authorized"] = False
    go_raw["expires_at"] = NOW + 3600.0
    go_raw["not_before"] = NOW
    go_raw["issued_at"] = NOW

    prereg_path = tmp_path / "preregistration.json"
    go_path = tmp_path / "operator_go.json"
    art_path = tmp_path / "authorization_artifact.json"
    write_json_atomic_v1(prereg_path, prereg_raw)
    write_json_atomic_v1(go_path, go_raw)
    write_json_atomic_v1(
        art_path,
        {
            "schema": "authorization_artifact_governed_binding_probe_v1",
            "authorization_id": "auth_governed_binding_v1",
            "preregistration_id": SESSION_ID,
            "repository_sha": sha,
            "network_scope": PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE,
            "network_authorized": network_authorized,
            "confirm_token_fingerprint": fingerprint_confirm_token(token),
            "notes": ["GOVERNED_BINDING_UNIT_ONLY", "NOT_A_FULL_V2_ARTIFACT"],
        },
    )
    return {
        "preregistration": prereg_path,
        "operator_go": go_path,
        "authorization_artifact": art_path,
        "fingerprint_ledger": ledger,
        "evidence_root": evidence_root,
    }


def _getpass_for_token(token: str) -> Callable[[str], str]:
    handle = SecureEphemeralConfirmTokenHandleV1.mint_bound_v1(
        family_id=FAMILY_PSO_GOVERNED_PUBLIC_MD,
        purpose=PURPOSE_PSO_WALLCLOCK_OBSERVE,
        session_id=SESSION_ID,
        repository_sha=_sha(),
        consumer_id="tests.ops.test_phase_9_2_step_4_governed_execution_binding",
        mint_fn=lambda: token,
    )
    return handle.as_getpass_fn_v1()


def test_constants_fail_closed() -> None:
    assert NETWORK_SESSION_ALLOWED is False
    assert GOVERNED_EXECUTION_BINDING_REAL_NETWORK_SIDE_EFFECTS_AUTHORIZED is False
    assert NETWORK_ALLOWLIST == "OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY"
    assert HTTP_METHOD_ALLOWLIST == "GET_ONLY"
    assert GOVERNED_EXECUTION_BINDING_CAPABILITY_ID.startswith("PHASE_9_2_STEP_4_GOVERNED_")
    assert "issuance.operator_go" in NETWORK_ALLOWED_AUTHORITY_SOURCE


def test_valid_issuance_builds_governed_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_governed_issuance(tmp_path, sha=sha)
    result = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=None,
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
        request_governed_public_network=True,
        cli_network_session_allowed=True,
        confirm_token_getpass_fn=_getpass_for_token(TOKEN),
        require_hidden_pty=True,
    )
    assert result.ok is True
    assert result.network_allowed_from_authorization is True
    assert result.session_request is not None
    assert result.session_request["use_real_network"] is True
    assert result.claims["NETWORK_ALLOWED_FROM_AUTHORIZATION"] is True
    assert result.claims["GOVERNED_PUBLIC_NETWORK_MODE_BOUND"] is True
    assert result.field_source_map["network_allowed"] == NETWORK_ALLOWED_AUTHORITY_SOURCE
    blob = json.dumps(result.to_dict())
    assert TOKEN not in blob
    assert result.to_dict()["session_request"]["confirm_token"] == "[REDACTED]"


def test_network_allowed_only_from_authorization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_governed_issuance(tmp_path, sha=sha, network_authorized=False)
    go = parse_operator_go_contract_v1(json.loads(paths["operator_go"].read_text(encoding="utf-8")))
    derived = derive_network_allowed_from_issuance_authorization_v1(
        operator_go=go,
        authorization_artifact_path=paths["authorization_artifact"],
        expected_repository_sha=sha,
        expected_session_id=SESSION_ID,
        cli_network_session_allowed=True,
    )
    assert derived.network_allowed is False
    assert derived.ok is False


def test_missing_network_permission_stops_before_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_governed_issuance(tmp_path, sha=sha, network_authorized=False)
    result = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=None,
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
        request_governed_public_network=True,
        cli_network_session_allowed=True,
        confirm_token_getpass_fn=_getpass_for_token(TOKEN),
        require_hidden_pty=True,
    )
    assert result.ok is False
    assert result.session_request is None
    assert "OPERATOR_GO_NETWORK_NOT_AUTHORIZED" in result.blockers or (
        "NETWORK_ALLOWED_MISSING_FROM_AUTHORIZATION" in result.blockers
    )


def test_sha_mismatch_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_governed_issuance(tmp_path, sha=sha)
    result = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=None,
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha="0" * 40,
        permit_canonical_runner_invoke=True,
        request_governed_public_network=True,
        cli_network_session_allowed=True,
        confirm_token_getpass_fn=_getpass_for_token(TOKEN),
        require_hidden_pty=True,
    )
    assert result.ok is False
    assert "CLI_EXPECTED_REPOSITORY_SHA_MISMATCH" in result.blockers


def test_hidden_pty_canonical_path(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    handoff = acquire_confirm_token_via_canonical_hidden_pty_v1(
        getpass_fn=_getpass_for_token(TOKEN),
        require_real_tty=False,
    )
    assert handoff.ok is True
    assert handoff.claims["CONFIRM_TOKEN_CANONICAL_PATH_USED"] is True
    assert handoff.confirm_token_fingerprint == fingerprint_confirm_token(TOKEN)
    assert TOKEN not in json.dumps(handoff.to_public_dict())
    handoff.clear_plaintext_v1()
    assert handoff.plaintext == ""


def test_missing_pty_fail_closed_no_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    handoff = acquire_confirm_token_via_canonical_hidden_pty_v1(
        getpass_fn=None,
        require_real_tty=True,
        stdin_stream=type("S", (), {"isatty": lambda self: False})(),
    )
    assert handoff.ok is False
    assert "CANONICAL_HIDDEN_PTY_CONFIRM_TOKEN_PATH_NOT_AVAILABLE" in handoff.blockers
    assert handoff.plaintext == ""


def test_token_digest_and_id_bound(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    handoff = acquire_confirm_token_via_canonical_hidden_pty_v1(
        getpass_fn=_getpass_for_token(TOKEN),
    )
    assert handoff.confirm_token_id.startswith("ctid_")
    assert len(handoff.confirm_token_fingerprint) == 64


def test_full_binding_exactly_once_consume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    cfg = _cfg()
    paths = _write_governed_issuance(tmp_path, sha=sha)
    adapter = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=None,
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
        request_governed_public_network=True,
        cli_network_session_allowed=True,
        expected_config_digest=cfg,
        confirm_token_getpass_fn=_getpass_for_token(TOKEN),
        require_hidden_pty=True,
    )
    assert adapter.ok is True
    assert adapter.session_request is not None
    go = adapter.session_request["go"]
    prereg = adapter.session_request["prereg"]
    calls: list[dict[str, Any]] = []

    def stub(**kwargs: Any) -> dict[str, Any]:
        calls.append({k: ("[REDACTED]" if k == "confirm_token" else v) for k, v in kwargs.items()})
        assert kwargs.get("use_real_network") is False
        return {"ok": True, "network_request_count": 0}

    binding = execute_governed_step4_execution_binding_v1(
        session_request=adapter.session_request,
        network_allowed_from_authorization=True,
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        authorization_id=adapter.authorization_id,
        authorization_digest=adapter.authorization_digest,
        confirm_token_binding_sha256=str(go.confirm_token_binding_sha256),
        confirm_token_plaintext=str(adapter.session_request["confirm_token"]),
        confirm_token_expires_at=float(go.expires_at),
        now_unix=NOW,
        persistence_root=tmp_path / "persist",
        wallclock_runner=stub,
        allow_real_network_side_effects=False,
        authorization_session_id=SESSION_ID,
        confirm_token_expected_session_id=SESSION_ID,
        confirm_token_expected_scope_digest=str(prereg.scope_digest()),
        runtime_session_id=SESSION_ID,
        authorization_scope=SESSION_SCOPE,
    )
    assert binding.ok is True
    assert binding.authorization_consumed is True
    assert binding.confirm_token_consumed is True
    assert binding.network_session_executed is False
    assert binding.real_network_request_count == 0
    assert len(calls) == 1

    # Replay must fail.
    adapter2 = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=None,
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
        request_governed_public_network=True,
        cli_network_session_allowed=True,
        expected_config_digest=cfg,
        confirm_token_getpass_fn=_getpass_for_token(TOKEN),
        require_hidden_pty=True,
    )
    replay = execute_governed_step4_execution_binding_v1(
        session_request=adapter2.session_request or {},
        network_allowed_from_authorization=True,
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        authorization_id=adapter.authorization_id,
        authorization_digest=adapter.authorization_digest,
        confirm_token_binding_sha256=str(go.confirm_token_binding_sha256),
        confirm_token_plaintext=TOKEN,
        confirm_token_expires_at=float(go.expires_at),
        now_unix=NOW + 1,
        persistence_root=tmp_path / "persist",
        wallclock_runner=stub,
        allow_real_network_side_effects=False,
        authorization_session_id=SESSION_ID,
        confirm_token_expected_session_id=SESSION_ID,
        confirm_token_expected_scope_digest=str(prereg.scope_digest()),
        runtime_session_id=SESSION_ID,
        authorization_scope=SESSION_SCOPE,
    )
    assert replay.ok is False
    assert "AUTHORIZATION_ALREADY_CONSUMED" in replay.blockers or (
        "AUTHORIZATION_VALIDATION_FAILED" in replay.blockers
    )


def test_invalid_token_stops_before_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    cfg = _cfg()
    paths = _write_governed_issuance(tmp_path, sha=sha)
    adapter = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=None,
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
        request_governed_public_network=True,
        cli_network_session_allowed=True,
        expected_config_digest=cfg,
        confirm_token_getpass_fn=_getpass_for_token(TOKEN),
        require_hidden_pty=True,
    )
    assert adapter.session_request is not None
    go = adapter.session_request["go"]
    prereg = adapter.session_request["prereg"]
    bad = execute_governed_step4_execution_binding_v1(
        session_request=adapter.session_request,
        network_allowed_from_authorization=True,
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        authorization_id=adapter.authorization_id,
        authorization_digest=adapter.authorization_digest,
        confirm_token_binding_sha256=str(go.confirm_token_binding_sha256),
        confirm_token_plaintext=CONFIRM_TOKEN_PREFIX + ("WRONG" + "Z" * 32),
        confirm_token_expires_at=float(go.expires_at),
        now_unix=NOW,
        persistence_root=tmp_path / "persist_bad",
        wallclock_runner=lambda **_k: {"ok": True},
        allow_real_network_side_effects=False,
        authorization_session_id=SESSION_ID,
        confirm_token_expected_session_id=SESSION_ID,
        confirm_token_expected_scope_digest=str(prereg.scope_digest()),
        runtime_session_id=SESSION_ID,
        authorization_scope=SESSION_SCOPE,
    )
    assert bad.ok is False
    assert bad.session_lock_acquired is False
    assert bad.authorization_consumed is False


def test_public_md_allowlist_and_private_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    boundary = prove_public_md_network_boundary_v1(environ={})
    assert boundary["PUBLIC_MD_ONLY_BOUND"] is True
    assert boundary["GET_ONLY_BOUND"] is True
    assert boundary["PRIVATE_ENDPOINT_REACHABLE"] is False
    assert boundary["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert boundary["ORDER_SIDE_EFFECT_OCCURRED"] is False


def test_parity_and_call_graph() -> None:
    parity = prove_phase92_rate_limit_reconnect_wallclock_binding_parity_v1()
    assert parity.get("ok") is True
    assert CALL_GRAPH_BEFORE
    assert "canonical hidden-PTY confirm-token acquisition" in CALL_GRAPH_AFTER
    assert "run_productive_wallclock_session_v1 (injected stub only in this capability)" in (
        CALL_GRAPH_AFTER
    )


def test_governed_mode_forbids_token_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_governed_issuance(tmp_path, sha=sha)
    token_file = tmp_path / "token.txt"
    token_file.write_text(TOKEN, encoding="utf-8")
    result = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=token_file,
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
        request_governed_public_network=True,
        cli_network_session_allowed=True,
        confirm_token_getpass_fn=_getpass_for_token(TOKEN),
        require_hidden_pty=True,
    )
    assert result.ok is False
    assert "GOVERNED_MODE_FORBIDS_CONFIRM_TOKEN_FILE" in result.blockers


def test_real_network_side_effects_flag_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    cfg = _cfg()
    paths = _write_governed_issuance(tmp_path, sha=sha)
    adapter = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=None,
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
        request_governed_public_network=True,
        cli_network_session_allowed=True,
        expected_config_digest=cfg,
        confirm_token_getpass_fn=_getpass_for_token(TOKEN),
        require_hidden_pty=True,
    )
    assert adapter.session_request is not None
    go = adapter.session_request["go"]
    prereg = adapter.session_request["prereg"]
    bad = execute_governed_step4_execution_binding_v1(
        session_request=adapter.session_request,
        network_allowed_from_authorization=True,
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        authorization_id=adapter.authorization_id,
        authorization_digest=adapter.authorization_digest,
        confirm_token_binding_sha256=str(go.confirm_token_binding_sha256),
        confirm_token_plaintext=TOKEN,
        confirm_token_expires_at=float(go.expires_at),
        now_unix=NOW,
        persistence_root=tmp_path / "persist_side",
        wallclock_runner=lambda **_k: {"ok": True},
        allow_real_network_side_effects=True,
        authorization_session_id=SESSION_ID,
        confirm_token_expected_session_id=SESSION_ID,
        confirm_token_expected_scope_digest=str(prereg.scope_digest()),
        runtime_session_id=SESSION_ID,
        authorization_scope=SESSION_SCOPE,
    )
    assert bad.ok is False
    assert "REAL_NETWORK_SIDE_EFFECTS_FORBIDDEN_IN_BINDING_CAPABILITY" in bad.blockers
