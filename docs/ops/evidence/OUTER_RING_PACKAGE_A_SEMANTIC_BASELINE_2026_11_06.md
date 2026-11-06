---
docs_token: DOCS_TOKEN_OUTER_RING_PACKAGE_A_SEMANTIC_BASELINE_2026_11_06
status: bounded_investigation
source_commit: 9397d04a37d527a8316b3e44ef4f80b4ef44db7a
source_tree: 9364d79f787b72ece2691e213e92d28e40a9a927
authority: NONE
runtime_authorization_effect: NONE
---

# Außenring, Paket A: Bedeutung, bestehende Übergaben und erster Umsetzungsschritt

Stand: 6. November 2026. Arbeitsgrundlage ist Franks Außenring-Fertigstellungsrunbook, Version 1.0. Dies ist dessen abgegrenzter erster Architektur- und Consumerabgleich. Die Ergebnisse sind Untersuchungsbefunde zur genannten Revision; sie ersetzen weder Fachowner noch das [kanonische Master-Runbook](../../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md).

## 1. Ergebnis und Reichweite

Der untersuchte Korridor reicht von relativer Auswahl über den gebundenen Double-Play-Kreis und gemeinsame Kapitalreservation bis zur Fortsetzung nach bestätigtem Schluss. Hinzu kommen die für diesen Korridor relevanten Lern- und Optimierungsrückwege. Die vorhandene Universenuntersuchung wurde gezielt vertieft; eine neue vollständige Außenbereichsinventur wurde nicht begonnen.

Die wichtigste Präzisierung betrifft P13/P14: Der aktuelle Code enthält bereits einen Anschluss von bestätigter Schlussausführung zu kanonischem Kapitalrefresh und zu einer ursprünglichen Membershipprüfung. Der E6-Beleg hält dagegen in seinem ausdrücklich anderen synthetischen Episodenpfad den Hold weiter. Aus dieser E6-Grenze folgt keine repositoryweite Abwesenheit eines Post-Close-Anschlusses.

Im jetzt ausgeführten injizierten N1-Fall wird der Kapitalhold tatsächlich freigegeben, der neue kanonische Kapitalwert konsumiert und eine Membership zum Behalten oder Ersetzen vorgeschlagen. Dieser Vorschlag wird dort absichtlich noch nicht persistiert. Damit fehlt in diesem verfolgten Anschluss der belegte fortgesetzte Weg bis zur dauerhaft veröffentlichten Folgezuordnung und ihrem nächsten Coreverbrauch. Ein anderer vollständiger natürlicher Hostpfad wurde nicht nachgewiesen.

Genau fünf definierte Lanes, höchstens fünf Membershipmitglieder, eine Position je gebundener Double-Play-Instanz und die bisherige globale N1-Freigabe sind unterschiedliche Aussagen. Keine davon wird durch die jeweils andere ersetzt. Die spätere Fünf-Futures-Zielwirkung bleibt eine Anforderung.

## 2. Originalkonstruktion und historische Varianten

### Double Play und Kapital

Der [Trading-Logic-Manifest](../specs/MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) beschreibt zwei gegengerichtete Seiten um dasselbe ausgewählte Future. Der normale State-Switch hält den Handelskreis am Instrument fortgesetzt. [State-Switch-Vertrag](../specs/FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md) und [Kapital-Slot-Vertrag](../specs/MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md) trennen diesen Wechsel von Kapitalratchet, Kapitalrelease und Instrumentneuauswahl. Beide Seiten teilen einen instrumentbezogenen Kapitalslot; daraus entstehen keine zwei gestapelten Kapitalbudgets.

Der ältere Kapitalslotentwurf enthält eine konservative Ratchetidee auf realisierter beziehungsweise abgewickelter Basis, Verlustfortschreibung und keine automatische Auffüllung aus fremden Reserven. Seine beispielhaften Zahlen sind keine bestätigten heutigen Parameter. Die genaue Bedeutung als Notional-, Equity- oder Marginhülle ist dort ausdrücklich nicht abschließend festgelegt. Der heutige Portfolio-Reservationsowner erklärt selbst, dass er diesen Ratchet nicht implementiert oder ersetzt. Diese historische Idee bleibt deshalb als gesonderte fachliche Fläche sichtbar.

