#**Extracting articles
# Import libraries
import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL of the news category
category_url = "https://www.alborsaanews.com/category/%D8%A7%D9%84%D8%A8%D9%88%D8%B1%D8%B5%D8%A9-%D9%88%D8%A7%D9%84%D8%B4%D8%B1%D9%83%D8%A7%D8%AA"

# Send HTTP GET request
response = requests.get(category_url)
response.encoding = 'utf-8'

soup = BeautifulSoup(response.text, "html.parser")

# 1. Find all article links
article_links = []
for a_tag in soup.find_all("a", href=True):
    href = a_tag['href']
    # Filter URLs that look like articles (contains year/month/day in URL)
    if "/202" in href and href.startswith("https://www.alborsaanews.com/"):
        article_links.append(href)

# Remove duplicates
article_links = list(dict.fromkeys(article_links))
print(f"Found {len(article_links)} article links.")

# 2. Extract title + article content
data = []

for link in article_links:
    try:
        resp = requests.get(link)
        resp.encoding = 'utf-8'
        article_soup = BeautifulSoup(resp.text, "html.parser")
        
        # Get title
        title_tag = article_soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "No title"
        
        # Get article content (usually in <p> tags inside div)
        paragraphs = article_soup.find_all("p")
        content = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        data.append({"Title": title, "URL": link, "Content": content})
        
        print(f"Extracted: {title}")
        
    except Exception as e:
        print(f"Error fetching {link}: {e}")

# 3. Save to Excel
df = pd.DataFrame(data)
df.to_excel("articles.xlsx", index=False)
print(f"{len(data)} articles saved to articles.xlsx successfully!")
print()

#**Summarizing all articles
# Function to summarize text in Arabic by splitting on Arabic periods
def summarize_text(text, num_sentences=5):
    # Arabic full stop "۔" or fallback to English period "."
    sentences = text.split("۔")
    if len(sentences) < 2:
        sentences = text.split(".")
    # Remove empty strings
    sentences = [s.strip() for s in sentences if s.strip()]
    return "۔ ".join(sentences[:num_sentences]) + ("۔" if sentences else "")

# URL of the news category
category_url = "https://www.alborsaanews.com/category/%D8%A7%D9%84%D8%A8%D9%88%D8%B1%D8%B5%D8%A9-%D9%88%D8%A7%D9%84%D8%B4%D8%B1%D9%83%D8%A7%D8%AA"

# Send GET request
response = requests.get(category_url)
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, "html.parser")

# 1. Find article links (filter by year in URL)
article_links = []
for a_tag in soup.find_all("a", href=True):
    href = a_tag['href']
    if "/202" in href and href.startswith("https://www.alborsaanews.com/"):
        article_links.append(href)

# Remove duplicates
article_links = list(dict.fromkeys(article_links))
print(f"Found {len(article_links)} article links.")

# 2. Extract articles and summarize
data = []

for link in article_links:
    try:
        resp = requests.get(link)
        resp.encoding = 'utf-8'
        article_soup = BeautifulSoup(resp.text, "html.parser")
        
        # Title
        title_tag = article_soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "No title"
        
        # Article content
        paragraphs = article_soup.find_all("p")
        content = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        # Summarize first 5 sentences
        summary = summarize_text(content, num_sentences=5)
        
        data.append({
            "Title": title,
            "URL": link,
            "Content": content,
            "Summary": summary
        })
        print(f"Summarized: {title}")
        
    except Exception as e:
        print(f"Error fetching {link}: {e}")

# 3. Save results to Excel
df = pd.DataFrame(data)
df.to_excel("articles_with_summaries.xlsx", index=False)
print(f"{len(data)} articles summarized and saved to articles_with_summaries.xlsx successfully!")