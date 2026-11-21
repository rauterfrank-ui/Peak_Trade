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

## Unabhängige O4-Messquelle für das I17-Instrument

Der [Archivsammler](../../../scripts/ops/capture_offline_learning_mark_window_v1.py)
und der [Archivleser](../../../src/research/offline_recorded_mark_horizon_source_v1.py)
prüfen dieselbe Instrumentbindung. Für das aktuelle I17-Profil sind kanonische
und native ID `ETH-USD_UM_XPERP-310404`. Die Bindungsdatei enthält beide IDs,
`venue=OKX`, den `mapping_digest` des kanonischen OKX-Resolvers sowie die
passende öffentliche Instrumentzeile unter `instrument_metadata`. Deren
Instrumenttyp, Status, Kontraktart, Settlement und Underlier müssen zum
gebundenen Profil passen. Die Bindungsdatei wird über SHA256 angegeben.
Alle Seiten dieses Profils müssen den öffentlichen EEA-Host und die native ID
im Requestbeleg führen. Das ältere `ETH-USDT-SWAP` bleibt ein separates
Archivprofil. Die Preiseinheiten sind USD pro ETH für XPERP und USDT pro ETH für
SWAP.

Das ausdrücklich angeforderte Stundenfenster muss vollständig aus originalen,
finalisierten Minuten bestehen. Die resultierenden O4-Bars stehen für die
Messung frühestens beim tatsächlichen Empfang aller zugehörigen Seiten zur
Verfügung. Die Offline-Gegenprobe verwendet Testantworten. Sie belegt den Weg
vom Sammler bis zum unabhängigen O4-Consumer; sie liefert weder ein ausgeführtes
Geschäft noch die Attribution an eine versiegelte I17-DDO-Entscheidung oder eine
Zulassung für GVEF.

## Slot- und Signalzuordnung vor dem kontinuierlichen Kartenanschluss

Lesender Abgleich vom 18. November 2026 gegen den Merge von PR #7340,
`351728852b6e48be09ad5c3fc3e7d2d670aba40c`. Die uncommittierte Vorarbeit im
Worktree `peaktrade-zkp-entry-liquidity` hat die Basis `3e4bbe45b` und wird
ausdrücklich getrennt bewertet. Der
[Zuordnungsbeleg](../evidence/INSTRUMENT_CARD_SIGNAL_ASSIGNMENT_2026-11-18.json)
bindet fünf Slotadressen, 25 Signalgruppen, elf offene Anschluss-/Prüfpunkte
und 36 Quellreferenzen an Pfad, Revision, Zeile und SHA-256.

Diese Ergänzung ist ein Arbeitsbefund für die Anschlussentwicklung. Sie
ersetzt weder die Ranking-/Cap23-/Cap24-Auswahl noch eine Betriebsfreigabe.
Die historischen Startzeiten und Blocker des lokalen Vorbereitungsplans sind
keine neuen Startaufträge und werden nicht ungeprüft als heutiger Status
übernommen. Die fünf dort geplanten Sitzungswurzeln sind beim Abgleich nicht
vorhanden; daraus folgt keine Aussage über andere oder inzwischen beendete
Sitzungen.

### Zuordnung und vorhandene Bündel je Slot

- **LANE_1 / ZKP / Paper:** `ZKP-USD_UM_XPERP-310905`. Der gemeinsame
  XPERP-Collector bindet 13 öffentliche Quellen an den Markt. Der bestehende
  Paper-Einstieg übergibt Mark, Index, Buch-Bid/Ask, 24h-Kontraktvolumen, OI,
  Funding, finale C1 und typisierte G17-Volatilität an die Originalconsumer.
  Nach dem Erstfill führt `ZkpPaperContinuationV1` denselben Instrument- und
  Entscheidungszustand fort. Der fortlaufende Kartenhook ist lokale Vorarbeit.
- **LANE_2 / UP / Paper:** `UP-USD_UM_XPERP-310919`. Gleicher Collector und
  gleiche fachliche Consumer wie ZKP, mit eigener Slot-/Instrumentbindung,
  Sitzungswurzel, Originalcursor und Buchhaltung. Die lokale Slotdatei und die
  Research-Kampagne stimmen in beiden Instrument-IDs, Lane und Betriebsart
  überein. Eine laufende Kartenversorgung ist dadurch noch nicht belegt.
- **LANE_3 / BTC / separat:** `BTC-USD_UM_XPERP-310328` steht im
  Vorbereitungsplan als Testnet-Referenz. BTC wird nur zur Abgrenzung genannt;
  weder sein Anschluss noch seine Freigaben oder Zustände werden bearbeitet.
- **LANE_4 / IRYS / Paper:** `IRYS-USD_UM_XPERP-310530`. Der Code unterstützt
  denselben isolierten Paper-Pfad. Die historische Konfiguration passt in
  Instrument und Lane, trägt aber `environment=PAPER` statt des vom heutigen
  `--slot-config`-Leser verlangten `surface=PAPER_EXCHANGE`. Sie ist deshalb
  noch kein unverändert konsumierbarer Starterinput. Das Original bleibt
  erhalten; die Schemaanpassung gehört zur folgenden Anschlussarbeit.
- **LANE_5 / SOPH / Shadow:** `SOPH-USD_UM_XPERP-310912`. Der vorhandene
  I17-Resolver und die lokale Slot-/Kampagnenbindung nennen diesen datierten
  Kontrakt. Das ältere `SOPH-USDT-SWAP` ist ein anderes Instrument. Der
  gemergte Shadow-Transport liefert Mark und Ticker; dies ist noch nicht der
  vollständige Kartenquellensatz. Die vollständige Quelle und der Kartenhook
  sind im Entwurf begonnen. Ein aktueller Slotbudget-Owner ist nicht gebunden.

Die drei Paper-Instrumente besitzen somit bereits einen gemeinsamen
Marktdaten- und Handelsconsumerpfad. SOPH besitzt einen eigenen
Shadow-Beobachtungs-/DDO-Pfad. Ein identischer Kartenvertrag verlangt
vollständige, semantisch passende Pflichtwerte aus dem jeweiligen Pfad.
Das Vorhandensein der historischen Kampagnendateien belegt die geplante
Slot-/Empfängerzuordnung, keinen gestarteten Research-Worker.

