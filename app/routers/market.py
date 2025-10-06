# # from fastapi import APIRouter, Query, HTTPException
# # from typing import List, Optional

# # from app.models.marketModel import MarketData

# # router = APIRouter( tags=["Market"])

# # # ---------- Search by symbol or partial name ----------
# # @router.get("/search")
# # async def search_market(query: Optional[str] = Query("", alias="query"), limit: int = Query(50)):
# #     try:
# #         cursor = MarketData.collection.find({
# #             "symbol": {"$regex": query, "$options": "i"}
# #         }).limit(limit)
# #         results = await cursor.to_list(length=limit)
# #         return results
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=str(e))


# # # ---------- Get by category / tab: Futures | Options | Forex | Crypto ----------
# # @router.get("/category/{type}")
# # async def get_market_by_category(type: str):
# #     allowed = ["Futures", "Options", "Forex", "Crypto"]
# #     if type not in allowed:
# #         raise HTTPException(status_code=400, detail="Invalid type")

# #     try:
# #         cursor = MarketData.collection.find({"instrumentType": type}).limit(200)
# #         results = await cursor.to_list(length=200)
# #         return results
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=str(e))


# # # ---------- Get single symbol latest ----------
# # @router.get("/{exchange}/{symbol}")
# # async def get_single_market(exchange: str, symbol: str):
# #     try:
# #         item = await MarketData.collection.find_one({"exchange": exchange.upper(), "symbol": symbol})
# #         if not item:
# #             raise HTTPException(status_code=404, detail="Not found")
# #         return item
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=str(e))


# # from fastapi import APIRouter, Query, HTTPException
# # from typing import List, Optional
# # from bson import ObjectId
# # from datetime import datetime
# # import asyncio
# # import httpx


# # from app.models.marketModel import MarketData
# # from app.services import alpacaService
# # from app.services import fyerService


# # router = APIRouter(tags=["Market"])
# # MT5_SERVICE_URL = "http://localhost:8000"  # Your MT5 FastAPI service URL
# # ALLOWED_EXCHANGES = ["FUTURES", "OPTIONS", "FOREX", "CRYPTO"]
# # from fastapi import APIRouter, Query, HTTPException
# # from typing import List, Optional
# # from bson import ObjectId
# # from datetime import datetime
# # import asyncio
# # import httpx


# # from app.models.marketModel import MarketData
# # from app.services import alpacaService
# # from app.services import fyerService


# # router = APIRouter(tags=["Market"])
# # MT5_SERVICE_URL = "http://localhost:8000"  # Your MT5 FastAPI service URL
# # ALLOWED_EXCHANGES = ["FUTURES", "OPTIONS", "FOREX", "CRYPTO"]
# # CATEGORY_MAP = {
# #     "FOREX": ["FOREX"],        # MT5
# #     "CRYPTO": ["CRYPTO"],      # MT5
# #     "COMEX": ["COMEX"],        # MT5
# #     "OPTIONS": ["US_OPTIONS"], # Alpaca
# #     "FUTURES": ["NSE", "MCX"]  # FYERS
# # }
# # # ----------------------
# # # Helper functions
# # # ----------------------
# # async def get_quote_alpaca(symbol: str):
# #     try:
# #         rest = alpacaService.get_rest_client()
# #         quote = rest.get_latest_quote(symbol)
# #         return {
# #             "symbol": symbol,
# #             "exchange": "ALPACA",
# #             "bid": float(getattr(quote, "bp", 0)),
# #             "ask": float(getattr(quote, "ap", 0)),
# #             "last_price": float(getattr(quote, "ap", 0)),  # use ask as last
# #             "timestamp": datetime.utcnow().isoformat(),
# #             "source": "ALPACA"
# #         }
# #     except Exception:
# #         return None


# # async def get_quote_fyers(symbol: str):
# #     token_data = fyerService.load_token()
# #     if not token_data:
# #         return None
# #     try:
# #         # Search Fyers MongoDB for latest tick
# #         doc = await fyerService.market_data.find_one({"symbol": symbol.upper()})
# #         if not doc:
# #             return None
# #         return {
# #             "symbol": doc["symbol"],
# #             "exchange": "FYERS",
# #             "bid": doc.get("bid"),
# #             "ask": doc.get("ask"),
# #             "last_price": doc.get("ltp"),
# #             "timestamp": datetime.utcnow().isoformat(),
# #             "source": "FYERS"
# #         }
# #     except Exception:
# #         return None


# # import httpx


# # MT5_SERVICE_URL = "http://localhost:8000"  # make sure this is defined

# # async def get_quote_mt5(symbol: str):
# #     """
# #     Fetch quote from MT5 service running on localhost:8000
# #     """
# #     print(f"[DEBUG] Starting MT5 quote fetch for symbol: {symbol}")

# #     async with httpx.AsyncClient() as client:
# #         try:
# #             url = f"{MT5_SERVICE_URL}/symbol/{symbol}"
# #             print(f"[DEBUG] Sending GET request to MT5 service: {url}")

