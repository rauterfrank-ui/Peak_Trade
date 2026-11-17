import hashlib
import json
import subprocess

import pytest

from scripts.ops import check_n1_double_play_runtime_seal_v1 as seal


@pytest.fixture
def sealed_repo(tmp_path):
    def write(path, content):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path, text=True).strip()

    git("init", "-q")
    file = "src/runtime/occupied.py"
    body = "scope = 1\n"
    write(file, body)
    manifest = {
        "schema": "peaktrade.n1_double_play_runtime_seal.v1",
        "state": "SEALED",
        "runtime_authorization_effect": "NONE",
        "directories": ["src/runtime"],
        "files": {file: hashlib.sha256(body.encode()).hexdigest()},
    }
    write(seal.MANIFEST, json.dumps(manifest))
    write(seal.CHECKER, "# base verifier\n")
    write(seal.POLICY, "policy\n")
    write(seal.REFERENCE_WORKFLOW, "# base reference gate\n")
    write(seal.LINT_WORKFLOW, seal.LINT_STEP + "\n        run: python3 checker.py\n")
    git("add", ".")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "commit", "-qm", "Seal")
    return tmp_path, write, git, file, manifest


def test_unrelated_edit_passes_both_checks(sealed_repo):
    root, write, git, _, _ = sealed_repo
    write("src/unrelated.py", "value = 2\n")
    git("add", ".")
    assert seal.verify_content(root) == []
    assert seal.verify_base_policy(root, "HEAD") == []


def test_changed_file_and_recomputed_hash_are_blocked_by_base_policy(sealed_repo):
    root, write, _, file, manifest = sealed_repo
    body = "scope = 2\n"
    write(file, body)
    assert seal.verify_content(root) == [f"sealed file changed: {file}"]
    manifest["files"][file] = hashlib.sha256(body.encode()).hexdigest()
    write(seal.MANIFEST, json.dumps(manifest))
    assert seal.verify_content(root) == []
    errors = seal.verify_base_policy(root, "HEAD")
    assert any(error.endswith(file) for error in errors)
    assert any(error.endswith(seal.MANIFEST) for error in errors)


def test_new_package_source_and_integrity_gate_removal_are_reported(sealed_repo):
    root, write, git, _, _ = sealed_repo
    added = "src/runtime/new_order.py"
    write(added, "order = 1\n")
    write(seal.LINT_WORKFLOW, "# removed\n")
    (root / seal.CHECKER).unlink()
    (root / seal.REFERENCE_WORKFLOW).unlink()
    git("add", "-A")
    assert seal.verify_content(root) == [f"new source in sealed package: {added}"]
    errors = seal.verify_base_policy(root, "HEAD")
    for path in (added, seal.LINT_WORKFLOW, seal.CHECKER, seal.REFERENCE_WORKFLOW):
        assert any(error.endswith(path) for error in errors)
