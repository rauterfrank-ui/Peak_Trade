---
docs_token: DOCS_TOKEN_PR_7180_CI_GATE_REPAIR_2026_11_06
base_commit: 44bf97953241c21e856976e798463b2a83e44bef
authority: NONE
runtime_authorization_effect: NONE
---

# PR 7180: Format- und Link-Trend-Korrektur

Der [Pull Request](https://github.com/rauterfrank-ui/Peak_Trade/pull/7180) besaß zwei verbleibende fehlgeschlagene Gates. Die Korrektur baut auf dem Kandidaten 44bf97953241c21e856976e798463b2a83e44bef auf. Das [Prüfprotokoll](PR_7180_CI_GATE_REPAIR_2026_11_06.json) bindet Quellen, Formatänderungen und tatsächliche Prüfergebnisse.

## Formatierung und Schutzverträge

Ruff 0.15.22 meldete 108 unformatierte Dateien. 77 davon werden formatiert; ihr vollständiger Python-AST bleibt vor und nach der Formatierung gleich. Dieser Vergleich belegt die begrenzte Formattransformation und ersetzt keinen Funktionsnachweis. Da auch konsumierte Module betroffen sind, werden die relevanten N1-Regressionsfälle erneut ausgeführt.

Die übrigen 31 Dateien unterliegen bestehenden bytegenauen Frozen-Verträgen: acht Master-V2-Dateien, eine Policydatei, eine kanonisch digestgebundene G17-Quelldatei und 21 durch die bestehende Economic-/Diagnostic-Mutationsgrenze gesperrte Research-/Testquellen. Darunter liegt ein Whole-File-Mitglied des Clean-Core-Seals. Eine globale Umformatierung würde diese bestehenden Schutzverträge verletzen. Der Formatverifier prüft deshalb zuerst die exakt benannte Menge gegen den Originalcommit, den bestehenden Source-Tag, das Atlasmodell und die aktuellen Bytes. Er weist diese 31 Originale aus und ruft Ruff für den gesamten verbleibenden ursprünglichen Suchumfang auf. Neue Dateien, Änderungen an einem Original und nachträglich angepasste Working-Digests bleiben Fehler.

Die genehmigten Reconfiguration-Quellen, die 31 bytegeschützten Originale und die bestehenden Master-V2-/Runtime-Vergleiche bleiben unverändert. Die separate Ruff-Fehlerprüfung schließt weiterhin alle 31 Dateien ein. Freeze-Tags und Produktzustände unter runtime bleiben erhalten.

Der vollständige Commitvergleich erfasst außerdem die bestehende Economic-/Diagnostic-Mutationsgrenze. Deren 21 bislang nicht für Änderungen zugelassene Research-/Testquellen bleiben exakt erhalten und gehören deshalb zur benannten Originalmenge. Ihr Fachgate und seine Freigaberegeln werden nicht geändert. Der abschließende Vergleich meldet keine unbekannte Mutation.

## Danach sichtbar gewordener Core-Seal-Altfehler

Der erstmals erreichte nächste Gateabschnitt scheitert lokal am alten Core-Siegel: vier Whole-File-Digests, ein geschützter AST-Digest und die inzwischen entfernte BTC-Sperrkonstante passen nicht mehr zum vorhandenen Quellstand. Der kombinierte Lauf meldet deshalb 247 PASS und fünf fehlgeschlagene Sealtests. Dieser Befund bleibt im Prüfprotokoll erhalten.

Die vorhandene [Ownerentscheidung zur gemeinsamen Futureszulassung](../specs/GGE_ONLY_FUTURES_AND_COMMON_ASSET_ADMISSION_V3.md) und der akzeptierte Frozencommit sind die Vergleichsquellen. Der Seal-Emitter prüft vor dem Re-Pin alle 20 Originaldateien bytegenau gegen genau diesen Commit und verweigert abweichende Workingquellen. Die Prüfmetadaten werden neu gebunden; keine dieser 20 Produktdateien wird geändert. Die alte Censusreferenz und das ursprüngliche Manifest bleiben über ihre frühere Revision im Prüfbeleg auffindbar.

Die obsolete Sperrkonstante im Prüfcensus wird durch den bestehenden tatsächlichen Instrumentzulassungsconsumer ersetzt. Dessen Delegation an die gemeinsame Futureszulassung ist damit AST-geschützt. Die 20 Mitglieder, Whole-/Mixed-File-Modi, übrigen Symbolmengen, Joinprojektion und negativen Schutzprüfungen bleiben bestehen. Der eingefrorene Policykatalog behält seine Originalobjekte; nur das gesondert deklarierte neue CI-Seal-Manifest darf über seinen exakten Entwicklungsdigest abweichen. Andere Policydateien besitzen keine solche Ausnahme.

## Veraltete Linkschuld-Vergleichsbasis

Die gespeicherte Grenze enthielt 243 fehlende Ziele. Ein lesender Git-Blobscan der tatsächlichen Mainbasis 9397d04a37d527a8316b3e44ef4f80b4ef44db7a liefert 653. Sämtliche Einträge stimmen mit dem zuvor geprüften PR-Vollscan überein; Quelldateien und fehlende Ziele stammen bereits aus Main. Kein neu gebrochener Link wird damit als Altbestand aufgenommen.

Die Baseline wird mit genau diesem Maincommit und seinem vollständigen Schuldensatz neu gebunden: 243 → 653, Differenz 410. Das ist eine Korrektur des veralteten Vergleichsstands. Die 653 Links gelten weiterhin als fehlend. Der [Projektleitfaden](../DOCS_REFERENCE_TARGETS_DEBT_GUIDE.md) schreibt für diese Situation den Abgleich auf den aktuellen Mainbestand mit Begründung und PR-Review vor. Der PR wird nicht automatisch gemergt.

Die Changed-Files-Prüfung bleibt streng, der Trendvergleich läuft weiter und seine Schuld wird nicht ignoriert. Die neue Baseline enthält Originalcommit, Quellart, frühere Anzahl und Begründung.

## Abnahme

Die konkreten lokalen Prüfergebnisse und ihre Quellenbindung stehen im Prüfprotokoll. Der Remoteausgang wird am tatsächlichen neuen PR-Commit geprüft. Aus dieser CI-Korrektur folgen weder Handelsaktivierung noch eine neue wirtschaftliche oder betriebliche Abnahme des N1-Anschlusses.

Nach der gezielten Seal-Korrektur bestehen 86 betroffene Atlas-/Law-/Sealtests. Ein abschließender Lauf mit den 14 neuen Formatgegenproben und den 22 tatsächlichen N1-Anschlussfällen besteht mit 36 Fällen. Der Formatverifier bestätigt 31 unveränderte Originale und 9.876 formatierte übrige Dateien. Ruff, Law-Währung, aktueller Atlas, Core-Siegel sowie die weiteren lokalen Lint-Gate-Verifier bestehen. Der gemeinsame Dokumentprüfer bestätigt fünf geänderte Markdowndateien, 44 Referenzen und einen stabilen Trend von 653 zu 653 fehlenden Zielen. Eine vollständig grüne Remote-CI wird erst nach deren tatsächlichem Abschluss beansprucht.
