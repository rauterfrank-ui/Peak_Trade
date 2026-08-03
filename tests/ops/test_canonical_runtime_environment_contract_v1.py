"""CAPABILITY_O1_CANONICAL_ENVIRONMENT_AND_MACOS_PLATFORM_CONTRACT_V1 tests."""

from __future__ import annotations

import copy
import os
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.ops.canonical_runtime_environment_contract_v1.builder_v1 import (
    CanonicalEnvironmentContractError,
    build_effective_runtime_environment_v1,
    build_or_raise_effective_runtime_environment_v1,
)
from src.ops.canonical_runtime_environment_contract_v1.constants_v1 import (
    ALLOWLIST_KEYS,
    ENVIRONMENT_POLICY_ID,
    MACOS_PORTABILITY_CONTRACT,
    REJECTED_PROXY_KEYS,
)
from src.ops.canonical_runtime_environment_contract_v1.digest_v1 import (
    effective_environment_digest_v1,
    parent_environment_digest_v1,
    redact_environment_mapping_v1,
)
from src.ops.canonical_runtime_environment_contract_v1.macos_portability_v1 import (
    run_macos_portability_preflight_v1,
)
from src.ops.canonical_runtime_environment_contract_v1.policy_v1 import (
    classify_parent_environment_v1,
)
from src.ops.canonical_runtime_environment_contract_v1.preflight_v1 import (
    assert_http_client_proxy_env_clean_v1,
    assert_preflight_before_authorization_consumption_v1,
    assert_preflight_before_network_client_construction_v1,
    assert_preflight_before_ohlcv_http_client_construction_v1,
    collect_proxy_no_proxy_blockers_v1,
    run_canonical_environment_preflight_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.network_boundary_guard_v1 import (
    assert_proxy_policy_fail_closed_v1,
    validate_request_boundary_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_run_entrypoint_v1 import (
    run_productive_wallclock_session_v1,
)
from src.ops.okx_public_market_data_client_v1 import (
    OkxPublicMarketDataClientV1,
    _build_proxy_free_https_opener_v1,
)


def _minimal_allowlist_env(**overrides: str) -> dict[str, str]:
    base = {
        "PATH": "/usr/bin:/bin",
        "PYTHONPATH": "/repo",
        "PYTHONUNBUFFERED": "1",
        "MPLCONFIGDIR": "/tmp/mpl",
        "HOME": "/tmp/home",
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "TMPDIR": "/tmp",
        "PEAK_TRADE_RUNTIME_MODE": "public_md_no_order",
        "PEAK_TRADE_REPOSITORY_SHA": "abc123",
        "PEAK_TRADE_CONFIG_PATH": "/tmp/config.json",
        "PEAK_TRADE_CONFIG_DIGEST": "deadbeef",
        "PEAK_TRADE_SESSION_ID": "sess-1",
        "PEAK_TRADE_AUTHORIZATION_ARTIFACT_PATH": "/tmp/auth.json",
        "PEAK_TRADE_CONFIRM_TOKEN_FILE": "/tmp/token",
        "PEAK_TRADE_PSO_WALLCLOCK_ALLOW_REAL_NETWORK": "1",
        "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT": "/tmp/archive",
        "PEAK_TRADE_LOG_ROOT": "/tmp/logs",
        "PEAK_TRADE_STATE_ROOT": "/tmp/state",
        "PEAK_TRADE_EVIDENCE_ROOT": "/tmp/evidence",
        "PEAK_TRADE_ENVIRONMENT_POLICY_ID": ENVIRONMENT_POLICY_ID,
    }
    base.update(overrides)
    return base


def test_allowlisted_environment_accepted() -> None:
    parent = _minimal_allowlist_env()
    result = build_effective_runtime_environment_v1(parent)
    assert result.ok
    assert result.environment_policy_id == ENVIRONMENT_POLICY_ID
    assert set(result.effective_environ) <= set(ALLOWLIST_KEYS)
    assert result.effective_environ["PEAK_TRADE_ENVIRONMENT_POLICY_ID"] == ENVIRONMENT_POLICY_ID


def test_deterministic_effective_environment_construction() -> None:
    parent = _minimal_allowlist_env(CURSOR_TRACE_ID="x", VSCODE_IPC_HOOK="y", TERM_SESSION_ID="z")
    a = build_effective_runtime_environment_v1(parent)
    b = build_effective_runtime_environment_v1(dict(reversed(list(parent.items()))))
    assert a.ok and b.ok
    assert a.effective_environ == b.effective_environ
    assert a.effective_environment_digest == b.effective_environment_digest


def test_global_os_environ_unchanged() -> None:
    before = copy.deepcopy(dict(os.environ))
    parent = _minimal_allowlist_env(HTTPS_PROXY="http://evil:1")
    result = build_effective_runtime_environment_v1(parent)
    assert not result.ok
    assert dict(os.environ) == before


def test_cursor_and_vscode_keys_stripped() -> None:
    parent = _minimal_allowlist_env(CURSOR_AGENT="1", VSCODE_PID="2", COLORFGBG="15;0")
    classification = classify_parent_environment_v1(parent)
    assert "CURSOR_AGENT" in classification.stripped_keys
    assert "VSCODE_PID" in classification.stripped_keys
    assert "COLORFGBG" in classification.stripped_keys
    result = build_or_raise_effective_runtime_environment_v1(parent)
    assert "CURSOR_AGENT" not in result
    assert "VSCODE_PID" not in result


@pytest.mark.parametrize(
    "key",
    sorted(
        k
        for k in REJECTED_PROXY_KEYS
        if k
        in {
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ALL_PROXY",
            "http_proxy",
            "https_proxy",
            "all_proxy",
            "SOCKS_PROXY",
            "SOCKS5_PROXY",
            "socks_proxy",
            "socks5_proxy",
            "GIT_HTTP_PROXY",
            "GIT_HTTPS_PROXY",
            "NO_PROXY",
            "no_proxy",
        }
    ),
)
def test_proxy_and_no_proxy_keys_rejected(key: str) -> None:
    parent = _minimal_allowlist_env(**{key: "http://proxy.example:8080"})
    result = build_effective_runtime_environment_v1(parent)
    assert not result.ok
    assert key in result.rejected_keys
    blockers = collect_proxy_no_proxy_blockers_v1(parent)
    assert any(key in b for b in blockers)


def test_unexpected_non_allowlisted_variable_rejected() -> None:
    parent = _minimal_allowlist_env(UNEXPECTED_MALICIOUS_FLAG="1")
    result = build_effective_runtime_environment_v1(parent)
    assert not result.ok
    assert "UNEXPECTED_MALICIOUS_FLAG" in result.rejected_keys


def test_credential_marker_rejected_without_printing_value() -> None:
    secret = "super-secret-value-do-not-leak"
    parent = _minimal_allowlist_env(OKX_API_KEY=secret)
    result = build_effective_runtime_environment_v1(parent)
    assert not result.ok
    blob = str(result.to_dict()) + ",".join(result.blockers) + ",".join(result.reason_codes)
    assert secret not in blob
    assert any("CREDENTIAL" in b for b in result.blockers)


def test_parent_and_effective_digest_deterministic_and_redacted() -> None:
    parent = _minimal_allowlist_env()
    d1 = parent_environment_digest_v1(parent)
    d2 = parent_environment_digest_v1(parent)
    assert d1 == d2
    redacted = redact_environment_mapping_v1(parent)
    assert redacted["HOME"].startswith("sha256:")
    assert "/tmp/home" not in redacted["HOME"]
    built = build_or_raise_effective_runtime_environment_v1(parent)
    e1 = effective_environment_digest_v1(built)
    e2 = effective_environment_digest_v1(built)
    assert e1 == e2


def test_preflight_before_authorization_consumption_api() -> None:
    parent = _minimal_allowlist_env()
    result = assert_preflight_before_authorization_consumption_v1(parent)
    assert result.ok
    assert result.stage == "BEFORE_AUTHORIZATION_CONSUMPTION"


def test_preflight_before_network_and_ohlcv_client_apis() -> None:
    parent = _minimal_allowlist_env()
    net = assert_preflight_before_network_client_construction_v1(parent)
    ohlcv = assert_preflight_before_ohlcv_http_client_construction_v1(parent)
    assert net.ok and ohlcv.ok
    assert net.stage == "BEFORE_NETWORK_CLIENT_CONSTRUCTION"
    assert ohlcv.stage == "BEFORE_OHLCV_HTTP_CLIENT_CONSTRUCTION"


def test_preflight_ordering_before_productive_auth_gate(tmp_path: Any) -> None:
    """Proxy preflight aborts productive run before authorization consumption side effects."""
    dirty = {"HTTPS_PROXY": "http://evil:8080", "PEAK_TRADE_PSO_WALLCLOCK_ALLOW_REAL_NETWORK": "1"}
    from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
        OperatorGoContractV1,
    )
    from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
        SessionPreregistrationContractV1,
    )

    prereg = MagicMock(spec=SessionPreregistrationContractV1)
    go = MagicMock(spec=OperatorGoContractV1)
    go.session_id = "sess-test"
    artifact = tmp_path / "missing_auth.json"
    result = run_productive_wallclock_session_v1(
        prereg=prereg,
        go=go,
        confirm_token="token",
        artifact_path=artifact,
        evidence_root=tmp_path / "evidence",
        expected_repository_sha="abc",
        fingerprint_ledger_path=tmp_path / "ledger.json",
        use_real_network=True,
        environ=dirty,
    )
    assert result.ok is False
    assert any("HTTPS_PROXY" in b for b in result.blockers)
    assert "O1_PREFLIGHT_BEFORE_AUTHORIZATION_CONSUMPTION" in result.notes
    assert not (tmp_path / "evidence" / "authorization_consumption_record.json").exists()
    _ = OperatorGoContractV1


