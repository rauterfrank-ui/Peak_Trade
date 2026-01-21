# PR #499 — ops(docs): self-contained Cursor timeout triage + track log collector

## Summary
PR #499 macht das Cursor-Timeout/Hang-Runbook operational und self-contained: tote Script-Referenzen wurden entfernt und durch inline, copy-paste-fähige Diagnose-Commands ersetzt. Zusätzlich wurde das Evidence-Pack auf `.tgz` konsolidiert und macOS-spezifische Advanced Diagnostics ergänzt. Ein Log-Collector wurde als ausführbares Script getrackt.

## Why
- Das Runbook referenzierte ein nicht existierendes Script (`triage_cursor_hang.sh`) und war dadurch für Operatoren faktisch nicht ausführbar.
- Erwartetes Evidence-Pack-Format war inkonsistent (.zip vs. tatsächlich .tgz), was zu Operator-Fehlannahmen führt.
- macOS-spezifische Diagnostik (für echte Hangs) fehlte.

## Changes
- Runbook vollständig self-contained gemacht (keine Dependencies auf externe Triage-Scripts).
- Inline-Diagnoseblöcke (No-Sudo) ergänzt: Prozess-/System-Snapshots, best-effort Netzwerk-Hinweise.
- Evidence-Pack Workflow als Checkliste präzisiert; Dokumentation konsistent auf `.tgz`.
- Advanced Diagnostics (macOS) ergänzt: `sample`, `spindump`, `fs_usage` inkl. sudo/Privacy-Hinweisen.
- `scripts/ops/collect_cursor_logs.sh` neu getrackt und executable (Mode 755); erzeugt `artifacts&#47;cursor_logs_YYYYMMDD_HHMMSS.tgz`.

## Verification
- CI grün (alle Checks erfolgreich).
- Runbook enthält keine Referenz mehr auf `triage_cursor_hang.sh`.
- Evidence-Pack Output-Format konsistent: `.tgz`.
- Commands sind nicht destruktiv; Advanced Diagnostics sind explizit als sudo/optional gekennzeichnet.

## Risk
- Logs/Snapshots können sensitive Daten enthalten (User-Pfade, Repo-Namen, Command-History, Extension-Infos). Vor externem Sharing sanitizen.
- macOS Advanced Diagnostics erfordern sudo und können macOS Permission Prompts auslösen.

## Operator How-To
1) `docs/ops/CURSOR_TIMEOUT_TRIAGE.md` öffnen und der „Evidence Pack"-Checkliste folgen.
2) Quick Snapshot (No-Sudo) ausführen.
3) Log-Bundle erzeugen:
   - bevorzugt: `scripts/ops/collect_cursor_logs.sh`
   - fallback: `bash scripts&#47;ops&#47;collect_cursor_logs.sh`
4) Optional (bei harten Hangs): macOS Advanced Diagnostics ausführen (sudo), Artefakte zusammen mit dem `.tgz` ablegen.

## References
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/499
- Squash commit: `f94b43b` — ops(docs): self-contained Cursor timeout triage + track log collector (#499)
- Files:
  - `docs/ops/CURSOR_TIMEOUT_TRIAGE.md`
  - `scripts/ops/collect_cursor_logs.sh`
