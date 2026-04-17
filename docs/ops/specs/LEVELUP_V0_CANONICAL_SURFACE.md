# LevelUp v0 — Canonical Ops/Spec Surface (additive)

**status:** active  
**last_updated:** 2026-04-17  
**purpose:** Kanonische **Auffindbarkeit** und **Claim-Grenzen** für die kleine LevelUp-v0-Schicht (Manifest-/IO-/CLI-Grundlage). Keine neue Governance-, Risk- oder Safety-Autorität.

**docs_token:** `DOCS_TOKEN_LEVELUP_V0_CANONICAL_SURFACE`

## 1) Zweck

LevelUp **v0** ist im Repo aktuell eine **kleine, additive** Grundlage: typisierte Manifest-Modelle, JSON-Lese-/Schreib-Hilfen und ein minimales CLI für Validierung und leere Template-Ausgabe. Sie dient der **Evidence-first**-Ausrichtung (Slice-Metadaten und Zeiger unter `out/ops/`), **ohne** Live-Trading, Broker-I/O oder Gate-Unlocks zu behaupten (siehe Modul-Docstrings in `src/levelup/v0_models.py`).

## 2) Scope (strikt)

| Bereich | In-Scope für diese Datei |
|--------|---------------------------|
| **Modelle** | `EvidenceBundleRefV0`, `SliceContractV0`, `LevelUpManifestV0` — nur soweit aus `src/levelup/v0_models.py` ablesbar. |
| **JSON/IO** | `read_manifest`, `write_manifest` in `src/levelup/v0_io.py` — **offline**, repo-lokale Pfade. |
| **CLI** | Nur das, was `src/levelup/cli.py` sowie `tests/levelup/test_v0_manifest.py` und `tests/levelup/test_v0_validate_cli.py` eindeutig belegen (siehe Abschnitt 6). |
| **Tests** | `tests/levelup/test_v0_manifest.py`, `tests/levelup/test_v0_validate_cli.py` als Verifikationsanker; Drift-Check für das committed JSON Schema (siehe Abschnitt 6). |

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
| `src/levelup/v0_models.py` | Pydantic-Modelle, Schema-String `levelup&#47;manifest&#47;v0`. |
| `src/levelup/v0_io.py` | JSON einlesen/ausgeben (Path). |
| `src/levelup/cli.py` | CLI-Einstieg (`validate`, `dump-empty`, `format`, `canonical-check`, `export-json-schema`). |
| `schemas/levelup/levelup_manifest_v0.schema.json` | Repo-committed JSON Schema für `LevelUpManifestV0` (gleiche Quelle wie `export-json-schema` / `levelup_manifest_v0_json_schema()` in `v0_models.py`). |
| `scripts/ops/sync_levelup_manifest_json_schema.py` | Regeneriert die committed Schema-Datei nach Modelländerungen. |
| `tests/levelup/test_v0_manifest.py` | Roundtrip-, Validierungs- und Basis-CLI-Tests. |
| `tests/levelup/test_v0_validate_cli.py` | Subprozess-Tests für `validate`-Exit-Codes und JSON-Fehlerobjekt. |

## 6) Current verified surface (eng, aus Code/Test)

Alles Folgende bezieht sich auf den **Ist**-Stand der genannten Dateien:

