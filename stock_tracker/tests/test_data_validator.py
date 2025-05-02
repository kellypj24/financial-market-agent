"""Test suite for the StockDataValidator class."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from stock_tracker.utils.data_validator import StockDataValidator


@pytest.fixture
def validator():
    """Create a StockDataValidator instance for testing."""
    return StockDataValidator()


@pytest.fixture
def valid_historical_data():
    """Create valid historical data DataFrame."""
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
def valid_stock_info():
    """Create valid stock info dictionary."""
    return {
        "symbol": "AAPL",
        "longName": "Apple Inc.",
        "marketCap": 2_000_000_000_000,
        "currentPrice": 150.0,
        "regularMarketPrice": 150.0,
        "previousClose": 149.0,
    }


@pytest.fixture
def valid_market_summary():
    """Create valid market summary DataFrame."""
    return pd.DataFrame(
        {
            "current_price": [150.0, 250.0, 350.0],
            "day_high": [155.0, 255.0, 355.0],
            "day_low": [145.0, 245.0, 345.0],
            "volume": [50000000, 60000000, 70000000],
            "market_cap": [2_000_000_000_000, 1_500_000_000_000, 1_000_000_000_000],
            "52_week_high": [200.0, 300.0, 400.0],
            "52_week_low": [100.0, 200.0, 300.0],
        },
        index=["AAPL", "MSFT", "GOOGL"],
    )


def test_validate_historical_data_success(validator, valid_historical_data):
    """Test successful validation of historical data."""
    assert validator.validate_historical_data(valid_historical_data) is True


def test_validate_historical_data_empty(validator):
    """Test validation of empty historical data."""
    with pytest.raises(ValueError, match="Historical data is empty"):
        validator.validate_historical_data(pd.DataFrame())


def test_validate_historical_data_missing_columns(validator, valid_historical_data):
    """Test validation of historical data with missing columns."""
    invalid_data = valid_historical_data.drop(columns=["Open", "High"])
    with pytest.raises(ValueError, match="Missing required columns"):
        validator.validate_historical_data(invalid_data)


def test_validate_historical_data_invalid_types(validator, valid_historical_data):
    """Test validation of historical data with invalid data types."""
    invalid_data = valid_historical_data.copy()
    invalid_data["Open"] = invalid_data["Open"].astype(str)
    with pytest.raises(ValueError, match="Column Open must be numeric"):
        validator.validate_historical_data(invalid_data)


def test_validate_historical_data_missing_values(validator, valid_historical_data):
    """Test validation of historical data with missing values."""
    invalid_data = valid_historical_data.copy()
    invalid_data.loc[invalid_data.index[0], "Open"] = np.nan
    with pytest.raises(ValueError, match="Historical data contains missing values"):
        validator.validate_historical_data(invalid_data)


def test_validate_historical_data_invalid_price_relationships(
    validator, valid_historical_data
):
    """Test validation of historical data with invalid price relationships."""
    invalid_data = valid_historical_data.copy()
    invalid_data.loc[invalid_data.index[0], "High"] = 90.0  # High < Low
    with pytest.raises(ValueError, match="Invalid price relationships detected"):
        validator.validate_historical_data(invalid_data)


def test_validate_historical_data_negative_values(validator, valid_historical_data):
    """Test validation of historical data with negative values."""
    invalid_data = valid_historical_data.copy()
    invalid_data.loc[invalid_data.index[0], "Open"] = -100.0
    with pytest.raises(ValueError, match="Negative values detected"):
        validator.validate_historical_data(invalid_data)


def test_validate_historical_data_zero_volume(validator, valid_historical_data):
    """Test validation of historical data with zero volume."""
    invalid_data = valid_historical_data.copy()
    invalid_data.loc[invalid_data.index[0], "Volume"] = 0
    with pytest.raises(ValueError, match="Zero volume detected"):
        validator.validate_historical_data(invalid_data)


def test_validate_stock_info_success(validator, valid_stock_info):
    """Test successful validation of stock info."""
    assert validator.validate_stock_info(valid_stock_info) is True


def test_validate_stock_info_missing_fields(validator, valid_stock_info):
    """Test validation of stock info with missing fields."""
    invalid_info = valid_stock_info.copy()
    del invalid_info["marketCap"]
    with pytest.raises(ValueError, match="Missing required fields"):
        validator.validate_stock_info(invalid_info)


def test_validate_stock_info_invalid_symbol(validator, valid_stock_info):
    """Test validation of stock info with invalid symbol."""
    invalid_info = valid_stock_info.copy()
    invalid_info["symbol"] = ""
    with pytest.raises(ValueError, match="Invalid symbol"):
        validator.validate_stock_info(invalid_info)


def test_validate_stock_info_invalid_market_cap(validator, valid_stock_info):
    """Test validation of stock info with invalid market cap."""
    invalid_info = valid_stock_info.copy()
    invalid_info["marketCap"] = -1
    with pytest.raises(ValueError, match="Invalid market capitalization"):
        validator.validate_stock_info(invalid_info)


def test_validate_market_summary_success(validator, valid_market_summary):
    """Test successful validation of market summary."""
    symbols = ["AAPL", "MSFT", "GOOGL"]
    assert validator.validate_market_summary(valid_market_summary, symbols) is True


def test_validate_market_summary_missing_symbols(validator, valid_market_summary):
    """Test validation of market summary with missing symbols."""
    symbols = ["AAPL", "MSFT", "GOOGL", "INVALID"]
    with pytest.raises(ValueError, match="Missing symbols in summary"):
        validator.validate_market_summary(valid_market_summary, symbols)


def test_validate_market_summary_invalid_price_relationships(
    validator, valid_market_summary
):
    """Test validation of market summary with invalid price relationships."""
    invalid_summary = valid_market_summary.copy()
    invalid_summary.loc["AAPL", "day_high"] = 140.0  # day_high < day_low
    with pytest.raises(ValueError, match="Invalid price relationships detected"):
        validator.validate_market_summary(invalid_summary, ["AAPL", "MSFT", "GOOGL"])


def test_validate_time_series_consistency_success(validator, valid_historical_data):
    """Test successful validation of time series consistency."""
    assert validator.validate_time_series_consistency(valid_historical_data) is True


def test_validate_time_series_consistency_non_datetime_index(validator):
    """Test validation of time series with non-datetime index."""
    data = pd.DataFrame({"value": [1, 2, 3]}, index=[1, 2, 3])
    with pytest.raises(ValueError, match="DataFrame index must be datetime"):
        validator.validate_time_series_consistency(data)


def test_validate_time_series_consistency_duplicate_dates(
    validator, valid_historical_data
):
    """Test validation of time series with duplicate dates."""
    invalid_data = pd.concat([valid_historical_data, valid_historical_data.iloc[[0]]])
    with pytest.raises(ValueError, match="Duplicate dates found in time series"):
        validator.validate_time_series_consistency(invalid_data)


def test_validate_time_series_consistency_inconsistent_intervals(validator):
    """Test validation of time series with inconsistent intervals."""
    dates = pd.DatetimeIndex(
        ["2024-01-01", "2024-01-02", "2024-01-04"]  # Skipped a day
    )
    data = pd.DataFrame({"value": [1, 2, 3]}, index=dates)
    with pytest.raises(ValueError, match="Inconsistent time intervals in time series"):
        validator.validate_time_series_consistency(data)
