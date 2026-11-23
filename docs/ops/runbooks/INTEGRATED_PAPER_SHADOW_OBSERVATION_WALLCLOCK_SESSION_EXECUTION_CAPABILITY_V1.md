# INTEGRATED_PAPER_SHADOW_OBSERVATION_WALLCLOCK_SESSION_EXECUTION_CAPABILITY_V1

```text
status: ACTIVE
capability: INTEGRATED_PAPER_SHADOW_OBSERVATION_WALLCLOCK_SESSION_EXECUTION_CAPABILITY_V1
owner: ops.integrated_paper_shadow_observation_wallclock_session_execution_v1
authority_effect: NONE
activation_effect: NONE
runtime_effect: NONE
order_effect: NONE
economic_gate_effect: NONE
```

> **Technical wallclock capability — not productive authorization.**
> Implements fail-closed OKX-EEA public REST market-data observation with
> atomic authorization consumption, evidence, and PASS/FAIL/ABORT semantics.
> Repository defaults do **not** authorize a productive session.
> No real network was used to land this capability.
> No productive preregistration, Operator-GO, confirm token, or authorization
> artifact is created by this capability PR.

## Pipeline position

```text
… → PAPER_SHADOW_OBSERVATION_READINESS_PASS
  → OPERATOR_PAPER_SHADOW_OBSERVATION_GO
  → INTEGRATED_PAPER_SHADOW_OBSERVATION   # this capability (wallclock MD-observe)
  → INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE
  → …
```

IPSO (`INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1`) remains the
offline observation contract owner and stays non-executing by default.
This capability is the sole wallclock execution successor.

## Hard invariants

```text
orders_authorized=false
testnet_authorized=false
live_authorized=false
auto_promotion_authorized=false
credentials_authorized=false
paper_execution_authorized=false
ECONOMIC_VALIDITY_PASS=false
PROMOTION_PASS=false
network_scope=okx_eea_futures_public_md_observe_v1   # required when network_authorized
session_execution_scope=paper_shadow_observation_wallclock_v1
transport=rest_poll_v1
host=eea.okx.com
instrument=ETH-USD_UM_XPERP-310404
max_session_duration_seconds=21600
execution_class=ANALYTICAL_SIMULATION_NOT_PAPER_EXECUTION
```

## Authorization

Requires a verified bundle from
`PAPER_SHADOW_OBSERVATION_OPERATOR_GO_AND_SESSION_PREREGISTRATION_CAPABILITY_V1`
with exact network and session-execution scopes.
GO alone does not start a session.
Consumption is atomic and happens before the first network byte.
Consumed bundles are single-use; start failure after consumption is ABORT.

## Transport

- REST polling only (WebSocket out of scope)
- Host: `https://eea.okx.com`
- GET only; public paths allowlisted
- No credentials, no private endpoints, no orders

## Observation semantics

Reuses IPSO / shadow-no-order / Master-V2 decision→risk→safety composition and
analytical portfolio economics labeled
`ANALYTICAL_SIMULATION_NOT_PAPER_EXECUTION`.
This is not Paper Execution and not venue fills.

## CLI

```bash
python scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py preflight
python scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py verify-evidence --evidence-root <path>
python scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py run ...
```

`preflight`, `verify-evidence` and `measure-shadow-outcome` are offline.
`run` delegates to the successor productive path
`INTEGRATED_PAPER_SHADOW_PRODUCTIVE_AUTHORIZATION_ISSUANCE_AND_REAL_NETWORK_EXECUTION_CAPABILITY_V1`
(verified non-fixture authorization required; real network additionally needs
`PEAK_TRADE_PSO_WALLCLOCK_ALLOW_REAL_NETWORK=1`, which is never sufficient alone).
Library tests continue to inject fake transport and fake clocks.

## Datenprüfung für den Paper-/Shadow-Pilot

Der Shadow-Preflight prüft den lokalen Startpfad. Die Sitzung liest den
öffentlichen OKX-EEA-Markpreis für `ETH-USD_UM_XPERP-310404`. Der
Volatilitätsproducer benötigt 61 aufeinanderfolgende finalisierte
Minuten-Markpreise. Die reguläre I17-Qualifikation bindet 7.200 Sekunden in
Preregistrierung, Operator-GO und Wallclock-V2-Autorisierung. Der optionale
verlängerte Lauf bindet 21.600 Sekunden. Vor der einmaligen Nutzung der
Autorisierung prüft der Gatekeeper die genehmigte Dauer. Die Marktdatenprüfung
weist die 61 finalisierten Werte für den konkreten Lauf nach.