### Bedeutung und Verwendung der Kartenwerte

Die 13 öffentlichen Eingänge sind `instrument`, `tiers`, `mark`, `index`,
`book`, `ticker`, `open-interest`, `trade-candles`, `mark-candles`, `adv`,
`funding`, `funding-history` und `usdc-index`. Für jeden Eingang führt der
Zuordnungsbeleg Producer, Transformation, Consumer, Einheit, Zeitbezug,
Persistenz und Aussagegrenze. Die folgenden Übergänge sind besonders relevant:

- **Mark, Index und Last:** Mark taktet die ursprüngliche Handelsbewertung.
  Index behält seine unabhängige Preisprovenienz. Last ist ein eigener
  Tickerwert. Preise in diesen vier Kartenslots sind USD je Basisasset;
  native Kontraktmengen werden mit dem jeweiligen Multiplikator umgerechnet.
- **C1 und G17:** Finale gehandelte Minutenkerzen liefern den ursprünglichen
  Feature-/Preisreiheninput. Die finale PT1M-Markhistorie liefert die typisierte
  Volatilität. Eine laufende Shadowtick-Reihe ersetzt diese beiden Fenster
  nicht automatisch. O4 bleibt ein späterer Stunden-Outcomehorizont.
- **Volumen und OI:** Das im Paper-Core gebundene `volume` stammt aus
  `vol24h` in Kontrakten; OI ist ebenfalls eine Kontraktzahl. ADV ist dagegen
  durchschnittlicher USD-Tagesumsatz aus abgeschlossenen UTC-Tagen. Keiner
  dieser Werte ist Slotkapital oder Kontogewinn.
- **Spread, Tiefe und Slippage:** Spread wird relativ zum Buchmittel in
  Basispunkten berechnet. Slippage vergleicht den für die konkrete Seite und
  Kontraktmenge erreichbaren, nachteilig gerundeten Buchpreis mit dem Mark.
  Fehlende Tiefe ist kein positiver Messwert. 88 Basispunkte bedeuten 0,88 %.
- **Budget und Sizing:** 25 USDC sind die Testallokation. Aktuelle Equity,
  geltendes Slotlimit, reservierte Mittel, freie neue Exposition und
  Kostenreserven sind getrennte Größen. `reserved_amount=null` im Entwurf
  bedeutet keinen belegten Nullbestand. Die gemeinsame Budgetrechnung weist
  nominale Kapazität vor Gebühren und Risiko-Sizing aus; die endgültige Menge
  bleibt beim vorhandenen Risiko-/Sizing-Owner.
- **Notional und Marktteilnahme:** Kontraktmenge mal Multiplikator mal
  relevantem USD-Preis ergibt den Orderwert. Orderwert geteilt durch ADV
  ergibt die Marktteilnahme. Budget/ADV ist eine gesonderte Kennzahl und nur
  bei entsprechendem Orderwert dieselbe Rechnung. Die USDC/USD-Umrechnung
  stammt aus einem eigenen zeitgebundenen Index.
- **Richtungswechsel:** Zielposition und ausgeführte Nettomenge bleiben
  getrennt. Bei +69 LONG auf −73 SHORT sind 142 SELL-Kontrakte auszuführen.
  Diese Nettomenge braucht den Tiefe-/Slippagenachweis; das Budget der neuen
  Zielposition ist nicht einfach der gesamte ausgeführte Umsatz.
- **Entscheidung und Wirkung:** Long/Long oder Short/Short ist die
  ursprüngliche Richtungsbestätigung. Finanz-/Kosten-/Liquiditätsadmission,
  simulierter Fill und Buchung folgen mit ihren eigenen Originalbelegen.
  Ein Kartenstatus `EVALUATED` ist keine positive Einstiegsfreigabe.
- **Funding und Lernen:** Die aktuelle öffentliche Rate ist Kontext und
  Reserveinput. Eine realisierte Rate wird erst mit dem gehaltenen Bestand
  und der Paper-Settlementreferenz gebucht. Abgeschlossene Paper-Episoden
  gelangen über ihr Originalarchiv an DDO/GVEF. SOPH-Shadow liefert über
  finale O4-Bars einen kontrafaktischen Preisverlauf; dieser ist kein
  realisierter Kontogewinn. Forecast, DDO, Optimierung, Meta und Apply behalten
  ihre eigenen Quellen-, Zeit- und Autoritätsgrenzen.

### Offene Anschlüsse und Härtungsnachweise

Der Quellabgleich bestätigt noch keine durchgängige Kartenversorgung:

1. Die Paper-Sitzungen erzeugen feste Instrument-/Slotbindungen, aber leere
   Ranking-/Universumsfelder. Die vollständige Ranking-/Cap23-/Cap24-Identität
   samt Generation ist noch nicht bis in den kontinuierlichen Stream belegt.
   Der versiegelte Offline-Kartenadapter prüft diese Identitäten bereits an
   seiner eigenen Schnittstelle; das ersetzt die fehlende Übernahme nicht.
2. Die kontinuierlichen Hooks, Kartenfassungen und Readbacks liegen lokal.
   Eine neue Quellen-/Budgetfassung muss bis zum tatsächlich konsumierten
   Master-V2-Input und dessen Entscheidung verfolgt werden. Originalcursor
   und Zustandswriter dürfen dabei nicht dupliziert oder zurückgesetzt werden.
3. Der gemergte Shadow-Marktkontext verwendet Index=Mark sowie feste Werte
   für Volumen, OI und Funding. Zusätzlich verwendet die Bridge
   `FuturesMarketType.PERPETUAL`, Tick-Finality und Marktick-Features, während
   SOPH hier ein datierter Future ist. Die Gleichheit von Kartenanzeige und
   fachlich richtigem Entscheidungsinput ist deshalb noch offen.
4. Der SOPH-Budgetcallback ist ungebunden. Im Entwurf prüft der Shadow-Gate
   einen positiven Betrag und Mindestmengenliquidität auf irgendeiner Seite.
   Das belegt noch keine budgetbezogene Zulassung der gewählten Seite und
   tatsächlichen Sizing-/Nettoausführungsmenge.
