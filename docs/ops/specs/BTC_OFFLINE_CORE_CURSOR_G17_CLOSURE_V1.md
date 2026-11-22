---
docs_token: DOCS_TOKEN_BTC_OFFLINE_CORE_CURSOR_G17_CLOSURE_V1
authority: NONE
runtime_authorization_effect: NONE
---

# BTC: Offlineanschluss von Core, Erstfill, Cursor und G17

Prüfbasis: `3674ea13aa27ec98a243f587da3220b4250a5137` (PR #7381).
Datum: 22. November 2026. Dies ist eine lokale Fortschreibung der
[vorherigen Budget-/Reconciliationprüfung](BTC_DEMO_HOST_BUDGET_RECONCILIATION_OFFLINE_V1.md).
Keine Betriebs-, Capture-, Demo-, Paper-, Shadow-, Trainings- oder
Researchsitzung wurde gestartet oder terminiert.

## Belegte Fehler und gezielte Änderungen

Der positive BTC-Pfad erreicht mit synthetischen Originalinputs erstmals den
ursprünglichen C1-/Exit-Publisher und anschließend den originalen
Occupied-Core-Consumer. Dabei traten drei konkrete Fehler auf:

- Dem vorhandenen Research-Readback fehlte der verwendete Import `asdict`.
  Ein gültiger veröffentlichter Erstfill scheiterte deshalb beim Lesen.
- Der native Erstfilladapter verglich Instrument und Seite, jedoch nicht die
  ursprüngliche Submit-Entscheidungs-ID mit der im Originalcursor behaltenen
  Core-Entscheidung. Jetzt müssen Entscheidung, Outcome und ursprünglicher
  finalisierter G17-Bezug vor dem ersten Episoden-/Opening-Schreiben passen.
- Die Wiederholung mit neuer Writer-Sitzung versuchte, den unveränderlichen
  Research-Openingbeleg mit neuer Herkunft zu überschreiben. Sie liest jetzt
  den Originalbeleg zurück und erhält dessen Sitzung, Revision und Zeit.

Der [Offlinehost](../../../src/ops/btc_demo_offline_trading_host_v1.py)
verbindet die vorhandenen Owner über explizite Einzelaufrufe:
ursprüngliche Instrumentbindung und finale Markhistorie → ursprünglicher G17
und Core mit flatem Markcursor → originale V2-Versuchsidentität und
Reconciliation → bestätigter Erstfill → ursprünglicher Exit-/C1-Publisher →
ursprünglicher Occupied-Mark-Consumer mit derselben Positionsepisode.
Reservierung, Versuch und GET-Antworten werden in den Tests ausdrücklich
synthetisch geliefert. Der Host erzeugt sie nicht aus einem USD-Preis.

Die neue explizite Adresse lautet relativ zur isolierten Demowurzel
`testnet-state&#47;LANE_3&#47;cursor&#47;LANE_3`. Sie erfüllt den bestehenden
Occupied-Adressvertrag. Der optionale Adressparameter des vorhandenen
[Entryclocks](../../../src/ops/first_entry_mark_clock_v2.py) benutzt denselben
Originalwriter. Ohne Parameter bleibt dessen bisherige Adresse erhalten;
vorhandene Stores werden weder verschoben noch automatisch übernommen.
Fremde Laneadressen, Symlinks und Adressen außerhalb der isolierten Wurzel
werden abgewiesen.

## Bedeutung, Zeit und Wiederanlauf

Die native Identität bleibt `BTC-USD_UM_XPERP-310328`, die Ausführungsumgebung
`TESTNET`, die Börsenidentität `okx` und das Deployment `OKX_EEA_DEMO`.
Die kanonische Instrumentidentität kommt im Test aus dem ursprünglichen
Universeproducer und gelangt unverändert zu Core, Originaljournal und Episode.
TESTNET wird nicht als simuliertes Accounting umbenannt. Die Core-Aufrufe
verwenden ausdrücklich den bestehenden nichtproduktiven Harness-Kontext.

Entrybestätigung zählt verschiedene Marks. Der ursprüngliche Erstfillpublisher
veröffentlicht danach den finalen C1-Kerzenöffnungszeitpunkt im Occupied-Cursor.
Der spätere Occupied-Scope-Mark behält seinen eigenen Ereigniszeitpunkt und
zählt keine neue C1-Bestätigung. Auch ein neuer G17-Schätzwert verändert nicht
allein diesen Bestätigungscursor. Finale Kerze, Mark, Empfang und Kenntniszeit
bleiben getrennt; der bestehende Mark-Frischevertrag wird konsumiert.

Long und Short erreichen den tatsächlichen Publisher und den tatsächlichen
Occupied-Core. Nach Schließen und Wiederöffnen des ursprünglichen Budgetowners
werden ursprüngliche Identität, Verpflichtung, Episodenquelle und veröffentlichter
Cursor wieder gelesen. Eine neue Writer-Sitzung erzeugt keinen neuen Openingbeleg.
Das belegt einen kalten Handle-/Store-Wiederanlauf, keinen Hostcrash oder
physischen Stromausfall.

Der ursprüngliche G17-Restore stellt Historie wieder her, jedoch keinen fertigen
Schätzwert. Ein dupliziertes Sample behebt das nicht. Erst ein neues verschiedenes
finales PT1M-Sample erreicht wieder die ursprüngliche Materialisierung und den
Occupied-Consumer. Am Erstfill wird fehlendes, kaltes, fremdes oder gegenüber der
Originalentscheidung fortgeschrittenes G17 vor dem Opening-Schreiben abgewiesen.
Die bereits veröffentlichte C1-Quelle darf bei Wiederholung nicht umgedeutet werden.

## USD und USDC bleiben offen, mit wirksamer Sperre

Der ursprüngliche
[Monetary-Normalizer](../../../src/ops/governed_productive_monetary_normalization_v1/normalize_v1.py)
weist native USD-Operanden mit `NORMALIZATION_UNAVAILABLE_FOR_USD` ab. Er besitzt
USDC-Identität und beobachtete USDT-/USDC-Konvertierung, aber keinen zugelassenen
USD-/USDC-Operator. Der neue Monetary-Check erhält die Originalentscheidung und
die geprüften ursprünglichen Coverageantworten, liefert jedoch ausdrücklich
`BLOCKED`, `authority=NONE` und keine kanonischen Sizingoperanden.

Eine private `settleCcy=USDC`-Zeile kann einen separaten finanziellen
USDC-Instrumentpfad beschreiben. Sie ändert die explizite USD-Einheit des
hier zugeführten Core-Preises nicht. Der öffentliche USDC-USD-Index ist ebenfalls
kein Beleg für eine ausführbare Konvertierung oder private Settlementregel.
Weder Parität noch ein Schutzpreis werden erfunden. Bestehende finanzielle
USDC-Consumer und ihre ursprünglichen Zulassungspredikate bleiben unverändert.

Die positive Ausführungsfixture verwendet eigene ausdrücklich synthetische
USDC-Sizingoperanden. Ihr Erfolg schließt den USD-/USDC-Mengen-, Margin-, Kosten-
und Settlementanschluss nicht. Für diesen Anschluss fehlen weiterhin zugelassene
ursprüngliche numerische Quellen samt Konto-, Instrument-, Mengen- und Zeitbezug.

## Umfang und verbleibende Betriebsgrenzen

Die Offlineprüfungen verwenden temporäre Stores, gesperrtes Netzwerk und
gesperrten echten Keychainzugriff. Originalpublisher und Core werden in den
positiven Integrationstests nicht ersetzt. Gegenfälle erhalten Kapitalbindungen
und verhindern neue Episoden beziehungsweise Cursoränderungen. Bestehende
Verpflichtungen sperren einen neuen flaten Einstieg.

Dies schließt den benannten positiven Offline-Core-/Erstfill-/Cursor-/G17-
Anschluss. Ein vollständiger autonomer Demohandel mit frischen privaten Quellen,
finanzieller USD-Zulassung, Permit, tatsächlichem Submit, Nettogegenwechsel,
Buchung und kontinuierlicher Wiederaufnahme bleibt offen. Der neue Host besitzt
keinen Feed, Signer, Order-/Cancelport oder Scheduler; der bisherige Stundenhost
bleibt GET/Recovery. Kein Startkommando und kein T0 werden erzeugt.
Versiegelter Core, Budgetowner, Budgetstore, Policyprojektion und Siegel bleiben
unverändert. Die Nachweise sind keine Gesamtbetriebs- oder Qualitätsabnahme.
