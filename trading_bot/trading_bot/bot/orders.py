"""
Order placement orchestration.

Sits between the CLI and the API client: validates input, calls the
client, and formats a clean summary for display. Kept separate from
client.py so business/display logic doesn't leak into the API wrapper.
"""

import logging

from bot.client import BinanceClientError, FuturesTestnetClient
from bot.validators import ValidationError, validate_order_params

logger = logging.getLogger("trading_bot")


class OrderResult:
    """Simple container for a formatted order outcome."""

    def __init__(self, success: bool, request: dict, response: dict = None, error: str = None):
        self.success = success
        self.request = request
        self.response = response
        self.error = error

    def summary_lines(self) -> list:
        lines = ["--- Order Request ---"]
        for key, value in self.request.items():
            if value is not None:
                lines.append(f"  {key}: {value}")

        if self.success and self.response:
            lines.append("--- Order Response ---")
            lines.append(f"  orderId: {self.response.get('orderId')}")
            lines.append(f"  status: {self.response.get('status')}")
            lines.append(f"  executedQty: {self.response.get('executedQty')}")
            avg_price = self.response.get("avgPrice")
            if avg_price is not None:
                lines.append(f"  avgPrice: {avg_price}")
            lines.append("SUCCESS: order placed.")
        else:
            lines.append("--- Error ---")
            lines.append(f"  {self.error}")
            lines.append("FAILURE: order was not placed.")

        return lines


def place_order(
    client: FuturesTestnetClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity,
    price=None,
    stop_price=None,
) -> OrderResult:
    """
    Validate parameters, place the order via the client, and return a
    structured OrderResult for display. Never raises — all errors are
    captured in the returned OrderResult so the CLI can print a clean
    success/failure message either way.
    """
    try:
        clean = validate_order_params(symbol, side, order_type, quantity, price, stop_price)
    except ValidationError as exc:
        logger.warning("Validation failed: %s", exc)
        request_echo = {
            "symbol": symbol,
            "side": side,
            "order_type": order_type,
            "quantity": quantity,
            "price": price,
            "stop_price": stop_price,
        }
        return OrderResult(success=False, request=request_echo, error=str(exc))

    request_summary = {
        "symbol": clean["symbol"],
        "side": clean["side"],
        "order_type": clean["order_type"],
        "quantity": clean["quantity"],
        "price": clean["price"],
        "stop_price": clean["stop_price"],
    }

    try:
        response = client.place_order(
            symbol=clean["symbol"],
            side=clean["side"],
            order_type=clean["order_type"],
            quantity=clean["quantity"],
            price=clean["price"],
            stop_price=clean["stop_price"],
        )
        return OrderResult(success=True, request=request_summary, response=response)
    except BinanceClientError as exc:
        logger.error("Order placement failed: %s", exc)
        return OrderResult(success=False, request=request_summary, error=str(exc))
