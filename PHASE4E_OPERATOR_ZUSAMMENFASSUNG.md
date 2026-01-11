# Phase 4E — Operator-Zusammenfassung (Deutsch)

**Datum:** 2026-01-11  
**Phase:** 4E — Validator Report Normalization  
**Status:** ✅ ABGESCHLOSSEN  
**Risiko:** NIEDRIG (nur Reporting, keine Trading-Logik)

---

## Was wurde geliefert?

Ein **normalisiertes, versioniertes Validator-Report-Format** (Schema v1.0.0) für:
- ✅ Maschinenlesbare Health-Checks
- ✅ Trend-Analysen
- ✅ CI-Artefakte (JSON + Markdown)
- ✅ Deterministische Outputs (byte-identisch)

---

## Wichtigste Dateien

### Source Code (3 Dateien, 824 Zeilen)
1. **Schema:** `src/ai_orchestration/validator_report_schema.py` (387 Zeilen)
   - Pydantic-Modelle für ValidatorReport, ValidationCheck, etc.
   - Schema-Version: v1.0.0
   - Kanonische Serialisierung (sortierte Keys, stabile Listen)

2. **Normalizer:** `src/ai_orchestration/validator_report_normalized.py` (167 Zeilen)
   - Konvertiert Legacy-Reports (Phase 4D) → Normalized Format
   - Hash-Berechnung (SHA256, nur kanonische Felder)
   - Determinismus-Validierung

3. **CLI:** `scripts/aiops/normalize_validator_report.py` (270 Zeilen)
   - Normalisierung von File oder stdin
   - Runtime-Context-Injection (git SHA, run ID, etc.)
   - Exit Codes: 0 (Erfolg), 1 (Fehler)

### Tests (2 Dateien, 856 Zeilen, 31 Tests)
4. **Unit Tests:** `tests/ai_orchestration/test_validator_report_normalized.py` (493 Zeilen, 21 Tests)
5. **CLI Tests:** `tests/ai_orchestration/test_normalize_validator_report_cli.py` (363 Zeilen, 10 Tests)

**Ergebnis:** ✅ 31 Tests bestanden in 1.55s (100% Pass-Rate)

### CI Integration
6. **Workflow:** `.github/workflows/l4_critic_replay_determinism_v2.yml`
   - 3 neue Steps: Normalisierung + Upload (normalized + legacy)
   - Artefakte: `validator-report-normalized-<run_id>` + `validator-report-legacy-<run_id>`

### Dokumentation
7. **Vollständige Spec:** `docs/governance/ai_autonomy/PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md` (600 Zeilen)
8. **Quickstart:** `docs/governance/ai_autonomy/PHASE4E_QUICKSTART.md` (300 Zeilen)

---

## Wie benutzen?

### 1. Report normalisieren (lokal)

```bash
python scripts/aiops/normalize_validator_report.py \
  --input .tmp/validator_report.json \
  --out-dir .tmp/normalized
```

**Output:**
- `validator_report.normalized.json` (kanonisch, deterministisch)
- `validator_report.normalized.md` (menschenlesbare Zusammenfassung)

---

### 2. CI-Modus (mit Runtime-Context)

```bash
python scripts/aiops/normalize_validator_report.py \
  --input .tmp/validator_report.json \
  --out-dir .tmp/normalized \
  --git-sha "${GITHUB_SHA}" \
  --run-id "${GITHUB_RUN_ID}" \
  --workflow "${GITHUB_WORKFLOW}" \
  --job "${GITHUB_JOB}" \
  --timestamp
```

**Hinweis:** Runtime-Context wird **nicht** in kanonischem JSON gespeichert (deterministischer Modus).

---

### 3. Determinismus verifizieren

```bash
# Zweimal ausführen
python scripts/aiops/normalize_validator_report.py \
  --input report.json --out-dir .tmp/run1 --quiet
python scripts/aiops/normalize_validator_report.py \
  --input report.json --out-dir .tmp/run2 --quiet

# Vergleichen (sollte identisch sein)
diff .tmp/run1/validator_report.normalized.json \
     .tmp/run2/validator_report.normalized.json

# Erwartung: Keine Unterschiede
```

**Verifiziert:** ✅ Outputs sind byte-identisch

**SHA256-Hashes:**
```
84fb7568af8764b2f1240d3bc76f021ba7f6377193ad09e45cf8d7e18d616743  run1/validator_report.normalized.json
84fb7568af8764b2f1240d3bc76f021ba7f6377193ad09e45cf8d7e18d616743  run2/validator_report.normalized.json
```

---

### 4. Report inspizieren

