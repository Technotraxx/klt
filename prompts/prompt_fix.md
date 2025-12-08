# Artikel-Korrektur

## Eingabe
1. Originaler Artikel (JSON)
2. Fehlerliste aus Check (JSON)
3. Original-Daten (JSON) – als Referenz

## Aufgabe
Korrigiere **nur die gemeldeten Fehler**. Keine weiteren Änderungen.

## Regeln
- Faktenfehler: Ersetze durch korrekten Wert aus Originaldaten
- MUSS-Fehler: Korrigiere exakt wie vorgeschlagen
- KANN-Fehler: Korrigiere wenn sinnvoll
- STIL-Hinweise: Ignorieren (optional für Redaktion)

## Output
Identisches JSON-Format wie Write-Prompt, plus:
```json
{
  "korrekturen_durchgefuehrt": [
    {
      "fehler": "[Aus Check-Liste]",
      "vorher": "[Originaltext]",
      "nachher": "[Korrigierter Text]"
    }
  ],
  "nicht_korrigiert": [
    "[Fehler die bewusst nicht korrigiert wurden + Begründung]"
  ]
}
```
