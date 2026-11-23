"""Validate and query the repository Atlas assignment and boundary registers."""

from __future__ import annotations

import argparse
from collections import Counter
import gzip
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
ATLAS = Path("docs/system_atlas")
SOURCE = ATLAS / "source"
VIEW = ATLAS / "generated/BOUNDARIES.md"
CORE_CATALOG = "src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/layer_catalog_v1.py"


def _load(root, name):
    return json.loads((root / SOURCE / name).read_bytes())


def _git(root, *args):
    return subprocess.check_output(["git", "--no-optional-locks", *args], cwd=root)


def _tree(root, revision):
    tree = {}
    for entry in _git(root, "ls-tree", "-rlz", revision).split(b"\0"):
        if entry:
            meta, name = entry.split(b"\t", 1)
            mode, kind, oid, size = meta.decode().split()
            if kind != "blob":
                raise ValueError(f"Unsupported Git artifact: {name!r} ({kind})")
            tree[name.decode()] = (mode, oid, int(size))
    return tree


def _unique(items, key):
    result = {}
    for item in items:
        name = item[key]
        if name in result:
            raise ValueError(f"Duplicate {key}: {name}")
        result[name] = item
    return result


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _validate_paths(rows, tree, domains, layers):
    for path, row in rows.items():
        canonical_path = Path(path)
        _require(
            not canonical_path.is_absolute()
            and ".." not in canonical_path.parts
            and canonical_path.as_posix() == path,
            f"Invalid assignment path: {path}",
        )
        _require(
            row["area"] in domains
            and row["role"]
            and row["basis"]
            and set(row.get("related_areas", [])) <= domains
            and row["area"] not in row.get("related_areas", []),
            f"Invalid assignment: {path}",
        )
        _require(set(row.get("layers", [])) <= layers, f"Unknown layer: {path}")
        if path.startswith("src/trading/master_v2/"):
            _require(row["area"] == "CORE", f"Master V2 artifact outside CORE: {path}")
        if path in tree:
            _require(
                (row.get("mode"), row.get("repo_blob")) == tree[path][:2],
                f"Git object mismatch: {path}",
            )
        else:
            _require(
                canonical_path.is_relative_to(ATLAS)
                and row["area"] == "ENG"
                and row["basis"] == "atlas_documentation"
                and "repo_blob" not in row,
                f"Assignment missing source tree binding: {path}",
            )


def _validate_boundaries(doc, model, tree):
    domains = {d["id"] for d in model["domains"]}
    inner = {d["id"] for d in model["domains"] if d["group"] == "Universen"}
    outer = domains - inner
    _require(
        doc["schema"] == "peaktrade.atlas_boundary_projection.v1"
        and doc["authority"] == doc["runtime_authorization_effect"] == "NONE"
        and set(doc["universes"]) == inner
        and doc["outer_group"] not in domains
        and not set(doc["cross_cutting"]) & domains,
        "Invalid Atlas boundary scope",
    )
    rubrics = [area for item in doc["outer_rubrics"] for area in item["domains"]]
    _require(
        set(rubrics) == outer and len(rubrics) == len(outer),
        "Outer rubrics must place each external domain exactly once",
    )
    ring = _unique(doc["ring_views"], "id")
    _require(set(ring) == {f"R{i:02}" for i in range(1, 9)}, "Incomplete outer-ring views")
    for name, item in ring.items():
        _require(set(item["domains"]) <= domains, f"Invalid scope in {name}")

    endpoints = domains | set(doc["cross_cutting"]) | {doc["outer_group"]}
    _require(not set(doc["endpoints"]) & endpoints, "Endpoint shadows an Atlas domain")
    route_endpoints = endpoints | set(doc["endpoints"])
    routes = _unique(doc["routes"] + doc["repo_contracts"], "id")
    for name, item in routes.items():
        _require(
            {item["from"], item["to"]} <= route_endpoints,
            f"Invalid route endpoints: {name}",
        )
        if item["status"] in {"offline_tested", "repo_contract"}:
            _require(
                {item["from"], item["to"]} <= endpoints
                and all(
                    item.get(field)
                    for field in ("producer", "payload", "state", "consumer", "effect")
                )
                and set(item["source_refs"]) <= tree.keys(),
                f"Incomplete repository contract: {name}",
            )
        else:
            _require(item["contract"], f"Missing documented contract: {name}")
            _require(
                set(item["current"].get("refs", ())) <= tree.keys(),
                f"Missing current source: {name}",
            )
    signals = _unique(doc["signals"], "id")
    _require(
        set(signals) == {f"E{i:02}" for i in range(1, 39)} | {f"O{i:02}" for i in range(1, 21)},
        "Incomplete system signal register",
    )
    for name, item in signals.items():
        incoming = name.startswith("E")
        prefix = "O" if incoming else "E"
        _require(
            item["direction"] == ("HINEIN" if incoming else "HINAUS")
            and bool(item["contract"])
            and bool(item["related_areas"])
            and set(item["related_areas"]) <= endpoints
            and all(
                other in signals and other.startswith(prefix) for other in item["counterparts"]
            ),
            f"Invalid signal direction or counterpart: {name}",
        )
    for item in doc["routes"] + doc["signals"]:
        for ref in item["source_refs"]:
            blob = tree.get(ref["path"], (None, None))[1]
            _require(ref["repo_blob"] == blob, f"Unbound boundary source: {ref['path']}")
            _require(
                (ref["repo_match"] == "missing") == (blob is None),
                f"Inconsistent boundary source status: {ref['path']}",
            )
    return routes, signals


