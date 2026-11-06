---
title: "Konkrete Werte bis zum Ursprung"
stand: "2026-11-06"
rolle: "Quellgebundener Standabgleich ohne Betriebsautoritaet"
authoritaet: "NONE"
---

# Konkrete Werte bis zum Ursprung

Vollständige Leserprojektion des im Repository mit `63a3627598ac` gesicherten Rückverfolgungsberichts. Untersuchter Produktstand: `28f0115fbc69a3bd1e8f5ad87f5f45492cf8dc44`. Die Rechnung und Consumerintervention sind ursprüngliche Belege des Berichts, kein neuer Lauf durch diesen Dokumentabgleich.

Untersucht am vollständigen Codecommit `28f0115fbc69a3bd1e8f5ad87f5f45492cf8dc44`. Verwendet sind die Originalartefakte des gerade bestandenen Verbundlaufs sowie die tatsächlichen Rechen- und Consumerfunktionen. Die Rückverfolgung startet bei konkreten Ergebnissen; anschließend werden die maßgeblichen Rechnungen und Auswahlentscheidungen vorwärts überprüft. [Zahlen, Originalbytes und Quellenbindung](/Users/frnkhrz/Peak_Trade/docs/ops/evidence/iu_sl_opt_concrete_origin_trace_2026_11_05/trace.json).

## 1. Der MI-Fehler 0,0670113769896297

Der fertige Consumer-ACK enthält Return 0,0870113769896297 und Fehler 0,0670113769896297. Rückwärts führt der ACK über den [numerischen MI-Readback und die DDO-Consumer](/Users/frnkhrz/Peak_Trade/src/ops/full_core_live_path_composition_root_v1/natural_enter_cross_session_outcome_closure_v1/offline_v1.py:632) zur Originalmessung des [N_BARS-Suppliers](/Users/frnkhrz/Peak_Trade/src/learning/deterministic_decision_outcome_v0/n_bars_bar_evidence_supplier_v1.py:199). Die erhaltene Messung nennt ausdrücklich Startpreis 110, Endpreis 120, zwei endgültige Barcloses und LOG_RETURN.

Diese beiden Preise stammen aus [der Testquelle](/Users/frnkhrz/Peak_Trade/tests/ops/test_bounded_offline_all_purpose_consumers_v1.py:21): Sie übergibt dem originalen O4-Produzenten drei künstliche Markbeobachtungen 100, 110, 120, erzeugt echte Producer-/Finalizerrecords und schreibt sie in den normalen Factstore. Der genaue spätere Horizont wählt die letzten beiden Closes 110 und 120. Bis dorthin ist die Herkunft verfolgt: Die ursprünglichen Preise sind Zahlen aus dem Testgenerator. Sie stammen in diesem Beleg nicht von einer Börsenverbindung.

Der andere Operand des Fehlers führt über den Forecastrecord direkt zu [outcome_episode](/Users/frnkhrz/Peak_Trade/tests/ops/_bounded_system_episode_fixture_v1.py:323): Dort sind Mittelwert 0,02 und Standardabweichung 0,1 vorgegeben. Der [Calibrationowner](/Users/frnkhrz/Peak_Trade/src/learning/market_intelligence_forecast_calibration_offline_stack_v1/calibration_evidence_v1.py:78) berechnet den Mittelwertfehler aus dem vom Supplier gemessenen Logreturn und dem gelieferten Forecastmittelwert. Die Rückrechnung aus den Originalwerten ergibt exakt dieselben gespeicherten Zahlen. Zwei Bars bedeuten hier einen Return zwischen diesen beiden Closes; weder der vorherige Preis 100 noch der Entry-/Fillpreis ist der Returnanker.

Auch die jüngere typisierte Integration hat einen konkreten Ursprung: [Ihr Testsetup](/Users/frnkhrz/Peak_Trade/tests/learning/test_intelligence_forecast_measurement_integration_v1.py:37) setzt den Mittelwert standardmäßig auf 0,02 und übergibt die Modellbytes als ausdrücklichen synthetischen Platzhalter mit dem Text NO INFERENCE. Der [Freezeconsumer](/Users/frnkhrz/Peak_Trade/src/learning/market_intelligence_forecast_calibration_offline_stack_v1/forecast_measurement_integration_v1.py:98) bindet diese gelieferten Bytes und Metadaten. Das in diesem Test gespeicherte Forecastresultat wurde folglich nicht aus einem dort trainierten Modell berechnet.

