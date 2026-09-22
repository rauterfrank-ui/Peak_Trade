"""One-shot fresh-envelope join proofs. Fakes only. No eea.okx.com contact."""

from __future__ import annotations

import json
import socket
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_canonical_okx_post_body_serialize_v1 import (
    serialize_canonical_okx_post_body_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    KEYCHAIN_ACCOUNT_ID,
    KEYCHAIN_SERVICE_ID,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
    FullCoreCheckoutIndependentOsNativeStoreAcquisitionError,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_item_class_and_value_encoding_v1 import (
    KEYCHAIN_ITEM_CLASS,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    POST_GO_STATUS,
    POST_OWNER_GO,
    CurrentProductiveOneShotFreshEnvelopeJoinError,
    OneShotJoinProbeV1,
    assert_one_shot_join_permit_constraints_v1,
    attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1,
    prove_one_shot_join_standing_boundary_v1,
)
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    _payload_from_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    ExternalEffectPermitV1,
    issue_external_effect_permit_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    ISSUED_FOR_EXACT_ACTION,
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)

JOIN_PATH = Path(
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py"
)
SEAM_PATH = Path(
    "src/ops/full_core_live_path_composition_root_v1/envelope_bound_external_effect_send_seam_v1.py"
)
HTTP_PATH = Path(
    "src/ops/full_core_live_path_composition_root_v1/full_core_productive_http_post_transport_v1.py"
)
K1_PATH = Path(
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1.py"
)
PORT_PATH = Path(
    "src/ops/capability_11_1_execution_domain_and_order_lifecycle_contracts_v1/execution_ports_v1.py"
)
ENVELOPE_PATH = Path("src/ops/full_core_live_path_composition_root_v1/final_order_envelope_v1.py")
PERMIT_PATH = Path("src/ops/full_core_live_path_composition_root_v1/external_effect_permit_v1.py")
CONSUME_PATH = Path(
    "src/ops/full_core_live_path_composition_root_v1/external_effect_permit_durable_consume_v1.py"
)
FAKE_OPAQUE = json.dumps(
    {"apiKey": "ak-test", "secretKey": "sk-test", "passphrase": "pp-test"},
    separators=(",", ":"),
).encode("utf-8")
NEXT_BLOCKER = "OWNER_GO_REQUIRED_FOR_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT"


class _FakeKeychainBackend:
    def __init__(self, *, payload: bytes | None = FAKE_OPAQUE, absent: bool = False) -> None:
        self.payload = payload
        self.absent = absent
        self.calls = 0

    def copy_matching_generic_password_value_data_v1(
        self,
        *,
        service: str,
        account: str,
        item_class: str,
    ) -> bytes:
        self.calls += 1
        assert service == KEYCHAIN_SERVICE_ID
        assert account == KEYCHAIN_ACCOUNT_ID
        assert item_class == KEYCHAIN_ITEM_CLASS
        if self.absent is True:
            raise FullCoreCheckoutIndependentOsNativeStoreAcquisitionError("KEYCHAIN_ITEM_ABSENT")
        if self.payload is None:
            raise FullCoreCheckoutIndependentOsNativeStoreAcquisitionError(
                "KEYCHAIN_VALUE_UNEXPECTED_REPRESENTATION"
            )
        return bytes(self.payload)


class _TimeoutOpener:
    def __init__(self) -> None:
        self.requests: list[Any] = []

    def open(self, req: Any, timeout: float = 0) -> Any:
        del timeout
        self.requests.append(req)
        raise TimeoutError("bounded-test-timeout")


@pytest.fixture(autouse=True)
def _forbid_real_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("NETWORK_FORBIDDEN")

    monkeypatch.setattr(socket, "create_connection", _boom)
    monkeypatch.setattr(socket.socket, "connect", _boom)