# #             response = await client.get(url)
# #             print(f"[DEBUG] Received response with status {response.status_code}")

# #             response.raise_for_status()

# #             # Attempt to parse JSON
# #             data = response.json()
# #             print(f"[DEBUG] MT5 raw response data: {data}")

# #             # Add additional fields if needed
# #             data.update({
# #                 "timestamp": datetime.utcnow().isoformat(),
# #                 "source": "MT5"
# #             })
# #             print(f"[DEBUG] Returning enriched MT5 data: {data}")

# #             return data

# #         except httpx.HTTPStatusError as e:
# #             print(f"[ERROR] MT5 service returned error (HTTP {e.response.status_code}): {e.response.text}")

# #         except httpx.RequestError as e:
# #             print(f"[ERROR] MT5 request failed (network issue): {e}")

# #         except Exception as e:
# #             print(f"[ERROR] Failed to fetch MT5 quote: {e}")

# #     print(f"[DEBUG] Returning None for symbol: {symbol} (no data fetched)")
# #     return None


# # # -------- Helper to fix Mongo ObjectId --------
# # def clean_doc(doc: dict) -> dict:
# #     """Convert ObjectId to str so FastAPI can serialize it"""
# #     if not doc:
# #         return doc
# #     if "_id" in doc and isinstance(doc["_id"], ObjectId):
# #         doc["_id"] = str(doc["_id"])
# #     return doc


# # # ---------- Search by symbol or partial name ----------
# # # @router.get("/search")
# # # async def search_market(query: Optional[str] = Query("", alias="query"), limit: int = Query(50)):
# # #     try:
# # #         cursor = MarketData.collection.find({
# # #             "symbol": {"$regex": query, "$options": "i"}
# # #         }).limit(limit)
# # #         results = await cursor.to_list(length=limit)
# # #         return [clean_doc(doc) for doc in results]
# # #     except Exception as e:
# # #         raise HTTPException(status_code=500, detail=str(e))
# # # @router.get("/search")
# # # async def search_market(query: Optional[str] = Query("", alias="query"), limit: int = Query(50)):
# # #     try:
# # #         cursor = MarketData.collection.find({
# # #             "symbol": {"$regex": query, "$options": "i"}
# # #         }).limit(limit)
# # #         results = await cursor.to_list(length=limit)

# # #         formatted = [
# # #             {
# # #                 "symbol": doc.get("symbol"),
# # #                 "exchange": doc.get("exchange"),
# # #                 "name": doc.get("name"),
# # #                 "sector": doc.get("sector"),
# # #                 "current_price": doc.get("current_price"),
# # #                 "day_change": doc.get("day_change"),
# # #                 "day_change_percentage": doc.get("day_change_percentage")
# # #             }
# # #             for doc in results
# # #         ]
# # #         return formatted
# # #     except Exception as e:
# # #         raise HTTPException(status_code=500, detail=str(e))

# # # ---------- Get by category / tab: Futures | Options | Forex | Crypto ----------
# # # ---------- Get by category / tab: Futures | Options | Forex | Crypto ----------
# # # @router.get("/category/{type}")
# # # async def get_market_by_category(type: str):
# # #     # Normalize input: strip spaces and uppercase
# # #     type_normalized = type.strip().upper()
    
# # #     # Allowed types in uppercase
# # #     allowed = ["FUTURES", "OPTIONS", "FOREX", "CRYPTO"]
# # #     if type_normalized not in allowed:
# # #         raise HTTPException(status_code=400, detail="Invalid type")

# # #     try:
# # #         # Case-insensitive regex match to avoid DB case issues
# # #         cursor = MarketData.collection.find({
# # #             "exchange": {"$regex": f"^{type_normalized}$", "$options": "i"}
# # #         }).limit(200)
# # #         results = await cursor.to_list(length=200)
# # #         return [clean_doc(doc) for doc in results]
# # #     except Exception as e:
# # #         raise HTTPException(status_code=500, detail=str(e))


# # # ----------------------
# # # Search Endpoint
# # # ----------------------
# # # @router.get("/search")
# # # async def search_symbol(symbol: str = Query(..., min_length=1)):
# # #     symbol = symbol.upper()
    
# # #     # Check Alpaca first
# # #     result = await get_quote_alpaca(symbol)
# # #     if result:
# # #         return result

# # #     # Check Fyers
# # #     # result = await get_quote_fyers(symbol)
# # #     # if result:
# # #     #     return result

# # #     # Check MT5
# # #     result = await get_quote_mt5(symbol)
# # #     if result:
        
# # #         return result

# # #     raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found in any broker")




# # @router.get("/search")
# # async def search_symbol(symbol: str = Query(..., min_length=1)):
# #     symbol = symbol.upper()
# #     print(f"[DEBUG] Received search request for symbol: {symbol}")

