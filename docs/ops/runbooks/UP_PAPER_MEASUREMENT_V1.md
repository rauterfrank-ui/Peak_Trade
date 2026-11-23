# Begrenzter UP-Paper-Messlauf

Der Messlauf verwendet den datierten UP-Future `UP-USD_UM_XPERP-310919`. Die archivierte Paper-Zuweisung lag auf Lane 2. Die neue Session benötigt ihre eigene zur Startzeit gültige Auswahl, die N5-Belegung, den sitzungsbezogenen virtuellen Kontoeröffnungsbeleg und die dazu passende Cap24-Bindung. Die bisherige Session `rang_lane_2_20261123_p01` ist geschlossen. Ihre erneuerte Auswahl endete am 23. November um 09:50:09 UTC.

## Vorbereitung und spätere Auswertung

Der Offline-Befehl erzeugt den Plan auf stdout. Ein Beispiel für eine neue, auf eine Stunde begrenzte Sitzung:

```sh
./scripts/pt scripts/ops/up_paper_measurement_v1.py plan \
  --session up_paper_ws_20261123_p02 --seconds 3600 \
  --parent "$MESSVERZEICHNIS" --slot-config "$NEUES_PAPER_PROFIL"
```

Das Messverzeichnis ist ein bestehender, isolierter Ordner außerhalb des Repos. Der Sessionordner, sein Eingabeordner und der Messordner müssen dort neu sein. Ohne neue Originale bleibt der Plan im Status `AWAITING_SESSION_BOUND_PAPER_SLOT_AND_CAP24`. Eine alte Session-ID, eine abgelaufene Auswahl oder eine fremde Bindung werden abgewiesen. Der gebundene Plan enthält Dauer, Prozessargumente, Datenpfade und die beiden Auswahldigests.

Erst bei einem separat beauftragten Lauf verwendet der Operator denselben Aufruf mit dem Unterbefehl `start`. Dieser prüft die Originale erneut. Er beginnt mit dem öffentlichen Recorder auf demselben Host. Innerhalb von 30 Sekunden müssen beide Abonnements bestätigt sein und ein frischer Markpreis sowie ein aus dem Snapshot aufgebautes Buch vorliegen. Erst dann läuft der begrenzte Paper-Treiber parallel. Der Recorder hat 60 Sekunden mehr Laufzeit. Paper verwendet seine vorhandenen Marktdatenquellen und Schutzgrenzen. Die WebSocket-Aufzeichnung dient dem Vergleich. Der detaillierte Python-Profiler bleibt aus.

Nach Abschluss liest dieser Offline-Aufruf die versiegelten Buchungen, die Bestätigungszeitpunkte und das WebSocket-Protokoll:

```sh
./scripts/pt scripts/ops/up_paper_measurement_v1.py report \
  --run-root "$MESSVERZEICHNIS/up_paper_ws_20261123_p02" \
  --evidence "$MESSVERZEICHNIS/up_paper_ws_20261123_p02-measurement"
```

## Was die 300 ms messen

- Die Hauptkennzahl beginnt beim Börsenzeitstempel des Markpreises, der den ursprünglichen L10-Wechsel ausgelöst hat. Sie endet unmittelbar nach der Rückgabe der bestätigten virtuellen Buchung, einschließlich Accounting-Readback und Nachfolgeepisode. Die Wartezeit eines zurückgestellten Wechsels zählt mit.
- Eine zweite Kennzahl beginnt beim tatsächlich zur Ausführung verwendeten Markpreis. Beide Kennzahlen enthalten einen möglichen Uhrversatz zwischen Börse und Host. Ein späterer Wiederanlauf erzeugt keinen nachträglichen Bestätigungszeitpunkt.
- Für einen passenden WebSocket-Markpreis wird zusätzlich der monotone Abstand vom Empfang bis zur Bestätigung auf demselben Host ausgewiesen. Fehlende zeitlich passende Originale, fremde Hosts und mehrdeutige Markpreiskorrekturen lassen diese Kennzahl offen. Die Auswertung nennt die Anzahl versiegelter Buchungen, messbarer Bestätigungen und Zeitpunkte innerhalb von 300 ms.
- Bei verzögerten Wechseln prüft der Vergleich den ersten beobachteten Zeitpunkt, an dem die ursprüngliche native Wechselmenge Spread, Slippage, ausführbare Tiefe und ADV-Beteiligung erfüllt. Lücken und Sequenzbrüche bleiben im Bericht sichtbar. Ob zu diesem Zeitpunkt auch alle anderen Einstiegsvoraussetzungen erfüllt waren, erfordert deren eigene Originale.

## Vorarbeiten vom 23. November

Bei neun archivierten Wechseln lagen die drei sofort ausführbaren im zweimaligen Offline-Replay nach Wiederverwendung des validierten DDO-Append-Index zwischen 102,09 und 167,77 ms ab Signal. Die sechs verzögerten Fälle hatten 119 Abrufe. Davon waren 102 liquiditätsbedingt gesperrt, elf technisch blockiert und sechs gebucht. Zwischen den historischen Abrufen lagen bis zu 13 Sekunden. Für 38 der 119 Abrufe genügten fünf Stufen auf mindestens einer Buchseite nicht. Der Recorder verwendet deshalb den öffentlichen Kanal `books`; die Auswertung verwendet wie der Paper-Treiber höchstens 50 Stufen je Seite.

Der Shadow-Erstkauf führt die native Sizingmenge und modellierte Kosten zum Slot-Budget-Owner. Für Slot 1 ist der getrennte Swap `UP-USDT-SWAP` vorgesehen. Das archivierte PIEVERSE-Mindestlos auf Slot 4 lag bei 34,80 USDT vor Kosten. OL auf Originalrang 6 hatte einen Mindestgegenwert von 0,320300 USDT. Für den vorbereiteten Ersatz mit maximal 10 USDC einschließlich Kosten fehlen die wirksame N5-Nachfolge und ihre Cap23-/Cap24-Bindung. Der historische Gegencheck mit geöffnetem Vorgänger ergab einen ausstehenden Ersatz. Der Kontrollfall ohne Vorgänger ist getrennt ausgewiesen.

[Historische Prüfergebnisse und Originaldigests](../evidence/UP_PAPER_SHADOW_PREPARATION_20261123.json) · [Offline-Prüfer für die OL-Übergabe](../../../scripts/ops/replay_ol_slot4_handoff_v1.py) · [Messprogramm](../../../scripts/ops/up_paper_measurement_v1.py)