def test_dashboard_ohlcv_client_cannot_inherit_parent_proxy_state() -> None:
    dirty = {"HTTPS_PROXY": "http://evil:8080"}
    with pytest.raises(CanonicalEnvironmentContractError) as exc:
        assert_http_client_proxy_env_clean_v1(environ=dirty)
    assert any("HTTPS_PROXY" in b for b in exc.value.blockers)
    with pytest.raises(CanonicalEnvironmentContractError):
        OkxPublicMarketDataClientV1(environ=dirty, enforce_proxy_preflight=True)
    opener = _build_proxy_free_https_opener_v1()
    handler_types = {type(h).__name__ for h in opener.handlers}
    assert "ProxyHandler" not in handler_types


def test_public_md_client_cannot_inherit_parent_proxy_state() -> None:
    dirty = {"ALL_PROXY": "socks5://evil:1080", "NO_PROXY": "*"}
    blockers = assert_proxy_policy_fail_closed_v1(environ=dirty)
    assert any("ALL_PROXY" in b for b in blockers)
    assert any("NO_PROXY" in b for b in blockers)
    attestation = validate_request_boundary_v1(
        url="https://eea.okx.com/api/v5/public/mark-price?instId=BTC-USD-260327",
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "t"},
        environ=dirty,
        allow_proxy=False,
    )
    assert not attestation.ok


