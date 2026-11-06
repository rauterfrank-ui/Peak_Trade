# Pending-Mark-Horizont: abgelaufene Bars und getrennte Quellen

Basis: be7ca7f0153d5bb1afd34438dda340e8fa2614ff. Der ursprüngliche Pending-
Resolver (29d4ccd52, 06.10.2026) finalisierte jeden ersten Sample-Bar sofort.
Die vorhandene O4-Sessionbindung besitzt bereits den passenden Gegenvertrag:
finalize_due_bars verwendet die Ereigniszeit zum Finalisieren abgelaufener Bars.
Dieser vorhandene Helper wird jetzt auch beim Pending-Ingest und Replay benutzt.
Keine neue Intervall-, Scope-, Handels- oder wirtschaftliche Messfensterregel.

Jede angenommene Markbeobachtung wird gespeichert, auch ohne neuen fertigen Bar.
Damit bleiben OHLC und sample_count innerhalb einer Stunde im Replay erhalten.
Gezählt werden nur vollständig nach der Entscheidung beginnende Bars, passend
zur vorhandenen Snapshot-Selektion. Zwei frühe Samples in zwei Stunden ergeben
nicht mehr einen bereits vollständigen Zwei-Bar-Horizont.

Neue Eventdetails tragen pending_mark_observation.v2_elapsed_finalization.
Alte Markevents ohne diese Kennung werden unverändert erhalten und bei neuem
Replay abgewiesen; keine stille Umdeutung früher versiegelter Ergebnisse. Das
ist eine neue Eingangs-/Replayversion, keine neue Outcome-Klasse. Neue Ingests
prüfen kanonische/native/Venue-Identität, positive endliche Preise, Ereignis-/
Empfangschronologie sowie eine der zwei vorhandenen Quellenkennungen. Gemischte
Quellen, verspätete Events und unbekannte Kennungen schreiben keinen neuen Input.

Explizite Fixtures dürfen mit allow_test_fixture weiterhin isolierte Mess-Bars
aufbauen. Ein vollständiger Fixture-Horizont endet jedoch vor dem produktiven
Horizon-/Evaluation-/Learningpfad mit PENDING_OUTCOME_PROVENANCE_NOT_BOUND. Keine
Ersatzklasse wird erfunden. Als REAL_PUBLIC_OBSERVATION deklarierte Eingänge
benötigen homogene v2-Historie und gemessene Closure-Kenntniszeit nach allen
Empfangszeiten. Die Bezeichnung allein ist weiterhin kein Authentizitätsbeweis.
Der globale Evaluator-Default außerhalb dieses Pending-Aufrufers bleibt separat.

Prüfung: 16 anfänglich neue Fälle scheiterten am Ausgangscode. Final 64 PASS im
Pending-/Replay-/Markclock-/Zählerscope, plus 30 PASS in getrennten nachgelagerten
Evaluation-/O4-/Messartefaktdateien. Vier zusätzliche neue Fälle prüfen vollständige
injizierte öffentliche Eingangskomposition, gemessene Kenntniszeit, Clockkonflikt,
Duplikat/Out-of-order und den partiellen Vorentscheidungsbar. Der positive Public-
Kontrollfall ist ein injizierter Vertragstest, kein natürlicher Marktnachweis.

Drei alte Anschlussassertionen erwarteten sofortige Finalisierung und produktive
Fixture-Closure; diese Erwartungen sind ausdrücklich ersetzt, nicht als bereits
korrekte Altregressionen ausgegeben. Die Terminal-CLOSED-Prüfung verwendet nun
sichtbar einen konstruierten Terminalzustand statt einer falschen Fixture-Closure.
Eine zwischenzeitliche neue Assertion verwendete den falschen State-Text
IN_PROGRESS statt des bestehenden IN_PROGRESS_BAR; korrigiert ohne Codeänderung.
Vorherquellen und fehlgeschlagene Zwischenresultate bleiben erhalten.

Offen: Journal-vs-Index-Schreibreihenfolge, gesamte Crash-/Writer-Semantik,
vollständige dauerhafte Messartefakte und natürliche Quell-/Aktualitätsnachweise.
Keine Gesamtbetriebs- oder Lernfreigabe; geschütztes ursprüngliches Ledger bleibt
unverändert. Keine Netzwerk-, Credential-, Dienst- oder GitHub-Aktion.

[Quell-/Prüfbindungen](receipt.json), [anfängliche Fehler](before.xml),
[finaler Scope](final_scope.xml), [nachgelagerte Prüfungen](downstream.xml).
