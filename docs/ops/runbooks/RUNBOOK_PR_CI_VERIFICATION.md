# RUNBOOK — PR / CI Verifikation (Feature-Branches)

**status:** active  
**last_updated:** 2026-04-12  
**purpose:** Truth-first Anleitung, welche **CI**-Läufe bei Pull Requests gegen `main` entstehen, wie man sie zuverlässig beobachtet und wie sie sich von manuellen Dispatch-Läufen unterscheiden — **ohne** Gate-Abschwächung und **ohne** Ausführungsautorität.

**docs_token:** `DOCS_TOKEN_RUNBOOK_PR_CI_VERIFICATION`

## Non-Goals

- Keine Änderung an Workflows, Branch-Protection oder Required Checks.
- Keine Empfehlung, Checks zu umgehen oder Merge-Regeln zu lockern.

## Kanonische Quelle

- Workflow **`CI`**: [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml) (Repository-Wurzel).

## `on:`-Ereignisse (Kurzüberblick)

| Mechanismus | Wann es feuert (laut Workflow) |
|-------------|--------------------------------|
| **`push`** | Nur für Branches **`main`** und **`master`**. Ein **Push auf einen Feature-Branch** löst **diesen** `push`-Pfad **nicht** aus. |
| **`pull_request`** | PRs gegen **`main`/`master`** (`opened`, `synchronize`, `reopened`, `ready_for_review`). Aktualisiert den PR-Head (z. B. nach weiterem Commit) → **`synchronize`**. |
| **`workflow_dispatch`** | Manuell in der GitHub-Actions-UI oder per `gh workflow run …`; optional Input **`force_matrix`**. **Kein** Ersatz für ein `pull_request`-Ereignis — anderes Event, anderer Kontext in der Run-Liste. |
| **`merge_group`** / **`schedule`** | Separate Pfade; für typische Feature-PR-Verifikation sekundär. |

**Truth-first:** „Push auf Feature-Branch startet **nicht** automatisch den `on.push`-CI“ — korrekt für dieses Repo. Für PRs gegen `main` ist **`pull_request`** der regelmäßige Pfad.

## Welchen Run beobachten?

- **`gh pr checks <PR> --watch`** zeigt oft nur einen **Teil** der Checks und kann **früh** enden, wenn nicht alle GitHub-Apps/Workflows in derselben Ansicht hängen.
- Für den **vollständigen** Workflow **`CI`** mit Job-Matrix (**`tests (3.9)`**, **`tests (3.11)`**, **`strategy-smoke`**, …): Run-ID ermitteln und **`gh run watch <RUN_ID>`** verwenden, z. B.  
  `gh run list --branch <feature-branch> --json databaseId,workflowName,event --limit 20`  
  und Eintrag mit **`workflowName` == `CI`** und **`event` == `pull_request`** wählen.

## `strategy-smoke` und Reihenfolge

- Im Workflow ist der Job **`strategy-smoke`** mit **`needs: [changes, tests]`** definiert — er startet **nach** den **`tests`**, Matrix inkl. **`tests (3.11)`**.  
- Ein Check-Run **`strategy-smoke`** kann auf dem Commit **fehlen**, solange **`tests (3.11)`** (oder die Matrix) noch **in Bearbeitung** ist — das ist **erwartetes** Verhalten, kein „fehlender“ Required-Check-Name durch Umbenennung.

## Required Status Checks (Namen)

- Branch-Protection auf `main` verlangt **exakte** Kontext-Namen (z. B. **`tests (3.11)`**, **`strategy-smoke`**, **`Lint Gate`**, …).  
- Abweichungen zwischen **Workflow-Job-`name:`** und Protection-**`context`** blockieren Merges — bei Umbenennungen immer **Workflow** und **Protection** gemeinsam prüfen (siehe auch `scripts/ops/check_required_ci_contexts_present.sh` im **`CI`**-Job **`ci-required-contexts-contract`**).

## Leerer Commit

- **`git commit --allow-empty`** + **`git push`** auf den Feature-Branch erzeugt einen neuen Commit und triggert bei offenem PR typischerweise **`pull_request`** (**`synchronize`**).  
- Er **ersetzt** keinen **`workflow_dispatch`** und startet **keinen** zusätzlichen `push`-CI auf dem Feature-Branch (siehe oben).

## Ops Cockpit (Lesekontext)

- Session-, Stale- und Run-Zustände im Cockpit sind **read-only** und an Payload-Keys gebunden — siehe [`OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`](../specs/OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md) (Abschnitt Session / Run / Stale).

## Related

- [`CI.md`](../CI.md) — CI-Überblick und Branch-Protection-Kontext.
- [`ci_required_checks_matrix_naming_contract.md`](../ci_required_checks_matrix_naming_contract.md) — Namenskonventionen für Required Checks.