Die [GGE-Änderung vom 3. November](../specs/GGE_ONLY_FUTURES_AND_COMMON_ASSET_ADMISSION_V3.md) ändert den geltenden Geometriepfad. Frühere Fixed-Scope- und gesonderte BTC-Ausschlussformulierungen werden dadurch nicht als heutige Zielregeln übernommen. Die untersuchten Quellen belegen diese erhaltenen Entwurfsstände; ein lückenloser Ursprung aller früheren Double-Play-Ideen wird nicht behauptet.

### Fünf Lanes und gemeinsames Portfolio

Ein erhaltener Nutzerauftrag vom 19. September 2026, 10:07 Uhr, Chat ea05daa0-f273-44c1-b907-eb2111342c89, Zeile 30, verlangt einen gemeinsamen Kapitalowner für zwei bis fünf isolierte Slots. Sein Zweck ist das Verhindern mehrfacher Verplanung derselben verfügbaren Mittel. Er hält N1- und External-Effect-Grenzen für diesen damaligen Auftrag ausdrücklich unverändert. Die Originalnachricht wurde im ausgelagerten Cursor-Protokoll gelesen; ihr vollständiger Inhalt und die aktuelle Fundstelle sind im [Quellen- und Prüfprotokoll](OUTER_RING_PACKAGE_A_SEMANTIC_BASELINE_2026_11_06.json) gebunden. Historische Befehle wurden nicht ausgeführt.

Der erhaltene Architekturentscheid 60f0c0820396 vom 20. Oktober behandelt N5 als Fünf-Stack-Zielarchitektur und Full-Core als technische Orchestrierung. Execution, Self-Learning, Optimization und Market Intelligence besitzen dort eigene Architekturidentitäten; Meta ist eine Verbindung zwischen SL und OPT. Die Vaultkopie des Entscheids wurde bytegleich gegen genau dieses Gitobjekt im externen Gitarchiv geprüft. Das ist Herkunftsevidence einer anderen Entwicklungslinie, keine automatische Übernahme als heutige Systemautorität. Die bestehende abweichende Einordnung von Execution als Außenbereich bleibt als Klassifikationsentscheidung offen.

### Selbstlernen, Optimierung und Marktmodell

Der [erhaltene ursprüngliche Self-Learning-Master](self_learning_original_layers_restoration_v1_2026_11_04/originals/self_learning_master_base.original.txt) umfasst Experimentidentität, unveränderliche Erinnerungen, Fehler, Robustheit, Vergleich, Champion/Challenger, Reality Gap und spätere Metaanalyse. Seine Aufgabe geht über DDO-Attribution hinaus. Das Original trennt lernende Evidenceerzeugung von Ausführungs- und Übernahmebefugnissen.

Die [OPT-Foundation](../specs/META_LEARNING_OPTIMIZATION_UNIVERSE_FOUNDATION_NORMATIVE_V1.md) definiert zunächst Identität, Registry und Inputgrenze. Das ist eine engere Teilkonstruktion als der spätere zusammengesetzte Researchpfad. Der [M6-Vertrag](../specs/SELF_LEARNING_M6_META_LEARNING_INGEST_AND_EVIDENCE_NORMATIVE_V1.md) beschreibt Evidenceaufnahme und ruft den numerischen Phase-11-Analyzer ausdrücklich nicht auf. SL-Phasen, M-Adressen, Researchmeta und native Corelayer sind daher keine einheitliche serielle Leiter.

## 3. Soll-/Ist-Kette am tatsächlichen Consumer

### A1: Daten, Rangfolge und Instrumentbindung

**Fachliche Aufgabe:** Unter den für ihren Zweck zugelassenen Futures die relativ stärkeren Kandidaten bestimmen und eine eindeutige Instrumentbindung herstellen. Ein ruhiger Gesamtmarkt begründet nach Franks Ziel keine neue absolute Volatilitätspause.

