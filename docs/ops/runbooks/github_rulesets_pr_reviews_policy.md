# GitHub Rulesets: PR-Pflicht vs. Approving Reviews (Policy & Runbook)

## Zweck
Dieses Runbook definiert und dokumentiert die Policy-Optionen für GitHub-Branch-Schutz (Rulesets / Branch Protection) im Peak_Trade Repo, insbesondere:

- **PR-Pflicht** (Merge nur über Pull Requests, keine Direct Pushes)
- **Approving Reviews** (mindestens N Approvals erforderlich)

Zusätzlich beschreibt es typische Symptome (z.B. `mergeable: UNKNOWN`) und eine robuste Verifikation.

## Geltungsbereich
- Repository: `rauterfrank-ui&#47;Peak_Trade`
- Branch: `main` (analog für weitere geschützte Branches)
- Mechanismen:
  - **Rulesets** (modern)
  - **Branch protection rules** (legacy)

## Begriffe
- **PR-Pflicht**: Merges nach `main` nur via Pull Request erlaubt.
- **Approving Review**: Ein explizites „Approve" durch Reviewer; kann mit Codeowners gekoppelt sein.
- **Required approving review count**: Minimale Anzahl Approvals.

## Empfohlene Standard-Policy (Peak_Trade)
Peak_Trade ist Safety-/Governance-sensitiv (Execution/Risk/Live). Daher gilt als Default:

- PR-Pflicht: **EIN**
- Approving Reviews: **EIN**, Count **≥ 1**
- Für hochkritische Pfade (z.B. Execution Layer) optional zusätzlich:
  - Codeowners + Require Codeowner Reviews
  - Dismiss stale approvals bei neuen Commits

Hinweis: Wenn du allein arbeitest und ein Review-Gate organisatorisch nicht sinnvoll ist, kann temporär gelten:
- PR-Pflicht: **EIN**
- Approving Reviews: **AUS** (oder effektiv 0)

Das ist **nicht** „paradox", sondern drückt aus: „PR-Flow erzwingen, aber keine Approvals erzwingen".

## Konfigurations-Optionen (Entscheidungsmatrix)

| Zielbild | PR-Pflicht | Approving Reviews | Count | Geeignet für |
|---|---:|---:|---:|---|
| Solo-Dev, PR-Flow erzwingen, keine Review-Hürde | EIN | AUS | 0 | Schnelle Iteration, dennoch PR-Disziplin |
| Team-Standard | EIN | EIN | 1 | Minimaler Governance-Gate |
| Sensitiv (Execution/Risk/Live) | EIN | EIN | 1–2 | Safety-First, Fehlerkosten hoch |
| Streng (Release/Prod) | EIN | EIN | 2+ | Höchste Governance-Anforderungen |

## Symptom: `mergeable&#47;mergeStateStatus = UNKNOWN`
`UNKNOWN` kann auftreten, obwohl `statusCheckRollup` bereits `SUCCESS` ist. Das ist häufig ein GitHub-Compute-/Timing-Effekt und nicht automatisch ein Blocker.

**Praktische Regel:**
- Wenn **alle Required Status Checks SUCCESS** sind und keine weiteren Ruleset-Bedingungen fehlen, kann Merge trotzdem möglich sein.
- Ein „Merge-Versuch" (UI oder `gh pr merge`) liefert die endgültige Wahrheit, ob blockiert ist.

## Operator Quickflow bei `mergeable: UNKNOWN`

1. Prüfe, ob alle **Required Status Checks** SUCCESS sind (PR UI → Checks).
2. Prüfe Ruleset-Merge-Anforderungen (PR UI → „Merge requirements").
3. Snapshot via CLI (ohne Watch): `gh pr view <N> --json mergeable,mergeStateStatus,reviewDecision,statusCheckRollup`
4. Wenn Rollup SUCCESS und Requirements erfüllt wirken: Merge-Versuch per `gh pr merge <N> --squash --delete-branch`
5. Falls blockiert: Fehlermeldung ist Source-of-Truth (Review/Queue/Up-to-date/Required Context).
6. Nur bei wiederkehrender Blockade: Ruleset/Branch-Policy korrigieren (Reviews OFF oder Count ≥ 1).

## Änderung in GitHub UI: Klickpfade

### A) Rulesets (modern, bevorzugt)
1. Repo → **Settings**
2. **Rules**
3. **Rulesets**
4. Ruleset auswählen, das `main` matcht (z.B. Target/Pattern)
5. **Edit**
6. Bereich **Pull request** / **Pull request requirements**
7. Setzen je nach Zielbild:
   - **Option A (keine Reviews):**
     - „Require pull request reviews before merging": **OFF**
   - **Option B (Reviews gewollt):**
     - „Require pull request reviews before merging": **ON**
     - „Required approving review count": **1** (oder höher)
8. **Save**

### B) Branch protection rules (legacy)
1. Repo → **Settings**
2. **Branches**
3. Unter „Branch protection rules" Regel für `main` → **Edit**
4. Bereich „Require a pull request before merging":
   - aktivieren/deaktivieren je nach Policy
5. Bereich „Require approvals" / „Required approving reviews":
   - Count auf **1+** setzen oder Requirement deaktivieren
6. **Save changes**

## Verifikation (ohne Watch)
Minimal:
- PR-Seite öffnen → „Checks" und „Merge requirements" ansehen.
- Sicherstellen, dass alle **required** Status Checks „Success" sind.

Optional per CLI (Snapshot, ohne `--watch`):
- `gh pr view <N> --json mergeable,mergeStateStatus,reviewDecision,statusCheckRollup`
- `gh api graphql` Snapshot, wenn Ruleset/Required Contexts unklar sind.

## Pitfalls / Best Practices
- Required Check Contexts müssen **immer materialisieren** (auch docs-only) → Stub-/Fast-Success Steps statt Job wegzu-`if`en.
- Concurrency PR-isoliert halten, um Cross-Cancel zu vermeiden.
- „Approvals required = ON, count=0" kann gewollt sein (PR-Flow ohne Approvals), ist aber für Operatoren oft missverständlich → Policy explizit dokumentieren (diese Datei).

## Peak_Trade Bezug
- CI-Härtung: Required Context Materialisierung (z.B. `tests (3.11)`, `strategy-smoke`) plus fail-open Change Detection.
- Referenz: PR #512 (CI required check robustness).

## Historie
- **2025-01-03**: Initial Policy & Runbook nach PR #512 CI-Härtung (fail-open changes + PR concurrency).
- **2025-01-03**: Added Operator Quickflow bei `mergeable: UNKNOWN`.
