"""Only the complete exact P5 source bundle is admitted; frozen policies stay."""

import hashlib
import json
from pathlib import Path
from runpy import run_path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
POLICY = run_path(str(ROOT / "docs/system_atlas/policy_projection.py"))
DELTAS = POLICY["P5_ARTIFACT_ADMISSION_DELTAS"]
LAW = json.loads((ROOT / POLICY["LAW"]).read_bytes())
BINDING = ROOT / "docs/system_atlas/source/development-binding-v1.json"


def frozen_bytes(path):
    return subprocess.check_output(["git", "show", LAW["baseline_sha"] + ":" + path], cwd=ROOT)


def seed(root, original=False):
    for path in DELTAS:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(frozen_bytes(path) if original else (ROOT / path).read_bytes())


@pytest.mark.parametrize("original", [True, False])
def test_frozen_and_exact_reviewed_sources_are_admitted(tmp_path, original):
    seed(tmp_path, original)
    POLICY["validate_p5_artifact_admission_bundle"](tmp_path, POLICY["load_policies"](ROOT, LAW))


@pytest.mark.parametrize("path", tuple(DELTAS))
@pytest.mark.parametrize("fault", ["partial", "unreviewed", "missing", "false_frozen_parent"])
def test_partial_or_rebound_source_is_not_a_reviewed_bundle(tmp_path, path, fault):
    seed(tmp_path)
    rows = POLICY["load_policies"](ROOT, LAW)
    if fault == "partial":
        (tmp_path / path).write_bytes(frozen_bytes(path))
    elif fault == "unreviewed":
        changed = (tmp_path / path).read_bytes() + b"\n# unrelated body\n"
        (tmp_path / path).write_bytes(changed)
        (tmp_path / "rebound-development.json").write_text(
            json.dumps(
                {
                    "path": path,
                    "before_sha256": DELTAS[path][0],
                    "sha256": hashlib.sha256(changed).hexdigest(),
                }
            )
        )
    elif fault == "missing":
        (tmp_path / path).unlink()
    else:
        for row in rows:
            if row["path"] == path:
                row["frozen_sha256"] = DELTAS[path][1]
    with pytest.raises(
        ValueError, match="P5_ARTIFACT_ADMISSION_(BASELINE_INVALID|REVIEWED_BUNDLE_REQUIRED)"
    ):
        POLICY["validate_p5_artifact_admission_bundle"](tmp_path, rows)


def test_actual_reader_requires_exact_sources_and_original_bindings():
    result = POLICY["validate_policy_inventory"](ROOT, LAW)
    assert set(DELTAS) <= set(result["development_policy_files"])
    assert result["runtime_effect_inferred"] is False


@pytest.mark.parametrize("path", tuple(DELTAS))
@pytest.mark.parametrize("fault", ["missing_row", "wrong_parent", "unreviewed_rehashed"])
def test_actual_reader_rejects_other_sources_and_unbound_rows(monkeypatch, path, fault):
    original = Path.read_bytes

    def read(target):
        raw = original(target)
        if target == ROOT / path and fault == "unreviewed_rehashed":
            return raw + b"\n# unreviewed replacement\n"
        if target == BINDING:
            doc = json.loads(raw)
            if fault == "missing_row":
                doc["files"] = [row for row in doc["files"] if row["path"] != path]
            else:
                for row in doc["files"]:
                    if row["path"] == path:
                        if fault == "wrong_parent":
                            row["before_sha256"] = "0" * 64
                        else:
                            row["sha256"] = hashlib.sha256(
                                original(ROOT / path) + b"\n# unreviewed replacement\n"
                            ).hexdigest()
            return json.dumps(doc).encode()
        return raw

    monkeypatch.setattr(Path, "read_bytes", read)
    reason = (
        "P5_ARTIFACT_ADMISSION_REVIEWED_BUNDLE_REQUIRED"
        if fault == "unreviewed_rehashed"
        else "POLICY_DEVELOPMENT_BINDING_INVALID"
    )
    with pytest.raises(ValueError, match=reason):
        POLICY["validate_policy_inventory"](ROOT, LAW)


def test_unrelated_policy_change_still_rejects(monkeypatch):
    original = Path.read_bytes
    target = ROOT / "src/trading/master_v2/double_play_entry_exit_policy_v0.py"

    def read(path):
        raw = original(path)
        return raw + b"\n# unrelated policy\n" if path == target else raw

    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(ValueError, match="POLICY_SOURCE_DRIFT"):
        POLICY["validate_policy_inventory"](ROOT, LAW)


def test_original_inventories_and_freeze_tag_stay():
    for path in (
        "docs/system_atlas/source/current-policies.jsonl.gz",
        "docs/system_atlas/source/current-files.jsonl.gz",
        "docs/system_atlas/source/current-model.json",
        "config/governance/current_law_impact_map_v1/source_v1.json",
    ):
        assert (ROOT / path).read_bytes() == subprocess.check_output(
            ["git", "show", "HEAD:" + path], cwd=ROOT
        )
    assert (
        subprocess.check_output(
            ["git", "rev-parse", LAW["source_tag"] + "^{commit}"], cwd=ROOT, text=True
        ).strip()
        == LAW["baseline_sha"]
    )
