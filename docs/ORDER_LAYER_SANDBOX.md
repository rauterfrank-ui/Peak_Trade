# Peak_Trade – Order-Layer (Sandbox & Order-Routing)

Dieses Dokument beschreibt den **Order-Layer** von Peak_Trade.
Der Layer bietet eine abstrahierte, erweiterbare Schnittstelle fuer Order-Ausfuehrung.

> **WICHTIG: Kein Real-Trading – alles Sandbox/Paper.**
>
> Dieser Layer schickt **keine echten Orders** an Boersen.
> Er dient ausschliesslich zur Simulation/Paper-Trading und als Basis
> fuer zukuenftige Testnet-/Live-Integrationen.

---

## 1. Ueberblick

Der Order-Layer (`src/orders/`) stellt bereit:

| Komponente | Beschreibung |
|------------|--------------|
| `OrderRequest` | Anfrage fuer eine Order (Symbol, Side, Quantity, etc.) |
| `OrderFill` | Informationen ueber eine ausgefuehrte Order |
| `OrderExecutionResult` | Ergebnis einer Order-Ausfuehrung (filled/rejected) |
| `OrderExecutor` | Protocol/Interface fuer Order-Executors |
| `PaperOrderExecutor` | Sandbox-Executor (keine echten Orders) |
| `PaperMarketContext` | Marktkontext mit Preisen fuer Paper-Trading |
| Mapper-Funktionen | Konvertierung von `LiveOrderRequest` / CSV → `OrderRequest` |

---

## 2. Dateien & Struktur

```
src/orders/
├── __init__.py           # Package-Exports
├── base.py               # Dataclasses: OrderRequest, OrderFill, OrderExecutionResult, OrderExecutor
├── paper.py              # PaperMarketContext, PaperOrderExecutor, ExchangeOrderExecutor (Stub)
└── mappers.py            # from_live_order_request(), from_orders_csv_row(), to_order_requests()
```

---

## 3. Order-Datenstrukturen

### 3.1 `OrderRequest`

Anfrage fuer eine Order:

```python
from src.orders import OrderRequest

req = OrderRequest(
    symbol="BTC/EUR",
    side="buy",           # "buy" oder "sell"
    quantity=0.1,
    order_type="market",  # "market" oder "limit"
    limit_price=None,     # nur bei order_type="limit"
    client_id="order-123",
    metadata={"strategy_key": "ma_crossover"},
)
```

**Felder:**

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `symbol` | `str` | Trading-Pair (z.B. "BTC/EUR") |
| `side` | `"buy"` \| `"sell"` | Kauf- oder Verkaufsorder |
| `quantity` | `float` | Menge (Stueckzahl) |
| `order_type` | `"market"` \| `"limit"` | Order-Typ |
| `limit_price` | `float` \| `None` | Limit-Preis (nur bei Limit-Orders) |
| `client_id` | `str` \| `None` | Client-ID fuer Tracking |
| `metadata` | `Dict[str, Any]` | Zusaetzliche Metadaten |

### 3.2 `OrderFill`

Informationen ueber eine ausgefuehrte Order:

```python
from src.orders import OrderFill

fill = OrderFill(
    symbol="BTC/EUR",
    side="buy",
    quantity=0.1,
    price=50000.0,
    timestamp=datetime.now(timezone.utc),
    fee=5.0,
    fee_currency="EUR",
)
```

### 3.3 `OrderExecutionResult`

Ergebnis einer Order-Ausfuehrung:

```python
from src.orders import OrderExecutionResult

# Erfolgreiche Order
result = OrderExecutionResult(
    status="filled",
    request=req,
    fill=fill,
    metadata={"notional": 5000.0},
)

# Abgelehnte Order
result = OrderExecutionResult(
    status="rejected",
    request=req,
    fill=None,
    reason="no_price_for_symbol: UNKNOWN/EUR",
)
```

**Status-Werte:**

| Status | Beschreibung |
|--------|--------------|
| `pending` | Order wartet auf Ausfuehrung |
| `filled` | Order vollstaendig ausgefuehrt |
| `partially_filled` | Order teilweise ausgefuehrt |
| `rejected` | Order abgelehnt |
| `cancelled` | Order storniert |

