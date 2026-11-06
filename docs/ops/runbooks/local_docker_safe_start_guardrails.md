# Local Docker Safe Start Guardrails

## Befund
- Repo-Compose ist aktuell nicht der wahrscheinliche Auslöser einer lokalen Datenwelle.
- Keine `restart:`-Policies in den gesichteten Repo-Compose-Dateien.
- Keine `profiles:`-Einträge in den gesichteten Repo-Compose-Dateien.
- `scripts/obs/up.sh` verweist auf ein nicht vorhandenes Verzeichnis und ist aktuell nicht belastbar.

## Wahrscheinliche Ursachen außerhalb des Repos
- ältere Docker-Desktop-Container/Stacks
- externe Compose-Projekte im Home-Verzeichnis
- wiederhergestellte lokale Altlasten
- große lokale Volumes/Logs

## Schutzprinzip
- Docker nicht blind starten
- zuerst externe Compose-Dateien inventarisieren
- schwere Services markieren
- erst danach gezielte lokale Safe-Start-Mechanik definieren

## Repo-spezifische Folgearbeiten
- defektes `scripts/obs/up.sh` entweder korrigieren oder klar als veraltet markieren
- optional später:
  - Compose-Profile
  - Safe-Override
  - log rotation
  - kleine lokale Retention


## Verifizierter Hauptbefund
- Die lokale Datenwelle ist aktuell nicht auf Peak_Trade-Compose zurückzuführen.
- Es wurden keine externen Compose-Dateien außerhalb des Repos als Ursache identifiziert.
- Der dominante lokale Speicherfresser ist Docker Desktop selbst:
  - Pfad: `~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw`
  - Größe: `460 GB`
- Solange Docker Desktop diesen Zustand wiederverwendet, bleibt das Risiko für lokale Speicher- und Datenwellen bestehen.

## Operative Folgerung
- AWS-/GitHub-basierte Paper-Tests und Evidence-Aufbau bleiben von diesem lokalen Befund getrennt.
- Lokaler Docker-Zustand ist als separater Altlasten-/Desktop-VM-Fall zu behandeln.
- Keine automatisierten Cleanup-Aktionen ausführen.
- Kein ungeprüfter Docker-Desktop-Start im aktuellen Zustand.

## Zulässige nächste Schritte
1. Nur Dokumentation und Preflight-Checks ergänzen
2. Optionale manuelle Aufräum-Hinweise separat dokumentieren
3. Erst nach expliziter Entscheidung eine lokale Docker-Reset-/Cleanup-Strategie verfolgen

## Nicht zulässige automatische Maßnahmen
- kein `docker system prune`
- kein automatisches Löschen/Verschieben von `Docker.raw`
- kein automatischer Docker-Desktop-Start
- keine Änderungen, die AWS-/GitHub-Evidence-Pfade tangieren
