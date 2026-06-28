# Peak Trade — Runbook Execution Governance v1

---
docs_token: DOCS_TOKEN_PEAK_TRADE_RUNBOOK_EXECUTION_GOVERNANCE_V1
STATUS: CANONICAL_EXECUTION_GOVERNANCE
VERSION: 1.0
scope: docs-only, strategic-execution-control, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Verbindliche Steuerungsnorm:** Dieses Dokument legt fest, wie das kanonische Runbook v2.6 die strategische Entwicklungsrichtung von Peak_Trade bestimmt. Es erzeugt **keine** Runtime-, Deployment-, Order- oder Live-Authority.

## Strategische Single Source of Truth

Das kanonische Runbook ist die **einzige verbindliche strategische SSOT** für:

- Zielarchitektur
- Phasenfolge
- kritischen Umsetzungspfad
- Authority-Grenzen
- Safety-Grenzen
- Single-SSOT-Regeln
- Exit-Kriterien
- stufenweise Freischaltung bis zum vollautonomen Futures-System

**Kanonischer Owner:** [`docs/architecture/PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md`](../architecture/PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md)

Die strategische Richtung darf **nicht** nach jedem Merge, PR, Evidence-Slice, CI-Fix, Manifest-Repair oder lokalen Gap neu gerankt, neu priorisiert oder neu verhandelt werden.

## Progress-Registry (Ist-Stand, nicht Authority)

Der Repo-Ist-Stand wird in der Progress-Registry geführt:

**Kanonischer Owner:** [`docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md`](PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md)

Die Progress-Registry:

- erzeugt **keinerlei Authority**,
- setzt **keine** Runtime-, Deployment-, Order- oder Live-Freigabe,
- verbindet Runbook-Soll mit gemergtem Repo-Ist.

## Systemweite Rankings — Ausnahme, nicht Standard

`SYSTEMWIDE_RANKING_DEFAULT_ALLOWED=false`

Systemweite Rankings sind **kein Standardprozess**. Sie dürfen ausschließlich vorgeschlagen oder ausgeführt werden, wenn mindestens **eine** dieser Bedingungen nachweislich erfüllt ist:

1. Das aktuelle Major Gap Package ist vollständig abgeschlossen.
2. Der nächste Runbook-Schritt besitzt trotz Reuse-before-new keinen bestimmbaren kanonischen Owner.
3. Neue Änderungen auf `origin/main` haben den geplanten Schritt semantisch obsolet gemacht.
4. Der geplante Schritt würde eine Safety-, Authority- oder Single-SSOT-Grenze verletzen.
5. Das Runbook enthält für den konkreten Übergang einen nachgewiesenen Widerspruch oder eine echte Lücke.
6. Ein vollständiger Runbook-Meilenstein ist abgeschlossen und mehrere unabhängige nächste Major Packages sind gleichzeitig zulässig.
7. Eine echte Ressourcenpriorisierung zwischen unabhängigen Runbook-Tracks ist erforderlich.
8. Der Operator erteilt ausdrücklich einen GO für ein neues systemweites Ranking.

**Nicht ausreichende Gründe:** normaler PR-Merge, Ende eines Evidence-Slices, CI-Fix, Hard-Retrigger, Manifest-Repair, Closeout, lokaler Binding-Gap, neuer Cursor-Chat, sichtbarer kleinerer Gap, Möglichkeit eines leichteren PRs.

## Keine strategische Rückfrage (Standardfall)

Solange keine Ausnahmebedingung erfüllt ist, darf Cursor **nicht** fragen:

- ob ein systemweites Ranking durchgeführt werden soll,
- welches Major Gap als Nächstes bearbeitet werden soll,
- ob das Runbook weiterverfolgt werden soll,
- ob ein anderer Track priorisiert werden soll,
- ob der aktuelle Package-Schritt übersprungen werden soll.

Stattdessen wird deterministisch **genau ein** nächster kanonischer Schritt aus Runbook, Progress-Registry und aktiver Package-Sequenz bestimmt.

## Package-Sequenzierung zwischen Major-Gap-Schritten

