# Audit-Check Timeline Investigation Report

**Erstellt:** 2025-12-26  
**Untersuchungszeitraum:** PRs #230-353  
**Repository:** rauterfrank-ui/Peak_Trade

---

## 🎯 Zusammenfassung

Der Audit-Check wurde am **23. Dezember 2025 um ~07:00 UTC** als required check aktiviert durch **PR #267**.

**Vor Aktivierung:** 13 PRs wurden trotz Audit-FAILURE gemerged  
**Nach Aktivierung:** Alle PRs mit Audit-FAILURE werden blockiert

---

## 📊 Statistische Übersicht (PRs #230-353)

| Metrik | Wert |
|--------|------|
| Gesamt-PRs mit Audit-Check | 122 |
| Erfolgreiche Audits (SUCCESS) | 102 (83.6%) |
| Fehlgeschlagene Audits (FAILURE) | 20 (16.4%) |
| PRs mit FAILURE gemerged | 13 |
| PRs mit FAILURE blockiert | 7 |

---

## 🚨 Die 13 gemergten PRs mit Audit-FAILURE

Alle zwischen **22.-23. Dezember 2025** (vor Aktivierung der Branch Protection):

| PR # | Merged At (UTC) | Audit Status | Titel |
|------|-----------------|--------------|-------|
| #248 | 2025-12-22 23:01 | FAILURE | ci(deps): guard that requirements.txt matches uv.lock export |
| #249 | 2025-12-22 22:42 | FAILURE | deps: make pyproject+uv.lock the source of truth |
| #250 | 2025-12-23 00:38 | FAILURE | feat(ops): add ops_doctor repo health check tool |
| #251 | 2025-12-23 00:51 | FAILURE | docs(ops): add PR #250 merge log |
| #253 | 2025-12-23 01:02 | FAILURE | docs(ops): document known CI audit non-blocking issue |
| #256 | 2025-12-23 02:03 | FAILURE | ci(policy): add format-only verifier guardrail for Policy Critic |
| #260 | 2025-12-23 03:51 | FAILURE | docs(ops): record toolkit smoke run |
| #261 | 2025-12-23 04:46 | FAILURE | chore(ops): add stash triage helper (export-first) |
| #262 | 2025-12-23 05:05 | FAILURE | docs(ops): add merge log workflow standard + template |
| #263 | 2025-12-23 05:19 | FAILURE | docs(ops): add merge log for PR #262 (meta: workflow standard) |
| #264 | 2025-12-23 05:27 | FAILURE | docs(ops): add PR #262 as merge log workflow example |
| #265 | 2025-12-23 05:52 | FAILURE | feat(ops): add ops center (central operator entry point) |
| #266 | 2025-12-23 05:59 | FAILURE | docs(ops): add PR #265 merge log |

**Wichtige Erkenntnisse:**
- ✅ Alle haben `run_count = 1` → Keine Re-runs
- ✅ Status blieb FAILURE → Keine späteren erfolgreichen Runs
- ✅ Alle wurden bewusst mit bekanntem FAILURE-Status gemerged

---

## 🔐 Der Wendepunkt: PR #267

**Titel:** "Activate P0 Guardrails: CODEOWNERS, merge queue support, and GitHub security configuration"  
**Erstellt:** 2025-12-23 07:00:23 UTC  
**Merged:** 2025-12-23 (erfolgreich mit Audit SUCCESS)

### Was wurde aktiviert:

#### 1. Workflow-Änderungen
- `merge_group` Trigger zu 8 Workflows hinzugefügt:
  - `.github/workflows/audit.yml` ✅
  - `.github/workflows/ci.yml`
  - `.github/workflows/lint.yml`
  - `.github/workflows/policy_critic.yml`
  - `.github/workflows/deps_sync_guard.yml`
  - `.github/workflows/test_health.yml`
  - Guard-Workflows

#### 2. Branch Protection (via GitHub UI konfiguriert)
```json
{
  "required_status_checks": {
    "strict": false,
    "contexts": [
      "audit",  ← JETZT REQUIRED
      "CI Health Gate (weekly_core)",
      "Guard tracked files in reports directories",
      "tests (3.11)",
      "strategy-smoke",
      "Policy Critic Gate",
      "Lint Gate",
      "Docs Diff Guard Policy Gate",
      "docs-reference-targets-gate"
    ]
  },
  "enforce_admins": {
    "enabled": true  ← Admins können nicht bypassen
  },
  "required_pull_request_reviews": {
    "required_approving_review_count": 0
  }
}
```

#### 3. Weitere Guardrails
- CODEOWNERS für kritische Pfade aktiviert
- Merge Queue Support vorbereitet
- Security Features dokumentiert

---

## 📈 Timeline Visualisierung

```
22. Dez 22:42 UTC  ┌─────────────────────────────────┐
                   │  PRs #248-266                    │
                   │  Audit-FAILURE = NON-BLOCKING    │
                   │  13 PRs trotz Failure gemerged   │
23. Dez 05:59 UTC  └─────────────────────────────────┘
                              ↓
23. Dez 07:00 UTC  ┌─────────────────────────────────┐
                   │  PR #267: "Activate Guardrails"  │
                   │  Branch Protection konfiguriert  │
23. Dez 07:XX UTC  └─────────────────────────────────┘
                              ↓
23. Dez 07:13 UTC  ┌─────────────────────────────────┐
                   │  Ab PR #268                      │
                   │  Audit-FAILURE = BLOCKING        │
                   │  PRs #268, #269 können nicht     │
heute              │  mehr gemerged werden             │
                   └─────────────────────────────────┘
```