## 2. Was von diesem MI-Ergebnis in die Forschung gelangt

Im [tatsächlichen E6-Researchaufruf](/Users/frnkhrz/Peak_Trade/tests/ops/_bounded_system_episode_fixture_v1.py:438) werden der geschlossene Job und genau dessen ursprünglicher Consumer-ACK vor jedem Provideraufruf zurückgelesen. Aus dem ACKhash entsteht die Parentlineage der Experimentidentität. Ein geänderter oder fehlender Abschluss blockiert den Versuch. Das ist eine belegte kausale Zulassungswirkung.

Die numerischen Forschungsdaten werden danach separat erzeugt. Weder der Return 0,0870113769896297 noch der Fehler 0,0670113769896297 wird dort als Preisreihe, Featurewert oder Researchscore eingesetzt. Die Rückverfolgung erreicht hier eine konkrete Zuständigkeits- und Bedeutungsgrenze: Die bestandene MI-Aufnahme erlaubt den nachfolgenden Forschungsaufruf, dessen Zahlen entstehen aus einer anderen Datenquelle.

Im originalen DDO-LearningState dieses Jobs steht außerdem Stateversion 1 mit Folgelabel UNKNOWN. Der numerische Forecastfehler wurde also nicht still zum opaken DDO-Label umgedeutet. Die drei Produkte sind in den Originalrecords unterscheidbar: numerische Calibration, DDO-Zustand und Researchzulassung.

## 3. Woher die Forschungs-Sharpes tatsächlich kommen

Die Werte 0,030562049388796947 und 0,030229745317592854 führen rückwärts über [die Statistik](/Users/frnkhrz/Peak_Trade/src/backtest/stats.py:118) zu den gespeicherten vollen Engine-Equityreihen. Der [Nativeprovider](/Users/frnkhrz/Peak_Trade/src/experiments/canonical_native_research_measurements_v1.py:197) berechnet einfache Equityreturns und verwendet eine Annualisierungsbasis von 1. Die unabhängige Nachrechnung aus den vollständigen gespeicherten Equitywerten reproduziert beide Scores bis auf Rundung unter 1e-15.

Die Equity startet jeweils bei 10.000 und endet für Slow 50 bei 10.136,033743093587 beziehungsweise für Slow 100 bei 10.127,395670007812. Der Backtest erhält die tatsächlich ausgeführten kanonischen MV2-Entscheidungssignale. In beiden Originalreceipts ist der tatsächliche Engine-Signaldigest identisch zum MV2-Replay-Digest und verschieden vom Digest der erzeugten rohen MA-Strategiereihe.

Dieser Unterschied ist semantisch wichtig: Das Feld strategy_provenance beschreibt weiterhin die konfigurierte Strategieeingabe. Es bezeichnet für diese Runs nicht den tatsächlichen Signalowner der Engine. Der [Wiringbody](/Users/frnkhrz/Peak_Trade/src/backtest/mv2_research_wiring_v1.py:2313) führt zuerst die Strategie aus, übergibt deren typisiertes Material an den Core und verwendet im kanonischen Modus dessen Replaysignale für die Engine.

Der MA-Eingang wirkt trotzdem an einer konkreten Stelle: [Der Adapter](/Users/frnkhrz/Peak_Trade/src/backtest/strategy_signal_suitability_agreement_adapter_v1.py:213) erhält den Rohwert 0 oder 1. Sein anfängliches Side-Agreement ist neutral. Erst [der wirkliche Suitabilityconsumer](/Users/frnkhrz/Peak_Trade/src/trading/master_v2/suitability_binding_v1.py:448) interpretiert diesen Wert relativ zur Directional-Assessment-Seite. Bei demselben Epoch 75 und LONG ergibt Slow 50 den Rohwert 1 und AGREE; Slow 100 ergibt Rohwert 0 und NEUTRAL. Diese Consumerprobe wurde direkt mit den rekonstruierten Originaleingängen durchgeführt. Ein neutraler Producerwert alleine hätte die Wirkung daher ebenfalls falsch beschrieben.

