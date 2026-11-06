# PR 1080 — Merge Log

PR: https:&#47;&#47;github.com&#47;rauterfrank-ui&#47;Peak_Trade&#47;pull&#47;1080

## Summary
- Docs: Standardisiert CLI-Beispiele auf `python3` / `python3 -m pytest` und reduziert Docs-Gate False-Positives (Token-Policy Validator akzeptiert `python3`/`python3.x` als Prefix).
- Portfolio: Vereinheitlicht Stress-Szenario-IDs in Presets/Recipes auf kanonische Namen.
- Tools: `run_portfolio_robustness` erhält Phase-53 **strategies-mode** (`strategies=[...]`) inkl. deterministischem Dummy-Returns-Cache (gated via `--use-dummy-data`); Golden-Path/Market-Scan/Sweep Defaults + Test angepasst.

## Why
- Konsistente, copy&#47;paste-sichere Docs & robustere Token-Policy-Validierung.
- Verhindert ID-Drift bei Stress-Szenarien zwischen Presets/Recipes/CLI.
- Phase-53 Presets laufen deterministisch über einen expliziten strategies-Pfad (kein Sweep&#47;Top-N).

## Changes
- Commit 1 (docs): breite Docs-Hygiene + `scripts&#47;ops&#47;validate_docs_token_policy.py` Prefix-Erweiterung.
- Commit 2 (funktional): Presets/Recipes Stress-IDs kanonisiert; Runner Defaults auf `config&#47;config.toml`; Phase-53 strategies-mode + Test.

## Verification
- `python3 scripts&#47;ops&#47;validate_docs_token_policy.py --paths docs`
- `python3 -m pytest -q tests&#47;test_research_cli_portfolio_presets.py`

## Risk
LOW–MEDIUM: Docs-Änderungen risikoarm; CLI-Default-Config-Pfad wurde intentionell vereinheitlicht. strategies-mode ist explizit via `--use-dummy-data` gated.

## Operator How-To
- Phase-53 Presets (Dummy-Pfad):
  - `python3 scripts&#47;run_portfolio_robustness.py --preset <PHASE53_PRESET> --use-dummy-data`

## References
- Merge Evidence (Truth):
  - state=MERGED
  - mergedAt=2026-01-30T15:36:20Z
  - mergeCommit=f866de04769fa310e63bc663a3da9882738180c0
  - matched headRefOid (guard)=883a4338812d15086761f5f6eb41a17427ee5193