```bash
./scripts/pt scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py preflight
./scripts/pt scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py \
  verify-evidence --evidence-root /absolute/shadow-evidence --require-typed-ddo
```

Die zweite Prüfung liest das versiegelte Sitzungsledger mit dem DDO-Owner
und dem Double-Play-Consumer. Sie verlangt einen vollständigen Abschluss mit
`PASS`, mindestens einen Zyklus mit typisierter Volatilität und für jeden
solchen Zyklus das vollständige Entscheidungsbündel mit exakt zugeordneter
Marktsequenz, Preisreferenz und Entscheidungszeit. Ein Zyklus ohne eigenen
Capture-Beleg bleibt im Nenner. Ein versiegelter Abbruch kann im allgemeinen
Archivcheck lesbar sein und erfüllt die strenge DDO-Prüfung nicht. Das JSON-Feld
`ddo_readback` meldet Schreibfehler, unpassende Zuordnungen und die Zahl der
vollständigen Bündel. Marktbeobachtung und analytische Fills verwenden
einen Markpreis und modellierte Zusatzinputs. Die Wirtschaftlichkeitsprüfung
braucht separat gebundene Originalquellen für Quotes, Tiefe, Kosten und
Funding.

Der Bundle-Prüfer verlangt Prüfsummeneinträge für Marktsequenz, Zyklusledger,
Zähler, Abschlussurteil und inneres Integritätsmanifest. Die beiden
Manifestlisten müssen für die enthaltenen Dateien übereinstimmen.

Das Zyklusledger bindet die zugehörige Marktsequenz, Venue-Zeit, den
tatsächlichen Markempfang und die Zeit nach Empfang aller Zyklusinputs.
Die zugehörige Double-Play-Aufzeichnung erhält den Zykluszeitpunkt in UTC
mit Subsekunden. Diese Zeit beschreibt die für die Entscheidung verwendete
Host-Uhr; sie ist keine separat gemessene Dauer der Core-Berechnung.
O4 vergleicht UTC-Zeitpunkte einschließlich ihrer Nachkommastellen.

Lehnt der Core einen Zyklus wegen nicht positiver Volatilität bei der
Geometrieinitialisierung ab, schließt I17 den Transport, gibt das Sitzungsschloss
frei und versiegelt die bis dahin vorhandene Aufzeichnung mit `ABORT`.
Der abgelehnte Zyklus wird nicht als abgeschlossene Entscheidung gezählt.

Die optionale O7-Anbindung an das Dashboard (`PEAK_TRADE_O7_LIVE_OHLCV_BRIDGE_ENABLED=1`)
braucht einen ausdrücklich gesetzten absoluten `PEAK_TRADE_STATE_ROOT`.
Vorprüfung und Laufzeitstart weisen einen fehlenden oder relativen Pfad ab,
bevor der Start die einmalige Autorisierung verbraucht. Ohne O7 benötigt die
DDO-Aufzeichnung nur das Evidenzverzeichnis der Shadow-Sitzung.

Paper verwendet eigene Evidenz- und Zustandswurzeln. Die lokalen
Roundtrip-Tests verwenden den Original-Core und simuliertes Accounting
mit einem DDO-Ledger je Slot. Der vorhandene Scheduler-Adapter mit
`high_vol_no_trade` deckt die Start- und Beobachtungsstrecke ab. Für den
Pilot mit simulierten Fills braucht es eine konkrete Bindung des
Paper-Starts an den Core, das Accounting und die vorgesehenen Datenprofile.
Der [Datenvertrag](../specs/CURRENT_PAPER_SHADOW_DATA_ROUTING_SEMANTICS_V1.md)
führt die zuständigen Eingangsconsumer und ihre Zeit- und Quellenbezüge.

Der [Paper-Vorcheck](../../../scripts/ops/prepare_bounded_paper_start_v1.py)
prüft am expliziten As-of die gespeicherten Facts durch die Ranking- und
C1-Consumer sowie die virtuelle Startbilanz im originalen Accounting.
Er öffnet keine Sitzung und meldet die offenen Startbindungen.