---

## 🟡 Aktuell blockierte PRs mit Audit-FAILURE

| PR # | Status | Erstellt | Titel |
|------|--------|----------|-------|
| #259 | OPEN | 2025-12-23 | ci(policy): run Policy Critic even when format-only verifier fails |
| #269 | OPEN | 2025-12-23 | chore(github): P0 guardrails (CODEOWNERS + workflows + docs) |
| #283 | OPEN | 2025-12-24 | docs(ops): integrate merge-log batch generator into ops center |
| #303 | OPEN | 2025-12-25 | docs(risk): portfolio-level VaR roadmap |

**Action Items:**
- Diese PRs müssen die Audit-Failures beheben, bevor sie gemerged werden können
- Link zu Failure-Details in: `reports/pr_audit_scan_230_353_*.tsv`

---

## ✅ Validierung nach Aktivierung (PRs #270-353)

**Alle gemergten PRs ab #270 haben Audit-SUCCESS:**

Stichprobe:
- #270: MERGED + SUCCESS (feat: risk layer v1)
- #271: MERGED + SUCCESS (chore: unify formatting)
- #272: MERGED + SUCCESS (test: validate P0 guardrails)
- #273-280: MERGED + SUCCESS
- ...
- #353: MERGED + SUCCESS (aktuelle PR)

**Erfolgsrate seit Aktivierung:** ~100% (alle gemergten PRs bestehen den Audit)

---

## 📂 Generierte Daten-Artefakte

1. **`reports/audit_runs_nonsuccess_*.tsv`**
   - Alle Workflow-Runs mit non-success Status
   - Zeitraum: Letzte 500 Runs des Audit-Workflows

2. **`reports/pr_audit_scan_230_353_*.tsv`**
   - Status aller PRs #230-353
   - Spalten: pr, state, mergedAt, conclusion, check_name, check_url, pr_url, title

3. **`reports/audit_merge_time_vs_latest_*.tsv`**
   - Detailanalyse der 13 gemergten FAILURE-PRs
   - Vergleich: Status beim Merge vs. aktueller Status
   - Spalten: pr, mergedAt, headSha, merge_time_conclusion, latest_conclusion, run_count

---

## 🎓 Lessons Learned

### Positives:
1. ✅ Branch Protection wurde erfolgreich aktiviert und funktioniert
2. ✅ Enforcement ist streng: `enforce_admins = true`
3. ✅ Audit-Check ist nun Teil eines umfassenden Gate-Systems (9 required checks)
4. ✅ Keine PRs mit Failure wurden seit Aktivierung gemerged

### Verbesserungspotential:
1. ⚠️ Die 13 PRs vor Aktivierung wurden mit bekanntem FAILURE gemerged
   - Möglicherweise beabsichtigt während der Einrichtungsphase
   - Dokumentiert in PR #253: "document known CI audit non-blocking issue"

2. 💡 4 PRs sind derzeit blockiert und benötigen Fixes
   - Siehe Liste oben für Details

---

## 📋 Empfehlungen

### Kurzfristig:
1. **Blockierte PRs aufarbeiten** (#259, #269, #283, #303)
   - Audit-Failures analysieren und beheben
   - Oder PRs schließen, falls nicht mehr relevant

2. **Pre-Guardrails PRs reviewen** (#248-266)
   - Nachträgliche Audit-Review durchführen
   - Potenzielle Probleme identifizieren und beheben

### Mittelfristig:
1. **Monitoring einrichten**
   - Alert bei Audit-Failures einrichten
   - Regelmäßige Reports über Check-Erfolgsraten

2. **Dokumentation erweitern**
   - Audit-Check Anforderungen dokumentieren
   - Troubleshooting-Guide für häufige Failures

3. **Branch Protection Review**
   - `strict: false` → `strict: true` evaluieren
   - Required reviews erhöhen (derzeit 0)

### Langfristig:
1. **Audit-Check optimieren**
   - Failure-Gründe analysieren (aus den 20 Failures)
   - Check robuster/schneller machen
   - False-Positives reduzieren

2. **GitHub Organization upgraden** (falls sinnvoll)
   - Ermöglicht Audit-Log-Zugriff
   - Bessere Team-Verwaltung für CODEOWNERS

---

## 🔗 Relevante Links

- [PR #267: Activate P0 Guardrails](https://github.com/rauterfrank-ui/Peak_Trade/pull/267)
- [P0 Guardrails Setup Guide](docs/GITHUB_P0_GUARDRAILS_SETUP.md)
- [P0 Guardrails Quick Reference](P0_GUARDRAILS_QUICK_REFERENCE.md)
- [Audit Workflow](.github/workflows/audit.yml)

---

## 📊 Anhang: Skripte für Reproduktion

Die Analyse wurde durchgeführt mit:

```bash
# 1. Workflow-Runs mit Failures exportieren
scripts/audit_runs_export.sh  # -> reports/audit_runs_nonsuccess_*.tsv

# 2. PR Audit-Status scannen
scripts/pr_audit_scan.sh  # -> reports/pr_audit_scan_*.tsv

# 3. Merge-Time-Analyse für gemergte Failures
scripts/audit_merge_time_analysis.sh  # -> reports/audit_merge_time_vs_latest_*.tsv

# 4. Branch Protection abrufen
gh api "repos/rauterfrank-ui/Peak_Trade/branches/main/protection" | jq
```

Alle Skripte sind in `scripts/` verfügbar.

---

**Ende des Reports**

