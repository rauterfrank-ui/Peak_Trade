# Selbstlernendes Universum: kausale Wirkung von Loop A und MI-Evidence

Stand 04.11.2026, Quellenpin `98e718250`. Fortsetzung der
[Primärquellenrekonstruktion](../self_learning_original_design_gvef_boundary_v1_2026_11_04/README.md).
Alle bestehenden Implementierungen bleiben gemäß aktueller Owner-Anweisung unverändert.
Nur Untersuchung, kontrollierte Offline-Aufrufe vorhandener Owner und Dokumentation.

## Ergebnis

Der konkrete DDO-Closed-Loop und das breitere Outcome-/Forecast-Lernen sind unterschiedliche
Nachweise. Die vorhandene DDO-Schleife führt ein ausdrücklich opakes ökonomisches Label
zurück. Die MI-Schleife erzeugt und speichert Kalibrierungs-Evidence; ihr geprüfter
M4-Anschluss bindet Herkunft, ohne die Kalibrierungszahl in die Forschungsberechnung zu
übersetzen. Das ist kein Beleg einer fehlenden Datei und kein pauschaler Defektbefund.
Es präzisiert, welche Bedeutung die vorhandenen Closure-Aussagen tatsächlich tragen.

## 1. Originalabsicht des implementierten DDO-Closed-Loop

