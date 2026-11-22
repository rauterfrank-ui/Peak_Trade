"""Admit an exact historical map without interpreting its baseline as current HEAD."""

import copy
import hashlib
import json

import pytest

from src.governance import unified_blueprint_d01_d02_topology_adjudication_v1 as owner

BINDING = {
    "scope": "FROZEN_MAP_CONTENT_AND_CURRENT_REFERENCE_CHECKS",
    "authority_effect": "NONE",
    "source_commit": "c742a23c964901c1353fcf3468e618db9cb6ef42",
    "source_sha256": "20438d7bfa7955673bcf94da032af242fb460e9bf14d41ee7e76ab7d0bc7e9fe",
    "map_baseline_sha": "1bac0d93302c6e589effafe46fccb055d82bd44e",
    "historical_authorized_baseline_sha": "dfcf4d04b8400763bee6ab0b465fa182927dea75",
}


@pytest.fixture
def original(tmp_path):
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    doc = json.loads((root / owner.ADJUDICATION_CONFIG).read_text())
    binding_path = tmp_path / owner.MAP_BINDING_EVIDENCE
    binding_path.parent.mkdir(parents=True)
    binding_path.write_text(json.dumps({"accepted_binding": BINDING}))
    path = tmp_path / owner.MAP_SOURCE
    path.parent.mkdir(parents=True)
    raw = (root / owner.MAP_SOURCE).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == BINDING["source_sha256"]
    path.write_bytes(raw)
    return doc, path, tmp_path


@pytest.mark.parametrize("head", ["a" * 40, "b" * 40, BINDING["map_baseline_sha"]])
def test_frozen_content_admission_does_not_depend_on_checkout_head(original, head, monkeypatch):
    doc, _, root = original
    monkeypatch.setattr(owner, "git_head_sha", lambda _: head)
    assert owner.validate_map_currency_binding(doc, root) == []


@pytest.mark.parametrize("fault", ["current_head", "authorized", "rehash", "missing_binding"])
def test_baseline_alias_cannot_authorize_changed_map_content(original, fault, monkeypatch):
    doc, path, root = original
    head = "a" * 40
    monkeypatch.setattr(owner, "git_head_sha", lambda _: head)
    content = json.loads(path.read_text())
    content["domains"][0]["role"] += " altered declaration"
    content["baseline_sha"] = (
        doc["authorized_baseline_sha"] if fault in {"authorized", "missing_binding"} else head
    )
    raw = json.dumps(content).encode()
    path.write_bytes(raw)
    if fault == "rehash":
        binding = {
            **BINDING,
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "map_baseline_sha": head,
        }
        (root / owner.MAP_BINDING_EVIDENCE).write_text(json.dumps({"accepted_binding": binding}))
    if fault == "missing_binding":
        (root / owner.MAP_BINDING_EVIDENCE).unlink()
    assert owner.validate_map_currency_binding(doc, root)


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_commit", "a" * 40),
        ("scope", "CURRENT_RUNTIME_PROVEN"),
        ("authority_effect", "APPLY"),
        ("historical_authorized_baseline_sha", "a" * 40),
    ],
)
def test_migration_cannot_relabel_historical_scope(original, field, value, monkeypatch):
    doc, path, root = original
    doc = copy.deepcopy(doc)
    binding = {**BINDING, field: value}
    (root / owner.MAP_BINDING_EVIDENCE).write_text(json.dumps({"accepted_binding": binding}))
    # A matching HEAD used to make all additional binding claims irrelevant.
    monkeypatch.setattr(owner, "git_head_sha", lambda _: BINDING["map_baseline_sha"])
    assert owner.validate_map_currency_binding(doc, root)


def test_old_unbound_conflict_still_rejects(original, monkeypatch):
    doc, _, root = original
    (root / owner.MAP_BINDING_EVIDENCE).unlink()
    monkeypatch.setattr(owner, "git_head_sha", lambda _: "a" * 40)
    assert owner.validate_map_currency_binding(doc, root)