**Ist:** [Cap23-Auswahl](../../../src/ops/single_selected_future_policy_v1/selection_v1.py) übernimmt die Upstream-Rangfolge. Bei offener Position hält sie das bisherige Instrument und führt den stärkeren Nachrücker als Replacement Pending. Ohne blockierende Position wirken ihre eigenen Mindesthalte- und Hysteresebedingungen. Die [MF-Membershipprüfung](../../../src/ops/mf_membership_selector_and_rotation_runtime_contract_v1.py) arbeitet separat mit Rankingbeobachtungen und einem Membershipartefakt.

**Wert- und Zeitvertrag:** Cap23 verwendet Sekunden, unter anderem 3.600 Sekunden Mindesthaltezeit als heutigen Default. Die MF-Policy verwendet zwei unterschiedliche Rankingbeobachtungen. Diese Einheiten sind nicht gleichbedeutend. Beide übernehmen Cap22-Ränge; keiner dieser Werte ist ein Kontogewinn.

**Übergabe und Writer:** Rankingidentität, Integritydigest, Universeidentität und Ereigniszeit werden über das [Membershipartefakt](../../../src/ops/mf_membership_context_artifact_contract_v1.py), den originalen Selectionwriter und die [geprüfte Veröffentlichung](../../../src/ops/current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1/checked_publication_v1.py) bis zur Topologie/Cap24-Bindung weitergeführt. Die Veröffentlichung besitzt bereits einen Unterbrechungscheckpoint. Diese Writer sollen wiederverwendet werden.

### A2: GGE, Scope, Richtung und Entscheidung

**Fachliche Aufgabe:** Am gebundenen Instrument Marktbewegung bewerten und den nächsten fachlichen Schritt im fortgesetzten Handelskreis bestimmen.

**Ist und Einheiten:** [GGE](../../../src/trading/master_v2/golden_geometry_engine_v1.py) berechnet positive endliche Volatilität mal Markpreis; das Ergebnis hat die Preiseinheit des Marks. [L6](../../../src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/l6_dynamic_scope_generator_v1.py) validiert und transportiert das gelieferte D_t. [L10](../../../src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/l10_bull_bear_switch_v1.py) vergleicht Gegenbewegung und D_t und setzt bei Regimewechsel die laufende Referenz zurück. Diese Übergänge erzeugen keinen bestätigten Positionsfill.

**Tatsächlicher Folgeconsumer:** Die [Entry-/Management-/Exit-Policy](../../../src/trading/master_v2/double_play_entry_exit_policy_v0.py) verarbeitet Direction-, Position-, Reconciliation- und Gatezustand getrennt. Ein ausgewähltes Gegensignal bei offener voller Position führt im gelesenen Zweig zu REDUCE mit Reversal Preparation. Teilzustand, Exit Pending und Unknown blockieren einen unmittelbaren Gegenentry. Die vollständige Folge braucht Mengenowner, Ausführung, bestätigte Positionswahrheit und einen weiteren Coreaufruf.

**Beleg:** 43 bestehende Policytests bestehen in dieser Untersuchung. Sie zeigen die abgegrenzte reine Policywirkung unter Testinputs; keine natürliche Venuefolge wird daraus abgeleitet.

### A3: Finale Menge und gemeinsame Kapitalbindung

**Fachliche Aufgabe:** Einen fachlichen Handelswunsch auf eine zulässige native Kontraktmenge und eine konsistente gemeinsame Kapitalbeanspruchung begrenzen.

**Ist:** Der [Portfolioowner](../../../src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py) verbraucht den typisierten 29P-Kapitaloutput. Der ursprüngliche CRS bleibt Mengenowner. Die Reservation ist an Account, Slot, Decision/Cycle und Kapitalbeobachtung gebunden. Native Kontrakte, accountgebundene USDC-Basis und instrumentbezogene Kapitalhülle werden nicht ineinander umbenannt.

**Persistenz:** [DurableBudgetStore](../../../src/ops/portfolio_capital_reservation_budget_v1/durable_store_v1.py) und die Originalwriter erhalten Holds, Executionlinks und Instrumentgenerationen. COMMITTED ist im ursprünglichen Pre-External-Vertrag ein interner Zustand und beweist für sich keinen Venuefill. Nach Restart ist frische Originalreconciliation notwendig. Die aktuelle Recovery kann neue Bindungen übernehmen, wenn dadurch kein noch aktiver Hold seine ursprüngliche Instrumentgeneration verliert.

