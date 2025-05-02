"""Core module for fetching stock market data from Yahoo Finance API."""

from typing import Optional, Dict, Any, List
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting constants
RATE_LIMIT_DELAY = 0.5  # seconds between API calls
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds between retries


def rate_limit(func):
    """Decorator to implement rate limiting for API calls."""
    last_call_time = 0

    @wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal last_call_time
        current_time = time.time()
        time_since_last_call = current_time - last_call_time

        if time_since_last_call < RATE_LIMIT_DELAY:
            sleep_time = RATE_LIMIT_DELAY - time_since_last_call
            time.sleep(sleep_time)

        last_call_time = time.time()
        return func(*args, **kwargs)

    return wrapper


def retry_on_failure(func):
    """Decorator to implement retry logic for API calls."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {str(e)}. Retrying..."
                    )
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"All {MAX_RETRIES} attempts failed")
                    raise last_exception

    return wrapper


class StockDataFetcher:
    """Core class for fetching stock market data from Yahoo Finance."""

    def __init__(self):
        """Initialize the StockDataFetcher."""
        self._session = yf.Ticker(
            "AAPL"
        )  # Initialize with any symbol to create session

    @rate_limit
    @retry_on_failure
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
            DataFrame containing historical stock data with columns:
            - Open: Opening price
            - High: Highest price
            - Low: Lowest price
            - Close: Closing price
            - Volume: Trading volume
            - Dividends: Dividend payments
            - Stock Splits: Stock split events

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

            # Ensure all required columns are present
            required_columns = ["Open", "High", "Low", "Close", "Volume"]
            missing_columns = [
                col for col in required_columns if col not in data.columns
            ]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")

            return data
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            raise ValueError(f"Error fetching historical data for {symbol}: {str(e)}")

    @rate_limit
    @retry_on_failure
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

            # Try different price fields
            price_fields = ["currentPrice", "regularMarketPrice", "previousClose"]
            for field in price_fields:
                if field in current_data and current_data[field] is not None:
                    return float(current_data[field])

            raise ValueError(f"Could not find current price for {symbol}")
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {str(e)}")
            raise ValueError(f"Error fetching current price for {symbol}: {str(e)}")

    @rate_limit
    @retry_on_failure
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get detailed information about a stock.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')

        Returns:
            Dictionary containing stock information including:
            - Basic info (name, symbol, sector, industry)
            - Financial metrics (market cap, P/E ratio, etc.)
            - Trading information (volume, average volume, etc.)

        Raises:
            ValueError: If the symbol is invalid or info cannot be fetched
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info:
                raise ValueError(f"No information found for symbol {symbol}")

            # Validate required fields
            required_fields = ["symbol", "longName", "marketCap"]
            missing_fields = [field for field in required_fields if field not in info]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")

            return info
        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {str(e)}")
            raise ValueError(f"Error fetching info for {symbol}: {str(e)}")

    @rate_limit
    @retry_on_failure
    def get_market_summary(self, symbols: List[str]) -> pd.DataFrame:
        """
        Get a summary of market data for multiple symbols.

        Args:
            symbols: List of stock symbols

        Returns:
            DataFrame containing market summary data with columns:
            - current_price: Current trading price
            - day_high: Highest price of the day
            - day_low: Lowest price of the day
            - volume: Trading volume
            - market_cap: Market capitalization
            - 52_week_high: 52-week high price
            - 52_week_low: 52-week low price

        Raises:
            ValueError: If any symbol is invalid or data cannot be fetched
        """
        try:
            data = {}
            for symbol in symbols:
                ticker = yf.Ticker(symbol)
                info = ticker.info

                # Validate required fields
                required_fields = [
                    "currentPrice",
                    "regularMarketPrice",
                    "dayHigh",
                    "dayLow",
                    "volume",
                    "marketCap",
                    "fiftyTwoWeekHigh",
                    "fiftyTwoWeekLow",
                ]
                missing_fields = [
                    field for field in required_fields if field not in info
                ]
                if missing_fields:
                    raise ValueError(
                        f"Missing required fields for {symbol}: {missing_fields}"
                    )

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
            logger.error(f"Error fetching market summary: {str(e)}")
            raise ValueError(f"Error fetching market summary: {str(e)}")
