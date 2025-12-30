import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# ---------------------------
# 1️⃣ Main page URL
# ---------------------------
main_url = "https://www.alborsaanews.com"  # You can change to a category page
response = requests.get(main_url)
soup = BeautifulSoup(response.text, "html.parser")

# ---------------------------
# 2️⃣ Extract article links
# ---------------------------
articles = soup.find_all("a", href=True)
article_links = []
for a in articles:
    href = a['href']
    if "/2025/" in href and href not in article_links:
        article_links.append(href)

print(f"Found {len(article_links)} articles.")

# ---------------------------
# 3️⃣ Initialize sentiment analyzer
# ---------------------------
analyzer = SentimentIntensityAnalyzer()

# ---------------------------
# 4️⃣ Function to process a single article
# ---------------------------
def process_article(url):
    if url.startswith("/"):
        url_full = main_url + url
    else:
        url_full = url

    try:
        res = requests.get(url_full, timeout=10)
        article_soup = BeautifulSoup(res.text, "lxml")  # faster parser

        # Extract article text
        body = article_soup.find("div", {"class": "post-content"})
        text = body.get_text(separator=" ", strip=True) if body else article_soup.get_text(separator=" ", strip=True)

        # Optional: Extract title
        title_tag = article_soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "No Title"

        # TextBlob sentiment
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        # VADER sentiment
        vader_scores = analyzer.polarity_scores(text)
        if vader_scores["compound"] >= 0.05:
            overall = "Positive"
        elif vader_scores["compound"] <= -0.05:
            overall = "Negative"
        else:
            overall = "Neutral"

        return {
            "Title": title,
            "URL": url_full,
            "Text Length": len(text),
            "TextBlob Polarity": polarity,
            "TextBlob Subjectivity": subjectivity,
            "VADER Compound": vader_scores["compound"],
            "VADER Positive": vader_scores["pos"],
            "VADER Neutral": vader_scores["neu"],
            "VADER Negative": vader_scores["neg"],
            "Overall Sentiment": overall
        }

    except Exception as e:
        print(f"Error processing {url_full}: {e}")
        return None

# ---------------------------
# 5️⃣ Parallel processing
# ---------------------------
results = []
with ThreadPoolExecutor(max_workers=10) as executor:
    for result in executor.map(process_article, article_links):
        if result:
            results.append(result)

# ---------------------------
# 6️⃣ Save to Excel
# ---------------------------
df = pd.DataFrame(results)
df.to_excel("articles_sentiment.xlsx", index=False, engine='openpyxl')  # no encoding needed
print("✅ Sentiment analysis saved to articles_sentiment.xlsx")



