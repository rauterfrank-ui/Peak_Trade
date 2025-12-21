# Test Health Automation – Quick Start

**5-Minuten-Einstieg** in das Test Health System von Peak_Trade.

Stand: Dezember 2024

---

## 🚀 Erste Schritte

### 1. Schneller Health-Check (lokal)

```bash
# Daily Quick Check (1-2 Sekunden)
python scripts/run_test_health_profile.py --profile daily_quick

# Ergebnis:
# ✅ 100% Health Score
# Reports in: reports/test_health/{timestamp}_daily_quick/
```

### 2. Historie ansehen

```bash
# Alle Profile
python scripts/show_test_health_history.py --all

# Einzelnes Profil
python scripts/show_test_health_history.py --profile weekly_core
```

### 3. CI/CD validieren

```bash
# Prüfe GitHub Actions Config
python scripts/validate_ci_config.py

# Ergebnis: ✅ Alle Validierungen erfolgreich!
```

---

## 📊 Verfügbare Profile

| Profil | Dauer | Verwendung | Expected Score |
|--------|-------|------------|----------------|
| `daily_quick` | 1-2s | Schneller Smoke-Test | 100% |
| `weekly_core` | 3-5s | Umfassender Core-Check | 100% |
| `full_suite` | 2-3s | Best-Effort alle Tests | 83% |
| `r_and_d_experimental` | 3-4s | Experimentelle Tests | 80% |
| `demo_simple` | <1s | Demo/Shell-Commands | 100% |

---

## 📁 Wichtige Dateien

```
Peak_Trade/
├── config/
│   └── test_health_profiles.toml      # Profile-Definitionen
├── scripts/
│   ├── run_test_health_profile.py     # CLI Haupt-Tool
│   ├── show_test_health_history.py    # Historie-Viewer
│   └── validate_ci_config.py          # CI-Validator
├── src/ops/
│   ├── test_health_runner.py          # Core-Logik
│   └── test_health_history.py         # Historie-Modul
├── .github/workflows/
│   └── test_health.yml                # GitHub Actions
├── docs/ops/
│   ├── TEST_HEALTH_AUTOMATION_V0.md   # Hauptdoku
│   ├── TEST_HEALTH_CI_CD.md           # CI/CD-Doku
│   ├── TEST_HEALTH_BADGE_TEMPLATE.md  # Badge-Templates
│   └── TEST_HEALTH_QUICKSTART.md      # Diese Datei
└── reports/test_health/
    ├── history.json                   # Historie-Daten
    └── {timestamp}_{profile}/         # Report-Verzeichnisse
        ├── summary.json               # Maschinen-lesbar
        ├── summary.md                 # Human-readable
        └── summary.html               # Visualisiert
```

---

## 🔧 Wichtige Commands

### Lokale Ausführung

```bash
# Default-Profil (daily_quick)
python scripts/run_test_health_profile.py

# Spezifisches Profil
python scripts/run_test_health_profile.py --profile weekly_core

# Alle Profile nacheinander
for profile in daily_quick weekly_core r_and_d_experimental; do
    python scripts/run_test_health_profile.py --profile $profile
done
```

### Historie

```bash
# Übersicht aller Profile (letzte 14 Tage)
python scripts/show_test_health_history.py --all

# Zeitraum filtern
python scripts/show_test_health_history.py --all --days 7

# JSON-Output für Scripting
python scripts/show_test_health_history.py --profile daily_quick --json
```

### Reports

```bash
# Letzte Reports anzeigen
ls -lt reports/test_health/ | head -10

# Markdown-Report ansehen
cat reports/test_health/{latest_dir}/summary.md

# HTML-Report öffnen
open reports/test_health/{latest_dir}/summary.html
```

---

## 🤖 GitHub Actions

### Automatische Runs

- **Täglich**: 06:00 UTC (`daily_quick`)
- **Wöchentlich**: Sonntags 03:00 UTC (`weekly_core` + `r_and_d_experimental`)
- **Pull Requests**: Bei Code-Änderungen (`daily_quick`)