```bash
./scripts/pt scripts/ops/prepare_bounded_paper_start_v1.py \
  --data-profile /absolute/paper-data-profile.json \
  --virtual-accounting /absolute/paper-virtual-accounting.json \
  --run-root /absolute/new-paper-run \
  --native-instrument "$paper_native_instrument" --as-of-ms "$paper_as_of_ms"
```

Das Datenprofil enthält die fünf Zweckschlüssel und je Zweck die
serialisierte Ausgabe von `PurposeBoundPublicFactSourceV1.profile_v1()`.
Die Accounting-Datei enthält `initial_equity` und `contract` mit den
Feldern aus `ContractMetadataV1.to_dict()`. Menge, Multiplikator,
Tickgröße, Währung und Marginsätze stammen aus dem gewählten
Simulationsprofil. Ein erfolgreicher Input-Vorcheck ist ein Teilbefund.
Die Ausgabe `launch_blockers` führt die noch fehlende Hostbindung und
die Prüfung von Core-Marktinputs und Kosten auf.

### ZKP-Paper-Einstieg auf LANE_1

Der [ZKP-Startpfad](../../../scripts/ops/run_zkp_lane1_paper_v1.py) liest
die öffentlichen OKX-EEA-Quellen für `ZKP-USD_UM_XPERP-310905`.
`preflight` prüft mit optionalem `--evidence-root` die Eingaben.

```bash
./scripts/pt scripts/ops/run_zkp_lane1_paper_v1.py preflight
```

Ein ausdrücklicher Aufruf mit `run` und einem neuen absoluten `--run-root`
legt den Paper-Zustand separat an. Das Zeitfenster für den Slot
beträgt standardmäßig 7.200 Sekunden. Der V2-Mark-Takt verbindet den
originalen Master-V2-Einstieg mit den finalisierten G17- und C1-Fenstern.
Die kanonische Mengenrechnung verwendet 25 virtuelle USDC und den
beobachteten USDC/USD-Index. Die Paper-Prüfung verlangt die volle vorgesehene
Menge auf beiden Orderbuchseiten und bewertet Spread, ADV-Anteil und
Slippage. [Paper-Liquiditätsprofil](../../../config/risk_liquidity_gate_paper.toml)
und [Slippage-Cap](../../../config/risk/slippage.toml) liefern die Limits.
Das ADV stammt aus 30 fertigen
UTC-Tageskerzen in USD. Der Fillpreis ergibt sich aus dem Orderbuch mit
nachteiliger Tick-Rundung. Die modellierte Taker-Gebühr beträgt 0,05 Prozent.
Die erwarteten Ausstiegskosten und die nächste Funding-Reserve gehen vor
der Buchung in die Budgetprüfung ein.

Der Erstfill speichert Buchung, offene Position und C1-Cursor. Die
[Fortsetzung](../../../src/ops/bounded_peaktrade_system_composition_v1/zkp_paper_continuation_v1.py)
führt den besetzten Slot mit aktuellen Marks und dem ursprünglichen Master V2
weiter. Ein bestätigter L10-Gegenwechsel am gebundenen Instrument prüft die
ausführbare Nettomenge im Orderbuch und bucht genau einen simulierten Fill
einschließlich Gebühr und Slippage. Dieselbe Cursoradresse führt die nächste
Positionsepisode. Das Verzeichnis `reversals` enthält die Buchungen mit Entscheidungs- und
Cursorbezug.

`resume` mit dem ursprünglichen `--run-root` nimmt einen unterbrochenen,
bereits besetzten Slot innerhalb seines ursprünglichen Zeitfensters wieder auf.
Ein gebuchter Fill wird aus dem Journal gelesen. Bei Fensterende oder `STOP`
bleibt die letzte Position zur Auswertung erhalten. Ein anderer Exit als der
L10-Gegenwechsel hält die Fortsetzung an.