Die Rohstrategie stammt aus [der MA-Crossover-Implementierung](/Users/frnkhrz/Peak_Trade/src/strategies/ma_crossover.py:20). Ihre schnelle Periode 10 und die Suchmöglichkeiten 50/100 sind explizite Vorgaben des Researchfixtures. Ihre Kursdaten führen weiter zurück zu [diesem Generator](/Users/frnkhrz/Peak_Trade/tests/backtest/test_parameter_sensitivity_split_observation_v1.py:14): 768 Stundenbars, Preis gleich 100 + 5·sin(i/12) + 0,01·i. Zeitindex und weitere Ausgangsspalten kommen aus [dem Barscaffold](/Users/frnkhrz/Peak_Trade/tests/backtest/test_mv2_research_wiring_v1.py:48); Startkapital, 10 bps Fees und 5 bps Slippage aus [der Konfiguration](/Users/frnkhrz/Peak_Trade/tests/backtest/test_mv2_research_wiring_v1.py:25), der Risk-per-Trade-Wert wird im Generator auf 0,002 gesetzt. Für jeden Kandidaten wurden die vollständigen Daten-/Konfigurationshashes und der Rohstrategie-Signaldigest aus diesen Ursprüngen exakt rekonstruiert.

Damit endet die Herkunftskette bei einer mathematisch erzeugten Testreihe und expliziten Konfigurationszahlen. Die zwei Sharpes sind tatsächliche Ergebnisse der verfolgten Owner auf diesen Eingaben. Sie sind keine aus dem MI-Fehler gelernte Marktprognose. Der Score für Slow 100 ist sogar etwas niedriger.

## 4. Was den E6-Wechsel 50 → 100 tatsächlich auslöst

Hier muss die bisherige verkürzte Zuschreibung an numerische Meta präzisiert werden. Der erste E6-Versuch schlägt Slow 50 mit Priorität 0 vor. Im zweiten Originalrecord steht für Slow 50 ausdrücklich REJECTED_DUPLICATE_WITHOUT_RETEST; Slow 100 wird mit Priorität 0 vorgeschlagen. Die Search-Metaidentität ist None und die Liste passender Meta-Proposals ist leer. Das ursprüngliche Startedjournal enthält zwar einen Meta-Auswertungsschritt, dessen Proposalresultat ist ebenfalls leer.

Der unmittelbare Auswahlgrund in diesem konkreten E6-Beleg ist somit die bestehende Duplikatsperre des schon untersuchten 50er-Kandidaten. Die neue Messung von 100 ist tatsächlich ausgeführt worden. Dieser spezielle Wechsel belegt jedoch keine numerische Meta-Priorisierung. Die unveränderten Originalartefakte bleiben erhalten; ihre frühere Zusammenfassung wird hier genauer eingeordnet.

## 5. Der getrennte, wirklich kausale Meta-Rückweg

[Der bereits ausgeführte Drei-Varianten-Versuch](/Users/frnkhrz/Peak_Trade/tests/experiments/test_measured_meta_next_trial_v1.py:24) liefert einen anderen und stärkeren Beleg. Aus derselben synthetischen Researchreihe werden kontrollierte historische Versuche mit den vorab gesetzten Seeds 55, 56, 57 erzeugt. Der Eingriff ist eine geänderte Bewertungspolicy: OOS-Collapse-Ratio 100 statt 0,5. Diese Seeds erzeugen keine drei unabhängigen Marktpopulationen.

