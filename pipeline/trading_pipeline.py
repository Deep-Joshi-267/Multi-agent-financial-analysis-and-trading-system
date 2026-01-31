"""Unified Trading Pipeline.

Orchestrates the complete trading analysis workflow:
1. Data Fetching → 2. Analyst Team → 3. Researcher Team → 4. CIO Decision → 5. Trader Execution → 6. Risk Management

Uses LangGraph for workflow management with proper state transitions,
feedback-driven reasoning, human-in-the-loop approval, and risk oversight.
"""

from typing import TypedDict, Optional, List, Literal
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

from analysts import AnalystsTeam
from researchers import ResearcherTeam
from traders import TraderTeam
from risk_management import RiskManagementTeam
from data import MarketDataFetcher


class PipelineState(TypedDict):
    """State for the complete trading pipeline."""
    
    # Input
    ticker: str
    
    # Configuration
    available_capital: float
    risk_tolerance: str
    portfolio: List[dict]
    enable_trading: bool
    require_human_approval: bool
    
    # Data layer
    market_data: Optional[dict]
    data_fetch_status: str
    
    # Analyst layer
    analyst_report: Optional[dict]
    analyst_status: str
    
    # Researcher layer
    research_report: Optional[dict]
    research_status: str
    
    # CIO Decision
    final_decision: Optional[dict]
    
    # Trader layer
    trade_execution: Optional[dict]
    trader_status: str
    
    # Risk Management layer
    risk_assessment: Optional[dict]
    risk_status: str
    
    # Metadata
    pipeline_stage: str
    errors: List[str]
    messages: List[dict]


FINAL_DECISION_PROMPT = """You are the Chief Investment Officer making the final trading decision.

TICKER: {ticker}

ANALYST TEAM REPORT:
Signal: {analyst_signal}
Confidence: {analyst_confidence}
Reasoning: {analyst_reasoning}

RESEARCHER TEAM REPORT:
Investment Thesis: {research_thesis}
Bull Case: {bull_case}
Bear Case: {bear_case}
Risk/Reward: {risk_reward}
Researcher Recommendation: {research_action}
Conviction: {research_conviction}

KEY RISKS: {key_risks}
KEY OPPORTUNITIES: {key_opportunities}

CONSENSUS POINTS: {consensus_points}
DISAGREEMENTS: {disagreements}

YOUR TASK:
Make the final trading decision by weighing both the analyst team's technical/fundamental 
analysis and the researcher team's balanced debate conclusions.

Respond in JSON format:
{{
    "final_action": "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL",
    "confidence": <float 0.0-1.0>,
    "position_size": "FULL" | "THREE_QUARTER" | "HALF" | "QUARTER" | "NONE",
    "time_horizon": "SHORT" | "MEDIUM" | "LONG",
    "entry_strategy": "<how to enter the position>",
    "exit_strategy": "<when to exit or stop-loss levels>",
    "risk_management": "<position sizing and risk controls>",
    "key_catalysts": ["<catalyst to watch>", ...],
    "reasoning": "<comprehensive reasoning for decision>",
    "dissenting_view": "<acknowledge any significant counter-arguments>"
}}
"""


