---
docs_token: DOCS_TOKEN_BREV_V2_POWER_NETWORK_PACKAGE
status: proposed
runtime_authorization_effect: NONE
---

# Power Network Package für BREV V2 auf LANE_1

Dieses Paket fasst die drei Abnahmen für denselben Mac-Betriebspunkt in einem
PR zusammen. Ausgangspunkt ist `47832d8dd` mit dem nachgewiesenen
Offline-Erstfill. Die [Paketbelege](../evidence/BREV_V2_POWER_NETWORK_PACKAGE.json)
halten den lesenden Mac-Abgleich und die Ergebnisse der isolierten Prüfungen fest.

```sh
./scripts/pt -B -m scripts.ops.check_brev_v2_operating_point \
  --manifest /absoluter/pfad/zum/privaten-v2-manifest.json
```

Der [Prüfer](../../../scripts/ops/check_brev_v2_operating_point.py) gibt die
Blocker aller drei Slices als JSON aus. Exitcode 75 bedeutet, dass die
Betriebsabnahme offen ist. Der Prüfer öffnet keine Runtimeports und erteilt keine
Freigabe. Die Belege für Konto, SQLite-Datei, Reservierung und Cursor bleiben lokal.

## Slice 1 – Mac-Betriebspunkt

Der V2-Manifestvertrag bindet Checkout, Betriebsgrenzen, Filegate und die
ursprünglichen Request-Pfade. Der Prüfer verwendet das bestehende Owner-GO-Gate
und löst die kanonischen F1/M9-Ledger über ihren Consumer auf.
Auf dem geprüften Mac ist V2 nicht geladen. Der Owner-GO stoppt mit
`BASELINE_LINEAGE_IMMUTABLE_SURFACE_DRIFT` und der kanonische Filegate-Nachweis
fehlt im geprüften Shell-Kontext. Der lesende F1/M9-Abgleich meldet
`CONTINUATION_COMPLETE`.

Für die Betriebsabnahme müssen der zuständige Owner die konkrete Revision
freigeben und der Betreiber ein gültiges Manifest für dieselbe Konto- und
Instrumentepisode vorlegen. Filegate, Cap24-Publikation, SQLite-Datei,
Reservierung, Cursor und F1/M9 gehören an diesen Betriebspunkt. Die Freigabe für
den tatsächlichen Start und die gegebenenfalls benötigten GETs bleibt separat.

## Slice 2 – Start und Wiederanlauf

Der [Cap24- und WAIT-Prüfpfad](../../../scripts/ops/run_offline_occupied_brev_with_cap24_v1.py)
wird gemeinsam vom Prüfer und vom vorhandenen Wiederanlauf verwendet.
Er bindet die Cap24-Publikation an das Instrument und prüft den gespeicherten
WAIT gegen die ursprüngliche SQLite-Datei, den Budgetstand, die Reservierung,
den Cursor und den Request-Digest. Der Mac-Manifestentwurf und seine plist
sind offline geprüft. Der Wiederanlauf nach simuliertem Fill und `SIGKILL`
ist für die belegte BREV-Fixture nachgewiesen. Eine alte Cap24-Publikation
bleibt an ihre historische Prüfuhr gebunden.

Der Betriebsnachweis erfordert einen gültigen Ausgangszustand und ein gültiges
Zeitfenster. Nach getrennt freigegebenem Dienststart muss ein frischer Prozess
denselben belegten Zustand wieder aufnehmen und `WAITING_FOR_NEXT_C1` im
zuständigen Ledger veröffentlichen. Das signierte Offline-Fenster bleibt ein
Testpfad.

## Slice 3 – Ordergebundene POST-Freigabe und Restore

Mit `--post-binding` kann der Prüfer zusätzlich die lokal bereitgestellte
Metadatenbindung des POST-Owners kontrollieren. Die JSON-Datei enthält `account`,
`store`, `store_id`, `issuer_id`, den öffentlichen Schlüssel `verify_key` als
Hexwert, den unabhängigen SQLite-`checkpoint` und `binding_sha256`. Beide
Dateipfade sind absolut. Der vorhandene POST-Authority-Owner prüft Generation
und Checkpoint. Dabei wird keine Grant-ID verbraucht.

Die Offline-Vertragstests belegen den bestehenden POST-Sender mit Testaussteller,
den Zustand `MAY_HAVE_SENT`, die Sperre gegen einen zweiten Versand sowie
Buchung und Restore in den jeweils geprüften Szenarien. Der V2-Mac-Dispatcher
hat derzeit keinen angeschlossenen POST-Port. Der vorhandene
[POST-Adapter](../../../src/ops/n1_post_authority_startup_v1.py) bindet die
Freigabequelle am V1-Supervisor. Dieser Teilnachweis erteilt dem V2-Host
keine Versandfreigabe.

Für die Betriebsabnahme braucht V2 die tatsächlich zugeordnete Freigabequelle
am selben Betriebspunkt. Die Order muss für Aussteller, Konto, Aktion und
Envelope-Digest gebunden sein. Nach unklarem Sendestatus müssen
`clOrdId` und Envelope-Digest über die vollständige Reconciliation bis zur
einmaligen Buchung und zum Restore derselben Position verfolgt werden. Bis zur
Klärung bleibt die ursprüngliche Reservierung gebunden.
