# Test Health CI/CD Integration

Stand: Dezember 2024

## Übersicht

Die Test Health Automation ist vollständig in GitHub Actions integriert und läuft automatisch nach folgendem Schedule:

- **Täglich** um 06:00 UTC (07:00 CET): `daily_quick` Profil
- **Wöchentlich** Sonntags um 03:00 UTC (04:00 CET): `weekly_core` + `r_and_d_experimental`
- **Pull Requests**: `daily_quick` bei Code-Änderungen
- **Manuell**: Alle Profile über GitHub UI

---

## 🔄 Workflow-Jobs

### 1. Daily Health Check

**Trigger**: Täglich um 06:00 UTC, PRs

**Profil**: `daily_quick`

**Ziel**: Schneller Smoke-Test der Core-Funktionalität

**Threshold**: Health Score ≥ 80%

```yaml
- Runs in: ~1-2 Minuten
- Tests: Core + Offline Basics
- Artifacts: 30 Tage Retention
```

**Failure-Verhalten**:
- Score < 80% → Workflow fails
- Benachrichtigung über GitHub (optional: Slack-Integration)

---

### 2. Weekly Health Check

**Trigger**: Sonntags um 03:00 UTC

**Profil**: `weekly_core`

**Ziel**: Umfassende Core-System-Prüfung

**Threshold**: Health Score ≥ 80%

```yaml
- Runs in: ~3-5 Minuten
- Tests: Core + Offline + Reporting + TriggerTraining
- Artifacts: 90 Tage Retention
- History: Zeigt Trend der letzten Wochen
```

---

### 3. R&D Health Check

**Trigger**: Sonntags um 03:00 UTC (zusammen mit weekly)

**Profil**: `r_and_d_experimental`

**Ziel**: Überwachung experimenteller Strategien

**Threshold**: Health Score ≥ 70% (toleranter als Core)

```yaml
- Runs in: ~3-4 Minuten
- Tests: Armstrong, El-Karoui, Bouchaud, Regime-Aware
- Artifacts: 90 Tage Retention
- Erlaubt Fehlschläge bei optionalen Dependencies
```

**Besonderheit**: R&D-Tests dürfen fehlschlagen, solange Core-Funktionalität intakt ist.

---

### 4. Manual Health Check

**Trigger**: Manual via GitHub UI

**Profil**: Wählbar (alle 5 Profile)

**Ziel**: Ad-hoc Checks für Debugging

```yaml
- Runs on-demand
- Profil-Auswahl im GitHub UI
- Zeigt komplette Historie aller Profile
- Artifacts: 30 Tage Retention
```

**Verwendung**:
1. Gehe zu `Actions` → `Test Health Automation`
2. Klicke `Run workflow`
3. Wähle Profil aus Dropdown
4. Klicke `Run workflow`

---

## 📊 Artifacts & Reports

Jeder Workflow-Run erzeugt **Artifacts** mit vollständigen Reports:

```
health-report-{profile}-{run_number}/
├── reports/
│   └── test_health/
│       ├── history.json
│       └── {timestamp}_{profile}/
│           ├── summary.json
│           ├── summary.md
│           └── summary.html
```

**Download**:
- Gehe zu `Actions` → Workflow-Run → `Artifacts` Section
- Klicke auf Artifact-Name zum Download

**Retention**:
- Daily/Manual: 30 Tage
- Weekly/R&D: 90 Tage

---

## 🎯 Health Score Thresholds

| Profil | Threshold | Expected | Failure Action |
|--------|-----------|----------|----------------|
| `daily_quick` | ≥ 80% | 100% | ❌ Workflow fails |
| `weekly_core` | ≥ 80% | 100% | ❌ Workflow fails |
| `full_suite` | ≥ 70% | 83.3% | ⚠️ Warning only |
| `r_and_d_experimental` | ≥ 70% | 80% | ⚠️ Warning only |
| `demo_simple` | ≥ 80% | 100% | ❌ Workflow fails |

---

## 🔧 Konfiguration

### GitHub Secrets (Optional)

Für erweiterte Funktionalität (z.B. Slack-Notifications):

```yaml
SLACK_WEBHOOK_URL: https://hooks.slack.com/...
```

### Workflow Anpassungen

**Datei**: `.github/workflows/test_health.yml`

**Schedule ändern**:
```yaml
schedule:
  - cron: '0 6 * * *'  # Täglich 06:00 UTC
  - cron: '0 3 * * 0'  # Sonntags 03:00 UTC
```

**Threshold ändern**:
```bash
# In Job-Steps:
if (( $(echo "$HEALTH_SCORE < 80" | bc -l) )); then
  # Ändere "80" zu gewünschtem Threshold
```

---

## 📈 Historie-Tracking in CI

Die Historie wird **nicht** im CI persistiert (ephemeral), da:
- Jeder Run startet mit frischem Checkout
- `history.json` wird nicht committed
- Artifacts enthalten individuelle Reports

