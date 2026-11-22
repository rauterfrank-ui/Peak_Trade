---
docs_token: DOCS_TOKEN_CURRENT_ORDERED_FUNDING_EPISODE_DEVELOPMENT_ADMISSION_V1
authority: DEVELOPMENT_DELTA_ONLY
runtime_authorization_effect: NONE
---

# Begrenzte Fortschreibung für geordnete Fundingzahlungen

Frank hat am 9. November 2026 die konkrete Entscheidungsvorlage mit
`Ja, genau diese Erweiterung; Wiederanlauf erhalten` bestätigt. Bezugsstand ist
`304719c94030ff9aacdf2571e2ae56533f9e6a25`. Die geprüfte Änderung betrifft genau:

- [Episodebindung](../../../src/ops/exit_policy_producer_binding_v1/position_episode_binding_v1.py)
- [simulierte Accountingquelle](../../../src/ops/exit_policy_producer_binding_v1/simulated_accounting_entry_source_v1.py)
- [Accountingfortschritt](../../../src/ops/exit_policy_producer_binding_v1/simulated_accounting_progress_v1.py)
- [simulierten Episodenabschluss](../../../src/ops/exit_policy_producer_binding_v1/simulated_accounting_close_v1.py)

Die [Policyprojektion](../../system_atlas/policy_projection.py) bindet je Datei
den unveränderten eingefrorenen und den konkret geprüften Nachfolgedigest.
Sie akzeptiert entweder die vier Originale oder das vollständige geprüfte
Nachfolgebundle. Ein fünfter Pfad, eine andere Implementierung, ein Teilbundle,
ein umgebundener Baselinehash oder ein allein nachgetragener Entwicklungshash
erhält dadurch keine Zulassung. Die ursprünglichen drei separaten
Entwicklungsausnahmen und die Prüfung der sechs numerischen Zulassungspfade
bleiben erhalten.

## Fachlicher Umfang

Der bestehende Accountingowner erhält für beobachtete Fundingbeträge optional
deren explizite Ereigniszeit und die tatsächliche Reihenfolge zwischen den
ursprünglichen Fills. Er bleibt der einzige Writer der Finanzrechnung. Der
Quelladapter verifiziert die vollständige Interleaving-Rechnung erneut über
diesen Originalowner. Die bestehende Episode speichert Funding-only-Fortschritt
über ihren Originalwriter, ohne einen Fill zu erfinden. Die neue Fortschrittsform
ist ausdrücklich `simulated_accounting_episode_progress.v2`; unfundierte
V1-Records bleiben in ihrem bisherigen Schema.

Signed Funding ist ein beobachteter Geldbetrag in der Vertragswährung, keine
Fundingrate, Gewinnprognose oder Survivalwahrscheinlichkeit. Fehlende Reihenfolge
in alten Fundingrecords wird nicht erfunden. Die tatsächliche Corebeobachtung
darf keine späteren Fundingereignisse konsumieren. Der Flat-Nachweis muss auch
das letzte Finanzereignis zeitlich abdecken. Idempotente Wiederholung verändert
weder Geld noch Episodegeneration erneut.

## Erhalt des Wiederanlaufs

Am geprüften Funding-Nachfolger
`e2abdf73876b6f093347b27c4145b86cb7fc16c6` sind Startupadapter, gespeicherte
Slot-/Instrumenttopologie, Private-Reconciliation, Kapitalrecovery und
ursprünglicher Membershipselector bytegleich zum Bezugsstand. Diese
Unverändertheitszusage betrifft die Funding-Erweiterung vom 9. November und
erteilt späteren Änderungen keine Zulassung. Der Restart liest die gespeicherten
Identitäten. Er führt weder
Neuauswahl noch Holdfreigabe oder zusätzlichen Versand aus. Die vier Adapter
erhalten ihre bisherigen Recovery-, Source-, Anchor- und CASprüfungen; sie
verarbeiten zusätzlich die ausdrücklich neue geordnete Fundinghistorie.

Freeze-Tags, eingefrorenes Policyinventar und ursprüngliche Policyobjekte bleiben
unverändert. Diese Fortschreibung ist kein Betriebsrecht. Ein physischer
Stromausfall wurde nicht durchgeführt.

