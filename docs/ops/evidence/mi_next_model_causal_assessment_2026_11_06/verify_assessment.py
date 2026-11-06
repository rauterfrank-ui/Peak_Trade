"""Read-only source, history, evidence and Obsidian integrity verification."""

from pathlib import Path
import gzip
import hashlib
import json
import math
import re
import subprocess
import xml.etree.ElementTree as ET

PACK = Path(__file__).resolve().parent
REPO = PACK.parents[3]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def verify():
    manifest = load(PACK / "manifest.json")
    actual = {
        str(p.relative_to(PACK))
        for p in PACK.rglob("*")
        if p.is_file() and p.name != "manifest.json" and "__pycache__" not in p.parts
    }
    assert actual == {x["path"] for x in manifest["files"]}
    for item in manifest["files"]:
        assert sha((PACK / item["path"]).read_bytes()) == item["sha256"], item["path"]
    sources = load(PACK / "sources.json")["files"]
    indexed = load(PACK / "consumer-index.json")["files_scanned"]
    for item in sources + indexed:
        assert sha((REPO / item["path"]).read_bytes()) == item["sha256"], item["path"]
    for item in load(PACK / "historical-sources.json"):
        raw = subprocess.check_output(
            ["git", "show", item["revision"] + ":" + item["source_path"]], cwd=REPO
        )
        assert sha(raw) == item["sha256"] == sha((PACK / item["snapshot"]).read_bytes())
    for source in load(PACK / "design-source-excerpts.json"):
        assert sha((REPO / source["source"]).read_bytes()) == source["snapshot_sha256"]
    for source in load(PACK / "original-learning-decisions.json"):
        assert sha(Path(source["path"]).read_bytes()) == source["source_sha256"]
        assert sha(source["text"].encode()) == source["text_sha256"]
    changes = load(PACK / "vault-changes.json")
    vault = Path(changes["vault"])
    links = 0
    for item in changes["changes"]:
        assert sha((vault / item["path"]).read_bytes()) == item["sha256"]
        assert sha((PACK / item["snapshot"]).read_bytes()) == item["sha256"]
        if item["before_snapshot"]:
            assert sha((PACK / item["before_snapshot"]).read_bytes()) == item["before_sha256"]
        text = (vault / item["path"]).read_text()
        for raw in re.findall(r"\[\[([^\]]+)\]\]", text):
            target = raw.split("|")[0].split("#")[0]
            if target:
                assert any((vault / (target + ext)).is_file() for ext in ["", ".md", ".canvas"]), (
                    target
                )
                links += 1
    binding = changes["binding"]
    before = load(PACK / binding["before_snapshot"])
    after_raw = (vault / binding["path"]).read_bytes()
    assert sha(after_raw) == binding["sha256"]
    assert sha(gzip.decompress((PACK / binding["snapshot"]).read_bytes())) == binding["sha256"]
    assert (
        sha(gzip.decompress((PACK / binding["before_snapshot"]).read_bytes()))
        == binding["before_sha256"]
    )
    after = json.loads(after_raw)
    overlay = after.pop("mi_next_model_causal_assessment")
    assert overlay["next_model_implemented"] is False
    old = before.pop("generated_files")
    new = after.pop("generated_files")
    assert before == after
    assert len(old) == len(new)
    changed = {x["path"] for x in changes["changes"]}
    for a, b in zip(old, new):
        assert a["path"] == b["path"]
        if b["path"] in changed:
            assert b["sha256"] == sha((vault / b["path"]).read_bytes())
        else:
            assert a == b
    for p in [PACK / "README.md", *(vault / x["path"] for x in changes["changes"])]:
        for raw in re.findall(r"\]\(([^\n]+?)\)", p.read_text()):
            target = raw.strip("<>").split("#")[0]
            if not target or re.match(r"[a-z]+:", target):
                continue
            assert (p.parent / target).is_file(), (p, target)
            links += 1
    tree = ET.parse(PACK / "existing-tests.xml").getroot()
    cases = tree.findall(".//testcase")
    failed = [c for c in cases if c.find("failure") is not None]
    skipped = [c for c in cases if c.find("skipped") is not None]
    assert len(cases) == 28 and len(failed) == 3 and len(skipped) == 3
    assert all("No module named 'sklearn'" in c.find("failure").get("message", "") for c in failed)
    assert all(
        "archive evidence unavailable" in c.find("skipped").get("message", "") for c in skipped
    )
    probe = load(PACK / "numeric-probe.json")
    fits = probe["ols_synthetic_controls"]
    assert math.isclose(fits["base"]["analysis_calculated_value_at_x8"], 17)
    assert math.isclose(fits["training_changed"]["analysis_calculated_value_at_x8"], 25)
    assert math.isclose(fits["heldout_only_changed"]["analysis_calculated_value_at_x8"], 17)
    prior = REPO / "docs/ops/evidence/independent_market_observation_v1_2026_11_06"
    prior_files = load(prior / "source-test-bindings-before.json")["files"]
    for item in prior_files:
        assert sha((REPO / item["path"]).read_bytes()) == item["sha256"]
    return {
        "assessment_integrity": "PASS",
        "next_model_implemented": False,
        "current_bound_sources": len(sources),
        "tracked_python_files_indexed": len(indexed),
        "checked_document_links": links,
        "historical_snapshots": 8,
        "existing_test_run": {
            "passed": 22,
            "failed_missing_sklearn": 3,
            "skipped_archive_unavailable": 3,
        },
        "numeric_probe": "PASS_BOUNDED_SYNTHETIC_AND_ORIGINAL_STORE_READ",
        "prior_source_test_config_files_unchanged": len(prior_files),
        "global_semantic_recertification": False,
        "runtime_authorization_effect": "NONE",
    }


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
