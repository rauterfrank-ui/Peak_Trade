---
docs_token: DOCS_TOKEN_BTC_DEMO_BOUNDED_HOST_V1
status: preparation
runtime_authorization_effect: NONE
---

# Slot 3: begrenzter ursprünglicher Demo-Host

Der [Host](../../../src/ops/btc_demo_bounded_host_v1.py) verbindet den vorhandenen
BTC-Erstkauf, die ursprünglichen authentifizierten Positionsbelege, den
fortgesetzten Core-/Scope-/SideState-Pfad und die ursprünglichen Netto-Wechsel.
Er begrenzt die Verarbeitung auf 60 Minuten ab dem einmal gespeicherten Start.
Danach folgt ausschließlich die [Abschlussbestätigung](BTC_DEMO_BOUNDED_SESSION_CLOSE_V1.md)
mit einem auf 120 Sekunden begrenzten Lese-/Abschlussfenster. Eine ungeklärte
Schlussorder behält ihren Hold und wird als unbestätigt ausgegeben.

Die [konkreten Ports](../../../src/ops/btc_demo_runtime_v1.py) konsumieren den
bisherigen Core, G17, den TESTNET-V3-Writer, private Kontraktmetadaten, native
Mengen, ursprüngliche Orderbuch-/Gebühren-/Fundingbelege und die vorhandenen
Sende-/Reconciliationownern. Ein ACK eröffnet keine lokale Position. Nach einer
Unterbrechung werden bereits gesendete Orders vor einer neuen Order
abgeglichen. Journal, Kapitalherkunft, 25 USDC Anfangszuweisung und Startfrist
werden weiterverwendet. Es erfolgt keine Neufinanzierung beim Richtungswechsel.

BTC bleibt eine ausdrücklich vom Nutzer festgelegte Demo-Instrumentbindung.
Sie behauptet keine relative Rangposition oder Cap23-Auswahl. Die Vorlage
bindet die bereits vorbereitete öffentliche Instrumentidentität per Hash;
die tatsächliche Konto-/Kontraktzulassung erfolgt an den ursprünglichen
privaten Eingangs- und Sendeprüfungen. Öffentliche USD-Notierungen werden nicht
in private USDC-Guthaben umbenannt.

Der Host verwendet den geprüften eigenen TESTNET-Budgetvertrag aus
[Revision 11](BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V11.json), eingeschränkt auf
Slot 3 und insgesamt 25 USDC. Er schaltet keinen Schutz dieses Vertrags ab.
Die zusätzliche X-Perp-Liquidationsprojektion anderer Budgetrevisionen ist
kein belegter Bestandteil dieses TESTNET-Anschlusses; eine solche Vorlage
wird vor Journalanlage abgewiesen. Das Profil der übrigen Slots wird hier
nicht verändert.

Der [begrenzte POST-Owner](../../../src/ops/btc_demo_bounded_post_owner_v1.py)
ist an genau die ausdrücklich gestartete Demo-Sitzung gebunden. Seine
signierten Einzelaufträge verwenden den bestehenden gemeinsamen Freigabestore
mit getrenntem Checkpoint. Jede Order benötigt den ursprünglichen Plan,
aktuellen Originalzustand und die vorhandene einmalige Sendebarriere.
LIVE-Freigaben werden nicht erzeugt. Der LIVE-Incidentwriter erhält keine
umetikettierten Demobelege; ungeklärte oder mengenwidrige Demo-Belege erreichen
keine neue Orderfreigabe.

Die erste bestätigte Position muss zum ursprünglichen G17-Fenster der
Erstentscheidung an die C1-Uhr übergeben werden. Der
[historische Quellenbeleg](../../../src/ops/btc_demo_entry_c1_source_v1.py)
bindet den vollständigen damaligen Cursor an seinen im Budgetwriter
gespeicherten Digest. Für diese ursprüngliche Publikation wird das damalige
G17-Fenster mit seinem Originalowner nachgeprüft. Dieser Beleg liefert keinen
aktuellen Forecast und verändert keinen Live-Checkpoint. Nach Cold-Restore
wartet der aktuelle G17-Pfad weiterhin auf einen neuen eigenständigen
finalisierten Minutenwert. Der Minutenwechsel überschreibt den Erstbezug nicht.

Eine Sitzung ohne Einstieg erhält eine eigene
[signierte Flachbestätigung](../../../src/ops/btc_demo_runtime_no_entry_v1.py).
Sie erfordert ein unverändert leeres Order-/Reservationsjournal und das
vollständige private FUTURES-Kontoinventar. Daraus entsteht weder ein Trade
noch ein erfundener PnL. Die vorhandene DDO-Erstentscheidungserfassung bleibt
im ursprünglichen Slot-3-Pfad. Die vorbereiteten DDO-/GVEF-Begleiter der anderen
Slots werden durch diesen Host nicht gestartet oder neu konfiguriert.

Der [Aufruf](../../../scripts/ops/run_btc_demo_bounded_host_v1.py) ist ohne
weitere Option eine reine Dateiprüfung. Er liest weder Schlüsselbund noch
Konto und legt keinen Lauf an. Die ausdrückliche Laufoption verlangt einen
separaten frischen Startbeleg, den gebundenen integrierten Quellstand und den
bestehenden Demo-Schlüsselbunddienst. Der Schlüssel wird ausschließlich in
diesem Laufzweig verdeckt in einen vorhandenen opaken TESTNET-Handle übergeben.
Ein solcher Startbeleg wird bei der Vorbereitung nicht erstellt.

Die [Hostregression](../../../tests/ops/test_btc_demo_bounded_host_v1.py)
führt beide Anfangsrichtungen durch Erstkauf, zwei Netto-Wechsel und den
bestätigten Schluss. Sie prüft Minutenwechsel, Timeout nach dem Socket,
Wiederaufnahme nach unklarem Erstkauf, Ablauf ohne Einstieg und eine abgelaufene
Startfreigabe. Nur HTTP-Antworten und temporäre Signierschlüssel werden simuliert;
Core, Journal, Kostenrechnung, Permits und Bestätigungsconsumer sind original.
Dies belegt keine tatsächliche Venueausführung, keinen physischen Stromausfall
und keinen gestarteten Fünferlauf.
