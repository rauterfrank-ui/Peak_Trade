"""GHV Full-System Testnet Observation PRE_EXTERNAL binding v1."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    FullCoreK1OkxVenueAuthError,
    bind_already_held_k1_venue_auth_session_v1,
    build_k1_okx_venue_auth_headers_v1,
    release_k1_venue_auth_session_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    TRANSPORT_CLASS_GHV_DEMO_READ_ONLY_GET,
    FreshPretradeGetTransportResultV1,
    _item_status_and_reasons,
    FreshPretradeGetItemSpecV1,
    ENDPOINT_ACCOUNT_BALANCE,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.constants_v1 import (
    PRIVATE_DEMO_HEADER_NAME,
    TRANSPORT_CLASS_DEMO_READ_ONLY_GET,
    write_contract_proof_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.demo_credential_bind_v1 import (
    GhvTestnetDemoCredentialBindError,
    assert_demo_credential_class_v1,
    assert_live_k1_credential_class_v1,
    open_ghv_testnet_demo_get_only_fresh_pretrade_transport_v1,
    prove_credential_isolation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.demo_okx_venue_auth_headers_v1 import (
    GhvDemoOkxVenueAuthError,
    bind_already_held_demo_venue_auth_session_v1,
    build_demo_okx_public_headers_v1,
    build_demo_okx_venue_auth_headers_v1,
    release_demo_venue_auth_session_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.demo_read_only_get_transport_v1 import (
    GhvDemoReadOnlyGetTransportError,
    GhvDemoReadOnlyGetTransportV1,
    reject_non_get_http_method_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.environment_validation_v1 import (
    GhvTestnetEnvironmentValidationInputV1,
    evaluate_ghv_testnet_environment_validation_v1,
    prove_instrument_identity_owners_unchanged_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.governance_v1 import (
    GhvTestnetObservationGovernanceError,
    OWNER_GO,
    assert_full_system_testnet_observation_owner_go_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.state_roots_v1 import (
    GhvTestnetStateIsolationError,
    assert_ghv_testnet_observation_state_roots_isolated_v1,
    derive_ghv_testnet_observation_state_roots_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.account_observation_evidence_v1 import (
    prove_outcome_closure_evidence_separation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REQUIRED_CREDENTIAL_CLASS as LIVE_K1_CREDENTIAL_CLASS,
)

_SYNTH_KEY = "k-demo"
_SYNTH_SECRET = "s-demo"
_SYNTH_PASS = "p-demo"
_GET_URL = "https://eea.okx.com/api/v5/account/balance"


def test_environment_contract_public_vs_demo_header_policy() -> None:
    proof = write_contract_proof_v1()
    assert proof["PUBLIC_DEMO_HEADER_REQUIRED"] is False
    assert proof["PRIVATE_DEMO_HEADER_REQUIRED"] is True
    assert proof["POST_ALLOWED"] is False
    assert proof["EXTERNAL_EFFECT_AUTHORIZED"] is False


def test_public_get_headers_exclude_demo_marker() -> None:
    headers = build_demo_okx_public_headers_v1()
    assert PRIVATE_DEMO_HEADER_NAME not in {k.lower() for k in headers}


def test_demo_private_get_requires_simulated_trading_header() -> None:
    handle = bind_already_held_demo_venue_auth_session_v1(
        api_key=_SYNTH_KEY,
        api_secret=_SYNTH_SECRET,
        passphrase=_SYNTH_PASS,
    )
    try:
        headers = build_demo_okx_venue_auth_headers_v1(
            handle=handle,
            url=_GET_URL,
            method="GET",
        )
        assert headers.get("x-simulated-trading") == "1"
    finally:
        release_demo_venue_auth_session_v1(handle)


def test_demo_private_get_without_demo_header_flag_rejected() -> None:
    handle = bind_already_held_demo_venue_auth_session_v1(
        api_key=_SYNTH_KEY,
        api_secret=_SYNTH_SECRET,
        passphrase=_SYNTH_PASS,
    )
    try:
        with pytest.raises(GhvDemoOkxVenueAuthError, match="DEMO_PRIVATE_GET_REQUIRES_DEMO_HEADER"):
            build_demo_okx_venue_auth_headers_v1(
                handle=handle,
                url=_GET_URL,
                method="GET",
                require_demo_header=False,
            )
    finally:
        release_demo_venue_auth_session_v1(handle)


def test_demo_header_on_live_k1_rejected() -> None:
    handle = bind_already_held_k1_venue_auth_session_v1(
        api_key=_SYNTH_KEY,
        api_secret=_SYNTH_SECRET,
        passphrase=_SYNTH_PASS,
    )
    try:
        with pytest.raises(FullCoreK1OkxVenueAuthError, match="DEMO_SIMULATION_HEADER_FORBIDDEN"):
            build_k1_okx_venue_auth_headers_v1(
                handle=handle,
                url=_GET_URL,
                method="GET",
                extra_headers={"x-simulated-trading": "1"},
            )
    finally:
        release_k1_venue_auth_session_v1(handle)


def test_live_credential_in_demo_bind_rejected() -> None:
    with pytest.raises(GhvTestnetDemoCredentialBindError, match="LIVE_CREDENTIAL_IN_DEMO_BIND"):
        assert_demo_credential_class_v1(LIVE_K1_CREDENTIAL_CLASS)


def test_demo_credential_in_live_bind_rejected() -> None:
    with pytest.raises(GhvTestnetDemoCredentialBindError, match="DEMO_CREDENTIAL_IN_LIVE_BIND"):
        assert_live_k1_credential_class_v1("OKX_EEA_DEMO_TRADING_API_KEY_ONLY")


def test_credential_isolation_proof() -> None:
    proof = prove_credential_isolation_v1()
    assert proof["LIVE_K1_DEMO_HEADER_ALLOWED"] == "false"
    assert proof["DEMO_CREDENTIAL_LIVE_K1_REUSE_ALLOWED"] == "false"


def test_non_get_methods_rejected() -> None:
    with pytest.raises(GhvDemoReadOnlyGetTransportError, match="NON_GET_FORBIDDEN"):
        reject_non_get_http_method_v1("POST")


def test_demo_transport_private_get_uses_demo_header_via_mock() -> None:
    handle = bind_already_held_demo_venue_auth_session_v1(
        api_key=_SYNTH_KEY,
        api_secret=_SYNTH_SECRET,
        passphrase=_SYNTH_PASS,
    )
    captured: dict[str, str] = {}

    def _factory() -> MagicMock:
        opener = MagicMock()
        resp = MagicMock()
        resp.status = 200
        resp.read.return_value = b'{"code":"0","data":[]}'
        resp.url = _GET_URL
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)

        def _open(req, timeout=0):  # noqa: ARG001
            captured.update(dict(req.headers.items()))
            return resp

        opener.open.side_effect = _open
        return opener

    transport = GhvDemoReadOnlyGetTransportV1(
        handle=handle,
        max_request_count=2,
        http_opener_factory=_factory,
    )
    try:
        result = transport.get(
            endpoint="/api/v5/account/balance",
            auth_required=True,
            pretrade_decision_id="t1",
        )
        assert result.get_performed is True
        assert (
            captured.get("X-simulated-trading") == "1" or captured.get("x-simulated-trading") == "1"
        )
    finally:
        release_demo_venue_auth_session_v1(handle)


def test_demo_transport_has_no_post_method() -> None:
    assert not hasattr(GhvDemoReadOnlyGetTransportV1, "post")


def test_instrument_identity_mismatch_fail_closed() -> None:
    result = evaluate_ghv_testnet_environment_validation_v1(
        input_v1=GhvTestnetEnvironmentValidationInputV1(
            cap23_selected_native_id="A",
            cap24_bound_native_id="B",
            validation_native_id="B",
        ),
    )
    assert result.fail_closed is True
    assert "CAP23_CAP24_NATIVE_ID_MISMATCH" in result.reason_codes


def test_instrument_substitution_probe_mismatch_fail_closed() -> None:
    native = "ETH-USD_UM_XPERP-310328"
    result = evaluate_ghv_testnet_environment_validation_v1(
        input_v1=GhvTestnetEnvironmentValidationInputV1(
            cap23_selected_native_id=native,
            cap24_bound_native_id=native,
            validation_native_id="BTC-USD_UM_XPERP-310328",
        ),
    )
    assert result.fail_closed is True
    assert "TESTNET_INSTRUMENT_MISMATCH" in result.reason_codes


def test_instrument_identity_owners_unchanged_proof() -> None:
    proof = prove_instrument_identity_owners_unchanged_v1()
    assert proof["SELECTED_INSTRUMENT_OWNER"] == "Cap23"
    assert proof["BOUND_INSTRUMENT_OWNER"] == "Cap24"


def test_fresh_pretrade_accepts_demo_transport_class() -> None:
    spec = FreshPretradeGetItemSpecV1("AVAILABLE_MARGIN", ENDPOINT_ACCOUNT_BALANCE, True, "balance")
    result = FreshPretradeGetTransportResultV1(
        get_performed=True,
        method="GET",
        endpoint=ENDPOINT_ACCOUNT_BALANCE,
        http_status=200,
        payload={"code": "0", "data": [{"availBal": "1", "ccy": "USDT"}]},
        auth_header_sent=True,
        transport_class=TRANSPORT_CLASS_GHV_DEMO_READ_ONLY_GET,
        venue_live_contact=True,
        historical_reuse=False,
        error_class="",
    )
    status, _ = _item_status_and_reasons(
        spec=spec,
        result=result,
        pretrade_decision_id="dec-1",
        requested_endpoint=ENDPOINT_ACCOUNT_BALANCE,
    )
    assert status == "TRUSTED_PRESENT"


def test_governance_owner_go_required_and_scoped() -> None:
    with pytest.raises(GhvTestnetObservationGovernanceError, match="OWNER_GO_ALIAS_FORBIDDEN"):
        assert_full_system_testnet_observation_owner_go_v1("TESTNET_AUTHORIZED")
    proof = assert_full_system_testnet_observation_owner_go_v1(f"OWNER_GO_{OWNER_GO}")
    assert proof["DEMO_AUTHENTICATED_GET_AUTHORIZED"] == "true"
    assert proof["TESTNET_EXECUTION_AUTHORIZED"] == "false"


def test_state_isolation_rejects_cross_env_paths(tmp_path) -> None:
    bad = tmp_path / "runtime" / "current_productive" / "live"
    bad.mkdir(parents=True)
    with pytest.raises(GhvTestnetStateIsolationError, match="TESTNET_STATE_ROOT_MARKER_REQUIRED"):
        assert_ghv_testnet_observation_state_roots_isolated_v1(
            evidence_root=bad / "evidence",
            lane_state_root=bad / "lane",
            productivity_root=bad / "productivity",
        )


def test_state_isolation_accepts_marker_paths(tmp_path) -> None:
    root = tmp_path / "ghv_full_system_testnet_observation_v1"
    proof = assert_ghv_testnet_observation_state_roots_isolated_v1(
        evidence_root=root / "evidence",
        lane_state_root=root / "lane_state",
        productivity_root=root / "productivity",
    )
    assert proof["TESTNET_STATE_ISOLATION"] == "true"


def test_derived_state_roots_include_o4_path(tmp_path) -> None:
    roots = derive_ghv_testnet_observation_state_roots_v1(tmp_path / "campaign")
    assert roots.o4_state_root.is_dir()


def test_outcome_closure_demo_account_not_o4() -> None:
    proof = prove_outcome_closure_evidence_separation_v1()
    assert proof["DEMO_ACCOUNT_OBSERVATION_EQ_O4_OUTCOME"] == "false"
    assert proof["O4_EVIDENCE_CLASS"] == "REAL_PUBLIC_OBSERVATION"


def test_demo_bind_fail_closed_without_executable_loader() -> None:
    with pytest.raises(GhvTestnetDemoCredentialBindError):
        with open_ghv_testnet_demo_get_only_fresh_pretrade_transport_v1(
            owner_go=f"OWNER_GO_{OWNER_GO}",
            max_request_count=4,
        ):
            pass


def test_demo_bind_accepts_injected_demo_handle() -> None:
    handle = bind_already_held_demo_venue_auth_session_v1(
        api_key=_SYNTH_KEY,
        api_secret=_SYNTH_SECRET,
        passphrase=_SYNTH_PASS,
    )
    try:
        with open_ghv_testnet_demo_get_only_fresh_pretrade_transport_v1(
            owner_go=f"OWNER_GO_{OWNER_GO}",
            max_request_count=4,
            demo_handle=handle,
        ) as (transport, proof):
            assert transport.transport_class == TRANSPORT_CLASS_DEMO_READ_ONLY_GET
            assert proof["READY_TO_EXECUTE_TESTNET_OBSERVATION"] == "false"
    finally:
        release_demo_venue_auth_session_v1(handle)


def test_demo_bind_rejects_k1_handle_injection() -> None:
    k1 = bind_already_held_k1_venue_auth_session_v1(
        api_key=_SYNTH_KEY,
        api_secret=_SYNTH_SECRET,
        passphrase=_SYNTH_PASS,
    )
    try:
        with pytest.raises(GhvTestnetDemoCredentialBindError, match="LIVE_K1_HANDLE"):
            with open_ghv_testnet_demo_get_only_fresh_pretrade_transport_v1(
                owner_go=f"OWNER_GO_{OWNER_GO}",
                max_request_count=4,
                demo_handle=k1,  # type: ignore[arg-type]
            ):
                pass
    finally:
        release_k1_venue_auth_session_v1(k1)
