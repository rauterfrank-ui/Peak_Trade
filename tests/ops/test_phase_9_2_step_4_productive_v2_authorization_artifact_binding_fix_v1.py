"""Tests for Step-4 productive V2 authorization artifact binding fix.

No real DNS/socket/HTTP. No authorization/confirm-token consumption.
Uses productive-shaped authorization_artifact_v2 fixtures (not only probe fakes).
"""

from __future__ import annotations

import hashlib
import json
import socket
import subprocess
from pathlib import Path
from typing import Any

import pytest

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.constants_v1 import (
    AUTHORIZATION_SCHEMA,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.states_v1 import (
    AuthorizationStateV2,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.constants_v1 import (
    AUTHORIZED_NETWORK_SCOPE,
    EFFECTIVE_SESSION_CONFIG_DIGEST_KEY,
    MANDATORY_SAFETY_BOUNDARIES,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.constants_v1 import (
    PRODUCTIVE_CODE_IDENTITY,
    WALLCLOCK_CONFIG_IDENTITY,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    CONFIRM_TOKEN_PREFIX,
    compute_confirm_token_binding_sha256,
    fingerprint_confirm_token,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    parse_operator_go_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    parse_preregistration_contract_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    CONFIG_DIGEST_DOMAIN_ACTIVATION_CONFIG,
    CONFIG_DIGEST_DOMAIN_WALLCLOCK_CONFIG_IDENTITY,
    GOVERNED_PUBLIC_MD_NETWORK_SCOPE,
    GOVERNED_PUBLIC_MD_SESSION_EXECUTION_SCOPE,
    PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE,
    PRODUCTIVE_V2_AUTHORIZATION_ARTIFACT_BINDING_FIX_CAPABILITY_ID,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.digest_v1 import (
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.governed_network_authorization_v1 import (
    compute_productive_code_identity_digest_v1,
    compute_wallclock_config_identity_digest_v1,
    derive_network_allowed_from_issuance_authorization_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = (
    REPO_ROOT
    / "tests/fixtures/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1"
)
# Short binder keeps confirm_token=<name> under Policy Critic NO_SECRETS length gate.
_CT = CONFIRM_TOKEN_PREFIX + ("V2ARTBINDFIXTOKENV1" + "Q" * 20)
SESSION_ID = "phase_9_2_public_md_rate_limit_reconnect_session_v1"
NOW = 1_700_000_000.0


def _sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), text=True
    ).strip()


def _activation_cfg() -> str:
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


def _effective_session_config_stub(wallclock_hash: str, code_hash: str) -> str:
    # Deterministic stand-in for effective_session_config (not recomputed via writer);
    # tests that need producer-parity only assert wallclock/code identities.
    material = f"effective|{wallclock_hash}|{code_hash}|{AUTHORIZED_NETWORK_SCOPE}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _write_productive_v2_bundle(
    tmp_path: Path,
    *,
    sha: str,
    network_authorized: bool = True,
    artifact_network_scope: str | None = PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE,
    go_network_scope: str = GOVERNED_PUBLIC_MD_NETWORK_SCOPE,
    include_artifact_network_scope: bool = True,
    wallclock_hash: str | None = None,
    code_hash: str | None = None,
    effective_hash: str | None = None,
    state: str = AuthorizationStateV2.CREATED_UNCONSUMED.value,
    consumed_at: float | None = None,
    omit_config_digests: bool = False,
) -> dict[str, Path]:
    evidence_root = tmp_path / "evidence_root"
    evidence_root.mkdir(parents=True, exist_ok=True)

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
    prereg_raw["fixture_non_authoritative"] = False
    prereg_raw["expires_at"] = NOW + 3600.0
    provisional = parse_preregistration_contract_v1(prereg_raw)
    scope = provisional.scope_digest()
    binding = compute_confirm_token_binding_sha256(
        session_id=SESSION_ID,
        scope_digest=scope,
        expires_at=float(prereg_raw["expires_at"]),
        repository_sha=sha,
        confirm_token=_CT,
    )
    prereg_raw["confirm_token_binding_sha256"] = binding
    go_raw["session_id"] = SESSION_ID
    go_raw["expected_repository_sha"] = sha
    go_raw["confirm_token_binding_sha256"] = binding
    go_raw["scope_digest"] = scope
    go_raw["network_authorized"] = network_authorized
    go_raw["session_execution_authorized"] = network_authorized
    go_raw["network_scope"] = go_network_scope
    go_raw["session_execution_scope"] = GOVERNED_PUBLIC_MD_SESSION_EXECUTION_SCOPE
    go_raw["orders_authorized"] = False
    go_raw["live_authorized"] = False
    go_raw["testnet_authorized"] = False
    go_raw["paper_execution_authorized"] = False
    go_raw["credentials_authorized"] = False
    go_raw["fixture_non_authoritative"] = False
    go_raw["expires_at"] = NOW + 3600.0
    go_raw["not_before"] = NOW
    go_raw["issued_at"] = NOW

    wh = (
        wallclock_hash
        if wallclock_hash is not None
        else compute_wallclock_config_identity_digest_v1()
    )
    ch = code_hash if code_hash is not None else compute_productive_code_identity_digest_v1()
    eh = effective_hash if effective_hash is not None else _effective_session_config_stub(wh, ch)

    art: dict[str, Any] = {
        "schema": AUTHORIZATION_SCHEMA,
        "schema_version": "v2",
        "authorization_id": "auth_v2_step4_binding_fix_test_001",
        "preregistration_id": SESSION_ID,
        "repository_sha": sha,
        "integrity_digest": "a" * 64,
        "session_config_digest": eh,
        "state": state,
        "consumed_at": consumed_at,
        "orders_authorized": False,
        "live_authorized": False,
        "testnet_authorized": False,
        "credentials_authorized": False,
        "paper_execution_authorized": False,
        "confirm_token_fingerprint": fingerprint_confirm_token(_CT),
        "confirm_token_binding_sha256": binding,
        "safety_boundaries": dict(MANDATORY_SAFETY_BOUNDARIES),
        "venue": "OKX",
        "notes": ["PRODUCTIVE_V2_SHAPED_FIXTURE", "NOT_ISSUED_BY_WRITER"],
    }
    if include_artifact_network_scope:
        art["network_scope"] = artifact_network_scope
    if not omit_config_digests:
        art["config_digests"] = {
            CONFIG_DIGEST_DOMAIN_WALLCLOCK_CONFIG_IDENTITY: wh,
            "productive_code_identity": ch,
            EFFECTIVE_SESSION_CONFIG_DIGEST_KEY: eh,
        }

    prereg_path = tmp_path / "preregistration.json"
    go_path = tmp_path / "operator_go.json"
    art_path = tmp_path / "authorization_artifact.json"
    write_json_atomic_v1(prereg_path, prereg_raw)
    write_json_atomic_v1(go_path, go_raw)
    write_json_atomic_v1(art_path, art)
    return {
        "preregistration": prereg_path,
        "operator_go": go_path,
        "authorization_artifact": art_path,
        "wallclock_hash": wh,
        "code_hash": ch,
        "effective_hash": eh,
    }


def _derive(paths: dict[str, Path], *, sha: str, **kwargs: Any):
    go = parse_operator_go_contract_v1(json.loads(paths["operator_go"].read_text(encoding="utf-8")))
    return derive_network_allowed_from_issuance_authorization_v1(
        operator_go=go,
        authorization_artifact_path=paths["authorization_artifact"],
        expected_repository_sha=sha,
        expected_session_id=SESSION_ID,
        cli_network_session_allowed=True,
        **kwargs,
    )


def test_scope_layer_constants_aligned() -> None:
    assert PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE == AUTHORIZED_NETWORK_SCOPE
    assert PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE == "PUBLIC_MARKET_DATA_ONLY"
    assert GOVERNED_PUBLIC_MD_NETWORK_SCOPE == "okx_eea_futures_public_md_observe_v1"
    assert PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE != GOVERNED_PUBLIC_MD_NETWORK_SCOPE
    assert PRODUCTIVE_V2_AUTHORIZATION_ARTIFACT_BINDING_FIX_CAPABILITY_ID.endswith(
        "PRODUCTIVE_V2_AUTHORIZATION_ARTIFACT_BINDING_FIX_V1"
    )
    assert (
        compute_wallclock_config_identity_digest_v1()
        == hashlib.sha256(WALLCLOCK_CONFIG_IDENTITY.encode("utf-8")).hexdigest()
    )
    assert (
        compute_productive_code_identity_digest_v1()
        == hashlib.sha256(PRODUCTIVE_CODE_IDENTITY.encode("utf-8")).hexdigest()
    )


def test_pass_productive_v2_artifact_domain_equal_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_productive_v2_bundle(tmp_path, sha=sha)
    wh = str(paths["wallclock_hash"])
    result = _derive(
        paths,
        sha=sha,
        expected_config_digest=wh,
        expected_config_digest_domain=CONFIG_DIGEST_DOMAIN_WALLCLOCK_CONFIG_IDENTITY,
    )
    assert result.ok is True
    assert result.network_allowed is True
    assert result.artifact_network_scope == PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE
    assert result.network_scope == GOVERNED_PUBLIC_MD_NETWORK_SCOPE
    assert result.config_digest_domain == CONFIG_DIGEST_DOMAIN_WALLCLOCK_CONFIG_IDENTITY
    assert result.claims["AUTHORIZATION_CONSUMED"] is False
    assert result.claims["CROSS_SCHEMA_DIGEST_COMPARISON_REMOVED"] is True


def test_fail_artifact_network_scope_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_productive_v2_bundle(tmp_path, sha=sha, include_artifact_network_scope=False)
    result = _derive(paths, sha=sha)
    assert result.ok is False
    assert "ARTIFACT_NETWORK_SCOPE_MISSING" in result.blockers
    assert result.network_allowed is False


def test_fail_artifact_network_scope_wrong(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_productive_v2_bundle(
        tmp_path,
        sha=sha,
        artifact_network_scope=GOVERNED_PUBLIC_MD_NETWORK_SCOPE,
    )
    result = _derive(paths, sha=sha)
    assert result.ok is False
    assert any(b.startswith("ARTIFACT_NETWORK_SCOPE_MISMATCH:") for b in result.blockers)


def test_fail_operator_go_network_scope_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_productive_v2_bundle(tmp_path, sha=sha, go_network_scope="")
    result = _derive(paths, sha=sha)
    assert result.ok is False
    assert "OPERATOR_GO_NETWORK_SCOPE_MISSING" in result.blockers


def test_fail_operator_go_network_scope_wrong(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_productive_v2_bundle(
        tmp_path, sha=sha, go_network_scope="PUBLIC_MARKET_DATA_ONLY"
    )
    result = _derive(paths, sha=sha)
    assert result.ok is False
    assert any(
        "GOVERNED_PUBLIC_MD_NETWORK_SCOPE_MISMATCH" in b or "NETWORK_SCOPE_MISMATCH" in b
        for b in result.blockers
    )


def test_fail_network_allowed_false(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_productive_v2_bundle(tmp_path, sha=sha, network_authorized=False)
    result = _derive(paths, sha=sha)
    assert result.ok is False
    assert "OPERATOR_GO_NETWORK_NOT_AUTHORIZED" in result.blockers
    assert result.network_allowed is False


def test_fail_same_domain_config_digest_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_productive_v2_bundle(tmp_path, sha=sha)
    result = _derive(
        paths,
        sha=sha,
        expected_config_digest="0" * 64,
        expected_config_digest_domain=CONFIG_DIGEST_DOMAIN_WALLCLOCK_CONFIG_IDENTITY,
    )
    assert result.ok is False
    assert "AUTHORIZATION_CONFIG_MISMATCH" in result.blockers


def test_fail_activation_config_domain_incompatible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_productive_v2_bundle(tmp_path, sha=sha)
    activation = _activation_cfg()
    result = _derive(paths, sha=sha, expected_config_digest=activation)
    assert result.ok is False
    assert any("CONFIG_DIGEST_DOMAIN_INCOMPATIBLE" in b for b in result.blockers)


def test_fail_explicit_activation_domain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_productive_v2_bundle(tmp_path, sha=sha)
    result = _derive(
        paths,
        sha=sha,
        expected_config_digest=_activation_cfg(),
        expected_config_digest_domain=CONFIG_DIGEST_DOMAIN_ACTIVATION_CONFIG,
    )
    assert result.ok is False
    assert any("CONFIG_DIGEST_DOMAIN_INCOMPATIBLE" in b for b in result.blockers)


def test_fail_unknown_digest_domain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_productive_v2_bundle(tmp_path, sha=sha)
    result = _derive(
        paths,
        sha=sha,
        expected_config_digest="f" * 64,
        expected_config_digest_domain="not_a_real_domain",
    )
    assert result.ok is False
    assert any(b.startswith("CONFIG_DIGEST_DOMAIN_UNKNOWN:") for b in result.blockers)


def test_fail_authorization_already_consumed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_productive_v2_bundle(
        tmp_path,
        sha=sha,
        state=AuthorizationStateV2.CONSUMED.value,
        consumed_at=NOW,
    )
    result = _derive(paths, sha=sha)
    assert result.ok is False
    assert "AUTHORIZATION_ALREADY_CONSUMED" in result.blockers


def test_pass_adapter_validation_leaves_authorization_unconsumed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_productive_v2_bundle(tmp_path, sha=sha)
    before = json.loads(paths["authorization_artifact"].read_text(encoding="utf-8"))
    result = _derive(
        paths,
        sha=sha,
        expected_config_digest=str(paths["wallclock_hash"]),
        expected_config_digest_domain=CONFIG_DIGEST_DOMAIN_WALLCLOCK_CONFIG_IDENTITY,
    )
    assert result.ok is True
    after = json.loads(paths["authorization_artifact"].read_text(encoding="utf-8"))
    assert after["state"] == AuthorizationStateV2.CREATED_UNCONSUMED.value
    assert after["consumed_at"] is None
    assert after == before
    assert result.claims["AUTHORIZATION_CONSUMED"] is False


def test_fail_wallclock_identity_producer_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_productive_v2_bundle(tmp_path, sha=sha, wallclock_hash="b" * 64)
    result = _derive(paths, sha=sha)
    assert result.ok is False
    assert "WALLCLOCK_CONFIG_IDENTITY_PRODUCER_MISMATCH" in result.blockers