# #     # --- Check Alpaca ---
# #     print(f"[DEBUG] Checking Alpaca for symbol: {symbol}")
# #     result = await get_quote_alpaca(symbol)
# #     if result:
# #         print(f"[DEBUG] Found symbol '{symbol}' in Alpaca: {result}")
# #         return {
# #             "source": "Alpaca",
# #             "symbol": symbol,
# #             "data": result
# #         }
# #     else:
# #         print(f"[DEBUG] Symbol '{symbol}' not found in Alpaca")

# #     # --- Check Fyers (optional) ---
# #     # print(f"[DEBUG] Checking Fyers for symbol: {symbol}")
# #     # result = await get_quote_fyers(symbol)
# #     # if result:
# #     #     print(f"[DEBUG] Found symbol '{symbol}' in Fyers: {result}")
# #     #     return {
# #     #         "source": "Fyers",
# #     #         "symbol": symbol,
# #     #         "data": result
# #     #     }
# #     # else:
# #     #     print(f"[DEBUG] Symbol '{symbol}' not found in Fyers")

# #     # --- Check MT5 ---
# #     print(f"[DEBUG] Checking MT5 for symbol: {symbol}")
# #     result = await get_quote_mt5(symbol)
# #     if result:
# #         print(f"[DEBUG] Found symbol '{symbol}' in MT5: {result}")
# #         return {
# #             "source": "MT5",
# #             "symbol": symbol,
# #             "data": result
# #         }
# #     else:
# #         print(f"[DEBUG] Symbol '{symbol}' not found in MT5")

# #     # --- If not found anywhere ---
# #     error_msg = f"Symbol '{symbol}' not found in any broker"
# #     print(f"[ERROR] {error_msg}")
# #     raise HTTPException(status_code=404, detail=error_msg)



# # @router.get("/category/{type}")
# # async def get_market_by_category(type: str):
# #     type_normalized = type.strip().upper()
# #     allowed = ["FUTURES", "OPTIONS", "FOREX", "CRYPTO"]
# #     if type_normalized not in allowed:
# #         raise HTTPException(status_code=400, detail="Invalid type")

# #     try:
# #         cursor = MarketData.collection.find({
# #             "exchange": {"$regex": f"^{type_normalized}$", "$options": "i"}
# #         }).limit(200)
# #         results = await cursor.to_list(length=200)

# #         formatted = [
# #             {
# #                 "symbol": doc.get("symbol"),
# #                 "exchange": doc.get("exchange"),
# #                 "name": doc.get("name"),
# #                 "sector": doc.get("sector"),
# #                 "current_price": doc.get("current_price"),
# #                 "day_change": doc.get("day_change"),
# #                 "day_change_percentage": doc.get("day_change_percentage")
# #             }
# #             for doc in results
# #         ]
# #         return formatted
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=str(e))
# # # ---------- Get single symbol latest ----------
# # # @router.get("/{exchange}/{symbol}")
# # # async def get_single_market(exchange: str, symbol: str):
# # #     try:
# # #         # Normalize input
# # #         exchange = exchange.strip()
# # #         symbol = symbol.strip()

# # #         # Case-insensitive search using regex
# # #         item = await MarketData.collection.find_one({
# # #             "exchange": {"$regex": f"^{exchange}$", "$options": "i"},
# # #             "symbol": {"$regex": f"^{symbol}$", "$options": "i"}
# # #         })

# # #         if not item:
# # #             raise HTTPException(status_code=404, detail="Not found")

# # #         return clean_doc(item)

# # #     except Exception as e:
# # #         raise HTTPException(status_code=500, detail=str(e))

# # # @router.get("/{exchange}/{symbol}")
# # # async def get_single_market(exchange: str, symbol: str):
# # #     try:
# # #         exchange = exchange.strip()
# # #         symbol = symbol.strip()

# # #         item = await MarketData.collection.find_one({
# # #             "exchange": {"$regex": f"^{exchange}$", "$options": "i"},
# # #             "symbol": {"$regex": f"^{symbol}$", "$options": "i"}
# # #         })

# # #         if not item:
# # #             raise HTTPException(status_code=404, detail="Not found")

# # #         data = {
# # #             "symbol": item.get("symbol"),
# # #             "exchange": item.get("exchange"),
# # #             "name": item.get("name"),
# # #             "sector": item.get("sector"),
# # #             "current_price": item.get("current_price"),
# # #             "day_change": item.get("day_change"),
# # #             "day_change_percentage": item.get("day_change_percentage"),
# # #             "open": item.get("open"),
# # #             "high": item.get("high"),
# # #             "low": item.get("low"),
# # #             "volume": item.get("volume"),
# # #             "market_cap": item.get("market_cap"),
# # #         }

# # #         return {"success": True, "data": data}

# # #     except Exception as e:
# # #         raise HTTPException(status_code=500, detail=str(e))

# # @router.get("/{exchange}/{symbol}")
# # async def get_single_market(exchange: str, symbol: str, category: str = None):
# #     try:
# #         # Normalize inputs
# #         exchange = exchange.strip().upper()
# #         symbol = symbol.strip().upper()
# #         category = category.strip().upper() if category else None

# #         # Validate exchange
# #         if exchange not in ALLOWED_EXCHANGES:
# #             raise HTTPException(status_code=400, detail=f"Exchange must be one of {ALLOWED_EXCHANGES}")