### A4: Ausführung, Positionsschluss und Kapitalrefresh P13

**Producer und Eintritt:** Der [Post-Submit-Lifecyclejoin](../../../src/ops/full_core_live_path_composition_root_v1/full_core_post_submit_exchange_reconciliation_lifecycle_join_v1.py) ruft bei explizitem Request den [Post-Close-Feedbackcomposer](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_post_close_feedback_v1.py) auf. Der Composer bindet die genaue Closingorder, Instrument/Lane/Epoch, Account/Environment, vollständigen Fill, Flatbeobachtung und leere Pendingbeobachtung. Er prüft die zeitliche Reihenfolge. Ein fehlender Positionsdatensatz gilt nur mit seinem gesonderten belegten Empty-Query-Vertrag als Flat.

**Budgetconsumer:** Die Methode refresh_after_reconciled_flat_v1 des ursprünglichen Portfolioowners übernimmt ausschließlich frische kanonische Kapitalevidence. Sie rekonstruiert keinen Geldbetrag aus Positionsmenge, Fill oder PnL. Close-Identität und Beobachtungswechsel begrenzen Replay. Die Methode kann in diesem N1-Vertrag nur den exakten gesamten aktiven Reservationssatz ihres Slots freigeben. Fremde oder uncommittete Holds verhindern den Übergang.

**Beobachtete Wirkung:** In den ausgeführten injizierten Fällen sinkt der aktive Hold von 40 auf 0 und die Budgetbasis wird auf den gelieferten kanonischen Wert 75 gesetzt. Die Zahl 75 ist Testinput, kein beobachteter Kontostand oder Gewinn. Teilclose hält Kapital und Custody. Durable Restart und Replay werden mitgeprüft.

**Grenze:** Dieser vorhandene N1-Pfad ist weder ein sicherer laneweiser N5-Refresh noch der E6-Episodenabschluss. [E6](BOUNDED_OFFLINE_STAGE_E6_ACCEPTANCE_2026_11_05.md) hält dort mangels eigener weiterer Kapitalevidence den Originalhold korrekt weiter. Beide Befunde können gleichzeitig gelten.

### A5: Membershipprüfung und dauerhafte Folgezuordnung P14

**Ist:** Nach dem bestätigten Flat kann der Feedbackcomposer mit frischem Ranking den ursprünglichen Selector aufrufen. Diese Prüfung kann auch ohne neue Kapitalevidence stattfinden; dann bleibt das Budget unverändert. Ihre Rückgabe enthält ein vorgeschlagenes Membershipartefakt, dessen persisted_artifact im geprüften Weg ausdrücklich leer bleibt.

**Vorhandene anschließende Mechanik:** persist_selector_result_v1 benutzt den ursprünglichen Membershipwriter mit Readback. Die geprüfte Selection-/Topologieveröffentlichung verlangt bei Ersatz zusätzlich frische Portfolioidentität und eine erlaubte COMMIT-Custodyentscheidung. [Positionspinning und Rotation](../../../src/ops/current_mf_n5_instrument_runtime_identity_closure_v1/lifecycle_v1.py) erhalten offene Instrumente.

**Konkrete Anschlussgrenze:** Für den untersuchten Feedbackpfad ist die Kette vom Vorschlag über diese dauerhafte Veröffentlichung, neue Originalbindings und einen tatsächlich folgenden Coreaufruf nicht durchgängig geschlossen. Die scoped Codesuche findet Weitergabe/Serialisierung des Feedbacks; daraus wird keine automatische Zustellung an den nächsten Host abgeleitet. Das ist eine Aussage über diesen Korridor, keine Behauptung über jedes Programm des Repositories.

### A6: Fünf Lanes, Host und fortgesetzte Episoden

