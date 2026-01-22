## Deterministic Replay Pack (Bundle Contract) — Slice 3.1

### Ziel
Ein Replay Pack ist ein **versioniertes, hash-verifiziertes Bundle**, das eine Execution-Run deterministisch reproduzierbar macht:

- Export einer Run-Event-Quelle (Slice‑1 Execution Events) in ein Bundle
- Validierung (Schema + Hashes)
- Deterministische Replay-Ausführung (optional mit Invariant-Checks gegen erwartete Outputs)

### Bundle Layout (v1)

```text
replay_pack/
  manifest.json
  inputs/
    config_snapshot.json
    strategy_params.json                (optional)
  events/
    execution_events.jsonl
    market_data_refs.json               (optional; nur Referenzen, keine großen Rohdaten)
  outputs/
    expected_fills.jsonl                (optional; für --check-outputs)
    expected_positions.json             (optional; für --check-outputs)
  meta/
    env.json                            (optional)
    git.json                            (optional)
  hashes/
    sha256sums.txt
```

### Manifest v1 (Pflichtfelder)
Das Manifest ist kanonisches JSON (sortierte Keys, kein Whitespace) und enthält mindestens:

- contract_version: "1"
- bundle_id: deterministischer Identifier (sha256 aus Run-ID + Content-Hashes)
- run_id: string
- created_at_utc: ISO8601 (in Tests übersteuerbar)
- peak_trade_git_sha: string (oder "UNKNOWN")
- producer: object
  - tool: "pt_replay_pack"
  - version: string
- contents: list of objects
  - path: string (relativ zur Bundle-Root)
  - sha256: hex string (64)
  - bytes: int
  - media_type: string
- canonicalization: object
  - json: "sort_keys_utf8_no_ws"
  - jsonl: "one_object_per_line_sorted_keys_lf"
- invariants: object
  - has_execution_events: true
  - ordering: "event_time_utc_then_seq"

Optionale Felder (forward-compatible): instruments, timerange, data_refs, notes

### Hashing-Regeln
- sha256 über **Raw Bytes** der Datei
- hashes/sha256sums.txt ist **nach Pfad sortiert**, LF-only
- sha256sums.txt enthält **alle** Dateien außer sich selbst (inklusive manifest.json)

### Event Ordering (Determinismus)
Die Replay-Pack-Events in events/execution_events.jsonl enthalten die Felder:

- event_time_utc: ISO8601 (deterministischer Surrogat-Zeitstempel)
- seq: int (stabiler Tie-Breaker)

Das File ist sortiert nach (event_time_utc, seq) und kann daher streamend gelesen werden.

### CLI Usage

```bash
python scripts/execution/pt_replay_pack.py build --run-id-or-dir <RUN_DIR> --out <OUT_DIR> --include-outputs
python scripts/execution/pt_replay_pack.py validate --bundle <OUT_DIR>/replay_pack
python scripts/execution/pt_replay_pack.py replay --bundle <OUT_DIR>/replay_pack --check-outputs
```

### Market Data References (market_data_refs) — Slice 3.2
Bundles bleiben bewusst leichtgewichtig: Market Data wird **nicht** eingebettet, sondern nur referenziert.

#### Datei
Die Referenzen liegen optional in:

```text
events/market_data_refs.json
```

#### Supported Top-Level Shapes

```json
[
  { "ref_id": "mdref-0001", "kind": "bars", "symbol": "AAPL", "start_utc": "2026-01-01T00:00:00Z", "end_utc": "2026-01-01T06:00:00Z", "source": "local_cache", "locator": { "namespace": "peaktrade_cache", "dataset": "bars_1m" } }
]
```

```json
{
  "market_data_refs": [
    { "ref_id": "mdref-0001", "kind": "bars", "symbol": "AAPL", "start_utc": "2026-01-01T00:00:00Z", "end_utc": "2026-01-01T06:00:00Z", "source": "local_cache", "locator": { "namespace": "peaktrade_cache", "dataset": "bars_1m" } }
  ]
}
```

```json
{
  "schema_version": "MARKET_DATA_REFS_V1",
  "refs": [
    { "ref_id": "mdref-0001", "kind": "bars", "symbol": "AAPL", "start_utc": "2026-01-01T00:00:00Z", "end_utc": "2026-01-01T06:00:00Z", "source": "local_cache", "locator": { "namespace": "peaktrade_cache", "dataset": "bars_1m" } }
  ]
}
```