**Alternative für Production**:
1. Commit `history.json` nach jedem Run (automated commit)
2. Externe Storage (S3, GCS) für Historie
3. Datenbank-Integration für Trend-Analysen

---

## 🚀 Badge-Integration

### GitHub Actions Badge

```markdown
![Test Health](https://github.com/{owner}/{repo}/actions/workflows/test_health.yml/badge.svg)
```

**Beispiel**:
![Test Health](https://github.com/your-org/Peak_Trade/actions/workflows/test_health.yml/badge.svg)

### Custom Health Score Badge

**Option 1**: shields.io Dynamic Badge
```markdown
![Health Score](https://img.shields.io/badge/Health-100%25-brightgreen)
```

**Option 2**: Automated Update via CI
- Commit Badge-JSON nach jedem Run
- shields.io liest JSON
- Auto-Update Badge Color basierend auf Score

---

## 🔔 Benachrichtigungen (Optional)

### Slack-Integration

Füge zum Workflow hinzu:

```yaml
- name: Notify Slack on Failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
    payload: |
      {
        "text": "❌ Test Health Check failed: ${{ github.workflow }}",
        "attachments": [{
          "color": "danger",
          "fields": [{
            "title": "Profile",
            "value": "${{ github.event.inputs.profile || 'daily_quick' }}",
            "short": true
          }, {
            "title": "Run",
            "value": "${{ github.run_number }}",
            "short": true
          }]
        }]
      }
```

### Email-Benachrichtigungen

GitHub sendet automatisch Emails bei Workflow-Failures an:
- Workflow-Autor
- Commit-Autor
- Repository-Owner (bei scheduled runs)

**Konfiguration**: GitHub Settings → Notifications

---

## 🧪 Testing der CI/CD-Integration

### 1. Lokaler Test

Teste Workflow-Commands lokal:

```bash
# Simuliere Daily Check
python3 scripts/run_test_health_profile.py --profile daily_quick

# Check Health Score
LATEST_DIR=$(ls -t reports/test_health/ | grep -v history.json | head -1)
python3 -c "import json; data=json.load(open('reports/test_health/${LATEST_DIR}/summary.json')); print(f\"Health Score: {data['health_score']}\")"
```

### 2. Manual Workflow Run

1. Push `.github/workflows/test_health.yml` to `main`
2. Gehe zu GitHub Actions
3. Wähle "Test Health Automation"
4. Klicke "Run workflow"
5. Wähle Profil
6. Prüfe Logs & Artifacts

### 3. Pull Request Test

Erstelle PR mit Dummy-Änderung:

```bash
git checkout -b test-health-ci
echo "# Test" >> README.md
git commit -am "test: trigger health check"
git push origin test-health-ci
```

→ Workflow sollte automatisch starten

---

## 📝 Best Practices

### ✅ DO

- **Regelmäßige Reviews** der Health-Trends
- **Threshold anpassen** wenn systematische Änderungen
- **Artifacts downloaden** bei Failures für Debugging
- **Historie lokal sammeln** für Trend-Analysen

### ❌ DON'T

- **Nicht** Workflow bei jedem Commit triggern (zu teuer)
- **Nicht** Thresholds zu hoch setzen (false positives)
- **Nicht** R&D-Failures als kritisch behandeln
- **Nicht** Artifacts unbegrenzt speichern (Kosten)

---

## 🔍 Troubleshooting

### Problem: Workflow startet nicht automatisch

**Lösung**:
1. Prüfe Cron-Syntax in `.github/workflows/test_health.yml`
2. Stelle sicher, Workflow ist in `main` Branch
3. GitHub Actions muss aktiviert sein (Settings → Actions)

### Problem: Health Check fails mit Score > 80%

**Lösung**:
- Prüfe Shell-Script-Syntax (`bc` nicht verfügbar?)
- Verwende Python für Score-Check:
  ```python
  import json
  with open('reports/test_health/{dir}/summary.json') as f:
      score = json.load(f)['health_score']
  if score < 80:
      exit(1)
  ```

### Problem: Artifacts zu groß

**Lösung**:
- Reduziere Retention Days
- Excludiere `history.json` (wird mit jedem Run größer)
- Komprimiere Reports:
  ```bash
  tar -czf reports.tar.gz reports/test_health/
  ```

---

## 📚 Weitere Ressourcen

- [GitHub Actions Dokumentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Cron Schedule Tester](https://crontab.guru/)
- [Test Health Automation Docs](./TEST_HEALTH_AUTOMATION_V0.md)

---

## 🎯 Nächste Schritte

1. **Push Workflow** zu `main` Branch
2. **Manual Run** zum Testen
3. **Badges** zu README.md hinzufügen
4. **Slack/Email** Notifications einrichten (optional)
5. **Historie-Storage** für Trend-Analysen (optional)
