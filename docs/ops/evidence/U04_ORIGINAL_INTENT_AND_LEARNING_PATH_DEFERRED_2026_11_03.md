# U04: ursprüngliche Absicht und Lern-/Evidence-Verbindungen

docs_token: DOCS_TOKEN_U04_ORIGINAL_INTENT_AND_LEARNING_PATH_DEFERRED_2026_11_03

Stand: 03.11.2026, Codebasis `aadba02744b20de9fa2129765b53a8504933b757`. **Auf Franks ausdrücklichen Wunsch zurückgestellt. Keine U04-Umstellung freigegeben oder übernommen.** Die ursprüngliche Begründung des pauschalen Null-Nachweises ist nicht eindeutig belegt. Vorläufige Versuchsänderungen wurden separat gesichert und der Produktivcode vollständig auf diese Basis zurückgesetzt.

## Belegte Konstruktion und historische Varianten

- PR #6494 / Commit `62ac12d8167757aeaa145af03d0e972772385195`, 15.09.2026: 29P verwendet währungsspezifische freie USDC-Margin, bereits netto börsenseitiger Bindungen, abzüglich bedingtem P01. Ein weiterer U04-Abzug ist in diesem Modell ausdrücklich verboten. [Spezifikation](../specs/FULL_CORE_CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_MODEL_V1.md).
- Der ursprüngliche Auftrag zu PR #6678 / Commit `2b0cd3bbc6bac462e8b9b6b6bb557ab998aa7744`, 21.09.2026, verlangt dagegen für den CT-Zweig ausdrücklich `BASE - U04 - P01_IF_APPLIES`, fehlende U04-Evidenz als Sperre und keine stillen Null-/None-Ersatzwerte. Das ist ein bewusst bestehender Prüfvertrag, nicht allein anhand heutiger Zahlen als überflüssig zu behandeln.
- Der ursprüngliche Treasury-Auftrag zu PR #6827 / Commit `9647cb7bbab8137d1db1f47cf053ab6fcb7057a9`, 25.09.2026, verlangt die Verbindung vorhandener U04/P01-/CT-Eligibility-Verträge mit der Treasury/E4/C08/B05-Kette, einen getrennten Reservierungs-Owner und ausdrücklich unveränderte Learning-/Optimizer-Bindung. Im eingeführten Handoff erscheint bereits der konstante Leerreservierungsnachweis. **Warum dieser konkrete Null-Nachweis fachlich für jeden Aufruf gelten sollte, ist damit noch nicht nachgewiesen.**

Originalaufträge: Cursor-Protokoll `01ab894c-9748-4246-aac4-ceec1f75313c`, Zeile 30, sowie `64a5c810-ec9e-4a53-884c-70ad6bfa77d4`, Zeile 115. Lokale Herkunft und Hashbindungen stehen im begleitenden Quellenmanifest. Historische Aufträge dienen hier ausschließlich als Belege; sie werden nicht erneut ausgeführt.

## Tatsächliche Wirkung im aktuellen Handoff

Der CT-Producer wird aufgerufen und sein Erfolg geprüft. Seine Zahl wird anschließend nicht als Endkapital übernommen: Der Handoff ruft den separaten vorhandenen Netto-Margin-Producer mit ursprünglicher Beobachtung und P01/Eligibility auf; U04 wird dort nicht erneut übergeben. CT ist deshalb in diesem Pfad zugleich ein wirksames Gate und kein numerischer Endkapital-Consumer.

Isolierter synthetischer Versuch bei freier Margin 1.000 USDC:

- U04 0: CT 1.000, finales Risikokapital 1.000.
- U04 25: CT 975, finales Risikokapital weiterhin 1.000, gleicher finaler Input-Digest.
- U04 1.001: CT produziert nicht; der gesamte Handoff sperrt.

Diese Beobachtung widerlegt die Gleichsetzung „numerisch nicht übernommen = wirkungslos“. Sie beweist weder die fachliche Richtigkeit des Null-Nachweises noch eine bestehende Doppelbelastung. Lokale Reservierungen werden zudem als finales Order-Notional geführt; börsenseitige gebundene Margin ist nicht ohne weiteren Nachweis dieselbe Größe. Deshalb kein Ersetzen von U04 durch die Summe lokaler Holds.

## Lern-/Evidence-Kanäle

Ein direkter U04-spezifischer Lernconsumer wurde in den untersuchten Lern-/Research-Quellen nicht gefunden. Das ist kein Vollständigkeits- oder Unbedenklichkeitsbeweis:

- [DDO-Capture](../../../src/learning/deterministic_decision_outcome_v0/capture_v0.py) beobachtet generische Sizing- und Order-Intent-Ergebnisse. Der vorhandene Sizer ist dekoriert; die Reconciliation-Startprüfung hat ebenfalls einen Beobachtungshook.
- Ein explizit gebundener Capture-Kontext um den echten injizierten 29P-Join schreibt im Versuch zwei Datensätze: Producer `capital_risk_sizing_v1` und `canonical_order_intent_v1`. Nach dem Rücksetzen dieses Kontexts hängt derselbe Join keine weiteren Datensätze an diese Ledgerdatei an. Die vorhandenen Capture-Datensätze haben hier `risk_snapshot_ref=null` und `decision_type=UNKNOWN`; sie beweisen keine vollständigen Kapital-/Ausführungslerndaten.
- Im regulären Master-V2-Pfad liegt die bestehende Replay-Erfassung vor dem späteren kontogebundenen 29P-Rebind. Welche äußeren Aufrufer weitere Capture-Kontexte binden und welche historischen Records tatsächlich in Auswertung/Training eingingen, ist nicht vollständig geprüft.
- Der bestehende Export-Handoff blockiert den ungeprüften N_BARS-Ausgang mit `VERIFIED_N_BARS_SOURCE_NOT_BOUND`. Das beweist keine Unverändertheit aller anderen historischen Lernkanäle und keinen vollständigen Anschluss von realer Ausführung an Lernen.
- Der vorhandene synthetische Gesamtkonstrukt-Runner konsumiert ebenfalls den E4/CT- und Handoff-Pfad als Evidenz. Solche Diagnose-/Closure-Verbraucher dürfen bei einer Migration nicht stillschweigend verschwinden.

## Offene Zuordnung und Fortsetzung

Offen bleiben der belegte fachliche Geltungsbereich des Null-Nachweises, die heutige Aufgabe des CT-Gates im neu zusammengestellten System, die Abgrenzung Venue-Margin/lokales Notional und die vollständige Zuordnung zu Capture-/Ausführungs-/Outcome-Daten. Vor einer späteren Änderung müssen ursprüngliche Absicht, aktuelle Gate-Wirkung und erforderliche Evidenz getrennt erhalten oder ausdrücklich ersetzt werden.

U04 bleibt auf Wunsch zurückgestellt. Die sieben älteren Startanschlüsse können unabhängig untersucht werden, solange keine leeren Portfolios erfunden, Reconciliation-/Capture-Ereignisse entfernt oder Kapital-/Lernsemantik mitgeändert werden. Noch keine Erledigtmeldung für diese Anschlüsse.

Alle Versuche verwenden injizierte Daten und temporäre Dateien. Kein realer privater GET, keine Credentials, Orders, Kapitalbewegungen oder Aktivierung. Bestehende Runtime-/Lernledger unverändert; keine Training-/Promotionsprüfung und keine Aussage über reale Handelswirkung.
