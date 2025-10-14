
# # fyerService.py
# import os
# import pandas as pd
# from datetime import datetime
# import logging
# import threading
# import time
# import asyncio
# from fyers_apiv3.FyersWebsocket import data_ws
# from motor.motor_asyncio import AsyncIOMotorClient
# from dotenv import load_dotenv

# # -----------------------
# # Logging setup
# # -----------------------
# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)
# load_dotenv()


# import queue

# # Add this near the top with other global configs
# message_queue = queue.Queue()


# # -----------------------
# # Global configs
# # -----------------------
# csv_file = "LiveData.csv"

# # Fyers credentials
# access_token = os.getenv("FYERS_ACCESS_TOKEN")
# if not access_token:
#     raise ValueError("FYERS_ACCESS_TOKEN not set")

# # MongoDB setup
# MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
# mongo_client = AsyncIOMotorClient(MONGO_URI)
# market_data = mongo_client["paper_trading"]["market_data"]

# # Async broadcast function (from main.py)
# broadcast_func = None

# # Main asyncio loop reference (set from main.py)
# MAIN_LOOP: asyncio.AbstractEventLoop | None = None

# # -----------------------
# # Fyers WebSocket callbacks
# # -----------------------
# # def onmessage(message):
# #     """Handle incoming Fyers tick data and put it in a queue."""
# #     try:
# #         # logger.info(f"Raw Fyers message: {message}")

# #         if "ltp" not in message:
# #             return

# #         epoch_time = message.get("last_traded_time", int(datetime.utcnow().timestamp()))
# #         dt_str = datetime.fromtimestamp(epoch_time).strftime("%Y-%m-%d %H:%M:%S")

# #         data = {
# #             "symbol": message.get("symbol"),
# #             "ltp": message.get("ltp"),
# #             "high": message.get("high_price"),
# #             "low": message.get("low_price"),
# #             "open": message.get("open_price"),
# #             "close": message.get("prev_close_price"),
# #             "timestamp": dt_str
# #         }

# #         # Put message in queue for main thread to process
# #         message_queue.put(data)
        
# #         # Immediate CSV logging (thread-safe)
# #         df = pd.DataFrame([data])
# #         df.to_csv(csv_file, mode="a", header=not os.path.exists(csv_file), index=False)
# #         # logger.info(f"📈 {data['symbol']} | LTP: {data['ltp']}")

# #     except Exception as e:
# #         logger.error(f"onmessage error: {e}")



# def onmessage(message):
#     """Handle incoming Fyers tick data and put it in a queue."""
#     try:
#         # logger.info(f"Raw Fyers message: {message}")

#         if "ltp" not in message:
#             return

#         epoch_time = message.get("last_traded_time", int(datetime.utcnow().timestamp()))
#         dt_str = datetime.fromtimestamp(epoch_time).strftime("%Y-%m-%d %H:%M:%S")

#         current_price = message.get("ltp")
#         open_price = message.get("open_price", 0)
        
#         # Calculate day change
#         day_change = 0.0
#         day_change_percentage = 0.0
        
#         if open_price and open_price > 0:
#             day_change = current_price - open_price
#             day_change_percentage = (day_change / open_price) * 100

#         data = {
#             "symbol": message.get("symbol"),
#             "ltp": current_price,
#             "high": message.get("high_price"),
#             "low": message.get("low_price"),
#             "open": open_price,
#             "close": message.get("prev_close_price"),
#             "day_change": day_change,
#             "day_change_percentage": day_change_percentage,
#             "timestamp": dt_str
#         }

#         # Put message in queue for main thread to process
#         message_queue.put(data)
        
#         # Immediate CSV logging (thread-safe)
#         df = pd.DataFrame([data])
#         df.to_csv(csv_file, mode="a", header=not os.path.exists(csv_file), index=False)
#         # logger.info(f"📈 {data['symbol']} | LTP: {data['ltp']} | Change: {day_change_percentage:.2f}%")

#     except Exception as e:
#         logger.error(f"onmessage error: {e}")





