---
docs_token: DOCS_TOKEN_CURRENT_PAPER_SHADOW_DATA_ROUTING_SEMANTICS_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Paper-/Shadow-Datenanschlüsse: Semantik vor einer Verschaltungsentscheidung

Untersucht am 9. November 2026 an `eb9633139fa26c44d9c76867e7695f406dfec127`.
Frank verlangt, vorhandene Besonderheiten und semantische Ebenen zu prüfen.
Eine gemeinsame Quelle ist ausdrücklich **keine** Vorgabe: Paper und Shadow
können unterschiedliche Datenströme oder mehrere Quellen verwenden.
OKX-Demohandel bleibt für die Abnahme ausgeschlossen.

Diese Anschlussprüfung ergänzt die
[Kosten-/Paper-/Shadow-Fortschreibung](CURRENT_BWP1_COST_PROVISION_AND_PAPER_SHADOW_V1.md).
Sie definiert weder einen zweiten Datenowner noch eine neue universelle Wahrheit.

## Betriebsart, Quelle und Consumer sind verschiedene Bindungen

Paper beziehungsweise Shadow bestimmen nicht allein, woher Daten stammen.
Der [vorhandene Gateway](../../../src/ops/economic_md_input_producer_v1/purpose_gateway_v1.py)
führt Instrument zu Verwendungszweck zu expliziter Quelle. Jede
[zweckgebundene Quelle](../../../src/ops/economic_md_input_producer_v1/purpose_consumers_v1.py)
besitzt ihre eigene Speicherwurzel und Policy. Es gibt keine Bedingung, dass
alle Verwendungszwecke denselben Speicher verwenden müssen. Eine geänderte
Quellenzuordnung ändert den gebundenen Profildigest.

Die [begrenzte Offline-Session](../../../src/ops/bounded_peaktrade_system_composition_v1/session_v1.py)
liest RANKING, TRADING, LIQUIDITY, OUTCOME und RESEARCH über ihre jeweiligen
Originaladapter. Ihr Datenprofil ist an ein Instrument und eine Episode
gebunden. Das ist kein automatischer Beleg für alle Zwecke in einem dauerhaften
Fünfslotbetrieb. Die konkrete Versorgung wird an ihren Aufrufen geprüft.

## Verschiedene vorhandene Paper-/Shadow-Konstruktionen

Der [generische ShadowPaperSession-Pfad](../../../src/live/shadow_session.py)
erhält eine ausdrückliche CandleSource und einen Strategy-/ExecutionPipeline-
Anschluss. Seine Factory lehnt eine fehlende Datenquelle ab. Seine konfigurierten
Gebühren-/Slippagewerte sind keine aus einem aktuellen Orderbuch gemessenen
Kontokosten. Diese Konstruktion wird nicht allein wegen ihres Namens zum
heutigen Master-V2-/Double-Play-Pfad erklärt.

Der [Cap-5.2-Collector](../../../src/ops/single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1/public_md_capture_v1.py)
liest öffentliche Markpreise und materialisiert damit einen Templatekörper.
Er belegt dadurch keine vollständige Orderbuchtiefe, private Gebührenquelle
oder komplette wirtschaftliche Inputherkunft aller Templatefelder.

Der [integrierte Wallclock-Beobachtungspfad](../../../src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/session_runtime_v1.py)
bindet einen eigenen Public-MD-Transport. Seine Evidence führt ausdrücklich
`paper_execution=False`. Ein beobachteter Zyklus aus diesem Pfad wird nicht
als simulierter Paperfill ausgegeben.

Der [kanonische Shadow-Execution-Entrypoint](../../../src/ops/canonical_shadow_runtime_enablement_v1/shadow_cycle_entrypoint_v1.py)
ist ein eigener simulierter Anschluss nach PRE_EXTERNAL mit getrennten
Aktivierungs- und Beobachtungsbedingungen. Seine Existenz aktiviert ihn nicht.
Die Herkunft früherer Konstruktionen und ein tatsächlicher dauerhafter Lauf
sind mit diesen heutigen Codebeobachtungen nicht vollständig rekonstruiert.

## Semantische Bedingungen der jeweiligen Übergabe

- **Instrument und Quelle:** Kanonische Identität, native Venueidentität,
  Universumsbindung und zugelassener Kanal bleiben erhalten. Ein anderes
  Instrument oder ein anderer Kanal wird nicht anhand eines ähnlichen Namens
  eingesetzt. Die zulässige Kandidatenmenge kommt weiter aus Cap21.
- **Preisfamilie und Zweck:** Mark, Index, Last und Bid/Ask bleiben verschiedene
  Werte. Die ursprüngliche Rankingprojektion verlangt 61 finale PT1M-Markwerte
  und erlaubt keinen Ersatz durch gewöhnliche OHLCV-Schlusskurse. Der Core
  erhält seine ursprünglichen C1-/Mark-/Indexbindungen; Kosten brauchen die
  tatsächlich erreichbare Orderbuchseite und native Mengen.
- **Einheiten:** Kontrakte, Basisasset, Quote-/Settlementwährung und USDC
  werden nicht gleichgesetzt. Der Kostenanschluss behält seine ursprüngliche
  Geldnormalisierung und Feegruppen-/Accountbindung.
- **Zeit und Wissen:** Ereigniszeit, Capture-/Kenntniszeit, Wirksamkeitszeit,
  Intervallbeginn und Finalisierung bleiben getrennt. Die
  [Zweckzulassung](../../../src/ops/economic_md_input_producer_v1/purpose_admission_v1.py)
  schließt nach dem jeweiligen As-of erst bekannt gewordene Daten aus.
  Eine spätere Korrektur ersetzt nicht still den damaligen Entscheidungsinput.
