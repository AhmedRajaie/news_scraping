#**Getting the headlines of articles in the website
# Import libraries
import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL of the news website
news_page_url = "https://www.alborsaanews.com/category/%D8%A7%D9%84%D8%A8%D9%88%D8%B1%D8%B5%D8%A9-%D9%88%D8%A7%D9%84%D8%B4%D8%B1%D9%83%D8%A7%D8%AA"

# Send HTTP GET request
response = requests.get(news_page_url)
response.encoding = 'utf-8'

# Check if the request was successful
print("Status code:", response.status_code)

# Parse HTML
soup = BeautifulSoup(response.text, "html.parser")

# Find all <h2> tags (headlines)
headline_tags = soup.find_all("h2")

# Extract the text of the first 5 headlines
headlines = [tag.get_text(strip=True) for tag in headline_tags[:5]]

# Print the headlines
for i, headline in enumerate(headlines, start=1):
    print(i, headline)

# Save headlines to Excel (no encoding needed)
df = pd.DataFrame(headlines, columns=["Headline"])
df.to_excel("headlines.xlsx", index=False)

print("Headlines saved to headlines.xlsx successfully!")

# URL of the news website
url = "https://www.alborsaanews.com/category/%D8%A7%D9%84%D8%A8%D9%88%D8%B1%D8%B5%D8%A9-%D9%88%D8%A7%D9%84%D8%B4%D8%B1%D9%83%D8%A7%D8%AA"

# Send HTTP GET request
response = requests.get(url)
response.encoding = 'utf-8'

# Check if the request was successful
print("Status code:", response.status_code)

# Parse HTML
soup = BeautifulSoup(response.text, "html.parser")

#**Titles in homepage**
titles = []

# Titles in <h2>
for tag in soup.find_all("h2"):
    title = tag.get_text(strip=True)
    if title:
        titles.append(title)

# Titles in <h1>, <h3>, <h4>
for tag in soup.find_all(["h1", "h3", "h4"]):
    title = tag.get_text(strip=True)
    if title:
        titles.append(title)

# Titles in <a> tags with a title attribute
for tag in soup.find_all("a", title=True):
    title = tag.get("title").strip()
    if title and title not in titles:
        titles.append(title)

# Remove duplicates
titles = list(dict.fromkeys(titles))

# Remove the last 5 titles
titles = titles[:-5] if len(titles) > 5 else []

# Print titles
for i, title in enumerate(titles, start=1):
    print(i, title)

# Save to Excel
df = pd.DataFrame(titles, columns=["Title"])
df.to_excel("all_titles.xlsx", index=False)

print(f"{len(titles)} titles saved to all_titles.xlsx successfully!")