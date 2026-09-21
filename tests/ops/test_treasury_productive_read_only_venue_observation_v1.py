"""Productive Treasury read-only venue observation WP tests."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any
from unittest.mock import patch

import pytest

from src.ops.offline_funding_balance_read_producer_v1.fixtures_v1 import fixture_usdc_nonzero_v1
from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
    parse_funding_account_balance_observation_v1,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.constants_v1 import (
    OWNER_GO as SESSION_OWNER_GO,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryDepositHistorySignalV1,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.context_v1 import (
    TreasuryCapitalDepositObservationContextV1,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.producer_v1 import (
    build_treasury_venue_observation_from_funding_balance_v1,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.capture_v1 import (
    execute_treasury_productive_read_only_venue_observation_v1,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.chain_v1 import (
    execute_treasury_productive_reconciliation_chain_v1,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.constants_v1 import (
    ALLOWED_WP_OWNER_GOS,
    OWNER_GO,
    WP_ID,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.errors_v1 import (
    TreasuryProductiveReadOnlyVenueObservationError,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.pre_network_gate_v1 import (
    build_treasury_productive_pre_network_gate_proof_v1,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.separation_matrix_v1 import (
    build_treasury_separation_matrix_v1,
)
from tests.ops.test_pl_tf_002_runtime_integrity_v1 import _FakeIntegrityBackend

_TEST_SHA = "402dbee646c85400c525acd14bc38f4c16e0a17f"
_INTEGRITY = _FakeIntegrityBackend(origin_main=_TEST_SHA, head=_TEST_SHA)


def test_standing_owner_go_tokens() -> None:
    assert "OWNER_GO=true" in ALLOWED_WP_OWNER_GOS
    assert WP_ID.endswith("_V1")


def test_pre_network_gate_only_no_network() -> None:
    out = execute_treasury_productive_read_only_venue_observation_v1(
        wp_owner_go="OWNER_GO=true",
        session_owner_go=SESSION_OWNER_GO,
        origin_main_sha=_TEST_SHA,
        execute_network=False,
        integrity_backend=_INTEGRITY,
    )
    assert out["disposition"] == "PRE_NETWORK_GATE_ONLY"
    assert out["NETWORK_READ_ONLY_USED"] is False
    assert out["S12_STATUS"] == "PASS"


def test_pre_network_gate_rejects_bad_session_owner_go() -> None:
    with pytest.raises(TreasuryProductiveReadOnlyVenueObservationError, match="SESSION_OWNER_GO"):
        build_treasury_productive_pre_network_gate_proof_v1(
            wp_owner_go=OWNER_GO,
            session_owner_go="WRONG",
            origin_main_sha=_TEST_SHA,
            integrity_backend=_INTEGRITY,
        )


def test_wp_owner_go_fail_closed() -> None:
    with pytest.raises(TreasuryProductiveReadOnlyVenueObservationError, match="WP_OWNER_GO"):
        execute_treasury_productive_read_only_venue_observation_v1(
            wp_owner_go="NOT_ALLOWED",
            session_owner_go=SESSION_OWNER_GO,
            origin_main_sha=_TEST_SHA,
            execute_network=False,
        )


def _treasury_observation_from_fixture() -> Any:
    funding = parse_funding_account_balance_observation_v1(
        body_bytes=fixture_usdc_nonzero_v1(),
        http_status=200,
        observed_at_utc="2026-09-21T01:00:00Z",
        venue="okx",
        rest_host="eea.okx.com",
        endpoint="/api/v5/asset/balances",
        headers={},
        transport_class="RecordingFakeCanaryTransportV1",
        get_performed=True,
    )
    ctx = TreasuryCapitalDepositObservationContextV1(
        evidence_id="tevidence-prod-ro-001",
        account_identity="okx-eea-uid:test-uid",
        instrument_id="ETH-USDT-SWAP",
        deposit_history_freshness=TreasuryDepositHistorySignalV1.UNCONFIRMED.value,
        deposit_history_confirms_increase=False,
    )
    return build_treasury_venue_observation_from_funding_balance_v1(funding, ctx)


def test_reconciliation_chain_fail_closed_without_deposit_confirm() -> None:
    observation = _treasury_observation_from_fixture()
    chain = execute_treasury_productive_reconciliation_chain_v1(observation)
    assert chain["RISK_ADMISSION_BINDING_STATUS"] == "NO_RISK_ADMISSIBLE_MINT"
    assert chain["ACCOUNT_STATE_JOIN_STATUS"]["orchestration_admitted"] is False
    assert chain["PRODUCTIVE_HOST_JOIN_STATUS"] == "PRODUCTIVE_HOST_JOIN_WIRED"
    assert chain["PRODUCTIVE_HOST_EVALUATION"]["fail_closed"] is True
    assert "C08_TREASURY" in chain["EARLIEST_NEW_REAL_BLOCKER"]


def test_separation_matrix_all_pass_offline() -> None:
    sep = build_treasury_separation_matrix_v1(
        network_read_only_used=False,
        secret_material_persisted=False,
        secret_material_logged=False,
    )
    for key in [f"S{i:02d}_STATUS" for i in range(1, 13)]:
        assert sep[key] == "PASS"


def test_package_has_no_direct_urllib() -> None:
    from pathlib import Path

    root = (
        Path(__file__).resolve().parents[2]
        / "src/ops/treasury_productive_read_only_venue_observation_v1"
    )
    joined = "\n".join(p.read_text(encoding="utf-8") for p in root.glob("*.py"))
    assert "urllib.request" not in joined


def test_productive_capture_with_mock_session() -> None:
    from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
        FreshPretradeGetTransportResultV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
        FullCoreProductiveReadOnlyGetTransportV1,
    )

    class _FakeTransport(FullCoreProductiveReadOnlyGetTransportV1):
        def __init__(self) -> None:
            super().__init__(handle=object(), max_request_count=4)
            self._handle = object()

        def get(self, *, endpoint: str, auth_required: bool, pretrade_decision_id: str):
            del auth_required, pretrade_decision_id
            path = str(endpoint).split("?", 1)[0]
            if path == "/api/v5/account/config":
                payload = {"code": "0", "data": [{"uid": "uid-test-42"}]}
            elif path == "/api/v5/asset/balances":
                import json

                payload = json.loads(fixture_usdc_nonzero_v1().decode("utf-8"))
            else:
                raise TreasuryProductiveReadOnlyVenueObservationError("UNEXPECTED_ENDPOINT")
            self.request_count += 1
            self.methods_used.append("GET")
            self.venue_live_contact = True
            return FreshPretradeGetTransportResultV1(
                get_performed=True,
                method="GET",
                endpoint=endpoint,
                http_status=200,
                payload=payload,
                auth_header_sent=True,
                transport_class="FULL_CORE_PRODUCTIVE_READ_ONLY_GET_V1",
                venue_live_contact=True,
                historical_reuse=False,
                error_class="",
                body_sha256="abc",
            )

    class _FakeSession:
        credential_acquired = True
        k1_handle_id = "h1"
        transport = _FakeTransport()

    with patch(
        "src.ops.treasury_productive_read_only_venue_observation_v1.capture_v1.open_pl_tf_002_productive_read_only_get_session_v1"
    ) as mock_open:
        mock_open.return_value.__enter__.return_value = _FakeSession()
        mock_open.return_value.__exit__.return_value = None
        out = execute_treasury_productive_read_only_venue_observation_v1(
            wp_owner_go="OWNER_GO=true",
            session_owner_go=SESSION_OWNER_GO,
            origin_main_sha=_TEST_SHA,
            execute_network=True,
            integrity_backend=_INTEGRITY,
        )
    assert out["disposition"] == "PRODUCTIVE_OBSERVATION_COMPLETE"
    assert out["NETWORK_READ_ONLY_USED"] is True
    assert out["NETWORK_REQUESTS_PERFORMED"] == 2
    assert out["treasury_venue_observation"]["account_identity"] == "okx-eea-uid:uid-test-42"
    assert out["treasury_venue_observation"]["venue_balance_raw"] == "12.5"
    assert out["reconciliation_chain"]["CAPITAL_ADMISSION_RISK_ADMISSIBLE"] is False
