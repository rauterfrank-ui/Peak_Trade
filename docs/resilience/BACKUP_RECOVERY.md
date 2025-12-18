# Backup & Recovery

## Überblick

Das Backup-System sichert automatisch Portfolio-States, Trading-History, Konfigurationen und gelernte Patterns. Ermöglicht schnelle Wiederherstellung nach Problemen.

## Features

- **Automatische Backups**: Scheduled und on-demand
- **Versionierung**: Alle Backups mit Timestamps
- **Kompression**: Optional GZIP für kleinere Backups
- **Retention-Policies**: Automatisches Cleanup alter Backups
- **CLI-Commands**: Einfache Bedienung
- **Lokale Backups**: Mit S3-Vorbereitung

## Verwendung

### CLI

```bash
# Backup erstellen
make backup
python src/infra/backup/__main__.py create

# Backups auflisten
make backup-list
python src/infra/backup/__main__.py list

# Neuestes Backup wiederherstellen
make restore
python src/infra/backup/__main__.py restore

# Spezifisches Backup wiederherstellen
python src/infra/backup/__main__.py restore manual_20251217_214030

# Backup löschen
python src/infra/backup/__main__.py delete manual_20251217_214030
```

### Programmatisch

```python
from src.infra.backup import BackupManager, BackupConfig

# Backup Manager erstellen
config = BackupConfig(
    backup_path="./backups",
    compress=True,
    retention_days=30,
)
manager = BackupManager(config)

# Backup erstellen
data = {
    "portfolio": {
        "positions": [...],
        "equity": 10000,
    },
    "config": {
        "strategy": "ma_crossover",
        "risk_per_trade": 0.01,
    },
}
backup_id = manager.create_backup(data, backup_type="manual")
print(f"Backup created: {backup_id}")

# Backups auflisten
backups = manager.list_backups()
for backup in backups:
    print(f"{backup.backup_id}: {backup.size_bytes} bytes")

# Backup laden
data = manager.load_backup(backup_id)
portfolio = data["portfolio"]
```

## Backup-Types

1. **Manual**: Manuell erstellte Backups
2. **Automatic**: Automatisch nach Schedule
3. **Pre-Trade**: Vor wichtigen Trades
4. **Scheduled**: Tägliche/wöchentliche Backups

## Was wird gesichert?

### Portfolio-States

```python
portfolio_state = {
    "timestamp": datetime.now().isoformat(),
    "equity": 10000.0,
    "positions": [
        {
            "symbol": "BTC/USD",
            "size": 0.1,
            "entry_price": 50000,
        }
    ],
    "cash": 5000.0,
}

manager.create_backup(
    {"portfolio": portfolio_state},
    backup_type="pre_trade"
)
```

### Trading-History

```python
trading_history = {
    "trades": [
        {
            "timestamp": "2025-12-17T10:00:00",
            "symbol": "BTC/USD",
            "side": "buy",
            "size": 0.1,
            "price": 50000,
        }
    ],
    "performance": {
        "total_return": 0.15,
        "sharpe_ratio": 1.8,
    },
}

manager.create_backup(
    {"history": trading_history},
    backup_type="automatic"
)
```

### Konfigurationen

```python
config_backup = {
    "strategy_config": {
        "name": "ma_crossover",
        "fast_period": 10,
        "slow_period": 30,
    },
    "risk_config": {
        "risk_per_trade": 0.01,
        "max_positions": 2,
    },
}

manager.create_backup(
    {"config": config_backup},
    backup_type="manual"
)
```

### Learned Patterns

```python
learned_data = {
    "patterns": {
        "successful_setups": [...],
        "failed_setups": [...],
    },
    "statistics": {
        "win_rate": 0.65,
        "avg_return": 0.02,
    },
}

manager.create_backup(
    {"learned": learned_data},
    backup_type="automatic"
)
```

## Recovery

### Automatic Recovery

```python
from src.infra.backup import RecoveryManager

recovery = RecoveryManager()

# Neuestes Backup wiederherstellen
data = recovery.restore_latest_backup()
portfolio = data["portfolio"]

# Spezifisches Backup wiederherstellen
data = recovery.restore_backup("manual_20251217_214030")
```

### Verify Backup

```python
recovery = RecoveryManager()

# Backup verifizieren
is_valid = recovery.verify_backup("manual_20251217_214030")
if is_valid:
    print("Backup is valid")
else:
    print("Backup is corrupted")
```

### Rollback nach Fehler

