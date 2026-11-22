---
docs_token: DOCS_TOKEN_BTC_DEMO_HOST_BUDGET_RECONCILIATION_OFFLINE_V1
authority: NONE
runtime_authorization_effect: NONE
---

# BTC Demo: Budget- und Reconciliation-Anschluss, 22. November 2026

Ausgangsrevision: `f52d52a6e0cd47cbec048adba9e9ff8283f9f693`.
Dieser lokale Entwicklungsstand bearbeitet Franks ausdrücklich beauftragte
BTC-Vorbereitung. Er startet keine Sitzung. Die bisherige Beschränkung „BTC
unverändert“ in älteren Abnahmen bleibt deren historischer Auftragsumfang.

## Nachgewiesene Ursachen

Der [ursprüngliche Budgetwriter](../../../src/ops/portfolio_capital_reservation_budget_v1/attempt_v2.py)
übernimmt die kanonische Börsenidentität aus dem ursprünglichen Kapitalbeleg.
Der [29P-Producer](../../../src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_29p_risk_capital_model_v1.py)
verlangt dafür `okx`. Die Ausführungsumgebung des originalen Venueplans ist
separat `TESTNET`. Der bisherige
[BTC-Consumer](../../../src/ops/btc_demo_lane3_v2.py) verlangte an derselben
Identitätsstelle dagegen den Deploymentnamen `OKX_EEA_DEMO`. Ein tatsächlich
vom ursprünglichen Budgetowner persistierter Versuch scheiterte deshalb am
BTC-Reader. Die Gegenprobe führt den Validator der Ausgangsrevision an einem
mit den Originalbuildern erzeugten synthetischen Store aus.

Die Coverageprüfung akzeptierte außerdem scheinbar gültige Antwortzeilen mit
API-Fehlercode, ungeordnete oder unzulässige Empfangszeiten früherer Reads,
eine fremde Settlementwährung und einen fehlenden Gebühren-Gruppenbezug.
Die ursprüngliche Negativbaseline enthält 19 solche ungebremsten Fälle und
eine erst für den neuen Bericht hinzugefügte Erhaltungskontrolle. Diese eine
Kontrolle ist kein zwanzigster historischer Fehlernachweis.

Beim Filllesen wurden Zwischenantworten mit der letzten Positions-Empfangszeit
versehen. Im neuen Collector bleibt jede tatsächliche Empfangszeit erhalten;
sie ist weiterhin keine unabhängig beglaubigte Venue-Ereigniszeit.

## Gezielter Anschluss und tatsächliche Consumer

Der [Demo-Host](../../../src/ops/btc_demo_budget_reconciliation_host_v1.py)
nimmt ausschließlich den ursprünglichen dauerhaften Budgetowner, dessen
exakte Kontowurzel und dessen ursprüngliche LANE_3-Instrumentbindung an.
Der Consumer liest Sequenz und Head aus dem ursprünglichen Journal unter der
vorhandenen Writersperre. Der unveränderte Originalsnapshot stoppt geschlossene
oder fehlgeschlagene Quellen; der Original-Revisionsreader prüft den Datensatz,
das vorhandene lesende Headgate zusätzlich Kontobindung und tatsächlichen
Disk-Head. Es entsteht kein zweiter Kapitalledger und kein Zulassungstoken.
Versiegelter Budgetowner, Store, Siegel, Durchsetzung und
[Policyprojektion](../../system_atlas/policy_projection.py) bleiben bytegleich
zur Ausgangsrevision. Der zusätzliche Getter im ersten PR-Head wurde nach
Abweisung durch beide ursprünglichen Siegelprüfungen entfernt; keine neue
Prüfsumme und keine neue Siegel-Ausnahme wurden zugelassen.

Coverageaufnahme: ursprüngliche fünf GET-Antworten mit Queries und Empfangszeit
→ Rekonstruktion des Readerberichts und Digestvergleich
→ Frischeprüfung aller Empfangszeiten gegen den vorhandenen Fünfsekundenvertrag
→ typisierter ursprünglicher 29P-Beleg und ursprüngliches Reconciliationgate
→ automatischer Recoveryconsumer des vorhandenen Budgetowners.

Der verfügbare USDC-Kontobetrag begrenzt diesen USDC-Kapitalbeleg. Vor jedem
Versuch wird eine bestehende Zulassung gesperrt; misslungene neue Prüfung lässt
sie gesperrt und erhält Verpflichtungen. Die vorhandene Policy muss den Slot,
höchstens 25 USDC je Einstieg und gleichzeitig reserviertem Slotbetrag sowie
Öffnungs-, Schließungs- und nächste Fundingkosten verlangen. Der Bericht selbst
ist kein Kapitalproducer. Sein Digest bestätigt lokale Konsistenz der geparsten
Antworten, keine unabhängige Herkunft oder vollständigen ursprünglichen HTTP-Bytes.

Ausführungsabgleich: ursprüngliche persistierte V2-Submitidentität
→ exakte konto-, umgebungs-, instrument- und ordergebundene GET-Antworten
→ ursprünglicher Exchange-Reconciliation-Snapshot und Portfoliowahrheit
→ Revisionsvergleich
→ ursprünglicher dauerhafter Reconciliationwriter mit Readback.
Ein identischer Snapshot einschließlich identischem Portfoliobeobachtungsbezug
erzeugt beim Wiederholen keine weitere Budgetrevision. Neue Empfangs- oder
Beobachtungszeiten sind neue Beobachtungen.

