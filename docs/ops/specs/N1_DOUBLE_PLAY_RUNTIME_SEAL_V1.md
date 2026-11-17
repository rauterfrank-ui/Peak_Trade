---
docs_token: DOCS_TOKEN_N1_DOUBLE_PLAY_RUNTIME_SEAL_V1
status: active
policy_id: N1_DOUBLE_PLAY_RUNTIME_SEAL_V1
runtime_authorization_effect: NONE
---

# Double Play und N1 versiegelt

Der [versiegelte Dateisatz](N1_DOUBLE_PLAY_RUNTIME_SEAL_V1.json) bindet die offline geprüfte Quellkonfiguration. Er umfasst die native Dynamic-Scope-Kette, die belegte N1-Spur, die gebundene Slot-Reservierung, die Vorbereitung der Netto-Order, die ordergebundene POST-Freigabe, den OKX-Sender und den Wiederanlauf. Ein normaler Richtungswechsel nutzt dasselbe Instrument und denselben Slot mit der ursprünglichen Reservierung. Positions- und 29P-Abfragen laufen parallel zur Marktverarbeitung.

Die aufgeführten Dateien und der geschützte Dateisatz bleiben eingefroren. Das Lint Gate prüft die SHA-256-Werte. Das Map Currency Gate lädt die Prüflogik aus dem Zielbranch und blockiert Änderungen an geschützten Dateien, dem Siegel und seiner Durchsetzung. Eine gemeinsam eingereichte neue Prüfsumme hebt die Sperre nicht auf. Beide Prüfungen nennen betroffene Pfade.

Vor Arbeiten am gekoppelten Pfad lässt sich die Sperre lokal prüfen. Den Zielbranch vor dem Vergleich auf den aktuellen freigegebenen Stand bringen.

```sh
./scripts/pt scripts/ops/check_n1_double_play_runtime_seal_v1.py
./scripts/pt scripts/ops/check_n1_double_play_runtime_seal_v1.py --base origin/main
```

Laufzeitbelege wie Marks, Ausführungen, Buchungen, POST-Freigaben und Hostzustand entstehen weiterhin im Betrieb. Das Siegel umfasst die versionierten Quellen und Konfigurationsregeln. Die produktive Freigabequelle für den Mac-Dienst bleibt ein eigener Betriebsnachweis.
