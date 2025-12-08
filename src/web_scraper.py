"""
Web Scraper Modul für Presseportal.de
"""
import requests
import json
from bs4 import BeautifulSoup

class PresseportalScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def scrape(self, url):
        """
        Scraped eine Presseportal URL und gibt ein Dict zurück.
        """
        if "presseportal.de" not in url:
            return {"error": "URL muss von presseportal.de sein"}

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            data = {
                "url": url,
                "metadata": {},
                "content": "",
                "pdf_url": None,
                "tags": [],
                "images": []
            }

            # 1. JSON-LD Metadaten extrahieren (Sehr zuverlässig)
            json_ld = soup.find('script', type='application/ld+json', string=lambda t: t and 'NewsArticle' in t)
            if json_ld:
                try:
                    meta = json.loads(json_ld.string)
                    data["metadata"]["headline"] = meta.get("headline")
                    data["metadata"]["date"] = meta.get("datePublished")
                    data["metadata"]["description"] = meta.get("description")
                    if "author" in meta and isinstance(meta["author"], dict):
                        data["metadata"]["sender"] = meta["author"].get("name")
                except:
                    pass

            # 2. PDF Link finden
            # Suche nach Link in der Docs-Box
            pdf_link = soup.select_one('a[data-label="pdf"]')
            if pdf_link and pdf_link.has_attr('href'):
                data["pdf_url"] = pdf_link['href']

            # 3. Tags extrahieren
            tags = soup.select('ul.tags li a')
            data["tags"] = [tag.get_text(strip=True) for tag in tags]

            # 4. Haupttext extrahieren (Body)
            # Wir holen den Text aus dem Artikel-Card div
            article_card = soup.select_one('article .card')
            if article_card:
                paragraphs = article_card.find_all('p')
                text_content = []
                
                for p in paragraphs:
                    text = p.get_text(" ", strip=True)
                    # Stop-Kriterien um Boilerplate am Ende zu vermeiden
                    if "Rückfragen bitte an:" in text or "Original-Content von:" in text:
                        break
                    # Metadaten-Zeilen überspringen (z.B. Datum am Anfang)
                    if p.get("class") and "date" in p.get("class"):
                        continue
                    if text:
                        text_content.append(text)
                
                data["content"] = "\n\n".join(text_content)

            # Fallback falls JSON-LD fehlte
            if not data["metadata"].get("headline") and article_card:
                h1 = article_card.find('h1')
                if h1: data["metadata"]["headline"] = h1.get_text(strip=True)

            return data

        except Exception as e:
            return {"error": str(e)}

    def format_for_llm(self, data):
        """Formatiert die Scrape-Daten als String für den Context"""
        if "error" in data:
            return f"FEHLER BEIM SCRAPING: {data['error']}"
            
        return (
            f"--- SCRAPED DATEN VON {data['url']} ---\n"
            f"HEADLINE: {data['metadata'].get('headline')}\n"
            f"ABSENDER: {data['metadata'].get('sender')}\n"
            f"DATUM: {data['metadata'].get('date')}\n"
            f"TAGS: {', '.join(data['tags'])}\n"
            f"PDF URL: {data['pdf_url']}\n\n"
            f"INHALT:\n{data['content']}\n"
            f"----------------------------------------"
        )
