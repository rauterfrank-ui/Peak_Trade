---
docs_token: DOCS_TOKEN_CURRENT_CORE_ENTRY_ATTEMPT_ADMISSION_2026_11_09
authority: NONE
runtime_authorization_effect: NONE
---

# Dauerhafter Coreversuch: negativer Entryanschluss

Basis ist `72c1de29b223abd6597fc1c88b38feeb1f1a7860`. Der tatsächliche N1/S7-Pfad veröffentlicht nun vor einem
neuen Corelauf eine negative Versuchsmarkierung im bestehenden Originalcursor.
So kann ein fehlschlagender Lauf nicht einfach den alten positiven Frame als
unverändert aktuellen Ausgang zurücklassen. Die [Semantik](../specs/CURRENT_CORE_ENTRY_ATTEMPT_ADMISSION_V1.md)
trennt diese Hosttatsache von nativen Handelsentscheidungen und Wirtschaftswerten.

**2421 gemeinsame Fälle PASS, Exit 0, ohne Ausschlüsse.** Die bisherigen
2.120 Fälle bleiben vollständig enthalten. Zusätzlich enthält der Lauf die neue
Versuchszulassung, die tatsächliche Sourceintegrität, betroffene ursprüngliche
Cursor-/Recovery-/Hostverträge und Governance-/Atlasprüfungen. Der
[JSON-Beleg](CURRENT_CORE_ENTRY_ATTEMPT_ADMISSION_2026_11_09.json) bindet
2048 Pythonkörper vor/nach dem Lauf, davon
1984 tatsächlich geladene Quellen, sowie
Selectoren, Runner, Inventar und Log. Bei anschließend identischen Pythonquellen
wird dieser PASS wiederverwendet.

Die kausale Gegenprobe entfernt ausschließlich die neue Veröffentlichung.
Derselbe native Inputfehler beziehungsweise dieselbe Producerexception lässt
dann den gehaltenen Plan weiter zugelassen. Mit Veröffentlichung verweigert
derselbe Originalconsumer. Native Cursorfelder und reserviertes Kapital bleiben
unverändert. Echte aktuelle LONG-/SHORT-Supervisorfortsetzung ersetzt die
Markierung durch native Ausgänge. Fehlender Bootstrap und ein neuerer Versuch
lassen sie negativ bestehen. Tatsächliche frühe/späte POST-Prüfungen, irreversibler
Verbrauch und möglicher Versand behalten ihre bisherigen Grenzen.

Die betroffenen alten Hostfixtures wurden an heutige Inputverträge angepasst:
100 ausdrückliche synthetische Schlusskurse, zulässige Futureidentität, kein
G17-Wissen aus der Zukunft und gleiche deklarierte Sealidentität für vollständige
Paritätsvergleiche. Produktzulassungen oder Handelsformeln wurden dafür nicht
geändert. Drei Restartverträge prüfen unveränderte native Felder plus die neue
negative Metadatenmarkierung. Veraltete direkte-write_text-Beschreibungen wurden
an den bereits auf Main vorhandenen atomaren Einzeldateiwriter angeglichen.
Die Behauptung vollständiger Checkpointatomarität bleibt false.

Der erste erweiterte gemeinsame Lauf endete mit 2.413 PASS und sechs FAIL.
Fünf betrafen eine echte fehlende Übergabe der öffentlichen Marktquelle im
direkten Fresh-Runtime-Wrapper, einer dessen entfernten Katalogpfad. Der
Wrapper reicht den ausdrücklichen Port nun an den bestehenden Cap21–Cap24-Owner
weiter. Offline ohne Port verweigert er vor dem Erstellen eines Netzwerkadapters;
ein expliziter bool-false-Port bleibt identisch erhalten. Zwei neue Fälle prüfen
diese Grenzen. 100 abgeschlossene Testkerzen und 61 dazu zeitlich passende
Markkerzen ersetzen unzureichende beziehungsweise zukünftige Fixtures.
Bestehende positive Core-/Restore-/No-Send-Erwartungen bleiben erhalten.
Die dokumentarische Prüfung nutzt das vorhandene Freeze-/Quellenbindungsverfahren.
Alle ursprünglichen Fälle bleiben im abschließenden gemeinsamen Lauf enthalten.
Diese öffentliche Ranking-Marktquelle ist keine Survival-Kostenherkunft.

Das unveränderte 20-Member-Kernsiegel, alle 31 Format-Freeze-Körper, der gesamte
Survival-/Replaykörper und ihre Schutzchecker bleiben erhalten. Die tatsächliche
Boundaryprüfung des ausdrücklich benannten Dateiumfangs besteht ohne neue
Governancefreigabe. Ein passender Hash ist keine wirtschaftliche Zulassung.

Offen: Scheitert der Speicherzugriff vor negativer Veröffentlichung, beginnt
Core nicht; der alte Cursor kann aber für einen unabhängigen Sender vorhanden
bleiben. Abgeschlossenes Datei-fsync/Readback plus Prozessende beweist weder
physischen Stromausfall noch atomaren Verbundcheckpoint oder Rollback anderer
bereits fortgeschriebener Stores. Wirtschaftliche Inputherkunft, Einheiten,
Horizont und produktives numerisches Risiko bleiben eigene offene Anschlüsse.
Keine reale Venue, Orders, Credentials oder operativen Einstellungen verändert.