Solange ein aktives Major Gap Package existiert und sein nächster sequenzieller Schritt technisch zulässig ist, die Runbook-Richtung einhält, nicht obsolet ist, keine Safety-/Authority-/Single-SSOT-Grenze verletzt und einen bestimmbaren kanonischen Owner besitzt, wird **genau dieser** nächste Package-Schritt vorbereitet und nach separatem Operator-GO umgesetzt.

**Zulässig zwischen Package-Schritten:**

- Merge-Closeout
- Baseline-Verifikation
- Reuse-before-new
- begrenzter Admissibility-/Readiness-Check
- Konfliktprüfung gegen aktuellen `origin/main`-Stand
- separater Operator-GO
- Implementierung
- lokale Tests
- Durable Evidence
- genau ein PR
- Required Checks
- Squash-Merge
- Closeout
- Progress-Registry-Aktualisierung

**Nicht zulässig zwischen normalen Package-Schritten:**

- neues systemweites Ranking
- neue strategische Kandidatenliste
- erneute Verhandlung der Zielrichtung
- Wechsel zu einem anderem Major Gap
- Vorziehen eines leichteren lokalen Gaps
- Überspringen eines sequenziellen Package-Schritts
- Vorziehen einer späteren Runbook-Phase
- neues Parallel-SSOT
- neue Architektur außerhalb des Runbooks

## Deterministischer Next-Step-Algorithmus

1. Kanonisches Runbook lesen.
2. Aktive Progress-Registry lesen.
3. Aktives Major Gap Package lesen.
4. Ersten noch nicht `COMPLETE` markierten sequenziellen Package-Schritt bestimmen.
5. Abhängigkeiten gegen aktuellen `origin/main`-Stand prüfen.
6. Reuse-before-new durchführen.
7. Begrenzten Readiness-/Admissibility-Check ausführen.
8. Genau einen Implementation-GO für diesen Schritt formulieren.
9. Keine alternativen Major Gaps vorschlagen.

## PR-Bundle-Regel

Vor jedem neuen Implementierungsslice prüfen, ob ein kleines logisch kohärentes PR-Bundle sicherer und effizienter ist.

Bündeln nur bei identischer Semantik, identischem kanonischem Owner, identischer Authority-Stufe, gemeinsamer Testowner-Struktur, bounded Diff, guter Reviewbarkeit, vorzugsweise FOCUSED- oder PR_BOUNDED_FULL-CI, keiner Consumer-Mutation und keiner Authority-Eskalation.

Die fünf Schritte des aktuellen Major Gap Packages bleiben grundsätzlich **SINGLE_PR**. Keine eigenmächtige Zusammenlegung mehrerer Package-Schritte.

## Evidence-Drift-Regel (PR #4629)

Für PR #4629 gilt dokumentiert:

- Implementation-Bundle: historischer Drift in `00_VERDICT.txt`, `MANIFEST_VERIFY_RC=1`
- Check-Recovery-Bundle: kein `MANIFEST.sha256`
- Closeout-Bundle: `MANIFEST_VERIFY_RC=0`

Diese historischen Befunde dürfen nicht überschrieben, stillschweigend neu gehasht, als RC=0 umetikettiert oder aus der Progress-Historie entfernt werden. Sie blockieren nicht die strategische Runbook-Sequenz, sofern Merge, Patch-Containment, Required Checks und das gültige Closeout-Bundle den implementierten Repo-Stand belastbar nachweisen.

## Safety- und Authority-Grenze

Evidence ist nicht Authority. Ein höheres Evidence Level erzeugt keine implizite Capability.

Kein Offline-Evidence-Schritt darf implizit erzeugen: Candidate Selection, Winner Selection, Candidate Acceptance, PromotionCandidate, Promotion Policy Execution, ConfigPatch-Erzeugung (sofern nicht der konkrete separat autorisierte Schritt dies erfordert), Consumer-Mutation, Runtime Eligibility, Deployment, Activation, Scheduler, Order Intent, Execution Permission, Order Submission oder Live Authority.

Jeder Implementierungsschritt benötigt weiterhin **separates Operator-GO** (`SEPARATE_GO_REQUIRED=true`).
