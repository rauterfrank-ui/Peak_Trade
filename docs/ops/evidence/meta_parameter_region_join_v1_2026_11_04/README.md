# Phase-11 → Phase-12 Parameterbereich-Anschluss

Begrenzte Umsetzung des ursprünglichen Search-Vertrags: identisch deklarierte vollständige Parameterregionen verwenden bei Meta-Producer und Search-Consumer dieselbe bestehende Digest-Domain und Darstellung. Der Producer verwendet einen gemeinsamen Helper; seine Fixture-Ausgabe einschließlich Meta-Identität bleibt exakt gleich. Search erkennt diese Hashadresse und verändert damit nur den passenden Kandidaten und gegebenenfalls dessen Budgetaufnahme.

Keine implizite Ergänzung fehlender Achsen aus der Strategievorlage. Ein Teilraum ist keine identische Region. Nicht-Hash-Einzelwertsignale bleiben als ältere Form erhalten; Hashadressen können nicht zufällig einzelne Hashwerte als Region treffen. Andere Target-Typen werden nicht in diesen Matcher gezwungen. M4s bislang fehlende optionale Meta-Zulieferung und äußere Planer bleiben separate Anschlussfragen.

37 Tests bestanden, darunter fünf neue Prüfungen mit tatsächlichem Meta-Producer, tatsächlichem Search-Consumer, Budgetwirkung und negativen Adressfällen. tests.xml und receipt.json binden Umfang und Ergebnisse. source_changes.patch.txt und die beiden vorherigen Quelltexte erhalten den genauen Änderungskontext. Historische Berichte/Probes bleiben unverändert an ihre alten Revisionen gebunden. Deren alte Current-Quellanker für diese zwei Module sind nach diesem ausdrücklich geprüften Fix entsprechend historisch, kein frischer Current-PASS.

Produktive Handelslogik, Konfiguration und originales Lerndaten-Ledger bleiben unverändert; keine Aktivierung oder automatische Experimentausführung. Details im [Blueprint Abschnitt 37](../../blueprints/PEAKTRADE_SYSTEM_RECONFIGURATION_BLUEPRINT_2026_11_03.md).
