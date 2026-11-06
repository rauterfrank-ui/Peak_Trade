# GVEF und Beziehungen zwischen den betrachteten Bereichen — 04.11.2026

Quellenpin `3a01199438acfe9050e5f3a6a1eafd032b6abaa5`. Aufnahme eines belegten
Untersuchungsergebnisses in den bestehenden Repo-Abgleich, kein neuer Systementwurf.
Master Runbook bleibt maßgeblich. GVEF ist bereits implementiert und wird ausdrücklich
als bestehende bereichsübergreifende Vergleichsfähigkeit berücksichtigt. Keine neue
Runtime-Kopplung, Taxonomie oder produktive Zuständigkeit aus diesem Befund.

## Aktuelle Owner-Präzisierungen und Scope-Grenze

Full Core im N5-Kontext bezeichnet nach aktueller User-Klarstellung **alle fünf Slots**.
Ein historischer Full-Core-Execution-Autonomy-Pfad ist getrennt davon zu untersuchen.
Slotumfang, autonome Ablaufsteuerung und tatsächlicher Betrieb sind verschiedene
Aussagen. Das Etikett „vollautomatisches Universe“ wird keinem Owner still zugeordnet.
Der N5-Vertrag benennt fünf isolierte N1-Lanes; der gelesene Pair-Map-Consumer bewahrt
je Lane Instrument-/Slot-/State-Root-Identität und endet vor dem Trading-Aufruf.

Die Scope-Berechnung gilt nach User-Kontext als bereits implementierter, funktionierender
Bestand. Hier wurden weder Formel noch Parameter, Policy, Zuständigkeit oder Consumer
umgebaut. Vier vorhandene Scope-/Geometriequellen sind gegen den Pin bytegleich
geprüft. Das ist Erhaltung, **kein neuer Funktionsnachweis**. Historische IU-Namen
lösen keine erneute Scope-Implementierung aus.

## Belegte Beziehungen

- **Gemeinsame GVEF-Sprache:** Kontext, Replay-Trace, Baseline-/Candidate-Ergebnis,
  geschützte Semantik, Delta, Boundary-Evidence und Registry-Referenz werden durch
  bestehende gemeinsame Verträge transportiert. Fünf konkrete Evaluatoren existieren:
  Productive Trading Path, Ranking Universe, Self-Learning, Optimization, Market Intelligence.
- **Fachliche Übergaben:** Ranking-Kontext, Cap23-Auswahl, Cap24-Binding und Trading
  bleiben getrennte Rollen. BoundInstrument ist der bestehende Ingress, kein zweiter
  Auswahlentscheid. Der SSF-Vertrag wird nicht mit isoliertem MF-Egress gleichgesetzt.
- **Beobachtungsbeziehung:** Ranking und simulierte Execution besitzen die konkreten
  DDO-Hooks selection.ranking und execution.simulated_outcome. Der Wrapper ruft den
  Producer auf und gibt dessen Ergebnis zurück; Capture hängt von aktiver Bindung ab.
  Ablage, späterer Outcome und numerische Lernwirkung sind weitere Schritte.
- **MI-/Research-Beziehung:** Der vorhandene Offline-Orchestrator komponiert MI-Lernexport
  und Optimization-Intake; MI-angereicherte M4-Komposition ist ausdrücklich bedingt.
  Ein Forecast-Record ist kein Modelltraining und ein ACK kein produktiver Apply.
- **Semantischer Vergleich:** Der bestehende Level3-Semantic-Diff-Owner unterscheidet
  deklarierte/strukturelle/Config-/Trace-/Replay-/Boundary-/Risk-/Intent-Unterschiede.
  Passende Baseline-/Candidate-Attestierungen und echte Quellensemantik bleiben nötig.

[Einzelrelationen mit Consumerpfaden und Grenzen](relations.json),
[aktuelle Quellen mit SHA256](repository_source_bindings.json).

## GVEF: was konkret geprüft ist

104 ausgewählte vorhandene Tests bestehen: BWP3-Domänen, BWP4/5/6-Domänen und BWP9.
Kein neuer Testowner und keine Änderung an bestehendem Python-Code.
Zusätzlich wurden die fünf tatsächlichen Domänen-Evaluatoren jeweils durch den
vorhandenen GenericRunner geführt: kontrollierte bestehende Fixture-Traces,
deterministische Testdoubles für Replay/Gates/Comparator/Delta/Evidence-Build und
In-Memory-Registry. Alle fünf erreichen REGISTERED mit EvidenceBundle. Der Default-
Promotion-Adapter liefert keinen Promotion-Envelope.

Ein kontrollierter Ranking-Trace mit unzulässigem Cap23-Anspruch scheitert im
vorhandenen integrierten Runner mit AUTHORITY_FAILURE und WHOLE_SYSTEM_REPROOF.
Diese Fan-out-Klasse bezeichnet erforderliche Nachprüfung; sie führt diese nicht
selbst aus. Das ist konkreter Mechanismennachweis, keine neue natürliche Marktstudie.
[Test-XML](tests.xml), [vollständige kontrollierte Ergebnisse](mechanism_probes.json),
[reproduzierbare Probe als erhaltene Textquelle](mechanism_probe.py.txt).
Reproduktion aus der Repo-Wurzel: kanonischen Launcher aufrufen und die Probe auf stdin
zuführen. Die erhaltene Textdatei ist Evidence, kein neuer ausführbarer Produktowner.

