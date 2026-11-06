# Evidence: Learning & Promotion Loop v1 – Verify (2026-01-27)

## Scope

- **Ziel**: “Docs-Konsistenz-Finalizer” für Learning&#47;Promotion&#47;Overrides + ausführbare Quickstart-Kommandos.
- **Nicht im Scope**: Live-Trading&#47;Execution-Änderungen (keine Touches an `src&#47;execution&#47;**`, `src&#47;risk&#47;**`, `src&#47;governance&#47;**` außerhalb Promotion-Loop-Doku).

## Repo Context

- **Repo**: `/Users/frnkhrz/Peak_Trade`
- **Branch**: `main` (lokal)

## Verifikation – Commands (copy/paste)

```bash
# Smoke: Runner muss auch ohne Inputs clean laufen
python3 scripts/run_learning_apply_cycle.py --dry-run

# Tests: Full suite
python3 -m pytest -q
```

## Observed Results

### Smoke (Learning Apply Runner)

- Ergebnis: **PASS**
- Erwartetes Verhalten bei leerem Input-Dir: Hinweis + Exit Code 0

### Tests

- Ergebnis: **PASS**
- Zusammenfassung: `6577 passed, 51 skipped, 3 xfailed, 1 warning`

## Docs Gates / Hygiene (lokal)

### Markdown Link Checker

```bash
python3 scripts/ops/check_markdown_links.py --paths \
  docs/RELEASE_NOTES_LEARNING_PROMOTION_LOOP_V1.md \
  docs/LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md \
  docs/LEARNING_PROMOTION_LOOP_INDEX.md \
  docs/QUICKSTART_LIVE_OVERRIDES.md \
  docs/LIVE_OVERRIDES_CONFIG_INTEGRATION.md \
  docs/IMPLEMENTATION_SUMMARY_LIVE_OVERRIDES.md \
  docs/learning_promotion/CHANGELOG_LEARNING_PROMOTION_LOOP.md \
  docs/PROMOTION_LOOP_V0.md
```

- Ergebnis: **PASS** (`no broken internal links found`)

### Docs Gates Snapshot (PR Mode)

```bash
bash scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main
```

- Hinweis: `--changed` arbeitet gegen committed Diff (PR&#47;HEAD). Lokal ohne Commit kann “not applicable” erscheinen.

## Notes

- Inline-Code Pfade wurden token-safe gehalten (z.B. `config&#47;...`, `scripts&#47;...`) oder als Code-Fences ausgeführt.
