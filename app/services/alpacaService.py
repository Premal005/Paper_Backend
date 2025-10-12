

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Set

from fastapi import APIRouter, Depends, HTTPException, Query
from alpaca_trade_api.rest import REST, TimeFrame
import websockets
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

ALPACA_API_KEY = os.getenv("ALPACA_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
ALPACA_WS = os.getenv("ALPACA_WS", "wss://stream.data.alpaca.markets/v2/iex")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "alpacaDB")
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client[DB_NAME]
market_collection = db["marketdata"]

router = APIRouter()

logger.info(f"Loaded Alpaca Key: {ALPACA_API_KEY}, Secret: {'SET' if ALPACA_SECRET_KEY else 'MISSING'}")


def get_rest_client():
    if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
        raise ValueError("Alpaca credentials missing")
    return REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)

# ✅ REST endpoints (unchanged)
@router.get("/account")
async def get_account_info(rest_client: REST = Depends(get_rest_client)):
    try:
        account = rest_client.get_account()
        return {
            "account_number": account.account_number,
            "cash": float(account.cash),
            "portfolio_value": float(account.portfolio_value),
            "buying_power": float(account.buying_power),
            "equity": float(account.equity),
            "status": account.status
        }
    except Exception as e:
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
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# @router.get("/quote/{symbol}")
# async def get_quote(symbol: str, rest_client: REST = Depends(get_rest_client)):
#     try:
#         quote = rest_client.get_latest_quote(symbol)
#         return {
#             "symbol": symbol,
#             "ask_price": float(getattr(quote, "ap", None) or 0),
#             "ask_size": getattr(quote, "as", None),
#             "bid_price": float(getattr(quote, "bp", None) or 0),
#             "bid_size": getattr(quote, "bs", None),
#             "timestamp": datetime.utcnow().isoformat()
#         }
#     except Exception as e:
#         logger.error(f"Error getting quote {symbol}: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))


# In alpacaService.py - update the get_quote function
@router.get("/quote/{symbol}")
async def get_quote(symbol: str, rest_client: REST = Depends(get_rest_client)):
    try:
        quote = rest_client.get_latest_quote(symbol)
        current_price = float(getattr(quote, "ap", None) or 0)
        logger.info(f"{quote}")
        # Calculate day change
        day_change = 0.0
        day_change_percentage = 0.0
        
        try:
            # Get today's bars to find open price
            today_bars = rest_client.get_bars(symbol, "1Day", limit=1).df
            # logger.info(f"{today_bars}")
            if not today_bars.empty:
                open_price = today_bars['open'].iloc[0]
                day_change = current_price - open_price
                day_change_percentage = (day_change / open_price) * 100 if open_price > 0 else 0
        except Exception as e:
            logger.warning(f"Could not calculate day change for {symbol}: {e}")
        
        return {
            "symbol": symbol,
            "ask_price": current_price,
            "ask_size": getattr(quote, "as", None),
            "bid_price": float(getattr(quote, "bp", None) or 0),
            "bid_size": getattr(quote, "bs", None),
            "last_price": current_price,
            "day_change": day_change,
            "day_change_percentage": day_change_percentage,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting quote {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))




# ✅ Alpaca WebSocket Feed
async def start_alpaca_feed(
    broadcast: Callable[[Any], None],
    subscribed_symbols: Set[str],
    ws_ref: Callable[[Any], None],
):
    """Start Alpaca WebSocket feed and support dynamic subscriptions"""
    url = ALPACA_WS
    key = ALPACA_API_KEY
    secret = ALPACA_SECRET_KEY

    if not url or not key or not secret:
        logger.warning("⚠️ Alpaca credentials missing; skipping WS feed")
        return

    while True:
        try:
            async with websockets.connect(url) as ws:
                ws_ref(ws)
                logger.info("✅ Alpaca WS connected")

                await ws.send(json.dumps({"action": "auth", "key": key, "secret": secret}))
                logger.info("🔑 Auth message sent")

                await ws.send(json.dumps({
                    "action": "subscribe",
                    "quotes": list(subscribed_symbols)
                }))
                logger.info(f"📡 Subscribed: {subscribed_symbols}")

                async for raw in ws:
                    msg = json.loads(raw)
                    logger.info(f"{msg}")
                    if isinstance(msg, list):
                        for item in msg:
                            if item.get("T") == "success":
                                logger.info("✅ Authenticated with Alpaca WS")
                                continue
                            if item.get("T") == "subscription":
                                logger.info(f"📌 Subscription updated: {item}")
                                continue
                            if item.get("T") == "q":
                                
                                tick = {
                                    "symbol": item.get("S"),
                                    "bid": item.get("bp"),
                                    "ask": item.get("ap"),
                                    "bid_size": item.get("bs"),
                                    "ask_size": item.get("as"),
                                    "timestamp": datetime.utcnow().isoformat() + "Z",
                                }

                                await market_collection.update_one(
                                    {"symbol": tick["symbol"], "exchange": "ALPACA"},
                                    {"$set": {**tick, "updatedAt": datetime.now()}},
                                    upsert=True,
                                )

                                await broadcast({**tick, "source": "ALPACA"})

        except Exception as e:
            logger.warning(f"⚠️ WS closed - retry in 5s: {e}")
            await asyncio.sleep(5)
