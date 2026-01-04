"""
Mubasher Egypt Article Scraper with Dynamic Content Handling
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime

def setup_driver():
    """Setup Chrome driver"""
    print("Setting up browser...")
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver

def wait_and_inspect_page(driver, wait_time=10):
    """Wait for page to fully load and inspect it"""
    print(f"\nWaiting {wait_time} seconds for page to load completely...")
    time.sleep(wait_time)
    
    # Additional wait for any input fields
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "input"))
        )
        print("✓ Input fields detected")
    except:
        print("⚠ No input fields found with WebDriverWait")
    
    # Save page for inspection
    with open('login_page_debug.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("✓ Saved page HTML to 'login_page_debug.html'")
    
    # Take screenshot
    driver.save_screenshot('login_page_screenshot.png')
    print("✓ Saved screenshot to 'login_page_screenshot.png'")
    
    # Parse and show all inputs
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    inputs = soup.find_all('input')
    
    print(f"\nFound {len(inputs)} input fields:")
    for inp in inputs:
        print(f"  ID: {inp.get('id', 'N/A'):<20} Name: {inp.get('name', 'N/A'):<20} Type: {inp.get('type', 'N/A'):<15} Placeholder: {inp.get('placeholder', 'N/A')}")
    
    return len(inputs) > 0

def login_to_mubasher(driver, email, password):
    """Login to Mubasher"""
    print("\n" + "="*60)
    print("ATTEMPTING LOGIN")
    print("="*60)
    
    driver.get("https://english.mubasher.info/account/login")
    
    # Wait for page to fully load
    if not wait_and_inspect_page(driver, wait_time=8):
        print("\n⚠ WARNING: No input fields found!")
        print("\nPossible issues:")
        print("1. Page requires user interaction (click a 'Login' button first)")
        print("2. JavaScript not loading properly")
        print("3. Site may be detecting automation")
        print("\nLet's try to find any clickable login elements...")
        
        # Try to find and click any "Login" or "Sign In" buttons/links
        try:
            login_triggers = driver.find_elements(By.XPATH, 
                "//*[contains(text(), 'Login') or contains(text(), 'Sign in') or contains(text(), 'log in')]")
            if login_triggers:
                print(f"✓ Found {len(login_triggers)} potential login triggers")
                login_triggers[0].click()
                print("✓ Clicked first login trigger, waiting...")
                time.sleep(5)
                wait_and_inspect_page(driver, wait_time=3)
        except Exception as e:
            print(f"Could not find login triggers: {e}")
    
    print("\n" + "="*60)
    print("MANUAL LOGIN MODE")
    print("="*60)
    print("\nThe browser window is open. Please:")
    print("1. Manually log in to Mubasher in the browser window")
    print("2. Once logged in, return here and press Enter")
    print("\nWaiting for you to complete login...")
    
    input("\nPress Enter after you've logged in manually...")
    
    # Check if login successful
    current_url = driver.current_url.lower()
    print(f"\nCurrent URL: {driver.current_url}")
    
    if "login" not in current_url:
        print("✓ Login appears successful!")
        return True
    else:
        print("⚠ Still on login page")
        retry = input("Try to continue anyway? (y/n): ")
        return retry.lower() == 'y'

def get_article_links(driver, url, max_links=30):
    """Get article links from listing page"""
    print(f"\n{'='*60}")
    print(f"Getting article links from: {url}")
    print("="*60)
    
    driver.get(url)
    print("Waiting for page to load...")
    time.sleep(5)
    
    # Scroll to load lazy content
    print("Scrolling to load more content...")
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    
    # Parse page
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # EXCLUDE these patterns - they are NOT articles
    exclude_patterns = [
        '/category/',
        '/now/exclusive',
        '/now/announcements',
        '/mubasherblog',
        '/oil-and-energy',
        '/banking',
        '/Category/',
        '/countries/',
        '/markets/EGX',
        'facebook.com',
        'twitter.com',
        'linkedin.com'
    ]
    
    # INCLUDE only these patterns - actual articles
    include_patterns = [
        '/news/4',  # Article IDs start with number
        '/news/eg/4',
        '/markets/news/4'
    ]
    
    # Find all article links
    article_links = []
    links = soup.find_all('a', href=True)
    
    for link in links:
        href = link.get('href', '')
        
        # Skip if matches exclude patterns
        if any(pattern in href for pattern in exclude_patterns):
            continue
        
        # Only include if matches article patterns
        if not any(pattern in href for pattern in include_patterns):
            continue
        
        full_url = href if href.startswith('http') else 'https://english.mubasher.info' + href
        
        # Get title from link text
        title = link.get_text(strip=True)
        
        # Filter out empty titles, very short titles, and navigation items
        if len(title) < 20 or title in ['Read More', 'More', 'News', 'Articles']:
            continue
        
        # Avoid duplicates
        if full_url not in [a['url'] for a in article_links]:
            article_links.append({
                'url': full_url,
                'title': title
            })
            
            if len(article_links) >= max_links:
                break
    
    print(f"✓ Found {len(article_links)} unique article links")
    return article_links

def extract_full_article(driver, article_url):
    """Extract full article content from article page"""
    try:
        driver.get(article_url)
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Extract article title
        title = ""
        title_elem = soup.find('h1')
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        # Extract article date/time
        date = ""
        date_elem = soup.find('time') or soup.find(class_=['date', 'published', 'post-date', 'article-date'])
        if date_elem:
            date = date_elem.get('datetime', date_elem.get_text(strip=True))
        
        # Extract author - try multiple strategies
        author = ""
        
        # Strategy 1: Look for author class
        author_elem = soup.find(class_=['author', 'byline', 'writer', 'article-author', 'post-author'])
        if author_elem:
            author = author_elem.get_text(strip=True).replace('By', '').replace('by', '').strip()
        
        # Strategy 2: Look for author in meta tags
        if not author:
            author_meta = soup.find('meta', {'name': 'author'}) or soup.find('meta', {'property': 'article:author'})
            if author_meta:
                author = author_meta.get('content', '').strip()
        
        # Strategy 3: Look for "By [Name]" pattern in text
        if not author:
            for p in soup.find_all('p', limit=3):
                text = p.get_text(strip=True)
                if text.startswith('By ') and len(text) < 50:
                    author = text.replace('By', '').replace('–', '').strip()
                    break
        
        # Extract category/tags - improved
        category = ""
        
        # Strategy 1: Look for breadcrumbs
        breadcrumb = soup.find(class_=['breadcrumb', 'breadcrumbs'])
        if breadcrumb:
            links = breadcrumb.find_all('a')
            if len(links) > 1:
                category = links[-1].get_text(strip=True)
        
        # Strategy 2: Look for category/tag elements
        if not category:
            category_elem = soup.find(class_=['category', 'tag', 'section', 'article-category', 'post-category', 'news-category'])
            if category_elem:
                category = category_elem.get_text(strip=True)
        
        # Strategy 3: Look for meta tags
        if not category:
            category_meta = soup.find('meta', {'property': 'article:section'}) or soup.find('meta', {'name': 'category'})
            if category_meta:
                category = category_meta.get('content', '').strip()
        
        # Strategy 4: Extract from URL
        if not category:
            # URL format: /news/eg/category/banking or /news/category/11/Banking-and-Finance
            url_parts = article_url.split('/')
            for i, part in enumerate(url_parts):
                if part in ['category', 'section'] and i + 1 < len(url_parts):
                    category = url_parts[i + 1].replace('-', ' ').replace('_', ' ').title()
                    break
        
        # Extract main article content - IMPROVED
        content = ""
        
        # Try to find article body with common selectors
        content_container = (
            soup.find('div', class_=lambda x: x and 'article-body' in str(x).lower()) or
            soup.find('div', class_=lambda x: x and 'article-content' in str(x).lower()) or
            soup.find('div', class_=lambda x: x and 'story-body' in str(x).lower()) or
            soup.find('div', class_=lambda x: x and 'news-body' in str(x).lower()) or
            soup.find('div', {'id': lambda x: x and 'article' in str(x).lower()}) or
            soup.find('article')
        )
        
        if content_container:
            # Extract all paragraphs - filter out short/empty ones
            paragraphs = content_container.find_all('p')
            valid_paragraphs = []
            
            for p in paragraphs:
                text = p.get_text(strip=True)
                # Only include paragraphs with substantial content
                if len(text) > 30 and not text.startswith('©') and 'cookie' not in text.lower():
                    valid_paragraphs.append(text)
            
            content = '\n\n'.join(valid_paragraphs)
        
        # If no content found, skip this article
        if not content or len(content) < 100:
            print(f"      ⚠ Skipping - insufficient content")
            return None
        
        # Extract featured image
        image = ""
        img_elem = soup.find('img', class_=lambda x: x and ('featured' in str(x).lower() or 'main' in str(x).lower()))
        if not img_elem:
            # Find first substantial image in article
            imgs = soup.find_all('img')
            for img in imgs:
                src = img.get('src', '')
                # Skip tracking pixels and tiny images
                if 'facebook.com' not in src and 'pixel' not in src and '1x1' not in src:
                    image = src
                    break
        else:
            image = img_elem.get('src', '')
        
        if image and not image.startswith('http'):
            image = 'https://english.mubasher.info' + image
        
        return {
            'title': title,
            'url': article_url,
            'date': date,
            'author': author,
            'category': category,
            'image': image,
            'content': content,
            'word_count': len(content.split()) if content else 0,
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        print(f"      ✗ Error extracting article: {e}")
        return None

def extract_article_info(container):
    """DEPRECATED - Old function kept for compatibility"""
    pass

def save_to_json(data, filename='mubasher_articles.json'):
    """Save to JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n{'='*60}")
    print(f"✓ SAVED {len(data)} ARTICLES")
    print(f"✓ File: {filename}")
    print("="*60)

