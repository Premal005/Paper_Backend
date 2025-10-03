import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable

from fastapi import APIRouter, Depends, HTTPException, Query
from alpaca_trade_api.rest import REST, TimeFrame
import websockets
import msgpack
from motor.motor_asyncio import AsyncIOMotorClient

# --- Logging ---
logger = logging.getLogger(__name__)

# --- Config ---
ALPACA_API_KEY = os.getenv("ALPACA_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
ALPACA_WS = os.getenv("ALPACA_WS", "wss://stream.data.alpaca.markets/v2/iex")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "alpacaDB")

mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client[DB_NAME]
market_collection = db["marketdata"]

# --- Router ---
router = APIRouter()
def get_rest_client():
    if not ALPACA_API_KEY or not ALPACA_SECRET_KEY or not ALPACA_BASE_URL:
        raise ValueError("Alpaca API credentials missing")
    return REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)



# -------------------------
# REST ENDPOINTS
# -------------------------
# @router.get("/account")
# async def get_account_info(rest_client: REST = Depends(get_rest_client)):
#     try:
#         account = rest_client.get_account()
#         return {
#             "account_number": account.account_number,
#             "cash": float(account.cash),
#             "portfolio_value": float(account.portfolio_value),
#             "buying_power": float(account.buying_power),
#             "equity": float(account.equity),
#             "status": account.status
#         }
#     except Exception as e:
#         logger.error(f"Error getting account info: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

