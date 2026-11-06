# Obsidian-Einstieg und Galaxy View · 06.11.2026

Start, System-Cockpit und die beiden zentralen Systemkarten des aktiven Obsidian-Vaults wurden an den belegten Repository-Checkpoint `c2df25a4834ac3a3a05b7949cbdbdcea6d05cf1b` angeglichen. Die unabhängige Marktbeobachtung stammt aus Produktcommit `9150b9d129cc630ab214f87b56422f4962e3a34e`. Dieses Paket ändert Ansichten und Navigation; die Produktimplementierung bleibt unverändert.

Die neuen Ansichten unterscheiden den ursprünglichen E6-Decisionpfad vom neuen entscheidungsfreien Marktmessungspfad. Sie bewahren Ownership, innere Ebenen, Mess-/Forecast-/PnL-Bedeutungen und Informationszeiten. Der E6-Wechsel 50→100 wird als Wirkung des Duplicatefilters benannt; die separate E4-Meta-Kontrolle bleibt ein eigener Nachweis. Der Anschluss vom Lernzustand zum nächsten tatsächlich verwendeten Modell bleibt ausdrücklich offen.

## Gesicherte Ansichten

- [Startseite](after/Start.md.txt) mit direktem Zugang zu Cockpit, beiden Karten, Graph und aktuellen Lücken.
- [System-Cockpit](<after/00 Systemindex/System Cockpit.md.txt>) mit getrennten Nachweisscopes und Herkunftsrevisionen.
- [Universen und Außenkanten](after/Systemkarte.canvas) mit den sechs vorhandenen Universen, den fünf Außenrubriken und Datei-Karten zu den Dossiers.
- [Zwei Offlinepfade](<after/Systemkarte Offlineverbund.canvas>) mit originaler E6-Episode und neuer unabhängiger Marktmessung. Der offene nächste Modellzustand erhält keine erfundene Anschlusskante.
- [Galaxy-Bedienung und Graphsemantik](<after/00 Systemindex/Galaxy View.md.txt>).

Die vollständigen Vorherbilder liegen unter `before`, die aktuellen Ansichten und Bindungsdateien unter `after`. Markdown-Snapshots tragen zur klaren Trennung von aktiven Repo-Dokumenten die Endung `.md.txt`. Die drei historischen Bindungsdateien behalten ihre Source-, Modell-, Proof-, Zähl- und Ursprungsfelder; nur vorhandene Hashes der betroffenen Ansichten werden aktualisiert und ein begrenzter neuer Ansichtsvermerk ergänzt. Die alten Zähler beschreiben weiterhin den historischen Scope.

## Tatsächlich geprüfte Obsidian-Ansicht

Die vorhandene Erweiterung **Galaxy View 0.6.1** war in der Konfiguration aufgeführt, wurde im eingeschränkten Obsidian-Modus aber nicht geladen. Sie wurde für den gewünschten Graphgebrauch aktiviert. Der laufende Graph, Knotensuche und Anflug auf die Systemkarte wurden in Obsidian 1.15.0 beobachtet. Die vier aktualisierten Einstiegsansichten wurden geöffnet; die Karten wurden in Gesamt- und Lesevergrößerung kontrolliert und die Kantenbeschriftungen gekürzt.

Die Graphansicht blendet die vier großen technischen Ordner Komponenten, Verbindungen, Register und Werte aus und zeigte beim Abschluss **1.061 Knoten**. Alle Dokumente bleiben erhalten und sind über „Alle anzeigen“ wieder einblendbar. Start, Cockpit, beide Karten und Galaxy bleiben als Tabs geöffnet. Die Systemkarte erschien in der Graphsuche mit **47 Links**; diese Zahl ist Graphnavigation, kein Runtimebeweis.

[Erfasste Galaxy-Einstellungen](galaxy-settings.json) enthalten die gespeicherten Ansichts-/Filterwerte. Nur der flüchtige geometrische Positionscache wird im Repo-Snapshot ausgelassen; die aktive Datei bleibt vollständig erhalten. [UI-Beobachtung](ui-observation.json) hält den Umfang der Sichtprüfung fest. Es wurde kein fremder Plugin-Code verändert oder als eigene Implementierung übernommen.

Herstellerdokumentation: [Galaxy View](https://github.com/Longwind1984/galaxy-view). Der Eintrag ist im [offiziellen Obsidian-Verzeichnis](https://github.com/obsidianmd/obsidian-releases/blob/master/community-plugins.json) vorhanden. Die lokale Version und beobachtete Bedienung sind für diesen Bericht maßgeblich.

## Prüfung und Grenzen

[Manifest](manifest.json) bindet Einzeldateien und aktive Vault-Ziele. Der [lesende Prüfer](verify_view.py) prüft lokale Links, Canvas-IDs und Kantenendpunkte, überschneidungsfreie Kartenrechtecke, Erhaltung der bisherigen Knoten/Kanten, aktuelle Ansichtshashes und unveränderte historische Bindungsfelder. Zusätzlich werden die **11.358 Source-/Test-/Configdateien** und der originale XML-Beleg mit **787 unterschiedlichen bestandenen Fällen** des [vorherigen Produktnachweises](../independent_market_observation_v1_2026_11_06/README.md) erneut gebunden. Die Tests werden wegen unveränderter Produktquellen wiederverwendet; es gibt keinen neuen Produkttestlauf.

Die früheren 1.509 E6-Tests und späteren 1.575 Integrationstests bleiben an ihren damaligen Scopes. Ihre Zahlen werden weder addiert noch durch 787 ersetzt. Die Ansichtskontrolle erneuert keine globale semantische Abnahme, natürliche Quellen-/Qualitätsprüfung, wirtschaftliche Bewertung oder Betriebsautorität. Graphkanten zeigen Dokumentbeziehungen. Ein nächster Lern-/Modellconsumer entsteht durch dieses Update nicht.
