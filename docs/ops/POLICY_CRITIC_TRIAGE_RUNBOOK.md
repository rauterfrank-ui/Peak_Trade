# Policy Critic Triage Runbook – Format-Only False Positives

**Zweck:** Operator-Runbook für Format-only PRs, die vom Policy Critic zu Unrecht blockiert werden.

**Zielgruppe:** Ops Engineers, Release Maintainer

**Status:** Active (v1.0)

---

## 📋 Quick Reference

**Problem:** Policy Critic blockiert einen PR, aber es ist ein reiner Format-Change ohne Logik-Änderung.

**Lösung:** Preflight-Checks → Admin-Bypass (mit Audit-Trail) → Post-Merge Sanity-Checks.

---

## 1️⃣ Definition: "Format-Only" PR

### ✅ Format-Only (Safe)

- **Black** / **Ruff** Auto-Formatting (line breaks, quotes, whitespace)
- **Import Sorting** (isort, Ruff `I` rules)
- **Whitespace Cleanup** (trailing spaces, newlines)
- **Docstring Formatting** (keine inhaltlichen Änderungen)
- **Pre-commit Hook Fixes** (nur Formatting)

### ❌ NICHT Format-Only (Unsafe)

- **Logic Changes** (if/else, loops, function calls)
- **Config Changes** (TOML, YAML, JSON values)
- **Dependency Updates** (requirements.txt, uv.lock, pyproject.toml)
- **Governance Changes** (Policy Packs, CI/CD Workflows)
- **Risk/Execution Changes** (src/risk/, src/execution/, src/live/)
- **Test Logic** (assertions, test cases, fixtures)
- **Schema/Model Changes** (data models, DB schemas)

---

## 2️⃣ Preflight-Checks

```bash
# 1) PR-Details abrufen
gh pr view <PR_NUMBER> --json title,body,changedFiles,files

# 2) Diff-Statistik prüfen
gh pr diff <PR_NUMBER> --stat

# 3) Changed Files auflisten
gh pr view <PR_NUMBER> --json files --jq '.files[].path'

# 4) Spot-Check: Diff durchsehen (erste 50 Zeilen)
gh pr diff <PR_NUMBER> | head -50
```

### ✅ Preflight-Checklist

- [ ] Titel deutet auf Format-only hin (`chore(format):`, `style:`, `black/ruff`)
- [ ] Keine `src/execution/`, `src/risk/`, `src/live/` Dateien geändert
- [ ] Keine `config/*.toml`, `pyproject.toml`, `requirements.txt` Änderungen
- [ ] Keine `.github/workflows/`, `policy_packs/` Änderungen
- [ ] Diff zeigt nur whitespace/import-order/quotes
- [ ] Policy Critic Details geprüft (URL im PR Comment)

**Wenn ALLE ✅ → Weiter zu Schritt 3.**

**Wenn EINE ❌ → STOP! Kein Bypass!** Siehe Abschnitt 4 (Do NOT Bypass).

---

## 3️⃣ Decision Tree: Admin-Bypass

```
┌─────────────────────────────────┐
│ Policy Critic blockiert PR?    │
└────────────┬────────────────────┘
             │
             ▼
       ┌──────────┐
       │ Format-  │ NO ──► STOP: Regulärer Review-Prozess
       │ only?    │
       └─────┬────┘
             │ YES
             ▼
   ┌────────────────────┐
   │ Preflight-Checks   │
   │ alle ✅?           │
   └─────┬──────────────┘
         │ YES
         ▼
┌──────────────────────────┐
│ 1) Audit-Kommentar       │
│ 2) Admin-Bypass Merge    │
│ 3) Post-Merge Sanity     │
└──────────────────────────┘
```

---

## 4️⃣ Admin-Bypass Vorgehen

### Step 1: Audit-Trail Kommentar

