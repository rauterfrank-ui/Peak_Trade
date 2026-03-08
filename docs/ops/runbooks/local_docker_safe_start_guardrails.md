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
