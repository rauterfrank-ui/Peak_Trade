---
docs_token: DOCS_TOKEN_CURRENT_CONTINUOUS_DOUBLE_PLAY_ECONOMIC_SEMANTICS_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Wirtschaftliche Bedeutung des fortgesetzten Double-Play-Kreises

## Auftrag und heutige Quellen

Nutzerpräzisierung vom 9. November 2026: Ein ausgewähltes Instrument soll im
belegten Slot fortlaufend Double-Play-Zyklen durchlaufen. Wird es relativ zu
anderen zulässigen Instrumenten zu schwach, soll die vorhandene Rotation einen
stärkeren Kandidaten zuführen. 24/7 bezeichnet diesen Betriebsablauf, keine
einzelne unendlich lange Position, keinen festen Tradegewinn und keine Erlaubnis,
offene Positionen oder Kapitalbindungen beim Instrumentwechsel zu verwerfen.
Dies ist das Ziel; ein durchgängig autonomer produktiver Betrieb ist damit nicht
nachgewiesen.

Die Prüfung beginnt am aktuellen Merge
`f7f6ad36e91016c93935d2f90ce9d9a125fa6000`. Bestehende Ranking-, Selection-,
Membership-, Slot- und Coreverträge werden verwendet. Frühere Implementierungen,
Parameter oder ein neues pauschales Profit-/Survivalgate werden nicht importiert.

## Was bereits definiert und angeschlossen ist

Die [Rankingmatrix](../../../src/ops/peak_trade_ranking_matrix_policy_v1.py)
definiert BALANCED_MOVEMENT_STRUCTURE. Der
[Merkmalsowner](../../../src/ops/peak_trade_ranking_feature_production_v1/pure_compute_v1.py)
verwendet 61 zusammenhängende finale PT1M-Markpreise: 60 Logreturns,
nicht annualisierte Populationsstreuung und die mittelpreisrelative Amplitude.
Volatilität hat die Einheit Per-Bar-Dezimalreturn-Volatilität; Amplitude ist
dimensionslos. Die
[Scorebildung](../../../src/ops/peak_trade_economic_ranking_runtime_v1/score_construction_v1.py)
gewichtet deren relative Midrank-Perzentile jeweils mit 0,5. Cap22 erzeugt die
Rangfolge; Auswahl und Rotation konsumieren sie ohne eigenes Rescoring.

Zwei Zeitverträge sind getrennt vorhanden:

- [Cap23](../../../src/ops/single_selected_future_policy_v1/selection_v1.py)
  führt Refresh, Mindesthaltezeit und Ranghysterese. Seine Moduldefaults sind
  300 Sekunden, 3600 Sekunden und ein Rang. Aufrufinputs bleiben maßgeblich;
  die Defaults sind keine Messung aktuell laufender Betriebsparameter.
- Der [Membershipselector](../../../src/ops/mf_membership_selector_and_rotation_runtime_contract_v1.py)
  führt seine Mindesthaltung über zwei unterschiedliche Rankingbeobachtungen
  in der ursprünglichen Artefaktkette. Wiederholung desselben Snapshots zählt
  nicht erneut. Das ist kein Zwei-Sekunden- oder Zwei-Minuten-Vertrag.
  Abwesende oder unzulässige Mitglieder haben ihre eigene Forced-Removal-Regel.

Die [Lane-Publikation](../../../src/ops/current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1/checked_publication_v1.py)
bindet Membership, tatsächlichen Ranking-Snapshot, Cap23-Auswahl und Topologie
aneinander. Der [positionsbewusste Rotationsowner](../../../src/ops/hard_facts_system_closure_v1/position_aware_rotation_v1.py)
trennt Vorschlag und Commit. Offene oder nur teilweise reduzierte Positionen
behalten ihre Zuständigkeit. Ein Wechsel verlangt unter anderem bestätigtes Flat,
Reconciliation und keine widersprechende Pending-Custody.

Die [Post-Close-Fortsetzung](../../../src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/post_close_continuation_v1.py)
prüft den ursprünglichen Close, die originale Kapitalfortschreibung und die
Rang-/Membershipentscheidung. Ihre dauerhafte Übergabe erreicht Cap24 und den
tatsächlichen nächsten N1/S7-Coreaufruf. KEEP setzt am gebundenen Instrument fort;
REPLACE bindet das neue Instrument über die bestehenden Owner. ACK-Replay und
verlorener ACK sind eigene Fälle. Dies wird im begrenzten injizierten Pfad
geprüft, nicht als unbegrenzter natürlicher Livebetrieb behauptet.

## Was Ranking nicht behauptet

