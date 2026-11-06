"""Tests for post-6944 scoped K1 PRE-POST perform v1."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.post_6944_k1_opaque_signing_handle_pre_post_scoped_perform_v1 import (
    DECISION_CONFIG,
    NORMATIVE_SPEC,
    OWNER_GO_TOKEN,
    VENUE_POST_NEXT_OWNER_GO,
    WORKPACKAGE_ID,
    build_k1_pre_post_perform_report_v1,
    perform_scoped_k1_pre_post_boundary_v1,
    validate_scoped_owner_go_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
)
from tests.governance.test_current_productive_k1_opaque_signing_handle_pre_post_policy_v1 import (
    FakeOsNativeStoreLookupBackendV1,
)

REPO = Path(__file__).resolve().parents[2]


def _bound_fake() -> FakeOsNativeStoreLookupBackendV1:
    return FakeOsNativeStoreLookupBackendV1()


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
    payload = perform_scoped_k1_pre_post_boundary_v1(
        repo_root=REPO,
        owner_go_token=OWNER_GO_TOKEN,
        use_productive_macos_backend=False,
        backend=fake,
    )
    assert payload["PERFORM_ATTEMPTED"] is True
    assert payload["K1_HANDLE_CREATED"] is True
    assert payload["SIGNING_PERFORMED"] is True
    assert payload["SECRET_DISCLOSED"] is False
    assert REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    blob = json.dumps(payload)
    assert "sk-test" not in blob
    assert "ak-test" not in blob


def test_perform_without_owner_go_token_fail_closed() -> None:
    payload = perform_scoped_k1_pre_post_boundary_v1(
        repo_root=REPO,
        owner_go_token="",
        use_productive_macos_backend=False,
        backend=_bound_fake(),
    )
    assert payload["PERFORM_ATTEMPTED"] is False


def test_build_report_fixpoint_on_success() -> None:
    fake = _bound_fake()
    perform = perform_scoped_k1_pre_post_boundary_v1(
        repo_root=REPO,
        owner_go_token=OWNER_GO_TOKEN,
        use_productive_macos_backend=False,
        backend=fake,
    )
    report = build_k1_pre_post_perform_report_v1(
        repo_root=REPO,
        baseline_sha="9f32275d158961fed2adec9dae6817fe99224dd9",
        owner_go_token=OWNER_GO_TOKEN,
        perform_payload=perform,
        chain_6942_report={"PRE_EXTERNAL_EFFECT_REACHED": True},
        material_load_6943_report={"MATERIAL_LOAD_PERFORMED": True},
        map_sha256="a",
        atlas_sha256="b",
        e2e_run_id="test",
        evidence_root="evidence/ops/test",
    )
    assert report["FIXPOINT_REACHED"] is True
    assert report["K1_OWNER_GO_CONSUMED"] is True
    assert report["VENUE_POST_OWNER_GO_CONSUMED"] is False
    assert report["EXTERNAL_EFFECT_PERMIT_MINTED"] is False
    assert report["FIRST_REAL_BLOCKER"] == VENUE_POST_NEXT_OWNER_GO
    assert report["WP"] == WORKPACKAGE_ID
