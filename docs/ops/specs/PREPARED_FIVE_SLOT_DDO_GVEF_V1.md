---
docs_token: DOCS_TOKEN_PREPARED_FIVE_SLOT_DDO_GVEF_V1
status: active
runtime_authorization_effect: NONE
---

# Gemeinsame Fünferlauf-Vorbereitung mit DDO und GVEF

Der Offlineaufruf `./scripts/pt -m scripts.ops.prepared_five_slot_run_v1 --preparation-folder <Ordner>` prüft die vorhandenen Originalzuweisungen, fünf Producer, isolierte Sitzungen, Forschungsdaten und den unverändert versiegelten BTC-Host. Er erzeugt JSON auf stdout. T0 bleibt ungebunden; kein Schlüsselbund-, Konto-, Netzwerk- oder Orderzugriff und kein angelegtes BTC-Laufziel gehören zur Vorbereitung. Ein schmutziger Checkout wird als `SOURCE_INTEGRATION_PENDING` ausgewiesen.

Die feste Folge ist UP-USDT-SWAP Shadow ab Minute 0 für 120 Minuten, UP-USD_UM_XPERP-310919 Paper ab Minute 20 für 120 Minuten, BTC-USD_UM_XPERP-310328 TESTNET ab Minute 40 für 60 Minuten, PIEVERSE-USDT-SWAP Shadow ab Minute 60 für 120 Minuten und OL-USD_UM_XPERP-310912 Paper ab Minute 80 für 60 Minuten. Die Versätze sind früheste Aufrufzeiten. Fehlende gültige Einstiegszulassung führt zum Warten bis zur ausdrücklich angegebenen Aufnahmefrist; weder Ersatzinstrument noch PENDING-Zuweisung entstehen. Verzögerungen verschieben den tatsächlichen Sitzungsbeginn und werden nicht als nachgewiesene gemeinsame Belegung ausgegeben.

## Später frisch zu erzeugende Eingänge

Nach einer gesonderten ausdrücklichen Startfreigabe liefern diese Aufrufe die Originale für jeden Einstieg:

1. `scripts.ops.capture_five_slot_entry_market_v1 --output-dir <neuer Quellenordner> --expected-repository-sha <freigegebener Merge>` erfasst ausschließlich öffentliche OKX-EEA-Daten. Die vollständige zulässige Kandidatenmenge erreicht den ursprünglichen Cap22-Produzenten; keine verkürzte Rangliste wird erfunden.
2. `scripts.ops.prepare_five_slot_entry_selections_v1 --preparation-folder <Ordner> --quellordner <Quellenordner>` erzeugt am Original-Cap23-Pfad eine Folgeauswahl für die feste ursprüngliche Slotbelegung. Historische N5-Revision und neue Produktionsrevision bleiben getrennt. Die Consumer prüfen beide Originalquellen und den vollständigen Policy-Replay. Der Konfigurationsdigest enthält die Revision und darf beim expliziten Revisionswechsel deshalb wechseln. Alte Gültigkeitsfristen werden nicht verlängert.
3. Shadow verwendet `scripts.ops.prepare_ranked_shadow_entry_v1 --slot-folder <LANE> --selection-root <Quellenordner>`. Cap24 entsteht erst am ursprünglichen Entscheidungstick aus Originalportfolio und Markpreis. Die ursprünglichen I17-Preregistration-, Operator-GO-, Token- und Autorisierungsproduzenten müssen zeitgebundene Nicht-Fixture-Eingänge ausstellen. Die deaktivierte Vorlage ist keine Freigabe. G17, Funding und aktuelle Preise bleiben Original-Runtimeinputs.
4. Paper verwendet `scripts.ops.prepare_ranked_paper_entry_v1 --slot-folder <LANE> --zulassungsordner <Quellenordner> --belegordner <eigener Generationsordner>`. Es entstehen ursprüngliche Kontoeröffnung, öffentliche USDC-Umrechnung und Cap24. USD-Markpreis und USDC-Anfangskapital werden nicht gleichgesetzt.
5. `scripts.ops.publish_five_slot_entry_v1 --plan <Plan> --lane <LANE> --slot-config <gebundenes Profil>` prüft die tatsächliche Zulassung und veröffentlicht einen Pointer. Bei BTC wird stattdessen `--operator-start <Originalstart>` geprüft. Ein neuer Pointer ersetzt nur den Pointer; die archivierten Generationen und Originale bleiben erhalten. Ein abgelaufener Pointer wird beim tatsächlichen Consumer erneut verworfen.

