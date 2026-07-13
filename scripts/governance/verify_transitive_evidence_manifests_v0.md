# Canonical Owner: Transitive Evidence MANIFEST Verifier v0

## Owner

- **Script**: `scripts/governance/verify_transitive_evidence_manifests_v0.py`
- **Test owner**: `tests/governance/test_verify_transitive_evidence_manifests_v0.py`
- **Role**: technischer, offline-only Verifier-Owner (kein Runbook, keine Governance-SSOT)

## Purpose

Offline-only, non-authorizing CLI-Tool zur **transitiven** Verifikation historischer Evidence-Bundles:

- **Read-only** gegenüber Repo, Archive und Source-Bundles (keine Mutation / kein Repair).
- **Extrahiert Bundle-Referenzen** aus explizit unterstützten Textartefakten innerhalb besuchter Bundles.
- **Kanonisiert Bundle-Identität** zu einem eindeutigen Bundle-Key (absoluter Verzeichnispfad).
- **Deterministische BFS-Traversierung** mit Queue/Visited und bounded Guards.
- **MANIFEST.sha256-Verifikation pro Bundle** über die repo-kanonische Primitive.
- **Checkpoint/Resume** (JSON, versioniertes Schema, atomic write).
- **Append-only Progress Log** (JSONL, run_id, monotone sequence).
- **Strukturierte Output-Artefakte** im gebundenen `--output-dir`.

## Hard boundaries

```text
OFFLINE_ONLY=true
NON_AUTHORIZING=true

REPOSITORY_MUTATION_FORBIDDEN=true
ARCHIVE_MUTATION_FORBIDDEN=true
SOURCE_BUNDLE_MUTATION_FORBIDDEN=true
SOURCE_MANIFEST_REGENERATION_FORBIDDEN=true
HISTORICAL_EVIDENCE_REPAIR_FORBIDDEN=true

ECONOMIC_EVALUATION_EXECUTED=false
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
BACKGROUND_WORKER=false
SELF_RESTART=false
ORDER_EFFECT=NONE
CREDENTIAL_EFFECT=NONE
```

Schreibzugriffe erfolgen ausschließlich in den per CLI gebundenen Output-/Log-/Checkpoint-Pfaden.

## CLI

Pflichtargumente:

```bash
python3 scripts/governance/verify_transitive_evidence_manifests_v0.py \
  --root-bundle <absolute path> \
  --archive-root <absolute path> \
  --output-dir <absolute path>
```

`--root-bundle` ist **repeatable** (mehrere Root-Bundles via mehrfaches Flag).

Optionale Argumente:

```text
--max-unique-bundles (default: 5000)
--max-queue-size (default: 5000)
--max-references-per-bundle (default: 500)
--resume-checkpoint <path>
--progress-log <path>
--reference-files <comma-separated basenames>
```

Nicht-CLI Defaults (konstant im Owner):

```text
max_file_size_bytes=524288
per_bundle_timeout_seconds=20
```

## Canonical bundle-key contract

- **Bundle-Key** ist der vom Owner normalisierte **absolute Verzeichnispfad** (ohne trailing slash).
- **Raw textual references** sind niemals Identität für Queue/Visited/Checkpoint/Progress.
- **Containment**: akzeptierte Bundle-Keys müssen **unterhalb** von `--archive-root` liegen.
- **Escape-Block**: Referenzen außerhalb von `--archive-root` werden fail-closed blockiert.
- **Alias-Normalisierung**: Wrapper (Markdown-Link/Code, Quotes, Whitespace, trailing slashes) werden normalisiert.
- **Self-reference** re-queued nicht.
- **Cycles terminieren** durch `visited` auf canonical keys.

## Deterministic traversal

- Traversal ist **BFS** (iterative Queue).
- Neu entdeckte canonical keys werden **sortiert**, bevor sie enqueue’d werden.
- Invarianten:

```text
QUEUE_USES_CANONICAL_BUNDLE_KEY=true
VISITED_USES_CANONICAL_BUNDLE_KEY=true
CHECKPOINT_USES_CANONICAL_BUNDLE_KEY=true
PROGRESS_LOG_USES_CANONICAL_BUNDLE_KEY=true
```

Determinismus (semantisch):

```text
SAME_INPUTS
AND SAME_ARCHIVE_CONTENT
AND SAME_REFERENCE_CONFIGURATION
AND SAME_LIMITS
THEN SEMANTIC_TRAVERSAL_RESULT_IDENTICAL=true
```

