import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.alborsaanews.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}

ARTICLE_REGEX = re.compile(r"/\d{4}/\d{2}/")

def get_article_links(pages=2):
    links = set()

    for page in range(1, pages + 1):
        url = f"{BASE_URL}/page/{page}/"
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if ARTICLE_REGEX.search(href):
                links.add(href)

    print(f"Found {len(links)} article links")
    return list(links)


def extract_article(url):
    r = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "lxml")

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "No title"

    content = soup.find("div", class_="entry-content")
    paragraphs = content.find_all("p") if content else []
    text = "\n".join(p.get_text(strip=True) for p in paragraphs)

    return {
        "url": url,
        "title": title,
        "text": text
    }