---

## 4. OrderExecutor Interface

Das `OrderExecutor`-Protocol definiert die Schnittstelle fuer Executors:

```python
from src.orders import OrderExecutor, OrderRequest, OrderExecutionResult
from typing import Protocol, Sequence, List

class OrderExecutor(Protocol):
    def execute_orders(self, orders: Sequence[OrderRequest]) -> List[OrderExecutionResult]:
        ...

    def execute_order(self, order: OrderRequest) -> OrderExecutionResult:
        ...
```

---

## 5. PaperOrderExecutor (Sandbox)

Der `PaperOrderExecutor` simuliert Order-Ausfuehrungen:

```python
from src.orders import PaperMarketContext, PaperOrderExecutor, OrderRequest

# Marktkontext mit aktuellen Preisen
ctx = PaperMarketContext(
    prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
    fee_bps=10.0,       # 0.1% Fee
    slippage_bps=5.0,   # 0.05% Slippage
    base_currency="EUR",
)

# Executor erstellen
executor = PaperOrderExecutor(ctx)

# Order ausfuehren
req = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.1)
result = executor.execute_order(req)

if result.is_filled:
    print(f"Filled @ {result.fill.price} with fee {result.fill.fee}")
else:
    print(f"Rejected: {result.reason}")
```

### 5.1 Verhalten

| Order-Typ | Verhalten |
|-----------|-----------|
| **Market** | Wird sofort zum Preis aus `PaperMarketContext` ausgefuehrt (mit Slippage) |
| **Limit Buy** | Wird ausgefuehrt wenn `market_price <= limit_price` |
| **Limit Sell** | Wird ausgefuehrt wenn `market_price >= limit_price` |
| **Unbekanntes Symbol** | Wird rejected mit `no_price_for_symbol` |

### 5.2 Slippage

Slippage wird in Basispunkten (bps) angegeben:

- **Buy**: `fill_price = market_price * (1 + slippage_bps / 10000)`
- **Sell**: `fill_price = market_price * (1 - slippage_bps / 10000)`

### 5.3 Fees

Fees werden als Prozentsatz des Notionals berechnet:

```
fee = quantity * price * (fee_bps / 10000)
```

---

## 6. Mapping-Helpers

### 6.1 Von `LiveOrderRequest`

```python
from src.orders import from_live_order_request
from src.live.orders import LiveOrderRequest

live_req = LiveOrderRequest(
    client_order_id="order-1",
    symbol="BTC/EUR",
    side="BUY",
    quantity=0.1,
    extra={"current_price": 50000.0},
)

order_req = from_live_order_request(live_req)
```

### 6.2 Von CSV-Zeile

```python
from src.orders import from_orders_csv_row

row = {
    "symbol": "BTC/EUR",
    "side": "BUY",
    "quantity": 0.1,
    "extra_json": '{"current_price": 50000.0}',
}

order_req = from_orders_csv_row(row)
```

### 6.3 Batch-Konvertierung

```python
from src.orders import to_order_requests
from src.live.orders import load_orders_csv

live_orders = load_orders_csv("reports/live/orders.csv")
order_requests = to_order_requests(live_orders)
```

---

## 7. Integration in Scripts

### 7.1 `paper_trade_from_orders.py`

Das Script unterstuetzt jetzt den Order-Layer via `--use-order-layer`:

```bash
# Mit altem PaperBroker (Standard)
python3 scripts/paper_trade_from_orders.py \
  --orders reports/live/preview_..._orders.csv \
  --starting-cash 10000

# Mit neuem Order-Layer
python3 scripts/paper_trade_from_orders.py \
  --orders reports/live/preview_..._orders.csv \
  --starting-cash 10000 \
  --use-order-layer
```

### 7.2 `preview_live_orders.py`

Das Script zeigt jetzt die Order-Layer-Kompatibilitaet:

```bash
python3 scripts/preview_live_orders.py \
  --signals reports/forward/..._signals.csv \
  --notional 500

# Output:
# ...
# 🔧 Order-Layer Kompatibilität:
#    3 OrderRequest-Objekte erstellt
#    Bereit für PaperOrderExecutor (--use-order-layer in paper_trade_from_orders.py)
```