Der [N5-Orchestrator](../../../src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/orchestrator_v1.py) komponiert bereits Positionspinning, geprüfte Veröffentlichung, Cap24-Bindung, Ingest, MV2/DP-Handoff und sequenzielle Readiness mit gemeinsamem Budgetowner. Der [Completionconsumer](../../../src/ops/current_mf_n5_full_autonomy_runtime_n5_completion_v1/completion_join_v1.py) kann für diesen begrenzten Zusammenschluss host_join und architecture_complete im Resultat setzen, während die standing Autorisierung weiterhin N1 und keine External Effects erlaubt. Diese unterschiedlich gebundenen Aussagen werden nicht zu einer Betriebsfreigabe zusammengezogen.

Die [bounded Session](../../../src/ops/bounded_peaktrade_system_composition_v1/session_v1.py) schützt Versuchsgrenzen, Quellenfenster und Originalzustände. Nach ihrem Flat-Seal ist SEALED ein absichtlicher Terminalzustand. Eine neue Folgeepisode braucht einen definierten Hostübergang mit erhaltener Originalhistorie; ein Reset dieser Session wäre keine autonome Fortsetzung.

Der [kontinuierliche S6-Controller](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_governed_continuous_cycle_orchestrator_v1.py) sequenziert bis PRE_EXTERNAL_EFFECT. Mehrere Beobachtungs-/Decisionzyklen dieses Controllers sind kein Nachweis mehrerer vollständig ausgeführter Handelszyklen.

## 4. Lern- und Optimierungsrückwege im Zielkorridor

**DDO:** Originalentscheidung, spätere Messung, Attribution und LearningState bleiben entscheidungs- und zeitgebunden. Der [E6-Kausalabgleich](IU_SL_OPT_UNDERSTANDING_RESOLUTION_2026_11_05.md) dokumentiert den tatsächlich verwendeten opaken Learninglabel-State. Ein neues Label wird daher nicht pauschal als numerisch verbessertes Modell beschrieben.

**MI-Modellfolge:** Der [OLS-Modellpfad](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_ols_next_forecast_v1.py) konsumiert abgeschlossene Originalmessjobs, trennt zeitliches Training und Validierung, speichert numerische Koeffizienten und lädt sie für die Berechnung des nächsten Forecastpayloads. Target, Instrumentidentität, Preisfamilie, Horizont, Kenntniszeit und Generation bleiben gebunden. Die elf bestehenden OLS-Tests bestehen einschließlich Cold Read, neuer kumulativer Evidence, Lookaheadabwehr und berechnetem Folgeforecast. Das belegt die begrenzte numerische Funktion unter Testdaten.

**Getrennter Phase21-Weg:** [Conditioned Compose](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/loop_a_conditioned_learning_evidence_v1.py) transportiert im gelesenen Aufruf weder realized_scalar noch originale Calibration an den [Basiscomposer](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/mi_to_learning_evidence_bridge_v1.py). Der unabhängige neue Marktmodellweg schließt diese andere Vertragsfrage nicht. Hier wurde kein neuer Phase21-Fehlertest ausgeführt.

**Research und Meta:** Der frühere MI-ACK gibt in E6 den Versuch frei und bindet Herkunft; die numerischen Researchdaten kommen dort aus einer gesonderten synthetischen Reihe. Der Wechsel 50 zu 100 hat im E6-Fall eine Duplikatsursache. Der eigenständige E4-Kontrollfall belegt regionale numerische Metapriorisierung. Diese beiden Ursachen bleiben getrennt. Aus keinem der Fälle folgt ein natürlicher ökonomischer Vorteil.

**Systemrückwirkung:** Ein gespeichertes Modell, ein Researchresultat oder eine Proposal müssen für produktiven Nutzen erst ihre erlaubte Übernahme und ihren echten Parameter-/Decisionconsumer erreichen. Automatischer Scheduler, geeignete Applyflächen und die qualitative Übernahmeregel sind noch zu bestimmen und zu belegen. Die grundlegende gewünschte Lernwirkung bleibt Pflichtziel; zusätzliche spezielle Loop-C-/B0–B5-/RAG-Flächen sind dadurch nicht automatisch gewählt.

## 5. Entscheidungsvorlagen für die betroffenen Änderungen

### D1: Gleichzeitige Positionen und Fünf-Lane-Ziel