```python
from src.infra.backup import RecoveryManager

def risky_operation():
    try:
        # Backup vor Operation
        manager = BackupManager()
        backup_id = manager.create_backup(
            {"portfolio": current_portfolio_state()},
            backup_type="pre_trade"
        )
        
        # Riskante Operation
        execute_trade()
        
    except Exception as e:
        # Bei Fehler: Rollback
        recovery = RecoveryManager()
        data = recovery.restore_backup(backup_id)
        restore_portfolio_state(data["portfolio"])
        raise
```

## Konfiguration

In `config.toml`:

```toml
[backup]
enabled = true
interval_hours = 24
retention_days = 30
backup_path = "./backups"
compress = true
```

### Config laden

```python
from src.core import load_config
from src.infra.backup import BackupConfig, BackupManager

cfg = load_config()

if hasattr(cfg, "backup"):
    backup_config = BackupConfig(
        backup_path=cfg.backup.backup_path,
        compress=cfg.backup.compress,
        retention_days=cfg.backup.retention_days,
    )
    manager = BackupManager(backup_config)
```

## Scheduled Backups

```python
import schedule
import time
from src.infra.backup import BackupManager

manager = BackupManager()

def create_scheduled_backup():
    data = collect_current_state()
    backup_id = manager.create_backup(data, backup_type="scheduled")
    print(f"Scheduled backup created: {backup_id}")

# Tägliches Backup um 2 Uhr nachts
schedule.every().day.at("02:00").do(create_scheduled_backup)

while True:
    schedule.run_pending()
    time.sleep(3600)  # Check every hour
```

## Retention-Policies

Alte Backups werden automatisch gelöscht basierend auf `retention_days`:

```python
config = BackupConfig(
    retention_days=30,  # Backups älter als 30 Tage löschen
)
manager = BackupManager(config)

# Cleanup wird automatisch bei jedem create_backup() aufgerufen
manager.create_backup(data)
```

### Manuelles Cleanup

```python
manager = BackupManager()

# Lösche alle Backups älter als 7 Tage
from datetime import datetime, timedelta
cutoff = datetime.now() - timedelta(days=7)

for backup in manager.list_backups():
    if backup.timestamp < cutoff:
        manager.delete_backup(backup.backup_id)
        print(f"Deleted old backup: {backup.backup_id}")
```

## Backup-Metadaten

```python
manager = BackupManager()
backups = manager.list_backups()

for backup in backups:
    print(f"ID: {backup.backup_id}")
    print(f"Type: {backup.backup_type}")
    print(f"Time: {backup.timestamp}")
    print(f"Size: {backup.size_bytes / 1024:.1f} KB")
    print(f"Compressed: {backup.compressed}")
    print(f"Files: {backup.files}")
    print()
```

## S3-Vorbereitung

Lokale Backups können später zu S3 hochgeladen werden:

```python
import boto3
from pathlib import Path

def upload_to_s3(backup_id: str):
    s3 = boto3.client("s3")
    bucket = "peak-trade-backups"
    
    backup_dir = Path(f"./backups/{backup_id}")
    for file_path in backup_dir.glob("*"):
        s3_key = f"{backup_id}/{file_path.name}"
        s3.upload_file(str(file_path), bucket, s3_key)
    
    print(f"Uploaded {backup_id} to S3")

# Nach Backup-Erstellung
manager = BackupManager()
backup_id = manager.create_backup(data)
upload_to_s3(backup_id)
```

## Best Practices

1. **Regelmäßige Backups**: Täglich oder vor wichtigen Operationen
2. **Verifizierung**: Teste Backups regelmäßig
3. **Retention**: 30 Tage Minimum, 90 Tage für Production
4. **Kompression**: Aktiviere für große Backups
5. **Off-Site**: Lade kritische Backups zu S3 hoch

### Backup-Strategy

- **Pre-Trade**: Vor jedem wichtigen Trade
- **Daily**: Täglich um 2 Uhr nachts
- **Weekly**: Sonntags Full-Backup
- **Manual**: Vor großen Code-Changes

## Troubleshooting

### Backup fehlgeschlagen

```python
try:
    manager.create_backup(data)
except Exception as e:
    logger.error(f"Backup failed: {e}")
    # Fallback: Speichere in temporärem Ordner
```

### Wiederherstellung fehlgeschlagen

```python
from src.infra.backup import RecoveryError

try:
    data = recovery.restore_backup(backup_id)
except RecoveryError as e:
    logger.error(f"Recovery failed: {e}")
    # Versuche älteres Backup
    backup_id = recovery.get_latest_backup()
    data = recovery.restore_backup(backup_id)
```

### Disk-Space voll

- Prüfe `retention_days` und verringere
- Lösche alte Backups manuell
- Aktiviere Kompression

## Siehe auch

- [Health Checks](HEALTH_CHECKS.md)
- [Monitoring](MONITORING.md)
- [Circuit Breaker](CIRCUIT_BREAKER.md)
