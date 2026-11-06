---
docs_token: DOCS_TOKEN_ACCOUNT_BILLS_OBSERVATION_AND_HISTORICAL_REPLAY_V1
status: working
scope: Observed account movements and historical replay; no equity or sizing authority
---

# Kontobewegungen und historische Buchführungsnachweise

Die historischen Bausteine werden erhalten. Der heutige Beobachtungspfad verwendet die vorhandene K1-Identitätsprüfung und den vorhandenen signierten GET-Transport. Er ergänzt eine Diagnose tatsächlicher Kontobuchungen; er erzeugt keinen neuen Kapitalverwalter und ersetzt keine Equity-Quelle.

## Historischer Umfang

[PR 6267](https://github.com/rauterfrank-ui/Peak_Trade/pull/6267) belegt einen einzelnen identitätsgebundenen SUI-Futures-Trade. Der bestehende Prüfer lässt sich auf den unveränderten Originaldateien erneut ausführen: beobachtetes Fill-PnL plus signierte Gebühr plus Funding plus Settlement entspricht exakt dem beobachteten realisierten PnL. Das ist kein allgemeiner Prüfer für beliebige Futures und kein Nachweis des ganzen Kontobestands. Die damalige Formel hat keinen expliziten Liquidationsstrafen-Term; eine Verallgemeinerung muss diesen Fall gesondert behandeln.

[PR 6468](https://github.com/rauterfrank-ui/Peak_Trade/pull/6468), [PR 6469](https://github.com/rauterfrank-ui/Peak_Trade/pull/6469) und [PR 6470](https://github.com/rauterfrank-ui/Peak_Trade/pull/6470) ratifizieren, verankern und registrieren einen genau datierten Anfangsbestand vom 14. September. Das ersetzt weder eine durchgehende Ereigniskette bis heute noch eine aktuelle Kontoidentitätsbindung. [PR 6491](https://github.com/rauterfrank-ui/Peak_Trade/pull/6491) trennt die versiegelte Rekonstruktion später vom aktuellen Sizing-Pfad.

`verify_historical_accounting_sources_v1` überprüft die gespeicherten Raw-Body-Hashes vor Wiederverwendung des bestehenden Trade-Prüfers und vergleicht Wert-, Zeit-, Kandidaten-, Ratifikations- und Ankerverweise der vier Dokumente. Diese Querprüfung ist keine neue Ratifikation und keine vollständige Neuzertifizierung ihrer damaligen Erwerbungskette. Originale bleiben unverändert.

## Heutige Beobachtung

`K1AccountObservationSourceV1.inspect_accounting_bills_v1` liest zuerst die konfigurierte Kontoidentität und danach ausschließlich das unfiltrierte Account-Bills-Archiv. `limit=100` ist fest; `after` ist ausschließlich eine positive native Bill-ID. Währungs-, Instrument-, Produkt- und andere Filter sind ausgeschlossen. Maximal sechs Seiten und eine Kontoabfrage, keine Wiederholung fehlgeschlagener Requests. Eine kurze Seite gilt nicht als Ende; erst eine leere Antwort beendet die Pagination. Eine wiederholte oder rückwärts laufende Cursorfolge wird abgewiesen.

`audit_bill_pages_v1` verbindet nur Seiten mit gleicher Kontobindung. Identische native Bill-IDs werden einmal gezählt; widersprüchliche vollständige Zeilen unter derselben ID werden abgewiesen. Zahlen müssen explizite endliche Dezimalstrings sein. Fehlende Werte sind keine Null. Salden werden getrennt nach Originalwährung in nativer ID-Reihenfolge verglichen; widersprüchliche Zeitreihenfolge wird abgewiesen. Weder EUR, USDC noch BTC werden ineinander umgerechnet.

Für jede Folgebuchung wird exakt geprüft, ob der vorherige beobachtete Saldo plus `balChg` den nächsten beobachteten Saldo ergibt. Die signierte Kontobewegung ist bereits gebucht: `pnl`, `fee`, Funding oder Settlement werden nicht nochmals hinzuaddiert. Der erste rechnerisch ableitbare Vorgängersaldo wird nicht als autorisierter Anfangsbestand verwendet. Grundlage der Feldbedeutung ist die [offizielle OKX-Dokumentation](https://www.okx.com/docs-v5/en/).

Ein erfolgreicher Vergleich beweist nur rechnerische Konsistenz der beobachteten Folge. Ausgleichende fehlende Buchungen, Retention, Vollständigkeit aller wirtschaftlichen Ereignisklassen und Equity-Bewertung offener Positionen sind damit nicht bewiesen. Leere Antworten beweisen keine Nullereignisse. Rohzeilen und Beträge werden nicht im Bericht gespeichert; die Seiten erhalten Inhaltsdigests. Ohne gespeicherte Rohseiten ist dieser heutige Bericht kein eigenständig neu berechenbarer Journalbestand.

## Bedienung und Grenzen

```sh
./scripts/pt -m scripts.ops.verify_historical_accounting_sources_v1
./scripts/pt -m scripts.ops.run_k1_account_observation_readiness_v1 --config config/ops/treasury_k1_account_source_v1.json --accounting-bills
```

Der zweite Aufruf prüft standardmäßig nur die Konfiguration. `--observe-once` wählt ausdrücklich reale K1-Lesezugriffe. `--accounting-bills` und `--treasury-inputs` sind gegenseitig ausgeschlossen. Ein tatsächlicher Bills-Bericht bleibt mit Exitcode 2 blockiert, solange vollständige Klassifikation und aktuelle Anfangsbestandsbrücke fehlen; ein HTTP-Erfolg wird nicht als fertige Buchführung bezeichnet.

Es bleiben die bisherigen Grenzen: keine Equity-Erzeugung, kein Sizing-Input aus dieser Diagnose, keine U04-/P01-Änderung, keine Änderung von Lernbeständen, keine Orders, Transfers oder Dienste. Der vorhandene Futures-Kern bleibt erhalten; sein simulierter Bridge-Aufruf und Standardanfangsbestand werden nicht in echte Kontoquelle umbenannt. Der ältere Spot-Ledger mit Cash-Notional-Buchungen wird nicht ungeprüft auf Futures angewandt.

Nachweise: [datierter Bericht](../evidence/EQUITY_ACCOUNTING_HISTORY_AND_BILLS_2026_11_03.md).

Fortschreibung vom 03.11.2026: [privates Originaljournal, aktueller Anker-/Kontoverbund und vollständiger beobachteter Bewegungsweg](REAL_EQUITY_WINDOW_RECONCILIATION_V1.md). Der damalige Beobachtungsschritt bleibt als Nachweis erhalten. Die neue Prüfung schließt die pauschale Anker-/Journal-/Klassifikationslücke für das datierte Fenster; der exakte allgemeine Venue-Präzisionsvertrag bleibt unbelegt.
