import json
import time
from datetime import datetime
import os

try:
    from openai import OpenAI
except ImportError:
    print("Error: OpenAI library not found!")
    print("Install it with: pip install openai")
    exit(1)

class ArticleSummarizer:
    def __init__(self, input_file='AlBorsaNewsScraped.json', api_key=''):
        """Initialize summarizer with OpenAI"""
        self.input_file = input_file
        self.articles = []
        self.summarized_articles = []
        
        # Initialize OpenAI client
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            print("⚠️  OpenAI API key not found!")
            print("\nOptions:")
            print("1. Set environment variable: export OPENAI_API_KEY='your-key-here'")
            print("2. Pass it when creating the summarizer: ArticleSummarizer(api_key='your-key')")
            print("\nGet your API key from: https://platform.openai.com/api-keys")
            
            self.api_key = input("\n👉 Enter your OpenAI API key (or press ENTER to exit): ").strip()
            if not self.api_key:
                print("Cancelled.")
                exit(1)
        
        self.client = OpenAI(api_key=self.api_key)
        print("✓ OpenAI client initialized\n")
        
    def load_articles(self):
        """Load articles from JSON file"""
        print("📂 Loading articles...")
        
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                self.articles = json.load(f)
            
            print(f"✓ Loaded {len(self.articles)} articles from {self.input_file}\n")
            return True
            
        except FileNotFoundError:
            print(f"✗ Error: File '{self.input_file}' not found!")
            print("  Make sure you've scraped articles first.")
            return False
        except Exception as e:
            print(f"✗ Error loading file: {e}")
            return False
    
    def summarize_with_openai(self, article, model="gpt-4o-mini"):
        """Summarize article using OpenAI API"""
        try:
            title = article.get('title', 'No Title')
            content = article.get('content', '')
            
            if not content or len(content) < 100:
                return {
                    'summary': 'محتوى غير كافٍ للتلخيص',
                    'key_points': [],
                    'error': 'Content too short'
                }
            
            # Truncate very long content to save tokens
            if len(content) > 4000:
                content = content[:4000] + "..."
            
            # Create prompt
            prompt = f"""قم بتلخيص هذا المقال الاقتصادي المصري باللغة العربية بشكل احترافي.

العنوان: {title}

المحتوى:
{content}

المطلوب:
1. ملخص شامل في 2-3 جمل يغطي أهم المعلومات
2. من 3 إلى 5 نقاط رئيسية محددة وواضحة

الرد يجب أن يكون بصيغة JSON فقط بدون أي نص إضافي:
{{
  "summary": "الملخص هنا",
  "key_points": ["نقطة 1", "نقطة 2", "نقطة 3"]
}}"""
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "أنت مساعد متخصص في تلخيص الأخبار الاقتصادية المصرية باللغة العربية. تقدم ملخصات دقيقة ومهنية."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"  ⚠️  JSON parsing error: {e}")
            return {
                'summary': 'خطأ في معالجة الرد',
                'key_points': [],
                'error': 'JSON parse error'
            }
        except Exception as e:
            print(f"  ✗ API Error: {e}")
            return {
                'summary': 'خطأ في الاتصال بالخدمة',
                'key_points': [],
                'error': str(e)
            }
    
    def summarize_all(self, delay=2, model="gpt-4o-mini"):
        """Summarize all articles using OpenAI"""
        print("="*80)
        print("📝 SUMMARIZING ARTICLES WITH OPENAI")
        print("="*80)
        print(f"Articles to summarize: {len(self.articles)}")
        print(f"Model: {model}")
        print(f"Delay between requests: {delay} seconds\n")
        
        total_cost = 0
        success_count = 0
        
        for idx, article in enumerate(self.articles, 1):
            title = article.get('title', 'No Title')
            print(f"[{idx}/{len(self.articles)}] {title[:60]}...")
            
            # Get summary from OpenAI
            summary_result = self.summarize_with_openai(article, model=model)
            
            # Create enhanced article
            enhanced_article = article.copy()
            enhanced_article['summary'] = summary_result.get('summary', '')
            enhanced_article['key_points'] = summary_result.get('key_points', [])
            enhanced_article['summarized_at'] = datetime.now().isoformat()
            enhanced_article['summarization_model'] = model
            
            self.summarized_articles.append(enhanced_article)
            
            # Show summary
            if summary_result.get('summary') and not summary_result.get('error'):
                print(f"  ✓ {summary_result['summary'][:80]}...")
                success_count += 1
            else:
                print(f"  ⚠️  Error: {summary_result.get('error', 'Unknown error')}")
            
            time.sleep(delay)
        
        print(f"\n{'='*80}")
        print(f"✅ SUMMARIZATION COMPLETE!")
        print(f"   Successfully summarized: {success_count}/{len(self.articles)} articles")
        print("="*80)
    
    def save_summaries(self, output_file='AlBorsaArticlesSummarized.json'):
        """Save summarized articles to JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.summarized_articles, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Saved to {output_file}")
        
    def create_summary_report(self, output_file='Summary_Report.txt'):
        """Create a readable summary report"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("تقرير ملخصات الأخبار الاقتصادية - Al Borsa News\n")
            f.write("="*80 + "\n\n")
            f.write(f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"عدد الأخبار: {len(self.summarized_articles)}\n")
            f.write(f"نموذج الذكاء الاصطناعي: OpenAI {self.summarized_articles[0].get('summarization_model', 'N/A') if self.summarized_articles else 'N/A'}\n")
            f.write("="*80 + "\n\n")
            
            for idx, article in enumerate(self.summarized_articles, 1):
                f.write(f"{idx}. {article.get('title', 'بدون عنوان')}\n")
                f.write("-"*80 + "\n")
                f.write(f"التاريخ: {article.get('date', 'N/A')}\n")
                f.write(f"الكاتب: {article.get('author', 'N/A')}\n")
                f.write(f"الفئة: {article.get('category', 'N/A')}\n")
                f.write(f"الرابط: {article.get('url', 'N/A')}\n\n")
                
                f.write("📝 الملخص:\n")
                f.write(f"{article.get('summary', 'لا يوجد ملخص')}\n\n")
                
                if article.get('key_points'):
                    f.write("🔑 النقاط الرئيسية:\n")
                    for point in article['key_points']:
                        f.write(f"  • {point}\n")
                    f.write("\n")
                
                f.write("="*80 + "\n\n")
        
        print(f"📄 Created text report: {output_file}")
    
    def create_html_report(self, output_file='Summary_Report.html'):
        """Create an HTML report"""
        html = """<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تقرير ملخصات الأخبار الاقتصادية</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: white;
            color: #333;
            padding: 40px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header h1 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2em;
        }
        .header .subtitle {
            color: #666;
            font-size: 1.1em;
        }
        .header .date {
            color: #999;
            margin-top: 10px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-card .icon {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .stat-card h3 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        .stat-card .number {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }
        .article {
            background: white;
            padding: 30px;
            margin-bottom: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .article:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }
        .article-number {
            display: inline-block;
            background: #667eea;
            color: white;
            width: 35px;
            height: 35px;
            border-radius: 50%;
            text-align: center;
            line-height: 35px;
            font-weight: bold;
            margin-left: 10px;
        }
        .article h2 {
            display: inline;
            color: #333;
            font-size: 1.4em;
        }
        .article-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            font-size: 0.9em;
        }
        .article-meta span {
            color: #666;
        }
        .summary {
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            padding: 20px;
            border-right: 4px solid #667eea;
            border-radius: 10px;
            margin: 20px 0;
            line-height: 1.9;
            font-size: 1.05em;
        }
        .summary-label {
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
            display: block;
        }
        .key-points {
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        .key-points h4 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.1em;
        }
        .key-points ul {
            margin: 0;
            padding-right: 25px;
        }
        .key-points li {
            margin-bottom: 12px;
            line-height: 1.7;
            color: #444;
        }
        .link {
            display: inline-block;
            margin-top: 15px;
            padding: 12px 25px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: background 0.3s;
        }
        .link:hover {
            background: #764ba2;
        }
        .footer {
            text-align: center;
            color: white;
            padding: 20px;
            margin-top: 30px;
        }
    </style>
</head>
<body>
    <div class="container">
"""
        
        # Header
        model_name = self.summarized_articles[0].get('summarization_model', 'OpenAI') if self.summarized_articles else 'OpenAI'
        html += f"""
        <div class="header">
            <h1>📊 تقرير ملخصات الأخبار الاقتصادية</h1>
            <div class="subtitle">جريدة البورصة - Al Borsa News</div>
            <div class="subtitle">مدعوم بـ OpenAI {model_name}</div>
            <div class="date">📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </div>
"""
        
        # Stats
        total_articles = len(self.summarized_articles)
        total_words = sum(len(a.get('content', '').split()) for a in self.summarized_articles)
        avg_words = total_words // total_articles if total_articles > 0 else 0
        
        html += f"""
        <div class="stats">
            <div class="stat-card">
                <div class="icon">📰</div>
                <h3>عدد الأخبار</h3>
                <div class="number">{total_articles}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📝</div>
                <h3>إجمالي الكلمات</h3>
                <div class="number">{total_words:,}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📊</div>
                <h3>متوسط الكلمات</h3>
                <div class="number">{avg_words}</div>
            </div>
        </div>
"""
        
        # Articles
        for idx, article in enumerate(self.summarized_articles, 1):
            html += f"""
        <div class="article">
            <span class="article-number">{idx}</span>
            <h2>{article.get('title', 'بدون عنوان')}</h2>
            
            <div class="article-meta">
                <span>📅 {article.get('date', 'N/A')}</span>
                <span>✍️ {article.get('author', 'N/A')}</span>
                <span>📁 {article.get('category', 'N/A')}</span>
            </div>
            
            <div class="summary">
                <span class="summary-label">📝 الملخص</span>
                {article.get('summary', 'لا يوجد ملخص')}
            </div>
"""
            
            if article.get('key_points'):
                html += """
            <div class="key-points">
                <h4>🔑 النقاط الرئيسية</h4>
                <ul>
"""
                for point in article['key_points']:
                    html += f"                    <li>{point}</li>\n"
                
                html += """
                </ul>
            </div>
"""
            
            html += f"""
            <a href="{article.get('url', '#')}" class="link" target="_blank">🔗 قراءة المقال الكامل</a>
        </div>
"""
        
        html += """
        <div class="footer">
            <p>تم إنشاء هذا التقرير باستخدام OpenAI</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"🌐 Created HTML report: {output_file}")


# Example usage
if __name__ == "__main__":
    print("\n" + "="*80)
    print("ARTICLE SUMMARIZER WITH OPENAI")
    print("="*80)
    print("This tool uses OpenAI to create high-quality Arabic summaries")
    print("="*80 + "\n")
    
    # Initialize (will prompt for API key if not found)
    summarizer = ArticleSummarizer('AlBorsaNewsScraped.json')
    
    # Load articles
    if not summarizer.load_articles():
        exit(1)
    
    # Show sample
    if summarizer.articles:
        print("📄 Sample article:")
        sample = summarizer.articles[0]
        print(f"   Title: {sample.get('title', 'N/A')}")
        print(f"   Content length: {len(sample.get('content', ''))} characters")
        print(f"   Words: ~{len(sample.get('content', '').split())} words\n")
    
    # Select model
    print("Available OpenAI models:")
    print("  1. gpt-4o-mini (Recommended - Fast & Affordable)")
    print("  2. gpt-4o (Best Quality)")
    print("  3. gpt-3.5-turbo (Most Affordable)\n")
    
    model_choice = input("Select model (1/2/3) [default: 1]: ").strip() or "1"
    
    model_map = {
        "1": "gpt-4o-mini",
        "2": "gpt-4o",
        "3": "gpt-3.5-turbo"
    }
    
    selected_model = model_map.get(model_choice, "gpt-4o-mini")
    print(f"✓ Selected model: {selected_model}\n")
    
    # Confirm
    print(f"⚠️  Note: This will make {len(summarizer.articles)} API calls to OpenAI")
    print(f"   Estimated cost: ~$0.01-0.05 USD (depending on model and content length)")
    
    response = input("\nStart summarizing? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        exit(0)
    
    # Summarize
    try:
        summarizer.summarize_all(delay=1, model=selected_model)
        
        # Save results
        summarizer.save_summaries('AlBorsaArticlesSummarized.json')
        summarizer.create_summary_report('Summary_Report.txt')
        summarizer.create_html_report('Summary_Report.html')
        
        print("\n" + "="*80)
        print("✅ ALL DONE!")
        print("="*80)
        print("\nCreated files:")
        print("  📄 AlBorsaArticlesSummarized.json - Full data with AI summaries")
        print("  📄 Summary_Report.txt - Readable text report")
        print("  🌐 Summary_Report.html - Beautiful HTML report (open in browser)")
        print("\n💡 Tip: Open Summary_Report.html in your browser for the best experience!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