Am [tatsächlichen Robustnessconsumer](/Users/frnkhrz/Peak_Trade/src/experiments/canonical_robustness_suite_v1.py:1301) lautet der Vergleich Holdout-Sharpe kleiner als Train-Sharpe mal Collapse-Ratio. Für den 50er-Versuch sind Train 0,03811009551571799 und Holdout 0,05228598850098903 gespeichert. Mit Faktor 0,5 liegt die Grenze bei etwa 0,019055; mit Faktor 100 bei etwa 3,81101. Der strengere Faktor erzeugt REJECTED_OVERFIT. Das ist ein kontrollierter Policyeingriff auf berechnete Zahlen, kein neu beobachteter Marktschock.

Nach drei passenden historischen Fehlerrecords erzeugt [numerische Meta](/Users/frnkhrz/Peak_Trade/src/experiments/canonical_meta_learning_v1.py:746) eine regionale DEPRIORITIZE_RESEARCH-Proposal. [Der Searchconsumer](/Users/frnkhrz/Peak_Trade/src/experiments/canonical_advanced_search_v1.py:1226) prüft die identische vollständige Parameterregion und addiert -20. Ein weiteres gemeinsames Signal trifft beide Kandidaten. Deshalb erhält Slow 50 insgesamt -40 und Slow 100 -20. [Die Budgetvergabe](/Users/frnkhrz/Peak_Trade/src/experiments/canonical_advanced_search_v1.py:788) wählt bei Budget 1 die höhere Priorität. Bei gleichem Score gilt anschließend die bestehende Ordnung der Hypothesis-ID; das ist keine Rangfolge gemessener Profitabilität.

Zusätzlich zu den ursprünglichen drei Kontrollen wurde jetzt am selben gespeicherten Kandidatenpaar nur dieses regionale Meta-Signal entfernt und der wirkliche Prioritäts-/Budgetconsumer erneut aufgerufen. Mit allen ursprünglichen Signalen wird 100 gewählt. Ohne ausschließlich das regionale Signal sind beide Scores -20, und 50 wird gewählt. Ohne sämtliche Meta-Signale sind beide Scores 0, und ebenfalls 50 wird gewählt. Kandidaten, Budget und übrige Eingaben bleiben dabei gleich. Die gezielte Ursache der Auswahländerung ist damit bis zum konkreten Consumer und zurück zu den drei policybedingt erzeugten Fehlerrecords verfolgt.

## Ergebnis dieser Rückverfolgung

Für diese beiden Korridore sind die Ursprünge und Wirkungen nun konkret benannt: MI-Rechnung aus künstlichen O4-Closes und geliefertem Forecast; DDO-State mit opakem Label; ACK als Zulassungs-/Herkunftskante; separate Sinusdaten als numerischer Researchinput; kanonische Core-Replaysignale als tatsächlicher Engineeingang; E6-Duplikatsauswahl und ein gesondert nachgewiesener regionaler Meta-Prioritätseffekt.

Die quantitative Verbindung vom MI-Lernergebnis zur nächsten eigenen Marktprognose entsteht in diesen verfolgten Aufrufen nicht. Das ist jetzt an der konkreten Weitergabe des ACKs und dem anschließenden separaten Researchinput belegt. Für andere Pfade wird keine Vollständigkeit behauptet. Hier wurde kein Produktcode geändert und kein neuer Backtest, kein Modelltraining oder Betriebsstart ausgeführt; die zusätzlichen Prüfungen waren Inputrekonstruktion, Rechnung aus Originalwerten und begrenzte stateless Consumerinterventionen.

## Anschluss an die vorhandenen Ebenen

[[00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/10 Innere Ebenen der aktuellen Anschlussmodule|Innere Verträge der neuen Anschlussmodule]] · [[00 Systemindex/Betrieb/Wiederanlauf und Stromausfall|Wiederanlauf und Stromausfall]] · [[00 Systemindex/Repoabgleich/Standabgleich mit dem Repository|Aktueller Abgleich und Grenzen]] · [[00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/Konstrukt von IU SL und OPT|Übergeordnetes Konstrukt]]

<!-- Vollständige Leserprojektion; Original: system:00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/09 Konkrete Werte bis zum Ursprung.md; SHA256: 18e70adecfceff4f3d796d911e74e6b439ed18391c765ae14068d114fbf77849. Native Wikilinks beziehen sich auf den ursprünglichen Vault. -->
