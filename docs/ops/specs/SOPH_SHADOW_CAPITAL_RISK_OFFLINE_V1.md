---
docs_token: DOCS_TOKEN_SOPH_SHADOW_CAPITAL_RISK_OFFLINE_V1
authority: NONE
runtime_authorization_effect: NONE
---

# SOPH: ursprüngliche Kapital-/Risikokette im analytischen Shadow-Pfad

Ausgangsrevision ist 9e6fd12a2872a61540701ef1439808502de8acfe.
Der unveränderte vierteilige Paper-/Shadow-Versuch vom 22.11.2026 enthält für
SOPH 137 Entscheidungen, jeweils no_action, ohne analytischen Fill. In allen
137 gespeicherten Core-Eingängen fehlt der finanzielle Boundary-Record,
obwohl das Kartenbudget bereits BOUND und aus dem ursprünglichen virtuellen
Portfolio gelesen ist. Der ursprüngliche Risikoanschluss ergänzt den Grund
CAPITAL_RISK_CONTEXT_UNRESOLVED auch bei nicht handelnden Entscheidungen.
Damit ist die fehlende Übergabe belegt; daraus folgt kein unterdrückter Entry
und keine Erklärung sämtlicher ausgebliebener Trades. Der archivierte Abbruch
wegen DATA_GAP bleibt ein gesonderter damaliger Befund.

## Ursprüngliche Owner und belegte Einheiten

Der [SOPH-Anschluss](../../../src/ops/soph_shadow_capital_risk_binding_v1.py)
liest das Budget des bestehenden shadow_budget_source_v1, dessen Policy und
den tatsächlichen Zustand des IdempotentPortfolioV2. Identität, Lane,
USDC-Währung, Zeit, Quelldigest, Policy, Originalportfolio, markierte Equity
und FX müssen zusammenpassen. Fremde oder nachträglich veränderte Zustände
erzeugen keine aktuelle finanzielle Eingabe. Es entsteht weder ein Budgethold
noch privates Kontowissen; reserved_amount bleibt unbekannt.

USDC-Grenzen werden mit dem tatsächlich gebundenen USDC/USD-Index in USD
umgerechnet. Die einmalige Modellallokation wird nicht erneut initialisiert.
Verfügbares Kapital bleibt durch markiertes Modellkapital und die ursprünglichen
25-USDC-Grenzen begrenzt. Der verwendete Verlustwert ist ebenfalls auf
Modellkapital und die ausdrückliche Slot-Testverlustgrenze begrenzt. Das alte
daily_loss_remaining_budget-Feld des Offlineadapters trägt hier ausdrücklich
diese begrenzte Testmodell-Hülle, wie der vorhandene Paper-Sizinganschluss.
Die Herkunft ist im Record als BOUNDED_SHADOW_TEST_LOSS_ENVELOPE_NOT_ACCOUNT_DAILY_BALANCE
markiert. Es ist kein verbleibendes Tagesverlustbudget eines privaten Kontos
und keine produktive Risikofreigabe. Erschöpftes Modellkapital wird abgewiesen.

Der ursprüngliche kanonische Intent bezeichnet seine Menge als CONTRACTS.
Deshalb erreichen native Losgröße, Mindest-/Maximalmenge und Kontraktmultiplikator
den ursprünglichen Sizing-Owner unverändert. Das analytische Portfolio bucht
dagegen Basismengen. Seine tatsächlich gebuchte Position wird für den
Core-Kontext in Kontrakte umgerechnet; ihr USD-Exposure bleibt dasselbe.
Der ursprüngliche Mapper erhält ebenfalls Kontraktmengen, damit sein Exit-Clamp
dieselben Einheiten vergleicht. Erst der Portfolio-Consumer multipliziert
die gemappte Menge mit dem nativen Kontraktwert. Eine Kontraktmenge wird weder
als Basismenge gebucht noch ein Intent nachträglich als Venue-Order freigegeben.
Die getrennten Einheiten und Umrechnungen stehen in den Eingangs- und Zyklusbelegen.

