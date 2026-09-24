"""Unified market data fetcher for Indian Stock Market (NSE/BSE)."""

from typing import Dict, List, Any

from .google_news_scraper import GoogleNewsScraper
from .stock_data import StockDataFetcher


def _normalize_ticker(ticker: str) -> str:
    """Auto-append .NS for Indian stocks if no suffix given."""
    ticker = ticker.strip().upper()
    if "." not in ticker:
        return ticker + ".NS"
    return ticker


class MarketDataFetcher:
    """Fetches news (Google News RSS) + price data (yfinance) for Indian stocks."""

    def __init__(self, verbose: bool = False):
        self.news_scraper  = GoogleNewsScraper()
        self.stock_fetcher = StockDataFetcher(verbose=verbose)
        self.verbose       = verbose

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"[MarketData] {msg}")

    def fetch_market_data(
        self,
        ticker: str,
        news_keyword: str = "",
        news_days: int = 7,
        news_limit: int = 15,
        price_days: int = 90,
    ) -> Dict[str, Any]:
        ticker = _normalize_ticker(ticker)
        self._log(f"Fetching market data for {ticker}")

        # Get company name for better news search
        try:
            info = self.stock_fetcher.get_company_info(ticker)
            company_name = info.get("name", "")
        except Exception:
            company_name = ticker.replace(".NS", "").replace(".BO", "")

        # Fetch news from Google News RSS
        self._log("Fetching news from Google News...")
        try:
            news_articles = self.news_scraper.get_news_articles(
                ticker=ticker,
                company_name=company_name,
                limit=news_limit,
            )
        except Exception as e:
            self._log(f"News fetch failed: {e}")
            news_articles = []

        # Fetch price/technical data
        self._log("Fetching price data from Yahoo Finance...")
        try:
            indicators        = self.stock_fetcher.get_technical_indicators(ticker)
            price_history     = self.stock_fetcher.get_price_history(ticker, days=price_days)
            volume_history    = self.stock_fetcher.get_volume_history(ticker, days=price_days)
            financial_reports = self.stock_fetcher.get_financial_reports(ticker)
        except Exception as e:
            self._log(f"Price fetch failed: {e}")
            indicators = {}; price_history = []; volume_history = []; financial_reports = {}

        self._log(f"Fetched: {len(news_articles)} news | {len(price_history)} price points")

        return {
            "current_price":        indicators.get("current_price", 0),
            "price_history":        price_history,
            "volume_history":       volume_history,
            "news_articles":        news_articles,
            "financial_reports":    financial_reports,
            "technical_indicators": indicators,
        }

    def get_quick_summary(self, ticker: str) -> dict:
        ticker     = _normalize_ticker(ticker)
        indicators = self.stock_fetcher.get_technical_indicators(ticker, days=30)
        info       = self.stock_fetcher.get_company_info(ticker)
        return {
            "ticker":        ticker,
            "name":          info.get("name", ticker),
            "sector":        info.get("sector"),
            "current_price": indicators.get("current_price"),
            "rsi":           indicators.get("rsi_14"),
            "momentum_5d":   indicators.get("momentum_5d"),
            "sma_20":        indicators.get("sma_20"),
        }


def fetch_market_data(ticker: str, **kwargs) -> Dict[str, Any]:
    return MarketDataFetcher().fetch_market_data(ticker, **kwargs)