5. Der Paper-Budgetentwurf unterscheidet `available_amount` und
   `available_for_new_entry`, berechnet die nominale Kartenkapazität aber aus
   ersterem. Bei offener Position muss der Consumer diese Bedeutung erhalten;
   daraus darf keine zusätzliche freie Allokation entstehen.
6. Ablauf am tatsächlichen Kartenleser, Datenabriss, Wiederaufnahme,
   Versionswechsel, Quellenverwechslung und Isolation der anderen Instrumente
   brauchen durchgängige Offline-Gegenproben. Ein gespeichertes `latest.json`
   allein belegt keine fortdauernde Frische.
7. IRYS benötigt die oben genannte Anpassung des konkreten Starterinputs.
   Paper- und Shadow-Lernempfänger behalten ihre unterschiedlichen
   Originalnachweise. Die vollständige Inventur und Härtung aller weiteren
   Systemverzweigungen bleibt ein eigener offener Teil des Gesamtauftrags.

Geprüft wurden Quellanker und Bytes gegen die Mergebasis, die fünf
Konfigurations-/Kampagnenhashes, alle fünf Kampagnenidentitäten sowie die vier
betroffenen Slotidentitäten gegen ihren Code. Es wurden keine neuen
Produkt- oder Integrationsprüfungen ausgeführt und keine Handels-/Shadow-
oder Paper-Sitzungen gestartet. Der Launcher im lokalen `main` meldete eine
Umgebungs-Fingerprintabweichung; dort wurde keine Python-Ausführung
fortgesetzt und kein Bootstrap vorgenommen. Der zuvor geprüfte
Arbeitsworktree hatte einen bestandenen `runtime-check`. Diese Zuordnung
ändert ausschließlich Dokumentation und behauptet keine abgeschlossene
Härtung oder Gesamtbetriebsabnahme.

## Fortlaufender Kartenanschluss: lokale Umsetzung vom 19. November 2026

Die folgende Umsetzung führt die vorstehende Zuordnung fort; der datierte
Zuordnungsbeleg bleibt als Befund vor der Änderung erhalten.

Der [Paper-Starter](../../../scripts/ops/run_zkp_lane1_paper_v1.py) projiziert
jede neue Originalaufnahme für ZKP, UP oder IRYS durch
[InstrumentCardStreamV1](../../../src/ops/instrument_card_stream_v1.py).
Die Projektion umfasst die vollständigen 13 Quellen, ihre Originalbytes und
GET-Receipts, aktuellen Slotkapitalbezug, Buchprüfung und die tatsächlich
vorbereitete Master-V2-Eingabe samt Originalergebnis. Sie erhält weder einen
zweiten Entscheidungswriter noch einen zweiten Handelscursor. Die vorhandene
Öffnung, Nettobuchung, Fundingverarbeitung und Originalfortsetzung bleiben
bei ihren bisherigen Ownern. Der Starter akzeptiert bei den historischen
Slotkonfigurationen auch das eindeutige `environment=PAPER`, ohne die Dateien
zu verändern; widersprechende Betriebsarten werden abgewiesen.

Für SOPH verbindet der
[I17-Entrypoint](../../../src/ops/integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1/productive_run_entrypoint_v1.py)
nach seinen unveränderten Startgates denselben vollständigen öffentlichen
Quellvertrag mit der Shadow-Karte. Mark und Ticker werden für die bestehende
Normalisierung aus genau dieser Aufnahme geliefert. Der Core erhält deren
eigenen Index, Buch-Bid/Ask, Kontraktvolumen, OI und Fundingrate sowie den
Markttyp `FUTURES`, finale gehandelte C1 für seinen Feature-/Preisreihenpfad
und die originale finale Markhistorie für den zuständigen G17-Produzenten.
Die bisherigen Tick-/Platzhalterinputs bleiben auf den bisherigen
Beobachtungspfad ohne vollständige Kartenquelle begrenzt. Solche Eingaben
werden ausdrücklich nicht zu einer vollständigen gültigen Karte erklärt.

Der SOPH-Kapitalbezug kommt aus dem ursprünglichen analytischen Portfolio und
der bestehenden Slot-Testbudgetpolicy. Vor dessen erstem analytischen Zyklus
wird die Testallokation einmal mit dem aktuellen USDC/USD-Index in seine
USD-Basis umgerechnet. Danach werden Originalzustand und markierte Equity
gelesen. Ein bereits verwendetes Portfolio darf nicht neu initialisiert werden.
Diese virtuelle Basis ist weder private Kontowahrheit noch ein Budgethold.
Die analytischen Portfolio-Fillmengen sind Basisassetmengen; vor einer
zusätzlichen Exposition wird die Menge ausdrücklich in native Kontrakte
umgerechnet und geprüft. Unvereinbare Mengen werden beim analytischen
Consumer gehalten. Die Originalentscheidung bleibt als solche erhalten;
der zusätzliche Neueinstiegscheck sperrt keine ursprünglichen Reduktions-
oder Exitaktionen. Die modellierten Shadow-Fills und Modellkosten bleiben
analytische Simulation und werden nicht zu echten Buchausführungen erklärt.

`available_amount` benennt die aktuelle begrenzte Kapitalbasis.
`available_for_new_entry` benennt die gesondert verfügbare Neueinstiegsbasis
und ist bei offener Position null. Die nominale Kartenkapazität wird aus
letzterer berechnet. Das ersetzt weder die ursprüngliche finale
Risiko-/Sizing-Menge noch deren vollständige Kostenprüfung. Reservierung
bleibt bei diesen Modellen ausdrücklich unbekannt beziehungsweise außerhalb
ihres Holdmodells; `null` wird nicht als null reserviertes Geld verwendet.

Die aktuelle Slot-/Instrumentzuordnung erreicht die Karte bereits automatisch
aus ihrem tatsächlichen Verbraucher. Der Paper-Driver übergibt `session.bound`
und die Lane des ursprünglichen Opening- beziehungsweise Fortsetzungsowners.
SOPH leitet Karte und Bridgezustand aus derselben geprüften Sitzungszuordnung ab.
Dieser Anschluss benötigt keine erneute Rangberechnung oder manuell hinzugefügte
Rankingbindung. Die Kartenprüfungen gleichen die gespeicherte Bindung am
tatsächlichen Verbraucheraufruf ab, auch nach einer Paper-Unterbrechung.

