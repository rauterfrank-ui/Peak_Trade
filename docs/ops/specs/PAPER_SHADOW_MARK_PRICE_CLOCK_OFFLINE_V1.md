---
docs_token: DOCS_TOKEN_PAPER_SHADOW_MARK_PRICE_CLOCK_OFFLINE_V1
status: active
scope: Offline diagnosis of archived Paper and Shadow observations; no operating authorization
---

# Paper/Shadow: Markpreis, Zeitpfad und IRYS-Originalauswertung

## Quellen und Aussagegrenzen

Die Untersuchung vom 22.11.2026 bindet den vorhandenen vierteiligen Laufbestand
`20261122T105506Z` an Repository-Revision
`b89da7f13e0ff2aa109b6b9fb8412af115f850d4`. Die getrennte lokale Auswertung liegt
im Arbeitsordner Runvorbereitung unter `2026-11-22-paper-shadow-offline-mark-clock`.
Dort stehen das reine Leseskript, der strukturierte Bericht und ein Vergleich
der SHA256-Werte aller 33.014 gelesenen Originaldateien vor/nach der Auswertung.
Die Klartext-Confirm-Datei wird nicht gelesen. Es wurden keine neuen Markt-,
Paper-, Shadow-, Testnet-, Live-, Trainings- oder Forschungsläufe gestartet.
BTC/Testnet und die ursprünglichen Archive bleiben unverändert.

Diese Diagnose ändert keine Auswahl, Strategie, Tradingparameter, Zeitgrenze,
Fundingperiode, Budgetgrenze oder Freigabe. Ein positiver Offline-Regressionstest
ist kein nachgeholter Betriebsnachweis. Der ursprüngliche SOPH-Abbruch bleibt
ABORT und unvollständig.

## SOPH: gleicher Markpreis, fehlerhafte Preisbasis-Rekonstruktion

Für alle 137 archivierten Zyklen stimmt der numerische Markpreis zwischen
Originalantwort, Marktsequenz, tatsächlich vorbereitetem Core-Eingang und
Zykluspreisbasis überein. Auch die Bid-/Ask-Werte des ursprünglichen öffentlichen
Orderbuchs erreichen den tatsächlichen Core-Eingang. Die jeweiligen DDO-Inputs
tragen denselben ursprünglichen Kontextbezug; das ist kein zusätzlicher Beweis
eines vollständigen Vorentscheidungszustands im DDO-Envelope.

Der seit dem Kartenanschluss in Commit
`ff101dc3e39e4eb0c992167c34a73e98cd50ad14` verwendete Preisbasisbuilder erhält
echte Buchquotes. Der Archivprüfer rekonstruierte dagegen eine zusammengefallene
Bid-/Ask-Basis am Markpreis. Der Referenzdigest stimmt in allen 137 Fällen,
die vollständige Basis jedoch nicht: Ask, Spread und Bid-/Ask-Policy weichen
137-mal ab; der Bid weicht 134-mal ab. Hinzu kommen zwei falsche Quelllabels:
Mark wird als `last` bezeichnet, öffentliche Buchquotes als Tickerquotes.

Die Korrektur betrifft die ursprünglichen Schnittstellen:

- [Sessionwriter](../../../src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/session_runtime_v1.py)
  übergibt das normalisierte Feld `markPx` ausdrücklich. Die versiegelte
  Marktsequenz erhält die tatsächlich verwendeten Buchquotes mit Endpoint,
  Original-Responsehash sowie Event- und Empfangszeit.
- [Preisbasisbuilder](../../../src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2/market_data_price_basis_v2.py)
  unterscheidet ausdrücklich öffentliche Buchquotes und Tickerquotes. Der
  generische Tickerdefault bleibt erhalten.
- [Archivprüfer](../../../src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/bundle_verifier_v1.py)
  rekonstruiert aus den archivierten Originalinputs dieselbe Basis. Preisfeld,
  Quote, Policy, Digest und vollständige Basis müssen passen. Fehlende,
  veränderte, nicht endliche oder erst nach der Entscheidung verfügbare Quotes
  werden nicht durch heutige Daten ersetzt.

Die Bindung schützt lokale Writer-/Archivkonsistenz; sie ist keine unabhängige
Börsenattestierung. Historische mislabeled oder unvollständige Belege werden
nicht umgeschrieben oder nachträglich zu PASS erklärt. Die unabhängige SOPH-
Sperre wegen ungeklärtem Kapital-/Risikokontext bleibt offen.

## Gemeinsamer Zeitpfad: zulässige Abweisung, fehlende Capturequittungen

Die drei Paper-Läufe verwerfen zusammen 154 Captures: 131 mit G17/C1-Abweichung
und 23 durch Fundingprüfung. Unter den G17/C1-Abweisungen liegt die letzte finale
Mark-Minute 35-mal um 60 Sekunden jünger als C1 und 29-mal um 60 Sekunden älter; 67-mal sind
die Minuten gleich, aber beim späteren aktuellen Mark bereits zu alt.
Insbesondere liefern die getrennten Endpoints nicht durchgehend denselben
Finalisierungsstand. Am Fundingwechsel erscheinen sowohl abgelaufene Perioden
als auch Antworten mit identischem vorherigem und aktuellem Fundingzeitpunkt.
Diese Inputs erfüllen die ursprünglichen Zeitverträge nicht. Ein Abschneiden
der Reihen, ein Rückdatieren oder eine großzügigere Altersgrenze wäre keine
belegte Reparatur.