**Ist:** Cap23 und nachgeordnete Assertions halten N1; der Code kann fünf isolierte Adressen komponieren. **Varianten:** globale Einpositionsgrenze beibehalten oder einen versionierten Vertrag mit höchstens einer aktiven Seite/Position je Lane und gesonderter Portfoliogrenze bis fünf schaffen. Nur die zweite Variante kann das festgelegte Fünf-Futures-Ziel erfüllen. **Empfehlung:** die erforderlichen Originalowner gemeinsam versionieren, Zuordnung und Kapitalaggregat explizit prüfen und N1-Kompatibilität erhalten. Die Zielzahl fünf wird nicht erneut zur Entscheidung gestellt. Konkreter Account-/Positionsmodus und Aktivierung bleiben eigene Voraussetzungen.

### D2: Reversal, Teilclose und Folgeentry

**Ist:** Der Core liefert Reversal Preparation/REDUCE; Mengenrepräsentation, tatsächlicher Close und Folgeentry liegen außerhalb dieser Entscheidung. **Varianten:** Close bis bestätigtes Flat mit anschließendem Gegenentry oder ein gesonderter echter Venue-Reversalvertrag. **Empfehlung für den ersten Anschluss:** die vorhandene Close-/Reconciliationsequenz weiterverwenden. Die REDUCE-Menge muss beim zuständigen Mengenowner mit dem Account-/Positionsmodus geklärt werden. Die zwei E6-Einlot-Reduktionen sind keine neue allgemeine Mengenregel. TimeExit-Zahlen werden nicht erfunden.

### D3: Stärkerer Nachrücker und Haltebedingungen

**Ist:** Cap23 misst Mindesthaltung in Sekunden; MF-Policy A zählt Rankingbeobachtungen. **Varianten:** dieselben heutigen Regeln bewusst für den gewählten Pfad übernehmen oder eine neue, einheitlich versionierte Rotationspolicy bei den Originalownern definieren. **Empfehlung:** zuerst den gewünschten Aufruf-/Beobachtungstakt und die gewünschte Reaktionsregel festlegen. Zwei Beobachtungen werden nicht still in Sekunden umgerechnet. Vor bestätigtem Flat und geklärter Custody bleibt der Ersatz blockiert; die Rangfolge selbst bleibt relativ.

### D4: N5-Kapitalrefresh

**Ist:** N1-Refresh verlangt den gesamten aktiven Reservationssatz des einen Slots. **Varianten:** alle Lanes bis zu einem globalen Flat warten lassen oder beim Budgetowner einen echten laneweisen, settlementgebundenen Refresh definieren. **Empfehlung für N5:** die zweite Variante fachlich ausarbeiten. Dabei muss geklärt werden, welche anderen Verpflichtungen bereits in frischer Account-Free-Margin enthalten sind und welche weiterhin intern zu reservieren sind. Einfaches Addieren, Freigeben aller Holds oder erneutes Subtrahieren bereits außenwirksamer Margin kann falsche verfügbare Mittel erzeugen. Der erste unten benannte N1-Anschluss verändert diese Geldsemantik nicht.

### D5: Architekturgranularität und Verantwortlichkeiten

**Ist:** Die historische Execution-Universumsidentität und die heutige Außenbereichsansicht verwenden verschiedene Klassifikationen; N5 ist zugleich Zieltopologie und Teil der FA-Ansicht. **Varianten:** Ansichten als unterschiedliche Granularitäten erläutern oder eine abgestimmte heutige Klassifikation ratifizieren. **Empfehlung:** zuerst Zustandswriter und tatsächliche Eingangs-/Ausgangsgrenzen erhalten und die Klassifikationsfrage getrennt entscheiden. Eine Umbenennung schließt keinen fehlenden Hostübergang. Der folgende Anschluss benötigt keine neue Universumsanzahl oder Guardianstruktur.

### D6: Qualitätsziel und erlaubte automatische Änderung