@router.get("/account")
async def get_account_info(rest_client: REST = Depends(get_rest_client)):
    try:
        account = rest_client.get_account()
        # Log full account object for debugging
        logger.info(f"Alpaca account raw response: {account.__dict__}")
        return {
            "account_number": account.account_number,
            "cash": float(account.cash),
            "portfolio_value": float(account.portfolio_value),
            "buying_power": float(account.buying_power),
            "equity": float(account.equity),
            "status": account.status
        }
    except Exception as e:
        # Catch and log full response or details
        logger.error("Error getting account info", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_positions(rest_client: REST = Depends(get_rest_client)):
    try:
        positions = rest_client.list_positions()
        return [
            {
                "symbol": pos.symbol,
                "qty": float(pos.qty),
                "current_price": float(pos.current_price),
                "market_value": float(pos.market_value),
                "unrealized_pl": float(pos.unrealized_pl)
            }
            for pos in positions
        ]
    except Exception as e:
        logger.error(f"Error getting positions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quote/{symbol}")
async def get_quote(symbol: str, rest_client: REST = Depends(get_rest_client)):
    try:
        quote = rest_client.get_latest_quote(symbol)

        # Depending on SDK, use getattr to avoid errors
        ask_price = getattr(quote, "ask_price", None) or getattr(quote, "ap", None)
        ask_size = getattr(quote, "ask_size", None) or getattr(quote, "as", None)
        bid_price = getattr(quote, "bid_price", None) or getattr(quote, "bp", None)
        bid_size = getattr(quote, "bid_size", None) or getattr(quote, "bs", None)
        timestamp = getattr(quote, "timestamp", None) or getattr(quote, "t", None)

        return {
            "symbol": symbol,
            "ask_price": float(ask_price) if ask_price else None,
            "ask_size": ask_size,
            "bid_price": float(bid_price) if bid_price else None,
            "bid_size": bid_size,
            "timestamp": timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
        }

    except Exception as e:
        logger.error(f"Error getting quote for {symbol}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# @router.get("/bars/{symbol}")
# async def get_historical_bars(
#     symbol: str,
#     timeframe: str = Query("1D", description="Timeframe: 1Min, 5Min, 15Min, 1H, 1D"),
#     days: int = Query(30, description="Number of days of historical data"),
# ):
#     try:
#         rest_client = get_rest_client()
#         timeframe_map = {
#             "1Min": TimeFrame.Minute,
#             "5Min": TimeFrame(5, TimeFrame.Minute),
#             "15Min": TimeFrame(15, TimeFrame.Minute),
#             "1H": TimeFrame.Hour,
#             "1D": TimeFrame.Day,
#         }
#         time_frame = timeframe_map.get(timeframe, TimeFrame.Day)
#         bars = rest_client.get_bars(
#             symbol,
#             time_frame,
#             start=(datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
#             end=datetime.now().strftime("%Y-%m-%d"),
#         )
#         return [
#             {
#                 "timestamp": bar.t.isoformat(),
#                 "open": float(bar.o),
#                 "high": float(bar.h),
#                 "low": float(bar.l),
#                 "close": float(bar.c),
#                 "volume": bar.v,
#             }
#             for bar in bars
#         ]
#     except Exception as e:
#         logger.error(f"Error getting bars for {symbol}: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

@router.get("/bars/{symbol}")
async def get_historical_bars(
    symbol: str,
    timeframe: str = Query("1D", description="1Min, 5Min, 15Min, 1H, 1D"),
    days: int = Query(30),
):
    try:
        rest_client = get_rest_client()
        timeframe_map = {
            "1Min": TimeFrame.Minute,
            "5Min": TimeFrame(5, TimeFrame.Minute),
            "15Min": TimeFrame(15, TimeFrame.Minute),
            "1H": TimeFrame.Hour,
            "1D": TimeFrame.Day,
        }
        time_frame = timeframe_map.get(timeframe, TimeFrame.Day)

        bars = rest_client.get_bars(
            symbol,
            time_frame,
            start=(datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
            end=datetime.now().strftime("%Y-%m-%d"),
            feed="iex"  # important for free-tier accounts
        )

        return [
            {
                "timestamp": bar.t.isoformat(),
                "open": float(bar.o),
                "high": float(bar.h),
                "low": float(bar.l),
                "close": float(bar.c),
                "volume": bar.v,
            }
            for bar in bars
        ]

    except Exception as e:
        logger.error(f"Error getting bars for {symbol}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# WEBSOCKET FEED
# -------------------------
def normalize_alpaca_message(msg):
    if not msg or not isinstance(msg, list):
        return None
    item = msg[0] if len(msg) > 0 else None
    if not item:
        return None
    return {
        "symbol": item.get("S") or item.get("sym") or item.get("s"),
        "exchange": "ALPACA",
        "brokerSymbol": item.get("S") or item.get("sym"),
        "instrumentType": "Options",
        "ltp": item.get("p") or item.get("last"),
        "bid": item.get("bp"),
        "ask": item.get("ap"),
        "volume": item.get("s"),
        "timestamp": datetime.now().timestamp() * 1000,
    }



async def start_alpaca_feed(broadcast: Callable[[Any], None], symbols: list[str] = None):
    url = ALPACA_WS
    key = ALPACA_API_KEY
    secret = ALPACA_SECRET_KEY
    symbols = symbols or ["AAPL", "RELI", "SPY"]

    if not url or not key or not secret:
        logger.warning("Alpaca credentials missing; skipping WS feed")
        return

    while True:
        try:
            async with websockets.connect(url) as ws:
                logger.info("✅ Alpaca WS connected")

                # Authenticate first
                await ws.send(json.dumps({"action": "auth", "key": key, "secret": secret}))
                logger.info("🔑 Auth message sent")

                # Subscribe after auth
                await ws.send(json.dumps({
                    "action": "subscribe",
                    "quotes": symbols
                }))
                logger.info(f"📡 Subscribed to quotes: {symbols}")

                # Now process incoming messages
                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                        logger.debug(f"WS MSG: {msg}")

                        # Handle auth success
                        if isinstance(msg, list):
                            for item in msg:
                                if item.get("T") == "success" and item.get("msg") == "authenticated":
                                    logger.info("✅ Authenticated with Alpaca WS")
                                    continue

                                if item.get("T") == "subscription":
                                    logger.info(f"📌 Subscription confirmed: {item}")
                                    continue

                                if item.get("T") == "q":  # Quote message
                                    # tick = {
                                    #     "symbol": item.get("S"),
                                    #     "exchange": "ALPACA",
                                    #     "brokerSymbol": item.get("S"),
                                    #     "instrumentType": "Stock",
                                    #     "ltp": None,
                                    #     "bid": item.get("bp"),
                                    #     "ask": item.get("ap"),
                                    #     "bid_size": item.get("bs"),
                                    #     "ask_size": item.get("as"),
                                    #     "volume": None,
                                    #     "timestamp": datetime.now().timestamp() * 1000,
                                    # }

                                    tick = {
                                        "symbol": item.get("S"),
                                        "bid": item.get("bp"),
                                        "ask": item.get("ap"),
                                        "bid_size": item.get("bs"),
                                        "ask_size": item.get("as"),
                                        "timestamp": datetime.utcnow().isoformat() + "Z",
                                    }

                                    # Save to Mongo
                                    await market_collection.update_one(
                                        {"symbol": tick["symbol"], "exchange": "ALPACA"},
                                        {"$set": {**tick, "updatedAt": datetime.now()}},
                                        upsert=True,
                                    )

                                    # Broadcast to WS clients
                                    await broadcast({**tick, "source": "ALPACA"})

                    except Exception as e:
                        logger.error(f"Parse error: {e}", exc_info=True)
                        continue

        except Exception as e:
            logger.warning(f"WS closed - retry in 5s: {e}")
            await asyncio.sleep(5)




