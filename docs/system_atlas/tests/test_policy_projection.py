"""Frozen policy references and retired-map boundaries, without trading effects."""

from copy import deepcopy
import hashlib
import json
import subprocess
from pathlib import Path
from runpy import run_path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
PROJECTION = run_path(str(ROOT / "docs/system_atlas/policy_projection.py"))
ATLAS = run_path(str(ROOT / "docs/system_atlas/current_atlas.py"))
LAW = json.loads((ROOT / "config/governance/current_law_impact_map_v1/source_v1.json").read_bytes())
SCOPE = json.loads((ROOT / "docs/system_atlas/source/documentation-cleanup.json").read_bytes())


def test_frozen_policy_sources_and_reference_targets_are_valid():
    result = PROJECTION["validate_policy_inventory"](ROOT, LAW)
    assert result["policy_files"] == 780
    assert result["static_reference_sites"] == 9940
    assert result["runtime_effect_inferred"] is False


@pytest.mark.parametrize("field", ["before_sha256", "sha256"])
def test_rebound_ci_seal_requires_its_exact_development_hash(monkeypatch, field):
    binding_path = ROOT / "docs/system_atlas/source/development-binding-v1.json"
    binding = json.loads(binding_path.read_bytes())
    row = next(
        row
        for row in binding["files"]
        if row["path"] == "config/governance/clean_core_seal_manifest_v1.json"
    )
    row[field] = "0" * 64
    original = Path.read_bytes

    def read(path):
        return json.dumps(binding).encode() if path == binding_path else original(path)

    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(ValueError, match="POLICY_DEVELOPMENT_BINDING_INVALID"):
        PROJECTION["validate_policy_inventory"](ROOT, LAW)


def test_rebound_ci_seal_still_rejects_unbound_working_bytes(monkeypatch):
    seal = ROOT / "config/governance/clean_core_seal_manifest_v1.json"
    original = Path.read_bytes

    def read(path):
        raw = original(path)
        return raw + b" " if path == seal else raw

    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(ValueError, match="POLICY_DEVELOPMENT_BINDING_INVALID"):
        PROJECTION["validate_policy_inventory"](ROOT, LAW)


@pytest.mark.parametrize("field", ["before_sha256", "sha256"])
def test_selection_policy_delta_requires_its_exact_development_hash(monkeypatch, field):
    binding_path = ROOT / "docs/system_atlas/source/development-binding-v1.json"
    binding = json.loads(binding_path.read_bytes())
    row = next(
        row
        for row in binding["files"]
        if row["path"] == "src/ops/single_selected_future_policy_v1/selection_v1.py"
    )
    row[field] = "0" * 64
    original = Path.read_bytes

    def read(path):
        return json.dumps(binding).encode() if path == binding_path else original(path)

    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(ValueError, match="POLICY_DEVELOPMENT_BINDING_INVALID"):
        PROJECTION["validate_policy_inventory"](ROOT, LAW)


def test_selection_policy_delta_still_rejects_unbound_working_bytes(monkeypatch):
    source = ROOT / "src/ops/single_selected_future_policy_v1/selection_v1.py"
    original = Path.read_bytes

    def read(path):
        raw = original(path)
        return raw + b" " if path == source else raw

    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(ValueError, match="POLICY_DEVELOPMENT_BINDING_INVALID"):
        PROJECTION["validate_policy_inventory"](ROOT, LAW)


def test_reviewed_development_policies_are_explicit_in_validation_result():
    result = PROJECTION["validate_policy_inventory"](ROOT, LAW)
    reviewed = {
        "config/governance/clean_core_seal_manifest_v1.json",
        "src/ops/single_selected_future_policy_v1/selection_v1.py",
        "config/governance/technical_canonical_wiring_authorization_v1.json",
        *PROJECTION["ORDERED_FUNDING_EPISODE_DELTAS"],
        *PROJECTION["RESERVED_SLOT_ROTATION_DELTAS"],
        *PROJECTION["MANAGED_FILEGATE_OWNER_DELTAS"],
        *PROJECTION["DOUBLE_PLAY_POLICY_DELTAS"],
    }
    frozen = {row["path"] for row in PROJECTION["load_policies"](ROOT, LAW)}
    assert set(result["development_policy_files"]) == reviewed & frozen


