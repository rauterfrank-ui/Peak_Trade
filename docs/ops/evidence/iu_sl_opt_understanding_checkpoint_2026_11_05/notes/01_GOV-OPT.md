---
title: "GOV-OPT · Governancegebundene Researchzulässigkeit an Surfaceprüfung"
stand: "2026-11-05"
rolle: "Architektonische Aussengrenze SL/OPT; keine Integrationsfreigabe"
authoritaet: "NONE"
---

# GOV-OPT · Governancegebundene Researchzulässigkeit an Surfaceprüfung

**Klassifikation:** `KONTROLLINPUT` · `STATISCH_KONKRET`. **Richtung:** [GOV](</Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL/00 Systemindex/Aussenbereiche/GOV.md>) → [OPT](../vault_exact/00%20Systemindex/Universen/OPT.md.json).

## Konkreter Anschluss

**Letzter eigener Producer / tatsächlicher Übergeber:** [resolve_optimizable_envelope_v1](../../../../../src/experiments/canonical_optimizable_envelope_v1.py#L286).

**Erster fremder Consumer / bei Innenverbindung nächster eigener Consumer:** [_validate_request_v1](../../../../../src/experiments/canonical_federated_surface_optimization_experiment_evidence_projection_v1.py#L199).

Hier muss die Autorität ausdrücklich getrennt bleiben: OPT darf eigene Experimente bauen, aber nicht seine zulässige Domain erzeugen oder erweitern. Resolverablage unter experiments ändert die Kontrollownerrolle nicht.

## Vertrag und Bindungen

Versionierte Envelopeauflösung mit Surface-/Owner-/Bounds-/Constraint-/Evidenceanforderungen und Auflösungsdigest.

surface_id/envelope_identity/version, owner_authorization_ref, resolution_digest, zulässige Domain/Beträge/Schrittweite/Riskrefs. Einheit je Surface, nicht universell ein Zahlenvektor. Keine Order-/Kapital-/Deploymentfreigabe.

## Zustands- und Autoritätsgrenze

Governance besitzt Definition/Geltung der erlaubten Surface; OPT besitzt lediglich die Anwendung dieser Schranke auf den eigenen Researchfall.

Kein Transfer fremder Writer-/Core-/Risk-/Selection-/Promotion-/Executionauthority. Empfänger entscheidet selbst über Annahme; jede weitere Wirkung nur aus eigenem Vertrag.

## Wirkung beim Consumer

OPT fragt den Resolver an und prüft erlaubte Surface und identischen Auflösungsdigest vor eigener Projektion. Generische M4-Synthetik löst separat NOT_AUTHORIZED auf und bleibt ausdrücklich offline.

**Konkrete Aufruf-/Kompositionsbelege:** [build_offline_research_context_v1](../../../../../src/experiments/canonical_optimization_universe_experiment_plane_v1.py#L131). Aufrufrichtung und Payloadrichtung können sich unterscheiden.

## Beleg und konkrete Grenze

Belegart: `STATIC_FUNCTION_BODY`. Quellbytes und Funktionszeilen sind im [Anschlussregister](../evidence/boundaries/anschlussregister.json) sowie [Quellenregister](../evidence/boundaries/quellenbindung.json) an HEAD `10d899b16356974bdd1f3c90f13681825cc09afe` und die tatsächlichen Worktreebytes gebunden. Kein Funktionsaufruf wurde dafür ausgeführt.

Registryeintrag und Researchresolution beweisen keine produktive Aktivierung. Der generische M4-Testpfad ist kein Nachweis einer autorisierten realen Surface.

## Spiegel auf beiden Seiten

[GOV](</Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL/00 Systemindex/Aussenbereiche/GOV.md>) und [OPT](../vault_exact/00%20Systemindex/Universen/OPT.md.json) verweisen auf denselben Datensatz `GOV-OPT`. Prüf- und Speicheranschlüsse stehen getrennt von Datenausgängen.

[Architektonische Außengrenzen SL und OPT](../vault_exact/00%20Systemindex/SL%20OPT%20Trennung/Aussenkanten%20Architektur/Aussenkanten%20SL%20und%20OPT.md.json)
