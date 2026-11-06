# PeakTrade System Atlas

```text
ATLAS_AUTHORITY=NONE
ATLAS_ROLE=CURRENT_FROZEN_SYSTEM_DESCRIPTION
RUNTIME_AUTHORIZATION_EFFECT=NONE
CURRENT_ONLY=true
SOURCE_TAG=freeze/visible-system-2026-11-06-v2
SOURCE_COMMIT=a8e1c0088e25651ad4bb29ebe02e10142a0a92b2
```

Der [System Atlas](generated/SYSTEM_ATLAS.md) beschreibt diesen fixierten Quellbaum mit Fachräumen, inneren Modulen, Eingängen, Verarbeitung, Ausgängen, Zustand und Consumergrenzen. Der [Quellenindex](generated/SOURCE_INDEX.md) erschließt alle Dateien des Fixpunkts.

Der Dateikatalog bezeichnet den unveränderten Freeze-Baum. Die aktuelle Dokumentationsprojektion ersetzt die Runbook-, Map- und Atlasdarstellung; ihre Dokumentbytes und Atlaswerkzeuge sind deshalb ausdrücklich von den fixierten Produktquellen getrennt. Der Freeze-Tag bleibt an seinem Commit.

Der [Abgrenzungsbeleg](source/successor-disposition.json) unterscheidet den aktuellen Arbeitsbestand, die benötigte `origin/main`-Vergleichsquelle und extern archivierte Bestände. Die 42 lokalen Worktrees wurden als historische Arbeitskopien ausgelagert; kein Worktree-Inhalt wurde integriert. 82 historische Repo-Dateien einschließlich Backup-Paketen und eines datierten Wiederherstellungsprüfers sind im Bereinigungsregister mit Transferdigests gebunden. Die Atlasprüfung braucht zum Prüfen dieser Belege kein angeschlossenes Archivlaufwerk.

Der historische Wiederherstellungsprüfer war am aktuellen Baum bereits vor seiner Auslagerung mit `CURRENT_CORPUS_PARITY_DRIFT` am N-Bars-Supplier fehlgeschlagen. Er und sein damaliges Eingabepaket bilden eine archivierte, datierte Prüfeinheit. Dieser Befund wird nicht in einen heutigen PASS umgedeutet. Produktimplementierungen, aktuelle Corpus-/Researchinputs und gespeicherte Runtimezustände werden dadurch nicht aus historischen Worktrees ersetzt.

Die [Law Impact Map](../governance/current_law_impact_map_v1/generated/LAW_CHANGE_IMPACT.md) ergänzt diesen Atlas um Originalregelquellen und den [Policy-Katalog](source/current-policies.jsonl.gz). Zusätzliche Kartenansichten sind gemäß [Bereinigungsregister](source/documentation-cleanup.json) entfernt und ihre Erzeugung ist gesperrt. Ein bereits konsumiertes maschinelles Quellenobjekt bleibt als Eingabevertrag für seine bestehenden Codeconsumer erhalten; daraus entsteht keine zusätzliche aktuelle Kartenansicht. Der Katalog belegt Referenzstellen, keine vollständige fachliche Wirksamkeit aller Policies.

Die Grundlage ist [current-model.json](source/current-model.json) mit den vollständigen Datei-, Python-Definitions- und Importkatalogen unter [source](source/). Das [Master Runbook](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) ist die primäre Betriebs-/Entwicklungsorientierung. Der Atlas schafft keine zusätzliche Fach-, Apply- oder Ausführungsauthority.

Erzeugen und prüfen, aus dem Repository-Stamm:

```text
./scripts/pt scripts/ops/generate_system_atlas_v1.py
./scripts/pt scripts/ops/validate_system_atlas_v1.py
./scripts/pt scripts/ops/check_system_atlas_impact_v1.py
```

Diese Einstiegspunkte verwenden für dieses Atlasmodell `current_atlas.py`. Die Prüfung kontrolliert Quellstand, vollständige Dateimenge, Quelldigests, Literalverträge, Dokumentlinks und deterministische Ausgabe. Sie weist ausgeführte Laufzeitwirkung nicht aus.

Der aktuelle Obsidian-Vault liegt außerhalb des Repos unter `/Users/frnkhrz/PEAK_TRADE_SYSTEM_AKTUELL`. Die Projektion aktualisiert seine Einstiege, die beiden Hauptkarten und die Quellenansichten; vorhandene Bereichsdossiers und ihre datierten Nachweise bleiben erhalten. Originale Bindungswerte werden nicht zu neuen Laufzeitnachweisen umgeschrieben. Der Abgleichbeleg im Vault bindet Quellen und Ansichten per SHA256:

```text
./scripts/pt docs/system_atlas/obsidian_projection.py plan
./scripts/pt docs/system_atlas/obsidian_projection.py apply
./scripts/pt docs/system_atlas/obsidian_projection.py check
```

`plan` und `check` lesen ausschließlich. `apply` schreibt den bestehenden Vault und seinen Abgleichbeleg, erstellt jedoch keine Sicherung und verändert weder den Freeze-Tag noch Produktquellen. Quellen und Markdownansichten sind bytegebunden. Bei Canvas-Dateien wird zusätzlich der vollständige JSON-Inhalt gebunden: Obsidian darf die Serialisierung ändern; solche Formatänderungen werden gesondert ausgegeben. Der angezeigte Dokumentationscommit bezeichnet die letzte Änderung der gespiegelten Repo-Dokumente. Die Prüfung belegt die dokumentierten Quellenbindungen, keine vollständige fachliche oder betriebliche Abnahme des Vault-Inhalts.

Die direkte Bibliothek `scripts.ops.system_atlas_v1.load_v1` erwartet weiterhin einen YAML-Atlas. Der eingefrorene Test `test_atlas_loads_and_validates` in der [Atlas-Testdatei](../../tests/ops/test_system_atlas_v1.py) ruft diese Bibliothek auf und scheitert am fehlenden Census-Eintrag:

```text
ATLAS_SOURCE_MISSING:census/census_meta.yaml
```

Die aktuellen CLI-Prüfungen ersetzen keine erfolgreiche Ausführung dieser Testbindung. Die Testdateien und die YAML-Bibliothek gehören zum unveränderten Quellstand.