@pytest.mark.parametrize("path", tuple(PROJECTION["DOUBLE_PLAY_POLICY_DELTAS"]))
@pytest.mark.parametrize("rebound", [False, True], ids=["prior-bytes", "different-rebound-bytes"])
def test_double_play_requires_exact_complete_policy_bundle(monkeypatch, path, rebound):
    source = ROOT / path
    binding_path = ROOT / "docs/system_atlas/source/development-binding-v1.json"
    original = Path.read_bytes
    raw = (
        original(source) + b"\n# different implementation\n"
        if rebound
        else subprocess.check_output(["git", "show", "835185fb1:" + path], cwd=ROOT)
    )
    binding = json.loads(original(binding_path))
    row = next(row for row in binding["files"] if row["path"] == path)
    row["sha256"] = hashlib.sha256(raw).hexdigest()

    def read(file):
        if file == source:
            return raw
        if file == binding_path:
            return json.dumps(binding).encode()
        return original(file)

    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(
        ValueError,
        match="(DOUBLE_PLAY_POLICY_REVIEWED_BUNDLE_REQUIRED|POLICY_SOURCE_DRIFT):" + path,
    ):
        PROJECTION["validate_policy_inventory"](ROOT, LAW)


@pytest.mark.parametrize("field", ["before_sha256", "sha256"])
def test_numeric_admission_policy_requires_exact_development_hash(monkeypatch, field):
    binding_path = ROOT / "docs/system_atlas/source/development-binding-v1.json"
    binding = json.loads(binding_path.read_bytes())
    row = next(row for row in binding["files"] if row["path"] == PROJECTION["TECHNICAL_ADMISSION"])
    row[field] = "0" * 64
    original = Path.read_bytes

    def read(path):
        return json.dumps(binding).encode() if path == binding_path else original(path)

    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(ValueError, match="POLICY_DEVELOPMENT_BINDING_INVALID"):
        PROJECTION["validate_policy_inventory"](ROOT, LAW)


@pytest.mark.parametrize(
    "fault",
    [
        "extra_path",
        "missing_path",
        "old_path",
        "runtime",
        "core",
        "check_waiver",
        "scope",
        "old_note",
        "new_note",
    ],
)
def test_numeric_admission_rejects_other_policy_changes_even_when_hash_rebound(monkeypatch, fault):
    source = ROOT / PROJECTION["TECHNICAL_ADMISSION"]
    data = json.loads(source.read_bytes())
    if fault == "extra_path":
        data["allowed_paths"].append("src/trading/master_v2/unapproved_seventh_file.py")
    elif fault == "missing_path":
        data["allowed_paths"].pop()
    elif fault == "old_path":
        data["allowed_paths"][0] = "src/trading/master_v2/unapproved_replacement.py"
    elif fault == "runtime":
        data["forbidden_effects"]["RUNTIME_EFFECT"] = "ENABLED"
    elif fault == "core":
        data["required_semantic_invariants"]["CORE_SEMANTICS_CHANGED"] = True
    elif fault == "check_waiver":
        data["required_check_waiver"] = True
    elif fault == "scope":
        data["authorized_path_prefixes"] = ["src/trading/master_v2/"]
    elif fault == "old_note":
        data["authorized_surface_notes"][0] = "Replaced prior attestation"
    else:
        data["authorized_surface_notes"][-1] = "Different purpose"
    raw = json.dumps(data).encode()
    binding_path = ROOT / "docs/system_atlas/source/development-binding-v1.json"
    binding = json.loads(binding_path.read_bytes())
    row = next(row for row in binding["files"] if row["path"] == PROJECTION["TECHNICAL_ADMISSION"])
    row["sha256"] = hashlib.sha256(raw).hexdigest()
    original = Path.read_bytes

    def read(path):
        if path == source:
            return raw
        return json.dumps(binding).encode() if path == binding_path else original(path)

    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(ValueError, match="POLICY_TECHNICAL_ADMISSION_DELTA_INVALID"):
        PROJECTION["validate_policy_inventory"](ROOT, LAW)


def test_numeric_admission_rejects_unbound_working_bytes(monkeypatch):
    source = ROOT / PROJECTION["TECHNICAL_ADMISSION"]
    original = Path.read_bytes

    def read(path):
        raw = original(path)
        return raw + b" " if path == source else raw

    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(ValueError, match="POLICY_DEVELOPMENT_BINDING_INVALID"):
        PROJECTION["validate_policy_inventory"](ROOT, LAW)


def test_binding_cannot_admit_another_changed_policy_source(monkeypatch):
    rel = "src/ops/single_selected_future_policy_v1/constants_v1.py"
    source = ROOT / rel
    original = Path.read_bytes
    raw = original(source)
    binding_path = ROOT / "docs/system_atlas/source/development-binding-v1.json"
    binding = json.loads(original(binding_path))
    binding["files"].append(
        {
            "path": rel,
            "before_sha256": hashlib.sha256(raw).hexdigest(),
            "sha256": hashlib.sha256(raw + b" ").hexdigest(),
        }
    )

    def read(path):
        if path == binding_path:
            return json.dumps(binding).encode()
        return raw + b" " if path == source else original(path)

    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(ValueError, match="POLICY_SOURCE_DRIFT"):
        PROJECTION["validate_policy_inventory"](ROOT, LAW)


