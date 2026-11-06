"""Read-only verification of this bounded evidence package and its active views.

Run with scripts/pt from the bound repository. This does not train, infer,
activate a host, inspect external disks or certify the whole system.
"""

from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote
import xml.etree.ElementTree as ET

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    market_ols_next_forecast_v1 as learner,
)


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[3]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def compressed(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def inventory():
    return {
        str(p.relative_to(PACKAGE)): sha(p.read_bytes())
        for p in sorted(PACKAGE.rglob("*"))
        if p.is_file() and p.name not in {"manifest.json", "lease"} and "__pycache__" not in p.parts
    }


def links(text):
    wiki = set(re.findall(r"\[\[([^\]\n]+)\]\]", text))
    markdown = set(re.findall(r"\[[^\]\n]*\]\((<[^>\n]+>|[^)\n]+)\)", text))
    return wiki, markdown


def check_links(new, old, base, vault=None):
    new_wiki, new_md = links(new)
    old_wiki, old_md = links(old)
    checked = 0
    for target in new_md - old_md:
        target = unquote(target.strip("<>"))
        if "://" in target or target.startswith("#"):
            continue
        path = Path(target.split("#", 1)[0])
        path = path if path.is_absolute() else base / path
        assert path.exists(), ("BROKEN_MARKDOWN_LINK", path)
        checked += 1
    for target in new_wiki - old_wiki:
        assert vault is not None, ("WIKI_WITHOUT_VAULT", target)
        target = target.split("|", 1)[0].split("#", 1)[0]
        if not target:
            continue
        candidates = [vault / target, base / target]
        candidates += [Path(str(p) + ".md") for p in candidates]
        assert any(p.is_file() for p in candidates), ("BROKEN_WIKI_LINK", target)
        checked += 1
    return checked


def canvas_text(canvas):
    return "\n".join(n.get("text", "") for n in canvas["nodes"])


def check_canvas(before, after, vault):
    nodes = after["nodes"]
    ids = [n["id"] for n in nodes]
    assert len(ids) == len(set(ids))
    assert ids == [n["id"] for n in before["nodes"]]
    assert after["edges"] == before["edges"]
    for edge in after["edges"]:
        assert edge["fromNode"] in ids and edge["toNode"] in ids
    for previous, current in zip(before["nodes"], nodes):
        for key in ("x", "y", "width", "height"):
            assert current[key] == previous[key]
        if current["type"] == "file":
            assert (vault / current["file"]).is_file()
    for i, a in enumerate(nodes):
        for b in nodes[i + 1 :]:
            overlap = min(a["x"] + a["width"], b["x"] + b["width"]) > max(a["x"], b["x"]) and min(
                a["y"] + a["height"], b["y"] + b["height"]
            ) > max(a["y"], b["y"])
            assert not overlap, ("OVERLAPPING_CANVAS_NODES", a["id"], b["id"])


def verify():
    manifest = load(PACKAGE / "manifest.json")
    assert manifest["files"] == inventory(), "PACKAGE_INVENTORY_MISMATCH"
    for name, expected in manifest["repository_documents"].items():
        assert sha((REPO / name).read_bytes()) == expected, name

    before = compressed(PACKAGE / "source-bindings-before.json.gz")
    after = compressed(PACKAGE / "source-bindings-after.json.gz")
    assert before == after
    sources = before["files"]
    assert len(sources) == len({r["path"] for r in sources}) == 11360
    for row in sources:
        assert sha((REPO / row["path"]).read_bytes()) == row["sha256"], row["path"]

    cases = ET.parse(PACKAGE / "connected-final.xml").findall(".//testcase")
    identities = {(c.get("classname"), c.get("name")) for c in cases}
    assert len(cases) == len(identities) == 798
    assert not any(
        c.find(tag) is not None for c in cases for tag in ("failure", "error", "skipped")
    )
    assert sum("test_market_ols_next_forecast_v1" in c.get("classname", "") for c in cases) == 11

    witness = load(PACKAGE / "example/witness.json")
    models = PACKAGE / "example/models"
    store = PACKAGE / "example/next-mi"
    first = learner.read_market_ols_model_v1(
        model_store_root=models, model_ref=witness["model_v1_ref"]
    )
    child = learner.read_market_ols_model_v1(
        model_store_root=models, model_ref=witness["model_v2_ref"]
    )
    assert first["model_version"] == 1 and child["model_version"] == 2
    assert child["request"]["parent_model_ref"] == first["model_ref"]
    for model, prefix in ((first, "v1"), (child, "v2")):
        assert model["coefficients"] == witness[prefix + "_coefficients"]
        assert model["validation"] == witness[prefix + "_validation"]
    assert any(
        s["job_key"] == witness["first_computed_forecast"]["frozen"]["job_key"]
        for s in child["request"]["samples"]
    )
    for name in ("first_computed_forecast", "child_forecast"):
        expected = witness[name]
        actual = learner.read_market_model_forecast_v1(
            model_store_root=models, store_root=store, job_key=expected["frozen"]["job_key"]
        )
        assert actual == expected
    common = witness["same_future_context"]
    assert common["features"] == {"mark": 114.0}
    assert common["parent_payload"]["mean_return"] == 0.0024985714285711332
    assert common["child_payload"]["mean_return"] == 0.02114303030303022
    assert common["child_payload"] == witness["child_forecast"]["provider"]["computed_payload"]
    assert witness["natural_source_quality_proven"] is False
    assert witness["double_play_benefit_proven"] is False
    assert witness["continuous_host_or_five_lane_runtime_activated"] is False

    changes = load(PACKAGE / "vault-changes.json")
    vault = Path(changes["vault"])
    changed = {r["path"]: r for r in changes["changes"]}
    link_count = check_links((PACKAGE / "README.md").read_text(), "", PACKAGE)
    for row in changes["changes"]:
        current = (vault / row["path"]).read_bytes()
        saved = (PACKAGE / row["snapshot"]).read_bytes()
        assert current == saved and sha(saved) == row["sha256"], row["path"]
        previous = b""
        if row["before_snapshot"] is not None:
            previous = (PACKAGE / row["before_snapshot"]).read_bytes()
            assert sha(previous) == row["before_sha256"]
        if row["path"].endswith(".canvas"):
            old_canvas, new_canvas = json.loads(previous), json.loads(saved)
            check_canvas(old_canvas, new_canvas, vault)
            old_text, new_text = canvas_text(old_canvas), canvas_text(new_canvas)
        else:
            old_text, new_text = previous.decode(), saved.decode()
        link_count += check_links(new_text, old_text, (vault / row["path"]).parent, vault)

    for row in changes["bindings"]:
        old_bytes = gzip.decompress((PACKAGE / row["before_snapshot"]).read_bytes())
        new_bytes = gzip.decompress((PACKAGE / row["snapshot"]).read_bytes())
        assert sha(old_bytes) == row["before_sha256"]
        assert sha(new_bytes) == row["sha256"]
        assert (vault / row["path"]).read_bytes() == new_bytes
        old, new = json.loads(old_bytes), json.loads(new_bytes)
        overlay = new.pop("independent_market_ols_next_forecast_v1")
        assert overlay["global_semantic_recertified"] is False
        assert overlay["runtime_authorization_effect"] == "NONE"
        expected = deepcopy(old)
        for item in expected["generated_files"]:
            if item["path"] in changed:
                item["sha256"] = changed[item["path"]]["sha256"]
        assert new == expected, ("HISTORICAL_BINDING_CHANGED", row["path"])

    goals = load(PACKAGE / "operating-goal-clarification.json")
    for row in goals["references"]:
        assert sha((REPO / row["path"]).read_bytes()) == row["sha256"]
    archive = load(PACKAGE / "next-archive-request.json")
    assert archive["archive_or_git_history_mutation_executed"] is False
    return {
        "result": "PASS",
        "package_files": len(manifest["files"]),
        "unchanged_bound_source_test_config_files": len(sources),
        "distinct_passed_testcases": len(cases),
        "new_testcases": 11,
        "cold_model_versions": 2,
        "cold_provider_receipts": 2,
        "active_vault_views": len(changes["changes"]),
        "preserved_historical_bindings_with_scoped_overlay": len(changes["bindings"]),
        "checked_added_local_links": link_count,
        "quality_or_whole_system_readiness_proven": False,
        "runtime_authorization_effect": "NONE",
    }


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
