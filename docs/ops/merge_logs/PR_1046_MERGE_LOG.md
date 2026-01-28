# PR 1046 — MERGE LOG

## Summary
PR #1046 wurde als squash gemerged; Branch gelöscht; guarded merge via `--match-head-commit` eingehalten.

## Why
Repo-Doku soll konsistent den neuen Strategy-Lifecycle kommunizieren: `prepare()` ist Hook-only; empfohlen ist `strategy.run(data)`.

## Changes
- docs&#47;STRATEGY_DEV_GUIDE.md
  - Beispiele auf Standard-Aufruf `strategy.run(df)` umgestellt (statt `generate_signals(df)` direkt)
  - ML-Beispiel-Fehlermeldung angepasst: Verweis auf `run()` bzw. `prepare_once()` statt „call prepare first“

## Verification
- PR Checks: alle relevanten Checks PASS
- Lokal (wie in PR beschrieben):
  - `python3 scripts&#47;ops&#47;validate_docs_token_policy.py --tracked-docs` → PASS
  - `bash scripts&#47;ops&#47;verify_docs_reference_targets.sh --warn-only` → PASS

## Merge Evidence
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/1046
- state: MERGED
- mergedAt: 2026-01-28T09:01:31Z
- mergeCommit: ec857a4db18d4daf0224ca77ed1d315dacbe54aa
- approval_exact_comment_id: 3809907681

## Risk
Low (Docs-only).

## Operator How-To
- Keine Operator-Aktion notwendig.

## References
- PR #1046