Der zusätzliche ursprüngliche Rankingnachweis ist davon getrennt. Paper und der
SOPH-I17-Begleiter können über
`--card-cap24-evidence-root` eine bereits vorhandene Cap24-Evidenz übernehmen.
Der vorhandene Cap24-Leser prüft Manifest, Recordstatus und Bindungsidentität;
die Instrumentpaarung muss exakt zum Slot passen. Auswahl-, Ranking- und
Universumsbezug werden in der Karte getrennt von der bestehenden isolierten
Entscheidungsbindung aufbewahrt. Der ursprüngliche Lane-Identitätsowner
berechnet daraus die Instrumentgeneration. Paper hält diese Kartenbindung
für den Wiederanlauf fest und weist einen Austausch ab. Ohne solche
Originaleingaben lautet der Status `EXPLICIT_ISOLATED_TEST_BINDING`.
Es gibt keinen automatischen Rerank, keine neue Cap23-Auswahl und keine
stillschweigende Übernahme späterer Rankinggenerationen. Die natürliche
Versorgung aus dem Ranking-/Rotationsowner bleibt ein eigener Betriebsanschluss.

Pro Sitzung und Lane liegen `latest.json`, unveränderliche Fassungen unter
`versions` und contentadressierte Originalantworten unter `sources` im
Kartenverzeichnis. Die Original-Shadow-Evidence bleibt separat versiegelt.
Neue Quellen- oder Budgetfassungen dürfen kein altes Einstiegsurteil als
neue Bewertung übernehmen. Fehler löschen die aktuelle Kartenbewertung;
Sitzungsende markiert die Karte gesperrt. Der lesende Zugang
`read_instrument_card_v1` prüft Digest, Entscheidungsbindung, Lane und
Verbrauchszeit und entfernt abgelaufene Werte aus seiner Rückgabe. Die
Frist kommt aus den bestehenden Mark-/Buch-Freshnessgrenzen und den
Originalquellzeiten; eine aktuelle Datei ist keine eigenständige Freigabe.

Die [Kartenprüfungen](../../../tests/ops/test_instrument_card_stream_v1.py),
die erweiterten [Paper-Ownerprüfungen](../../../tests/ops/test_zkp_lane1_paper_opening_v1.py)
und die [Shadow-Prüfungen](../../../tests/ops/test_integrated_paper_shadow_observation_wallclock_session_execution_v1.py)
verwenden synthetische Originalantworten und gesperrte externe Verbindungen.
Sie prüfen die fortlaufende Übergabe im bestehenden Verbraucherpfad.
Ein realer Datenlauf, ein automatisch zugelassener N5-Host und eine
Gesamtabnahme aller Systemverzweigungen werden daraus nicht abgeleitet.

Der [Prüfbeleg vom 19. November](../evidence/INSTRUMENT_CARD_CONTINUOUS_CONNECTION_2026-11-19.json)
bindet die geprüften Quelldateien per SHA-256. Im abschließenden Paket bestanden
131 von 132 Offline-Fällen. Offen bleibt
`test_case_d_adverse_exit_uses_canonical_producer`: derselbe Kontrollfall
scheitert auch einzeln auf `83cce4ca6`, dessen Git-Baum mit der Mergebasis
`351728852` identisch ist, an derselben Trigger-Erwartung. Der Test und seine
Schwellen wurden nicht geändert; seine fachliche Ursache ist noch nicht
abschließend beurteilt. Ruff, Formatprüfung, Diff-Prüfung sowie Karten-,
N1- und Clean-Core-Siegel bestanden. Die Kartenprüfung ersetzt diesen offenen
Safety-Befund nicht.

Die abschließende Dokument-/Atlas-/Law-Map-Currency-Prüfkette bestand auf
`ff101dc3e`. Der zusätzliche Law-Impact-Advisory meldet weiterhin allgemeinen
Reviewbedarf gegenüber dem Freeze: vier unklassifizierte Oberflächen und
zwei unbekannte Grenztreffer. Dieselben Treffer und Zählwerte wurden auf der
unveränderten Mergebasis reproduziert. Dies ist keine neue Regelratifikation
oder fachliche Freigabe; der Bedarf bleibt im Prüfbeleg offen ausgewiesen.

### Originaler Paper-Entscheidungsbeleg bis zum Lernconsumer

Der XPERP-Originalstore enthält im Openingplan und in der ursprünglichen
Reversal-Publikation bereits den jeweiligen Entscheidungscursor. Darin liegen
die kanonischen Core-, Policy-, Composition-, Assessment-, Survival- und
Suitability-Ausgaben samt Marktkontext und gebundenen Digests. Der Episodenleser
hatte diese geprüften Inhalte bislang auf Identitäten und Digests reduziert.

Neue Importe durch den [Paper-Lernadapter](../../../scripts/ops/paper_episode_learning_handoff_v1.py)
übernehmen nun diese originalen Cursor zusätzlich in die unveränderliche
Messung. Der [Episodenleser](../../../src/ops/bounded_peaktrade_system_composition_v1/xperp_paper_episode_outcome_v1.py)
prüft dafür weiterhin Originalmanifest, Instrument, Slot, Entscheidung, Epoche,
Fill und die ursprünglichen Komponentenbindungen. DDO führt den Originalbezug
über seine Evidence- und Marktkontextreferenzen weiter; der LearningState
verweist auf genau dieses DecisionEvent. Der Default des reinen Episodenlesers
bleibt unverändert. Bereits importierte Messungen und Ledger behalten ihre
ursprüngliche Fassung und werden weiterhin gegen das Originalarchiv geprüft.

Der Cursor ist der Zustand **nach der ursprünglichen Entscheidung**, kein
vollständiger damaliger DDO-Informationssatz. Fehlende Before-State-, Risk-,
DataQuality- oder Incident-Snapshots werden nicht nachgebildet. Native
Tradeausgänge und Reason-Codes bleiben im Originalbeleg; sie werden nicht in
die hierfür ungebundenen DDO-v0-Tokens übersetzt. Entscheidungstyp, Ergebnis
und Qualitätslabels bleiben insoweit ausdrücklich `UNKNOWN`.

