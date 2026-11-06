# BTC: gemeinsame neue Zulassung und alte Forschungs-Kohorten trennen

Frank bestätigt erneut die gemeinsame BTC-Zulassung. Die aktuelle gemeinsame Asset-Policy ist leer; die im GGE-/Double-Play-Checkpoint angepasste Canonicalization lässt BTC zu. Das ist keine Ausnahme von Metadaten-, Kapital-, Größen- oder Risikoprüfungen.

Der erneute Abgleich zeigt eine verbleibende Integrationslücke: Der generische PIT-Manifest-Validator und der Lifecycle-Registry-Validator besitzen noch eigene feste BTC-/Alias-Sperren. Das sind tatsächliche Instrumentfilter, nicht lediglich die Flagge bitcoin_direction_allowed. Die ursprünglichen Git-Fassungen stammen vom 03.07.2026; die drei erhaltenen Quellen sind an ihre genauen Revisionen gebunden. Der gemeinsame Canonicalization-Anschluss wurde später im neuen System geändert.

Der kontrollierte heutige Generatorlauf lässt BTC/XBT/WBTC zunächst kanonisieren und lehnt erst bei der Manifestvalidierung ab. Die vorhandene fokussierte Suite ergibt 70 PASS und drei FAIL: Die drei alten Generator-Tests erwarten noch den früheren Ausschluss vor der Manifestbildung. Es wurde keine Erwartung nur zum Erreichen eines grünen Ergebnisses umgeschrieben.

Die Materialisierung und ihr OKX-Source-/Dataset-Period-Zweig sind zusätzlich explizit an eine alte Non-Bitcoin-Forschungskohorte gebunden. Ein Entfernen der Sperren nur im generischen Validator wäre deshalb kein vollständiger Beleg eines korrekt neu gebundenen Forschungslaufs. Vor einer Übernahme dieses Zweigs müssen allgemeine Instrumentvalidierung, ausdrückliche Kohortenzusammensetzung und neue Identitäts-/Konfigurationsbindung gemeinsam stimmen. Alte Kohorten und Ergebnisse behalten ihre ursprüngliche Bedeutung. Diese Altpfade begründen keine neue globale BTC-Sperre.

Aktueller Produktcode wurde durch diese Untersuchung nicht geändert. Der bereits umgestellte Double-Play-Pfad bleibt bei gemeinsamer Zulassung. Die vollständige BTC-Ausrichtung sämtlicher alten Forschungsanschlüsse wird ausdrücklich nicht als abgeschlossen geführt.

[Kontrollierter Probeausgang](controlled_probe.json), [gebundene Quellen und Tests](receipt.json), [Blueprint Abschnitt 42](../../blueprints/PEAKTRADE_SYSTEM_RECONFIGURATION_BLUEPRINT_2026_11_03.md).
