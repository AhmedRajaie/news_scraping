import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from urllib.parse import urljoin

class AlBorsaNewsScraper:
    def __init__(self):
        self.base_url = "https://www.alborsaanews.com"
        self.category_url = f"{self.base_url}/category/%d8%a7%d9%84%d8%a8%d9%88%d8%b1%d8%b5%d8%a9-%d9%88%d8%a7%d9%84%d8%b4%d8%b1%d9%83%d8%a7%d8%aa"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.articles_data = []
    
    def get_article_links_from_page(self, page_number=1):
        """Extract article links from a category page"""
        if page_number == 1:
            url = self.category_url
        else:
            url = f"{self.category_url}/page/{page_number}"
        
        print(f"Fetching article links from page {page_number}...")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all article links
            article_links = []
            
            # Look for article titles with links
            articles = soup.find_all('h2') + soup.find_all('h3')
            
            for article in articles:
                link = article.find('a')
                if link and link.get('href'):
                    article_url = link.get('href')
                    if article_url.startswith('http'):
                        article_links.append(article_url)
            
            print(f"Found {len(article_links)} articles on page {page_number}")
            return article_links
            
        except Exception as e:
            print(f"Error fetching page {page_number}: {e}")
            return []
    
    def extract_article_content(self, article_url):
        """Extract full content from an article page"""
        print(f"Extracting: {article_url}")
        
        try:
            response = requests.get(article_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = ""
            title_tag = soup.find('h1', class_='jeg_post_title') or soup.find('h1')
            if title_tag:
                title = title_tag.get_text(strip=True)
            
            # Extract author
            author = ""
            author_tag = soup.find('div', class_='jeg_meta_author') or soup.find('a', rel='author')
            if author_tag:
                author = author_tag.get_text(strip=True)
            
            # Extract date
            date = ""
            date_tag = soup.find('div', class_='jeg_meta_date') or soup.find('time')
            if date_tag:
                date = date_tag.get_text(strip=True)
            
            # Extract category
            category = ""
            category_tag = soup.find('div', class_='jeg_meta_category') or soup.find('a', rel='category tag')
            if category_tag:
                category = category_tag.get_text(strip=True)
            
            # Extract main content
            content = ""
            content_div = soup.find('div', class_='content-inner') or soup.find('div', class_='entry-content') or soup.find('article')
            
            if content_div:
                # Remove script and style tags
                for script in content_div(['script', 'style']):
                    script.decompose()
                
                # Get paragraphs
                paragraphs = content_div.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            
            article_data = {
                'url': article_url,
                'title': title,
                'author': author,
                'date': date,
                'category': category,
                'content': content,
                'scraped_at': datetime.now().isoformat()
            }
            
            return article_data
            
        except Exception as e:
            print(f"Error extracting article {article_url}: {e}")
            return None
    
    def scrape_articles(self, start_page=1, end_page=1, delay=1):
        """Scrape articles from multiple pages"""
        print(f"Starting to scrape pages {start_page} to {end_page}")
        
        all_article_links = []
        
        # Collect all article links first
        for page_num in range(start_page, end_page + 1):
            links = self.get_article_links_from_page(page_num)
            all_article_links.extend(links)
            time.sleep(delay)  # Be respectful to the server
        
        # Remove duplicates
        all_article_links = list(set(all_article_links))
        print(f"\nTotal unique articles to scrape: {len(all_article_links)}\n")
        
        # Extract content from each article
        for idx, article_url in enumerate(all_article_links, 1):
            print(f"\n[{idx}/{len(all_article_links)}]")
            article_data = self.extract_article_content(article_url)
            
            if article_data:
                self.articles_data.append(article_data)
            
            time.sleep(delay)  # Be respectful to the server
        
        print(f"\n✓ Successfully scraped {len(self.articles_data)} articles")
        return self.articles_data
    
    def save_to_json(self, filename='AlBorsaArticles.json'):
        """Save articles to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.articles_data, f, ensure_ascii=False, indent=2)
        print(f"✓ Saved to {filename}")


# Example usage
if __name__ == "__main__":
    # Initialize scraper
    scraper = AlBorsaNewsScraper()
    
    # Scrape articles from pages 1-3 (adjust as needed)
    # Note: Be respectful and don't scrape too many pages at once
    articles = scraper.scrape_articles(start_page=1, end_page=2, delay=2)
    
    # Save to JSON format
    scraper.save_to_json('AlBorsaArticles.json')
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*80}")
    print(f"Total articles scraped: {len(articles)}")
    print(f"File created: AlBorsaArticles.json")
    