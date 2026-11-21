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
