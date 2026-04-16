# LevelUp v0 — Canonical Ops/Spec Surface (additive)

**status:** active  
**last_updated:** 2026-04-16  
**purpose:** Kanonische **Auffindbarkeit** und **Claim-Grenzen** für die kleine LevelUp-v0-Schicht (Manifest-/IO-/CLI-Grundlage). Keine neue Governance-, Risk- oder Safety-Autorität.

**docs_token:** `DOCS_TOKEN_LEVELUP_V0_CANONICAL_SURFACE`

## 1) Zweck

LevelUp **v0** ist im Repo aktuell eine **kleine, additive** Grundlage: typisierte Manifest-Modelle, JSON-Lese-/Schreib-Hilfen und ein minimales CLI für Validierung und leere Template-Ausgabe. Sie dient der **Evidence-first**-Ausrichtung (Slice-Metadaten und Zeiger unter `out/ops/`), **ohne** Live-Trading, Broker-I/O oder Gate-Unlocks zu behaupten (siehe Modul-Docstrings in `src/levelup/v0_models.py`).

## 2) Scope (strikt)

| Bereich | In-Scope für diese Datei |
|--------|---------------------------|
| **Modelle** | `EvidenceBundleRefV0`, `SliceContractV0`, `LevelUpManifestV0` — nur soweit aus `src/levelup/v0_models.py` ablesbar. |
| **JSON/IO** | `read_manifest`, `write_manifest` in `src/levelup/v0_io.py` — **offline**, repo-lokale Pfade. |
| **CLI** | Nur das, was `src/levelup/cli.py` und `tests/levelup/test_v0_manifest.py` eindeutig belegen (siehe Abschnitt 6). |
| **Tests** | `tests/levelup/test_v0_manifest.py` als Verifikationsanker. |

**Out-of-Scope:** LevelUp v1/vNext, Runtime-/E2E-Garantien, Produktions-Gates, Execution- oder Order-Autorität.

## 3) Claim-Disziplin

- **Ist (repo-evidenced):** Nur Aussagen, die sich direkt aus genannten Quelldateien oder dem Test ableiten lassen.
- **Intended / documented:** Geplante oder narrative Erweiterungen — klar als solche kennzeichnen, nicht als implementierte Garantie.
- **Unclear:** Offene Punkte explizit benennen; nicht als Fakt ausgeben.

Ausrichtung an den verbindlichen Vokabular-/Authority-/Provenance-Regeln: [`CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md`](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md) (Abschnitt 6 — Claim-Klassen). **Diese Datei** normiert keine zusätzlichen Authority-Reihenfolgen.

## 4) Authority-Hinweis

- **Diese Spezifikation definiert keine neue** Governance-, Risk-, Safety- oder Execution-Autorität.
- Bindende Canonical-Vocabulary-/Authority-/Provenance-Regeln bleiben in [`CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md`](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md).

## 5) Repo-Verweise (Quellen)

| Pfad | Rolle |
|------|--------|
| `src/levelup/__init__.py` | Öffentliche Re-Exports der v0-API. |
| `src/levelup/v0_models.py` | Pydantic-Modelle, Schema-String `levelup/manifest/v0`. |
| `src/levelup/v0_io.py` | JSON einlesen/ausgeben (Path). |
| `src/levelup/cli.py` | CLI-Einstieg (`validate`, `dump-empty`). |
| `tests/levelup/test_v0_manifest.py` | Roundtrip-, Validierungs- und CLI-Tests. |

## 6) Current verified surface (eng, aus Code/Test)

Alles Folgende bezieht sich auf den **Ist**-Stand der genannten Dateien:

- **Schema:** `LevelUpManifestV0.schema_version` ist fix `levelup/manifest/v0` (`src/levelup/v0_models.py`).
- **Evidence-Pfade:** `EvidenceBundleRefV0.relative_dir` muss mit `out/ops/` beginnen; Traversal wird abgewiesen (Validator in `v0_models.py`); abgelehnte Beispiele und Roundtrip-Verhalten sind in `tests/levelup/test_v0_manifest.py` abgedeckt.
- **IO:** `read_manifest` nutzt `model_validate_json` auf Dateiinhalt; `write_manifest` schreibt formatiertes JSON (inkl. Elternverzeichnis-Anlage).
- **CLI (read-only Doku):** Einstieg `python -m src.levelup.cli` mit Unterbefehlen `validate <manifest>` und `dump-empty <manifest>` (`argparse`-`prog` in `cli.py`). `validate` gibt eine JSON-Zeile mit `ok`, `schema`, `slices` aus; `dump-empty` schreibt ein leeres Manifest und gibt `ok`/`wrote` zurück. Subprozess-Checks: `test_cli_validate_and_dump_empty` in `tests/levelup/test_v0_manifest.py`.

**Non-claims:** Keine Aussage über Integration in Deployments, CI-Pflicht oder Freigabeprozesse — sofern nicht separat und repo-evidenced dokumentiert.