```bash
# Kommentar im PR hinterlassen
gh pr comment <PR_NUMBER> --body "$(cat <<'EOF'
## 🛡️ Policy Critic Bypass – Audit Trail

**Bypass Grund:** Format-only PR (false positive)

**Operator:** @<YOUR_GITHUB_USERNAME>
**Timestamp:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")

### Preflight-Checks Ergebnis
- ✅ Format-only (Black/Ruff/Import-Sorting)
- ✅ Keine Logic/Config/Deps Änderungen
- ✅ Keine Governance/Risk/Execution Dateien
- ✅ Policy Critic Details geprüft: <POLICY_CRITIC_DETAILS_URL>

### Evidence
\`\`\`bash
gh pr diff <PR_NUMBER> --stat
\`\`\`

**Decision:** Admin-Bypass approved (format-only false positive).

**Post-Merge Plan:**
1. `ruff check .` (CI)
2. `black --check .` (CI)
3. Optional: `pytest tests/ -x` (Smoke Test)

**Rationale:** No logic impact, pure formatting. Policy Critic triggered on diff size, but changes are mechanical (auto-formatter).

---
**Approved by:** @<YOUR_GITHUB_USERNAME>
**Merge Method:** Admin-Bypass (--admin)
EOF
)"
```

**Template Variables:**
- `<PR_NUMBER>` → PR-Nummer
- `<YOUR_GITHUB_USERNAME>` → Dein GitHub Username
- `<POLICY_CRITIC_DETAILS_URL>` → Link zu Policy Critic Details (aus PR Comment)

---

### Step 2: Admin-Bypass Merge

```bash
# Merge mit --admin Flag (umgeht Required Checks)
gh pr merge <PR_NUMBER> \
  --admin \
  --squash \
  --subject "chore(format): <SHORT_TITLE>" \
  --body "Format-only PR. Policy Critic bypass approved (false positive). See PR comments for audit trail."
```

**Flags:**
- `--admin` → Umgeht Required Checks (nur für Admins)
- `--squash` → Squash-Merge (Clean History)
- `--subject` → Custom Commit Message
- `--body` → Merge Commit Body (Rationale)

**⚠️ Nur ausführen wenn:**
- Preflight-Checks alle ✅
- Audit-Kommentar erstellt
- Du bist Admin/Maintainer

---

### Step 3: Post-Merge Sanity-Checks

```bash
# Lokalen main branch aktualisieren
git checkout main
git pull --ff-only

# 1) Ruff Check (Linting)
ruff check .

# 2) Black Check (Formatting)
black --check .

# 3) Optional: Pytest Smoke Test (Sample)
pytest tests/test_utils_sample.py -x

# 4) CI Status prüfen (nach ~2-5min)
gh pr view <PR_NUMBER> --json statusCheckRollup

# 5) Fallback: CI-Run auf main prüfen
gh run list --branch main --limit 1
```

**Expected Results:**
- `ruff check .` → ✅ No errors
- `black --check .` → ✅ No changes needed
- CI auf main → ✅ Passing

**Bei Fehler:**
- Revert Commit erstellen
- Issue öffnen (Label: `ops/policy-critic-false-positive`)
- Post-Mortem durchführen

---

## 5️⃣ Do NOT Bypass – Stop Criteria

**STOP und kein Admin-Bypass bei folgenden Änderungen:**

### 🔴 Critical (Always Block)

- [ ] **Execution Pipeline:** `src/execution/`, `src/execution_simple/`, `src/live/`
- [ ] **Risk Management:** `src/risk/`, `src/governance/`
- [ ] **Live Trading:** `src/live/`, `config/live_policies.toml`
- [ ] **Dependencies:** `requirements.txt`, `uv.lock`, `pyproject.toml` (versions)
- [ ] **Governance:** `policy_packs/`, `.github/workflows/policy_*.yml`
- [ ] **Config Values:** `config/*.toml` (nicht whitespace, sondern Werte)

### 🟡 High-Risk (Verify First)

- [ ] **Tests:** Neue/geänderte Assertions, Fixtures, Test-Logic
- [ ] **CI/CD:** `.github/workflows/`, `docker/`, `Makefile` (Logic)
- [ ] **Schema:** Data schemas, DB Migrations
- [ ] **Telemetry:** `src/obs/`, `config/telemetry_alerting.toml`
- [ ] **Macro Regimes:** `config/macro_regimes/`, `src/macro_regimes/`

### 🟢 Okay for Bypass (Format-Only)

- [ ] **Black/Ruff:** Whitespace, Quotes, Line Breaks
- [ ] **Import Sorting:** `import` Statement Order
- [ ] **Docstrings:** Formatting (keine Inhaltsänderungen)
- [ ] **Comments:** Whitespace, Trailing Spaces
- [ ] **Markdown:** Docs-Formatting (`docs/*.md`, README.md)

