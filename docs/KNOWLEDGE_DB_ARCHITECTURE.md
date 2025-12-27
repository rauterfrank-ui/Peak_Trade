# Knowledge Database Integration: Architecture & Usage Guide

## Übersicht

Die Knowledge Database Integration ermöglicht die Nutzung externer Wissensdatenbanken für KI-basierte Research- und Entscheidungsprozesse in Peak_Trade. Das System kombiniert:

- **Vector Databases** für semantische Suche (Chroma, Pinecone, Qdrant)
- **Time-Series Databases** für historische Daten (InfluxDB, Parquet)
- **RAG (Retrieval-Augmented Generation)** für KI-gestützte Antworten
- **API Security & Management** für sichere Integration

**Ziel:** Portfolio-Strategien und Research-Entscheidungen durch strukturierte Wissensintegration verbessern.

---

## 1. Architektur

### 1.1 Komponenten

```
┌─────────────────────────────────────────────────────────────┐
│                    Peak_Trade Core                           │
│  (Research, Portfolio, Strategies, Backtest)                 │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Knowledge Integration Layer                     │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Vector DB   │  │ Time-Series  │  │  RAG Pipeline    │  │
│  │ (Semantic   │  │ DB (Ticks,   │  │  (AI-Augmented   │  │
│  │  Search)    │  │  Portfolio)  │  │   Queries)       │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Manager (Security)                   │  │
│  │  - Key Management  - Rate Limiting  - Monitoring     │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────┬──────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │ ChromaDB │   │ InfluxDB │   │ Parquet  │
  │ (Local)  │   │ (Cloud)  │   │ (Local)  │
  └──────────┘   └──────────┘   └──────────┘
```

### 1.2 Datenfluss

1. **Ingestion:** Datenquellen → API Manager → Vector/Time-Series DB
2. **Query:** User/System → RAG Pipeline → Vector DB → Context Retrieval
3. **Response:** Context + AI Prompt → Augmented Answer
4. **Monitoring:** API Manager → Usage Logs → Security Reports

### 1.3 Access Control & Readonly Mode

**KNOWLEDGE_READONLY Environment Flag:**

Das System unterstützt einen globalen Readonly-Modus für alle Knowledge DB Operationen:

```bash
export KNOWLEDGE_READONLY=true  # Blockiert alle Schreibzugriffe
export KNOWLEDGE_READONLY=false # Erlaubt Schreibzugriffe (Default)
```

**Access Matrix:**

| Context      | GET (Read) | WRITE (Add/Delete) |
|--------------|------------|-------------------|
| dashboard    | ✅ YES     | ❌ NO             |
| research     | ✅ YES     | ✅ YES            |
| live_track   | ✅ YES     | ❌ NO             |
| admin        | ✅ YES     | ✅ YES            |
| **READONLY=true** | ✅ YES | ❌ NO (enforced) |

**Implementierung:**
- Alle Write-Operationen prüfen `KNOWLEDGE_READONLY` via `_check_readonly()`
- Bei `READONLY=true` wird `ReadonlyModeError` geworfen
- Read-Operationen (search, query) bleiben verfügbar
- Context-spezifische Gating (dashboard/live_track) erfolgt auf API-Layer-Ebene

**Betroffene Operationen:**
- Vector DB: `add_documents()`, `delete()`, `clear()`
- Time-Series DB: `write_ticks()`, `write_portfolio_history()`
- RAG Pipeline: `add_documents()`, `clear_knowledge_base()`

---

## 2. Module-Referenz

### 2.1 Vector Database (`src/knowledge/vector_db.py`)

**Zweck:** Semantische Suche über Text-Dokumente (Strategien, Reports, Papers)

**Unterstützte Backends:**
- **ChromaDB** (empfohlen für Einstieg): Lokal, kostenlos, embedded
- **Qdrant**: Lokal/Cloud, skalierbar
- **Pinecone**: Cloud, kostenpflichtig (~$70/Monat)