Ab dem Funding-Zeitpunkt wartet der besetzte Slot auf die bestätigte Rate
`realizedRate` aus der öffentlichen OKX-Funding-Historie und die finale
Mark-Minutenkerze unmittelbar vor dem Settlement. Deren Schlusskurs dient
als Paper-Referenzpreis. Die offene Anzahl Kontrakte, die Kontraktgröße,
der Referenzpreis und die bestätigte Rate bestimmen den virtuellen USD-Betrag.
Bei positiver Rate wird Long belastet und Short gutgeschrieben. Das
Journal `funding` bindet die Buchung an Settlement-Zeit, Positionsepisode
und Quellenprüfsummen. Nach dem Readback kann Double Play am selben Cursor
weiterlaufen. Der Paper-Pfad verwendet ausschließlich öffentliche GETs und
simuliertes Accounting.

Der Paper-Starter verwendet für neue UP-Sitzungen `UP-USD_UM_XPERP-310919` auf `LANE_5`
und `IRYS-USD_UM_XPERP-310530` auf `LANE_4`. `--slot-config` verlangt die
exakte Kombination aus Lane, kanonischer und nativer Instrument-ID sowie
`surface = PAPER_EXCHANGE` und `authority = NONE`. Öffnung, Nettobuchung und
Wiederanlauf verwenden den Zustand der jeweiligen Lane. Der Liquiditätscheck
bleibt an die vorgesehenen Kontrakte und den aktuellen Markt gebunden.

Am Ende des Paper-Fensters oder beim kontrollierten Stopp versiegelt der
Starter den Buchungsverlauf mit `MANIFEST.sha256`, sofern ein bestätigter
Nettofill eine Folgeepisode eröffnet hat. Die Offline-GVEF-Kampagne liest den Originalordner unter
`paper_runs&#47;<session_id>`. Sie prüft Lane, Sitzung, beide Instrument-IDs,
Entscheidungs- und Fillzeiten sowie Entscheidung, Funding und Accounting vor
dem Schreiben des DDO-Lernbelegs. Der Richtungswechsel liefert genau einen
gemeinsamen Fill mit anteiligen Gebühren, Notional und Slippage für beide
Positionsepisoden. Nur die durch einen bestätigten Nettofill abgeschlossene
Episode wird ausgewertet. Der noch offene Nachfolger bleibt im Originalstore.
Der Research-Schritt braucht weiterhin eigene instrumentgebundene Eingaben.

### Eigenständiger Shadow-Begleittest für das Selbstlernen

Der lokale Entwicklungsstand vom 19. November 2026 ergänzt die kontinuierliche
Kartenprojektion für ZKP/UP/IRYS-Paper und SOPH-Shadow. Der
[Semantik- und Anschlussbefund](../specs/CURRENT_PAPER_SHADOW_DATA_ROUTING_SEMANTICS_V1.md)
beschreibt ihre Originalconsumer und Grenzen. Diese Ergänzung ist keine
Startfreigabe; im Rahmen dieser Änderung wurden nur Offline-Prüfungen ausgeführt.

Paper schreibt pro ursprünglichem Lauf unter `instrument-cards&#47;<lane>`;
Neue SOPH-Shadow-Sitzungen schreiben separat neben ihrem Evidenceverzeichnis unter
`instrument-card-stream&#47;<session>&#47;instrument-cards&#47;LANE_2`. `latest.json`
ist eine Inhaltsdigest-gesicherte Ansicht. Die Unterordner `versions` und
`sources` behalten die Fassungen, tatsächlichen Master-V2-Eingaben und
Originalantworten. Datenabriss und Sitzungsende sperren die Ansicht.
Ein Verbraucher muss `read_instrument_card_v1` mit der aktuellen
Entscheidungs-/Slotbindung, gegebenenfalls der Original-Rankingbindung und
seiner Verbrauchszeit verwenden. Ein direkter Dateiread erteilt keine
Frische-, Budget- oder Einstiegszulassung.

Die vorhandenen Starter akzeptieren optional
`--card-cap24-evidence-root` für eine bereits erzeugte Cap24-Auswahl.
Paper bewahrt diese Kartenbindung im Originalordner für `resume` auf;
ein Austausch wird abgewiesen. Ohne Originalauswahl ist die Karte ausdrücklich
eine isolierte Testbindung. Der Anschluss wählt und rotiert keine Instrumente.
SOPH liest sein virtuelles Testkapital aus dem ursprünglichen analytischen
Portfolio und der bestehenden Slotbudgetpolicy. Kapitalbasis und freier
Neueinstiegsbetrag bleiben getrennt. Analytische Shadowmengen werden als
Basisassetmengen behandelt und für die zusätzliche Prüfung ausdrücklich in
native Kontrakte umgerechnet. Private Kapital-/Hold-/Fillowner bleiben davon
unberührt; der Shadowpfad bleibt analytische Simulation.

