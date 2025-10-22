


from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from bson import ObjectId
from datetime import datetime
import httpx

from app.models.marketModel import MarketData
from app.services import alpacaService
from app.services import fyerService


import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Market"])
MT5_SERVICE_URL = "http://13.53.42.25:5000"  # Your MT5 FastAPI service URL
# MT5_SERVICE_URL = "http://localhost:8000"
ALLOWED_EXCHANGES = ["FUTURES", "OPTIONS", "FOREX", "CRYPTO", "MCX"]

CATEGORY_MAP = {
    "FOREX": ["FOREX"],        # MT5
    "CRYPTO": ["CRYPTO"],      # MT5
    "COMEX": ["COMEX"],        # MT5
    "OPTIONS": ["US_OPTIONS"], # Alpaca
    "FUTURES": ["NSE", "MCX"],  # FYERS
    "MCX": ["COMMODITY"],
}

# ----------------------
# Helper functions
# ----------------------
# async def get_quote_alpaca(symbol: str):
#     try:
#         rest = alpacaService.get_rest_client()
#         quote = rest.get_latest_quote(symbol)
#         logger.info(f"{quote}")
#         try:
#             asset = rest.get_asset(symbol)
#             name = asset.name
#             exchange = asset.exchange
#         except Exception:
#             name = ""
#             exchange = "ALPACA"

#         return {
#             "symbol": symbol,
#             "exchange": exchange,
#             "name": name,
#             "bid": float(getattr(quote, "bp", 0)),
#             "ask": float(getattr(quote, "ap", 0)),
#             "last_price": float(getattr(quote, "ap", 0)),  # use ask as last
#             "timestamp": datetime.utcnow().isoformat(),
#             "source": "ALPACA",
#             "day_change": getattr(quote, "day_change",0),
#             "day_change_percentage":getattr(quote, "day_change_percentage", 0),
#         }
#     except Exception:
#         return None


async def get_quote_alpaca(symbol: str):
    try:
        rest = alpacaService.get_rest_client()
        quote = rest.get_latest_quote(symbol)
        # logger.info(f"{quote}")
        
        # Calculate current price (midpoint between bid and ask)
        bid_price = float(getattr(quote, "bp", 0))
        ask_price = float(getattr(quote, "ap", 0))
        current_price = (bid_price + ask_price) / 2 if bid_price and ask_price else ask_price
        
        try:
            asset = rest.get_asset(symbol)
            name = asset.name
            exchange = asset.exchange
        except Exception:
            name = ""
            exchange = "ALPACA"

        # Calculate day change using historical data
        day_change = 0.0
        day_change_percentage = 0.0
        
        try:
            # Get today's bars to find open price
            today_bars = rest.get_bars(symbol, "1Day", limit=1).df
            if not today_bars.empty:
                open_price = today_bars['open'].iloc[0]
                day_change = current_price - open_price
                day_change_percentage = (day_change / open_price) * 100 if open_price > 0 else 0
        except Exception as e:
            logger.warning(f"Could not calculate day change for {symbol}: {e}")
        # logger.info(f"{day_change}")
        return {
            "symbol": symbol,
            "exchange": exchange,
            "name": name,
            "bid": bid_price,
            "ask": ask_price,
            "last_price": current_price,  # Use midpoint as last price
            "timestamp": datetime.utcnow().isoformat(),
            "source": "ALPACA",
            "day_change": day_change,
            "day_change_percentage": day_change_percentage,
        }
    except Exception as e:
        logger.error(f"Error getting Alpaca quote for {symbol}: {e}")
        return None




# async def get_quote_fyers(symbol: str):
    
#     try:
#         doc = await fyerService.market_data.find_one({"symbol": symbol.upper()})
#         if not doc:
#             return None
#         return {
#             "symbol": doc.get("symbol", symbol),
#             "exchange": "FYERS",
#             "bid": doc.get("bid_price", 0),
#             "ask": doc.get("ask_price", 0),
#             "last_price": doc.get("ltp", 0),
#             "timestamp": datetime.utcnow().isoformat(),
#             "source": "FYERS",
#             "day_change": doc.get("day_change"),
#             "day_change_percentage":doc.get("day_change_percentage"),
#         }
#     except Exception:
#         return None