def _envelope():
    plan = VenuePlanCandidateV1(
        instrument_id="okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
        side="buy",
        quantity="1",
        order_type="market",
        td_mode="cross",
        reduce_only=False,
        clordid="pt-fc-one-shot-join-v1",
        venue_native_payload={
            "instId": "okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
            "ordType": "market",
            "side": "buy",
            "sz": "1",
            "tdMode": "cross",
        },
        quantity_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        side_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        instrument_source="DH_CAP24_BOUND_INSTRUMENT_ID",
        path_kind="FULL_CORE_CURRENT_PRODUCTIVE",
    )
    return bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref="TEST_ADMISSION_REF",
        provenance_ref="TEST_PROVENANCE_REF",
        creation_epoch="2026-09-22T00:00:00Z",
    )


def _attempt(tmp_path: Path, **kwargs: Any):
    opener = kwargs.pop("opener", _TimeoutOpener())
    probe = kwargs.pop("probe", OneShotJoinProbeV1())
    backend = kwargs.pop("backend", _FakeKeychainBackend())
    attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
        envelope=kwargs.pop("envelope", _envelope()),
        post_owner_go=kwargs.pop("post_owner_go", POST_OWNER_GO),
        store_root=kwargs.pop("store_root", tmp_path),
        k1_backend=kwargs.pop("k1_backend", backend),
        opener_factory=kwargs.pop("opener_factory", lambda: opener),
        probe=probe,
        **kwargs,
    )
    return probe, opener


def test_standing_pins_and_post_go_remain_unconsumed() -> None:
    proof = prove_one_shot_join_standing_boundary_v1()
    assert proof["POST_GO_STATUS"] == "UNCONSUMED"
    assert proof["POST_GO_CONSUMED"] == "false"
    assert proof["EXTERNAL_EFFECT_COUNT"] == "0"
    assert proof["STEP_29Q_STATUS"] == "PLAN_ONLY"
    assert proof["FIRST_REAL_BLOCKER"] == NEXT_BLOCKER
    assert REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    assert REAL_KEYCHAIN_ACCESS_IMPLEMENTED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert STEP_29Q_PLAN_ONLY == "PLAN_ONLY"
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert current_productive_first_real_blocker_v1() == NEXT_BLOCKER
    assert POST_GO_STATUS == "UNCONSUMED"


def test_without_post_go_mints_nothing_and_does_not_post(tmp_path: Path) -> None:
    probe = OneShotJoinProbeV1()
    opener = _TimeoutOpener()
    with pytest.raises(CurrentProductiveOneShotFreshEnvelopeJoinError, match="POST_GO_REQUIRED"):
        _attempt(tmp_path, post_owner_go="WRONG_AUTHORITY_REF", probe=probe, opener=opener)
    assert probe.permit_minted is False
    assert probe.http_post_attempts == 0
    assert probe.external_effect_count == 0
    assert probe.events == []
    assert opener.requests == []
    assert list(tmp_path.iterdir()) == []


def test_request_shape_retry_second_submit_and_backflow_deny_before_mint(tmp_path: Path) -> None:
    cases = (
        {"retry_allowed": True, "match": "RETRY_ALLOWED_FORBIDDEN"},
        {"second_submit_allowed": True, "match": "SECOND_SUBMIT_FORBIDDEN"},
        {"max_post_count": 2, "match": "MAX_POST_COUNT_NOT_ONE"},
        {"rerank": True, "match": "DECISION_BACKFLOW_FORBIDDEN"},
        {"reselect": True, "match": "DECISION_BACKFLOW_FORBIDDEN"},
        {"sizing_recompute": True, "match": "DECISION_BACKFLOW_FORBIDDEN"},
        {"mv2_double_play_reevaluate": True, "match": "DECISION_BACKFLOW_FORBIDDEN"},
    )
    for case in cases:
        probe = OneShotJoinProbeV1()
        token = case["match"]
        kwargs = {key: value for key, value in case.items() if key != "match"}
        with pytest.raises(CurrentProductiveOneShotFreshEnvelopeJoinError, match=token):
            _attempt(tmp_path, probe=probe, **kwargs)
        assert probe.permit_minted is False
        assert probe.http_post_attempts == 0
    assert list(tmp_path.iterdir()) == []