# async def process_fyers_messages():
#     """Process Fyers messages from the queue in the main asyncio loop."""
#     while True:
#         try:
#             # Non-blocking queue get with timeout
#             data = message_queue.get_nowait()
            
#             # Process in main asyncio context
#             await market_data.update_one(
#                 {"symbol": data["symbol"]}, 
#                 {"$set": data}, 
#                 upsert=True
#             )
            
#             if broadcast_func:
#                 await broadcast_func(data)
                
#         except queue.Empty:
#             # No messages in queue, sleep a bit
#             await asyncio.sleep(0.1)
#         except Exception as e:
#             logger.error(f"Error processing Fyers message: {e}")


# def onerror(message):
#     logger.error(f"Fyers WS error: {message}")


# def onclose(message):
#     logger.info(f"Fyers WS closed: {message}")







# # -----------------------
# # Start Fyers WebSocket
# # -----------------------
# def start_fyers_feed(broadcast=None, main_loop=None, subscribed_symbols=None):
#     """
#     Start Fyers WebSocket in a separate thread.
#     :param broadcast: async function to broadcast messages to clients
#     :param main_loop: main asyncio loop (required for thread-safe updates)
#     :param subscribed_symbols: list of symbols to subscribe
#     """
#     global broadcast_func, MAIN_LOOP
#     broadcast_func = broadcast

#     if main_loop is None:
#         raise ValueError("main_loop must be passed")
#     MAIN_LOOP = main_loop

#     if not subscribed_symbols:
#         subscribed_symbols = ["NSE:RELIANCE-EQ", "NSE:ITC-EQ"]

#     # -----------------------
#     # Fyers connect callback
#     # -----------------------
#     def on_connect():
#         fyers.subscribe(symbols=subscribed_symbols, data_type="SymbolUpdate")
#         fyers.keep_running()
#         logger.info("✅ Fyers WS subscribed and running")

#     # -----------------------
#     # Create Fyers WebSocket
#     # -----------------------
#     global fyers
#     fyers = data_ws.FyersDataSocket(
#         access_token=access_token,
#         log_path="",
#         litemode=False,
#         write_to_file=False,
#         reconnect=True,
#         on_connect=on_connect,
#         on_close=onclose,
#         on_error=onerror,
#         on_message=onmessage
#     )

#     # -----------------------
#     # Run WebSocket in daemon thread
#     # -----------------------
#     def run_ws():
#         try:
#             fyers.connect()
#         except Exception as e:
#             logger.error(f"Fyers WS failed: {e}")

#     thread = threading.Thread(target=run_ws, daemon=True)
#     thread.start()
#     time.sleep(2)
#     logger.info("✅ Fyers WebSocket Connected (thread-safe)")




import os
import pandas as pd
from datetime import datetime
import logging
import threading
import time
import asyncio
import queue
from fyers_apiv3.FyersWebsocket import data_ws
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# -----------------------
# Logging setup
# -----------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
load_dotenv()

# Message queue for thread-safe processing
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
# FYERS Symbol Format Helper
# -----------------------

def get_fyers_symbol_format(symbol: str, instrument_type: str = "EQ") -> str:
    """
    Convert symbol to FYERS format based on instrument type
    Formats:
    - Equity: NSE:SYMBOL-EQ
    - Futures: NSE:SYMBOLYYMMFUT
    - Options: NSE:SYMBOLYYMMSTRIKEPE/C
    """
    symbol = symbol.upper().strip()
    
    if instrument_type == "FUTURES":
        # Example: RELIANCE Sep 2024 -> NSE:RELIANCE24SEPFUT
        # You'll need to implement date parsing based on your symbol format
        return f"NSE:{symbol}FUT"  # Adjust based on your futures symbol format
    
    elif instrument_type == "OPTIONS":
        # Example: RELIANCE 1500 CE Sep 2024 -> NSE:RELIANCE24SEP1500CE
        return f"NSE:{symbol}"  # Adjust based on your options symbol format
    
    else:  # EQ - Equity
        return f"NSE:{symbol}-EQ"

# -----------------------
# Fyers WebSocket callbacks
# -----------------------

