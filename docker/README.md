# Peak_Trade – Docker (local)

## Start
```bash
docker compose -f docker/compose.yml up -d --build
```

## UI
http://localhost:5001

## Stop
```bash
docker compose -f docker/compose.yml down
```

## Reset (löscht MLflow DB + Artifacts)
```bash
docker compose -f docker/compose.yml down -v
```