Der [bestehende Boundary-Record](../../../src/trading/master_v2/capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0.py)
besitzt dafür ein optionales typisiertes In-Memory-Metadatenfeld.
Der [ursprüngliche dynamische Kontextbuilder](../../../src/trading/master_v2/mv2_offline_boundary_dynamic_price_context_v1.py)
übernimmt diese expliziten linearen Futuresbedingungen. Ein falscher Typ,
ein fremdes Instrument oder ein anderer Markttyp wird abgewiesen. Ältere
Aufrufer ohne dieses Feld behalten ihren vorhandenen Pfad; der Dateiparser
bekommt keine neue implizite Metadatenquelle. Der geschützte integrierte
Replaykörper und die Risikoformel bleiben unverändert. Mark und Schutzstop
stammen weiterhin aus seinem gebundenen Mark und seinem tatsächlichen
DynamicScope-Abstand. Der Modus bleibt OFFLINE_ALGEBRA.

## Verbrauch und zusätzliches Kostenveto

Die [vorhandene Bridge](../../../src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2/hardening_cycle_bridge_v2.py)
übergibt den Record und die tatsächliche Positionsbeobachtung vor Core-Aufruf,
Kartenbeobachtung und DDO-Erfassung. Die originale Entscheidung, Safety,
Mengenrechnung und der kanonische Intent bleiben deren jeweilige Ownerausgänge.

Vor zusätzlicher analytischer Exposition werden die exakte Menge und das
native Buch mit dem bestehenden Mengenprüfer erneut geprüft. Zusätzlich
müssen Notional plus Öffnungs-/Schließkosten und eine Vorsorge für den nächsten
Fundingtermin in die begrenzte Basis passen. Der Stopverlust plus diese Kosten
muss in die begrenzte Testverlust-Hülle passen. Der Abstand stammt aus der
tatsächlichen originalen Pre-Sizing-Risikoprüfung. Eine unvereinbare Menge wird
gehalten; weder Nachsizing noch ein kleinerer Ersatzintent wird erzeugt.

Die Kosten stammen aus den tatsächlichen unveränderten Modellparametern:
2 bps Gebühren und 1 bp Slippage. Die Schließkostenvorsorge verwendet einen
konservativen Preisbezug aus Mark, ursprünglichem Risikoabstand und aktuellem
Buch; sie ist keine zukünftige Ausführungszusage. Die Fundingvorsorge verwendet
die native belastende Ratenober-/untergrenze. Das ursprüngliche Shadow-Modell
bucht weiterhin seine bestehende Fundingrate null. Eine Vorsorge wird nicht
nachträglich als gebuchte Fundingzahlung ausgegeben und eine analytische
Ausführung nicht als native Buchausführung dargestellt.

Der [Wallclock-Host](../../../src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/session_runtime_v1.py)
übergibt seine vorhandene Uhr bis zum Verbraucher. Vor einem neuen Fill werden
Quellenfrische, Fundinggrenze und Portfolio-/Budgetreadback nach dem Core-Aufruf
nochmals geprüft. Eine Verzögerung erzeugt keine neue Aufnahme oder Freigabe.
Null freies Neueinstiegskapital bei bestehender Position sperrt keinen
ursprünglichen Reduktions-/Exitauftrag. Der eigene zusätzliche Neueinstiegscheck
wird für reine Reduktionen nicht verwendet. Eine Exitgarantie bei tatsächlich
erschöpftem/ungültigem Modellkapital wird ausdrücklich nicht behauptet.

## Nachweise und verbleibende Grenzen

Die [SOPH-Gegenprüfungen](../../../tests/ops/test_soph_shadow_capital_risk_binding_v1.py)
verfolgen die numerische Mengenänderung durch Original-Sizing und Original-Intent
bei FX 0,8/1/2, native Grenzen, die Portfolio-Projektion, echte offene Mengen,
Kostenüberschreitung und fehlerhafte Quellen. Diese positiven Mengenfälle sind
ausdrückliche Mechanismus-Fixtures; sie belegen keinen natürlich erreichten
Full-Core-Entry. Die [bestehende Host-Integration](../../../tests/ops/test_instrument_card_stream_v1.py)
prüft am vollständigen Offline-Host mit Testuhr den tatsächlich verbrauchten
Finanzkontext, gespeicherte Eingänge und die strenge ursprüngliche DDO-Rücklese.

