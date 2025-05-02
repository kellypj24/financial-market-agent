"""Module for validating stock market data using Pydantic models."""

from typing import Dict, Any, List, Optional
import pandas as pd
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic.types import confloat, conint


class StockInfo(BaseModel):
    """Pydantic model for stock information validation."""

    symbol: str = Field(..., min_length=1)
    longName: str
    marketCap: confloat(gt=0)
    currentPrice: Optional[confloat(gt=0)] = None
    regularMarketPrice: Optional[confloat(gt=0)] = None
    previousClose: Optional[confloat(gt=0)] = None

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate stock symbol format."""
        if not v.isalpha():
            raise ValueError("Symbol must contain only letters")
        return v.upper()


class HistoricalDataPoint(BaseModel):
    """Pydantic model for a single historical data point."""

    Open: confloat(gt=0)
    High: confloat(gt=0)
    Low: confloat(gt=0)
    Close: confloat(gt=0)
    Volume: conint(gt=0)

    @model_validator(mode="after")
    def validate_price_relationships(self) -> "HistoricalDataPoint":
        """Validate price relationships (High >= Low, etc.)."""
        if self.High < self.Low:
            raise ValueError("High price must be greater than or equal to Low price")
        if self.Open > self.High or self.Open < self.Low:
            raise ValueError("Open price must be between High and Low")
        if self.Close > self.High or self.Close < self.Low:
            raise ValueError("Close price must be between High and Low")
        return self


class MarketSummaryPoint(BaseModel):
    """Pydantic model for a single market summary data point."""

    current_price: confloat(gt=0)
    day_high: confloat(gt=0)
    day_low: confloat(gt=0)
    volume: conint(gt=0)
    market_cap: confloat(gt=0)
    week_52_high: confloat(gt=0)
    week_52_low: confloat(gt=0)

    @model_validator(mode="after")
    def validate_price_relationships(self) -> "MarketSummaryPoint":
        """Validate price relationships."""
        if self.day_high < self.day_low:
            raise ValueError("Day high must be greater than or equal to day low")
        if self.current_price > self.day_high or self.current_price < self.day_low:
            raise ValueError("Current price must be between day high and low")
        if self.week_52_high < self.week_52_low:
            raise ValueError(
                "52-week high must be greater than or equal to 52-week low"
            )
        return self


def validate_historical_data(data: pd.DataFrame) -> bool:
    """
    Validate historical stock data using Pydantic models.

    Args:
        data: DataFrame containing historical stock data

    Returns:
        bool: True if data is valid, raises ValueError if invalid

    Raises:
        ValueError: If data fails validation
    """
    if data.empty:
        raise ValueError("Historical data is empty")

    # Check required columns
    required_columns = ["Open", "High", "Low", "Close", "Volume"]
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Check for missing values
    if data[required_columns].isnull().any().any():
        raise ValueError("Historical data contains missing values")

    # Validate each row using Pydantic model
    for idx, row in data.iterrows():
        try:
            HistoricalDataPoint(**row.to_dict())
        except ValueError as e:
            raise ValueError(f"Invalid data at index {idx}: {str(e)}")

    return True


def validate_stock_info(info: Dict[str, Any]) -> bool:
    """
    Validate stock information using Pydantic model.

    Args:
        info: Dictionary containing stock information

    Returns:
        bool: True if data is valid, raises ValueError if invalid

    Raises:
        ValueError: If data fails validation
    """
    try:
        StockInfo(**info)
        return True
    except ValueError as e:
        raise ValueError(f"Invalid stock info: {str(e)}")


def validate_market_summary(summary: pd.DataFrame, symbols: List[str]) -> bool:
    """
    Validate market summary data using Pydantic models.

    Args:
        summary: DataFrame containing market summary data
        symbols: List of symbols that should be in the summary

    Returns:
        bool: True if data is valid, raises ValueError if invalid

    Raises:
        ValueError: If data fails validation
    """
    if summary.empty:
        raise ValueError("Market summary is empty")

    # Check if all symbols are present
    missing_symbols = [symbol for symbol in symbols if symbol not in summary.index]
    if missing_symbols:
        raise ValueError(f"Missing symbols in summary: {missing_symbols}")

    # Check for missing values
    if summary.isnull().any().any():
        raise ValueError("Market summary contains missing values")

    # Validate each row using Pydantic model
    for symbol, row in summary.iterrows():
        try:
            MarketSummaryPoint(**row.to_dict())
        except ValueError as e:
            raise ValueError(f"Invalid data for symbol {symbol}: {str(e)}")

    return True


def validate_time_series_consistency(data: pd.DataFrame) -> bool:
    """
    Validate time series data consistency.

    Args:
        data: DataFrame with datetime index

    Returns:
        bool: True if data is valid, raises ValueError if invalid

    Raises:
        ValueError: If data fails validation
    """
    # Check if index is datetime
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("DataFrame index must be datetime")

    # Check for duplicate dates
    if data.index.duplicated().any():
        raise ValueError("Duplicate dates found in time series")

    # Check for gaps in time series
    date_diff = data.index.to_series().diff()
    if len(date_diff.unique()) > 2:  # More than one unique time difference
        raise ValueError("Inconsistent time intervals in time series")

    return True