#### Offline Resolver (deterministisch)
Der Resolver nutzt ausschließlich lokale Filesystem-Quellen (kein HTTP/Netzwerk) und erzeugt einen deterministischen Report.

```bash
python scripts/execution/pt_replay_pack.py resolve-datarefs --bundle <OUT_DIR>/replay_pack --cache-root <CACHE_ROOT> --mode best_effort
python scripts/execution/pt_replay_pack.py resolve-datarefs --bundle <OUT_DIR>/replay_pack --cache-root <CACHE_ROOT> --mode strict
```

Report (default):

```text
meta/resolution_report.json
```

Replay mit optionalem Resolve-Schritt:

```bash
python scripts/execution/pt_replay_pack.py replay --bundle <OUT_DIR>/replay_pack --resolve-datarefs best_effort --cache-root <CACHE_ROOT>
python scripts/execution/pt_replay_pack.py replay --bundle <OUT_DIR>/replay_pack --resolve-datarefs strict --cache-root <CACHE_ROOT>
```

### Compare Report (Baseline vs Replay) — Slice 3.3
Ein Compare Report ist ein deterministisches JSON-Artefakt für CI und Ops, das DataRefs-Status und Replay-Invariants zusammenfasst.

```bash
python scripts/execution/pt_replay_pack.py compare --bundle <OUT_DIR>/replay_pack --generated-at-utc <ISO8601>
python scripts/execution/pt_replay_pack.py compare --bundle <OUT_DIR>/replay_pack --check-outputs --generated-at-utc <ISO8601>
```

Optional (inkl. Offline-DataRefs-Resolve vor dem Compare):

```bash
python scripts/execution/pt_replay_pack.py compare --bundle <OUT_DIR>/replay_pack --resolve-datarefs best_effort --cache-root <CACHE_ROOT> --generated-at-utc <ISO8601>
python scripts/execution/pt_replay_pack.py compare --bundle <OUT_DIR>/replay_pack --resolve-datarefs strict --cache-root <CACHE_ROOT> --generated-at-utc <ISO8601>
```

Default Output:

```text
meta/compare_report.json
```

### CI/OPS Wrapper + CI Artefakt — Slice 3.4
Für Ops und CI gibt es einen Wrapper, der Compare deterministisch ausführt und einen Report in einen festen Pfad schreibt.

Wrapper:

```text
scripts/ops/pt_replay_compare_ci.sh
```

Beispiel:

```bash
bash scripts/ops/pt_replay_compare_ci.sh --bundle <OUT_DIR>/replay_pack --generated-at-utc <ISO8601>
echo $?
```

CI:
- Workflow:

```text
.github/workflows/replay_compare_report.yml
```

- Artefakt Name:

```text
replay-compare-report
```

### Determinismus-Garantien (MUST)
- Stabile Sortierung (manifest.contents und execution_events)
- Kanonisches JSON/JSONL (sort_keys, separators, UTF-8, LF)
- Keine Floats in deterministischen Artefakten (hard error)
- Keine Wall-Clock-Abhängigkeit für created_at_utc im Default-Pfad (deterministisch aus erstem Event)

### Contract Hardening (v1.x)
Zusätzliche, strikt validierte Regeln (ohne Contract-Version-Bump):

- **Manifest Schema**: Pflichtfelder, Typen, Enums (canonicalization und invariants) werden strikt geprüft.
- **Float-forbidden**: Jede Float-Zahl irgendwo in Events oder Payload führt zu einem Hard Error.
- **LF-only**: manifest.json und hashes/sha256sums.txt müssen LF-only sein und mit LF enden (CRLF wird abgelehnt).
- **Hashes**: sha256sums.txt muss alle Dateien außer sich selbst enthalten (inklusive manifest.json) und nach Pfad sortiert sein.
- **Ordering Invariant**: events werden auf strikt monotones (event_time_utc, seq) geprüft; seq muss bei 0 starten und lückenlos sein.

### CLI Exit Codes (v1.x)

| Code | Meaning |
|------|---------|
| 0 | OK |
| 2 | Contract violation oder schema validation |
| 3 | Hash mismatch |
| 4 | Replay mismatch (check-outputs) |
| 5 | Unexpected exception |
| 6 | Missing required DataRef (strict) |

### Einschränkungen
- v1 ist auf Slice‑1 Events mit schema_version "BETA_EXEC_V1" fokussiert.
- market_data_refs ist bewusst nur ein Referenz-Container; keine großen Rohdaten im Bundle per Default.