Das simulierte Nettoergebnis bleibt unabhängig davon in Quote-Währung
gemessen. Weder ein positives Ergebnis noch die erfolgreiche Quellenprüfung
erzeugen ein Gut-/Schlecht-Urteil, ein Update von Modellparametern oder eine
Applyfreigabe. Originalarchive und Handelszustände werden nicht verändert.

### Weitere Signalverzweigungen: Nachprüfung vom 21. November 2026

Lesende Ausgangsbasis ist der Merge von PR #7344,
`9914f21ba8ada16fd0a8df0525d0e8dcc2666ecd`. Die historischen Offen-Labels oben
bleiben an ihren damaligen Stand gebunden. An folgenden vorhandenen Pfaden
wurde keine zusätzliche Producer-/Consumerübergabe benötigt:

- Die zweckgebundenen Datenadapter erhalten Quellenwahl, Preisfamilie,
  Finalisierung und Kenntniszeit getrennt für RANKING, TRADING, LIQUIDITY,
  OUTCOME und RESEARCH. Eine gemeinsame Kartenquelle ist kein Anlass,
  diese Zwecke oder ihre Zulassung gleichzusetzen.
- Der [Shadow-Lernadapter](../../../scripts/ops/shadow_ddo_learning_handoff_v1.py)
  übernimmt bereits die ursprüngliche Entscheidung samt kausalen Eltern aus
  dem versiegelten Ledger. Er bindet die unabhängig geprüften finalen O4-Bars,
  Messung, LearningState und Readback. Der spätere LOG_RETURN bleibt ein
  kontrafaktischer Preisverlauf ohne Fill und ohne realisierten Kontogewinn.
- Der [archivierte Marktpfad](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/offline_recorded_market_replay_v1.py)
  führt zugelassene Originalkontexte an den gespeicherten OLS-Forecast und
  die spätere Originalmessung an Calibration. Der vorhandene
  [Kohortenanschluss](../../../scripts/ops/run_offline_learning_mark_ols_follow_up_v1.py)
  bindet abgeschlossene Messjobs an numerisches Training und einen ausdrücklich
  künftigen Forecast. Marktidentität und Quellengeneration bleiben erhalten;
  es werden keine Decision-/Slotidentitäten erfunden. Der Codepfad ist kein
  selbständig gestarteter oder unbegrenzt fortlaufender Trainingsdienst.
- Native Researchresultate erreichen Meta und die folgende Suche bereits
  über den [bestehenden Feedbackowner](../../../src/experiments/canonical_research_result_to_meta_input_v1.py).
  Der typisierte Meta-Router trennt Researchwahl und Repräsentationsresearch;
  UNKNOWN/MIXED oder ein falscher Empfänger öffnen keinen Rückweg. Ein
  Researchplan ist kein Modell-Apply und keine Handelsfreigabe.
- Der [Meta-Intake](../../../src/experiments/canonical_meta_learning_ingest_v1.py)
  prüft native M5-Quittung und föderierten Returnjoin jeweils erneut gegen
  ihren Originalproducer. Native Plane-Identität und föderierte
  Surface-Ausführungsidentität bleiben unterschiedliche Verträge. Ein neuer
  Transporthash macht einen fremden Join nicht gültig; die
  [föderierten Gegenproben](../../../tests/experiments/test_canonical_federated_m5_m6_return_join_v1.py)
  prüfen auch die Abweisung am tatsächlich aufgerufenen Meta-Consumer.

Die Härtung der hier geprüften Ketten verfolgt Originalproducer, Transformation,
Persistenz/Übergabe, tatsächlichen Consumer und dessen Wirkung. Die Gegenproben
prüfen Quellen-/Instrumentverwechslung, unvereinbare Einheiten oder Preisfamilie,
fehlende Finalisierung, Kenntnis nach dem Verbrauchszeitpunkt, geänderte
Beleginhalte und Wiederholung am jeweils zuständigen Originalowner. Eine gültige
Identität oder ein gültiger einzelner Record ersetzt nicht den Abgleich der
zusammengehörigen Inhalte. Bestehende passende Nachweise werden weiterverwendet;
fehlende Gegenproben werden gezielt ergänzt.

Eine konkrete Bindung fehlte im
[Loop-C-Orchestrator](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/phase_24_representation_feedback_loop_evidence_v1.py):
Die Routerquittung wurde mitgeführt, aber nicht gegen die tatsächlich an den
Plan übergebene Learning-Entscheidung geprüft. Eine für sich gültige Quittung
einer anderen Repräsentationsherkunft oder eines anderen Musters konnte so
einem fremden Folgeplan zugeordnet werden. Der vorhandene Belegdigest,
Meta-Parent und alleinige Learning-Empfänger werden jetzt vor Plan und
Auswertung abgeglichen. Die Gegenproben im
[Loop-C-Test](../../../tests/learning/test_phase_24_representation_feedback_loop_evidence_v1.py)
vertauschen zwei durch den Originalrouter erzeugte gültige Pakete und verlangen
die Abweisung vor beiden Folgeconsumern. Auch die Übernahme eines anderen
Musters unter derselben Parentbezeichnung wird über den Inhaltsdigest abgewiesen.

Die bisherigen Fixtureauswertungen und typisierten Nichtauswertungen bleiben
erhalten. Dieser Abgleich erzeugt weder zusätzliche Features noch neue
Qualitätslabels, Modellparameter, Rotationslogik oder Betriebsfreigaben. Ein
vollständiger Dauerbetrieb und die Semantik aller übrigen Systempfade sind
damit weiterhin nicht pauschal abgenommen.

### MI-Lernexport und M4: weiterer kausaler Prüfblock

