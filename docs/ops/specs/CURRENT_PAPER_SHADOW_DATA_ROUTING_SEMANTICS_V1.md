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

### Repräsentations-Forschungsplan bis zur Offline-Auswertung

Ausgangsbasis ist PR #7349,
`182899ded2925baa60eae6b82e376f1b6e7c03e9`. Native und föderierte Meta-Aufnahme
binden ihre Empfangsquittungen bereits an den Originalproducer. Die typisierte
Routerhülle prüft Inhalt, Herkunft und einzelnen Empfänger; der Loop-C-Join bindet
die tatsächliche Learning-Entscheidung vor dem Plan. Der innere Meta-
Reproduzierbarkeitsdigest bezeichnet seine ursprünglichen Herkunfts-/Messbezüge,
nicht sämtliche später interpretierenden Felder. Diese Bedeutung bleibt erhalten.

Die ursprüngliche [Plan-Konstruktion](UNIFIED_BLUEPRINT_PHASE_24_REPRESENTATION_FEEDBACK_LOOP_NORMATIVE_V1.md)
und ihre zwei Statuszweige sind bereits im eingefrorenen Quellbestand `9397d04a3`
vorhanden. Die spätere Änderung `50fb4cb9c` formatiert diesen Owner; sie begründet
keine neue fachliche Konstruktion. Der
[Offline-Consumer](../../../src/experiments/canonical_learning_representation_offline_evaluation_v1.py)
verwendet bereits den Planvalidator, dessen Aufnahme jedoch nur Identität,
Gesamtprüfsumme und No-Authority-Felder vollständig prüfte. Neu berechnete
Planidentitäten und Prüfsummen konnten widersprüchlichen Status, Auswertungsschalter,
Forschungszweck oder fehlenden Kontext bis zur Fixture-Auswertung weiterreichen.

Der [Plan-Owner](../../../src/experiments/canonical_learning_representation_research_adaptation_plan_v1.py)
prüft jetzt zusätzlich seine ursprüngliche Domain und die vorhandenen Beziehungen:
READY braucht ein nichtleeres Stringmuster samt Repräsentationsherkunft, den Zweck
des bestehenden Klassifizierers und den echten Wahrheitswert True. FAIL_CLOSED
behält No-Action-Zweck, Fail-Closed-Label, fehlende Repräsentationsherkunft und den
echten Wahrheitswert False. Zahlen und Strings werden nicht als Schalter akzeptiert.
Musterstrings werden dabei nicht umgeschrieben oder als reale Messwerte interpretiert.

93 gezielte Offline-Fälle bestanden: die 71 vorhandenen Plan-/Entscheidungs-/Router-/
Loop-C-/Governancefälle sowie 22 neue Fälle. Davon prüfen 17 widersprüchliche, frisch
versiegelte Pläne die Abweisung vor dem Fixture-Zweig und einer die Abweisung vor
neuer Loop-C-Evidence. Alle 18 Negativfälle reproduzierten zuvor die fehlende
Abweisung. Vier weitere Fälle erhalten vollständige Ausgaben nach JSON-Rücklesen.
Die [Gegenproben](../../../tests/experiments/test_representation_plan_semantic_admission_v1.py)
verwenden Originalbuilder und synthetische Offline-Eingaben. Zwölf vollständige
gültige Plan-/Auswertungsvarianten wurden zusätzlich mit ihren Ausgaben vor der
Korrektur abgeglichen; Identitäten und Digests bleiben gleich.

Bekannte Fixture-Ergebnisse sind weiterhin Kontrollnachweise, keine neu gemessene
Feature- oder OOS-Güte. Gültige unbekannte Muster liefern weiterhin die typisierte
Nichtauswertung. Die innere Konsistenzprüfung authentifiziert weder eine nur als
Digest referenzierte Originalentscheidung noch externe Herkunft. Sie erzeugt keinen
Lernwriter, kein Modell-Apply und keine Betriebsfreigabe. BTC, Originalstores und
numerische Modelle bleiben unverändert. Der historische D01/D02-Basiskonflikt bleibt
offen und wurde nicht erneut ausgeführt; eine Gesamtsystemhärtung ist nicht belegt.

### Offline-Auswertungsrückgabe bis zum nächsten Loop-C-Beleg

Ausgangsbasis ist PR #7350,
`ce1342eab782528448e136e453362ee5c9c6f0f2`. Planaufnahme und die vorhandenen
Fixture-Zweige sind verbunden und besitzen die zuvor dokumentierten Prüfungen.
Die bisherige Auswertungskonstruktion ist seit dem eingefrorenen Bestand
`9397d04a3` bytegleich erhalten. Der Loop-C-Owner übernahm ihre Rückgabe jedoch
ohne einen erneuten vollständigen Abgleich mit dem tatsächlich verwendeten Plan
in Zyklusidentität und nächsten Forschungsbeleg.

Zwölf Gegenproben bestätigten die fehlende Abweisung vor dem tatsächlichen
Folgebeleg. Zwei verwenden vom Originalproducer erzeugte gültige Auswertungen
fremder Pläne. In einem Fall bleiben Plan- und Auswertungs-ID gleich, während der
vollständige Planinhalt und dessen Ergebnisdigest eine andere Repräsentationsherkunft
tragen. Die übrigen Fälle verändern Outcome, Status, Fixture, Forschungszweck,
Domain oder Wirkungsangaben und berechnen die ursprünglichen Hashes erneut;
ein Kontrollfall behält dabei ausdrücklich die alte innere Auswertungs-ID.

Der [Auswertungsowner](../../../src/experiments/canonical_learning_representation_offline_evaluation_v1.py)
stellt jetzt einen vollständigen Rückgabevalidator bereit. Er verwendet dieselbe
ursprüngliche deterministische Fixture-Konstruktion für den tatsächlich validierten
Plan. Der [Loop-C-Consumer](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/phase_24_representation_feedback_loop_evidence_v1.py)
gleicht damit das ganze kanonische Paket ab, bevor Zyklusidentität oder nächster
Beleg entstehen. Plan-Ergebnisdigest, Outcome, Auswertungsstatus, IDs und
No-Effect-Felder bleiben gemeinsam gebunden. Ein numerischer Nullwert ersetzt
keinen Wahrheitswert False. Schreibgeschützte Originalrückgaben und JSON-Pakete
bleiben zulässig; ursprüngliche ID- und Digestformeln werden nicht erweitert.

109 unterschiedliche Offline-Fälle bestanden: die vorhandenen 93 Fälle und
16 neue Fälle. Die zwölf Negativfälle reproduzierten vor der Korrektur die fehlende
Abweisung. Vier Positivfälle erhalten die vollständige Loop-C-Ausgabe nach
JSON-Rücklesen. Die [Rückgabe-Gegenproben](../../../tests/learning/test_representation_evaluation_return_binding_v1.py)
verwenden Originalbuilder, isolierte synthetische Eingaben und den tatsächlichen
Folgebelegconsumer. Zehn vollständige gültige Loop-C-Ausgaben einschließlich aller
Identitäten und Digests stimmen außerdem mit ihren Ausgaben vor der Korrektur
überein. Wiederholungen sind nicht doppelt gezählt.

Die Rekonstruktion des Fixture-Pakets ist kein neuer Mess- oder Trainingslauf.
Bestehende Fixture-Ergebnisse und die typisierte Nichtauswertung unbekannter Muster
bleiben erhalten; numerische Lernqualität und externe Herkunft werden damit nicht
belegt. Der nächste Forschungsbeleg ist weiterhin eine Rückgabe ohne produktiven
Lernwriter oder Modell-Apply. Seine eigenen No-Apply-/No-Mutation-Konstanten waren
bereits zuvor geschlossen. BTC, Originalstores und Betriebsfreigaben bleiben
unverändert. Der historische D01/D02-Basiskonflikt bleibt offen und wurde nicht
erneut ausgeführt; eine Gesamtsystemhärtung ist damit nicht abgenommen.

### Originalmessung bis OLS-Modell und Folgeforecast: Zeitbezug

Ausgangsbasis ist PR #7351,
`d0225e916d80b938be3b45d79dcd758d5a9cf2e4`. Der native numerische Lernpfad
ist seit dem eingefrorenen Bestand `9397d04a3` vorhanden. Der spätere
[Store-Selektor](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_ols_store_training_v1.py)
aus `45f627944` verwendet bereits die exakte Quellzeitordnung. Die vorhandene
Kette erhält Originalmessung und Calibration, Markt-/Targetidentität, Einheiten,
Samplemanifest, Modellstore, tatsächliche numerische Inferenz und Originalfreeze.
Einheiten von Trades und OHLCV werden bereits beim Kontextowner zugelassen;
ein weiterer Mengenadapter oder eine neue numerische Lernverbindung wird nicht
ergänzt. Kaltlesen bleibt ausdrücklich ohne Fit, Inferenz oder Trainingsquellen.

Eine echte Präzisionslücke lag an den vorhandenen Zeitgates des
[OLS-Adapters](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_ols_next_forecast_v1.py):
`datetime` reduzierte gültige Quellzeitbruchteile auf Mikrosekunden. Elf
Gegenproben bestätigten, dass um eine Nanosekunde widersprüchliche
Veröffentlichungs-, Label-/Trainingscutoff-, Parent-/Folgemodell- und
Modell-/Kontext-/Forecastbezüge beziehungsweise Altersgrenzen den tatsächlichen
Fitter oder Featureconsumer erreichen konnten.