---

## 8. Beispiel: Vollstaendiger Flow

```python
from src.orders import (
    PaperMarketContext,
    PaperOrderExecutor,
    to_order_requests,
)
from src.live.orders import load_orders_csv

# 1. Orders aus CSV laden
live_orders = load_orders_csv("reports/live/preview_orders.csv")

# 2. Zu OrderRequests konvertieren
order_requests = to_order_requests(live_orders)

# 3. Marktkontext erstellen (Preise aus Orders extrahieren)
prices = {}
for order in live_orders:
    if order.extra and order.extra.get("current_price"):
        prices[order.symbol] = float(order.extra["current_price"])

ctx = PaperMarketContext(
    prices=prices,
    fee_bps=10.0,
    slippage_bps=5.0,
)

# 4. Executor erstellen und Orders ausfuehren
executor = PaperOrderExecutor(ctx)
results = executor.execute_orders(order_requests)

# 5. Ergebnisse auswerten
for result in results:
    if result.is_filled:
        print(f"✅ {result.fill.side.upper()} {result.fill.symbol} "
              f"@ {result.fill.price:.2f} (fee: {result.fill.fee:.4f})")
    else:
        print(f"❌ {result.request.symbol}: {result.reason}")
```

---

## 9. Beispiel-Ergebnisse

### Gefuellte Order

```python
OrderExecutionResult(
    status="filled",
    request=OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.1, ...),
    fill=OrderFill(
        symbol="BTC/EUR",
        side="buy",
        quantity=0.1,
        price=50005.0,      # mit Slippage
        timestamp=datetime(2025, 12, 4, 10, 0, 0, tzinfo=timezone.utc),
        fee=5.0005,         # 10 bps auf 5000.5 EUR
        fee_currency="EUR",
    ),
    reason=None,
    metadata={
        "execution_id": 1,
        "market_price": 50000.0,
        "notional": 5000.5,
        "fee": 5.0005,
        "slippage_bps": 10.0,
        "mode": "paper",
    },
)
```

### Abgelehnte Order

```python
OrderExecutionResult(
    status="rejected",
    request=OrderRequest(symbol="UNKNOWN/EUR", side="buy", quantity=1.0, ...),
    fill=None,
    reason="no_price_for_symbol: UNKNOWN/EUR",
    metadata={"execution_id": 2},
)
```

---

## 10. Tests

Die Tests befinden sich in `tests/test_orders_smoke.py`:

```bash
python3 -m pytest tests/test_orders_smoke.py -v
# 31 passed
```

Getestete Bereiche:

- Dataclass-Instanziierung und Validierung
- PaperOrderExecutor (Market/Limit, Slippage, Fees)
- Mapper-Funktionen
- Integration-Tests

---

## 11. Zukuenftige Erweiterungen

> **Nicht in Phase 15 implementiert:**

1. **TestnetOrderExecutor**: Echte Orders an Testnet-APIs
2. **LiveOrderExecutor**: Echte Orders an Produktions-APIs
3. **Position-Tracking**: Der Order-Layer trackt keine Positionen (dafuer: `PaperBroker`)
4. **PnL-Berechnung**: Keine Realized/Unrealized PnL (dafuer: `PaperBroker`)

Der `ExchangeOrderExecutor` ist als Stub vorhanden und wirft `NotImplementedError`.

---

## 12. Vergleich: Order-Layer vs. PaperBroker

| Feature | Order-Layer | PaperBroker |
|---------|-------------|-------------|
| Order-Ausfuehrung | ✅ | ✅ |
| Fees & Slippage | ✅ | ✅ |
| Position-Tracking | ❌ | ✅ |
| Cash-Tracking | ❌ | ✅ |
| Realized/Unrealized PnL | ❌ | ✅ |
| Trade-History | ❌ | ✅ |
| Abstrahiertes Interface | ✅ | ❌ |
| Erweiterbar (Testnet/Live) | ✅ | ❌ |

**Empfehlung:**

- Fuer vollstaendige Paper-Trading-Simulation: `PaperBroker` verwenden
- Fuer abstrahierte Order-Ausfuehrung (zukuenftig erweiterbar): Order-Layer verwenden