**Ist:** Numerischer MI-Folgeforecast und begrenzte Researchmechanik existieren; natürliche ökonomische Überlegenheit ist nicht belegt. **Varianten:** zunächst Forecastgüte gegen die direkte bisherige Forecastbaseline messen oder zusätzlich einen getrennten nachfolgenden Systemvergleich auswählen. **Empfehlung:** beide Aussagen bei Bedarf separat definieren: Messziel, unabhängige Population, damaliger Informationsstand, Horizont, Netto-/Kosten-/Fundingumfang und Unsicherheit. Für jede automatisch übernehmbare Parameterfläche wird ein benannter Consumer mit Grenzen und Rücknahmevertrag benötigt. Gute technische Zustellung allein erfüllt die Übernahmeregel nicht.

## 6. Erster abgegrenzter Umsetzungsschritt

**Arbeitsauftrag:** Im bestehenden FA-/Hostpfad einen expliziten, dauerhaften N1-Fortsetzungsübergang vom bereits geprüften Post-Close-Ergebnis zur nächsten originalen Instrument-/Corebindung schließen. Kein zweiter Selector, Budget- oder Mengenowner und kein pauschales Umschalten von N5-/Liveflags.

**Eingang:** vollständiger bestehender Close-Request samt Lifecycle-/Reconciliationresultat, Account/Environment, alte Lane-/Instrumentgeneration, Close-Envelopeidentität, gegebenenfalls originales Refreshresultat sowie der ursprüngliche Membershipvorschlag mit Ranking- und Priorreferenz. Ein bloßes Flat-/Reviewed-Label ist unzureichend.

**Originalowner und Reihenfolge:**

1. Den Original-Feedbackcomposer verwenden. Membershipreview und Kapitalevidence behalten ihre getrennten Zulassungen; ohne frisches Kapital ist weiterhin nur die zulässige Reviewwirkung möglich.
2. Den ursprünglichen Membershipwriter und seinen Readback für das unveränderte Ergebnis verwenden. Der Host führt einen dauerhaften Übergabebeleg mit Closeidentität, altem und neuem Membershipdigest und Phase; dieser Beleg übernimmt keine fachliche Entscheidung.
3. Die bestehende checked Selection-/Topologiepublication samt Custody-COMMIT und Unterbrechungscheckpoint verwenden. Vorhandene Holds, Pending/Unknown und Instrumentgenerationen bleiben Bindungsbedingungen.
4. Frische Originalreconciliation und zulässige Originalbudget-Recovery für die Folgeinstrumentbindung nachweisen. Eine neue Instrumentgeneration darf keinen noch aktiven alten Hold umdeuten.
5. Genau diese veröffentlichte Bindung an einen weiteren begrenzten Coreaufruf übergeben. Der Abnahmepunkt ist dessen tatsächlich konsumierte Identität und Entscheidung bis zur bisherigen PRE_EXTERNAL-Grenze. Kein weiterer Trade wird allein durch den Übergabebeleg autorisiert.

**Persistenz und Wiederaufnahme:** Unterbrechungen zwischen Membershipwrite, Publication, Budgetaufnahme und Consumer-ACK müssen an den vorhandenen Originalcheckpoints fortsetzen. Die Übergangsidentität bindet Close, Lane/Instrumentgeneration und Zielmembership. Replay darf keinen zweiten Kapitalrelease, keine doppelte Publication, keinen neuen ungezählten Versuch und keine zweite Folgeverarbeitung erzeugen. Bestehende Scope-/SideState-/Learninghistorie bleibt erhalten.

**Abhängigkeiten:** Für diesen N1-Nachweis bleiben die heutigen Originalmengen- und Policyinputs explizit gebunden. Die N5-Entscheidungen D1/D4 und natürliche Ausführungsfreigaben werden dafür nicht vorweggenommen. Der genaue Hosteintritt muss gegen seine Originallease-/Attempt-/Sessionverträge implementiert werden; SEALED wird nicht durch einen Reset umgangen.

## 7. Abnahme des ersten Anschlusses

Die folgenden Fälle sind der konkrete künftige Änderungsnachweis, nicht bereits ausgeführte neue Tests:

