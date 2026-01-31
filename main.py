#!/usr/bin/env python3
"""
TradingAgents - Production-Ready Multi-Agent Financial Analysis System

A LangGraph-powered trading analysis framework with:
- Analyst Team: News, Fundamentals, Sentiment, Technical analysts
- Researcher Team: Bullish vs Bearish debate with multi-round dialectics
- Trading Pipeline: Complete workflow from data to final decision

Usage:
    python main.py AAPL                    # Full pipeline analysis
    python main.py AAPL --quick            # Analyst-only (no debate)
    python main.py AAPL MSFT GOOGL         # Analyze multiple tickers
    python main.py --visualize             # Show workflow graph
    python main.py AAPL --output json      # Output as JSON
    python main.py AAPL --verbose          # Verbose logging
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("TradingAgents")


def setup_environment() -> bool:
    """Load environment variables and validate configuration."""
    load_dotenv()
    
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        logger.error("GROQ_API_KEY not found in environment")
        logger.error("Set it in .env file: GROQ_API_KEY=gsk_...")
        return False
    
    if groq_key.startswith("gsk_") and len(groq_key) > 20:
        logger.info("Groq API key configured ✓")
        return True
    
    logger.warning("GROQ_API_KEY format may be invalid")
    return True


def visualize_graph(save_path: Optional[str] = None, full_pipeline: bool = True) -> None:
    """
    Visualize the LangGraph workflow and optionally save to file.
    
    Args:
        save_path: Optional path to save the graph image
        full_pipeline: If True, show full pipeline; else show analyst team only
    """
    try:
        if full_pipeline:
            from pipeline import TradingPipeline
            logger.info("Building full pipeline graph...")
            pipeline = TradingPipeline()
            graph = pipeline.graph
        else:
            from analysts import AnalystsTeam
            logger.info("Building analyst team graph...")
            team = AnalystsTeam()
            graph = team.graph
        
        # Try to use graphviz for visualization
        try:
            from IPython.display import Image, display
            
            # Generate PNG using mermaid
            png_data = graph.get_graph().draw_mermaid_png()
            
            if save_path:
                with open(save_path, "wb") as f:
                    f.write(png_data)
                logger.info(f"Graph saved to: {save_path}")
            else:
                # Save to default location
                output_path = Path("workflow_graph.png")
                with open(output_path, "wb") as f:
                    f.write(png_data)
                logger.info(f"Graph saved to: {output_path.absolute()}")
                
        except ImportError:
            # Fallback: print ASCII representation
            logger.info("Graphviz not available, printing ASCII representation:")
            print_ascii_graph()
            
    except Exception as e:
        logger.error(f"Failed to visualize graph: {e}")
        print_ascii_graph()


def print_ascii_graph() -> None:
    """Print ASCII representation of the full trading pipeline."""
    graph_ascii = """
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                         TRADING AGENTS - FULL PIPELINE GRAPH                          ║
╠═══════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                       ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐  ║
║  │                            STAGE 1: DATA FETCHING                               │  ║
║  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │  ║
║  │  │  News Scraper   │    │  Stock Data     │    │  Market Data    │             │  ║
║  │  │  (MoneyControl) │    │  (yfinance)     │    │  (Combined)     │             │  ║
║  │  └─────────────────┘    └─────────────────┘    └─────────────────┘             │  ║
║  └──────────────────────────────────┬──────────────────────────────────────────────┘  ║
║                                     │                                                 ║
║                                     ▼                                                 ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐  ║
║  │                            STAGE 2: ANALYST TEAM                                │  ║
║  │  ┌────────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐           │  ║
║  │  │    News    │  │ Fundamentals │  │  Sentiment  │  │  Technical   │           │  ║
║  │  │  Analyst   │─▶│   Analyst    │─▶│   Analyst   │─▶│   Analyst    │           │  ║
║  │  └────────────┘  └──────────────┘  └─────────────┘  └──────────────┘           │  ║
║  │                                     │                                           │  ║
║  │                                     ▼                                           │  ║
║  │                          ┌──────────────────┐                                   │  ║
║  │                          │   Consolidate    │                                   │  ║
║  │                          │  (Analyst CIO)   │                                   │  ║
║  │                          └──────────────────┘                                   │  ║
║  └──────────────────────────────────┬──────────────────────────────────────────────┘  ║
║                                     │                                                 ║
║                                     ▼                                                 ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐  ║
║  │                          STAGE 3: RESEARCHER TEAM                               │  ║
║  │                                                                                 │  ║
║  │     ┌──────────────────┐           ┌──────────────────┐                        │  ║
║  │     │     BULLISH      │◀─────────▶│     BEARISH      │                        │  ║
║  │     │   RESEARCHER     │  DEBATE   │   RESEARCHER     │                        │  ║
║  │     │                  │  ROUNDS   │                  │                        │  ║
║  │     │ • Growth thesis  │◀─────────▶│ • Risk analysis  │                        │  ║
║  │     │ • Opportunities  │           │ • Downsides      │                        │  ║
║  │     │ • Bull case      │           │ • Bear case      │                        │  ║
║  │     └────────┬─────────┘           └────────┬─────────┘                        │  ║
║  │              │                              │                                   │  ║
║  │              └──────────────┬───────────────┘                                   │  ║
║  │                             ▼                                                   │  ║
║  │                  ┌──────────────────┐                                           │  ║
║  │                  │    Synthesize    │                                           │  ║
║  │                  │  (Debate Result) │                                           │  ║
║  │                  └──────────────────┘                                           │  ║
║  └──────────────────────────────────┬──────────────────────────────────────────────┘  ║
║                                     │                                                 ║
║                                     ▼                                                 ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐  ║
║  │                          STAGE 4: CIO DECISION                                  │  ║
║  │                       ┌──────────────────────┐                                  │  ║
║  │                       │   CHIEF INVESTMENT   │                                  │  ║
║  │                       │       OFFICER        │                                  │  ║
║  │                       └──────────────────────┘                                  │  ║
║  └──────────────────────────────────┬──────────────────────────────────────────────┘  ║
║                                     │                                                 ║
║                                     ▼                                                 ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐  ║
║  │                          STAGE 5: TRADER TEAM                                   │  ║
║  │                                                                                 │  ║
║  │   ┌─────────────┐    ┌──────────────┐    ┌───────────────┐    ┌────────────┐   │  ║
║  │   │   TRADER    │───▶│    RISK      │───▶│   PORTFOLIO   │───▶│  EXECUTOR  │   │  ║
║  │   │   AGENT     │    │   MANAGER    │    │   MANAGER     │    │            │   │  ║
║  │   └─────────────┘    └──────────────┘    └───────────────┘    └──────┬─────┘   │  ║
║  │         ▲                   │                                        │         │  ║
║  │         │    FEEDBACK       │                                        ▼         │  ║
║  │         │    LOOP           │                              ┌─────────────────┐ │  ║
║  │         └───────────────────┘                              │  HUMAN APPROVAL │ │  ║
║  │         (Max 3 iterations)                                 │  (if required)  │ │  ║
║  │         Score threshold: 0.6                               └─────────────────┘ │  ║
║  └──────────────────────────────────┬──────────────────────────────────────────────┘  ║
║                                     │                                                 ║
║                                     ▼                                                 ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐  ║
║  │                          STAGE 6: RISK MANAGEMENT TEAM                          │  ║
║  │                                                                                 │  ║
║  │   ┌─────────────┐    ┌──────────────┐    ┌───────────────┐                     │  ║
║  │   │   RISKY     │    │   NEUTRAL    │    │     SAFE      │                     │  ║
║  │   │  ADVISOR    │    │   ADVISOR    │    │   ADVISOR     │                     │  ║
║  │   │ (Aggressive)│    │  (Balanced)  │    │(Conservative) │                     │  ║
║  │   └──────┬──────┘    └──────┬───────┘    └───────┬───────┘                     │  ║
║  │          └──────────────────┼────────────────────┘                             │  ║
║  │                             ▼                                                   │  ║
║  │                  ┌──────────────────┐                                           │  ║
║  │                  │  REPORT MANAGER  │                                           │  ║
║  │                  │ (Final Approval) │                                           │  ║
║  │                  └──────────────────┘                                           │  ║
║  └─────────────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                       ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝
"""
    print(graph_ascii)


def analyze_ticker(
    ticker: str,
    verbose: bool = False,
    output_format: str = "text",
    quick_mode: bool = False,
) -> Dict[str, Any]:
    """
    Run full analysis on a single ticker.
    
    Args:
        ticker: Stock ticker symbol
        verbose: Enable verbose logging
        output_format: "text" or "json"
        quick_mode: If True, run analyst-only (skip researcher debate)
        
    Returns:
        Analysis result dictionary
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    ticker = ticker.upper().strip()
    logger.info(f"Analyzing {ticker}..." + (" (quick mode)" if quick_mode else " (full pipeline)"))
    
    if quick_mode:
        # Quick mode: Analyst team only
        from analysts import AnalystsTeam
        from data import MarketDataFetcher
        
        logger.info("Fetching market data...")
        fetcher = MarketDataFetcher(verbose=verbose)
        
        try:
            market_data = fetcher.fetch_market_data(
                ticker=ticker,
                news_days=3,
                news_limit=10,
                price_days=60,
            )
        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
            return {"error": str(e), "ticker": ticker}
        
        logger.info(f"  Price: ${market_data.get('current_price', 0):.2f}")
        logger.info(f"  News articles: {len(market_data.get('news_articles', []))}")
        
        logger.info("Running analyst team...")
        team = AnalystsTeam()
        
        try:
            result = team.analyze(ticker=ticker, market_data=market_data)
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {"error": str(e), "ticker": ticker}
        
        result["ticker"] = ticker
        result["timestamp"] = datetime.now().isoformat()
        result["mode"] = "quick"
        return result
    
    else:
        # Full pipeline: Analysts + Researchers + Final Decision
        from pipeline import TradingPipeline
        
        logger.info("Running full trading pipeline...")
        pipeline = TradingPipeline(verbose=verbose)
        
        try:
            result = pipeline.run(ticker=ticker)
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {"error": str(e), "ticker": ticker}
        
        result["timestamp"] = datetime.now().isoformat()
        result["mode"] = "full"
        return result