def test_macos_path_does_not_require_setsid_executable() -> None:
    result = run_macos_portability_preflight_v1()
    assert MACOS_PORTABILITY_CONTRACT["SETSID_CLI_REQUIRED"] is False
    assert result.setsid_cli_required is False
    assert result.ok
    assert result.launch_backend_deferred_to_o2 is True
    # Absence of setsid CLI must not fail O1.
    if not result.setsid_cli_present:
        assert result.ok


def test_no_o2_supervisor_or_launcher_symbols_introduced() -> None:
    import src.ops.canonical_runtime_environment_contract_v1 as pkg

    banned = (
        "start_supervisor",
        "process_group",
        "pid_file",
        "launchd",
        "peak_trade_runtime",
        "session_registry",
    )
    surface = " ".join(dir(pkg)).lower()
    for token in banned:
        assert token not in surface


def test_full_preflight_rejects_proxy_before_effective_build() -> None:
    parent = _minimal_allowlist_env(http_proxy="http://x")
    result = run_canonical_environment_preflight_v1(
        parent, stage="BEFORE_AUTHORIZATION_CONSUMPTION"
    )
    assert not result.ok
    assert result.effective_environment_digest == ""


def test_empty_no_proxy_key_presence_rejected() -> None:
    parent = _minimal_allowlist_env()
    parent["NO_PROXY"] = ""
    blockers = collect_proxy_no_proxy_blockers_v1(parent)
    assert any("NO_PROXY" in b for b in blockers)


def test_network_fetcher_construction_preflight(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1 import (
        real_http_fetcher_v1 as mod,
    )

    with pytest.raises(CanonicalEnvironmentContractError):
        mod.make_real_eea_public_md_fetcher_v1(environ={"HTTPS_PROXY": "http://evil:1"})


def test_refresh_dashboard_preflight_blocks_proxy(
    tmp_path: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts.ops.refresh_okx_market_dashboard_v1 import refresh_okx_market_dashboard_v1

    with pytest.raises(SystemExit) as exc:
        refresh_okx_market_dashboard_v1(
            archive_root=tmp_path,
            venue="OKX",
            market_type="FUTURES",
            settle_ccy="USD",
            exclude_underlying="",
            bar="1H",
            verify_manifest=False,
            materialize_readmodels=False,
            dry_run=True,
            environ={"HTTPS_PROXY": "http://evil:1"},
        )
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "O1_PROXY_POLICY_FAILURE" in err
    assert "HTTPS_PROXY" in err
