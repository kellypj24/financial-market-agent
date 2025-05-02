"""Module for fetching stock market data using yfinance."""

from typing import Optional, Dict, Any
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


class StockDataFetcher:
    """Class for fetching and managing stock market data."""

    def __init__(self):
        """Initialize the StockDataFetcher."""
        self._cache: Dict[str, pd.DataFrame] = {}

    def get_historical_data(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch historical stock data for a given symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            period: Time period to fetch (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval: Data interval (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)

        Returns:
            DataFrame containing historical stock data

        Raises:
            ValueError: If the symbol is invalid or data cannot be fetched
        """
        try:
            ticker = yf.Ticker(symbol)

            if start_date and end_date:
                data = ticker.history(start=start_date, end=end_date, interval=interval)
            else:
                data = ticker.history(period=period, interval=interval)

            if data.empty:
                raise ValueError(f"No data found for symbol {symbol}")

            return data
        except Exception as e:
            raise ValueError(f"Error fetching data for {symbol}: {str(e)}")

    def get_current_price(self, symbol: str) -> float:
        """
        Get the current price for a given stock symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')

        Returns:
            Current stock price

        Raises:
            ValueError: If the symbol is invalid or price cannot be fetched
        """
        try:
            ticker = yf.Ticker(symbol)
            current_data = ticker.info
            if "currentPrice" in current_data:
                return current_data["currentPrice"]
            elif "regularMarketPrice" in current_data:
                return current_data["regularMarketPrice"]
            else:
                raise ValueError(f"Could not find current price for {symbol}")
        except Exception as e:
            raise ValueError(f"Error fetching current price for {symbol}: {str(e)}")

    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get detailed information about a stock.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')

        Returns:
            Dictionary containing stock information

        Raises:
            ValueError: If the symbol is invalid or info cannot be fetched
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if not info:
                raise ValueError(f"No information found for symbol {symbol}")
            return info
        except Exception as e:
            raise ValueError(f"Error fetching info for {symbol}: {str(e)}")

    def get_market_summary(self, symbols: list[str]) -> pd.DataFrame:
        """
        Get a summary of market data for multiple symbols.

        Args:
            symbols: List of stock symbols

        Returns:
            DataFrame containing market summary data

        Raises:
            ValueError: If any symbol is invalid or data cannot be fetched
        """
        try:
            data = {}
            for symbol in symbols:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                data[symbol] = {
                    "current_price": info.get(
                        "currentPrice", info.get("regularMarketPrice")
                    ),
                    "day_high": info.get("dayHigh"),
                    "day_low": info.get("dayLow"),
                    "volume": info.get("volume"),
                    "market_cap": info.get("marketCap"),
                    "52_week_high": info.get("fiftyTwoWeekHigh"),
                    "52_week_low": info.get("fiftyTwoWeekLow"),
                }
            return pd.DataFrame(data).T
        except Exception as e:
            raise ValueError(f"Error fetching market summary: {str(e)}")
