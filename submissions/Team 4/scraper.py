import mwclient
import mwparserfromhell
import json
import os
from tqdm import tqdm

class MetaKGPClientScraper:
    def __init__(self, output_dir="metakgp_data_clean"):
        self.site = mwclient.Site('wiki.metakgp.org', path='/')
        self.output_dir = output_dir

        os.makedirs(output_dir, exist_ok=True)

    def is_valid_page(self, title: str) -> bool:
        """
        Filter out pages we do NOT want
        """
        blacklist = ["Talk:", "File:", "Special:", "User:", "Template:"]
        return not any(title.startswith(b) for b in blacklist)

    def parse_sections(self, raw_wikitext: str):
        """
        Split raw Wikitext into section-level chunks
        """
        wikicode = mwparserfromhell.parse(raw_wikitext)
        sections = []

        for section in wikicode.get_sections(include_lead=True, flat=True):
            heading = section.filter_headings()
            heading_text = heading[0].title.strip_code() if heading else "Lead"

            text = section.strip_code().strip()
            if len(text) < 50:
                continue  

            sections.append({
                "heading": heading_text,
                "text": text
            })

        return sections

    def scrape_all(self, limit=300):
        print("Fetching pages via MetaKGP MediaWiki API...")

        page_generator = self.site.allpages(limit=limit)
        count = 0

        for page in tqdm(page_generator, total=limit):
            if count >= limit:
                break

            title = page.name

            if not self.is_valid_page(title):
                continue

            try:
                raw_text = page.text()
                if not raw_text or len(raw_text) < 100:
                    continue

                sections = self.parse_sections(raw_text)

                if not sections:
                    continue

                edges = [link.name for link in page.links()]
                url = f"https://wiki.metakgp.org/index.php/{title.replace(' ', '_')}"

                data = {
                    "title": title,
                    "url": url,
                    "sections": sections,
                    "edges": edges
                }

                with open(f"{self.output_dir}/{count}.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                count += 1

            except Exception as e:
                print(f"[SKIP] {title}: {e}")

        print(f" Scraping complete. Pages saved: {count}")



if __name__ == "__main__":
    scraper = MetaKGPClientScraper(output_dir="data")
    scraper.scrape_all(limit=4500)