# #         # Validate category
# #         allowed_categories = CATEGORY_MAP.get(exchange, [])
# #         if category and category not in allowed_categories:
# #             raise HTTPException(status_code=400, detail=f"Category for {exchange} must be one of {allowed_categories}")

# #         # Fetch data based on exchange
# #         item = None
# #         if exchange in ["FOREX", "CRYPTO", "COMEX"]:
# #             item = await get_quote_mt5(symbol)
# #         elif exchange == "OPTIONS":
# #             item = await get_quote_alpaca(symbol)
# #         # elif exchange == "FUTURES":
# #         #     item = await get_quote_fyers(symbol)

# #         if not item:
# #             raise HTTPException(status_code=404, detail="Market data not found")

# #         return item

# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=str(e))
# # # ----------------------
# # # Helper functions
# # # ----------------------
# # async def get_quote_alpaca(symbol: str):
# #     try:
# #         rest = alpacaService.get_rest_client()
# #         quote = rest.get_latest_quote(symbol)
# #         return {
# #             "symbol": symbol,
# #             "exchange": "ALPACA",
# #             "bid": float(getattr(quote, "bp", 0)),
# #             "ask": float(getattr(quote, "ap", 0)),
# #             "last_price": float(getattr(quote, "ap", 0)),  # use ask as last
# #             "timestamp": datetime.utcnow().isoformat(),
# #             "source": "ALPACA"
# #         }
# #     except Exception:
# #         return None


# # async def get_quote_fyers(symbol: str):
# #     token_data = fyerService.load_token()
# #     if not token_data:
# #         return None
# #     try:
# #         # Search Fyers MongoDB for latest tick
# #         doc = await fyerService.market_data.find_one({"symbol": symbol.upper()})
# #         if not doc:
# #             return None
# #         return {
# #             "symbol": doc["symbol"],
# #             "exchange": "FYERS",
# #             "bid": doc.get("bid"),
# #             "ask": doc.get("ask"),
# #             "last_price": doc.get("ltp"),
# #             "timestamp": datetime.utcnow().isoformat(),
# #             "source": "FYERS"
# #         }
# #     except Exception:
# #         return None


# # import httpx


# # MT5_SERVICE_URL = "http://localhost:8000"  # make sure this is defined

# # async def get_quote_mt5(symbol: str):
# #     """
# #     Fetch quote from MT5 service running on localhost:8000
# #     """
# #     print(f"[DEBUG] Starting MT5 quote fetch for symbol: {symbol}")

# #     async with httpx.AsyncClient() as client:
# #         try:
# #             url = f"{MT5_SERVICE_URL}/symbol/{symbol}"
# #             print(f"[DEBUG] Sending GET request to MT5 service: {url}")

# #             response = await client.get(url)
# #             print(f"[DEBUG] Received response with status {response.status_code}")

# #             response.raise_for_status()

# #             # Attempt to parse JSON
# #             data = response.json()
# #             print(f"[DEBUG] MT5 raw response data: {data}")

# #             # Add additional fields if needed
# #             data.update({
# #                 "timestamp": datetime.utcnow().isoformat(),
# #                 "source": "MT5"
# #             })
# #             print(f"[DEBUG] Returning enriched MT5 data: {data}")

# #             return data

# #         except httpx.HTTPStatusError as e:
# #             print(f"[ERROR] MT5 service returned error (HTTP {e.response.status_code}): {e.response.text}")

# #         except httpx.RequestError as e:
# #             print(f"[ERROR] MT5 request failed (network issue): {e}")

# #         except Exception as e:
# #             print(f"[ERROR] Failed to fetch MT5 quote: {e}")

# #     print(f"[DEBUG] Returning None for symbol: {symbol} (no data fetched)")
# #     return None


# # # -------- Helper to fix Mongo ObjectId --------
# # def clean_doc(doc: dict) -> dict:
# #     """Convert ObjectId to str so FastAPI can serialize it"""
# #     if not doc:
# #         return doc
# #     if "_id" in doc and isinstance(doc["_id"], ObjectId):
# #         doc["_id"] = str(doc["_id"])
# #     return doc


# # # ---------- Search by symbol or partial name ----------
# # # @router.get("/search")
# # # async def search_market(query: Optional[str] = Query("", alias="query"), limit: int = Query(50)):
# # #     try:
# # #         cursor = MarketData.collection.find({
# # #             "symbol": {"$regex": query, "$options": "i"}
# # #         }).limit(limit)
# # #         results = await cursor.to_list(length=limit)
# # #         return [clean_doc(doc) for doc in results]
# # #     except Exception as e:
# # #         raise HTTPException(status_code=500, detail=str(e))
# # # @router.get("/search")
# # # async def search_market(query: Optional[str] = Query("", alias="query"), limit: int = Query(50)):
# # #     try:
# # #         cursor = MarketData.collection.find({
# # #             "symbol": {"$regex": query, "$options": "i"}
# # #         }).limit(limit)
# # #         results = await cursor.to_list(length=limit)

