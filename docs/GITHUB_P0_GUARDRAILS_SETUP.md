# GitHub P0 Guardrails Setup Guide

**Status:** ✅ PRODUCTION READY  
**Version:** 1.0  
**Last Updated:** 2025-12-23  
**Owner:** @rauterfrank-ui

---

## Executive Summary

Dieses Dokument beschreibt die Einrichtung und Verwaltung der **P0 (Priority Zero) GitHub Guardrails** für Peak_Trade. Diese Guardrails sind kritische Sicherheits- und Qualitätsgates, die automatisch bei jedem Pull Request und Merge ausgeführt werden.

### Was sind P0 Guardrails?

P0 Guardrails sind **nicht-verhandelbare** Sicherheits- und Qualitätschecks, die JEDER Code-Change durchlaufen muss, bevor er in `main` gemerged wird. Sie schützen vor:

- **Sicherheitslücken** in Dependencies (Dependency Review)
- **Code-Schwachstellen** (CodeQL Static Analysis)
- **Ungetesteten Changes** (CI/Test Health Gates)
- **Policy-Verstößen** (Policy Critic, Governance Guards)
- **Supply Chain Attacks** (Dependency Review + CodeQL)

---

## 🛡️ Implementierte Guardrails

### 1. Dependency Review (PR Gate)

**Workflow:** `.github/workflows/dependency-review.yml`

**Zweck:** Blockiert PRs mit bekannten Sicherheitslücken in Dependencies.

**Trigger:**
- Bei jedem Pull Request

**Konfiguration:**
```yaml
fail-on-severity: high
```

**Verhalten:**
- ❌ **BLOCK**: PR wird blockiert bei HIGH/CRITICAL Schwachstellen
- ✅ **PASS**: Keine kritischen Schwachstellen gefunden

**Bypass:** NICHT möglich (P0 = Required Check)

---

### 2. CodeQL Static Analysis

**Workflow:** `.github/workflows/codeql.yml`

**Zweck:** Erkennt Code-Schwachstellen durch statische Analyse (SQL Injection, XSS, Command Injection, etc.)

**Trigger:**
- Pull Requests
- Push zu `main`
- Wöchentlich (Montags 3:17 UTC) - Scheduled Scan

**Sprachen:** Python

**Verhalten:**
- 🔍 Analysiert gesamte Codebase
- ⚠️ Erstellt Security Alerts bei Findings
- 📊 Resultate in GitHub Security Tab

**Bypass:** NICHT möglich (P0 = Required Check)

**Best Practice:**
- Security Alerts regelmäßig reviewen (wöchentlich)
- False Positives als "Dismissed" markieren mit Begründung

---

### 3. Merge Queue Support

**Konfiguration:** `merge_group` Trigger in allen Required Check Workflows

**Zweck:** Ermöglicht GitHub Merge Queue für serialisiertes, sicheres Merging

**Implementiert in folgenden Workflows:**
1. `.github/workflows/ci.yml`
2. `.github/workflows/lint.yml`
3. `.github/workflows/policy_critic.yml`
4. `.github/workflows/audit.yml`
5. `.github/workflows/deps_sync_guard.yml`
6. `.github/workflows/test_health.yml`
7. `.github/workflows/guard-reports-ignored.yml`
8. `.github/workflows/policy_tracked_reports_guard.yml`

**Beispiel-Konfiguration:**
```yaml
on:
  pull_request:
  merge_group:  # <- Ermöglicht Merge Queue
  push:
    branches: [main]
```

**Verhalten:**
- Merge Queue führt Tests auf **finalem Merge-Commit** aus
- Verhindert "broken main" durch Race Conditions
- Serialisiert Merges automatisch

---

### 4. CODEOWNERS Enforcement

**Datei:** `.github/CODEOWNERS`

**Zweck:** Erzwingt Reviews durch Code-Owner für kritische Pfade

**Kritische Pfade:**
- `/src/governance/` - Governance & Compliance Code
- `/src/execution/` - Order Execution
- `/src/risk/` - Risk Management
- `/src/live/` - Live Trading
- `.github/workflows/` - CI/CD Workflows
- `config/` - Configuration Files

**Verhalten:**
- ✅ PR benötigt Approval von definierten Ownern
- 🔒 Kann in Branch Protection Rules als Required Review konfiguriert werden

---

## 📋 Required Checks Configuration

### Empfohlene Branch Protection Rules für `main`

1. **Require Pull Request Reviews:**
   - Required approvals: 1
   - Dismiss stale reviews: ✅
   - Require review from Code Owners: ✅

2. **Require Status Checks:**
   - Require branches to be up to date: ✅
   - **Required Checks (P0):**
     - `Dependency Review` (dependency-review)
     - `Analyze (CodeQL)` (codeql/analyze)
     - `CI Tests` (tests + strategy-smoke)
     - `Lint` (lint)
     - `CI Health Gate` (ci-health-gate)
     - `Policy Critic Review` (policy-review)
     - `Audit` (audit)
     - `deps-sync-guard` (guard)
     - `Guard reports/ ignored` (guard-reports-ignored)
     - `Policy Guard - No Tracked Reports` (guard-no-tracked-reports)

