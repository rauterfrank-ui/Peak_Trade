---
docs_token: DOCS_TOKEN_CURRENT_SCOPE_MARK_AND_USDC_MOVEMENT_ADMISSION_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Quellenzeit, absolute Bewegung und USDC-Abrechnung

Fortschreibung über PR 7211 (`9d2ff67b0ccfdc16d9641900a10f00b3c61eac67`).
Der Nutzer beauftragt den PR und Merge dieses geprüften Zwischenstands.
BWP1 bleibt in Bearbeitung; dies ist keine Gesamt- oder Betriebsabnahme.

## Markquelle bis zum Scopeconsumer

Der ursprüngliche Public-WS-Transport abonniert jetzt `mark-price`. Nur dessen
positiver endlicher `markPx` wird zum MarkPriceFact. Ein `tickers.last`, ein
anderes Instrument oder eine fehlende Ereigniszeit ersetzt diesen Preis nicht.
Die Ereigniszeit liegt bei OKX innerhalb der Datenzeile. Die Sequenz führt daher
eigene Uhren je Kanal und Instrument. Gleiche Markzeit mit verändertem Wert ist
eine Korrektur; A → B → A bleibt zulässig. Der Markzweig hält nur den letzten
Snapshot je Stream statt einer ständig wachsenden Menge früherer Mark-IDs.

Der ursprüngliche Runtimeowner normalisiert das gesamte Batch vor der ersten
Factappendierung und veröffentlicht den neuen In-Memory-Cursor nach erfolgreicher
Sequenzpersistenz. Der Sequenzwriter schreibt per temporärer Datei, fsync und
atomarem Replace. Ungültige bestehende Sequenzdateien werden nicht zu einem
leeren Neustart umgedeutet. Die Factappendierung und der Sequenzwriter sind
weiterhin getrennte Speicheroperationen: Das ist keine gemeinsame Transaktion,
kein Exactly-once-Versprechen und kein Nachweis physischen Stromausfalls.

Am ursprünglichen Core-Eingang werden Venuezeit, tatsächliche Capturezeit und
Bewertungszeit getrennt geprüft. Alle drei relevanten Altersdifferenzen müssen
die vorhandene Public-MD-Fünfsekundenregel erfüllen; Zukunft und nichtendliche
Alter sind unzulässig. Das erneute Empfangen einer alten Markzeile macht sie
nicht aktuell. Fehlende Capturezeit wird nicht aus einem Candlezeitpunkt erfunden.

Der Originalcursor kann den Assessmentframe v2 speichern: Markrohbeobachtung,
Capturezeit, Payloadhash und originaler CMC-Digest gehören zusammen. Sein
Quellenhash erreicht den CMC-Kontext und den ursprünglichen Decisionparent.
Cold-Read prüft den damaligen Bezug; der spätere Entryreader prüft die Markzeit
erneut an seiner aktuellen Uhr. Legacyframe v1 bleibt lesbar und ausdrücklich
ohne belegte Quellenzeit. Explizite synthetische Fixtures bleiben synthetisch.
Native GGE-, Scope-, Confirmation- und Double-Play-Formeln sind unverändert.

Auch der Cap24-/Post-Close-Anschluss reicht den ursprünglichen passenden
Lane-Preisbeleg durch. Er prüft native Identität und Preis gegen die Cap24-Bindung;
er ersetzt Capture- und Quellenzeiten nicht durch einen bloßen Sidecar-Zahlenwert.
Explizite synthetische Lanequellen behalten ihre Kennzeichnung. Für genau die
drei betroffenen bereits geschützten äußeren Adapter wird im Policyreader ein
vollständiges, exakt gebundenes Nachfolgebundle geprüft. Alte zugelassene Bundles,
native Corebodies und fremde Policyquellen behalten ihre Grenzen. Ein gewöhnlich
nachgeführter Entwicklungshash allein lässt weder Teilbundle noch andere Bodies zu.

## Absolute Bewegung bei der finalen Menge

Das neue explizite interne Testprofil
[Revision 11](BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V11.json) verlangt den
ursprünglichen typisierten Economic-MD-Input desselben Instruments: 61 finale,
zusammenhängende PT1M-Markpunkte bis zum zuletzt abgeschlossenen Minutenbucket.
Digest, Instrument, Quelle, Finalisierung und Kenntniszeiten werden neu geprüft.
Die ursprüngliche B03-Rechnung liefert separat Volatilität (`ddof=0` der 60
Logreturns) und relative Amplitude `(Maximum−Minimum) ÷ Mittelpunkt`.

Notwendige Zulassungsregel: Die exakt als Bruch berechnete relative Amplitude
mal aktuellem nativen Notional der **final zugelassenen Kontraktmenge** muss
die ursprünglichen tatsächlichen Opening-, Closing- und Fundingkosten dieser
Menge übersteigen. Gleichheit reicht nicht. Die bereits vorhandenen nativen
Kostenowner werden erneut konsumiert; Initialmargin wird nicht als Handelskosten
ausgegeben. Es gibt kein Resizing durch diesen Filter und keine neue Rangfolge.

Historische Amplitude ist weder erreichbarer Kursweg noch erwarteter Gewinn.
Volatilität wird nicht zur Survivalwahrscheinlichkeit oder zu einer neuen frei
gewählten Mindestschwelle. Die lokale RawInput-Übergabe mit Receipt ersetzt keinen
noch fehlenden automatischen Live-Collector und keinen Profitabilitätsnachweis.
Die festen nativen Replay-Survival-/Bruttoedgewerte bleiben ungemessene Inputs.