Ausgangsbasis dieses Blocks ist PR #7345,
`2b4f8689004d56cd4a6a7a036ba4f8798e9e0641`. Die vorhandene Kette aus
MI-Bridge, eigenem Lernbelegstore, Export und optionaler M4-Anreicherung war
bereits verbunden. Loop A besitzt ebenfalls seinen vorhandenen
Writer-/Store-/Readback-/Exportpfad. Eine zusätzliche Verbindung zum
produktiven DDO-Reducer oder zum numerischen Marktmodell wird daraus nicht
abgeleitet oder hinzugefügt.

Die Prüfung reproduzierte folgende konkrete Aufnahme- und Bindungslücken:

- Der [MI-Lernbelegvalidator](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/mi_learning_evidence_record_v1.py)
  prüfte die ID gegen den angegebenen Digest, berechnete diesen aber nicht
  erneut aus seinen ursprünglichen kanonischen Feldern. Veränderte Outcome-,
  Horizont-, Preisfamilien-/Instrument- oder konditionierte Verhaltensbezüge
  konnten deshalb unter der alten ID exportiert oder kalt gelesen werden.
  Die bestehende Digestformel wird jetzt an diesem Owner erneut ausgewertet.
- Der [MI-Lernexport](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/mi_learning_evidence_learning_export_v1.py)
  konnte eine deklarierte DDO-Referenz mit einem anderen für sich gültigen
  DDO-Lernbeleg kombinieren. Bei mitgeliefertem Beleg muss die erklärte
  Referenz jetzt dessen tatsächlicher Record-ID entsprechen. Ein bloßer
  Verweis bleibt ohne behauptete DDO-Payload-Kompatibilität zulässig.
- Die [MI-Researchaufnahme](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/mi_optimization_research_input_v1.py)
  übernahm den deklarierten Inhaltsdigest ohne den vorhandenen
  Researchrecordvalidator aufzurufen. Sie verwendet jetzt denselben Owner
  wie der dauerhafte Researchstore. Inhaltsbindung, Domain und die
  ursprünglichen No-Runtime-/No-Promotion-Felder werden geprüft; ein neu
  berechneter Transporthash rechtfertigt keine andere Wirkung.
- Der [M4-Consumer](../../../src/experiments/canonical_optimization_universe_mi_enriched_m4_intake_v1.py)
  trug einen optionalen MI-Lernexport als Herkunft weiter, ohne ihn an die
  tatsächlich aufgenommenen Research- und DDO-Belege zu binden. Er liest ihn
  jetzt über den Originalexporter zurück und vergleicht den gesamten Export,
  Forecast-/Calibration-ID, N-Bars-/Barspezifikation und die ausdrücklich
  zugeordneten DDO-Belege vor dem Experimentaufruf.

Die Gegenproben verwenden durch Originalbuilder erzeugte Ausgangsbelege.
Sie prüfen Inhaltsvertauschung unter derselben ID, Cold-Read-Abweisung und
den unveränderten Originalstore sowie fremde, für sich gültige Forecast-/DDO-
Pakete und manipulierte Exportreferenzen am tatsächlichen M4-Consumer. Die
bisherigen MI-only-, Reference-only- und Payload-only-Fassungen bleiben
zulässig. Eine optionale Zuordnung behauptet weder gleichen numerischen
Outcome noch gleiche Messgröße zwischen MI und DDO.

Originale ID-/Digestformeln, Forecast- und Messhorizonte, Qualitätslabels,
DDO-Reducer, Modellparameter, BTC und Betriebsfreigaben bleiben unverändert.
Ein Inhalts-/Zuordnungscheck ist kein Nachweis externer Quellenwahrheit,
wirtschaftlicher Güte oder einer pauschalen Härtung aller Systemketten.

Prüfstand dieses Blocks: 150 unterschiedliche synthetische Offline-Testfälle
bestanden (67 für die betroffene Kette, 3 weitere optionale Eingangsformen,
80 benachbarte Governance-/Markt-/Replay-/Modellfälle). Ein vorhandener
Gesamtvertrag bleibt ausdrücklich fehlgeschlagen:
`test_adjudication_proof_passes_on_current_repo` aus
[der D01/D02-Prüfung](../../../tests/governance/test_unified_blueprint_d01_d02_topology_adjudication_v1.py).
Sein unveränderter Baseline-Abgleich verlangt den autorisierten Wert
`dfcf4d04b8400763bee6ab0b465fa182927dea75` oder den aktuellen HEAD;
die unveränderte Interaktionskarte nennt
`1bac0d93302c6e589effafe46fccb055d82bd44e`. Beide Konfigurationen sowie
Prüfcode und Test sind bytegleich zum Ausgangscommit `2b4f8689`.
Census-, D02-Kanten- und Authority-Einzelvalidatoren bestanden. Diese
Änderung ersetzt oder lockert den fehlgeschlagenen Gesamtvertrag nicht.

### M7-Rückgabe an den nächsten Offline-Zyklus

Ausgangsbasis ist PR #7346,
`82c97d4e41dc663074a7838b9b8a908ad19d6281`. Die ursprünglichen
Konstruktionen für [nativen M8-Replay](OPTIMIZATION_META_M8_DETERMINISTIC_MULTI_CYCLE_OFFLINE_REPLAY_NORMATIVE_V1.md),
[MI-Crossing](UNIFIED_BLUEPRINT_PHASE_10_MI_CROSSING_MULTI_CYCLE_OFFLINE_REPLAY_NORMATIVE_V1.md)
und [föderierten M5–M8-Replay](M5_M8_BOUNDED_META_RETURN_AND_REPLAY_COMPLETION_NORMATIVE_V1.md)
enthalten bereits Producer, Rückgabe und Folgezyklus. Der frühere G2-Abgleich
in `a734876d0` bindet den nativen Eingang zusätzlich an denselben originalen
Lernbeleg; diese Verbindung wird nicht erneut aufgebaut oder verändert.

Eine gemeinsame Lücke lag an den drei Mehrzyklusübergängen: Eine ausdrücklich
mitgelieferte vorherige Rückgabe wurde nur anhand ihrer Feedback-ID mit dem
gerade erzeugten Original verglichen. Veränderte Meta-Herkunft,
Forschungspriorität oder Suchmethodenbewertung erreichten dadurch unter
derselben ID den nächsten Zyklus, auch mit neu berechnetem Transporthash.

