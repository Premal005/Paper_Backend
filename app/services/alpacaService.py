# import asyncio
# import json
# import logging
# from datetime import datetime
# from typing import Callable, Any

# import websockets
# from ..config import Config

# from  ..models.marketModel import MarketData

# logger = logging.getLogger(__name__)

# def normalize_alpaca_message(msg):
#     if not msg or not isinstance(msg, list):
#         return None
        
#     item = msg[0] if len(msg) > 0 else None
#     if not item:
#         return None

#     return {
#         "symbol": item.get("S") or item.get("sym") or item.get("s") or None,
#         "exchange": "ALPACA",
#         "brokerSymbol": item.get("S") or item.get("sym"),
#         "instrumentType": "Options",
#         "ltp": item.get("p") or item.get("last") or None,
#         "bid": item.get("bp") or None,
#         "ask": item.get("ap") or None,
#         "volume": item.get("s") or None,
#         "timestamp": datetime.now().timestamp() * 1000
#     }

# async def start_alpaca_feed(broadcast: Callable[[Any], None]):
#     url = Config.ALPACA_WS
#     key = Config.ALPACA_KEY
#     secret = Config.ALPACA_SECRET
    
#     if not url or not key or not secret:
#         logger.warning("Alpaca credentials missing; skipping Alpaca feed")
#         return
        
#     while True:
#         try:
#             async with websockets.connect(url) as ws:
#                 logger.info("✅ Alpaca WS connected")
                
#                 auth_msg = json.dumps({"action": "auth", "key": key, "secret": secret})
#                 await ws.send(auth_msg)
                
#                 async for raw in ws:
#                     try:
#                         msg = json.loads(raw)
#                         tick = normalize_alpaca_message(msg)
#                         if not tick or not tick.get("symbol"):
#                             continue
                            
#                         await MarketData.update_one(
#                             {"symbol": tick["symbol"], "exchange": "ALPACA"},
#                             {
#                                 "$set": {
#                                     "brokerSymbol": tick["brokerSymbol"],
#                                     "instrumentType": tick["instrumentType"],
#                                     "ltp": tick["ltp"],
#                                     "bid": tick["bid"],
#                                     "ask": tick["ask"],
#                                     "volume": tick["volume"],
#                                     "updatedAt": datetime.now()
#                                 }
#                             },
#                             upsert=True
#                         )
                        
#                         broadcast({**tick, "source": "ALPACA"})
                        
#                     except (json.JSONDecodeError, KeyError) as e:
#                         logger.debug(f"Message parsing error: {e}")
#                         continue
                        
#         except (websockets.ConnectionClosed, ConnectionError) as e:
#             logger.warning(f"Alpaca WS closed - retry in 5s: {e}")
#             await asyncio.sleep(5)
#         except Exception as e:
#             logger.error(f"Alpaca WS error: {e}")
#             await asyncio.sleep(5)


# import asyncio
# import json
# import logging
# from datetime import datetime
# from typing import Callable, Any

# import websockets
# import msgpack
# from ..config import Config
# from ..models.marketModel import MarketData

# logger = logging.getLogger(__name__)

# def normalize_alpaca_message(msg):
#     if not msg or not isinstance(msg, list):
#         return None

#     item = msg[0] if len(msg) > 0 else None
#     if not item:
#         return None

#     return {
#         "symbol": item.get("S") or item.get("sym") or item.get("s") or None,
#         "exchange": "ALPACA",
#         "brokerSymbol": item.get("S") or item.get("sym"),
#         "instrumentType": "Options",
#         "ltp": item.get("p") or item.get("last") or None,
#         "bid": item.get("bp") or None,
#         "ask": item.get("ap") or None,
#         "volume": item.get("s") or None,
#         "timestamp": datetime.now().timestamp() * 1000
#     }

# async def start_alpaca_feed(broadcast: Callable[[Any], None]):
#     url = Config.ALPACA_WS
#     key = Config.ALPACA_KEY
#     secret = Config.ALPACA_SECRET

#     if not url or not key or not secret:
#         logger.warning("Alpaca credentials missing; skipping Alpaca feed")
#         return

#     while True:
#         try:
#             async with websockets.connect(url) as ws:
#                 logger.info("✅ Alpaca WS connected")

