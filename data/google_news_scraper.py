"""
Google News RSS Scraper for Indian Stock Market.

Uses Google News RSS feed — no API key required.
Fetches real news for any NSE/BSE listed company.
"""

import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List
import re


class GoogleNewsScraper:
    """Scrapes financial news from Google News RSS for Indian stocks."""

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    def get_news_articles(
        self,
        ticker: str,
        company_name: str = "",
        limit: int = 15,
    ) -> List[str]:
        """
        Fetch news headlines from Google News RSS.

        Args:
            ticker:       Stock ticker e.g. RELIANCE.NS
            company_name: Full company name e.g. Reliance Industries
            limit:        Max articles to return

        Returns:
            List of formatted news strings ready for LLM consumption.
        """
        clean_ticker = ticker.replace(".NS", "").replace(".BO", "")
        queries = []

        if company_name:
            queries.append(f"{company_name} stock NSE")
        queries.append(f"{clean_ticker} NSE share price")
        queries.append(f"{clean_ticker} stock India")

        articles = []
        seen_titles = set()

        for query in queries:
            if len(articles) >= limit:
                break
            try:
                encoded = urllib.parse.quote(query)
                url = (
                    f"https://news.google.com/rss/search"
                    f"?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
                )
                req = urllib.request.Request(url, headers=self.HEADERS)
                with urllib.request.urlopen(req, timeout=10) as r:
                    xml_data = r.read()

                root = ET.fromstring(xml_data)
                channel = root.find("channel")
                if channel is None:
                    continue

                for item in channel.findall("item"):
                    if len(articles) >= limit:
                        break

                    title = (item.findtext("title") or "").strip()
                    title = re.sub(r" - [^-]+$", "", title).strip()  # remove " - Source Name"
                    if not title or title in seen_titles:
                        continue
                    seen_titles.add(title)

                    pub_date = item.findtext("pubDate") or ""
                    source   = item.findtext("source") or "Google News"
                    link     = item.findtext("link") or ""

                    parts = [f"Headline: {title}"]
                    if source:
                        parts.append(f"Source: {source}")
                    if pub_date:
                        parts.append(f"Date: {pub_date[:25]}")

                    articles.append("\n".join(parts))

                time.sleep(0.3)  # polite delay between queries

            except Exception:
                continue

        return articles[:limit]
