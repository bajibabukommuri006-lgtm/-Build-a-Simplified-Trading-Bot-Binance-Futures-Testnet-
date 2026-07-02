"""Unit tests for bot.validators. Run with: python -m pytest tests/"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from bot.validators import ValidationError, validate_order_params


def test_valid_market_order():
    result = validate_order_params("btcusdt", "buy", "market", "0.01")
    assert result["symbol"] == "BTCUSDT"
    assert result["side"] == "BUY"
    assert result["order_type"] == "MARKET"
    assert result["quantity"] == 0.01
    assert result["price"] is None


def test_valid_limit_order():
    result = validate_order_params("ETHUSDT", "SELL", "LIMIT", "1.5", price="3000")
    assert result["price"] == 3000.0


def test_limit_order_missing_price_raises():
    with pytest.raises(ValidationError):
        validate_order_params("BTCUSDT", "BUY", "LIMIT", "0.01")


def test_invalid_side_raises():
    with pytest.raises(ValidationError):
        validate_order_params("BTCUSDT", "HOLD", "MARKET", "0.01")


def test_invalid_symbol_raises():
    with pytest.raises(ValidationError):
        validate_order_params("bad symbol!", "BUY", "MARKET", "0.01")


def test_negative_quantity_raises():
    with pytest.raises(ValidationError):
        validate_order_params("BTCUSDT", "BUY", "MARKET", "-1")


def test_non_numeric_quantity_raises():
    with pytest.raises(ValidationError):
        validate_order_params("BTCUSDT", "BUY", "MARKET", "abc")


def test_stop_limit_requires_stop_price():
    with pytest.raises(ValidationError):
        validate_order_params("BTCUSDT", "BUY", "STOP_LIMIT", "0.01", price="61000")


def test_stop_limit_valid():
    result = validate_order_params(
        "BTCUSDT", "BUY", "STOP_LIMIT", "0.01", price="61000", stop_price="60900"
    )
    assert result["stop_price"] == 60900.0
