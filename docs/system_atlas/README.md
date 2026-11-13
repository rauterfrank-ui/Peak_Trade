# PeakTrade System Atlas

```text
ATLAS_AUTHORITY=NONE
ATLAS_ROLE=CURRENT_FROZEN_SYSTEM_DESCRIPTION
RUNTIME_AUTHORIZATION_EFFECT=NONE
CURRENT_ONLY=true
SYSTEM_FREEZE_TAG=freeze/clean-system-complete-2026-11-06-v1
SOURCE_TAG=freeze/clean-system-2026-11-06-v1
SOURCE_COMMIT=c742a23c964901c1353fcf3468e618db9cb6ef42
```

Der [System Atlas](generated/SYSTEM_ATLAS.md) beschreibt diesen fixierten Quellbaum mit Fachräumen, inneren Modulen, Eingängen, Verarbeitung, Ausgängen, Zustand und Consumergrenzen. Der [Quellenindex](generated/SOURCE_INDEX.md) erschließt alle Dateien des Fixpunkts.

Der Dateikatalog bezeichnet den unveränderten Freeze-Baum. Die aktuelle Dokumentationsprojektion ersetzt die Runbook-, Map- und Atlasdarstellung; ihre Dokumentbytes und Atlaswerkzeuge sind deshalb ausdrücklich von den fixierten Produktquellen getrennt. Der Freeze-Tag bleibt an seinem Commit.

Der [Abgrenzungsbeleg](source/successor-disposition.json) unterscheidet den aktuellen Arbeitsbestand, die benötigte origin/main-Vergleichsquelle und extern archivierte Bestände. Die 42 lokalen Worktrees wurden als historische Arbeitskopien ausgelagert; kein Worktree-Inhalt wurde integriert. 82 historische Repo-Dateien einschließlich Backup-Paketen und eines datierten Wiederherstellungsprüfers sind im Bereinigungsregister mit Transferdigests gebunden. Die Atlasprüfung braucht zum Prüfen dieser Belege kein angeschlossenes Archivlaufwerk.

Der historische Wiederherstellungsprüfer war am aktuellen Baum bereits vor seiner Auslagerung mit `CURRENT_CORPUS_PARITY_DRIFT` am N-Bars-Supplier fehlgeschlagen. Er und sein damaliges Eingabepaket bilden eine archivierte, datierte Prüfeinheit. Dieser Befund wird nicht in einen heutigen PASS umgedeutet. Produktimplementierungen, aktuelle Corpus-/Researchinputs und gespeicherte Runtimezustände werden dadurch nicht aus historischen Worktrees ersetzt.

Die [Law Impact Map](../governance/current_law_impact_map_v1/generated/LAW_CHANGE_IMPACT.md) ergänzt diesen Atlas um Originalregelquellen und den [Policy-Katalog](source/current-policies.jsonl.gz). Das [Bereinigungsregister](source/documentation-cleanup.json) führt die früheren separaten Karten und die erhaltenen maschinellen Verträge. Die folgende Außenansicht ist Teil des System Atlas. Der Katalog belegt Referenzstellen und ihren jeweiligen Prüfstatus.

Die Grundlage ist [current-model.json](source/current-model.json) mit den vollständigen Datei-, Python-Definitions- und Importkatalogen unter [source](source/). Das [Master Runbook](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) ist die primäre Betriebs-/Entwicklungsorientierung. Der Atlas schafft keine zusätzliche Fach-, Apply- oder Ausführungsauthority.

Erzeugen und prüfen, aus dem Repository-Stamm:

```text
./scripts/pt scripts/ops/generate_system_atlas_v1.py
./scripts/pt scripts/ops/validate_system_atlas_v1.py
./scripts/pt scripts/ops/check_system_atlas_impact_v1.py
```

Diese Einstiegspunkte verwenden für dieses Atlasmodell `current_atlas.py`. Die Prüfung kontrolliert Quellstand, vollständige Dateimenge, Quelldigests, Literalverträge, Dokumentlinks und deterministische Ausgabe. Sie weist ausgeführte Laufzeitwirkung nicht aus.

