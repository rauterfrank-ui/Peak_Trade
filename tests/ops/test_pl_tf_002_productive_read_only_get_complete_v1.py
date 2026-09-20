"""Tests for PL-TF-002 productive read-only GET completion WP."""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import patch

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
    OWNER_GO,
    SESSION_OWNER_GO,
)
from src.ops.pl_tf_002_productive_read_only_get_complete_v1.errors_v1 import (
    PlTf002ProductiveReadOnlyGetCompleteError,
)
from src.ops.pl_tf_002_productive_read_only_get_complete_v1.pre_network_jit_v1 import (
    build_pl_tf_002_pre_network_jit_proof_v1,
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
