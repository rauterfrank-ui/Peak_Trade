"""Instrument-card freezing rejects source drift and rehashed manifests."""

import hashlib
import json
import os
import subprocess

import pytest

from scripts.ops import check_master_v2_instrument_cards_seal_v1 as seal


@pytest.fixture
def sealed_cards(tmp_path, monkeypatch):
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        monkeypatch.delenv(key, raising=False)

    def write(name, body):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)

    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"}
    }

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path, env=env)

    files = {name: hashlib.sha256(b"value = 1\n").hexdigest() for name in seal.SOURCE_FILES}
    for name in files:
        write(name, "value = 1\n")
    manifest = dict(
        schema="peaktrade.master_v2_instrument_cards_seal.v1",
        state="SEALED",
        owner_universe="Master V2 Double Play",
        runtime_authorization_effect="NONE",
        files=files,
    )
    write(seal.MANIFEST, json.dumps(manifest))
    write(seal.CHECKER, "# checker fixture\n")
    write(seal.WORKFLOW, seal.STEP + "\n        run: python3 checker.py\n")
    git("init", "-q")
    git("add", ".")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "commit", "-qm", "Seal")
    return tmp_path, write, manifest


def test_current_adapter_and_its_ci_guard_match_the_seal(sealed_cards):
    root, _, _ = sealed_cards
    assert seal.verify(root, "HEAD") == []


def test_changed_adapter_and_rehashed_manifest_remain_frozen(sealed_cards):
    root, write, manifest = sealed_cards
    source = sorted(seal.SOURCE_FILES)[0]
    write(source, "value = 2\n")
    assert "sealed file changed: " + source in seal.verify(root)
    manifest["files"][source] = hashlib.sha256(b"value = 2\n").hexdigest()
    write(seal.MANIFEST, json.dumps(manifest))
    assert seal.verify(root) == []
    errors = seal.verify(root, "HEAD")
    assert any(source in error for error in errors)
    assert any(seal.MANIFEST in error for error in errors)


def test_ci_step_removal_is_reported(sealed_cards):
    root, write, _ = sealed_cards
    write(seal.WORKFLOW, "# removed\n")
    assert "instrument-card seal CI step missing" in seal.verify(root, "HEAD")