# # #         formatted = [
# # #             {
# # #                 "symbol": doc.get("symbol"),
# # #                 "exchange": doc.get("exchange"),
# # #                 "name": doc.get("name"),
# # #                 "sector": doc.get("sector"),
# # #                 "current_price": doc.get("current_price"),
# # #                 "day_change": doc.get("day_change"),
# # #                 "day_change_percentage": doc.get("day_change_percentage")
# # #             }
# # #             for doc in results
# # #         ]
# # #         return formatted
# # #     except Exception as e:
# # #         raise HTTPException(status_code=500, detail=str(e))

# # # ---------- Get by category / tab: Futures | Options | Forex | Crypto ----------
# # # ---------- Get by category / tab: Futures | Options | Forex | Crypto ----------
# # # @router.get("/category/{type}")
# # # async def get_market_by_category(type: str):
# # #     # Normalize input: strip spaces and uppercase
# # #     type_normalized = type.strip().upper()
    
# # #     # Allowed types in uppercase
# # #     allowed = ["FUTURES", "OPTIONS", "FOREX", "CRYPTO"]
# # #     if type_normalized not in allowed:
# # #         raise HTTPException(status_code=400, detail="Invalid type")

# # #     try:
# # #         # Case-insensitive regex match to avoid DB case issues
# # #         cursor = MarketData.collection.find({
# # #             "exchange": {"$regex": f"^{type_normalized}$", "$options": "i"}
# # #         }).limit(200)
# # #         results = await cursor.to_list(length=200)
# # #         return [clean_doc(doc) for doc in results]
# # #     except Exception as e:
# # #         raise HTTPException(status_code=500, detail=str(e))


# # # ----------------------
# # # Search Endpoint
# # # ----------------------
# # # @router.get("/search")
# # # async def search_symbol(symbol: str = Query(..., min_length=1)):
# # #     symbol = symbol.upper()
    
# # #     # Check Alpaca first
# # #     result = await get_quote_alpaca(symbol)
# # #     if result:
# # #         return result

# # #     # Check Fyers
# # #     # result = await get_quote_fyers(symbol)
# # #     # if result:
# # #     #     return result

# # #     # Check MT5
# # #     result = await get_quote_mt5(symbol)
# # #     if result:
        
# # #         return result

# # #     raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found in any broker")




# # @router.get("/search")
# # async def search_symbol(symbol: str = Query(..., min_length=1)):
# #     symbol = symbol.upper()
# #     print(f"[DEBUG] Received search request for symbol: {symbol}")

# #     # --- Check Alpaca ---
# #     print(f"[DEBUG] Checking Alpaca for symbol: {symbol}")
# #     result = await get_quote_alpaca(symbol)
# #     if result:
# #         print(f"[DEBUG] Found symbol '{symbol}' in Alpaca: {result}")
# #         return {
# #             "source": "Alpaca",
# #             "symbol": symbol,
# #             "data": result
# #         }
# #     else:
# #         print(f"[DEBUG] Symbol '{symbol}' not found in Alpaca")

# #     # --- Check Fyers (optional) ---
# #     # print(f"[DEBUG] Checking Fyers for symbol: {symbol}")
# #     # result = await get_quote_fyers(symbol)
# #     # if result:
# #     #     print(f"[DEBUG] Found symbol '{symbol}' in Fyers: {result}")
# #     #     return {
# #     #         "source": "Fyers",
# #     #         "symbol": symbol,
# #     #         "data": result
# #     #     }
# #     # else:
# #     #     print(f"[DEBUG] Symbol '{symbol}' not found in Fyers")

# #     # --- Check MT5 ---
# #     print(f"[DEBUG] Checking MT5 for symbol: {symbol}")
# #     result = await get_quote_mt5(symbol)
# #     if result:
# #         print(f"[DEBUG] Found symbol '{symbol}' in MT5: {result}")
# #         return {
# #             "source": "MT5",
# #             "symbol": symbol,
# #             "data": result
# #         }
# #     else:
# #         print(f"[DEBUG] Symbol '{symbol}' not found in MT5")

# #     # --- If not found anywhere ---
# #     error_msg = f"Symbol '{symbol}' not found in any broker"
# #     print(f"[ERROR] {error_msg}")
# #     raise HTTPException(status_code=404, detail=error_msg)



# # @router.get("/category/{type}")
# # async def get_market_by_category(type: str):
# #     type_normalized = type.strip().upper()
# #     allowed = ["FUTURES", "OPTIONS", "FOREX", "CRYPTO"]
# #     if type_normalized not in allowed:
# #         raise HTTPException(status_code=400, detail="Invalid type")

# #     try:
# #         cursor = MarketData.collection.find({
# #             "exchange": {"$regex": f"^{type_normalized}$", "$options": "i"}
# #         }).limit(200)
# #         results = await cursor.to_list(length=200)

