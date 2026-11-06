# Markpreiszeit und gemessenen Empfang am Pending-Eingang binden

Ausgangsrevision: d85947ffe691e62cfed1cf5ab18a188d3dfee4a1. Der vorhandene
Cross-Session-Adapter (Ursprung 29d4ccd52, spätere Zählerdelegation 8de545518)
verknüpfte den Markpreis mit Candle-Öffnungszeit. Sein Sammelresolver erfand
Empfang als Ereigniszeit plus eine Sekunde. Der vorangegangene Replayfix
beseitigte diese Neuerzeugung am Eingang noch nicht.

## Begrenzte Implementierung

Der Wrapper liest Preis und Ereigniszeit derselben einzelnen erfolgreichen,
nativ passend gebundenen Markpreiszeile. ts bleibt die bestehende OKX-Konvention
ganzzahliger Millisekunden; der normalisierte Eingang verwendet Unix-Sekunden.
Candle-Zeit ist kein Ersatz. Fehlende, mehrdeutige, nicht endliche, gebrochene
Millisekunden oder zum lokal gemessenen Empfang zukünftige Zeitangaben führen
zu keiner Pending-Fortschreibung. Das ursprüngliche Beobachtungsobjekt wird
unverändert an den Trading-Aufrufer zurückgegeben; Zähler bleiben delegiert.

Empfang wird unmittelbar nach Rückkehr von inner.poll mit der lokalen UTC-Epoch-
Uhr gemessen. Das ist ausdrücklich der Empfang am Wrapper, nicht der genaue
HTTP-/Socket-Empfang, eine Venue-Snapshotzeit oder eine bewiesene Quellfrische.
Der aufgerufene Sammelresolver verlangt diesen Empfang ausdrücklich und erhält
ihn über Event-Ledger und Replay unverändert. Ungültige Chronologie wird vor
Zustandszugriff abgewiesen. Der vorhandene direkte normalisierte Ingest ist ein
separater API-Pfad und erhält durch diesen Fix keine allgemeine neue Validierung.

## Verifikation und Grenzen

18 neue anfängliche Fälle ergaben vor der Änderung 16 FAIL und zwei bereits
richtige Kontrollen. Davon sind sechs API-Erweiterungs-/Receipt-Fälle vor der
Änderung wegen des damals unbekannten Arguments fehlgeschlagen; das ist kein
separater Nachweis falscher damaliger Wertberechnung. Der echte Wrapper-Fall
belegt dagegen den um 1800 Sekunden falschen Markzeitbezug direkt.

Nachher: 40 PASS im neuen und benachbarten Closure-/Replay-/Zähler-Scope.
Die abschließenden 22 neuen Fälle bestehen einschließlich vier ergänzter Fälle:
echter Wrapper→Sammelresolver→temporäres Ledger sowie erfolglose/mehrdeutige
Markantworten. Insgesamt 44 unterschiedliche Fälle über überlappende Läufe;
40 und 22 werden nicht addiert. XML-Dateien und Vorherquellen sind erhalten.
Kontrollierte injizierte Daten sind keine natürlichen Marktbeobachtungen.

Offen bleiben insbesondere die vorzeitige Bar-Finalisierung, Kenntnis-/Capture-
Zeit, Quellklasse im nachgelagerten Lernrecord, persistierte vollständige Mess-
artefakte und der zusammenhängende Restart-Nachweis. Keine neue Klasse, kein
Messfensterwechsel und keine neue Finalisierungsregel wurden erfunden. Keine
Aussage über Verunreinigung des geschützten originalen Lernledgers. Dessen Hash
bleibt separat geprüft. GAP-0370, U04, echte Daten-/Betriebsnachweise und GitHub-
CI bleiben offen. Keine Netzwerk-, Credential-, Order- oder Dienstaktion.

[Quellhashes und Prüfumfang](receipt.json), [Vorher](before.xml),
[erster Nachherlauf](after.xml), [abschließender neuer Scope](mark_clock_final.xml).
