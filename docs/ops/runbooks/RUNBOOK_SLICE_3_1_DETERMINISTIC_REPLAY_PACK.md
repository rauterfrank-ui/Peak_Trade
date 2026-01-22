## RUNBOOK — Slice 3.1 Deterministic Replay Pack

### Entry Criteria
- Repo ist buildbar (lokal) und Tests laufen grundsätzlich
- Slice‑1 Execution Events existieren als JSONL (schema_version "BETA_EXEC_V1")
- Keine Live-Ausführung (Governance bleibt unverändert gesperrt)

### Phase 0 — Contract First
- Bundle Layout und Manifest v1 sind definiert
- Hashing- und Canonicalization-Regeln sind festgelegt
- Validierungsregeln + Fehlerklassen sind vorhanden

### Phase 1 — Build (Bundle erzeugen)

```bash
python scripts/execution/pt_replay_pack.py build --run-id-or-dir <RUN_DIR> --out <OUT_DIR> --include-outputs
```

Erwartung:
- Unter OUT_DIR entsteht ein Verzeichnis replay_pack
- replay_pack enthält manifest.json, events/execution_events.jsonl und hashes/sha256sums.txt

### Phase 2 — Validate (Schema + Hashes prüfen)

```bash
python scripts/execution/pt_replay_pack.py validate --bundle <OUT_DIR>/replay_pack
echo $?
```

Exit Codes:
- 0: ok
- 2: Contract violation oder schema validation
- 3: Hash mismatch
- 5: Unexpected exception

### Phase 3 — Replay (Deterministisch ausführen)

```bash
python scripts/execution/pt_replay_pack.py replay --bundle <OUT_DIR>/replay_pack
python scripts/execution/pt_replay_pack.py replay --bundle <OUT_DIR>/replay_pack --check-outputs
echo $?
```

### Phase 3.1 — DataRefs Resolver (Slice 3.2, optional)
Voraussetzung:
- Lokaler Cache ist verfügbar (kein Netzwerkzugriff).

Best-effort (Replay läuft weiter, Report enthält MISSING):

```bash
python scripts/execution/pt_replay_pack.py resolve-datarefs --bundle <OUT_DIR>/replay_pack --cache-root <CACHE_ROOT> --mode best_effort
```

Strict (Exit 6 bei fehlenden required Refs, Exit 3 bei sha256_hint mismatch):

```bash
python scripts/execution/pt_replay_pack.py resolve-datarefs --bundle <OUT_DIR>/replay_pack --cache-root <CACHE_ROOT> --mode strict
```

Replay inkl. Resolver:

```bash
python scripts/execution/pt_replay_pack.py replay --bundle <OUT_DIR>/replay_pack --resolve-datarefs best_effort --cache-root <CACHE_ROOT>
python scripts/execution/pt_replay_pack.py replay --bundle <OUT_DIR>/replay_pack --resolve-datarefs strict --cache-root <CACHE_ROOT>
```

Erwartete Outputs:
- Report wird standardmäßig unter:

```text
meta/resolution_report.json
```
- Strict bricht deterministisch ab, wenn required Refs fehlen oder Hash-Hints nicht passen.

### Phase 3.2 — Compare Report (Slice 3.3, optional)
Ziel:
- Deterministisches Compare-Artefakt für CI/Ops (Baseline vs Replay).

Minimal:

```bash
python scripts/execution/pt_replay_pack.py compare --bundle <OUT_DIR>/replay_pack --generated-at-utc <ISO8601>
```

Mit Output-Invariants (falls expected Outputs vorhanden):

```bash
python scripts/execution/pt_replay_pack.py compare --bundle <OUT_DIR>/replay_pack --check-outputs --generated-at-utc <ISO8601>
```

Mit Offline-DataRefs-Resolve:

```bash
python scripts/execution/pt_replay_pack.py compare --bundle <OUT_DIR>/replay_pack --resolve-datarefs best_effort --cache-root <CACHE_ROOT> --generated-at-utc <ISO8601>
python scripts/execution/pt_replay_pack.py compare --bundle <OUT_DIR>/replay_pack --resolve-datarefs strict --cache-root <CACHE_ROOT> --generated-at-utc <ISO8601>
```

Erwartete Outputs:
- Compare Report unter:

```text
meta/compare_report.json
```

Exit Codes:
- 0: ok
- 2: Contract- oder Validierungsfehler
- 3: Hash mismatch
- 4: Replay mismatch (check-outputs)
- 5: Unexpected exception
- 6: Missing required DataRef (nur bei strict)

### Phase 3.3 — CI/OPS Integration: Compare JSON (Slice 3.4)
Ziel:
- Compare deterministisch operationalisieren (Wrapper + CI Artefakt), ohne bestehendes Replay-Pack Verhalten zu ändern.
- Kein Netzwerkzugriff: Compare arbeitet offline (optional mit lokalem Cache für DataRefs).

#### Lokaler Ops Run (Wrapper)
Wrapper Script:

```text
scripts/ops/pt_replay_compare_ci.sh
```

Minimal (deterministischer Timestamp erforderlich):

```bash
bash scripts/ops/pt_replay_compare_ci.sh --bundle <BUNDLE_DIR> --generated-at-utc <ISO8601>
echo $?
```

Mit Output-Invariants:

```bash
bash scripts/ops/pt_replay_compare_ci.sh --bundle <BUNDLE_DIR> --check-outputs --generated-at-utc <ISO8601>
echo $?
```

Mit Offline-DataRefs Resolve:

```bash
bash scripts/ops/pt_replay_compare_ci.sh --bundle <BUNDLE_DIR> --resolve-datarefs best_effort --cache-root <CACHE_ROOT> --generated-at-utc <ISO8601>
bash scripts/ops/pt_replay_compare_ci.sh --bundle <BUNDLE_DIR> --resolve-datarefs strict --cache-root <CACHE_ROOT> --generated-at-utc <ISO8601>
echo $?
```

Output (default):

```text
meta/compare_report.json
```

Hinweis:
- Der Wrapper setzt immer explizit einen Output-Pfad, damit Compare einen Report schreiben kann (auch wenn Validierung fehlschlägt).
- Exit Codes werden 1:1 durchgereicht (0, 2, 3, 4, 5, 6).

#### CI Workflow (Artefakt)
Workflow Datei:

```text
.github/workflows/replay_compare_report.yml
```

Artefakt:
- Name:

```text
replay-compare-report
```

- Datei im Artefakt:

```text
compare_report.json
```

Determinismus:
- CI nutzt eine fixe:

```text
--generated-at-utc 2026-01-01T00:00:00Z
```

#### Report Interpretation (Operator Kurzreferenz)
Wichtigste Felder:
- Summary:

```text
summary.status
summary.exit_code
summary.reasons
```

- Replay:

```text
replay.validate_bundle
replay.replay_exit_code
replay.check_outputs
replay.invariants.fills
replay.invariants.positions
replay.diffs.fills_diff
replay.diffs.positions_diff
```

Exit-Code Mapping:
- 0: PASS
- 2: Contract / Schema / missing cache-root (wenn resolver angefordert)
- 3: Hash mismatch (Bundle oder DataRefs sha256_hint)
- 4: Expected Outputs mismatch (nur bei check-outputs)
- 5: Unexpected error
- 6: Missing required DataRef (strict)

### Phase 3.4 — Consume Compare Report (Slice 3.5)
Ziel:
- Compare Report in einen kompakten CI Log Summary (stdout) und eine minified JSON Summary für Dashboards umwandeln.
- Offline-only, deterministisch, ohne Wall-Clock.

Consumer Script:

```text
scripts/ops/pt_compare_consume.py
```

Input:

```text
meta/compare_report.json
```

Output (default):

```text
compare_summary.min.json
```

CI Mode (single-line Summary):

```bash
python3 scripts/ops/pt_compare_consume.py --report <BUNDLE_DIR>/meta/compare_report.json --mode ci
```

Ops Mode (two-line Summary):

```bash
python3 scripts/ops/pt_compare_consume.py --report <BUNDLE_DIR>/meta/compare_report.json --mode ops
```

Strict Mode (Exit-Code aus Report übernehmen, wenn FAIL):

```bash
python3 scripts/ops/pt_compare_consume.py --report <BUNDLE_DIR>/meta/compare_report.json --strict
echo $?
```

### Phase 4 — Verification Checklist
- Manifest ist kanonisch (sortierte Keys, kein Whitespace, LF)
- hashes/sha256sums.txt deckt alle Dateien ab (außer sich selbst), LF-only
- events/execution_events.jsonl ist sortiert nach (event_time_utc, seq)
- Optional: --check-outputs ist grün (expected_fills und expected_positions passen)

### Hardening Checks (v1.x)
- Validator lehnt CRLF ab (LF-only + trailing LF).
- Validator lehnt Floats überall in Events/Payload ab (hard error).
- sha256sums.txt muss manifest.json enthalten, exakt alle Dateien außer sich selbst abdecken und nach Pfad sortiert sein.
- events müssen strikt nach (event_time_utc, seq) sortiert sein; seq startet bei 0 und ist lückenlos.

### Exit Codes (CLI, v1.x)
- 0: OK
- 2: Contract violation oder schema validation
- 3: Hash mismatch
- 4: Replay mismatch (check-outputs)
- 5: Unexpected exception
- 6: Missing required DataRef (strict)

### Exit Criteria (Definition of Done)
- build erzeugt Bundle inkl. manifest + hashes + required layout
- validate ist grün auf frischem Bundle und rot nach Tampering
- replay ist grün auf minimalem Bundle (CI Smoke Test)
- Tests für Replay Pack sind in CI grün

### Rollback Notes
- Replay Pack ist additive Funktionalität (neues Paket + neues Script)
- Rollback: neue Dateien entfernen oder Script nicht deployen; keine bestehenden APIs werden geändert