# async def get_quote_fyers(symbol: str):
#     try:
#         # Convert symbol to FYERS format if needed
#         fyers_symbol = symbol
#         if ":" not in symbol and "-" not in symbol:
#             # Assume it's a basic symbol, try different formats
#             possible_symbols = [
#                 f"NSE:{symbol}-EQ",  # Equity
#                 f"NSE:{symbol}FUT",  # Futures  
#                 f"NSE:{symbol}CE",   # Call Options
#                 f"NSE:{symbol}PE",   # Put Options
#             ]
            
#             for possible_symbol in possible_symbols:
#                 doc = await fyerService.market_data.find_one({"symbol": possible_symbol})
#                 if doc:
#                     fyers_symbol = possible_symbol
#                     break
#         else:
#             doc = await fyerService.market_data.find_one({"symbol": symbol.upper()})
        
#         if not doc:
#             return None
            
#         return {
#             "symbol": doc.get("symbol", symbol),
#             "exchange": "FYERS", 
#             "name": doc.get("symbol", symbol),
#             "bid": doc.get("ltp", 0),
#             "ask": doc.get("ltp", 0), 
#             "last_price": doc.get("ltp", 0),
#             "open": doc.get("open", 0),
#             "high": doc.get("high", 0),
#             "low": doc.get("low", 0),
#             "close": doc.get("close", 0),
#             "volume": doc.get("volume", 0),
#             "timestamp": datetime.utcnow().isoformat(),
#             "source": "FYERS",
#             "day_change": doc.get("day_change", 0),
#             "day_change_percentage": doc.get("day_change_percentage", 0),
#         }
#     except Exception as e:
#         logger.error(f"Error getting FYERS quote for {symbol}: {e}")
#         return None

async def get_quote_fyers(symbol: str):
    try:
        fyers_symbol = symbol
        
        # Check if it's explicitly an MCX or NSE symbol
        if ":" not in symbol and "-" not in symbol:
            # Try both NSE and MCX formats
            possible_symbols = [
                # NSE formats
                f"NSE:{symbol}-EQ",  # Equity
                f"NSE:{symbol}FUT",  # Futures  
                f"NSE:{symbol}CE",   # Call Options
                f"NSE:{symbol}PE",   # Put Options
                
                # MCX formats
                f"MCX:{symbol}FUT",  # MCX Futures
                f"MCX:{symbol}CE",   # MCX Call Options
                f"MCX:{symbol}PE",   # MCX Put Options
                f"MCX:{symbol}",     # MCX Spot
            ]
            
            for possible_symbol in possible_symbols:
                doc = await fyerService.market_data.find_one({"symbol": possible_symbol})
                if doc:
                    fyers_symbol = possible_symbol
                    break
        else:
            # Symbol already has exchange prefix
            doc = await fyerService.market_data.find_one({"symbol": symbol.upper()})
        
        if not doc:
            return None
        
        # Determine exchange from symbol prefix
        if doc.get("symbol", "").startswith("MCX:"):
            exchange = "MCX"
            instrument_type = doc.get("instrument_type", "COMMODITY")
        else:
            exchange = "NSE" 
            instrument_type = doc.get("instrument_type", "EQUITY")
            
        return {
            "symbol": doc.get("symbol", symbol),
            "exchange": exchange,
            "instrument_type": instrument_type,
            "name": doc.get("symbol", symbol),
            "bid": doc.get("ltp", 0),
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
        logger.error(f"Error getting FYERS quote for {symbol}: {e}")
        return None


async def get_quote_mt5(symbol: str):
    print(f"[DEBUG] Starting MT5 quote fetch for symbol: {symbol}")
    async with httpx.AsyncClient() as client:
        try:
            url = f"{MT5_SERVICE_URL}/symbol/{symbol}"
            print(f"[DEBUG] Sending GET request to MT5 service: {url}")
            response = await client.get(url)
            print(f"[DEBUG] Received response with status {response.status_code}")

            if response.status_code != 200:
                print(f"[WARN] MT5 did not return data for {symbol}")
                return None

            data = response.json()
            
            # logger.info(f"{data}")

            # ✅ Add exchange and last_price so search endpoint maps correctly
            data.update({
                "last_price": (data.get("bid", 0) + data.get("ask", 0)) / 2,
                "exchange": "MT5",
                "name": symbol,
                "sector": "CRYPTO" if symbol in ["BTC", "ETH", "XRP", "DOGE"] else "FOREX",
                "timestamp": datetime.utcnow().isoformat(),
                "source": "MT5",
                "day_change": data.get("change"),
                "day_change_percentage":data.get("day_change_percentage"),
            })
            return data

        except Exception as e:
            print(f"[ERROR] Failed to fetch MT5 quote: {e}")

    print(f"[DEBUG] Returning None for symbol: {symbol} (no data fetched)")
    return None



def clean_doc(doc: dict) -> dict:
    """Convert ObjectId to str so FastAPI can serialize it"""
    if not doc:
        return doc
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])
    return doc