Der [forensische GHV-Crosswalk](../../scripts/ops/ghv_forensic_whole_system_crosswalk_v1/cli.py) liest dieses Modell und das versionierte Übergaberegister. Er nimmt nur explizite Repo-Verträge mit unveränderten Quellpfaden und im Census verankerten Endpunkten als Navigationskanten auf. Die importierten Routen aus älteren Ansichten, offenen Endpunkte und Offline-Belege bleiben außerhalb dieser Projektion. Das Prüfwerkzeug schreibt seine Berichte in den gewählten Ausgabeordner. Bei abweichenden Quellrevisionen bleibt die strenge Verifikation gesperrt. Der Modus `--navigation-only` liefert in diesem Fall eine Ansicht ohne Laufzeitnachweis.

## Außenstruktur und aktuelles Dateiregister

Die [Fachbereiche und Außenkanten](generated/BOUNDARIES.md) erschließen die sechs Universen, den Außenring mit fünf Rubriken und acht überlappenden Sichten sowie die externe Metaebene. Die inneren Gruppen verweisen auf die Originalverträge des Repo-Atlas und den nativen Core-Katalog. Das [Übergabe- und Signalregister](source/boundaries.json) führt die Obsidian-Quellen mit Hash, ihre ursprünglichen Kantenadressen, Richtung und Semantik. Die Repo-Belege kennzeichnen abweichende oder fehlende Quelldateien und ergänzen den Offline-Pfad nach PR #7241.

Der [Zuordnungskatalog](source/artifact-assignments.jsonl.gz) enthält eine primäre Adresse und eine Artefaktrolle pro Pfad. Gemeinsame Zuständigkeiten bleiben als Querbezüge erhalten. Evidence- und Testartefakte beschreiben ihre dokumentarische oder prüfende Funktion. Der [Manifestbeleg](source/artifact-assignments.json) bindet die Zuordnungen an einen Git-Baum. Archiv, Entwicklungsdaten und neue Atlasdateien sind im selben Katalog adressierbar.

```bash
./scripts/pt docs/system_atlas/coverage.py check
./scripts/pt docs/system_atlas/coverage.py area SL
./scripts/pt docs/system_atlas/coverage.py edge REPO-7241-SL-OPT
./scripts/pt docs/system_atlas/coverage.py path src/experiments/offline_ddo_research_cycle_v1.py
```

Der normale Atlas-Check validiert den gebundenen Stand und zählt neue oder entfernte Pfade im Checkout. Die strikte Dateiprüfung meldet die einzelnen fehlenden oder überholten Zuordnungen als Fehler. Bei einer Nachführung die betroffenen Pfade, ihre Rolle und bei einer neuen Referenzrevision auch die Git-Objekte sowie die Manifestzählung aktualisieren. Ignorierte lokale Laufzeitdateien und externe Bestände liegen außerhalb dieses Git-Katalogs.

Der aktuelle Obsidian-Vault liegt außerhalb des Repos unter `/Users/frnkhrz/PEAK_TRADE_SYSTEM_AKTUELL`. Die Projektion aktualisiert seine Einstiege, die beiden Hauptkarten und die Quellenansichten; vorhandene Bereichsdossiers und ihre datierten Nachweise bleiben erhalten. Originale Bindungswerte werden nicht zu neuen Laufzeitnachweisen umgeschrieben. Der Abgleichbeleg im Vault bindet Quellen und Ansichten per SHA256:

```text
./scripts/pt docs/system_atlas/obsidian_projection.py plan
./scripts/pt docs/system_atlas/obsidian_projection.py apply
./scripts/pt docs/system_atlas/obsidian_projection.py check
```

`plan` und `check` lesen ausschließlich. `apply` schreibt den bestehenden Vault und seinen Abgleichbeleg, erstellt jedoch keine Sicherung und verändert weder den Freeze-Tag noch Produktquellen. Quellen und Markdownansichten sind bytegebunden. Bei Canvas-Dateien wird zusätzlich der vollständige JSON-Inhalt gebunden: Obsidian darf die Serialisierung ändern; solche Formatänderungen werden gesondert ausgegeben. Der angezeigte Dokumentationscommit bezeichnet die letzte Änderung der gespiegelten Repo-Dokumente. Die Prüfung belegt die dokumentierten Quellenbindungen, keine vollständige fachliche oder betriebliche Abnahme des Vault-Inhalts.