### Manual Run

1. Gehe zu GitHub → Actions
2. Wähle "Test Health Automation"
3. Klicke "Run workflow"
4. Wähle Profil aus Dropdown
5. Klicke "Run workflow"

### Artifacts

Nach jedem Run:
- Download über Actions → Run → Artifacts Section
- Enthält vollständige Reports (JSON, Markdown, HTML)
- Retention: 30-90 Tage

---

## 📈 Health Score Interpretation

| Score | Ampel | Status | Action |
|-------|-------|--------|--------|
| 80-100% | 🟢 Green | Gesund | Weiter so! |
| 50-79% | 🟡 Yellow | Teilweise | Genauer hinsehen |
| 0-49% | 🔴 Red | Kritisch | Sofortiges Handeln |

**Beispiele**:
- `daily_quick`: 100% → 🟢 Perfekt
- `full_suite`: 83% → 🟢 Best-Effort OK
- `r_and_d_experimental`: 80% → 🟢 Experimentelle Fehler akzeptabel

---

## 🎯 Typische Workflows

### Morning Check

```bash
# Schneller Check vor dem Arbeiten
python scripts/run_test_health_profile.py --profile daily_quick

# Bei 100%: Alles gut ✅
# Bei <100%: Fehler-Details in summary.md ansehen
```

### Weekly Review

```bash
# Umfassender Check
python scripts/run_test_health_profile.py --profile weekly_core

# Historie-Trend prüfen
python scripts/show_test_health_history.py --profile weekly_core

# Bei Trend "declining": Ursache identifizieren
```

### Before Release

```bash
# Full Suite Check
python scripts/run_test_health_profile.py --profile full_suite

# R&D Check
python scripts/run_test_health_profile.py --profile r_and_d_experimental

# Alle Reports prüfen
ls -lt reports/test_health/ | head -5
```

### Debugging Failures

```bash
# Run mit Failed Check
python scripts/run_test_health_profile.py --profile full_suite

# Markdown-Report öffnen
cat reports/test_health/{latest_dir}/summary.md

# Scrolle zu "❌ Fehlgeschlagene Checks (Details)"
# Dort findest du:
#   - Error Message
#   - Stdout (letzte 2000 chars)
#   - Stderr (letzte 2000 chars)
#   - Command
#   - Return Code
```

---

## 🔍 Troubleshooting

### Problem: "No module named 'src'"

**Lösung**: Python-Path fehlt
```bash
export PYTHONPATH="${PYTHONPATH}:${PWD}"
python scripts/run_test_health_profile.py
```

### Problem: Health Score unerwartet niedrig

**Lösung**: Fehler-Details ansehen
```bash
# Letzte Reports
cd reports/test_health/
ls -lt | head -5

# Markdown öffnen
cat {latest_dir}/summary.md | grep -A50 "Fehlgeschlagene Checks"
```

### Problem: Historie zeigt "Keine Daten"

**Lösung**: Erst einen Run durchführen
```bash
python scripts/run_test_health_profile.py
python scripts/show_test_health_history.py --all
```

### Problem: CI-Workflow startet nicht

**Lösung**: Prüfe GitHub Actions Settings
1. Settings → Actions → General
2. "Allow all actions and reusable workflows"
3. Save

---

## 📚 Weiterführende Docs

- [Vollständige Doku](./TEST_HEALTH_AUTOMATION_V0.md)
- [CI/CD-Integration](./TEST_HEALTH_CI_CD.md)
- [Badge-Templates](./TEST_HEALTH_BADGE_TEMPLATE.md)

---

## 💡 Best Practices

✅ **DO**:
- Führe `daily_quick` regelmäßig aus
- Prüfe Health-Trends wöchentlich
- Untersuche Failures sofort
- Nutze Historie für Trend-Analysen

❌ **DON'T**:
- `full_suite` zu oft laufen lassen (teuer)
- R&D-Failures als kritisch behandeln
- Thresholds zu hoch setzen
- Historie-Daten löschen

---

**Happy Testing! 🎉**
