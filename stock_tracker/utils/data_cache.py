"""Module for caching stock market data using DuckDB."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import duckdb
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)


class DataCache:
    """Class for caching stock market data using DuckDB."""

    def __init__(self, db_path: Union[str, Path] = "stock_data.db"):
        """
        Initialize the data cache.

        Args:
            db_path: Path to the DuckDB database file
        """
        self.db_path = Path(db_path)
        self.connection = None
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize the database and create necessary tables."""
        try:
            self.connection = duckdb.connect(str(self.db_path))
            self._create_tables()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

    def _create_tables(self) -> None:
        """Create necessary tables if they don't exist."""
        # Historical data table
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS historical_data (
                symbol VARCHAR,
                date DATE,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                volume BIGINT,
                last_updated TIMESTAMP,
                PRIMARY KEY (symbol, date)
            )
        """
        )

        # Current prices table
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS current_prices (
                symbol VARCHAR PRIMARY KEY,
                price DOUBLE,
                last_updated TIMESTAMP
            )
        """
        )

        # Market summaries table
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS market_summaries (
                symbol VARCHAR PRIMARY KEY,
                current_price DOUBLE,
                day_high DOUBLE,
                day_low DOUBLE,
                volume BIGINT,
                market_cap DOUBLE,
                week_52_high DOUBLE,
                week_52_low DOUBLE,
                last_updated TIMESTAMP
            )
        """
        )

    def store_historical_data(self, symbol: str, data: pd.DataFrame) -> None:
        """
        Store historical stock data in the cache.

        Args:
            symbol: Stock symbol
            data: DataFrame containing historical data
        """
        try:
            # Convert index to date column and ensure proper date format
            df = data.reset_index()
            logger.debug(f"Input data columns: {df.columns}")

            # Convert column names to lowercase for storage
            df.columns = [col.lower() for col in df.columns]
            logger.debug(f"Lowercase columns: {df.columns}")

            # Convert index to date column, preserving datetime type
            df = df.rename(columns={"index": "date"})
            df["symbol"] = symbol
            df["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            logger.debug(f"Final DataFrame to store:\n{df}")

            # Store data with explicit column mapping
            self.connection.execute(
                """
                INSERT OR REPLACE INTO historical_data 
                (symbol, date, open, high, low, close, volume, last_updated)
                SELECT 
                    symbol,
                    CAST(date AS DATE),
                    CAST(open AS DOUBLE),
                    CAST(high AS DOUBLE),
                    CAST(low AS DOUBLE),
                    CAST(close AS DOUBLE),
                    CAST(volume AS BIGINT),
                    CAST(last_updated AS TIMESTAMP)
                FROM df
            """
            )
            logger.info(f"Stored historical data for {symbol}")

        except Exception as e:
            logger.error(f"Failed to store historical data for {symbol}: {str(e)}")
            raise

    def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Optional[pd.DataFrame]:
        """
        Retrieve historical stock data from the cache.

        Args:
            symbol: Stock symbol
            start_date: Start date for data retrieval
            end_date: End date for data retrieval

        Returns:
            DataFrame containing historical data or None if not found
        """
        try:
            query = """
                SELECT date, open, high, low, close, volume
                FROM historical_data
                WHERE symbol = ?
            """
            params = [symbol]

            if start_date:
                query += " AND date >= ?"
                params.append(start_date.date())
            if end_date:
                query += " AND date <= ?"
                params.append(end_date.date())

            result = self.connection.execute(query, params).df()
            if result.empty:
                return None

            # Convert date column to datetime64[ns] to match input format
            result["date"] = pd.to_datetime(result["date"]).astype("datetime64[ns]")
            result.set_index("date", inplace=True)
            result.index.name = None  # Remove index name to match input

            # Convert column names back to proper case
            result.columns = ["Open", "High", "Low", "Close", "Volume"]

            # Ensure the index is in the same format as the input
            result.index = result.index.normalize()  # Remove time component if any

            return result
        except Exception as e:
            logger.error(f"Failed to retrieve historical data for {symbol}: {str(e)}")
            return None

    def store_current_price(self, symbol: str, price: float) -> None:
        """
        Store current stock price in the cache.

        Args:
            symbol: Stock symbol
            price: Current price

        Raises:
            ValueError: If price is invalid (negative or zero)
        """
        if price <= 0:
            raise ValueError("Invalid current price")

        try:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO current_prices 
                VALUES (?, ?, ?)
            """,
                (symbol, price, datetime.now()),
            )
            logger.info(f"Stored current price for {symbol}")
        except Exception as e:
            logger.error(f"Failed to store current price for {symbol}: {str(e)}")
            raise

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Retrieve current stock price from the cache.

        Args:
            symbol: Stock symbol

        Returns:
            Current price or None if not found
        """
        try:
            result = self.connection.execute(
                """
                SELECT price FROM current_prices 
                WHERE symbol = ? AND last_updated >= ?
            """,
                (symbol, datetime.now() - timedelta(minutes=5)),
            ).fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to retrieve current price for {symbol}: {str(e)}")
            return None

    def store_market_summary(self, symbol: str, summary: Dict[str, float]) -> None:
        """
        Store market summary data in the cache.

        Args:
            symbol: Stock symbol
            summary: Dictionary containing market summary data

        Raises:
            ValueError: If summary is invalid
        """
        if not isinstance(summary, dict):
            raise ValueError("Invalid market summary: must be a dictionary")

        try:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO market_summaries 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    symbol,
                    summary.get("current_price"),
                    summary.get("day_high"),
                    summary.get("day_low"),
                    summary.get("volume"),
                    summary.get("market_cap"),
                    summary.get("week_52_high"),
                    summary.get("week_52_low"),
                    datetime.now(),
                ),
            )
            logger.info(f"Stored market summary for {symbol}")
        except Exception as e:
            logger.error(f"Failed to store market summary for {symbol}: {str(e)}")
            raise

    def get_market_summary(self, symbol: str) -> Optional[Dict[str, float]]:
        """
        Retrieve market summary data from the cache.

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary containing market summary data or None if not found
        """
        try:
            result = self.connection.execute(
                """
                SELECT * FROM market_summaries 
                WHERE symbol = ? AND last_updated >= ?
            """,
                (symbol, datetime.now() - timedelta(minutes=5)),
            ).fetchone()

            if not result:
                return None

            return {
                "current_price": result[1],
                "day_high": result[2],
                "day_low": result[3],
                "volume": result[4],
                "market_cap": result[5],
                "week_52_high": result[6],
                "week_52_low": result[7],
            }
        except Exception as e:
            logger.error(f"Failed to retrieve market summary for {symbol}: {str(e)}")
            return None

    def cleanup_old_data(self, days_to_keep: int = 30) -> None:
        """
        Remove old data from the cache.

        Args:
            days_to_keep: Number of days of data to keep
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            # Clean historical data
            self.connection.execute(
                """
                DELETE FROM historical_data 
                WHERE date < ?
            """,
                (cutoff_date.date(),),
            )

            # Clean current prices
            self.connection.execute(
                """
                DELETE FROM current_prices 
                WHERE last_updated < ?
            """,
                (cutoff_date,),
            )

            # Clean market summaries
            self.connection.execute(
                """
                DELETE FROM market_summaries 
                WHERE last_updated < ?
            """,
                (cutoff_date,),
            )

            logger.info(f"Cleaned up data older than {days_to_keep} days")
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {str(e)}")
            raise

    def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