def onmessage(message):
    """Handle incoming Fyers tick data and put it in a queue."""
    try:
        logger.debug(f"Raw Fyers message: {message}")

        # Check if this is a valid tick message
        if "ltp" not in message and "lp" not in message:
            return

        # Extract symbol and determine instrument type
        symbol = message.get("symbol", "")
        instrument_type = "EQ"  # Default to equity
        
        # Detect instrument type from symbol
        if "FUT" in symbol:
            instrument_type = "FUTURES"
        elif "CE" in symbol or "PE" in symbol:
            instrument_type = "OPTIONS"
        
        # Extract prices with fallbacks for different message formats
        current_price = message.get("ltp") or message.get("lp") or 0
        open_price = message.get("open_price") or message.get("price_open") or 0
        high_price = message.get("high_price") or message.get("high") or 0
        low_price = message.get("low_price") or message.get("low") or 0
        close_price = message.get("prev_close_price") or message.get("close") or 0
        volume = message.get("vol_traded") or message.get("volume") or 0
        
        # Calculate day change
        day_change = 0.0
        day_change_percentage = 0.0
        
        if open_price and open_price > 0:
            day_change = current_price - open_price
            day_change_percentage = (day_change / open_price) * 100

        epoch_time = message.get("last_traded_time", int(datetime.utcnow().timestamp()))
        dt_str = datetime.fromtimestamp(epoch_time).strftime("%Y-%m-%d %H:%M:%S")

        data = {
            "symbol": symbol,
            "instrument_type": instrument_type,
            "ltp": current_price,
            "high": high_price,
            "low": low_price,
            "open": open_price,
            "close": close_price,
            "volume": volume,
            "day_change": day_change,
            "day_change_percentage": day_change_percentage,
            "timestamp": dt_str,
            "source": "FYERS"
        }

        # Put message in queue for main thread to process
        message_queue.put(data)
        
        # Immediate CSV logging (thread-safe)
        df = pd.DataFrame([data])
        df.to_csv(csv_file, mode="a", header=not os.path.exists(csv_file), index=False)
        # logger.info(f"📈 {data['symbol']} | LTP: {data['ltp']} | Type: {instrument_type}")

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

    # Default symbols if none provided
    if not subscribed_symbols:
        subscribed_symbols = [
            # Equity
            "NSE:RELIANCE-EQ", 
            "NSE:TCS-EQ",
            # Futures (example formats)
            "NSE:BANKNIFTY24SEPFUT",  # BANKNIFTY Sep 2024 Futures
            "NSE:NIFTY24SEPFUT",      # NIFTY Sep 2024 Futures
            # Options (example formats)  
            "NSE:BANKNIFTY2422945000CE",  # BANKNIFTY 45000 CE
            "NSE:BANKNIFTY2422945000PE",  # BANKNIFTY 45000 PE
        ]

    # -----------------------
    # Fyers connect callback
    # -----------------------
    def on_connect():
        fyers.subscribe(symbols=subscribed_symbols, data_type="SymbolUpdate")
        fyers.keep_running()
        logger.info(f"✅ Fyers WS subscribed to {len(subscribed_symbols)} symbols")

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

# -----------------------
# Helper function to get FYERS quote
# -----------------------
async def get_quote_fyers(symbol: str):
    try:
        # Try exact match first
        doc = await market_data.find_one({"symbol": symbol.upper()})
        if not doc:
            return None
        
        return {
            "symbol": doc.get("symbol", symbol),
            "exchange": "FYERS",
            "name": doc.get("symbol", symbol),  # Use symbol as name if not available
            "bid": doc.get("ltp", 0),  # FYERS doesn't always provide bid/ask in WS
            "ask": doc.get("ltp", 0),
            "last_price": doc.get("ltp", 0),
            "open": doc.get("open", 0),
            "high": doc.get("high", 0),
            "low": doc.get("low", 0),
            "close": doc.get("close", 0),
            "volume": doc.get("volume", 0),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "FYERS",
            "day_change": doc.get("day_change", 0),
            "day_change_percentage": doc.get("day_change_percentage", 0),
        }
    except Exception as e:
        logger.error(f"Error getting FYERS quote: {e}")
        return None