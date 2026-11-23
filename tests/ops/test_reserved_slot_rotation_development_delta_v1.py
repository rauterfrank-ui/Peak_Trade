"""Exact current development progression; no directory or operational grant."""

import hashlib
import json
from pathlib import Path
from runpy import run_path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
POLICY = run_path(str(ROOT / "docs/system_atlas/policy_projection.py"))
DELTAS = POLICY["RESERVED_SLOT_ROTATION_DELTAS"]
BASE = "e2abdf73876b6f093347b27c4145b86cb7fc16c6"
DOUBLE_PLAY_PARENT = "fd5e14ed6f709a0eb22464b47fcd1e666d559be6"
ROTATION_SUCCESSOR = "6b132fa1bd4788a937243c179cf294658c5389f7"
NET_REVERSAL_BOOKING_SUCCESSOR = "78170916f5fd32267b54eb55b241fa65feb1486f"
SOPH_PARENT = "2f6091dd0b9b7de2c110ba9681be1bb8386f214f"
CAP23_PARENT = "8557138f16298f18a3c187b70570aa59c2db90a4"
PUBLISHER = "src/ops/current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1/checked_publication_v1.py"
RECONCILIATION_STARTUP = "src/ops/productive_reconciliation_runtime_binding_v1/startup_gate_v1.py"
LAW = json.loads((ROOT / POLICY["LAW"]).read_text())
ROWS = POLICY["load_policies"](ROOT, LAW)
BEFORE = {
    p: None
    if before is None
    else subprocess.check_output(["git", "show", BASE + ":" + p], cwd=ROOT)
    for p, (before, after) in DELTAS.items()
}


def seed(root, *, before=False):
    for path in DELTAS:
        body = (
            BEFORE[path]
            if before
            else subprocess.check_output(["git", "show", DOUBLE_PLAY_PARENT + ":" + path], cwd=ROOT)
        )
        if body is not None:
            destination = root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(body)


@pytest.mark.parametrize("before", [True, False])
def test_previous_current_tree_or_exact_reviewed_successor_is_accepted(tmp_path, before):
    seed(tmp_path, before=before)
    POLICY["validate_reserved_slot_rotation_bundle"](tmp_path, ROWS)


@pytest.mark.parametrize("parent", [SOPH_PARENT, CAP23_PARENT])
def test_shadow_slot2_publisher_requires_its_exact_rotation_parent(tmp_path, parent):
    validate = POLICY["validate_reserved_slot_rotation_bundle"]
    for path in (
        *DELTAS,
        POLICY["DIRECT_REVERSAL_SOURCE"],
        POLICY["NET_REVERSAL_GET_RECONCILIATION_SOURCE"],
    ):
        dest = tmp_path / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(subprocess.check_output(["git", "show", f"{parent}:{path}"], cwd=ROOT))
    validate(tmp_path, ROWS, double_play=True)

    publisher = tmp_path / PUBLISHER
    successor = (ROOT / PUBLISHER).read_bytes()
    publisher.write_bytes(successor)
    if parent == CAP23_PARENT:
        with pytest.raises(ValueError, match="RESERVED_SLOT_ROTATION_REVIEWED_BUNDLE_REQUIRED"):
            validate(tmp_path, ROWS, double_play=True)
        return

    validate(tmp_path, ROWS, double_play=True)
    publisher.write_bytes(successor + b"\n")
    with pytest.raises(ValueError, match="RESERVED_SLOT_ROTATION_REVIEWED_BUNDLE_REQUIRED"):
        validate(tmp_path, ROWS, double_play=True)


@pytest.mark.parametrize("path", tuple(DELTAS))
def test_partial_bundle_is_rejected(tmp_path, path):
    seed(tmp_path)
    if BEFORE[path] is None:
        (tmp_path / path).unlink()
    else:
        (tmp_path / path).write_bytes(BEFORE[path])
    with pytest.raises(ValueError, match="RESERVED_SLOT_ROTATION_REVIEWED_BUNDLE_REQUIRED"):
        POLICY["validate_reserved_slot_rotation_bundle"](tmp_path, ROWS)