**Beispiel:**
```python
from src.knowledge import VectorDBFactory, APIManager
from src.knowledge.vector_db import ReadonlyModeError
import os

api_manager = APIManager()
config = api_manager.get_db_config("chroma")
vector_db = VectorDBFactory.create("chroma", config)

# Add documents (nur wenn nicht readonly)
try:
    vector_db.add_documents(
        documents=["RSI strategy works in ranging markets"],
        metadatas=[{"source": "strategy_docs", "category": "strategy"}],
        ids=["rsi_strategy"]
    )
except ReadonlyModeError:
    print("Write blocked: KNOWLEDGE_READONLY is enabled")

# Search (funktioniert immer)
results = vector_db.search("strategy for ranging market", top_k=3)
for doc, score, metadata in results:
    print(f"Score: {score:.4f} - {doc[:100]}")
```

### 2.2 Time-Series Database (`src/knowledge/timeseries_db.py`)

**Zweck:** Historische Zeitreihen (Ticks, Portfolio-Equity, Performance-Metriken)

**Unterstützte Backends:**
- **Parquet** (empfohlen für Einstieg): Lokal, kostenlos, Pandas-kompatibel
- **InfluxDB**: Professionell, Cloud/Self-hosted, Zeit-optimiert

**Beispiel:**
```python
from src.knowledge import TimeSeriesDBFactory
import pandas as pd

ts_db = TimeSeriesDBFactory.create("parquet", {"base_path": "./data/timeseries"})

# Write portfolio history
portfolio_df = pd.DataFrame({
    "timestamp": pd.date_range("2024-01-01", periods=365, freq="D"),
    "equity": [10000 + i*10 for i in range(365)],
})
ts_db.write_portfolio_history(portfolio_df, tags={"portfolio": "my_portfolio"})

# Query
history = ts_db.query_portfolio_history(
    start_time="2024-01-01",
    end_time="2024-12-31"
)
```

### 2.3 RAG Pipeline (`src/knowledge/rag.py`)

**Zweck:** Knowledge-Augmented AI Queries (Retrieval-Augmented Generation)

**Features:**
- Context Retrieval aus Vector DB
- Formatierung für AI-Prompts
- Spezialisierte RAG-Typen (Strategy, Market Analysis)

**Beispiel:**
```python
from src.knowledge import RAGPipeline, VectorDBFactory, APIManager

api_manager = APIManager()
config = api_manager.get_db_config("chroma")
vector_db = VectorDBFactory.create("chroma", config)

rag = RAGPipeline(vector_db=vector_db)

# Add knowledge
rag.add_documents(
    documents=["Backtest Q1: Sharpe 1.8, Drawdown 12%"],
    metadatas=[{"source": "backtest", "date": "2024-03-31"}]
)

# Query
response = rag.query("What was the Sharpe ratio in Q1?", top_k=3)
print(response["context"])
```

**Spezialisierte RAG-Typen:**
```python
from src.knowledge import StrategyRAG, MarketAnalysisRAG

# Strategy Recommendations
strategy_rag = StrategyRAG(vector_db=vector_db)
recommendation = strategy_rag.recommend_strategy(
    market_conditions={"regime": "ranging", "volatility": "low"},
    top_k=3
)

# Market Regime Analysis
market_rag = MarketAnalysisRAG(vector_db=vector_db)
analysis = market_rag.analyze_regime(
    current_metrics={"volatility": 0.8, "trend_strength": 0.7},
    top_k=5
)
```

### 2.4 API Manager (`src/knowledge/api_manager.py`)

**Zweck:** Sichere API-Key-Verwaltung, Rate-Limiting, Monitoring

**Features:**
- Environment-basierte Key-Verwaltung
- Key-Rotation-Tracking
- Request-Monitoring
- Rate-Limit-Checks

**Beispiel:**
```python
from src.knowledge import APIManager

api_manager = APIManager()

# Get API key (from environment)
pinecone_key = api_manager.get_api_key("PINECONE_API_KEY", required=False)

# Track request
api_manager.track_request("pinecone", endpoint="/query")

# Check rate limit
if api_manager.check_rate_limit("pinecone"):
    # Make request
    pass

# Security report
report = api_manager.get_security_report()
```

---

## 3. Integration in Peak_Trade

### 3.1 Configuration (`config/config.toml`)

```toml
[knowledge]
enabled = true
vector_db_backend = "chroma"
timeseries_db_backend = "parquet"
rag_enabled = true

[knowledge.vector_db.chroma]
persist_directory = "./data/chroma_db"
collection_name = "peak_trade"

[knowledge.timeseries_db.parquet]
base_path = "./data/timeseries"
```