# #         formatted = [
# #             {
# #                 "symbol": doc.get("symbol"),
# #                 "exchange": doc.get("exchange"),
# #                 "name": doc.get("name"),
# #                 "sector": doc.get("sector"),
# #                 "current_price": doc.get("current_price"),
# #                 "day_change": doc.get("day_change"),
# #                 "day_change_percentage": doc.get("day_change_percentage")
# #             }
# #             for doc in results
# #         ]
# #         return formatted
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=str(e))
# # # ---------- Get single symbol latest ----------
# # # @router.get("/{exchange}/{symbol}")
# # # async def get_single_market(exchange: str, symbol: str):
# # #     try:
# # #         # Normalize input
# # #         exchange = exchange.strip()
# # #         symbol = symbol.strip()

# # #         # Case-insensitive search using regex
# # #         item = await MarketData.collection.find_one({
# # #             "exchange": {"$regex": f"^{exchange}$", "$options": "i"},
# # #             "symbol": {"$regex": f"^{symbol}$", "$options": "i"}
# # #         })

# # #         if not item:
# # #             raise HTTPException(status_code=404, detail="Not found")

# # #         return clean_doc(item)

# # #     except Exception as e:
# # #         raise HTTPException(status_code=500, detail=str(e))

# # # @router.get("/{exchange}/{symbol}")
# # # async def get_single_market(exchange: str, symbol: str):
# # #     try:
# # #         exchange = exchange.strip()
# # #         symbol = symbol.strip()

# # #         item = await MarketData.collection.find_one({
# # #             "exchange": {"$regex": f"^{exchange}$", "$options": "i"},
# # #             "symbol": {"$regex": f"^{symbol}$", "$options": "i"}
# # #         })

# # #         if not item:
# # #             raise HTTPException(status_code=404, detail="Not found")

# # #         data = {
# # #             "symbol": item.get("symbol"),
# # #             "exchange": item.get("exchange"),
# # #             "name": item.get("name"),
# # #             "sector": item.get("sector"),
# # #             "current_price": item.get("current_price"),
# # #             "day_change": item.get("day_change"),
# # #             "day_change_percentage": item.get("day_change_percentage"),
# # #             "open": item.get("open"),
# # #             "high": item.get("high"),
# # #             "low": item.get("low"),
# # #             "volume": item.get("volume"),
# # #             "market_cap": item.get("market_cap"),
# # #         }

# # #         return {"success": True, "data": data}

# # #     except Exception as e:
# # #         raise HTTPException(status_code=500, detail=str(e))

# # @router.get("/{exchange}/{symbol}")
# # async def get_single_market(exchange: str, symbol: str, category: str = None):
# #     try:
# #         # Normalize inputs
# #         exchange = exchange.strip().upper()
# #         symbol = symbol.strip().upper()
# #         category = category.strip().upper() if category else None

# #         # Validate exchange
# #         if exchange not in ALLOWED_EXCHANGES:
# #             raise HTTPException(status_code=400, detail=f"Exchange must be one of {ALLOWED_EXCHANGES}")

# #         # Validate category
# #         allowed_categories = CATEGORY_MAP.get(exchange, [])
# #         if category and category not in allowed_categories:
# #             raise HTTPException(status_code=400, detail=f"Category for {exchange} must be one of {allowed_categories}")

# #         # Fetch data based on exchange
# #         item = None
# #         if exchange in ["FOREX", "CRYPTO", "COMEX"]:
# #             item = await get_quote_mt5(symbol)
# #         elif exchange == "OPTIONS":
# #             item = await get_quote_alpaca(symbol)
# #         # elif exchange == "FUTURES":
# #         #     item = await get_quote_fyers(symbol)

# #         if not item:
# #             raise HTTPException(status_code=404, detail="Market data not found")

# #         return item

# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=str(e))




# from fastapi import APIRouter, Query, HTTPException
# from typing import Optional
# from bson import ObjectId
# from datetime import datetime
# import httpx

# from app.models.marketModel import MarketData
# from app.services import alpacaService
# from app.services import fyerService

# router = APIRouter(tags=["Market"])
# MT5_SERVICE_URL = "http://localhost:8000"  # Your MT5 FastAPI service URL
# ALLOWED_EXCHANGES = ["FUTURES", "OPTIONS", "FOREX", "CRYPTO"]

# CATEGORY_MAP = {
#     "FOREX": ["FOREX"],        # MT5
#     "CRYPTO": ["CRYPTO"],      # MT5
#     "COMEX": ["COMEX"],        # MT5
#     "OPTIONS": ["US_OPTIONS"], # Alpaca
#     "FUTURES": ["NSE", "MCX"]  # FYERS
# }

# # ----------------------
# # Helper functions
# # ----------------------
# async def get_quote_alpaca(symbol: str):
#     try:
#         rest = alpacaService.get_rest_client()
#         quote = rest.get_latest_quote(symbol)
#         return {
#             "symbol": symbol,
#             "exchange": "ALPACA",
#             "bid": float(getattr(quote, "bp", 0)),
#             "ask": float(getattr(quote, "ap", 0)),
#             "last_price": float(getattr(quote, "ap", 0)),  # use ask as last
#             "timestamp": datetime.utcnow().isoformat(),
#             "source": "ALPACA"
#         }
#     except Exception:
#         return None


