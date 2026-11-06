# Ursprüngliche Ebenen wieder vollständig lesbar: Quellenrestauration und Code-Abgleich

Stand 04.11.2026; Ist-Pin `68c687a64a3e767c19bf52d90b896cc598c6d62f`. Fortsetzung von Blueprint88, keine neue System-SSOT.

## Konkrete Wiederherstellung

Die beiden vollständigen ursprünglichen Self-Learning-Master und alle zwölf
historischen Phasenverträge liegen jetzt bytegenau als inerte Originaltexte im
Repo. Bisher waren die Master dort nur in ausgewählten Auszügen gesichert. Damit
sind Entwicklungsfolge, innere fachliche Funktionen, Authority-Trennung,
Minimal-Kreis, Gesamt-Definition-of-Done, Core-Attribution und ursprüngliche
Zusammenhänge ohne externe lokale Ordner vollständig an diesen Quellen lesbar.

[Grundfassung](originals/self_learning_master_base.original.txt),
[Core-gebundene Fassung](originals/self_learning_master_core_bound.original.txt),
[Herkunft und SHA256 aller Originale](restored_source_manifest.json),
[frühere Recovery-Provenienz](originals/original_master_recovery.provenance.json).
Die Fassungen werden nebeneinander erhalten. Sie beschreiben historische Ziele,
Varianten und damalige Aufträge; sie ersetzen weder heutiges Master Runbook noch
Quell-/Consumer-Prüfungen. „Vollständig“ bezieht sich hier auf diese konkreten
Originaldateien, nicht alle Quellen oder die Funktionsvollständigkeit des Systems.

## Jede ursprüngliche Phase und ihr heutiger Code

Phase0 ist die ursprüngliche Legacy-Adjudication/Authority-Firewall, keine
verschollene dreizehnte Rechenebene. Sie steht vollständig in beiden Mastertexten.
Ihre globale Erfüllung wird hier nicht aus späterer Modulexistenz abgeleitet.

- **SL01**: [Originalvertrag](originals/SL01-CANONICAL_EXPERIMENT_IDENTITY_V1.original.txt), [heutiger Owner](../../../../src/experiments/canonical_experiment_identity_v1.py). Einführungscode unverändert.
- **SL02**: [Originalvertrag](originals/SL02-CANONICAL_EXPERIMENT_MEMORY_V1.original.txt), [heutiger Owner](../../../../src/experiments/canonical_experiment_memory_v1.py). Einführungscode unverändert.
- **SL03**: [Originalvertrag](originals/SL03-CANONICAL_FAILURE_MEMORY_V1.original.txt), [heutiger Owner](../../../../src/experiments/canonical_failure_memory_v1.py). Einführungscode unverändert.
- **SL04**: [Originalvertrag](originals/SL04-CANONICAL_ROBUSTNESS_SUITE_V1.original.txt), [heutiger Owner](../../../../src/experiments/canonical_robustness_suite_v1.py). Einführungscode unverändert.
- **SL05**: [Originalvertrag](originals/SL05-CANONICAL_COMPARISON_SSOT_V1.original.txt), [heutiger Owner](../../../../src/experiments/canonical_comparison_ssot_v1.py). Einführungscode unverändert.
- **SL06**: [Originalvertrag](originals/SL06-CANONICAL_CHAMPION_CHALLENGER_V1.original.txt), [heutiger Owner](../../../../src/experiments/canonical_champion_challenger_v1.py). Einführungscode unverändert.
- **SL07**: [Originalvertrag](originals/SL07-CANONICAL_REALITY_GAP_STORE_V1.original.txt), [heutiger Owner](../../../../src/experiments/canonical_reality_gap_store_v1.py). Einführungscode unverändert.
- **SL08**: [Originalvertrag](originals/SL08-CANONICAL_REGIME_AWARE_EVALUATION_V1.original.txt), [heutiger Owner](../../../../src/experiments/canonical_regime_aware_evaluation_v1.py). Einführungscode unverändert.
- **SL09**: [Originalvertrag](originals/SL09-CANONICAL_PORTFOLIO_LEARNING_V1.original.txt), [heutiger Owner](../../../../src/experiments/canonical_portfolio_learning_v1.py). Einführungscode unverändert.
- **SL10**: [Originalvertrag](originals/SL10-CANONICAL_AUTOMATED_OFFLINE_RESEARCH_LOOP_V1.original.txt), [heutiger Owner](../../../../src/experiments/canonical_automated_offline_research_loop_v1.py). Vorhanden, später weiterentwickelt.
- **SL11**: [Originalvertrag](originals/SL11-CANONICAL_META_LEARNING_V1.original.txt), [heutiger Owner](../../../../src/experiments/canonical_meta_learning_v1.py). Vorhanden, später weiterentwickelt.
- **SL12**: [Originalvertrag](originals/SL12-CANONICAL_ADVANCED_SEARCH_V1.original.txt), [heutiger Owner](../../../../src/experiments/canonical_advanced_search_v1.py). Vorhanden, später weiterentwickelt.

