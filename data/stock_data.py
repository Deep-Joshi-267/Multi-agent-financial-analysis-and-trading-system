"""Stock data fetcher with technical indicators using yfinance."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    yf = None


class StockDataFetcher:
    """Fetches stock data and calculates technical indicators for LangGraph agents."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        if yf is None:
            raise ImportError("yfinance is required. Install with: pip install yfinance")

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"[StockData] {msg}")

    def get_historical_data(
        self,
        symbol: str,
        days: int = 365,
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data."""
        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.today()
            start_date = end_date - timedelta(days=days)
            hist = ticker.history(start=start_date, end=end_date, interval="1d")
            self._log(f"Fetched {len(hist)} days of data for {symbol}")
            return hist
        except Exception as e:
            self._log(f"Error fetching {symbol}: {e}")
            return pd.DataFrame()

    def get_company_info(self, symbol: str) -> dict:
        """Get comprehensive company fundamentals for financial cards."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}

            # Helper for clean ratio formatting
            def _pct(val):
                return f"{val * 100:.2f}%" if val is not None and not np.isnan(val) else "—"

            def _fmt_val(val, prefix="", suffix=""):
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    return "—"
                if isinstance(val, (int, float)):
                    if abs(val) >= 1e12:
                        return f"{prefix}{val / 1e12:.2f}T{suffix}"
                    elif abs(val) >= 1e9:
                        return f"{prefix}{val / 1e9:.2f}B{suffix}"
                    elif abs(val) >= 1e7:
                        return f"{prefix}{val / 1e7:.2f}Cr{suffix}"
                    elif abs(val) >= 1e5:
                        return f"{prefix}{val / 1e5:.2f}L{suffix}"
                    return f"{prefix}{val:.2f}{suffix}"
                return str(val)

            # Extract Financial Statements for ratios not directly in ticker.info
            roe = info.get("returnOnEquity")
            roce = None
            interest_coverage = None
            op_cashflow = info.get("operatingCashflow")
            free_cashflow = info.get("freeCashflow")

            try:
                fin = ticker.financials
                bs = ticker.balance_sheet
                cf = ticker.cashflow

                if cf is not None and not cf.empty:
                    if op_cashflow is None and "Operating Cash Flow" in cf.index:
                        op_cashflow = cf.loc["Operating Cash Flow"].iloc[0]
                    if free_cashflow is None and "Free Cash Flow" in cf.index:
                        free_cashflow = cf.loc["Free Cash Flow"].iloc[0]

                if fin is not None and not fin.empty and bs is not None and not bs.empty:
                    ebit = fin.loc["EBIT"].iloc[0] if "EBIT" in fin.index else (fin.loc["Operating Income"].iloc[0] if "Operating Income" in fin.index else None)
                    interest_exp = abs(fin.loc["Interest Expense"].iloc[0]) if "Interest Expense" in fin.index else None
                    if ebit and interest_exp and interest_exp > 0:
                        interest_coverage = round(ebit / interest_exp, 2)

                    total_assets = bs.loc["Total Assets"].iloc[0] if "Total Assets" in bs.index else None
                    curr_liab = bs.loc["Current Liabilities"].iloc[0] if "Current Liabilities" in bs.index else None
                    if ebit and total_assets and curr_liab:
                        cap_employed = total_assets - curr_liab
                        if cap_employed > 0:
                            roce = (ebit / cap_employed)

                    if roe is None and "Net Income" in fin.index and "Stockholders Equity" in bs.index:
                        net_inc = fin.loc["Net Income"].iloc[0]
                        equity = bs.loc["Stockholders Equity"].iloc[0]
                        if equity and equity > 0:
                            roe = net_inc / equity
            except Exception:
                pass

            rev_growth = info.get("revenueGrowth")
            earn_growth = info.get("earningsGrowth") or info.get("earningsQuarterlyGrowth")
            op_margin = info.get("operatingMargins")
            prof_margin = info.get("profitMargins")
            d_e = info.get("debtToEquity")
            pe = info.get("trailingPE") or info.get("forwardPE")
            pb = info.get("priceToBook")
            ev_ebitda = info.get("enterpriseToEbitda")
            mcap = info.get("marketCap")

            return {
                "name": info.get("shortName", symbol),
                "symbol": symbol,
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "market_cap": _fmt_val(mcap, prefix="Rs. ") if ".NS" in symbol or ".BO" in symbol else _fmt_val(mcap, prefix="$"),
                "revenue_growth": _pct(rev_growth),
                "earnings_growth": _pct(earn_growth),
                "eps_growth": _pct(earn_growth),  # Proxy YoY growth
                "roe": _pct(roe),
                "roce": _pct(roce),
                "operating_margin": _pct(op_margin),
                "profit_margin": _pct(prof_margin),
                "debt_to_equity": f"{d_e:.2f}" if d_e is not None else "—",
                "interest_coverage": f"{interest_coverage:.2f}x" if interest_coverage is not None else "—",
                "pe_ratio": f"{pe:.2f}" if pe is not None else "—",
                "price_to_book": f"{pb:.2f}" if pb is not None else "—",
                "ev_ebitda": f"{ev_ebitda:.2f}" if ev_ebitda is not None else "—",
                "operating_cashflow": _fmt_val(op_cashflow, prefix="Rs. ") if ".NS" in symbol or ".BO" in symbol else _fmt_val(op_cashflow, prefix="$"),
                "free_cashflow": _fmt_val(free_cashflow, prefix="Rs. ") if ".NS" in symbol or ".BO" in symbol else _fmt_val(free_cashflow, prefix="$"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "avg_volume": info.get("averageVolume"),
                "description": info.get("longBusinessSummary", ""),
            }
        except Exception as e:
            self._log(f"Error getting info for {symbol}: {e}")
            return {"symbol": symbol, "error": str(e)}

    def calculate_sma(self, prices: pd.Series, window: int) -> pd.Series:
        """Calculate Simple Moving Average."""
        return prices.rolling(window=window).mean()

    def calculate_ema(self, prices: pd.Series, span: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return prices.ewm(span=span, adjust=False).mean()

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> Dict[str, pd.Series]:
        """Calculate MACD indicator."""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return {
            "macd_line": macd_line,
            "signal_line": signal_line,
            "histogram": histogram,
        }

    def calculate_bollinger_bands(
        self,
        prices: pd.Series,
        window: int = 20,
        num_std: int = 2,
    ) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands."""
        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)

        return {
            "upper_band": upper,
            "middle_band": sma,
            "lower_band": lower,
        }

    def get_technical_indicators(self, symbol: str, days: int = 365) -> dict:
        """Get all technical indicators for a symbol."""
        hist = self.get_historical_data(symbol, days)
        if hist.empty:
            return {"error": "No data available"}

        closes = hist["Close"].dropna()
        latest_price = float(closes.iloc[-1]) if len(closes) > 0 else 0

        # Calculate indicators
        rsi = self.calculate_rsi(closes)
        macd = self.calculate_macd(closes)
        bb = self.calculate_bollinger_bands(closes)

        # Get latest values
        latest_rsi = float(rsi.iloc[-1]) if len(rsi) > 0 and not np.isnan(rsi.iloc[-1]) else None
        latest_macd = float(macd["macd_line"].iloc[-1]) if len(macd["macd_line"]) > 0 else None
        latest_signal = float(macd["signal_line"].iloc[-1]) if len(macd["signal_line"]) > 0 else None

        # Moving averages
        sma_10 = float(self.calculate_sma(closes, 10).iloc[-1]) if len(closes) >= 10 else None
        sma_20 = float(self.calculate_sma(closes, 20).iloc[-1]) if len(closes) >= 20 else None
        sma_50 = float(self.calculate_sma(closes, 50).iloc[-1]) if len(closes) >= 50 else None
        sma_200 = float(self.calculate_sma(closes, 200).iloc[-1]) if len(closes) >= 200 else None

        # Momentum
        momentum_5d = ((closes.iloc[-1] - closes.iloc[-5]) / closes.iloc[-5] * 100) if len(closes) >= 5 else None
        momentum_20d = ((closes.iloc[-1] - closes.iloc[-20]) / closes.iloc[-20] * 100) if len(closes) >= 20 else None

        return {
            "current_price": latest_price,
            "rsi_14": latest_rsi,
            "macd": latest_macd,
            "macd_signal": latest_signal,
            "sma_10": sma_10,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "sma_200": sma_200,
            "momentum_5d": momentum_5d,
            "momentum_20d": momentum_20d,
            "bb_upper": float(bb["upper_band"].iloc[-1]) if not np.isnan(bb["upper_band"].iloc[-1]) else None,
            "bb_lower": float(bb["lower_band"].iloc[-1]) if not np.isnan(bb["lower_band"].iloc[-1]) else None,
        }

    def get_price_history(self, symbol: str, days: int = 60) -> List[float]:
        """Get list of closing prices for LangGraph technical analyst."""
        hist = self.get_historical_data(symbol, days)
        if hist.empty:
            return []
        return hist["Close"].dropna().tolist()

    def get_volume_history(self, symbol: str, days: int = 60) -> List[int]:
        """Get list of volumes for LangGraph technical analyst."""
        hist = self.get_historical_data(symbol, days)
        if hist.empty:
            return []
        return hist["Volume"].dropna().astype(int).tolist()

    def get_financial_reports(self, symbol: str) -> dict:
        """Get financial report data formatted for the 100-point fundamental analysis engine."""
        info = self.get_company_info(symbol)

        return {
            "Sector": info.get("sector", "N/A"),
            "Market Cap": info.get("market_cap", "N/A"),
            "Revenue Growth": info.get("revenue_growth", "—"),
            "Earnings Growth": info.get("earnings_growth", "—"),
            "EPS Growth": info.get("eps_growth", "—"),
            "ROE": info.get("roe", "—"),
            "ROCE": info.get("roce", "—"),
            "Operating Margin": info.get("operating_margin", "—"),
            "Profit Margin": info.get("profit_margin", "—"),
            "Debt/Equity": info.get("debt_to_equity", "—"),
            "Interest Coverage": info.get("interest_coverage", "—"),
            "P/E": info.get("pe_ratio", "—"),
            "P/B": info.get("price_to_book", "—"),
            "EV/EBITDA": info.get("ev_ebitda", "—"),
            "Operating Cash Flow": info.get("operating_cashflow", "—"),
            "Free Cash Flow": info.get("free_cashflow", "—"),
        }