# async def get_quote_fyers(symbol: str):
#     token_data = fyerService.load_token()
#     if not token_data:
#         return None
#     try:
#         doc = await fyerService.market_data.find_one({"symbol": symbol.upper()})
#         if not doc:
#             return None
#         return {
#             "symbol": doc["symbol"],
#             "exchange": "FYERS",
#             "bid": doc.get("bid"),
#             "ask": doc.get("ask"),
#             "last_price": doc.get("ltp"),
#             "timestamp": datetime.utcnow().isoformat(),
#             "source": "FYERS"
#         }
#     except Exception:
#         return None


# async def get_quote_mt5(symbol: str):
#     """
#     Fetch quote from MT5 service running on localhost:8000
#     """
#     print(f"[DEBUG] Starting MT5 quote fetch for symbol: {symbol}")

#     async with httpx.AsyncClient() as client:
#         try:
#             url = f"{MT5_SERVICE_URL}/symbol/{symbol}"
#             print(f"[DEBUG] Sending GET request to MT5 service: {url}")

#             response = await client.get(url)
#             print(f"[DEBUG] Received response with status {response.status_code}")

#             response.raise_for_status()
#             data = response.json()
#             print(f"[DEBUG] MT5 raw response data: {data}")

#             data.update({
#                 "timestamp": datetime.utcnow().isoformat(),
#                 "source": "MT5"
#             })
#             print(f"[DEBUG] Returning enriched MT5 data: {data}")
#             return data

#         except httpx.HTTPStatusError as e:
#             print(f"[ERROR] MT5 service returned error (HTTP {e.response.status_code}): {e.response.text}")
#         except httpx.RequestError as e:
#             print(f"[ERROR] MT5 request failed (network issue): {e}")
#         except Exception as e:
#             print(f"[ERROR] Failed to fetch MT5 quote: {e}")

#     print(f"[DEBUG] Returning None for symbol: {symbol} (no data fetched)")
#     return None


# def clean_doc(doc: dict) -> dict:
#     """Convert ObjectId to str so FastAPI can serialize it"""
#     if not doc:
#         return doc
#     if "_id" in doc and isinstance(doc["_id"], ObjectId):
#         doc["_id"] = str(doc["_id"])
#     return doc


# @router.get("/search")
# async def search_symbol(symbol: str = Query(..., min_length=1)):
#     symbol = symbol.upper()
#     print(f"[DEBUG] Received search request for symbol: {symbol}")

#     print(f"[DEBUG] Checking Alpaca for symbol: {symbol}")
#     result = await get_quote_alpaca(symbol)
#     if result:
#         return {"source": "Alpaca", "symbol": symbol, "data": result}

#     print(f"[DEBUG] Checking MT5 for symbol: {symbol}")
#     result = await get_quote_mt5(symbol)
#     if result:
#         return {"source": "MT5", "symbol": symbol, "data": result}

#     error_msg = f"Symbol '{symbol}' not found in any broker"
#     print(f"[ERROR] {error_msg}")
#     raise HTTPException(status_code=404, detail=error_msg)


# @router.get("/category/{type}")
# async def get_market_by_category(type: str):
#     type_normalized = type.strip().upper()
#     allowed = ["FUTURES", "OPTIONS", "FOREX", "CRYPTO"]
#     if type_normalized not in allowed:
#         raise HTTPException(status_code=400, detail="Invalid type")

#     try:
#         cursor = MarketData.collection.find({
#             "exchange": {"$regex": f"^{type_normalized}$", "$options": "i"}
#         }).limit(200)
#         results = await cursor.to_list(length=200)

#         formatted = [
#             {
#                 "symbol": doc.get("symbol"),
#                 "exchange": doc.get("exchange"),
#                 "name": doc.get("name"),
#                 "sector": doc.get("sector"),
#                 "current_price": doc.get("current_price"),
#                 "day_change": doc.get("day_change"),
#                 "day_change_percentage": doc.get("day_change_percentage")
#             }
#             for doc in results
#         ]
#         return formatted
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/{exchange}/{symbol}")
# async def get_single_market(exchange: str, symbol: str, category: str = None):
#     try:
#         exchange = exchange.strip().upper()
#         symbol = symbol.strip().upper()
#         category = category.strip().upper() if category else None

#         if exchange not in ALLOWED_EXCHANGES:
#             raise HTTPException(status_code=400, detail=f"Exchange must be one of {ALLOWED_EXCHANGES}")

#         allowed_categories = CATEGORY_MAP.get(exchange, [])
#         if category and category not in allowed_categories:
#             raise HTTPException(status_code=400, detail=f"Category for {exchange} must be one of {allowed_categories}")

#         item = None
#         if exchange in ["FOREX", "CRYPTO", "COMEX"]:
#             item = await get_quote_mt5(symbol)
#         elif exchange == "OPTIONS":
#             item = await get_quote_alpaca(symbol)
#         # elif exchange == "FUTURES":
#         #     item = await get_quote_fyers(symbol)

