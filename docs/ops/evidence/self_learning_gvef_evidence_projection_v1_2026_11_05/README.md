---
docs_token: DOCS_TOKEN_SELF_LEARNING_GVEF_EVIDENCE_PROJECTION_V1
status: supplemental_source_review
runtime_authorization_effect: NONE
---

# SelfLearning: Ergebnis, registriertes Bundle und späterer Meta-Eingang

Diese Ergänzung bindet ihre Aussagen an den eingefrorenen Quellstand
`732601aeacca7b87ff3df2e0373f180f8de50081`. Sie ergänzt die
[vorherige GVEF-Prüfgrenzenanalyse](../self_learning_gvef_functional_addendum_v1_2026_11_05/README.md).
Implementierung, Konfiguration und Scope-Berechnung bleiben unverändert.
Das [Master-Runbook](../../../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) bleibt maßgeblich.

## Drei getrennte Datenwege

Im vorhandenen [Messreferenz-Test](../../../../tests/evaluation/golden_vectors/test_measured_learning_reference_v1.py)
wird das konkrete Corpus-Gate verwendet. Die übrigen Dependencies stammen aus einem
[Testhelper](../../../../tests/evaluation/golden_vectors/test_gvef_domain_evaluators_bwp456_v1.py):
Comparator, Evidence-Builder und Evidence-Registry sind deterministische Fixtures.

- Im Runrecord bleibt das detaillierte SelfLearning-Candidate-Ergebnis mit Artefaktdigest erhalten.
- Das registrierte Fixture-Bundle übernimmt dieses Ergebnis nicht vollständig. Sein Builder setzt
  beispielsweise eine feste Invariante `i1`, eine feste Corpusversion und den Seed-Digest als
  Corpusdigest. Er übernimmt CRS-/Ranking-Sonderfelder, jedoch keine SelfLearning-Artefaktdeltas.
- Der spätere numerische Meta-Aufruf verwendet den separat geladenen Forschungsdatensatz.
  Er konsumiert an dieser Stelle nicht das registrierte Fixture-Bundle.

Das erklärt die vorhandene Verbindung genauer: Konkrete Eingangsprüfung, detaillierter Runrecord,
registrierte Evidence-Projektion und späterer numerischer Consumer haben jeweils eigene Verträge.
Die vorhandene Archiv-/Meta-Verbindung bleibt erhalten. Fixture-Felder belegen keinen Produktivfehler.

## Geltungsbereich des geschützten Output-Digests

Der Runner bindet Zustandsfolge, Manifest-, Baseline-, Delta-, Fach- und Evidence-Digests.
Er bindet keinen Candidate-Result- oder Replay-Trace-Digest direkt.
Im betrachteten Fixture-Pfad ignoriert der Comparator die Candidate-Werte, und der Builder
übernimmt die SelfLearning-Artefaktdeltas nicht. Wenn sämtliche übrigen Digest-Eingaben gleich
bleiben, muss eine ausschließlich dortige Candidate-Änderung deshalb den Output-Digest nicht ändern.
Das ist eine begrenzte Aussage über die Eingabeprojektion; es wurde keine Hashkollision erzeugt.
Andere injizierte Implementierungen können Candidate-Inhalte transitiv binden.

Der aktuelle Messreferenz-Loader liefert einen einzelnen ungelabelten Artefakteintrag für beide
Evaluationsseiten. Dieser konkrete Referenztest ist kein unabhängiger Qualitätsvergleich zweier
Forschungskandidaten. Weder der Test noch der Runner wurden für diese Untersuchung ausgeführt.

## Ergänzungsbedarf

Wenn ein Consumer vollständige Candidate- oder Corpusidentität benötigt, muss deren Erhaltung
bis zu diesem Consumer ausdrücklich nachgewiesen werden. Ein Digestname oder `REGISTERED` reicht
dafür allein nicht. Sechs konkrete, noch nicht ausgeführte Kriterien sowie exakte Quellrevisionen,
Zeilenspannen und Datei-/Ausschnitt-Hashes stehen in [findings.json](findings.json).
Die [Manifestdatei](manifest.json) bindet die Dateien dieses Quellenbefunds.
