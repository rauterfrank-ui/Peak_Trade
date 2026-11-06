# Local Docker Manual Cleanup Options

## Zweck
Optionale manuelle Aufräum-Hinweise für lokalen Docker-Desktop-Zustand. Keine automatischen Maßnahmen.

## Voraussetzung
- Siehe [local_docker_safe_start_guardrails.md](local_docker_safe_start_guardrails.md)
- Nur nach expliziter Entscheidung ausführen
- Keine Auswirkung auf AWS-/GitHub-Evidence-Pfade

## Optionale manuelle Schritte

### 1. Ungenutzte Images/Container/Volumes prüfen
```bash
docker system df
```

### 2. Ungenutzte Ressourcen bereinigen (manuell)
```bash
docker system prune -a   # Images, Container, Networks
docker volume prune     # Ungenutzte Volumes
```
**Hinweis:** Nur ausführen, wenn keine laufenden Paper-Tests oder benötigten Daten betroffen sind.

### 3. Docker.raw-Größe reduzieren
- Docker Desktop → Settings → Resources → Disk image size
- Oder: Factory Reset (verlustreich, alle lokalen Daten weg)

### 4. Logs prüfen
```bash
du -sh ~/Library/Containers/com.docker.docker
du -sh ~/.docker
```

## Nicht zulässig (automatisch)
- Kein automatisches `docker system prune`
- Kein automatisches Löschen/Verschieben von `Docker.raw`
- Kein automatischer Docker-Desktop-Start