---

## 6️⃣ Evidence & Logging

### Was ins PR muss (Audit-Trail)

1. **Policy Critic Details URL** (aus PR Comment/Check)
2. **Preflight-Checks Output** (gh pr diff --stat)
3. **Changed Files List** (gh pr view --json files)
4. **Rationale** (warum Format-only, warum False Positive)
5. **Operator Name + Timestamp** (Accountability)
6. **Post-Merge Plan** (ruff/black/pytest)

### Template-Kommentar (siehe Step 1 oben)

```markdown
## 🛡️ Policy Critic Bypass – Audit Trail
**Bypass Grund:** ...
**Operator:** ...
**Timestamp:** ...
**Evidence:** ...
**Decision:** ...
**Post-Merge Plan:** ...
```

---

## 7️⃣ Minimal-Kommandos (Cheat Sheet)

```bash
# 1) PR Details
gh pr view <PR_NUMBER>

# 2) Diff Stat
gh pr diff <PR_NUMBER> --stat

# 3) Files Changed
gh pr view <PR_NUMBER> --json files --jq '.files[].path'

# 4) Spot-Check Diff
gh pr diff <PR_NUMBER> | head -50

# 5) Audit-Kommentar
gh pr comment <PR_NUMBER> --body "<AUDIT_TEMPLATE>"

# 6) Admin-Merge
gh pr merge <PR_NUMBER> --admin --squash

# 7) Lokalen main updaten
git checkout main && git pull --ff-only

# 8) Sanity-Checks
ruff check . && black --check .

# 9) CI Status prüfen
gh run list --branch main --limit 1
```

---

## 8️⃣ Rollback-Plan (bei Post-Merge Fehler)

```bash
# 1) Merge Commit finden
git log --oneline -1

# 2) Revert erstellen
git revert HEAD

# 3) Revert pushen
git push origin main

# 4) Issue öffnen
gh issue create \
  --title "Policy Critic Bypass Rollback: PR #<PR_NUMBER>" \
  --label "ops/policy-critic-false-positive" \
  --body "Revert required. Post-merge checks failed. See logs."

# 5) Post-Mortem
# - Was ging schief?
# - War es wirklich format-only?
# - Policy Critic Regel anpassen?
```

---

## 9️⃣ FAQ

### Q: Wann ist ein PR "format-only"?

**A:** Wenn ALLE Änderungen rein mechanisch sind (Black, Ruff, isort) und KEINE Logik/Config/Deps betroffen sind.

### Q: Kann ich Format-Only PRs automatisch mergen?

**A:** Nein. Immer manuell prüfen (Preflight-Checks). Keine Automation für Admin-Bypass.

### Q: Was wenn Policy Critic bei echten Problemen triggert?

**A:** Kein Bypass! Regulärer Review-Prozess. Fixes implementieren, Re-Review.

### Q: Wie erkenne ich Format-Only vs. Logic-Change?

**A:** Diff durchsehen. Format-Only = nur whitespace/quotes/imports. Logic-Change = if/else/loops/function-calls/config-values.

### Q: Was wenn Post-Merge Checks fehlschlagen?

**A:** Sofort Revert (siehe Rollback-Plan), Issue öffnen, Post-Mortem.

---

## 🔗 Verwandte Dokumentation

- [CI Large PR Handling](CI_LARGE_PR_HANDLING.md)
- [Merge Log Template](MERGE_LOG_TEMPLATE_COMPACT.md)
- [PR Report Automation Runbook](PR_REPORT_AUTOMATION_RUNBOOK.md)

---

**Version:** 1.0.0  
**Letzte Aktualisierung:** 2025-12-23  
**Maintainer:** Peak_Trade Ops Team  
**Issue Reference:** #255

<!-- SAFETY_FIX_SECTION_START -->

## Safety Fix: False-Positives reduzieren, ohne Safety zu verlieren

> **⚡ Status:** ✅ **Implemented** (CI-Guardrail aktiv)  
> **Implementation:** `scripts/ops/verify_format_only_pr.sh` + GitHub Actions `format-only-verifier` job  
> **Siehe:** [ops README](README.md)

**Problem:** Wenn Policy Critic bei *format-only* PRs (Black/Ruff) blockiert, entsteht schnell *Bypass-Kultur* (`--admin`) und damit sinkt die reale Sicherheitswirkung des Critic.

