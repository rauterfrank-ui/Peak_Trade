---
docs_token: DOCS_TOKEN_REAL_EQUITY_WINDOW_RECONCILIATION_V1
status: working
scope: Existing equity owner, factual private replay, no capital or sizing authority
---

# Tatsächliche Equity im belegten Kontofenster

Der vorhandene Equity-Owner erhält ein privates Originaljournal und einen deterministischen Replay-Pfad. Der bisherige Bills-Beobachter bleibt erhalten. Die neue Komponente erklärt tatsächliche Cash-Bewegungen und den beobachteten Flat-Endbestand; sie erzeugt keinen zweiten Kapitalverwalter und ersetzt nicht den bestehenden Sizing-Pfad.

## Ursprüngliche Konstruktion und heutige Verwendung

Der ratifizierte historische Anfangsbestand wird mit seinen ursprünglichen Erwerbungsantworten, Kandidaten-, Ratifikations-, Anker- und Mitgliedschaftsdigests sowie den versiegelten Manifesten geprüft. Die heutige erwartete Kontoidentität stammt weiterhin unabhängig aus der bestehenden Konfiguration. Historischer Account und heutige signierte Abfragen müssen übereinstimmen. Ein alter Stock wird nicht bloß wegen seines Dateinamens oder Zeitstempels übernommen.

Der physische Buchbestand ist vom verfügbaren Sizing-Kapital getrennt. Ein im Anfangsbestand enthaltener offener Positions-PnL wird nicht später nochmals zusätzlich abgezogen. Bereits gebuchte Gebühren, PnL und Funding werden nicht erneut auf die signierten nativen Cash-Bewegungen gerechnet. Reservierungen, U04, P01 und Lernbestände werden nicht geändert.

## Originaljournal und Erwerbung

`PrivateEquityJournalV1` schreibt Original-Response-Bodies mit SHA256 und verketteten Dateihashes ausschließlich in ein neues privates Verzeichnis. Verzeichnis 0700, Dateien 0600, exklusives Anlegen, Dateien vor Abschluss synchronisiert. Fehlerzustände werden versiegelt; fehlgeschlagene Erwerbungen sind keine Replay-Quelle. Authentifizierungsheader und Credential-Material werden nicht an den Journal-Callback weitergegeben.

Der vorhandene GET-Transport hat dafür einen standardmäßig ungebundenen Raw-Response-Callback. Ohne explizite Bindung bleibt sein Verhalten erhalten. Der Callback liefert keine Schreib- oder Orderberechtigung. Das vorhandene K1-Kontextmanagement räumt Callback, Caches und Handle-Referenz nach Ende auf.

Das Trading-Profil hat höchstens zehn GETs: konfigurierte Kontoidentität, Balance und vollständige Positionsliste vor und nach den Bills, maximal zwei Archivseiten, eine aktuelle Bills-Seite, Funding-Balance und abschließende Kontoidentität. Das Funding-Profil hat höchstens neun GETs: Kontoidentität und Funding-Balances vor/nach der begrenzten Funding-Historie sowie native Bill-Typologie. Bestehendes Request-Limit bleibt bestehen; keine automatischen Wiederholungen, keine Dienstaktivierung.

Abfragen sind unfiltriert. Trading verwendet ausschließlich native Bill-IDs als `after`-Cursor. Funding verwendet ausdrücklich Zeitstempel; diese verschiedenen Cursorverträge werden nicht vermischt. Bei einer vollen 100-Zeilen-Funding-Seite wird wegen der möglichen Zeitstempel-Grenzmehrdeutigkeit abgewiesen. Funding-History-Aufrufe werden auf höchstens einen pro Sekunde begrenzt. Eine kurze Seite allein gilt nicht als Vollständigkeitsbeweis; es muss eine leere Abschlussseite vorliegen.

