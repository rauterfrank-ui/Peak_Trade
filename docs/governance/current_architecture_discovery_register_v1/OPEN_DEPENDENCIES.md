# Offene Abhängigkeiten V1

```text
DRAFT_ONLY
UNRATIFIED
NON_AUTHORITATIVE_FOR_TRADING
AUTHORITY=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
GUARDIAN_ASSIGNMENTS=OPEN
GUARDIAN_RATIFICATION=NONE
BASELINE_SHA=ff7985e3c5dd9c1823a7dfd0ad5924d72a0c09a4
BASELINE_TREE=cbe53c0b64fe01c9477e93372adf877e6cedb172
REGISTER_SOURCE=CHAT_TRANSCRIPT_EVIDENCE
ON_ORIGIN_MAIN_BEFORE_THIS_DRAFT=ABSENT
FULL_EVIDENTIARY_PRESERVATION=NOT_CLAIMED
```

Offen heißt: der zugehörige Abschluss hat die Abhängigkeit nicht geschlossen. Dieses Register schließt sie ebenfalls nicht.

Nachbarregister: [Discovery-Index](DISCOVERY_INDEX.md), [Finding-Register](FINDING_REGISTER.md), [Funktionsflächen](FUNCTIONAL_AREA_REGISTER.md), [Owner-Referenzen](OWNER_DECISION_REFERENCES.md), [Evidence-Quellen](EVIDENCE_SOURCE_INDEX.md).

`SOURCE=CHAT_TRANSCRIPT_EVIDENCE` und `BASELINE=ff7985e3c5dd9c1823a7dfd0ad5924d72a0c09a4`, sofern eine Zeile nichts anderes sagt.

