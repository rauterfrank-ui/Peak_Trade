"""The repaired adjudication checker has one exact source admission, no policy grant."""

import hashlib
import json
from pathlib import Path
from runpy import run_path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
POLICY = run_path(str(ROOT / "docs/system_atlas/policy_projection.py"))
LAW = json.loads((ROOT / POLICY["LAW"]).read_bytes())
CHECKER = "src/governance/unified_blueprint_d01_d02_topology_adjudication_v1.py"
BINDING = ROOT / "docs/system_atlas/source/development-binding-v1.json"


def test_exact_checker_is_admitted_without_runtime_effect():
    result = POLICY["validate_policy_inventory"](ROOT, LAW)
    assert CHECKER in result["development_policy_files"]
    assert result["runtime_effect_inferred"] is False


@pytest.mark.parametrize("fault", ["different_source_rehashed", "missing_row", "wrong_parent"])
def test_other_source_or_unbound_checker_is_rejected(monkeypatch, fault):
    original = Path.read_bytes

    def read(path):
        raw = original(path)
        if path == ROOT / CHECKER and fault == "different_source_rehashed":
            return raw + b"\n# unreviewed body\n"
        if path == BINDING:
            doc = json.loads(raw)
            if fault == "missing_row":
                doc["files"] = [r for r in doc["files"] if r["path"] != CHECKER]
            else:
                for row in doc["files"]:
                    if row["path"] == CHECKER:
                        if fault == "wrong_parent":
                            row["before_sha256"] = "0" * 64
                        else:
                            row["sha256"] = hashlib.sha256(
                                original(ROOT / CHECKER) + b"\n# unreviewed body\n"
                            ).hexdigest()
            return json.dumps(doc).encode()
        return raw

    monkeypatch.setattr(Path, "read_bytes", read)
    reason = (
        "POLICY_SOURCE_DRIFT"
        if fault == "different_source_rehashed"
        else "POLICY_DEVELOPMENT_BINDING_INVALID"
    )
    with pytest.raises(ValueError, match=reason):
        POLICY["validate_policy_inventory"](ROOT, LAW)


def test_frozen_map_config_and_inventories_are_preserved():
    for path in (
        "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
        "config/governance/unified_blueprint_d01_d02_topology_adjudication_v1.json",
        "docs/system_atlas/source/current-policies.jsonl.gz",
        "docs/system_atlas/source/current-model.json",
    ):
        # Atlas metadata were generated after the source freeze; preserve their
        # accepted checkout bytes, while source/config retain the source commit.
        revision = "HEAD" if path.startswith("docs/") else LAW["baseline_sha"]
        assert (ROOT / path).read_bytes() == subprocess.check_output(
            ["git", "show", f"{revision}:{path}"], cwd=ROOT
        )
    model = json.loads((ROOT / "docs/system_atlas/source/current-model.json").read_bytes())
    assert model["source_commit"] == LAW["baseline_sha"]


def test_unrelated_policy_still_rejects(monkeypatch):
    original = Path.read_bytes
    target = ROOT / "src/trading/master_v2/double_play_entry_exit_policy_v0.py"

    def read(path):
        raw = original(path)
        return raw + b"\n# unrelated change\n" if path == target else raw

    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(ValueError, match="POLICY_SOURCE_DRIFT"):
        POLICY["validate_policy_inventory"](ROOT, LAW)