Der Adapter verwendet jetzt denselben ursprünglichen Quellzeitowner wie die
Store-Auswahl. UTC-Zulassung bleibt erhalten; kanonische Bruchteile mit einer bis
neun Stellen und UTC-Offset null werden exakt geordnet. Samplechronologie und
Nichtüberlappung verwenden ebenfalls diese Ordnung. Die vorhandenen Alterslimits
in ganzen Sekunden werden ohne Rundung als ganzzahlige Nanosekunden verglichen.
Dadurch entsteht keine neue Altersgrenze oder Kalenderobergrenze. Originale
Zeitstrings, Policywerte, Fitter, Split, Koeffizienten-/Residualrechnung, Targets,
Einheiten und ID-/Digestformeln bleiben erhalten. Die normale Quellenbindung neuer
Trainingsrequests umfasst weiterhin die Implementierungsversion; eine dadurch
andere Modellreferenz ist kein Nachweis numerischen Lernfortschritts.

87 unterschiedliche Offline-Fälle bestanden: 68 vorhandene Markt-/Modell-/Mess-/
Replayfälle und 19 neue Fälle. Elf Negativfälle reproduzierten vor der Korrektur
die fehlende Abweisung. Acht Positivfälle prüfen gültige Gleichzeitigkeit,
erhaltene Zeitstrings, zulässige große Alterslimits, Wiederholung und Kaltlesen
sowie die beiden archivierten Originalmodelle ohne Fit oder Quellenmessung.
Die [Gegenproben](../../../tests/learning/test_market_ols_exact_clock_admission_v1.py)
verwenden synthetische Originaljobs in temporären Verzeichnissen und sperren den
tatsächlichen Fitter beziehungsweise Featureconsumer an der Aufnahmegrenze.
Originalmodelle bleiben bytegleich; Wiederholungen sind nicht doppelt gezählt.

Die [ursprüngliche OLS-Semantik](INDEPENDENT_MARKET_OLS_NEXT_FORECAST_V1.md)
bleibt begrenzt: Target ist LOG_RETURN, die gehaltene Residualstreuung ist keine
bewiesene Verteilungskalibrierung, und eine Prognose ist kein Kontogewinn. Diese
Änderung prüft deklarierte Chronologie an den benannten OLS-Übergaben; sie
authentifiziert weder externe Zeitquellen noch sämtliche Zeitprüfungen anderer
Owner. BTC, Originalstores, produktiver DDO-LearningState, Betriebsfreigaben und
Modell-Apply bleiben unverändert. Der historische D01/D02-Basiskonflikt bleibt
offen und wurde nicht erneut ausgeführt. Eine Gesamtsystemhärtung ist nicht belegt.

### Originalquellen bis Kontextaufnahme und archiviertes Rücklesen

Ausgangsbasis ist PR #7352,
`efe7e0a067bd477c88cf7480c3d1d2a80296dac0`. Der gemeinsame
[Kontextowner](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/context_admission_v1.py)
ist seit `9397d04a3` vorhanden. Originalbytes, kanonische/native Instrumentidentität,
Generation, Einheiten, Finalisierung, vollständige Minutenraster, native
Merkmalsberechnung und Rekonstruktion aus gespeicherten Belegen sind bereits
verbunden. Marktidentität und entscheidungsbezogene Identität bleiben getrennt;
eine neue Lern-, Karten- oder Rotationsverbindung ist hier nicht erforderlich.

Eine echte Lücke betraf die Präzision dieser Aufnahmegrenze: `datetime` schnitt
gültige Quellzeitbruchteile nach Mikrosekunden ab. Zwölf direkte Gegenproben für
beide Identitäten erreichten dadurch mit widersprüchlichen Ereignis-, Kenntnis-,
Verfügbarkeits-, Capture- oder Altersbezügen die ursprüngliche Merkmalsberechnung.
Zwei neu versiegelte Archivpakete erreichten sie beim Rücklesen ebenfalls; die
spätere vollständige Replay-Gleichheit ersetzt diese frühe Abweisung nicht.
Vier gültige Präzisionsfälle belegten außerdem verlorene Nachkommastellen in
den gespeicherten Zeitbindungen.

Beide Aufnahmen verwenden jetzt den ursprünglichen Quellzeitdecoder mit genauer
Ordnung bis neun Nachkommastellen und unveränderter UTC-Zulassung. Bestehende
Alterslimits in ganzen Sekunden werden ganzzahlig ohne Rundung verglichen.
Minutenquellen behalten Intervallstart als Ereignis und Intervallende als
Voraussetzung finaler Verfügbarkeit; O4 behält den Originalschluss. Punktquellen
behalten ihre tatsächliche Ereigniszeit. Zeitbindungen speichern die volle
Präzision in kanonischem UTC-Text; Originalpayload und Quellbytes werden nicht
umgeschrieben. Bei bereits präzisionsgetreuen Paketen bleibt die bisherige
kanonische Darstellung erhalten. Neue präzise Inhalte erhalten gegebenenfalls
über die unveränderte Digestformel eine andere Paketidentität.

Die native Open-Interest-Wertauswahl sortiert weiterhin mit Mikrosekunden. Ihre
bisherige Duplikatgrenze bleibt deshalb erhalten; genauer geordnete Quellzeiten
geben dort keine vorher abgewiesenen, intern zeitlich zusammenfallenden Werte
frei. Frühere Pakete, deren abgeschnittene Receipts den erhaltenen Originalbytes
widersprechen, werden abgewiesen. Fehlende Kenntniszeiten werden weder erfunden
noch aus Capture-Zeit oder späterer Verfügbarkeit rückdatiert.

156 unterschiedliche Offline-Fälle bestehen: 122 vorhandene Kontext-, Forecast-,
Mess-, Modell- und Replayfälle sowie 34
[neue Gegen- und Positivproben](../../../tests/learning/test_context_exact_clock_admission_v1.py).
Die neuen Fälle umfassen frühe Abweisung, präzise Gleichzeitigkeit,
Originalbytes, Archiv-Rücklesen, Wiederholung, erhaltene Open-Interest-Grenzen,
große gültige Alterslimits und unveränderte typisierte Enthaltung. Zwölf vor der
Korrektur gesicherte vollständige Pakete sind danach einschließlich Referenzen
und Digests bytegleich. Der OLS-Zeittestaufbau gibt dem Quellkontext bei
absichtlich späterem Beobachtungszeitpunkt eine Sekunde Altersreserve, damit
seine eigenständigen späteren OLS-Grenzprüfungen erreichbar bleiben. Produktive
Policies und Altersgrenzen ändern sich dadurch nicht.

Die [ursprüngliche Marktbeobachtungssemantik](INDEPENDENT_MARKET_OBSERVATION_V1.md)
bleibt maßgeblich. Diese Änderung belegt die benannte Aufnahme- und Rücklesekette,
keine durchgängige Präzision sämtlicher anderer Owner oder Betriebsbereitschaft.
BTC, Originalstores, numerische Merkmalsformeln, Betriebsfreigaben und Apply
bleiben unverändert; es wurde kein Betriebs-, Paper-, Shadow- oder Forschungslauf
gestartet. Der historische D01/D02-Basiskonflikt bleibt offen und wurde nicht
erneut ausgeführt.

### Gelieferter Forecast bis Freeze und entscheidungsbezogener Messaufnahme

Ausgangsbasis ist PR #7353,
`2a15f3fa16d94b1d2de47bc3409dde31eeba7aa4`. Der gemeinsame
[Freeze- und Messadapter](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/forecast_measurement_integration_v1.py)
stammt aus `9397d04a3`; `2d8fe77e8` ergänzte den unveränderlichen Markt-Forecastreader.
Kontext-Replay, Modellartefaktbytes, Provider-/Kontextbindung, Instrument und Target,
vollständiger Jobschlüssel, Original-Forecastpayload, atomare Publikation,
Originalkalibrierung, typisierte SL-/OPT-Übergaben und numerisches Kaltlesen sind
bereits verbunden. Es wird kein neuer Forecastprovider oder Forschungsauftrag
angeschlossen.

Eine echte Präzisionslücke lag in den bestehenden Zeitgates vor der Publikation.
`datetime` reduzierte gültige Zeitbruchteile auf Mikrosekunden. Zwölf Gegenproben
für Markt- und Entscheidungsidentität erreichten mit widersprüchlichem
Trainingsende, Modellverfügbarkeit, Kontext-/Forecastzeit, Kontextalter,
Forecast-/Horizontstart oder abweichendem Forecastende die Grenze zum originalen
Schreibpfad. Zwei weitere Gegenproben erreichten diese Grenze mit einer deklarierten
Messverfügbarkeit eine Nanosekunde nach der Auswertungszeit.

Die Gates verwenden jetzt die ursprüngliche Quellzeitordnung bis neun Stellen
bei unveränderter UTC-Zulassung. Die vorhandene Kontextaltersgrenze in ganzen
Sekunden wird ohne Rundung ganzzahlig verglichen. Alle Abweisungen erfolgen vor
Lease, Forecast-/Messattachment und Originalkalibrierung. Die bestehenden
Zeitrelationen bleiben erhalten: Trainingsende ≤ Modellverfügbarkeit ≤ Kontext
≤ Forecast ≤ Targetstart; Rückgabeschluss und Forecastende müssen denselben
Zeitpunkt bezeichnen. Bei der entscheidungsbezogenen Messaufnahme gilt weiterhin
Forecastende ≤ deklarierte Messverfügbarkeit ≤ Auswertungszeit der gelieferten
Observation. Die separate tatsächliche Auswertungszeit der unabhängigen
Marktbeobachtung wird nicht in diese andere Observation umgedeutet.

