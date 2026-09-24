"""Sentiment Analyst Agent.

Performs market sentiment analysis using social signals, analyst ratings,
and overall market mood. Inspired by debate-driven agent architectures.
"""

from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

from .state import AnalystState, AnalystReport


SENTIMENT_PROMPT = """You are a market sentiment specialist analyzing investor psychology and market mood.

TASK: Assess overall market sentiment for {ticker}.

NEWS HEADLINES:
{news_headlines}

PRICE ACTION:
- Current Price: ${current_price}
- Recent Price Change: {price_change}%

Analyze sentiment across multiple dimensions:
1. News tone and media coverage sentiment
2. Implied investor fear/greed based on price action
3. Sector rotation signals
4. Contrarian indicators (extreme sentiment often reverses)

Consider both retail and institutional sentiment signals.

Respond in JSON format:
{{
    "signal": "BUY" | "SELL" | "HOLD",
    "confidence": <float 0.0-1.0>,
    "reasoning": "<sentiment analysis with psychological factors>",
    "key_factors": ["<factor1>", "<factor2>", ...]
}}
"""


class SentimentAnalyst:
    """Sentiment analyst evaluating market psychology and investor mood."""

    def __init__(self, llm: Optional[ChatGroq] = None):
        self.llm = llm or ChatGroq(model="qwen/qwen3.8-27b", temperature=0.2)
        self.prompt = ChatPromptTemplate.from_template(SENTIMENT_PROMPT)
        self.parser = JsonOutputParser()

    def analyze(self, state: AnalystState) -> dict:
        """Analyze sentiment and return updated state."""
        market_data = state.get("market_data", {})
        news_articles = market_data.get("news_articles", [])
        price_history = market_data.get("price_history", [])
        current_price = market_data.get("current_price", 0)

        # Calculate price change
        price_change = 0.0
        if len(price_history) >= 2:
            price_change = ((price_history[-1] - price_history[0]) / price_history[0]) * 100

        # Extract headlines (first line of each article)
        headlines = [article.split("\n")[0][:200] for article in news_articles[:10]]
        headlines_text = "\n".join([f"- {h}" for h in headlines]) if headlines else "No headlines available"

        chain = self.prompt | self.llm | self.parser

        try:
            result = chain.invoke({
                "ticker": state["ticker"],
                "news_headlines": headlines_text,
                "current_price": current_price,
                "price_change": f"{price_change:.2f}",
            })

            return {
                "sentiment_analysis": {
                    "analyst_type": "sentiment",
                    "signal": result.get("signal", "HOLD"),
                    "confidence": float(result.get("confidence", 0.5)),
                    "reasoning": result.get("reasoning", ""),
                    "key_factors": result.get("key_factors", []),
                }
            }
        except Exception as e:
            return {
                "sentiment_analysis": {
                    "analyst_type": "sentiment",
                    "signal": "HOLD",
                    "confidence": 0.0,
                    "reasoning": f"Analysis failed: {str(e)}",
                    "key_factors": [],
                }
            }

    def __call__(self, state: AnalystState) -> dict:
        """Make the analyst callable for LangGraph nodes."""
        return self.analyze(state)
