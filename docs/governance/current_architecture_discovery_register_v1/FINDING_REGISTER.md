# Finding-Register V1

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

Spätere Verengungen ersetzen die Ursprungs-ID nicht. `STATUS=PRESERVED` ist der Stand des Chat-Abschlusses, keine Trading-Autorität. `BASELINE` jeder Zeile ist `ff7985e3c5dd9c1823a7dfd0ad5924d72a0c09a4`. `SOURCE=CHAT_TRANSCRIPT_EVIDENCE`, außer wo die Zeile `EVIDENCE_NOT_RECOVERED` sagt.

Nachbarregister: [Discovery-Index](DISCOVERY_INDEX.md), [Funktionsflächen](FUNCTIONAL_AREA_REGISTER.md), [Owner-Referenzen](OWNER_DECISION_REFERENCES.md), [Evidence-Quellen](EVIDENCE_SOURCE_INDEX.md), [Offene Abhängigkeiten](OPEN_DEPENDENCIES.md).

## OF-S4-01 bis OF-S4-10

| ID | CLAIM | PROOF_SCOPE | STATUS | OPEN_DEPENDENCY |
|---|---|---|---|---|
| OF-S4-01 | GAP-13 bleibt offen. Kartennamen sind keine geschlossenen Domänen. | S4-Abschluss | OPEN | GAP-13 |
| OF-S4-02 | Landscape-Producer- und Consumer-Listen leer. PROVEN_CURRENT nicht übernommen. | S4-Abschluss | OPEN | Landscape-Listen |
| OF-S4-03 | Equity-Paket mischt Truth, C08, Cap21–Cap24, Credentials und Send-Seam. Mitgliedschaft ungeschlossen. | S4-Ursprung. S9 bestätigt die Mischung. S17 lässt die Einzelrolle offen. | OPEN | Einzelrolle, [Owner-Referenzen](OWNER_DECISION_REFERENCES.md) |
| OF-S4-04 | WP-A ist nicht der direkte Master-V2-Import. Preisherkunft und Reference-Price-Owner sind getrennt. | S4-Abschluss | OPEN | beide Owner getrennt |
| OF-S4-05 | `src/data` und `src/markets` waren Public Market Data nicht zugeordnet. | S4-Ursprung. S15: statisch unabhängig, Universum UNASSIGNED. | NARROWED | Universum UNASSIGNED |
| OF-S4-06 | Runbook-WebUI-Pfad auf dieser Baseline abwesend. | S4-Abschluss, danach nicht erneut gelesen | OPEN | Pfad |
| OF-S4-07 | Rückkonsum der Presentation durch Decision-Owner nicht erschöpfend ausgeschlossen. | S4-Ursprung. S13/S14: acht Projektionen ohne produktiven Decision-Leser. Readmodel ist simulierte Identitätsmarke. Full-Core-Feedback NOT_PROVEN. | NARROWED | PRODUCTIVE_FULL_CORE_FEEDBACK=NOT_PROVEN |
| OF-S4-08 | Research-Mitgliedschaft ohne Vertrag. S4: Importisolation nicht belegt. | S16: `src/knowledge` statisch isoliert, Mitgliedschaft PROVISIONAL. Nicht automatisch aufgelöst. | NARROWED | Zugehörigkeit |
| OF-S4-09 | GHV-Graphen vom 2026-10-16 nicht gegen den Pin geprüft. | S15/S16: Snapshot `cc0d6099` ist nicht der Pin und keine CURRENT-Autorität. | OPEN | Graph bleibt stale für diesen Pin |
| OF-S4-10 | S1, S2, S3, S3B bleiben OPEN. Keine Reparatur. | S4-Abschluss | OPEN | S1, S2, S3, S3B |

OF-S4-07 behält diese drei Formeln:

```text
EIGHT_PRESENTATION_PROJECTIONS=NO_PROVEN_PRODUCTIVE_DECISION_READER
UNIVERSE_SELECTION_READMODEL=CONFIRMED_SIMULATED_DECISION_IDENTITY_PATH
PRODUCTIVE_FULL_CORE_FEEDBACK=NOT_PROVEN
```