Die frisch gelesene [ursprüngliche PR #6634](original_closed_loop_pr6634.json), Merge
`c889577bef56300f74039d921472f0638cbb8810` vom 19.09.2026, beschränkt den Scope explizit
auf economic_score label feedback. Regime-, Kalibrierungs-, Drift- und Model-Quality-
Reducer, Promotion und Optimization-Join waren außerhalb dieses Pakets. Alte Testzahlen
in der PR sind historische Angaben, keine heutige Suite-Prüfung.

Der [bestehende normative Vertrag](../../specs/LEARNING_OUTCOME_EVIDENCE_INGEST_AND_STATE_NORMATIVE_V1.md)
benennt den Consumer als Real-Outcome-Horizon-Host und die Wirkung als opakes Label in
der nächsten evaluation_observation. Numerisches Kalibrieren und abgeleitete Performance
gehören nicht zu diesem Reducer. Der breite Originalmaster darf deshalb nicht mit dem
engen Paketabschluss SELF_LEARNING_PRODUCTIVE_CLOSED_LOOP_V1 gleichgesetzt werden.

## 2. Tatsächlicher DDO-Wirkpfad

Der O4-/N_BARS-Supplier berechnet Messwerte aus den Bar-Schlusskursen und mintet deren
Content-Referenz. Das Economic-Label wird separat vom Aufrufer geliefert. Der Horizon-
Owner reicht es weiter. EvaluationBundle und Ingest validieren Datensätze, Herkunft,
Identitätsbezüge und Reihenfolge; der Reducer übernimmt das Label in den versionierten
Learning-State. Der Host prüft die gebundene Konfiguration und setzt das nächste
Horizon-Eingabelabel. Im gelesenen Bridge-Aufruf wird dieser Wert nicht zum Trading-
Replay-Input gemacht. Die nächste Wirkung liegt wieder im Auswertungszweig.

[Kontrollierte bestehende Owner-Aufrufe](controlled_consumer_probes.json) zeigen:

- Preis 100→110: gemessener Log-Return 0,0953101798; geliefertes Label OPAQUE_A bleibt OPAQUE_A.
- Preis 100→90: Log-Return −0,1053605157; dasselbe gelieferte Label bleibt OPAQUE_A.
- Bei unverändertem Preis 100→110 führt allein OPAQUE_B zu OPAQUE_B im State und Feedback.
- Eine fremde Capture-Konfiguration setzt das zuvor passende Feedback auf UNKNOWN.

Damit sind Messung und Label-Rückführung kausal getrennt. Der Zahlenwert wird nicht in
diesem Pfad automatisch zum Label gelernt. Der Test benutzt temporäre Ledger und einen
kleinen Host-State am tatsächlichen Feedback-Port, keinen vollständigen produktiven
Host. Die gültig geformten Code-/Config-Digests sind kontrollierte Fixture-Werte; ihre
Annahme authentifiziert keine natürliche Quelle. Das ursprüngliche Ledger wird inhaltlich nicht ausgewertet,
neu klassifiziert oder beschrieben; sein Hash wird separat kontrolliert.

## 3. MI-Kalibrierung: Zahl, Kennung und numerischer Consumer

Bei derselben Prognose mit p_up=0,5, p_down=0,3 und p_flat=0,2 und derselben N_BARS-
Beobachtung wurden UP, DOWN und FLAT als separate kontrollierte Aufruferlabels geliefert.
Der reale Kalibrierungsowner berechnet 0,5 / 0,7 / 0,8. Fehlendes Label wird mit
REALIZED_DIRECTION_REQUIRED abgelehnt. Die Beobachtung wird nicht selbst zur Richtung
aufgelöst; die widersprechenden Labels sind Eingabeinterventionen, keine behaupteten
Marktwahrheiten.

Semantisch relevant: Der Methodenname lautet BRIER_SCORE_V1, die tatsächlich gelesene
Richtungsformel lautet **1 − Wahrscheinlichkeit der gelieferten realisierten Klasse**.
Sie ist schon in der [ursprünglichen Implementierung an 32171b35e](original_calibration_32171b35e.py.txt)
vorhanden. Der Name wird hier weder umdefiniert noch als Beweis einer quadratischen
Mehrklassenbewertung oder einer gemessenen Kalibrierung über eine Population benutzt.
Keine Formel wird geändert.

Die drei Ergebnisse erzeugen unterschiedliche Calibration-/MI-Evidence-Kennungen.
MI-Learning-Record und Research-Projektion transportieren in diesem Pfad IDs, Digests,
Evaluability, Horizon und Herkunft, nicht das numerische calibration_result selbst.
Der MI-enriched-M4-Owner nimmt diese Lineage auf, ruft die bestehende Experiment Plane
aber mit dem separat gelieferten plane_request auf. Champion-/Challenger-Scores und
Robustheitsbeobachtungen stammen weiterhin aus diesem Request.

Die drei tatsächlichen MI-enriched-M4-Aufrufe enthalten auch den optionalen validierten
MI-Lernexport. Nach Entfernung genau der zwei MI-Anhangsfelder mi_enriched_m4_intake
und mi_lineage_refs sind **sämtliche übrigen Chain-Felder vollständig identisch**.
Unterschiedliche Kalibrierungswerte verändern in diesem kontrollierten Fall also
Provenienz, aber weder Search-/Challenger- noch Robustheits-/Proposal-Ergebnis.
Das ist ein lokaler Interventionstest bei festem Experiment-Request, keine Behauptung,
dass jeder mögliche externe oder dynamische Consumer diese Werte ignoriert.

## 4. Persistenz ist vorhanden; Referenztransport ist kein Datenverlustbeweis

Der bestehende MiLearningEvidenceStore speichert drei unterschiedliche Lernrecords;
identische Wiederholung wird jeweils IDEMPOTENT_REPLAY. Der separate
MiOfflineDurableEvidenceStore speichert die vollständige Triade aus Forecast,
Calibration und Research-Projektion. Alle drei Kalibrierungsresultate wurden am
jeweiligen durable_evidence_id wieder gelesen und vollständig verglichen.

Numerische Kalibrierung ist somit im vorhandenen Triad-Store erhaltbar. Das vermeidet
die falsche Schlussfolgerung, eine referenzbasierte Projektion habe die Zahl systemweit
vernichtet. Ein späterer numerischer Leser müsste die Triade jedoch tatsächlich laden
und fachlich verwenden. Die [begrenzte Symbolsuchen](bounded_consumer_searches.json)
in src/scripts lokalisieren keinen solchen späteren Aufruf des Forecast-Lookups außerhalb
des Store-Owners. Dynamische oder externe Wege sind dadurch nicht global ausgeschlossen.

## 5. Conditioned Loop A: tatsächliche Closure und deren Bedeutung

Zusätzlich wurde der vorhandene conditioned Cycle mit bestehenden synthetischen
Context-/Behavior-/Forecast-Helfern ausgeführt. Writer→Store→Reader/Export ist gleich;
loop_a_proven, persistence_proven und export_retrieval_proven werden true. Die vorhandene
optionale Termination am Evidence Adjudicator A liefert für MI und Learning ADMIT.

Diese konkrete Verbindung ist vorhanden. Die Funktion komponiert und exportiert
Evidence, ohne dadurch einen Forecast-Parameter zu trainieren oder den nächsten
numerischen Forecast zu erzeugen. ADMIT am A-Eingang ist keine B-/DP-Aktivierung.
Die Kennungen und Behavior-Semantikzustände bleiben Evidence, keine neue Autorität.
Der Phase-21-Vertrag bezeichnet genau diese Integration; ein neuer Gesamtbeweis für
lernende Vorhersagequalität entsteht aus seinem Closure-Label nicht.

## 6. Einordnung in die vollständige Rekonstruktion

**Belegt:** enger DDO-Labelpfad, echte numerische MI-Kalibrierungsberechnung aus gelieferten
Labels, append/read/idempotent replay, separate vollständige Triad-Persistenz,
conditioned Evidence-Export bis A und MI-Lineage im M4-Aufruf.

**Weiter offen:** authentischer Producer des realisierten Labels mit passendem Forecast-
Messfenster; numerischer Leser für kohortenbezogene Kalibrierungs-/Modellqualität;
beobachtete Änderung eines späteren Forecasts oder Forschungsrequests durch diese
Information; anschließende Messung ihres Nutzens. Die breiteren Loop-B-/Loop-C- und
GVEF-Fragen aus Blueprint 84 bleiben eigenständige Nachweise.

Eine erkannte historische Absicht, ein fehlender Nachweis oder eine ungewöhnliche
Metrikbezeichnung hebt Franks Erhaltungsentscheidung nicht auf. Weitere Arbeit sucht
vorhandene Zwischenowner, alternative Pfade und retained Evidence. Wo eine Closure nur
mit Implementierungsänderung erreichbar wäre, bleibt sie unter dieser Grenze offen.

## Prüfung und Erhaltung

[Quellpfade und SHA256](source_bindings.json), [Receipt und Aussagegrenzen](receipt.json),
[reproduzierbare Probe als Textquelle](controlled_consumer_probe.py.txt),
[Scope-Erhaltung](scope_preservation.json).
Keine neue pytest-Suite, kein geänderter Test oder Produktcode. Die tatsächlichen
Aufrufe enthalten Assertions für die beschriebenen positiven und negativen Kontrollen.
Die anfänglich falsch geformte 40-stellige Probe-Code-ID wurde vom vorhandenen Vertrag
abgelehnt; ausschließlich der eigene Fixture-Eingang wurde auf 64 Stellen korrigiert.
Alle Stores lagen temporär außerhalb des Repos. U04 und GAP-0370 bleiben zurückgestellt;
keine Aktivierung, Orders, Dienste, Netzwerk-Marktruns oder externe Quellenschreibzugriffe.
