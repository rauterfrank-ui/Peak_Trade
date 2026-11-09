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

Startupadapter, gespeicherte Slot-/Instrumenttopologie, Private-Reconciliation,
Kapitalrecovery und ursprünglicher Membershipselector bleiben bytegleich zum
Bezugsstand. Der Restart liest die gespeicherten Identitäten. Er führt weder
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

Das gesamte [BWP 1](CURRENT_SYSTEM_FIVE_BOUNDED_WORK_PACKAGES_V1.md) bleibt offen,
bis auch die fachliche Kosten-/Margin-/Verlustbudgetzulassung am ursprünglichen
Consumer belegt ist.
