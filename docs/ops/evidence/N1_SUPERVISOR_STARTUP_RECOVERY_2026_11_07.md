---
docs_token: DOCS_TOKEN_N1_SUPERVISOR_STARTUP_RECOVERY_2026_11_07
status: implemented_bounded_offline_with_open_acceptance
authority: NONE
runtime_authorization_effect: NONE
---

# N1-Hoststart: Originalübergang aufklären, aktuelle Freigabe getrennt halten

Basis ist ba01032d7c1e423bd75287896e79b1739d7ddc5b, nach dem Merge von PR 7183. Der [maschinenlesbare Beleg](N1_SUPERVISOR_STARTUP_RECOVERY_2026_11_07.json) bindet Quellen und Prüfungen. Der [Originalvertrag](../specs/PRODUCTIVE_N1_POST_CLOSE_CONTINUATION_V1.md) beschreibt die Schnittstelle.

## Änderung und tatsächliche Wirkung

Der vorhandene Standing-Supervisor kann einen expliziten ursprünglichen Post-Close-Startkontext übernehmen. Er prüft Originalwriter, dieselbe Topologiebasis, dauerhafte Budgetwurzel, Account, vollständige Instrumentgeneration und den erhaltenen Übergangsbeleg. Die neue private Beobachtung stammt vom bestehenden Budgethost. Offene Orders oder ungelöste Ausführungsreconciliation sperren die Fortsetzung.

Die ursprüngliche Fortsetzung repariert ausschließlich einen vorbereiteten Originalabschluss und dessen historischen ACK. Der Startanschluss akzeptiert CONSUMING und ACKED; MEMBERSHIP_STORED und fehlende Übergänge bleiben hier gesperrt. Vorbereitete neue Übergänge benötigen ihren ursprünglichen eigenen Ablauf. Die Recovery läuft vor WP02 und vor einem neuen Corezyklus; bei einem Fehler wird der Hostowner geschlossen.

Der historische ACK schaltet das Budget nicht frei. Der normale Hostpfad verlangt an der bestehenden Entry-Schnittstelle weiterhin frische kanonische Kapital-/Portfoliofacts. Die Scope-API des Budgetowners liefert nur seine dauerhafte Adresse und den Account, auch nach Schließung; sie ist kein Admissiontoken.

Die bisherige Unified-Recovery vermischte tatsächlich ausgeführte Beobachtungsschritte mit Beispielen für Order-Lifecycle, Reservation-Enums, Treasuryguards und Safetyregeln. Diese Beispiele stehen jetzt separat als contract_checks. Vollständige Runtime-/Finanzrecovery bleibt unbelegt. Der Supervisor meldet deshalb observation_recovery_completed separat; die breite Pre-External-Admission darf daraus kein unified_restart_safe ableiten.

## Prüfungen

Die gezielte Auswahl aus Hoststart, Supervisor, Budgethost, Accountbindung, Laufzeitmeldung, privater Reconciliation und bisherigem Admissionbundle besteht mit 128 PASS. Der spätere Owner-/Abnahmelauf besteht mit 123 PASS und sechs FAIL. Beide Auswahlen überlappen; die Zahlen werden nicht als unabhängige Gesamtzahl addiert.

Alle 18 finalen neuen Hoststartfälle bestehen. Die Zählung umschließt die tatsächliche ursprüngliche Corefunktion und ersetzt ihr Ergebnis nicht: ACK-Recovery erzeugt keinen weiteren alten Coreaufruf. Genau ein weiterer tatsächlicher Coreaufruf konsumiert den nächsten eigenständig autorisierten C1. Ein WP02-Beobachtungshook sieht bereits ACKED, bevor dieser neue Aufruf stattfindet. Die beiden Fehlerfälle am tatsächlichen Supervisor prüfen außerdem die Sperre vor WP02 und das Schließen des Budgetowners.

Geprüfte Gegenfälle sind falsche Topologie, Account, Budgetwurzel oder Generation, fehlender beziehungsweise korrupter Originalbeleg, MEMBERSHIP_STORED, fehlender oder korrupter Consumerabschluss, geänderter Originalaufruf, verlorener Writerlock, Pendingorders, fremde frische Accountidentität und vorübergehender Transportausfall. Nach gültigen neuen Kontofacts darf derselbe erhaltene Übergang erneut aufgearbeitet werden; das Budget bleibt dabei ohne frische Originaladmission gesperrt.

Der neue Semantik-Gegenfall scheiterte vor der Änderung: Die alte Recovery meldete eine Rekonstruktion tatsächlicher Orders, Holds, Treasury und Runtimeeligibility allein aus Beispielprüfungen.

## Offene bestehende Abnahme

Sechs Fälle der bestehenden WP03-/WP04-Abnahme scheitern weiterhin. Der Zwei-C1-Harness übergibt beim Bootstrap nur 14 Kerzen; der Originalconsumer lehnt die unzureichende finale Historie ab. Weitere Fälle erreichen in der bisherigen natürlichen LONG-Vorbereitung den erwarteten enter_long nicht, bereits vor dem geänderten Recovery-/Admissionconsumer.

Diese Fehler bleiben als eigene Außenringarbeit offen. Ein Vergleich lädt die betroffenen ursprünglichen Recovery-/Supervisor-/Trace-/Harnessmodule aus dem Basiscommit in denselben temporären Testprozess; er ist ausdrücklich kein vollständiger sauberer Checkoutlauf. Die erfolgreichen neuen Hoststarttests ersetzen diese fehlgeschlagene Abnahme nicht.

## Grenzen und Folgearbeit

Der aufrufende Owner muss den vollständigen ursprünglichen typisierten Startkontext bereitstellen. Ein dauerhafter Prozesshost-Lader und ein autonomer Dienstneustart wurden nicht implementiert. Ohne jeden dauerhaften Originalabschluss bleibt der Coreausgang ungeklärt. Vollständige Safety-/Runtimeadmission, natürlicher N5-Dauerbetrieb und physischer Stromausfall sind nicht abgenommen.

Alle Inputs dieses Belegs sind explizite Offlineinjektionen; die Writer, Budgetowner und Coreconsumer sind Originalcode auf temporären Wurzeln. Keine aktive Runtimewurzel, Venueorder, Kapitalbewegung, fachliche Parameterwahl oder Kraken-Reaktivierung gehört zu dieser Änderung. Die zurückgestellte Link-/Krakenrecherche und das separate Latenz-Control-Runbook bleiben zurückgestellt. Eine Fertigmeldung für den gesamten Außenring folgt aus diesem Anschluss nicht.