Eine relative Rangfolge beantwortet, welcher zulässige Kandidat im gegebenen
Vergleich stärker bewegt ist. Wenn alle Kandidaten proportional schwächere
Rohmerkmale haben, können Reihenfolge und Scores gleich bleiben. Der
[kausale Test](../../../tests/ops/test_current_ranking_economic_semantics_v1.py)
prüft dies am wirklichen Cap22-Producer mit verschieden schwachen synthetischen
Inputs und weiterhin unterschiedlichen Evidenzdigests.

Dies ist korrekt für den vorhandenen Rankingzweck. Der Score ist weder ein
erwarteter Nettogewinn noch ein Liquidationsabstand oder Survival-Ratio. Eine
neue absolute Eignungsgrenze darf daraus nicht stillschweigend entstehen.

## Kosten, Bruttoedge und Survival

Der aktuelle [native Survivalbuilder](../../../src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py)
setzt Kosten, Bruttoedge und vier Survival-Ratios weiterhin auf feste Replaywerte.
Sein [Survivalowner](../../../src/trading/master_v2/survival_assessment_v1.py)
addiert Kosten und vergleicht Ratios mit den übergebenen Grenzen. Das Vorhandensein
dieser Felder belegt weder produktive Herkunft noch eine vollständige Definition
von Zähler, Nenner, wirtschaftlicher Einheit und Horizont.

Bestehende andere Quellen sind zweckgebunden: Der
[Fundingowner](../../../src/backtest/funding_model_v1.py) modelliert explizite
Offlinezahlungen an Zahlungsereignissen; der
[Roundtripledger](../../../src/ops/integrated_paper_shadow_observation_session_v1/simulated_economics_round_trip_ledger_v1.py)
misst simulierte abgeschlossene Zyklen und offene Lifecycleanteile. Der
[Fee-Observer](../../../src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/fee_observed_predicate_v1.py)
verlangt tatsächliche identitätsgebundene Fillgebühren samt Gebührenwährung.
Der [Shadow-Assembler](../../../src/ops/productive_pure_stack_numeric_policy_shadow_campaign_v1/shadow_survival_envelope_assembler_v1.py)
verweigert ausdrücklich produktive Grenzwerte und SurvivalResult-Zuordnung.
Keine dieser Quellen wird durch einen ähnlichen Namen zum heutigen positiven
Survival-Inputproducer.

Für die weitere Untersuchung ist der bereits definierte Handelskreis die
Bezugsgröße: Slot-/Instrumentepisode, einzelne Positionszyklen, Fillereignisse
und Fundingereignisse müssen getrennt bleiben. Zeitfenster der Instrumentrotation
sind kein automatisch gültiger Forecast-/Funding-/Risikohorizont. D_t ist eine
Scopegröße und kein belegter erwarteter Tradegewinn.

Es wird zunächst geprüft, welche Anforderungen vorhandene Markt-, Kapital-,
Margin-, Mengen-, Reconciliation- und Ausfallverträge bereits erfüllen. Eine
zusätzliche Gewinnprognose oder Survival-Quote wird erst nach einer belegten
fachlichen Notwendigkeit als mögliche Weiterentwicklung vorgeschlagen.
Vorhandene native Gates werden hier weder entfernt noch umgangen. Die
[numerische Zulassung](CURRENT_SURVIVAL_NUMERIC_ADMISSION_V1.md) und die
[Versuchssperre](CURRENT_CORE_ENTRY_ATTEMPT_ADMISSION_V1.md) bleiben erhalten.

## Gegenprüfung: Stillstand, Rotation und native Quoten

Franks Rückfrage vom 9. November wird im Arbeitsstand auf Basis von
`304719c94030ff9aacdf2571e2ae56533f9e6a25` am heutigen Consumerpfad geprüft.
Die heutige Implementierung belegt zwei unterschiedliche Verwendungen:

- Gemessene Volatilität und Amplitude erreichen die relative Cap22-Rangfolge.
  Der Membershipselector erhält Instrument-ID und Rang; der tatsächliche
  [Post-Close-Consumer](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_post_close_feedback_v1.py)
  ruft diesen Selector nach den getrennten Close-/Reconciliation- und
  Kapitalprüfungen auf. Erwartete Bruttoedge und native Survival-Ratios sind
  keine Inputs dieser Rotationsentscheidung.
- Der native Replaybuilder setzt `expected_gross_edge=0.02`, drei Ratios auf
  `0.8` und den Liquidationspuffer auf `0.2`. Nach der Richtungsbewertung werden
  diese Werte vom Survivalowner für das bereits gebundene Instrument geprüft.
  Survival erreicht Suitability und Composition und kann den neuen Entry
  sperren. Daraus entsteht kein Instrumentwechselauftrag.

Insbesondere ist `volatility_survival_ratio` keine gemessene Rankingvolatilität.
Der [typisierte Volatilitätsvertrag](../../../src/trading/master_v2/canonical_volatility_estimate_typed_consumption_contract_v1.py)
führt diese Größe ausdrücklich als Non-Alias. Eine Transformation aus
Rankingamplitude oder -volatilität in die festen Quoten ist am untersuchten
Pfad nicht implementiert. Der Name allein belegt auch keine frühere Absicht.

