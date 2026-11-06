# Erhaltener Architekturbestand und aktueller Abgleich — 04.11.2026

Dieses Paket gehört zum bestehenden System-Rekonfigurations-Blueprint, Abschnitt 35. Es ist Quellen-/Untersuchungsevidence ohne Betriebsautorität und ohne neue Universe-Taxonomie. Historische Anweisungen bleiben inerte Quellen. Die Dateien sind keine Runtime-Konfiguration.

## Inhalt und Reichweite

- 99 unveränderte Hauptberichte aus dem vorhandenen Blueprint-Anhang B, erneut gegen alle dort verzeichneten SHA256-Werte geprüft.
- 44 unveränderte CON-Befundblöcke aus dem bisherigen Anhang A.
- Zwölf frühere SL01–SL12-Codefassungen mit zwölf History-Records; direkter Abgleich gegen genaue lokale Git-Revision/Pfad-Objekte in historical_git_verification.json.
- Neun vorhandene Vault-Navigations-/Registerdateien als datierte Text-Snapshots. Originale bleiben unverändert.
- Zeilengenaues Inventar der 2.212 ID-Zeilen im erhaltenen Vertrags-/Kanten-/Zustandsregister. Das sind keine 2.212 abgeschlossenen Kausalketten.
- alignment.json: 32 konkrete Rollen-/Übergangsbefunde mit heutigen Symbol-/Quellhashankern, getrennten Beleggraden und verbleibenden Nachweisen; sechs vertiefte semantische Übergangsbeschreibungen und der nachgewiesene SL10-Zwischenbinder.
- integration_tests.xml: 204 bestandene vorhandene lokale Tests. intermediate_tests.xml: weitere 38 bestanden, neun fehlgeschlagen. Insgesamt 242 bestanden, neun fehlgeschlagen; G2-Ursache in g2_failure_diagnosis.json. Kein Gesamt-PASS und keine natürliche Dauerlaufwirkung.

Alle verlinkten Originalunterlagen sind nicht transitiv archiviert: Unterberichte, Anhänge, vollständige Originalchats, PR-Dateien und weitere Recovery-Inhalte müssen bei Bedarf aus ihrer Provenienz erneut geöffnet werden. Lokale Git-Historie ist shallow; verfügbare genaue Objekte beweisen nicht den globalen Ursprung. Absolute Originalpfade bleiben als Provenienz erhalten, sind zum Lesen der hier kopierten Haupttexte nicht erforderlich.

## Leseregel

Ein fehlender direkter Producer-/Consumer-Anschluss ist zuerst eine Untersuchungsfrage. Adapter, Aggregation, Zustände, Zeitversätze und alternative Pfade müssen vor jedem Umbau verfolgt werden. Originale Absicht, Varianten, heutige Implementierung und gewünschte Endfassung bleiben getrennt. Rohgröße, Zustand, Bewertung, Abweichung, Meta-Aussage, Forschungssignal, Änderungsvorschlag und Consumer-Wirkung dürfen nicht durch gleiche Feldnamen zusammengezogen werden. Das Prüfraster ist keine behauptete historische Layerzahl.

Der gesamte vorhandene Vertragsbestand bleibt zur Prüfung erhalten; seine alten PARTIAL/PROVEN/COMPLETE-Labels werden nicht als neue Prüfung übernommen. Symbolpräsenz ist als solche markiert. Die vollständige Rekonstruktion und Bewertung jeder Kette ist offen.

## Wiederholbare Integritätsprüfung

Vom tatsächlichen Checkout mit dem kanonischen Launcher:

```sh
./scripts/pt scripts/ops/verify_architecture_reconstruction_alignment_v1.py
```

Der Prüfer liest keine Zugangsdaten, fragt keinen Dienst ab und importiert keine Produktmodule. Er bestätigt archivierte Bytes, vorhandene Inventarzeilen und unveränderte aktuelle Codeanker. Bei späteren Codeänderungen verlangt er erneuten Abgleich. Ein PASS ist kein Nachweis kausaler/semantischer Vollständigkeit; die Ausgabe hält die Rekonstruktion ausdrücklich INCOMPLETE.

Führende Arbeitsdarstellung bleibt [Blueprint Abschnitt 35](../../blueprints/PEAKTRADE_SYSTEM_RECONFIGURATION_BLUEPRINT_2026_11_03.md). Operative Bedeutung und Grenzen verbleiben beim [Master Runbook](../../../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md), tatsächlichem Code, Config und passenden Laufzeitbelegen.

Die lokale .gitattributes erhält für historische Textkopien und originale XML-Testausgaben deren exakte Bytes einschließlich ursprünglicher Leerzeichen/Zeilenenden. Produktcode und seine Prüfregeln sind davon nicht betroffen; die Quellenhashprüfung bleibt verpflichtend.