class TradingPipeline:
    """
    Complete trading analysis pipeline integrating all teams.
    
    Pipeline Flow:
    ┌──────────────┐    ┌───────────────┐    ┌─────────────────┐    ┌────────────┐    ┌─────────────┐    ┌─────────────────┐
    │ Data Fetch   │───▶│ Analyst Team  │───▶│ Researcher Team │───▶│    CIO     │───▶│ Trader Team │───▶│ Risk Management │
    │ (Market Data)│    │ (4 Analysts)  │    │ (Bull vs Bear)  │    │  Decision  │    │ (Execution) │    │ (3 Advisors)    │
    └──────────────┘    └───────────────┘    └─────────────────┘    └────────────┘    └─────────────┘    └─────────────────┘
    
    Features:
    - Feedback-driven reasoning in Trader Team
    - Human-in-the-loop for trade approval
    - Max iteration threshold to prevent infinite loops
    - Scoring system for decision quality
    - Risk Management with Risky/Neutral/Safe advisors
    """

    def __init__(
        self,
        llm: Optional[ChatGroq] = None,
        max_debate_rounds: int = 2,
        max_trade_iterations: int = 3,
        score_threshold: float = 0.6,
        require_human_approval: bool = True,
        verbose: bool = False,
    ):
        self.llm = llm or ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
        self.verbose = verbose
        self.require_human_approval = require_human_approval
        
        # Initialize teams
        self.data_fetcher = MarketDataFetcher(verbose=verbose)
        self.analyst_team = AnalystsTeam(llm=self.llm)
        self.researcher_team = ResearcherTeam(llm=self.llm, max_debate_rounds=max_debate_rounds)
        self.trader_team = TraderTeam(
            llm=self.llm,
            max_iterations=max_trade_iterations,
            score_threshold=score_threshold,
            require_human_approval=require_human_approval,
        )
        self.risk_management_team = RiskManagementTeam(llm=self.llm)
        
        # Build pipeline graph
        self.graph = self._build_pipeline()
        
        # Decision prompt
        self.decision_prompt = ChatPromptTemplate.from_template(FINAL_DECISION_PROMPT)
        self.parser = JsonOutputParser()

    def _build_pipeline(self) -> StateGraph:
        """Build the complete trading pipeline graph."""
        
        workflow = StateGraph(PipelineState)

        # Add nodes for each stage
        workflow.add_node("fetch_data", self._fetch_data_node)
        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("research", self._research_node)
        workflow.add_node("decide", self._decide_node)
        workflow.add_node("trade", self._trade_node)
        workflow.add_node("risk_manage", self._risk_manage_node)

        # Set entry point
        workflow.set_entry_point("fetch_data")

        # Linear flow with error handling
        workflow.add_conditional_edges(
            "fetch_data",
            self._check_data_status,
            {
                "success": "analyze",
                "error": END,
            }
        )
        
        workflow.add_conditional_edges(
            "analyze",
            self._check_analyst_status,
            {
                "success": "research",
                "error": "decide",  # Still try to decide with partial data
            }
        )
        
        workflow.add_edge("research", "decide")
        
        # Conditional: Execute trade or end
        workflow.add_conditional_edges(
            "decide",
            self._should_execute_trade,
            {
                "execute": "trade",
                "skip": END,
            }
        )
        
        # After trade, run risk management
        workflow.add_edge("trade", "risk_manage")
        workflow.add_edge("risk_manage", END)

        return workflow.compile()

    def _fetch_data_node(self, state: PipelineState) -> dict:
        """Fetch market data for the ticker."""
        ticker = state["ticker"]
        
        if self.verbose:
            print(f"[Pipeline] Fetching data for {ticker}...")
        
        try:
            market_data = self.data_fetcher.fetch_market_data(
                ticker=ticker,
                news_days=3,
                news_limit=10,
                price_days=60,
            )
            
            return {
                "market_data": market_data,
                "data_fetch_status": "success",
                "pipeline_stage": "data_fetched",
            }
        except Exception as e:
            return {
                "market_data": {},
                "data_fetch_status": "error",
                "errors": state.get("errors", []) + [f"Data fetch failed: {str(e)}"],
                "pipeline_stage": "data_error",
            }

    def _analyze_node(self, state: PipelineState) -> dict:
        """Run analyst team analysis."""
        ticker = state["ticker"]
        market_data = state.get("market_data", {})
        
        if self.verbose:
            print(f"[Pipeline] Running analyst team for {ticker}...")
        
        try:
            analyst_report = self.analyst_team.analyze(
                ticker=ticker,
                market_data=market_data,
            )
            
            return {
                "analyst_report": analyst_report,
                "analyst_status": "success",
                "pipeline_stage": "analyzed",
            }
        except Exception as e:
            return {
                "analyst_report": {"error": str(e)},
                "analyst_status": "error",
                "errors": state.get("errors", []) + [f"Analysis failed: {str(e)}"],
                "pipeline_stage": "analysis_error",
            }

    def _research_node(self, state: PipelineState) -> dict:
        """Run researcher team debate."""
        ticker = state["ticker"]
        analyst_report = state.get("analyst_report", {})
        market_data = state.get("market_data", {})
        
        if self.verbose:
            print(f"[Pipeline] Running researcher debate for {ticker}...")
        
        try:
            research_report = self.researcher_team.research(
                ticker=ticker,
                analyst_report=analyst_report,
                market_data=market_data,
            )
            
            return {
                "research_report": research_report,
                "research_status": "success",
                "pipeline_stage": "researched",
            }
        except Exception as e:
            return {
                "research_report": {"error": str(e)},
                "research_status": "error",
                "errors": state.get("errors", []) + [f"Research failed: {str(e)}"],
                "pipeline_stage": "research_error",
            }

    def _decide_node(self, state: PipelineState) -> dict:
        """Make final trading decision."""
        ticker = state["ticker"]
        analyst_report = state.get("analyst_report", {})
        research_report = state.get("research_report", {})
        
        if self.verbose:
            print(f"[Pipeline] Making final decision for {ticker}...")
        
        try:
            chain = self.decision_prompt | self.llm | self.parser
            
            result = chain.invoke({
                "ticker": ticker,
                "analyst_signal": analyst_report.get("final_signal", "N/A"),
                "analyst_confidence": f"{analyst_report.get('confidence', 0):.0%}",
                "analyst_reasoning": analyst_report.get("reasoning", "N/A"),
                "research_thesis": research_report.get("investment_thesis", "N/A"),
                "bull_case": research_report.get("bull_case_summary", "N/A"),
                "bear_case": research_report.get("bear_case_summary", "N/A"),
                "risk_reward": research_report.get("risk_reward_assessment", "N/A"),
                "research_action": research_report.get("recommended_action", "N/A"),
                "research_conviction": research_report.get("position_conviction", "N/A"),
                "key_risks": ", ".join(research_report.get("key_risks", [])[:5]),
                "key_opportunities": ", ".join(research_report.get("key_opportunities", [])[:5]),
                "consensus_points": ", ".join(research_report.get("consensus_points", [])[:3]),
                "disagreements": ", ".join(research_report.get("key_disagreements", [])[:3]),
            })
            
            final_decision = {
                "ticker": ticker,
                "action": result.get("final_action", "HOLD"),
                "confidence": float(result.get("confidence", 0.5)),
                "position_size": result.get("position_size", "NONE"),
                "time_horizon": result.get("time_horizon", "MEDIUM"),
                "entry_strategy": result.get("entry_strategy", ""),
                "exit_strategy": result.get("exit_strategy", ""),
                "risk_management": result.get("risk_management", ""),
                "key_catalysts": result.get("key_catalysts", []),
                "reasoning": result.get("reasoning", ""),
                "dissenting_view": result.get("dissenting_view", ""),
                "analyst_report": analyst_report,
                "research_report": research_report,
            }
            
            return {
                "final_decision": final_decision,
                "pipeline_stage": "complete",
            }
            
        except Exception as e:
            return {
                "final_decision": {
                    "ticker": ticker,
                    "action": "HOLD",
                    "confidence": 0.0,
                    "reasoning": f"Decision failed: {str(e)}",
                    "analyst_report": analyst_report,
                    "research_report": research_report,
                },
                "pipeline_stage": "decision_error",
                "errors": state.get("errors", []) + [f"Decision failed: {str(e)}"],
            }

    def _trade_node(self, state: PipelineState) -> dict:
        """Execute trading workflow with feedback loop."""
        ticker = state["ticker"]
        
        if self.verbose:
            print(f"[Pipeline] Running trader team for {ticker}...")
        
        try:
            trade_result = self.trader_team.execute_trade(
                ticker=ticker,
                analyst_report=state.get("analyst_report", {}),
                research_report=state.get("research_report", {}),
                final_decision=state.get("final_decision", {}),
                market_data=state.get("market_data", {}),
                available_capital=state.get("available_capital", 100000.0),
                risk_tolerance=state.get("risk_tolerance", "moderate"),
                portfolio=state.get("portfolio", []),
            )
            
            return {
                "trade_execution": trade_result,
                "trader_status": "success",
                "pipeline_stage": "executed",
            }
        except Exception as e:
            return {
                "trade_execution": {"error": str(e)},
                "trader_status": "error",
                "errors": state.get("errors", []) + [f"Trade execution failed: {str(e)}"],
                "pipeline_stage": "trade_error",
            }

    def _risk_manage_node(self, state: PipelineState) -> dict:
        """Execute risk management assessment."""
        ticker = state["ticker"]
        
        if self.verbose:
            print(f"[Pipeline] Running risk management team for {ticker}...")
        
        try:
            risk_result = self.risk_management_team.assess_risk(
                ticker=ticker,
                trade_execution=state.get("trade_execution", {}),
                final_decision=state.get("final_decision", {}),
                analyst_report=state.get("analyst_report", {}),
                research_report=state.get("research_report", {}),
                market_data=state.get("market_data", {}),
                available_capital=state.get("available_capital", 100000.0),
                current_exposure=0.0,  # Could be calculated from portfolio
                risk_tolerance=state.get("risk_tolerance", "moderate"),
                portfolio=state.get("portfolio", []),
            )
            
            return {
                "risk_assessment": risk_result,
                "risk_status": "success",
                "pipeline_stage": "risk_assessed",
            }
        except Exception as e:
            return {
                "risk_assessment": {"error": str(e)},
                "risk_status": "error",
                "errors": state.get("errors", []) + [f"Risk assessment failed: {str(e)}"],
                "pipeline_stage": "risk_error",
            }

    def _check_data_status(self, state: PipelineState) -> Literal["success", "error"]:
        """Check if data fetch was successful."""
        return "success" if state.get("data_fetch_status") == "success" else "error"

    def _check_analyst_status(self, state: PipelineState) -> Literal["success", "error"]:
        """Check if analyst phase was successful."""
        return "success" if state.get("analyst_status") == "success" else "error"

    def _should_execute_trade(self, state: PipelineState) -> Literal["execute", "skip"]:
        """Determine if trade execution should proceed."""
        enable_trading = state.get("enable_trading", True)
        final_decision = state.get("final_decision", {})
        action = final_decision.get("action", "HOLD")
        
        # Skip trading if disabled or HOLD action
        if not enable_trading:
            return "skip"
        
        if action == "HOLD":
            return "skip"
        
        return "execute"

    def run(
        self,
        ticker: str,
        available_capital: float = 100000.0,
        risk_tolerance: str = "moderate",
        portfolio: list = None,
        enable_trading: bool = True,
    ) -> dict:
        """
        Run the complete trading pipeline for a ticker.
        
        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            available_capital: Capital available for trading
            risk_tolerance: "conservative", "moderate", or "aggressive"
            portfolio: Current portfolio positions
            enable_trading: Whether to execute trades
            
        Returns:
            Complete trading decision with execution results
        """
        initial_state: PipelineState = {
            "ticker": ticker.upper().strip(),
            "available_capital": available_capital,
            "risk_tolerance": risk_tolerance,
            "portfolio": portfolio or [],
            "enable_trading": enable_trading,
            "require_human_approval": self.require_human_approval,
            "market_data": None,
            "data_fetch_status": "pending",
            "analyst_report": None,
            "analyst_status": "pending",
            "research_report": None,
            "research_status": "pending",
            "final_decision": None,
            "trade_execution": None,
            "trader_status": "pending",
            "risk_assessment": None,
            "risk_status": "pending",
            "pipeline_stage": "initialized",
            "errors": [],
            "messages": [],
        }

        result = self.graph.invoke(initial_state)
        
        # Build comprehensive result
        final_decision = result.get("final_decision", {})
        trade_execution = result.get("trade_execution", {})
        risk_assessment = result.get("risk_assessment", {})
        
        return {
            **final_decision,
            "trade_execution": trade_execution,
            "risk_assessment": risk_assessment,
            "pipeline_stage": result.get("pipeline_stage"),
            "errors": result.get("errors", []),
        }

    def run_with_details(
        self,
        ticker: str,
        available_capital: float = 100000.0,
        risk_tolerance: str = "moderate",
        portfolio: list = None,
        enable_trading: bool = True,
    ) -> dict:
        """Run pipeline and return full state including intermediate results."""
        initial_state: PipelineState = {
            "ticker": ticker.upper().strip(),
            "available_capital": available_capital,
            "risk_tolerance": risk_tolerance,
            "portfolio": portfolio or [],
            "enable_trading": enable_trading,
            "require_human_approval": self.require_human_approval,
            "market_data": None,
            "data_fetch_status": "pending",
            "analyst_report": None,
            "analyst_status": "pending",
            "research_report": None,
            "research_status": "pending",
            "final_decision": None,
            "trade_execution": None,
            "trader_status": "pending",
            "risk_assessment": None,
            "risk_status": "pending",
            "pipeline_stage": "initialized",
            "errors": [],
            "messages": [],
        }

        result = self.graph.invoke(initial_state)
        
        return {
            "ticker": ticker,
            "final_decision": result.get("final_decision"),
            "analyst_report": result.get("analyst_report"),
            "research_report": result.get("research_report"),
            "trade_execution": result.get("trade_execution"),
            "risk_assessment": result.get("risk_assessment"),
            "market_data_summary": {
                "current_price": result.get("market_data", {}).get("current_price"),
                "news_count": len(result.get("market_data", {}).get("news_articles", [])),
            },
            "pipeline_stage": result.get("pipeline_stage"),
            "errors": result.get("errors", []),
        }