Der Test `test_atlas_loads_and_validates` in der [Atlas-Testdatei](../../tests/ops/test_system_atlas_v1.py) prüft das aktuelle Atlasmodell mit `current_atlas.py`. Die archivierten YAML-Verträge in derselben Testdatei können mit `PEAKTRADE_LEGACY_ATLAS_REPO_ROOT` gegen einen vollständigen historischen Checkout geprüft werden. Die Tests lesen dessen Census, Katalog und generierte Ansichten direkt aus dem angegebenen Bestand.

## Gebundene Weiterentwicklung nach dem Freeze

Der Katalog bleibt eine Ansicht des unveränderten Freeze-Commits. Spätere Produktänderungen werden im separaten [Entwicklungsbeleg](source/development-binding-v1.json) mit ursprünglichem und aktuellem SHA256 pro Datei gebunden. Die normale Prüfung akzeptiert nur dieses konkrete Delta und meldet seine Größe sowie veränderte Produktquellen ausdrücklich. Nicht gebundene oder nachträglich veränderte Produktdateien bleiben Fehler. Der Beleg erzeugt keine fachliche oder betriebliche Freigabe und macht den alten Katalog nicht zu einem neuen Gesamtkatalog.

Die erste gebundene Änderung ist der [N1-Post-Close-Fortsetzungsanschluss](../ops/specs/PRODUCTIVE_N1_POST_CLOSE_CONTINUATION_V1.md). Seine Abnahme und offenen Grenzen stehen im [Umsetzungsbeleg](../ops/evidence/PRODUCTIVE_N1_POST_CLOSE_CONTINUATION_2026_11_06.md). Die Freeze-Tags, ihr ursprünglicher Dateikatalog und die strikte Prüfung mit dem Modus frozen bleiben unverändert.

Der vollständige Freeze umfasst den bereinigten Quellstand und die nachgeführten Dokumentationsansichten. Sein Tag ist oben gesondert benannt. Den exakten Arbeitsbaum, die Grenze der lokal vorhandenen Commit-Vorgeschichte und die einzige nicht versionierte Betriebsabhängigkeit `.venv&#47;` prüft:

```text
PYTHONDONTWRITEBYTECODE=1 ./scripts/pt docs/system_atlas/current_atlas.py frozen
```

Diese Prüfung ist absichtlich strikt: zusätzliche lokale Dateien oder spätere Änderungen am eingefrorenen Arbeitsbaum werden gemeldet. Leere Ausgabeverzeichnisse für die vorhandenen Writer enthalten keine Archivdaten und bleiben als Betriebsadressen erhalten. Der Dateikatalog des Atlas bindet den Quell-Fixpunkt; der vollständige System-Tag bindet zusätzlich die aktuellen Ansichten über seinen Git-Baum.

## Formatprüfung und eingefrorene Bytes

Die CI-Formatprüfung verwendet [den Formatverifier](../../scripts/ci/check_ruff_frozen_format_v1.py). Er prüft 31 [exakt benannte Originaldateien](../../scripts/ci/ruff_frozen_format_exceptions_v1.json) gegen ihre unveränderten Frozen-Gitobjekte und die aktuellen Dateibytes. Damit bleiben die bestehenden Master-V2-, Policy- und Whole-File-Seal-Verträge gültig. Eine Änderung an einer dieser Dateien ist ein Fehler, auch bei nachgeführtem Manifestdigest. Zusätzliche Ausnahmen sind nicht zulässig.

Alle übrigen Pythondateien in src, tests und scripts durchlaufen weiterhin die Ruff-Formatprüfung. Die separate Ruff-Fehlerprüfung konsumiert den gesamten ursprünglichen Suchumfang einschließlich der 31 bytegeschützten Dateien. Die [CI-Korrektur](../ops/evidence/PR_7180_CI_GATE_REPAIR_2026_11_06.md) hält Formatänderungen, negative Prüfungen und den belegten Main-Abgleich der Linkschulden fest.