- **Messhorizonte:** Der C1-/Ranking-Minutenpfad ist nicht der ursprüngliche
  PT1H-/N-Bars-Outcomehorizont. Auch Fundingzeitpunkt, Positionsdauer und
  Rotationswartefrist sind keine gegenseitigen Aliase.
- **Fehlende Größen:** Der ursprüngliche LIQUIDITY-Consumer liefert für bloßes
  Top-of-Book weder vollständige Tiefe noch ADV oder Slippage. Er setzt dafür
  `CANNOT_EVALUATE`, fehlende Größen und `risk_admitted=False`. Dieser Output
  darf nicht als vollständiger positiver Kosten-/Risikoinput weitergereicht werden.
- **Private Wahrheit:** Kontokapital, private Gebühren, bestätigte Fills und
  Fundingbuchungen behalten ihre eigenen Owner. Ein öffentlicher Funding-Satz
  mit Zeitpunkt ist keine schon gebuchte Geldzahlung. Die vorhandene Funding-
  Factstruktur enthält zudem nicht automatisch alle künftig nötigen Vorsorgefelder.
- **Lernen und Research:** Ein späterer Outcome und eine Researchreturnreihe
  sind keine damals verfügbaren Handelsinputs. Die getrennten Marktforecast-,
  DDO-/Learning-, Research- und Applyconsumer behalten ihre Zulassung und Wirkung.
  Ein gemeinsamer Preisinput allein verändert kein gespeichertes Modell.

## Geprüfte Mehrquellen-Gegenprobe und verbleibende Verschaltung

Zwei unabhängige synthetische Factstores wurden am unveränderten Originalgateway
verwendet: RANKING und LIQUIDITY aus A, TRADING und RESEARCH aus B, OUTCOME über
seinen PT1H-Originaladapter. Unterschiedliche numerische Werte blieben bei ihren
jeweiligen Quellen sichtbar. Ein Quellenwechsel änderte den Profildigest;
später erfasste Korrekturen blieben am früheren As-of ausgeschlossen.

Diese Gegenprobe belegt die getrennte Auswahl und den tatsächlichen Verbrauch
durch diese Adapter. Sie belegt **keinen** automatisch richtigen Abgleich
widersprechender Quellen und keine gemeinsame Core-/Finanzzulassung. Für eine
spätere Zusammenführung braucht es pro Consumer eine ausdrückliche Quellenwahl,
Zeitabstimmung und Behandlung von Abweichung/Ausfall. Ein Fallback wird nicht
stillschweigend aus einem anderen Verwendungszweck abgeleitet.

44 ausgewählte vorhandene Daten-/Semantik-/Offline-Consumerfälle bestanden am
genannten Stand. Darin enthaltene synthetische N1-/N5-Verbindungen werden nicht
zu einem realen Paper-/Shadow-Dauerlauf oder zu kompletter Instrumentabdeckung
umgedeutet. Die Quellenbindung und Fallgrenzen stehen im
[Prüfbeleg](../evidence/CURRENT_PAPER_SHADOW_DATA_ROUTING_SEMANTICS_V1_2026-11-09.json).

Die weitere Kosten-/Fundingzulassung bleibt Teil von BWP1. Der durchgängige
Mehrbereichsbetrieb und die gemeinsame Abnahme gehören weiterhin zu den
entsprechenden Betriebs- und Endsystemkriterien des
[bestehenden Paketplans](CURRENT_SYSTEM_FIVE_BOUNDED_WORK_PACKAGES_V1.md).

## Ergänzender Obsidian-Abgleich

Auf Franks ausdrücklichen Hinweis wurden die datierten lokalen DATA-, S01-/S06-,
E06-/E12-/E24-Notizen und die unabhängige Marktbeobachtung nachgelesen. Ihre
Pfad-/Byte-/Datumsbindung steht im Prüfbeleg. Die Notizen sind Wissensquellen;
ihre alten Fertig- oder PROVEN-Aussagen wurden nicht als neue Abnahme übernommen.

Der dort benannte
[Existing-Fact-MI-Anschluss](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_context_existing_fact_mi_bridge_v1.py)
verarbeitet einen eigenen Marktcontext und begrenzt seine Wirkung ausdrücklich
auf Offlinebeobachtung. Der
[unabhängige Messpfad](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/independent_market_forecast_measurement_v1.py)
benötigt weder Dummyentscheidung noch Lane. Eine künstliche gemeinsame
Handels-/Slotidentität für sämtliche Marktbeobachtung wäre daher falsch.

E06 behandelt öffentliche Funding-/OI-Kontexte; E12 behandelt private Bills und
bereits gebuchte Nettobewegungen. Diese Quellen sind kein Ersatz füreinander.
Die [ursprüngliche Billsbeobachtung](../../../src/ops/okx_eea_private_account_state_runtime_v1/bills_observation_v1.py)
behält ihre ID-/Account-/Währungs- und Kontinuitätsgrenze. Ein gelieferter
Netto-Billbetrag darf nicht nochmals um seine bereits enthaltenen Gebühren oder
Fundingkomponenten erhöht werden.

Die ebenfalls nachgelesene Shadow-/Reality-Gap-Notiz unterscheidet gemessene
Backtestwerte von gesondert gelieferten Shadowbeobachtungen. Der aktuelle
[Native-Research-Provider](../../../src/experiments/canonical_native_research_measurements_v1.py)
übernimmt Gapdimensionen aus seinem expliziten Context; er erzeugt damit keine
unabhängige natürliche Slippage- oder Fundingmessung. Genau diese Provenienz
muss auch eine spätere Paper-/Shadow-Datennachführung erhalten.
