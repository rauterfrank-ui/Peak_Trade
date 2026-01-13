# MERGE LOG — PR #694 — docs(ops): v2 auto-fixer + tests for docs token policy gate

**PR:** https://github.com/rauterfrank-ui/Peak_Trade/pull/694  
**Merged:** 2026-01-13  
**Merge Commit:** `<pending-auto-merge>`

---

## Zusammenfassung

- Erweitert das Docs Token Policy Gate Runbook um eine "Auto-Fix Scripts" Sektion, die den konservativen v2 auto-fixer empfiehlt (v1 als Fallback erhalten)
- Fügt Unit Tests für v2 auto-fixer Heuristiken und Edge Cases hinzu (13 Test-Cases)

## Warum

- **Operator-Safe Remediation:** Bietet einen rauscharmen, sicheren Weg zur Behebung von `docs-token-policy-gate` Failures
- **Regression Prevention:** Sichert v2 Klassifikations- und Rewrite-Verhalten durch schnelle, deterministische Tests
- **Low-Noise Strategy:** v2 ist selektiv (nur commands/endpoints), verhindert Over-Escaping wie bei v1 (aggressiv)

## Änderungen

**Geändert**
- `docs/ops/runbooks/RUNBOOK_DOCS_TOKEN_POLICY_GATE.md`
  - Neue Sektion "Auto-Fix Scripts" mit v2-first Guidance (konservativ) und v1 als Fallback (aggressiv)
  - Dokumentiert Idempotenz-Erwartungen und Operator-Validierungs-Befehle
  - Usage: `python3 scripts&#47;ops&#47;autofix_docs_token_policy_inline_code_v2.py --dry-run <files>` → `--write <files>`

**Neu**
- `tests/ops/test_autofix_docs_token_policy_v2.py` (150 Zeilen) — Unit Tests für v2 auto-fixer:
  - **Command Token Detection:** pytest/git/uv/python/gh/curl/make/bash/zsh
  - **HTTP Endpoint Detection:** GET/POST/DELETE + path patterns (z.B. `GET &#47;ops&#47;ci-health`)
  - **URL Skipping:** http:// und https:// URLs werden nicht rewritten
  - **Idempotency:** Already-escaped tokens (`&#47;`) werden nicht erneut rewritten
  - **Fenced Block Protection:** Code in ``` ... ``` Blöcken wird nicht modifiziert
  - **Coverage:** 13/13 Tests passed in 0.06s

## Verifikation

**Lokal**
```bash
# 1. Run v2 unit tests
uv run python -m pytest tests/ops/test_autofix_docs_token_policy_v2.py -v
# Expected/Observed: 13 passed

# 2. Validate gates
uv run python scripts/ops/validate_docs_token_policy.py --changed
# PASS

bash scripts/ops/verify_docs_reference_targets.sh --changed
# PASS
```

**CI**
- docs-token-policy-gate: PASS
- docs-reference-targets-gate: PASS
- Lint Gate: PASS (formatting fix applied)
- tests (3.9, 3.10, 3.11): PASS
- All 23 required checks: PASS

## Risiko

**Risk:** 🟢 Low (docs-only + additive; no workflow changes; v1 remains available and unchanged)

**Begründung**
- **Docs-only PR:** Keine Runtime-Code-Änderungen, keine CI-Workflow-Änderungen
- **Additive:** v2 bleibt unverändert (nur formatiert), v1 bleibt als Fallback
- **Test Coverage:** 13 Tests decken alle v2 Heuristiken ab
- **No Breaking Changes:** Validator und CI Gates unverändert

## Rollback

- Use v1 script as fallback (unchanged)
- Revert PR #694 (docs-only; no runtime impact)
- If needed, allowlist specific edge cases rather than widening global rewrites

## Operator How-To

**Preferred (v2):**
```bash
# 1. Preview changes (dry-run)
python3 scripts/ops/autofix_docs_token_policy_inline_code_v2.py --dry-run <file1.md> <file2.md>

# 2. Apply fixes
python3 scripts/ops/autofix_docs_token_policy_inline_code_v2.py --write <file1.md> <file2.md>

# 3. Verify gates
uv run python scripts/ops/validate_docs_token_policy.py --changed
bash scripts/ops/verify_docs_reference_targets.sh --changed
```

**Fallback (v1, aggressive):**
```bash
# Use v1 if v2 misses violations (rewrites ALL "/" in inline-code)
python3 scripts/ops/autofix_docs_token_policy_inline_code.py --dry-run <file1.md>
python3 scripts/ops/autofix_docs_token_policy_inline_code.py --write <file1.md>

# Verify gates
uv run python scripts/ops/validate_docs_token_policy.py --changed
bash scripts/ops/verify_docs_reference_targets.sh --changed
```

## Referenzen

- **PR #694:** https://github.com/rauterfrank-ui/Peak_Trade/pull/694
- **PR #693 (Initial Gate):** https://github.com/rauterfrank-ui/Peak_Trade/pull/693
- **Merge Commit:** `<pending-auto-merge>`
- **Runbook:** `docs/ops/runbooks/RUNBOOK_DOCS_TOKEN_POLICY_GATE.md`
- **v2 Auto-Fixer:** `scripts/ops/autofix_docs_token_policy_inline_code_v2.py`
- **v2 Tests:** `tests/ops/test_autofix_docs_token_policy_v2.py`