## Grenzen, die die Aufnahme ausdrücklich nicht überschreitet

Der GenericRunner erhält **einen** Evaluator pro Aufruf. Auch whole_system_runner
setzt zunächst nur die integrierte Fail-closed-Reproof-Klasse. Daraus folgt weder eine
automatisch ausgeführte Fünf-Domänen-Kette noch die Prüfung sämtlicher N5-Slots.

Der gelesene PTP-Evaluator prüft gelieferte Stage-Traces bis PRE_EXTERNAL und verwendet
Owner-Referenzen als Strings. Er ruft nicht allein dadurch reale Markt-, Scope-,
Trading-, Venue- oder Fill-Owner auf. Der MI-Evaluator verarbeitet angelieferte
Context-Bundles; Herkunfts-/Causality-/Freshness-Felder ersetzen keine unabhängig
beobachtete Datenquelle. Geschützte Digests stammen aus dem EvaluationContext, nicht
zwingend aus erneut ausgeführter Produktlogik.

Default-Corpus-/Promotion-Gates können Pass-through-Adapter sein. Die konkrete
GvefEvidenceRegistry ist in-memory; ihre Referenz belegt keinen dauerhaft geschriebenen
Evidence-Store. REGISTERED oder evidence_complete allein ist keine universelle
Semantik-, Profitabilitäts-, Deployment- oder Promotion-Freigabe.

Der bisherige numerische Forschung→Meta→Search-Adapter ist ein anderer expliziter
Offline-Pfad. Für eine tatsächliche GVEF-Anbindung müssen Experiment-/Run-/Lane-/
Instrumentidentität, Datenfenster, Kennzahlen-Einheiten, Baseline/Candidate, tatsächliche
Trace-Producer und Consumerwirkung passen. Diese Verbindung wird hier nicht erfunden.
Es gibt keinen neuen GVEF-Aufruf im produktiven Host oder Forschungsloop.

## Historische Bedeutungen und externe Quellen

Die erhaltene [Owner-Nachricht vom 01.10.](historical_iu_scope_owner_request.txt) begrenzt
IU auf Scope-Berechnung/-Übergabe für den bereits ausgewählten Future. Die spätere
[14-Layer-Projektion](historical_iu_layer_projection.json) gruppiert hingegen eine
breitere Instrument-/Ranking-/Binding-Kette. Diese datierten Bedeutungsumfänge bleiben
getrennt; Market Intelligence wird nicht zum Synonym erklärt. Historische GO-/STOP-
Texte in archivierten Quellen sind keine aktuellen Anweisungen.

Die [erhaltenen PDF-Seiten 1–2](historical_autonomy_source_excerpt.json) beschreiben
Full-Core Execution Autonomy als getrennte Ablauf-/Authority-Kette. Original-PDF-Hash
ist geprüft; die frühere Extraktion wurde gelesen, nicht neu gerendert. Ein damaliger
Snapshot wird nicht zum heutigen Betriebsstand übernommen.

[GitHub-PR-Metadaten und Beschreibungen](github_pr_sources.json) verankern #6206, #6524,
#6847, #6880, #7039 und #7044 mit Merge-Revision. Historische Testzahlen dieser PRs
werden nicht als heutige Ergebnisse übernommen. Lokale Git-Historie ist shallow.

[M2-/Recovery-Fundbindungen](external_copy_bindings.json): sieben gezielt gelesene
Backup-Dateien stimmen mit dem Repo überein, darunter drei GVEF-Evaluatoren.
Das Recovery-v3.4-Addendum ist ebenfalls bytegleich. Erhaltene Kopien sind keine
unabhängigen Laufzeitbeweise. Mount-Identität wurde erneut geprüft; externe Originale
wurden nicht beschrieben. Keine vollständige Prüfung aller Recovery-Dateien behauptet.
[Obsidian-Quellenbindung](obsidian_source_bindings.json) hält die gelesenen datierten
Register getrennt von aktuellem Code fest.

## Ergebnis der Aufnahme

**Aufgenommen:** GVEF als belegte vorhandene Vergleichsfähigkeit im Architekturabgleich,
konkrete Beziehungen, Namens-/Rollenunterschiede und prüfbare Grenzen samt Quellen.
**Nicht belegt und deshalb nicht neu verdrahtet:** automatische bereichsübergreifende
Runtime, GVEF→numerischer Folgeversuch, vollständige Lane-/Daten-/Outcome-Attribution.

[Scope-Erhaltung](protected_scope_source_hashes.json), [Receipt und lokale Checks](receipt.json).
Originales Learning-Ledger unverändert. U04 und GAP-0370 bleiben zurückgestellt.
Keine Produktivaktivierung, Orders, Zugangsdaten, Veröffentlichung oder Push.
