"""Reject changes to the reviewed Git tree or the independent review inputs."""

from hashlib import sha256
import json
from pathlib import Path
import subprocess

import pytest

from scripts.ci import check_n1_v2_brev_admission as admission


SOURCE = Path(__file__).resolve().parents[2]


@pytest.fixture
def release_repo(tmp_path):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path, text=True).strip()

    def write(path, content):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def write_json(path, value):
        write(path, json.dumps(value))

    def commit():
        git("add", "-A")
        git(
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.test",
            "commit",
            "-qm",
            "Fixture",
        )
        return git("rev-parse", "HEAD")

    git("init", "-q")
    original_manifest = (SOURCE / admission.V1_MANIFEST).read_text()
    write(admission.V1_MANIFEST, original_manifest)
    write_json(admission.ATLAS, {"authority": "NONE", "files": []})
    write_json(admission.IMPACT, {"changed_paths": [], "authority_effect": "NONE"})
    reviewed = commit()
    sources = {path: f"# reviewed {path}\n" for path in admission.V2_PATHS}
    hashes = {path: sha256(content.encode()).hexdigest() for path, content in sources.items()}
    evidence = json.loads((SOURCE / admission.EVIDENCE).read_text())
    evidence.update(repository_base=reviewed, source_sha256=hashes)
    evidence_raw = json.dumps(evidence)
    policy = json.loads((SOURCE / admission.POLICY).read_text())
    policy.update(
        reviewed_base=reviewed,
        source_sha256=hashes,
        evidence_sha256=sha256(evidence_raw.encode()).hexdigest(),
    )
    for path in admission.CONTROL_PATHS - {admission.POLICY, admission.EVIDENCE}:
        write(path, f"# {path}\n")
    write_json(admission.POLICY, policy)
    write(admission.EVIDENCE, evidence_raw)
    write_json(admission.ATLAS, {"authority": "NONE", "files": [], "revision": "governance"})
    write_json(
        admission.IMPACT,
        {"changed_paths": sorted(admission.CONTROL_PATHS), "authority_effect": "NONE"},
    )
    governance = commit()

    def implementation():
        for path, content in sources.items():
            write(path, content)
        write_json(
            admission.ATLAS,
            {
                "authority": "NONE",
                "revision": "governance",
                "files": [
                    {"path": path, "before_sha256": None, "sha256": digest}
                    for path, digest in hashes.items()
                ],
            },
        )
        paths = sorted(admission.CONTROL_PATHS | admission.V2_PATHS)
        write_json(
            admission.IMPACT,
            {
                "changed_paths": paths,
                "changed_paths_sha256": sha256("\n".join(paths).encode()).hexdigest(),
                "authority_effect": "NONE",
            },
        )
        return commit()

    return tmp_path, reviewed, governance, implementation, write, commit


def test_governance_bootstrap_and_then_exact_implementation(release_repo):
    root, reviewed, governance, implementation, _, _ = release_repo
    assert admission.verify(root, reviewed, governance, bootstrap=True) == "GOVERNANCE_BOOTSTRAP"
    assert admission.verify(root, governance, governance) == "V2_ABSENT"
    accepted = implementation()
    assert admission.verify(root, governance, accepted) == "V2_SOURCE_ADMITTED"
    assert admission.verify(root, accepted, accepted) == "V2_SOURCE_PRESERVED"


@pytest.mark.parametrize(
    "path", [admission.CHECKER, admission.WORKFLOW, admission.POLICY, admission.EVIDENCE]
)
def test_candidate_cannot_edit_trusted_inputs(release_repo, path):
    root, _, governance, _, write, commit = release_repo
    write(path, "forged")
    with pytest.raises(admission.AdmissionError, match="TRUSTED_GOVERNANCE_FILES_CHANGED"):
        admission.verify(root, governance, commit())


@pytest.mark.parametrize(
    ("path", "message"),
    [
        (f"{admission.V2_ROOT}/runtime.py", "V2_SOURCE_DIGEST_MISMATCH"),
        (f"{admission.V2_ROOT}/extra.py", "V2_PATH_SET_CHANGED"),
        (admission.ATLAS, "UNREVIEWED_ATLAS_DELTA"),
        (admission.IMPACT, "UNREVIEWED_LAW_IMPACT_DELTA"),
        ("src/extra.py", "UNREVIEWED_IMPLEMENTATION_DIFF"),
    ],
)
def test_candidate_cannot_extend_reviewed_diff(release_repo, path, message):
    root, _, governance, implementation, write, commit = release_repo
    implementation()
    if path.endswith(".json"):
        record = json.loads((root / path).read_text())
        record["authority" if path == admission.ATLAS else "authority_effect"] = "ALTERED"
        write(path, json.dumps(record))
    else:
        write(path, "# altered\n")
    with pytest.raises(admission.AdmissionError, match=message):
        admission.verify(root, governance, commit())


def test_runtime_base_drift_requires_new_review(release_repo):
    root, _, _, implementation, write, commit = release_repo
    write("src/extra.py", "outside reviewed base")
    drifted = commit()
    with pytest.raises(admission.AdmissionError, match="REVIEWED_BASE_CHANGED"):
        admission.verify(root, drifted, implementation())


def test_bootstrap_must_exclude_runtime(release_repo):
    root, reviewed, _, implementation, _, _ = release_repo
    with pytest.raises(admission.AdmissionError, match="UNREVIEWED_BOOTSTRAP_DIFF"):
        admission.verify(root, reviewed, implementation(), bootstrap=True)


def test_bootstrap_rejects_unbound_proof(release_repo):
    root, reviewed, _, _, write, commit = release_repo
    write(admission.EVIDENCE, '{"start_authorized": true}')
    with pytest.raises(admission.AdmissionError, match="OFFLINE_EVIDENCE_DIGEST_MISMATCH"):
        admission.verify(root, reviewed, commit(), bootstrap=True)


def test_replacing_source_with_symlink_is_rejected(release_repo):
    root, _, governance, implementation, _, commit = release_repo
    implementation()
    source = root / admission.V2_ROOT / "runtime.py"
    source.unlink()
    source.symlink_to("checkpoint.py")
    with pytest.raises(admission.AdmissionError, match="REGULAR_FILE_REQUIRED"):
        admission.verify(root, governance, commit())
