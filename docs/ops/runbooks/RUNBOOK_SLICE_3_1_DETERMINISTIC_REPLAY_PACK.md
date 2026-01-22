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
- 2: Contract- oder Hash-Verletzung

### Phase 3 — Replay (Deterministisch ausführen)

```bash
python scripts/execution/pt_replay_pack.py replay --bundle <OUT_DIR>/replay_pack
python scripts/execution/pt_replay_pack.py replay --bundle <OUT_DIR>/replay_pack --check-outputs
echo $?
```

Exit Codes:
- 0: ok
- 2: Contract- oder Validierungsfehler
- 3: Replay-Mismatch gegen erwartete Outputs

### Phase 4 — Verification Checklist
- Manifest ist kanonisch (sortierte Keys, kein Whitespace, LF)
- hashes/sha256sums.txt deckt alle Dateien ab (außer sich selbst), LF-only
- events/execution_events.jsonl ist sortiert nach (event_time_utc, seq)
- Optional: --check-outputs ist grün (expected_fills und expected_positions passen)

### Exit Criteria (Definition of Done)
- build erzeugt Bundle inkl. manifest + hashes + required layout
- validate ist grün auf frischem Bundle und rot nach Tampering
- replay ist grün auf minimalem Bundle (CI Smoke Test)
- Tests für Replay Pack sind in CI grün

### Rollback Notes
- Replay Pack ist additive Funktionalität (neues Paket + neues Script)
- Rollback: neue Dateien entfernen oder Script nicht deployen; keine bestehenden APIs werden geändert
