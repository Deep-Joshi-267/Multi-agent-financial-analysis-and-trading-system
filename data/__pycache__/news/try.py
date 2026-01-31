"""
TradingAgents - Complete Integration Demo
Fetches real market data and runs through the LangGraph analysts team.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from dotenv import load_dotenv

load_dotenv()

from data import MarketDataFetcher
from analysts import AnalystsTeam


def run_analysis(ticker: str, verbose: bool = True):
    """
    Run full trading analysis pipeline.
    
    Args:
        ticker: Stock symbol (e.g., "AAPL", "TCS.NS", "RELIANCE.NS")
        verbose: Print progress updates
    """
    print(f"\n{'='*60}")
    print(f"  TRADING AGENTS ANALYSIS: {ticker}")
    print(f"{'='*60}\n")

    # Step 1: Fetch market data
    if verbose:
        print("[1/3] Fetching market data...")
    
    fetcher = MarketDataFetcher(verbose=verbose)
    market_data = fetcher.fetch_market_data(
        ticker=ticker,
        news_days=3,
        news_limit=8,
        price_days=60,
    )

    if verbose:
        print(f"  - Current price: ${market_data.get('current_price', 'N/A')}")
        print(f"  - News articles: {len(market_data.get('news_articles', []))}")
        print(f"  - Price history: {len(market_data.get('price_history', []))} days")

    # Step 2: Run analysts team
    if verbose:
        print("\n[2/3] Running analysts team...")

    team = AnalystsTeam()
    result = team.analyze(ticker=ticker, market_data=market_data)

    # Step 3: Display results
    if verbose:
        print("\n[3/3] Analysis complete!")

    print(f"\n{'─'*60}")
    print(f"  CONSOLIDATED RECOMMENDATION")
    print(f"{'─'*60}")
    print(f"  Signal:        {result.get('final_signal', 'N/A')}")
    print(f"  Confidence:    {result.get('confidence', 0):.1%}")
    print(f"  Position Size: {result.get('position_size', 'N/A')}")
    print(f"  Time Horizon:  {result.get('time_horizon', 'N/A')}")
    print(f"{'─'*60}")

    print(f"\nReasoning:\n{result.get('reasoning', 'N/A')}")

    print(f"\nAnalyst Agreement:\n{result.get('analyst_agreement', 'N/A')}")

    if result.get("risk_factors"):
        print(f"\nRisk Factors:")
        for risk in result["risk_factors"]:
            print(f"  • {risk}")

    # Show individual analyst signals
    individual = result.get("individual_reports", {})
    if individual:
        print(f"\n{'─'*60}")
        print("  INDIVIDUAL ANALYST SIGNALS")
        print(f"{'─'*60}")
        for name, report in individual.items():
            if report:
                sig = report.get("signal", "N/A")
                conf = report.get("confidence", 0)
                print(f"  {name.upper():15} {sig:6} ({conf:.0%})")

    return result


def main():
    """Main entry point."""
    # Default ticker or from command line
    ticker = sys.argv[1].strip() if len(sys.argv) > 1 else "AAPL"
    
    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        print("WARNING: GROQ_API_KEY not set. Set it in .env file or environment.")
        print("Example: GROQ_API_KEY=gsk_...")
        return

    result = run_analysis(ticker)
    return result


if __name__ == "__main__":
    main()