Run-spezifische Provenance-Felder (z.B. `run_id`, Timestamps, sequence) sind erwartbar variabel.

## Reference extraction

Extraktion erfolgt ausschließlich aus **explizit unterstützten** Textartefakten innerhalb eines Bundles:

- Basenames:
  - `final_report.txt`
  - `source_manifest_verification.txt`
  - `preflight.txt`
  - `closeout_report.txt`
  - `manifest_verification.txt`
  - `references.txt`
  - `MANIFEST.sha256` (wird nur als Textquelle gelesen; keine Regeneration)
- Suffixe (nur direkte Kinder-Dateien im Bundle-Verzeichnis):
  - `.json`, `.jsonl`, `.md`

Referenzen werden als **absolute Path-Kandidaten** aus Text extrahiert (kein Command-Parsing, keine Link-Opens).

Fail-closed:

- Datei größer als `max_file_size_bytes` → Guard/Run-Abbruch mit Checkpoint (falls möglich)
- NUL-Bytes im Text → `REFERENCE_PARSE_FAILED`

## Manifest verification

- `MANIFEST.sha256` muss im Bundle-Verzeichnis existieren, sonst `MANIFEST_MISSING`.
- Verifikation pro Bundle via repo-kanonischer Primitive in `scripts/ops/primary_evidence_retention_v0.py`
  (Funktion: `verify_manifest_sha256`).
- Keine Manifest-Regeneration, kein Repair.

## Limits and fail-closed behavior

Bounded Guards (CLI/konstant):

- `max_unique_bundles`
- `max_queue_size`
- `max_references_per_bundle`
- `max_file_size_bytes` (konstant)
- `per_bundle_timeout_seconds` (konstant; wallclock-Guard)

```text
GUARD_EXCEEDED_TERMINATES_RUN=true
PARTIAL_SUCCESS_MAY_NOT_BE_REPORTED_AS_COMPLETE_SUCCESS=true
CHECKPOINT_MISMATCH_FAILS_CLOSED=true
PATH_ESCAPE_FAILS_CLOSED=true
```

## Exit codes (stable)

```text
0 = complete success
1 = manifest/reference verification failure
2 = invalid invocation or unsafe path
3 = bounded guard exceeded
4 = checkpoint invalid/corrupt (inkl. progress-log invalid)
5 = internal deterministic contract violation
```

## Checkpoint and resume

- Checkpoint: `checkpoint.json` im `--output-dir`
- Versioniertes Schema: `schema_version`
- Enthält canonical keys für `queue` und `visited`
- Bindet `archive_root`, `root_bundle` und `limits`
- Resume fail-closed bei:
  - Schema mismatch
  - `archive_root` mismatch
  - `root_bundle` mismatch
  - Limits mismatch
  - invalid/outside-root references in checkpoint
- Atomic write: tempfile + fsync + replace

## Progress log

- Default: `progress.jsonl` im `--output-dir` (oder per `--progress-log`)
- JSONL append-only, `run_id` pro Lauf, `sequence` streng monoton pro Lauf
- Fail-closed bei:
  - korrupten JSON-Zeilen im existierenden Log
  - Wiederverwendung derselben `run_id`

Pflichtfelder pro Record:

```text
schema_version
timestamp_utc
run_id
sequence
event_type
```

Optional (je Event): `bundle_key`, `bundle_path`, `parent_bundle_key`, `result`, `reason_code`, `counts`.

## Output artifacts

Im `--output-dir`:

- `run_contract.json`
- `bundle_results.jsonl`
- `graph_summary.json`
- `checkpoint.json`
- `progress.jsonl` (oder `--progress-log`)
- `final_report.txt`

## Import contract

```text
IMPORT_SIDE_EFFECT_FREE=true
```

Import erzeugt keine Files und startet keinen Run; Ausführung erfolgt nur über `main()` / CLI.

## Non-execution / no-mutation contract (compact)

```text
OFFLINE_ONLY=true
REPOSITORY_MUTATION=false
ARCHIVE_MUTATION=false
SOURCE_BUNDLE_MUTATION=false
SOURCE_MANIFEST_REGENERATION=false
ECONOMIC_EVALUATION_EXECUTED=false
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
ORDER_EFFECT=NONE
CREDENTIAL_EFFECT=NONE
```

