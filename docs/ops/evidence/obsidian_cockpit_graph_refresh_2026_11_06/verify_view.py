"""Read-only integrity check for the dated Obsidian entry-view refresh."""

from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET

PACK = Path(__file__).resolve().parent
REPO = PACK.parents[3]
VAULT = Path("/Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def verify():
    manifest = load(PACK / "manifest.json")
    actual = {
        str(p.relative_to(PACK))
        for p in PACK.rglob("*")
        if p.is_file() and p.name != "manifest.json" and "__pycache__" not in p.parts
    }
    assert actual == {item["path"] for item in manifest["files"]}
    for item in manifest["files"]:
        assert sha(PACK / item["path"]) == item["sha256"], item["path"]
    for item in manifest["reused_product_evidence"]:
        assert sha(REPO / item["path"]) == item["sha256"], item["path"]
    links = 0
    canvas_counts = {}
    for item in manifest["vault_files"]:
        active = VAULT / item["path"]
        archived = PACK / item["snapshot"]
        assert sha(active) == sha(archived) == item["sha256"], item["path"]
        if active.suffix == ".canvas":
            data = load(active)
            before = load(PACK / "before" / item["path"])
            nodes = {n["id"]: n for n in data["nodes"]}
            assert len(nodes) == len(data["nodes"])
            assert {n["id"] for n in before["nodes"]} <= set(nodes)
            assert {e["id"] for e in before["edges"]} <= {e["id"] for e in data["edges"]}
            for edge in data["edges"]:
                assert edge["fromNode"] in nodes and edge["toNode"] in nodes
            for index, node in enumerate(data["nodes"]):
                if node["type"] == "file":
                    assert (VAULT / node["file"]).is_file(), node["file"]
                    links += 1
                for other in data["nodes"][index + 1 :]:
                    intersects = max(node["x"], other["x"]) < min(
                        node["x"] + node["width"], other["x"] + other["width"]
                    ) and max(node["y"], other["y"]) < min(
                        node["y"] + node["height"], other["y"] + other["height"]
                    )
                    assert not intersects, (active.name, node["id"], other["id"])
            texts = [n.get("text", "") for n in data["nodes"]]
            canvas_counts[item["path"]] = {
                "nodes": len(nodes),
                "edges": len(data["edges"]),
                "file_cards": sum(n["type"] == "file" for n in nodes.values()),
            }
        elif active.suffix == ".md":
            texts = [active.read_text()]
        else:
            continue
        for text in texts:
            for raw in re.findall(r"\[\[([^\]]+)\]\]", text):
                target = raw.split("|")[0].split("#")[0]
                if not target:
                    continue
                candidates = [
                    VAULT / target,
                    VAULT / (target + ".md"),
                    VAULT / (target + ".canvas"),
                ]
                assert any(p.is_file() for p in candidates), (active.name, raw)
                links += 1
    changed_views = {
        item["path"]
        for item in manifest["vault_files"]
        if item["path"].endswith((".md", ".canvas"))
    }
    for name in ["Systemindexbindung.json", "Systematlasbindung.json", "Ansichtsbindung.json"]:
        before = load(PACK / "before" / name)
        after = load(VAULT / name)
        overlay = after.pop("cockpit_and_galaxy_view_refresh")
        assert overlay["global_semantic_or_runtime_recertified"] is False
        assert overlay["runtime_authorization_effect"] == "NONE"
        old_generated = before.pop("generated_files")
        new_generated = after.pop("generated_files")
        assert before == after, name
        assert len(old_generated) == len(new_generated)
        for old, new in zip(old_generated, new_generated):
            assert old["path"] == new["path"]
            if new["path"] in changed_views:
                assert new["sha256"] == sha(VAULT / new["path"])
            else:
                assert old == new
    prior = REPO / "docs/ops/evidence/independent_market_observation_v1_2026_11_06"
    bindings = load(prior / "source-test-bindings-before.json")["files"]
    for item in bindings:
        assert sha(REPO / item["path"]) == item["sha256"], item["path"]
    tree = ET.parse(prior / "connected-final.xml").getroot()
    cases = tree.findall(".//testcase")
    assert len(cases) == len({(c.get("classname"), c.get("name")) for c in cases}) == 787
    assert not tree.findall(".//failure") + tree.findall(".//error") + tree.findall(".//skipped")
    settings = load(VAULT / ".obsidian/plugins/galaxy-view/data.json")
    captured = load(PACK / "galaxy-settings.json")
    assert {k: v for k, v in settings.items() if k != "positionCache"} == captured
    assert set(captured["hiddenFolders"]) == {
        "06 Komponenten",
        "07 Verbindungen",
        "08 Register",
        "09 Werte",
    }
    assert load(VAULT / ".obsidian/plugins/galaxy-view/manifest.json")["version"] == "0.6.1"
    assert "galaxy-view" in load(VAULT / ".obsidian/community-plugins.json")
    return {
        "result": "PASS",
        "scope": "ENTRY_VIEWS_LINKS_GEOMETRY_BINDING_PRESERVATION_AND_PRIOR_PASS_REUSE",
        "vault_files": len(manifest["vault_files"]),
        "resolved_local_links_and_file_cards": links,
        "canvases": canvas_counts,
        "prior_source_test_config_hashes_verified": len(bindings),
        "prior_distinct_passes_reused": len(cases),
        "new_product_test_run": False,
        "global_semantic_recertification": False,
        "runtime_authorization_effect": "NONE",
    }


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
