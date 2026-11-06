---
title: "RANK-OPT · Persistierte Auswahl an STEP29M-Researchbinding"
stand: "2026-11-05"
rolle: "Architektonische Aussengrenze SL/OPT; keine Integrationsfreigabe"
authoritaet: "NONE"
---

# RANK-OPT · Persistierte Auswahl an STEP29M-Researchbinding

**Klassifikation:** `DATEN` · `STATISCH_KONKRET`. **Richtung:** [RANK](</Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL/00 Systemindex/Universen/RANK.md>) → [OPT](../vault_exact/00%20Systemindex/Universen/OPT.md.json).

## Konkreter Anschluss

**Letzter eigener Producer / tatsächlicher Übergeber:** [load_and_validate_selection_v1](../../../../../src/ops/single_selected_future_policy_v1/persistence_v1.py#L156).

**Erster fremder Consumer / bei Innenverbindung nächster eigener Consumer:** [resolve_step29m_instrument_binding_from_selection_state_root_v1](../../../../../src/backtest/step29m_current_single_selected_future_dynamic_binding_v1.py#L170).

Vorhandenes Auswahlresultat wird zur eigenen Forschung übernommen; Parity-/Robustnessnachweis über Ranking ist dagegen eigenständiger Prüfbezug, keine Selectionauthority in OPT.

## Vertrag und Bindungen

Persistiertes Cap23-Auswahlartefakt nach Manifest-/Bindingvalidation; STEP29M konsumiert post-selection only.

selection_id/integrity_digest/state, canonical/native Instrument, now/max_age und Quellenartefakt. Kein übertragener Rankingauftrag und keine Kapital-/Ordermenge.

## Zustands- und Autoritätsgrenze

RANK bleibt alleiniger Auswahlwriter. OPT besitzt Bindung seines Offline-Evaluationsfalls.

Kein Transfer fremder Writer-/Core-/Risk-/Selection-/Promotion-/Executionauthority. Empfänger entscheidet selbst über Annahme; jede weitere Wirkung nur aus eigenem Vertrag.

## Wirkung beim Consumer

Researchresolver prüft Auswahlzustand/Freshness/Identität und baut Step29mInstrumentBindingV1; keine Neuauswahl und kein Lesen fremder Ranking-/Universesnapshots als Ersatz.

## Beleg und konkrete Grenze

Belegart: `STATIC_FUNCTION_BODY`. Quellbytes und Funktionszeilen sind im [Anschlussregister](../evidence/boundaries/anschlussregister.json) sowie [Quellenregister](../evidence/boundaries/quellenbindung.json) an HEAD `10d899b16356974bdd1f3c90f13681825cc09afe` und die tatsächlichen Worktreebytes gebunden. Kein Funktionsaufruf wurde dafür ausgeführt.

Der gelesene Legacyport enthält engere Instrument-/BTC-/SWAP-Guards als andere spätere Profile. Keine universelle Zulassung aller aktuellen Futures aus diesem alten Port ableiten.

## Spiegel auf beiden Seiten

[RANK](</Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL/00 Systemindex/Universen/RANK.md>) und [OPT](../vault_exact/00%20Systemindex/Universen/OPT.md.json) verweisen auf denselben Datensatz `RANK-OPT`. Prüf- und Speicheranschlüsse stehen getrennt von Datenausgängen.

[Architektonische Außengrenzen SL und OPT](../vault_exact/00%20Systemindex/SL%20OPT%20Trennung/Aussenkanten%20Architektur/Aussenkanten%20SL%20und%20OPT.md.json)