Der erweiterte Ownerlauf ergibt 329 bestandene Prüfungen und einen offenen
historischen Dokumentverweisfehler:
[test_core_logic_change_is_adjudicated_honestly](../../../tests/ops/test_hardening_v2_scope_direction_overlay_generator_inert_v1.py)
erwartet einen nicht mehr enthaltenen Abschnitt des Master-Runbooks. Test und
Runbook sind bytegleich mit der Ausgangsrevision; der Abschnitt fehlt bereits
dort. Die tatsächlichen SideState-/Scope-Projektionsfälle bestehen. Dieser
Altfehler bleibt ausdrücklich offen; weder der fixierte Runbookbestand noch
die bestehende Prüferwartung werden für einen grünen Gesamtstatus geändert.

Der [Prüfbeleg](../evidence/SOPH_SHADOW_CAPITAL_RISK_OFFLINE_2026_11_22.json)
bindet Quellen, Prüfungen und die lesende Prüfung aller 137 Originalzustände.
Historische Entscheidungen und Archive werden nicht umgeschrieben. Ein
bestandener Anschluss belegt keine aktuelle Betriebsfortsetzung, natürliche
Handelsentscheidung, wirtschaftliche Qualität oder Account-/Orderzulassung.
Kein Betriebsversuch wurde gestartet; BTC/Testnet und Freeze-Referenzen bleiben
unverändert. Scope-/SideState-, Reserve-, Permit- und Learningowner behalten ihre
eigenen Übergänge.

## Kartenfreigabe und Positionsführung auf Basis von PR 7385

Die analytische Vorprüfung verwendet das freie Budget der einzelnen Karte. Sie prüft für BUY und SELL das Mindestlos gegen Budget, Markpreis, Kontraktwert, natives Buch und Marktteilnahme. Die Karte weist zusätzlich aus, ob die gesamte nominale Budgetkapazität vor Kosten ins Buch passt. Erst das ursprüngliche Risiko-Sizing bestimmt die konkrete Intentmenge. Eine wartende Karte liefert keine Handelsentscheidung. Die vorhandenen Paper- und Shadow-Hosts lesen ihre jeweils zugewiesene Karte. Die gemeinsame Offlineprüfung akzeptiert mehrere Karten zu einem Prüfzeitpunkt und gibt das Ergebnis je Slot zurück.

Im SOPH-Shadow-Pfad müssen kanonische und native ID der freigegebenen Karte zum Originalmark und zum gebundenen Modellportfolio passen. Die GGE liefert den Abstand für diesen Marktkontext. Vor der Modellbuchung vergleicht der Consumer den verwendeten Scope-Abstand und die Instrumentidentität mit der gebundenen Geometrie. Der eingefrorene Replaykern berechnet seinen numerischen Abstand intern zweimal ohne ID erneut. Die beiden numerischen Aufrufe treffen keine Instrumentauswahl.

Bei flachem Portfolio verarbeitet die Richtungsbestätigung zeitlich verschiedene Originalmarks desselben Instruments. Ein gebuchter Eröffnungsfill setzt den ersten Positionsanker auf den modellierten Fillpreis. Der Anker folgt bei Long höheren und bei Short tieferen Marks. Ein geschlossener Bestand gibt den Anker frei. Freies Budget für einen weiteren Einstieg und die Verwaltung des gebuchten Bestands haben unterschiedliche Eingänge.

Der SOPH-Modus bewertet lineare Futures in USD. Kontowert ist hinterlegtes Modellkapital zuzüglich realisierter und unrealisierter Ergebnisänderungen, abzüglich der gebuchten Gebühren und Fundingbeträge. Die wirtschaftliche Rekonstruktion liest denselben Modus und den Mark der jeweiligen Entscheidung. Die Obergrenze für neue Einstiege bleibt bei 25 USDC.

Im Offlinevergleich der 137 archivierten Entscheidungen vom 22.11.2026 entstanden neun reguläre Short-Intents. Ein gesonderter damaliger Ausführungszeitpunkt fehlt. Eine zweite Rechnung mit sofortiger Ausführungsprüfung am Entscheidungszeitpunkt hielt alle neun Mengen wegen Notional plus Kostenreserve oberhalb des Slotbudgets. Das Originalarchiv enthält null Fills. Die Fortschreibung eines belegten Positionsankers wurde mit Offline-Testdaten gesondert geprüft.