OF-S4-05 behält diese vier Formeln aus S15:

```text
SRC_DATA_SRC_MARKETS=STATICALLY_INDEPENDENT_FROM_PMD_RUNTIME
UNIVERSE_MEMBERSHIP=UNASSIGNED
CCXT_PRIVATE_ACCOUNT_READS=SEPARATE_FUNCTIONAL_BOUNDARY
QUALITY_MONITOR_IMPORT_MISMATCH=DOCUMENTED_NOT_REPAIRED
```

## NF-S5-01 bis NF-S5-07

| ID | CLAIM | PROOF_SCOPE | STATUS | OPEN_DEPENDENCY |
|---|---|---|---|---|
| NF-S5-01 | Cap22-Paket enthält keinen Import und kein Symbol von Cycle, BoundInstrumentV1 oder Cap23. | S5-Abschluss | OPEN | keine Cap22-Kante |
| NF-S5-02 | Die Cycle-Datei enthält kein Ranking-Token. | S5-Abschluss | OPEN | E-IN-10 |
| NF-S5-03 | Der Handoff gibt die Lane-Map zurück und ruft den Cycle nicht auf. | S5-Abschluss | OPEN | E-IN-11 |
| NF-S5-04 | Ein späterer Orchestratorschritt erreicht den Cycle über andere Module. | S5-Abschluss | OPEN | getrennte Kette |
| NF-S5-05 | Addressing-Invoke und Carry haben Cycle-Aufrufe und keinen src-Aufrufer außerhalb ihrer Definitionen. | S5-Abschluss | OPEN | Aufrufer |
| NF-S5-06 | Dieselbe Cycle-Funktion hat weitere direkte Aufrufer, darunter sieben Fresh-Runtime-Module im Equity-Paket. | S5-Abschluss | OPEN | keine Einzelrolle |
| NF-S5-07 | Alternative BoundInstrument-Konstruktoren sind keine Cap22-Kante. | S5-Ursprung. S8: keine Quellkante zum Cycle-Parameter. Existenz bleibt. | PRESERVED | Existenz bleibt |

## NF-S9-01 bis NF-S9-04

| ID | CLAIM | PROOF_SCOPE | STATUS | OPEN_DEPENDENCY |
|---|---|---|---|---|
| NF-S9-01 | 158 Module bestätigt. | S9-Abschluss. S17 stichprobenartig 158. | PRESERVED | Per-File-Register nicht in dieses Dokument kopiert |
| NF-S9-02 | Leerer Slot und erzeugter Sizing-Producer sind zwei Pins. | S9-Abschluss. S17 bestätigt. | PRESERVED | siehe Owner-Referenzen |
| NF-S9-03 | Send-Seam bricht ab, solange die POST-Flags nicht falsch sind. | S9-Abschluss, in S17 nicht neu gelesen | PRESERVED | nicht neu gelesen |
| NF-S9-04 | Standing-Gate-Setter quellverdrahtet, aktiv NOT_PROVEN. | S10: kein produktiver Aufrufer. Diese `execute_*` schreiben die Flags nicht. | OPEN | Aktivierung NOT_PROVEN |

## NF-S15-01 bis NF-S15-06

Tokens aus dem S15-Abschluss. In der S18-Tabelle nicht erneut ausformuliert und hier erhalten, damit die IDs nicht verloren gehen.

