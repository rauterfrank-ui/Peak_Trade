# Ausführbarer nächster Forschungsversuch mit späterem Meta-/GVEF-Bezug

Stand 04.11.2026; Basis `2ed94965facb87bb24eaa386b44d78c233be8dc2`, neue Implementierung durch Quellhashes gebunden.
Fortsetzung von Blueprint89 unter Master Runbook; keine neue System-SSOT.

## Was jetzt tatsächlich ergänzt ist

Der neue [Kompositions-Owner](../../../../src/experiments/canonical_search_candidate_research_execution_v1.py)
verbindet einen ausdrücklich PROPOSED Search-Kandidaten mit einem ausdrücklich
übergebenen Offline-Experimentlieferanten, anschließend dem vorhandenen Phase10-
Loop und einem erneut verwendbaren ResearchResultMetaInputV1. Eine begrenzte
zweite Funktion komponiert vorhandenes Research→Phase11→Search mit genau diesem
nächsten Versuch. Bestehende Owner und Definitionen wurden nicht verändert.

Das setzt die im ursprünglichen Master §§3.1/15/22 belegte fachliche Verbindung
Runner→Memory→Rückkopplung weiter um. Es sind **neue ausführbare Verbindungen auf
Basis rekonstruierter Absicht**, keine Behauptung wiedergefundener alter Codebytes.
Franks Ergänzungsauftrag umfasst diesen Schritt. Der alte Search-Owner bleibt
reine Kandidatenerzeugung; seine historischen Proposal-Records werden nicht auf
executed=true umgeschrieben. Ein separates Ausführungsartefakt hält den späteren
Vorgang fest. [Vertrag](../../specs/CANONICAL_SEARCH_CANDIDATE_RESEARCH_EXECUTION_V1.md).

## Tatsächlich durchlaufener Kontrollfall

Drei aus expliziten Return-Arrays berechnete Kontrollversuche benutzen von Anfang
an native fast_window/slow_window-Namen. Sie teilen denselben synthetischen
Kurvenfall und sind keine drei unabhängigen Marktbeobachtungen. Vorhandene
Robustheit/Failure Memory/Meta leiten daraus ein Overfit-Region-Proposal ab.
Bei gleichem Suchbudget1 wechselt der tatsächlich vorgeschlagene Kandidat von
fast_window=10, slow_window=50 auf fast_window=10, slow_window=100.

Genau der zweite Kandidat wird durch den neuen ausdrücklichen Eingang an einen
lokalen Testlieferanten übergeben. Dieser ruft drei echte vorhandene MV2-Research-
Backtest-Engines auf den chronologisch getrennten Train-/Validation-/Holdout-
Slices von768 deklarierten synthetischen Stundenbars auf. Die beobachtete Strategie-
Provenienz enthält genau die ausgewählten nativen Parameter. Engine-Signal-Digest
und MV2-Replay-Signal-Digest stimmen jeweils überein. Das ist der vorhandene
Research-Replay-Pfad mit dessen bekannten Einschränkungen, kein vollständiger
aktueller produktiver Core-/Attributionsnachweis.

Der bestehende Statistik-Owner wird ausdrücklich mit periods_per_year=1 auf den
tatsächlichen Engine-Equity-Kurven aufgerufen. Damit stimmt Sharpe mit dem
nicht annualisierten Robustheitsvertrag überein; kein unbekannter Einheitenfaktor
wird geraten. Train-Sharpe0.03688030075443945, Validation−0.07216878364870323,
Holdout0.05228598850098903. Die Memory-Metrik heißt ausdrücklich **oos_sharpe**,
weil sie nur den Holdout betrifft. Die vollen Splitbeobachtungen und exakten
Equity-/Input-CSV-Bytes bleiben erhalten. Kein Sortino oder fehlendes Verfahren
wird mit einem erfundenen Wert ersetzt.

[Kontrolleingänge](artifacts/source_inputs.json), [Ausgangssuche](artifacts/before_search.json),
[Messungen](artifacts/observed_splits.json), [Engine-Konfiguration](artifacts/native_cfg.json),
[synthetische Bars](artifacts/native_bars.csv), [Ausführungspaket](artifacts/execution_packet.json).

## Konkrete Beweisverbindung zum späteren metasemantischen Bereich

Der [maschinenlesbare Wirkungs-/Bedeutungsnachweis](metasemantic_witness.json)
verbindet die tatsächlich verwendeten Experiment-IDs, Frage/Proposal-IDs,
Suchentscheidung, gemessenen Parameter, Dataset-/Signal-/Loop-Digests,
Memory-Metrik und späteren Meta-Eingang. Er unterscheidet Daten, Interpretation,
Forschungswahl und tatsächliche Consumer-Wirkung statt nur Pfeile zu benennen.

Das gemessene Ergebnis läuft durch die vorhandenen Memory-/Robustheits-/Vergleichs-
Owner zurück in den bestehenden Meta-Adapter und Phase11. Dort ist dieselbe
Experiment-/Loop-Identität nachgewiesen. Der späteren Meta-Auswertung fehlen aber
für mehrere Fragen weitere Fähigkeiten/Beobachtungen. Insbesondere benötigt ihre
OOS-Survival-Aussage mehr als den einzelnen gemessenen Holdout. Sie meldet bei
sample_size1 INSUFFICIENT_EVIDENCE, keine neue Qualitäts- oder Kausalbehauptung.
[Späterer tatsächlicher Meta-Output](artifacts/later_meta.json).

