"""Project current repository documentation into the existing external Obsidian vault."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VAULT = Path("/Users/frnkhrz/PEAK_TRADE_SYSTEM_AKTUELL")
PREFIX = "00 Systemindex/Aktueller Repo-Stand"
RECEIPT = ".belege/Aktueller Repo-Abgleich 2026-11-06.json"
PROFILE = Path("/Users/frnkhrz/.codex/AGENTS.md")
LAW_ROOT = "docs/governance/current_law_impact_map_v1/generated/"
MIRRORS = {
    "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md": PREFIX + "/Master Runbook.md",
    "docs/system_atlas/generated/SYSTEM_ATLAS.md": PREFIX + "/System Atlas.md",
    "docs/system_atlas/generated/SOURCE_INDEX.md": PREFIX + "/Quellenindex.md",
    "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md": PREFIX + "/Map of Truth.md",
    LAW_ROOT + "LAW_CHANGE_IMPACT.md": PREFIX + "/Law Impact Map.md",
    LAW_ROOT + "law_reference_index_v1.md": PREFIX + "/Regelquellen.md",
    LAW_ROOT + "semantic_object_index_v1.md": PREFIX + "/Fachvertraege.md",
    LAW_ROOT + "surface_census_v1.md": PREFIX + "/Policy-Dateien.md",
    LAW_ROOT + "unknown_and_conflict_v1.md": PREFIX + "/Offene Regelbeziehungen.md",
}
MARKER = re.compile(
    r"\n<!-- current-repo-projection:start -->.*?<!-- current-repo-projection:end -->\n", re.S
)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def json_content_digest(raw: bytes) -> str:
    """Bind every JSON value while allowing Obsidian to change serialization."""
    return digest(
        json.dumps(
            json.loads(raw), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    )


def verify_generated_file(raw: bytes, item: dict) -> bool:
    """Return whether only canvas serialization changed; reject content edits."""
    if digest(raw) == item["sha256"]:
        return False
    if item["path"].endswith(".canvas") and item.get("json_sha256"):
        if json_content_digest(raw) == item["json_sha256"]:
            return True
    raise ValueError("PROJECTION_CONTENT_CHANGED:" + item["path"])


def wiki(path: str, label: str | None = None) -> str:
    target = path.removesuffix(".md")
    return "[[" + target + ("|" + label if label else "") + "]]"


def note_header(title: str) -> str:
    return (
        "---\ntitle: "
        + json.dumps(title, ensure_ascii=False)
        + "\nstand: 2026-11-06\nrolle: Abgeleitete Repo-Ansicht\nauthoritaet: NONE\n---\n\n"
    )


def slug(heading: str) -> str:
    return re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")


def mirror_links(body: str, source: Path) -> str:
    def replace(match):
        label, target = match.groups()
        target = target.strip("<>")
        if "://" in target or target.startswith("#"):
            return match.group(0)
        path, _, fragment = target.partition("#")
        resolved = (source.parent / unquote(path)).resolve()
        try:
            rel = resolved.relative_to(ROOT).as_posix()
        except ValueError:
            return match.group(0)
        if rel in MIRRORS:
            heading = ""
            if fragment:
                headings = re.findall(r"^#{1,6}\s+(.+)$", resolved.read_text(), re.M)
                heading = next((x for x in headings if slug(x) == fragment), fragment)
            target_note = MIRRORS[rel].removesuffix(".md") + ("#" + heading if heading else "")
            return wiki(target_note, label.replace("`", ""))
        return "[" + label + "](" + resolved.as_uri() + ("#" + fragment if fragment else "") + ")"

    return re.sub(r"\[([^\]\n]+)\]\((<[^>\n]+>|[^)\n]+)\)", replace, body)


def normalize_repo_wikilinks(text: str, retired: set[str]) -> tuple[str, int]:
    count = 0

    def replace(match):
        nonlocal count
        target, _, label = match.group(1).partition("|")
        path, _, fragment = target.partition("#")
        if not path.startswith(str(ROOT) + "/"):
            return match.group(0)
        count += 1
        rel = Path(path).relative_to(ROOT).as_posix()
        label = label or rel
        if rel in MIRRORS:
            return wiki(MIRRORS[rel], label)
        if Path(path).exists():
            return (
                "["
                + label
                + "]("
                + Path(path).as_uri()
                + ("#" + fragment if fragment else "")
                + ")"
            )
        if rel in retired or rel.startswith("docs/system_atlas/"):
            return (
                wiki(MIRRORS["docs/system_atlas/generated/SYSTEM_ATLAS.md"], "Aktueller Atlas")
                + " (referenzierter Quellpfad im aktuellen Repo entfernt: `"
                + rel
                + "`)"
            )
        return label + " (am aktuellen Repo-Stand nicht vorhandener Quellpfad: `" + rel + "`)"

    return re.sub(r"\[\[([^\]\n]+)\]\]", replace, text), count


def current_block(domain: dict, model: dict, docs_commit: str) -> str:
    lines = [
        "\n<!-- current-repo-projection:start -->\n",
        "> [!info] Aktueller Repo-Abgleich · 06.11.2026\n",
        f"> Codequelle `{model['source_tag']}` / `{model['source_commit'][:9]}`. Dokumentationsstand `{docs_commit[:9]}`. "
        "Die folgende Ergänzung bindet diesen Bereich an dieselben Quellen wie das Master Runbook und der aktuelle Atlas.\n\n",
        "## Aktuelle Owner- und Zustandsübersicht\n\n",
        domain["purpose"] + "\n\n",
    ]
    for field, label in [
        ("inputs", "Eingänge"),
        ("processing", "Verarbeitung"),
        ("outputs", "Ausgänge"),
        ("state", "Zustand"),
        ("boundary", "Grenze"),
    ]:
        lines.append("**" + label + ":** " + domain[field] + "\n\n")
    lines.append("### Innere Module am fixierten Quellstand\n\n")
    for layer in domain["layers"]:
        path = ROOT / layer["source"]
        lines.append("- **" + layer["name"] + "**: [Originalowner](" + path.as_uri() + ")")
        if layer.get("symbols"):
            lines.append(
                " · "
                + ", ".join(
                    "`" + s["name"] + "` (Zeile " + str(s["line"]) + ")" for s in layer["symbols"]
                )
            )
        lines.append(".\n")
    lines += [
        "\n"
        + wiki(MIRRORS["docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"], "Master Runbook")
        + " · "
        + wiki(MIRRORS["docs/system_atlas/generated/SYSTEM_ATLAS.md"], "Aktueller Atlas")
        + " · "
        + wiki(MIRRORS[LAW_ROOT + "LAW_CHANGE_IMPACT.md"], "Regeln und Änderungsfolgen")
        + "\n\n",
        "> [!note] Reichweite der vorhandenen Vertiefung\n",
        "> Die nachfolgenden Anschluss-, Zustands-, Feld- und Herkunftsdossiers bleiben erhalten. Ihre datierten Nachweise werden durch diesen Quellenabgleich nicht pauschal zu einer neuen Laufzeit- oder Qualitätsabnahme.\n",
        "<!-- current-repo-projection:end -->\n",
    ]
    return "".join(lines)


def insert_current_block(original: str, block: str) -> str:
    base = MARKER.sub("\n", original)
    heading = re.search(r"^# .+$", base, re.M)
    if not heading:
        raise ValueError("DOMAIN_HEADING_MISSING")
    return (
        base[: heading.end()].rstrip()
        + "\n\n"
        + block.strip()
        + "\n\n"
        + base[heading.end() :].lstrip("\n")
    )


def build(vault: Path) -> tuple[dict[str, bytes], dict]:
    vault = vault.resolve()
    if vault == ROOT or vault.is_relative_to(ROOT) or not (vault / ".obsidian").is_dir():
        raise ValueError("EXISTING_EXTERNAL_VAULT_REQUIRED")
    model = json.loads((ROOT / "docs/system_atlas/source/current-model.json").read_bytes())
    cleanup = json.loads(
        (ROOT / "docs/system_atlas/source/documentation-cleanup.json").read_bytes()
    )
    law = json.loads(
        (ROOT / "config/governance/current_law_impact_map_v1/source_v1.json").read_bytes()
    )
    # A tooling-only commit does not create a new revision of the mirrored sources.
    docs_commit = subprocess.check_output(
        ["git", "log", "-1", "--format=%H", "--", *sorted(MIRRORS)], cwd=ROOT, text=True
    ).strip()
    files: dict[str, bytes] = {}
    sources = []
    for rel, dest in MIRRORS.items():
        source = ROOT / rel
        raw = source.read_bytes()
        title = Path(dest).stem
        text = note_header(title)
        text += "> [!info] Abgeleitete Ansicht aus dem aktuellen Repository\n> "
        text += (
            "[Originaldatei]("
            + source.as_uri()
            + ") · SHA256 `"
            + digest(raw)
            + "`. Maßgeblich bleibt die Quelle im Repo.\n\n"
        )
        text += mirror_links(raw.decode(), source)
        files[dest] = text.rstrip().encode() + b"\n"
        sources.append({"source": str(source), "source_sha256": digest(raw), "vault_path": dest})
    profile_raw = PROFILE.read_bytes()
    files[PREFIX + "/Arbeitsprofil.md"] = (
        note_header("Arbeitsprofil")
        + "> Quelle: [Globale Arbeitsanweisung]("
        + PROFILE.as_uri()
        + "). Diese Datei steuert die Arbeit des Assistenten; sie erzeugt keine Trading- oder Betriebsfreigabe.\n\n"
        + profile_raw.decode()
    ).encode()
    sources.append(
        {
            "source": str(PROFILE),
            "source_sha256": digest(profile_raw),
            "vault_path": PREFIX + "/Arbeitsprofil.md",
        }
    )
    master = wiki(MIRRORS["docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"], "Master Runbook")
    atlas = wiki(MIRRORS["docs/system_atlas/generated/SYSTEM_ATLAS.md"], "System Atlas")
    truth = wiki(MIRRORS["docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"], "Map of Truth")
    impact = wiki(MIRRORS[LAW_ROOT + "LAW_CHANGE_IMPACT.md"], "Law Impact Map")
    profile = wiki(PREFIX + "/Arbeitsprofil.md", "Arbeitsprofil")
    binding = f"Code-Fixpunkt **`{model['source_tag']}` / `{model['source_commit'][:9]}`**. Nachgeführte Repo-Dokumentation **`{docs_commit[:9]}`**. Vault: `{vault}`.\n\n"
    nav = master + " · " + atlas + " · " + truth + " · " + impact + " · " + profile + "\n\n"
    common = (
        "## Die belegten Größen getrennt lesen\n\n"
        "Entscheidung, Sicherheit, Ausführung und wirtschaftliches Ergebnis haben eigene Rollen. "
        "Marktreturn, Forecastfehler, Researchscore und Kontogewinn sind verschiedene Größen. "
        "Ein Import, eine Datei oder ein korrekt transportiertes Label belegt noch keine ausgeführte Wirkung.\n\n"
        "Cap23 führt im fixierten Code ein ausgewähltes Instrument und MaxPos 1. Die Positionsgrenze "
        "begrenzt gleichzeitig gehaltene Positionen; sie begrenzt nicht die Anzahl fortgesetzter Handelszyklen. "
        "Das Nutzerziel bleibt der fortgesetzte Double-Play-Kreis und die durchgängige Belegung freigeschalteter Slots. "
        "Vorbereitete N5-Strukturen und der konkrete Hostjoin werden getrennt belegt.\n\n"
        "Der numerische OLS-Folgeforecast ist als begrenzter Offlineadapter vorhanden. Natürliche Qualität, "
        "vollautomatischer Trainingsbetrieb, produktives Apply und durchgängige wirtschaftliche Wirkung "
        "folgen nicht allein aus diesem Adapter.\n\n"
    )
    files["Start.md"] = (
        note_header("PeakTrade · Aktuelles System")
        + "# PeakTrade · Aktuelles System\n\n"
        + binding
        + nav
        + "**"
        + wiki("00 Systemindex/System Cockpit", "System-Cockpit")
        + " · "
        + wiki("Systemkarte.canvas", "Universen und Außenkanten")
        + " · "
        + wiki("Systemkarte Offlineverbund.canvas", "Die Offlinepfade")
        + " · "
        + wiki("00 Systemindex/Galaxy View", "3D-Galaxie")
        + "**\n\n"
        + "## Was angeglichen ist\n\nMaster Runbook, Atlas, Map of Truth und Arbeitsprofil führen durch denselben fixierten Bestand. "
        "Die Law Impact Map ergänzt Originalregelquellen, Referenzstellen und offenen Prüfbedarf. "
        f"{len(cleanup['removed'])} zusätzliche Repo-Kartendateien sind entfernt. Drei maschinell genutzte Dokumente und ein noch konsumiertes JSON-Quellenobjekt bleiben als Originalverträge erhalten.\n\n"
        + "## Fachliche Tiefe\n\n"
        + wiki("PeakTrade-Systemindex", "22 Bereiche, innere Module, Anschlüsse und Zustände")
        + " · "
        + wiki("00 Systemindex/Semantische Ebenen", "Semantische Ebenen")
        + " · "
        + wiki("00 Systemindex/Grenzregister", "Eigene Outputs und erste fremde Consumer")
        + "\n\n"
        + common
        + "## Offene Punkte\n\n"
        + wiki(
            MIRRORS[LAW_ROOT + "unknown_and_conflict_v1.md"],
            "Konkrete Regel- und Bedeutungsunterschiede",
        )
        + " · "
        + wiki(
            "00 Systemindex/Repoabgleich/Konkrete Luecken im Repository",
            "Weitere konkrete Lücken und Nachweisgrenzen",
        )
        + "\n\n"
        + "Diese Ansicht führt keinen Host aus und erteilt keine Trading-, Order- oder Applyfreigabe.\n"
    ).encode()
    counts = json.loads((ROOT / "docs/system_atlas/source/policy-inventory.json").read_bytes())
    cockpit = (
        note_header("PeakTrade System-Cockpit") + "# PeakTrade System-Cockpit\n\n" + binding + nav
    )
    cockpit += (
        "## Navigation\n\n"
        + wiki("Start", "Start")
        + " · "
        + wiki("Systemkarte.canvas", "Systemkarte")
        + " · "
        + wiki("Systemkarte Offlineverbund.canvas", "Offlineverbund")
        + " · "
        + wiki("00 Systemindex/Galaxy View", "Galaxy View")
        + "\n\n"
    )
    cockpit += common
    cockpit += f"## Regeln, Quellen und Grenzen\n\n**{law['policy_inventory']['count']} Policy-/Regeldateien** und **{counts['static_reference_count']} statische Referenzstellen** sind erfasst. Bei **{counts['no_static_reference_discovered']} Dateien** wurde im erfassten Pythonbestand keine Referenz entdeckt; daraus folgt keine automatische Lösch- oder Nichtverwendungsentscheidung.\n\n"
    cockpit += (
        wiki(MIRRORS[LAW_ROOT + "surface_census_v1.md"], "Policy-Dateien und Referenzstellen")
        + " · "
        + wiki(MIRRORS[LAW_ROOT + "semantic_object_index_v1.md"], "Zuordnung zu Fachverträgen")
        + " · "
        + wiki(MIRRORS[LAW_ROOT + "unknown_and_conflict_v1.md"], "Offene Regelbeziehungen")
        + "\n\n"
    )
    cockpit += "Die Repo-Dokumentationsänderung ist mit 27 gezielten Tests geprüft. Das ist keine vollständige System-, Policy- oder Wirtschaftsabnahme. Frühere Testnachweise behalten ihre datierten Scopes; ihre Zahlen werden nicht addiert oder als heutiger Gesamt-PASS übernommen.\n\n"
    cockpit += "## Bereiche und innere Ebenen\n\n"
    index = note_header("PeakTrade-Systemindex") + "# PeakTrade-Systemindex\n\n" + binding + nav
    index += "22 fachliche Navigationsbereiche mit eigenen Eingängen, Verarbeitung, Ausgängen, Zuständen und Consumergrenzen. Die Gliederung erteilt keine zusätzliche Fachautorität.\n\n"
    for d in model["domains"]:
        path = (
            "00 Systemindex/"
            + (
                "Universen/"
                if d["id"] in {"RANK", "CORE", "SL", "OPT", "INT", "FA"}
                else "Aussenbereiche/"
            )
            + d["id"]
            + ".md"
        )
        original = (vault / path).read_text()
        files[path] = insert_current_block(original, current_block(d, model, docs_commit)).encode()
        cockpit += (
            "- "
            + wiki(path, d["name"])
            + " · "
            + wiki("00 Systemindex/Zustaende/" + d["id"], "Zustands- und Feldverträge")
            + ".\n"
        )
        index += "## " + wiki(path, d["name"]) + "\n\n" + d["purpose"] + "\n\n"
        index += "Innere Module: " + "; ".join(x["name"] for x in d["layers"]) + ".\n\n"
        index += (
            wiki("00 Systemindex/Zustaende/" + d["id"], "Felder und Zustände")
            + " · "
            + wiki("00 Systemindex/Auswirkungen/" + d["id"], "Übergaben und Auswirkungen")
            + ".\n\n"
        )
    cockpit += "\n## Belegarten\n\nAbsicht, vorhandener Code, statische Verbindung, beobachteter Einzelfall und natürliche/wirtschaftliche/operative Wirkung bleiben getrennte Aussagen. Die bestehenden fachlichen Detaildossiers und ihre Originalnachweise bleiben erhalten.\n"
    files["00 Systemindex/System Cockpit.md"] = cockpit.encode()
    files["PeakTrade-Systemindex.md"] = index.encode()
    galaxy = (vault / "00 Systemindex/Galaxy View.md").read_text()
    galaxy = galaxy.replace(
        "Die neue Marktbeobachtung endet nach originaler Calibration und nativem Cold Readback. **Lernzustand → nächstes tatsächlich verwendetes Modell bleibt offen**; aus dem Dokumentgraph entsteht keine automatische Trainings- oder Trading-Schleife.",
        "Der numerische OLS-Modellstore und tatsächlich berechnete Folgeforecast sind als begrenzter Offlineadapter vorhanden. Natürliche Modellqualität, ein automatischer Trainingsscheduler und produktives Apply bleiben getrennte Nachweise. Der Dokumentgraph erzeugt keine automatische Trainings- oder Trading-Schleife.\n\n"
        + nav,
    )
    files["00 Systemindex/Galaxy View.md"] = galaxy.encode()
    canvas_before = {}
    for name in ["Systemkarte.canvas", "Systemkarte Offlineverbund.canvas"]:
        data = json.loads((vault / name).read_bytes())
        canvas_before[name] = {
            "nodes": [n["id"] for n in data["nodes"]],
            "edges": [e["id"] for e in data["edges"]],
        }
        data["nodes"] = [n for n in data["nodes"] if not n["id"].startswith("current-repo-")]
        data["edges"] = [e for e in data["edges"] if not e["id"].startswith("current-repo-")]
        title = next(n for n in data["nodes"] if n["id"] == "title")
        title["text"] = (
            "# PeakTrade · "
            + (
                "Universen und Außenkanten"
                if name == "Systemkarte.canvas"
                else "Dokumentierte Offlinepfade"
            )
            + "\n\nCode-Fixpunkt `"
            + model["source_commit"][:9]
            + "`, aktuelle Repo-Dokumentation `"
            + docs_commit[:9]
            + "`. Fachliche Ebenen und Zustandsdossiers bleiben einzeln erreichbar. Diagramm- und Dateikanten sind keine neue Laufzeitabnahme.\n\n"
            + nav
        )
        y = max(n["y"] + n["height"] for n in data["nodes"]) + 160
        x = min(n["x"] for n in data["nodes"])
        for i, (key, target) in enumerate(
            [
                ("master", MIRRORS["docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"]),
                ("law", MIRRORS[LAW_ROOT + "LAW_CHANGE_IMPACT.md"]),
            ]
        ):
            nid = "current-repo-" + key
            data["nodes"].append(
                {
                    "id": nid,
                    "type": "file",
                    "file": target,
                    "x": x + i * 700,
                    "y": y,
                    "width": 560,
                    "height": 220,
                }
            )
            data["edges"].append(
                {
                    "id": "current-repo-edge-" + key,
                    "fromNode": "title",
                    "fromSide": "bottom",
                    "toNode": nid,
                    "toSide": "top",
                    "label": "Quellenstand" if key == "master" else "Regeln und Prüfbedarf",
                }
            )
        files[name] = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode()
    retired = {x["path"] for x in cleanup["removed"]}
    normalized = 0
    for path in vault.rglob("*.md"):
        rel = path.relative_to(vault).as_posix()
        if any(p.startswith(".") for p in path.relative_to(vault).parts):
            continue
        text = files[rel].decode() if rel in files else path.read_text()
        text, count = normalize_repo_wikilinks(text, retired)
        if count:
            files[rel] = text.encode()
            normalized += count
    receipt = {
        "schema": "peaktrade.current_obsidian_projection.v1",
        "vault": str(vault),
        "source_tag": model["source_tag"],
        "product_source_commit": model["source_commit"],
        "documentation_source_commit": docs_commit,
        "source_files": sources,
        "domains": len(model["domains"]),
        "policy_files": law["policy_inventory"]["count"],
        "removed_repo_map_files": len(cleanup["removed"]),
        "normalized_external_repo_wikilinks": normalized,
        "canvas_before": canvas_before,
        "runtime_authorization_effect": "NONE",
        "backup_created": False,
    }
    return files, receipt


def apply(vault: Path) -> dict:
    before = {
        p.relative_to(vault).as_posix(): digest(p.read_bytes())
        for p in vault.rglob("*")
        if p.is_file() and ".obsidian" not in p.relative_to(vault).parts
    }
    files, receipt = build(vault)
    for rel, raw in files.items():
        path = vault / rel
        if rel in before and digest(path.read_bytes()) != before[rel]:
            raise ValueError("CONCURRENT_VAULT_EDIT:" + rel)
        if rel not in before and path.exists():
            raise ValueError("CONCURRENT_VAULT_FILE_CREATED:" + rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    receipt["generated_files"] = [
        {
            "path": p,
            "sha256": digest(raw),
            **({"json_sha256": json_content_digest(raw)} if p.endswith(".canvas") else {}),
        }
        for p, raw in sorted(files.items())
    ]
    for name in ["Systemindexbindung.json", "Systematlasbindung.json", "Ansichtsbindung.json"]:
        path = vault / name
        obj = json.loads(path.read_bytes())
        original = {k: v for k, v in obj.items() if k != "current_repository_projection"}
        receipt.setdefault("preserved_binding_values", {})[name] = digest(
            json.dumps(original, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        )
        obj["current_repository_projection"] = {
            "schema": receipt["schema"],
            "vault": str(vault),
            "source_tag": receipt["source_tag"],
            "product_source_commit": receipt["product_source_commit"],
            "documentation_source_commit": receipt["documentation_source_commit"],
            "receipt": RECEIPT,
            "runtime_authorization_effect": "NONE",
            "original_fields_role": "DATED_SOURCE_BINDING_NOT_REWRITTEN",
        }
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")
    path = vault / RECEIPT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    return check(vault)


def check(vault: Path) -> dict:
    receipt = json.loads((vault / RECEIPT).read_bytes())
    assert receipt["vault"] == str(vault.resolve())
    assert (
        subprocess.check_output(
            ["git", "rev-parse", receipt["source_tag"] + "^{commit}"], cwd=ROOT, text=True
        ).strip()
        == receipt["product_source_commit"]
    )
    for item in receipt["source_files"]:
        assert digest(Path(item["source"]).read_bytes()) == item["source_sha256"], item
    serialization_changes = [
        item["path"]
        for item in receipt["generated_files"]
        if verify_generated_file((vault / item["path"]).read_bytes(), item)
    ]
    for name, old in receipt["canvas_before"].items():
        data = json.loads((vault / name).read_bytes())
        nodes = {n["id"]: n for n in data["nodes"]}
        edges = {e["id"]: e for e in data["edges"]}
        assert len(nodes) == len(data["nodes"]) and len(edges) == len(data["edges"])
        assert set(old["nodes"]) <= set(nodes) and set(old["edges"]) <= set(edges)
        assert all(e["fromNode"] in nodes and e["toNode"] in nodes for e in edges.values())
        for n in nodes.values():
            if n["type"] == "file":
                assert (vault / n["file"]).is_file(), n
            if not n["id"].startswith("current-repo-"):
                continue
            for other in nodes.values():
                if n["id"] == other["id"] or other["type"] == "group":
                    continue
                assert not (
                    n["x"] < other["x"] + other["width"]
                    and n["x"] + n["width"] > other["x"]
                    and n["y"] < other["y"] + other["height"]
                    and n["y"] + n["height"] > other["y"]
                ), [name, n["id"], other["id"]]
    for rel in ["Systemindexbindung.json", "Systematlasbindung.json", "Ansichtsbindung.json"]:
        data = json.loads((vault / rel).read_bytes())
        assert (
            data["current_repository_projection"]["documentation_source_commit"]
            == receipt["documentation_source_commit"]
        )
        original = {k: v for k, v in data.items() if k != "current_repository_projection"}
        assert (
            digest(
                json.dumps(
                    original, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                ).encode()
            )
            == receipt["preserved_binding_values"][rel]
        )
    return {
        "result": "PASS",
        "vault": str(vault),
        "product_source_commit": receipt["product_source_commit"],
        "documentation_source_commit": receipt["documentation_source_commit"],
        "projected_files": len(receipt["generated_files"]),
        "domains": receipt["domains"],
        "policy_files": receipt["policy_files"],
        "normalized_external_repo_wikilinks": receipt["normalized_external_repo_wikilinks"],
        "canvas_serialization_changes": serialization_changes,
        "runtime_authorization_effect": "NONE",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["plan", "apply", "check"])
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    args = parser.parse_args()
    vault = args.vault.resolve()
    if args.mode == "plan":
        files, receipt = build(vault)
        result = {
            "vault": str(vault),
            "projected_files": len(files),
            "domains": receipt["domains"],
            "sources": len(receipt["source_files"]),
        }
    else:
        result = apply(vault) if args.mode == "apply" else check(vault)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
