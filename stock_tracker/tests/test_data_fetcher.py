"""Test suite for the StockDataFetcher class."""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import time
from stock_tracker.utils.data_fetcher import (
    StockDataFetcher,
    rate_limit,
    retry_on_failure,
)


@pytest.fixture
def fetcher():
    """Create a StockDataFetcher instance for testing."""
    return StockDataFetcher()


@pytest.fixture
def test_symbols():
    """Return a list of test stock symbols."""
    return ["AAPL", "MSFT", "GOOGL"]


@pytest.fixture
def mock_historical_data():
    """Create mock historical data DataFrame."""
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0],
            "High": [105.0, 106.0, 107.0],
            "Low": [95.0, 96.0, 97.0],
            "Close": [103.0, 104.0, 105.0],
            "Volume": [1000000, 1100000, 1200000],
            "Dividends": [0.0, 0.0, 0.0],
            "Stock Splits": [0.0, 0.0, 0.0],
        },
        index=pd.date_range(start="2024-01-01", periods=3),
    )


@pytest.fixture
def mock_stock_info():
    """Create mock stock info dictionary."""
    return {
        "symbol": "AAPL",
        "longName": "Apple Inc.",
        "marketCap": 2_000_000_000_000,
        "currentPrice": 150.0,
        "regularMarketPrice": 150.0,
        "dayHigh": 155.0,
        "dayLow": 145.0,
        "volume": 50_000_000,
        "fiftyTwoWeekHigh": 200.0,
        "fiftyTwoWeekLow": 100.0,
    }


def test_rate_limit_decorator():
    """Test that rate limiting decorator enforces delay between calls."""

    @rate_limit
    def test_func():
        return time.time()

    # First call
    start_time = test_func()
    # Second call should be delayed
    end_time = test_func()

    # Check that at least the minimum delay has passed
    assert end_time - start_time >= 0.5


def test_retry_on_failure_decorator():
    """Test that retry decorator attempts multiple times before failing."""
    attempts = 0

    @retry_on_failure
    def failing_func():
        nonlocal attempts
        attempts += 1
        raise ValueError("Test error")

    with pytest.raises(ValueError):
        failing_func()

    assert attempts == 3  # Should try 3 times before giving up


@patch("yfinance.Ticker")
def test_get_historical_data_success(mock_ticker, fetcher, mock_historical_data):
    """Test successful historical data retrieval."""
    mock_ticker.return_value.history.return_value = mock_historical_data

    data = fetcher.get_historical_data("AAPL", period="5d")

    assert isinstance(data, pd.DataFrame)
    assert not data.empty
    assert all(
        col in data.columns for col in ["Open", "High", "Low", "Close", "Volume"]
    )


@patch("yfinance.Ticker")
def test_get_historical_data_missing_columns(mock_ticker, fetcher):
    """Test handling of historical data with missing columns."""
    mock_ticker.return_value.history.return_value = pd.DataFrame(
        {
            "Open": [100.0],
            "High": [105.0],
            # Missing 'Low', 'Close', 'Volume'
        }
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        fetcher.get_historical_data("AAPL")


@patch("yfinance.Ticker")
def test_get_current_price_success(mock_ticker, fetcher):
    """Test successful current price retrieval."""
    mock_ticker.return_value.info = {
        "currentPrice": 150.0,
        "regularMarketPrice": 150.0,
        "previousClose": 149.0,
    }

    price = fetcher.get_current_price("AAPL")
    assert isinstance(price, float)
    assert price == 150.0


@patch("yfinance.Ticker")
def test_get_current_price_no_price_fields(mock_ticker, fetcher):
    """Test handling of missing price fields."""
    mock_ticker.return_value.info = {}

    with pytest.raises(ValueError, match="Could not find current price"):
        fetcher.get_current_price("AAPL")


@patch("yfinance.Ticker")
def test_get_stock_info_success(mock_ticker, fetcher, mock_stock_info):
    """Test successful stock info retrieval."""
    mock_ticker.return_value.info = mock_stock_info

    info = fetcher.get_stock_info("AAPL")
    assert isinstance(info, dict)
    assert all(field in info for field in ["symbol", "longName", "marketCap"])


@patch("yfinance.Ticker")
def test_get_stock_info_missing_fields(mock_ticker, fetcher):
    """Test handling of stock info with missing required fields."""
    mock_ticker.return_value.info = {
        "symbol": "AAPL"
        # Missing 'longName' and 'marketCap'
    }

    with pytest.raises(ValueError, match="Missing required fields"):
        fetcher.get_stock_info("AAPL")


@patch("yfinance.Ticker")
def test_get_market_summary_success(
    mock_ticker, fetcher, mock_stock_info, test_symbols
):
    """Test successful market summary retrieval."""
    mock_ticker.return_value.info = mock_stock_info

    summary = fetcher.get_market_summary(test_symbols)
    assert isinstance(summary, pd.DataFrame)
    assert not summary.empty
    assert all(symbol in summary.index for symbol in test_symbols)
    assert all(
        col in summary.columns
        for col in [
            "current_price",
            "day_high",
            "day_low",
            "volume",
            "market_cap",
            "52_week_high",
            "52_week_low",
        ]
    )


@patch("yfinance.Ticker")
def test_get_market_summary_missing_fields(mock_ticker, fetcher, test_symbols):
    """Test handling of market summary with missing required fields."""
    mock_ticker.return_value.info = {
        "symbol": "AAPL"
        # Missing required fields
    }

    with pytest.raises(ValueError, match="Missing required fields"):
        fetcher.get_market_summary(test_symbols)