202 unterschiedliche Offline-Fälle bestehen: 174 vorhandene Kontext-, Forecast-,
Mess-, Kalibrierungs-, Modell- und Replayfälle sowie 28
[neue Gegen- und Positivproben](../../../tests/learning/test_forecast_freeze_exact_clock_v1.py).
14 Negativfälle belegen frühe Abweisung vor dem tatsächlichen Lease-/Schreibpfad.
14 Positivfälle erhalten präzise Modellzeitgleichheit, UTC-Offset null, große
gültige Alterslimits, Gleichheit am Horizontstart, äquivalente Endzeitdarstellungen,
Originalstrings, Messzeitgleichheit, unveränderliche Wiederholung und Kaltlesen.
Zwölf vor der Änderung gesicherte vollständige Freeze-Pakete bleiben danach
einschließlich Job, Forecast, Kontext und Digests bytegleich. Alte Prüfläufe werden
nicht zusätzlich als neue Fälle gezählt.

Der [ursprüngliche Übergabevertrag](INTELLIGENCE_EXACT_FORECAST_MEASUREMENT_HANDOFF_V1.md)
behält seine Grenzen: Provider-/Trainings-/Admissionangaben sind gelieferte
Belege, keine unabhängige Beglaubigung oder Inferenzbestätigung. LOG_RETURN über
N−1 Schlussintervalle, Prognosefehler, wirtschaftliches Ergebnis und Applyfreigabe
bleiben getrennt. Originalstrings, Zahlenrechnung, Policies, Stores und
ID-/Digestformeln ändern sich nicht. Kaltlesen bleibt reine Inhalts-/Parent- und
Zahlenprüfung ohne erneute Kontextberechnung oder Modellzulassung; ältere Archive
werden nicht umgeschrieben oder rückwirkend als zeitlich korrekt bestätigt.
Andere Messzeitowner bleiben gesondert zu prüfen. BTC und Betriebsfreigaben
bleiben unverändert; keine Betriebs-, Paper-, Shadow- oder Forschungsläufe wurden
gestartet. Der historische D01/D02-Basiskonflikt bleibt offen und wurde nicht
erneut ausgeführt. Dieser Block ist kein Nachweis vollständiger Systemhärtung.

### Unabhängige Markt-Receipts bis Return und Kalibrierung

Ausgangsbasis ist PR #7354,
`191303305d1c0e5719aae350016cd16a6e993580`. Der
[Markt-Messowner](../../../src/learning/deterministic_decision_outcome_v0/independent_market_horizon_v1.py)
ist im Bestand `9397d04a3` bereits vorhanden und blieb bis zu dieser Ausgangsbasis
unverändert. Die [datierte Ursprungsanalyse](../evidence/mi_independent_market_observation_history_2026_11_06/README.md)
trennt Markt-/Baridentität und Messrecord bereits von der eigenständigen
DDO-Attribution. Request und Originalreceipts, Sourcebytes, Instrument-/Venue- und
Generationsbindung, Preisfamilie und Einheiten, vollständiges finales Stundenraster,
native Returnrechnung und erneute Beobachtungsprüfung am Kalibrierungsconsumer
sind bereits verbunden. Ein zweiter Messowner oder ein künstliches DecisionEvent
wird nicht ergänzt.

Eine echte Präzisionslücke lag an den vorhandenen Raster-, Receipt- und
Altersprüfungen: `datetime` und nachfolgende Unix-Fließkommawerte verloren gültige
Zeitbruchteile. Dreizehn Gegenproben erreichten damit den tatsächlichen nativen
Returnkern: widersprüchliche Kenntnis-/Verfügbarkeits-/Auswertungszeiten,
überschrittenes Endalter, ihre Wiederaufnahme aus neu versiegelten Observationen
am Kalibrierungsconsumer sowie ein um eine Nanosekunde verschobener
Messrequest-Start. Eine zusätzliche Gegenprobe zeigte, dass der Targetbuilder
diesen rasterfremden Start ebenfalls zuließ.

Der Owner verwendet jetzt die ursprüngliche Quellzeitordnung bis neun Stellen
bei erhaltener UTC-Zulassung. Der Start muss vollständig auf dem bestehenden
Stundenraster liegen; ein nicht nullwertiger Bruchteil wird nicht weggerundet.
Erst das unverändert geprüfte vollständige Bar-Raster belegt die ganzen
Schlusszeiten. Danach gilt ohne Fließkommarundung weiterhin Schluss ≤ Kenntnis
≤ Verfügbarkeit ≤ tatsächliche Auswertung. Das Endalter wird ganzzahlig gegen
die unveränderte explizite Sekundengrenze geprüft. Alle Abweisungen erfolgen vor
nativer Returnberechnung; die vorhandene erneute Beobachtungsprüfung vor
Kalibrierung und Attachments verwendet dieselben Gates. Ein frischer Digest
ersetzt keine Zeitkonsistenz.

246 unterschiedliche Offline-Fälle bestehen: 216 vorhandene Kontext-, Forecast-,
Mess-, Kalibrierungs-, Modell-, Replay- und ursprüngliche DDO-O4-Fälle sowie 30
[neue Gegen- und Positivproben](../../../tests/learning/test_market_horizon_exact_clock_admission_v1.py).
Die 14 Negativfälle belegen die beschriebenen Abweisungen. 16 Positivfälle
erhalten präzise Receipt-Zeitgleichheit, UTC-Offset null, zulässige Altersgrenzen
einschließlich null und großer Werte, nullwertige Rasterbruchteile, ursprüngliche
Receipt-Reihenfolge, korrigierte und unkorrigierte Quellen, Originalbytes, Kalibrierung,
Wiederholung und Kaltlesen ohne Neuberechnung. Sechzehn vor der Korrektur
gesicherte vollständige Observationen samt Targets bleiben danach einschließlich
Messidentitäten und Digests bytegleich.

Die [ursprüngliche Marktbeobachtungssemantik](INDEPENDENT_MARKET_OBSERVATION_V1.md)
bleibt erhalten: LOG_RETURN verwendet ersten und letzten Close der N Bars, also
N−1 Intervalle. Die native Messung behält den logischen Horizontschluss als
Evaluationzeit; das separate tatsächliche evaluated-at-Feld und die
Receipt-Zeiten werden nicht darauf rückdatiert. Eine deklarierte Uhrzeit ist
keine externe Quellenbeglaubigung. Preisbasis, Originalstrings und -bytes,
Einheiten, Formeln, Sourcegeneration, IDs und Policies ändern sich nicht.
Kaltlesen bleibt Inhalts-/Parent- und Zahlenprüfung ohne erneute Messung;
historische Archive werden nicht umgeschrieben oder rückwirkend zeitlich
zertifiziert. Andere Owner und vollständige Systemhärtung bleiben gesondert zu
prüfen. BTC und Betriebsfreigaben bleiben unverändert; keine Betriebs-, Paper-,
Shadow- oder Forschungsläufe wurden gestartet. Der historische D01/D02-Konflikt
bleibt offen und wurde nicht erneut ausgeführt.

### Nativer Forecast-/Outcome-Join bis zum typisierten MI-Lernbeleg

Ausgangsbasis ist PR #7355,
`4a6247c1f81bdff8d4a7ad252765a99c8ed17337`. Der
[native Join](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/forecast_outcome_join_v1.py)
und die [typisierte Lernbrücke](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/mi_to_learning_evidence_bridge_v1.py)
enthalten ihre Zeitbedingungen bereits im Bestand `9397d04a3`; die spätere
Join-Änderung in `50fb4cb9c` war an dieser Stelle reine Formatierung. Native
Forecast-/Observationvalidierung, N-/Barspezifikation, Outcomeverweis,
Originalkalibrierung, kanonischer MI-Inhaltsdigest, Lernstore und Export sind
bereits verbunden. Die stärkeren vorgelagerten Freeze- und Markt-Messgates
ersetzen diese eigenständig aufrufbaren nativen und typisierten Aufnahmen nicht.

Eine echte Präzisionslücke betraf bestehende Zeitvergleiche mit `datetime`.
Zwei direkte Gegenproben ließen einen um eine beziehungsweise 999 Nanosekunden
abweichenden Forecastschluss an denselben Originalschluss anschließen. Sechs
weitere Fälle erreichten damit über native Kalibrierung, Lernbrücke oder
Lern-Ingest die tatsächliche Kalibrierungsgrenze. Vier Fälle erreichten den
Join aus der Lernbrücke beziehungsweise dem Ingest, obwohl der Forecast bereits
knapp nach dem Horizontstart entstand. Neue IDs oder ein gültiger Record-Digest
machen diese Zeitwidersprüche nicht richtig.

Der native Join verwendet jetzt die ursprüngliche Quellzeitordnung für die
Gleichheit von Forecastende und letztem Originalclose. Die Lernbrücke prüft ihre
bestehenden Zeitrelationen in derselben Präzision, bevor Join, Kalibrierung und
Store-Append erreicht werden. Die bisherige UTC-Z-Zulassung bleibt erhalten;
Originalzeitstrings werden nicht umformatiert. Eine spätere Auswertungszeit ist
weiterhin zulässig und wird nicht als neuer Outcome-Schluss verwendet. Eine
äquivalente nullwertige Bruchteilsschreibweise bleibt zeitlich gleich; ein
tatsächlich anderer Zeitpunkt nicht.

303 unterschiedliche Offline-Fälle bestehen: 279 vorhandene Kontext-, Forecast-,
Mess-, Kalibrierungs-, DDO-O4-, Lern-/Export-, Orchestrator- und bedingte Lernfälle
sowie 24 [neue Gegen- und Positivproben](../../../tests/learning/test_mi_learning_exact_clock_admission_v1.py).
Zwölf Negativfälle belegen die beschriebenen Aufnahmegrenzen. Zwölf Positivfälle
für N=2 und N=3 erhalten Originalzeitstrings, äquivalente Enddarstellung,
spätere Auswertung, fehlenden Outcome, unzureichende Evidenz und vollständig
mitgelieferte Originalkalibrierung einschließlich ihrer Provenienz. Originalstore,
unveränderliche Wiederholung, Kaltlesen und Export werden ebenfalls geprüft.
Zwölf vor der Korrektur gesicherte vollständige Pakete aus Join, Kalibrierung,
Lernrecord und Export bleiben danach einschließlich IDs und Digests bytegleich.

