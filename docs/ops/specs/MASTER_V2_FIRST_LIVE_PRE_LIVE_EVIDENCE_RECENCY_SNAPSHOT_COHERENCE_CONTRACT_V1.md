# MASTER V2 - First Live Pre-Live Evidence Recency Snapshot Coherence Contract v1 (Docs-Only, Non-Authorizing)

status: ACTIVE
last_updated: 2026-04-20
owner: Peak_Trade
intent: Verbindlicher docs-only Mindestvertrag fuer eine kandidatenspezifische, fail-closed und evidence-bound Recency-Snapshot-Kohaerenzlage als Decision-Input-Surface fuer operative Pre-Live-Readiness-Pruefung
docs_token: DOCS_TOKEN_MASTER_V2_FIRST_LIVE_PRE_LIVE_EVIDENCE_RECENCY_SNAPSHOT_COHERENCE_CONTRACT_V1

## 1) Titel + Status &#47; Intent

Diese Spezifikation materialisiert genau eine additive Single-Topic-Slice fuer operative First-Live-Pre-Live-Readiness: die kohaerente, kandidatenspezifische Recency-Snapshot-Pruefung bestehender Evidence-Pointer.

Verbindliche Boundary:

- docs-only
- non-authorizing
- fail-closed
- safety-first
- evidence-bound

Diese Spezifikation autorisiert nichts, schliesst kein Gate und erteilt keine Live-Freischaltung.

## 2) Zweck &#47; Scope &#47; Nicht-Ziele

Zweck:

- eine reproduzierbare Recency-Snapshot-Disziplin fuer vorhandene candidate-scoped Evidence-Pointer bereitstellen
- Recency-Unklarheit und Quellenwiderspruch konservativ als blocker behandeln
- einen klaren Decision-Input-Surface fuer nachgelagerte externe Entscheidungsstellen bereitstellen, ohne lokale Entscheidungsbefugnis zu erweitern

Scope:

- genau ein Recency-Snapshot-Kohaerenzvertrag fuer `L1` bis `L5` in der Pre-Live-Lage
- Required Inputs, Preconditions, Adjudication-Regeln und Review-Pack-Mindestinhalt
- explizite stop &#47; reject &#47; escalate Regeln fuer Recency- und Kollisionstatbestaende

Nicht-Ziele:

- keine Approval-, Autorisierungs-, Gate-Pass-, Promotion- oder Go-Live-Ableitung
- keine Runtime-, Config-, Workflow-, Script-, Test- oder Code-Aenderung
- keine Evidenzerzeugung, keine Evidenzmutation, keine neue Prozessfamilie
- keine Umdeutung von `Verified` in Autorisierung

## 3) Begriffs- und Boundary-Definitionen

- `recency_snapshot`: strikt pointer-basierte Momentaufnahme der sichtbaren Zeitnaehe je required Evidence-Klasse fuer genau eine `candidate_id`.
- `snapshot_coherence`: Zustand, in dem Pointer-Herkunft, Zeitnaehe und Quellenbezug ohne unaufgeloeste Widersprueche nachvollziehbar sind.
- `decision_input_surface`: nicht-autorisierende, traceable Uebergabeflaeche fuer externe Entscheidungsinstanzen.
- `recency_state`: zulaessige Werte sind `fresh`, `stale`, `unknown`; `unknown` ist nie neutral.
- `coherence_break`: jede Lage mit `Missing`, `Partial`, `Unknown`, `Contradiction` oder `Stale&#47;Unknown recency`.

Boundary-Regel:

- lokale Snapshot-Kohaerenz ist nur ein Lese- und Nachweiszustand; sie ist nie eine Freigabeaussage.

## 4) Inputs &#47; Preconditions &#47; Required Evidence Pointers

Required Inputs (bestehende kanonische Quellen, pointer-basiert):