Die [Fundingprüfungen](../../../tests/ops/test_ordered_funding_episode_continuity_v1.py)
decken Geldwirkung, LONG/SHORT, Reihenfolge, Cold-Read, Exit, Flat, doppelte IDs,
zukünftige Ereignisse und alte unfundierte Records ab. Die
[Delta-Prüfung](../../../tests/ops/test_current_ordered_funding_episode_policy_delta_v1.py)
prüft die tatsächliche Policyadmission einschließlich ihrer Negativfälle und
die unveränderten Wiederanlaufowner. Der bestehende verbundene Slot- und
Wiederanlaufnachweis bleibt erforderlich.

## Spätere Startupgate-Fortschreibung und Snapshotprüfung

Nachweisstand 22. November 2026: Das
[Reconciliation-Startupgate](../../../src/ops/productive_reconciliation_runtime_binding_v1/startup_gate_v1.py)
wurde später mit [PR #7307](https://github.com/rauterfrank-ui/Peak_Trade/pull/7307)
in Commit `78170916f5fd32267b54eb55b241fa65feb1486f` geändert. Die aktuelle
Datei entspricht exakt diesem Nachfolger. Der Fundingtest und der
[benachbarte Rotationstest](../../../tests/ops/test_reserved_slot_rotation_development_delta_v1.py)
prüfen die damalige Bytegleichheit an ihren ursprünglichen Nachfolgercommits
und die heutige Startupgate-Datei an diesem separat geprüften Commit.
Sie überspringen die Prüfung nicht und akzeptieren keine beliebigen neuen
Dateibytes oder allein umgebundenen Entwicklungshashes. Funding-Bundle,
Policyprojektion, Freeze-Inventare und Freeze-Tags bleiben unverändert.

Der spätere Pfad gleicht ausschließlich eine bereits authentifiziert gebuchte
Net-Reversal-Position über den ursprünglichen Host-/Budgetowner ab. Er prüft
Hosttyp, Reconciliation-Statewurzel, Session, Repositorybezug und dieselbe
Beobachtung. Der Originalowner muss die gebuchte Obligation und den zugehörigen
authentifizierten Entrybeleg lesen; Buchungsdigest und Instrument müssen passen.
Die beobachtete Zielmenge sowie die gespeicherte Ausgangsmenge sind vorzeichenbehaftete
native Kontraktmengen. Eine bereits identische Position wird idempotent behandelt;
abweichende Ausgangspositionen, fehlender Parent oder widersprüchlicher Writer
werden abgewiesen. Der ursprüngliche Classifier und die atomare Persistenz mit
Verifikation bleiben zuständig. Der Pfad berechnet keine Fundingrate, erzeugt
keinen Fill und vergibt kein zusätzliches Budget-, Permit- oder Versandrecht.

Die [bestehenden Reconciliationfälle](../../../tests/ops/test_productive_reconciliation_runtime_binding_v1.py)
prüfen unter anderem den Hardstop bei unbelegtem Seitenwechsel, Reduce-only-Recovery,
fehlende/veraltete Wahrheit, Writerkonflikte und Wiederanlauf. Die
[synthetischen signierten Buchungsfälle](../../../tests/ops/test_execution_reconciliation_get_provenance_v1.py)
verwenden Fixtureantworten und isolierte Originalstores. Sie binden den ursprünglichen
Auftrag, vollständige Fills, Settlement, unveränderte Reservation und Cold-Read
zusammen und weisen unvollständige, fremde oder widersprüchliche Belege zurück.
Diese Offline-Prüfungen belegen den jeweiligen Consumerpfad, keinen heutigen
Venuebetrieb, physischen Stromausfall oder eine Gesamtbetriebsfreigabe.

Das gesamte [BWP 1](CURRENT_SYSTEM_FIVE_BOUNDED_WORK_PACKAGES_V1.md) bleibt offen,
bis auch die fachliche Kosten-/Margin-/Verlustbudgetzulassung am ursprünglichen
Consumer belegt ist.
