# Regulärer Messlieferant und konkrete Funding-Verbindung

Stand04.11.2026, Basis `df645ae88eddd2b207ff94de9f75ddbd17634b94`, neue Dateien durch Quellhashes gebunden.

Der [neue reguläre Owner](../../../../src/experiments/canonical_native_research_measurements_v1.py)
misst den vollständigen nativen Research-Engine-Pfad und drei chronologische Splits.
Er benutzt keine Test-Fixture-Producer. Dataset und Konfiguration sind bytegebunden;
Phase1-Domänen prüfen Parameter, Dataset und sechs quellspezifische Komponenten:
Fee, Slippage, Funding-Konfiguration, Risk, Single-Instrument-Portfolio und tatsächliche
Splitgrenzen. Die vorhandenen Canonical-Owner behalten ihre Definitionen. Auch nach
neuer cfg-Hashbildung werden geänderte Kosten/Risiken gegen dieselbe alte Kandidaten-
Identität vor Engine-Aufruf abgewiesen. Core/Feature/Git-Herkunft wird dadurch nicht
extern authentifiziert.

Der volle Renditepfad wird nicht aus separat zurückgesetzten Splitkurven zusammengesetzt.
Er speist vorhandene Monte-Carlo-, Block-Bootstrap-, Rolling-OOS- und Crash-Owner.
Alle vier sind im Kontrollfall tatsächlich ausgewertet. Fehlende weitere Eingänge
bleiben offen. Nichtfinite Metriken werden mit Status und null erhalten; kein
erfundener Sortino/Turnover/Stability-Wert. Sharpe wird durch den vorhandenen Stats-
Owner ausdrücklich nicht annualisiert berechnet. Metriknamen nennen die noch nicht
quantitäts-/cashflowgebundene Funding-Basis.

[Messungen und Equity-Kurven](artifacts/measurement_receipt.json),
[tatsächlicher Phase10-Durchlauf](artifacts/execution.json),
[Status und verbleibende konkrete Verpflichtungen](status_and_obligations.json),
[späteres Meta](artifacts/later_meta.json),
[identisches Meta nach Referenz-Reload](artifacts/later_meta_after_reference_reload.json).
Szenariozeiten sind Fixture-Zeiten, keine behauptete Ausführung im August.

## Der offene Funding-Punkt ist jetzt konkret belegt

Der alte Funding-Owner berechnet aus einer integerkonvertierten position_series.
Der Economic-Viability-Caller übergibt dafür wiring_result.signals. Diese Signale
sind keine tatsächlichen gehaltenen Mengen. Die Simulation hält hier Positionen
mit9.899947659083931 beziehungsweise10.348220336271233 Einheiten; an84 strikt
zwischen Ein- und Ausstieg liegenden Funding-Zeitpunkten ist das gemappte Signal0.
Damit darf weder fehlende Kostenwirkung noch zero funding aus diesem Signal
abgeleitet werden.

Zusätzliche kontrollierte Intervention: Nur das Funding-Binding wird aktiviert;
Daten, Parameter, Anfangscash und Risiko bleiben gleich. Die sourcegebundenen
Experimentidentitäten unterscheiden sich korrekt. Modellversion meldet gebunden,
die volle Engine-Equity und die Signale bleiben identisch. Das ist kein Nachweis
einer gebuchten Funding-Wirkung. Der [vollständige Probe-Befund](artifacts/funding_binding_effect_probe.json)
hält die tatsächlichen Mengen, Funding-Zeitpunkte und die getrennte Unit-Proxy-
Berechnung fest. Zukünftige Schließung muss Menge, Settlement-Zeitpunkt, Cashflow
und tatsächliche Equity-/Risk-Wirkung erhalten; bloßes Setzen eines BOUND-Labels
ist keine Reparatur.

Codeanker: [Funding-Owner](../../../../src/backtest/funding_model_v1.py),
[derzeitiger Economic-Viability-Caller](../../../../src/backtest/economic_viability_evidence_v1.py),
[vorhandener beobachteter Funding-Buchungsport](../../../../src/ops/productive_futures_accounting_runtime_binding_v1/accounting_engine_v1.py).
Der Buchungsport nimmt signierte beobachtete Beträge, keine bloßen Raten entgegen.
Diese Rollen bleiben getrennt. Bestehende Funding-/Accounting-Implementierungen
werden in diesem Checkpoint nicht überschrieben.

18 neue Tests PASS: [XML](tests.xml), [Tests](../../../../tests/experiments/test_canonical_native_research_measurements_v1.py).
Ruff/Format PASS. Vorherige32 PASS werden nicht zu dieser Zahl addiert.
[Quellbindungen](source_bindings.json), [Artefakthashes](artifact_manifest.json),
[Scope-Erhaltung](scope_preservation.json), [Receipt](receipt.json).
Keine globale Vollständigkeits-, Profitabilitäts- oder Betriebsfreigabe.