def main():
    """Main function"""
    print("="*60)
    print("MUBASHER EGYPT ARTICLE SCRAPER")
    print("="*60)
    
    driver = setup_driver()
    all_articles = []
    
    try:
        # Attempt login (with manual fallback)
        login_successful = login_to_mubasher(driver, "", "")
        
        if not login_successful:
            print("\n❌ Cannot proceed without login")
            return
        
        # Extract articles
        print("\n" + "="*60)
        print("STARTING ARTICLE EXTRACTION")
        print("="*60)
        
        sections = [
            ("Egypt News", "https://english.mubasher.info/countries/eg", "Egyptian Markets & Economy"),
            ("Markets", "https://english.mubasher.info/markets/EGX", "Stock Markets"),
            ("Economy", "https://english.mubasher.info/news/economy", "Economic News"),
        ]
        
        for section_name, url, default_category in sections:
            print(f"\n📰 Section: {section_name}")
            
            # Step 1: Get article links from listing page
            article_links = get_article_links(driver, url, max_links=15)
            
            # Step 2: Visit each article and extract full content
            print(f"\nExtracting full content from {len(article_links)} articles...")
            section_articles = []
            
            for i, link_info in enumerate(article_links, 1):
                print(f"  [{i}/{len(article_links)}] {link_info['title'][:60]}...")
                
                article_data = extract_full_article(driver, link_info['url'])
                
                if article_data and article_data['word_count'] > 50:  # Only save articles with real content
                    article_data['section'] = section_name
                    # If no category found, use the section's default category
                    if not article_data.get('category'):
                        article_data['category'] = default_category
                    # Add author as "Mubasher" if empty
                    if not article_data.get('author'):
                        article_data['author'] = "Mubasher"
                    section_articles.append(article_data)
                    print(f"      ✓ Extracted ({article_data['word_count']} words)")
                
                time.sleep(1.5)  # Be polite to the server
            
            all_articles.extend(section_articles)
            print(f"\n✓ Section complete: {len(section_articles)} articles extracted")
            time.sleep(2)
        
        # Results
        print("\n" + "="*60)
        print(f"EXTRACTION COMPLETE - Total: {len(all_articles)}")
        print("="*60)
        
        if all_articles:
            print("\nSample Articles:\n")
            for i, article in enumerate(all_articles[:3], 1):
                print(f"{i}. {article['title']}")
                print(f"   Section: {article['section']}")
                print(f"   Date: {article['date']}")
                print(f"   Word Count: {article['word_count']}")
                print(f"   Content Preview: {article['content'][:150]}...")
                print()
            
            save_to_json(all_articles)
            print("\n✅ SUCCESS! Your articles with full content are ready.")
        else:
            print("\n⚠ No articles extracted")
            print("Check the debug HTML files to see page structure")
    
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPress Enter to close browser...")
        driver.quit()
        print("✓ Browser closed")

if __name__ == "__main__":
    main()