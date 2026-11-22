"""Only the exact reviewed binding validator and its original parent are admitted."""

import hashlib
import json
from pathlib import Path
from runpy import run_path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
POLICY = run_path(str(ROOT / "docs/system_atlas/policy_projection.py"))
LAW = json.loads((ROOT / POLICY["LAW"]).read_bytes())
PATH = next(iter(POLICY["P5_BINDING_CONTEXT_ADMISSION_DELTAS"]))
BINDING = ROOT / "docs/system_atlas/source/development-binding-v1.json"


@pytest.mark.parametrize("original", [False, True])
def test_actual_policy_reader_accepts_exact_reviewed_or_original_source(monkeypatch, original):
    read = Path.read_bytes
    frozen = subprocess.check_output(["git", "show", LAW["baseline_sha"] + ":" + PATH], cwd=ROOT)
    monkeypatch.setattr(
        Path, "read_bytes", lambda p: frozen if original and p == ROOT / PATH else read(p)
    )
    result = POLICY["validate_policy_inventory"](ROOT, LAW)
    assert (PATH in result["development_policy_files"]) is not original
    assert result["runtime_effect_inferred"] is False


@pytest.mark.parametrize(
    "fault", ["unreviewed", "unreviewed_rehashed", "missing_row", "wrong_parent"]
)
def test_unknown_body_or_incorrect_parent_binding_stays_rejected(monkeypatch, fault):
    original = Path.read_bytes
    altered = original(ROOT / PATH) + b"\n# unreviewed replacement\n"

    def read(p):
        raw = original(p)
        if p == ROOT / PATH and fault.startswith("unreviewed"):
            return altered
        if p == BINDING:
            doc = json.loads(raw)
            if fault == "missing_row":
                doc["files"] = [r for r in doc["files"] if r["path"] != PATH]
            for row in doc["files"]:
                if row["path"] == PATH:
                    if fault == "unreviewed_rehashed":
                        row["sha256"] = hashlib.sha256(altered).hexdigest()
                    elif fault == "wrong_parent":
                        row["before_sha256"] = "0" * 64
            return json.dumps(doc).encode()
        return raw

    monkeypatch.setattr(Path, "read_bytes", read)
    reason = (
        "POLICY_SOURCE_DRIFT"
        if fault.startswith("unreviewed")
        else "POLICY_DEVELOPMENT_BINDING_INVALID"
    )
    with pytest.raises(ValueError, match=reason):
        POLICY["validate_policy_inventory"](ROOT, LAW)


def test_unrelated_core_policy_drift_still_rejects(monkeypatch):
    original = Path.read_bytes
    target = ROOT / "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda p: original(p) + b"\n# unrelated change\n" if p == target else original(p),
    )
    with pytest.raises(ValueError, match="POLICY_SOURCE_DRIFT"):
        POLICY["validate_policy_inventory"](ROOT, LAW)


def test_frozen_inventories_and_tag_stay_original():
    for path in (
        "docs/system_atlas/source/current-model.json",
        "docs/system_atlas/source/current-files.jsonl.gz",
        "docs/system_atlas/source/current-policies.jsonl.gz",
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
