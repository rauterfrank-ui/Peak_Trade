---
docs_token: DOCS_TOKEN_BTC_DEMO_ENTRY_SUBMIT_V1
status: preparation
runtime_authorization_effect: NONE
---

# Slot 3: ursprünglicher Demo-Erstkauf bis zur bestätigten Position

Die [Demo-Sendeübergabe](../../../src/ops/btc_demo_entry_submit_v1.py) konsumiert
die unveränderte Core-Entscheidung, die einmal finanzierte Slot-3-Reservierung
und ihren ursprünglichen TESTNET-Orderplan. Der bisherige Nachweis legte die
Ausführungsidentität direkt im Writer an. Die Regression beginnt jetzt mit
der tatsächlichen lokalen Sendekette und einem isolierten HTTP-Testserver.

Die Übergabe verlangt eine separat ausgestellte, signierte TESTNET-ENTER-Freigabe,
das ursprüngliche Konto-Inventar sowie denselben bereits gehaltenen
TESTNET-Signierhandle für Mengenabfragen und POST. Kein Schlüssel wird geladen.
Die gebundenen USD-Preise und USDC-Abrechnung bleiben beim ursprünglichen
Monetary-/Kostenowner; eine neue Menge wird nicht berechnet.

Die zwei Mengenabfragen laufen über den bestehenden TESTNET-N1-Vertrag.
Ihre Originalbytes bleiben am Envelope gespeichert. Der ausschließlich für
Echtgeld definierte DataSafety-Live-Binder wird nicht auf Demo-Daten angewendet.
Vor Freigabeverbrauch, vor Signierung und vor der Socketgrenze werden
Originalentscheidung, Cursor, Kosten, Kontobeobachtung, native Mengengrenzen,
Quellenbytes und Freigabe erneut geprüft.

Der bestehende Sendepfad schreibt die Ausführungsidentität im Budgetjournal
und konsumiert das einmalige Permit vor dem Transport. Ein Timeout hält die
Reservierung und sperrt einen erneuten POST. Ein Widerruf oder geänderter Beleg
vor dem Socket beendet ausschließlich den ursprünglichen Transportversuch
als `ABORTED`; die Reservation wird dadurch nicht freigegeben.

Eine ACK eröffnet keine Position. Die anschließenden signierten GET-Belege
erreichen den ursprünglichen Reconciliation- und Episode-Owner. Bestehende
Regressionen prüfen anschließend L10, Netto-Gegenwechsel, Cold-Recovery und
den Rückwechsel in beiden Richtungen mit demselben einmaligen Slotkapital.

169 Offline-Prüfungen bestanden einschließlich des bestehenden Live-Sendejoins.
Es wurden ausschließlich temporäre Testschlüssel und synthetische HTTP-Antworten
verwendet. Es gab keine echte Kontoabfrage, Order oder Slot-Session.

Offen bleiben der begrenzte Abschluss der Demo-Session, der 60-Minuten-Host
sowie die integrierte Startstaffel und DDO-/GVEF-Verarbeitung aller fünf Slots.
Diese Quellreparatur erklärt den Fünferlauf nicht als startbereit. Feste Pins
einschließlich PIEVERSE und das Warten auf gültige Einstiege bleiben bestehen.