def format_result_text(result: Dict[str, Any]) -> str:
    """Format analysis result as readable text."""
    if "error" in result:
        return f"❌ Error analyzing {result.get('ticker', 'unknown')}: {result['error']}"
    
    mode = result.get("mode", "quick")
    
    if mode == "full":
        return format_full_pipeline_result(result)
    else:
        return format_quick_result(result)


def format_quick_result(result: Dict[str, Any]) -> str:
    """Format quick (analyst-only) result."""
    lines = [
        "",
        "═" * 70,
        f"  TRADING ANALYSIS: {result.get('ticker', 'N/A')} (Quick Mode)",
        f"  Generated: {result.get('timestamp', 'N/A')}",
        "═" * 70,
        "",
        f"  📊 RECOMMENDATION: {result.get('final_signal', 'N/A')}",
        f"  📈 Confidence:     {result.get('confidence', 0):.1%}",
        f"  💰 Position Size:  {result.get('position_size', 'N/A')}",
        f"  ⏱️  Time Horizon:   {result.get('time_horizon', 'N/A')}",
        "",
        "─" * 70,
        "  REASONING:",
        "─" * 70,
        f"  {result.get('reasoning', 'N/A')}",
        "",
    ]
    
    # Individual analyst signals
    individual = result.get("individual_reports", {})
    if individual:
        lines.extend([
            "─" * 70,
            "  INDIVIDUAL ANALYST SIGNALS:",
            "─" * 70,
        ])
        for name, report in individual.items():
            if report:
                sig = report.get("signal", "N/A")
                conf = report.get("confidence", 0)
                lines.append(f"    {name.upper():15} {sig:6} ({conf:.0%})")
        lines.append("")
    
    lines.append("═" * 70)
    return "\n".join(lines)