# ----------------------
# API Endpoints
# ----------------------

# @router.get("/search")
# async def search_symbol(symbol: str = Query(..., min_length=1)):
#     symbol = symbol.upper()
#     result = await get_quote_alpaca(symbol) or await get_quote_mt5(symbol)
#     if not result:
#         return {
#             "symbol": symbol,
#             "source": None,
#             "data": {
#                 "bid": 0,
#                 "ask": 0,
#                 "last_price": 0,
#                 "timestamp": datetime.utcnow().isoformat(),
#                 "note": "Symbol not found in any broker"
#             }
#         }
#     return {"symbol": symbol, "source": result.get("source"), "data": result}


@router.get("/search")
async def search_symbol(symbol: str = Query(..., min_length=1)):
    symbol = symbol.upper()
    result = await get_quote_fyers(symbol) or await get_quote_mt5(symbol) or await get_quote_alpaca(symbol) 

    if not result:
        return []

    # Map to marketSearchResponse format
    formatted = [{
        "symbol": result.get("symbol", symbol),
        "exchange": result.get("exchange", ""),
        "name": result.get("name", ""),  # add mapping if available
        "sector": result.get("sector", ""),  # add mapping if available
        "current_price": result.get("last_price", 0),
        "day_change": result.get("day_change", 0),
        "day_change_percentage": result.get("day_change_percentage", 0)
    }]
    return formatted



@router.get("/category/{type}")
async def get_market_by_category(type: str):
    type_normalized = type.strip().upper()
    if type_normalized not in ALLOWED_EXCHANGES:
        raise HTTPException(status_code=400, detail="Invalid type")
    try:
        cursor = MarketData.collection.find({
            "exchange": {"$regex": f"^{type_normalized}$", "$options": "i"}
        }).limit(200)
        results = await cursor.to_list(length=200)

        formatted = [
            {
                "symbol": doc.get("symbol", ""),
                "exchange": doc.get("exchange", ""),
                "name": doc.get("name", ""),
                "sector": doc.get("sector", ""),
                "current_price": doc.get("current_price", 0),
                "day_change": doc.get("day_change", 0),
                "day_change_percentage": doc.get("day_change_percentage", 0)
            }
            for doc in results
        ]
        return formatted
    except Exception as e:
        return {"error": str(e), "data": []}


# @router.get("/{exchange}/{symbol}")
# async def get_single_market(exchange: str, symbol: str, category: Optional[str] = None):
#     try:
#         exchange = exchange.strip().upper()
#         symbol = symbol.strip().upper()
#         category = category.strip().upper() if category else None

#         # ✅ Validate exchange
#         if exchange not in ALLOWED_EXCHANGES:
#             return {
#                 "success": False,
#                 "error": f"Exchange must be one of {ALLOWED_EXCHANGES}"
#             }

