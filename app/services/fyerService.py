# import asyncio
# import json
# import logging
# from datetime import datetime
# from typing import Any, Callable, Set

# import websockets
# from motor.motor_asyncio import AsyncIOMotorClient

# logger = logging.getLogger(__name__)

# # MongoDB Setup
# MONGO_URI = "mongodb+srv://<user>:<pass>@cluster.mongodb.net/?retryWrites=true&w=majority"
# DB_NAME = "market_data"
# mongo_client = AsyncIOMotorClient(MONGO_URI)
# db = mongo_client[DB_NAME]
# market_data = db["fyers"]

# async def start_fyers_feed(
#     broadcast: Callable[[Any], None] = None,
#     subscribed_symbols: Set[str] = None,
# ):
#     import os

#     FYERS_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIl0sImF0X2hhc2giOiJnQUFBQUFCbzZwRF9FT3ZTMnBYSHl5X3ZMZUl3NDl0dkhJMGZnX0VZNmJ1MGJ3YTVaTTlRZzNmLXpWUXdKckNYbU9NZWk2MktnMUl0cEo5MlRFdjIzQk5FQ19PNzJuSWktUXhRUHlLT3VNME1kcGxkQ082cGZmaz0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJlN2ZhZmU2OTdmNTQ4MGNjZjk3M2RjZDVmNzJmYTAwNDgxNjNkNTBiMWJiMTBlM2I2NzgxN2U4YyIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiRkFENDE5MTIiLCJhcHBUeXBlIjoxMDAsImV4cCI6MTc2MDIyOTAwMCwiaWF0IjoxNzYwMjAzMDA3LCJpc3MiOiJhcGkuZnllcnMuaW4iLCJuYmYiOjE3NjAyMDMwMDcsInN1YiI6ImFjY2Vzc190b2tlbiJ9.cPwrP2BC2ezDmip3pDzBaJ0aVXl4ryarzRADiww4vhw"
#     FYERS_WS = "wss://api.fyers.in/socket/v3/data"

#     if not FYERS_ACCESS_TOKEN:
#         logger.warning("⚠️ FYERS_ACCESS_TOKEN not set. Please update your .env daily.")
#         return

#     symbols = subscribed_symbols or {"NSE:NIFTY50-INDEX", "NSE:BANKNIFTY-INDEX"}
#     retry_delay = 5  # initial backoff in seconds
#     max_backoff = 300  # max backoff = 5 min

#     while True:
#         url = f"{FYERS_WS}{FYERS_ACCESS_TOKEN}"
#         logger.info(f"🔌 Connecting to Fyers WS: {url}")

#         try:
#             async with websockets.connect(url) as ws:
#                 logger.info("✅ Connected to Fyers WebSocket")
#                 retry_delay = 5  # reset backoff after successful connection

#                 # Subscribe to symbols
#                 sub_msg = {"symbol": list(symbols)}
#                 await ws.send(json.dumps(sub_msg))
#                 logger.info(f"📡 Subscribed to symbols: {symbols}")

#                 async for raw_msg in ws:
#                     try:
#                         msg = json.loads(raw_msg)
#                         tick = normalize_fyers_message(msg)
#                         if not tick or not tick.get("symbol"):
#                             continue

#                         # Save/update MongoDB
#                         await market_data.update_one(
#                             {"symbol": tick["symbol"], "exchange": "FYERS"},
#                             {"$set": {
#                                 "brokerSymbol": tick["brokerSymbol"],
#                                 "instrumentType": tick["instrumentType"],
#                                 "ltp": tick["ltp"],
#                                 "bid": tick["bid"],
#                                 "ask": tick["ask"],
#                                 "volume": tick["volume"],
#                                 "oi": tick["oi"],
#                                 "updatedAt": datetime.utcnow(),
#                             }},
#                             upsert=True
#                         )

#                         if broadcast:
#                             await broadcast({**tick, "source": "FYERS"})

#                     except Exception as e:
#                         logger.error(f"❌ Error processing Fyers message: {e}")

#         except websockets.exceptions.InvalidStatusCode as e:
#             if e.status_code == 503:
#                 logger.warning(f"🚨 Fyers WS 503 - server busy. Retrying in {retry_delay}s...")
#             else:
#                 logger.error(f"🚨 Fyers WS rejected: {e.status_code} - {e}")

#         except Exception as e:
#             logger.error(f"🚨 Fyers WS connection error: {e}")

#         # Exponential backoff for reconnect
#         logger.info(f"♻️ Reconnecting to Fyers WS in {retry_delay}s...")
#         await asyncio.sleep(retry_delay)
#         retry_delay = min(retry_delay * 2, max_backoff)


