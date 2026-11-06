"""Read-only verification of the bound independent-market implementation evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

PACK = Path(__file__).resolve().parent
REPO = PACK.parents[3]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load(name: str):
    return json.loads((PACK / name).read_text())


def verify() -> dict:
    binding = load("source-test-bindings-before.json")
    for item in binding["files"]:
        assert sha((REPO / item["path"]).read_bytes()) == item["sha256"], item["path"]
    for item in load("source-changes.json")["files"]:
        assert sha((REPO / item["path"]).read_bytes()) == item["after_sha256"]
    tree = ET.parse(PACK / "connected-final.xml").getroot()
    cases = tree.findall(".//testcase")
    assert not tree.findall(".//failure") + tree.findall(".//error") + tree.findall(".//skipped")
    assert len(cases) == len({(c.get("classname"), c.get("name")) for c in cases}) == 787
    result = load("test-result.json")
    assert (
        result["distinct_testcases"] == len(cases) and result["new_independent_market_cases"] == 40
    )
    witness = load("example/witness.json")
    for item in witness["store_files"]:
        assert sha((PACK / item["path"]).read_bytes()) == item["sha256"]
    assert witness["original_triad_exact_digest"] == witness["readback_original_triad_exact_digest"]
    assert witness["canonical_measurement_equals_preserved_original"] is True
    assert not {"decision_event_ref", "lane_id", "epoch"} & set(witness["job_key"])
    roots = {
        "system": Path("/Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL"),
        "plan": Path("/Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEMPLAN"),
    }
    for item in load("vault-changes.json")["changes"]:
        assert sha((roots[item["vault"]] / item["path"]).read_bytes()) == item["after_sha256"]
        if item["backup"]:
            assert sha((PACK / item["backup"]).read_bytes()) == item["before_sha256"]
    view = load("obsidian-view.json")
    assert sha(view["text"].encode()) == view["sha256"]
    assert (roots["system"] / view["path"]).read_text() == view["text"]
    if (PACK / "manifest.json").exists():
        manifest = load("manifest.json")
        actual = {
            str(p.relative_to(PACK))
            for p in PACK.rglob("*")
            if p.is_file() and p.name != "manifest.json" and "__pycache__" not in p.parts
        }
        assert actual == {item["path"] for item in manifest["files"]}
        for item in manifest["files"]:
            assert sha((PACK / item["path"]).read_bytes()) == item["sha256"]
        for item in manifest["external_documents"]:
            assert sha((REPO / item["path"]).read_bytes()) == item["sha256"]
    return {
        "result": "PASS",
        "scope": "BOUNDED_OFFLINE_RETURN_PATH_AND_EXACT_EVIDENCE_BINDING",
        "distinct_passed_cases": len(cases),
        "new_cases": 40,
        "source_test_config_bindings": len(binding["files"]),
        "original_store_json_files": len(witness["store_files"]),
        "point1_bounded_offline_path_implemented": True,
        "point2_next_model_learning_implemented": False,
        "natural_source_quality_proven": False,
        "runtime_activation": False,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
