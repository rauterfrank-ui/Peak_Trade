# Phase C4 – Restack Risk-PR auf main (nach B1-Merge)

**Ziel:** Risk-PR zeigt nur Risk-Änderungen (direkt gegen main), sobald B1 gemerged ist.

## Merge-Reihenfolge (manuell im Browser)

1. **B1:** https://github.com/rauterfrank-ui/Peak_Trade/compare/feat/research-cli-evidence-chain?expand=1  
2. **B2:** https://github.com/rauterfrank-ui/Peak_Trade/compare/feat/live-ops-evidence-chain?expand=1  
3. **C:**  https://github.com/rauterfrank-ui/Peak_Trade/compare/feat/risk-var-core?expand=1  

## Sobald B1 in main ist: Restack ausführen

```bash
cd "$(git rev-parse --show-toplevel)"
git checkout feat/risk-var-core
git fetch origin main --prune
# Prüfen:
git show origin/main:src/ops/evidence.py >/dev/null 2>&1 && echo "OK: evidence.py on main" || echo "WAIT: B1 not merged yet"
# Nur wenn OK:
git rebase origin/main
# Bei Konflikt in src/ops/evidence.py: main behalten
# git checkout --ours src/ops/evidence.py
# git add src/ops/evidence.py
# git rebase --continue
# Post-check:
git diff --name-only origin/main...HEAD | grep -E '^(src/ops/evidence\.py|scripts/research_cli\.py)$' && echo "ERROR: base leakage" || echo "OK: risk-only diff"
# Smoke + Push:
PEAKTRADE_SANDBOX=1 python3 scripts/risk_cli.py --run-id smoke_c4 var --returns-file tests/fixtures/returns_normal_5k.txt --alpha 0.99 --method historical
python3 -m pytest -q tests/risk/test_var_core.py tests/risk/test_risk_cli_smoke.py --maxfail=1
git push --force-with-lease origin feat/risk-var-core
```

## Aktueller Status

- **WAIT:** B1 noch nicht in main → Rebase auf main erst nach B1-Merge ausführen.
- Bis dahin: Risk-PR bleibt auf B1 gestackt (Base = feat/research-cli-evidence-chain).