# def normalize_fyers_message(msg: dict):
#     """Normalize Fyers WS message"""
#     try:
#         return {
#             "symbol": msg.get("s") or msg.get("symbol"),
#             "exchange": "FYERS",
#             "brokerSymbol": msg.get("s"),
#             "instrumentType": msg.get("instrumentType", "Futures"),
#             "ltp": (msg.get("ltpc", {}).get("ltp") if msg.get("ltpc") else msg.get("ltp")),
#             "bid": (msg.get("ltpc", {}).get("bid") if msg.get("ltpc") else None),
#             "ask": (msg.get("ltpc", {}).get("ask") if msg.get("ltpc") else None),
#             "volume": msg.get("vol"),
#             "oi": msg.get("oi"),
#             "timestamp": datetime.utcnow().timestamp(),
#         }
#     except Exception as e:
#         logger.warning(f"⚠️ Normalization failed: {e}")
#         return None
# app/services/fyerService.py


# # fyerService.py
# import os
# import pandas as pd
# from datetime import datetime
# import logging
# import time
# import asyncio
# from fyers_apiv3.FyersWebsocket import data_ws
# from motor.motor_asyncio import AsyncIOMotorClient
# from dotenv import load_dotenv

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)
# load_dotenv()

# # --- Global configs ---
# csv_file = 'LiveData.csv'

# # --- Fyers credentials from environment variables ---
# access_token = os.getenv("FYERS_ACCESS_TOKEN")
# if not access_token:
#     raise ValueError("FYERS_ACCESS_TOKEN not set in environment variables")

# client_id = os.getenv("CLIENT_ID")
# if not client_id:
#     raise ValueError("FYERS_CLIENT_ID not set in environment variables")

# # --- MongoDB setup ---
# MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
# mongo_client = AsyncIOMotorClient(MONGO_URI)
# market_data = mongo_client["paper_trading"]["market_data"]

# # --- Asyncio loop reference ---
# MAIN_LOOP = asyncio.get_event_loop()

# # Optional: WebSocket broadcast function (set from main.py)
# broadcast_func = None

# # ---------------------------
# # Fyers WebSocket callbacks
# # ---------------------------

# def onmessage(message):
#     """Handle incoming Fyers tick data safely in the main asyncio loop."""
#     try:
#         if "ltp" not in message:
#             return

#         epoch_time = message["last_traded_time"]
#         dt_str = datetime.fromtimestamp(epoch_time).strftime("%Y-%m-%d %H:%M:%S")

#         data = {
#             "symbol": message["symbol"],
#             "ltp": message["ltp"],
#             "high": message["high_price"],
#             "low": message["low_price"],
#             "open": message["open_price"],
#             "close": message["prev_close_price"],
#             "timestamp": dt_str
#         }

#         # Schedule MongoDB update in main loop
#         asyncio.run_coroutine_threadsafe(
#             market_data.update_one(
#                 {"symbol": data["symbol"]},
#                 {"$set": data},
#                 upsert=True
#             ),
#             MAIN_LOOP
#         )

#         # Append to CSV
#         df = pd.DataFrame([data])
#         df.to_csv(csv_file, mode='a', header=not os.path.exists(csv_file), index=False)

#         # Optional: broadcast to connected WebSocket clients
#         if broadcast_func:
#             asyncio.run_coroutine_threadsafe(broadcast_func(data), MAIN_LOOP)

#         logger.info(f"📈 {data['symbol']} | LTP: {data['ltp']}")

#     except Exception as e:
#         logger.error(f"onmessage error: {e}")


# def onerror(message):
#     logger.error(f"Fyers WS error: {message}")


# def onclose(message):
#     logger.info(f"Fyers WS closed: {message}")


# def onopen():
#     """Subscribe to symbols when WebSocket connects."""
#     symbols = ['NSE:RELIANCE-EQ', 'NSE:ITC-EQ']
#     data_type = "SymbolUpdate"
#     fyers.subscribe(symbols=symbols, data_type=data_type)
#     fyers.keep_running()


# # ---------------------------
# # Fyers WebSocket setup
# # ---------------------------

# fyers = data_ws.FyersDataSocket(
#     access_token=access_token,
#     log_path="",           # logs saved in current folder
#     litemode=False,
#     write_to_file=False,
#     reconnect=True,
#     on_connect=onopen,
#     on_close=onclose,
#     on_error=onerror,
#     on_message=onmessage
# )


# def start_fyers_feed(broadcast=None, subscribed_symbols=None):
#     """
#     Start the Fyers WebSocket in a separate thread.
#     :param broadcast: async function to broadcast messages to clients
#     :param subscribed_symbols: optional, list of symbols to subscribe
#     """
#     global broadcast_func
#     broadcast_func = broadcast