Für den späteren gemeinsamen Testblock läuft der bestehende I17-Shadow-Test
auf dem ETH-Kontrakt `ETH-USD_UM_XPERP-310404` in einer eigenen Sitzung und
mit eigenen Evidenz- und Lernwurzeln. Das Ziel ist ein dauerhaft zurückgelesener
Lernbeleg aus einer im Begleittest tatsächlich erfassten Shadow-Entscheidung.
Die Beobachtungsphase kann parallel zu ZKP-Paper laufen. Die Messung und der
Lernbeleg folgen erst, wenn beide zum Entscheidungsfenster passenden O4-Bars
final und verfügbar sind. ZKP-Funding fließt in die Paper-Buchhaltung;
I17 liefert dem Selbstlernen einen kontrafaktischen Preisverlauf.

Der [I17-Begleiter](../../../scripts/ops/run_i17_shadow_learning_companion_v1.py)
verwendet beim späteren ausdrücklichen Start die reguläre I17-Preregistration,
den Operator-GO und die vorhandene Startprüfung. Shadow-Evidenzverzeichnis,
Begleiterverzeichnis und ZKP-Paper-State gehören zu getrennten Sitzungen.
Die O4-Instrumentbindung stammt aus einem archivierten öffentlichen
Instrumentenbeleg für denselben Kontrakt. Sie wird vor dem Start geprüft
und nach Abschluss mit der Instrumentbindung aus dem Shadow-Archiv abgeglichen.
Neue SOPH-Shadow-Sitzungen binden `SOPH-USD_UM_XPERP-310912` an `LANE_2`.
Für den zugewiesenen Erstkauf liest der Begleiter mit
`--card-lane-sources TOPOLOGY RANKING UNIVERSE` die N5-Veröffentlichung
und den Cap24-Beleg dieser Lane. Beim Rücklesen älterer Sitzungen gelten
die damals aufgezeichneten Bindungen für SOPH in Slot 5 und UP in Slot 2.
Preregistrierung und spätere Freigabe binden genau diesen Kontrakt. Die
öffentlichen Abrufe und der DDO-Lernbeleg verwenden dieselbe Instrumentbindung.
Der Slot-Empfänger liest die versiegelte Abschlussdatei und prüft den Lernbeleg
erneut. Die zweistündige O4-Messung beginnt an der zur Entscheidung gehörenden
Stundengrenze.

```bash
./scripts/pt -m scripts.ops.run_i17_shadow_learning_companion_v1 run \
  --preregistration "$i17_prereg" --operator-go "$i17_go" \
  --authorization-artifact "$i17_auth" --confirm-token-file "$i17_token_file" \
  --evidence-root "$i17_shadow_root" --fingerprint-ledger "$i17_fingerprint_ledger" \
  --expected-repository-sha "$repository_sha" \
  --companion-root "$i17_companion_root" --o4-instrument-binding "$i17_o4_binding"
```

Beim späteren Start gilt das bestehende Opt-in
`PEAK_TRADE_PSO_WALLCLOCK_ALLOW_REAL_NETWORK=1`. Der Begleiter liest nach
Abschluss das versiegelte Shadow-Archiv und nimmt die erste vollständig
belegte Entscheidung mit typisierter Volatilität. Der O4-Abruf wartet bis
zum Ende der zweiten zugehörigen Stundenkerze und wiederholt vorläufige
oder lückenhafte Antworten im Fenster von zehn Minuten nach Kerzenschluss.
Wenn die finalen Daten vorliegen, schreibt der bestehende DDO-Eingang den
Lernzustand. `completion.json` wird erst nach dessen Readback veröffentlicht.
`resume` mit demselben `--companion-root` setzt bei einem bereits versiegelten
Shadow-Archiv die Übergabe fort. Es liest einen bereits erfassten O4-Beleg
erneut und kann eine fehlende Abschlussbestätigung nachholen.

