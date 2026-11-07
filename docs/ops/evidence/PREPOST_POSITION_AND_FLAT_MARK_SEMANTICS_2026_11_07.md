---
docs_token: DOCS_TOKEN_PREPOST_POSITION_AND_FLAT_MARK_SEMANTICS_2026_11_07
authority: NONE
runtime_authorization_effect: NONE
---

# Positionsbeobachtung vor Versand und Marktpreis bei flachem Bestand

Basis: 7a44ea6b395e98a7e000a2c3cd89a744092210b0 nach PR 7190.
Der [JSON-Beleg](PREPOST_POSITION_AND_FLAT_MARK_SEMANTICS_2026_11_07.json)
bindet Quellen, Teststände und die verbliebenen Grenzen. QB02 erhält hier seinen
Positionsquellenschutz. Die ursprüngliche Account-/Envelopebindung und die
vollständige aktuelle Versandzulassung bleiben gesonderte offene Anschlüsse.

## Bedeutung der Position und ihres Marktbezugs

Eine Positionsmenge null bedeutet keinen gehaltenen Bestand. Sie setzt den
aktuellen Marktpreis des gebundenen Futures weder auf null noch außer Kraft.
Der Marktpreis kommt weiterhin aus seinem unabhängigen ursprünglichen
Marktdatenpfad. Der aktuelle Wert des gehaltenen Bestands ist bei Menge null
null; frühere Gebühren, Funding, Cash und verbleibende Reservationspflichten
werden dadurch nicht gelöscht. Flat ist kein fremder Holdrelease.

