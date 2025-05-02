"""Test suite for the StockDataFetcher class."""

import pytest
from stock_tracker.utils.data_fetcher import StockDataFetcher
import pandas as pd


@pytest.fixture
def fetcher():
    """Create a StockDataFetcher instance for testing."""
    return StockDataFetcher()


@pytest.fixture
def test_symbols():
    """Return a list of test stock symbols."""
    return ["AAPL", "MSFT", "GOOGL"]


def test_get_current_price(fetcher, test_symbols):
    """Test fetching current prices for valid symbols."""
    for symbol in test_symbols:
        price = fetcher.get_current_price(symbol)
        assert isinstance(price, float)
        assert price > 0


def test_get_current_price_invalid_symbol(fetcher):
    """Test handling of invalid stock symbols."""
    with pytest.raises(ValueError):
        fetcher.get_current_price("INVALID_SYMBOL")


def test_get_historical_data(fetcher, test_symbols):
    """Test fetching historical data for valid symbols."""
    for symbol in test_symbols:
        data = fetcher.get_historical_data(symbol, period="5d")
        assert isinstance(data, pd.DataFrame)
        assert not data.empty
        assert all(
            col in data.columns for col in ["Open", "High", "Low", "Close", "Volume"]
        )


def test_get_historical_data_with_dates(fetcher):
    """Test fetching historical data with specific date range."""
    data = fetcher.get_historical_data(
        "AAPL", start_date="2024-01-01", end_date="2024-01-31"
    )
    assert isinstance(data, pd.DataFrame)
    assert not data.empty
    assert len(data) > 0


def test_get_stock_info(fetcher, test_symbols):
    """Test fetching stock information."""
    for symbol in test_symbols:
        info = fetcher.get_stock_info(symbol)
        assert isinstance(info, dict)
        assert len(info) > 0
        assert "symbol" in info or "longName" in info


def test_get_market_summary(fetcher, test_symbols):
    """Test fetching market summary for multiple symbols."""
    summary = fetcher.get_market_summary(test_symbols)
    assert isinstance(summary, pd.DataFrame)
    assert not summary.empty
    assert all(symbol in summary.index for symbol in test_symbols)
    assert all(
        col in summary.columns
        for col in ["current_price", "day_high", "day_low", "volume"]
    )