def test_envelope_id_and_digest_mismatch_deny_before_mint(tmp_path: Path) -> None:
    envelope = _envelope()
    probe = OneShotJoinProbeV1()
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError,
        match="ENVELOPE_ID_DIGEST_BINDING_MISMATCH",
    ):
        _attempt(tmp_path, envelope=replace(envelope, envelope_id="env-not-bound"), probe=probe)
    assert probe.permit_minted is False
    probe_digest = OneShotJoinProbeV1()
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError, match="ENVELOPE_DIGEST_MISMATCH"
    ):
        _attempt(
            tmp_path,
            envelope=replace(envelope, envelope_digest="0" * 64),
            probe=probe_digest,
        )
    assert probe_digest.permit_minted is False
    assert list(tmp_path.iterdir()) == []


def test_forged_permit_constraints_deny() -> None:
    envelope = _envelope()
    forged = ExternalEffectPermitV1(
        permit_id="eep-forged",
        envelope_id=envelope.envelope_id,
        envelope_digest=envelope.envelope_digest,
        authority_ref=POST_OWNER_GO,
        issued_for_exact_action=ISSUED_FOR_EXACT_ACTION,
        max_post_count=2,
    )
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError, match="MAX_POST_COUNT_NOT_ONE"
    ):
        assert_one_shot_join_permit_constraints_v1(forged, envelope)
    retry = replace(forged, max_post_count=1, retry_allowed=True)
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError, match="RETRY_ALLOWED_FORBIDDEN"
    ):
        assert_one_shot_join_permit_constraints_v1(retry, envelope)
    second = replace(forged, max_post_count=1, second_submit_allowed=True)
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError, match="SECOND_SUBMIT_FORBIDDEN"
    ):
        assert_one_shot_join_permit_constraints_v1(second, envelope)
    wrong_authority = issue_external_effect_permit_v1(envelope, authority_ref="OTHER_AUTHORITY_REF")
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError, match="AUTHORITY_REF_MISMATCH"
    ):
        assert_one_shot_join_permit_constraints_v1(wrong_authority, envelope)
    mismatched = replace(wrong_authority, envelope_digest="ab" * 32)
    with pytest.raises(CurrentProductiveOneShotFreshEnvelopeJoinError, match="DIGEST_MISMATCH"):
        assert_one_shot_join_permit_constraints_v1(mismatched, envelope)


def test_durable_consume_precedes_k1_and_http_and_timeout_is_single_unknown(
    tmp_path: Path,
) -> None:
    opener = _TimeoutOpener()
    probe = OneShotJoinProbeV1()
    with pytest.raises(CurrentProductiveOneShotFreshEnvelopeJoinError, match="UNKNOWN_OUTCOME"):
        _attempt(tmp_path, probe=probe, opener=opener)
    assert probe.events == [
        "PERMIT_MINTED",
        "DURABLE_CONSUME_OBSERVED",
        "K1_BOUND",
        "HTTP_POST_ENTER",
    ]
    assert probe.permit_minted is True
    assert probe.http_post_attempts == 1
    assert probe.one_shot_real_post_forwarded is True
    assert probe.external_effect_count == 0
    assert probe.observed_transport_venue_live_contact == 0
    assert len(opener.requests) == 1
    body = opener.requests[0].data.decode("utf-8")
    envelope = _envelope()
    assert body == serialize_canonical_okx_post_body_v1(_payload_from_envelope_v1(envelope))
    parsed = json.loads(body)
    assert parsed["instId"] == envelope.instrument_id
    assert parsed["side"] == envelope.side
    assert parsed["sz"] == envelope.quantity
    assert parsed["ordType"] == envelope.order_type
    assert parsed["tdMode"] == envelope.td_mode
    assert parsed["clOrdId"] == envelope.client_order_id
    assert "OK-ACCESS-TIMESTAMP" not in body
    assert envelope.creation_epoch not in body
    timestamp = opener.requests[0].get_header("Ok-access-timestamp")
    assert timestamp
    assert timestamp != envelope.creation_epoch
    durable = json.loads(
        (tmp_path / "full_core_external_effect_permit_consume_v1.json").read_text()
    )
    assert durable["durable_state"] == "SENT_INITIATED"
    assert durable["retry_allowed"] is False
    assert durable["resubmit_allowed"] is False
    assert durable["second_submit_allowed"] is False
    assert durable["max_post_count"] == 1
    assert "sk-test" not in json.dumps(durable)
    retry_probe = OneShotJoinProbeV1()
    with pytest.raises(CurrentProductiveOneShotFreshEnvelopeJoinError, match="CONSUMED_PERMIT"):
        _attempt(tmp_path, probe=retry_probe, opener=opener)
    assert retry_probe.http_post_attempts == 0
    assert retry_probe.events == ["PERMIT_MINTED"]
    assert len(opener.requests) == 1