Die Feldbedeutungen, native Typologie, Retention und Cursorsemantik wurden gegen die [offizielle OKX-Dokumentation](https://www.okx.com/docs-v5/en/) und die tatsächlich authentifizierte Typologie-Antwort geprüft. Funding-History kann verzögert aktualisiert sein; stabile Snapshots, letzte beobachtete Buchungszeit und Gegenkonten werden deshalb im datierten Nachweis berücksichtigt. Eine leere Antwort beweist niemals außerhalb des dokumentierten Quellenfensters Ereignisfreiheit.

## Replay und Bilanzgrenzen

Der Loader verlangt unabhängig gebundene Manifest-Hashes. Er prüft Originaldatei, Body-Digest, Hashkette, erfolgreiche frische GET-Provenienz, eindeutige JSON-Felder, Labels und konkrete Endpunkte. Das Replay prüft Reihenfolge, unfiltrierte Cursor, leere Endseiten, ein konservativ unter 89 Tagen liegendes Ankerfenster und einen nativen Pre-Anker-Bill-Zeugen. Dieselbe Bill-ID mit widersprüchlichen Daten wird abgewiesen.

Unterstützt ist der beobachtete Fall: Futures-Kontomodus, Net-Modus, kein Auto-Borrowing, am Ende zweimal leere Positionslisten und stabile Cash-/Equity-Felder. Isolierte oder anderweitig verwaltete Equity-Anteile, Verbindlichkeiten, offene Positionsbewertung, unbekannte wirtschaftliche Klassen und fehlende Gegenbuchungen werden abgewiesen. Das ist keine allgemeine Behauptung, jeder künftige Kontozustand sei bereits angebunden.

Alle Bewegungen bleiben in ihrer ursprünglichen Währung. Explizit unterstützte Transfer-, Futures-Ausführungs-, Funding-, Convert- und Simple-Trade-Buchungen werden anhand der tatsächlichen Felder geprüft. Umtausch benötigt beide nativen Währungsseiten mit gleichem Trade-/Instrument-/Zeitbezug. Der Umtauschbetrag ist eine tatsächliche Bewegung, keine angenommene aktuelle Währungsbewertung und kein behaupteter Trading-Gewinn.

Interne Funding-/Trading-Transfers benötigen genau einen Gegenkandidaten nach Währung, Richtung, Betrag und dem Sekunden-/Millisekunden-Zeitbezug. Dies ersetzt keinen gemeinsamen Transfer-ID-Nachweis. Beide Originalwerte werden bewahrt. Für den beobachteten EUR-Transfer gibt es eine separat ausgewiesene Darstellungsdifferenz; die Erhaltungsrechnung mit den präziseren Trading-Gegenbewegungen trifft den Funding-Endbestand exakt. Der native Funding-Posting-Replay bleibt daneben mit seinem Residuum erhalten.

Ausgelassene Nullwährungszeilen werden ausschließlich im ausdrücklich dokumentierten vollständigen Balance-Antwortfall behandelt, verbunden mit einem ersten nativen Zugang aus belegtem Null-Vorgänger beziehungsweise einem rekonstruierten Null-Endsaldo. Fehlende numerische Felder werden weiterhin abgewiesen. Vor dem aktiven Fenster liegende unbekannte Migrationstypen werden nicht nachträglich als Nullereignisse ratifiziert.

## Präzision und Autorität

Das native Dezimaljournal wird nie gerundet. Differenzen zu publizierten Cash-/Equity-Strings bleiben numerisch sichtbar. Eine Übereinstimmung mit der deterministischen kürzesten Binär64-Darstellung wird separat diagnostiziert; sie ist kein erfundener Epsilon-Vergleich, keine Buchungskorrektur und kein nachgewiesener allgemeiner Formatvertrag der Börse.

Ein vollständig exakt passender unterstützter Testfall erhält einen exakten Beobachtungsstatus. Der echte datierte Fall bleibt wegen nicht exakt gleicher Snapshot-/Ledger-Dezimalwerte als **Bewegungsfenster mit expliziten Darstellungsresiduen erklärt** gekennzeichnet. Der allgemeine Formatvertrag wurde in den untersuchten Primärquellen nicht belegt. Die Anforderung an eine exakte autoritative Equity-Quelle wird daher nicht für einen grünen Status aufgeweicht. Universelle D6-Vollständigkeit, verfügbare Sizing-Equity und Kapitalfreigabe bleiben unberührt.

## Bedienung

Der kanonische Einstieg ist `scripts.ops.run_real_equity_reconciliation_v1` über `./scripts/pt -m`. Ohne ausdrückliches `--acquire` läuft ausschließlich Replay. Es benötigt die beiden privaten Journale und ihre unabhängig gebundenen Manifest-Hashes. `--private-output` schreibt einen neuen privaten Vollbericht außerhalb des Repos. `--expected-report-sha256` verlangt byteidentische Wiederholung.

Mit `--acquire trading` oder `--acquire funding` und `--private-journal` wird genau eine neue begrenzte K1-Beobachtung gewählt. Ein vorhandenes Journal wird niemals überschrieben. Der volle private Nachweis wird nicht auf GitHub publiziert. CLI-Ausgabe enthält nur Status, Hashes, Zeitpunkte und Zähler.

Exitcodes: 0 für exakt passenden unterstützten Beobachtungsfall beziehungsweise erfolgreiche Erwerbung, 3 für erklärtes Fenster mit offenem exaktem Präzisionsvertrag, 2 für Fehler. Kein Status aktiviert Handel oder Geldbewegungen.

Nachweis: [datierte Rekonstruktion](../evidence/REAL_EQUITY_WINDOW_RECONSTRUCTION_2026_11_03.md).

Fortschreibung 03.11.2026: [interne Vergleichsregel, korrigiertes Accounting-Binding und lokale Betriebsprüfungen](EQUITY_CONTINUOUS_VERIFICATION_PREPARATION_V1.md). Die mathematischen Kernel-Primitive bleiben unverändert; Checkpoint-Version 2 und expliziter lokaler Abgleich sind geprüft. Legacy-Checkpoint-Migration und echte Betriebsfreigabe werden nicht daraus abgeleitet.