### 3.2 Environment Variables

```bash
# .env (NICHT ins Repo committen!)

# Optional: Für Cloud-Backends
# PINECONE_API_KEY=your_key
# QDRANT_API_KEY=your_key
# INFLUXDB_TOKEN=your_token
```

### 3.3 Verwendung in Research-Pipeline

```python
# scripts/research_with_knowledge.py
from src.knowledge import VectorDBFactory, RAGPipeline, APIManager
from src.backtest import BacktestEngine

# Initialize knowledge layer
api_manager = APIManager()
config = api_manager.get_db_config("chroma")
vector_db = VectorDBFactory.create("chroma", config)
rag = RAGPipeline(vector_db=vector_db)

# Add backtest results to knowledge base
def store_backtest_result(result, strategy_name):
    summary = f"Strategy: {strategy_name}, Sharpe: {result.sharpe:.2f}, Drawdown: {result.max_dd:.2%}"
    rag.add_documents(
        documents=[summary],
        metadatas=[{
            "source": "backtest",
            "strategy": strategy_name,
            "timestamp": datetime.now().isoformat()
        }]
    )

# Query for best strategy
response = rag.query("What is the best strategy for low volatility?", top_k=3)
```

---

## 4. Use Cases

### 4.1 Strategy Selection

**Problem:** Welche Strategie passt am besten zu aktuellen Market Conditions?

**Lösung:**
```python
from src.knowledge import StrategyRAG, VectorDBFactory, APIManager

api_manager = APIManager()
config = api_manager.get_db_config("chroma")
vector_db = VectorDBFactory.create("chroma", config)
strategy_rag = StrategyRAG(vector_db=vector_db)

# Add strategy performance history
strategy_rag.add_documents(
    documents=[
        "RSI Strategy: Sharpe 1.8 in ranging markets, 1.2 in trending",
        "Momentum: Sharpe 2.1 in trending markets, 0.8 in ranging"
    ],
    metadatas=[
        {"type": "strategy", "name": "rsi"},
        {"type": "strategy", "name": "momentum"}
    ]
)

# Get recommendation
recommendation = strategy_rag.recommend_strategy(
    market_conditions={"regime": "ranging", "volatility": "medium"}
)
```

### 4.2 Portfolio Review

**Problem:** Portfolio-Performance im historischen Kontext analysieren

**Lösung:**
```python
from src.knowledge import TimeSeriesDBFactory
import pandas as pd

ts_db = TimeSeriesDBFactory.create("parquet", {"base_path": "./data/timeseries"})

# Store daily portfolio snapshots
def store_daily_snapshot(equity, cash, positions_value):
    df = pd.DataFrame({
        "timestamp": [datetime.now()],
        "equity": [equity],
        "cash": [cash],
        "positions_value": [positions_value]
    })
    ts_db.write_portfolio_history(df, tags={"portfolio": "live"})

# Analyze performance
history = ts_db.query_portfolio_history(
    start_time="2024-01-01",
    end_time="2024-12-31"
)
max_dd = (history["equity"].min() / history["equity"].max()) - 1
print(f"Max Drawdown: {max_dd:.2%}")
```

### 4.3 Research Paper Integration

**Problem:** Trading Research Papers in Wissensbank aufnehmen

**Lösung:**
```python
from src.knowledge import VectorDBFactory, RAGPipeline, APIManager

api_manager = APIManager()
config = api_manager.get_db_config("chroma")
vector_db = VectorDBFactory.create("chroma", config)
rag = RAGPipeline(vector_db=vector_db)

# Add research paper
paper_text = """
Title: Machine Learning for Momentum Trading
Key Findings:
- LSTM models outperform traditional indicators
- Regime detection improves Sharpe by 15%
- Best on 1h-4h timeframes
"""

rag.add_documents(
    documents=[paper_text],
    metadatas=[{
        "source": "arxiv",
        "url": "https://arxiv.org/abs/1234.5678",
        "category": "research",
        "review_status": "reviewed"
    }],
    ids=["arxiv_1234_5678"]
)

# Query
response = rag.query("What do research papers say about ML for momentum?")
```

---

## 5. Governance & Best Practices

### 5.1 Data Quality