- Voller bestätigter Close, frisches Kapital und stärkere zulässige Membership: Originalwriter/Publication/Readback führen zur richtigen neuen Instrumentgeneration beim nächsten Coreconsumer.
- Bestätigter Close bei weiterhin stärkstem bisherigem Instrument: fortgesetzter Kreis am selben Instrument mit richtigem Scope-/SideStatebezug.
- Teilclose, offene Restposition oder Pending/Unknown: Custody und Hold bleiben erhalten; keine falsche Folgezuordnung.
- Rankingreview ohne neue Kapitalevidence: zulässiges Review bleibt möglich; ein neuer finanzieller Entry bleibt an seiner eigenen Admission gebunden.
- Replay vor und nach Prozessneustart: identische Übergangsidentität, genau eine Publication und keine doppelte Kapital- oder Consumerwirkung.
- Fehler an jeder originalen Write-/ACK-Grenze: bestehender Checkpoint wird fortgesetzt; keine neue Genesis und kein Reset verbrauchter Versuche.
- Fremder Account, falsche Instrumentepoch, alter Rankingdigest oder zukünftige Beobachtung: Ablehnung am zuständigen Originalconsumer.
- Geänderte oder nicht genügend frische Quelle zwischen Vorschlag und Commit: kein unkontrolliertes Materialisieren eines alten Vorschlags.

## 8. Prüfungen, vorziehbare Arbeit und offene Grenzen

Neu ausgeführt gegen die Produktbasis dieses Dokuments:

- Runtimecheck: PASS, checkoutgebundenes Python 3.11.14 und unveränderte Lockbindung.
- Aktueller Atlasmodus check: PASS; 22.459 eingefrorene Dateien und ihre deklarierte Source-/Policyprojektion geprüft. Das ist keine Fachabnahme.
- Obsidianprojektion check: PASS; die deklarierte abgeleitete Ansicht ist konsistent. Historische Links und Originalnotizen bleiben datiert.
- Fünf fokussierte Dateien zu Closefeedback, durablem Budget, Rotation und N5-Orchestrierung: 77 PASS in 22,91 Sekunden.
- Reine Double-Play-Policy und numerischer OLS-Folgeforecast: 54 PASS in 2,82 Sekunden. Die beiden Populationen sind disjunkt; zusammen 131 ausgewählte Tests, keine Gesamtsuite.

Der alte YAML-Atlasvertrag wurde gesondert geprüft: test_atlas_loads_and_validates endet mit einem Setup-ERROR, weil load_atlas_v1 weiterhin die fehlende census_meta.yaml aus seinem deklarierten Quellensatz verlangt. Exitcode 1; genaue Auswahl und Fehlermeldung stehen im Quellen- und Prüfprotokoll. Ursache ist die bestehende fehlende Quellenbindung dieses Loaders im bereinigten Bestand; ob sein ausgewählter Altvertrag migriert oder durch eine begründete aktuelle Vertragsbindung abgelöst werden soll, ist noch zu entscheiden. Eine synthetisch ergänzte Censusdatei wäre kein Quellenbeweis. Ein PASS der neuen Atlasansicht ersetzt diesen anderen Vertrag nicht. Die im Fertigstellungsrunbook genannten früheren Docs-Token-, Verweisziel-, Ruff- und Whitespacebefunde wurden hier nicht pauschal neu ausgeführt oder für erledigt erklärt.

Unabhängig vorziehbar sind die Messdefinition aus D6, eine konkrete natürliche Quellen-/Account-/Hostvorlage und die Ursachenarbeit an diesem bestehenden Integrationsvertrag. Ihre Vorbereitung setzt weder Orderbetrieb noch einen physischen Ausfall voraus.

**Paket-A-Abschluss für diesen Korridor:** Quellenstand, Originalkonstruktionen und Varianten, konkrete Übergaben, nachgewiesene Teilpfade, Anschlussgrenzen, Entscheidungsvorlagen sowie erster Änderungsauftrag und Abnahmefälle liegen vor. Technische Vollständigkeit aller Universumsgrenzen, alle W-Themen, natürlicher Dauerbetrieb, N5-Handelswirkung, positive wirtschaftliche Qualität und Strom-/Boot-Fortsetzung bleiben offen. Produktcode, finanzielle Parameter, Freeze-Tags und Betriebsfreigaben wurden durch diese Untersuchung nicht verändert.
