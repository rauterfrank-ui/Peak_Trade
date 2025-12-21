# External Knowledge Sources: Governance & Quality Control Playbook

## Übersicht

Dieses Playbook definiert den Prozess zur systematischen Überprüfung und Einpflege externer Wissensquellen in die Peak_Trade Knowledge Databases. Es stellt sicher, dass nur qualitativ hochwertige, relevante und sichere Daten in die KI- und Research-Systeme integriert werden.

**Ziel:** Konsistente, nachvollziehbare und sichere Integration externer Wissensdatenbanken für AI-basierte Research- und Entscheidungsprozesse.

---

## 1. Governance-Prinzipien

### 1.1 Safety First

- **Keine sensiblen Daten**: Niemals persönliche Daten, API-Keys oder Secrets in Knowledge Databases speichern
- **Quellen-Validierung**: Alle externen Quellen müssen vor Integration geprüft werden
- **Versionierung**: Jede Datenquelle muss versioniert und nachverfolgbar sein
- **Rollback-Fähigkeit**: Möglichkeit, problematische Daten schnell zu entfernen

### 1.2 Qualitäts-Standards

- **Relevanz**: Daten müssen Trading-, Portfolio- oder Market-Research relevant sein
- **Aktualität**: Zeitstempel und Gültigkeitsdauer müssen dokumentiert sein
- **Vollständigkeit**: Metadaten (Quelle, Datum, Autor, Tags) sind Pflicht
- **Konsistenz**: Format und Struktur müssen Standard-Schema folgen

### 1.3 Compliance & Audit Trail

- **Nachvollziehbarkeit**: Jede Integration muss dokumentiert werden
- **Review-Prozess**: Vier-Augen-Prinzip für kritische Datenquellen
- **Audit-Log**: Automatisches Logging aller Änderungen
- **Retention Policy**: Definierte Aufbewahrungsfristen

---

## 2. Datenquellen-Kategorien

### 2.1 Interne Quellen (Vertrauensstufe: Hoch)

**Beispiele:**
- Eigene Backtest-Ergebnisse
- Portfolio-Performance-Historien
- Strategy-Research-Reports
- Market-Regime-Analysen

**Prüfprozess:**
- [x] Quelle stammt aus eigenem System
- [x] Datenformat validiert
- [x] Metadaten vollständig
- [x] Automatische Integration möglich

### 2.2 Öffentliche Marktdaten (Vertrauensstufe: Mittel-Hoch)

**Beispiele:**
- Exchange-OHLCV-Daten (Kraken, Binance)
- On-Chain-Metriken (Glassnode, CoinMetrics)
- Sentiment-Daten (Fear & Greed Index)

**Prüfprozess:**
- [x] API-Quelle verifiziert und dokumentiert
- [x] Datenqualität geprüft (Gaps, Outliers)
- [x] Rate-Limits beachtet
- [x] Fehlerbehandlung implementiert
- [x] Kosten/Budget berücksichtigt

### 2.3 Research-Papers & Whitepapers (Vertrauensstufe: Mittel)

**Beispiele:**
- Academic Papers (arXiv, SSRN)
- Trading-Strategy-Whitepapers
- Technical Analysis Guides

**Prüfprozess:**
- [x] Quelle und Autor verifiziert
- [x] Publikationsdatum geprüft
- [x] Inhaltliche Relevanz bewertet
- [x] Copyright/Lizenz geklärt
- [x] Manuelle Review durchgeführt

### 2.4 Community & Social Data (Vertrauensstufe: Niedrig)

**Beispiele:**
- Reddit/Twitter Sentiment
- Trading Forums
- Discord/Telegram Diskussionen

**Prüfprozess:**
- [x] Mehrfach-Quellen-Validierung
- [x] Bias-Prüfung
- [x] Zeitliche Aktualität
- [x] Manuelle Stichproben-Prüfung
- [x] **Disclaimer-Kennzeichnung in Metadaten**

---

## 3. Integration-Workflow

### Phase 1: Evaluation

**Schritt 1.1: Datenquelle identifizieren**
```
- Name der Quelle: _______________
- URL/API: _______________
- Kategorie: [ ] Intern [ ] Marktdaten [ ] Research [ ] Community
- Geschätzte Datenmenge: _______________
```

