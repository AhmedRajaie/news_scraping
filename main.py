import pandas as pd
from tqdm import tqdm
from scraper import get_article_links, extract_article
from nlp import summarize, sentiment

results = []

links = get_article_links(pages=3)

for url in tqdm(links):
    try:
        article = extract_article(url)
        summary = summarize(article["text"])
        sent = sentiment(article["text"])

        results.append({
            "url": article["url"],
            "title": article["title"],
            "summary": summary,
            "sentiment": sent["label"],
            "confidence": sent["score"]
        })

    except Exception as e:
        print(f"Error with {url}: {e}")

df = pd.DataFrame(results)
df.to_csv("data.csv", index=False, encoding="utf-8-sig")