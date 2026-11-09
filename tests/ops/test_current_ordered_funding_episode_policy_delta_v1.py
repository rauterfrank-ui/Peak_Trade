"""Exact reviewed Funding bundle; original recovery and unrelated freezes stay."""

import hashlib
import json
from pathlib import Path
from runpy import run_path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
POLICY = run_path(str(ROOT / "docs/system_atlas/policy_projection.py"))
DELTAS = POLICY["ORDERED_FUNDING_EPISODE_DELTAS"]
LAW = json.loads((ROOT / "config/governance/current_law_impact_map_v1/source_v1.json").read_text())
FROZEN = LAW["baseline_sha"]
BASE = "304719c94030ff9aacdf2571e2ae56533f9e6a25"
BINDING = ROOT / "docs/system_atlas/source/development-binding-v1.json"
PRESERVED = (
    "src/ops/current_mf_n5_durable_lane_assignment_persistence_v1/persistence_v1.py",
    "src/ops/n1_standing_pre_external_runtime_supervisor_v1/startup_binding_v1.py",
    "src/ops/portfolio_capital_reservation_budget_v1/recovery_v1.py",
    "src/ops/productive_reconciliation_runtime_binding_v1/startup_gate_v1.py",
    "src/ops/mf_membership_selector_and_rotation_runtime_contract_v1.py",
)


def git_bytes(revision, path):
    return subprocess.check_output(["git", "show", revision + ":" + path], cwd=ROOT)


def policies():
    return POLICY["load_policies"](ROOT, LAW)


def seed(root, *, original=False):
    for path in DELTAS:
        destination = root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(git_bytes(FROZEN, path) if original else (ROOT / path).read_bytes())


@pytest.mark.parametrize("original", [True, False], ids=["frozen-originals", "reviewed-successor"])
def test_original_and_exact_reviewed_bundle_are_admissible(tmp_path, original):
    seed(tmp_path, original=original)
    POLICY["validate_ordered_funding_episode_bundle"](tmp_path, policies())


@pytest.mark.parametrize("path", tuple(DELTAS))
@pytest.mark.parametrize("damage", ["partial", "unreviewed-rebound", "baseline-rebound"])
def test_other_bodies_or_partial_bundle_cannot_be_admitted_by_hash_rebinding(
    tmp_path, path, damage
):
    seed(tmp_path)
    rows = policies()
    if damage == "partial":
        (tmp_path / path).write_bytes(git_bytes(FROZEN, path))
    elif damage == "unreviewed-rebound":
        modified = (tmp_path / path).read_bytes() + b"\n# unreviewed change\n"
        (tmp_path / path).write_bytes(modified)
        # Even a perfectly rebound ordinary development row is not approval.
        binding = dict(
            path=path, before_sha256=DELTAS[path][0], sha256=hashlib.sha256(modified).hexdigest()
        )
        (tmp_path / "rebound-development.json").write_text(json.dumps(binding))
    else:
        for row in rows:
            if row["path"] == path:
                row["frozen_sha256"] = hashlib.sha256((tmp_path / path).read_bytes()).hexdigest()
    with pytest.raises(
        ValueError, match="ORDERED_FUNDING_EPISODE_(REVIEWED_BUNDLE_REQUIRED|BASELINE_INVALID)"
    ):
        POLICY["validate_ordered_funding_episode_bundle"](tmp_path, rows)


def test_actual_policy_inventory_accepts_reviewed_bundle_with_original_binding():
    result = POLICY["validate_policy_inventory"](ROOT, LAW)
    assert set(DELTAS) <= set(result["development_policy_files"])
    assert result["runtime_effect_inferred"] is False


@pytest.mark.parametrize("path", tuple(DELTAS))
def test_actual_reader_rejects_missing_original_development_binding(monkeypatch, path):
    original = Path.read_bytes

    def read_bytes(target):
        raw = original(target)
        if target == BINDING:
            doc = json.loads(raw)
            doc["files"] = [row for row in doc["files"] if row["path"] != path]
            return json.dumps(doc).encode()
        return raw

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    with pytest.raises(ValueError, match="POLICY_DEVELOPMENT_BINDING_INVALID"):
        POLICY["validate_policy_inventory"](ROOT, LAW)


def test_actual_reader_still_refuses_an_unrelated_frozen_policy(monkeypatch):
    path = ROOT / "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
    original = Path.read_bytes

    def read_bytes(target):
        raw = original(target)
        return raw + b"\n# unrelated frozen change\n" if target == path else raw

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    with pytest.raises(ValueError, match="POLICY_SOURCE_DRIFT"):
        POLICY["validate_policy_inventory"](ROOT, LAW)


@pytest.mark.parametrize("path", PRESERVED)
def test_startup_topology_reconciliation_budget_and_reviewed_rotation_owner(path):
    # The later explicit rotation instruction extends the membership owner.
    # The original Funding grant alone still cannot admit that extension.
    rotation = POLICY["RESERVED_SLOT_ROTATION_DELTAS"]
    if path in rotation:
        POLICY["validate_reserved_slot_rotation_bundle"](ROOT, policies())
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == rotation[path][1]
    else:
        assert (ROOT / path).read_bytes() == git_bytes(BASE, path)


def test_frozen_inventory_and_tags_remain_original():
    for path in (
        "docs/system_atlas/source/current-policies.jsonl.gz",
        "docs/system_atlas/source/current-model.json",
    ):
        assert (ROOT / path).read_bytes() == git_bytes(BASE, path)
    resolved = subprocess.check_output(
        ["git", "rev-parse", LAW["source_tag"] + "^{commit}"], cwd=ROOT, text=True
    ).strip()
    assert resolved == FROZEN