**Schritt 1.2: Qualitäts-Check**
```python
# Beispiel-Checkliste
quality_check = {
    "source_verified": False,      # Quelle geprüft?
    "data_format_valid": False,    # Format OK?
    "metadata_complete": False,    # Metadaten vollständig?
    "relevance_high": False,       # Trading-relevant?
    "no_sensitive_data": False,    # Keine Secrets/PII?
    "license_ok": False,           # Lizenz geklärt?
}
# Alle Checks müssen True sein für Go-Decision
```

**Schritt 1.3: Go/No-Go Decision**
- **GO**: Alle Checks bestanden → Weiter zu Phase 2
- **NO-GO**: Mindestens ein Check failed → Dokumentieren und ablehnen

### Phase 2: Vorbereitung

**Schritt 2.1: Daten-Ingestion-Script erstellen**
```python
# scripts/ingest_<source_name>.py
from src.knowledge import VectorDBFactory, APIManager

def ingest_source_data():
    """Ingest data from <source_name>."""
    api_manager = APIManager()
    vector_db = VectorDBFactory.create("chroma", api_manager.get_db_config("chroma"))

    # Load data
    documents = load_data_from_source()

    # Add metadata
    metadatas = [
        {
            "source": "<source_name>",
            "timestamp": datetime.now().isoformat(),
            "category": "research",  # or "market_data", "strategy", etc.
            "version": "1.0",
        }
        for _ in documents
    ]

    # Ingest
    vector_db.add_documents(documents=documents, metadatas=metadatas)
```

**Schritt 2.2: Test-Run durchführen**
- Kleine Datenmenge (Sample) testen
- Queries validieren
- Performance prüfen

### Phase 3: Integration

**Schritt 3.1: Produktiv-Ingestion**
- Komplette Datenmenge einpflegen
- Logs überprüfen
- Metrik-Tracking aktivieren

**Schritt 3.2: Dokumentation**
- Eintrag in `docs/KNOWLEDGE_SOURCES_REGISTRY.md`
- Ingestion-Script dokumentieren
- Metadaten-Schema dokumentieren

**Schritt 3.3: Review & Sign-Off**
- Peer-Review durch zweite Person
- Funktions-Test durch Stakeholder
- Freigabe dokumentieren

### Phase 4: Monitoring & Maintenance

**Schritt 4.1: Regelmäßige Updates**
- Update-Frequenz definieren (täglich, wöchentlich, monatlich)
- Automatisierung prüfen
- Fehler-Handling testen

**Schritt 4.2: Qualitäts-Monitoring**
- Query-Performance überwachen
- Daten-Drift erkennen
- Staleness-Checks

**Schritt 4.3: Audit & Review**
- Quartalsweise Review aller Quellen
- Nicht mehr relevante Quellen entfernen
- Kosten-Nutzen-Analyse

---

## 4. Metadaten-Schema

### Standard-Metadaten (Pflicht)

```python
{
    "source": str,           # Name der Quelle
    "timestamp": str,        # ISO 8601 Timestamp
    "category": str,         # "research" | "market_data" | "strategy" | "community"
    "version": str,          # Versionsnummer
    "author": str,           # Autor/System
    "tags": List[str],       # Schlagworte
}
```

### Erweiterte Metadaten (Optional)

```python
{
    "url": str,              # Quell-URL
    "license": str,          # Lizenz
    "confidence": float,     # Konfidenz-Score (0-1)
    "expiry_date": str,      # Gültig bis (falls zeitlich begrenzt)
    "review_status": str,    # "draft" | "reviewed" | "approved"
    "related_docs": List[str],  # IDs verwandter Dokumente
}
```

---

## 5. API-Sicherheit & Key-Management

### 5.1 API-Key Handling

**NIEMALS:**
- API-Keys in Code committen
- Keys in Config-Files speichern
- Keys in Logs ausgeben

**IMMER:**
- Keys in `.env` oder Umgebungsvariablen
- `src.knowledge.api_manager.APIManager` verwenden
- Keys regelmäßig rotieren (alle 90 Tage)