def format_full_pipeline_result(result: Dict[str, Any]) -> str:
    """Format full pipeline result with researcher debate."""
    lines = [
        "",
        "═" * 80,
        f"  TRADING AGENTS ANALYSIS: {result.get('ticker', 'N/A')} (Full Pipeline)",
        f"  Generated: {result.get('timestamp', 'N/A')}",
        "═" * 80,
        "",
        "┌" + "─" * 78 + "┐",
        "│  📊 FINAL DECISION" + " " * 59 + "│",
        "├" + "─" * 78 + "┤",
        f"│  Action:         {result.get('action', 'N/A'):58} │",
        f"│  Confidence:     {result.get('confidence', 0):.1%}{' ' * 54}│",
        f"│  Position Size:  {result.get('position_size', 'N/A'):58} │",
        f"│  Time Horizon:   {result.get('time_horizon', 'N/A'):58} │",
        "└" + "─" * 78 + "┘",
        "",
    ]
    
    # Entry/Exit Strategy
    if result.get("entry_strategy") or result.get("exit_strategy"):
        lines.extend([
            "─" * 80,
            "  📈 TRADING STRATEGY:",
            "─" * 80,
            f"  Entry: {result.get('entry_strategy', 'N/A')}",
            f"  Exit:  {result.get('exit_strategy', 'N/A')}",
            f"  Risk:  {result.get('risk_management', 'N/A')}",
            "",
        ])
    
    # Key Catalysts
    catalysts = result.get("key_catalysts", [])
    if catalysts:
        lines.extend([
            "─" * 80,
            "  🎯 KEY CATALYSTS TO WATCH:",
            "─" * 80,
        ])
        for cat in catalysts[:5]:
            lines.append(f"    • {cat}")
        lines.append("")
    
    # Reasoning
    lines.extend([
        "─" * 80,
        "  💭 REASONING:",
        "─" * 80,
        f"  {result.get('reasoning', 'N/A')}",
        "",
    ])
    
    # Dissenting View
    if result.get("dissenting_view"):
        lines.extend([
            "─" * 80,
            "  ⚖️  DISSENTING VIEW:",
            "─" * 80,
            f"  {result.get('dissenting_view', 'N/A')}",
            "",
        ])
    
    # Research Report Summary
    research = result.get("research_report", {})
    if research and not research.get("error"):
        lines.extend([
            "═" * 80,
            "  📚 RESEARCHER TEAM DEBATE SUMMARY",
            "═" * 80,
            "",
            f"  Investment Thesis: {research.get('investment_thesis', 'N/A')}",
            "",
            "  🐂 BULL CASE:",
            f"     {research.get('bull_case_summary', 'N/A')}",
            "",
            "  🐻 BEAR CASE:",
            f"     {research.get('bear_case_summary', 'N/A')}",
            "",
        ])
        
        # Consensus points
        consensus = research.get("consensus_points", [])
        if consensus:
            lines.append("  ✓ CONSENSUS POINTS:")
            for point in consensus[:3]:
                lines.append(f"     • {point}")
            lines.append("")
        
        # Disagreements
        disagreements = research.get("key_disagreements", [])
        if disagreements:
            lines.append("  ✗ KEY DISAGREEMENTS:")
            for point in disagreements[:3]:
                lines.append(f"     • {point}")
            lines.append("")
    
    # Analyst Team Summary
    analyst = result.get("analyst_report", {})
    if analyst and not analyst.get("error"):
        individual = analyst.get("individual_reports", {})
        if individual:
            lines.extend([
                "═" * 80,
                "  👥 ANALYST TEAM SIGNALS",
                "═" * 80,
            ])
            for name, report in individual.items():
                if report:
                    sig = report.get("signal", "N/A")
                    conf = report.get("confidence", 0)
                    lines.append(f"    {name.upper():18} {sig:12} ({conf:.0%})")
            lines.append("")
    
    # Trade Execution Summary
    trade_exec = result.get("trade_execution", {})
    if trade_exec and not trade_exec.get("error"):
        lines.extend([
            "═" * 80,
            "  💹 TRADE EXECUTION",
            "═" * 80,
        ])
        
        trade_decision = trade_exec.get("trade_decision", {})
        final_score = trade_exec.get("final_score", {})
        executed_orders = trade_exec.get("executed_orders", [])
        
        lines.append(f"  Action:          {trade_decision.get('action', 'N/A')}")
        lines.append(f"  Order Type:      {trade_decision.get('order_type', 'N/A')}")
        lines.append(f"  Position Size:   {trade_decision.get('quantity_percent', 0)*100:.1f}% of capital")
        lines.append(f"  Entry Timing:    {trade_decision.get('entry_timing', 'N/A')}")
        lines.append(f"  Stop Loss:       {trade_decision.get('stop_loss_percent', 0)}%")
        lines.append(f"  Take Profit:     {trade_decision.get('take_profit_percent', 0)}%")
        lines.append(f"  Risk/Reward:     {trade_decision.get('risk_reward_ratio', 0):.2f}")
        lines.append("")
        
        # Scoring
        if final_score:
            lines.append("  📊 DECISION QUALITY SCORE:")
            lines.append(f"     Overall:    {final_score.get('overall_score', 0):.2f}/1.0")
            lines.append(f"     Risk:       {final_score.get('risk_score', 0):.2f}")
            lines.append(f"     Reward:     {final_score.get('reward_score', 0):.2f}")
            lines.append(f"     Timing:     {final_score.get('timing_score', 0):.2f}")
            lines.append(f"     Alignment:  {final_score.get('alignment_score', 0):.2f}")
            lines.append(f"     Iterations: {trade_exec.get('iterations_used', 1)}")
            lines.append("")
        
        # Execution status
        exec_status = trade_exec.get("execution_status", "N/A")
        human_approved = trade_exec.get("human_approved")
        
        lines.append(f"  Execution Status: {exec_status}")
        if human_approved is not None:
            lines.append(f"  Human Approved:   {'✓ Yes' if human_approved else '✗ No'}")
        
        # Executed orders
        if executed_orders:
            lines.append("")
            lines.append("  📋 EXECUTED ORDERS:")
            for order in executed_orders:
                lines.append(f"     [{order.get('order_id', 'N/A')}] {order.get('side', 'N/A')} "
                           f"{order.get('quantity', 0)} shares @ ${order.get('execution_price', 0):.2f}")
        lines.append("")
    
    # Risk Management Assessment
    risk_assessment = result.get("risk_assessment", {})
    if risk_assessment and not risk_assessment.get("error"):
        final_rec = risk_assessment.get("final_recommendation", {})
        advisors = risk_assessment.get("advisor_assessments", {})
        
        lines.extend([
            "═" * 80,
            "  🛡️ RISK MANAGEMENT ASSESSMENT",
            "═" * 80,
        ])
        
        lines.append(f"  Final Action:      {final_rec.get('action', 'N/A')}")
        lines.append(f"  Risk Level:        {final_rec.get('risk_level', 'N/A')}")
        lines.append(f"  Confidence:        {final_rec.get('confidence', 0):.0%}")
        lines.append(f"  Approved Size:     {final_rec.get('approved_position_size', 0)*100:.0f}% of requested")
        lines.append(f"  Required Stop:     {final_rec.get('required_stop_loss', 0)}%")
        lines.append(f"  Senior Approval:   {'Required' if final_rec.get('requires_senior_approval') else 'Not Required'}")
        lines.append("")
        
        # Advisor perspectives
        lines.append("  📊 ADVISOR PERSPECTIVES:")
        for advisor_type in ["risky", "neutral", "safe"]:
            advisor = advisors.get(advisor_type, {})
            if advisor:
                emoji = {"risky": "🔥", "neutral": "⚖️", "safe": "🛡️"}.get(advisor_type, "•")
                lines.append(f"     {emoji} {advisor_type.upper():8} → {advisor.get('recommendation', 'N/A'):20} "
                           f"(Risk: {advisor.get('risk_score', 0):.2f}, Adj: {advisor.get('position_adjustment', 1.0):.1f}x)")
        lines.append("")
        
        # Key risks
        key_risks = final_rec.get("key_risks_identified", [])
        if key_risks:
            lines.append("  ⚠️ KEY RISKS:")
            for risk in key_risks[:3]:
                lines.append(f"     • {risk}")
            lines.append("")
        
        # Mitigation strategies
        mitigations = final_rec.get("mitigation_strategies", [])
        if mitigations:
            lines.append("  ✓ MITIGATION STRATEGIES:")
            for strategy in mitigations[:3]:
                lines.append(f"     • {strategy}")
            lines.append("")
        
        # Approval conditions
        conditions = final_rec.get("approval_conditions", [])
        if conditions:
            lines.append("  📋 APPROVAL CONDITIONS:")
            for condition in conditions[:3]:
                lines.append(f"     • {condition}")
            lines.append("")
    
    lines.append("═" * 80)
    return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="TradingAgents - Multi-Agent Financial Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py AAPL                    Full pipeline (Analysts + Researchers)
  python main.py AAPL --quick            Quick mode (Analysts only)
  python main.py AAPL MSFT GOOGL         Analyze multiple stocks
  python main.py --visualize             Show workflow graph
  python main.py AAPL --output json      Output as JSON
  python main.py AAPL -v                 Verbose mode

