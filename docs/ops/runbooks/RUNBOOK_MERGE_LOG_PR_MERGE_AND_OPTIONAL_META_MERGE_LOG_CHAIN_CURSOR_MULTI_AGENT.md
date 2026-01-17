# RUNBOOK: Merge-Log PR mergen + optional Meta Merge-Log Chain (Cursor Multi-Agent)

## Zweck
Dieses Runbook beschreibt den standardisierten Ablauf, um **Merge-Log Pull Requests** (z.B. PR #733) sicher zu mergen: **CI Snapshot (no-watch)** → **Squash Merge** → **Post-Merge Verify (main)** → **Branch Cleanup**. Optional kann danach ein **Meta Merge-Log** (Merge-Log für den Merge-Log PR) erstellt werden, wenn eine lückenlose Dokumentationskette gewünscht ist.

## Scope
In-Scope:
- Merge von Merge-Log PRs gegen `main`
- Post-Merge Verifikation auf `main`
- Optional: Erstellung eines Meta Merge-Log PRs

Out-of-Scope:
- Code-Änderungen außerhalb Docs/Ops-Dokumentation
- Rewriting oder Kürzung bestehender Dokumente ("KEEP EVERYTHING")

## Rollen (Cursor Multi-Agent)
- ORCHESTRATOR: end-to-end Steuerung, Entscheidungspunkte
- POLICY_GUARDIAN: Token-Policy / Reference-Targets Safety (Backticks, Links)
- QA_VERIFIER: lokale Snapshot-Gates (no-watch), sanity checks
- EVIDENCE_SCRIBE: Evidence/Artefakte dokumentieren (SHAs, PR-IDs)
- DOCS_NAV_CURATOR: Runbook-README Navigation

## Vorbedingungen
- Repo vorhanden (typisch: /Users/frnkhrz/Peak_Trade)
- Working Tree clean
- `gh` authentifiziert
- Keine Shell-Continuation aktiv (z.B. `dquote>` oder `>`)

---

## Phase 0 — Pre-Flight (Repo + Continuation-Guard)
Ziel: Sicherstellen, dass wir im richtigen Repo sind und keine Terminal-Continuation aktiv ist.

Operator Notes:
- Falls ein Prompt wie `>` oder `dquote>` sichtbar ist: **Ctrl-C** drücken, dann neu starten.
- Danach ins Repo wechseln und Status prüfen.

Empfohlene Commands (Snapshot, kein Watch):
- `cd /Users/frnkhrz/Peak_Trade`
- `pwd`
- `git rev-parse --show-toplevel`
- `git status -sb`

---

## Phase 1 — CI Status Snapshot (no-watch) für PR <PR_NUM>
Ziel: Point-in-time Checks prüfen, ohne Polling/Watch.

Snapshot Commands:
- `gh pr view <PR_NUM> --json number,title,state,mergeable,headRefName,baseRefName,commits,url`
- `gh pr checks <PR_NUM>`

Merge-Kriterium:
- Alle **required** Checks: ✅ SUCCESS
- Keine ❌ FAILURES
- Pending nur, wenn explizit non-blocking (z.B. rein informational), ansonsten warten (manuell refreshen, kein Watch).

---

## Phase 2 — Merge Execution (Squash + delete branch)
Ziel: Merge durchführen, Branch serverseitig bereinigen.

Command (Standard):
- `gh pr merge <PR_NUM> --squash --delete-branch`

Erwartetes Ergebnis:
- PR wird gemerged (Squash)
- Branch wird gelöscht (remote), lokal später bereinigen falls nötig

Wenn Merge blockiert:
- Nicht "forcen". Zurück zu Phase 1 und Failure-Ursache beheben.

---

## Phase 3 — Post-Merge Verify (main)
Ziel: Verifizieren, dass `main` lokal mit `origin&#47;main` synchron ist und den Merge enthält.

Snapshot Commands:
- `git switch main`
- `git fetch origin`
- `git status -sb`
- `git log -1 --oneline`
- Optional: `git rev-parse HEAD`

Erfolgskriterien:
- `main...origin&#47;main` aligned (kein ahead/behind)
- HEAD entspricht dem erwarteten Merge Commit (oder enthält ihn in der Historie)
- Working tree clean

---

## Phase 4 — Optional: Meta Merge-Log Decision (Merge-Log für Merge-Log PR)
Ziel: Konsistent entscheiden, ob für den Merge-Log PR ein weiteres Merge-Log erstellt wird.

Entscheidungsmatrix:
- JA, wenn:
  - wir eine lückenlose "Merge-Log Chain" als Standard fahren, oder
  - der Merge-Log PR operative/policy-relevante Fixes enthält (z.B. Token-Policy Remediation), oder
  - es in der Ops-Policy explizit gefordert ist
- NEIN, wenn:
  - es reine Routine ist ohne neue Erkenntnisse, und
  - die Dokumentationskosten den Nutzen übersteigen

Wenn JA:
1) Branch erstellen (Beispiel-Pattern):
   - `git switch -c merge-log&#47;pr-<PR_NUM>-meta`