def _obsidian_record(row):
    record = row.copy()
    record["blob"] = record.pop("repo_blob")
    return record


def _record_bytes(record):
    return (
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()


def _current_assignments(root, base, update, domains, layers):
    revision = update["repo_commit"]
    _require(
        len(revision) == 40 and all(c in "0123456789abcdef" for c in revision),
        "Invalid assignment commit",
    )
    snapshot = _tree(root, revision + "^{commit}")
    additions = _unique(update["additions"], "path")
    _require(not base.keys() & additions.keys(), "Assignment addition replaces a baseline path")
    _require(
        base.keys() | additions.keys() == snapshot.keys(),
        "Assignments differ from the bound Git tree",
    )
    _validate_paths(additions, snapshot, domains, layers)
    reviewed = update["reviewed_basis"]
    _require(
        reviewed.keys() <= base.keys() and all(reviewed.values()),
        "Invalid reviewed assignment basis",
    )

    rows = {}
    digest = sha256()
    for path in sorted(snapshot):
        source = base[path] if path in base else additions[path]
        mode, blob, size = snapshot[path]
        original = source.get("zuordnungsbasis_blob", source["repo_blob"])
        row = {
            **source,
            "basis": reviewed.get(path, source["basis"]),
            "mode": mode,
            "repo_blob": blob,
            "bytes": size,
            "revision": revision,
            "zuordnungsbasis_blob": original,
            "zuordnung_bytes": "identisch" if original == blob else "geaendert",
        }
        rows[path] = row
        digest.update(_record_bytes(_obsidian_record(row)))
    _require(
        digest.hexdigest() == update["records_sha256"],
        "Current assignment digest differs from Obsidian",
    )
    return rows


def compare_obsidian(rows, register):
    raw = register.read_bytes()
    obsidian = _unique((json.loads(line) for line in raw.splitlines()), "path")
    _require(rows.keys() == obsidian.keys(), "Repo and Obsidian assignment paths differ")
    for path, row in rows.items():
        _require(
            _record_bytes(_obsidian_record(row)) == _record_bytes(obsidian[path]),
            f"Obsidian assignment differs: {path}",
        )
    return {
        "obsidian_matching_records": len(rows),
        "obsidian_register_sha256": sha256(raw).hexdigest(),
    }


def load_coverage(root, model, *, strict=False):
    manifest = _load(root, "artifact-assignments.json")
    doc = _load(root, "boundaries.json")
    _require(
        manifest["schema"] == "peaktrade.atlas_artifact_assignments.v1"
        and manifest["authority"] == "NONE"
        and manifest["repo_commit"] == doc["reviewed_repo_commit"]
        and manifest["obsidian_commit"] == doc["obsidian_baseline"],
        "Mismatched Atlas register provenance",
    )
    tree = _tree(root, manifest["repo_commit"])
    _require(
        _git(root, "rev-parse", manifest["repo_commit"] + "^{tree}").decode().strip()
        == manifest["repo_tree"],
        "Atlas repository tree mismatch",
    )
    raw = gzip.decompress((root / SOURCE / "artifact-assignments.jsonl.gz").read_bytes())
    _require(sha256(raw).hexdigest() == manifest["sha256"], "Assignment digest mismatch")
    rows = _unique((json.loads(line) for line in raw.splitlines()), "path")
    _require(tree.keys() <= rows.keys(), "Missing assignments in the bound repository tree")
    _require(
        len(rows) == manifest["artifact_count"]
        and len(tree) == manifest["repo_artifact_count"]
        and Counter(row["area"] for row in rows.values()) == manifest["by_area"]
        and Counter(row["basis"] for row in rows.values()) == manifest["by_basis"],
        "Assignment totals differ from the manifest",
    )
    domains = {d["id"] for d in model["domains"]} | set(doc["cross_cutting"])
    layers = {
        f"{d['id']}-FG{i:02}" for d in model["domains"] for i, _ in enumerate(d["layers"], 1)
    } | {f"CORE-L{i}" for i in range(1, 11)}
    _validate_paths(rows, tree, domains, layers)
    routes, signals = _validate_boundaries(doc, model, tree)
    binding_path = root / SOURCE / "development-binding-v1.json"
    revision = manifest["repo_commit"]
    if binding_path.is_file():
        binding = json.loads(binding_path.read_bytes())
        update = binding.get("artifact_assignments")
        if update is not None:
            rows = _current_assignments(root, rows, update, domains, layers)
            revision = update["repo_commit"]
        if "reviewed_file_connections" in binding:
            bundle = binding["reviewed_file_connections"]
            _validate_file_connections(root, bundle)
            doc["reviewed_file_connections"] = bundle
    current = set(
        _git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
        .decode()
        .split("\0")
    )
    current.discard("")
    missing = sorted(current - rows.keys())
    extra = sorted(rows.keys() - current)
    if strict:
        _require(
            not missing and not extra, f"Checkout coverage drift: missing={missing}, stale={extra}"
        )
    counts = {
        "atlas_assignment_revision": revision,
        "atlas_baseline_assigned_paths": manifest["artifact_count"],
        "atlas_assigned_paths": len(rows),
        "atlas_checkout_missing_paths": len(missing),
        "atlas_checkout_stale_paths": len(extra),
        "atlas_boundary_records": len(routes),
        "atlas_signal_records": len(signals),
        "atlas_open_boundary_addresses": sum(
            row["status"] == "endpoint_open" for row in routes.values()
        ),
    }
    if "reviewed_file_connections" in doc:
        evidence = doc["reviewed_file_connections"]["evidence"]
        counts["atlas_file_connection_revision"] = evidence["revision"]
        counts["atlas_file_connections_by_category"] = Counter(
            edge["category"] for edge in evidence["connections"]
        )
    return doc, rows, routes, signals, counts


def _validate_file_connections(root, bundle):
    evidence = bundle["evidence"]
    raw = (json.dumps(evidence, indent=2, ensure_ascii=False) + "\n").encode()
    _require(
        sha256(raw).hexdigest() == bundle["obsidian_sha256"], "File connection digest mismatch"
    )
    revision = evidence["revision"]
    _require(
        len(revision) == 40 and all(c in "0123456789abcdef" for c in revision),
        "Invalid file connection revision",
    )
    _require(
        evidence["runtime_authorization_effect"] == "NONE"
        and _git(root, "rev-parse", revision + "^1").decode().strip() == evidence["base_revision"],
        "File connection provenance mismatch",
    )
    connections = evidence["connections"]
    pairs = {(edge["source"], edge["target"]) for edge in connections}
    _require(pairs and len(pairs) == len(connections), "Missing or duplicate file connection")
    targets = {target for _, target in pairs}
    found = _git(root, "ls-tree", "-r", "--name-only", "-z", revision, "--", *sorted(targets))
    _require(set(found.decode().split("\0")[:-1]) == targets, "Unknown file connection target")
    sources = {}
    for edge in connections:
        source = edge["source"]
        _require(
            edge["category"] in {"Dateizugriff", "Dokumentlink", "Katalogprüfung"}
            and edge["sites"],
            f"Missing file connection classification or evidence: {source}",
        )
        if source not in sources:
            sources[source] = _git(root, "show", f"{revision}:{source}").decode().splitlines()
        lines = sources[source]
        for site in edge["sites"]:
            first, last = site["line"], site["end_line"]
            _require(
                1 <= first <= last <= len(lines)
                and "\n".join(lines[first - 1 : last]) == site["source_excerpt"],
                f"File connection source differs: {revision}:{source}:{first}-{last}",
            )


def _link(path, label=None):
    return f"[{label or Path(path).name}](../../../{quote(path, safe='/')})"


def _area_boundaries(addresses, routes):
    return {
        "incoming": [
            item for item in routes if item["to"] in addresses and item["from"] not in addresses
        ],
        "outgoing": [
            item for item in routes if item["from"] in addresses and item["to"] not in addresses
        ],
        "internal": [item for item in routes if {item["from"], item["to"]} <= addresses],
    }


def render_boundaries(doc, rows, model):
    domains = {d["id"]: d for d in model["domains"]}
    counts = Counter(row["area"] for row in rows.values())
    lines = [
        "# Fachbereiche, Außenkanten und Dateizuordnung",
        "",
        f"Stand der Außenkanten `{doc['reviewed_repo_commit']}` · Obsidian-Basis `{doc['obsidian_baseline']}`.",
        f"Dateizuordnung für {len(rows):,} Pfade am Repo-Stand `{next(iter(rows.values())).get('revision', doc['reviewed_repo_commit'])}`.".replace(
            ",", "."
        ),
        "Die Karte führt die Außenstruktur des Obsidian-Registers und die Fachowner aus dem Repo zusammen.",
        "Die Zuordnung hat Autorität NONE. Dokumentierte, historische, offene und offline ausgeführte Kanten behalten ihren Belegstatus.",
        "",
        "## Universen und Außengliederung",
        "",
        "- Universen: " + ", ".join(doc["universes"]) + ".",
        "- Querschnitt: META. Seine Meta-Analyse liefert Forschungsrückgaben an die vertraglich gebundenen Empfänger.",
        "- Außenring: gemeinsame fachliche Sicht mit eigenen Zuständigkeiten je Bereich.",
        "",
    ]
    lines += [f"- **{r['name']}** · {', '.join(r['domains'])}." for r in doc["outer_rubrics"]]
    lines += ["", "## Acht überlappende Außenringsichten", ""]
    for item in doc["ring_views"]:
        lines.extend(
            [
                f"### {item['id']} · {item['name']}",
                "",
                item["purpose"],
                "",
                item["boundary"],
                "",
                f"Bereiche {', '.join(item['domains'])}.",
                "",
                item["open"],
                "",
            ]
        )
    lines += ["## Innere Ebenen aus den Repo-Verträgen", ""]
    lines += [
        "Die Funktionsgruppen verwenden die vorhandenen Atlas-Quellen. "
        "Die native Core-Reihenfolge und ihre Consumer stehen im "
        + _link(CORE_CATALOG, "Core-L1–L10-Katalog")
        + ".",
        "",
    ]
    for area, domain in domains.items():
        lines.extend(
            [f"### {area} · {domain['name']}", "", f"{counts[area]} zugeordnete Dateien.", ""]
        )
        for i, layer in enumerate(domain["layers"], 1):
            source = layer["source"]
            reference = _link(source) if source in rows else f"Modulfamilie {Path(source).name}"
            lines.append(f"- {area}-FG{i:02} · {layer['name']} · {reference}.")
        boundaries = _area_boundaries({area}, doc["routes"] + doc["repo_contracts"])
        for label, side in (
            ("Eingehende Übergaben", "incoming"),
            ("Ausgehende Übergaben", "outgoing"),
        ):
            if boundaries[side]:
                lines.extend(
                    ["", f"{label}: " + ", ".join(row["id"] for row in boundaries[side]) + "."]
                )
        lines.append("")
    lines += [
        "## Systemsignale in beide Richtungen",
        "",
        "Netz, Datei, Prozess und interne Fachgrenzen besitzen eigene Klassen. Gegenrichtungen behalten die Beziehungen der Originalnotizen.",
        "",
    ]
    for direction, label in (("HINEIN", "Eingänge"), ("HINAUS", "Ausgänge")):
        lines.extend([f"### {label}", ""])
        for item in sorted(doc["signals"], key=lambda row: row["id"]):
            if item["direction"] == direction:
                peers = (
                    " · Gegenrichtung " + ", ".join(item["counterparts"])
                    if item["counterparts"]
                    else ""
                )
                lines.append(f"- {item['id']} · {item['name']} · {item['boundary_class']}{peers}.")
        lines.append("")
    lines += ["## Aktuelle Repo-Verträge", ""]
    for edge in doc["repo_contracts"]:
        links = " · ".join(_link(path) for path in edge["source_refs"])
        lines.extend(
            [
                f"### {edge['from']} → {edge['to']} · {edge['title']}",
                "",
                "Offline ausgeführt."
                if edge["status"] == "offline_tested"
                else "Am Repo-Vertrag abgeglichen.",
                "",
                f"{edge['producer']} {edge['consumer']}",
                "",
                f"{edge['payload']} {edge['state']}",
                "",
                f"{edge['effect']} {links}",
                "",
            ]
        )
    lines += [
        "## Vollständige Register",
        "",
        "- [Übergaben und Signalverträge](../source/boundaries.json) mit ursprünglichen Adressen, "
        "Richtung, Nutzdaten, Zustand, Verbrauch, Beleggrenze und Repo-Quellen. "
        "Die direkte M4/M5-Aufnahme zu Governance ist seit #7240 als historischer Pfad markiert.",
        "- [Ursprüngliche Dateizuordnungen](../source/artifact-assignments.jsonl.gz), [Manifest](../source/artifact-assignments.json) und [nachgeführte Zuordnungen im Entwicklungsbeleg](../source/development-binding-v1.json).",
        "- Abfragen und strikte Prüfung stehen in der [Atlas-Anleitung](../README.md).",
        "",
    ]
    if "reviewed_file_connections" in doc:
        evidence = doc["reviewed_file_connections"]["evidence"]
        lines.extend(
            [
                "## Gerichtete Dateiverbindungen nach Belegart",
                "",
                f"Die Zeilen beziehen sich auf den Quellstand `{evidence['revision']}`. "
                "Der Pfeil führt von der verweisenden Datei zum Ziel.",
                "",
            ]
        )
        for category in ("Dateizugriff", "Dokumentlink", "Katalogprüfung"):
            lines.extend([f"### {category}", ""])
            for edge in evidence["connections"]:
                if edge["category"] != category:
                    continue
                lines.append(f"- `{edge['source']}` → `{edge['target']}`")
                for site in edge["sites"]:
                    first, last = site["line"], site["end_line"]
                    span = str(first) if first == last else f"{first}–{last}"
                    lines.append(f"  - Z. {span} · **{site['label']}**. {site['detail']}")
            lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("check", "path", "area", "edge"))
    parser.add_argument("key", nargs="?")
    parser.add_argument(
        "--obsidian-register",
        type=Path,
        help="Compare every field with the supplied Obsidian JSONL catalog.",
    )
    parser.add_argument(
        "--obsidian-connections", type=Path, help="Compare the reviewed Obsidian connections JSON."
    )
    args = parser.parse_args()
    if (args.mode == "check") != (args.key is None):
        parser.error("path, area and edge each require a key")
    if (args.obsidian_register or args.obsidian_connections) and args.mode != "check":
        parser.error("Obsidian comparisons require check")
    model = _load(ROOT, "current-model.json")
    doc, rows, routes, signals, counts = load_coverage(ROOT, model, strict=args.mode == "check")
    if args.mode == "check":
        result = counts
        if args.obsidian_register is not None:
            result.update(compare_obsidian(rows, args.obsidian_register))
        if args.obsidian_connections is not None:
            digest = sha256(args.obsidian_connections.read_bytes()).hexdigest()
            bundle = doc.get("reviewed_file_connections")
            _require(
                bundle and digest == bundle["obsidian_sha256"], "Obsidian file connections differ"
            )
            result["obsidian_file_connections_sha256"] = digest
    elif args.mode == "path":
        result = rows[args.key]
    elif args.mode == "edge":
        result = (routes | signals)[args.key]
    else:
        area = next((d for d in model["domains"] if d["id"] == args.key), None)
        if area is None and args.key not in {*doc["cross_cutting"], doc["outer_group"]}:
            parser.error(f"Unknown area: {args.key}")
        addresses = {args.key}
        if args.key == doc["outer_group"]:
            addresses.update(area for rubric in doc["outer_rubrics"] for area in rubric["domains"])
        result = {
            "domain": area,
            **_area_boundaries(addresses, routes.values()),
            "signals": [
                item for item in signals.values() if addresses.intersection(item["related_areas"])
            ],
            "artifacts": [row for row in rows.values() if row["area"] in addresses],
        }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
