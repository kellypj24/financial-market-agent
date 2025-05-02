"""Test script for the StockDataFetcher class."""

from stock_tracker.utils.data_fetcher import StockDataFetcher
import pandas as pd
from rich.console import Console
from rich.table import Table


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