Die [nativen](../../../src/experiments/canonical_deterministic_multi_cycle_offline_replay_v1.py),
[MI-angereicherten](../../../src/experiments/canonical_unified_blueprint_mi_crossing_bounded_multi_cycle_offline_replay_v1.py)
und [föderierten](../../../src/experiments/canonical_federated_bounded_multi_cycle_offline_replay_v1.py)
Orchestratoren vergleichen jetzt den vollständigen kanonischen Paketinhalt
mit der tatsächlich vorliegenden Rückgabe des vorherigen Zyklus, bevor sie
den Folgeconsumer aufrufen. Dazu werden die vorhandene JSON-Normalisierung
und Inhaltshashfunktion verwendet. Wahrheitswerte und Zahlen bleiben
unterschiedliche Typen. Es wird keine neue gespeicherte ID- oder
Digestformel eingeführt.

Die [gemeinsamen Gegenproben](../../../tests/experiments/test_canonical_deterministic_multi_cycle_offline_replay_v1.py)
verwenden tatsächliche Originalproducer und prüfen die Abweisung vor dem
nächsten Zyklus in allen drei Varianten. 24 negative Fälle prüfen fremde
Herkunft, geänderte Dispositionen und Typverwechslung mit altem oder neu
berechnetem Transporthash. Drei positive Fälle belegen, dass ein unverändertes
JSON-Paket dieselbe Replay-Identität und denselben Ergebnisdigest liefert wie
die bestehende automatische Übernahme. 55 gezielte Kettenfälle und 27
benachbarte Governance-/G2-/Rückwegfälle bestanden; Wiederholungen sind nicht
doppelt gezählt. Die oben beschriebene historische D01/D02-Baselineprüfung
bleibt ein offener Befund und wurde hierfür nicht erneut ausgeführt.

Die mitgeführten Dispositionen stehen im vorhandenen
`cycle_n_plus_1_input_semantics`-Beleg. Dieser Bezug schreibt die vom Aufrufer
gelieferte nächste Experimentanfrage nicht um und ist kein automatischer
Such-, Trainings- oder Applyauftrag. Native Plane-Identität und föderierte
Surface-Ausführungsidentität bleiben getrennt; der föderierte Pfad startet
weiterhin keine M4-Plane. DDO-LearningState, Marktmodell, Bewertungsdefinitionen,
BTC und Betriebsfreigaben bleiben unverändert. Die synthetischen Tests sind
kein Beleg für wirtschaftliche Güte oder eine vollständige Härtung sämtlicher
Systemketten.

### Fehler- und Reality-Gap-Belege bis Meta und Forschungswahl

Ausgangsbasis ist PR #7347,
`a01ac96dbcb4b79c140ac524ce0e99e846d8e8e8`. Die vorhandenen
[Fehlerbeleg-](CANONICAL_FAILURE_MEMORY_V1.md) und
[Reality-Gap-Owner](CANONICAL_REALITY_GAP_STORE_V1.md) besitzen bereits
Inhalts-/Identitätsprüfung, unveränderliche Records und dauerhafte Writer mit
Readback. Auch die Übergaben an [Meta](CANONICAL_META_LEARNING_V1.md) und
[Advanced Search](CANONICAL_ADVANCED_SEARCH_V1.md) sind verbunden. Der
[bestehende Ergebnis-/Meta-/Suchadapter](CANONICAL_RESEARCH_RESULT_META_SEARCH_FEEDBACK_V1.md)
bindet weiterhin Originalmessung, Experiment, Parameterregion, Kontext und
die ausdrücklich nachfolgende Forschungswahl. Dafür wird kein neuer Store
oder weiterer Rückweg erzeugt.

Die acht Gegenproben mit vollständigen Originalbuilder-Records bestätigten
eine fehlende zeitliche Aufnahmebedingung: Später erstellte Fehler- oder
Gap-Belege erreichten unter gültigen IDs die Meta-Findings beziehungsweise
die Suchkandidatenwahl einer früher datierten Anfrage. Schon eine Nanosekunde
nach dem Verbrauchszeitpunkt wurde nicht abgewehrt. Die vorhandene
Lookahead-Prüfung von Experiment- und Later-Outcome-Inputs ersetzte diesen
Abgleich für die zusätzlichen Records nicht.

Der [Meta-Owner](../../../src/experiments/canonical_meta_learning_v1.py)
bindet jetzt beide Record-Arten an die bereits gelieferte Analysezeit, bevor
Findings berechnet werden. [Search](../../../src/experiments/canonical_advanced_search_v1.py)
übergibt seine vorhandene Anfragezeit an denselben Zeitprüfer, bevor
Kandidaten bewertet werden. Der Prüfer verwendet die bestehende validierte
UTC-Kalender-/Integer-Nanosekundenordnung. Es gibt keine Rundung,
Altersgrenze, neue Uhrquelle oder Änderung einer gespeicherten ID-/Digestformel.
Frühere und zeitgleiche Records bleiben zulässig, auch bei unterschiedlicher
zulässiger Nachkommastellendarstellung derselben Zeit.

132 unterschiedliche Offline-Testfälle bestanden: 83 für die betroffenen
Memory-/Meta-/Such-/Researchpfade, 38 für benachbarte Mess-, Stichproben-,
Parameterregion- und M4-Pfade sowie elf bestehende Zeitsemantikfälle. Die
16 neuen Fälle enthalten acht Abweisungen vor dem tatsächlichen Folgeconsumer
und acht gültige Grenzfälle mit unveränderten Zeitstrings. Gültige Records
behalten ihre ursprüngliche Wirkung auf die Forschungspriorität; andere
Forschungskandidaten bleiben verfügbar. Wiederholungen sind nicht doppelt
gezählt. Der historische D01/D02-Baseline-Konflikt bleibt offen und wurde
für diesen Block nicht erneut ausgeführt.

