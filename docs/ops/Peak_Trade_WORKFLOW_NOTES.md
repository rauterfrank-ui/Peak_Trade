# Peak_Trade — Workflow Notes (Repo-local)

Diese Datei ist die repo-lokale Referenz für Arbeitskonventionen (Cursor Multi-Agent / Terminal Blocks / Evidence / Gates).
Sie ersetzt externe/mounted Pfade.

## Terminal-Konvention (robust)

- Wenn Prompt in `dquote>` / `cmdsubst>` / `heredoc>` hängt: **Ctrl-C**.
- Terminal-Outputs als **ein zusammengefasster Block** (kein Schritt-für-Schritt), inkl.:
  1) `cd` ins Repo
  2) `pwd`
  3) `git rev-parse --show-toplevel`
  4) `git status -sb`
- Keine Guards, die die Session hart beenden (kein „exit 1“ ohne Kontext).

## Scope-Lock (standard)

- Default: nur `docs&#47;**`, `tests&#47;**`, `scripts&#47;obs&#47;**` (wenn Observability).
- Keine Änderungen an `src&#47;**` ohne explizite Anweisung.

## Evidence & Verifikation (operator-grade)

- Jede Änderung hat klare Verifikation:
  - Tests (pytest) oder verify scripts mit deterministischem Output.
  - Evidence-Dateien&#47;Artefakte timestamped, minimal, reproduzierbar.
- Bei HTTP&#47;Prom&#47;Grafana Checks: keine riskanten raw pipes (`curl | python json.load(stdin)` vermeiden).
  - Stattdessen: helper scripts mit `--out` file, retries, und fail-snippets (Header/Body).

## Links / Navigation (Grafana)

- Interne Dashboard-Links ausschließlich per `&#47;d&#47;<uid>` (keine title-based Links).
- UIDs stabil halten; Drilldowns dürfen nicht von URL-Encoding-Fallen abhängen.

## Merge/PR-Gates (allgemein)

- Kein Merge ohne erfüllte Gates (Checks grün, approvals, mergeStateStatus=CLEAN wenn relevant).
- Merge nur „genau 1×“ und guarded, wenn explizit angefordert.