| ID | CLAIM | PROOF_SCOPE | STATUS | OPEN_DEPENDENCY |
|---|---|---|---|---|
| NF-S15-01 | `NF-S15-01_ZERO_IMPORT_EDGE_BOTH_DIRECTIONS` | S15-Abschluss | PRESERVED | Universum UNASSIGNED |
| NF-S15-02 | `NF-S15-02_FULL_CORE_USES_SAFETY_ENUMS_ONLY` | S15-Abschluss | PRESERVED | kein Kerzenfluss aus diesem Token |
| NF-S15-03 | `NF-S15-03_CCXT_PROVIDER_ALSO_READS_BALANCE_AND_OPEN_ORDERS` | S15-Abschluss | PRESERVED | getrennte Funktionsgrenze |
| NF-S15-04 | `NF-S15-04_CME_METADATA_HAS_NO_DECISION_PACKAGE_IMPORTER` | S15-Abschluss | PRESERVED | keine Decision-Mitgliedschaft |
| NF-S15-05 | `NF-S15-05_LIVE_FEED_IS_IN_MODULE_STUB` | S15-Abschluss | PRESERVED | Stub, keine Aktivierung |
| NF-S15-06 | `NF-S15-06_OHLCV_FRAME_AND_PMD_FACT_RECORD_ARE_DISTINCT_CONTRACTS` | S15-Abschluss | PRESERVED | Verträge nicht verschmolzen |

## NF-S16-01 bis NF-S16-08

Tokens aus dem S16-Abschluss. Ebenfalls nicht in der S18-Tabelle ausformuliert und hier erhalten.

| ID | CLAIM | PROOF_SCOPE | STATUS | OPEN_DEPENDENCY |
|---|---|---|---|---|
| NF-S16-01 | `NF-S16-01_ZERO_IMPORT_EDGE_TO_NEIGHBORS_AND_DECISION_PACKAGES` | S16-Abschluss | PRESERVED | Zugehörigkeit PROVISIONAL |
| NF-S16-02 | `NF-S16-02_CONFIG_KNOWLEDGE_ENABLED_UNREAD_BY_PACKAGE` | S16-Abschluss | PRESERVED | Config schaltet das Paket nicht |
| NF-S16-03 | `NF-S16-03_RAG_RETURNS_CONTEXT_WITHOUT_MODEL_CALL` | S16-Abschluss | PRESERVED | kein Modellaufruf aus diesem Token |
| NF-S16-04 | `NF-S16-04_TIMESCALEDB_DOCSTRING_ONLY` | S16-Abschluss | PRESERVED | Docstring ist keine Implementierung |
| NF-S16-05 | `NF-S16-05_QDRANT_AND_PINECONE_ADD_SEARCH_UNIMPLEMENTED` | S16-Abschluss | PRESERVED | nicht implementiert |
| NF-S16-06 | `NF-S16-06_NO_SINGLE_WRITER_NO_ARTIFACT_VERSION` | S16-Abschluss | PRESERVED | kein Single-Writer |
| NF-S16-07 | `NF-S16-07_DEMO_SCRIPT_IS_ONLY_NON_TEST_CALLER` | S16-Abschluss | PRESERVED | Demo ist kein Decision-Leser |
| NF-S16-08 | `NF-S16-08_KNOWLEDGE_WEB_WRITE_ENABLED_ABSENT_FROM_THE_FIVE_MODULES` | S16-Abschluss | PRESERVED | Flag nicht in den fünf Modulen |

## NF-S17-01 und NF-S17-02

| ID | CLAIM | PROOF_SCOPE | STATUS | OPEN_DEPENDENCY |
|---|---|---|---|---|
| NF-S17-01 | S9 nennt 49 Nicht-Test-Referenzen. Eine frische String-Zählung ergibt 51. Die Differenz ist nicht klassifiziert. | S17-Abschluss | OPEN | 49er-Dateiliste `EVIDENCE_NOT_RECOVERED` |
| NF-S17-02 | Runbook-B05 setzt `GOVERNED_PRODUCER_CREATED=true`. `constants_v1.py` Zeile 56 setzt dasselbe Flag auf `False`. Die Implementierung bleibt in beiden Quellen `false`. | S17-Abschluss und Pin-Zeilen | OPEN | keine Auflösung |

## E-IN-10, E-IN-11, E-N5-01

| ID | CLAIM | PROOF_SCOPE | STATUS | OPEN_DEPENDENCY |
|---|---|---|---|---|
| E-IN-10 | Direkte Ranking-nach-Cycle-Kante im Quelltext abwesend. | S5-Abschluss | PRESERVED | indirekte Kette schließt sie nicht |
| E-IN-11 | Handoff ruft den Cycle nicht auf. | S5-Abschluss | PRESERVED | späterer Pfad getrennt |
| E-N5-01 | Tokenkonflikt zweier Slice-Objekte. Produktive Fünf-Lane-Aktivierung NOT_PROVEN. | S6-Abschluss | PRESERVED | GAP-09 Laufzeit |

