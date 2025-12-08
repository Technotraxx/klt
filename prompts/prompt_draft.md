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
    "print_hauptzeile": "Neues Tech-Zentrum: 50 Jobs für Hannover",
    "print_unterzeile": "Beispiel GmbH investiert 12 Millionen Euro in Start-up-Campus",
    "online_seo": "Technologiezentrum Hannover eröffnet - 50 neue Arbeitsplätze",
    "social_media": "🚀 Tech-Boom in Hannover: Neues Zentrum eröffnet!",
    "reasoning": "Lokaler Bezug + Arbeitsplätze als Aufmacher",
    "confidence": 2
  },
  
  "teaser": {
    "print": {
      "text": "Die Beispiel GmbH eröffnet am 15. März ein 5000 Quadratmeter großes Technologiezentrum in Hannover. Mit einer Investition von 12 Millionen Euro entstehen 50 neue Arbeitsplätze.",
      "zeichen": 180,
      "reasoning": "Alle Kernfakten kompakt",
      "confidence": 2
    },
    "online": {
      "text": "Hannover bekommt ein neues Technologiezentrum: Die Beispiel GmbH investiert 12 Millionen Euro in einen modernen Start-up-Campus. Am 15. März wird das 5000 Quadratmeter große Zentrum eröffnet, das Platz für 50 neue Arbeitsplätze bietet.",
      "zeichen": 245,
      "reasoning": "SEO-Keywords integriert",
      "confidence": 2
    },
    "social_media": {
      "facebook": "🎉 Große Neuigkeiten für #Hannover! Die Beispiel GmbH eröffnet ein hochmodernes Technologiezentrum. 12 Mio. € Investition = 50 neue Jobs! Eröffnung am 15.3. mit OB @belitOnay. #Innovation #Startups #Wirtschaft",
      "instagram": "Tech-Boom in Hannover! 🚀 Neues Zentrum → 50 Jobs 💼 Opening 15.3. #hannoverliebe #startuplife #innovation",
      "linkedin": "Beispiel GmbH investiert 12 Mio. EUR in neues Technologiezentrum Hannover. 5000qm für innovative Start-ups. Eröffnung 15.03.2024. Ein wichtiger Schritt für den Wirtschaftsstandort Region Hannover.",
      "reasoning": "Plattformspezifisch optimiert",
      "confidence": 1
    }
  },
  
  "artikel_struktur": {
    "lead": "HANNOVER. Mit einer Investition von 12 Millionen Euro eröffnet die Beispiel GmbH am 15. März ein 5000 Quadratmeter großes Technologiezentrum im Technologiepark Hannover, das 50 neue Arbeitsplätze schaffen soll.",
    "absatz_reihenfolge": [
      "1. Eröffnungsdetails und Investitionssumme",
      "2. Zitat Oberbürgermeister zur Bedeutung",
      "3. Details zum Zentrum und Ausstattung",
      "4. Zitat Geschäftsführer zu Zielen",
      "5. Hintergrund Digitalisierungsstrategie",
      "6. Infobox mit Termin Tag der offenen Tür"
    ],
    "zitat_platzierung": {
      "absatz_2": "Zitat Onay - politische Einordnung",
      "absatz_4": "Zitat Weber - Unternehmensperspektive"
    },
    "laenge": {
      "print_zeilen": 45,
      "online_woerter": 350,
      "reasoning": "Standardlänge Wirtschaftslokal",
      "confidence": 1
    }
  },
  
  "seo_optimierung": {
    "hauptkeyword": "Technologiezentrum Hannover",
    "nebenkeywords": [
      "Start-up Campus Hannover",
      "Beispiel GmbH",
      "Arbeitsplätze Hannover",
      "Innovation Hannover",
      "Technologiepark"
    ],
    "meta_description": "Beispiel GmbH eröffnet neues Technologiezentrum in Hannover. 12 Mio Euro Investition schafft 50 Arbeitsplätze für Start-ups. Eröffnung am 15. März 2024.",
    "url_slug": "technologiezentrum-hannover-eroeffnung-2024",
    "reasoning": "Lokale + thematische Keywords",
    "confidence": 2
  },
  
  "crossmedia_planung": {
    "print": {
      "ausgabe": ["HAZ Lokalteil", "NP Wirtschaft"],
      "platzierung": "Seite 1 Lokalteil oder Wirtschaft",
      "samstag_ausgabe": true,
      "mit_bild": true
    },
    "online": {
      "channels": ["HAZ.de", "NP-Online", "Newsletter"],
      "kategorie": "Wirtschaft/Lokales",
      "push_notification": false,
      "paywall": false
    },
    "timing": {
      "online_first": "15.03.2024, 06:00 Uhr",
      "print": "15.03.2024, Morgenausgabe",
      "social_media": "15.03.2024, 11:00 Uhr",
      "newsletter": "15.03.2024, 17:00 Uhr",
      "reasoning": "Termingebunden, Morgenpublikation",
      "confidence": 2
    }
  },
  
  "empfehlungen": {
    "prioritaet": "Hoch",
    "ressort": "Wirtschaft/Lokales",
    "follow_up": [
      "Fotostrecke Tag der offenen Tür",
      "Interview mit ersten Start-ups",
      "Hintergrund: Start-up-Szene Hannover"
    ],
    "bildvorschlag": "Rendering/Foto Technologiezentrum prominent",
    "reasoning": "Hoher Lokalbezug + Wirtschaftsrelevanz",
    "confidence": 2
  }
}
```
