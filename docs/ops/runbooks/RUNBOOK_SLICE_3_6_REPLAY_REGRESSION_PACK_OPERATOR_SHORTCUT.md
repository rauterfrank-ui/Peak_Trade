## RUNBOOK — Slice 3.6 Replay Regression Pack (Operator Shortcut)

### Purpose
Ein einzelner, offline-only Shortcut für einen deterministischen End-to-End Replay Regression Run:

- Bundle bestimmen (vorhandenes Bundle verwenden oder deterministisch bauen)
- Compare Report erzeugen (primäres Ergebnis, Exit Codes 1:1)
- Consumer laufen lassen (deterministische stdout Summary + minified JSON Summary)
- Alle Outputs unter einem OUT_DIR mit stabilem Layout ablegen

### Scope
Nutze dieses Runbook, wenn du lokal/offline eine deterministische Regression gegen einen Replay Pack Bundle durchführen willst, ohne CI zu involvieren.

### Pre-flight Checklist
- Keine Live-Ausführung (Governance bleibt gesperrt)
- Offline-only: keine Netzwerk-/HTTP-Abhängigkeiten
- Python ist verfügbar (python3)
- Optional: lokaler Cache Root, falls DataRefs Resolve genutzt wird

### Steps

#### Step 1 — OUT_DIR vorbereiten
Wähle ein leeres oder dediziertes Verzeichnis als OUT_DIR.

#### Step 2A — Run mit vorhandenem Bundle
Beispiel:

```bash
bash scripts/ops/pt_replay_regression_pack.sh \
  --bundle <BUNDLE_DIR> \
  --out-dir <OUT_DIR> \
  --generated-at-utc <ISO8601>
```

Optional:

```bash
bash scripts/ops/pt_replay_regression_pack.sh \
  --bundle <BUNDLE_DIR> \
  --bundle-mode copy \
  --out-dir <OUT_DIR> \
  --check-outputs \
  --resolve-datarefs best_effort \
  --cache-root <CACHE_ROOT> \
  --generated-at-utc <ISO8601>
```

#### Step 2B — Run mit Bundle Build (wenn kein Bundle existiert)
Hinweis: Build benötigt einen Run-ID oder ein Run-Verzeichnis.

```bash
bash scripts/ops/pt_replay_regression_pack.sh \
  --run-id-or-dir <RUN_ID_OR_DIR> \
  --out-dir <OUT_DIR> \
  --generated-at-utc <ISO8601>
```

Wenn du Output-Invariants prüfen willst, ist es sinnvoll, die erwarteten Outputs beim Build einzuschließen:

```bash
bash scripts/ops/pt_replay_regression_pack.sh \
  --run-id-or-dir <RUN_ID_OR_DIR> \
  --out-dir <OUT_DIR> \
  --include-outputs \
  --check-outputs \
  --generated-at-utc <ISO8601>
```

#### Step 3 — Ergebnisse interpretieren
- Primär ist der Exit Code des Compare-Schritts (0, 2, 3, 4, 5, 6).
- Der Consumer ist standardmäßig informational (Exit 0), außer wenn strict aktiviert ist:

```bash
bash scripts/ops/pt_replay_regression_pack.sh \
  --bundle <BUNDLE_DIR> \
  --out-dir <OUT_DIR> \
  --strict-consumer \
  --generated-at-utc <ISO8601>
```

### Output Layout (stable)

```text
OUT_DIR/
  bundle/
  reports/
    compare_report.json
    compare_summary.min.json
  logs/
    regression_pack.log
```

### Verification
- compare_report.json existiert und ist kanonisches JSON (LF-only)
- compare_summary.min.json existiert und ist minified + deterministisch (LF-only)
- regression_pack.log existiert und enthält Exit Codes und relative Output-Refs

### Troubleshooting
- Exit 2: Contract violation (z.B. fehlende Inputs, fehlender Cache Root bei DataRefs)
- Exit 3: Hash mismatch
- Exit 4: Replay mismatch (bei check-outputs)
- Exit 6: Missing required DataRef (strict)

### References
- Deterministic Replay Pack Runbook (Slice 3.1)
- Compare Consumer (Slice 3.5)