#         if not item:
#             raise HTTPException(status_code=404, detail="Market data not found")

#         return item

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))



from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from bson import ObjectId
from datetime import datetime
import httpx

from app.models.marketModel import MarketData
from app.services import alpacaService
from app.services import fyerService

router = APIRouter(tags=["Market"])
MT5_SERVICE_URL = "http://localhost:8000"  # Your MT5 FastAPI service URL
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
            "exchange": "ALPACA",
            "bid": float(getattr(quote, "bp", 0)),
            "ask": float(getattr(quote, "ap", 0)),
            "last_price": float(getattr(quote, "ap", 0)),  # use ask as last
            "timestamp": datetime.utcnow().isoformat(),
            "source": "ALPACA"
        }
    except Exception:
        return None

async def get_quote_fyers(symbol: str):
    token_data = fyerService.load_token()
    if not token_data:
        return None
    try:
        doc = await fyerService.market_data.find_one({"symbol": symbol.upper()})
        if not doc:
            return None
        return {
            "symbol": doc.get("symbol", symbol),
            "exchange": "FYERS",
            "bid": doc.get("bid", 0),
            "ask": doc.get("ask", 0),
            "last_price": doc.get("ltp", 0),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "FYERS"
        }
    except Exception:
        return None

async def get_quote_mt5(symbol: str):
    """
    Fetch quote from MT5 service running on localhost:8000
    """
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
            data.update({
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
    result = await get_quote_alpaca(symbol) or await get_quote_mt5(symbol)

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

#  @router.get("/{exchange}/{symbol}")
#  async def get_single_market(exchange: str, symbol: str, category: str = None):


#     exchange = exchange.strip().upper()
#     symbol = symbol.strip().upper()
#     category = category.strip().upper() if category else None

#     if exchange not in ALLOWED_EXCHANGES:
#         return {"error": f"Exchange must be one of {ALLOWED_EXCHANGES}", "data": {}}

#     allowed_categories = CATEGORY_MAP.get(exchange, [])
#     if category and category not in allowed_categories:
#         return {"error": f"Category for {exchange} must be one of {allowed_categories}", "data": {}}

#     item = None
#     if exchange in ["FOREX", "CRYPTO", "COMEX"]:
#         item = await get_quote_mt5(symbol)
#     elif exchange == "OPTIONS":
#         item = await get_quote_alpaca(symbol)
#     # elif exchange == "FUTURES":
#     #     item = await get_quote_fyers(symbol)

#     if not item:
#         return {
#             "symbol": symbol,
#             "exchange": exchange,
#             "category": category,
#             "bid": 0,
#             "ask": 0,
#             "last_price": 0,
#             "timestamp": datetime.utcnow().isoformat(),
#             "note": "Market data not found"
#         }

#     return item


# @router.get("/{exchange}/{symbol}")
# async def get_single_market(exchange: str, symbol: str, category: str = None):
#     exchange = exchange.strip().upper()
#     symbol = symbol.strip().upper()
#     category = category.strip().upper() if category else None

#     if exchange not in ALLOWED_EXCHANGES:
#         return {"success": False, "error": f"Exchange must be one of {ALLOWED_EXCHANGES}"}

#     allowed_categories = CATEGORY_MAP.get(exchange, [])
#     if category and category not in allowed_categories:
#         return {"success": False, "error": f"Category for {exchange} must be one of {allowed_categories}"}

#     item = None
#     if exchange in ["FOREX", "CRYPTO", "COMEX"]:
#         item = await get_quote_mt5(symbol)
#     elif exchange == "OPTIONS":
#         item = await get_quote_alpaca(symbol)
#     # elif exchange == "FUTURES":
#     #     item = await get_quote_fyers(symbol)

#     if not item:
#         return {
#             "success": False,
#             "data": {
#                 "symbol": symbol,
#                 "exchange": exchange,
#                 "name": "",
#                 "sector": "",
#                 "current_price": 0,
#                 "day_change": 0,
#                 "day_change_percentage": 0,
#                 "open": 0,
#                 "high": 0,
#                 "low": 0,
#                 "volume": 0,
#                 "market_cap": 0
#             },
#             "note": "Market data not found"
#         }

#     # Map to marketSymbolResponse format
#     mapped = {
#         "symbol": item.get("symbol", symbol),
#         "exchange": item.get("exchange", exchange),
#         "name": item.get("name", ""),
#         "sector": item.get("sector", ""),
#         "current_price": item.get("last_price", 0),
#         "day_change": item.get("day_change", 0),
#         "day_change_percentage": item.get("day_change_percentage", 0),
#         "open": item.get("open", 0),
#         "high": item.get("high", 0),
#         "low": item.get("low", 0),
#         "volume": item.get("volume", 0),
#         "market_cap": item.get("market_cap", 0),
#     }

#         return {"success": True, "data": mapped}


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
        # elif exchange == "FUTURES":
        #     item = await get_quote_fyers(symbol)

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