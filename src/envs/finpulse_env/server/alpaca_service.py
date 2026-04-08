"""
Alpaca API Integration
Fetches real-time market data from Alpaca Paper Trading API
"""
import os
from typing import Dict, List
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


class AlpacaMarketDataService:
    """Service for fetching real-time market data from Alpaca"""

    def __init__(self, api_key: str, secret_key: str):
        """
        Initialize Alpaca clients

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
        """
        # Data client for market data
        self.data_client = StockHistoricalDataClient(api_key, secret_key)

        # Trading client for account info (not executing real trades)
        self.trading_client = TradingClient(api_key, secret_key, paper=True)

    def get_latest_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get latest prices for given symbols

        Args:
            symbols: List of stock symbols (e.g., ['AAPL', 'MSFT'])

        Returns:
            Dict mapping symbol to current price
        """
        try:
            # Create request for latest quotes
            request_params = StockLatestQuoteRequest(symbol_or_symbols=symbols)

            # Fetch latest quotes
            quotes = self.data_client.get_stock_latest_quote(request_params)

            # Extract prices (use bid-ask midpoint)
            prices = {}
            for symbol in symbols:
                if symbol in quotes:
                    quote = quotes[symbol]
                    # Use midpoint of bid/ask for fair price
                    prices[symbol] = (quote.bid_price + quote.ask_price) / 2.0
                else:
                    # Fallback if symbol not found
                    prices[symbol] = 0.0

            return prices

        except Exception as e:
            print(f"⚠️ Alpaca API error: {e}")
            # Return fallback prices
            return {symbol: 100.0 for symbol in symbols}

    def get_account_info(self) -> dict:
        """Get paper trading account information"""
        try:
            account = self.trading_client.get_account()
            return {
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'buying_power': float(account.buying_power)
            }
        except Exception as e:
            print(f"⚠️ Alpaca account error: {e}")
            return {'cash': 10000.0, 'portfolio_value': 10000.0, 'buying_power': 10000.0}


def create_alpaca_service() -> AlpacaMarketDataService:
    """
    Create Alpaca service from environment variables

    Returns:
        AlpacaMarketDataService instance or None if credentials missing
    """
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    if not api_key or not secret_key:
        print("⚠️ Alpaca credentials not found in environment")
        return None

    try:
        service = AlpacaMarketDataService(api_key, secret_key)
        print("✅ Connected to Alpaca Paper Trading API")
        return service
    except Exception as e:
        print(f"❌ Failed to connect to Alpaca: {e}")
        return None