1. [MASTER_V2_FIRST_LIVE_PRE_LIVE_EVIDENCE_REQUIREMENT_CONTRACT_V1.md](MASTER_V2_FIRST_LIVE_PRE_LIVE_EVIDENCE_REQUIREMENT_CONTRACT_V1.md)
2. [MASTER_V2_FIRST_LIVE_PRE_LIVE_DRY_RUN_ACCEPTANCE_CONTRACT_V1.md](MASTER_V2_FIRST_LIVE_PRE_LIVE_DRY_RUN_ACCEPTANCE_CONTRACT_V1.md)
3. [MASTER_V2_FIRST_LIVE_CANDIDATE_EVIDENCE_BUNDLE_LEDGER_V1.md](MASTER_V2_FIRST_LIVE_CANDIDATE_EVIDENCE_BUNDLE_LEDGER_V1.md)
4. [MASTER_V2_FIRST_LIVE_CROSS_GATE_EVIDENCE_BUNDLE_INDEX_V1.md](MASTER_V2_FIRST_LIVE_CROSS_GATE_EVIDENCE_BUNDLE_INDEX_V1.md)
5. [MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md)
6. [MASTER_V2_FIRST_LIVE_OPERATIONAL_SIGNOFF_PROCEDURE_V1.md](MASTER_V2_FIRST_LIVE_OPERATIONAL_SIGNOFF_PROCEDURE_V1.md)
7. [MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md](MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md)
8. [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md)

Preconditions:

- `candidate_id` ist ueber alle Inputs stabil und eindeutig.
- jede Required-Pointer-Klasse aus der relevanten Intake-Lage ist entweder explizit vorhanden oder explizit als blocker markiert.
- Zeitnaehe bleibt pointer-sichtbar; keine implizite Normalisierung.
- authority boundary bleibt extern; lokal keine Entscheidungsausdehnung.

Required Evidence Pointer Surface (pro Snapshot-Zeile):

- `candidate_id`
- `level` (`L1` bis `L5`)
- `pointer_class`
- `source_pointer`
- `observed_recency_state` (`fresh`, `stale`, `unknown`)
- `coherence_flag` (`coherent`, `break`)
- `ambiguity_reason` (falls `break`)

## 5) Operativer Kernvertrag: Recency Snapshot Coherence Matrix + Adjudication + Review-Pack

### 5.1 Matrix (L1 bis L5)

| level | required recency snapshot focus | coherence minimum | decision-input use boundary |
|---|---|---|---|
| `L1` | dry-validation und execution-nahe Pointer-Zeitnaehe | alle required Pointer-Klassen recency-sichtbar und ohne Widerspruch | nur intake-bezogene Lageklarheit, keine Abschlussaussage |
| `L2` | verdict-nahe Pointer-Zeitnaehe und Lesekonsistenz | keine unaufgeloeste Divergenz zwischen Verdict-Sources | nur konservative Lesehilfe fuer naechsten Review-Schritt |
| `L3` | prerequisite- und entry-boundary-nahe Recency-Lage | prerequisite-Pointer zeitlich nachvollziehbar oder blocker-markiert | nur boundary-klarer Input, keine Entry-Freigabe |
| `L4` | candidate-flow-nahe Snapshot-Konsistenz | session-flow-Pointer und Zeitnaehe sind konfliktfrei oder explizit offen | nur flow-bezogene Risiko-Sicht, keine Betriebsfreigabe |
| `L5` | incident- und safe-stop-nahe Recency-Lage | incident-relevante Pointer mit klarer Zeitnaehe oder fail-closed blocker | nur Eskalations-Input, keine Entwarnungsaussage |

### 5.2 Adjudication-Regeln

- `coherent`: nur wenn alle required Pointer-Klassen recency-sichtbar sind und keine Quellenkollision offen bleibt.
- `break`: sobald eine required Klasse `Missing`, `Partial`, `Unknown`, `Contradiction` oder `Stale&#47;Unknown recency` zeigt.
- keine lokale Priorisierung konkurrierender Quellen ohne kanonischen Anker.
- keine aufwaertsgerichtete Umdeutung durch Nachbarstaerke.

### 5.3 Review-Pack Mindestinhalt

Ein gueltiger Review-Pack fuer diese Slice enthaelt mindestens:

1. Snapshot-Tabelle mit allen required Pointer-Klassen je `L1` bis `L5`
2. explizite `coherence_break`-Liste mit Grundklasse pro Treffer
3. konservative `decision_input_surface`-Notiz mit non-authorizing Sprache
4. pointer-trace auf verwendete kanonische Quellen

## 6) Fail-Closed Stop &#47; Reject &#47; Escalate-Regeln

Bindend fuer jede Snapshot-Zeile und fuer die Gesamtlage:

- `Missing` -> `reject`, sofort `stop &#47; escalate`
- `Partial` -> `reject`, keine Auffuellung per Annahme, `stop &#47; escalate`
- `Unknown` -> `reject`, keine lokale Aufloesung, `stop &#47; escalate`
- `Contradiction` -> `reject`, keine Mittelung, `stop &#47; escalate`
- `Stale&#47;Unknown recency` -> `reject`, nicht als aktuell interpretieren, `stop &#47; escalate`

Gesamtregel:

- ein einzelner `coherence_break` reicht fuer fail-closed Gesamtstatus.
- lokale Bearbeitung endet an der Eskalationsgrenze; keine implizite Gate-Closure.

Escalation-Payload-Mindestfelder:

- `candidate_id`
- `level`
- `pointer_class`
- `source_pointer`
- `ambiguity_reason`
- `requested_external_adjudication_context`

## 7) Traceability &#47; Cross-References auf bestehende repo-kanonische Ziele

Primäre Referenzen:

- [MASTER_V2_FIRST_LIVE_PRE_LIVE_EVIDENCE_REQUIREMENT_CONTRACT_V1.md](MASTER_V2_FIRST_LIVE_PRE_LIVE_EVIDENCE_REQUIREMENT_CONTRACT_V1.md)
- [MASTER_V2_FIRST_LIVE_PRE_LIVE_DRY_RUN_ACCEPTANCE_CONTRACT_V1.md](MASTER_V2_FIRST_LIVE_PRE_LIVE_DRY_RUN_ACCEPTANCE_CONTRACT_V1.md)
- [MASTER_V2_FIRST_LIVE_OPERATIONAL_SIGNOFF_PROCEDURE_V1.md](MASTER_V2_FIRST_LIVE_OPERATIONAL_SIGNOFF_PROCEDURE_V1.md)
- [MASTER_V2_FIRST_LIVE_CANDIDATE_EVIDENCE_BUNDLE_LEDGER_V1.md](MASTER_V2_FIRST_LIVE_CANDIDATE_EVIDENCE_BUNDLE_LEDGER_V1.md)
- [MASTER_V2_FIRST_LIVE_CROSS_GATE_EVIDENCE_BUNDLE_INDEX_V1.md](MASTER_V2_FIRST_LIVE_CROSS_GATE_EVIDENCE_BUNDLE_INDEX_V1.md)
- [MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md)
- [MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md](MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md)
- [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md)
- [MASTER_V2_VOCAB_BOUNDARY_LOCK_V1.md](MASTER_V2_VOCAB_BOUNDARY_LOCK_V1.md)
- [MASTER_V2_FIRST_LIVE_AUTHORITY_HANDOFF_PACKET_CONTRACT_V1.md](MASTER_V2_FIRST_LIVE_AUTHORITY_HANDOFF_PACKET_CONTRACT_V1.md)

Traceability-Regeln:

- jede Aussage im Snapshot muss auf mindestens einen Source-Pointer rueckfuehrbar sein.
- jede offene Ambiguitaet bleibt explizit offen und wird nicht sprachlich geglaettet.
- Pointer-Praesenz erhoeht nie die Entscheidungskompetenz.

## 8) Abschluss: Klare Non-Authorizing Boundary

Dieser Contract ist eine operative, pruefbare Recency-Snapshot-Kohaerenz-Slice fuer Pre-Live-Readiness und ausschliesslich Decision-Input-Surface.

Er ist keine Freigabe, kein Gate-Pass, keine Promotion und keine Go-Live-Erlaubnis; finale Entscheidungshoheit bleibt ausserhalb dieses Dokuments.