## Execution F1–F12

S7 lässt F1–F12 offen. Gehobene Einzeiler stammen aus dem Execution-Abschluss vor S1.

| ID | CLAIM | PROOF_SCOPE | STATUS | OPEN_DEPENDENCY |
|---|---|---|---|---|
| F1 | PIN_DRIFT: Verifier-Pin `5b90ede6` / `d9be174f` gegen den damals aktuellen Stand. | Execution-Abschluss, Einzeiler | OPEN | nicht in S1–S17 repariert |
| F2 | `EVIDENCE_NOT_RECOVERED` | ID im Abschluss vorhanden, Einzelsatz in S18 nicht gehoben | OPEN | Satz fehlt |
| F3 | `EVIDENCE_NOT_RECOVERED` | ID im Abschluss vorhanden, Einzelsatz in S18 nicht gehoben | OPEN | Satz fehlt |
| F4 | `EVIDENCE_NOT_RECOVERED` | ID im Abschluss vorhanden, Einzelsatz in S18 nicht gehoben | OPEN | Satz fehlt |
| F5 | `EVIDENCE_NOT_RECOVERED` | ID im Abschluss vorhanden, Einzelsatz in S18 nicht gehoben | OPEN | Satz fehlt |
| F6 | ACCOUNTING_KERNEL: Paper-`futures_accounting` `BOUND_NOT_ACTIVATED`. | Execution-Abschluss, Einzeiler | OPEN | nicht aktiviert |
| F7 | `EVIDENCE_NOT_RECOVERED` | ID im Abschluss vorhanden, Einzelsatz in S18 nicht gehoben | OPEN | Satz fehlt |
| F8 | SOCKET_BRANCH: Full-Core-HTTP-Post nur erreichbar, wenn `one_shot_real_post` und `REAL_VENUE_POST_ALLOWED` falsch sind. Der Cycle ruft ihn nicht auf. | Execution-Abschluss, Einzeiler | OPEN | kein ausgeführter POST |
| F9 | `EVIDENCE_NOT_RECOVERED` | ID im Abschluss vorhanden, Einzelsatz in S18 nicht gehoben | OPEN | Satz fehlt |
| F10 | LOCAL_DRIFT: HEAD `28240231`. | Execution-Abschluss, Einzeiler | OPEN | Preservation-Checkout, nicht der Pin |
| F11 | WEBHOOK: `urllib`-Import, Erreichbarkeit NOT_PROVEN. | Execution-Abschluss, Einzeiler | OPEN | Erreichbarkeit |
| F12 | FIVE_OPEN_TASKS: EX-OPEN-01 bis EX-OPEN-05 bleiben OPEN. | Execution-Abschluss, Einzeiler | OPEN | Einzelclaims `EVIDENCE_NOT_RECOVERED` |

## GAP-01 bis GAP-18

```text
PROOF_SCOPE=S7-Abschluss
SOURCE=CHAT_TRANSCRIPT_EVIDENCE
BASELINE=ff7985e3c5dd9c1823a7dfd0ad5924d72a0c09a4
STATUS=OPEN außer GAP-06 und GAP-15
OPEN_DEPENDENCY=Einzelsätze außer der Statusklasse EVIDENCE_NOT_RECOVERED
```