Der [OKX-Vertrag](https://www.okx.com/docs-v5/en/) unterscheidet bei Positionen
net mit vorzeichenbehafteter Menge und getrennte positive long-/short-Beine.
Nullzeilen können existieren, ohne einen gehaltenen Bestand darzustellen.
Gegenläufige offene Hedge-Beine dürfen deshalb nicht zu FLAT saldiert werden.
Nur Mengen desselben gebundenen Instruments werden auf Identität verglichen;
fremde Instrumentmengen werden nicht addiert oder in dessen Kontrakte umgerechnet.

Ein instrumentbezogener Positionsread trägt außerdem weniger Information als
der bestehende kontoweite Read. Die beiden Aufnahmen liegen zeitlich auseinander.
Unterschiede können eine echte zwischenzeitliche Änderung bedeuten; sie sind
kein automatischer Nachweis eines fehlerhaften Producers. Für diesen neuen
Entry reicht ein solcher ungeklärter Übergang nicht als stabile Admission.

## Ursprünglicher Weg und gezielter Positionsanschluss

Die bestehende Vorversandfunktion holt neun gemeinsame Fetchgruppen und danach
eine instrumentbezogene Positionsantwort. Am Basisstand nutzt der zweite Read
die cachebare Snapshotvorgabe. Sein Consumer prüft primär get_performed und
verwendet den allgemeinen Positionsdecoder. Fehlercode plus leere Datenliste,
alte/fremde Aufnahme oder eine nicht lesbare Menge können dadurch FLAT ergeben.
Eine bereits offene gebundene Position wird außerdem zum positiven
Frischegesamtausgang zugelassen; eine fremde Position im globalen Read geht in
diesem Vergleich verloren. Der ursprüngliche unmittelbare Freshness-Validator
stammt aus der bereits rekonstruierten Revision 093b481458c86af5fa8a5105d202935fde30c521
zu PR 6931. Das ist nicht die später separat entstandene historische Pflichtzulassung.

Der Anschluss behält dieselben zehn Reads und denselben Ressourcenowner:

1. Der originale Collector transportiert seine tatsächlich aufgenommenen,
   abgetrennten Ergebnisse zum Consumer. Er erzeugt kein neues Portfoliobuch.
2. Der zweite Positionsread fordert nun ebenfalls den ursprünglichen
   entscheidungsgebundenen Snapshotmodus an. Exakter Endpoint, GET-Methode,
   Auth-/HTTP-/Venueerfolg, Decision-ID, ursprüngliche Aufnahmezeit und
   DataSafety-Predicate müssen beim tatsächlichen Consumer passen.
3. Nach dem letzten Read wird das ursprüngliche Aufnahmealter aller neun
   gemeinsamen Ergebnisse erneut geprüft. Der zehnte Read erneuert keine Uhr
   und erzeugt keine neue gemeinsame Planverfallsfrist. Die separate originale
   DataSafety-Conjunction wird ausdrücklich konsumiert.
4. Der lokale Positionsdecoder bewahrt Instrument, Bein, Marginmodus und
   Währungsidentität. Fehlende, nicht endliche, widersprüchliche oder doppelte
   Zeilen bleiben ungeklärt. Der allgemeine Decoder und Core bleiben unverändert.
5. Der Consumer vergleicht die offene gebundene Position aus globalem und scoped
   Read. Unterschiedliche Aufnahmen sperren als geändert/ungeklärt. Bei zwei
   frischen, vereinbaren Aufnahmen bleibt eine offene Position ein frischer
   gültiger Zustand, ist aber kein neuer Entry. Eine fremde offene Position
   sperrt unter dem bestehenden MAX_POSITIONS_EFFECTIVE=1.
6. Echte leere oder gültige Nullzeilen liefern weiter FLAT. Nur der
   positionsbezogene Öffnungsanteil ist dann bestanden. Reduce-only/Close
   benötigt seinen eigenen ursprünglichen Positions-/Mengenowner und wird
   durch diesen Öffnungsconsumer nicht freigegeben.
7. Der Rückgabebeleg trennt Frische, Vereinbarkeit und neue Entry-Zulässigkeit
   und bindet die beiden Quellen an den exakten Envelopedigest. Der ursprüngliche
   aufrufende POST-Owner erhält den konkreten Grund vor dauerhaftem GO-Consume
   und Sendaufruf zurück. Die bestehende Pre-Live-Prüfung erzeugt vorher bereits
   einen temporären In-Memory-Permit; hier wird keine pauschale Abwesenheit
   jeglicher Permiterzeugung behauptet.

Der neue Beleg ist PREPOST_FRESHNESS_AND_NEW_ENTRY_POSITION_ONLY.
account_identity_binding_status=NOT_ASSESSED kennzeichnet die hier nicht geprüfte
ursprüngliche Konto-/Orderbindung. Dieses Label ist kein zusätzlicher wirksamer
Account-Sperrconsumer. Der alte Feldname
all_required_pre_post_gates_pass bleibt für den vorhandenen Caller bestehen,
ist aber kein Nachweis einer vollständigen Risiko-/Safety-/Kapitalzulassung.
Insbesondere ist eine frische Accountaufnahme nicht gleichbedeutend mit der
Herkunft dieses Envelopes aus genau diesem Konto.

## Preisquelle bis zur Anzeige bei weiter flachem Bestand

Der unabhängige originale Public-MD-Adapter und der ausgewählte OHLCV-Producer
liefern live_mark_price als Dezimaltext. Der Greenfield-Consumer erwartet am
Basisstand dagegen ein Objekt. Deshalb erscheint dort der Kerzenschluss statt
des tatsächlich gelieferten Live-Marks. Das betrifft die Anzeige auch bei
weiter flacher Position; es ist keine neue Positions- oder Handelsrechnung.

Der Consumer übernimmt jetzt das originale skalare Preisformat und bewahrt
die ältere Objektform als Eingangskompatibilität. Er akzeptiert nur positive
endliche Preise. Er verändert keine OHLCV-Geometrie und leitet keinen aktuellen
Markpreis aus einer privaten Nullpositionszeile ab.

Die Ausgabe und der bestehende Browserconsumer unterscheiden MARK_PRICE,
CANDLE_CLOSE und UNAVAILABLE. Der angezeigte Preis trägt seinen eigenen
ursprünglichen Ereignis-/Aufnahmezeitbezug und eine eigene Frischebewertung
nach dem vorhandenen reference_mark_price-Vertrag. Frische Candles machen
keinen alten Mark frisch. Fehlende/fehlerhafte Markquelle bleibt unbekannt;
ein noch vorhandener Kerzenschluss wird sichtbar als Kerzenschluss bezeichnet.
Eine alte Zahl wird nicht durch die aktuelle Browserabfrage erneuert.

Der kanonische API-Aggregator bewertet die Quellen erst nach deren Aufnahme
beziehungsweise Load. Sonst kann die gerade empfangene Quelle gegenüber dem
früher festgehaltenen Startzeitpunkt scheinbar in der Zukunft liegen. Die
Quellenzeiten werden dabei nicht überschrieben. Die Marktprojektion bleibt
außerhalb des bestehenden Caches für den übrigen Systemzustand. Drei Polls
zeigen deshalb veränderte Live-Marks bei unverändertem synthetischem Flat-
Systemzustand. Der tatsächliche Browsercode zeigt zugehörige Quelle und Frische.

Die ursprüngliche flache Accounting-Session behält bei mark_to_market ebenfalls
den neuen Mark, während Notional und Positionsbestand null bleiben. Ihr
Accountingkernel und die Core-Marktcontextbildung werden nicht geändert.
Das ist ein gebundener Offlinebeleg, kein beobachteter natürlicher Dauerbetrieb.

## Prüfung und verbleibender Umfang

Die finalen Prüfzahlen und unveränderten Source-/Testhashes stehen im JSON.
23 gezielte Gegenfälle scheitern mit den beiden exakten Originalproduktmodulen;
sie erfassen die bisherigen Positionslücken, den ungebundenen letzten Read und
den ursprünglichen Caller vor einem verbotenen GO-Consume. Netzwerk ist dabei
gesperrt; die letzte Wirkung ist eine ausdrücklich verbotene Testfunktion.

Die breiteren Originalmodulvergleiche reproduzieren zehn bestehende Fehler.
Drei stammen aus nicht mehr passenden Testportsignaturen und fehlenden
Aufnahme-/DataSafetyfeldern. Diese Ports tragen jetzt den originalen Vertrag;
ein alter kanonischer Instrumentplatzhalter wird zur tatsächlich behaupteten
nativen Wire-ID korrigiert. Die bisherigen Negativassertionen bleiben erhalten.
Sieben andere Altverträge der Collector-/Account-Closeout-Suiten bleiben offen,
darunter veraltete Runbook-/Blockerannahmen und die UID-Typerwartung. Sie werden
nicht durch einen neuen Dokumentchecker oder einzelne PASS-Fälle geschlossen.

Die Browseränderung besitzt zusätzlich eine exakte Entwicklungsbindung für
genau die bestehende Preis-Anzeigedatei. Andere statische Dateien bleiben
außerhalb dieser Akzeptanz; Negativfälle prüfen fremde Pfade und veränderte
Digests. Die fixierten Kataloge, Originalpolicyobjekte und numerischen
Frischegrenzen bleiben erhalten.

Weiter offen sind ursprüngliche Account-/Budget-/Reservations-/Executionbindung
bis zum späteren Sendconsumer, Pending-Order-Custody, erneute Mengen-/Risiko-/
Safetyadmission, Altplan-Gültigkeit, persistente Wiederaufnahme und das
fortlaufende Hostmandat. Weder ein frischer Mark noch FLAT noch dieser lokale
Positionsbeleg hebt eine Sperre auf oder erteilt eine Orderfreigabe.
