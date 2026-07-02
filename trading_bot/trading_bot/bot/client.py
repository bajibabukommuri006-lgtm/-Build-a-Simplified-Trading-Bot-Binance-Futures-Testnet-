"""
Thin wrapper around the Binance Futures Testnet API.

Uses the `python-binance` library's `Client` configured for the USDT-M
Futures Testnet. All requests and responses are logged. Network and API
errors are caught and re-raised as `BinanceClientError` so the CLI layer
can handle them uniformly.
"""

import logging

from binance import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

logger = logging.getLogger("trading_bot")

FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"


class BinanceClientError(Exception):
    """Raised for any API, network, or auth error talking to Binance."""


class FuturesTestnetClient:
    """
    Wraps python-binance's Client for USDT-M Futures Testnet order placement.

    This class is the only place in the codebase that talks to Binance,
    which keeps the CLI layer free of API/network concerns and makes the
    client easy to mock in tests.
    """

    def __init__(self, api_key: str, api_secret: str):
        if not api_key or not api_secret:
            raise BinanceClientError(
                "API key/secret not provided. Set BINANCE_API_KEY and "
                "BINANCE_API_SECRET (env vars or .env file)."
            )
        try:
            self._client = Client(api_key, api_secret, testnet=True)
            # python-binance's testnet flag targets spot testnet by default;
            # explicitly point FAPI calls at the futures testnet base URL.
            self._client.FUTURES_URL = FUTURES_TESTNET_BASE_URL + "/fapi"
        except Exception as exc:  # noqa: BLE001 - surface as our own error type
            logger.exception("Failed to initialize Binance client")
            raise BinanceClientError(f"Could not initialize Binance client: {exc}") from exc

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = None,
        stop_price: float = None,
        time_in_force: str = "GTC",
    ) -> dict:
        """
        Place an order on the USDT-M Futures Testnet.

        Args:
            symbol: e.g. "BTCUSDT"
            side: "BUY" or "SELL"
            order_type: "MARKET", "LIMIT", or "STOP_LIMIT" (mapped to
                Binance's STOP order type with a limit price)
            quantity: order quantity
            price: required for LIMIT / STOP_LIMIT
            stop_price: required for STOP_LIMIT
            time_in_force: "GTC" (default), "IOC", or "FOK" — used for
                LIMIT-style orders only

        Returns:
            Raw order response dict from Binance.

        Raises:
            BinanceClientError: on API errors or network failures.
        """
        params = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
        }

        if order_type == "MARKET":
            params["type"] = "MARKET"
        elif order_type == "LIMIT":
            params["type"] = "LIMIT"
            params["price"] = price
            params["timeInForce"] = time_in_force
        elif order_type == "STOP_LIMIT":
            params["type"] = "STOP"
            params["price"] = price
            params["stopPrice"] = stop_price
            params["timeInForce"] = time_in_force
        else:
            raise BinanceClientError(f"Unsupported order type: {order_type}")

        logger.info("Sending order request: %s", params)

        try:
            response = self._client.futures_create_order(**params)
            logger.info("Order response: %s", response)
            return response
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("Binance API error placing order %s: %s", params, exc)
            raise BinanceClientError(f"Binance API error: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - network/timeout/etc.
            logger.error("Network or unexpected error placing order %s: %s", params, exc)
            raise BinanceClientError(f"Network or unexpected error: {exc}") from exc

    def get_order_status(self, symbol: str, order_id: int) -> dict:
        """Fetch the current status of a previously placed order."""
        logger.info("Querying order status: symbol=%s order_id=%s", symbol, order_id)
        try:
            response = self._client.futures_get_order(symbol=symbol, orderId=order_id)
            logger.info("Order status response: %s", response)
            return response
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("Binance API error querying order %s: %s", order_id, exc)
            raise BinanceClientError(f"Binance API error: {exc}") from exc
        except Exception as exc:  # noqa: BLE001
            logger.error("Network or unexpected error querying order %s: %s", order_id, exc)
            raise BinanceClientError(f"Network or unexpected error: {exc}") from exc