Die Bindung wird im vorhandenen Sizingzustand v8 und im Originalbudgetwriter
gespeichert. Atomare Reservation, identischer Replay, später Entry und Cold-Read
konsumieren sie. Fehlende oder widersprüchliche Quellen erzeugen keinen partiellen
Hold. Ein Alt-Hold wird nicht nachträglich durch einen neuen Quellenbeleg aufgewertet.

## USDC und USD-X-Perp sind getrennte Bedeutungen

Für den ausschließlich lesend untersuchten aktuellen Account wurden Futures-Modus
(`acctLv=2`), Net-Modus, `settleCcy=USDC` und `autoLoan=false` beobachtet. Beim
Kontrakt `BTC-USD_UM_XPERP-310404` nennt die öffentliche Instrumentliste USD,
die authentifizierte Account-Instrumentliste dagegen USDC als Abrechnungswährung.
Beide liefern einen linearen FUTURES-Kontrakt mit `ctVal=0.0001 BTC`, `ctMult=1`.
Diese Recherchebeobachtungen sind keine aktuellen entscheidungsgebundenen Inputs.
Private Rohantworten, Kontokennungen und Kontostände werden nicht veröffentlicht.

Laut [OKX-Produktdefinition](https://www.okx.com/en-eu/help/faq-on-usd-margined-futures-contracts)
werden Kosten, PnL und Margin in der gewählten Abrechnungswährung berechnet,
bezahlt oder empfangen. Der [API-Vertrag](https://www.okx.com/docs-v5/en/)
definiert den linearen PnL in der Instrumentabrechnungswährung. Der neue begrenzte
Finanzpfad bindet deshalb die authentifizierte Instrumentquelle zusammen mit
Accountconfig, Gebühren und Book an dieselbe Entscheidung. X-Perp-Familie,
Underlying, native Identität, Kontraktwerteinheit und Accountmodus müssen passen.
Eine öffentliche USD-Zeile wird nicht zu einer privaten USDC-Quelle umetikettiert.
Es wird kein externer USD-/USDC-Kurs und keine allgemeine Paritätsregel erzeugt.

Die kanonische öffentliche Instrumentidentität behält den USD-Quotebezug. Bei
leeren Futuresfeldern werden Basis und Quote aus dem gelieferten Underlyingpaar
gelesen. Der äußere Identitätsadapter erkennt X-Perps als datierte FUTURES und
vergleicht die kanonische Identität mit dem genauen nativen Kontrakt. Er macht
daraus keinen SWAP. Der Sizer kann USDC ohne irrelevante USDT-FX-Quelle berechnen.

Nur die neue Testpolicy verlangt USDC als native Settlementwährung beim
ursprünglichen Marginconsumer und im Cold-Read aktiver Holds. Alte Profile bleiben
unverändert. Ein vorhandener USDT-Hold kann auch durch neu gehashte Speicherbytes
nicht als USDC-Verpflichtung zugelassen werden. 25 USDC Notional und 25 USDC
Testverlustzulage je Slot bleiben getrennt; keine automatische Auffüllung.

## Nachweis und Grenzen

Der [quellengebundene Prüfbeleg](../evidence/CURRENT_SCOPE_MARK_AND_USDC_MOVEMENT_ADMISSION_V1_2026-11-09.json)
benennt den endgültigen Testumfang und seine Quellen. Interne simulierte
GETs, Corezyklen, Holds und Wiederaufnahme sind von den echten lesenden
Recherchebeobachtungen getrennt. Ein tatsächlicher Handelsauftrag wird nicht versandt.

Offen bleiben insbesondere die accountwirksame Maintenance-/Liquidationsdeckung,
die vollständige Erfassung dieses FUTURES-Accountscopes durch den bisher
SWAP-bezogenen Host, der automatische echte Produceranschluss des Bewegungsfilters
und der gesamte vorvalidierte Wirtschaftsrahmen. Ungeklärte Ausführung und
vorhandene Holds bleiben beim Originalowner. Eine alte Quelle gibt sie nicht frei.
Der aktuelle Law-Index erhält den neuen Quellhash und die zugehörigen Nachweise.
Sein Navigationseintrag führt den ursprünglichen Cleanup-Nachhash zusätzlich als
`historical_cleanup_after_sha256` weiter; der aktuelle Erwartungshash beschreibt
die nachgeführte Indexdatei. Die ursprüngliche Cleanup-Revision und beide
Freeze-Tags bleiben unverändert. Die Indexfortschreibung erzeugt keine Authority.
Ein fehlender aktueller Mark kann die Coreauswertung bis zu frischen Daten anhalten;
eine jederzeit verfügbare Closeausführung ohne zulässigen Preis wird nicht behauptet.
Der bisherige REST-Indexsymboladapter ist weiterhin auf SWAP zugeschnitten; dieser
Zwischenstand belegt keine vollständige X-Perp-Marktfeed- und Hostintegration.
Die gesonderte Anti-Latenz-Control ist auf später verschoben. Fünf Sekunden sind
eine Frischeobergrenze und keine garantierte Umschaltlatenz. Operative Defaults,
native Coreformeln und beide Freeze-Tags bleiben erhalten.

Siehe [Arbeitspakete und Nutzerentscheidungen](CURRENT_SYSTEM_FIVE_BOUNDED_WORK_PACKAGES_V1.md),
[native Kostendeckung](CURRENT_NATIVE_COST_COVER_V1.md) und
[native Initialmargin](CURRENT_NATIVE_INITIAL_MARGIN_ADMISSION_V1.md).