#         # ✅ Validate category
#         allowed_categories = CATEGORY_MAP.get(exchange, [])
#         if category and category not in allowed_categories:
#             return {
#                 "success": False,
#                 "error": f"Category for {exchange} must be one of {allowed_categories}"
#             }

#         # ✅ Fetch market data
#         item = None
#         if exchange in ["FOREX", "CRYPTO", "COMEX"]:
#             item = await get_quote_mt5(symbol)
#         elif exchange == "OPTIONS":
#             item = await get_quote_alpaca(symbol)
#         elif exchange == "FUTURES":
#             item = await get_quote_fyers(symbol)

#         # ✅ Fallback response if no data found
#         if not item:
#             return {
#                 "success": False,
#                 "data": {
#                     "symbol": symbol,
#                     "exchange": exchange,
#                     "name": "",
#                     "sector": "",
#                     "current_price": 0,
#                     "day_change": 0,
#                     "day_change_percentage": 0,
#                     "open": 0,
#                     "high": 0,
#                     "low": 0,
#                     "volume": 0,
#                     "market_cap": 0
#                 },
#                 "note": "Market data not found"
#             }

#         # ✅ Map fields safely
#         mapped = {
#             "symbol": item.get("symbol", symbol),
#             "exchange": item.get("exchange", exchange),
#             "name": item.get("name", ""),
#             "sector": item.get("sector", ""),
#             "current_price": item.get("last_price", 0),
#             "day_change": item.get("day_change", 0),
#             "day_change_percentage": item.get("day_change_percentage", 0),
#             "open": item.get("open", 0),
#             "high": item.get("high", 0),
#             "low": item.get("low", 0),
#             "volume": item.get("volume", 0),
#             "market_cap": item.get("market_cap", 0),
#         }

#         return {"success": True, "data": mapped}

#     except Exception as e:
#         # ✅ Catch unexpected errors
#         return {"success": False, "error": str(e)}
    


@router.get("/{exchange}/{symbol}")
async def get_single_market(exchange: str, symbol: str, category: Optional[str] = None):
    try:
        exchange = exchange.strip().upper()
        symbol = symbol.strip().upper()
        category = category.strip().upper() if category else None

        # ✅ Validate exchange
        if exchange not in ALLOWED_EXCHANGES:
            return {
                "success": False,
                "error": f"Exchange must be one of {ALLOWED_EXCHANGES}"
            }

        # ✅ Validate category
        allowed_categories = CATEGORY_MAP.get(exchange, [])
        if category and category not in allowed_categories:
            return {
                "success": False,
                "error": f"Category for {exchange} must be one of {allowed_categories}"
            }

        # ✅ Fetch market data
        item = None
        if exchange in ["FOREX", "CRYPTO", "COMEX"]:
            item = await get_quote_mt5(symbol)
        elif exchange == "OPTIONS":
            item = await get_quote_alpaca(symbol)
        elif exchange in ["FUTURES", "MCX"]:  # UPDATE: Both NSE and MCX
            item = await get_quote_fyers(symbol)

        # ✅ Fallback response if no data found
        if not item:
            return {
                "success": False,
                "data": {
                    "symbol": symbol,
                    "exchange": exchange,
                    "name": "",
                    "sector": "",
                    "current_price": 0,
                    "day_change": 0,
                    "day_change_percentage": 0,
                    "open": 0,
                    "high": 0,
                    "low": 0,
                    "volume": 0,
                    "market_cap": 0
                },
                "note": "Market data not found"
            }

        # ✅ Map fields safely
        mapped = {
            "symbol": item.get("symbol", symbol),
            "exchange": item.get("exchange", exchange),
            "name": item.get("name", ""),
            "sector": item.get("sector", ""),
            "current_price": item.get("last_price", 0),
            "day_change": item.get("day_change", 0),
            "day_change_percentage": item.get("day_change_percentage", 0),
            "open": item.get("open", 0),
            "high": item.get("high", 0),
            "low": item.get("low", 0),
            "volume": item.get("volume", 0),
            "market_cap": item.get("market_cap", 0),
        }

        return {"success": True, "data": mapped}

    except Exception as e:
        return {"success": False, "error": str(e)}    