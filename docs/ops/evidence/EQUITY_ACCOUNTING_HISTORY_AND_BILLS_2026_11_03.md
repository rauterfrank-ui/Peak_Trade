---
docs_token: DOCS_TOKEN_EQUITY_ACCOUNTING_HISTORY_AND_BILLS_2026_11_03
status: working
scope: Historical source reconstruction and real read-only bills observation
---

# Wiedergefundene Buchführung und echte Kontobewegungen

Ausgangspunkt ist der lokale Commit `9d32ebde39c760c6f68c3fec1c0232e509fd0985`. GitHub-Verlauf, vorhandener Code und Originalbelege wurden gemeinsam betrachtet. Die neue Konfiguration bleibt maßgeblich; historische Freigabetexte wurden nicht als neue Aufträge ausgeführt.

## Wiedergefunden und erneut geprüft

- [PR 6267](https://github.com/rauterfrank-ui/Peak_Trade/pull/6267), Merge `4ad023a01708d897cd5a49bd06bff7bb02bbf590`: echter einzelner SUI-Futures-Trade, exakter realisierter Netto-PnL `-0.000374 USDC`. Bestehender Prüfer erneut auf den Originaldateien ausgeführt, Body-Hashes zusätzlich geprüft. Restart und vollständige Kontobuchführung waren ausdrücklich nicht geschlossen.
- [PR 6441](https://github.com/rauterfrank-ui/Peak_Trade/pull/6441): D6-Ereignisstrom-Vertrag. Das vorhandene Vertragsmodell und damalige Rohbeobachtungen ersetzen keinen vollständigen klassifizierten Buchungsstrom.
- [PR 6468](https://github.com/rauterfrank-ui/Peak_Trade/pull/6468), [PR 6469](https://github.com/rauterfrank-ui/Peak_Trade/pull/6469), [PR 6470](https://github.com/rauterfrank-ui/Peak_Trade/pull/6470): Kandidat, Ratifikation, Anker und Mitgliedschaft vom 14. September wiedergefunden. Wert und Zeitpunkt sind durchgehend identisch; Digest-Verweise stimmen überein. Das korrigiert die zu pauschale frühere Aussage, ein Anfangsbestand fehle überhaupt. Ein heutiger, durchgehend fortgeschriebener Anfangsbestand ist damit weiterhin nicht belegt.
- [PR 6491](https://github.com/rauterfrank-ui/Peak_Trade/pull/6491): versiegelte historische Rekonstruktion vom aktuellen Sizing-Pfad getrennt. Diese Trennung wird erhalten.
- Historische Bills vom 13. September: 36 eindeutige Buchungen, davon 4 EUR und 32 USDC; 22 identische Überlappungen zwischen den beiden Abfragen. Alle 34 tatsächlich vergleichbaren Übergänge stimmen exakt. Das ist eine zusätzliche arithmetische Diagnose, kein nachträglicher D6-Vollständigkeitsnachweis.

Die PR-Metadaten mit Mergezeit, SHA und damaligem Beschreibungstext sowie die erneut berechneten Ergebnisse liegen im [Nachweisordner](equity_accounting_history_and_bills_v1_2026_11_03/historical_replay.json). Der GitHub-Connector war technisch nicht aufrufbar; die GitHub-API über das vorhandene `gh` lieferte die Metadaten. Kein Push, PR oder CI-Lauf wurde ausgelöst.

## Externe Quellen

M2DATA und PeakDATARecovery waren als getrennte lokale Volumes gemountet. Der gezielte Prozesscheck zeigte keinen Prozessnamen für photorec, testdisk oder ddrescue; dies ist kein allgemeiner Beweis ruhender Recovery. Das M2-Backup `Peak_Trade_Disaster_Backup_20261017T190216Z&#47;repo` hat HEAD `242b7974fc93f0bdb47706556101bd6f0c497414`. Drei gezielte Vergleichsdateien – Trade-Prädikat, Mitgliedschaftsbeleg und historische Archiv-Bills – sind mit dem heutigen Original byteidentisch. Damit ist das Backup eine unabhängige Fundstelle derselben historischen Dateien, keine zweite Laufzeitbeobachtung.

Die gezielte Recovery-Code-Dateinamensuche nach den beiden Buchführungs-/Stream-Modulnamen lieferte keine Kandidaten. Daraus folgt keine Vollständigkeits- oder Abwesenheitsaussage über das Recovery. Nach dem zuvor beobachteten I/O-Fehler an einer AppleDouble-Datei wurde keine breite Inhaltssuche, Reparatur oder neuer Recovery-Scan durchgeführt. Beide externen Quellen blieben unbeschrieben. Vorhandene Obsidian- und Chat-Rekonstruktionshinweise dienten der Navigation; Originaldateien und konkrete Revisionen tragen die Aussagen.

## Neu umgesetzt und real beobachtet

Der vorhandene K1-Beobachter kann jetzt unfiltrierte Kontobuchungen begrenzt paginieren und die Saldenfolgen getrennt je Währung prüfen. Wiederholte Cursor, widersprüchliche Bill-IDs, vermischte Kontobindungen, fehlende Zahlen und Zeitwidersprüche werden abgewiesen. Gebühren-/PnL-Felder werden nicht zusätzlich auf die bereits gebuchte Kontobewegung gerechnet. Siehe [Vertrag](../specs/ACCOUNT_BILLS_OBSERVATION_AND_HISTORICAL_REPLAY_V1.md); Feldbedeutungen wurden gegen die [offizielle OKX-Dokumentation](https://www.okx.com/docs-v5/en/) geprüft.

Echter einmaliger Lauf: 3 GETs, davon eine Kontoidentitätsprüfung und zwei Archivseiten einschließlich leerer Abschlussseite. 49 eindeutige Buchungen: BTC 3, EUR 5, USDC 41. Alle 46 vergleichbaren Übergänge stimmen exakt, keine Cursor-/Duplikatkonflikte. Es wurden keine Beträge oder Rohzeilen im neuen Bericht gespeichert. Die exakten Codefassungen vor diesem Lauf sind separat gebunden. Ein erster direkter Skriptaufruf scheiterte vor Import der Quelle; er führte keinen Credential- oder Netzwerkzugriff aus. Der tatsächliche Lauf verwendete den kanonischen Modulaufruf.

[Echter Bericht](equity_accounting_history_and_bills_v1_2026_11_03/real_bills_observation.json) und [Codebindung](equity_accounting_history_and_bills_v1_2026_11_03/real_probe_source_bindings.json). `result=BLOCKED` und Exitcode 2 sind hier absichtlich korrekt: API-Beobachtung und Saldenvergleich erfolgreich, vollständige klassifizierte Equity-Rekonstruktion nicht belegt. Aus einer geleerten API-Pagination oder konsistenten Salden kann insbesondere kein Beweis gegen ausgleichende fehlende Ereignisse abgeleitet werden.

## Verbleibende Arbeit für vollständige echte Equity

Die konkrete Lösung baut auf den wiedergefundenen Originalen und dem vorhandenen Owner auf: historisch oder neu gebundener Anfangsbestand; dauerhaftes privates Journal der Originalereignisse; nachgewiesenes Zeitfenster und Konto; vollständige Klassifikation einschließlich Transfers, Umtausch, Gebühren, Funding, Settlement, Liquidation und Verbindlichkeiten; explizite Bewertungsgrundlage für offene Positionen; deterministischer Neustart und unabhängiger Abgleich. Bills-Salden, Fill-Abrechnung und Equity sind unterschiedliche Ebenen und werden nicht einfach summiert. Ein echter neuer Trade ist für historische Prüfung oder Kontobeobachtung nicht erforderlich.

Die heutige Diagnose speichert Seitenhashes, keinen vollständigen Roh-Journalbestand. Die Brücke vom historischen Stock zum heutigen Konto und die klassifizierte Ereignisabdeckung bleiben deshalb ausdrücklich offen. U04 bleibt wie vereinbart zurückgestellt. Der vorhandene Sizing-/Kapitalpfad und Lernbestand wurden nicht verändert.

Validierung und unveränderte Schutzdateien werden im [Prüfmanifest](equity_accounting_history_and_bills_v1_2026_11_03/verification_manifest.json) gebunden. Ein vorhandener historischer Dokumentationstest verlangte bereits am Ausgangs-HEAD einen nicht mehr vorhandenen Runbook-Abschnitt und alte Live-Fertigmeldungen. Er wurde auf die heutige historische Nachweisführung und die ausdrücklich fehlende aktuelle Stock-Autorität umgestellt; historische Funktions-, Digest- und Ablehnungsprüfungen bleiben bestehen.

Abschlussprüfung: **141 Tests bestanden**, Ruff-Format und Lint grün, Atlas gültig ohne generierten Drift, geänderte Markdown-Verweise und Token geprüft. Historische Originale, zurückgestellte U04-Dateien und ursprünglicher Lernbestand anhand SHA256 unverändert. Desktop- und Repo-Blueprint nach Frontmatter identisch.
