# Missing Features – Prioritized (heuristic)

## infra
- **3. Known Limitations (PEAK_TRADE_V1_KNOWN_LIMITATIONS.md)**: {'Bereich': '**Infra**', 'Fehlendes Feature': 'Horizontale Skalierung / Multi-Instance'}
- **4. Roadmap „bis Finish“ (INSTALLATION_UND_ROADMAP_BIS_FINISH)**: {'Phase': '**15**', 'Thema': 'Cloud & Scalability', 'Fehlende Features (Auszug)': 'Kubernetes, Docker-Compose, AWS/GCP/Azure, Auto-Scaling, Load-Balancing, Multi-Region'}

## risk
- **3. Known Limitations (PEAK_TRADE_V1_KNOWN_LIMITATIONS.md)**: {'Bereich': '**Risk**', 'Fehlendes Feature': 'Automatische Position-Liquidation bei Limit-Verletzung'}
- **4. Roadmap „bis Finish“ (INSTALLATION_UND_ROADMAP_BIS_FINISH)**: {'Phase': '**16**', 'Thema': 'Advanced Risk & Portfolio', 'Fehlende Features (Auszug)': 'VaR/CVaR, Stress-Testing, Portfolio-Optimization (Markowitz, Black-Litterman), Risk-Parity, Factor-Models, Attribution'}
- **7. Einordnung**: {'Kategorie': '**Research-Track**', 'Bedeutung': 'Sweeps, Metriken, Heatmaps, Vol-Regime-Wrapper, Regime-adaptive Strategien, Auto-Portfolio, Nightly-Sweeps, Feature-Importance.'}

## execution
- **3. Known Limitations (PEAK_TRADE_V1_KNOWN_LIMITATIONS.md)**: {'Bereich': '**Live/Execution**', 'Fehlendes Feature': 'Echte Live-Order-Ausführung (blockiert durch SafetyGuard / LiveNotImplementedError)'}
- **3. Known Limitations (PEAK_TRADE_V1_KNOWN_LIMITATIONS.md)**: {'Bereich': '**Live/Execution**', 'Fehlendes Feature': 'Testnet ohne Dry-Run (echte Testnet-Orders)'}
- **3. Known Limitations (PEAK_TRADE_V1_KNOWN_LIMITATIONS.md)**: {'Bereich': '**Exchange**', 'Fehlendes Feature': 'Multi-Exchange (nur Kraken; Binance, Coinbase etc. fehlen)'}
- **3. Known Limitations (PEAK_TRADE_V1_KNOWN_LIMITATIONS.md)**: {'Bereich': '**Web-Dashboard**', 'Fehlendes Feature': 'POST/PUT/DELETE (Order-Erzeugung, Start/Stop aus Web-UI)'}
- **3. Known Limitations (PEAK_TRADE_V1_KNOWN_LIMITATIONS.md)**: {'Bereich': '**Daten**', 'Fehlendes Feature': 'Multi-Exchange-Datenquellen / aggregierte Feeds'}
- **4. Roadmap „bis Finish“ (INSTALLATION_UND_ROADMAP_BIS_FINISH)**: {'Phase': '**13**', 'Thema': 'Production Live-Trading', 'Fehlende Features (Auszug)': 'Live-Orders via CCXT, Multi-Exchange, Order-Routing/Smart-Order-Routing, Fill-Tracking, Live-PnL, Emergency-Stop (Governance-Review)'}

## features
- **2. Architektur-Vision vs. Implementierung (trading_bot_notes / Feature-Engine)**: {'Feature (Vision)': '**Feature-Engine als zentrale Schicht**', 'Status': '❌ Fehlt', 'Anmerkung': '`src/features/` ist nur Placeholder („wird später mit ECM-Features gefüllt“). Kein dediziertes Modul „Research & Feature-Engine“.'}
- **2. Architektur-Vision vs. Implementierung (trading_bot_notes / Feature-Engine)**: {'Feature (Vision)': '**Indikatoren (TA)**', 'Status': '✅ Teilweise', 'Anmerkung': 'In Strategien/Regime verteilt (MA, RSI, ATR, Vol-Score etc.), nicht als einheitliche Feature-Pipeline.'}
- **2. Architektur-Vision vs. Implementierung (trading_bot_notes / Feature-Engine)**: {'Feature (Vision)': '**Regime-Labels**', 'Status': '✅ Vorhanden', 'Anmerkung': '`src/regime/`, `src/core/regime.py`, `src/analytics/regimes.py`.'}
- **2. Architektur-Vision vs. Implementierung (trading_bot_notes / Feature-Engine)**: {'Feature (Vision)': '**Volatilitäts-Cluster**', 'Status': '✅ Teilweise', 'Anmerkung': 'Vol-Regime/Labels vorhanden; „Cluster“-Pipeline nicht als eigenes Feature-Modul.'}
- **2. Architektur-Vision vs. Implementierung (trading_bot_notes / Feature-Engine)**: {'Feature (Vision)': '**ECM-Fenster / ECM-Features**', 'Status': '❌ Fehlt', 'Anmerkung': 'In `src/features/__init__.py` als „später“ genannt, nicht implementiert.'}
- **2. Architektur-Vision vs. Implementierung (trading_bot_notes / Feature-Engine)**: {'Feature (Vision)': '**Sentiment (News/Makro/Krypto-Onchain)**', 'Status': '❌ Fehlt', 'Anmerkung': 'In trading_bot_notes als „optional, später“ genannt.'}
- **2. Architektur-Vision vs. Implementierung (trading_bot_notes / Feature-Engine)**: {'Feature (Vision)': '**Orderbuch-/Tickdaten**', 'Status': '❌ Fehlt', 'Anmerkung': 'In trading_bot_notes als „später“ genannt.'}
- **4. Roadmap „bis Finish“ (INSTALLATION_UND_ROADMAP_BIS_FINISH)**: {'Phase': '**14**', 'Thema': 'Advanced Analytics & ML', 'Fehlende Features (Auszug)': 'LSTM/Transformer Predictions, Reinforcement Learning, **Sentiment-Analysis**, **Feature-Engineering-Pipeline**, Model-Training, Online-Learning'}
- **7. Einordnung**: {'Kategorie': '**Architektur-Vision**', 'Bedeutung': 'Feature-Engine, Sentiment, Orderbuch/Tick, ECM – in Vision/Docs genannt, nicht als durchgängige Schicht umgesetzt.'}
- **7. Einordnung**: {'Kategorie': '**Stubs/Placeholder**', 'Bedeutung': 'Kill-Switch RiskHook, PagerDuty, WP0C-Adapter, einige R&D-Strategien, `src&#47;features`, Meta-Labeling Feature-Engineering.'}