```bash
# JSON (kanonisch)
jq . .tmp/normalized/validator_report.normalized.json

# Markdown (menschenlesbar)
cat .tmp/normalized/validator_report.normalized.md

# Gesamtergebnis extrahieren
jq -r '.result' validator_report.normalized.json
# Output: PASS oder FAIL

# Zusammenfassung
jq '.summary' validator_report.normalized.json
# Output: {"passed": 1, "failed": 0, "total": 1}
```

---

### 5. Von CI herunterladen

```bash
# Artefakte auflisten
gh run view <run-id>

# Normalisierten Report herunterladen
gh run download <run-id> -n validator-report-normalized-<run-id>

# Inspizieren
jq . validator_report.normalized.json
cat validator_report.normalized.md
```

---

## Schema-Übersicht (v1.0.0)

### Top-Level-Struktur

```json
{
  "schema_version": "1.0.0",
  "tool": {
    "name": "l4_critic_determinism_contract_validator",
    "version": "1.0.0"
  },
  "subject": "l4_critic_determinism_contract_v1.0.0",
  "result": "PASS",
  "checks": [
    {
      "id": "determinism_contract_validation",
      "status": "PASS",
      "message": "Reports are identical (0 diffs)",
      "metrics": {
        "baseline_hash": "abc123...",
        "candidate_hash": "abc123...",
        "first_mismatch_path": null
      }
    }
  ],
  "summary": {
    "passed": 1,
    "failed": 0,
    "total": 1
  },
  "evidence": {
    "baseline": "tests/fixtures/.../baseline.json",
    "candidate": ".tmp/candidate.json",
    "diff": null
  },
  "runtime_context": {
    "git_sha": "abc123",
    "run_id": "123456",
    "workflow": "L4 Critic Replay Determinism",
    "job": "validate_determinism_contract",
    "generated_at_utc": "2026-01-11T12:00:00Z"
  }
}
```

**Hinweis:** `runtime_context` wird in deterministischem Modus **ausgeschlossen** (nicht in kanonischem JSON).

---

## Tests ausführen

```bash
# Alle Tests
pytest tests/ai_orchestration/test_validator_report_normalized.py \
       tests/ai_orchestration/test_normalize_validator_report_cli.py -v

# Erwartung: 31 passed in ~1.5s
```

**Ergebnis:** ✅ 31 Tests bestanden in 1.55s

---

## Risikobewertung

**Risiko:** NIEDRIG

**Begründung:**
- ✅ Nur Reporting/CI-Artefakte (keine Trading-Logik)
- ✅ Keine Strategie-/Config-/Risk-Änderungen
- ✅ Rückwärtskompatibel (Legacy-Reports werden weiterhin hochgeladen)
- ✅ Additive Änderungen (neue Artefakte, keine Entfernungen)
- ✅ Umfassende Test-Coverage (31 Tests)
- ✅ Determinismus verifiziert (byte-identische Outputs)

**Scope-Verifikation:**
- ✅ Geändert: `src/ai_orchestration/`, `scripts/aiops/`, `tests/`, `.github/workflows/`, `docs/`
- ✅ NICHT geändert: Trading/Execution-Logik, Strategie-Configs, Risk-Management, Portfolio-Management

---

## Rollback-Strategie

Falls Probleme auftreten:

1. **CI-Workflow-Änderungen zurücksetzen**
   ```bash
   git revert <commit-sha>
   ```

2. **Legacy-Artefakte bleiben verfügbar**
   - `validator-report-legacy-<run_id>` wird weiterhin hochgeladen
   - Keine Breaking Changes für bestehende Consumer

3. **Keine Auswirkung auf bestehende Determinismus-Validierung**
   - Phase 4D Validator läuft weiterhin
   - Bestehende Gates unberührt

---

## CI-Verhalten (nach Merge)

### Workflow: `l4_critic_replay_determinism_v2.yml`

**Neue Artefakte (Phase 4E):**
1. **`validator-report-normalized-<run_id>`** (JSON + Markdown)
   - Kanonisches, deterministisches Format
   - Schema-Version: v1.0.0
   - Aufbewahrung: 14 Tage

2. **`validator-report-legacy-<run_id>`** (Phase 4D Format)
   - Rückwärtskompatibilität
   - Aufbewahrung: 14 Tage

**Erwartetes Verhalten:**
- Normalisierungs-Step läuft nach Determinismus-Contract-Validierung
- Runtime-Context wird injiziert (git SHA, run ID, workflow, job, timestamp)
- Beide Artefakte werden hochgeladen (normalized + legacy)
- Keine Breaking Changes für bestehende Gates

---

## Häufige Anwendungsfälle

### Use Case 1: Automatisierte Health-Checks

