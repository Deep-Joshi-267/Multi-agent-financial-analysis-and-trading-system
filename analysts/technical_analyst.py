"""Technical Analyst Agent.

Analyzes price patterns, technical indicators, and chart formations.
Inspired by FinAgent (Zhang et al., 2024b) multimodal technical analysis.
"""

from typing import Optional, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

from .state import AnalystState, AnalystReport


TECHNICAL_PROMPT = """You are an AI Technical Stock Analysis Engine designed for analyzing stocks listed in the Indian stock market using technical indicators and price action parameters.

Your task is to analyze the provided technical indicator parameters for {ticker} and classify the stock into exactly ONE of these categories:
* BUY
* HOLD
* SELL

IMPORTANT:
Do not make the classification based on a single metric. Evaluate all available technical parameters together.

==================================================
INPUT DATA FOR {ticker}
=======================
Current Price: {current_price}
Calculated Indicators & Signals:
{indicators}

Recent Price History: {price_history}
Recent Volume History: {volume_history}

==================================================
ANALYSIS FRAMEWORK
==================

Calculate a Technical Score out of 100 using the following weights:

1. TREND & PRICE ACTION — 30 POINTS
   - Evaluate Price trend direction, 5d/20d momentum, 52-week high/low proximity.
   - Score = 0–30.

2. MOMENTUM INDICATORS — 25 POINTS
   - Evaluate RSI (14), MACD vs MACD Signal Line crossover.
   - Overbought RSI (>70) or oversold RSI (<30), bullish/bearish MACD divergence.
   - Score = 0–25.

3. MOVING AVERAGES — 20 POINTS
   - Evaluate SMA 20, SMA 50, SMA 200 alignment and price relative to moving averages (Golden cross vs Death cross).
   - Score = 0–20.

4. VOLUME & LIQUIDITY — 15 POINTS
   - Evaluate recent volume vs 5-day average volume, volume confirmation on price moves.
   - Score = 0–15.

5. VOLATILITY & BANDS — 10 POINTS
   - Evaluate Bollinger Bands (Upper/Lower band squeeze or breakout) and volatility levels.
   - Score = 0–10.

TOTAL = 100 POINTS

==================================================
CLASSIFICATION RULE
===================
75–100: BUY
55–74: HOLD
0–54: SELL

==================================================
OUTPUT FORMAT
=============
Return the result ONLY as valid JSON.

Use exactly this structure:
{{
"classification": "BUY | HOLD | SELL",
"technical_score": 0,
"confidence": 0,

"scores": {{
"trend": 0,
"momentum": 0,
"moving_averages": 0,
"volume": 0,
"volatility": 0
}},

"analysis": {{
"trend": "",
"momentum": "",
"moving_averages": "",
"volume": "",
"volatility": ""
}},

"positive_factors": [
"",
"",
""
],

"risk_factors": [
"",
"",
""
],

"key_reason": "",

"data_quality": "HIGH | MEDIUM | LOW"
}}
"""


class TechnicalAnalyst:
    """Technical analyst using price action and indicators."""

    def __init__(self, llm: Optional[ChatGroq] = None):
        self.llm = llm or ChatGroq(model="qwen/qwen3.8-27b", temperature=0.1)
        self.prompt = ChatPromptTemplate.from_template(TECHNICAL_PROMPT)
        self.parser = JsonOutputParser()

    def analyze(self, state: AnalystState) -> dict:
        """Analyze technicals and return updated state."""
        market_data = state.get("market_data", {})
        price_history = market_data.get("price_history", [])
        volume_history = market_data.get("volume_history", [])
        current_price = market_data.get("current_price", 0)

        # Calculate basic indicators
        indicators = self._calculate_indicators(price_history, volume_history)

        chain = self.prompt | self.llm | self.parser

        try:
            result = chain.invoke({
                "ticker": state["ticker"],
                "current_price": current_price,
                "price_history": self._format_list(price_history[-20:]),
                "volume_history": self._format_list(volume_history[-20:]),
                "indicators": indicators,
            })

            signal = result.get("classification") or result.get("signal") or "HOLD"
            score = result.get("technical_score", 50)
            reasoning = result.get("key_reason") or str(result.get("analysis", {}))
            positives = result.get("positive_factors", [])
            risks = result.get("risk_factors", [])

            return {
                "technical_analysis": {
                    "analyst_type": "technical",
                    "signal": signal.upper(),
                    "confidence": float(result.get("confidence", 0.75)),
                    "reasoning": f"Technical Score: {score}/100. {reasoning}",
                    "key_factors": positives + risks,
                    "raw_report": result,
                }
            }
        except Exception as e:
            return {
                "technical_analysis": {
                    "analyst_type": "technical",
                    "signal": "HOLD",
                    "confidence": 0.0,
                    "reasoning": f"Analysis failed: {str(e)}",
                    "key_factors": [],
                }
            }

    def _calculate_indicators(self, prices: List[float], volumes: List[int]) -> str:
        """Calculate basic technical indicators."""
        if len(prices) < 5:
            return "Insufficient data for indicator calculation"

        indicators = []

        # Simple Moving Averages
        if len(prices) >= 10:
            sma_10 = sum(prices[-10:]) / 10
            indicators.append(f"SMA(10): ${sma_10:.2f}")

        if len(prices) >= 20:
            sma_20 = sum(prices[-20:]) / 20
            indicators.append(f"SMA(20): ${sma_20:.2f}")

        # Price momentum
        if len(prices) >= 5:
            momentum_5d = ((prices[-1] - prices[-5]) / prices[-5]) * 100
            indicators.append(f"5-day Momentum: {momentum_5d:.2f}%")

        # Volatility (simple std dev proxy)
        if len(prices) >= 10:
            mean_price = sum(prices[-10:]) / 10
            variance = sum((p - mean_price) ** 2 for p in prices[-10:]) / 10
            volatility = variance ** 0.5
            indicators.append(f"10-day Volatility: ${volatility:.2f}")

        # Volume trend
        if len(volumes) >= 5:
            avg_volume = sum(volumes[-5:]) / 5
            indicators.append(f"Avg Volume (5d): {int(avg_volume):,}")

        # RSI approximation (simplified)
        if len(prices) >= 14:
            gains = []
            losses = []
            for i in range(-14, -1):
                change = prices[i + 1] - prices[i]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))

            avg_gain = sum(gains) / 14
            avg_loss = sum(losses) / 14

            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            indicators.append(f"RSI(14): {rsi:.1f}")

        return "\n".join(indicators) if indicators else "No indicators calculated"

    def _format_list(self, data: list) -> str:
        """Format a list for display."""
        if not data:
            return "N/A"
        if len(data) <= 5:
            return str(data)
        return f"[...{len(data)} values, latest: {data[-5:]}]"

    def __call__(self, state: AnalystState) -> dict:
        """Make the analyst callable for LangGraph nodes."""
        return self.analyze(state)
