---
docs_token: DOCS_TOKEN_CURRENT_POST_ORIGINAL_ENTRY_BUDGET_POLICY_2026_11_08
authority: NONE
runtime_authorization_effect: NONE
---

# Aktuelle ursprüngliche Notionalgrenzen am späteren Versand

Basis adbc67a6914558b44a7aeae98df04b79c32d5c31, Branch
fix/current-entry-policy-plan-revalidation. [Semantik](../specs/CURRENT_POST_ORIGINAL_ENTRY_BUDGET_POLICY_V1.md)
und [JSON-Beleg](CURRENT_POST_ORIGINAL_ENTRY_BUDGET_POLICY_2026_11_08.json) binden
ursprüngliche Konstruktion, aktuelle Consumer und den abgeschlossenen Prüflauf.

Die ursprüngliche äußere Entrypolicy begrenzt beim LIVE-29P-Sizing den einzelnen
und den gesamten reservierten USDC-Notionalbetrag. Spätere Plan-/POST-Reader
verbrauchen diese inzwischen geltenden Grenzen bisher nicht. Acht Gegenfälle
am unveränderten Basiscode weisen engere Einzel-/Aggregatgrenzen sowie fehlende
oder ungültige Policy nicht ab; sechs positive Fälle bestehen schon vorher.

Derselbe Originalbudgetowner liest nun die ursprüngliche aktuelle Policy,
die tatsächliche COMMITTED-Reservation und seine ursprüngliche RESERVED-/COMMITTED-
Summe unter seinem bestehenden Lock. Der eigene Hold ist bereits genau einmal
enthalten. Die aktuellen Grenzen erreichen den bisherigen frühen Planconsumer
und die vier späten K1-/HTTP-/Vor-Socket-Readbacks. Die unveränderte ursprüngliche
Policyimplementierung wird zusätzlich vom vorhandenen POST-Integritätsschutz
erfasst. Die operative Konfiguration bleibt unverändert und dynamisch lesbar.

Die erste neue Suite hat 38 PASS. Die Erweiterung prüft zwölf weitere erfolgreiche
Holdfälle; zwei neue Assertions verwenden zunächst ein nicht vorhandenes
Resultfeld und werden auf die tatsächlichen ursprünglichen Outcome-/Recordfelder
korrigiert. Der vollständige finale Lauf endet mit **1184 PASS, Exit 0, ohne
Deselektion**: die bisherigen 1132 Fälle und 52 neue Consumerfälle. Quellen,
Kommando, Wrapper, geladenes Inventar und Log sind im JSON gebunden. Vor- und
Nachhashes stimmen überein. Dieser fertige PASS wird beim Commit wiederverwendet.

Die Originalpolicy-, Konfigurations- und numerischen Offline-Riskkörper bleiben
bytegleich zum Source-Freeze. Es gibt keine neue finanzielle Grenze, automatische
Erhöhung, Plan-TTL, Mengenänderung, Neubewertung des ursprünglichen Notionals,
GET, Retry oder Reserve-/Releaseberechtigung. Engere Vorgaben stoppen den
Versand; nach möglicher Außenwirkung bleiben Ungewissheit und Kapitalhold erhalten.
Ein gültiger Revisionswechsel allein ist kein erfundenes globales Veto.

**Weiter offen:** vollständige spätere Core-/Risk-/Markt-/Altplanadmission,
unabhängige Sendemandate, globale Root-/Ownerherkunft, signierte Recovery,
vollständige Pending-Custody, autonome Hostfortsetzung sowie sieben ältere
Collector-/Account-Verträge und die breitere Abnahme. Die alte Offline-Riskpolicy
wird nicht produktiv umbenannt. Dies ist ein belegter Teilanschluss in Paket 1.
