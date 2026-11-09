---
docs_token: DOCS_TOKEN_CURRENT_CONTINUOUS_DOUBLE_PLAY_ECONOMIC_SEMANTICS_2026_11_09
authority: NONE
runtime_authorization_effect: NONE
---

# Punkt 1: vorhandene wirtschaftliche Auswahl und fortgesetzter Handelskreis

Ausgangspunkt: `f7f6ad36e91016c93935d2f90ce9d9a125fa6000`. Die Nutzerpräzisierung verlangt
fortgesetzte Double-Play-Zyklen und vorhandene Instrumentrotation. Diese
Konstruktion wird zuerst geprüft; ein neues pauschales Profit-/Survivalgate
wird nicht vorausgesetzt.

**153 gemeinsame Fälle PASS, Exit 0, keine Deselektion.** Der
[JSON-Beleg](CURRENT_CONTINUOUS_DOUBLE_PLAY_ECONOMIC_SEMANTICS_2026_11_09.json)
bindet 1696 Pythonkörper vor/nach dem Lauf, davon
1696 tatsächlich geladene Quellen. Loghash:
`e81f298591f011c88261068fdea348347942e89f14da7f484fd09bc62d23a075`. Die [Semantik](../specs/CURRENT_CONTINUOUS_DOUBLE_PLAY_ECONOMIC_SEMANTICS_V1.md)
führt die Originalowner und ihre tatsächlichen Consumer zusammen.

Cap22-Merkmale/Score, Cap23 mit Sekundenfristen, Membership mit unterschiedlichen
Rankingbeobachtungen, Positionscustody, Cap24 und tatsächliche nächste
N1/S7-Fortsetzung sind enthalten. KEEP, REPLACE, Mindesthaltung,
Expiry-Review und verlorener ACK behalten ihre Bedeutung. Drei neue
Gegenproben zeigen, dass proportional schwächere Rohbewegungen dieselben
relativen Scores liefern können, ohne ihre Inputdigests gleichzusetzen.
Das ist kein Fehler der relativen Rankingpolicy und kein Kosten-/Survivalbeweis.

Zwei alte Testannahmen sind korrigiert. Ein ausdrücklich suspendierter
Kandidat ersetzt die aufgegebene implizite BTC-Sperre; zusätzlich wird ein
zulässiger Live-BTC gerankt. Der kanonische Replaytest initialisiert seinen
aktuellen Snapshot ausdrücklich im temporären Store und prüft dort Replay
ohne zweite Instanz. Er verwendet nicht mehr eine ältere Membership als
angeblich identischen heutigen Snapshot und schreibt nicht ins Repoverzeichnis.
Die entstandene Testspur bleibt lokal erhalten; das Originalmanifest ist
exakt wiederhergestellt. Alle Fälle bleiben enthalten, Produktregeln gleich.

Abgeschlossen ist diese Quellen-/Anforderungsklärung. Nicht abgeschlossen sind
produktive Kosten-/Survivalherleitung, deren nötige Definitionen und vollständiger
24/7-Betrieb. Replaywerte, Rankingperzentile, simulierte Ledgerwerte,
Fillgebühren und Shadow-Ratios werden nicht ineinander umbenannt. Risiko- und
Mengenconsumer sowie Ausfallkoordination folgen mit eigenen Commits.