Zusätzlich besteht ein expliziter Bezug zum vorhandenen GVEF-SelfLearning-Evaluator:
Seine kanonischen Artefakte verbieten Floats. Das vollständige numerische Paket
wird deshalb **ohne Zahlenkonvertierung** als kanonische UTF8-JSON-Datei erhalten.
Eine floatfreie Referenz bindet ihren relativen Pfad und den SHA256 der exakten
Dateibytes. Der GVEF-Evaluator verarbeitet diese Referenz als MECHANISM_TEST_EVIDENCE.
Sein PASS besagt weiterhin Artefakt-/Boundary-Prüfung; er wertet damit nicht die
fachliche Lernqualität sämtlicher numerischen Felder aus.

[Exakte numerische JSON-Bytes](artifacts/executed_research.canonical.json),
[GVEF-Referenz](artifacts/gvef_reference.json),
[tatsächliches GVEF-Ergebnis](artifacts/gvef_packet_evaluation.json).

Der neue Leser prüft den Bytehash, kanonische Darstellung, Referenzidentitäten und
die vorhandenen Search-/Phase10-Verträge vor erneuter Meta-Nutzung. Nach dieser
Serialisierung/GVEF-Referenzprüfung und dem Reload entsteht **derselbe vollständige
spätere Meta-Output**, inklusive seiner fehlenden Evidence. Manipulierte Bytes,
Referenz-IDs, veraltete Digests und abweichender Meta-Eingang werden abgewiesen.
[Meta-Resultat nach tatsächlichem Reload](artifacts/later_meta_after_gvef_reference_reload.json).

Drei Hashbedeutungen bleiben getrennt: execution content_digest bindet den
Owner-Inhalt ohne sein eigenes Digestfeld; payload_sha256 bindet alle exakten
serialisierten Dateibytes; sl.artifact_digest bindet die floatfreie GVEF-Referenz.
Keine davon beweist Quellenauthentizität oder ökonomischen Nutzen. Der rohe
Dataset-CSV-SHA256 wird zusätzlich durch den bestehenden Phase1-Owner in dessen
dataset-Domaene gebunden; er ist daher nicht gleich dessen dataset_digest. Ebenso
ist ein Strategy-Provenienz-Digest nicht automatisch ein Phase1-Parameterdigest.

## Prüfungen, Erhaltung und Grenzen

**32 neue Tests PASS**, [Originalausgabe](tests.xml),
[Tests](../../../../tests/experiments/test_canonical_search_candidate_research_execution_v1.py).
Sie prüfen auch echte bestehende Memory-/Failure-/Gap-Stores mit Persistenz und
Reload in temporären Verzeichnissen sowie die Ablehnung abweichender Kandidaten
vor dem persistierenden Phase10-Aufruf. Kein Betriebssystem-Neustart- oder
Mehrdatei-Transaktionsbeweis. Ruff/Format PASS. Frühere90/128 PASS bleiben getrennte
gebundene Scopes und werden nicht zu dieser Zahl addiert.

Die Daten sind kontrolliert synthetisch. Ancillary Core-/Kosten-/Identitätswerte,
Champion-Score und Shadow-/Reality-Gap-Kontext enthalten ausdrücklich Fixture-
Material; COMPLETE ist deren Strukturstatus, keine aktuelle Quellenbeglaubigung.
Die im Kontrollfall serialisierten August-Zeitpunkte sind Szenariozeiten der
Vertrags-Fixtures, keine Behauptung tatsächlicher Ausführung im August. Die hier
gebundenen Tests wurden am04.11.2026 ausgeführt.
Funding bleibt NOT_BOUND, economic_interpretation_allowed=false und Robustheit
BLOCKED. Nichtfinite Ausgangsmetriken sind namentlich dokumentiert. Die neuen
Funktionen bestätigen weder natürliche Labelherkunft noch besseren Forecast,
inkrementellen Feature-Nutzen oder nützliche autonome Gesamtfunktion. Regime-/
Portfolio-Owner sind durch diesen Schritt nicht automatisch überall aufgerufen.

Ein Provider-Aufruf je expliziter Komposition ist kein installierter Scheduler
und keine Sandbox für beliebigen Caller-Code. Vergleichs-/Gap-Kontext und
Messkonventionen bleiben Verantwortung des konkreten Lieferanten. Die alte
fast/slow-Kontrollidentität wurde nicht umbenannt oder rückwirkend ausgeführt.
Dieser neue native Fall schließt eine konkrete kontrollierte Ausführungslücke;
er ist kein pauschaler Abschluss aller24 Rekonstruktionsfragen.

[Quellbindungen](source_bindings.json), [Artefakthashes](artifact_manifest.json),
[Receipt](receipt.json), [Scope-Erhaltung](scope_preservation.json).
Alle bestehenden Implementierungen, Konfigurationen und Original-Learning-Ledger
bleiben erhalten. U04/GAP-0370 zurückgestellt. Keine Aktivierung, Dienste, Orders,
produktive Parameteränderung, Veröffentlichung oder externen Schreibzugriffe.

## Zusätzlicher Nachweis aus dem gespeicherten Commit

Nach Commit1c34978282ede5aa4e25542bbb83fb7360d7d10b wurde die gesamte
Artefaktmenge mit git show revision:path aus Git-Objekten gelesen. Alle15
Artefakthashes stimmen. Der verifizierte numerische GVEF-Bezug liefert auch mit
diesen gespeicherten Bytes denselben vollständigen späteren Meta-Output. Das
prüft zusätzlich die tatsächliche Repo-Aufnahme einschließlich der vier explizit
aufgenommenen synthetischen CSV-Dateien. Es ist kein neuer natürlicher Lauf.
[Ergebnis](git_numeric_roundtrip.json), [lesender Wiederholungsprobe-Quelltext](git_numeric_roundtrip_probe.py.txt).
