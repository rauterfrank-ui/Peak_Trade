# Meta-Wissenszeit: exakter UTC-Vergleich

Der bisherige Meta-Builder verglich zulässige UTC-Zeittexte direkt. Bei wechselnder Nachkommastellenlänge war lexikalische Ordnung nicht chronologische Ordnung. Ein späterer .100Z-Evidence-Zeitpunkt wurde gegenüber derselben ganzen Sekunde zugelassen. Die historische Rekonstruktion EVI-2251 hatte G05 bereits als Codefrage markiert.

Nun werden Kalenderzeit und ganzzahlige Nanosekunden verglichen. Originalzeittexte werden nicht normalisiert oder historische Records umgeschrieben. Evidence muss bis zur Analyse bekannt sein; ein späteres Outcome muss zwischen Evidence und Analyse liegen. Ungültige Kalenderdaten werden abgelehnt. Gleiche Instants mit unterschiedlicher Präzision bleiben zulässig; Unterschiede von einer Nanosekunde werden erhalten.

34 Tests bestehen, einschließlich elf neuer Grenzfälle und vorhandener Meta/Search/M4-Verbindungen. Die gebundene normale Meta-Fixture behält exakt ihre frühere Identität. before_cases.json enthält auch einen zuvor bereits richtig abgelehnten gleichpräzisen Nanosekundenfall; dieser ist kein behaupteter alter Fehler.

Die reine UTC-Ordnung belegt keine echten Messwerte oder Originalherkunft. Börsen-/Handels-/Kapitalrechte und das ursprüngliche Lern-Ledger bleiben unverändert. Frühere Quellhashanker gelten weiterhin nur an ihrer damaligen Revision.

[Blueprint Abschnitt 40](../../blueprints/PEAKTRADE_SYSTEM_RECONFIGURATION_BLUEPRINT_2026_11_03.md).
