---
docs_token: DOCS_TOKEN_EQUITY_CONTINUOUS_PREPARATION_2026_11_03
status: working
scope: Local verification prepared, no actual continuous-operation approval
---

# Equity-Prüfungen vorbereitet; echter Dauerbetrieb gesperrt

Ausgangsrevision `a4459354489570ac361951b86c81d23fd7290898`. Auf den Auftrag zur Ausarbeitung wurden die interne Vergleichsregel, Prüfungen des vorhandenen Accounting-Bindings und die dokumentierte Freigabegrenze umgesetzt.

## Ergebnis

**256 relevante Tests bestanden.** Die vorhandenen Originaldaten bestehen die neue ausdrücklich gewählte interne Vergleichsregel. Ein zusätzlicher Prozess lädt außerdem einen synthetischen Accounting-Checkpoint mit Fill-/Funding-Replay. Ein weiterer Prozess erzeugt byteidentisch denselben neuen Bericht, während K1-Öffnung und Socket-Verbindungen ausdrücklich gesperrt sind. Keine neue Börsenabfrage, keine Orders, keine Transfers, keine Dienstaktivierung.

- Neuer lokaler Status: `LOCAL_VERIFICATION_PASS_RUNTIME_BLOCKED`.
- Ursprünglicher vollständiger Rekonstruktionshash bleibt `1ebacbce7afccaba7146785549be7e05d76cbff998c51f4f333eb0ea8e52c928`.
- Neues Ergebnis mit unverändertem Originalteil und separater interner Bewertung: `99d9506ef142e12f376aefb6204b86b69e03c6fafc8a3994082f856106212e28`.
- [Erster lokaler Abgleich](equity_continuous_preparation_v1_2026_11_03/real_originals_local_policy_receipt.json) und [erneuter gesperrter Offline-Prozess](equity_continuous_preparation_v1_2026_11_03/local_policy_restart_receipt.json).

„Präzisionsvertrag“ ist damit für diesen Arbeitsschritt eine interne, explizit konfigurierte Prüfregel. Ihre kleine Obergrenze reicht allein nicht: Es muss genau die festgelegte Darstellung vorliegen; ein nahe gelegener anderer Wert oder eine ungeklärte Funding-Differenz bleibt blockiert. Es gibt keine Journalanpassung und keine Behauptung über die interne Implementierung der Börse. [Vollständiger Vertrag](../specs/EQUITY_CONTINUOUS_VERIFICATION_PREPARATION_V1.md).

## Im bestehenden Binding korrigiert

Die neuen konkreten Szenarien haben mehrere bisher nicht ausreichend geprüfte Probleme des bestehenden Wrappers sichtbar gemacht: Schließungsgebühren wurden bereits im realisierten Ergebnis und nochmals im Gebührenkonto abgezogen; Slippage wurde zusätzlich zu ihrer Wirkung im Ausführungspreis abgezogen; die analytische Cash-Projektion übernahm diese doppelte Wirkung. Diese Pfade sind korrigiert. Die zugrunde liegenden kanonischen PnL-Primitiven bleiben unverändert.

Funding wird nun mit expliziter Ereignisidentität einmal signiert erfasst und über Schließungen und Neustarts erhalten. Neue Fills mit bereits verwendeter Identität, aber anderem Inhalt scheitern. Der erstmalige falsche Instrumentbezug wird ebenfalls abgewiesen. Ein idempotenter Replay verwendet den aktuellen Mark; fehlgeschlagene Fill-/Mark-Berechnungen ändern den letzten gültigen Zustand nicht teilweise.

Neue Version-2-Checkpoints erhalten die erforderliche Historie. Korruption, Pflichtdateiverlust, unvollständige Veröffentlichung, fremder Kernel-Owner, unbekannte Aktionen und fehlende Anfangswerte werden abgewiesen. Version-1-Originale wurden nicht migriert oder überschrieben. Ein aktiver realer Zustand wurde nicht geladen oder verändert.

## Aussagekraft der Prüfungen

Positiv geprüft sind kontrollierte lineare Long-/Short-Fälle mit unterschiedlichen Preisen und Multiplikatoren, Öffnung, Bewertung, Funding, Teilverkauf, vollständiger Schließung, Shell-Projektion und Neustart. Der längere Test enthält 500 Fills und 250 Funding-Ereignisse mit zehn Persistenz-/Reload-Zyklen. Ablehnungsfälle enthalten widersprüchliche Duplikate, verspätete Fills, fehlende reale Buchungsgegenstücke, Datenlücken, ungültige Meta-/Geldwerte und inkonsistente Checkpoints.

Die Preis-PnL- und Gebührenrollen wurden außerdem mit den [offiziellen OKX-PnL-Regeln](https://www.okx.com/en-eu/help/futures-pnl-calculation-rules) und den [offiziellen Gebühreninformationen](https://www.okx.com/en-eu/help/trading-fee-rules-faq) abgeglichen. Der Offlinekern behauptet weiterhin keine vollständige Venue-/Liquidationsgenauigkeit.

**Offen für eine spätere Betriebsfreigabe:** tatsächliche zusammenhängende Laufzeitbeobachtung, reale aktuelle Instrument-/Positionsbindung und unterstützte reale Bewertung. Die vorhandene echte Kontorekonstruktion bleibt auf den belegten Flat-Fall begrenzt. Inverse sowie sonstige nicht unterstützte Zustände werden nicht durch die kontrollierten linearen Fälle freigegeben. Ein unterbrochenes Bundle wird sicher abgewiesen; automatische Reparatur und Migration alter Laufzeitbestände sind nicht damit bewiesen.

U04 bleibt zurückgestellt. P01, der bestehende 29P-/Treasury-Kapital-Owner und ursprüngliche Lernbestand wurden nicht verändert. Der lokale Vorbereitungsabschnitt kann damit abgeschlossen werden, während die tatsächliche Betriebsfreigabe bewusst offen bleibt. Keine Remote-CI und kein GitHub-Push.

Prüf- und Quellenbindungen: [Abschlussmanifest](equity_continuous_preparation_v1_2026_11_03/verification_manifest.json).