def test_consume_failure_leaves_transport_unreached(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.ops.full_core_live_path_composition_root_v1 import (
        envelope_bound_external_effect_send_seam_v1 as seam,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        FullCoreExternalEffectDurableConsumeError,
    )

    def _fail(**_kwargs: Any) -> dict[str, Any]:
        raise FullCoreExternalEffectDurableConsumeError("DURABLE_CONSUME_FORCED_FAIL")

    monkeypatch.setattr(seam, "persist_external_effect_durable_consume_v1", _fail)
    probe = OneShotJoinProbeV1()
    opener = _TimeoutOpener()
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError, match="DURABLE_CONSUME_FORCED_FAIL"
    ):
        _attempt(tmp_path, probe=probe, opener=opener)
    assert "HTTP_POST_ENTER" not in probe.events
    assert "K1_BOUND" not in probe.events
    assert probe.http_post_attempts == 0
    assert opener.requests == []
    assert list(tmp_path.iterdir()) == []


def test_k1_failure_after_consume_makes_post_unreachable(tmp_path: Path) -> None:
    probe = OneShotJoinProbeV1()
    opener = _TimeoutOpener()
    backend = _FakeKeychainBackend(absent=True)
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError, match="K1_SIGNING_HANDLE_UNAVAILABLE"
    ):
        _attempt(tmp_path, probe=probe, opener=opener, backend=backend)
    assert probe.events == ["PERMIT_MINTED", "DURABLE_CONSUME_OBSERVED", "K1_FAILED"]
    assert probe.http_post_attempts == 0
    assert opener.requests == []
    assert probe.external_effect_count == 0
    durable = tmp_path / "full_core_external_effect_permit_consume_v1.json"
    assert durable.is_file()
    recovery = OneShotJoinProbeV1()
    with pytest.raises(CurrentProductiveOneShotFreshEnvelopeJoinError, match="CONSUMED_PERMIT"):
        _attempt(tmp_path, probe=recovery, opener=opener, backend=_FakeKeychainBackend())
    assert recovery.http_post_attempts == 0
    assert opener.requests == []


def test_missing_backend_does_not_open_real_keychain(tmp_path: Path) -> None:
    probe = OneShotJoinProbeV1()
    opener = _TimeoutOpener()
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError, match="K1_SIGNING_HANDLE_UNAVAILABLE"
    ):
        _attempt(tmp_path, probe=probe, opener=opener, k1_backend=None, backend=None)
    assert probe.http_post_attempts == 0
    assert opener.requests == []
    assert REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    assert REAL_KEYCHAIN_ACCESS_IMPLEMENTED is False