Environment:
  GROQ_API_KEY    Required. Get from https://console.groq.com/keys
        """,
    )
    
    parser.add_argument(
        "tickers",
        nargs="*",
        help="Stock ticker symbols to analyze (e.g., AAPL MSFT)",
    )
    parser.add_argument(
        "--visualize", "-g",
        action="store_true",
        help="Visualize the workflow graph",
    )
    parser.add_argument(
        "--output", "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--save-graph",
        type=str,
        metavar="PATH",
        help="Save workflow graph to specified path",
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Quick mode: run analyst team only (skip researcher debate)",
    )
    
    args = parser.parse_args()
    
    # Setup environment
    if not setup_environment():
        return 1
    
    # Handle visualization
    if args.visualize or args.save_graph:
        visualize_graph(args.save_graph)
        if not args.tickers:
            return 0
    
    # Require tickers for analysis
    if not args.tickers:
        parser.print_help()
        print("\n❌ Error: No tickers provided. Use --visualize to see the graph.")
        return 1
    
    # Analyze each ticker
    results = []
    for ticker in args.tickers:
        ticker = ticker.strip().upper()
        result = analyze_ticker(
            ticker=ticker,
            verbose=args.verbose,
            output_format=args.output,
            quick_mode=args.quick,
        )
        results.append(result)
        
        # Output result
        if args.output == "json":
            print(json.dumps(result, indent=2, default=str))
        else:
            print(format_result_text(result))
    
    # Summary for multiple tickers
    if len(results) > 1 and args.output == "text":
        print("\n" + "═" * 80)
        print("  PORTFOLIO SUMMARY")
        print("═" * 80)
        for r in results:
            if "error" not in r:
                action = r.get('action') or r.get('final_signal', 'N/A')
                print(f"  {r.get('ticker', 'N/A'):8} {action:12} ({r.get('confidence', 0):.0%})")
        print("═" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