SOPH protokolliert vor seinem Abbruch G17/C1-Abweisungen. Der Sicherheitsowner
beendet den Lauf bei einer Datenlücke von 13,845 Sekunden. Aus dieser lokalen
Abweisung folgt kein unabhängiger Nachweis eines Börsen- oder Internetausfalls.
Die Quittungen verworfener SOPH-Kartencaptures fehlen im historischen Bestand;
die genaue Abruf-/Ankunftschronologie ist deshalb nicht nachträglich beweisbar.

Auch bei allen 154 verworfenen Paper-Captures fehlen die ursprünglichen
Empfangsquittungen, obwohl die Rohantworten bereits geschrieben wurden: Die
Quittungspublikation lag hinter dem fehlgeschlagenen Admissionaufruf.
Die [gemeinsame Retention](../../../src/ops/bounded_peaktrade_system_composition_v1/paper_market_liquidity_v1.py)
schreibt künftig im endgültigen Captureabschluss die Originalquittungen auch
bei Abweisung oder teilweisem Transportabbruch. Der ursprüngliche
[Paper-Eingang](../../../scripts/ops/run_zkp_lane1_paper_v1.py) und der
[SOPH-Kartenabruf](../../../src/ops/instrument_card_stream_v1.py) verwenden
denselben Writer. SOPH hält diese Captures neben dem versiegelten Sitzungsarchiv.
Admissionfehler bleiben Fehler; fehlende historische Empfangszeiten bleiben
fehlend. Wiederholungen oder zweite Netzwerkversuche werden nicht eingeführt.

## IRYS: Entscheidung, Ausführung und Modellwirtschaftlichkeit

Der unveränderte ursprüngliche
[Episodenleser](../../../src/ops/bounded_peaktrade_system_composition_v1/xperp_paper_episode_outcome_v1.py)
bestätigt alle 15 geschlossenen Positionsepisoden einschließlich ursprünglichem
Entscheidungscursor, Instrument, Gebührenzuordnung und Accounting-Replay.
Der Erstfill eröffnet 12 native Kontrakte SHORT. Jeder der 15 Nettogegenwechsel
schließt 12 Kontrakte und eröffnet 12 in Gegenrichtung durch genau einen Fill
über 24 Kontrakte. Das sind 16 Fills, 15 geschlossene Episoden und eine weiterhin
offene simulierte Longposition über 12 Kontrakte; die gleichzeitige
Positionsgrenze ist keine Begrenzung auf einen Handelszyklus.

Jede Schließung ist mit der ursprünglichen Strategieinvalidation und ihrem
L10-Scopewechsel verbunden. Die vollständige unabhängige Wiederberechnung der
damaligen Entscheidung einschließlich aller Vorzustände ist damit nicht belegt.
Ein Scopewechsel wird nicht mit einem Fill gleichgesetzt. Die belegten
Entscheidung-zu-Fill-Abstände reichen von 0,0517 bis 30,0466 Sekunden. Fünf
Gegenwechselversuche wurden wegen abgelaufener Marktdaten abgewiesen. Die
vorhandenen Belege begründen deshalb kein pauschales Urteil über Latenzgüte.

Die Eröffnungsnotionale der geschlossenen Episoden liegen bei 22,752 bis
23,676 USD. Die größere Gesamtmenge eines Nettogegenwechsels enthält auch das
Schließen der Vorgängerposition; sie ist nicht allein eine neue Kapitalaufnahme.
USDC-Zuteilung, USD-Preise und der ursprüngliche öffentliche Umrechnungseingang
bleiben getrennte Größen. Ein gemeinsam über alle Prozesse geführtes produktives
Budget wird nicht behauptet.

Die 15 geschlossenen Episoden liefern im ursprünglichen USD-Papermodell:

- realisiertes PnL aus Fillpreisen: +1,04400 USD;
- zugeordnete Gebühren: 0,347418 USD;
- modelliertes Funding: −0,010179687713216976 USD;
- Netto: +0,686402312286783024 USD; sieben positive, acht negative Episoden.

Die zugeordneten 0,69600 USD Slippage sind bereits in den Fillpreisen enthalten
und werden nicht erneut abgezogen. Funding verwendet die öffentliche
realisierte Rate und den unmittelbar vorherigen finalen Mark-Minutenclose;
dies ersetzt keine private Kontobuchung oder den privaten Assessment-Mark.

Zum letzten Fill am 22.11.2026 um 13:40:15,849 MEZ beträgt der gebuchte
virtuelle Equitystand 25,638798312286783024 USD. Der Unterschied zum Netto der
geschlossenen Episoden ist exakt durch die noch offene Position erklärt:
0,011604 USD Eröffnungsgebühr und −0,03600 USD unrealisierte Bewertung.
Dieser Buchungsstand ist keine neu berechnete Bewertung zum späteren Fensterende,
kein Kontogewinn, kein unabhängiger Strategievalidierungsnachweis und keine
Freigabe für produktive Anwendung.

## Offline-Verifikation

[Gezielte Regressionen](../../../tests/ops/test_paper_shadow_mark_clock_offline_v1.py)
prüfen abgewiesene und teilweise Captures an beiden Originalports, unveränderte
G17/C1-/Fundinggates sowie Preis-, Quote-, Label- und Zeitmanipulationen.
Der vorhandene vollständige SOPH-Kartentest in
[Instrument-Card-Tests](../../../tests/ops/test_instrument_card_stream_v1.py)
prüft jetzt zusätzlich den strengen DDO-Readback mit echten Fixture-Buchquotes
am tatsächlichen Core-Consumer. Alle Daten dieser Tests sind lokal und
synthetisch; sie starten keine Betriebssitzung und erzeugen keine Orders.
