"""Read-only law/policy projection of the frozen source inventory."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import gzip
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
LAW = "config/governance/current_law_impact_map_v1/source_v1.json"
TECHNICAL_ADMISSION = "config/governance/technical_canonical_wiring_authorization_v1.json"
NUMERIC_ADMISSION_PATHS = (
    "src/trading/master_v2/survival_numeric_admission_v1.py",
    "src/trading/master_v2/survival_suitability_scenario_binding_adapter_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
    "tests/trading/master_v2/test_surface_p_explicit_financial_context_v1.py",
    "tests/trading/master_v2/test_surface_p_required_proof_input_binding_contract_v0.py",
    "tests/trading/master_v2/test_survival_numeric_admission_v1.py",
)
NUMERIC_ADMISSION_ID = "CURRENT_NUMERIC_INPUT_ADMISSION_AND_EXPLICIT_OFFLINE_FINANCIAL_CONTEXT_V1"


def validate_numeric_technical_admission_delta(original: bytes, current: bytes) -> None:
    """Admit only the owner-requested six-file extension of the frozen contract.

    Hash rebinding alone cannot change a prior grant, an invariant, an effect,
    or add a seventh file. The original frozen inventory stays authoritative
    for the baseline; this is a separately bound development delta.
    """
    before, after = json.loads(original), json.loads(current)
    mutable = {"allowed_paths", "authorized_surface_notes"}
    if (
        set(before) != set(after)
        or any(after[k] != v for k, v in before.items() if k not in mutable)
        or any(p in before["allowed_paths"] for p in NUMERIC_ADMISSION_PATHS)
        or after["allowed_paths"] != before["allowed_paths"] + list(NUMERIC_ADMISSION_PATHS)
        or not isinstance(after["authorized_surface_notes"], list)
        or len(after["authorized_surface_notes"]) != len(before["authorized_surface_notes"]) + 1
        or after["authorized_surface_notes"][:-1] != before["authorized_surface_notes"]
        or type(after["authorized_surface_notes"][-1]) is not str
        or not after["authorized_surface_notes"][-1].startswith(NUMERIC_ADMISSION_ID + ": ")
    ):
        raise ValueError("POLICY_TECHNICAL_ADMISSION_DELTA_INVALID")


def policy_scope_kind(path: str) -> str | None:
    if path.startswith("config/governance/current_law_impact_map_v1/") or path in {
        "config/ops/docs_truth_map.yaml",
        "config/ops/repo_truth_claims.yaml",
        "config/governance/current_system_census_graph_v1/README.md",
    }:
        return None
    if path.startswith(".cursor/rules/"):
        return "DEVELOPMENT_GUIDANCE"
    if path.startswith("policy_packs/"):
        return "DEVELOPMENT_CHECK_POLICY"
    if path.startswith(("config/", "src/")) and (
        re.search(
            r"policy|policies|governance|(?:^|[_/])law(?:[_/.]|$)|(?:^|[_/])rule(?:[_/.]|$)",
            path,
            re.I,
        )
        or path.startswith(("src/risk/", "src/risk_layer/"))
    ):
        if path.startswith(
            (
                "config/governance/current_system_census_graph_v1/",
                "config/governance/current_system_interaction_authority_map_v1/",
            )
        ):
            return "DOCUMENTARY_INDEX_DATA"
        return "MACHINE_CONFIGURATION" if path.startswith("config/") else "SOURCE_INTERFACE"
    return None


def load_policies(root: Path, doc: dict) -> list[dict]:
    meta = doc["policy_inventory"]
    if (
        set(meta) != {"path", "sha256", "count", "schema"}
        or meta["path"] != "docs/system_atlas/source/current-policies.jsonl.gz"
        or meta["schema"] != "peaktrade.frozen_policy_inventory.v1"
        or type(meta["count"]) is not int
        or not isinstance(meta["sha256"], str)
        or re.fullmatch(r"[a-f0-9]{64}", meta["sha256"]) is None
    ):
        raise ValueError("POLICY_INVENTORY_CONTRACT_INVALID")
    raw = (root / meta["path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != meta["sha256"]:
        raise ValueError("POLICY_INVENTORY_DIGEST_MISMATCH")
    rows = [json.loads(x) for x in gzip.decompress(raw).splitlines()]
    if len(rows) != meta["count"] or len({x["path"] for x in rows}) != len(rows):
        raise ValueError("POLICY_INVENTORY_COUNT_MISMATCH")
    return rows


def link(path: str, label: str | None = None) -> str:
    return f"[{label or path}](../../../../{path})"


def render_law_views(doc: dict, root: Path = ROOT) -> dict[str, str]:
    policies = load_policies(root, doc)
    header = (
        "<!-- GENERATED FILE. DO NOT EDIT BY HAND. FROZEN_LAW_POLICY_VIEW AUTHORITY=NONE -->\n\n"
        "```text\nLAW_IMPACT_MAP_AUTHORITY=NONE\nLAW_REFERENCE_IS_NORMATIVE=false\n"
        f"SOURCE_TAG={doc['source_tag']}\nSOURCE_COMMIT={doc['baseline_sha']}\n"
        "RUNTIME_AUTHORIZATION_EFFECT=NONE\n```\n\n"
    )
    intro = (
        "Diese abgeleitete Sicht zeigt Regelquellen, statische Referenzen und Prüfbedarf. "
        "Die Definition und Durchsetzung einer Regel gehören zu ihrem Originalowner. "
        "Ein Pfad, Import oder Stringliteral belegt keine ausgeführte Consumerkette.\n\n"
        "Einstiege: "
        + link("docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md", "Master Runbook")
        + " · "
        + link("docs/system_atlas/generated/SYSTEM_ATLAS.md", "System Atlas")
        + ".\n\n"
    )
    law = ["# Regelquellen\n\n", header, intro]
    for item in sorted(doc["law_references"], key=lambda x: x["law_id"]):
        law += [
            f"## {item['law_id']}\n\n",
            link(item["canonical_source"]) + "\n\n",
            f"Quellanker: `{item['canonical_anchor']}`. SHA256: `{item['source_sha256']}`. "
            f"Index: `{item['index_status']}`.\n\n",
        ]
    objects = ["# Zuordnung zu Fachverträgen\n\n", header, intro]
    objects.append(
        "Die Einträge bezeichnen zu prüfende Fachverträge. Ihre Funktion wird durch "
        "diese Dokumenterzeugung nicht erneut ausgeführt oder als betriebsbereit bestätigt.\n\n"
    )
    for obj in sorted(doc["semantic_objects"], key=lambda x: x["id"]):
        objects += [
            f"## {obj['id']}\n\n",
            f"Rolle: `{obj['semantic_class']}`. Prüfumfang: `{obj['current_status']}`.\n\n",
        ]
        for path in obj.get("code_surfaces", []) + obj.get("config_surfaces", []):
            objects.append("- " + link(path) + "\n")
        objects.append(
            "\nRegelreferenzen: " + ", ".join(f"`{x}`" for x in obj["law_ref_ids"]) + ".\n\n"
        )
    unknown = ["# Offene Beziehungen und Unterschiede\n\n", header, intro]
    unknown.append("## UNKNOWN_RELATION — offene Zuordnungen\n\n")
    for item in doc["unknown_relations"]:
        unknown += [f"## {item['id']}\n\n", f"`{item['unknown_class']}`. {item['statement']}\n\n"]
    for item in doc["semantic_divergence_index"]:
        unknown += [f"## {item['id']}\n\n", f"`{item['adjudication']}`. {item['statement']}\n\n"]
        for path in item.get("evidence_refs", []):
            if (root / path).is_file():
                unknown.append("- " + link(path) + "\n")
        unknown.append("\n")
    census = ["# Policy- und Regeldateien des Freeze\n\n", header, intro]
    census += [
        f"**{len(policies)} Dateien** im ausgewiesenen Suchumfang. "
        "Die vollständigen Referenzstellen und Quelldigests stehen im "
        "[maschinenlesbaren Katalog](../../../system_atlas/source/current-policies.jsonl.gz).\n\n",
        "Suchumfang: versionierte Quell-/Konfigurationspfade mit policy/policies/governance/law/rule, "
        "Risk-Verzeichnisse, Policy Packs und Entwicklungsregeln. Die Quellen der "
        "Dokumentprojektion und die beiden Dokumentgate-Selektoren werden gesondert geprüft. "
        "Der Katalog weist damit diesen Dateiumfang vollständig aus; die semantische "
        "Wirksamkeit jeder Regel bleibt eine Prüfung ihres konkreten Consumers.\n\n",
        "`SOURCE` bezeichnet eine Referenz aus einer Quelldatei, `TOOL` eine aus Werkzeugcode "
        "und `TEST` eine aus Tests. Ein eindeutiger Dateinamenliteral bleibt eine statische "
        "Fundstelle. Keine entdeckte Referenz ist kein Beweis für Nichtverwendung.\n\n",
    ]
    for kind in sorted({p["kind"] for p in policies}):
        census.append(f"## {kind}\n\n")
        for p in policies:
            if p["kind"] != kind:
                continue
            census += [
                "- "
                + link(p["path"])
                + f" · `{p['parse_status']}` · SHA256 `{p['frozen_sha256']}`\n",
                f"  Referenzstellen: SOURCE {p['source_reference_count']}, "
                f"TOOL {p['tool_reference_count']}, TEST {p['test_reference_count']}. "
                f"`{p['reference_status']}`.\n",
            ]
            refs = [r for r in p["static_references"] if r["scope"] == "SOURCE"][:3]
            for ref in refs:
                census.append(
                    "  "
                    + link(ref["path"], ref["path"] + ":" + str(ref["line"]))
                    + f" · `{ref['kind']}`.\n"
                )
        census.append("\n")
    census.append("## Weiterer semantischer Prüfbedarf\n\n")
    for row in doc.get("unclassified_current_surfaces", []):
        census.append("- UNCLASSIFIED: " + link(row["path"]) + "\n")
    for row in doc.get("semantic_divergence_index", []):
        census.append(f"- `{row['id']}`: `{row['adjudication']}`; siehe offene Beziehungen.\n")
    no_refs = sum(not p["static_references"] for p in policies)
    impact = ["# Law Impact Map — Regeln und Änderungsfolgen\n\n", header, intro]
    impact += [
        f"## Bestand\n\n{len(doc['law_references'])} explizite Regelreferenzen, "
        f"{len(doc['semantic_objects'])} Fachverträge und {len(policies)} indexierte Policy-/Regeldateien. "
        f"{no_refs} dieser Dateien haben im erfassten Pythonbestand keine entdeckte statische Referenz.\n\n",
        "- [Regelquellen](law_reference_index_v1.md): Originalowner, Anker und aktueller Digest.\n",
        "- [Fachverträge](semantic_object_index_v1.md): Code-/Configzuordnung ohne neue Freigabe.\n",
        "- [Vollständiger Dateiumfang](surface_census_v1.md): typisierte Policydateien und Referenzstellen.\n",
        "- [Offene Beziehungen](unknown_and_conflict_v1.md): konkrete Unterschiede und Prüfbedarf.\n\n",
        "## Prüfung einer Änderung\n\n",
        "1. Geänderte Originalregel mit dem gebundenen Quellstand vergleichen.\n",
        "2. Direkte Regelreferenzen, statische Import-/Pfadfundstellen und zugeordnete Fachverträge ermitteln.\n",
        "3. Zahlen-, Einheiten-, Zeit-, Identitäts- und Zustandsvertrag am tatsächlichen Consumer prüfen.\n",
        "4. Betroffene Prüfungen mit Originalinputs ausführen; unklassifizierte Folgen als offen belassen.\n",
        "5. Quellenbindung und diese abgeleiteten Ansichten gemeinsam nachführen.\n\n",
        "## Aussagegrenze\n\n",
        "Die jetzige Dokumentprüfung kontrolliert Dateibestand, Syntax strukturierter Quellen, "
        "Digests, Quellanker, Referenzziele und deterministische Ausgabe. Sie erteilt kein "
        "Gesamturteil über die fachliche Richtigkeit sämtlicher Policies und bestätigt keinen "
        "durchgängigen Betrieb. Numerischer Wertverbrauch, Risikoentscheidung, Permit, "
        "Venuewirkung und produktives Apply brauchen jeweils ihre eigenen Nachweise.\n",
    ]
    impact.append("\n## Erhaltene maschinell genutzte Dokumente\n\n")
    impact.append(
        "Diese Dateien sind Originaleingaben oder Schreibziele bestehender Module. Ihre Erhaltung macht sie zu keiner zusätzlichen aktuellen Systemlandkarte. Die jeweiligen Verwendungen sind statische Codebefunde.\n\n"
    )
    for item in doc.get("consumed_documents", []):
        impact.append("- " + link(item["path"]) + f" · `{item['role']}`.\n")
        for ref in [x for x in item["static_references"] if x["scope"] == "SOURCE"]:
            impact.append("  " + link(ref["path"], ref["path"] + ":" + str(ref["line"])) + ".\n")
    return {
        "law_reference_index": "".join(law).rstrip() + "\n",
        "semantic_object_index": "".join(objects).rstrip() + "\n",
        "unknown_and_conflict": "".join(unknown).rstrip() + "\n",
        "surface_census": "".join(census).rstrip() + "\n",
        "law_change_impact": "".join(impact).rstrip() + "\n",
    }


def policy_impact_for_paths(doc: dict, paths: list[str], root: Path = ROOT) -> dict:
    changed = set(paths)
    direct, source_refs, test_refs, tool_refs = set(), set(), set(), set()
    for policy in load_policies(root, doc):
        refs = policy["static_references"]
        if policy["path"] in changed or any(r["path"] in changed for r in refs):
            direct.add(policy["path"])
            for ref in refs:
                target = (
                    source_refs
                    if ref["scope"] == "SOURCE"
                    else test_refs
                    if ref["scope"] == "TEST"
                    else tool_refs
                )
                target.add(ref["path"])
    return {
        "policies": sorted(direct),
        "source_references": sorted(source_refs),
        "test_references": sorted(test_refs),
        "tool_references": sorted(tool_refs),
        "runtime_effect_inferred": False,
    }


def validate_policy_inventory(root: Path, doc: dict) -> dict:
    model = json.loads((root / "docs/system_atlas/source/current-model.json").read_bytes())
    if doc["baseline_sha"] != model["source_commit"] or doc["source_tag"] != model["source_tag"]:
        raise ValueError("LAW_POLICY_SOURCE_BINDING_MISMATCH")
    resolved = subprocess.check_output(
        ["git", "rev-parse", doc["source_tag"] + "^{commit}"], cwd=root, text=True
    ).strip()
    if resolved != doc["baseline_sha"]:
        raise ValueError("LAW_POLICY_TAG_MISMATCH")
    inventory = [
        json.loads(x)
        for x in gzip.decompress(
            (root / "docs/system_atlas/source/current-files.jsonl.gz").read_bytes()
        ).splitlines()
    ]
    frozen = {p["path"]: p for p in inventory}
    policies = load_policies(root, doc)
    if {p["path"] for p in policies} != {p for p in frozen if policy_scope_kind(p)}:
        raise ValueError("POLICY_SCOPE_COVERAGE_MISMATCH")
    tree = {}
    for entry in subprocess.check_output(["git", "ls-tree", "-r", "-z", resolved], cwd=root).split(
        b"\0"
    ):
        if entry:
            meta, path = entry.split(b"\t", 1)
            tree[path.decode()] = meta.decode().split()[2]
    development_policy_files = []
    for policy in policies:
        path = policy["path"]
        raw = (root / path).read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        original = raw
        if actual != policy["frozen_sha256"]:
            if path not in {
                "config/governance/clean_core_seal_manifest_v1.json",
                "src/ops/single_selected_future_policy_v1/selection_v1.py",
                TECHNICAL_ADMISSION,
            }:
                raise ValueError("POLICY_SOURCE_DRIFT:" + path)
            binding = json.loads(
                (root / "docs/system_atlas/source/development-binding-v1.json").read_bytes()
            )
            rows = [row for row in binding["files"] if row["path"] == path]
            if (
                binding.get("schema") != "peaktrade.atlas_development_binding.v1"
                or binding.get("authority") != "NONE"
                or binding.get("runtime_authorization_effect") != "NONE"
                or binding.get("frozen_source_commit") != resolved
                or len(rows) != 1
                or rows[0]["before_sha256"] != policy["frozen_sha256"]
                or rows[0]["sha256"] != actual
            ):
                raise ValueError("POLICY_DEVELOPMENT_BINDING_INVALID:" + path)
            original = subprocess.check_output(["git", "show", resolved + ":" + path], cwd=root)
            if path == TECHNICAL_ADMISSION:
                validate_numeric_technical_admission_delta(original, raw)
            development_policy_files.append(path)
        original_digest = hashlib.sha256(original).hexdigest()
        if original_digest != policy["frozen_sha256"] or original_digest != frozen[path]["sha256"]:
            raise ValueError("POLICY_SOURCE_DRIFT:" + path)
        git_digest = hashlib.sha1(
            b"blob " + str(len(original)).encode() + b"\0" + original
        ).hexdigest()
        if git_digest != policy["git_blob_oid"] or git_digest != tree[path]:
            raise ValueError("POLICY_GIT_OBJECT_MISMATCH:" + path)
        if policy["kind"] != policy_scope_kind(path):
            raise ValueError("POLICY_KIND_MISMATCH:" + path)
        for ref in policy["static_references"]:
            if ref["path"] not in frozen or not (root / ref["path"]).is_file() or ref["line"] < 1:
                raise ValueError("POLICY_REFERENCE_MISSING:" + ref["path"])
    for item in doc.get("consumed_documents", []):
        raw = (root / item["path"]).read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if actual != item["sha256"] or actual != frozen[item["path"]]["sha256"]:
            raise ValueError("CONSUMED_DOCUMENT_DRIFT:" + item["path"])
        git_digest = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if git_digest != tree[item["path"]]:
            raise ValueError("CONSUMED_DOCUMENT_GIT_MISMATCH:" + item["path"])
    return {
        "policy_files": len(policies),
        "static_reference_sites": sum(len(p["static_references"]) for p in policies),
        "no_static_reference_discovered": sum(not p["static_references"] for p in policies),
        "by_kind": dict(Counter(p["kind"] for p in policies)),
        "runtime_effect_inferred": False,
        "retained_consumed_documents": len(doc.get("consumed_documents", [])),
        "development_policy_files": development_policy_files,
    }
