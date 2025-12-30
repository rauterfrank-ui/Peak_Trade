# Incident / RCA: Formatter Drift im Audit-Check → Tool Alignment (2025-12-26)

## Summary
Ein Audit-Failure am 2025-12-26 war ein **Detektor** für einen latenten Tool-Alignment-Drift:  
Repo/Pre-Commit Standard ist **ruff format**, während Branch-Inhalte teils **black-formatiert** waren bzw. Legacy-Referenzen im Audit-Kontext existierten.  
Ergebnis: `ruff format --check` hat korrekt Drift gefunden und den PR blockiert. Anschließend wurde der Drift behoben und dauerhaft eliminiert (Tool-Alignment PR).

## Impact Scope
- Affected PRs: **#259, #269, #283, #303**
- Beobachtetes Symptom: Audit failures (Formatter / Tests)
- Governance outcome: **korrektes Blockieren** durch Required Checks (kein Bypass)

## Evidence Chain
- PR #354 (Tool Alignment): https://github.com/rauterfrank-ui/Peak_Trade/pull/354
- Run #20527440524 (Audit success / alignment): https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20527440524

## Timeline (UTC)
- ❌ 18:21 — Run #20527237392 (PR #259 / `ci/policy-critic-always-run`)
  - Finding: `ruff format --check` failed (exit 1)
  - Tool detection: `ruff OK`, `black OK` (Legacy), `rg missing`
  - Interpretation: realer Formatter-Drift; Audit hat korrekt blockiert
- ✅ 18:26 — Run #20527299199 (gleicher Branch)
  - Fix: Code mit **ruff format** reformatiert → Audit success
- ✅ 18:36 — Tool-Alignment merged (PR #354, Commit 16f0614)
  - Entfernt Legacy-`black` aus `scripts/ops/run_audit.sh`
  - Single Source of Truth: **RUFF**

## Root Cause
**Tool-Alignment Drift / Legacy-Formatter:**  
Historisch existierte `black` (Legacy) als Referenz im Audit-Kontext, während Repo-Standard `ruff format` ist.  
Branches mit black-formatierten Änderungen führen dann korrekt zu `ruff format --check` failures.

## Remediation
- Sofort: Betroffene Branches via `uv run ruff format .` auf Repo-Standard gebracht.
- Dauerhaft: PR #354 entfernte black-Legacy aus `scripts/ops/run_audit.sh` und erzwingt ruff-only.

## Verification
- Guardrail: `bash scripts/ops/check_no_black_enforcement.sh` ✅
- Audit formatting: `uv run ruff format --check .` ✅

## Resolution Status
- #259 ✅ (Audit success)
- #269 🔄 pending (Merge-Konflikte / CI)
- #283 🔄 pending (Merge-Konflikte / CI)
- #303 🔄 pending (Merge-Konflikte / CI)

## Follow-up (optional hardening)
`rg missing` tauchte in CI auf:
- Lokal: ✅ installiert (v15.1.0)
- CI: ❌ nicht installiert
Empfehlung: `ripgrep` in `audit.yml` installieren oder `run_audit.sh` mit grep-fallback robust machen.
