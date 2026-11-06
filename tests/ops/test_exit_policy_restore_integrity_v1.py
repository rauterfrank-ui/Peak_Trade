"""Existing exit state must not cross instrument or partial-publication boundaries."""

import json
from pathlib import Path

import pytest

from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
    COMMIT_MARKER_FILENAME,
    EXIT_STATE_FILENAME,
    MANIFEST_FILENAME,
)
from src.ops.exit_policy_producer_binding_v1.host_binding_v1 import (
    HostExitPolicyBindingV1,
    commit_host_exit_policy_state_v1,
    ensure_host_exit_policy_binding_v1,
)
from src.ops.exit_policy_producer_binding_v1.persistence_v1 import (
    ExitPolicyPersistenceError,
    load_exit_policy_state_v1,
    write_manifest,
)


def _persist(root: Path):
    binding = ensure_host_exit_policy_binding_v1(
        HostExitPolicyBindingV1(),
        instrument_id="instrument-A",
        repository_sha="revision",
        config_digest="config",
        state_root=root,
    )
    binding.has_open_position = True
    binding.existing_position_side = "long"
    binding.entry_price = 1000.0
    binding.entry_event_time = 1700000000.0
    commit_host_exit_policy_state_v1(binding, persist=True, writer_session_id="test")
    return binding


def test_restore_does_not_attach_foreign_instrument_entry(tmp_path):
    _persist(tmp_path)
    binding = HostExitPolicyBindingV1()
    with pytest.raises(ExitPolicyPersistenceError, match="INSTRUMENT_MISMATCH"):
        ensure_host_exit_policy_binding_v1(
            binding,
            instrument_id="instrument-B",
            repository_sha="revision",
            config_digest="config",
            state_root=tmp_path,
        )
    assert binding.alpha_blocked


@pytest.mark.parametrize("damage", ["empty_manifest", "missing_marker", "inconsistent_marker"])
def test_partial_or_inconsistent_exit_publication_is_preserved_and_rejected(tmp_path, damage):
    _persist(tmp_path)
    if damage == "empty_manifest":
        (tmp_path / MANIFEST_FILENAME).write_text("")
    elif damage == "missing_marker":
        (tmp_path / COMMIT_MARKER_FILENAME).unlink()
    else:
        marker_path = tmp_path / COMMIT_MARKER_FILENAME
        marker = json.loads(marker_path.read_text())
        marker["state_digest"] = "0" * 64
        marker_path.write_text(json.dumps(marker))
        write_manifest(tmp_path, (EXIT_STATE_FILENAME, COMMIT_MARKER_FILENAME))
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir() if p.is_file()}
    with pytest.raises(ExitPolicyPersistenceError):
        ensure_host_exit_policy_binding_v1(
            HostExitPolicyBindingV1(),
            instrument_id="instrument-A",
            repository_sha="revision",
            config_digest="config",
            state_root=tmp_path,
        )
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir() if p.is_file()} == before


def test_existing_integer_valued_anchor_keeps_original_marker_hash_valid(tmp_path):
    binding = _persist(tmp_path)
    binding.entry_price = 1000
    commit_host_exit_policy_state_v1(binding, persist=True, writer_session_id="integer-anchor")
    loaded = load_exit_policy_state_v1(
        tmp_path, expected_repository_sha="revision", expected_config_digest="config"
    )
    assert loaded.entry_price == 1000.0


@pytest.mark.parametrize(
    "field,value",
    [
        ("has_open_position", "false"),
        ("entry_price", True),
        ("entry_event_time", float("inf")),
        ("commit_sequence", None),
    ],
)
def test_resealed_structurally_invalid_state_cannot_change_meaning(tmp_path, field, value):
    _persist(tmp_path)
    path = tmp_path / EXIT_STATE_FILENAME
    payload = json.loads(path.read_text())
    payload[field] = value
    path.write_text(json.dumps(payload))
    write_manifest(tmp_path, (EXIT_STATE_FILENAME, COMMIT_MARKER_FILENAME))
    with pytest.raises(ExitPolicyPersistenceError, match="EXIT_STATE_CORRUPT"):
        load_exit_policy_state_v1(
            tmp_path, expected_repository_sha="revision", expected_config_digest="config"
        )
