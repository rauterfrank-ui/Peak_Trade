# N_BARS: vorhandene Messartefakte bis zur Evaluation erhalten

Der bestehende alleinige Supplier berechnet Anfangs-/Endpreis und Logreturn und erzeugt inhaltsadressierte Mess- und Informationsset-Artefakte. Der Horizon-Host gab zuvor nur die Observation mit Referenzen und Metadaten weiter. Jetzt bleiben die vorhandenen Artefakte im Host- und Evaluationsergebnis als unabhängige Kopien erhalten. Die bestehenden Ops-Bindings reichen dieses Ergebnis unverändert weiter.

Vor Evaluation oder Ledgerzugriff werden bestehende Schema-/Producer-/Bridge-Identität, beide Inhaltsreferenzen sowie Instrument, Bar-Spezifikation, Horizont, Bar-Identitäten, Skalarbedeutung, Decision und Evaluationsgrenze abgeglichen. Eine nur teilweise gelieferte Artefaktpaarung wird abgelehnt. Ältere reine Referenzeingänge bleiben akzeptiert, erhalten aber ausdrücklich keine behauptete Messartefaktaufbewahrung.

41 Tests bestehen, darunter zehn neue Fälle mit ETH, BTC und SUI, JSON-Roundtrip, manipulierten Inhalten, neu gehashtem falschem Kontext und Abgrenzung des Messfensters. Es gelten die identischen Rechenregeln für die drei Instrumente; dies ist kein separater Zulassungsnachweis.

Der bestehende Return misst ersten bis letzten Bar-Schluss, nicht den Abstand vom Grid-Start zur letzten Bar. Er ist weder Konto-PnL noch automatisch ein ökonomisches Score- oder MI-Richtungslabel. Kosten, Position, Funding, echte Herkunft und Zielzeitfenster werden nicht ergänzt oder erfunden. Die Änderung erhält Artefakte im Prozess/serialisierbaren Ergebnis; sie erzeugt keinen neuen dauerhaften Store und keinen natürlichen Dauerlaufnachweis. Ursprüngliches Lern-Ledger und historische Originale sind unverändert.

[Blueprint Abschnitt 41](../../blueprints/PEAKTRADE_SYSTEM_RECONFIGURATION_BLUEPRINT_2026_11_03.md) und [gebundene Ergebnisse](receipt.json).