3. **Additional Settings:**
   - Require conversation resolution: ✅
   - Do not allow bypassing settings: ✅
   - Restrict who can push: Admins only

---

## 🚀 Merge Queue Activation (Optional but Recommended)

### Vorteile

- **Eliminiert "broken main"** durch Race Conditions
- **Serialisiert Merges** automatisch
- **Führt Tests auf finalem Merge-Commit** aus (nicht nur PR HEAD)
- **Höhere Zuversicht** bei hochfrequentem Merging

### Aktivierung

**GitHub UI:** Settings → General → Pull Requests → Enable Merge Queue

**Empfohlene Konfiguration:**
- **Merge Method:** Squash and merge
- **Minimum PRs to merge:** 1
- **Maximum PRs to merge:** 5
- **Merge timeout:** 30 minutes
- **Status checks:** Alle P0 Required Checks

### Nutzung

```bash
# Statt "Merge" Button:
gh pr merge --merge-queue

# Oder über GitHub UI:
# "Add to merge queue" Button
```

---

## 🔧 Maintenance & Monitoring

### Wöchentliche Aufgaben

1. **CodeQL Security Alerts reviewen**
   - GitHub UI: Security → Code scanning alerts
   - False Positives dismissen mit Begründung

2. **Dependency Review Alerts prüfen**
   - GitHub UI: Security → Dependabot alerts
   - Updates planen für kritische Schwachstellen

3. **Workflow-Runs monitoren**
   - Failure Rate < 5% (ohne echte Errors)
   - Performance: Jobs sollten < 10min laufen

### Monatliche Aufgaben

1. **CODEOWNERS aktualisieren**
   - Team-Changes reflektieren
   - Neue kritische Pfade hinzufügen

2. **Branch Protection Rules reviewen**
   - Sind alle Required Checks aktuell?
   - Gibt es neue Guardrails?

---

## 🚨 Troubleshooting

### Problem: Dependency Review schlägt fehl

**Symptom:** PR wird blockiert mit "High Severity Vulnerability"

**Lösung:**
1. Alert in PR-Checks ansehen
2. Vulnerable Dependency identifizieren
3. Optionen:
   - **Option A:** Dependency updaten (`pip install --upgrade <package>`)
   - **Option B:** Alternative Dependency suchen
   - **Option C:** Security Advisory erstellen (wenn False Positive)

**Bypass:** NICHT möglich - das ist absichtlich so!

---

### Problem: CodeQL findet Schwachstelle

**Symptom:** Security Alert in GitHub Security Tab

**Lösung:**
1. Alert Details ansehen (Dataflow, Sink, Source)
2. Code fixen (Sanitization, Input Validation)
3. Re-run CodeQL (automatisch bei nächstem Push)
4. Alert schließt sich automatisch bei Fix

**False Positive?**
- Alert als "Dismissed" markieren
- Begründung: "False Positive - reason XYZ"
- Code-Kommentar mit Verweis auf Alert-ID

---

### Problem: Merge Queue steckt fest

**Symptom:** PR wartet ewig in Merge Queue

**Diagnose:**
```bash
gh pr view <number> --json statusCheckRollup
```

**Häufige Ursachen:**
- Ein Required Check schlägt fehl → Check fixen
- Timeout (>30min) → Status Checks optimieren
- Merge Conflict → Rebase auf main

**Notfall-Bypass (ONLY for emergencies):**
```bash
# Admin kann Queue leeren
gh pr merge <number> --admin --merge
```

---

## 📚 Related Documentation

- [P0 Guardrails Quick Reference](../P0_GUARDRAILS_QUICK_REFERENCE.md)
- [Policy Critic Documentation](governance/POLICY_CRITIC.md)
- [GitHub Merge Queue Docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)

---

## 🔄 Change Log

### 2025-12-23: Initial P0 Setup
- ✅ Dependency Review Workflow hinzugefügt
- ✅ CodeQL Workflow hinzugefügt
- ✅ merge_group Trigger zu 8 kritischen Workflows hinzugefügt
- ✅ CODEOWNERS Datei erstellt
- ✅ Dokumentation erstellt

---

## ✅ Verification Checklist

Nach Setup/Änderungen:

- [ ] `.github/workflows/dependency-review.yml` existiert
- [ ] `.github/workflows/codeql.yml` existiert
- [ ] `.github/CODEOWNERS` existiert und enthält keine Platzhalter
- [ ] Alle 8 kritischen Workflows haben `merge_group` trigger
- [ ] Branch Protection Rules für `main` sind konfiguriert
- [ ] Required Checks enthalten alle P0 Workflows
- [ ] Test-PR läuft durch und alle Checks sind grün
- [ ] CodeQL Security Tab zeigt "CodeQL is running"

---

**END OF DOCUMENT**
