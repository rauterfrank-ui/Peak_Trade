# Health Checks Documentation

## Überblick

Das Health-Check-System überwacht kontinuierlich alle kritischen Komponenten von Peak_Trade und zeigt den Systemzustand in einem Ampel-System (GREEN/YELLOW/RED) an.

## Features

- **Ampel-System**: GREEN (OK), YELLOW (Warnung), RED (Kritisch)
- **Modulare Checks**: Backtest, Exchange, Portfolio, Risk, Live
- **CLI & JSON Output**: Für Menschen und Maschinen lesbar
- **Async/Await**: Performance-optimiert
- **Detaillierte Fehlerberichte**: Mit Timestamps und Details

## Verwendung

### CLI

```bash
# Alle Checks ausführen
make health-check

# Oder direkt:
python -m src.infra.health.health_checker

# JSON-Output für Monitoring-Tools
make health-check-json
python -m src.infra.health.health_checker --json

# Spezifische Checks
python -m src.infra.health.health_checker backtest exchange
```

### Programmatisch

```python
import asyncio
from src.infra.health import HealthChecker

async def main():
    checker = HealthChecker()
    results = await checker.run_all_checks()
    
    for name, result in results.items():
        print(f"{name}: {result.status} - {result.message}")

asyncio.run(main())
```

## Health Checks

### 1. Backtest Check

Prüft die Verfügbarkeit der Backtest-Engine:
- ✓ Backtest-Module importierbar
- ✓ Config geladen
- ✓ Results-Directory existiert

**Status:**
- GREEN: Alles OK
- YELLOW: Config-Probleme
- RED: Module nicht verfügbar

### 2. Exchange Check

Prüft Exchange-Verbindungen (Kraken, Binance, Coinbase):
- ✓ CCXT Library verfügbar
- ✓ Exchange-Module importierbar
- ✓ Unterstützte Exchanges verfügbar

**Status:**
- GREEN: Alle Exchanges verfügbar
- YELLOW: Einige Exchanges fehlen
- RED: CCXT nicht verfügbar

### 3. Portfolio Check

Prüft Portfolio-Management:
- ✓ Portfolio-Module importierbar
- ✓ Config geladen
- ✓ Risk-Module verfügbar

**Status:**
- GREEN: Alles OK
- YELLOW: Config-Probleme
- RED: Module nicht verfügbar

### 4. Risk Check

Prüft Risk-Management und validiert Risk-Parameter:
- ✓ Risk-Module importierbar
- ✓ Config geladen
- ✓ Risk-Parameter validiert

**Warnungen:**
- `risk_per_trade > 2%`: Hohes Risiko
- `max_position_size > 50%`: Hohe Konzentration
- `max_daily_loss > 5%`: Hohes Risiko

**Status:**
- GREEN: Alles OK
- YELLOW: Parameter-Warnungen
- RED: Module nicht verfügbar

### 5. Live Check

Prüft Live-Trading Safety-Settings:
- ✓ Live-Module importierbar (optional)
- ✓ Environment-Settings geprüft
- ✓ Safety-Gates aktiv

**Status:**
- GREEN: Safe Configuration
- YELLOW: Live-Module nicht verfügbar (expected)
- RED: Live-Trading enabled ohne Safety

## Eigene Health-Checks

```python
from src.infra.health.checks import BaseHealthCheck, HealthStatus

class CustomCheck(BaseHealthCheck):
    def __init__(self):
        super().__init__("custom")
    
    async def check(self):
        try:
            # Deine Prüflogik
            result = await some_check()
            
            return self._create_result(
                status=HealthStatus.GREEN,
                message="Check passed",
                details={"info": result}
            )
        except Exception as e:
            return self._create_result(
                status=HealthStatus.RED,
                message="Check failed",
                error=str(e)
            )

# Verwende Custom Check
from src.infra.health import HealthChecker

checker = HealthChecker()
checker.checks["custom"] = CustomCheck()
results = await checker.run_all_checks()
```

## Integration mit Monitoring

### JSON-Output für Dashboards

```bash
# Output als JSON speichern
python -m src.infra.health.health_checker --json > health_status.json

# In Monitoring-System einlesen
cat health_status.json | jq '.overall_status'
```

### Alerts bei Fehlern

```python
from src.infra.health import HealthChecker
from src.infra.monitoring import get_alert_manager, AlertLevel

checker = HealthChecker()
results = await checker.run_all_checks()

alert_manager = get_alert_manager()
overall = checker.get_overall_status(results)

if overall == "red":
    alert_manager._trigger_alert(Alert(
        level=AlertLevel.CRITICAL,
        message="Health check failed",
        timestamp=datetime.now(),
        source="health_checker"
    ))
```

## Konfiguration

In `config.toml`:

```toml
[health_checks]
enabled = true
interval_seconds = 60
alert_on_failure = true
checks = ["backtest", "exchange", "portfolio", "risk", "live"]
```

## Best Practices

1. **Regelmäßige Checks**: Führe Health-Checks vor wichtigen Operationen aus
2. **CI/CD Integration**: Integriere in Build-Pipeline
3. **Monitoring**: Sende Results an Monitoring-System
4. **Alerts**: Konfiguriere Alerts für kritische Fehler
5. **Custom Checks**: Erstelle eigene Checks für spezifische Komponenten

## Troubleshooting

### Check schlägt fehl

1. Prüfe Details in der Ausgabe
2. Validiere Konfiguration
3. Prüfe Dependencies
4. Schaue in Logs

### Exchange Check YELLOW

- Coinbase Pro nicht verfügbar → Normal, wenn nicht installiert
- Prüfe CCXT Version: `pip show ccxt`

### Risk Check YELLOW

- Risk-Parameter zu hoch
- Passe in `config.toml` an:
  ```toml
  [risk]
  risk_per_trade = 0.01  # Max 2%
  max_position_size = 0.25  # Max 50%
  ```

## Siehe auch

- [Circuit Breaker](CIRCUIT_BREAKER.md)
- [Monitoring](MONITORING.md)
- [Backup & Recovery](BACKUP_RECOVERY.md)