def test_cap23_policy_change_identifies_selection_consumer():
    result = PROJECTION["policy_impact_for_paths"](
        LAW, ["src/ops/single_selected_future_policy_v1/constants_v1.py"], ROOT
    )
    assert "src/ops/single_selected_future_policy_v1/selection_v1.py" in result["source_references"]
    assert result["runtime_effect_inferred"] is False


def test_corrupt_policy_inventory_digest_is_rejected():
    doc = deepcopy(LAW)
    doc["policy_inventory"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="POLICY_INVENTORY_DIGEST_MISMATCH"):
        PROJECTION["load_policies"](ROOT, doc)


def test_inventory_path_is_restricted_before_reading_files():
    doc = deepcopy(LAW)
    doc["policy_inventory"]["path"] = "/unexpected/external/file.json"
    with pytest.raises(ValueError, match="POLICY_INVENTORY_CONTRACT_INVALID"):
        PROJECTION["load_policies"](ROOT, doc)


def test_missing_policy_in_the_declared_scope_is_rejected(monkeypatch):
    rows = PROJECTION["load_policies"](ROOT, LAW)
    validate = PROJECTION["validate_policy_inventory"]
    monkeypatch.setitem(validate.__globals__, "load_policies", lambda root, doc: rows[:-1])
    with pytest.raises(ValueError, match="POLICY_SCOPE_COVERAGE_MISMATCH"):
        validate(ROOT, LAW)


def test_missing_law_source_anchor_is_rejected():
    module = run_path(str(ROOT / "scripts/ops/current_law_impact_map_v1.py"))
    doc = deepcopy(LAW)
    doc["law_references"][0]["canonical_anchor"] = "NONEXISTENT_ANCHOR_FOR_TEST"
    assert any("STALE canonical_anchor" in e for e in module["validate_law_references"](doc, ROOT))


def test_retired_system_map_cannot_recreate_views():
    module = run_path(str(ROOT / "scripts/ops/current_system_interaction_authority_map_v1.py"))
    with pytest.raises(RuntimeError, match="RETIRED_MAP"):
        module["write_views"]({})
    assert not (
        ROOT / "docs/governance/current_system_interaction_authority_map_v1/generated"
    ).exists()


def test_retired_census_cli_does_not_claim_current_currency(monkeypatch):
    module = run_path(str(ROOT / "scripts/ops/validate_current_system_census_graph_v1.py"))
    monkeypatch.setattr(sys, "argv", ["validate_current_system_census_graph_v1.py"])
    assert module["main"]() == 2


def test_retired_files_are_absent_and_consumed_input_is_retained():
    assert len(SCOPE["removed"]) == 51
    assert all(not (ROOT / p["path"]).exists() for p in SCOPE["removed"])
    assert (
        ROOT / "config/governance/current_system_interaction_authority_map_v1/source_v1.json"
    ).is_file()
    for item in SCOPE["retained_consumed_documents"]:
        assert (ROOT / item["path"]).is_file()


def test_documentation_scope_cannot_authorize_trading_source_changes():
    assert not ATLAS["allowed"]("src/trading/master_v2/double_play_entry_exit_policy_v0.py", SCOPE)
    assert not ATLAS["allowed"]("config/live_policies.toml", SCOPE)
    assert not ATLAS["allowed"]("runtime/current_productive/new_state.json", SCOPE)


def test_law_views_are_deterministic_and_bound_to_frozen_source():
    first = PROJECTION["render_law_views"](LAW, ROOT)
    assert first == PROJECTION["render_law_views"](LAW, ROOT)
    assert len(first) == 5
    assert all(LAW["baseline_sha"] in view and "AUTHORITY=NONE" in view for view in first.values())


def test_externalized_archives_do_not_include_runtime_or_current_source_inputs():
    rows = SCOPE["externalized_archives"]
    assert len(rows) == 82
    assert all(ATLAS["historical_archive_scope"](row["path"]) for row in rows)
    assert all(not (ROOT / row["path"]).exists() for row in rows)
    assert all(row["role"] == "HISTORICAL_ARCHIVE_NOT_CURRENT_PRODUCT_INPUT" for row in rows)


@pytest.mark.parametrize(
    "path",
    [
        "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
        "runtime/current_productive/state.json",
        "config/live_policies.toml",
        "DISASTER_RECOVERY_other/../../src/current.py",
        ".worktrees/current/src/module.py",
    ],
)
def test_historical_archive_scope_cannot_silently_retire_product_inputs(path):
    assert not ATLAS["historical_archive_scope"](path)