@pytest.mark.parametrize("path", tuple(DELTAS))
def test_different_bodies_cannot_be_admitted_by_rebinding_an_ordinary_hash(tmp_path, path):
    seed(tmp_path)
    raw = (tmp_path / path).read_bytes() + b"\n# different implementation\n"
    (tmp_path / path).write_bytes(raw)
    (tmp_path / "rebound.json").write_text(
        json.dumps(dict(path=path, sha256=hashlib.sha256(raw).hexdigest()))
    )
    with pytest.raises(ValueError, match="RESERVED_SLOT_ROTATION_REVIEWED_BUNDLE_REQUIRED"):
        POLICY["validate_reserved_slot_rotation_bundle"](tmp_path, ROWS)


@pytest.mark.parametrize("path", [p for p in DELTAS if p in {r["path"] for r in ROWS}])
def test_original_policy_baseline_cannot_be_redefined(tmp_path, path):
    seed(tmp_path)
    rows = [{**r, "frozen_sha256": DELTAS[path][1]} if r["path"] == path else dict(r) for r in ROWS]
    with pytest.raises(ValueError, match="RESERVED_SLOT_ROTATION_BASELINE_INVALID"):
        POLICY["validate_reserved_slot_rotation_bundle"](tmp_path, rows)


def test_actual_reader_binds_the_new_policies_and_preserves_startup_and_funding():
    result = POLICY["validate_policy_inventory"](ROOT, LAW)
    admitted = set(result["development_policy_files"])
    assert {p for p in DELTAS if p in {r["path"] for r in ROWS}} <= admitted
    assert result["runtime_effect_inferred"] is False
    for path in (
        "src/ops/current_mf_n5_durable_lane_assignment_persistence_v1/persistence_v1.py",
        "src/ops/n1_standing_pre_external_runtime_supervisor_v1/startup_binding_v1.py",
        "src/ops/portfolio_capital_reservation_budget_v1/recovery_v1.py",
        "src/ops/productive_reconciliation_runtime_binding_v1/startup_gate_v1.py",
        *POLICY["ORDERED_FUNDING_EPISODE_DELTAS"],
    ):
        # Original rotation preserved startup/Funding at its own reviewed revision.
        # The current checkout also includes separately reviewed successors.
        assert subprocess.check_output(
            ["git", "show", ROTATION_SUCCESSOR + ":" + path], cwd=ROOT
        ) == subprocess.check_output(["git", "show", BASE + ":" + path], cwd=ROOT)
        current = (ROOT / path).read_bytes()
        if path == RECONCILIATION_STARTUP:
            assert current == subprocess.check_output(
                ["git", "show", NET_REVERSAL_BOOKING_SUCCESSOR + ":" + path], cwd=ROOT
            )
        elif path in POLICY["DIRECT_REVERSAL_POLICY_DELTAS"]:
            parent, successor = POLICY["DIRECT_REVERSAL_POLICY_DELTAS"][path]
            original = subprocess.check_output(["git", "show", "71e4ce6912:" + path], cwd=ROOT)
            assert hashlib.sha256(original).hexdigest() == parent
            assert hashlib.sha256(current).hexdigest() == successor
        elif path in POLICY["DOUBLE_PLAY_POLICY_DELTAS"]:
            parent, successor = POLICY["DOUBLE_PLAY_POLICY_DELTAS"][path]
            original = subprocess.check_output(
                ["git", "show", DOUBLE_PLAY_PARENT + ":" + path], cwd=ROOT
            )
            assert hashlib.sha256(original).hexdigest() == parent
            assert hashlib.sha256(current).hexdigest() == successor
        else:
            assert current == subprocess.check_output(["git", "show", BASE + ":" + path], cwd=ROOT)
