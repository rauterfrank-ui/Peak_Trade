---
docs_token: DOCS_TOKEN_BTC_DEMO_BOUNDED_SESSION_CLOSE_V1
status: preparation
runtime_authorization_effect: NONE
---

# Slot 3: bestätigter Abschluss nach 60 Minuten

Der Nutzer hat für die begrenzte BTC-Demositzung den Abschluss einer dann
offenen Position mit bestätigter Ausführung gewählt. Diese Vorgabe betrifft
ausschließlich Slot 3. Die vier Paper-/Shadow-Slots behalten ihre eigenen
Laufzeiten und festen Instrumentbindungen einschließlich PIEVERSE.

Die [Sitzungsregistrierung](../../../src/ops/btc_demo_session_control_v1.py)
speichert Start, feste Dauer von 3.600 Sekunden und Operationsbezug im
ursprünglichen [TESTNET-Budgetwriter](../../../src/ops/btc_demo_budget_owner_v3.py).
Sie ist Zeitmetadatum und erteilt keine Start- oder Orderfreigabe.
Sie kann nur vor der ersten Reservierung in einem frischen Writer angelegt
werden. Nach Ablauf sperrt sie weitere Einstiege und Netto-Wechsel.
Die Bestätigung zuvor gesendeter Orders bleibt möglich.

Die [Abschlussvorbereitung](../../../src/ops/btc_demo_session_close_v1.py)
verlangt den ursprünglichen authentifizierten Positionsepisodenbeleg und
das vollständige FUTURES-Kontoinventar. Eine noch ungeklärte Netto-Order
blockiert den Abschluss. Die neue Ursache heißt `BOUNDED_SESSION_CLOSE`;
sie verändert weder Scope noch L10 oder SideState. Ihre Reduce-only-Menge
ist die volle bestätigte native Position am gebundenen BTC-Instrument.

Der [Kostenowner](../../../src/ops/portfolio_capital_reservation_budget_v1/position_close_quote_v1.py)
verbraucht die aktuellen Originalantworten für Kontokonfiguration, privaten
Kontrakt, Gebühren und Orderbuch. Er prüft ausführbare Tiefe, native Lotgröße
und die private lineare USDC-Abrechnung. USD-Marktnotierungen bleiben Preise.
Der Beleg enthält eine geschätzte Gebühr; spätere Zahlungen stammen aus der
bestätigten Venueabrechnung. Er berechnet keine neue Einstiegsmenge.

Die [Sendeübergabe](../../../src/ops/btc_demo_session_close_submit_v1.py)
verlangt eine getrennte signierte TESTNET-Abschlussfreigabe für genau diesen
Envelope und denselben gehaltenen Demo-Signierhandle wie die Kontobelege.
Sie verwendet die ursprünglichen Owner-GO-/Permitbarrieren und den bestehenden
HTTP-Sender. Der Sender prüft unmittelbar vor dem Socket erneut Position,
Frist, Konto, Kostenquellen, Sicherheitszustand und Widerruf. Die neue
Freigabeaktion ist für LIVE unzulässig. Ein ACK oder Timeout hält das Budget;
derselbe Versuch kann nicht erneut gesendet werden.

Die [Reconciliation](../../../src/ops/btc_demo_session_close_reconciliation_v1.py)
verlangt vollständige signierte Order-/Fill-/Positionsabfragen, die genau
gebundene geschlossene Position in der Historie und anschließend ein neues
vollständiges FUTURES-Kontoinventar ohne Position, normale Orders, Algo- oder
Bot-Aufträge. Positionshistorie, Fills, Gebühren, Funding und abgerechneter
PnL müssen sich rechnerisch entsprechen. Fehlende oder widersprüchliche
Belege ändern den Hold nicht.

Bei einer nach Netto-Wechsel eröffneten Position ist deren Eröffnungsgebühr
bereits im vorherigen Netto-Wechsel gebucht. Der Abschluss zieht diese
bereits gebuchte Gebühr aus dem vollständigen Positionsresultat heraus.
Beim ursprünglichen Erstkauf wird die Eröffnungsgebühr erstmals zusammen
mit dem Abschluss gebucht. Das ursprüngliche Budgetjournal speichert
Abschlussbuchung und Holdfreigabe in derselben dauerhaften Revision.
Es entsteht kein zweites Kapital- oder Zahlungsledger.

Der Cold-Read prüft Quellenbytes, Sendebarriere, Historie und Rechnung erneut.
Die Sitzungsbasis summiert das einmalige ursprüngliche Startkapital, die
bestätigten Netto-Wechsel und den bestätigten Schlussdelta. Sie ist keine
Behauptung über den gesamten Kontostand oder eine durch Marktrenditen
ersetzte Kontorendite.

Die [Offline-Regressionen](../../../tests/ops/test_btc_demo_session_close_v1.py)
beginnen mit dem tatsächlichen lokalen Erstkaufsender und signierten
HTTP-Testantworten. Beide Anfangsrichtungen werden nach null, einem und zwei
ursprünglichen Netto-Wechseln geschlossen. ACK und Timeout konvergieren erst
durch unabhängige GET-Bestätigung. Cold-Recovery, späte Bestätigung eines
vor Ablauf gesendeten Wechsels, fehlende Quellen, Teilausführung, offenes
Restinventar, unzureichende Tiefe und später Widerruf werden gesondert geprüft.
Die gemeinsame Regression umfasst 252 bestandene Prüfungen.
Alle Schlüssel sind temporäre Testschlüssel; es wurde keine Venueorder gesendet.

Dieser Baustein startet keine Sitzung. Der 60-Minuten-Host, der Abschluss
einer Sitzung ohne Einstieg, ein eigener Folgeauftrag nach bestätigter
Teilausführung und die gemeinsame Fünferstaffel mit DDO/GVEF sind damit
noch nicht als Betriebsstrecke belegt. Eine ungeklärte oder partielle
Schlussorder bleibt gesperrt und benötigt ihren eigenen Abgleich; sie wird
nicht als abgeschlossener Lauf ausgegeben.