#                 # Authenticate
#                 auth_msg = json.dumps({"action": "auth", "key": key, "secret": secret})
#                 await ws.send(auth_msg)

#                 async for raw in ws:
#                     try:
#                         # Decode message depending on type
#                         if isinstance(raw, bytes):
#                             msg = msgpack.unpackb(raw, raw=False)
#                         else:
#                             msg = json.loads(raw)

#                         tick = normalize_alpaca_message(msg)
#                         if not tick or not tick.get("symbol"):
#                             continue

#                         # Update MongoDB
#                         await MarketData.update_one(
#                             {"symbol": tick["symbol"], "exchange": "ALPACA"},
#                             {
#                                 "$set": {
#                                     "brokerSymbol": tick["brokerSymbol"],
#                                     "instrumentType": tick["instrumentType"],
#                                     "ltp": tick["ltp"],
#                                     "bid": tick["bid"],
#                                     "ask": tick["ask"],
#                                     "volume": tick["volume"],
#                                     "updatedAt": datetime.now()
#                                 }
#                             },
#                             upsert=True
#                         )

#                         # Broadcast to other services
#                         broadcast({**tick, "source": "ALPACA"})

#                     except (json.JSONDecodeError, KeyError, msgpack.exceptions.ExtraData, msgpack.exceptions.UnpackException) as e:
#                         logger.debug(f"Message parsing error: {e}")
#                         continue

#         except (websockets.ConnectionClosed, ConnectionError) as e:
#             logger.warning(f"Alpaca WS closed - retry in 5s: {e}")
#             await asyncio.sleep(5)
#         except Exception as e:
#             logger.error(f"Alpaca WS error: {e}")
#             await asyncio.sleep(5)





# import os
# import asyncio
# import json
# import logging
# from datetime import datetime, timedelta
# from typing import Any, Callable

# from fastapi import FastAPI, HTTPException, Depends, Query
# from fastapi.middleware.cors import CORSMiddleware
# from dotenv import load_dotenv

# from alpaca_trade_api.rest import REST, TimeFrame
# import alpaca_trade_api as tradeapi

# import websockets
# import msgpack
# from motor.motor_asyncio import AsyncIOMotorClient

# # --- Load env ---
# load_dotenv()

# # --- Logging ---
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # --- Alpaca Config ---
# ALPACA_API_KEY = os.getenv("ALPACA_KEY")
# ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET")
# ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
# ALPACA_WS = os.getenv("ALPACA_WS", "wss://stream.data.alpaca.markets/v2/iex")

# # --- Mongo Config ---
# MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
# DB_NAME = os.getenv("DB_NAME", "alpacaDB")

# mongo_client = AsyncIOMotorClient(MONGO_URI)
# db = mongo_client[DB_NAME]
# market_collection = db["marketdata"]

# # --- FastAPI ---
# app = FastAPI(
#     title="Alpaca API Integration",
#     description="FastAPI service for Alpaca trading + WebSocket feed",
#     version="2.0.0"
# )

# # --- CORS ---
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- REST Client ---
# def get_rest_client():
#     return REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)


# # -------------------------
# # REST API ENDPOINTS
# # -------------------------
# @app.get("/")
# async def root():
#     return {"message": "Alpaca API Integration Service"}

# @app.get("/account")
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

