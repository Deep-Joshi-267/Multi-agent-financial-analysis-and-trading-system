"""News Analyst Agent — Indian Stock Market (NSE/BSE).

Analyzes Google News headlines to determine short-term price impact.
Gives DECISIVE BUY/SELL/HOLD signals.
"""

import time
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

from .state import AnalystState


NEWS_ANALYST_PROMPT = """You are a senior financial news analyst for the Indian stock market (NSE/BSE).

TASK: Analyze the following recent news for {ticker} and give a DECISIVE trading signal.

NEWS ARTICLES:
{news_articles}

CURRENT PRICE: Rs. {current_price}

Analysis criteria:
1. Corporate earnings, revenue, profit/loss announcements
2. Management guidance, promoter activity, bulk/block deals
3. Regulatory actions (SEBI, RBI, government policy impacts)
4. Sector tailwinds or headwinds (Budget, GST, interest rates)
5. Global cues affecting Indian markets (FII/DII flows, crude oil, USD/INR)

IMPORTANT RULES:
- You MUST give a clear BUY or SELL unless truly neutral/no news
- Positive earnings/guidance/deal wins/expansion -> BUY
- Profit warnings/regulatory trouble/high debt/fraud -> SELL
- Mixed signals or no material news -> HOLD
- Be specific in reasoning, reference the news headlines

Respond ONLY in valid JSON (no extra text, no markdown):
{{
    "signal": "BUY" | "SELL" | "HOLD",
    "confidence": <float 0.0-1.0>,
    "reasoning": "<2-3 sentences citing specific news>",
    "key_factors": ["<factor1>", "<factor2>", "<factor3>"]
}}
"""

NO_NEWS_PROMPT = """You are a senior financial analyst for Indian markets (NSE/BSE).

No recent news articles are available for {ticker} (Price: Rs. {current_price}).

Based on the absence of news and general market context, provide a neutral assessment.

Respond ONLY in valid JSON:
{{
    "signal": "HOLD",
    "confidence": 0.4,
    "reasoning": "No recent news available for {ticker}. Maintaining neutral stance pending news catalysts.",
    "key_factors": ["No recent news", "Insufficient information", "Await catalyst"]
}}
"""


class NewsAnalyst:
    """News-driven analyst agent for Indian stock market."""

    def __init__(self, llm: Optional[ChatGroq] = None):
        self.llm    = llm or ChatGroq(model="qwen/qwen3.8-27b", temperature=0.1)
        self.parser = JsonOutputParser()

    def _invoke_with_retry(self, chain, inputs: dict, retries: int = 3) -> dict:
        """Invoke LLM chain with exponential backoff retry."""
        for attempt in range(retries):
            try:
                return chain.invoke(inputs)
            except Exception as e:
                if attempt == retries - 1:
                    raise
                wait = 2 ** attempt
                time.sleep(wait)

    def analyze(self, state: AnalystState) -> dict:
        """Analyze news and return updated state with news signal."""
        market_data   = state.get("market_data", {})
        news_articles = market_data.get("news_articles", [])
        ticker        = state.get("ticker", "")
        price         = market_data.get("current_price", "N/A")

        try:
            if not news_articles:
                # No news — use simplified prompt
                prompt = ChatPromptTemplate.from_template(NO_NEWS_PROMPT)
                chain  = prompt | self.llm | self.parser
                result = self._invoke_with_retry(chain, {
                    "ticker": ticker,
                    "current_price": price,
                })
            else:
                news_text = "\n\n".join(
                    f"[{i+1}] {article}" for i, article in enumerate(news_articles)
                )
                prompt = ChatPromptTemplate.from_template(NEWS_ANALYST_PROMPT)
                chain  = prompt | self.llm | self.parser
                result = self._invoke_with_retry(chain, {
                    "ticker":        ticker,
                    "news_articles": news_text,
                    "current_price": price,
                })

            return {
                "news_analysis": {
                    "analyst_type": "news",
                    "signal":       result.get("signal", "HOLD"),
                    "confidence":   float(result.get("confidence", 0.5)),
                    "reasoning":    result.get("reasoning", ""),
                    "key_factors":  result.get("key_factors", []),
                    "news_count":   len(news_articles),
                }
            }

        except Exception as e:
            return {
                "news_analysis": {
                    "analyst_type": "news",
                    "signal":       "HOLD",
                    "confidence":   0.0,
                    "reasoning":    f"News analysis failed: {str(e)}",
                    "key_factors":  [],
                    "news_count":   len(news_articles),
                }
            }

    def __call__(self, state: AnalystState) -> dict:
        return self.analyze(state)
