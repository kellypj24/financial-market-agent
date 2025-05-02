"""Test suite for the stock market data cache."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil
from stock_tracker.utils.data_cache import DataCache


@pytest.fixture
def temp_db_dir():
    """Create a temporary directory for the database."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def data_cache(temp_db_dir):
    """Create a DataCache instance with a temporary database."""
    db_path = Path(temp_db_dir) / "test_stock_data.db"
    cache = DataCache(db_path)
    yield cache
    cache.close()


@pytest.fixture
def sample_historical_data():
    """Create sample historical data DataFrame."""
    dates = pd.date_range(start="2024-01-01", periods=5)
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0, 103.0, 104.0],
            "High": [105.0, 106.0, 107.0, 108.0, 109.0],
            "Low": [95.0, 96.0, 97.0, 98.0, 99.0],
            "Close": [103.0, 104.0, 105.0, 106.0, 107.0],
            "Volume": [1000000, 1100000, 1200000, 1300000, 1400000],
        },
        index=dates,
    )


@pytest.fixture
def sample_market_summary():
    """Create sample market summary data."""
    return {
        "current_price": 150.0,
        "day_high": 155.0,
        "day_low": 145.0,
        "volume": 50000000,
        "market_cap": 2_000_000_000_000,
        "week_52_high": 200.0,
        "week_52_low": 100.0,
    }


def test_initialization(data_cache):
    """Test database initialization and table creation."""
    # Verify tables exist
    tables = data_cache.connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    table_names = [t[0] for t in tables]
    assert "historical_data" in table_names
    assert "current_prices" in table_names
    assert "market_summaries" in table_names


def test_store_and_get_historical_data(data_cache, sample_historical_data):
    """Test storing and retrieving historical data."""
    symbol = "AAPL"

    # Store data
    data_cache.store_historical_data(symbol, sample_historical_data)

    # Retrieve data
    retrieved_data = data_cache.get_historical_data(symbol)
    assert retrieved_data is not None
    assert isinstance(retrieved_data, pd.DataFrame)
    assert len(retrieved_data) == len(sample_historical_data)

    # Verify data integrity
    pd.testing.assert_frame_equal(
        retrieved_data,
        sample_historical_data,
        check_dtype=False,
    )


def test_historical_data_date_range(data_cache, sample_historical_data):
    """Test retrieving historical data with date range filters."""
    symbol = "AAPL"
    data_cache.store_historical_data(symbol, sample_historical_data)

    # Test with start date
    start_date = datetime(2024, 1, 2)
    filtered_data = data_cache.get_historical_data(symbol, start_date=start_date)
    assert len(filtered_data) == 4  # Should exclude first day

    # Test with end date
    end_date = datetime(2024, 1, 4)
    filtered_data = data_cache.get_historical_data(symbol, end_date=end_date)
    assert len(filtered_data) == 4  # Should exclude last day

    # Test with both dates
    filtered_data = data_cache.get_historical_data(
        symbol, start_date=start_date, end_date=end_date
    )
    assert len(filtered_data) == 3


def test_store_and_get_current_price(data_cache):
    """Test storing and retrieving current price."""
    symbol = "AAPL"
    price = 150.0

    # Store price
    data_cache.store_current_price(symbol, price)

    # Retrieve price
    retrieved_price = data_cache.get_current_price(symbol)
    assert retrieved_price == price

    # Test expiration
    data_cache.connection.execute(
        """
        UPDATE current_prices 
        SET last_updated = ? 
        WHERE symbol = ?
        """,
        (datetime.now() - timedelta(minutes=6), symbol),
    )
    expired_price = data_cache.get_current_price(symbol)
    assert expired_price is None


def test_store_and_get_market_summary(data_cache, sample_market_summary):
    """Test storing and retrieving market summary."""
    symbol = "AAPL"

    # Store summary
    data_cache.store_market_summary(symbol, sample_market_summary)

    # Retrieve summary
    retrieved_summary = data_cache.get_market_summary(symbol)
    assert retrieved_summary is not None
    assert retrieved_summary == sample_market_summary

    # Test expiration
    data_cache.connection.execute(
        """
        UPDATE market_summaries 
        SET last_updated = ? 
        WHERE symbol = ?
        """,
        (datetime.now() - timedelta(minutes=6), symbol),
    )
    expired_summary = data_cache.get_market_summary(symbol)
    assert expired_summary is None


def test_cleanup_old_data(data_cache, sample_historical_data):
    """Test cleaning up old data."""
    symbol = "AAPL"

    # Store data
    data_cache.store_historical_data(symbol, sample_historical_data)

    # Delete old data and insert with new dates
    old_date = datetime.now() - timedelta(days=31)

    # First delete the existing data
    data_cache.connection.execute(
        "DELETE FROM historical_data WHERE symbol = ?", (symbol,)
    )

    # Then insert the data with new dates
    data_cache.connection.execute(
        """
        INSERT INTO historical_data
        SELECT 
            symbol,
            ? as date,
            open,
            high,
            low,
            close,
            volume,
            last_updated
        FROM historical_data
        WHERE symbol = ?
        """,
        (old_date.date(), symbol),
    )

    # Clean up old data
    data_cache.cleanup_old_data(days_to_keep=30)

    # Verify data is removed
    result = data_cache.get_historical_data(symbol)
    assert result is None


def test_error_handling(data_cache):
    """Test error handling for invalid operations."""
    # Test invalid historical data (empty DataFrame)
    with pytest.raises(
        Exception,
        match='Binder Error: Referenced column "open" not found in FROM clause!',
    ):
        data_cache.store_historical_data("AAPL", pd.DataFrame())

    # Test invalid current price
    with pytest.raises(Exception, match="Invalid current price"):
        data_cache.store_current_price("AAPL", -1.0)

    # Test invalid market summary
    with pytest.raises(Exception, match="Invalid market summary"):
        data_cache.store_market_summary(pd.DataFrame())


def test_concurrent_access(temp_db_dir):
    """Test concurrent access to the database."""
    db_path = Path(temp_db_dir) / "test_stock_data.db"

    # Create two cache instances
    cache1 = DataCache(db_path)
    cache2 = DataCache(db_path)

    try:
        # Store data with first instance
        cache1.store_current_price("AAPL", 150.0)

        # Retrieve with second instance
        price = cache2.get_current_price("AAPL")
        assert price == 150.0
    finally:
        cache1.close()
        cache2.close()
