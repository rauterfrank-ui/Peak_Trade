#!/usr/bin/env bash
# [Cursor Terminal — PR X2 Auto-Prep]
# Zweck:
# 1) Sammeln: git status + diff (unstaged + staged) als Artefakte
# 2) Erzeugen: zwei PR-Body Template-Dateien (Feature + Docs) zum direkten Befüllen/Anpassen
# 3) Alles landet unter docs/ops/pr_bodies/

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

OUT_DIR="docs/ops/pr_bodies"
TS="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$OUT_DIR"

echo "==> Writing git artifacts to $OUT_DIR (timestamp: $TS)"

git status > "$OUT_DIR/git_status_$TS.txt"

# Unstaged
git diff --stat > "$OUT_DIR/git_diff_unstaged_stat_$TS.txt" || true
git diff > "$OUT_DIR/git_diff_unstaged_$TS.patch" || true

# Staged
git diff --cached --stat > "$OUT_DIR/git_diff_staged_stat_$TS.txt" || true
git diff --cached > "$OUT_DIR/git_diff_staged_$TS.patch" || true

git log -10 --oneline > "$OUT_DIR/git_log_10_$TS.txt" || true

echo "==> Creating PR body templates…"

cat > "$OUT_DIR/PR_BODY_FEATURE_TEMPLATE.md" <<'MD'
# Title (suggestion)
feat: <short, specific title>

## Summary
-

## Why
-

## Scope
**In:**
- [ ]

**Out (explicitly not):**
- [ ]

## Changes
-
-

## Safety / Governance
- Policy-Critic-relevant? **[ ] yes / [ ] no**
- Guardrails betroffen (live/execution/risk/governance)? **[ ] yes / [ ] no**
- Neue Defaults konservativer als vorher? **[ ] yes / [ ] no**
- Backwards-compat? **[ ] yes / [ ] no**
- Migration/Config changes needed? **[ ] yes / [ ] no**

## Verification
**CI:**
- [ ] lint gate ✅
- [ ] policy critic gate ✅ / n/a
- [ ] tests (3.11) ✅
- [ ] strategy-smoke ✅
- [ ] audit ✅ / allowed fail (falls zutreffend)

**Local:**
```bash
# minimal
python -m pytest -q

# targeted (anpassen)
python -m pytest -q tests/<area>/
# optional: run relevant script/entrypoint
# python scripts/<...>.py --help
```

## Risk
**Risk Level:** [ ] Low / [ ] Medium / [ ] High

**Failure modes:**
-

**Mitigation:**
-

## Rollback Plan
- **Revert commit / PR:**
- **Config rollback:**
- **Data/Cache considerations (falls relevant):**

## Operator How-To
<!-- Was muss ein Operator konkret tun/prüfen? -->
-

## References
- Closes #___
- Docs: `docs/...`
- Related PRs: #___
MD

cat > "$OUT_DIR/PR_BODY_DOCS_TEMPLATE.md" <<'MD'
# Title (suggestion)
docs: <short, specific title>

## Summary
<!-- 1–2 Sätze: Welche Doku/Runbook/Workflow-Verbesserung? -->
-

## Why
-

## Changes
-
-

## Reader Impact
**Für Operatoren:**
- [ ] Neues Runbook
- [ ] Aktualisierte Quick Commands
- [ ] Neue/angepasste Troubleshooting Steps

**Für Devs:**
- [ ] Template/Standard erweitert
- [ ] CI/Guardrails Doku aktualisiert

## Verification
- [ ] Markdown gerendert/Links geprüft
- [ ] Beispiele/Kommandos einmal ausgeführt (wo möglich)
- [ ] Keine policy-sensitiven Codepfade verändert (falls zutreffend)

```bash
# optional: schnelle Checks (falls im Repo vorhanden)
python -m compileall -q src || true
python -m pytest -q tests/ops/ || true
```

## Risk
**Risk Level:** Low

- Docs-only / keine Runtime-Änderungen

## Operator How-To
<!-- Wenn der PR neue Abläufe beschreibt: mini-checklist -->
-

## References
- Closes #___
- Related: `docs/ops/...`
- Example output: `docs/ops/...`
MD

echo ""
echo "✅ PR Body Templates created:"
echo "   - $OUT_DIR/PR_BODY_FEATURE_TEMPLATE.md"
echo "   - $OUT_DIR/PR_BODY_DOCS_TEMPLATE.md"
echo ""
echo "📊 Git Artifacts (timestamp: $TS):"
ls -lh "$OUT_DIR"/*_$TS.* 2>/dev/null || echo "   (none)"
echo ""
echo "🚀 Next Steps:"
echo "   1) Review git artifacts: cat $OUT_DIR/git_status_$TS.txt"
echo "   2) Fill PR bodies: vim $OUT_DIR/PR_BODY_FEATURE_TEMPLATE.md"
echo "   3) Create PR: gh pr create --body-file $OUT_DIR/PR_BODY_FEATURE_TEMPLATE.md"