2) Merge-Log Datei anlegen:
   - `docs&#47;ops&#47;merge_logs&#47;PR_<PR_NUM>_MERGE_LOG.md`
3) Commit + Push + PR erstellen
4) Zurück zu Phase 1–3 für den Meta-PR

Wenn NEIN:
- Kurze Evidence-Notiz intern festhalten (z.B. im PR-Kommentar oder im bestehenden Merge-Log als Addendum), ohne neue Targets/Violations zu erzeugen.

---

## Phase 5 — Local Docs Gates Snapshot (no-watch)
Ziel: Vor Push/PR und nach Fixes schnelle Punktprüfung (kein Watch).

Guidance:
- Nutze den etablierten Snapshot-Runner (repo-intern). Keine Polling-Schleifen.
- Bei Token-Policy Violations:
  - Illustrative Branch/Range Tokens wie `main...origin&#47;main` ggf. als `main...origin&#47;main`
  - Illustrative `origin&#47;main` → `origin&#47;main`
  - URLs nach Möglichkeit nicht in Inline-Code; wenn notwendig, Token-Policy-sicher formatieren.

---

## Evidence & Artefakte (Minimum Set)
Für jeden Merge:
- PR Nummer + Titel
- Merge Commit SHA
- Merge-Zeitpunkt (lokal)
- Datei-Liste (Diff-Umfang grob)
- Gate-Snapshot (welche Checks required/grün)

---

## Failure Modes & Recovery
1) Required Check FAIL:
- Fix in Branch, push, neuer CI Snapshot (Phase 1), erst dann mergen.

2) Token-Policy FAIL (Docs):
- Identifiziere Backtick-Tokens mit "/"
- Klassifiziere: realer Pfad vs illustrativ
- Fix: illustrativ → &#47; (minimal-invasiv, Semantik unverändert)

3) Reference Targets FAIL:
- Prüfe, ob Links/Targets auf nicht existierende Dateien/Anker zeigen
- Beispiele nicht als Links formatieren; reine Textdarstellung bevorzugen

---

## Operator Quickstart (Minimal)
1) Phase 0 Pre-Flight
2) Phase 1 CI Snapshot: `gh pr checks <PR_NUM>`
3) Phase 2 Merge: `gh pr merge <PR_NUM> --squash --delete-branch`
4) Phase 3 Verify main
5) Optional Phase 4 Meta Merge-Log
6) Phase 5 Local Docs Gates Snapshot (bei Änderungen)

---

## See Also
- [RUNBOOK_DOCS_ONLY_PR_MERGE_AUTOMERGE_AND_MERGE_LOG_CHAIN_CURSOR_MULTI_AGENT.md](RUNBOOK_DOCS_ONLY_PR_MERGE_AUTOMERGE_AND_MERGE_LOG_CHAIN_CURSOR_MULTI_AGENT.md) — Docs-only PR merge workflow
- [RUNBOOK_POST_MERGE_VERIFY_MAIN_AND_DOCS_GATES_SNAPSHOT_CURSOR_MULTI_AGENT.md](RUNBOOK_POST_MERGE_VERIFY_MAIN_AND_DOCS_GATES_SNAPSHOT_CURSOR_MULTI_AGENT.md) — Post-merge verification standalone
- [RUNBOOK_DOCS_GATES_FIX_FORWARD_CI_TRIAGE_CURSOR_MULTI_AGENT.md](RUNBOOK_DOCS_GATES_FIX_FORWARD_CI_TRIAGE_CURSOR_MULTI_AGENT.md) — Fix-forward CI triage for gate failures

---

**Owner:** ops  
**Last Updated:** 2026-01-14  
**Target Use Case:** PR #733 (merge-log/pr-732-docs-only-pr-merge-runbook) + future merge-log PRs
