---
docs_token: DOCS_TOKEN_CURRENT_N1_RISK_AND_QUANTITY_CONSUMPTION_2026_11_09
authority: NONE
runtime_authorization_effect: NONE
---

# Punkt 2: bestehende Risiko- und Mengenconsumer

**496 gemeinsame Fälle PASS, Exit 0, keine Deselektion.**
Der [JSON-Beleg](CURRENT_N1_RISK_AND_QUANTITY_CONSUMPTION_2026_11_09.json)
bindet 1851 Pythonkörper vor/nach dem Lauf, davon
1851 tatsächlich geladen. Loghash:
`a2d2d13c30e3614c0fcd002175ec05804143f811195d1215ba6f2ae19acdc7e8`. Die
[Quellenklärung](../specs/CURRENT_N1_RISK_AND_QUANTITY_CONSUMPTION_V1.md)
führt ursprüngliche Kapitalquelle, Währung, Stopbasis, Mengenrechnung,
Reservation, native Venuegrenzen und spätere POST-Consumer zusammen.

LONG und SHORT durchlaufen den tatsächlichen N1 mit synthetischen Ports.
Originalentscheidung, modellierter Stopverlust, Notional, gespeicherte Menge,
Reservation und endgültiger Envelope stimmen überein. Die Gegenprobe sperrt
Netzwerkverbindungen; es entstehen keine Orders oder positiven Rechte.

Die 25 USDC sind die anfängliche Testgrenze für den ersten Slot. Frank entscheidet
ausdrücklich, wann die Testphase endet. Ein automatischer Übergang ist weder
definiert noch gewünscht. Die vorhandene kapitalabhängige Rechnung liegt bereits
unter dieser zusätzlichen Grenze; mehr Kontokapital hebt sie nicht selbst an.
Eine spätere konkrete Allokationspolicy wird hier nicht erfunden oder aktiviert.

Der erste gemeinsame Lauf enthielt sieben Fehler: einen abgelösten Atlas-/Navigations-
vertrag und sechs durch fremde synthetische Testbeobachtungen gesperrte alte
Accountinputs. Der originale Quellkatalog ersetzt die alten Navigationsasserts;
die Pack-/Manifestprüfung bleibt. Processlokale Capital-/Treasurycaches werden
zwischen unabhängigen Tests geleert, innerhalb jedes Tests bleiben alle
Replaysperren aktiv. Der abschließende gemeinsame Lauf enthält auch Punkt 1 und
die ursprünglichen Ordering-/Content-Gegenfälle. Keine Deselektion oder Änderung
produktiver Regeln beseitigt die Fehler.

Abgeschlossen ist die Prüfung dieser bestehenden Consumer. Produktive statistische
Verlust-/Survivaldefinition, ökonomische Kalibrierung, echte Tagesverlustfortschreibung
und unbegrenzter autonomer Betrieb sind damit nicht nachgewiesen. Der VaR-/Stress-/
Liquiditätspfad bleibt ausdrücklich Offline-Testpolicy. Ausfallkoordination folgt
als dritter Schritt.
