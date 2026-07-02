"""
Input validation for order parameters.

Keeping validation isolated from the CLI and API layers makes it easy to
unit test and reuse (e.g. if a web UI is added later).
"""

import re

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}

# Reasonable Binance-style symbol pattern, e.g. BTCUSDT, ETHUSDT
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,20}$")


class ValidationError(Exception):
    """Raised when user-supplied order parameters are invalid."""


def validate_symbol(symbol: str) -> str:
    symbol = (symbol or "").strip().upper()
    if not symbol or not SYMBOL_PATTERN.match(symbol):
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Expected format like 'BTCUSDT'."
        )
    return symbol


def validate_side(side: str) -> str:
    side = (side or "").strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(f"Invalid side '{side}'. Must be one of {sorted(VALID_SIDES)}.")
    return side


def validate_order_type(order_type: str) -> str:
    order_type = (order_type or "").strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of {sorted(VALID_ORDER_TYPES)}."
        )
    return order_type


def validate_quantity(quantity) -> float:
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Quantity must be a number, got '{quantity}'.")
    if qty <= 0:
        raise ValidationError(f"Quantity must be greater than 0, got {qty}.")
    return qty


def validate_price(price, order_type: str):
    """
    Price is required for LIMIT and STOP_LIMIT orders, and must be absent
    or ignored for MARKET orders.
    """
    if order_type in ("LIMIT", "STOP_LIMIT"):
        if price is None:
            raise ValidationError(f"Price is required for {order_type} orders.")
        try:
            price_val = float(price)
        except (TypeError, ValueError):
            raise ValidationError(f"Price must be a number, got '{price}'.")
        if price_val <= 0:
            raise ValidationError(f"Price must be greater than 0, got {price_val}.")
        return price_val
    return None


def validate_stop_price(stop_price, order_type: str):
    """Stop price is required only for STOP_LIMIT orders (bonus feature)."""
    if order_type == "STOP_LIMIT":
        if stop_price is None:
            raise ValidationError("Stop price is required for STOP_LIMIT orders.")
        try:
            sp = float(stop_price)
        except (TypeError, ValueError):
            raise ValidationError(f"Stop price must be a number, got '{stop_price}'.")
        if sp <= 0:
            raise ValidationError(f"Stop price must be greater than 0, got {sp}.")
        return sp
    return None


def validate_order_params(symbol, side, order_type, quantity, price=None, stop_price=None):
    """
    Validate a full set of order parameters at once.

    Returns a dict of cleaned/normalized values ready to be passed to the
    API client layer.
    """
    clean_symbol = validate_symbol(symbol)
    clean_side = validate_side(side)
    clean_type = validate_order_type(order_type)
    clean_qty = validate_quantity(quantity)
    clean_price = validate_price(price, clean_type)
    clean_stop_price = validate_stop_price(stop_price, clean_type)

    return {
        "symbol": clean_symbol,
        "side": clean_side,
        "order_type": clean_type,
        "quantity": clean_qty,
        "price": clean_price,
        "stop_price": clean_stop_price,
    }