## streaming
- **3. Known Limitations (PEAK_TRADE_V1_KNOWN_LIMITATIONS.md)**: {'Bereich': '**Web-Dashboard**', 'Fehlendes Feature': 'SSE/WebSocket (nur Polling)'}
- **3. Known Limitations (PEAK_TRADE_V1_KNOWN_LIMITATIONS.md)**: {'Bereich': '**Daten**', 'Fehlendes Feature': 'Real-Time-WebSocket-Streams (nur REST/Polling)'}
- **4. Roadmap „bis Finish“ (INSTALLATION_UND_ROADMAP_BIS_FINISH)**: {'Phase': '**12**', 'Thema': 'Real-Time Data & Streaming', 'Fehlende Features (Auszug)': 'WebSocket-Integration, Real-Time-Signale, Streaming-Backtest-Engine, Latency-Monitoring, Order-Book-Analytics, Tick-Level-Backtests'}
- **7. Einordnung**: {'Kategorie': '**v1.0 bewusst ausgenommen**', 'Bedeutung': 'Live-Execution, Multi-Exchange, Web-Auth, WebSocket, ML-Strategien, Auto-Liquidation, 100 % Coverage, API-Doku, Skalierung.'}
- **7. Einordnung**: {'Kategorie': '**Roadmap 2026**', 'Bedeutung': 'Phasen 11–17 (Optimization, Streaming, Live, ML, Cloud, Risk-Parity, Community).'}

## web
- **3. Known Limitations (PEAK_TRADE_V1_KNOWN_LIMITATIONS.md)**: {'Bereich': '**Web-Dashboard**', 'Fehlendes Feature': 'Authentifizierung, Access-Control, Benutzerverwaltung'}
- **3. Known Limitations (PEAK_TRADE_V1_KNOWN_LIMITATIONS.md)**: {'Bereich': '**Daten/Assets**', 'Fehlendes Feature': 'Corporate Actions (Splits, Dividenden), Futures/Options (Spot-Fokus)'}

## research
- **4. Roadmap „bis Finish“ (INSTALLATION_UND_ROADMAP_BIS_FINISH)**: {'Phase': '**11**', 'Thema': 'Advanced Strategy Research', 'Fehlende Features (Auszug)': 'Genetic Algorithm, Bayesian Optimization, Adaptive Parameter-Tuning, Multi-Objective, Strategy-Ensemble, Auto-ML Strategy-Selection'}

## other
- **3. Known Limitations (PEAK_TRADE_V1_KNOWN_LIMITATIONS.md)**: {'Bereich': '**Strategien**', 'Fehlendes Feature': 'ML-basierte Strategien, komplexe Multi-Factor-Modelle'}
- **3. Known Limitations (PEAK_TRADE_V1_KNOWN_LIMITATIONS.md)**: {'Bereich': '**Testing**', 'Fehlendes Feature': '100 % Test-Coverage'}
- **3. Known Limitations (PEAK_TRADE_V1_KNOWN_LIMITATIONS.md)**: {'Bereich': '**Doku**', 'Fehlendes Feature': 'Automatisch generierte API-Doku (OpenAPI/Swagger)'}
- **4. Roadmap „bis Finish“ (INSTALLATION_UND_ROADMAP_BIS_FINISH)**: {'Phase': '**17**', 'Thema': 'Community & Open-Source', 'Fehlende Features (Auszug)': 'Open-Source-Release, Contributing-Guide, Plugin-System für Community-Strategien'}
