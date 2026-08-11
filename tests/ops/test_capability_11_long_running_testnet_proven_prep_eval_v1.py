"""Tests for LONG_RUNNING_TESTNET_PROVEN prep/eval, query-sign, and baseline preflight."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.ops.capability_11_long_running_testnet_proven_prep_eval_v1.constants_v1 import (
    CANONICAL_EXECUTE_OWNER_GO_SCOPE,
    LONG_RUNNING_TESTNET_PROVEN,
    SECTION_11_12_8_CLOSED,
    SECTION_11_12_8_REOPENED,
)
from src.ops.capability_11_long_running_testnet_proven_prep_eval_v1.evaluator_v1 import (
    evaluate_long_running_testnet_proven_evidence_v1,
)
from src.ops.capability_11_long_running_testnet_proven_prep_eval_v1.verifier_v1 import (
    verify_capability_11_long_running_testnet_proven_prep_eval_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    ACCEPTED_OWNER_GO_SCOPES,
    SCOPED_OWNER_GO_SCOPE,
    SCOPED_OWNER_GO_SCOPE_LEGACY_ALIAS,
    SCOPED_OWNER_GO_SCOPE_LEGACY_XPERP,
    SCOPED_OWNER_GO_TOKEN,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.hidden_confirm_v1 import (
    ActualStartConfirmError,
    latch_and_consume_confirm_digest_v1,
    reset_confirm_consumption_registry_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.owner_go_consumer_v1 import (
    ActualStartOwnerGoError,
    consume_actual_start_owner_go_v1,
    reset_owner_go_consumption_registry_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.bound_testnet_http_client_v1 import (
    BoundOkxTestnetHttpClientV1,
    BoundTestnetHttpClientError,
    sign_okx_request_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.governance_acceptance_v1 import (
    prove_governance_acceptance_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.immutable_baseline_preflight_v1 import (
    ImmutableBaselinePreflightError,
    evaluate_immutable_baseline_preflight_v1,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PREP_EVIDENCE = (
    REPO_ROOT / "docs" / "evidence" / "capability_11_long_running_testnet_proven_prep_eval_v1"
)


@pytest.fixture(autouse=True)
def _reset_registries() -> None:
    reset_owner_go_consumption_registry_v1()
    reset_confirm_consumption_registry_v1()


def test_canonical_execute_token_is_primary() -> None:
    assert SCOPED_OWNER_GO_SCOPE == CANONICAL_EXECUTE_OWNER_GO_SCOPE
    assert SCOPED_OWNER_GO_SCOPE == ("EXECUTE_BOUNDED_LONG_RUNNING_PRODUCTIVE_TESTNET_CAMPAIGN_NOW")
    assert SCOPED_OWNER_GO_SCOPE_LEGACY_XPERP in ACCEPTED_OWNER_GO_SCOPES
    assert SCOPED_OWNER_GO_SCOPE_LEGACY_ALIAS in ACCEPTED_OWNER_GO_SCOPES
    assert LONG_RUNNING_TESTNET_PROVEN is False
    assert SECTION_11_12_8_CLOSED is True
    assert SECTION_11_12_8_REOPENED is False


def test_owner_go_consume_and_refuse_replay() -> None:
    first = consume_actual_start_owner_go_v1(
        owner_go_token=SCOPED_OWNER_GO_TOKEN,
        owner_go_scope=SCOPED_OWNER_GO_SCOPE,
        owner_go_authorization=SCOPED_OWNER_GO_SCOPE,
        consumption_id="lr-prep-1",
    )
    assert first.consumed is True
    assert first.live_authorized is False
    with pytest.raises(ActualStartOwnerGoError, match="OWNER_GO_REPLAY_FORBIDDEN"):
        consume_actual_start_owner_go_v1(
            owner_go_token=SCOPED_OWNER_GO_TOKEN,
            owner_go_scope=SCOPED_OWNER_GO_SCOPE,
            owner_go_authorization=SCOPED_OWNER_GO_SCOPE,
            consumption_id="lr-prep-1",
        )
    # Legacy XPerp alias still consumable (same surface; not section reopen).
    legacy = consume_actual_start_owner_go_v1(
        owner_go_token=SCOPED_OWNER_GO_TOKEN,
        owner_go_scope=SCOPED_OWNER_GO_SCOPE_LEGACY_XPERP,
        owner_go_authorization=SCOPED_OWNER_GO_SCOPE_LEGACY_XPERP,
        consumption_id="lr-prep-legacy-xperp",
    )
    assert legacy.consumed is True


def test_hidden_confirm_replay_refused() -> None:
    digest = hashlib.sha256(b"confirm-lr-prep").hexdigest()
    latch_and_consume_confirm_digest_v1(confirm_token_digest=digest)
    with pytest.raises(ActualStartConfirmError, match="REPLAY|ALREADY"):
        latch_and_consume_confirm_digest_v1(confirm_token_digest=digest)


def test_query_sign_includes_query_string() -> None:
    from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.secretref_credential_v1 import (
        resolve_and_load_secretref_ephemeral_v1,
    )

    secret = "test-secret"
    ts = "2026-08-11T00:00:00.000Z"
    path_only = sign_okx_request_v1(
        secret=secret,
        timestamp=ts,
        method="GET",
        request_path="/api/v5/trade/orders-pending",
        body="",
    )
    with_query = sign_okx_request_v1(
        secret=secret,
        timestamp=ts,
        method="GET",
        request_path="/api/v5/trade/orders-pending?instId=BTC-USD_UM_XPERP-310328",
        body="",
    )
    assert path_only != with_query

    material = json.dumps(
        {"api_key": "k", "api_secret": secret, "passphrase": "p"},
        separators=(",", ":"),
    )
    handle = resolve_and_load_secretref_ephemeral_v1(stub_material=material)
    client = BoundOkxTestnetHttpClientV1(credential_handle=handle, wire_send_enabled=False)
    result = client.request(
        method="GET",
        url=("https://eea.okx.com/api/v5/trade/orders-pending?instId=BTC-USD_UM_XPERP-310328"),
    )
    assert result["wire_sent"] is False
    prepared = client.prepared_requests[-1]
    assert prepared["sign_request_path_includes_query"] is True
    assert prepared["permanent_query_sign_fix"] is True
    assert prepared["sign_request_path"].endswith("?instId=BTC-USD_UM_XPERP-310328")


def test_live_host_hard_block() -> None:
    from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.secretref_credential_v1 import (
        resolve_and_load_secretref_ephemeral_v1,
    )

    material = json.dumps(
        {"api_key": "k", "api_secret": "s", "passphrase": "p"},
        separators=(",", ":"),
    )
    handle = resolve_and_load_secretref_ephemeral_v1(stub_material=material)
    client = BoundOkxTestnetHttpClientV1(credential_handle=handle, wire_send_enabled=False)
    with pytest.raises(BoundTestnetHttpClientError, match="LIVE_HOST_HARD_BLOCK"):
        client.request(method="GET", url="https://www.okx.com/api/v5/account/balance")


def test_immutable_baseline_preflight_ignores_untracked(tmp_path: Path) -> None:
    # Against real repo: untracked evidence must not fail tracked-clean check.
    result = evaluate_immutable_baseline_preflight_v1(repo_root=REPO_ROOT)
    assert result.untracked_ignored_for_preflight is True
    # On a dirty tracked feature branch this may be false; do not require ok here.
    # Explicit expected-SHA mismatch must fail closed.
    with pytest.raises(ImmutableBaselinePreflightError):
        from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.immutable_baseline_preflight_v1 import (
            assert_immutable_baseline_preflight_v1,
        )

        assert_immutable_baseline_preflight_v1(
            repo_root=REPO_ROOT,
            expected_origin_main_sha="0" * 40,
        )


def test_governance_acceptance_includes_prep_markers() -> None:
    proof = prove_governance_acceptance_v1()
    assert proof["ok"] is True
    assert proof["GOVERNANCE_ACCEPTANCE"] == "PASS"


def test_prep_verifier_keeps_proven_false() -> None:
    result = verify_capability_11_long_running_testnet_proven_prep_eval_v1(
        evidence_dir=PREP_EVIDENCE
    )
    assert result["ok"] is True
    assert result["LONG_RUNNING_TESTNET_PROVEN"] is False
    assert result["MANIFEST_VERIFY_RC"] == 0


def test_evaluator_refuses_historical_and_transport_403(tmp_path: Path) -> None:
    # Minimal sealed-looking dir for non-historical path.
    root = tmp_path / "campaign"
    root.mkdir()
    payload = {
        "BOUND_REACHED_REASON": "DURATION_BOUND",
        "completed": True,
        "ORDER_ACK_COUNT": 0,
        "FINAL_OPEN_ORDER_COUNT": 0,
        "FINAL_OPEN_POSITION_COUNT": 0,
        "LIVE_ORDER_EFFECT": "NONE",
        "LIVE_AUTHORIZED": False,
        "FINAL_EXCHANGE_RECONCILIATION": "PASS",
        "HTTP_STATUS": 403,
        "HTTP_403_CLASSIFICATION": (
            "TRANSPORT_OR_GATEWAY_HTTP_403_NON_JSON_BODY_NOT_EXCHANGE_SEMANTIC_REJECT"
        ),
    }
    (root / "MACHINE_READABLE_PROOF.json").write_text(json.dumps(payload), encoding="utf-8")
    digest = hashlib.sha256((root / "MACHINE_READABLE_PROOF.json").read_bytes()).hexdigest()
    (root / "MANIFEST.sha256").write_text(
        f"{digest}  MACHINE_READABLE_PROOF.json\n", encoding="utf-8"
    )
    evaluated = evaluate_long_running_testnet_proven_evidence_v1(evidence_root=root)
    assert evaluated["LONG_RUNNING_TESTNET_PROVEN"] is False
    assert "ORDER_ACK_COUNT_LT_1" in evaluated["REFUSE_REASONS"]
    assert "TRANSPORT_ONLY_HTTP_403_REFUSED" in evaluated["REFUSE_REASONS"]

    hist = evaluate_long_running_testnet_proven_evidence_v1(
        evidence_root=REPO_ROOT
        / "evidence/ops/section_11_12_8_bounded_long_running_productive_testnet_campaign_now/20260808T181528Z",
        campaign_payload={
            "BOUND_REACHED_REASON": "DURATION_BOUND",
            "completed": True,
            "ORDER_ACK_COUNT": 1,
            "FINAL_OPEN_ORDER_COUNT": 0,
            "FINAL_OPEN_POSITION_COUNT": 0,
            "LIVE_ORDER_EFFECT": "NONE",
            "FINAL_EXCHANGE_RECONCILIATION": "PASS",
        },
    )
    assert hist["LONG_RUNNING_TESTNET_PROVEN"] is False
    assert hist["HISTORICAL_PROMOTION_REFUSED"] is True


def test_evaluator_pass_minima_when_complete(tmp_path: Path) -> None:
    root = tmp_path / "good_campaign"
    root.mkdir()
    payload = {
        "BOUND_REACHED_REASON": "DURATION_BOUND",
        "completed": True,
        "ORDER_ACK_COUNT": 1,
        "CANCEL_COUNT": 1,
        "FINAL_OPEN_ORDER_COUNT": 0,
        "FINAL_OPEN_POSITION_COUNT": 0,
        "LIVE_ORDER_EFFECT": "NONE",
        "LIVE_AUTHORIZED": False,
        "unknown_submit_hard_stop": False,
        "FINAL_EXCHANGE_RECONCILIATION": "PASS",
        "HTTP_STATUS": 200,
    }
    (root / "MACHINE_READABLE_PROOF.json").write_text(json.dumps(payload), encoding="utf-8")
    digest = hashlib.sha256((root / "MACHINE_READABLE_PROOF.json").read_bytes()).hexdigest()
    (root / "MANIFEST.sha256").write_text(
        f"{digest}  MACHINE_READABLE_PROOF.json\n", encoding="utf-8"
    )
    evaluated = evaluate_long_running_testnet_proven_evidence_v1(evidence_root=root)
    assert evaluated["LONG_RUNNING_TESTNET_PROVEN"] is True
    assert evaluated["REFUSE_REASONS"] == []