| ID | CLAIM | STATUS |
|---|---|---|
| GAP-01 bis GAP-05 | Einzelsatz `EVIDENCE_NOT_RECOVERED` | OPEN |
| GAP-06 | Für den S7-Scope geschlossen. Kein allgemeines All-Clear. | CLOSED_FOR_THIS_SCOPE |
| GAP-07, GAP-08 | Einzelsatz `EVIDENCE_NOT_RECOVERED` | OPEN |
| GAP-09 | In der S7-Tabelle benannt. Laufzeitfrage aus S6. Einzelsatz nicht neu abgeschrieben. | OPEN |
| GAP-10, GAP-11 | In der S7-Tabelle benannt. Einzelsatz `EVIDENCE_NOT_RECOVERED`. | OPEN |
| GAP-12 | Einzelsatz `EVIDENCE_NOT_RECOVERED` | OPEN |
| GAP-13 | Von OF-S4-01 offen gehalten. Einzelsatz über diese Aussage hinaus `EVIDENCE_NOT_RECOVERED`. | OPEN |
| GAP-14 | Einzelsatz `EVIDENCE_NOT_RECOVERED` | OPEN |
| GAP-15 | Aus dem S7-Scope ausgeschlossen. | EXCLUDED |
| GAP-16, GAP-17 | Einzelsatz `EVIDENCE_NOT_RECOVERED` | OPEN |
| GAP-18 | In der S7-Tabelle benannt und an S3 gebunden. Einzelsatz `EVIDENCE_NOT_RECOVERED`. | OPEN |

## EL-SURF-01 bis EL-SURF-19

```text
PROOF_SCOPE=S7-Klassifikation
STATUS=UNCLASSIFIED außer den fünf teilgeprüften Karten
OPEN_DEPENDENCY=Kartensätze EVIDENCE_NOT_RECOVERED
```

Teilgeprüft nach S7: EL-SURF-04 Cap24, EL-SURF-05 und EL-SURF-07 Public Market Data, EL-SURF-06 Private Account, EL-SURF-14 Research, EL-SURF-15 Presentation. Die übrigen Nummern 01, 02, 03, 08, 09, 10, 11, 12, 13, 16, 17, 18 und 19 bleiben IDs mit `EVIDENCE_NOT_RECOVERED` für den Einzelsatz und Status `UNCLASSIFIED`.

## E-IN, E-OUT, E-LEARN-OPT

| ID | CLAIM | PROOF_SCOPE | STATUS | OPEN_DEPENDENCY |
|---|---|---|---|---|
| E-IN-01 bis E-IN-09 | Inventarzeilen. Einzelsatz `EVIDENCE_NOT_RECOVERED`. | S7: nicht untersucht, außer den gesondert geführten E-IN-10 und E-IN-11 | NOT_EXAMINED | Satz fehlt |
| E-OUT-01 bis E-OUT-11 | Inventarzeilen. Einzelsatz `EVIDENCE_NOT_RECOVERED`. | S7 | NOT_EXAMINED | Satz fehlt |
| E-LEARN-OPT | Inventarzeile. Einzelsatz `EVIDENCE_NOT_RECOVERED`. | S7 | NOT_EXAMINED | Satz fehlt |

## Weitere S7-Register-IDs

| ID | CLAIM | PROOF_SCOPE | STATUS | OPEN_DEPENDENCY |
|---|---|---|---|---|
| C-CAP21, C-CAP22, C-CAP23 | S7-Registerzeilen. Claim-Satz `EVIDENCE_NOT_RECOVERED`. | S7 | ID_PRESERVED | Satz fehlt |
| ED-SELECTION-BINDING, ED-N5-HANDOFF, ED-N5-COMPLETION | S7-Registerzeilen. Claim-Satz `EVIDENCE_NOT_RECOVERED`. | S7 | ID_PRESERVED | Satz fehlt |
| ED-PRICE, ED-RECON, ED-CURSOR, ED-KILL-SWITCH, ED-CRS, ED-ORDER-INTENT, ED-SAFETY-KERNEL, ED-P5 | In S1–S6 nicht untersucht. Körper `EVIDENCE_NOT_RECOVERED`. | S7 | NOT_EXAMINED | Satz fehlt |
| EX-OPEN-01 bis EX-OPEN-05 | Von F12 als offen benannt. Einzelclaim `EVIDENCE_NOT_RECOVERED`. | F12-Einzeiler | OPEN | Satz fehlt |

## Was dieses Register nicht behauptet

Die vorhandene ID-Liste ist keine vollständige Beweissicherung. Wo der Satz fehlt, steht `EVIDENCE_NOT_RECOVERED`. Es wird kein fehlender Claim ergänzt.