def test_callgraph_binds_existing_owners_and_not_a_second_port() -> None:
    join_source = JOIN_PATH.read_text(encoding="utf-8")
    seam_source = SEAM_PATH.read_text(encoding="utf-8")
    http_source = HTTP_PATH.read_text(encoding="utf-8")
    port_source = PORT_PATH.read_text(encoding="utf-8")
    for path in (ENVELOPE_PATH, PERMIT_PATH, CONSUME_PATH, K1_PATH, HTTP_PATH, PORT_PATH):
        assert path.is_file()
    assert "issue_external_effect_permit_v1" in join_source
    assert "attempt_envelope_bound_external_effect_send_v1" in join_source
    assert "open_current_productive_k1_opaque_signing_handle_session_v1" in join_source
    assert "FullCoreProductiveHttpTradeOrderTransportV1" in join_source
    assert "construct_live_execution_port_v1" not in join_source
    assert "one_shot_real_post=True" not in join_source
    assert "eea.okx.com" not in join_source
    assert "urlopen" not in join_source
    consume_at = seam_source.index("persist_external_effect_durable_consume_v1(")
    post_at = seam_source.index("transport.post_trade_order(")
    assert consume_at < post_at
    perform_at = http_source.index("def _perform_http_post_v1(")
    assert "def post_trade_order(" in http_source
    assert perform_at > http_source.index("def post_trade_order(")
    assert "def construct_live_execution_port_v1(" in port_source
    assert "post_trade_order" not in port_source
    assert "_perform_http_post_v1" not in port_source
    for marker in (
        "REAL_KEYCHAIN_ACCESS_AUTHORIZED = True",
        "REAL_KEYCHAIN_ACCESS_IMPLEMENTED = True",
        "POST_ALLOWED = True",
        "REAL_VENUE_POST_ALLOWED = True",
        "EXTERNAL_EFFECT_AUTHORIZED = True",
        'POST_GO_STATUS = "CONSUMED"',
        "STEP_29Q_PLAN_ONLY = ",
    ):
        assert marker not in join_source


def test_bypass_flags_are_false(tmp_path: Path) -> None:
    no_go = OneShotJoinProbeV1()
    with pytest.raises(CurrentProductiveOneShotFreshEnvelopeJoinError, match="POST_GO_REQUIRED"):
        _attempt(tmp_path / "nogo", post_owner_go="", probe=no_go)
    assert no_go.http_post_attempts == 0
    k1 = OneShotJoinProbeV1()
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError, match="K1_SIGNING_HANDLE_UNAVAILABLE"
    ):
        _attempt(tmp_path / "k1", probe=k1, k1_backend=None, backend=None)
    assert k1.http_post_attempts == 0
    opener = _TimeoutOpener()
    first = OneShotJoinProbeV1()
    with pytest.raises(CurrentProductiveOneShotFreshEnvelopeJoinError, match="UNKNOWN_OUTCOME"):
        _attempt(tmp_path / "once", probe=first, opener=opener)
    second = OneShotJoinProbeV1()
    with pytest.raises(CurrentProductiveOneShotFreshEnvelopeJoinError, match="CONSUMED_PERMIT"):
        _attempt(tmp_path / "once", probe=second, opener=opener)
    assert first.external_effect_count == 0
    assert second.http_post_attempts == 0
    assert len(opener.requests) == 1
    can_reach_without_permit = no_go.http_post_attempts != 0
    can_reach_without_credential = k1.http_post_attempts != 0
    can_bypass_durable = (
        "HTTP_POST_ENTER" in k1.events[: k1.events.index("DURABLE_CONSUME_OBSERVED")]
    )
    can_retry_second = second.http_post_attempts != 0
    can_crash_recovery_second = len(opener.requests) != 1
    assert can_reach_without_permit is False
    assert can_reach_without_credential is False
    assert can_bypass_durable is False
    assert can_retry_second is False
    assert can_crash_recovery_second is False
