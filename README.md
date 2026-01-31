# TradingAgents

A production-ready multi-agent financial analysis and trading system powered by LangGraph and Groq LLM.

## Features

- **5-Stage Pipeline**: Data → Analysts → Researchers → CIO → Traders
- **Multi-Agent Architecture**: Specialized agents for analysis, research, and execution
- **Bull vs Bear Debate**: Researchers engage in multi-round debates for balanced insights
- **Feedback-Driven Trading**: Iterative decision refinement with scoring
- **Human-in-the-Loop**: Manual approval before trade execution
- **Real-Time Data**: Live news and stock data integration
- **Graph Visualization**: Visual workflow representation
- **Production CLI**: Full command-line interface with multiple modes

## Architecture

```
┌──────────────┐    ┌───────────────┐    ┌─────────────────┐    ┌────────────┐    ┌─────────────┐
│  STAGE 1     │    │   STAGE 2     │    │    STAGE 3      │    │  STAGE 4   │    │  STAGE 5    │
│  Data Fetch  │───▶│ Analyst Team  │───▶│ Researcher Team │───▶│    CIO     │───▶│ Trader Team │
│              │    │ (4 Analysts)  │    │ (Bull vs Bear)  │    │  Decision  │    │ (Execution) │
└──────────────┘    └───────────────┘    └─────────────────┘    └────────────┘    └─────────────┘
```

### Stage 2: Analyst Team
```
┌────────────┐  ┌──────────────┐  ┌─────────────┐  ┌─────────────┐
│    News    │  │ Fundamentals │  │  Sentiment  │  │  Technical  │
│   Analyst  │  │   Analyst    │  │   Analyst   │  │   Analyst   │
└─────┬──────┘  └──────┬───────┘  └──────┬──────┘  └──────┬──────┘
      └────────────────┴─────────────────┴─────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   Consolidated Report  │
                    └────────────────────────┘
```

### Stage 3: Researcher Team
```
┌─────────────────┐         ┌─────────────────┐
│     BULLISH     │◄───────►│     BEARISH     │
│   RESEARCHER    │ DEBATE  │   RESEARCHER    │
└─────────────────┘ (2 rds) └─────────────────┘
         │                           │
         └───────────┬───────────────┘
                     ▼
          ┌──────────────────┐
          │    Synthesized   │
          │  Research Report │
          └──────────────────┘
```

### Stage 5: Trader Team
```
┌─────────────┐    ┌──────────────┐    ┌───────────────┐    ┌────────────┐
│   TRADER    │───▶│    RISK      │───▶│   PORTFOLIO   │───▶│  EXECUTOR  │
│   AGENT     │    │   MANAGER    │    │   MANAGER     │    │            │
└─────────────┘    └──────────────┘    └───────────────┘    └──────┬─────┘
      ▲                   │                                        │
      │    FEEDBACK       │                                        ▼
      │    LOOP           │                              ┌─────────────────┐
      └───────────────────┘                              │  HUMAN APPROVAL │
      (Max 3 iterations)                                 └─────────────────┘
```

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd hekronpy

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirement.txt
```

## Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=gsk_your_api_key_here
```

Get your Groq API key from: https://console.groq.com/keys

## Usage

### Command Line

```bash
# Full pipeline (Analysts + Researchers + CIO + Traders)
python main.py AAPL

# Quick mode (Analysts only - faster)
python main.py AAPL --quick

# Analyze multiple stocks
python main.py AAPL MSFT GOOGL

# Visualize the workflow graph
python main.py --visualize

# Output as JSON
python main.py AAPL --output json

# Verbose mode
python main.py AAPL -v

# Save graph to specific path
python main.py --save-graph my_graph.png
```

### Python API

```python
from pipeline import TradingPipeline

# Full pipeline with all stages
pipeline = TradingPipeline(
    max_debate_rounds=2,      # Researcher debate rounds
    max_trade_iterations=3,   # Trader feedback iterations
    require_human_approval=True,
)

result = pipeline.run(
    ticker="AAPL",
    available_capital=100000,
    risk_tolerance="moderate",  # conservative, moderate, aggressive
)

print(f"Action: {result['action']}")
print(f"Confidence: {result['confidence']:.1%}")
```

### Quick Analysis (Analysts Only)

```python
from analysts import AnalystsTeam
from data import MarketDataFetcher

fetcher = MarketDataFetcher()
team = AnalystsTeam()

market_data = fetcher.fetch_market_data("AAPL")
result = team.analyze(ticker="AAPL", market_data=market_data)

print(f"Signal: {result['final_signal']}")
```

### Flask API

```bash
python -m data.api
```

Endpoints:
- `GET /api/news?keyword=AAPL&days=7` - Fetch news
- `GET /api/stock/AAPL` - Get stock data with indicators
- `GET /api/market-data/AAPL` - Full market data for analysis
- `GET /api/health` - Health check

## Project Structure

