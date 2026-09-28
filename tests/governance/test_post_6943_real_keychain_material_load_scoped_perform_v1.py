"""Tests for post-6943 scoped real Keychain material load perform v1."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.post_6943_real_keychain_material_load_scoped_perform_v1 import (
    DECISION_CONFIG,
    NORMATIVE_SPEC,
    OWNER_GO_TOKEN,
    WORKPACKAGE_ID,
    build_material_load_perform_report_v1,
    perform_scoped_material_load_v1,
    validate_scoped_owner_go_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    KEYCHAIN_ACCOUNT_ID,
    KEYCHAIN_ITEM_CLASS,
    KEYCHAIN_SERVICE_ID,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    coerce_opaque_value_data_v1,
)
from tests.governance.test_real_keychain_access_or_credential_material_load_policy_v1 import (
    FakeOsNativeStoreLookupBackendV1,
)

REPO = Path(__file__).resolve().parents[2]
FAKE_OPAQUE = b"\x00\x01OPAQUE-TEST-VECTOR-post6943-not-operator-material"


def _bound_fake() -> FakeOsNativeStoreLookupBackendV1:
    fake = FakeOsNativeStoreLookupBackendV1()
    fake.put(
        service=KEYCHAIN_SERVICE_ID,
        account=KEYCHAIN_ACCOUNT_ID,
        item_class=KEYCHAIN_ITEM_CLASS,
        values=[FAKE_OPAQUE],
    )
    return fake


def test_workpackage_paths_exist() -> None:
    assert (REPO / NORMATIVE_SPEC).is_file()
    assert (REPO / DECISION_CONFIG).is_file()


def test_owner_go_validation_fail_closed() -> None:
    bad = validate_scoped_owner_go_v1(repo_root=REPO, owner_go_token="WRONG")
    assert bad.ok is False
    good = validate_scoped_owner_go_v1(repo_root=REPO, owner_go_token=OWNER_GO_TOKEN)
    assert good.ok is True


def test_perform_with_fake_backend_and_owner_go() -> None:
    fake = _bound_fake()
    payload = perform_scoped_material_load_v1(
        repo_root=REPO,
        owner_go_token=OWNER_GO_TOKEN,
        use_productive_macos_backend=False,
        backend=fake,
    )
    assert payload["MATERIAL_LOAD_PERFORMED"] is True
    assert payload["SECRET_DISCLOSED"] is False
    assert REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    blob = json.dumps(payload)
    assert "OPAQUE-TEST-VECTOR" not in blob


def test_perform_without_owner_go_token_fail_closed() -> None:
    payload = perform_scoped_material_load_v1(
        repo_root=REPO,
        owner_go_token="",
        use_productive_macos_backend=False,
        backend=_bound_fake(),
    )
    assert payload["PERFORM_ATTEMPTED"] is False


def test_build_report_fixpoint_on_success() -> None:
    fake = _bound_fake()
    perform = perform_scoped_material_load_v1(
        repo_root=REPO,
        owner_go_token=OWNER_GO_TOKEN,
        use_productive_macos_backend=False,
        backend=fake,
    )
    report = build_material_load_perform_report_v1(
        repo_root=REPO,
        baseline_sha="25f46626dac36b3d53f17c073fd4f4094de9fdf2",
        owner_go_token=OWNER_GO_TOKEN,
        perform_payload=perform,
        chain_6942_report={"PRE_EXTERNAL_EFFECT_REACHED": True},
        map_sha256="a",
        atlas_sha256="b",
        e2e_run_id="test",
        evidence_root="evidence/ops/test",
    )
    assert report["FIXPOINT_REACHED"] is True
    assert report["K1_OWNER_GO_CONSUMED"] is False
    assert report["EXTERNAL_EFFECT_AUTHORIZED"] is False


def test_orchestrator_script_exists() -> None:
    assert (
        REPO / "scripts/ops/run_post_6943_real_keychain_material_load_scoped_perform_v1.py"
    ).is_file()


def test_workpackage_id_stable() -> None:
    assert WORKPACKAGE_ID == "POST_6943_REAL_KEYCHAIN_MATERIAL_LOAD_SCOPED_PERFORM_V1"