# @app.get("/positions")
# async def get_positions(rest_client: REST = Depends(get_rest_client)):
#     try:
#         positions = rest_client.list_positions()
#         return [
#             {
#                 "symbol": pos.symbol,
#                 "qty": float(pos.qty),
#                 "current_price": float(pos.current_price),
#                 "market_value": float(pos.market_value),
#                 "unrealized_pl": float(pos.unrealized_pl)
#             }
#             for pos in positions
#         ]
#     except Exception as e:
#         logger.error(f"Error getting positions: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/quote/{symbol}")
# async def get_quote(symbol: str, rest_client: REST = Depends(get_rest_client)):
#     try:
#         quote = rest_client.get_latest_quote(symbol)
#         return {
#             "symbol": symbol,
#             "ask_price": float(quote.askprice),
#             "ask_size": quote.asksize,
#             "bid_price": float(quote.bidprice),
#             "bid_size": quote.bidsize,
#             "timestamp": quote.timestamp.isoformat() if hasattr(quote.timestamp, 'isoformat') else str(quote.timestamp)
#         }
#     except Exception as e:
#         logger.error(f"Error getting quote for {symbol}: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/bars/{symbol}")
# async def get_historical_bars(
#     symbol: str,
#     timeframe: str = Query("1D", description="Timeframe: 1Min, 5Min, 15Min, 1H, 1D"),
#     days: int = Query(30, description="Number of days of historical data")
# ):
#     try:
#         rest_client = get_rest_client()
#         timeframe_map = {
#             "1Min": TimeFrame.Minute,
#             "5Min": TimeFrame(5, TimeFrame.Minute),
#             "15Min": TimeFrame(15, TimeFrame.Minute),
#             "1H": TimeFrame.Hour,
#             "1D": TimeFrame.Day
#         }
#         time_frame = timeframe_map.get(timeframe, TimeFrame.Day)
#         bars = rest_client.get_bars(
#             symbol,
#             time_frame,
#             start=(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
#             end=datetime.now().strftime('%Y-%m-%d')
#         )
#         return [
#             {
#                 "timestamp": bar.t.isoformat(),
#                 "open": float(bar.o),
#                 "high": float(bar.h),
#                 "low": float(bar.l),
#                 "close": float(bar.c),
#                 "volume": bar.v
#             }
#             for bar in bars
#         ]
#     except Exception as e:
#         logger.error(f"Error getting bars for {symbol}: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))


# # -------------------------
# # WEBSOCKET FEED
# # -------------------------
# def normalize_alpaca_message(msg):
#     if not msg or not isinstance(msg, list):
#         return None
#     item = msg[0] if len(msg) > 0 else None
#     if not item:
#         return None
#     return {
#         "symbol": item.get("S") or item.get("sym") or item.get("s"),
#         "exchange": "ALPACA",
#         "brokerSymbol": item.get("S") or item.get("sym"),
#         "instrumentType": "Options",
#         "ltp": item.get("p") or item.get("last"),
#         "bid": item.get("bp"),
#         "ask": item.get("ap"),
#         "volume": item.get("s"),
#         "timestamp": datetime.now().timestamp() * 1000
#     }

# async def start_alpaca_feed(broadcast: Callable[[Any], None]):
#     url = ALPACA_WS
#     key = ALPACA_API_KEY
#     secret = ALPACA_SECRET_KEY

#     if not url or not key or not secret:
#         logger.warning("Alpaca credentials missing; skipping WS feed")
#         return

#     while True:
#         try:
#             async with websockets.connect(url) as ws:
#                 logger.info("✅ Alpaca WS connected")

#                 auth_msg = json.dumps({"action": "auth", "key": key, "secret": secret})
#                 await ws.send(auth_msg)

#                 async for raw in ws:
#                     try:
#                         if isinstance(raw, bytes):
#                             msg = msgpack.unpackb(raw, raw=False)
#                         else:
#                             msg = json.loads(raw)

#                         tick = normalize_alpaca_message(msg)
#                         if not tick or not tick.get("symbol"):
#                             continue

#                         # Save to MongoDB
#                         await market_collection.update_one(
#                             {"symbol": tick["symbol"], "exchange": "ALPACA"},
#                             {
#                                 "$set": {
#                                     "brokerSymbol": tick["brokerSymbol"],
#                                     "instrumentType": tick["instrumentType"],
#                                     "ltp": tick["ltp"],
#                                     "bid": tick["bid"],
#                                     "ask": tick["ask"],
#                                     "volume": tick["volume"],
#                                     "updatedAt": datetime.now()
#                                 }
#                             },
#                             upsert=True
#                         )

#                         # Broadcast (to logs or pub/sub)
#                         broadcast({**tick, "source": "ALPACA"})

#                     except Exception as e:
#                         logger.debug(f"Message parse error: {e}")
#                         continue

#         except Exception as e:
#             logger.warning(f"WS closed - retry in 5s: {e}")
#             await asyncio.sleep(5)


# # -------------------------





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


# async def start_alpaca_feed(broadcast: Callable[[Any], None]):
#     url = ALPACA_WS
#     key = ALPACA_API_KEY
#     secret = ALPACA_SECRET_KEY

#     if not url or not key or not secret:
#         logger.warning("Alpaca credentials missing; skipping WS feed")
#         return

