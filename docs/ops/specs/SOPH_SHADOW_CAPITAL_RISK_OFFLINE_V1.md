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

Beim erweiterten Ownerlauf zu PR #7385 bestanden 329 Prüfungen. Der
Runbook-Verweistest scheiterte auch in der Auswahl zu PR #7387 (107 von 108).
Er suchte die damalige Freigabe in Abschnitt 11.2.1.E des aktuellen
Master-Runbooks. Der Abschnitt fehlte bereits auf der jeweiligen Ausgangsrevision.
Die Verhaltenstests zur Ableitung der Scope-Richtung aus dem SideState bestanden.

Der [Verweistest](../../../tests/ops/test_hardening_v2_scope_direction_overlay_generator_inert_v1.py)
prüft die vier ursprünglichen Aussagen jetzt im archivierten Originalabschnitt.
Die einmalige Freigabe und der Arbeitsstopp beziehen sich auf die damalige
Änderung am Hardening-v2-Host. Der Auszug umfasst die Überschrift bis zum Ende
des letzten Codeblocks. [Original in PR #6283](https://github.com/rauterfrank-ui/Peak_Trade/blob/82659f5a0112024f42e49ff3d4eea18d6500fd0d/docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#L7248-L7329) · [Lokaler Auszug](../evidence/PR_6283_RUNBOOK_11_2_1_E.txt)

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

Der SOPH-Modus bewertet lineare Futures in USD. Kontowert ist hinterlegtes Modellkapital zuzüglich realisierter und unrealisierter Ergebnisänderungen, abzüglich der gebuchten Gebühren und Fundingbeträge. Die wirtschaftliche Rekonstruktion liest denselben Modus und den Mark der jeweiligen Entscheidung. In der Testphase begrenzen die Paper-Allokation und die Slot-Testpolicy den Betrag für neue Einstiege auf höchstens 25 USDC. Bei geringerem verfügbarem Modellkapital sinkt der Betrag entsprechend.

Im Offlinevergleich der 137 archivierten Entscheidungen vom 22.11.2026 entstanden neun reguläre Short-Intents. Ein gesonderter damaliger Ausführungszeitpunkt fehlt. Eine zweite Rechnung mit sofortiger Ausführungsprüfung am Entscheidungszeitpunkt hielt alle neun Mengen wegen Notional plus Kostenreserve oberhalb des Slotbudgets. Das Originalarchiv enthält null Fills. Die Fortschreibung eines belegten Positionsankers wurde mit Offline-Testdaten gesondert geprüft.

## Zeitquittung der Ausführungsprüfung

Bei einer Prüfung für zusätzliche Exposition enthält der Zyklusbeleg den gültigen gelesenen Zeitpunkt in `checked_at_unix` auch dann, wenn eine Marktquelle bereits abgelaufen ist. `check_time_source` kennzeichnet die übergebene Prüfuhr als `EXECUTION_CLOCK`. Verwendet ein Aufrufer die Zykluszeit als Ersatz, lautet die Herkunft `EVENT_TIME`. Liefert eine übergebene Uhr keinen gültigen Zeitpunkt, bleibt die Prüfung gesperrt und der Beleg enthält nur den Sperrgrund und das negative Prüfergebnis. Historische Belege können ohne diese Zeitfelder vorliegen.

## Offline-Gegenprobe zur Sizing-Schnittstelle auf Basis von PR 7386

Die bestehende Kapitalübergabe transportiert über `scope_capital_limit` eine positive Nominalgrenze je Auftrag in USD. Für die Gegenprobe wurden für BUY und SELL vor der Seitenentscheidung auf dem nativen Losraster die Buch- und Modellkosten geprüft. In den neun untersuchten Short-Fällen ergab sich für beide Seiten dieselbe bezahlbare Höchstmenge. Ihr Marknominal wurde als obere Grenze an das ursprüngliche Sizing übergeben. Modellkapital, Verlustlimit und Instrumentmetadaten behielten ihre eigene Bedeutung. Der reguläre Shadow-Pfad verwendet weiterhin seine bestehende Kapitalübergabe und die gesonderte Prüfung vor einer Modellbuchung.

Mit 25 USDC ergaben sich je nach Zyklus 265 bis 267 Kontrakte, mit hypothetischen 12,50 USDC 132 bis 133. Alle neun ursprünglichen Short-Signale blieben erhalten. Die Vergleichsmengen bestanden die Kostenprüfung unter der Annahme einer sofortigen Prüfung. Die Gegenproben wurden einzeln am jeweiligen flachen Archivzustand ausgewertet. In Zyklus 65 reduzierte ein engeres Verlustlimit die Menge nochmals auf drei Kontrakte. Im Beobachtungszyklus 64 entstand auch mit der Obergrenze kein Intent.

Eine positive Grenze unter dem Mindestlos verhinderte in Zyklus 65 den Intent. Der Zahlenwert null im selben Feld aktivierte hingegen die vorhandene Ersatzgrenze von 25 USD und ergab erneut 269 Kontrakte. Fehlt eine bezahlbare Losmenge, benötigt ein späterer Anschluss eine ausdrückliche Einstiegssperre für die betroffene Karte und Seite. Das gemeinsame USD-Feld allein bildet unterschiedliche Freigaben für BUY und SELL nicht ab.

## Mindestlos vor der Richtungsbestätigung

Bei einer flachen SOPH-Shadow-Karte prüft die Bridge das native Mindestlos für den ersten Kauf. Für eine Long-Eröffnung bewertet sie die verfügbaren Verkaufsangebote (Asks), für eine Short-Eröffnung die Kaufgebote (Bids). Den Schutzpreis ermittelt sie für die jeweilige Marktrichtung aus dem aktuellen Markpreis und dem Layer-C-Abstand des gebundenen Ereignisses. Der Abstand hat die Einheit USD je SOPH. Der Kostenprüfer erhält die Basismenge in SOPH, das freie Slotbudget in USDC, den Wechselkurs, die Modellkosten einschließlich der Fundingvorsorge für die jeweilige Positionsrichtung und die Verlustgrenze.

Reicht das Budget für den Kauf bei der beobachteten Marktrichtung nicht aus, stellt die Bridge diese Kartenbeobachtung zurück. Sie aktualisiert den Markpreisvergleich und verwirft die angefangene Richtungsbestätigung. Bei ausreichendem Budget folgen die reguläre Richtungsbestätigung und das ursprüngliche Sizing. Die Bridge prüft den Schutzabstand und bewertet die endgültige Menge zum Entscheidungszeitpunkt. Das laufende Positionsmanagement führt seinen eigenen Scope-Anker. Der Betrag von 25 USDC stammt aus der Testpolicy.

## Einstiegsbudget und endgültige Menge im SOPH-Shadow

Das Slotkapital stammt aus der Testallokation und dem markierten virtuellen Portfolio. Die Nominalgrenze je Auftrag begrenzt den Positionswert. Für eine flache SOPH-Karte kann ein Aufrufer zusätzlich den Gesamtbedarf eines Einstiegs in USDC begrenzen. Die optionale CLI-Angabe `--soph-entry-cost-limit-usdc` entspricht dem Feld `soph_entry_cost_limit_usdc` der analytischen Sessionkonfiguration. Bei einem Wert von 10 und 25 verfügbaren USDC im Slot dürfen Positionswert und modellierte Kosten dieses Einstiegs zusammen höchstens 10 USDC beanspruchen. Ein Wert von null stellt neue Einstiege zurück. Ohne diese Zusatzgrenze gilt das tatsächlich freie Slotbudget. Die Umrechnung in USD verwendet den USDC/USD-Index der aktuellen Karte.

Nach der Mindestlosprüfung ermittelt die Bridge eine kostenverträgliche Kaufmenge auf dem nativen Losraster. Markpreis, verfügbare Tiefe auf der jeweiligen Orderbuchseite, richtungsabhängiger Schutzabstand, Fundingvorsorge und Verlustgrenze stammen aus derselben gebundenen Entscheidung. Der positive Marknominalwert in USD gelangt als `scope_capital_limit` in das ursprüngliche Sizing. Dessen Risikoregeln und Instrumentgrenzen bestimmen die endgültige Kontraktmenge. Der Beleg `flat_entry_cost_bound` führt die beobachtete Richtung in `market_direction` und die native Eröffnungsseite in `side`. Instrument, Marktereignis, Budgetquelle mit Wechselkurs und nominale Obergrenze bleiben an diese Berechnung gebunden.

## Vom Richtungsentscheid zur Budgetbestätigung

Die SOPH-Shadow-Bridge übernimmt im selben Entscheidungszyklus die bestätigte Richtung und das endgültige Sizing für die freigegebene Karte. Der Beleg `soph_confirmed_entry_budget` bindet Session, Slot, Auswahl, beide Instrument-IDs, Marktereignis und Entscheidungszeit an die ursprüngliche Richtungsprüfung und den Sizingentscheid. Er nennt native Kontrakte, Marknominal in USD, dessen Gegenwert in USDC zum Kartenkurs und die modellierte Kostenvorsorge in USD. Die erste Bestätigung hält die Karte für diese Entscheidung belegt. Weitere Beobachtungen führen den Beleg fort. Im Modell bleiben Kapitalstand, Gebühren und Positionsmenge durch diese Bestätigung unberührt. Der Positionsanker setzt eine gebuchte Position voraus.

Fachlich bindet der Portfolio-Budget-Owner den vom Risk Sizing bestimmten Einstiegsbetrag an den bereits zugewiesenen Slot, seine Auswahl und genau dieses Instrument. Diese Zuordnung gilt für die laufende Instrumentbelegung. Long–Long bestätigt den Long-Markt, Short–Short den Short-Markt. Der separate Erstkauf eröffnet aus flacher Position das gewählte Futures-Exposure. Beim linearen SOPH-Kontrakt erhöht eine ausgeführte native BUY-Order die Nettomenge auf einen positiven Wert. Eine ausgeführte native SELL-Order senkt sie auf einen negativen Wert. Aus diesem Vorzeichen folgt die Wirkung späterer Markpreisänderungen. Erst eine bestätigte Buchung begründet eine Position für die anschließende Double-Play-Führung auf demselben Instrument.

Der analytische Budget-Owner schreibt `nominal_usdc` als gebundenen Betrag. `entry_action=FIRST_PURCHASE` bezeichnet die fachliche Handlung für beide Richtungen. `direction` hält die bestätigte Marktrichtung fest und `first_purchase_side` die native Eröffnungsseite (Long → BUY, Short → SELL). Eine identische Wiederholung bewahrt denselben Beleg. Eine abweichende Neubelegung während dieser Bindung wird abgewiesen.

Die [Double-Play-Spezifikation](NAKED_MV2_DP_SINGLE_BOUNDARY_PURIFICATION_SPEC_V1.md) bezeichnet den aktuellen Markpreis des Instruments als Nulllinie (`M_t`). Das Feld `nullline_price` der Stufe 5 hält den Markpreis bei der Initialisierung fest. Die [Stufen 8 bis 10](../../../src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/running_mechanics_pipeline_v1.py) vergleichen jeden angenommenen Markpreis mit dem laufenden Hoch im Bull-Regime oder Tief im Bear-Regime. Erreicht die Gegenbewegung den gültigen Scope-Abstand, wechselt das Regime und der aktuelle Markpreis wird zur neuen Referenz. Der Regimewechsel liefert Richtung und Referenz für die Fortführung auf demselben Instrument.

Im [Fünf-Slot-Orchestrator](../../../src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/orchestrator_v1.py) gehen Ranking, Slotzuordnung und ID-Bindung der Handelsentscheidung voraus. Die [29P-Anbindung](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_enter_live_29p_join_v1.py) führt auf ihrem Ausführungspfad einen eigenen technischen Hold für einen konkreten Auftrag. Der [Übersetzer des Börsenauftrags](../../../src/ops/full_core_live_path_composition_root_v1/venue_translation_v1.py) bildet eine Long-Eröffnung auf `buy` und eine Short-Eröffnung auf `sell` ab. Der [Ausführungsvalidator des Budget-Owners](../../../src/ops/portfolio_capital_reservation_budget_v1/execution_v1.py) prüft die native Seite gegen die gesizte Richtung, die Instrument-ID, die Kontraktmenge und `reduce_only=false`. Die [Versandschnittstelle](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py) verlangt eine auf den konkreten Auftrag gebundene Einmalfreigabe.

Der SOPH-Beleg gehört zum analytischen Modell innerhalb einer Session. Im Archiv vom 22.11.2026 ist SOPH ausdrücklich an Slot 5 gebunden. Die Angaben zur Ranking- und Universumsauswahl sind leer. Der [Originalvalidator für dauerhafte Slotbindungen](../../../src/ops/portfolio_capital_reservation_budget_v1/recovery_v1.py) weist diese Kartenbindung mit `DURABLE_INSTRUMENT_IDENTITY_INCOMPLETE` ab. Die Übergabe an den dauerhaften Budget-Owner benötigt die ursprüngliche Auswahl für Slot 5. Für diesen Archivstand sind dauerhafte Kapitalbindung, ausgeführter Erstkauf und anschließende Positionsführung offen.

## Simulierter Erstkauf und Haltezeit im belegten SOPH-Slot

Im Zyklus der Budgetbindung prüft der simulierte Erstkauf die ursprüngliche Auswahl anhand der Ranking- und Universumsquellen. Der interne Ausführungsplan übernimmt Instrument, native Seite und Kontraktmenge aus der gebundenen Entscheidung. Vor der Buchung prüft der Consumer die Gültigkeit der Auswahl, die aktuelle Karte und die Kosten. Der Fill im Modellportfolio verweist auf den geprüften Auftrag. [Übergabe und Prüfung des Buchungsbelegs](../../../src/ops/soph_shadow_first_purchase_v1.py)

Im chronologischen Replay der 137 Archivzyklen bestätigt Zyklus 65 Short–Short. Das Sizing ergibt 106 Kontrakte mit einem Markgegenwert von 9,81772 USDC. Der Betrag wird an Slot 5 gebunden. Der Erstkauf endet wegen der fehlenden Ranking- und Universumsreferenzen mit `SOPH_FIRST_PURCHASE_RANKING_UNIVERSE_BINDING_REQUIRED`. Die Anzahl simulierter Fills beträgt null.

Zwei synthetische Kontrollfälle mit gültiger Auswahl buchen in Zyklus 3 jeweils einen Erstkauf. Long hält 28 Kontrakte, Short hält 31. Zuvor löste die allgemeine Haltefrist in beiden Fällen genau 3.600 Sekunden nach der ersten Beobachtung der offenen Position eine Glattstellung in Zyklus 64 aus. Für eine belegte SOPH-Karte setzt ein zeitbezogener Rotationsausstieg einen belegten Instrumentwechsel voraus. Beide Kontrollfälle halten ihre Position bis Zyklus 120 und führen den Scope-Anker fort. Ein separat ausgelöster Killswitch stellt beide Richtungen an der früheren Zeitgrenze glatt. [Offline-Kontrollfälle](../../../tests/ops/test_instrument_card_stream_v1.py)
