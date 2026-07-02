#!/usr/bin/env python3
"""
CLI entry point for the Simplified Trading Bot (Binance Futures Testnet).

Examples:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 60000
    python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.01 \\
        --price 61000 --stop-price 60900

Credentials are read from environment variables (or a local .env file):
    BINANCE_API_KEY
    BINANCE_API_SECRET
"""

import argparse
import os
import sys

from dotenv import load_dotenv

from bot.client import BinanceClientError, FuturesTestnetClient
from bot.logging_config import setup_logging
from bot.orders import place_order

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place MARKET / LIMIT / STOP_LIMIT orders on Binance Futures Testnet (USDT-M).",
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL", "buy", "sell"], help="Order side")
    parser.add_argument(
        "--type",
        dest="order_type",
        required=True,
        choices=["MARKET", "LIMIT", "STOP_LIMIT", "market", "limit", "stop_limit"],
        help="Order type",
    )
    parser.add_argument("--quantity", required=True, type=float, help="Order quantity")
    parser.add_argument("--price", type=float, default=None, help="Limit price (required for LIMIT/STOP_LIMIT)")
    parser.add_argument(
        "--stop-price", type=float, default=None, help="Stop trigger price (required for STOP_LIMIT)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Console log verbosity (file log always captures DEBUG)",
    )
    return parser


def main(argv=None) -> int:
    load_dotenv()  # picks up BINANCE_API_KEY / BINANCE_API_SECRET from a .env file if present

    parser = build_parser()
    args = parser.parse_args(argv)

    logger = setup_logging(args.log_level)

    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    try:
        client = FuturesTestnetClient(api_key, api_secret)
    except BinanceClientError as exc:
        logger.error("Startup failed: %s", exc)
        print(f"FAILURE: {exc}")
        return 1

    result = place_order(
        client=client,
        symbol=args.symbol,
        side=args.side,
        order_type=args.order_type,
        quantity=args.quantity,
        price=args.price,
        stop_price=args.stop_price,
    )

    for line in result.summary_lines():
        print(line)

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
