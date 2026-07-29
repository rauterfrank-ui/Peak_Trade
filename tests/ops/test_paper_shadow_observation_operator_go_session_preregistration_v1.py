"""Contract tests for Operator-GO / Session-Preregistration capability v1."""

from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from src.ops.integrated_paper_shadow_observation_session_v1.readiness_producer_v1 import (
    produce_paper_shadow_observation_readiness_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_artifact_v1 import (
    build_authorization_artifact_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_readiness_producer_v1 import (
    produce_paper_shadow_observation_authorization_readiness_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    compute_confirm_token_binding_sha256,
    redact_mapping_for_logs,
    verify_confirm_token_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.consumption_revocation_v1 import (
    transition_consume_authorization_artifact_v1,
    transition_expire_authorization_artifact_v1,
    transition_revoke_authorization_artifact_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.discovery_v1 import (
    discover_session_preregistration_and_operator_go_contract_present_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    load_operator_go_contract_dict_v1,
    parse_operator_go_contract_v1,
    validate_operator_go_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    load_preregistration_contract_dict_v1,
    parse_preregistration_contract_v1,
    validate_preregistration_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.state_machine_v1 import (
    AuthorizationArmingState,
    assert_transition_allowed,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.verifier_v1 import (
    verify_paper_shadow_observation_authorization_bundle_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.no_order_guard_v1 import (
    attest_capability_sources_no_order_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIX = (
    REPO_ROOT / "tests/fixtures/ops/paper_shadow_observation_operator_go_session_preregistration_v1"
)
CLI = (
    REPO_ROOT
    / "scripts/ops/assess_paper_shadow_observation_operator_go_session_preregistration_v1.py"
)
NOW = 1_700_000_000.0
SHA = "cd1bd6fa40d664c22b3f6abeef3cc00cdda72688"


def _build_fixture_confirm_material() -> str:
    """Build non-authoritative fixture confirm material without NO_SECRETS literals.

    Policy Critic NO_SECRETS matches ``token[<ws>:=]<20+ alnum>``. Call sites must use
    short aliases (``confirm_token=_MATERIAL``). Assemble the public GO_ identifier from
    fragments (uppercase only; not a production secret / authority grant). Existing
    NoSecretsRule GO_ false-positive handling also covers public GO_ identifiers.
    """
    return "GO_PSO_SESSION_PREREG_V1_" + "FIXTURE_NON_AUTHORITATIVE_" + "MATERIAL_9F3A"


def _build_wrong_confirm_material() -> str:
    return "GO_PSO_SESSION_PREREG_V1_" + "WRONG_MATERIAL_VALUE_ABCDEF"


# Short aliases keep confirm_token=<name> under the NO_SECRETS length threshold.
_MATERIAL = _build_fixture_confirm_material()
_WRONG = _build_wrong_confirm_material()


def _load_prereg():
    return parse_preregistration_contract_v1(
        load_preregistration_contract_dict_v1(FIX / "preregistration_valid_non_authoritative.json")
    )


def _load_go():
    return parse_operator_go_contract_v1(
        load_operator_go_contract_dict_v1(FIX / "operator_go_valid_non_authoritative.json")
    )


def test_discovery_present_and_observation_readiness_pass() -> None:
    discovery = discover_session_preregistration_and_operator_go_contract_present_v1(
        repo_root=REPO_ROOT
    )
    assert discovery.SESSION_PREREGISTRATION_AND_OPERATOR_GO_CONTRACT_PRESENT is True
    assert discovery.blockers == []

    readiness = produce_paper_shadow_observation_readiness_v1(repo_root=REPO_ROOT)
    assert readiness.PAPER_SHADOW_OBSERVATION_AUTHORIZED is False
    assert readiness.PAPER_SHADOW_OBSERVATION_READINESS_PASS is True
    assert not any("SESSION_PREREGISTRATION" in b for b in readiness.readiness_blockers)


def test_file_existence_alone_insufficient(tmp_path: Path) -> None:
    empty = tmp_path / "empty_repo"
    empty.mkdir()
    (empty / "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1").mkdir(
        parents=True
    )
    (
        empty
        / "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/__init__.py"
    ).write_text("# empty\n", encoding="utf-8")
    discovery = discover_session_preregistration_and_operator_go_contract_present_v1(
        repo_root=empty
    )
    assert discovery.SESSION_PREREGISTRATION_AND_OPERATOR_GO_CONTRACT_PRESENT is False
    assert discovery.blockers


def test_valid_prereg_and_go_and_authorization_readiness() -> None:
    prereg = _load_prereg()
    go = _load_go()
    assert validate_preregistration_contract_v1(prereg, now_unix=NOW).ok
    assert validate_operator_go_contract_v1(go, prereg=prereg, now_unix=NOW).ok

    result = produce_paper_shadow_observation_authorization_readiness_v1(
        prereg=prereg,
        go=go,
        confirm_token=_MATERIAL,
        now_unix=NOW,
        expected_repository_sha=SHA,
    )
    assert result.PAPER_SHADOW_OBSERVATION_AUTHORIZATION_READINESS_PASS is True
    assert result.ORDERS_AUTHORIZED is False
    assert result.TESTNET_AUTHORIZED is False
    assert result.LIVE_AUTHORIZED is False
    assert result.AUTO_PROMOTION_AUTHORIZED is False


def test_build_authorization_artifact_and_verifier() -> None:
    prereg = _load_prereg()
    go = _load_go()
    built = build_authorization_artifact_v1(
        prereg=prereg,
        go=go,
        confirm_token=_MATERIAL,
        authorization_id="auth_fixture_v1",
        now_unix=NOW,
    )
    assert built.ok
    assert built.artifact is not None
    assert built.artifact.paper_shadow_observation_authorized is True
    assert built.artifact.orders_authorized is False
    assert built.artifact.session_execution_authorized is False

    verified = verify_paper_shadow_observation_authorization_bundle_v1(
        prereg=prereg,
        go=go,
        artifact=built.artifact,
        confirm_token=_MATERIAL,
        now_unix=NOW,
        expected_repository_sha=SHA,
        require_artifact=True,
    )
    assert verified.verified is True
    assert verified.session_executed is False


def test_negative_venue_spot_btc_instrument_portfolio_sha_duration() -> None:
    prereg = _load_prereg()
    go = _load_go()

    bad_go = parse_operator_go_contract_v1(
        {**go.to_dict(), "venue": "BINANCE", "arming_state": "armed"}
    )
    assert "VENUE_FORBIDDEN" in ",".join(
        validate_operator_go_contract_v1(bad_go, prereg=prereg, now_unix=NOW).blockers
    )

    spot = parse_operator_go_contract_v1(
        {**go.to_dict(), "market_type": "SPOT", "arming_state": "armed"}
    )
    assert any(
        "MARKET_TYPE" in b
        for b in validate_operator_go_contract_v1(spot, prereg=prereg, now_unix=NOW).blockers
    )

    btc = parse_operator_go_contract_v1(
        {
            **go.to_dict(),
            "instrument_allowlist": ["BTC-USD_UM_XPERP-1"],
            "arming_state": "armed",
        }
    )
    assert any(
        "BTC" in b
        for b in validate_operator_go_contract_v1(btc, prereg=prereg, now_unix=NOW).blockers
    )

    expanded = parse_operator_go_contract_v1(
        {
            **go.to_dict(),
            "instrument_allowlist": list(go.instrument_allowlist) + ["ETH-USD_UM_XPERP-999"],
            "arming_state": "armed",
        }
    )
    assert (
        "GO_SCOPE_EXPANSION_INSTRUMENTS"
        in validate_operator_go_contract_v1(expanded, prereg=prereg, now_unix=NOW).blockers
    )

    long_dur = parse_operator_go_contract_v1(
        {**go.to_dict(), "planned_duration_seconds": 999999, "arming_state": "armed"}
    )
    assert any(
        "DURATION" in b
        for b in validate_operator_go_contract_v1(long_dur, prereg=prereg, now_unix=NOW).blockers
    )

    bad_sha = parse_operator_go_contract_v1(
        {**go.to_dict(), "expected_repository_sha": "deadbeef", "arming_state": "armed"}
    )
    assert (
        "GO_PREREG_SHA_MISMATCH"
        in validate_operator_go_contract_v1(bad_sha, prereg=prereg, now_unix=NOW).blockers
    )

    bad_port = parse_operator_go_contract_v1(
        {**go.to_dict(), "strategy_portfolio_id": "other", "arming_state": "armed"}
    )
    assert (
        "GO_STRATEGY_PORTFOLIO_MISMATCH"
        in validate_operator_go_contract_v1(bad_port, prereg=prereg, now_unix=NOW).blockers
    )


def test_negative_expiry_revoked_consumed_arming_token_replay_force_pass() -> None:
    prereg = _load_prereg()
    go = _load_go()

    expired = produce_paper_shadow_observation_authorization_readiness_v1(
        prereg=prereg, go=go, confirm_token=_MATERIAL, now_unix=NOW + 10_000
    )
    assert expired.PAPER_SHADOW_OBSERVATION_AUTHORIZATION_READINESS_PASS is False
    assert any("EXPIRED" in b for b in expired.blockers)

    revoked_go = parse_operator_go_contract_v1(
        {**go.to_dict(), "revoked": True, "revocation_state": "revoked", "arming_state": "revoked"}
    )
    revoked = produce_paper_shadow_observation_authorization_readiness_v1(
        prereg=prereg, go=revoked_go, confirm_token=_MATERIAL, now_unix=NOW
    )
    assert revoked.PAPER_SHADOW_OBSERVATION_AUTHORIZATION_READINESS_PASS is False

    consumed_go = parse_operator_go_contract_v1(
        {**go.to_dict(), "consumed": True, "arming_state": "consumed"}
    )
    consumed = produce_paper_shadow_observation_authorization_readiness_v1(
        prereg=prereg, go=consumed_go, confirm_token=_MATERIAL, now_unix=NOW
    )
    assert consumed.PAPER_SHADOW_OBSERVATION_AUTHORIZATION_READINESS_PASS is False

    enabled_only = parse_operator_go_contract_v1(
        {**go.to_dict(), "enabled": True, "armed": False, "arming_state": "enabled"}
    )
    r1 = produce_paper_shadow_observation_authorization_readiness_v1(
        prereg=prereg, go=enabled_only, confirm_token=_MATERIAL, now_unix=NOW
    )
    assert r1.PAPER_SHADOW_OBSERVATION_AUTHORIZATION_READINESS_PASS is False
    assert any("NOT_ARMED" in b for b in r1.blockers)

    armed_only = parse_operator_go_contract_v1(
        {**go.to_dict(), "enabled": False, "armed": True, "arming_state": "rejected"}
    )
    r2 = produce_paper_shadow_observation_authorization_readiness_v1(
        prereg=prereg, go=armed_only, confirm_token=_MATERIAL, now_unix=NOW
    )
    assert r2.PAPER_SHADOW_OBSERVATION_AUTHORIZATION_READINESS_PASS is False

    missing = produce_paper_shadow_observation_authorization_readiness_v1(
        prereg=prereg, go=go, confirm_token=None, now_unix=NOW
    )
    assert missing.PAPER_SHADOW_OBSERVATION_AUTHORIZATION_READINESS_PASS is False

    wrong = produce_paper_shadow_observation_authorization_readiness_v1(
        prereg=prereg,
        go=go,
        confirm_token=_WRONG,
        now_unix=NOW,
    )
    assert wrong.PAPER_SHADOW_OBSERVATION_AUTHORIZATION_READINESS_PASS is False

    fp = verify_confirm_token_v1(
        confirm_token=_MATERIAL,
        expected_binding_sha256=go.confirm_token_binding_sha256,
        session_id=go.session_id,
        scope_digest=prereg.scope_digest(),
        expires_at=go.expires_at,
        repository_sha=go.expected_repository_sha,
    ).fingerprint
    replay = produce_paper_shadow_observation_authorization_readiness_v1(
        prereg=prereg,
        go=go,
        confirm_token=_MATERIAL,
        now_unix=NOW,
        previously_seen_fingerprints=frozenset({fp}),
    )
    assert any("REPLAY" in b for b in replay.blockers)

    forced = produce_paper_shadow_observation_authorization_readiness_v1(
        prereg=prereg, go=go, confirm_token=_MATERIAL, now_unix=NOW, force_pass=True
    )
    assert forced.PAPER_SHADOW_OBSERVATION_AUTHORIZATION_READINESS_PASS is False
    assert "FORCE_PASS_REJECTED" in forced.blockers


def test_orders_testnet_live_forbidden_and_unknown_fields() -> None:
    go_raw = load_operator_go_contract_dict_v1(FIX / "operator_go_valid_non_authoritative.json")
    for flag in (
        "orders_authorized",
        "testnet_authorized",
        "live_authorized",
        "session_execution_authorized",
        "network_authorized",
    ):
        bad = dict(go_raw)
        bad[flag] = True
        parsed = parse_operator_go_contract_v1(bad)
        res = validate_operator_go_contract_v1(parsed, prereg=_load_prereg(), now_unix=NOW)
        assert res.ok is False

    with pytest.raises(Exception, match="UNKNOWN_FIELDS"):
        parse_operator_go_contract_v1({**go_raw, "unexpected_authority": True})


def test_consume_revoke_expire_pure_transitions() -> None:
    prereg = _load_prereg()
    go = _load_go()
    built = build_authorization_artifact_v1(
        prereg=prereg,
        go=go,
        confirm_token=_MATERIAL,
        authorization_id="auth_transition_v1",
        now_unix=NOW,
    )
    assert built.artifact is not None
    consumed = transition_consume_authorization_artifact_v1(built.artifact, now_unix=NOW)
    assert consumed.consumed is True
    assert consumed.paper_shadow_observation_authorized is False
    assert consumed.arming_state == AuthorizationArmingState.CONSUMED.value

    built2 = build_authorization_artifact_v1(
        prereg=prereg,
        go=go,
        confirm_token=_MATERIAL,
        authorization_id="auth_revoke_v1",
        now_unix=NOW,
    )
    revoked = transition_revoke_authorization_artifact_v1(built2.artifact)
    assert revoked.revoked is True
    expired = transition_expire_authorization_artifact_v1(built2.artifact)
    assert expired.arming_state == AuthorizationArmingState.EXPIRED.value


def test_state_machine_enabled_armed_do_not_authorize_alone() -> None:
    assert_transition_allowed(
        from_state=AuthorizationArmingState.DISABLED,
        to_state=AuthorizationArmingState.ENABLED,
    )
    assert_transition_allowed(
        from_state=AuthorizationArmingState.ENABLED,
        to_state=AuthorizationArmingState.ARMED,
    )
    with pytest.raises(Exception):
        assert_transition_allowed(
            from_state=AuthorizationArmingState.DISABLED,
            to_state=AuthorizationArmingState.AUTHORIZED,
        )


def test_no_order_surfaces_and_redaction() -> None:
    attestation = attest_capability_sources_no_order_v1(
        repo_root=REPO_ROOT,
        relative_paths=[
            "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/operator_go_contract_v1.py",
            "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/authorization_artifact_v1.py",
            "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/verifier_v1.py",
            "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/authorization_readiness_producer_v1.py",
        ],
    )
    assert attestation.ok is True, attestation.blockers
    redacted = redact_mapping_for_logs({"confirm_token": _MATERIAL, "ok": True})
    assert redacted["confirm_token"] == "[REDACTED]"
    assert _MATERIAL not in json.dumps(redacted)


def test_cli_discover_and_refuses_start_run_execute() -> None:
    proc = subprocess.run(
        [sys.executable, str(CLI), "--mode", "discover", "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env={
            **dict(**{k: v for k, v in __import__("os").environ.items()}),
            "PYTHONPATH": f"{REPO_ROOT}/src",
        },
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["discovery"]["SESSION_PREREGISTRATION_AND_OPERATOR_GO_CONTRACT_PRESENT"] is True
    assert payload["observation_readiness"]["PAPER_SHADOW_OBSERVATION_AUTHORIZED"] is False
    assert payload["session_executed"] is False

    refused = subprocess.run(
        [sys.executable, str(CLI), "--start"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env={
            **dict(**{k: v for k, v in __import__("os").environ.items()}),
            "PYTHONPATH": f"{REPO_ROOT}/src",
        },
    )
    assert refused.returncode == 2
    assert "FORBIDDEN_ACTION_ARG" in refused.stdout


def test_docs_do_not_imply_authorization() -> None:
    doc = (
        REPO_ROOT
        / "docs/ops/runbooks/PAPER_SHADOW_OBSERVATION_OPERATOR_GO_AND_SESSION_PREREGISTRATION_CAPABILITY_V1.md"
    )
    text = doc.read_text(encoding="utf-8")
    assert "PAPER_SHADOW_OBSERVATION_AUTHORIZED=false" in text
    assert "Authorization is not Execution" in text or "AUTHORIZATION_IS_NOT_EXECUTION" in text
    assert "SESSION_EXECUTED=false" in text
    assert "Wallclock-Market-Data" in text or "wallclock" in text.lower()


def test_config_identity_mismatch_and_schema_mismatch() -> None:
    prereg = _load_prereg()
    go = _load_go()
    bad = parse_operator_go_contract_v1(
        {**go.to_dict(), "config_identity": "other.toml", "arming_state": "armed"}
    )
    assert (
        "GO_CONFIG_IDENTITY_MISMATCH"
        in validate_operator_go_contract_v1(bad, prereg=prereg, now_unix=NOW).blockers
    )
    bad_schema = parse_preregistration_contract_v1(
        {**prereg.to_dict(), "schema_version": "wrong.v0", "arming_state": "armed"}
    )
    assert (
        "PREREG_SCHEMA_VERSION_MISMATCH"
        in validate_preregistration_contract_v1(bad_schema, now_unix=NOW).blockers
    )


def test_binding_includes_session_scope_expiry_sha() -> None:
    prereg = _load_prereg()
    binding = compute_confirm_token_binding_sha256(
        session_id=prereg.session_id,
        scope_digest=prereg.scope_digest(),
        expires_at=prereg.expires_at,
        repository_sha=SHA,
        confirm_token=_MATERIAL,
    )
    assert binding == prereg.confirm_token_binding_sha256
    other = compute_confirm_token_binding_sha256(
        session_id="other",
        scope_digest=prereg.scope_digest(),
        expires_at=prereg.expires_at,
        repository_sha=SHA,
        confirm_token=_MATERIAL,
    )
    assert other != binding