**Ziel:** Schneller Merge für echte Format-PRs **ohne** den Safety-Layer zu entwerten.

### Prinzip: "Skip nur mit Guardrail"
Wir erlauben ein gezieltes Skipping von Policy Critic **nur dann**, wenn ein **Format-Only Verifier** sicherstellt, dass der PR wirklich nur Formatierung enthält.

**Bausteine (Minimal-Variante, empfohlen):**
1) **Label:** `ops/format-only`  
2) **CI-Job:** `format-only-verifier` (required check)  
3) **Policy Critic:** skippt **nur**, wenn:
   - Label `ops/format-only` gesetzt **und**
   - `format-only-verifier` **PASS** ist  
   Andernfalls läuft Policy Critic normal und bleibt blockierend.

---

### A) "Format-only" Definition (strict default)
**Strict (empfohlen als Start):**
- Erlaubt: `**/*.py`, `**/*.md`
- In `.py` nur Black/Ruff-Formatierung, Import-Sortierung, whitespace, Kommentar-/Docstring-Whitespace
- **Nicht erlaubt:** jede Änderung an:
  - `**/*.yml|yaml|toml|json` (CI/Config)  
  - `src/**` wenn der Diff nicht eindeutig Formatierung ist
  - Governance/Risk/Execution Pfade (z.B. `src/governance/**`, `src/live/**`, `src/execution/**`)
  - Dependencies (`pyproject.toml`, `requirements*.txt`, `uv.lock`)

**Warum strict?** Weniger False-Negatives → weniger Risiko. Lockern kann man später gezielt.

---

### B) Operator-Flow: Wann Label setzen?
**Nur setzen, wenn alle Punkte erfüllt sind:**
- ✅ `gh pr diff <PR> --stat` wirkt wie Format-Diff
- ✅ `gh pr diff <PR> --name-only` zeigt nur erlaubte Pfade/Typen (strict: `.py/.md`)
- ✅ Spot-Check: `gh pr diff <PR> | sed -n '1,200p'` → keine Logik-/Config-Änderungen sichtbar
- ✅ Audit-Trail Kommentar im PR (Rationale + Evidence + Accountability)

**Label setzen (Beispiel):**
- `gh pr edit <PR> --add-label "ops/format-only"`

---

### C) Format-Only Verifier: Was muss er garantieren?
Der Verifier ist die Sicherheitsbremse: Er muss **FAIL** sein, sobald der PR nicht sicher format-only ist.

**Strict Checks (robust, low-maintenance):**
- 1) **Changed-Files Allowlist**: nur `.py` und `.md`
- 2) **Formatter Idempotenz**:
  - `ruff format` / `black` laufen und erzeugen **keine weiteren** Änderungen
- 3) Optional: "Sensitive path denylist" → FAIL bei Änderungen in Governance/Risk/Execution, selbst wenn `.py`

**Wenn der Verifier FAILt:**
- Label entfernen
- Policy Critic wieder normal laufen lassen
- PR als "nicht format-only" behandeln (normale Review + Checks)

---

### D) GitHub Actions Skizze (Konzept)
**Job 1: `format-only-verifier`**
- Läuft nur, wenn Label vorhanden ist  
- Ist *required check* (Branch Protection)

**Job 2: `policy_critic`**
- Skippt nur, wenn Label gesetzt **und** Verifier PASS  
- Sonst normal blockierend

**Wichtig:** "Skip" ist nur erlaubt, wenn gleichzeitig ein **blockierender Verifier** existiert.

---

### E) Rollback / Safety Net
Wenn sich das Skip/Verifier-Setup als zu streng oder noisy erweist:
- Entferne die Skip-Condition bei Policy Critic
- Behalte den Verifier optional (oder entferne ihn)
- Runbook bleibt gültig (Triage + Audit-Trail)

---

### F) Warum das funktioniert
- Reduziert False-Positive Friction (Format-PRs laufen durch)
- Verhindert Bypass-Kultur (kein `--admin` als Default)
- Erhält die Schutzwirkung: echte PRs triggern weiterhin Policy Critic
- Schafft saubere Evidence Chain (Label + Verifier-Logs + Audit-Trail)

<!-- SAFETY_FIX_SECTION_END -->