Der [ursprüngliche Phase-8-Vertrag](UNIFIED_BLUEPRINT_PHASE_8_MI_TO_LEARNING_INTEGRATION_NORMATIVE_V1.md)
behält seine Grenzen. MI-Lernbeleg, DDO-Entscheidung und produktiver LearningState
sind verschiedene Objekte. Kalibrierungsmethoden und numerische Formeln werden
hier weder geändert noch als inhaltlich richtig oder wirtschaftlich erfolgreich
zertifiziert. Digest- und ID-Formeln bleiben erhalten. Fehlender Outcome bleibt
NOT_EVALUABLE; unzureichende Evidenz bleibt typisierte Enthaltung. Kaltlesen bleibt
ohne neue Kalibrierung; historische Records werden nicht umgeschrieben oder
rückwirkend zeitlich zertifiziert. Die separaten Forecast-, Kontext- und übrigen
Zeitowner bleiben gesondert zu prüfen. BTC, Betriebsfreigaben und produktive
Reducer bleiben unverändert; keine Betriebs-, Paper-, Shadow- oder Forschungsläufe
wurden gestartet. Der historische D01/D02-Basiskonflikt bleibt offen und wurde
nicht erneut ausgeführt. Eine vollständige Systemhärtung ist damit nicht belegt.

### Kontext → Verhalten → bedingter Lernbeleg: Originalzeitordnung am 21. November