Record-Erstellung, Experiment-/Barzeit und Zeitpunkt der konsumierenden
Anfrage sind unterschiedliche Bezüge. Der Abgleich prüft ihre deklarierte
Chronologie; eine tatsächliche damalige Ankunft, externe Quellenwahrheit oder
ein vollständiger damaliger Informationssatz wird dadurch nicht bestätigt.
Failure-Labels, Gap-Messgrößen und Schwellen behalten ihre Originalbedeutung.
Forschungspriorisierung ist weder eine Instrumentrangfolge noch ein neuer
automatischer Forschungsbann oder eine Handels-/Applyfreigabe. Originalstores,
DDO-LearningState, numerische Modelle, BTC und Betriebsfreigaben werden nicht
verändert; vollständige Systemhärtung und wirtschaftliche Güte bleiben
gesonderte Nachweisfragen.

### Meta-Kostenbefund bis zum F2-Forschungsconsumer

Ausgangsbasis ist PR #7348,
`8b14d027e9918a3579cb0644c809cc3bf7cde038`. Die explizite Übergabe nativer
Meta-Prioritätsvorschläge an Search/M4 sowie deren Zielartenprüfung ist bereits
verbunden. Ein `cost_model`-Vorschlag ist dabei kein Instrument- oder
Strategiefamilienziel. Der eigene
[F2-Folgeconsumer](../../../src/experiments/f2_meta_cost_model_follow_up_v1.py)
erhält den vollständigen Meta-Beleg und bindet bereits ausgewählten Vorschlag,
Kostenbefund, ursprüngliches Baseline-Kostenmodell und archiviertes F2-Grid.
Der historische Anschluss archivierter Fill-Gebühren aus `778116f38` bleibt
erhalten. Keine weitere Verbindung oder neue Suche wird hinzugefügt.

Sieben Gegenproben bestätigten eine fehlende Aufnahmebedingung am tatsächlichen
Szenarienconsumer: Ein neu gehashter Meta-Gesamtbeleg konnte veränderte
Vorschlagsgründe, eine Kausalaussage, ein Champion-Apply-Flag oder einen
Vorschlag trotz nicht tragfähigem Frage-Status/Aussagegewicht weiterreichen.
Auch ein durch den ursprünglichen generischen Builder neu berechneter
Vorschlagsdigest stellte den Bezug zum konkreten Kostenbefund nicht her.

Der [Meta-Owner](../../../src/experiments/canonical_meta_learning_v1.py)
stellt jetzt die vorhandene Kosten-Vorschlagskonstruktion für diesen Rücklese-
Abgleich bereit. Nur COMPUTED Kostenbefunde mit ihrer ursprünglichen
deskriptiven Aussageart, Stärke NONE und ohne Kausalbehauptung liefern dort
zulässige Vorschläge. Der F2-Consumer vergleicht den vollständigen gewählten
Vorschlag gegen diese Originalkonstruktion, bevor er Szenarien auswertet.
Bestehende Vorschlags-/Record-IDformeln, Gebühren-/Slippagerechnung, Grid,
Schwellen und Stichprobenregeln bleiben unverändert. Die kanonische
Inhaltsprüfung setzt einen Wahrheitswert nicht mit einer Zahl gleich.

69 gezielte Offline-Fälle bestanden: 22 Meta-Vertragsfälle, 27 Zielarten-/
Parameterregionfälle, vier M4-Prioritätsfälle und 16 F2-Anschlussfälle. Darin
enthalten sind die sieben neuen Abweisungen vor der Szenarienauswertung.
Die Tests verwenden temporäre Kontrollarchive und isolierte Fill-Fixtures.
Die [F2-Gegenproben und Positivfälle](../../../tests/experiments/test_f2_meta_cost_model_follow_up_v1.py)
erhalten auch Kaltlesen, idempotente Ausgabe, unveränderte Originalarchive,
gemessene Fill-Gebühren und die ausdrückliche Nichtauswertung ohne OOS-Trades.
Wiederholungen sind nicht doppelt gezählt. Der historische D01/D02-Baseline-
Konflikt bleibt offen und wurde für diesen Block nicht erneut ausgeführt.

Geprüft wird die innere Zuordnung eines deklarierten Kostenbefunds zu seinem
Forschungsvorschlag. Originalmessungen und numerische Stichprobengüte werden
dadurch nicht erneut berechnet oder authentifiziert. Eine einzelne bestätigte
Order bleibt eine deskriptive Diagnose; modellierte OOS-Kostendeltas sind
keine bestätigten Kontogewinne. Gültige bisherige Befunde und begrenzte
Nichtauswertungszustände bleiben erhalten. BTC, historische Records,
DDO-LearningState, numerische Modelle und Betriebsfreigaben bleiben unverändert.
Vollständige Systemhärtung und wirtschaftliche Güte sind damit weiterhin
nicht pauschal abgenommen.

### Nachprüfung des historischen Safety-Kontrollfalls am 19. November

Die [fachliche Nachprüfung](MASTER_V2_HARDENING_V2_HISTORICAL_SAFETY_SEAM_REMEDIATION_V1.md#4-full-scope-test-reconciliation-2026-11-19)
ordnet den oben dokumentierten Fehler als veraltete Testerwartung ein:
PR #7302 hatte den separaten frühen Adverse-Exit bewusst entfernt, der alte
Test verlangte ihn weiterhin bei 80 Preiseinheiten Abstand vom Einstieg.
Diese historische Zahl ist weder die aktuelle Scope-Distanz noch ein
Basispunktwert. Der aktuelle Consumer verwendet den vollen effektiven `D_t`;
der Schutzgeometriewert begründet keinen zusätzlichen frühen Scope-Exit.

Die korrigierten LONG-/SHORT-Fälle prüfen am echten Replay mit gültiger
typisierter Markvolatilität, dass diese alte Auslösung ausbleibt und ein
unabhängiger Sicherheits-Exit bis zur simulierten Schließung wirksam bleibt.
Die eigenständigen Scope-Grenzfälle prüfen weiterhin Downscope und dessen
Epochbestätigung. Der [Nachprüfbeleg](../evidence/HARDENING_V2_FULL_SCOPE_SAFETY_CONTRACT_RECONCILIATION_2026-11-19.json)
bindet die Ergebnisse an ihre Quellen. Produktcode und Handelsparameter wurden
dafür nicht geändert. Der ursprüngliche Prüfstand 131/132 bleibt im damaligen
Bericht erhalten; eine Gesamtabnahme des Systems folgt daraus weiterhin nicht.