```python
import json
from pathlib import Path

# Normalisierten Report laden
data = json.loads(Path(".tmp/normalized/validator_report.normalized.json").read_text())

# Gesamtergebnis prüfen
if data["result"] == "PASS":
    print("✅ Alle Checks bestanden")
    exit(0)
else:
    print(f"❌ {data['summary']['failed']} Checks fehlgeschlagen")
    for check in data["checks"]:
        if check["status"] == "FAIL":
            print(f"  - {check['id']}: {check['message']}")
    exit(1)
```

### Use Case 2: Trend-Analyse

```python
import json
from pathlib import Path
from collections import defaultdict

# Reports von mehreren Runs sammeln
reports = []
for report_file in Path("artifacts/").glob("**/validator_report.normalized.json"):
    reports.append(json.loads(report_file.read_text()))

# Trends analysieren
pass_rate = sum(1 for r in reports if r["result"] == "PASS") / len(reports)
print(f"Pass-Rate: {pass_rate:.1%}")

# Check-Level-Trends
check_stats = defaultdict(lambda: {"pass": 0, "fail": 0})
for report in reports:
    for check in report["checks"]:
        check_stats[check["id"]][check["status"].lower()] += 1

for check_id, stats in check_stats.items():
    total = stats["pass"] + stats["fail"]
    pass_rate = stats["pass"] / total if total > 0 else 0
    print(f"{check_id}: {pass_rate:.1%} Pass-Rate ({stats['pass']}/{total})")
```

---

## Troubleshooting

### Fehler: "Invalid JSON input"

**Ursache:** Input-Datei ist kein gültiges JSON.

**Lösung:**
```bash
# JSON validieren
jq . input.json

# Syntax-Fehler prüfen
python -m json.tool input.json
```

### Fehler: "Input file not found"

**Ursache:** Dateipfad ist falsch.

**Lösung:**
```bash
# Datei existiert?
ls -lh .tmp/validator_report.json

# Absoluten Pfad verwenden
python scripts/aiops/normalize_validator_report.py \
  --input "$(pwd)/.tmp/validator_report.json" \
  --out-dir .tmp/normalized
```

### Nicht-deterministische Outputs

**Symptom:** Zwei Runs produzieren unterschiedliche JSONs.

**Ursache:** Runtime-Context in kanonischem Modus enthalten (Bug).

**Lösung:**
```bash
# Verifizieren, dass runtime_context ausgeschlossen ist
jq 'has("runtime_context")' .tmp/normalized/validator_report.normalized.json
# Erwartung: false (im deterministischen Modus)

# Falls true, Bug-Report erstellen
```

---

## Referenzen

- **Vollständige Spec:** [PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md](docs/governance/ai_autonomy/PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md)
- **Quickstart:** [PHASE4E_QUICKSTART.md](docs/governance/ai_autonomy/PHASE4E_QUICKSTART.md)
- **Implementation Summary:** [PHASE4E_IMPLEMENTATION_SUMMARY.md](PHASE4E_IMPLEMENTATION_SUMMARY.md)
- **Phase 4D:** [L4 Critic Determinism Contract](docs/governance/ai_autonomy/PHASE4D_L4_CRITIC_DETERMINISM_CONTRACT.md)
- **CLI Help:** `python scripts/aiops/normalize_validator_report.py --help`

---

## Nächste Schritte (nach Merge)

1. ✅ CI-Artefakte in nachfolgenden Runs überwachen
2. ✅ Verifizieren, dass normalisierte Reports korrekt hochgeladen werden
3. ✅ Normalisierte Reports für Health-Checks/Trend-Analysen verwenden
4. ✅ Zukünftige Erweiterungen in Betracht ziehen:
   - Multi-Validator-Support (VaR Backtest, etc.)
   - Trend-Dashboard
   - Alert-Thresholds

---

## Schnellreferenz

### Report normalisieren
```bash
python scripts/aiops/normalize_validator_report.py \
  --input .tmp/validator_report.json \
  --out-dir .tmp/normalized
```

### Determinismus verifizieren
```bash
for i in 1 2; do
  python scripts/aiops/normalize_validator_report.py \
    --input report.json --out-dir .tmp/run$i --quiet
done
diff .tmp/run1/validator_report.normalized.json \
     .tmp/run2/validator_report.normalized.json
```

### Tests ausführen
```bash
pytest tests/ai_orchestration/test_validator_report_normalized.py \
       tests/ai_orchestration/test_normalize_validator_report_cli.py -v
```

### Report inspizieren
```bash
jq . .tmp/normalized/validator_report.normalized.json
cat .tmp/normalized/validator_report.normalized.md
```

---

**Phase 4E Abgeschlossen** ✅

**Status:** Bereit für Review + Merge  
**Risiko:** NIEDRIG  
**Test-Coverage:** 31 Tests, 100% Pass-Rate  
**Determinismus:** Verifiziert (byte-identisch)
