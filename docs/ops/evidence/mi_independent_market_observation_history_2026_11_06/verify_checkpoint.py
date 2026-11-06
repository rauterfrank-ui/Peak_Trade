"""Read-only verification of the historical Point-1 contract checkpoint."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


PACK = Path(__file__).resolve().parent
REPO = PACK.parents[3]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load(name: str):
    return json.loads((PACK / name).read_text())


def verify() -> dict:
    history = load("historical-sources.json")
    for source in history:
        raw = (PACK / source["snapshot"]).read_bytes()
        assert sha(raw) == source["sha256"], source["path"]
        reference = source["commit"] + ":" + source["path"]
        assert subprocess.check_output(["git", "show", reference], cwd=REPO) == raw
        blob = subprocess.check_output(["git", "rev-parse", reference], cwd=REPO, text=True)
        assert blob.strip() == source["git_blob"]
    for source in load("current-sources.json"):
        assert sha((REPO / source["path"]).read_bytes()) == source["sha256"], source["path"]
    equivalence = load("historical-blob-equivalence.json")
    assert len(set(equivalence["blobs"].values())) == 1
    for revision, expected in equivalence["blobs"].items():
        actual = subprocess.check_output(
            ["git", "rev-parse", revision + ":" + equivalence["path"]], cwd=REPO, text=True
        )
        assert actual.strip() == expected
    expected_merges = {
        6207: "2c67dd736216151b7bc1f70acaaff515e17b56ea",
        6626: "31f869272982385fb9afecdfe98b6895b18729e1",
        6627: "5320a087f4c4d58a54b9710ac663bb9cd355bcea",
        6628: "3279f991e155a5fc0a31df521ab72e5edc279778",
        6847: "32171b35e631cab767dca4f5fcd99b8a837caf23",
    }
    for number, expected in expected_merges.items():
        pr = load(f"pr-{number}.json")
        assert pr["merged"] is True and pr["merge_commit_sha"] == expected
    probes = load("consumer-probes.json")
    assert len(probes["cases"]) == 8 and probes["original_capsule_unchanged"] is True
    assert probes["product_writes_performed"] is False
    assert probes["cases"]["no_observation"]["evaluability"] == "NOT_EVALUABLE"
    assert probes["cases"]["original_measurement_record"]["decision_field_present"] is False
    for change in load("vault-changes.json")["changes"]:
        root = Path("/Users/frnkhrz/Desktop") / (
            "PEAK_TRADE_SYSTEM_AKTUELL" if change["vault"] == "system" else "PEAK_TRADE_SYSTEMPLAN"
        )
        assert sha((root / change["path"]).read_bytes()) == change["after_sha256"]
        if change["backup"]:
            assert sha((PACK / change["backup"]).read_bytes()) == change["before_sha256"]
    view = load("obsidian-view.json")
    assert sha(view["text"].encode()) == view["sha256"]
    assert sha((Path(view["vault"]) / view["path"]).read_bytes()) == view["sha256"]
    navigation = load("repository-navigation-change.json")
    assert sha((REPO / navigation["path"]).read_bytes()) == navigation["after_sha256"]
    assert sha((PACK / navigation["backup"]).read_bytes()) == navigation["before_sha256"]
    for root in ("src", "tests", "config", "scripts", "docs/runbooks/canonical"):
        diff = subprocess.check_output(["git", "diff", "907afde6c", "--", root], cwd=REPO)
        assert not diff, root
    if (PACK / "manifest.json").exists():
        for item in load("manifest.json")["files"]:
            assert sha((PACK / item["path"]).read_bytes()) == item["sha256"], item["path"]
    return {
        "result": "PASS",
        "scope": "HISTORICAL_PROVENANCE_CURRENT_CONTRACT_PROBES_AND_VIEW_PRESERVATION",
        "historical_sources_verified": len(history),
        "current_sources_verified": len(load("current-sources.json")),
        "pr_merge_bindings_verified": len(expected_merges),
        "recorded_stateless_consumer_cases": 8,
        "historical_runtime_reexecuted": False,
        "product_code_changed": False,
        "independent_end_to_end_measurement_implemented": False,
        "global_semantic_recertified": False,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