Bestätigte, partielle und unklare Ausführungen behalten ihre Kapitalbindung.
Eine bestätigte terminale Stornierung ohne Fill, ohne verbleibende Position
und mit passendem Pending-/Custodynachweis darf der Originalowner freigeben.
Sein bestehender Fillmengen-Unterrand schützt auch nach kaltem Owner-Neustart
vor einer späteren widersprüchlichen Null-Fill-Freigabe.

Die optionale Erstfillübergabe verwendet genau den persistiert abgeglichenen
Antwortbatch. Fremde Revisionen, veränderte Quellen und unbestätigte Ergebnisse
scheitern vor dem Positionswriter. Der bestehende native V2-Adapter prüft
anschließend weiter Menge, Fillanker, Gebühren, Finalstatus, Originalcursor und
G17. Der neue Testumfang belegt diesen kompletten positiven Cursor-/G17-
Publikationsweg für BTC nicht; fehlende Quellen werden nicht durch Testdoubles
als erfolgreiche Veröffentlichung ersetzt.

## Begrenzter GET-/Recovery-Host

Der Supervisor erhält Leseport, Uhr und Pause explizit. Er konstruiert weder
Transport noch Signer. Sein unveränderliches ursprüngliches Zeitfenster endet
nach 3600 Sekunden. Wiedereintritt setzt es nicht zurück; ein gespeicherter
Abschluss bleibt terminal, auch wenn eine STOP-Datei später entfernt wird.
Die Uhr muss innerhalb eines Aufrufs monoton sein. Exklusive Sperre, getrennte
Metadatenwurzel und unveränderliche Beobachtungsdateien verhindern Vermischung
mit den ursprünglichen Lane-/Budgetownern. Fensterende oder STOP beendet die
Beobachtung, ohne offene Orders zu stornieren oder Kapitalbindungen freizugeben.
Ein bereits laufender GET wird dadurch nicht technisch unterbrochen.

Dies ist der GET-/Recovery-Teil eines Hosts. Ein neuer autonomer Entry-,
Netto-Gegenwechsel-, Orderdispatch- oder Wiederaufnahmepfad wird nicht behauptet.
Der bestehende [simulierte Multislot-Host](../../../src/ops/portfolio_capital_reservation_budget_v1/host_v1.py)
behält seine Grenze `INTERNAL_SIMULATED_EXECUTION`; TESTNET wird dafür nicht
in Simulation umbenannt.

## Weiterhin offene fachliche und betriebliche Nachweise

- Native Instrumentidentität bleibt `BTC-USD_UM_XPERP-310328`; die kanonische
  Identität kommt aus dem Originalenvelope. Keine neue Paper-ID wird erfunden.
- Ein beobachteter öffentlicher USDC-USD-Index bewertet die deklarierte
  25-USDC-Größe in USD. Er beweist weder private Margin-/Settlementregeln noch
  eine ausführbare Konvertierung. USD-Preise bleiben USD-Preise.
- Der echte native USD-Sizing-/Kostenanschluss an USDC-Kapital braucht seine
  zulässigen ursprünglichen Instrument-, Margin-, Umrechnungs- und Kostenquellen.
  Die isolierte Ausführungsfixture enthält ausdrücklich synthetische
  USDC-Sizingoperanden und keinen solchen USD-Konversionsnachweis.
- Frische private Konto-, Instrument-, Gebühren- und Collateralbelege, echte
  Originalentscheidung, Reservierung, Permit, Submit und Fill fehlen für den
  vorbereiteten Lauf. Sie werden ohne Betriebsauftrag nicht beschafft.
- Vollständiger autonomer BTC-Handelskreis, positiver Originalcursor-/G17-Join,
  tatsächlicher Wiederanlauf und Hostcrash-/Stromausfallbelege bleiben offen.

Die synthetischen Offlineprüfungen verwenden temporäre Stores und gesperrten
Netzwerk-/Keychainzugriff. Sie belegen den genannten Codeanschluss und seine
Gegenfälle, keinen Demobetrieb und keine vollständige Startbereitschaft.

## Angrenzende Prüffixtures und ursprüngliche Freigabegrenze

Die erweiterte Prüfung zeigte zusätzlich veraltete Baselineinputs in zwei
N1-/Continuous-Testfixturen. Sie nannten `8da476238040545d2c1e5c1bf2e950d4388dba68`,
der unveränderte ursprüngliche Owner-GO-Beleg bindet jedoch
`98976dc93ba5bf7aff3723472be3bb111e020303`. Der originale Validator verweigert
den alten Fixturebezug nachweislich und akzeptiert seinen eigenen festen
Belegbezug. Die synthetischen Positivinputs werden deshalb an diesen festen
Originalbeleg angeglichen; eine Gegenprobe erhält die alte Abweisung.
Dieser SHA bezeichnet den Entscheidungskontext der Fixture, keine aktuelle
Codefreigabe. Produktionskonfiguration, Validator und geschützte Grenzen
werden dafür nicht verändert. Eine frühere Angabe als „current main“ wird
entsprechend nicht fortgeführt.

## Nachfolgende lokale Offlineprüfung auf PR #7381

Die damalige offene positive BTC-Core-/Cursor-/G17-Kette wird in der
[Offlinefortschreibung](BTC_OFFLINE_CORE_CURSOR_G17_CLOSURE_V1.md) mit ihren
tatsächlichen Originalconsumern geprüft. Der vorstehende Bericht behält seinen
historischen Prüfumfang. USD-/USDC-Zulassung und vollständiger autonomer
Demobetrieb sind weiterhin gesondert offen; nichts wurde gestartet.