**Beispiel:**
```bash
# .env (NICHT im Repo!)
PINECONE_API_KEY=your_key_here
INFLUXDB_TOKEN=your_token_here
```

```python
from src.knowledge import APIManager

api_manager = APIManager()
pinecone_key = api_manager.get_api_key("PINECONE_API_KEY")
```

### 5.2 Key-Rotation

**Prozess:**
1. Neuen Key beim Provider generieren
2. Alten Key in `.env` durch neuen ersetzen
3. System testen
4. Alten Key beim Provider deaktivieren
5. Rotation in Log dokumentieren

**Automatisches Monitoring:**
```python
api_manager = APIManager()
report = api_manager.get_security_report()

# Check ob Rotation nötig
for key_name, needs_rotation in report["rotation_needed"].items():
    if needs_rotation:
        print(f"⚠️  Key {key_name} sollte rotiert werden!")
```

### 5.3 Netzwerk-Monitoring

**Rate-Limiting beachten:**
```python
api_manager = APIManager()

# Vor jedem Request prüfen
if not api_manager.check_rate_limit("pinecone"):
    raise Exception("Rate limit exceeded, wait before retry")

# Request tracken
api_manager.track_request("pinecone", endpoint="/query", metadata={"query_type": "semantic"})
```

**Kosten-Tracking:**
- Monatliches Budget definieren
- API-Usage regelmäßig prüfen
- Alerts bei Schwellwert-Überschreitung

---

## 6. Beispiel-Szenarien

### Szenario 1: Integration eigener Backtest-Reports

**Kategorie:** Intern (High Trust)

**Steps:**
1. Backtest-Reports in strukturiertem Format exportieren
2. Metadaten hinzufügen (Strategy, Timeframe, Markt, Datum)
3. In Vector-DB einpflegen
4. RAG-Pipeline testen: "Was ist die beste RSI-Strategie für BTC?"

**Script:**
```python
from src.knowledge import VectorDBFactory, APIManager

api_manager = APIManager()
vector_db = VectorDBFactory.create("chroma", api_manager.get_db_config("chroma"))

# Backtest-Report laden
with open("results/backtest_rsi_btc_2024.txt") as f:
    report = f.read()

# Metadaten
metadata = {
    "source": "internal_backtest",
    "timestamp": "2024-12-20T10:00:00Z",
    "category": "strategy",
    "strategy": "rsi_strategy",
    "market": "BTC/EUR",
    "version": "1.0",
}

# Einpflegen
vector_db.add_documents(
    documents=[report],
    metadatas=[metadata],
    ids=["backtest_rsi_btc_2024"]
)
```

### Szenario 2: Integration Glassnode On-Chain Metrics

**Kategorie:** Marktdaten (Medium-High Trust)

**Steps:**
1. Glassnode API-Key in `.env` hinterlegen
2. API-Client implementieren
3. Daten-Validierung (Gaps, Outliers)
4. In Time-Series-DB speichern
5. Regelmäßige Updates (täglich/wöchentlich)

**Script:**
```python
from src.knowledge import TimeSeriesDBFactory, APIManager
import pandas as pd

api_manager = APIManager()
ts_db = TimeSeriesDBFactory.create("parquet", config={"base_path": "./data/timeseries"})

# Glassnode-Daten laden (Mock)
glassnode_data = pd.DataFrame({
    "timestamp": pd.date_range("2024-01-01", periods=365, freq="D"),
    "metric": "active_addresses",
    "value": [10000 + i*10 for i in range(365)],
})

# In Time-Series-DB schreiben
ts_db.write_ticks(
    symbol="BTC/USD",
    data=glassnode_data,
    tags={"source": "glassnode", "metric": "active_addresses"}
)
```

### Szenario 3: Integration Trading-Paper von arXiv

**Kategorie:** Research (Medium Trust)

**Steps:**
1. Paper-PDF herunterladen
2. Text extrahieren (OCR/PDF-Parser)
3. Manuelle Review: Relevanz, Qualität, Copyright
4. Zusammenfassung erstellen
5. In Vector-DB einpflegen mit Disclaimer

