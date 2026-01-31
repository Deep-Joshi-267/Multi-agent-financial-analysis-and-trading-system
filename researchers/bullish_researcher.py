"""Bullish Researcher Agent.

Advocates for investment opportunities by highlighting positive indicators,
growth potential, and favorable market conditions.
"""

from typing import Optional, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

from .state import ResearcherState


BULLISH_PROMPT = """You are a senior bullish investment researcher. Your role is to advocate for 
investment opportunities by identifying growth potential and favorable conditions.

TICKER: {ticker}

ANALYST TEAM REPORT:
{analyst_report}

MARKET DATA SUMMARY:
- Current Price: ${current_price}
- Recent Price Trend: {price_trend}
- Technical Indicators: {technical_summary}

{debate_context}

YOUR TASK:
Construct a compelling BULLISH case for investing in {ticker}. Focus on:
1. Growth catalysts and market opportunities
2. Competitive advantages and moat
3. Favorable financial metrics and trends
4. Positive market sentiment indicators
5. Potential upside scenarios

{counter_instruction}

Respond in JSON format:
{{
    "investment_thesis": "<compelling bullish thesis in 2-3 sentences>",
    "key_arguments": [
        {{
            "point": "<argument title>",
            "evidence": "<supporting data/facts>",
            "impact": "<potential positive impact>"
        }}
    ],
    "growth_catalysts": ["<catalyst1>", "<catalyst2>", ...],
    "upside_potential": "<percentage or price target>",
    "confidence": <float 0.0-1.0>,
    "risk_mitigants": ["<how key risks are manageable>"],
    "recommended_action": "STRONG_BUY" | "BUY" | "HOLD"
}}
"""


class BullishResearcher:
    """Bullish researcher that advocates for investment opportunities."""

    def __init__(self, llm: Optional[ChatGroq] = None):
        self.llm = llm or ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)
        self.prompt = ChatPromptTemplate.from_template(BULLISH_PROMPT)
        self.parser = JsonOutputParser()

    def _get_price_trend(self, price_history: List[float]) -> str:
        """Calculate price trend description."""
        if not price_history or len(price_history) < 2:
            return "Insufficient data"
        
        recent = price_history[-5:] if len(price_history) >= 5 else price_history
        start, end = recent[0], recent[-1]
        change = ((end - start) / start) * 100
        
        if change > 5:
            return f"Strong uptrend (+{change:.1f}%)"
        elif change > 0:
            return f"Mild uptrend (+{change:.1f}%)"
        elif change > -5:
            return f"Mild downtrend ({change:.1f}%)"
        else:
            return f"Strong downtrend ({change:.1f}%)"

    def _get_technical_summary(self, analyst_report: dict) -> str:
        """Extract technical summary from analyst report."""
        individual = analyst_report.get("individual_reports", {})
        technical = individual.get("technical", {})
        
        if not technical:
            return "Technical data unavailable"
        
        return f"Signal: {technical.get('signal', 'N/A')}, Confidence: {technical.get('confidence', 0):.0%}"

    def analyze(self, state: ResearcherState) -> dict:
        """Generate bullish analysis for the ticker."""
        analyst_report = state.get("analyst_report", {})
        market_data = state.get("market_data", {})
        debate_history = state.get("debate_history", [])
        current_round = state.get("current_round", 1)
        
        # Build debate context for subsequent rounds
        debate_context = ""
        counter_instruction = ""
        
        if debate_history and current_round > 1:
            last_bearish = None
            for entry in reversed(debate_history):
                if entry.get("perspective") == "bearish":
                    last_bearish = entry
                    break
            
            if last_bearish:
                debate_context = f"""
PREVIOUS BEARISH ARGUMENT (Round {current_round - 1}):
{last_bearish.get('investment_thesis', 'N/A')}
Key Concerns: {', '.join(last_bearish.get('key_risks', [])[:3])}
"""
                counter_instruction = """
IMPORTANT: Address the bearish concerns raised above. Provide counter-arguments 
and explain why the risks are overstated or manageable.
"""

        price_history = market_data.get("price_history", [])
        current_price = market_data.get("current_price", 0)

        try:
            chain = self.prompt | self.llm | self.parser
            result = chain.invoke({
                "ticker": state["ticker"],
                "analyst_report": str(analyst_report),
                "current_price": current_price,
                "price_trend": self._get_price_trend(price_history),
                "technical_summary": self._get_technical_summary(analyst_report),
                "debate_context": debate_context,
                "counter_instruction": counter_instruction,
            })

            bullish_analysis = {
                "perspective": "bullish",
                "round": current_round,
                "investment_thesis": result.get("investment_thesis", ""),
                "key_arguments": result.get("key_arguments", []),
                "growth_catalysts": result.get("growth_catalysts", []),
                "upside_potential": result.get("upside_potential", ""),
                "confidence": float(result.get("confidence", 0.5)),
                "risk_mitigants": result.get("risk_mitigants", []),
                "recommended_action": result.get("recommended_action", "HOLD"),
            }

            # Update debate history
            updated_history = debate_history + [bullish_analysis]

            return {
                "bullish_analysis": bullish_analysis,
                "debate_history": updated_history,
            }

        except Exception as e:
            return {
                "bullish_analysis": {
                    "perspective": "bullish",
                    "round": current_round,
                    "investment_thesis": f"Analysis failed: {str(e)}",
                    "key_arguments": [],
                    "confidence": 0.0,
                    "recommended_action": "HOLD",
                },
            }

    def __call__(self, state: ResearcherState) -> dict:
        """Make the researcher callable for LangGraph."""
        return self.analyze(state)
