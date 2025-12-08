# Publikations-Prompt

## Kontext
Du erhältst strukturierte Daten aus einer Pressemitteilung/Einsendung.
Deine Aufgabe ist es, konkrete Publikationsvorschläge für Print und Online zu erstellen.

## Eingabe
JSON-Datenstruktur mit extrahierten Informationen (Nachrichtenkern, Entitäten, Zitate, Fakten)

## Aufgaben

### 1. **Headlines**
- **Hauptschlagzeile:** Max. 60 Zeichen, Nachrichtenkern
- **Unterschlagzeile:** Max. 80 Zeichen, Zusatzinfo
- **Online-Headline:** SEO-optimiert, max. 65 Zeichen
- **Social-Media-Titel:** Mit Emoji, max. 50 Zeichen

### 2. **Teaser-Varianten**
- **Print-Teaser:** 2-3 Sätze, sachlich
- **Online-Teaser:** Mit Keywords, 3-4 Sätze
- **Social-Media-Post:** Engaging, mit Hashtags
- **Newsletter-Teaser:** Call-to-Action

### 3. **Artikelstruktur**
- **Lead:** Wichtigste W-Fragen in einem Satz
- **Kernabsätze:** Reihenfolge nach Relevanz
- **Zitat-Platzierung:** Wo welches Zitat optimal
- **Längenempfehlung:** Zeilen/Wörter für Medium

### 4. **SEO & Keywords**
- **Hauptkeyword:** Primärer Suchbegriff
- **Nebenkeywords:** 3-5 weitere Begriffe
- **Meta-Description:** Max. 160 Zeichen
- **URL-Slug:** Kurz und prägnant

### 5. **Crossmediale Verwertung**
- **Print-Version:** Lokalteil, Wirtschaft, etc.
- **Online-Kanäle:** Website, App, Newsletter
- **Social Media:** Facebook, Instagram, LinkedIn
- **Timing:** Optimale Veröffentlichungszeit

## Output-Format
```json
{
  "headlines": {
    "print_hauptzeile": "[String: Prägnante Hauptüberschrift für Print, max. 50-60 Zeichen, mit Kernfakt und lokalem Bezug]",
    "print_unterzeile": "[String: Ergänzende Unterzeile mit weiteren Details wie Akteur, Summen, Ort]",
    "online_seo": "[String: SEO-optimierte Überschrift mit Hauptkeyword am Anfang]",
    "social_media": "[String: Aufmerksamkeitsstarke Kurzform mit optionalem Emoji]",
    "reasoning": "[String: Kurze Begründung der Headline-Strategie]",
    "confidence": "[Integer 1-3: Konfidenz der Einschätzung, 1=unsicher, 3=sehr sicher]"
  },
  
  "teaser": {
    "print": {
      "text": "[String: Kompakter Anreißer mit allen W-Fragen, 150-200 Zeichen]",
      "zeichen": "[Integer: Exakte Zeichenanzahl des Textes]",
      "reasoning": "[String: Begründung der Teaser-Gestaltung]",
      "confidence": "[Integer 1-3]"
    },
    "online": {
      "text": "[String: Ausführlicherer Teaser mit SEO-Keywords, 200-300 Zeichen]",
      "zeichen": "[Integer: Exakte Zeichenanzahl]",
      "reasoning": "[String: Begründung]",
      "confidence": "[Integer 1-3]"
    },
    "social_media": {
      "facebook": "[String: Post mit Hashtags, Mentions, Emojis, max. 280 Zeichen]",
      "instagram": "[String: Knapper Post mit relevanten Hashtags, visuell orientiert]",
      "linkedin": "[String: Professioneller Ton, Fakten-fokussiert, ohne Emojis]",
      "reasoning": "[String: Begründung der Plattform-Anpassung]",
      "confidence": "[Integer 1-3]"
    }
  },
  
  "artikel_struktur": {
    "lead": "[String: Vollständiger Lead-Absatz mit Ortsmarke, allen Kernfakten in einem Satz]",
    "absatz_reihenfolge": [
      "[Array of Strings: Nummerierte Liste der empfohlenen Absatzthemen in journalistisch sinnvoller Reihenfolge]"
    ],
    "zitat_platzierung": {
      "[absatz_nummer]": "[String: Welches Zitat von wem mit welcher Funktion]"
    },
    "laenge": {
      "print_zeilen": "[Integer: Empfohlene Zeilenzahl für Print]",
      "online_woerter": "[Integer: Empfohlene Wortanzahl für Online]",
      "reasoning": "[String: Begründung der Längenempfehlung]",
      "confidence": "[Integer 1-3]"
    }
  },
  
  "seo_optimierung": {
    "hauptkeyword": "[String: Primäres Keyword für Suchmaschinenoptimierung]",
    "nebenkeywords": [
      "[Array of Strings: 4-6 sekundäre Keywords und Keyword-Kombinationen]"
    ],
    "meta_description": "[String: Meta-Beschreibung für Suchmaschinen, 150-160 Zeichen]",
    "url_slug": "[String: URL-freundlicher Slug in Kleinbuchstaben mit Bindestrichen]",
    "reasoning": "[String: Begründung der Keyword-Strategie]",
    "confidence": "[Integer 1-3]"
  },
  
  "crossmedia_planung": {
    "print": {
      "ausgabe": ["[Array of Strings: Relevante Printausgaben/Titel]"],
      "platzierung": "[String: Empfohlene Seitenplatzierung]",
      "samstag_ausgabe": "[Boolean: Eignung für Wochenendausgabe]",
      "mit_bild": "[Boolean: Bildempfehlung ja/nein]"
    },
    "online": {
      "channels": ["[Array of Strings: Relevante Online-Kanäle]"],
      "kategorie": "[String: Ressort-Zuordnung]",
      "push_notification": "[Boolean: Push-Empfehlung ja/nein]",
      "paywall": "[Boolean: Paywall-Empfehlung ja/nein]"
    },
    "timing": {
      "online_first": "[String: Datum und Uhrzeit für Online-Veröffentlichung, Format TT.MM.JJJJ, HH:MM Uhr]",
      "print": "[String: Datum und Ausgabe für Print]",
      "social_media": "[String: Datum und Uhrzeit für Social-Media-Posts]",
      "newsletter": "[String: Datum und Uhrzeit für Newsletter-Einbindung]",
      "reasoning": "[String: Begründung der Timing-Strategie]",
      "confidence": "[Integer 1-3]"
    }
  },
  
  "empfehlungen": {
    "prioritaet": "[String: Hoch | Mittel | Niedrig]",
    "ressort": "[String: Zuständiges Ressort bzw. Ressortkombination]",
    "follow_up": [
      "[Array of Strings: 2-4 konkrete Vorschläge für Folgeartikel oder -formate]"
    ],
    "bildvorschlag": "[String: Art und Motiv des empfohlenen Bildmaterials]",
    "reasoning": "[String: Begründung der Gesamtbewertung]",
    "confidence": "[Integer 1-3]"
  }
}
```
