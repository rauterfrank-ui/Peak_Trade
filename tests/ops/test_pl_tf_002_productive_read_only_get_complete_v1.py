"""Tests for PL-TF-002 productive read-only GET completion WP."""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.ops.pl_tf_002_network_evidence_contract_v1.constants_v1 import (
    F1_REQUIRED_GET_ITEM_IDS,
    NE_TF_001_ENDPOINT_PATH,
)
from src.ops.pl_tf_002_network_evidence_contract_v1.verifier_v1 import (
    verify_pl_tf_002_network_evidence_v1,
)
from src.ops.pl_tf_002_productive_read_only_get_complete_v1.capture_v1 import (
    build_network_evidence_bundle_v1,
    execute_pl_tf_002_productive_read_only_get_capture_v1,
)
from src.ops.pl_tf_002_productive_read_only_get_complete_v1.constants_v1 import (
    F1_OWNER_SCOPED_CUMULATIVE_GET_BUDGET,
    MAX_NETWORK_REQUEST_COUNT,
    OWNER_GO,
    SESSION_OWNER_GO,
    AUTHORIZED_NETWORK_HOST,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.owner_scoped_get_budget_enforcement_v1.enforcer_v1 import (
    OwnerScopedGetBudgetEnforcerV1,
)
from src.ops.owner_scoped_get_budget_enforcement_v1.errors_v1 import OwnerScopedGetBudgetError
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.session_executor_v1 import (
    PlTf002ProductiveReadOnlyGetSessionV1,
    PlTf002ReadOnlyGetSessionPreflightV1,
)
from tests.ops.test_owner_scoped_get_budget_enforcement_v1 import (
    _FakeFreshPretradeTransport,
    _FakeHttpResponse,
)
from src.ops.pl_tf_002_productive_read_only_get_complete_v1.errors_v1 import (
    PlTf002ProductiveReadOnlyGetCompleteError,
)
from src.ops.pl_tf_002_productive_read_only_get_complete_v1.persist_v1 import (
    complete_pl_tf_002_network_evidence_pack_manifest_v1,
    persist_pl_tf_002_network_evidence_pack_v1,
)
from src.ops.pl_tf_002_productive_read_only_get_complete_v1.pre_network_jit_v1 import (
    build_pl_tf_002_pre_network_jit_proof_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    MANIFEST_FILENAME,
)
from tests.ops.test_pl_tf_002_runtime_integrity_v1 import _FakeIntegrityBackend

_TEST_ORIGIN_MAIN = "9bd633bb175dab27dc383b91a512e379bd31cefa"
_TEST_INTEGRITY = _FakeIntegrityBackend(
    origin_main=_TEST_ORIGIN_MAIN,
    head=_TEST_ORIGIN_MAIN,
)


def test_pre_network_jit_rejects_wrong_session_owner_go() -> None:
    from src.ops.pl_tf_002_productive_read_only_session_executor_v1.errors_v1 import (
        PlTf002ProductiveReadOnlySessionError,
    )

    with pytest.raises(PlTf002ProductiveReadOnlySessionError, match="OWNER_GO_MISMATCH"):
        build_pl_tf_002_pre_network_jit_proof_v1(
            session_owner_go="WRONG",
            origin_main_sha=_TEST_ORIGIN_MAIN,
            integrity_backend=_TEST_INTEGRITY,
        )


def test_capture_pre_network_only_no_network() -> None:
    out = execute_pl_tf_002_productive_read_only_get_capture_v1(
        wp_owner_go=OWNER_GO,
        session_owner_go=SESSION_OWNER_GO,
        origin_main_sha=_TEST_ORIGIN_MAIN,
        execute_network=False,
        integrity_backend=_TEST_INTEGRITY,
    )
    assert out["disposition"] == "PRE_NETWORK_JIT_ONLY"
    assert out["NETWORK_REQUEST_COUNT"] == 0
    assert out["jit_proof"]["SESSION_OWNER_GO_ACCEPTED"] is True


def test_wp_owner_go_mismatch_fail_closed() -> None:
    with pytest.raises(PlTf002ProductiveReadOnlyGetCompleteError, match="WP_OWNER_GO"):
        execute_pl_tf_002_productive_read_only_get_capture_v1(
            wp_owner_go="WRONG",
            session_owner_go=SESSION_OWNER_GO,
            origin_main_sha=_TEST_ORIGIN_MAIN,
            execute_network=False,
        )


def _f1_items() -> dict[str, Any]:
    return {
        item_id: {
            "get_performed": True,
            "method": "GET",
            "venue_live_contact": True,
            "transport_class": "FULL_CORE_PRODUCTIVE_READ_ONLY_GET_V1",
        }
        for item_id in F1_REQUIRED_GET_ITEM_IDS
    }


def test_persist_network_evidence_pack_writes_verifiable_manifest(tmp_path: Any) -> None:
    now_ms = int(time.time() * 1000)
    raw = {"code": "0", "msg": "", "data": [{"uid": "uid-1", "perm": "read_only"}]}
    bundle = build_network_evidence_bundle_v1(
        f1_items=_f1_items(),
        f2_raw=raw,
        expected_credential_uid="uid-1",
        observed_at_unix_ms=now_ms,
    )
    verification = verify_pl_tf_002_network_evidence_v1(bundle, now_unix_ms=now_ms)
    out = persist_pl_tf_002_network_evidence_pack_v1(
        evidence_root=tmp_path,
        origin_main_sha=_TEST_ORIGIN_MAIN,
        capture_summary={"NETWORK_REQUEST_COUNT": 7},
        verification=verification,
        evidence_bundle=bundle,
    )
    pack = Path(out["EVIDENCE_PACK"])
    assert (pack / MANIFEST_FILENAME).is_file()
    assert int(out["MANIFEST_VERIFY_RC"]["MANIFEST_VERIFY_RC"]) == 0
    complete = complete_pl_tf_002_network_evidence_pack_manifest_v1(pack_dir=pack)
    assert int(complete["MANIFEST_VERIFY_RC"]["MANIFEST_VERIFY_RC"]) == 0


def test_bundle_builder_verifier_pass() -> None:
    now_ms = int(time.time() * 1000)
    raw = {"code": "0", "msg": "", "data": [{"uid": "uid-1", "perm": "read_only"}]}
    bundle = build_network_evidence_bundle_v1(
        f1_items=_f1_items(),
        f2_raw=raw,
        expected_credential_uid="uid-1",
        observed_at_unix_ms=now_ms,
    )
    result = verify_pl_tf_002_network_evidence_v1(bundle, now_unix_ms=now_ms)
    assert result["VERIFICATION_RESULT"] == "PASS"
    assert result["PL_TF_002_CLOSURE_RESULT"]["closed"] is True
    assert bundle["F2_NE_TF_001"]["endpoint_path"] == NE_TF_001_ENDPOINT_PATH


def test_execute_network_requires_grant_store_and_budget() -> None:
    with pytest.raises(
        PlTf002ProductiveReadOnlyGetCompleteError, match="OWNER_SCOPED_GET_BUDGET_STORE_REQUIRED"
    ):
        execute_pl_tf_002_productive_read_only_get_capture_v1(
            wp_owner_go=OWNER_GO,
            session_owner_go=SESSION_OWNER_GO,
            origin_main_sha=_TEST_ORIGIN_MAIN,
            execute_network=True,
            integrity_backend=_TEST_INTEGRITY,
        )
    with pytest.raises(
        PlTf002ProductiveReadOnlyGetCompleteError,
        match="OWNER_SCOPED_CUMULATIVE_REQUEST_BUDGET_REQUIRED",
    ):
        execute_pl_tf_002_productive_read_only_get_capture_v1(
            wp_owner_go=OWNER_GO,
            session_owner_go=SESSION_OWNER_GO,
            origin_main_sha=_TEST_ORIGIN_MAIN,
            execute_network=True,
            integrity_backend=_TEST_INTEGRITY,
            owner_scoped_get_budget_store_root="/tmp/unused",
        )


def test_owner_budget_cannot_exceed_technical_limit(tmp_path: Path) -> None:
    with pytest.raises(
        PlTf002ProductiveReadOnlyGetCompleteError,
        match="EXCEEDS_TECHNICAL_LIMIT",
    ):
        execute_pl_tf_002_productive_read_only_get_capture_v1(
            wp_owner_go=OWNER_GO,
            session_owner_go=SESSION_OWNER_GO,
            origin_main_sha=_TEST_ORIGIN_MAIN,
            execute_network=True,
            integrity_backend=_TEST_INTEGRITY,
            owner_scoped_get_budget_store_root=tmp_path,
            owner_scoped_cumulative_request_budget=MAX_NETWORK_REQUEST_COUNT + 1,
        )


@contextmanager
def _fake_pl_tf_002_session(*, grant_context, origin_main_sha: str):
    enforcer = OwnerScopedGetBudgetEnforcerV1(grant_context=grant_context)
    transport = FullCoreProductiveReadOnlyGetTransportV1(
        handle=MagicMock(),
        owner_scoped_get_budget_enforcer=enforcer,
    )
    pre = PlTf002ReadOnlyGetSessionPreflightV1(
        disposition="PREFLIGHT_PASS",
        wp_id="WP",
        owner_go_accepted="true",
        origin_main_sha_bound=origin_main_sha,
        authorized_host=AUTHORIZED_NETWORK_HOST,
        http_method_allowlist=("GET",),
        f1_endpoint_paths=("/api/v5/public/instruments",),
        f2_endpoint_path="/api/v5/account/config",
        transport_class="FULL_CORE_PRODUCTIVE_READ_ONLY_GET_V1",
        k1_may_perform_get_standing="false",
        k1_real_keychain_access_standing="false",
        ephemeral_keychain_consumer="X",
        external_effect_authorized="false",
        post_allowed_standing="false",
        credential_class="K1",
        source_ref_uri="uri",
        join_seam_id="join",
    )
    yield PlTf002ProductiveReadOnlyGetSessionV1(
        preflight=pre,
        transport=transport,
        k1_handle_id="h",
        credential_acquired=True,
        network_executed_by_executor=False,
    )


def test_capture_with_budget_nine_mints_and_blocks_tenth(tmp_path: Path) -> None:
    from src.ops.owner_scoped_get_budget_enforcement_v1.enforcer_v1 import (
        OwnerScopedGetBudgetGrantContextV1,
    )
    from src.ops.owner_scoped_get_budget_enforcement_v1.grant_identity_v1 import (
        OwnerScopedGetBudgetGrantBindingV1,
    )
    from src.ops.pl_tf_002_productive_read_only_get_complete_v1.constants_v1 import WP_ID

    binding = OwnerScopedGetBudgetGrantBindingV1(
        owner_go=f"{OWNER_GO}|{SESSION_OWNER_GO}",
        work_package_id=WP_ID,
        origin_main_sha=_TEST_ORIGIN_MAIN,
        cumulative_request_budget=F1_OWNER_SCOPED_CUMULATIVE_GET_BUDGET,
        authorized_host=AUTHORIZED_NETWORK_HOST,
    )

    def payload_for(url: str) -> bytes:
        return json.dumps(
            {
                "code": "0",
                "data": [
                    {
                        "uid": "uid-1",
                        "perm": "read_only",
                        "instId": "ETH-USDT-SWAP",
                        "tdMode": "cross",
                        "mgnMode": "cross",
                    }
                ],
            }
        ).encode()

    def fake_open_factory(grant_holder: list):
        @contextmanager
        def fake_open(
            *,
            owner_go,
            origin_main_sha,
            acquire_credential,
            backend=None,
            integrity_backend=None,
            owner_scoped_get_budget_grant=None,
        ):
            assert owner_scoped_get_budget_grant is not None
            grant_holder.append(owner_scoped_get_budget_grant)
            with _fake_pl_tf_002_session(
                grant_context=owner_scoped_get_budget_grant,
                origin_main_sha=origin_main_sha,
            ) as session:
                yield session

        return fake_open

    grants: list = []

    def _open(req, timeout=0):
        return _FakeHttpResponse(status=200, body=payload_for(req.full_url), url=req.full_url)

    with (
        patch(
            "src.ops.pl_tf_002_productive_read_only_get_complete_v1.capture_v1.open_pl_tf_002_productive_read_only_get_session_v1",
            fake_open_factory(grants),
        ),
        patch(
            "src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1.build_k1_okx_venue_auth_headers_v1",
            return_value={"OK-ACCESS-KEY": "x"},
        ),
        patch(
            "src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1.build_opener"
        ) as bo,
    ):
        bo.return_value.open.side_effect = _open
        out = execute_pl_tf_002_productive_read_only_get_capture_v1(
            wp_owner_go=OWNER_GO,
            session_owner_go=SESSION_OWNER_GO,
            origin_main_sha=_TEST_ORIGIN_MAIN,
            execute_network=True,
            integrity_backend=_TEST_INTEGRITY,
            owner_scoped_get_budget_store_root=tmp_path,
            owner_scoped_cumulative_request_budget=F1_OWNER_SCOPED_CUMULATIVE_GET_BUDGET,
        )
    assert out["disposition"] == "NETWORK_CAPTURE_COMPLETE"
    assert out["NETWORK_REQUEST_COUNT"] == F1_OWNER_SCOPED_CUMULATIVE_GET_BUDGET
    assert out["OWNER_SCOPED_CUMULATIVE_REQUEST_BUDGET"] == F1_OWNER_SCOPED_CUMULATIVE_GET_BUDGET
    assert grants
    enforcer = OwnerScopedGetBudgetEnforcerV1(grant_context=grants[0])
    with pytest.raises(OwnerScopedGetBudgetError):
        enforcer.begin_get_v1(endpoint_path="/api/v5/account/config")


def test_f1_default_budget_constant_is_nine() -> None:
    assert F1_OWNER_SCOPED_CUMULATIVE_GET_BUDGET == 9
    assert MAX_NETWORK_REQUEST_COUNT == 16


def test_persist_failure_does_not_imply_capture_retry(tmp_path: Path) -> None:
    """Capture API has no persist hook; failed persist is operator-driven only."""
    now_ms = int(time.time() * 1000)
    bundle = build_network_evidence_bundle_v1(
        f1_items=_f1_items(),
        f2_raw={"code": "0", "data": [{"uid": "uid-1", "perm": "read_only"}]},
        expected_credential_uid="uid-1",
        observed_at_unix_ms=now_ms,
    )
    verification = verify_pl_tf_002_network_evidence_v1(bundle, now_unix_ms=now_ms)
    with patch(
        "src.ops.pl_tf_002_productive_read_only_get_complete_v1.persist_v1.verify_manifest_v1",
        return_value={"MANIFEST_VERIFY_RC": 1},
    ):
        with pytest.raises(
            PlTf002ProductiveReadOnlyGetCompleteError, match="MANIFEST_VERIFY_FAILED"
        ):
            persist_pl_tf_002_network_evidence_pack_v1(
                evidence_root=tmp_path,
                origin_main_sha=_TEST_ORIGIN_MAIN,
                capture_summary={"NETWORK_REQUEST_COUNT": 9},
                verification=verification,
                evidence_bundle=bundle,
            )
    transport = _FakeFreshPretradeTransport(enforcer=None)
    from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
        collect_fresh_pretrade_runtime_get_v1,
    )
    from src.ops.pl_tf_002_productive_read_only_get_complete_v1.constants_v1 import (
        FRESH_PRETRADE_INST_TYPE,
        FRESH_PRETRADE_TD_MODE,
        FRESH_PRETRADE_VENUE_INST_ID,
    )

    collect_fresh_pretrade_runtime_get_v1(
        pretrade_decision_id="after-persist-fail",
        instrument_id=FRESH_PRETRADE_VENUE_INST_ID,
        td_mode=FRESH_PRETRADE_TD_MODE,
        inst_type=FRESH_PRETRADE_INST_TYPE,
        transport=transport,
        require_collection=True,
    )
    assert transport.request_count == 9