Die ergänzte [Verbundprobe](../../../tests/ops/test_current_ranking_economic_semantics_v1.py)
berechnet beide Merkmale mit den Originalrechnungen aus ausdrücklich
synthetischen 61-Mark-Fenstern. Sie führt die Ergebnisse durch den Original-
Cap22-Producer sowie Selector, Writer und Cold-Read der Membershipkette:

- Nur ETH steht still: ETH fällt hinter die fünf weiter bewegten Kandidaten.
  Die erste neue Beobachtung erhält die bisherigen Mitglieder; nach der
  bestehenden Mindesthaltung ersetzt DOT das schwache ETH. Reordering der
  gehaltenen Mitglieder bleibt vom tatsächlichen Austausch unterschieden.
- Alle sechs stehen still: Beide Rohmerkmale sind null. Alle sechs bleiben
  relativ zulässig und erhalten den gleichen Score `0.5`; die deterministische
  Tie-Reihenfolge kann weiterhin die Membership ändern. Das ist keine
  absolute Mindestbewegungs- oder Kostendeckungsprüfung.
- Readback und Replay desselben Snapshots schaffen keine neue Beobachtung.

Dabei wurde ein konkreter Identitätsfehler im
[Rankingproducer](../../../src/ops/productive_futures_ranking_producer_v1/producer_v1.py)
sichtbar: Seine bisherige Default-ID berücksichtigte die wirtschaftliche
Merkmalsmessung nicht. Neue Merkmale bei gleichem Universum konnten deshalb
dieselbe ID mit verändertem Integritätsdigest erhalten; der Selector verweigerte
diese widersprüchliche Identität korrekt. Die Default-ID bindet nun zusätzlich
den ursprünglichen Merkmalsdigest und den Universe-Payloaddigest. Unveränderte
Messung und Quellen behalten bei späterer Neuberechnung ID und Integritätsdigest.
Explizite Caller-IDs sowie die Lesbarkeit bestehender Records bleiben erhalten.
Rankingformel, Haltebedingung und Survivalgates werden dadurch nicht geändert.

Die ausdrückliche Erhaltungsbedingung für den Wiederanlauf bleibt bestehen:
Der [ursprüngliche Topologieleser](../../../src/ops/current_mf_n5_durable_lane_assignment_persistence_v1/persistence_v1.py)
stellt exakt die gespeicherten Slot-/Instrumentzuordnungen wieder her und führt
keine Mappingtransition aus. Der
[Supervisor-Startadapter](../../../src/ops/n1_standing_pre_external_runtime_supervisor_v1/startup_binding_v1.py)
und die [Kapitalrecovery](../../../src/ops/portfolio_capital_reservation_budget_v1/recovery_v1.py)
bleiben unverändert. Die neue Default-ID betrifft neue Rankingproduktion;
beim Lesen alter Records wird keine ID neu berechnet oder migriert.
Eine zusätzliche Kompatibilitätsprobe persistiert einen synthetischen Record
mit dem exakten bisherigen ID-Algorithmus und prüft Original-Readback und
Membership-Replay ohne Änderung seiner gespeicherten Dateien.

Diese Probe belegt die numerische Verbindung und die dauerhafte
Membershipentscheidung. Sie ersetzt weder die Zulassung öffentlicher Originalfacts
noch echte Kontocustody, eine Venueausführung oder einen autonomen Dauerhost.
Die fachlich belastbare absolute Kosten-/Risikozulassung bleibt Bestandteil des
offenen [ersten Arbeitspakets](CURRENT_SYSTEM_FIVE_BOUNDED_WORK_PACKAGES_V1.md).

## Abschluss dieses Untersuchungsschritts

Bestehende ökonomische Rankinginputs, Zeitverträge und tatsächliche Fortsetzung
sind am aktuellen Code und ausgewählten Ownerprüfungen gebunden. Der einzelne
alte Rankingtest, der BTC implizit als verboten verwendete, erhält stattdessen
einen ausdrücklich suspendierten Kandidaten. Eine zusätzliche positive BTC-Probe
erhält die heutige Zulassung. Die Produktionsfilter bleiben unverändert.

Der [Prüfbeleg](../evidence/CURRENT_CONTINUOUS_DOUBLE_PLAY_ECONOMIC_SEMANTICS_2026_11_09.md)
trennt diese Quellenklärung von noch nicht belegter produktiver Kosten-/Survival-
Ableitung und der Gesamtabnahme. Die weiteren Punkte sind die tatsächliche
Risiko-/Mengenverwendung und Ausfallkoordination, jeweils mit eigenem Commit.