**Script:**
```python
from src.knowledge import VectorDBFactory, APIManager

api_manager = APIManager()
vector_db = VectorDBFactory.create("chroma", api_manager.get_db_config("chroma"))

# Paper-Text (gekürzt)
paper_text = """
Title: Machine Learning for Momentum Trading
Abstract: This paper explores ML techniques for momentum strategies...
Key Findings:
- LSTM models outperform traditional momentum indicators
- Regime-detection improves Sharpe ratio by 15%
...
"""

metadata = {
    "source": "arxiv",
    "timestamp": "2024-12-20T10:00:00Z",
    "category": "research",
    "author": "John Doe et al.",
    "url": "https://arxiv.org/abs/1234.5678",
    "license": "CC-BY-4.0",
    "review_status": "reviewed",
    "tags": ["machine_learning", "momentum", "LSTM"],
}

vector_db.add_documents(
    documents=[paper_text],
    metadatas=[metadata],
    ids=["arxiv_1234_5678"]
)
```

---

## 7. Troubleshooting & FAQ

### Q: Wie gehe ich mit Rate-Limits um?

**A:**
1. Rate-Limits in `APIManager` konfigurieren
2. Exponential Backoff implementieren
3. Caching nutzen (Time-Series-DB)
4. Bei kritischen Quellen: Bezahl-Plan upgraden

### Q: Was tun bei schlechter Daten-Qualität?

**A:**
1. Datenquelle nochmal validieren
2. Outlier-Detektion aktivieren
3. Confidence-Score in Metadaten setzen
4. Bei persistenten Problemen: Quelle deaktivieren

### Q: Wie handle ich große Datenmengen?

**A:**
1. Batch-Processing verwenden
2. Inkrementelle Updates statt Full-Refresh
3. Time-Series-DB für historische Daten
4. Vector-DB nur für semantisch relevante Zusammenfassungen

### Q: Wie teste ich RAG-Queries?

**A:**
```python
from src.knowledge import RAGPipeline, VectorDBFactory, APIManager

api_manager = APIManager()
vector_db = VectorDBFactory.create("chroma", api_manager.get_db_config("chroma"))
rag = RAGPipeline(vector_db=vector_db)

# Test-Query
response = rag.query("What is the best momentum strategy?", top_k=3)
print("Context:", response["context"])
print("Sources:", len(response["sources"]))
```

---

## 8. Checkliste für neue Datenquelle

- [ ] Datenquelle identifiziert und dokumentiert
- [ ] Kategorie zugeordnet (Intern/Marktdaten/Research/Community)
- [ ] Qualitäts-Check durchgeführt (alle Checks bestanden)
- [ ] Lizenz/Copyright geklärt
- [ ] API-Keys sicher hinterlegt (wenn nötig)
- [ ] Ingestion-Script erstellt und getestet
- [ ] Metadaten-Schema definiert
- [ ] Sample-Daten erfolgreich eingepflegt
- [ ] RAG-Queries getestet
- [ ] Peer-Review durchgeführt
- [ ] Dokumentation in `KNOWLEDGE_SOURCES_REGISTRY.md` ergänzt
- [ ] Monitoring und Update-Frequenz definiert
- [ ] Sign-Off durch Stakeholder

---

## 9. Verantwortlichkeiten

| Rolle | Verantwortung |
|-------|---------------|
| **Data Owner** | Entscheidung über neue Quellen, Go/No-Go |
| **Developer** | Implementierung Ingestion-Scripts, Testing |
| **Reviewer** | Peer-Review, Qualitäts-Check |
| **Stakeholder** | Fachliche Validierung, Use-Case-Relevanz |

---

## 10. Wartung & Review-Zyklen

### Wöchentlich
- API-Usage prüfen
- Fehler-Logs checken
- Neue Datenquellen-Requests bearbeiten

### Monatlich
- Kosten-Analyse
- Performance-Review (Query-Zeiten)
- Update-Status prüfen

### Quartalsweise
- Vollständiger Audit aller Quellen
- Nicht mehr genutzte Quellen archivieren/löschen
- Key-Rotation-Status prüfen
- Governance-Playbook updaten

---

**Version:** 1.0  
**Stand:** Dezember 2024  
**Nächste Review:** März 2025