Der spätere gemeinsame Aufruf lautet `./scripts/pt -m scripts.ops.prepared_five_slot_run_v1 --plan <Plan> --run --start-bundle <neues Bündel>`. Das Bündel benötigt `action=START_PREPARED_FIVE_SLOT_RUN`, den exakten `plan_digest`, ein ausdrücklich gewähltes zoniertes `t0`, `expires_at_utc` und `admission_wait_until_utc`. Es wird jetzt nicht ausgestellt. Die ursprünglichen Slot-Gates bleiben zusätzlich erforderlich. Der gemeinsame Auftrag ersetzt weder BTC-Startautorisierung noch I17-Autorisierung.

## Tatsächliche Übergaben

Shadow läuft über seinen bestehenden I17-Lernbegleiter mit `--gvef-campaign`. Dieser wartet nach der ursprünglichen Entscheidung auf zwei finale Stundenbars, führt den ursprünglichen DDO-Handoff aus und übergibt dessen LearningEvidence an GVEF. Diese O4-Messfrist ist von der 120-Minuten-Beobachtungsdauer getrennt und kann einen Nachlauf erfordern.

Paper läuft über den ursprünglichen Paperdriver. Nach dessen Ende liest die gemeinsame Steuerung sein tatsächliches `window.json` und sämtliche abgeschlossenen simulierten Episoden des manifestgebundenen Archivs. Der bestehende Kampagnenconsumer führt den ursprünglichen Paper-DDO-Handoff und den Forschungs-/GVEF-Kreis aus. Noch offene Episoden werden nicht zu abgeschlossenen Trades erklärt; fehlende oder blockierte Ergebnisse bleiben offen.

BTC läuft über `scripts.ops.run_btc_demo_learning_session_v1`. Dieser ruft den unveränderten versiegelten begrenzten Host mit dem Originalstart auf. Die einmalige Anfangszuteilung bleibt 25 USDC. Der ursprüngliche Registrierungswriter bestimmt die unveränderliche 60-Minuten-Frist; höchstens 120 weitere Sekunden gehören ausschließlich zum bestätigten Abschluss. ACK, Teilfill oder Timeout bleiben vom bestätigten Abschluss getrennt.

Der neue Host erzeugt **keine** V2-`research-first-fills`-Dateien. Der lesende Adapter `scripts.ops.btc_demo_bounded_learning_source_v1` prüft stattdessen seine ursprüngliche G17/C1-Cursorkopie, Original-Budgetrevision, authentifizierten GET-Proof, genaue Fill-/Positionsanker und das ursprüngliche Positions-Episodenmanifest. Er wählt die früheste passende bestätigte Beobachtung und erhält deren Zeit und Identität. Der bestehende BTC-DDO-Consumer prüft zusätzlich ursprüngliche Policyentscheidung, Codebezug, Instrument, Zyklus, Information und Entscheidungszeit. Die Quelle ist in der Kampagne ausdrücklich `BOUNDED_HOST_ENTRY`; der ältere V2-Pfad bleibt eigenständig.

Erst nach dem Abschlussversuch des Hosts läuft dieser DDO-/GVEF-Nachlauf. Forschungsfehler dürfen keinen Closeversuch unterdrücken, eine Frist verschieben oder Kapital freigeben. Das GVEF-Quellfenster stammt aus der tatsächlichen Originalregistrierung und beträgt eine Stunde; der spätere Mess-/Forschungszeitpunkt verlängert es nicht. Ein Wiederaufruf liest dieselben Originale und verwendet bestehende Handoff-/Jobreceipts idempotent weiter.

Der BTC-Handoff bewertet den ursprünglichen bestätigten Ersteinstieg mit `IMMEDIATE_POST_EVENT`. Er ist kein Nettoergebnisnachweis aller späteren Richtungswechsel oder des gesamten Kontos. Wirtschaftliches `BLOCKED` bleibt `BLOCKED`. Auch ein bestandener Offline-Fixturelauf belegt keine tatsächliche Venueausführung, Lerngüte, Promotion oder vollständigen autonomen Fünferbetrieb. Ein offener Produzent oder Nachlauf bleibt im gemeinsamen Ergebnis offen.

## Quellen und begrenzte Verifikation

[Gemeinsame Steuerung](../../../scripts/ops/prepared_five_slot_run_v1.py), [BTC-Nachlauf](../../../scripts/ops/run_btc_demo_learning_session_v1.py), [Originalbelegadapter](../../../scripts/ops/btc_demo_bounded_learning_source_v1.py), [bestehender Kampagnenconsumer](../../../scripts/ops/run_recurrent_offline_research_v1.py) und [Offline-Verbindungstests](../../../tests/ops/test_prepared_five_slot_run_v1.py) sind Produktquellen. Der [bestehende Hostvertrag](BTC_DEMO_BOUNDED_HOST_V1.md) bleibt maßgeblich für BTC-Handel und bestätigten Abschluss. Der eingefrorene Atlasbestand und seine Freeze-Tags bleiben unverändert; die konkreten Entwicklungspfade werden getrennt gebunden.