**Checkliste für neue Datenquellen:**
- [ ] Quelle verifiziert und dokumentiert
- [ ] Metadaten vollständig (source, timestamp, category)
- [ ] Lizenz/Copyright geklärt
- [ ] Qualitäts-Check durchgeführt (Relevanz, Aktualität)
- [ ] Peer-Review abgeschlossen

**Siehe:** `docs/KNOWLEDGE_SOURCES_GOVERNANCE_PLAYBOOK.md`

### 5.2 Security

**API-Key-Management:**
- NIEMALS Keys in Code oder Config committen
- Keys nur in `.env` oder Umgebungsvariablen
- Regelmäßige Key-Rotation (alle 90 Tage)
- `APIManager` für alle Key-Zugriffe verwenden

**Rate-Limiting:**
- Vor jedem API-Call `check_rate_limit()` prüfen
- Requests mit `track_request()` loggen
- Monatliche Kosten-Review

### 5.3 Monitoring

**KPIs:**
- Ingestion Success Rate > 99%
- Query Response Time < 500ms (p95)
- Data Freshness < 24h
- API Rate Limit Usage < 80%

**Alerts:**
```python
api_manager = APIManager()
report = api_manager.get_security_report()

# Check key rotation
for key, needs_rotation in report["rotation_needed"].items():
    if needs_rotation:
        print(f"⚠️  Key {key} needs rotation!")

# Check usage
stats = api_manager.get_usage_stats("pinecone", hours=24)
if stats["request_count"] > 800:  # 80% of limit
    print("⚠️  High API usage!")
```

---

## 6. Troubleshooting

### 6.1 "Module not found: chromadb"

**Problem:** ChromaDB nicht installiert

**Lösung:**
```bash
pip install chromadb
```

### 6.2 "API key not found"

**Problem:** API-Key nicht in Environment

**Lösung:**
```bash
# .env erstellen
export PINECONE_API_KEY=your_key_here

# Oder im Code optional machen
api_manager.get_api_key("PINECONE_API_KEY", required=False)
```

### 6.3 Langsame Queries

**Problem:** Vector-Suche dauert zu lange

**Lösungen:**
1. `top_k` reduzieren (z.B. 3 statt 10)
2. Metadata-Filter nutzen für präzisere Suche
3. Index-Optimierung (bei Pinecone/Qdrant)
4. Lokales ChromaDB statt Cloud-Backend

### 6.4 Rate Limit Exceeded

**Problem:** Zu viele API-Requests

**Lösungen:**
1. Caching aktivieren (Time-Series-DB)
2. Batch-Processing verwenden
3. Request-Frequenz reduzieren
4. Bezahl-Plan upgraden

---

## 7. Roadmap

### Phase 1: Foundation (✅ Abgeschlossen)
- [x] Vector DB Integration (Chroma, Qdrant, Pinecone)
- [x] Time-Series DB Integration (Parquet, InfluxDB)
- [x] RAG Pipeline
- [x] API Manager & Security
- [x] Governance Playbook

### Phase 2: Integration (🚧 In Progress)
- [ ] Kraken OHLCV Ingestion
- [ ] Backtest-Results → Vector DB
- [ ] Portfolio-History → Time-Series DB
- [ ] Research-CLI Integration

### Phase 3: Advanced Features (📋 Geplant)
- [ ] Glassnode On-Chain Metrics
- [ ] Research Paper Auto-Ingestion
- [ ] Multi-Modal RAG (Text + Charts)
- [ ] Real-time Streaming Updates

---

## 8. Ressourcen

**Dokumentation:**
- [Governance Playbook](KNOWLEDGE_SOURCES_GOVERNANCE_PLAYBOOK.md)
- [Sources Registry](KNOWLEDGE_SOURCES_REGISTRY.md)
- [Architecture Overview](ARCHITECTURE_OVERVIEW.md)

**Beispiel-Scripts:**
- `scripts/demo_knowledge_db.py` - Vollständiges Demo
- Tests: `tests/test_knowledge_integration.py`

**External Docs:**
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Qdrant Docs](https://qdrant.tech/documentation/)
- [InfluxDB Docs](https://docs.influxdata.com/)

---

**Version:** 1.0  
**Stand:** Dezember 2024  
**Maintained by:** Peak_Trade Team
