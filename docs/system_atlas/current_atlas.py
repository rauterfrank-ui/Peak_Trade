"""Render and check the Atlas projection of one fixed repository tree."""

from pathlib import Path
import argparse
import ast
import gzip
import hashlib
import json
import os
import re
import subprocess
from runpy import run_path

ROOT = Path(__file__).resolve().parents[2]
ATLAS = "docs/system_atlas/"
MASTER = "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MAP = "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
RATIFICATION = "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK_RATIFICATION.json"
TOOLS = {
    "scripts/ops/generate_system_atlas_v1.py",
    "scripts/ops/validate_system_atlas_v1.py",
    "scripts/ops/check_system_atlas_impact_v1.py",
}


# The Safety signature implementation adds PyNaCl and preserves the locked web extra.
FILEGATE_DEPENDENCY_DELTA = {
    "requirements.txt": "4f5666c408eebfa758db3112a12e8234900336f06aa223b6898f90b549b174d6",
    "pyproject.toml": "060a5b5751e1b2b6188fcb1c33c879101c11cee03d2b2494d859fa934915c014",
    "uv.lock": "3f522959780c4a36ba3cd739cb7b6edd5e96ee0cab3c5c64e5ffba413acba280",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    return subprocess.check_output(["git", "--no-optional-locks", *args], cwd=root)


def load(root):
    return json.loads((root / ATLAS / "source/current-model.json").read_bytes())


def records(root, name):
    raw = gzip.decompress((root / ATLAS / "source" / name).read_bytes())
    return [json.loads(line) for line in raw.splitlines()]


def source_link(path, label=None):
    return "[" + (label or path) + "](../../../" + path + ")"


def views(model):
    parts = [
        "<!-- GENERATED_CURRENT_FROZEN_VIEW -->\n# PeakTrade System Atlas\n\n",
        "```text\nATLAS_AUTHORITY=NONE\nATLAS_ROLE=CURRENT_FROZEN_SYSTEM_DESCRIPTION\nRUNTIME_AUTHORIZATION_EFFECT=NONE\nCURRENT_ONLY=true\nSOURCE_TAG="
        + model["source_tag"]
        + "\nSOURCE_COMMIT="
        + model["source_commit"]
        + "\nSYSTEM_FREEZE_TAG="
        + model.get("system_freeze_tag", model["source_tag"])
        + "\n```\n\n",
        "Dieser Atlas beschreibt den Dateibestand, die benannten Schnittstellen und die Fachgrenzen des fixierten Quellbaums. Die Fachgruppen sind Navigationsräume. Autorität und tatsächliche Zustandswirkung ergeben sich aus den zitierten Codeownern und dem [Master Runbook](../../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md).\n\n",
        "## Vollständiger Quellenbestand\n\n",
        f"Der Dateikatalog enthält **{model['file_count']:,} Dateien**, der Pythonkatalog **{model['python_modules_parsed']:,} syntaktisch gelesene Module**, **{model['named_definitions']:,} benannte Definitionen** und **{model['lexical_imports']:,} lexikalische Importreferenzen**. ".replace(
            ",", "."
        ),
        "Die vollständigen Pfade, Git-Objekte, Größen und SHA256 stehen in [current-files.jsonl.gz](../source/current-files.jsonl.gz). [current-symbols.jsonl.gz](../source/current-symbols.jsonl.gz) enthält Funktionen, Klassen, Parameter und annotierte Felder mit Quellzeilen. [current-imports.jsonl.gz](../source/current-imports.jsonl.gz) enthält die syntaktischen Importstellen.\n\n",
        "Ein Import ist eine Quellreferenz. Ein definierter Parameter ist noch kein beobachteter Wertverbrauch. Diese Kataloge behaupten keine ausgeführte Laufzeitkette. Der vollständige Dateibestand umfasst auch Dokumentations-, Test- und Belegdateien, die im fixierten Baum vorhanden sind; deren Inhalte werden dadurch nicht zu Betriebsregeln.\n\n",
        "## Datenverträge und Größen\n\n",
        "- Instrumentidentität bindet kanonische/native ID, Venue und erforderliche Metadaten.\n",
        "- Rankingvolatilität ist die Populationsstreuung von 60 Logreturns aus 61 finalen PT1M-Marks. Amplitude ist `(Maximum−Minimum) ÷ ((Maximum+Minimum) ÷ 2)`. Die Scorebildung verwendet relative Perzentile mit jeweils Gewicht 0,5.\n",
        "- GGE-Magnitude ist `Volatilität × Markpreis` in der Preiseinheit. L6 nimmt einen vorgeschlagenen positiven endlichen `D_t` an seinem Generatorseam an.\n",
        "- L5-Initialpreis und L8-Laufreferenz `R_t` sind verschiedene Zustände. L10 schaltet das Regime bei `CM_t >= D_t`.\n",
        "- Entscheidung, Risk-Admissibility, finale native Menge, Reservation, Envelope, bestätigter Fill und Accountingzustand sind getrennte Übergaben.\n",
        "- Ein Markthorizont bindet Instrument, Preisfamilie, Zeitraum und Quellengeneration. N Schlusskurse bilden N−1 Returnintervalle. Realisierter Logreturn, Forecastfehler, Researchscore und Kontogewinn sind verschiedene Größen.\n\n",
        "Quellen: "
        + source_link("src/ops/peak_trade_ranking_feature_production_v1/pure_compute_v1.py")
        + "; "
        + source_link("src/ops/peak_trade_economic_ranking_runtime_v1/score_construction_v1.py")
        + "; "
        + source_link("src/trading/master_v2/golden_geometry_engine_v1.py")
        + "; "
        + source_link(
            "src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/layer_catalog_v1.py"
        )
        + ".\n\n",
        "## Fachräume und innere Verarbeitung\n\n",
    ]
    for d in model["domains"]:
        parts += [
            "### " + d["id"] + " · " + d["name"] + "\n\n",
            d["purpose"] + "\n\n",
            "**Eingänge:** " + d["inputs"] + "\n\n",
            "**Verarbeitung:** " + d["processing"] + "\n\n",
            "**Ausgänge:** " + d["outputs"] + "\n\n",
            "**Zustand:** " + d["state"] + "\n\n",
            "**Grenze:** " + d["boundary"] + "\n\n",
            "**Innere Module und Schnittstellen:**\n\n",
        ]
        for layer in d["layers"]:
            line = "- " + layer["name"] + ": " + source_link(layer["source"])
            symbols = layer.get("symbols", [])
            if symbols:
                line += " · " + ", ".join(
                    "`" + s["name"] + "` (Zeile " + str(s["line"]) + ")" for s in symbols
                )
            parts.append(line + ".\n")
        parts.append("\n")
    parts += [
        "## Konkrete Konfigurationsgrenzen\n\n",
        "Cap23 führt `SELECTED_FUTURE_COUNT=1`, `MAX_POSITIONS_EFFECTIVE=1`, Default-Refresh 300 Sekunden, Default-Mindesthaltezeit 3.600 Sekunden und Hystereseverbesserung um einen Rang. Es konsumiert die vorgegebene Rangfolge. Ein Ersatz bei offener Position bleibt Pending; es erfolgt kein stiller Instrumentwechsel. Die Werte sind Moduldefaults, keine Behauptung eines laufenden Hosts.\n\n",
        source_link("src/ops/single_selected_future_policy_v1/constants_v1.py")
        + " · "
        + source_link("src/ops/single_selected_future_policy_v1/policy_v1.py")
        + "\n\n",
        "Der benannte Occupied-Lane-N1-Join enthält False-Pins für `HOST_JOIN`, `FIVE_LANE_RUNTIME_CREATED`, `FIVE_LANE_CONTINUOUS_HOST_JOIN` und Mehrinstrument-Ausführungsfreigabe. Vorbereitete Laneadressen und ihre Existenz sind getrennt von diesem Hostjoin.\n\n",
        source_link(
            "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/constants_v1.py"
        )
        + "\n\n",
        "Der Universefilter konsumiert die leere Menge `FORBIDDEN_FUTURES_BASE_ASSETS`. Der separate Literalwert `BTC_EXCLUDED=True` im Universe-Constantsmodul stimmt als Metadatenbezeichnung nicht mit diesem konsumierten Filterset überein. Assetzulassung folgt im gezeigten Filter dem Set und den übrigen Futures-/Qualitätsbedingungen.\n\n",
        source_link("src/trading/master_v2/double_play_futures_input.py")
        + " · "
        + source_link("src/ops/governed_futures_universe_producer_v1/eligibility_v1.py")
        + " · "
        + source_link("src/ops/governed_futures_universe_producer_v1/constants_v1.py")
        + "\n\n",
        "## Numerischer Marktmodellpfad\n\n",
        "`train_market_ols_model_v1` liest abgeschlossene Originaljobs, bindet zugelassene Featurewerte und den tatsächlichen realisierten Logreturn, trennt zeitliches Trainingspräfix und Validation und speichert numerische Koeffizienten mit Parent- und Inhaltsbindung. Neue kumulative Originalevidence ist für eine nächste Version erforderlich. `forecast_from_market_ols_model_v1` lädt diese Gewichte, berechnet einen Payload und verwendet den Original-Forecastfreeze. `read_market_ols_model_v1` und `read_market_model_forecast_v1` sind Cold-Read-Einstiege. Der Providerreceipt und der Freeze haben getrennte Inferenzrollen.\n\n",
        "Die gespeicherte Streuung ist eine empirische Held-out-Residualstreuung. Dieser caller-invoked Offlinepfad setzt keinen Trainingsscheduler, keine automatische Promotion und keine produktive Parameteränderung voraus.\n\n",
        source_link(
            "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_ols_next_forecast_v1.py"
        )
        + "\n\n",
        "## Quell- und Ausführungsgrenze\n\n",
        "S6 sequenziert begrenzte Governedcycles und beendet den benannten ENTER-Pfad an `PRE_EXTERNAL_EFFECT`. Budget-, Cursor-, Pending-, MI- und OLS-Stores haben eigene Identitäten und Writer. Im Dateikatalog vorhandene Reports ersetzen keine Beobachtung des laufenden Systems. Die Dokumentation aktiviert keinen Prozess und erteilt keine Order-, Kapital- oder Credentialberechtigung.\n\n",
        source_link(
            "src/ops/full_core_live_path_composition_root_v1/current_productive_governed_continuous_cycle_orchestrator_v1.py"
        )
        + "\n",
    ]
    index = (
        "# Quellenindex des fixierten Atlas\n\nQuelle: "
        + model["source_tag"]
        + " · `"
        + model["source_commit"]
        + "`.\n\n"
    )
    index += (
        "Alle "
        + str(model["file_count"])
        + " Quellpfade stehen im [Dateikatalog](../source/current-files.jsonl.gz). Die Angaben beziehen sich auf den fixierten Git-Baum. Die Dokumentationsprojektionen werden aus diesem Bestand dargestellt.\n\n## Verteilung nach oberstem Pfad\n\n"
    )
    index += "".join(
        "- `" + k + "`: " + str(v) + " Dateien.\n" for k, v in model["top_level_counts"].items()
    )
    return {"SYSTEM_ATLAS.md": "".join(parts), "SOURCE_INDEX.md": index}


DOC_TOOLING = {
    "tests/ops/test_current_law_impact_map_v1.py",
    "scripts/ops/current_law_impact_map_v1.py",
    "scripts/ops/check_current_law_impact_v1.py",
    "scripts/ops/current_system_interaction_authority_map_v1.py",
    "scripts/ops/validate_current_system_census_graph_v1.py",
    "scripts/ops/law_map_v1/impact_v1.py",
    "scripts/ops/law_map_v1/ucs_evidence_binding_v1.py",
    "scripts/ops/law_map_v1/remaining_29_evidence_exhaustion_v1.py",
    ".github/workflows/map_currency_gate_v1.yml",
    "config/ops/docs_truth_map.yaml",
    "config/ops/repo_truth_claims.yaml",
    "config/governance/current_law_impact_map_v1/source_v1.json",
    "config/governance/current_law_impact_map_v1/schema_v1.json",
    "config/governance/current_law_impact_map_v1/impact_candidates_v1.json",
    "config/governance/current_law_impact_map_v1/impact_adjudication_v1.json",
}
LAW_NAMES = {
    "law_reference_index": "law_reference_index_v1.md",
    "semantic_object_index": "semantic_object_index_v1.md",
    "unknown_and_conflict": "unknown_and_conflict_v1.md",
    "surface_census": "surface_census_v1.md",
    "law_change_impact": "LAW_CHANGE_IMPACT.md",
}
LAW_ROOT = "docs/governance/current_law_impact_map_v1/generated"
DEVELOPMENT_BINDING = ATLAS + "source/development-binding-v1.json"


def validate_development_binding(root, model, frozen, changed, extras, cleanup):
    """Bind an explicit development delta without rewriting the frozen inventory."""
    unexpected = {p for p in changed + extras if not allowed(p, cleanup)}
    path = root / DEVELOPMENT_BINDING
    if not path.is_file():
        assert not unexpected, ["UNSCOPED_CHANGE", *sorted(unexpected)]
        return {}
    binding = json.loads(path.read_bytes())
    assert binding["schema"] == "peaktrade.atlas_development_binding.v1"
    assert binding["authority"] == binding["runtime_authorization_effect"] == "NONE"
    assert binding["frozen_source_commit"] == model["source_commit"]
    parent = binding["development_parent_commit"]
    assert re.fullmatch(r"[0-9a-f]{40}", parent), "DEVELOPMENT_PARENT_INVALID"
    git(root, "merge-base", "--is-ancestor", parent, "HEAD")
    rows = binding["files"]
    assert isinstance(rows, list) and rows, "DEVELOPMENT_BINDING_EMPTY"
    indexed = {}
    actual_changes = set(changed + extras)
    if actual_changes & FILEGATE_DEPENDENCY_DELTA.keys():
        assert FILEGATE_DEPENDENCY_DELTA.keys() <= actual_changes
        assert all(
            digest((root / name).read_bytes()) == expected
            for name, expected in FILEGATE_DEPENDENCY_DELTA.items()
        ), "FILEGATE_DEPENDENCY_BUNDLE_DRIFT"
    for row in rows:
        rel = row["path"]
        assert (
            isinstance(rel, str)
            and not Path(rel).is_absolute()
            and ".." not in Path(rel).parts
            and rel == Path(rel).as_posix()
            and rel != DEVELOPMENT_BINDING
            and rel not in indexed
            and rel in actual_changes
        ), ["DEVELOPMENT_PATH_INVALID", rel]
        assert (
            rel.startswith(("src/", "tests/", "docs/", "scripts/", ".github/workflows/"))
            or rel == "config/governance/clean_core_seal_manifest_v1.json"
            or rel == "config/governance/technical_canonical_wiring_authorization_v1.json"
            or rel == "static/js/market_surface_greenfield_v1/surface_app_v1.js"
            or rel in FILEGATE_DEPENDENCY_DELTA
        ), rel
        expected_before = frozen.get(rel, {}).get("sha256")
        assert row["before_sha256"] == expected_before, ["DEVELOPMENT_BASE_MISMATCH", rel]
        file = root / rel
        assert file.is_file() and not file.is_symlink(), ["DEVELOPMENT_SOURCE_MISSING", rel]
        assert row["sha256"] == digest(file.read_bytes()), ["DEVELOPMENT_SOURCE_DRIFT", rel]
        indexed[rel] = row
    assert unexpected <= indexed.keys(), ["UNSCOPED_CHANGE", *sorted(unexpected - indexed.keys())]
    return indexed


def allowed(path, cleanup=None):
    base = path.startswith(ATLAS) or path in {MASTER, MAP, RATIFICATION} | TOOLS
    if cleanup is None:
        return base
    named = {
        p["path"]
        for p in cleanup["removed"]
        + cleanup["navigation_edits"]
        + cleanup.get("externalized_archives", [])
    }
    return base or path in named | DOC_TOOLING or path.startswith(LAW_ROOT + "/")


def historical_archive_scope(rel):
    return (
        rel.startswith("backups/local_checkpoints/20261103T173259Z/")
        or rel.startswith("docs/ops/evidence/obsidian_repo_alignment_2026_11_06/archives/")
        or rel.startswith(
            "docs/ops/evidence/self_learning_full_original_corpus_and_contract_reconciliation_v1_2026_11_04/"
        )
        or ("/" not in rel and rel.startswith("DISASTER_RECOVERY_"))
        or rel
        in {
            "RESTORE_INSTRUCTIONS.txt",
            "sidebar_before.png",
            "scripts/ops/verify_self_learning_restoration_v1.py",
        }
    ) and ".." not in Path(rel).parts


def validate_cleanup(root, model, frozen):
    path = root / ATLAS / "source/documentation-cleanup.json"
    if not path.is_file():
        return None
    cleanup = json.loads(path.read_bytes())
    assert cleanup["schema"] == "peaktrade.documentation_cleanup.v1"
    assert cleanup["source_commit"] == model["source_commit"]
    # After a clean cut, transfer receipts are bound in the new baseline itself.
    retired = {}
    if any(row["path"] not in frozen for row in cleanup["removed"]):
        baseline = json.loads(
            git(
                root,
                "show",
                model["source_commit"] + ":" + ATLAS + "source/documentation-cleanup.json",
            )
        )
        retired = {
            row["path"]: row
            for row in baseline["removed"] + baseline.get("externalized_archives", [])
        }
    removed = cleanup["removed"]
    assert len({p["path"] for p in removed}) == len(removed)
    for row in removed:
        rel = row["path"]
        assert (
            rel.startswith("docs/") and not rel.startswith(ATLAS)
        ) or rel == "config/governance/current_system_census_graph_v1/README.md"
        assert rel not in {MASTER, MAP, RATIFICATION}
        bound = frozen[rel] if rel in frozen else retired[rel]
        assert row["sha256"] == bound["sha256"]
        assert row["git_blob_oid"] == bound["git_blob_oid"]
        assert not (root / rel).exists(), ["RETIRED_MAP_REAPPEARED", rel]
    for row in cleanup["navigation_edits"]:
        rel = row["path"]
        assert (
            (rel.startswith("docs/") and rel.endswith(".md"))
            or rel == "README.md"
            or rel in DOC_TOOLING
        )
        assert digest((root / rel).read_bytes()) == row["after_sha256"], rel
    archive_paths = set()
    for row in cleanup.get("externalized_archives", []):
        rel = row["path"]
        assert rel not in archive_paths
        archive_paths.add(rel)
        assert historical_archive_scope(rel), ["ARCHIVE_SCOPE_NOT_HISTORICAL", rel]
        bound = frozen[rel] if rel in frozen else retired[rel]
        assert row["sha256"] == bound["sha256"], rel
        assert row["bytes"] == bound["bytes"], rel
        assert row["role"] == "HISTORICAL_ARCHIVE_NOT_CURRENT_PRODUCT_INPUT"
        assert not (root / rel).exists(), ["ARCHIVED_PAYLOAD_REAPPEARED", rel]
        assert Path(row["archive_path"]).is_relative_to(cleanup["external_archive_root"])
    return cleanup


def validate(root, check_outputs=True):
    if not __debug__:
        raise RuntimeError("Atlas verification requires enabled assertions.")
    m = load(root)
    assert m["schema"] == "peaktrade.current_frozen_atlas.v1"
    assert m["authority"] == "NONE" and m["runtime_authorization_effect"] == "NONE"
    assert (
        git(root, "rev-parse", m["source_tag"] + "^{commit}").decode().strip() == m["source_commit"]
    )
    assert (
        git(root, "rev-parse", m["source_commit"] + "^{tree}").decode().strip() == m["source_tree"]
    )
    for name, info in m["files"].items():
        assert digest((root / ATLAS / "source" / name).read_bytes()) == info["sha256"], name
    inventory = records(root, "current-files.jsonl.gz")
    by_path = {r["path"]: r for r in inventory}
    frozen = {}
    for entry in git(root, "ls-tree", "-r", "-z", m["source_commit"]).split(b"\0"):
        if entry:
            meta, path = entry.split(b"\t", 1)
            frozen[path.decode()] = meta.decode().split()[2]
    assert len(inventory) == len(by_path) == m["file_count"]
    assert {k: v["git_blob_oid"] for k, v in by_path.items()} == frozen
    cleanup = validate_cleanup(root, m, by_path)
    changed = git(root, "diff", "--name-only", m["source_commit"], "--").decode().splitlines()
    extras = git(root, "ls-files", "--others", "--exclude-standard").decode().splitlines()
    development = validate_development_binding(root, m, by_path, changed, extras, cleanup)
    symbols = records(root, "current-symbols.jsonl.gz")
    imports = records(root, "current-imports.jsonl.gz")
    assert len(symbols) == m["named_definitions"]
    assert len(imports) == m["lexical_imports"]
    assert all(r["path"] in by_path for r in symbols + imports)
    for d in m["domains"]:
        for layer in d["layers"]:
            path = layer["source"]
            assert path in by_path or any(p.startswith(path.rstrip("/") + "/") for p in by_path), (
                path
            )
            if path in by_path:
                expected = development.get(path, by_path[path])["sha256"]
                assert digest((root / path).read_bytes()) == expected, path
    for claim in m["constant_claims"]:
        tree = ast.parse((root / claim["path"]).read_bytes())
        matching = []
        for n in tree.body:
            targets = (
                n.targets
                if isinstance(n, ast.Assign)
                else [n.target]
                if isinstance(n, ast.AnnAssign)
                else []
            )
            if any(isinstance(t, ast.Name) and t.id == claim["name"] for t in targets):
                value = n.value
                matching.append(
                    []
                    if isinstance(value, ast.Call)
                    and isinstance(value.func, ast.Name)
                    and value.func.id == "frozenset"
                    and not value.args
                    else ast.literal_eval(value)
                )
        assert matching == [claim["value"]], claim
    rat = json.loads((root / RATIFICATION).read_bytes())
    assert rat["source_commit"] == m["source_commit"]
    assert rat["canonical_document_sha256"] == digest((root / MASTER).read_bytes())
    documents = [
        root / MASTER,
        root / MAP,
        root / ATLAS / "README.md",
        root / ATLAS / "ATLAS_AUTHORITY_AND_USAGE.md",
    ]
    if check_outputs:
        for name, expected in views(m).items():
            p = root / ATLAS / "generated" / name
            assert p.read_text() == expected, ["GENERATED_DRIFT", name]
            documents.append(p)
    policy_result = {}
    if m.get("policy_files"):
        projection = run_path(str(root / ATLAS / "policy_projection.py"))
        law = json.loads(
            (root / "config/governance/current_law_impact_map_v1/source_v1.json").read_bytes()
        )
        policy_result = projection["validate_policy_inventory"](root, law)
        assert policy_result["policy_files"] == m["policy_files"]
        if check_outputs:
            for key, expected in projection["render_law_views"](law, root).items():
                p = root / LAW_ROOT / LAW_NAMES[key]
                assert p.read_text() == expected, ["LAW_GENERATED_DRIFT", p]
                documents.append(p)
    link_count = 0
    for p in documents:
        text = p.read_text()
        assert not re.search(
            r"OWNER_GO_STATUS=CONSUMED|LAST_MERGED_PR=|CURRENT_ORIGIN_MAIN_SHA=|origin/main@|Superseded static repair|### 11\.13\.5",
            text,
        ), p
        for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", text):
            if "://" in target:
                continue
            path, _, fragment = target.strip("<>").partition("#")
            resolved = (p.parent / path).resolve() if path else p
            assert resolved.exists(), [p, target]
            if fragment and resolved.suffix == ".md":
                headings = re.findall(r"^#{1,6}\s+(.+)$", resolved.read_text(), re.M)
                anchors = {re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings}
                assert fragment in anchors, [p, target, "MISSING_ANCHOR"]
            link_count += 1
    coverage = {}
    if (root / ATLAS / "source/boundaries.json").is_file():
        projection = run_path(str(root / ATLAS / "coverage.py"))
        boundary, assignments, _, _, coverage = projection["load_coverage"](root, m)
        if check_outputs:
            assert (root / projection["VIEW"]).read_text() == projection["render_boundaries"](
                boundary, assignments, m
            ), "ATLAS_BOUNDARIES_VIEW_DRIFT"
    return {
        "result": "PASS",
        "source_commit": m["source_commit"],
        "frozen_files": len(inventory),
        "python_modules": m["python_modules_parsed"],
        "named_definitions": len(symbols),
        "lexical_imports": len(imports),
        "areas": len(m["domains"]),
        "checked_links": link_count,
        "product_paths_unchanged": not any(p.startswith("src/") for p in development),
        "development_bound_files": len(development),
        "catalog_scope": "FROZEN_SOURCE_SNAPSHOT",
        "development_binding": DEVELOPMENT_BINDING if development else None,
        "runtime_authorization_effect": "NONE",
        "removed_extra_map_files": len(cleanup["removed"]) if cleanup else 0,
        "externalized_historical_files": len(cleanup.get("externalized_archives", []))
        if cleanup
        else 0,
        **policy_result,
        **coverage,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["generate", "check", "impact", "frozen"])
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    model = load(root)
    if args.mode == "generate":
        for name, text in views(model).items():
            (root / ATLAS / "generated" / name).write_text(text)
        if (root / ATLAS / "source/boundaries.json").is_file():
            projection = run_path(str(root / ATLAS / "coverage.py"))
            boundary, assignments, _, _, _ = projection["load_coverage"](root, model)
            (root / projection["VIEW"]).write_text(
                projection["render_boundaries"](boundary, assignments, model)
            )
        if model.get("policy_files"):
            projection = run_path(str(root / ATLAS / "policy_projection.py"))
            law = json.loads(
                (root / "config/governance/current_law_impact_map_v1/source_v1.json").read_bytes()
            )
            for key, text in projection["render_law_views"](law, root).items():
                (root / LAW_ROOT / LAW_NAMES[key]).write_text(text)
    result = validate(root)
    if args.mode == "frozen":
        tag = model["system_freeze_tag"]
        commit = git(root, "rev-parse", tag + "^{commit}").decode().strip()
        assert git(root, "rev-parse", "HEAD").decode().strip() == commit
        assert not git(root, "diff", "--name-only", commit, "--").strip()
        verified_files = 0
        for entry in git(root, "ls-tree", "-r", "-z", commit).split(b"\0"):
            if not entry:
                continue
            meta, rel = entry.split(b"\t", 1)
            mode, kind, oid = meta.decode().split()
            path = root / rel.decode()
            assert kind == "blob", ["UNSUPPORTED_FROZEN_ENTRY", rel]
            if mode == "120000":
                assert path.is_symlink(), path
                raw = os.fsencode(os.readlink(path))
            else:
                assert path.is_file() and not path.is_symlink(), path
                assert bool(path.stat().st_mode & 0o111) == (mode == "100755"), path
                raw = path.read_bytes()
            actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            assert actual == oid, ["FROZEN_FILE_BYTES_CHANGED", rel]
            verified_files += 1
        assert not git(root, "ls-files", "--others", "--exclude-standard").strip()
        ignored = (
            git(
                root,
                "ls-files",
                "--others",
                "--ignored",
                "--exclude-standard",
                "--directory",
                "--no-empty-directory",
            )
            .decode()
            .splitlines()
        )
        assert all(p == ".venv/" for p in ignored), ["UNSCOPED_LOCAL_FILES", ignored]
        disposition = json.loads((root / ATLAS / "source/successor-disposition.json").read_bytes())
        for key, value in disposition.get("protected_git_configuration", {}).items():
            assert key in {
                "core.abbrev",
                "remote.origin.fetch",
                "remote.origin.tagOpt",
                "remote.origin.skipDefaultUpdate",
                "remote.origin.skipFetchAll",
            }
            assert git(root, "config", "--get", key).decode().strip() == value, key
        comparison = next(
            x["commit"]
            for x in disposition["required_git_references"]
            if x["reference"] == "refs/remotes/origin/main"
        )
        expected = {commit, model["source_commit"], comparison}
        assert set(git(root, "rev-list", "--all").decode().splitlines()) == expected
        local_commits = {
            line.split()[1]
            for line in git(
                root, "cat-file", "--batch-all-objects", "--batch-check=%(objecttype) %(objectname)"
            )
            .decode()
            .splitlines()
            if line.startswith("commit ")
        }
        assert local_commits == expected, ["EXTRA_LOCAL_COMMIT_OBJECTS", local_commits - expected]
        assert git(root, "worktree", "list", "--porcelain").decode().count("worktree ") == 1
        expected_refs = {
            "refs/heads/main",
            "refs/remotes/origin/main",
            "refs/tags/" + model["source_tag"],
            "refs/tags/" + tag,
        }
        assert (
            set(git(root, "for-each-ref", "--format=%(refname)").decode().splitlines())
            == expected_refs
        )
        result.update(
            system_freeze_tag=tag,
            system_freeze_commit=commit,
            complete_working_tree_matches_freeze=True,
            verified_working_tree_files=verified_files,
            local_commit_count=len(expected),
            local_historical_worktrees=0,
            allowed_nonversioned_dependency=".venv/",
        )
    if args.mode == "impact":
        print("ATLAS_IMPACT=UPDATED\nSYSTEM_ATLAS_DRIFT_DETECTED=false")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