| ID | Warum offen | PROOF_SCOPE | STATUS | OPEN_DEPENDENCY |
|---|---|---|---|---|
| OF-S4-01 | GAP-13 bleibt offen. Kartennamen sind keine geschlossenen Domänen. | S4 | OPEN | GAP-13 |
| OF-S4-02 | Leere Landscape-Listen. PROVEN_CURRENT nicht übernommen. | S4 | OPEN | Landscape-Listen |
| OF-S4-03 | Mischung bestätigt, Einzelrolle offen. | S9, S17 | OPEN | Owner-Entscheidung Trackname gegen leeren Slot |
| OF-S4-04 | WP-A ist nicht der direkte Master-V2-Import. | S4, S19, S20 | NARROWED | Preisherkunft und Reference-Price-Owner. PRODUCTIVE_CALLER=SOURCE_NOT_PROVEN. VALUE_CONTINUITY=CONDITIONAL. INSTRUMENT_IDENTITY=NOT_PROVEN. MARK_FRESHNESS=NOT_PROVEN. PRODUCTIVE_RUNTIME_EFFECT=NOT_PROVEN |
| OF-S4-05 | Paketgrenze belegt, Universum nicht. | S15 | NARROWED | Universum UNASSIGNED |
| OF-S4-06 | Runbook-WebUI-Pfad auf dieser Baseline abwesend. Nach S4 nicht erneut gelesen. | S4 | OPEN | Pfad bleibt abwesend, bis neu gelesen |
| OF-S4-07 | Full-Core-Feedback nicht belegt. | S13, S14 | NARROWED | PRODUCTIVE_FULL_CORE_FEEDBACK=NOT_PROVEN |
| OF-S4-08 | Zugehörigkeit vorläufig. S4 und S16 nicht automatisch aufgelöst. | S4, S16 | NARROWED | Research-Zugehörigkeit |
| OF-S4-09 | GHV-Graphen vom 2026-10-16 nicht gegen den Pin geprüft. | S4, S15, S16 | OPEN | Snapshot `cc0d6099` ist nicht der Pin |
| OF-S4-10 | S1, S2, S3, S3B ohne Reparatur. | S4 | OPEN | die genannten Discoveries |
| NF-S5-01 | Cap22 ohne Import und Symbol von Cycle, BoundInstrumentV1 oder Cap23. | S5 | OPEN | keine Cap22-Kante |
| NF-S5-02 | Cycle-Datei ohne Ranking-Token. | S5 | OPEN | E-IN-10 |
| NF-S5-03 | Handoff gibt die Lane-Map zurück und ruft den Cycle nicht auf. | S5 | OPEN | E-IN-11 |
| NF-S5-04 | Späterer Orchestratorschritt ist eine andere Kette. | S5 | OPEN | schließt E-IN-11 nicht |
| NF-S5-05 | Addressing-Invoke und Carry ohne src-Aufrufer außerhalb ihrer Definitionen. | S5 | OPEN | Aufrufer |
| NF-S5-06 | Weitere direkte Cycle-Aufrufer, darunter sieben Fresh-Runtime-Module im Equity-Paket. | S5 | OPEN | keine Einzelrolle |
| E-IN-10 | Direkte Ranking-nach-Cycle-Kante abwesend. | S5 | PRESERVED | indirekte Kette schließt sie nicht |
| E-IN-11 | Handoff ruft den Cycle nicht auf. | S5 | PRESERVED | späterer Pfad getrennt |
| E-N5-01 | Tokenkonflikt zweier Slice-Objekte. | S6 | PRESERVED | GAP-09 Laufzeit |
| GAP-09 | Als Laufzeitfrage offen. Einzelsatz nicht neu abgeschrieben. | S6, S7 | OPEN | Laufzeit NOT_PROVEN |
| GAP-01 bis GAP-18 außer GAP-06 und GAP-15 | S7: offen. Einzelsätze überwiegend `EVIDENCE_NOT_RECOVERED`. | S7 | OPEN | technische Außengrenze |
| GAP-06 | Für den S7-Scope geschlossen. | S7 | CLOSED_FOR_THIS_SCOPE | kein allgemeines All-Clear |
| GAP-15 | Aus dem S7-Scope ausgeschlossen. | S7 | EXCLUDED | nicht als geschlossen lesen |
| NF-S9-04 | Aktivierung der Standing-Gate-Setter nicht belegt. | S9, S10 | OPEN | Aktivierung NOT_PROVEN |
| NF-S17-01 | 49 gegen 51 unklassifiziert. | S17 | OPEN | Dateiliste `EVIDENCE_NOT_RECOVERED` |
| NF-S17-02 | Runbook-B05 `GOVERNED_PRODUCER_CREATED=true` gegen Code `False`. | S17 und Pin-Zeilen | OPEN | keine Auflösung in diesem Register |
| NF-S19-07 | Produktive Herkunft von mark_px bleibt NOT_PROVEN. | S19 | OPEN | PRODUCTIVE_CALLER=SOURCE_NOT_PROVEN |
| NF-S20-03 | Execute-Funktionen ohne produktiven Außenaufrufer auf diesem Pin. Sechs verlangen einen älteren origin_main_sha. | S20 | OPEN | PRODUCTIVE_CALLER=SOURCE_NOT_PROVEN |
| F1–F12 | Von S7 offen gelassen. | Execution-Abschluss, S7 | OPEN | F2, F3, F4, F5, F7, F9 Satz `EVIDENCE_NOT_RECOVERED` |
| EX-OPEN-01 bis EX-OPEN-05 | Von F12 als offen benannt. Einzelclaims nicht gehoben. | F12-Einzeiler | OPEN | `EVIDENCE_NOT_RECOVERED` für den Einzelsatz |
| S1, S2 | Technische Außengrenze. | S1, S2, S7 | OPEN | NOT_PROVEN |
| S3 | Aktivierung. | S3 | OPEN | GAP-18 |
| S3B | Witness-Epoch und Bypass-Konstruktoren. | S3B, S8 | OPEN | Existenz der Konstruktoren bleibt |
| S15 | Universum von `src/data/` und `src/markets/`. | S15 | UNASSIGNED | OF-S4-05 |
| S16 | Research-Zugehörigkeit. | S16 | PROVISIONAL | OF-S4-08 |
| Guardian | Keine Zuordnung und keine Ratifikation. | dieser Entwurf | OPEN | separates Owner-GO, hier nicht erteilt |

NF-S5-07 ist im [Finding-Register](FINDING_REGISTER.md) erhalten. S8 hat die fehlende Quellkante zum Cycle-Parameter festgehalten. Die Existenz alternativer Konstruktoren bleibt. NF-S9-01, NF-S9-02 und NF-S9-03 sind dort als erhaltene Pins geführt und in dieser Offen-Liste nicht erneut als ungelöste Sachfrage aufgeführt. NF-S9-03 wurde in S17 nicht neu gelesen.

Eine nächste Architektur-Discovery ist aus diesem Register nicht abgeleitet. Die nächste sichere Handlung nach dem Schreibdurchgang ist die Owner-Sichtung des Entwurfs, ohne Commit.

S20 hat NF-S5-05 und NF-S5-06 nicht geschlossen. Diese beiden Zeilen bleiben unverändert.

```text
DISCOVERY_BRANCH_STATUS=STOP
```
