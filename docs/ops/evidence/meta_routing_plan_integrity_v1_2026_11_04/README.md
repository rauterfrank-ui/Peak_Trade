# Meta-Routing und Repräsentationsplan-Integrität

MR01: Der vorhandene Top-Level-Dual-Router reicht requested_consumer_override jetzt an die vorhandene Empfängerprüfung weiter. Vorher ließen sich zwei Negativfälle reproduzieren, bei denen trotz ausdrücklich widersprechender Gegenstelle ein Research-Consumer aufgerufen wurde. Nun werden beide vor jedem Consumer abgelehnt. Normale und ausdrücklich passende Routen bleiben identisch; UNKNOWN/MIXED bleiben geschlossen.

MP01: Der bisherige Plan-Validator prüfte die gespeicherten Identitäts-/Inhaltshashes nicht nach. Ein anderes Fixture-Label konnte unter alter Identität die Evaluation von REJECTED_REDUNDANCY zu RESEARCH_EVIDENCE_SUPPORTED ändern. Nun werden die vorhandene Planidentität und der gesamte Result-Digest nachgerechnet und die bestehenden fehlenden Apply-/Mutations-/Promotion-Rechte geprüft. Die Factory-Funktion und das Fixture-Auswertungsschema bleiben unverändert.

40 aktuelle Tests bestehen. after_tests.xml ist das aktuelle kombinierte Ergebnis; before_router_tests.xml enthält die zwei absichtlich vor dem Fix reproduzierten Fehler. Das sind keine zwei verbleibenden aktuellen Fehler. plan_tamper_before.json hält den ursprünglichen kontrollierten Integritätsbruch fest. receipt.json und Vorher-Snapshots binden die Quelländerungen.

Grenze: Loop C wertet im gelesenen Pfad Fixture-/Pattern-Labels aus. Das ist kein tatsächlich gemessener numerischer Forschungsfortschritt. Die erzeugte Next-Evidence ist weder automatischer Apply noch Nachweis einer folgenden Repräsentationsänderung. Ein finaler Messwert-/Folgeconsumer-Vertrag bleibt offen. Historische Quellen, Original-Learning-Ledger und Handelskonfiguration werden nicht verändert.

[Blueprint Abschnitt 38](../../blueprints/PEAKTRADE_SYSTEM_RECONFIGURATION_BLUEPRINT_2026_11_03.md).
