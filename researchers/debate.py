"""Debate Coordinator for Researcher Team.

Manages multi-round debates between bullish and bearish researchers,
synthesizes arguments, and determines consensus.
"""

from typing import Optional, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

from .state import ResearcherState


SYNTHESIS_PROMPT = """You are a senior investment committee moderator synthesizing a debate 
between bullish and bearish researchers.

TICKER: {ticker}

DEBATE SUMMARY:
{debate_summary}

BULLISH FINAL POSITION:
Thesis: {bullish_thesis}
Key Arguments: {bullish_arguments}
Confidence: {bullish_confidence}
Recommended Action: {bullish_action}

BEARISH FINAL POSITION:
Thesis: {bearish_thesis}
Key Arguments: {bearish_arguments}
Confidence: {bearish_confidence}
Recommended Action: {bearish_action}

YOUR TASK:
Synthesize both perspectives into a balanced research report. Consider:
1. Which arguments have stronger evidence?
2. What is the risk/reward profile?
3. Where do both sides agree (consensus)?
4. What are the key unresolved disagreements?
5. What is the most prudent investment action?

Respond in JSON format:
{{
    "investment_thesis": "<balanced thesis considering both perspectives>",
    "bull_case_summary": "<strongest bull arguments>",
    "bear_case_summary": "<strongest bear arguments>",
    "consensus_points": ["<point both sides agree on>", ...],
    "key_disagreements": ["<unresolved debate point>", ...],
    "risk_reward_assessment": "<balanced risk/reward analysis>",
    "key_risks": ["<risk1>", "<risk2>", ...],
    "key_opportunities": ["<opportunity1>", "<opportunity2>", ...],
    "confidence_score": <float 0.0-1.0>,
    "recommended_action": "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL",
    "position_conviction": "HIGH" | "MEDIUM" | "LOW",
    "reasoning": "<detailed reasoning for final recommendation>"
}}
"""


ROUND_EVALUATION_PROMPT = """Evaluate the current debate round and determine if consensus 
has been reached or if another round is needed.

ROUND {round_number} SUMMARY:

BULLISH ARGUMENT:
{bullish_argument}

BEARISH ARGUMENT:
{bearish_argument}

Evaluate:
1. Are there significant unaddressed points?
2. Have both sides made their strongest cases?
3. Is there enough information for a decision?

Respond in JSON format:
{{
    "consensus_reached": <boolean>,
    "key_points_addressed": ["<point1>", "<point2>", ...],
    "unresolved_issues": ["<issue1>", "<issue2>", ...],
    "debate_quality_score": <float 0.0-1.0>,
    "recommendation": "continue" | "conclude",
    "reasoning": "<why continue or conclude>"
}}
"""


