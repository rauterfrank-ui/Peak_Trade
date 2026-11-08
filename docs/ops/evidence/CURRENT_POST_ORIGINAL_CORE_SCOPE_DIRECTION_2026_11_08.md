---
docs_token: DOCS_TOKEN_CURRENT_POST_ORIGINAL_CORE_SCOPE_DIRECTION_2026_11_08
authority: NONE
runtime_authorization_effect: NONE
---

# Ursprüngliche Richtung und CHOP am späteren Entryconsumer

Basis 023c8a92b385bb98c148748a55e62c0307fcb77b auf demselben Arbeitsbranch.
[Semantik](../specs/CURRENT_POST_ORIGINAL_CORE_SCOPE_DIRECTION_V1.md) und
[JSON-Beleg](CURRENT_POST_ORIGINAL_CORE_SCOPE_DIRECTION_2026_11_08.json) binden
Originalkonstruktion, tatsächliche Quelle, Gegenprobe und endgültigen Prüflauf.

Zwei tatsächliche N1-/Supervisorproben zeigen die passenden ursprünglichen
armed-Zustände für Long und Short bei der Planbindung. Entscheidungsepoche und
persistierte nächste Cursorepoche bleiben verschiedene Bezüge. Zehn Gegenfälle
am unveränderten Basiscode werden später nicht abgewiesen: CHOP, entgegengesetzte
Bereitschaft, vollzogene Aktivierung, fehlender RuntimeScopeState und untypisiertes
Latch, jeweils mit V1-/V2-Executionbezug. Die Gegenprobe endet mit 10 FAIL durch
fehlende erwartete Ablehnung; es wird kein Venuekontakt ausgeführt.

Der vorhandene Cursorconsumer verwendet nun den ursprünglichen Coremapper und
das ursprüngliche armed-Prädikat. Seine Richtung muss wie im ursprünglichen
Entryzweig zur unveränderten ursprünglichen Intentseite passen. Die originale
CHOP-Projection konsumiert den tatsächlichen nativen Boolean-Latch; fehlende
oder uneindeutige Rohwerte werden nicht zu false normalisiert. CHOP bleibt
Scopepolicy und erzeugt keine Richtung. KILL_ALL behält seine Priorität.

Die erste Suite besteht mit 16 neuen Fällen. Die erweiterte Prüfung besteht mit
69 Fällen: 58 neue Consumerfälle und elf unveränderte ursprüngliche Long-/Short-/
CHOP-Verträge. Zwei zusätzliche Verbrauchsproben zeigen, dass CHOP-Clearing einen
abgebrochenen und verbrauchten Einmalversuch nicht erneut öffnet.

Der vollständige finale Lauf endet mit **1314 PASS, Exit 0, ohne Deselektion**:
bisherige 1243 Fälle, 60 neue und elf zusätzliche Originalownerfälle. Vor- und
Nachhashes der gebundenen Pythonquellen stimmen überein. Kommando, tatsächlich
geladene Quellen, Runner, Wrapper und Loghash stehen im JSON. Dieser fertig
abgeschlossene PASS wird beim Commit wiederverwendet.

Kandidatenfortschritt, der die ursprüngliche Bereitschaft erhält, erzeugt keine
pauschale Ablaufregel. Der ursprüngliche NOOP kann CHOP aufheben; er erzeugt
kein neues Permit oder Release. Eine gültige Coreaktivierung ist kein erneutes
Entryrecht und kein bestätigter Fill. Nach möglicher Socketwirkung bleiben
UNKNOWN, Permitverbrauch und Hold bestehen. Reconciliation, Full-Close und
Kapitalrelease behalten ihre zuständigen Originalowner.

Originalmapper, Entry-Policy, CHOP-Owner und Statefunktion bleiben unverändert
und werden von der vorhandenen POST-Quellintegritätsoberfläche geschützt. Keine
neue Persistenz, Originversion, Uhr, allgemeine TTL, Finanzgrenze, Menge, GET,
Retry oder positive Authority entsteht. Alle neuen Quell-/State-/Portänderungen
sind temporäre Testinputs; operative Konfiguration und echte Zustände bleiben.

Der gelesene Cursor ist der letzte dauerhafte Zustand. Er ersetzt keinen neuen
vollständigen Coreframe. Frische Scope-/Regime-/C3-/Survival-/Suitabilitybewertung,
unabhängige Markt-/Finanzinputs und produktive numerische Riskpolicy bleiben
offen. Offlinepolicy, Legacy ohne Quelle, globale Root-/Ownerherkunft,
Sendemandate, signierte Recovery, vollständige Custody, autonomer Host und die
sieben älteren Collector-/Account-Verträge werden damit nicht geschlossen.
