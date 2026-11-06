---
title: "RUNTIME-SL · Runtime-Beobachtungsbundle in Learninginputadmission"
stand: "2026-11-05"
rolle: "Architektonische Aussengrenze SL/OPT; keine Integrationsfreigabe"
authoritaet: "NONE"
---

# RUNTIME-SL · Runtime-Beobachtungsbundle in Learninginputadmission

**Klassifikation:** `DATEN` · `STATISCH_KONKRET`. **Richtung:** [HOST](</Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL/00 Systemindex/Aussenbereiche/HOST.md>) → [SL](../vault_exact/00%20Systemindex/Universen/SL.md.json).

## Konkreter Anschluss

**Letzter eigener Producer / tatsächlicher Übergeber:** [evaluate_runtime_observation_bundle_v1](../../../../../src/meta/learning_loop/runtime_observation_feedback_v1.py#L610).

**Erster fremder Consumer / bei Innenverbindung nächster eigener Consumer:** [evaluate_runtime_to_learning_input_v1](../../../../../src/meta/learning_loop/runtime_observation_feedback_v1.py#L712).

Aufnahme ist architektonisch eigenständig neben DDO. Gleiche Pythondatei für Observation- und Learninginputbau beseitigt die zwei Aufgaben nicht; die Datenquelle bleibt fremd.

## Vertrag und Bindungen

RuntimeToLearningInputRequest mit verifiziertem source_observation_body/ref/digest/status und gesonderten Performance-/Cost-/Execution-/Risk-/Reconciliationrefs.

runtime_session_id, environment/venue/instrument, strategy_version, created_at/builder/policy; output_digest und parent refs. Metrikreferenzen sind keine aufgelösten PnL-/Kosten-/Latenzeinheiten.

## Zustands- und Autoritätsgrenze

HOST verantwortet Beobachtungsquellen und deren Runtimeidentität. SL verantwortet die Zulässigkeit dieses getrennten Learningeingangs, nicht nachträglich dessen Markt-/Executionwahrheit.

Kein Transfer fremder Writer-/Core-/Risk-/Selection-/Promotion-/Executionauthority. Empfänger entscheidet selbst über Annahme; jede weitere Wirkung nur aus eigenem Vertrag.

## Wirkung beim Consumer

Empfangende Learninginputprüfung liefert VALID/INCOMPLETE/INVALID und eigenen runtime_to_learning_input-Vertrag. Optionaler Bundlewriter persistiert mit Manifest/Readback; kein DDO-Reducer-/Modellfitaufruf.

**Konkrete Aufruf-/Kompositionsbelege:** [main](../../../../../scripts/run_runtime_to_learning_input_v1.py#L36). Aufrufrichtung und Payloadrichtung können sich unterscheiden.

## Beleg und konkrete Grenze

Belegart: `STATIC_FUNCTION_BODY`. Quellbytes und Funktionszeilen sind im [Anschlussregister](../evidence/boundaries/anschlussregister.json) sowie [Quellenregister](../evidence/boundaries/quellenbindung.json) an HEAD `10d899b16356974bdd1f3c90f13681825cc09afe` und die tatsächlichen Worktreebytes gebunden. Kein Funktionsaufruf wurde dafür ausgeführt.

CLI ersetzt nicht die fünf fixturebasierten Default-Metrikrefs durch gemessene Zahlen; alte BTC-Guards gelten hier. Ein natürlicher Join in DDO/RealityGap/numerischen Meta ist nicht belegt.

## Spiegel auf beiden Seiten

[HOST](</Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL/00 Systemindex/Aussenbereiche/HOST.md>) und [SL](../vault_exact/00%20Systemindex/Universen/SL.md.json) verweisen auf denselben Datensatz `RUNTIME-SL`. Prüf- und Speicheranschlüsse stehen getrennt von Datenausgängen.

[Architektonische Außengrenzen SL und OPT](../vault_exact/00%20Systemindex/SL%20OPT%20Trennung/Aussenkanten%20Architektur/Aussenkanten%20SL%20und%20OPT.md.json)