class DebateCoordinator:
    """Coordinates multi-round debates and synthesizes final research report."""

    def __init__(self, llm: Optional[ChatGroq] = None, max_rounds: int = 3):
        self.llm = llm or ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
        self.synthesis_prompt = ChatPromptTemplate.from_template(SYNTHESIS_PROMPT)
        self.evaluation_prompt = ChatPromptTemplate.from_template(ROUND_EVALUATION_PROMPT)
        self.parser = JsonOutputParser()
        self.max_rounds = max_rounds

    def evaluate_round(self, state: ResearcherState) -> dict:
        """Evaluate if the current debate round warrants continuation."""
        bullish = state.get("bullish_analysis", {})
        bearish = state.get("bearish_analysis", {})
        current_round = state.get("current_round", 1)

        try:
            chain = self.evaluation_prompt | self.llm | self.parser
            result = chain.invoke({
                "round_number": current_round,
                "bullish_argument": bullish.get("investment_thesis", "N/A"),
                "bearish_argument": bearish.get("investment_thesis", "N/A"),
            })

            should_continue = (
                result.get("recommendation") == "continue" 
                and current_round < self.max_rounds
                and not result.get("consensus_reached", False)
            )

            return {
                "consensus_reached": result.get("consensus_reached", False),
                "should_continue": should_continue,
                "round_evaluation": result,
            }

        except Exception as e:
            return {
                "consensus_reached": False,
                "should_continue": current_round < self.max_rounds,
                "round_evaluation": {"error": str(e)},
            }

    def synthesize_debate(self, state: ResearcherState) -> dict:
        """Synthesize all debate rounds into final research report."""
        bullish = state.get("bullish_analysis", {})
        bearish = state.get("bearish_analysis", {})
        debate_history = state.get("debate_history", [])

        # Build debate summary
        debate_summary = self._build_debate_summary(debate_history)

        try:
            chain = self.synthesis_prompt | self.llm | self.parser
            result = chain.invoke({
                "ticker": state["ticker"],
                "debate_summary": debate_summary,
                "bullish_thesis": bullish.get("investment_thesis", "N/A"),
                "bullish_arguments": self._format_arguments(bullish.get("key_arguments", [])),
                "bullish_confidence": bullish.get("confidence", 0),
                "bullish_action": bullish.get("recommended_action", "HOLD"),
                "bearish_thesis": bearish.get("investment_thesis", "N/A"),
                "bearish_arguments": self._format_arguments(bearish.get("key_arguments", [])),
                "bearish_confidence": bearish.get("confidence", 0),
                "bearish_action": bearish.get("recommended_action", "HOLD"),
            })

            research_report = {
                "investment_thesis": result.get("investment_thesis", ""),
                "bull_case_summary": result.get("bull_case_summary", ""),
                "bear_case_summary": result.get("bear_case_summary", ""),
                "consensus_points": result.get("consensus_points", []),
                "key_disagreements": result.get("key_disagreements", []),
                "risk_reward_assessment": result.get("risk_reward_assessment", ""),
                "key_risks": result.get("key_risks", []),
                "key_opportunities": result.get("key_opportunities", []),
                "confidence_score": float(result.get("confidence_score", 0.5)),
                "recommended_action": result.get("recommended_action", "HOLD"),
                "position_conviction": result.get("position_conviction", "MEDIUM"),
                "reasoning": result.get("reasoning", ""),
                "debate_rounds": len([h for h in debate_history if h.get("perspective") == "bullish"]),
                "bullish_final": bullish,
                "bearish_final": bearish,
            }

            return {
                "research_report": research_report,
                "consensus_reached": True,
            }

        except Exception as e:
            return {
                "research_report": {
                    "investment_thesis": f"Synthesis failed: {str(e)}",
                    "recommended_action": "HOLD",
                    "confidence_score": 0.0,
                    "position_conviction": "LOW",
                },
                "consensus_reached": False,
            }

    def _build_debate_summary(self, debate_history: List[dict]) -> str:
        """Build a summary of all debate rounds."""
        if not debate_history:
            return "No debate history available."

        summary_parts = []
        round_num = 0
        
        for i, entry in enumerate(debate_history):
            if entry.get("perspective") == "bullish":
                round_num += 1
                summary_parts.append(f"\n--- Round {round_num} ---")
            
            perspective = entry.get("perspective", "unknown").upper()
            thesis = entry.get("investment_thesis", "N/A")
            confidence = entry.get("confidence", 0)
            
            summary_parts.append(f"{perspective}: {thesis} (Confidence: {confidence:.0%})")

        return "\n".join(summary_parts)

    def _format_arguments(self, arguments: List[dict]) -> str:
        """Format key arguments for prompt."""
        if not arguments:
            return "No arguments provided"
        
        formatted = []
        for arg in arguments[:5]:  # Limit to top 5
            if isinstance(arg, dict):
                point = arg.get("point", "")
                evidence = arg.get("evidence", "")
                formatted.append(f"• {point}: {evidence}")
            else:
                formatted.append(f"• {arg}")
        
        return "\n".join(formatted)

    def __call__(self, state: ResearcherState) -> dict:
        """Make coordinator callable for LangGraph."""
        return self.synthesize_debate(state)