Für die spätere [DDO-/GVEF-Auswertung](../specs/OFFLINE_DDO_NATIVE_RESEARCH_CYCLE_V1.md)
müssen die vollständigen Entscheidungsbelege erhalten bleiben. Die
Outcome-Messung benötigt mindestens zwei lückenlose finalisierte
O4-Stundenbars nach dem eingefrorenen Startzeitpunkt des Messfensters,
passend zu Venue und Instrument. Für eine ausdrücklich ausgewählte,
typisierte I17-Double-Play-Entscheidung kann der Offline-Befehl
beide Originalarchive zusammen lesen:

```bash
./scripts/pt scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py \
  measure-shadow-outcome --evidence-root /absolute/shadow-evidence \
  --decision-event-ref "$shadow_decision_event_ref" --o4-mark-archive /absolute/recorded \
  --n-bars 2 --evaluated-at-utc "$evaluation_utc" --max-end-age-seconds "$end_age_limit_seconds"
```

Die Entscheidungsreferenz ist die Original-ID aus dem typisierten DDO-Zyklus.
Das Fenster beginnt an der ersten vollen UTC-Stunde auf oder nach dem
Entscheidungszeitpunkt. Die Kursmessung reicht vom Schluss der ersten bis
zum Schluss der letzten angeforderten Stundenkerze. Das Archiv muss zum
angegebenen Auswertungszeitpunkt nachweislich verfügbar sein und dieselbe
Instrumentbindung führen. Der Befehl gibt einen prüfsummengebundenen
Lesebeleg aus. Er verändert weder Archiv noch DDO-Ledger. Die Messung ist
ein späterer Markpreis-Logreturn ohne Fill, ohne Kontorendite und ohne
Lern- oder Freigabewirkung. Die lokalen Prüfsummen sind keine unabhängige
Bestätigung der Marktdaten durch die Börse.

Mit der Option `--outcome-receipt-out` speichert der
Messbefehl den Beleg zusätzlich in einem bestehenden Ausgabeverzeichnis
außerhalb der beiden Quellarchive. Eine identische Wiederholung akzeptiert
die bereits gespeicherten Bytes. Abweichender Inhalt am selben Ziel führt
zum Abbruch.

Für den späteren Readback genügt der Beleg zusammen mit den zwei
Originalarchiven. Der Befehl übernimmt die Messparameter aus dem Beleg,
prüft beide Archive erneut und vergleicht die Prüfsumme der neu berechneten
Messung mit der gespeicherten.

```bash
./scripts/pt scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py \
  measure-shadow-outcome --evidence-root /absolute/shadow-evidence \
  --o4-mark-archive /absolute/recorded \
  --verify-outcome-receipt /absolute/auswertung/shadow-o4.json
```

Der [I17-Follow-up](../../../scripts/ops/run_offline_ddo_learning_follow_up_v1.py)
prüft mit `complete-shadow` beide Originalarchive und den Messbeleg erneut.
Er schreibt für die Shadow-Entscheidung einen eigenen DDO-Lernbeleg als
`SHADOW_COUNTERFACTUAL`. Zur Abnahme gehören der Readback aus dem eigenen
Lernstore und der Abgleich von ursprünglicher Decision-ID, Instrument,
Messzeitfenster und Belegdigest. Die Test-Fixture trägt
`TEST_ONLY_SYNTHETIC`. Für die spätere Abnahme zählen die gemessenen
Originaldaten aus der Begleitsitzung.

## Explicit non-goals (this capability PR #5592)

- Productive preregistration / Operator-GO / confirm token issuance
  (owned by successor productive-issuance capability)
- Automatic session grant on merge
- Paper / Testnet / Live orders
- Economic Validity PASS
- Auto-promotion
- Dashboard authority
- Zero-Order as substitute

## Successor note

PR #5592 alone was not real-startfähig (`REAL_NETWORK_CLI_PATH_NOT_ENABLED_IN_THIS_PR`,
no productive issuance, no default real HTTP fetcher). The successor capability
supplies productive issuance and the real public-MD transport while keeping
Orders/Paper/Testnet/Live/credentials forbidden.

Decision→economics binding (non-HOLD, persistent portfolio, reconstruction
verifier) is owned by
`WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_V1`
(enabled by default in wallclock runtime config).
