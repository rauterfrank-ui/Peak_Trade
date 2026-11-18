import json
from pathlib import Path
import plistlib
import time

import pytest

from scripts.ops import brev_v2_mac_host_service as service, peak_trade_runtime
from scripts.ops import check_brev_v2_operating_point as inspection


@pytest.fixture
def manifest(tmp_path):
    root = tmp_path.resolve()
    revision = "1" * 40
    value = {
        "schema": service.SCHEMA,
        "repository_root": str(service.REPO),
        "checkout_sha": revision,
        "sandbox_root": str(root),
        "mode": "offline_replay",
        "bounds": {
            "host_id": "offline-test",
            "repository_sha": revision,
            "runtime_config_digest": "2" * 64,
            "expires_at_unix": time.time() + 120,
            "max_total_cycles": 1,
            "max_total_seconds": 60,
            "wait_interval_seconds": 1,
        },
        "runtime_request_config": {
            "repository_sha": revision,
            "bound": {"venue_native_id": "BREV-USDT-SWAP"},
            "authorization": {
                "max_cycles_per_run": 1,
                "max_run_duration_seconds": 60,
                "wait_interval_seconds": 1,
            },
        },
        "cap24": {
            "productivity_root": str(root / "cap24"),
            "repository_sha": revision,
            "publication_sha256": "3" * 64,
        },
        "filegate": {"state_path": str(root / "filegate.json"), "authority_root": None},
    }
    return root / "manifest.json", value


def test_v2_plist_dispatches_to_the_canonical_launcher_and_requires_replay_ports(
    manifest,
    capsys,
):
    path, value = manifest
    path.write_text(json.dumps(value))
    output = path.with_suffix(".plist")
    assert (
        peak_trade_runtime.main(
            ["host-service", "prepare", "--manifest", str(path), "--output-path", str(output)]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["service_activated"] is False
    plist = plistlib.loads(output.read_bytes())
    assert plist["Label"] == service.LABEL
    assert plist["KeepAlive"] == {"SuccessfulExit": False}
    assert plist["ProgramArguments"][:2] == [
        str(service.REPO / "scripts/pt"),
        str(service.REPO / "scripts/ops/peak_trade_runtime.py"),
    ]
    assert peak_trade_runtime.main(plist["ProgramArguments"][2:]) == 75
    assert json.loads(capsys.readouterr().out)["error_code"] == (
        "HOST_BREV_V2_OFFLINE_FIXTURE_PORTS_REQUIRED"
    )
    assert not (path.parent / "occupied-n1-v2").exists()


def test_scoped_get_run_stops_before_preparing_ports_when_owner_go_is_denied(
    manifest,
    capsys,
    monkeypatch,
):
    path, value = manifest
    value["mode"] = "scoped_readonly_get"
    path.write_text(json.dumps(value))
    monkeypatch.delenv(service.ROOT_ENV, raising=False)
    monkeypatch.setenv(service.FILEGATE_ENV, value["filegate"]["state_path"])
    monkeypatch.setattr(service, "_require_checkout", lambda revision: None)
    monkeypatch.setattr(
        service,
        "validate_bounded_continuous_run_owner_go_decision_v1",
        lambda **_: (False, ("BASELINE_LINEAGE_IMMUTABLE_SURFACE_DRIFT",)),
    )
    monkeypatch.setattr(
        service,
        "_prepare_occupied_n1_request",
        lambda **_: pytest.fail("owner denial reached the runtime request"),
    )
    assert peak_trade_runtime.main(["host-service", "run", "--manifest", str(path)]) == 75
    assert json.loads(capsys.readouterr().out)["error_code"] == (
        "BASELINE_LINEAGE_IMMUTABLE_SURFACE_DRIFT"
    )
    assert not Path(value["filegate"]["state_path"]).exists()


def test_package_exposes_independent_operating_restart_and_post_blockers(
    manifest, capsys, monkeypatch
):
    path, value = manifest
    value["mode"] = "scoped_readonly_get"
    value["bounds"]["expires_at_unix"] = time.time() - 5
    path.write_text(json.dumps(value))
    monkeypatch.setattr(
        service, "_run", lambda *args: pytest.fail("inspection entered the runtime")
    )
    monkeypatch.setattr(service, "_require_checkout", lambda revision: None)
    monkeypatch.setattr(
        service,
        "validate_bounded_continuous_run_owner_go_decision_v1",
        lambda **_: (False, ("BASELINE_LINEAGE_IMMUTABLE_SURFACE_DRIFT",)),
    )
    assert inspection.main(["--manifest", str(path)]) == 75
    report = json.loads(capsys.readouterr().out)
    assert report["runtime_authorization_effect"] == "NONE"
    slices = report["slices"]
    assert "BASELINE_LINEAGE_IMMUTABLE_SURFACE_DRIFT" in slices["operating_point"]["blockers"]
    assert "CANONICAL_FILEGATE_UNPROVEN" in slices["operating_point"]["blockers"]
    assert "MANIFEST_WINDOW_EXPIRED" in slices["restart"]["blockers"]
    assert "MAC_SERVICE_START_AND_RESTART_UNPROVEN" in slices["restart"]["blockers"]
    assert "POST_ISSUER_AND_STORE_UNBOUND" in slices["post"]["blockers"]
    assert "V2_POST_PORT_NOT_CONNECTED" in slices["post"]["blockers"]
    assert not (path.parent / "occupied-n1-v2").exists()


def test_post_slice_checks_original_store_and_independent_checkpoint_without_consuming(tmp_path):
    from nacl.signing import SigningKey
    from src.ops.full_core_live_path_composition_root_v1.current_productive_shared_post_owner_authority_v1 import (
        PostOwnerAuthorityStoreV1,
        SharedPostOwnerAuthorityError,
    )

    root = tmp_path.resolve()
    verify_key = bytes(SigningKey.generate().verify_key)
    store_dir, checkpoint_dir = root / "store", root / "checkpoint"
    store_dir.mkdir()
    checkpoint_dir.mkdir()
    store = PostOwnerAuthorityStoreV1(
        store_dir / "post.sqlite",
        "test-store",
        "test-issuer",
        verify_key,
        checkpoint_dir / "post-checkpoint.sqlite",
    )
    store.provision_v1()
    digest = store.binding_digest_v1()
    config = {
        "account": "test-account",
        "store": str(store.path),
        "store_id": store.store_id,
        "issuer_id": store.issuer_id,
        "verify_key": verify_key.hex(),
        "checkpoint": str(store.checkpoint_path),
        "binding_sha256": digest,
    }
    binding = root / "post-binding.json"
    binding.write_text(json.dumps(config))
    original = (store.path.read_bytes(), store.checkpoint_path.read_bytes())
    assert inspection._check_post_binding(binding, "test-account") == digest
    assert (store.path.read_bytes(), store.checkpoint_path.read_bytes()) == original
    with pytest.raises(ValueError, match="POST_BINDING_SCOPE_MISMATCH"):
        inspection._check_post_binding(binding, "foreign-account")
    binding.write_text(json.dumps({**config, "verify_key": "ab" * 32}))
    with pytest.raises(
        SharedPostOwnerAuthorityError, match="POST_AUTHORITY_STORE_IDENTITY_MISMATCH"
    ):
        inspection._check_post_binding(binding, "test-account")