#     import threading

#     thread = threading.Thread(target=fyers.connect, daemon=True)
#     thread.start()
#     time.sleep(2)
#     logger.info("✅ Fyers WebSocket Connected")

# fyerService.py
import os
import pandas as pd
from datetime import datetime
import logging
import threading
import time
import asyncio
from fyers_apiv3.FyersWebsocket import data_ws
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# -----------------------
# Logging setup
# -----------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
load_dotenv()


import queue

# Add this near the top with other global configs
message_queue = queue.Queue()


# -----------------------
# Global configs
# -----------------------
csv_file = "LiveData.csv"

# Fyers credentials
access_token = os.getenv("FYERS_ACCESS_TOKEN")
if not access_token:
    raise ValueError("FYERS_ACCESS_TOKEN not set")

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = AsyncIOMotorClient(MONGO_URI)
market_data = mongo_client["paper_trading"]["market_data"]

# Async broadcast function (from main.py)
broadcast_func = None

# Main asyncio loop reference (set from main.py)
MAIN_LOOP: asyncio.AbstractEventLoop | None = None

# -----------------------
# Fyers WebSocket callbacks
# -----------------------
def onmessage(message):
    """Handle incoming Fyers tick data and put it in a queue."""
    try:
        # logger.info(f"Raw Fyers message: {message}")

        if "ltp" not in message:
            return

        epoch_time = message.get("last_traded_time", int(datetime.utcnow().timestamp()))
        dt_str = datetime.fromtimestamp(epoch_time).strftime("%Y-%m-%d %H:%M:%S")

        data = {
            "symbol": message.get("symbol"),
            "ltp": message.get("ltp"),
            "high": message.get("high_price"),
            "low": message.get("low_price"),
            "open": message.get("open_price"),
            "close": message.get("prev_close_price"),
            "timestamp": dt_str
        }

        # Put message in queue for main thread to process
        message_queue.put(data)
        
        # Immediate CSV logging (thread-safe)
        df = pd.DataFrame([data])
        df.to_csv(csv_file, mode="a", header=not os.path.exists(csv_file), index=False)
        # logger.info(f"📈 {data['symbol']} | LTP: {data['ltp']}")

    except Exception as e:
        logger.error(f"onmessage error: {e}")


async def process_fyers_messages():
    """Process Fyers messages from the queue in the main asyncio loop."""
    while True:
        try:
            # Non-blocking queue get with timeout
            data = message_queue.get_nowait()
            
            # Process in main asyncio context
            await market_data.update_one(
                {"symbol": data["symbol"]}, 
                {"$set": data}, 
                upsert=True
            )
            
            if broadcast_func:
                await broadcast_func(data)
                
        except queue.Empty:
            # No messages in queue, sleep a bit
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error processing Fyers message: {e}")


def onerror(message):
    logger.error(f"Fyers WS error: {message}")


def onclose(message):
    logger.info(f"Fyers WS closed: {message}")







# -----------------------
# Start Fyers WebSocket
# -----------------------
def start_fyers_feed(broadcast=None, main_loop=None, subscribed_symbols=None):
    """
    Start Fyers WebSocket in a separate thread.
    :param broadcast: async function to broadcast messages to clients
    :param main_loop: main asyncio loop (required for thread-safe updates)
    :param subscribed_symbols: list of symbols to subscribe
    """
    global broadcast_func, MAIN_LOOP
    broadcast_func = broadcast

    if main_loop is None:
        raise ValueError("main_loop must be passed")
    MAIN_LOOP = main_loop

    if not subscribed_symbols:
        subscribed_symbols = ["NSE:RELIANCE-EQ", "NSE:ITC-EQ"]

    # -----------------------
    # Fyers connect callback
    # -----------------------
    def on_connect():
        fyers.subscribe(symbols=subscribed_symbols, data_type="SymbolUpdate")
        fyers.keep_running()
        logger.info("✅ Fyers WS subscribed and running")

    # -----------------------
    # Create Fyers WebSocket
    # -----------------------
    global fyers
    fyers = data_ws.FyersDataSocket(
        access_token=access_token,
        log_path="",
        litemode=False,
        write_to_file=False,
        reconnect=True,
        on_connect=on_connect,
        on_close=onclose,
        on_error=onerror,
        on_message=onmessage
    )

    # -----------------------
    # Run WebSocket in daemon thread
    # -----------------------
    def run_ws():
        try:
            fyers.connect()
        except Exception as e:
            logger.error(f"Fyers WS failed: {e}")

    thread = threading.Thread(target=run_ws, daemon=True)
    thread.start()
    time.sleep(2)
    logger.info("✅ Fyers WebSocket Connected (thread-safe)")