#     while True:
#         try:
#             async with websockets.connect(url) as ws:
#                 logger.info("✅ Alpaca WS connected")

#                 auth_msg = json.dumps({"action": "auth", "key": key, "secret": secret})
#                 await ws.send(auth_msg)

#                 async for raw in ws:
#                     try:
#                         msg = (
#                             msgpack.unpackb(raw, raw=False)
#                             if isinstance(raw, bytes)
#                             else json.loads(raw)
#                         )
#                         tick = normalize_alpaca_message(msg)
#                         if not tick or not tick.get("symbol"):
#                             continue

#                         await market_collection.update_one(
#                             {"symbol": tick["symbol"], "exchange": "ALPACA"},
#                             {"$set": {
#                                 "brokerSymbol": tick["brokerSymbol"],
#                                 "instrumentType": tick["instrumentType"],
#                                 "ltp": tick["ltp"],
#                                 "bid": tick["bid"],
#                                 "ask": tick["ask"],
#                                 "volume": tick["volume"],
#                                 "updatedAt": datetime.now(),
#                             }},
#                             upsert=True,
#                         )

#                         broadcast({**tick, "source": "ALPACA"})

#                     except Exception as e:
#                         logger.debug(f"Message parse error: {e}")
#                         continue

#         except Exception as e:
#             logger.warning(f"WS closed - retry in 5s: {e}")
#             await asyncio.sleep(5)


async def start_alpaca_feed(broadcast: Callable[[Any], None]):
    url = ALPACA_WS
    key = ALPACA_API_KEY
    secret = ALPACA_SECRET_KEY

    if not url or not key or not secret:
        logger.warning("Alpaca credentials missing; skipping WS feed")
        return

    while True:
        try:
            async with websockets.connect(url) as ws:
                logger.info("✅ Alpaca WS connected")

                # Authenticate with JSON (not msgpack)
                auth_msg = json.dumps({
                    "action": "auth", 
                    "key": key, 
                    "secret": secret
                })
                await ws.send(auth_msg)

                # Subscribe to quotes (adjust symbols as needed)
                subscribe_msg = json.dumps({
                    "action": "subscribe",
                    "quotes": ["AAPL", "MSFT", "SPY"]  # Add your desired symbols
                })
                await ws.send(subscribe_msg)

                async for raw in ws:
                    try:
                        # Parse JSON message
                        msg = json.loads(raw)
                        
                        # Handle authentication response
                        if msg.get("msg") == "authenticated":
                            logger.info("🔑 Authenticated with Alpaca")
                            continue
                            
                        # Handle subscription response
                        if msg.get("msg") == "subscribed":
                            logger.info(f"✅ Subscribed to: {msg.get('subscriptions', {}).get('quotes', [])}")
                            continue
                            
                        # Handle error messages
                        if msg.get("T") == "error":
                            logger.error(f"Alpaca error: {msg.get('msg')}")
                            continue

                        # Process quote messages
                        if msg.get("T") == "q":  # Quote message
                            tick = {
                                "symbol": msg.get("S"),
                                "exchange": "ALPACA",
                                "brokerSymbol": msg.get("S"),
                                "instrumentType": "Stock",
                                "ltp": None,
                                "bid": msg.get("bp"),
                                "ask": msg.get("ap"),
                                "bid_size": msg.get("bs"),
                                "ask_size": msg.get("as"),
                                "volume": None,
                                "timestamp": datetime.now().timestamp() * 1000,
                            }

                            await market_collection.update_one(
                                {"symbol": tick["symbol"], "exchange": "ALPACA"},
                                {"$set": {
                                    "brokerSymbol": tick["brokerSymbol"],
                                    "instrumentType": tick["instrumentType"],
                                    "ltp": tick["ltp"],
                                    "bid": tick["bid"],
                                    "ask": tick["ask"],
                                    "volume": tick["volume"],
                                    "updatedAt": datetime.now(),
                                }},
                                upsert=True,
                            )

                            broadcast({**tick, "source": "ALPACA"})

                    except Exception as e:
                        logger.debug(f"Message parse error: {e}")
                        continue

        except Exception as e:
            logger.warning(f"WS closed - retry in 5s: {e}")
            await asyncio.sleep(5)