Geprüfter Ausgangspunkt ist Merge `bbd8b5c5b2caf2699b01f6f5320641961e5b8d1f`
(PR #7356). Kontextfamilien, N_BARS-Verhaltensjoin, bedingter MI-Lernbeleg und
Writer/Store/Export sind bereits verbunden. Die vorhandenen Zeitbedingungen
verloren jedoch an drei Übergängen Originalpräzision; im Zweig ohne Ergebnis
wurde die Kontextzeitbedingung vollständig übersprungen.

Vor der Korrektur ließen 14 Gegenproben über alle sieben Kontextfamilien um
eine beziehungsweise 999 Nanosekunden zukünftige PIT-Beiträge zu. Sechs
Verhaltensfälle erreichten trotz zeitlichem Widerspruch den ursprünglichen
Forward-Behavior-Materialisierer; zehn Composer-/Ingest-Fälle erreichten die
ursprüngliche MI-Brücke. Darunter sind fehlende Outcomes mit einem Kontext
nach Forecastentstehung, auch mit einer ganzen Sekunde Abstand. Ein gültiger
numerischer O4-Zeitpunkt unterhalb einer fraktionalen Auswertungsgrenze wurde
umgekehrt wegen Rundung fälschlich zurückgewiesen.

Die drei bestehenden Owner verwenden jetzt die vorhandene Quellzeitordnung.
Kontextbeiträge dürfen nicht nach Kontextbeobachtung liegen; der Kontext darf
nicht nach Horizontstart beziehungsweise Forecastentstehung liegen; letzter
Close und O4-Beobachtung dürfen die Auswertung nicht überschreiten. Die bedingte
Aufnahme prüft den Kontext bereits vor MI-Brücke/Kalibrierung, auch ohne Outcome.
O4-Zahlen bleiben Unix-Sekunden mit dem tatsächlich dargestellten Zahlenwert;
UTC-Z-Zeitstrings behalten bis zu neun Bruchteilziffern. Nichtendliche O4-Zahlen
werden als ungültige Zeitangaben abgewiesen. Keine neue Toleranz oder
Zeitnormalisierung wird eingeführt.

Acht vor der Korrektur gesicherte vollständige Originalpakete aus Kontext,
Forecast, Verhaltensbeleg, Lernrecord und Export bleiben danach bytegleich,
einschließlich Identitäten und Digests. Die
[neuen Offline-Gegen- und Positivproben](../../../tests/learning/test_conditioned_learning_exact_clock_v1.py)
prüfen außerdem den bestehenden Ingest, idempotente Persistenz, Kaltlesen und
Export. Insgesamt bestehen 153 unterschiedliche Offline-Fälle: 111 vorhandene
Kontext-, Verhaltens-, Lern-, Export-, inkrementelle Evidenz- und Governancefälle
sowie 42 neue Fälle. Der ursprüngliche Abgleich reproduzierte 31 Fehler bei
acht bereits gültigen Positivfällen; drei weitere neue Fälle sichern ungültige
nichtendliche O4-Zeiten ab. Die ursprünglichen Verträge für
[Kontext](UNIFIED_BLUEPRINT_PHASE_17_NORMATIVE_NON_PRICE_CMC_CONTRACT_NORMATIVE_V1.md),
[Verhalten](UNIFIED_BLUEPRINT_PHASE_20_BEHAVIOR_JOIN_NORMATIVE_V1.md) und
[bedingtes Lernen](UNIFIED_BLUEPRINT_PHASE_21_LEARNING_INTEGRATION_NORMATIVE_V1.md)
halten die fachlichen Grenzen fest.

Der Kontext ist eine beigefügte bedingte Evidenz, kein Beweis seines tatsächlichen
Verbrauchs durch den ursprünglichen Forecast. Deshalb wird keine neue Gleichheit
verschiedener Information-Set-IDs erfunden. Später gemessenes Verhalten bleibt
von ursprünglicher Entscheidung und produktivem LearningState getrennt.
Fehlender Outcome bleibt NOT_EVALUABLE, unzureichende Evidenz bleibt Enthaltung;
klassische MFE/MAE und Regimeübergang bleiben semantisch offen. Preis-/Return- und
Kalibrierungsformeln sowie IDs/Digests werden nicht verändert oder fachlich
gesamtzertifiziert. Kaltlesen von MI-Lernrecords erzeugt keine neue Kalibrierung
und keine rückwirkende Zeitfreigabe. Andere kausale Wege bleiben gesondert zu
prüfen. BTC bleibt unverändert; keine Betriebs-, Paper-, Shadow- oder
Forschungsläufe werden gestartet. Der historische D01/D02-Basiskonflikt bleibt
offen. Eine vollständige Systemhärtung ist weiterhin nicht belegt.

### Forschungs-Vorgängerbeleg vor M4: Inhalts- und Bedeutungsbindung am 21. November

Ausgangspunkt ist Merge `e4575dd5bfe267c2c1f7a87403c5fb189f2aa19c`
(PR #7357). Die vorhandene Phase-22-Kette projiziert Kontextfamilien, erzeugt
Information-Set-/Datasetidentitäten und führt Forschungs-, Vergleichs-, Failure-
und Meta-Belege über die bestehenden Owner weiter. Bereits gehärtet ist die
unmittelbare Stufenfolge: Ein B0-Beleg darf nicht als B1-Vorgänger einer B2-Stufe
ausgegeben werden; B0 selbst darf keinen Vorgänger konsumieren. Die direkte
Aufnahme prüfte danach aber nicht den vollständigen Vorgängerinhalt.

15 synthetische Gegenproben erreichten vor der Korrektur den tatsächlichen
M4-Consumer: veränderte Bewertung, Merkmalsdigest oder Plane-Referenz unter
beibehaltenem Originaldigest, ungültige Vertragsangaben sowie beschädigte oder
aus anderen nativen Belegen zusammengesetzte Information-Set-/Datasetbindungen.
Auch ein neu berechneter äußerer Hash machte innere ID- und Bedeutungswidersprüche
nicht richtig. Die isolierte Horizontgegenprobe hält alle übrigen Referenzen
unverändert und weist denselben Übergabefehler nach.

Die bestehende aktive Aufnahme prüft jetzt vor Kontextprojektion und M4-Plane den
gesamten gespeicherten Stufendigest, das native Schema, das vorhandene
Bewertungsvokabular und Authority NONE. Sie reproduziert Information-Set und
Dataset mit ihren ursprünglichen Metadatenbuildern und prüft die inneren Bezüge
auf Stufe, Vorgängerstufe, Information-Set-ID, Horizont und Verhaltensversion.
Das ist Metadatenprüfung; sie startet keinen Forschungsversuch und führt den
Vorgänger nicht erneut aus. Originalkonstruktion, ID-/Digestformeln, Writer und
numerische Regeln bleiben erhalten.

Fünf vor der Korrektur gesicherte vollständige Originalpakete bleiben bytegleich:
zusammenhängende B0–B4-Kette, B0–DEFERRED B5, fehlender Vorgänger, explizit fehlende
Familie und ein intern konsistenter Vorgänger mit anderem Horizont. Unveränderte
JSON-Belege bleiben konsumierbar. Die
[neuen Offline-Gegen- und Positivproben](../../../tests/learning/test_incremental_predecessor_content_admission_v1.py)
prüfen den tatsächlichen M4-Eingang und die unveränderten temporären Eingaben.
Der frühe B5-Zweig konsumiert weiterhin weder Vorgänger noch Plane. Der
[ursprüngliche Phase-22-Vertrag](UNIFIED_BLUEPRINT_PHASE_22_INCREMENTAL_RESEARCH_NORMATIVE_V1.md)
benennt diese Grenze ausdrücklich.

80 unterschiedliche Offline-Fälle bestehen: 59 vorhandene Informationsset-,
Stufenfolge-, Phase-22-, M4-, Rückgabe-/Experimentbeleg-, Meta-Ingest- und
Governancefälle sowie 21 neue Gegen- und Positivproben. Die vollständigen
ursprünglichen Fehlbelege bleiben getrennt vom bestandenen Nachweis erhalten.

Ein unveränderter Beleg beweist seine innere Integrität, nicht die fachliche
Richtigkeit seiner gelieferten Scores oder seine Herkunftsauthentizität. Der
ältere Phase-22-Wrapper berechnet den Challenger-Delta weiterhin aus gelieferten
M4-Champion-/Challengerscores; die Gleichheit zum gemessenen unmittelbaren
Vorgänger ist hier nicht belegt. Dataset-Zeitflags sind deklarierte Metadaten,
kein Nachweis tatsächlich getrennter Trainings-/OOS-Daten. Vergleichbarkeit von
Samples, Fenstern, Targets und Horizonten zwischen zwei Stufen bleibt separat
offen; dafür wird keine neue globale Gleichheit erfunden. Der getrennte
Paired-Market-Research-Pfad und numerische Lernqualität werden durch diese
Übergabehärtung nicht zertifiziert. Vorhandene Failure-Labels werden nicht als
neu bewiesene Fehlerursache interpretiert. BTC, Originalstores, Betriebsfreigaben
und produktive Reducer bleiben unverändert. Keine Betriebs-, Paper-, Shadow- oder
Forschungsläufe wurden gestartet. Der historische D01/D02-Basiskonflikt bleibt
offen und wird nicht durch diese gezielten Prüfungen ersetzt.

### Gepaarter B0-/B1-Vergleich: Originalzeit bis zum Meta-Rückweg am 22. November

Geprüfter Ausgangspunkt ist Merge `d3d15bb7b02869d573904f00b274e605b67d527a`
(PR #7358). Der getrennte Paired-Market-Owner stammt aus `d2f16d9ae` und ist
bereits mit ursprünglichem Forecastfreeze, Kontextreplay, Originalmessung,
gemeinsamer B0-/B1-Fallmenge, Zeit-Holdout, RMSE-Vergleich und dem
Learning-Research-Meta-Rückweg verbunden. Target, Instrument/Quellengeneration,
Einheiten, doppelte Originaljobs/Outcomes, Versionsbezüge und vollständige
Meta-Reproduktion besitzen bestehende Gates. Eine neue Übergabearchitektur
ist dafür nicht erforderlich.

Eine belegte Präzisionslücke lag in den eigenen Zeitvergleichen und in der
Fallordnung anhand der gekürzten Darstellung. Acht Gegenproben mit um eine
beziehungsweise 999 Nanosekunden verspäteten Labels, überlappenden Fällen oder
falscher Holdout-Zuordnung erreichten die Merkmalsberechnung. Zwei weitere
Forecast-/Auswertungswidersprüche erreichten den nächsten Messungsreader.
Drei zulässige Fälle wurden umgekehrt falsch eingeordnet: zwei FIT-Kontexte
knapp vor ihrem Cutoff sowie ein Fall mit zwei verschiedenen noch ungemessenen
Originalzeitpunkten, deren Mikrosekundendarstellung identisch ist. Der mit nativen
Original-APIs aufgebaute Ausgangsabgleich hielt 13 Fehler und acht gültige
Positivfälle fest. Synthetische Frischevorgaben werden dabei ausdrücklich im
vorhandenen Vertrag angegeben; Produktionslimits werden nicht verändert.

Die bestehenden Zeitrelationen verwenden jetzt die vorhandene Quellzeitordnung.
Die Fallliste und die strenge Zeit-Eindeutigkeit werden an den gebundenen
Originalkontexten geprüft. Später verfügbare Ergebnisse bleiben ausdrücklich
LABEL_NOT_AVAILABLE_AT_CUTOFF, enthalten kein numerisches Target und führen
zur Nichtauswertung. Ein FIT-Kontext vor dem Cutoff ist zeitlich zulässig;
dadurch wird sein späteres Ergebnis nicht automatisch verfügbar. Forecast-,
Split- und Überlappungswidersprüche stoppen vor dem nächsten Consumer.

Die bestehende `context_as_of`-Darstellung in Fallrecord und Matrix bleibt zur
Artefaktkompatibilität auf Mikrosekunden kanonisiert. Sie ersetzt keine
Quellzeit. Die vollständige Originalzeit bleibt an Kontext-/Jobidentität und
Digest gebunden und wird für Aufnahme und Sortierung verwendet. Verschiedene
Pending-Originale mit derselben Anzeige bleiben als verschiedene, unvollständige
Belege erkennbar; sie werden nicht zu Trainingsfällen. Die genaue Fallordnung
bleibt auch bei umgekehrter Eingabereihenfolge erhalten.

147 unterschiedliche Offline-Fälle bestehen: 126 vorhandene Markt-/OLS-,
Zeitaufnahme-, Mess-/Freeze-, Phase-22- und Governancefälle sowie
21 [neue Gegen- und Positivproben](../../../tests/learning/test_paired_market_exact_clock_admission_v1.py).
Acht vor der Korrektur gesicherte vollständige Vergleichs- und Meta-Pakete
bleiben bytegleich, einschließlich IDs, Digests, Fits, Holdoutfehlern,
Forschungsfrage, Router und Plan. Sie erhalten nullwertige Bruchteilsschreibweise,
UTC-Offset null, zulässige Gleichheit am Holdout-Cutoff, fehlenden Proxy,
Pending-Messung, blockierten Fit und den vorhandenen Fall eines späten Labels.
Die synthetischen Originaldateien bleiben ebenfalls bytegleich.

Der [Phase-22-Vertrag](UNIFIED_BLUEPRINT_PHASE_22_INCREMENTAL_RESEARCH_NORMATIVE_V1.md)
trennt diesen numerischen Paired-Pfad weiterhin vom älteren Wrapper mit
gelieferten Scores. B0 bleibt Preis/Flow, B1 ergänzt den OHLCV-Proxy und kein
TRUE_L2. Der Delta ist RMSE(B0) minus RMSE(B1) in LOG_RETURN, kein Kontogewinn.
Ein einzelner chronologischer Holdout ist keine unabhängige Qualitätsabnahme.
Die Meta-Frage und der daraus gebildete Plan bleiben Research, ohne Apply- oder
Betriebsfreigabe. Historische Records werden nicht umgeschrieben oder rückwirkend
zeitlich zertifiziert. Andere Signal-/Rückwege, der D01/D02-Basiskonflikt und
Gesamtbetriebsbereitschaft bleiben offen. BTC, Originalstores und produktive
Reducer bleiben unverändert; keine Betriebs-, Paper-, Shadow- oder
Forschungsläufe wurden gestartet.

### Originalzeitbindung des deklarierten Repräsentationskohortenplans — 22. November

Geprüft wurde der Anschluss vom gespeicherten Kohortenplan über Originalforecast,
gemessenes Vorgängerergebnis und Nachfolgeplan an Vergleich und Meta-Übergabe.
Vergleichsrekonstruktion, Forschungsfrage, typisierter Router und Forschungsplan
sind bereits verbunden und prüfen ihre Inhalts- und Bedeutungsbindungen.
An diesen Ownern wurde keine zusätzliche Logik ergänzt.

Vier vorhandene Zeitprüfungen verloren jedoch Nachkommastellen jenseits von
Mikrosekunden: die Stundenraster-Zulassung des Nachfolgers und der Kohorte sowie
die beiden Meta-Zuordnungen des deklarierten Starts zu Originalforecast und
Nachfolgeanfrage. Acht synthetische Gegenproben erreichten dadurch den nächsten
Consumer trotz einer Abweichung um 1 beziehungsweise 999 Nanosekunden. Neun
gültige Kontrollfälle bestanden bereits vor der Korrektur.

Diese vier Prüfungen verwenden jetzt die vollständige vorhandene Quellzeit.
Ein Start knapp nach einer vollen Stunde wird vor der üblichen Kanonisierung
abgewiesen. Eine neu versiegelte widersprüchliche Plandeklaration ersetzt nicht
die Originalzeit des eingefrorenen Targets oder des Nachfolgeplans. Nullwertige
Bruchteile und UTC-Offset null bleiben zulässig und zeitlich gleichwertig.
Aufteilung, Mindestabstand, Rechenverfahren und Zuständigkeiten bleiben erhalten.

51 Offline-Fälle bestehen: 34 vorhandene Kontrollen und 17
[neue Gegen- und Positivproben](../../../tests/ops/test_representation_cohort_clock_binding_v1.py).
Drei vor der Korrektur gesicherte vollständige Originalketten mit jeweils acht
Jobs bleiben bytegleich, einschließlich Forecasts, Calibration, Nachfolgeplänen,
Links, Jobidentitäten und Receipt-Zeiten; alle 306 Originaldateien sind unverändert.
Der fokussierte Meta-Test ersetzt allein das Capture-Advance durch nativen
Calibration-Readback. Der bestehende synthetische Integrationstest prüft daneben
den echten Capture-/Readback-Anschluss, Vergleich, Meta, Folgeforschung und
erneutes Lesen nach Prozessende mit Fixtureantworten beziehungsweise Netzsperre.

Der [Phase-22-Vertrag](UNIFIED_BLUEPRINT_PHASE_22_INCREMENTAL_RESEARCH_NORMATIVE_V1.md)
beschreibt diese begrenzte Zeitbindung. Ein Researchplan erteilt keine Apply- oder
Betriebsfreigabe; Vergleichs-RMSE ist weiterhin LOG_RETURN und kein Kontogewinn.
Andere Zeitrelationen dieser Skripte, weitere Signal-/Rückwege, der historische
D01/D02-Basiskonflikt und Gesamtbetriebsbereitschaft bleiben offen. BTC und
betriebliche Stores bleiben unverändert. Keine Betriebs-, Paper-, Shadow- oder
Forschungsläufe wurden gestartet.

### Folgeforschung und ursprüngliche Antwortzeiten — 22. November

Der in `03871e22d` eingeführte Folgeversuch liest den ursprünglichen Meta-Plan
zurück und bindet dessen Forschungszweck, Repräsentationslinie, Target und Split.
Seit `02248b61d` wird auch die vollständige gespeicherte Antwort vor einer
weiteren Wiederholung aus ihren ursprünglichen Kohorten rekonstruiert.
Diese Inhaltsbindungen waren vorhanden und wurden nicht neu aufgebaut.

Fünf vorhandene Zeitgates des Folgeforschungsadapters verloren jedoch
Nanosekunden. Der Ausgangsabgleich reproduzierte acht unzulässige Übergänge:
zwei Starts neben dem Stundenraster sowie je zwei Widersprüche bei neuer
Deklaration, Planreplay und Antwort-Readback. Vier zulässige Kontexte knapp nach
der ursprünglichen Auswertung wurden umgekehrt als zeitgleich abgewiesen.
Zehn Kontrollfälle bestanden bereits vor der Korrektur.

Jetzt gilt die vorhandene Reihenfolge mit voller Quellpräzision:
Elternauswertung < neuer Kontext <= Forecastverifikation <= Deklaration < erstes
Fenster. Die beiden strikten Grenzen bleiben strikt. Gleichheit zwischen
Verifikation und Deklaration bleibt zulässig. Der Stundenrastercheck prüft die
Originaleingabe vor der bisherigen Kanonisierung. Eine Neusiegelung widersprüchlicher
Zeiten repariert ihren Bedeutungsbezug nicht.

73 Offline-Fälle bestehen: 51 vorhandene Kontrollen und 22
[neue Gegen-/Positivproben](../../../tests/ops/test_representation_follow_up_clock_binding_v1.py).
Die fokussierten Tests
verwenden native aufgezeichnete Kontexte, Freeze- und Messplan-APIs. Der bereits
verifizierte Parentvertrag wird in diesen isolierten Helfertests ausdrücklich
vorgegeben; dies ersetzt keinen Meta-Herkunftsnachweis. Der bestehende synthetische
Integrationstest prüft daneben Originalaufnahme, Vergleich, tatsächlichen
Meta-Plan, Folgeversuch, wiederholte Antwort und Cold-Replay.

Zwei vor der Korrektur gesicherte vollständige Antworten bleiben beim nativen
Readback bytegleich, ebenso zehn vollständige Vergleichs-/Meta-/Folgeplan- und
Antwortpakete und sämtliche 472 synthetischen Originaldateien. Netzwerkzugriff
ist bei diesem Readback ausdrücklich gesperrt. Zahlenrechnung, Featureversionen,
Split, Mindestabstand und Schema-/ID-/Digestformeln bleiben erhalten.

Der [Phase-22-Vertrag](UNIFIED_BLUEPRINT_PHASE_22_INCREMENTAL_RESEARCH_NORMATIVE_V1.md)
grenzt die Härtung ab: Die Antwort bleibt Forschung, independent_quality_proven
und productive_apply_authorized bleiben false. LOG_RETURN-RMSE ist kein
Kontogewinn. Der separate Mess-/Captureadapter, weitere kausale Wege und der
historische D01/D02-Basiskonflikt sind damit nicht abgenommen. BTC und betriebliche
Stores bleiben unverändert; keine Betriebs- oder Forschungsläufe wurden gestartet.

### Mess-/Captureadapter und D01/D02-Versionsabgleich — 22. November

Die beiden zuvor ausgenommenen Themen wurden gezielt bearbeitet. Der
Mess-/Captureadapter vergleicht Forecastverifikation, Erfassungsfenster und
Archivbeleg jetzt mit vollständiger Originalzeit. Die bestehenden inklusiven
Fristen, stündlichen Fenster, UTC-Zulassung und Zahlenrechnung bleiben erhalten.
Ein verspäteter neuer Capture stoppt vor dem Captureconsumer, ein verspäteter
oder noch nicht verfügbarer Archivbeleg vor der Originalmessung. Ein rechtzeitig
gespeicherter Beleg bleibt auch beim späteren Wiederanlauf lesbar.

Der Captureproducer prüft den unveränderten Stundenrastervertrag am rohen Input
und die Reihenfolge Anfrage <= Antwort vor der Seitenspeicherung. Die letzte
Antwort wird zeitlich bestimmt, ihr Originaltext bleibt im Manifest erhalten.
Der Ausgangsabgleich reproduzierte 14 Fehlfälle; sechs gültige Rand-/UTC-Fälle
bestanden bereits. Sechs zuvor gesicherte vollständige Originalpakete bleiben
bytegleich, ebenso alle 90 synthetischen Originaldateien. Der
[Marktvertrag](INDEPENDENT_MARKET_OBSERVATION_V1.md) grenzt Zeitkonsistenz von
Quellenbeglaubigung und wirtschaftlicher Qualität ab.

Der ursprüngliche D01/D02-Gesamtprüffall besteht jetzt. Die Ursache war ein
September-Abgleich gegen eine später fortgeschriebene Karte mit Oktober-Bezug.
Beide Werte bleiben erhalten: Sie sind historische Bezugspunkte, nicht die
Dateiidentität der Karte. Die vorhandene Karte wird an die exakten Bytes des
unveränderten Freeze-Quellstands gebunden. Weder passender HEAD noch geänderter
Baseline-Text oder nachgerechneter Hash einer fremden Karte ersetzt diese Bindung.
Zehn neue Gegen-/Positivfälle deckten vor der Korrektur falsche Zulassungen bzw.
Ablehnungen auf; zwei weitere Kontrollen bestanden bereits.

Die ergänzende Prüfung des alten Kartentools reproduzierte drei veraltete
Testerwartungen. Die fünf Ansichten wurden im dokumentierten Cleanup bewusst
entfernt; ihre neu gerenderten Inhalte stimmen mit sämtlichen Lösch-Hashes
überein. Acht fehlende Verweisdiagnosen an drei historischen Pfaden bleiben
ausdrücklich erhalten. Die historischen Tests prüfen jetzt diesen belegten
Status. Aktuelle Referenzvalidatoren werden nicht gelockert; fehlende Dateien
werden nicht als vorhanden gewertet oder wiederhergestellt.

169 gezielte Offline-Fälle einschließlich 25 historischer Kartenprüfungen
bestanden am abschließenden Stand. Darin enthalten sind 32 neue Gegen-/Positivfälle. Der ursprüngliche
D01/D02-Fehler und die drei alten Kartentesterwartungen bleiben als frühere
Befunde dokumentiert; diese Fortschreibung ersetzt ihre Offen-Kennzeichnung
nur für den konkret geklärten Versions-/Prüfumfang. Der
[D01/D02-Vertrag](UNIFIED_BLUEPRINT_D01_D02_TOPOLOGY_ADJUDICATION_NORMATIVE_V1.md)
und der [Herkunftsbeleg](../evidence/D01_D02_MAP_BINDING_RECONCILIATION_2026-11-22.json)
begrenzen den PASS auf eingefrorenen Karteninhalt und aktuelle deklarierte
D01/D02-Referenz-/Authorityprüfungen. Dies ist keine heutige Gesamtsemantik-
oder Betriebsabnahme. Der Summary weist runtime_execution_proven false aus.

Sechs weitere Prüfungen bestehen für die exakt gebundene Aufnahme des korrigierten
D01/D02-Prüfers in das vorhandene Policy-Inventargate. Die ursprüngliche
Konfiguration bleibt bytegleich; nur genau der geprüfte Vorher-/Nachher-Quellhash
ist zugelassen. Eine freie Nachbindung fremder Prüfer oder anderer Policies bleibt
gesperrt. Insgesamt sind damit 175 gezielte Fälle grün.

Die zusätzliche breitere Funding-Prüfung hat einen separaten bestehenden Fehler:
test_startup_topology_reconciliation_budget_and_reviewed_rotation_owner verlangt
für den Reconciliation-Startupgate weiterhin die Bytes aus
304719c94030ff9aacdf2571e2ae56533f9e6a25. Der heutige, in dieser Änderung
unangetastete Source enthält bereits die spätere gebuchte Net-Reversal-Übergabe.
Der gleiche Fehler wurde mit dem originalen Policy-Projektor des Ausgangsstands
reproduziert. Dieser Funding-Snapshotvertrag bleibt FAILED und wird hier weder
gelockert noch durch die neuen grünen Fälle ersetzt. Er ist nicht der behobene
D01/D02-Baseline-Konflikt; eine Gesamtfreigabe wird daraus nicht abgeleitet.

BTC, betriebliche Stores, produktive Reducer und Betriebsfreigaben bleiben
unverändert. Keine Betriebs-, Erfassungs-, Paper-, Shadow-, Testnet-, Live- oder
Forschungsläufe wurden gestartet. Nur synthetische Offline-Prüfungen mit
Fixtureantworten beziehungsweise gesperrten Netzwerkconsumern wurden ausgeführt.

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

### Härtung des bereits verbundenen Messwert-Calibrationspfads — 22. November

Der direkte Messwertadapter ist bereits mit Forecast-Anheftung, expliziter
Offline-Pending-Fortsetzung, ursprünglicher Calibration, MI-Speicherung und
numerischem Readback verbunden. Target, Instrument-/Decisionbezug, Horizont,
originale Messartefakte und numerische Zulassung werden dort schon geprüft.
Diese Verbindungen und Owner wurden nicht neu aufgebaut.

Zwei vorhandene Zeitprädikate verloren jedoch Nachkommastellen jenseits von
Mikrosekunden. Acht Gegenproben reproduzierten unzulässige Übergänge an
Vorbereitung und Speicherung: Forecastentstehung 1 beziehungsweise 999
Nanosekunden nach Horizontbeginn sowie neu gebundene Messdeklarationen mit
einem finalen Close 1 beziehungsweise 999 Nanosekunden nach der Auswertung.
Solche nachgerechneten Inhaltsreferenzen beglaubigen weder ihre Zeitordnung
noch eine neue O4-Quellbeobachtung. 14 Kontrollfälle bestanden bereits vorher.

Die vorhandenen Grenzen Forecastentstehung <= Horizontbeginn und
Auswertung >= finaler Return-Close verwenden jetzt die volle ursprüngliche
Zeitpräzision. Widersprüche stoppen vor Calibrationrechnung, Researchprojektion
und MI-Store. Gleichheit und nullwertige Bruchteile bleiben zulässig. Native
Forecast-/DDO-Zulassung bleibt bei UTC mit `Z` und höchstens neun Bruchteilziffern;
der gemeinsame Zeitdecoder erweitert diesen Eingangsvertrag nicht.
Auswertungsgrenze und tatsächliche Quellenverfügbarkeit bleiben getrennt.

147 gezielte Offline-Fälle bestanden, darunter 22 neue Gegen-/Positivproben.
Zehn vor der Korrektur gesicherte vollständige Vorbereitungs-/Calibration- und
Readbackpakete bleiben bytegleich, ebenso alle zehn Dateien ihrer synthetischen
Originalstores. Die bestehenden Integrationsfälle prüfen außerdem den Weg von
der originalen Entscheidung über Pending und N_BARS bis zu Calibration und
Cold-Read. Netzwerkzugriffe waren gesperrt; keine Betriebs- oder Forschungsläufe
wurden gestartet.

Der [genaue Übergabevertrag](INTELLIGENCE_EXACT_FORECAST_MEASUREMENT_HANDOFF_V1.md#direct-measured-return-admission-hardening--22-november-2026)
grenzt den Befund ab. N finale Closes bleiben N−1 Returnintervalle; LOG_RETURN
und Returnfehler werden weder zu Kontogewinn noch zu Entscheidungsqualität.
Target, IDs/Digests, Zahlenrechnung, Persistenzowner, produktiver DDO-Reducer,
BTC und Freigaben bleiben erhalten. Weitere Signal-/Rückwege und vollständige
Systemhärtung sind damit nicht insgesamt abgenommen.

Der weiter oben dokumentierte separate Funding-Snapshotfehler wurde inzwischen
mit PR #7363 im [eigenen historischen Vertragsumfang](CURRENT_ORDERED_FUNDING_EPISODE_DEVELOPMENT_ADMISSION_V1.md#spätere-startupgate-fortschreibung-und-snapshotprüfung)
behoben; seine früheren FAILED-Belege bleiben historische Befunde.

### Originalmessung und Zeitbezug der bestehenden DP-Attribution — 22. November

Der vorhandene Phase-25-Composer verbindet typisierten Marktkontext,
Decision-/Selection-/SideState-/Konfigurationsreferenzen, N_BARS-Beobachtung
und späteres RealizedBehavior mit dem bestehenden Phase-14-Evaluationsowner.
Inspection und Replay existieren bereits. Der nachvollzogene Aufrufumfang sind
Offline-Tests und Governance-/Referenzprüfungen; ein produktiver Consumer oder
automatischer Lernrückweg wurde dadurch nicht nachgewiesen.

Am Übergang fehlte der Abgleich der Originalmessung: Zwei vollständig gültige
native Verhaltensbelege konnten denselben Kontext und Horizont tragen, aber
unterschiedliche `actual_outcome_ref` und sogar entgegengesetzte Returns.
Der Composer nahm den fremden Beleg bisher als ATTRIBUTED auf. Ebenso wenig
rechtfertigen gleiche Returnzahlen aus anderen Endpunkten oder gleiche Preise
aus anderer Provenienz die Vermischung zweier Messungen. Jetzt muss die
Messreferenz mit der ursprünglichen Evaluationsbeobachtung übereinstimmen.
Eine passend zusammengeführte neue Originalmessung bleibt zulässig.

Die beiden vorhandenen Grenzen Kontextzeit <= Entscheidungszeit und, bei
geliefertem Verhalten, Kontextzeit <= Horizontbeginn erhalten jetzt außerdem
die vollständige Quellpräzision. So wird ein erst 1 oder 999 Nanosekunden nach
der Entscheidung deklarierter Kontext nicht mehr als damals bekannt ausgegeben.
Die Gegenprobe neu versiegelter widersprüchlicher Horizontdeklarationen
beglaubigt keine neue Quellbeobachtung. Widersprüche stoppen vor Phase 14.
Gleichheit, nullwertige Bruchteile und die native UTC-Z-Syntax bleiben erhalten.
Ein zeitlich gültiger vollständiger Horizont ohne Verhaltensbeleg bleibt
INSUFFICIENT; fehlende Daten werden nicht ergänzt.

Der [Phase-25-Vertrag](UNIFIED_BLUEPRINT_PHASE_25_DP_ATTRIBUTION_NORMATIVE_V1.md#original-measurement-and-exact-declared-pit-binding--22-november-2026)
grenzt den Befund ab. Einheiten, LOG_RETURN, Preisweg-Excursion,
Volatilitätsverfahren und explizit ungeklärte klassische MFE/MAE-/Regimefelder
bleiben erhalten. Die Attribution vergibt keine Trading-, Apply- oder
Betriebsfreigabe und ersetzt kein Urteil über Regeltreue oder Kontogewinn.
Der Inspector belegt ohne Originalrequest nur seine bestehenden Inhalts- und
Referenzprüfungen; historische Belege werden nicht nachträglich zeitlich zertifiziert.
BTC, produktive Reducer und Handelsowner bleiben unverändert. Keine Betriebs-
oder Forschungsläufe wurden gestartet; weitere Ketten und Gesamtsemantik bleiben
gesondert zu prüfen.

Für diesen Phase-25-Abschnitt bestehen 101 gezielte Offline-Fälle: 31 neue
Gegen-/Positivproben und 70 vorhandene Attribution-/Verhaltens-/Zeit-/Governancefälle.
Der Ausgangsabgleich reproduzierte neun fälschliche ATTRIBUTED-Resultate und vier
INSUFFICIENT-Resultate für widersprüchliche Zukunftskontexte, die als REJECTED
auszugeben sind; 18 Kontrollen bestanden bereits. Vierzehn vollständige originale
Request-/Result-/Inspector-/Replaypakete bleiben bytegleich. Diese Eingriffskontrolle
belegt die begrenzte Übergabe und keine allgemeine Quellen- oder Systemabnahme.

### Phase-14-Attribution vor LearningState und Replay — 22. November

Der optionale Lernadapter ist bereits mit dem ursprünglichen DDO-Ingest und
dessen dauerhaftem Ledger verbunden. Der Originalconsumer prüft unter anderem
typisierte Records, Provenienz, tatsächlich gespeicherte Inhalte,
Konfigurationspools und idempotente Fortsetzung. Dieser Anschluss wurde nicht
neu aufgebaut. Seine auffindbaren Aufrufer sind Offline-Tests; ein produktiver
Host oder automatischer Lernauftrag ist dadurch nicht nachgewiesen.

Die Bindung des konkreten Attributionsbelegs an das übergebene Auswertungspaket
fehlte jedoch. Ein anderer gültiger nativer ETH-Messbeleg konnte bei gleichen
Decision- und Auswertungs-IDs einen anderen Outcome, entgegengesetzten Return
oder andere Messprovenienz tragen. War dieses andere Paket im Ledger gespeichert,
nahm der Originalconsumer es unter dem fremden Attributionsmantel auf.
Auch fehlender beziehungsweise widersprüchlicher Beleginhalt und ein anderer
gespeicherter Entscheidungsinhalt mit derselben ID stoppten den Adapter nicht.

Jetzt müssen Beleg-/Resultdigest, vorhandene Evidence-only-Grenzen, drei
Originalrecords, Entscheidungsbezug, ursprünglicher Outcome und Horizont sowie
der unveränderte Phase-14-Fingerprint und seine abgeleitete ID zusammenpassen.
Der volle Entscheidungsinhalt, Instrument- und Konfigurationsbezug werden am
Originalrecord des Ledgers gebunden. Widersprüche stoppen vor dem Lernconsumer
und vor jedem Append. Der bestehende Ingest behält Prüfung und Speicherung
seiner Originalrecords; der produktive Reducer bleibt unverändert.

Der Replayvergleich prüft jetzt den vollständig neu zusammengesetzten Inhalt
einschließlich Auswertung, MI-Referenzquery und Gründen. Gleiche gespeicherte
IDs und Digests genügen nicht. JSON-Roundtrips bleiben zulässig. Replay ohne
Ledger bestätigt keine eigenständige historische Quellenauthentizität.
Für die bestehende Digestprüfung wird die ursprüngliche Reihenfolge des inneren
Horizontobjekts nach sortierter JSON-Serialisierung wiederhergestellt; Werte
und Digestverfahren bleiben unverändert. Die erste Härtungsfassung wies drei
gültige JSON-Fälle ab; diese Zwischenregression ist reproduziert und behoben.

Der [Phase-14-Vertrag](UNIFIED_BLUEPRINT_PHASE_14_DECISION_ATTRIBUTION_NORMATIVE_V1.md#original-attribution-at-the-learning-handoff--22-november-2026)
begrenzt die Aussage. 103 gezielte Offline-Fälle bestehen, darunter 27 neue
Gegen-/Positivproben. Der korrigierte Ausgangsabgleich reproduzierte 13 falsche
Lernzulassungen und sechs falsche Replays; acht Kontrollen bestanden bereits.
Sechs vollständige Originalpakete und sechs synthetische Ledgerdateien bleiben
bytegleich. Netzwerkzugriffe waren gesperrt. Opaque Scorelabels, LOG_RETURN,
getrennte Fingerprintverfahren und alle ursprünglichen Rechen-/Speicherowner
bleiben erhalten. Daraus folgen weder Kontogewinn noch Modelltraining,
Entscheidungsqualität, Applyfreigabe oder Gesamtbetriebsbereitschaft.
BTC bleibt unverändert; keine Betriebs- oder Forschungsläufe wurden gestartet.

Die Quellenadmission bindet ausschließlich die konkrete ursprüngliche und neue
Governance-Datei über das bestehende Paar exakter Quellhashes. Sechs zusätzliche
Gegen-/Erhaltungsproben prüfen diese Aufnahme ohne neue Betriebsautorität.
Die veraltete Reviewed-Policy-Mengenerwartung ließ schon am Ausgangsstand den
bereits zugelassenen D01/D02-Prüfer aus; sie wird auf die tatsächlich bestehenden
exakten Zulassungen nachgeführt. Eingefrorene Policy-Inventare und Authority-
Konstanten bleiben erhalten; ein bloß nachgeführter Hash ersetzt keine Zulassung.

### Optionale MI-Zuordnung und originale Messreferenz — 22. November

Die vorhandene Abfrage erhält Forecast, Attribution und Kalibrierung bereits
aus Offline-Orchestrator und Phase 14. Forecast und Attribution wurden einzeln
validiert; Kalibrierung und ihre Querbezüge blieben ungeprüft. Widersprüchliche
Decision-/Auswahlsreferenzen konnten einander überschreiben. Ein gültiger
Kalibrierungsbeleg eines anderen Forecasts, Horizonttyps oder einer anderen
Messung konnte unter der gemeinsamen Query erscheinen.

Jetzt nutzt die Query den bestehenden Kalibrierungsvalidator und vergleicht
vorhandene Entscheidungs- und Auswahlreferenzen sowie MI-Domäne, Forecast-ID,
n_bars, Bar-Spezifikation und Forecasttyp. Phase 14 übergibt seine bereits
vorhandene Original-Outcome-Referenz; eine Kalibrierung mit anderer Messreferenz
stoppt vor Veröffentlichung des Attributionsresultats. Auch gleiche Forecasts,
Horizonte und neu berechnete Digests ersetzen diese Bindung nicht. Die bisherige
exakte Quellenadmission wird nur auf diesen konkreten Nachfolger fortgeschrieben.

Fehlende optionale Angaben bleiben fehlend. Ein früherer nativer
NOT_EVALUABLE-Beleg ohne Outcome wird auch neben einer späteren tatsächlichen
Messung nicht ergänzt. Queryfehler sind Validierungsausnahmen; es wird kein
erfolgreicher oder künstlicher REJECTED-Beleg daraus gebaut. Der ursprüngliche
Lernadapter, vollständige Replayvergleich und produktive Reducer bleiben erhalten.

Der [MI-Query-Vertrag](MARKET_INTELLIGENCE_FORECAST_CALIBRATION_OFFLINE_STACK_NORMATIVE_V1.md#optional-decision-attribution-query-binding--2026-11-22)
begrenzt die Aussage: 21 falsche Ausgaben wurden am Original reproduziert,
darunter fünf über den tatsächlichen Phase-14-Aufrufer; 14 Kontrollen bestanden
bereits. 35 neue Gegen-/Positivproben prüfen die Grenze. Dreizehn vollständige
Originalpakete und zwei synthetische Ledgerdateien bleiben bytegleich.
Auswahlreceipts bleiben von Marktinstrument-IDs getrennt; Kenntniszeit und
tatsächlicher damaliger Forecastverbrauch werden nicht aus Referenzen abgeleitet.
Ohne gelieferte Original-Outcome-Referenz kann die Query keine eigenständige
Messquellenbindung bestätigen. Die bestehenden Forecast-Digests schließen die
optionalen Decision-/Auswahlfelder weiterhin nicht ein. Rechenmethoden und
Methodenlabels werden nicht neu bewertet oder zu Lernqualität, Kontogewinn oder
Kausaleffekt umgedeutet. Produktiver Automatikbetrieb bleibt gesondert zu prüfen.
BTC, betriebliche Originalstores, Finanzregeln, Handelsowner und Freigaben bleiben
unverändert; keine Betriebs- oder Forschungsläufe wurden gestartet.

### Gemeinsamer Nachweis der abgeschlossenen Ketten — 22. November

Auf Franks erneute Vorgabe wurden alle bisher in diesem Arbeitsstrang
abgeschlossenen Abschnitte gemeinsam in die Offline-Vertragsprüfung einbezogen.
Der konkrete Herkunftsumfang sind PR #7337 bis #7366: 30 Lieferpakete mit 53
verschiedenen geänderten Testdateien. Ein Paket betrifft nur einen bestehenden
Harness-Bezug und begründet keine zusätzliche Signal- oder Betriebsautorität.
Die Auswahl wurde aus den tatsächlichen Git-Änderungen dieser Revisionen
hergeleitet; historische Fertigmeldungen wurden nicht als heutiger PASS übernommen.

233 aktuelle Owner-/Nachbarfälle einschließlich 35 neuer Query-Gegen-/Positivfälle
und 966 ergänzende Fälle aus den übrigen 49 Testdateien bestanden vollständig,
ohne Fehler oder Skip. Die beiden Mengen sind disjunkt; bereits abgeschlossene
PASS-Fälle wurden nicht erneut nur zur Nachweiserzeugung gestartet. Der ergänzende
Block verwendete ausschließlich Fixtureantworten und temporäre Teststores,
eine Python-Netzwerksperre und eine zusätzliche Betriebssystem-Netzwerksperre,
die auch für Unterprozesse gilt. Die anfängliche Aufrufprotokollierung wurde
wegen ihres Aufwands unterbrochen und separat erhalten; sie zählt nicht als PASS.
Der endgültige vollständige Block ohne Zusatzprotokollierung bestand mit Exit 0.

Der gemeinsame Prüfrahmen erhält insbesondere folgende bestehende Verträge:

- [Karten und Zuordnung](../../../tests/ops/test_instrument_card_stream_v1.py):
  Slot, Instrument, Quellen-/Budgetfassung und ursprünglicher Rankingbezug
  erreichen den tatsächlichen Consumer. Kartenbewertung ersetzt keine Freigabe.
- [Paper-Entscheidung und Rücklesen](../../../tests/ops/test_zkp_lane1_paper_opening_v1.py):
  ursprüngliche Entscheidung, simulierter Fill, Buchung und spätere DDO-Evidence
  bleiben unterschiedliche, miteinander gebundene Originale.
- [Shadow und O4](../../../tests/ops/test_integrated_paper_shadow_observation_wallclock_session_execution_v1.py):
  Modellkosten und kontrafaktischer Preisverlauf werden nicht zu Kontogewinn;
  der spätere Messbeleg bleibt am ursprünglichen Entscheidungsbezug.
- [Lernaufnahme und M4](../../../tests/experiments/test_canonical_optimization_universe_mi_enriched_m4_intake_v1.py):
  MI und DDO bleiben eigene Evidenztypen; Inhalt, Zuordnung und ursprüngliche
  Entscheidung werden vor dem Verbrauch geprüft.
- [Meta und Folgezyklus](../../../tests/experiments/test_canonical_deterministic_multi_cycle_offline_replay_v1.py):
  vollständige Rückgaben, Knowledge-/Record-Zeit und Forschungszweck bleiben
  gebunden; Research, Proposal, Authorization und Apply sind getrennte Grenzen.
- [OLS und Originalzeiten](../../../tests/learning/test_market_ols_exact_clock_admission_v1.py):
  Kenntnis-/Verfügbarkeitszeit, Forecastentstehung und Messschluss behalten ihre
  jeweilige Bedeutung und vollständige ursprüngliche Präzision.
- [Capture](../../../tests/ops/test_recorded_measurement_capture_exact_clock_v1.py)
  und [Folgeforschung](../../../tests/ops/test_representation_follow_up_clock_binding_v1.py):
  Aufnahme, Originalquellen, Antwortzeiten, Replay und Wiederaufnahme behalten
  ihre zuständigen Owner und expliziten Nichtauswertungs-/Sperrzustände.

Einheiten und Bedeutung bleiben ebenfalls begrenzt: Mark, Index und Last sind
eigene Quellen; USD, USDC, Basisassetmengen und native Kontrakte sind keine
austauschbaren Zahlen. N finale Closes liefern N−1 Returnintervalle. LOG_RETURN,
opaque Economic-/Decision-/Safety-Labels und Kalibrierungsmethoden sind keine
automatischen Aussagen über Kontogewinn, Entscheidungsregeltreue oder Kausaleffekt.
Fehlende Werte bleiben fehlend; eine lokale Flat-Markierung oder ein Research-PASS
erteilt keine fremde Kapital-, Permit- oder Applyfreigabe.

Dieser Nachweis prüft die vorhandenen synthetischen Consumer- und Gegenverträge
aller genannten abgeschlossenen Abschnitte. Er zertifiziert weder unabhängig
die historischen Quellen-/Clockangaben noch sämtliche numerischen Methoden,
wirtschaftliche Lernqualität, natürlichen automatischen Betrieb oder physische
Crash-/Stromausfallfestigkeit. Weitere bisher offene Systemverzweigungen bleiben
offen. Neue Verbindungen wurden nur für die konkret belegte MI-Query-Lücke im
vorhergehenden Abschnitt ergänzt; bestehende Owner und Schutzgrenzen bleiben
erhalten. BTC und Betriebsfreigaben wurden nicht verändert.
