# IU SL und OPT Dokumentationscheckpoint

Stand 5. November 2026. Dieser lokale Checkpoint sichert die korrigierten architektonischen Außenkanten und den anschließenden Verständnisabgleich. Er enthält keine Produktänderung, keine vollständige fachliche Abnahme und keine Betriebsfreigabe.

## Einstieg

[Zusammenhängendes Konstrukt](notes/36_Konstrukt%20von%20IU%20SL%20und%20OPT.md)

Die sechs neuen Kapitel erläutern Ursprung und Varianten, innere Aufgaben, Zustände, Rückkopplungen, Datenbedeutung, die drei Integrationscommits und die verbleibenden Verständnisfragen. Die Außenkantendefinitionen und ihre Portnotizen sind mitgesichert. Leserfassungen unter `notes/` lösen die eingeschlossenen Obsidianlinks auf. Weiterführende lokale Vaultverweise bleiben ausdrücklich lokale Navigation.

## Herkunft und Quellstand

Der untersuchte Git-Stand ist `10d899b16356974bdd1f3c90f13681825cc09afe` auf `feat/ghv-current-exchange-reconciliation-pr-integration-v1` mit der vorhandenen lokalen Arbeit. Die drei bestehenden Teilimplementierungen `3aa3ad751`, `4d312c378` und `10d899b16` bleiben Prüfkandidaten. Dieser Commit macht sie weder zu einer freigegebenen Zielarchitektur noch zu einem natürlichen Lernkreislauf.

Unveränderte geprüfte Quellen sind an Gitblobs dieses Ausgangscommits gebunden. Abweichende Arbeitskopien sind als **inert gespeicherte UTF-8-Quelltexte in JSON** enthalten. Sie werden nicht als Produktdateien übernommen und vom Prüfer nicht importiert. Die früheren 135 geänderten beziehungsweise untracked Dateien bleiben außerhalb des Commits erhalten.

`vault_exact/` und `evidence/` bewahren die Originaltexte mit ihrem ursprünglichen Bytehash. JSONhüllen erhalten auch historische Zeilenenden und Leerzeichen; die Leserfassungen sind gesonderte Projektionen. Die vollständige ursprüngliche Repository-Hashliste wird aus kleinen JSONteilen exakt rekonstruiert. Vier Original-PDFs und die ausgewählten historischen Requesttexte sind enthalten; ganze Gesprächsprotokolle oder Kontodaten werden nicht übernommen.

## Prüfung

Lesender Aufruf aus dem Repository:

```sh
./scripts/pt docs/ops/evidence/iu_sl_opt_understanding_checkpoint_2026_11_05/verify_checkpoint.py
```

Der Prüfer bindet Paketbytes, Originaltexte, PDFhashes, die ursprüngliche Repositorybaseline und die Quellen/Funktionsanker an ihre tatsächlichen Bytes. Er importiert keine Produktmodule und führt keine Produkttests aus. Der erhaltene Dokumentcheck stammt vom Abgleich vor diesem Commit. Seine damalige HEAD- und Bestandserhaltung bleibt datiert; sie wird nicht auf den neuen HEAD umgedeutet.

## Weiterer Arbeitsumfang

Weiterhin zuerst das Konstrukt verstehen: eigenständige Markt-/Outcomemessung, tatsächlicher Learningconsumer, numerische Forschungsfrage und Repräsentationsrückkopplung. Fehlende Verträge, Implementierungsanschlüsse und Laufzeitbelege bleiben getrennt. Kein neuer Modellbau, Training, Apply, Tradinglauf, Push oder Veröffentlichung folgt aus diesem Checkpoint.
