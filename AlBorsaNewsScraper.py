import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime

class AlBorsaNewsScraper:
    def __init__(self):
        self.base_url = "https://www.alborsaanews.com"
        self.category_url = f"{self.base_url}/category/%d8%a7%d9%84%d8%a8%d9%88%d8%b1%d8%b5%d8%a9-%d9%88%d8%a7%d9%84%d8%b4%d8%b1%d9%83%d8%a7%d8%aa"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.articles_data = []
        self.seen_urls = set()  # Track URLs to avoid duplicates
        self.static_articles = set()  # Track static articles that appear on every page
    
    def get_article_links_from_page(self, page_number=1, identify_static=False):
        """Extract article links from a category page"""
        if page_number == 1:
            url = self.category_url
        else:
            url = f"{self.category_url}/page/{page_number}"
        
        print(f"\n{'='*80}")
        print(f"📰 Fetching Page {page_number}")
        print(f"   URL: {url}")
        print("="*80)
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all article links
            article_links = []
            
            # Method 1: Find h2 and h3 tags with links (main article titles)
            headlines = soup.find_all(['h2', 'h3'])
            
            for headline in headlines:
                link = headline.find('a', href=True)
                if link and link.get('href'):
                    article_url = link.get('href')
                    if article_url.startswith('http'):
                        article_links.append(article_url)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_links = []
            for link in article_links:
                if link not in seen:
                    seen.add(link)
                    unique_links.append(link)
            
            article_links = unique_links
            
            # If this is page 1 and we're identifying static articles
            if page_number == 1 and identify_static:
                print(f"\n   ℹ️  Analyzing page structure to identify static articles...")
                # Store all links from page 1 to compare with page 2
                return article_links, set(article_links)
            
            # Filter out static articles if we've identified them
            if self.static_articles:
                before_filter = len(article_links)
                article_links = [link for link in article_links if link not in self.static_articles]
                filtered_count = before_filter - len(article_links)
                if filtered_count > 0:
                    print(f"   🔹 Filtered out {filtered_count} static articles")
            
            # Filter out already seen articles
            new_links = []
            for link in article_links:
                if link not in self.seen_urls:
                    new_links.append(link)
                    self.seen_urls.add(link)
            
            duplicate_count = len(article_links) - len(new_links)
            if duplicate_count > 0:
                print(f"   🔹 Skipped {duplicate_count} duplicate articles")
            
            print(f"\n   ✅ Found {len(new_links)} new unique articles on this page")
            
            if new_links and len(new_links) <= 5:
                print(f"\n   📄 Sample articles:")
                for url in new_links[:5]:
                    print(f"      • {url}")
            
            return new_links, None
            
        except Exception as e:
            print(f"   ❌ Error fetching page {page_number}: {e}")
            return [], None
    
    def identify_static_articles(self):
        """Identify static articles by comparing page 1 and page 2"""
        print("\n" + "="*80)
        print("🔍 IDENTIFYING STATIC ARTICLES")
        print("="*80)
        print("Comparing pages 1 and 2 to find articles that appear on both...")
        
        # Temporarily store the current seen_urls
        original_seen = self.seen_urls.copy()
        
        # Clear seen_urls for identification phase
        self.seen_urls = set()
        
        # Get articles from page 1
        page1_links, page1_set = self.get_article_links_from_page(1, identify_static=True)
        time.sleep(1)
        
        # Get articles from page 2
        page2_links, _ = self.get_article_links_from_page(2, identify_static=False)
        page2_set = set(page2_links)
        
        # Find common articles (these are static/featured)
        static = page1_set.intersection(page2_set)
        
        if static:
            self.static_articles = static
            print(f"\n   ✅ Identified {len(static)} static articles that appear on every page")
            print(f"\n   📌 Static articles (will be excluded):")
            for url in static:
                print(f"      • {url}")
        else:
            print(f"\n   ℹ️  No static articles detected")
        
        # Clear seen_urls again so scraping starts fresh
        self.seen_urls = set()
        
        print("\n" + "="*80)
    
    def extract_article_content(self, article_url, verbose=False):
        """Extract full content from an article page"""
        if verbose:
            print(f"\n📄 Extracting: {article_url}")
        
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
            
            if verbose:
                print(f"   Title: {title[:70]}..." if len(title) > 70 else f"   Title: {title}")
            
            # Extract author
            author = ""
            author_tag = soup.find('div', class_='jeg_meta_author') or soup.find('a', rel='author')
            if author_tag:
                author = author_tag.get_text(strip=True)
            
            if verbose and author:
                print(f"   Author: {author}")
            
            # Extract date
            date = ""
            date_tag = soup.find('div', class_='jeg_meta_date') or soup.find('time')
            if date_tag:
                date = date_tag.get_text(strip=True)
            
            if verbose and date:
                print(f"   Date: {date}")
            
            # Extract category - try multiple methods
            category = ""
            # Method 1: Look for category link
            category_tag = soup.find('a', rel='category tag')
            if not category_tag:
                # Method 2: Look for meta category div
                category_tag = soup.find('div', class_='jeg_meta_category')
            if not category_tag:
                # Method 3: Look for any link with 'category' in href
                category_links = soup.find_all('a', href=True)
                for link in category_links:
                    if '/category/' in link.get('href', ''):
                        category_tag = link
                        break
            
            if category_tag:
                category = category_tag.get_text(strip=True)
            
            if verbose:
                print(f"   Category: {category if category else 'N/A'}")
            
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
            
            if verbose:
                content_preview = content[:100] + "..." if len(content) > 100 else content
                print(f"   Content length: {len(content)} chars")
                if content:
                    print(f"   Preview: {content_preview}")
            
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
            if verbose:
                print(f"   ❌ Error extracting article: {e}")
            return None
    
    def scrape_articles(self, start_page=1, end_page=1, delay=1, verbose=False):
        """Scrape articles from multiple pages"""
        print("\n" + "="*80)
        print("ALBORSA NEWS SCRAPER")
        print("="*80)
        print(f"Pages: {start_page} to {end_page}")
        print(f"Delay: {delay} seconds between requests")
        print("="*80)
        
        # First, identify static articles by comparing page 1 and 2
        if start_page == 1:
            self.identify_static_articles()
            time.sleep(delay)
        
        # Now scrape the requested pages
        print("\n" + "="*80)
        print("SCRAPING ARTICLES")
        print("="*80)
        
        all_article_links = []
        
        # Collect all article links
        for page_num in range(start_page, end_page + 1):
            links, _ = self.get_article_links_from_page(page_num)
            all_article_links.extend(links)
            time.sleep(delay)
        
        print(f"\n" + "="*80)
        print(f"📊 TOTAL: {len(all_article_links)} unique articles to extract")
        print("="*80)
        
        if not all_article_links:
            print("\n⚠️  No articles found!")
            return []
        
        # Extract content from each article
        print("\n" + "="*80)
        print("EXTRACTING ARTICLE CONTENT")
        print("="*80)
        
        for idx, article_url in enumerate(all_article_links, 1):
            print(f"\n[{idx}/{len(all_article_links)}]")
            article_data = self.extract_article_content(article_url, verbose=verbose)
            
            if article_data:
                self.articles_data.append(article_data)
                if not verbose:
                    print(f"   ✅ {article_data['title'][:60]}...")
            
            time.sleep(delay)
        
        print(f"\n" + "="*80)
        print(f"✅ SCRAPING COMPLETE!")
        print(f"   Successfully scraped: {len(self.articles_data)} articles")
        print("="*80)
        
        return self.articles_data
    
    def save_to_json(self, filename='AlBorsaNewsScraped.json'):
        """Save articles to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.articles_data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Saved {len(self.articles_data)} articles to {filename}")


# Example usage
if __name__ == "__main__":
    # Initialize scraper
    scraper = AlBorsaNewsScraper()
    
    # Scrape articles from pages 1-3
    # Set verbose=True to see detailed extraction info
    articles = scraper.scrape_articles(start_page=1, end_page=3, delay=2, verbose=False)
    
    if articles:
        # Save to JSON format
        scraper.save_to_json('AlBorsaNewsScraped.json')
        
        # Print summary
        print(f"\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total articles: {len(articles)}")
        
        # Show categories
        categories = {}
        for article in articles:
            cat = article.get('category', 'N/A')
            categories[cat] = categories.get(cat, 0) + 1
        
        if categories:
            print(f"\nArticles by category:")
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {cat}: {count}")
        
        # Show sample
        if articles:
            print(f"\n📄 Sample article:")
            print(f"   Title: {articles[0]['title']}")
            print(f"   Date: {articles[0]['date']}")
            print(f"   Category: {articles[0]['category']}")
            print(f"   Content: {len(articles[0]['content'])} characters")
    else:
        print("\n⚠️  No articles were scraped")
        