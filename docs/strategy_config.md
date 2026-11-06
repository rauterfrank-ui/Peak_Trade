# Strategy Config Management

## Übersicht

Peak_Trade bietet eine typsichere, validierte Verwaltung von Strategie-Konfigurationen über `config.toml`.

---

## Funktionen

### `get_strategy_cfg(name: str) -> Dict[str, Any]`

Lädt Strategie-Parameter aus `config.toml` mit klarer Fehlerbehandlung.

**Beispiel:**

```python
from src.core import get_strategy_cfg

# Strategie-Config laden
params = get_strategy_cfg("ma_crossover")

print(params['fast_period'])  # 10
print(params['slow_period'])  # 30
print(params['stop_pct'])     # 0.02
```

**Fehlerfall:**

```python
try:
    params = get_strategy_cfg("non_existent")
except KeyError as e:
    print(e)
    # "Strategy 'non_existent' nicht in config.toml definiert.
    #  Verfügbare Strategien: ma_crossover"
```

---

### `list_strategies() -> List[str]`

Gibt sortierte Liste aller definierten Strategien zurück.

**Beispiel:**

```python
from src.core import list_strategies

strategies = list_strategies()
print(strategies)  # ['ma_crossover', 'rsi_strategy']
```

---

## Config-Format (config.toml)

```toml
[strategy.ma_crossover]
fast_period = 10
slow_period = 30
stop_pct = 0.02

[strategy.rsi_strategy]
rsi_period = 14
overbought = 70
oversold = 30
stop_pct = 0.025
```

---

## Best Practices

### 1. Immer get_strategy_cfg() verwenden

❌ **NICHT SO:**
```python
cfg = get_config()
params = cfg.strategy.get('ma_crossover', {})  # Kein Error bei Tippfehler!
```

✅ **SONDERN SO:**
```python
params = get_strategy_cfg('ma_crossover')  # Klarer Fehler bei Tippfehler!
```

### 2. Fehlerbehandlung

```python
try:
    params = get_strategy_cfg(strategy_name)
except KeyError as e:
    print(f"❌ {e}")
    print("Verfügbare Strategien:", list_strategies())
    return
```

---

## Integration in Backtest-Scripts

**Nachher (typsicher):**
```python
try:
    params = get_strategy_cfg('ma_crossover')
except KeyError as e:
    print(f"❌ FEHLER: {e}")
    return
```

---

**Built with ❤️ and type safety**
