# PR #501 — Merge Log

## Summary
- **PR:** #501 — Cursor Timeout / Hang Triage Quick Start (Frontdoor)
- **Status:** Merged (Squash) into `main`
- **Merge commit:** `e5d4a13`
- **Type:** Docs-only (ops)

## Why
Operatoren benötigen einen schnellen, verlässlichen Einstiegspunkt, um Cursor-Hänger/Timeouts sofort zu triagieren (inkl. Shell-Continuation-Fix) und anschließend das vollständige Runbook sowie Evidence-Pack-Collection aufzurufen.

## Changes
- `docs/ops/README.md`
  - Neue Sektion **"Cursor Timeout / Hang Triage (Quick Start)"**
  - Positioniert direkt nach **"Cursor Multi-Agent Runbooks"**
  - Enthält:
    - Shell-Continuation Fix (`>` / `dquote>` / heredoc-Continuation)
    - Link/Verweis auf das vollständige Runbook
    - Evidence Pack Collection Command
    - Optional: Advanced Diagnostics (macOS)
    - Privacy-Hinweis

## Verification
- `git status -sb` sauber auf `main` nach Merge (keine pending changes)
- Änderung ist **docs-only**; keine Runtime-/CI-Pfade betroffen.

## Risk
- **Low** — Dokumentationsänderung ohne Codepfade.
- Risiko beschränkt auf mögliche Fehlleitung durch Doku; mitigiert durch Verweis auf vollständiges Runbook.

## Operator How-To
1) Bei Cursor-Hänger zuerst Quick Start in `docs/ops/README.md` öffnen.
2) Shell-Continuation fixen (wenn Prompt auf `>` / `dquote>` steht: `Ctrl-C`).
3) Evidence Pack Command ausführen und Logs sichern.
4) Danach dem vollständigen Runbook folgen (Advanced Diagnostics optional).

## References
- PR #501 (Merged): https://github.com/rauterfrank-ui/Peak_Trade/pull/501
- Merge commit: `e5d4a13`