Alle zwölf Einführungscodefassungen wurden **erneut gegen ihr genaues lokales
Git-Objekt revision:path** abgeglichen. Neun heutige Module sind bytegleich,
SL10/11/12 weiterentwickelt. Keine der in den zwölf historischen Einführungs-
Dateilisten als hinzugefügt genannten Dateien fehlt heute. Das ist eine
abgegrenzte überprüfte Menge, keine vollständige Git-/Datenträgerhistorie.
[Einzelresultate, Hashes und direkte Aufrufziele](phase_code_and_connection_parity.json).

Die drei späteren Änderungen werden erhalten und sind explizit lesbar:
[SL10-Diff](SL10_evolution.diff.txt), [SL11-Diff](SL11_evolution.diff.txt),
[SL12-Diff](SL12_evolution.diff.txt). Alte Fassungen werden nicht über heutigen
Code kopiert. Fachliche Funktionsverträge, SL-Entwicklungsphasen, M-Rollout,
MI-Forschungsleiter und tatsächliche innere Datenebenen bleiben verschiedene Achsen.

## Scheinbar fehlende Verbindung tatsächlich verfolgen

Der Abgleich der explizit importierten direkten Aufrufziele zwischen den zwölf
Modulen findet in SL10 zwei frühere direkte Phase2-Ziele nicht mehr im selben
Modul: Memory-Request und Memory-Builder. Der aktuelle Funktionskörper ruft jedoch
seinen Identitäts-/Owner-/Duplicate-Binder auf. Dieser konstruiert genau den
Phase2-Request und ruft den vorhandenen Memory-Builder auf. Das ist ein bestehender
Zwischenpfad, keine verlorene Verbindung. Direkte zusätzliche Verdrahtung würde
die vorhandene Bindungsprüfung umgehen oder verdoppeln.

Die Methode erfasst nur explizit aufgelöste importierte Aufrufziele innerhalb der
zwölf Phasenmodule. Dynamische Aufrufe, gesamte externe Abhängigkeiten, Ausführungs-
reihenfolgen und beobachtete Laufzeit werden dadurch nicht vollständig geprüft.
Der separat bereits belegte90-Test-Scope wird bei unverändertem Code-/Teststand
wiederverwendet; die korrigierte finale Kontroll-Datei ist gegen ihren PASS-Receipt
gehasht. Keine neue Testanzahl und keine globale Lernzertifizierung.
[Prüfbeleg und genaue Grenzen](verification_receipt.json).

Zusätzlich wurden die konkreten Python-Pfadnennungen der drei wiedergefundenen
Sept30-Golden-Vector-Berichte gegen das aktuelle Repo geprüft:75 Nennungen,
alle vorhanden. Das zählt Mehrfachnennungen über Berichte und beweist weder
historische Ausführung noch kompletten Corpus.
[Pfadweise Resultate](golden_report_referenced_path_check.json).

## Was daraus für die weitere Herstellung folgt

Franks Freigabe lautet: Fehlende Ebenen und Verbindungen werden ergänzt, wenn
historische Existenz und Rolle ausreichend belegt sind. Diese Freigabe ist
aufgenommen. Sie bedeutet keinen pauschalen Rückbau der heutigen Implementierung.
Scope bleibt erhalten. Für die hier geprüften ursprünglichen Produktdateien
wurde keine verlorene Implementierung gefunden; deshalb wird keine neue Kopie
oder Umgehungsverbindung als vermeintliche Wiederherstellung hinzugefügt.

Das verbleibende Integrationsproblem ist genauer: Der Original-Master beschreibt
Experiment-Runner, Messung, Shadow/Reality Gap und erneute Hypothese als Ziel.
Die einzelnen erhaltenen Module und ihre belegten begrenzten Verbindungen sind
vorhanden. Die vollständige tatsächlich ausgeführte Kette samt passender Daten-,
Kosten-, Core-, Zeit- und Kandidatenbindung ist weiterhin gesondert nachzuweisen.
Eine im Zielbild gezeichnete Verbindung beweist nicht, dass ihr später fehlender
Code tatsächlich existierte. Neue Umsetzung dieser Absicht wäre als neue Umsetzung
zu benennen und dürfte keine unbelegten Messgrößen/Identity-Aliase erzeugen.

Der [zusammenhängende Architektur-Einstieg](../self_learning_reconstruction_resolution_v1_2026_11_04/README.md)
bleibt die Navigation für DDO, Loop A/B/C, Optimierung, Meta, interne Golden Vectors,
GVEF und produktive Authority-Grenzen. Die24 Einzelfragen dort behalten ihre offenen
Nachweise. Diese Quellenrestauration schließt keine davon durch Dateiexistenz allein.
Originalledger und Scope unverändert, U04/GAP-0370 zurückgestellt. Keine Aktivierung.
