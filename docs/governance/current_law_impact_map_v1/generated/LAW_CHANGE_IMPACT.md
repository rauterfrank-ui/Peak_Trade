# Law Impact Map — Regeln und Änderungsfolgen

<!-- GENERATED FILE. DO NOT EDIT BY HAND. FROZEN_LAW_POLICY_VIEW AUTHORITY=NONE -->

```text
LAW_IMPACT_MAP_AUTHORITY=NONE
LAW_REFERENCE_IS_NORMATIVE=false
SOURCE_TAG=freeze/clean-system-2026-11-06-v1
SOURCE_COMMIT=c742a23c964901c1353fcf3468e618db9cb6ef42
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

Diese abgeleitete Sicht zeigt Regelquellen, statische Referenzen und Prüfbedarf. Die Definition und Durchsetzung einer Regel gehören zu ihrem Originalowner. Ein Pfad, Import oder Stringliteral belegt keine ausgeführte Consumerkette.

Einstiege: [Master Runbook](../../../../docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) · [System Atlas](../../../../docs/system_atlas/generated/SYSTEM_ATLAS.md).

## Bestand

40 explizite Regelreferenzen, 34 Fachverträge und 780 indexierte Policy-/Regeldateien. 52 dieser Dateien haben im erfassten Pythonbestand keine entdeckte statische Referenz.

- [Regelquellen](law_reference_index_v1.md): Originalowner, Anker und aktueller Digest.
- [Fachverträge](semantic_object_index_v1.md): Code-/Configzuordnung ohne neue Freigabe.
- [Vollständiger Dateiumfang](surface_census_v1.md): typisierte Policydateien und Referenzstellen.
- [Offene Beziehungen](unknown_and_conflict_v1.md): konkrete Unterschiede und Prüfbedarf.

## Prüfung einer Änderung

1. Geänderte Originalregel mit dem gebundenen Quellstand vergleichen.
2. Direkte Regelreferenzen, statische Import-/Pfadfundstellen und zugeordnete Fachverträge ermitteln.
3. Zahlen-, Einheiten-, Zeit-, Identitäts- und Zustandsvertrag am tatsächlichen Consumer prüfen.
4. Betroffene Prüfungen mit Originalinputs ausführen; unklassifizierte Folgen als offen belassen.
5. Quellenbindung und diese abgeleiteten Ansichten gemeinsam nachführen.

## Aussagegrenze

Die jetzige Dokumentprüfung kontrolliert Dateibestand, Syntax strukturierter Quellen, Digests, Quellanker, Referenzziele und deterministische Ausgabe. Sie erteilt kein Gesamturteil über die fachliche Richtigkeit sämtlicher Policies und bestätigt keinen durchgängigen Betrieb. Numerischer Wertverbrauch, Risikoentscheidung, Permit, Venuewirkung und produktives Apply brauchen jeweils ihre eigenen Nachweise.

## Erhaltene maschinell genutzte Dokumente

Diese Dateien sind Originaleingaben oder Schreibziele bestehender Module. Ihre Erhaltung macht sie zu keiner zusätzlichen aktuellen Systemlandkarte. Die jeweiligen Verwendungen sind statische Codebefunde.

- [docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md](../../../../docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md) · `MODEL_REGISTRY_VALIDATOR_INPUT`.
  [src/governance/validate_ai_matrix_vs_registry.py:49](../../../../src/governance/validate_ai_matrix_vs_registry.py).
- [docs/governance/PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md](../../../../docs/governance/PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md) · `EVIDENCE_GATE_MARKER_INPUT_NOT_CURRENT_SYSTEM_VIEW`.
  [src/ops/config_truth_alignment_contract_v1.py:715](../../../../src/ops/config_truth_alignment_contract_v1.py).
  [src/ops/single_future_canonical_runtime_deterministic_offline_evidence_v1/evidence_gate_v1.py:240](../../../../src/ops/single_future_canonical_runtime_deterministic_offline_evidence_v1/evidence_gate_v1.py).
  [src/ops/single_future_canonical_runtime_pre_activation_closure_v1/pre_activation_gate_v1.py:256](../../../../src/ops/single_future_canonical_runtime_pre_activation_closure_v1/pre_activation_gate_v1.py).
  [src/ops/single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1/evidence_gate_v1.py:219](../../../../src/ops/single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1/evidence_gate_v1.py).
- [docs/mindmap/INFOSTREAM_LEARNING_LOG.md](../../../../docs/mindmap/INFOSTREAM_LEARNING_LOG.md) · `LEARNING_LOG_WRITE_TARGET`.
  [src/meta/infostream/run_cycle.py:64](../../../../src/meta/infostream/run_cycle.py).