```
hekronpy/
├── main.py                 # Production CLI entry point
├── requirement.txt         # Dependencies
├── .env                    # Environment variables (create this)
├── README.md
│
├── analysts/               # Stage 2: Analyst Team
│   ├── __init__.py
│   ├── state.py            # Shared state definitions
│   ├── news_analyst.py     # News-driven analysis
│   ├── fundamentals_analyst.py
│   ├── sentiment_analyst.py
│   ├── technical_analyst.py
│   └── team.py             # LangGraph coordinator
│
├── researchers/            # Stage 3: Researcher Team
│   ├── __init__.py
│   ├── state.py            # Research state definitions
│   ├── bullish_researcher.py   # Bull case arguments
│   ├── bearish_researcher.py   # Bear case arguments
│   ├── debate.py           # Debate coordinator
│   └── team.py             # LangGraph workflow
│
├── traders/                # Stage 5: Trader Team
│   ├── __init__.py
│   ├── state.py            # Trade state, orders, scoring
│   ├── trader_agent.py     # Core decision-making
│   ├── risk_manager.py     # Risk assessment + feedback scoring
│   ├── portfolio_manager.py    # Position sizing
│   ├── execution.py        # Human-in-the-loop approval
│   └── team.py             # Feedback loop workflow
│
├── pipeline/               # Stage 4: CIO + Orchestration
│   ├── __init__.py
│   └── trading_pipeline.py # Full 5-stage pipeline
│
├── data/                   # Stage 1: Data Fetchers
│   ├── __init__.py
│   ├── news_scraper.py     # MoneyControl news scraper
│   ├── stock_data.py       # yfinance + indicators
│   ├── market_data.py      # Combined fetcher
│   └── api.py              # Flask API
│
└── workflow_graph.png      # Generated workflow visualization
```

## Agent Teams

### Analyst Team (Stage 2)

| Agent | Role | Data Sources |
|-------|------|--------------|
| **News Analyst** | Analyzes market news impact | News articles, headlines |
| **Fundamentals Analyst** | Evaluates financial health | P/E, EPS, balance sheet |
| **Sentiment Analyst** | Assesses market psychology | Price action, news tone |
| **Technical Analyst** | Price patterns & indicators | RSI, MACD, SMA, volume |

### Researcher Team (Stage 3)

| Agent | Role | Output |
|-------|------|--------|
| **Bullish Researcher** | Builds investment case | Growth catalysts, opportunities |
| **Bearish Researcher** | Identifies risks | Challenges, downsides |
| **Debate Coordinator** | Manages multi-round debate | Synthesized research report |

### Trader Team (Stage 5)

| Agent | Role | Output |
|-------|------|--------|
| **Trader Agent** | Core decision-making | Order type, sizing, timing |
| **Risk Manager** | Scores decisions | Risk/Reward/Timing/Alignment scores |
| **Portfolio Manager** | Optimizes allocation | Position sizing, concentration limits |
| **Trade Executor** | Handles approval flow | Human-in-the-loop, order execution |

## Key Configurations

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_debate_rounds` | 2 | Researcher debate iterations |
| `max_trade_iterations` | 3 | Trader feedback loop limit |
| `score_threshold` | 0.6 | Minimum score to proceed |
| `require_human_approval` | True | Manual trade approval |
| `risk_tolerance` | "moderate" | conservative / moderate / aggressive |

## Output Example

### Full Pipeline Output
```
┌──────────────────────────────────────────────────────────────────────────────┐
│  📊 FINAL INVESTMENT DECISION: AAPL                                          │
├──────────────────────────────────────────────────────────────────────────────┤
│  Action:         BUY                                                         │
│  Confidence:     72.0%                                                       │
│  Position Size:  HALF                                                        │
│  Time Horizon:   MEDIUM                                                      │
└──────────────────────────────────────────────────────────────────────────────┘

════════════════════════════════════════════════════════════════════════════════
  📚 RESEARCHER TEAM DEBATE SUMMARY
════════════════════════════════════════════════════════════════════════════════
  🐂 BULL CASE: Strong brand, competitive moat, solid balance sheet...
  🐻 BEAR CASE: High valuation, competitive pressures, concentration risk...
  ✓ CONSENSUS: Strong fundamentals, market leader position
  ✗ DISAGREEMENTS: Valuation metrics, growth trajectory

════════════════════════════════════════════════════════════════════════════════
  👥 ANALYST TEAM SIGNALS
════════════════════════════════════════════════════════════════════════════════
    NEWS               BUY          (65%)
    FUNDAMENTALS       HOLD         (60%)
    SENTIMENT          BUY          (70%)
    TECHNICAL          BUY          (68%)

════════════════════════════════════════════════════════════════════════════════
  💹 TRADE EXECUTION
════════════════════════════════════════════════════════════════════════════════
  Action:          BUY
  Position Size:   15.0% of capital
  Stop Loss:       5%
  Take Profit:     12%

  📊 DECISION QUALITY SCORE:
     Overall:    0.72/1.0
     Risk:       0.35
     Reward:     0.78
     Iterations: 2

  Execution Status: AWAITING_HUMAN_APPROVAL
════════════════════════════════════════════════════════════════════════════════
```

## Dependencies

- **langgraph** - Workflow orchestration
- **langchain-groq** - Groq LLM integration
- **yfinance** - Stock data
- **beautifulsoup4** - News scraping
- **flask** - REST API
- **pandas/numpy** - Data processing

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key for LLM |

## License

MIT
