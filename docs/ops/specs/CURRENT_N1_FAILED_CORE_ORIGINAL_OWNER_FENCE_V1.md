---
docs_token: DOCS_TOKEN_CURRENT_N1_FAILED_CORE_ORIGINAL_OWNER_FENCE_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Ausfall vor der negativen Corepublikation am ursprünglichen N1-Owner

Basis ist `27680a294` nach der
[Risiko-/Mengenprüfung](CURRENT_N1_RISK_AND_QUANTITY_CONSUMPTION_V1.md).
Die ursprüngliche [Versuchssperre](CURRENT_CORE_ENTRY_ATTEMPT_ADMISSION_V1.md)
veröffentlicht vor einem neuen S7-Coreaufruf eine negative Admission im
originalen Cursor. Fehlerhafte Eingangsdaten, Producerfehler und fehlgeschlagene
Abschlusspublikation lassen diese Sperre bestehen. Ein anderer Fall liegt vor,
wenn bereits das Schreiben der Sperre fehlschlägt: Core startet nicht, doch der
vorherige positive Cursor kann unverändert vorhanden bleiben.

## Enge Ursache und Änderung

Der bisherige [N1-Dispatch](../../../src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py)
reicht S7-Fehler weiter, ohne selbst die Admission seines vorhandenen Budgetowners
zurückzunehmen. Sein Host schließt den Owner im normalen Abbau ohnehin. Die
zusätzliche Absicherung wirkt vor Rückgabe des Fehlers und damit vor diesem
späteren Hostabbau, auch gegenüber einem Sender mit bereits gebundenem Altplan.

Bei einer Exception aus der tatsächlichen S7-Komposition ruft derselbe N1 nun
`close()` an seinem übergebenen ursprünglichen Budgetowner auf. Die
[originale Closefunktion](../../../src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py)
setzt unter ihrem eigenen Lock zuerst `admitted=False` und den geschlossenen
Ownerzustand, danach schließt sie ihre Writerlease. Holds, Sizingbindung und
Ausführungslinks werden nicht gelöscht oder freigegeben. Ein Lease-Cleanupfehler
kann diesen bereits gesetzten negativen Zustand nicht in eine Zulassung ändern;
der ursprüngliche Corefehler wird mit Cleanupfehler als Ursache weitergegeben.
Das bestehende Mapping spezifischer Addressingfehler bleibt erhalten.

Damit werden die ursprünglichen frühen und späten Budgetreader des Senders
negativ. Es gibt keinen zweiten Budgetowner oder zweiten Fehlerstore, keinen
neuen Hold, kein Release, keine Ersatzmenge, keinen zusätzlichen GET und keinen
neuen Permit. Insbesondere wird der nicht geschriebene Cursor nicht als
veröffentlichte negative Corebewertung ausgegeben. Close benötigt keinen
zusätzlichen dauerhaften Budgetcommit, dessen Bestätigung ebenfalls ausfallen
könnte. Native Handelsformeln und bestehende finanzielle Policy bleiben gleich.

## Consumerwirkung und Grenzen

Die [kausalen Fälle](../../../tests/ops/test_current_n1_failed_core_owner_fence_v1.py)
führen denselben tatsächlichen N1-Dispatch und ursprünglichen S7-Writer aus.
Die Cursorpublikation schlägt vor dem Coreaufruf fehl. Wird allein die neue
Ownerclose-Wirkung in der Gegenprobe entfernt, bleibt der ursprüngliche Altplan
zugelassen. Mit der Änderung wird dieser Originalowner negativ, obwohl derselbe
alte Cursor bytegleich stehen bleibt. V1/V2-Ausführungsidentitäten sind enthalten.

Die echten späteren POST-Funktionen werden mit synthetischen Ports vor GET,
nach GET, während K1 und nach Openerkonstruktion geprüft. Vor möglicher
Socketwirkung stoppen sie; nach möglicher Wirkung bleiben ursprünglicher
MAY_HAVE_SENT-Claim, UNKNOWN und Kapitalhold erhalten. Ein lokaler Corefehler
beweist kein Never-submitted. Cold-Reopen bewahrt die ursprünglichen Holds und
Links und beginnt weiterhin ohne Admission an der ursprünglichen Recoverygate.

Der [gemeinsame Beleg](../evidence/CURRENT_N1_FAILED_CORE_ORIGINAL_OWNER_FENCE_2026_11_09.md)
bindet diesen Pfad mit bestehenden positiven Fortsetzungen, Originalbudget-/
POST-Ownern und Laneadressierung. Die Gegenproben verwenden keine realen
Credentials oder Netzwerkeffekte.

Die Änderung wirkt auf genau den N1 übergebenen Owner und Sender, die dessen
ursprünglichen Kontext konsumieren. Ein direkter S7-Aufruf ohne diesen Owner
erhält daraus keine zusätzliche globale Sperre. Fremde Owner, unabhängige Sender
und die letzte Racegrenze nach der letzten lokalen Prüfung bleiben gesondert.
Cold-Reopen ist keine erneute Zulassung. Die bestehende Recovery ist aber auch
kein Beleg, dass nach vollständiger frischer Recovery zwingend eine neue
Coreentscheidung nötig wird; diese übergreifende Herkunfts-/Recoveryfrage bleibt
offen. Physischer Stromausfall und unbegrenzter autonomer Betrieb sind damit
nicht bewiesen.

Der aktuelle Dispatch ist N1. Bei einem später gemeinsam genutzten Mehrslotowner
würde dessen Close alle daran gebundenen neuen Entries sperren und alle Holds
behalten. Weiterlauf anderer Slots oder der Positionsverwaltung nach einem
Slotfehler wird hier nicht behauptet. Die
[Mehrslot-Testanforderung](CURRENT_MULTISLOT_TEST_PHASE_REQUIREMENTS_V1.md)
führt diese noch gesondert zu belegenden Wirkungen auf.
