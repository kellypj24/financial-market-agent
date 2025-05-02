"""Test suite for the StockDataFetcher class."""

import pytest
from stock_tracker.utils.data_fetcher import StockDataFetcher
import pandas as pd
from rich.console import Console
from rich.table import Table


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


def main():
    """Run a demonstration of the StockDataFetcher."""
    console = Console()
    fetcher = StockDataFetcher()

    # Test symbols
    symbols = ["AAPL", "MSFT", "GOOGL"]

    console.print("\n[bold blue]Stock Market Data Fetcher Demo[/bold blue]\n")

    # Test current prices
    console.print("[bold]Current Prices:[/bold]")
    for symbol in symbols:
        try:
            price = fetcher.get_current_price(symbol)
            console.print(f"{symbol}: ${price:.2f}")
        except ValueError as e:
            console.print(f"[red]Error fetching {symbol}: {str(e)}[/red]")

    # Test historical data
    console.print("\n[bold]Historical Data (Last 5 Days):[/bold]")
    for symbol in symbols:
        try:
            data = fetcher.get_historical_data(symbol, period="5d")
            console.print(f"\n{symbol} Historical Data:")
            console.print(data[["Open", "High", "Low", "Close", "Volume"]].to_string())
        except ValueError as e:
            console.print(
                f"[red]Error fetching historical data for {symbol}: {str(e)}[/red]"
            )

    # Test market summary
    console.print("\n[bold]Market Summary:[/bold]")
    try:
        summary = fetcher.get_market_summary(symbols)
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Symbol")
        table.add_column("Current Price", justify="right")
        table.add_column("Day High", justify="right")
        table.add_column("Day Low", justify="right")
        table.add_column("Volume", justify="right")

        for symbol in symbols:
            if symbol in summary.index:
                row = summary.loc[symbol]
                table.add_row(
                    symbol,
                    f"${row['current_price']:.2f}",
                    f"${row['day_high']:.2f}",
                    f"${row['day_low']:.2f}",
                    f"{row['volume']:,}",
                )

        console.print(table)
    except ValueError as e:
        console.print(f"[red]Error fetching market summary: {str(e)}[/red]")


if __name__ == "__main__":
    main()
