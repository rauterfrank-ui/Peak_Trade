# Local Docker Desktop Preflight

## Zweck
Read-only Preflight-Checks vor einem lokalen Docker-Desktop-Start. Keine Änderungen, keine Runtime-Aktionen.

## Verwendung
```bash
./scripts/ops/docker_desktop_preflight_readonly.sh
```

## Geprüfte Aspekte
1. **Docker.raw** – Pfad und Größe (`~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw`)
2. **Settings** – AutoStart, relevante Keys in `settings-store.json`
3. **Compose-Inventar** – vorhandene Compose-Dateien unter `~` (maxdepth 5)
4. **Verzeichnisgrößen** – `~/.docker`, `com.docker.docker`, `group.com.docker`

## Ausgabe
- Read-only: keine Änderungen am System
- Hinweise bei großer Docker.raw (> 100GB)
- Verweis auf [local_docker_safe_start_guardrails.md](local_docker_safe_start_guardrails.md)

## Abhängigkeiten
- Keine Docker-Runtime erforderlich
- Kein Netzwerkzugriff
- Nur lokale Dateisystem-Leserechte
