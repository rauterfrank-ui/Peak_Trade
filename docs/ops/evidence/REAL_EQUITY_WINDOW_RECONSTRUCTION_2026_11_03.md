---
docs_token: DOCS_TOKEN_REAL_EQUITY_WINDOW_RECONSTRUCTION_2026_11_03
status: working
scope: Original private evidence, observed window replay and precise remaining boundary
---

# Equity bis zum tatsächlich beobachteten Endbestand

Ausgangspunkt: lokaler Commit `bcff47c08f2b51cf41c4226a06ada0ad96f0f605`. Der Auftrag wurde über die bloße History-Sichtung hinaus bis zu den originalen Kontobuchungen, Funding-Gegenbuchungen und dem erneuten Replay bearbeitet. Historische Originale und bestehende Lern-/Kapitalregeln blieben erhalten.

## Nachgewiesener Fortschritt

- Historische und heutige Kontoidentität verbunden; ursprüngliche Erwerbungs-Body-Hashes, versiegelte Manifeste sowie Kandidaten-, Ratifikations-, Anker- und Mitgliedschaftsdigests erneut geprüft.
- Zwei neue begrenzte reale K1-Erwerbungen mit insgesamt **17 GETs**: Trading-Originaljournal mit 10 Antworten, Funding-/Typologie-Journal mit 7 Antworten. Keine Orders, Transfers oder Dienste.
- Trading: 49 native Archiv-Buchungen mit leerer Abschlussseite, aktuelle Bills-Antwort leer, beide End-Positionslisten leer, relevante Balancefelder unverändert.
- Im aktiven Fenster nach dem Anker: **11 Trading-Buchungen und 5 Funding-Buchungen** klassifiziert und nachgerechnet. Gebühren und PnL sind nicht doppelt gebucht; ursprüngliches offenes UPL wird nicht zusätzlich zum bereits realisierten Pfad abgezogen.
- Drei Trading-Transfers haben jeweils genau einen beobachteten Funding-Gegenkandidaten. EUR- und BTC-Umtausch haben beide nativen Währungsseiten. Die EUR-/BTC-Zugänge sind keine behaupteten Trading-Gewinne.
- Alle Currency-Cash-Bewegungen bleiben einzeln sichtbar. Funding wird separat betrachtet; EUR wird nicht zu einer impliziten USDC-Sizing-Quelle gemacht.
- Vollständiger Ergebnisbericht in einem neuen Prozess erneut erzeugt, mit ausdrücklich gesperrter K1-Öffnung und gesperrten Socket-Verbindungen. Ergebnis-SHA256 identisch: `1ebacbce7afccaba7146785549be7e05d76cbff998c51f4f333eb0ea8e52c928`.
- **179 relevante Tests bestanden**, einschließlich neuer Originaljournal-/Replay-Fehlerfälle und bestehender K1-, Startup-, historischer Accounting-/Anker- sowie dauerhafter Close-Ketten-Prüfungen.

Die Erwerbungsfassungen sind exakt privat gespeichert. Spätere Journal-Metadaten-Härtungen wurden auf dem finalen Code geprüft; sie werden nicht rückwirkend als der tatsächlich verwendete Erwerbungscode ausgegeben. [Erwerbungsbelege](real_equity_window_reconstruction_v1_2026_11_03/real_capture_receipts.json) und [gesperrter Offline-Neustart](real_equity_window_reconstruction_v1_2026_11_03/offline_restart_receipt.json).

## Konkrete Aufschlüsselung und belastbare Grenze

Die USDC-Endequity ist nun vom historischen Cash-Zeugen über die drei weiteren Funding-Belastungen, die Futures-Schließung einschließlich Gebühr und die beiden Umtauschzugänge nachvollzogen. BTC wurde vollständig umgetauscht; verbleibende EUR-Bestände in Trading und Funding werden separat ausgewiesen. Die eigenen Originalantworten mit Beträgen und Kontoidentität liegen privat außerhalb Git.

Es gibt eine konkrete Präzisionsgrenze, keine pauschal offene „Equity-Frage“: Der exakte native USDC-Buchbestand und der publizierte Endwert unterscheiden sich um **0.0000000000000132 USDC**. Der Endwert entspricht exakt der kürzesten Binär64-Darstellung des nativen Dezimalbestands. Dieselbe Art von Darstellung ist bereits im ursprünglichen Cash-/Equity-Paar sichtbar. Beim internen EUR-Transfer unterscheiden sich die Kontoseiten um **0.0000000000000008 EUR**; eine separate Erhaltungsrechnung mit den präzisen Gegenbewegungen trifft den Funding-Endwert exakt.

Diese Originalwerte werden nicht gerundet, ersetzt oder um eine erfundene Gebühr korrigiert. Ein allgemeiner verbindlicher Venue-Präzisionsvertrag konnte in der gezielten lokalen und offiziellen Dokumentationssuche nicht belegt werden. Deshalb lautet der echte Replay-Status `OBSERVED_WINDOW_EXPLAINED_WITH_EXPLICIT_PRESENTATION_RESIDUALS`, mit Exitcode 3 und ausdrücklich fehlender exakter autoritativer Source-Freigabe. Die im dokumentierten Fenster beobachteten Bewegungen sind aufgeschlüsselt; eine exakte Gleichheit aller nativen Snapshot-Felder wird nicht behauptet. Vergleichsrelation, Inferenz und Grenze stehen im [Vertrag](../specs/REAL_EQUITY_WINDOW_RECONCILIATION_V1.md).

## Dauerhafte Nachweise und weiterer Systemumfang

Originaljournale, Original-Erwerbungscode, vollständiges Ergebnis, verständliche Aufschlüsselung, Replay-Quellen und Neustartbeleg sind zusätzlich als privates Archiv auf dem Desktop gesichert. Das Repo enthält nur Quellcode, Tests und datenarme Nachweisbindungen. Private Originale werden nicht automatisch auf GitHub gepusht.

Für den dauerhaften automatischen Equity-Producer bleiben der verbindliche Präzisions-/Abgleichsvertrag und die Verifikation weiterer zukünftiger Kontozustände erforderlich. Der neue Replay verweigert offene Positionen, isolierte/verwaltete Equity, Verbindlichkeiten, unbekannte Ereignisarten, nicht erschöpfte Quellen und echte Buchungslücken. Er behauptet weder vollständige Historie seit Kontoeröffnung noch universellen D6-Abschluss. Funding-Vollhistorie enthält ältere Migrationstypen außerhalb des aktiven Fensters; diese werden erhalten und nicht pauschal freigegeben. Andere Konten und Vermögensprodukte außerhalb der beobachteten Trading-/Funding-Quellen sind nicht Gegenstand dieses Nachweises.

U04 bleibt zurückgestellt. Der bestehende 29P-/Treasury-Kapital-Owner, P01, Double Play und der ursprüngliche Lernbestand wurden nicht verändert. Kein kontinuierlicher Dienst, keine Live-Freigabe, kein Push und keine Remote-CI aus diesem Arbeitsschritt.

Prüfungen und unveränderte Schutzdateien: [Abschlussmanifest](real_equity_window_reconstruction_v1_2026_11_03/verification_manifest.json).
