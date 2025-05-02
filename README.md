# Stock Market Tracking Agent

A sophisticated stock market tracking agent built using LangGraph and Python. This agent monitors stock performance, analyzes market trends, and provides trading suggestions based on a play account.

## Features

- Real-time stock data monitoring
- Historical data analysis
- Trading strategy recommendations
- Portfolio performance tracking
- Risk assessment
- Customizable alerts
- Support for paper trading

## Installation

This project uses Poetry for dependency management. To get started:

1. Install Poetry if you haven't already:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Clone this repository and install dependencies:
   ```bash
   git clone <repository-url>
   cd stock-market-agent
   poetry install
   ```

3. Create a `.env` file in the project root with your API keys:
   ```
   ALPHA_VANTAGE_API_KEY=your_key_here
   ```

## Project Structure

```
stock_tracker/
├── config/         # Configuration files
├── agents/         # Agent implementations
├── models/         # Data models
├── utils/          # Utility functions
├── ui/            # User interface components
└── tests/         # Test suite
```

## Development

To run the development environment:

```bash
poetry shell
pytest  # Run tests
```

## License

MIT License 