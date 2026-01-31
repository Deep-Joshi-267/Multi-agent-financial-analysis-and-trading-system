import argparse
import json
import random
import time
from datetime import datetime, timedelta

import pandas as pd
import requests
from bs4 import BeautifulSoup

class FinanceNewsScraper:
    def __init__(self, verbose: bool = False):
        self.headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/91.0.4472.124 Safari/537.36')
        }
        # Removed trailing slash to avoid double slashes in URLs
        self.base_url = "https://www.moneycontrol.com/news/business/stocks"
        self.source = "Money Control"
        self.verbose = verbose

    def get_soup(self, url):
        """Make HTTP request and return BeautifulSoup object."""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            if self.verbose:
                print(f"Fetching page: {url}")
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching URL {url}: {e}")
            return None

    def parse_date(self, date_str):
        """Parse a date string into a datetime object."""
        try:
            if not date_str:
                return None

            date_str = date_str.lower().strip()
            today = datetime.now()

            if 'mins ago' in date_str or 'min ago' in date_str:
                mins = int(''.join(filter(str.isdigit, date_str)))
                return today - timedelta(minutes=mins)
            elif 'hours ago' in date_str or 'hour ago' in date_str:
                hours = int(''.join(filter(str.isdigit, date_str)))
                return today - timedelta(hours=hours)
            elif 'days ago' in date_str or 'day ago' in date_str:
                days = int(''.join(filter(str.isdigit, date_str)))
                return today - timedelta(days=days)
            else:
                # Try several common formats
                for fmt in ['%B %d, %Y %I:%M %p', '%b %d, %Y %I:%M %p', '%d %B %Y']:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
                return None
        except Exception as e:
            print(f"Error parsing date {date_str}: {e}")
            return None

    def extract_article_data(self, article):
        """Extract title, url, date, source, and a description (if available) from an article element."""
        try:
            # Try different possible selectors for the title element
            title_tag = (article.find('h2') or 
                         article.find('h1') or 
                         article.find('a', class_='headline'))
            if not title_tag:
                return None

            title = title_tag.get_text().strip()
            # If the title tag is not a link, try to find an <a> tag inside it
            link_tag = title_tag.find('a') if title_tag.name != 'a' else title_tag
            link = link_tag.get('href') if link_tag else None

            # Try different selectors for the date element
            timestamp = (article.find('span', class_='article_schedule') or
                         article.find('span', class_='date') or
                         article.find('time'))
            date_str = timestamp.text.strip() if timestamp else None
            date = self.parse_date(date_str) if date_str else None

            # Optionally, try to extract a description. For Money Control you might not have a clear description,
            # so we leave it as an empty string.
            description = ""
            
            if self.verbose:
                print(f"Found article: {title[:50]}... | Date: {date_str}")
            
            return {
                'title': title,
                'url': link,
                'date': date,
                'source': self.source,
                'description': description
            }
        except Exception as e:
            print(f"Error extracting article data: {e}")
            return None

    def search_by_keyword(self, keyword, num_days, num_pages=5):
        """Scrape articles across multiple pages that match a given keyword and date range."""
        all_articles = []
        cutoff_date = datetime.now() - timedelta(days=num_days)

        for page in range(1, num_pages + 1):
            url = f"{self.base_url}/page-{page}"
            soup = self.get_soup(url)
            if not soup:
                continue

            # Try different article container selectors
            articles = (soup.find_all('li', class_='clearfix') or
                        soup.find_all('div', class_='article-list') or
                        soup.find_all('div', class_='article_box') or
                        soup.find_all('div', class_='news_listing'))
            if self.verbose:
                print(f"Found {len(articles)} articles on page {page}")

            for article in articles:
                data = self.extract_article_data(article)
                if not data:
                    continue

                matches_keyword = True
                if keyword:
                    matches_keyword = keyword.lower() in data["title"].lower()

                if matches_keyword:
                    # Include articles with no date or within the desired date range
                    if not data['date'] or data['date'] >= cutoff_date:
                        all_articles.append(data)

            # Be polite with the website by waiting a bit between requests
            time.sleep(random.uniform(2, 4))

        df = pd.DataFrame(all_articles)
        if not df.empty:
            df = df.sort_values('date', ascending=False, na_position='last')
        return df

    def to_json_records(self, df: pd.DataFrame, limit: int | None = None) -> list[dict]:
        records = df.to_dict(orient="records") if df is not None else []
        if limit is not None:
            records = records[:limit]
        for r in records:
            d = r.get("date")
            r["date"] = d.isoformat() if hasattr(d, "isoformat") and d is not None else None
        return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyword", default="")
    parser.add_argument("--days", type=int, default=2)
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    scraper = FinanceNewsScraper(verbose=args.verbose)
    df = scraper.search_by_keyword(keyword=args.keyword, num_days=args.days, num_pages=args.pages)
    records = scraper.to_json_records(df, limit=args.limit)
    news_articles = []
    for r in records:
        parts = [r.get("title") or ""]
        if r.get("source"):
            parts.append(f"Source: {r['source']}")
        if r.get("date"):
            parts.append(f"Date: {r['date']}")
        if r.get("url"):
            parts.append(f"URL: {r['url']}")
        if r.get("description"):
            parts.append(f"Summary: {r['description']}")
        news_articles.append("\n".join(parts).strip())

    payload = {
        "keyword": args.keyword,
        "source": scraper.source,
        "news_articles": news_articles,
        "articles": records,
    }
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
