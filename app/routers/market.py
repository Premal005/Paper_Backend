


from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from bson import ObjectId
from datetime import datetime
import httpx

from app.models.marketModel import MarketData
from app.services import alpacaService
from app.services import fyerService

router = APIRouter(tags=["Market"])
MT5_SERVICE_URL = "http://13.53.42.25:5000"  # Your MT5 FastAPI service URL
# MT5_SERVICE_URL = "http://localhost:8000"
ALLOWED_EXCHANGES = ["FUTURES", "OPTIONS", "FOREX", "CRYPTO"]

CATEGORY_MAP = {
    "FOREX": ["FOREX"],        # MT5
    "CRYPTO": ["CRYPTO"],      # MT5
    "COMEX": ["COMEX"],        # MT5
    "OPTIONS": ["US_OPTIONS"], # Alpaca
    "FUTURES": ["NSE", "MCX"]  # FYERS
}

# ----------------------
# Helper functions
# ----------------------
async def get_quote_alpaca(symbol: str):
    try:
        rest = alpacaService.get_rest_client()
        quote = rest.get_latest_quote(symbol)

        try:
            asset = rest.get_asset(symbol)
            name = asset.name
            exchange = asset.exchange
        except Exception:
            name = ""
            exchange = "ALPACA"

        return {
            "symbol": symbol,
            "exchange": exchange,
            "name": name,
            "bid": float(getattr(quote, "bp", 0)),
            "ask": float(getattr(quote, "ap", 0)),
            "last_price": float(getattr(quote, "ap", 0)),  # use ask as last
            "timestamp": datetime.utcnow().isoformat(),
            "source": "ALPACA"
        }
    except Exception:
        return None

async def get_quote_fyers(symbol: str):
    
    try:
        doc = await fyerService.market_data.find_one({"symbol": symbol.upper()})
        if not doc:
            return None
        return {
            "symbol": doc.get("symbol", symbol),
            "exchange": "FYERS",
            "bid": doc.get("bid_price", 0),
            "ask": doc.get("ask_price", 0),
            "last_price": doc.get("ltp", 0),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "FYERS"
        }
    except Exception:
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

            # ✅ Add exchange and last_price so search endpoint maps correctly
            data.update({
                "last_price": (data.get("bid", 0) + data.get("ask", 0)) / 2,
                "exchange": "MT5",
                "name": symbol,
                "sector": "CRYPTO" if symbol in ["BTC", "ETH", "XRP", "DOGE"] else "FOREX",
                "timestamp": datetime.utcnow().isoformat(),
                "source": "MT5"
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
    result = await get_quote_alpaca(symbol) or await get_quote_fyers(symbol) or await get_quote_mt5(symbol)

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
        elif exchange == "FUTURES":
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
        # ✅ Catch unexpected errors
        return {"success": False, "error": str(e)}
    