- **Schema:** `LevelUpManifestV0.schema_version` ist fix `levelup&#47;manifest&#47;v0` (`src/levelup/v0_models.py`).
- **Committed JSON Schema (reviewbar):** `schemas/levelup/levelup_manifest_v0.schema.json` materialisiert das Pydantic-JSON-Schema für `LevelUpManifestV0`. Synchronisation: `uv run python scripts/ops/sync_levelup_manifest_json_schema.py` (nutzt dieselbe Erzeugung wie `export-json-schema` über `levelup_manifest_v0_json_schema()`). Drift-Tests: `test_committed_levelup_manifest_json_schema_matches_model` und Abgleich in `test_cli_export_json_schema_success` in `tests/levelup/test_v0_manifest.py`.
- **Manifest-Titel:** `LevelUpManifestV0.title` wird an den Enden getrimmt; nur nicht-leer nach dem Trim ist gültig (Leer- bzw. Nur-Whitespace-Titel werden abgewiesen). Positiv-/Negativfälle: `test_manifest_root_title_strips_surrounding_whitespace`, `test_manifest_root_title_rejects_empty_after_strip` in `tests/levelup/test_v0_manifest.py`.
- **Slice-IDs:** `slice_id`-Werte müssen innerhalb eines Manifests **eindeutig** sein (`test_manifest_rejects_duplicate_slice_id` in `tests/levelup/test_v0_manifest.py`).
- **Evidence-Pfade:** `EvidenceBundleRefV0.relative_dir` muss mit `out/ops/` beginnen; Traversal wird abgewiesen (Validator in `v0_models.py`); abgelehnte Beispiele und Roundtrip-Verhalten sind in `tests/levelup/test_v0_manifest.py` abgedeckt.
- **IO:** `read_manifest` nutzt `model_validate_json` auf Dateiinhalt; `write_manifest` schreibt formatiertes JSON (inkl. Elternverzeichnis-Anlage).
- **CLI (read-only Doku):** Einstieg `python -m src.levelup.cli` mit Unterbefehlen `validate <manifest>`, `dump-empty <manifest>`, `format <manifest>`, `canonical-check <manifest>` und `export-json-schema` (`argparse`-`prog` in `cli.py`). **validate** schreibt **genau eine JSON-Zeile auf stdout** (stderr leer im erwarteten Fehlerpfad):
  - **Erfolg:** `ok: true`, plus `schema`, `slices` (Anzahl).
  - **Fehler:** `ok: false`, `error` (`input` | `validation`), `reason` (z. B. `json_parse_failed`, `manifest_read_failed`, `model_validation_failed`), knappe `message`; bei `validation` zusätzlich `issues` (gekürzte Pydantic-Fehlerliste).
  - **Exit-Codes:** `0` = Validierung ok; `2` = Usage/Eingabe (u. a. fehlende Datei, Lesefehler, ungültiges JSON, UTF-8-Dekodierung); `3` = JSON parsebar, Modell-/Schema-Validierung fehlgeschlagen.
  - **dump-empty:** schreibt ein leeres Manifest; **Erfolg:** eine JSON-Zeile auf stdout mit `ok: true`, `wrote` (Pfad), Exit `0`, stderr leer. **Fehler (Schreib-/Pfadproblem):** eine JSON-Zeile mit `ok: false`, `error: input`, `reason` (`target_path_is_directory` wenn der Zielpfad ein Verzeichnis ist, sonst bei `OSError` am Schreibpfad typischerweise `manifest_write_failed`), `message`; Exit `2`, stderr leer im erwarteten Operator-Pfad.
  - **format:** liest ein bestehendes Manifest, validiert gegen `LevelUpManifestV0` und schreibt es kanonisch an denselben Pfad zurück. **Erfolg:** eine JSON-Zeile mit `ok: true`, `wrote`, `schema`, `slices`, Exit `0`, stderr leer. **Fehler:** Read-/Decode-/JSON-Inputfehler wie bei `validate` (`error: input`, Exit `2`), Modell-/Schemafehler wie bei `validate` (`error: validation`, `reason: model_validation_failed`, Exit `3`), sowie Schreibfehler (`error: input`, `reason: manifest_write_failed` oder `target_path_is_directory`, Exit `2`).
  - **canonical-check (read-only):** liest und validiert ein bestehendes Manifest, vergleicht den aktuellen Dateiinhalt gegen die kanonische Serialisierung (gleiche Normalisierung wie `write_manifest`/`format`), schreibt **nichts** zurück. **Erfolg:** eine JSON-Zeile mit `ok: true`, `canonical: true`, `schema`, `slices`, Exit `0`, stderr leer. **Fehler:** Input-/Read-/Decode-/JSON-Pfade wie bei `validate` (Exit `2`); Modell-/Schemafehler wie bei `validate` (Exit `3`); valide aber nicht-kanonische Datei: `ok: false`, `error: validation`, `reason: manifest_not_canonical`, `canonical: false`, Exit `3`.
  - **export-json-schema:** exportiert das JSON-Schema von `LevelUpManifestV0` als **eine** JSON-Zeile auf stdout (`ok: true`, `schema`, `json_schema`), Exit `0`, stderr leer im Erfolgsfall.
  - Subprozess-Checks: `test_cli_validate_and_dump_empty`, `test_cli_dump_empty_target_path_is_directory`, `test_cli_dump_empty_not_writable_target_file` in `tests/levelup/test_v0_manifest.py`, `test_v0_validate_cli.py` in `tests/levelup/`.
  - Zusätzliche format-Checks: `test_cli_format_success_canonical_rewrite`, `test_cli_format_invalid_manifest_model_validation_failed`, `test_cli_format_not_writable_target_file` in `tests/levelup/test_v0_manifest.py`.
  - Zusätzliche canonical-check-Checks: `test_cli_canonical_check_already_canonical`, `test_cli_canonical_check_valid_but_not_canonical`, `test_cli_canonical_check_invalid_manifest_model_validation_failed`, `test_cli_canonical_check_empty_file_json_parse_failed` in `tests/levelup/test_v0_manifest.py`.
  - Zusätzlicher export-json-schema-Check: `test_cli_export_json_schema_success` in `tests/levelup/test_v0_manifest.py`.

**Non-claims:** Keine Aussage über Integration in Deployments, CI-Pflicht oder Freigabeprozesse — sofern nicht separat und repo-evidenced dokumentiert.
