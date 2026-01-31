"""Bearish Researcher Agent.

Focuses on potential downsides, risks, and unfavorable market signals.
Provides cautionary insights and highlights possible negative outcomes.
"""

from typing import Optional, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

from .state import ResearcherState


BEARISH_PROMPT = """You are a senior bearish investment researcher. Your role is to identify risks,
potential downsides, and unfavorable conditions that could impact investment returns.

TICKER: {ticker}

ANALYST TEAM REPORT:
{analyst_report}

MARKET DATA SUMMARY:
- Current Price: ${current_price}
- Recent Price Trend: {price_trend}
- Technical Indicators: {technical_summary}

{debate_context}

YOUR TASK:
Construct a compelling BEARISH case against investing in {ticker}. Focus on:
1. Key risk factors and potential threats
2. Competitive pressures and market challenges
3. Concerning financial metrics or trends
4. Negative sentiment indicators
5. Potential downside scenarios

{counter_instruction}

Respond in JSON format:
{{
    "investment_thesis": "<compelling bearish thesis in 2-3 sentences>",
    "key_arguments": [
        {{
            "point": "<risk/concern title>",
            "evidence": "<supporting data/facts>",
            "impact": "<potential negative impact>"
        }}
    ],
    "key_risks": ["<risk1>", "<risk2>", ...],
    "downside_potential": "<percentage or price target>",
    "confidence": <float 0.0-1.0>,
    "bull_case_weaknesses": ["<weakness in bull argument>"],
    "recommended_action": "HOLD" | "SELL" | "STRONG_SELL"
}}
"""


class BearishResearcher:
    """Bearish researcher that identifies risks and potential downsides."""

    def __init__(self, llm: Optional[ChatGroq] = None):
        self.llm = llm or ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)
        self.prompt = ChatPromptTemplate.from_template(BEARISH_PROMPT)
        self.parser = JsonOutputParser()

    def _get_price_trend(self, price_history: List[float]) -> str:
        """Calculate price trend description."""
        if not price_history or len(price_history) < 2:
            return "Insufficient data"
        
        recent = price_history[-5:] if len(price_history) >= 5 else price_history
        start, end = recent[0], recent[-1]
        change = ((end - start) / start) * 100
        
        if change > 5:
            return f"Strong uptrend (+{change:.1f}%) - potentially overextended"
        elif change > 0:
            return f"Mild uptrend (+{change:.1f}%)"
        elif change > -5:
            return f"Mild downtrend ({change:.1f}%) - weakness emerging"
        else:
            return f"Strong downtrend ({change:.1f}%) - bearish momentum"

    def _get_technical_summary(self, analyst_report: dict) -> str:
        """Extract technical summary from analyst report."""
        individual = analyst_report.get("individual_reports", {})
        technical = individual.get("technical", {})
        
        if not technical:
            return "Technical data unavailable"
        
        return f"Signal: {technical.get('signal', 'N/A')}, Confidence: {technical.get('confidence', 0):.0%}"

    def analyze(self, state: ResearcherState) -> dict:
        """Generate bearish analysis for the ticker."""
        analyst_report = state.get("analyst_report", {})
        market_data = state.get("market_data", {})
        debate_history = state.get("debate_history", [])
        current_round = state.get("current_round", 1)
        
        # Build debate context for counter-arguments
        debate_context = ""
        counter_instruction = ""
        
        # Find the latest bullish argument to counter
        last_bullish = None
        for entry in reversed(debate_history):
            if entry.get("perspective") == "bullish":
                last_bullish = entry
                break
        
        if last_bullish:
            debate_context = f"""
CURRENT BULLISH ARGUMENT (Round {current_round}):
{last_bullish.get('investment_thesis', 'N/A')}
Growth Catalysts Claimed: {', '.join(last_bullish.get('growth_catalysts', [])[:3])}
Upside Potential: {last_bullish.get('upside_potential', 'N/A')}
"""
            counter_instruction = """
IMPORTANT: Directly challenge the bullish arguments above. Explain why the growth 
catalysts may not materialize and why the upside potential is overstated.
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

            bearish_analysis = {
                "perspective": "bearish",
                "round": current_round,
                "investment_thesis": result.get("investment_thesis", ""),
                "key_arguments": result.get("key_arguments", []),
                "key_risks": result.get("key_risks", []),
                "downside_potential": result.get("downside_potential", ""),
                "confidence": float(result.get("confidence", 0.5)),
                "bull_case_weaknesses": result.get("bull_case_weaknesses", []),
                "recommended_action": result.get("recommended_action", "HOLD"),
            }

            # Update debate history
            updated_history = debate_history + [bearish_analysis]

            return {
                "bearish_analysis": bearish_analysis,
                "debate_history": updated_history,
            }

        except Exception as e:
            return {
                "bearish_analysis": {
                    "perspective": "bearish",
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
