




# # --------------------------------------------------------------
# from fastapi import APIRouter, Depends, HTTPException, Request
# from fastapi.security import HTTPBearer
# from datetime import datetime
# import jwt, os, logging

# from app.models.userModel import User
# from app.models.watchlistModel import Watchlist
# from app.routers.market import get_quote_alpaca, get_quote_fyers, get_quote_mt5  # Use market.py functions

# logger = logging.getLogger(__name__)

# router = APIRouter(tags=["Watchlist"])
# security = HTTPBearer()
# JWT_SECRET = os.getenv("JWT_SECRET", "secret")

# # ============================================================== 
# # 🧩 Authentication 
# # ============================================================== 
# async def authenticate(req: Request):
#     auth_header = req.headers.get("Authorization")
#     if not auth_header or not auth_header.startswith("Bearer "):
#         raise HTTPException(status_code=401, detail="Access denied. No token provided.")

#     token = auth_header.split(" ")[1]
#     try:
#         payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
#         user = await User.find_by_id(payload["userId"])
#         if not user or not user.get("isActive", True):
#             raise HTTPException(status_code=401, detail="User no longer exists or is deactivated")
#         return user
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token expired")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=401, detail="Invalid token")

# # ============================================================== 
# # 🧮 Helper: Format watchlist with live data
# # ============================================================== 
# async def format_watchlist_symbols(symbols: list):
#     formatted = []

#     for s in symbols:
#         symbol = s["symbol"].upper()
#         exchange = s["exchange"].upper()

#         # Use the SAME logic as market.py search endpoint
#         result = None
#         if exchange == "ALPACA":
#             result = await get_quote_alpaca(symbol)
#         elif exchange == "FYERS":
#             result = await get_quote_fyers(symbol)
#         elif exchange == "MT5":
#             result = await get_quote_mt5(symbol)
#         else:
#             # Fallback: try all sources like market.py does
#             result = await get_quote_alpaca(symbol) or await get_quote_fyers(symbol) or await get_quote_mt5(symbol)

#         # Map to watchlist format using the same field names as market search
#         if result:
#             formatted.append({
#                 "symbol": result.get("symbol", symbol),
#                 "exchange": result.get("exchange", exchange),
#                 "current_price": round(result.get("last_price", 0.0), 2),
#                 "day_change": result.get("day_change"),
#                 "day_change_percentage": result.get("day_change_percentage"),
#                 "added_at": s.get("added_at") or datetime.utcnow().isoformat() + "Z"
#             })
#         else:
#             # If no data found, return zero values like market.py does
#             formatted.append({
#                 "symbol": symbol,
#                 "exchange": exchange,
#                 "current_price": 0.0,
#                 "day_change": 0.0,
#                 "day_change_percentage": 0.0,
#                 "added_at": s.get("added_at") or datetime.utcnow().isoformat() + "Z",
#                 "note": "No market data available"
#             })

#     return formatted
# # ============================================================== 
# # 📘 GET /watchlist
# # ============================================================== 
# @router.get("/")
# async def get_watchlist(user: dict = Depends(authenticate)):
#     user_id = str(user["_id"])
#     watchlist = await Watchlist.find_by_user(user_id)
#     if not watchlist:
#         return []
#     return await format_watchlist_symbols(watchlist.get("symbols", []))

# # ============================================================== 
# # ➕ POST /watchlist (add symbol)
# # ============================================================== 
# @router.post("/")
# async def add_symbol(data: dict, user: dict = Depends(authenticate)):
#     user_id = str(user["_id"])
#     symbol = data.get("symbol")
#     exchange = data.get("exchange")

#     if not symbol or not exchange:
#         raise HTTPException(status_code=400, detail="Symbol and exchange are required")

#     watchlist = await Watchlist.find_by_user(user_id)
#     if not watchlist:
#         await Watchlist.create(user_id, symbols=[])
#         watchlist = await Watchlist.find_by_user(user_id)

#     # Prevent duplicates
#     if any(s["symbol"].upper() == symbol.upper() and s["exchange"].upper() == exchange.upper() for s in watchlist.get("symbols", [])):
#         raise HTTPException(status_code=400, detail="Symbol already exists in watchlist")

#     # Add symbol with timestamp
#     watchlist["symbols"].append({
#         "symbol": symbol.upper(),
#         "exchange": exchange.upper(),
#         "added_at": datetime.utcnow().isoformat() + "Z"
#     })

#     await Watchlist.update_symbols(user_id, watchlist["symbols"])
#     return await format_watchlist_symbols(watchlist["symbols"])

# # ============================================================== 
# # ❌ DELETE /watchlist (remove symbol)
# # ============================================================== 
# @router.delete("/")
# async def remove_symbol(data: dict, user: dict = Depends(authenticate)):
#     user_id = str(user["_id"])
#     symbol = data.get("symbol")
#     exchange = data.get("exchange")

#     if not symbol or not exchange:
#         raise HTTPException(status_code=400, detail="Symbol and exchange are required")

#     watchlist = await Watchlist.find_by_user(user_id)
#     if not watchlist:
#         raise HTTPException(status_code=404, detail="Watchlist not found")

#     watchlist["symbols"] = [
#         s for s in watchlist.get("symbols", [])
#         if not (s["symbol"].upper() == symbol.upper() and s["exchange"].upper() == exchange.upper())
#     ]

#     await Watchlist.update_symbols(user_id, watchlist["symbols"])
#     return await format_watchlist_symbols(watchlist["symbols"])

# # ============================================================== 
# # 🔁 PUT /watchlist (replace full list)
# # ============================================================== 
# @router.put("/")
# async def update_watchlist(data: dict, user: dict = Depends(authenticate)):
#     user_id = str(user["_id"])
#     symbols = data.get("symbols")

#     if symbols is None or not isinstance(symbols, list):
#         raise HTTPException(status_code=400, detail="Symbols must be a list")

#     # Ensure each symbol has uppercase exchange & added_at timestamp
#     for s in symbols:
#         s["symbol"] = s.get("symbol", "").upper()
#         s["exchange"] = s.get("exchange", "").upper()
#         if "added_at" not in s:
#             s["added_at"] = datetime.utcnow().isoformat() + "Z"

#     await Watchlist.update_symbols(user_id, symbols)
#     watchlist = await Watchlist.find_by_user(user_id)
#     return await format_watchlist_symbols(watchlist.get("symbols", []))












from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import BackgroundTasks
from datetime import datetime
import jwt, os, logging, asyncio

from app.models.userModel import User
from app.models.watchlistModel import Watchlist
from app.routers.market import get_quote_alpaca, get_quote_fyers, get_quote_mt5

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Watchlist"])
JWT_SECRET = os.getenv("JWT_SECRET", "secret")

UPDATE_INTERVAL = 10 #SECONDS between auto-updates

# ============================================================== 
# 🧩 Authentication
# ============================================================== 
async def authenticate(req: Request):
    auth_header = req.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Access denied. No token provided.")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user = await User.find_by_id(payload["userId"])
        if not user or not user.get("isActive", True):
            raise HTTPException(status_code=401, detail="User no longer exists or is deactivated")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============================================================== 
# 🧮 Helper: Fetch live data for symbols
# ============================================================== 
async def fetch_live_data(symbols: list):
    updated_symbols = []

    for s in symbols:
        symbol = s["symbol"].upper()
        exchange = s["exchange"].upper()

        result = None
        if exchange == "ALPACA":
            result = await get_quote_alpaca(symbol)
        elif exchange == "FYERS":
            result = await get_quote_fyers(symbol)
        elif exchange == "MT5":
            result = await get_quote_mt5(symbol)
        else:
            result = await get_quote_alpaca(symbol) or await get_quote_fyers(symbol) or await get_quote_mt5(symbol)

        if result:
            s["current_price"] = round(result.get("last_price", 0.0), 2)
            s["day_change"] = result.get("day_change", 0.0)
            s["day_change_percentage"] = result.get("day_change_percentage", 0.0)
        else:
            s["current_price"] = 0.0
            s["day_change"] = 0.0
            s["day_change_percentage"] = 0.0
            s["note"] = "No market data available"

        updated_symbols.append(s)

    return updated_symbols

# ============================================================== 
# 🔁 Background updater
# ============================================================== 
# ============================================================== 
# 🔁 Background updater (non-blocking)
# ============================================================== 
async def update_all_watchlists_loop():
    logger.info("📈 Watchlist auto-updater started...")
    while True:
        try:
            users_watchlists = await Watchlist.get_all()
            logger.info(f"🔄 Updating {len(users_watchlists)} watchlists...")

            for w in users_watchlists:
                symbols = w.get("symbols", [])
                if not symbols:
                    continue
                updated_symbols = await fetch_live_data(symbols)
                await Watchlist.update_symbols(str(w["userId"]), updated_symbols)

            logger.info("✅ Watchlists auto-updated successfully.")
        except Exception as e:
            logger.error(f"❌ Error auto-updating watchlists: {e}")

        await asyncio.sleep(UPDATE_INTERVAL)  # interval in seconds


def start_watchlist_updater(loop):
    """Starts background updater as a detached asyncio Task"""
    try:
        loop.create_task(update_all_watchlists_loop())
        logger.info("🚀 Watchlist auto-update loop initialized.")
    except Exception as e:
        logger.error(f"Failed to start watchlist updater: {e}")


# # Call this function at app startup to start auto-updates
# def start_watchlist_updater(app):
#     loop = asyncio.get_event_loop()
#     loop.create_task(update_all_watchlists_loop())

# ============================================================== 
# 📘 GET /watchlist
# ============================================================== 
@router.get("/")
async def get_watchlist(user: dict = Depends(authenticate)):
    user_id = str(user["_id"])
    watchlist = await Watchlist.find_by_user(user_id)
    if not watchlist:
        return []

    symbols = watchlist.get("symbols", [])
    updated_symbols = await fetch_live_data(symbols)
    await Watchlist.update_symbols(user_id, updated_symbols)
    return updated_symbols

# ============================================================== 
# ➕ POST /watchlist (add symbol)
# ============================================================== 
@router.post("/")
async def add_symbol(data: dict, user: dict = Depends(authenticate)):
    user_id = str(user["_id"])
    symbol = data.get("symbol")
    exchange = data.get("exchange")

    if not symbol or not exchange:
        raise HTTPException(status_code=400, detail="Symbol and exchange are required")

    watchlist = await Watchlist.find_by_user(user_id)
    if not watchlist:
        await Watchlist.create(user_id, symbols=[])
        watchlist = await Watchlist.find_by_user(user_id)

    if any(s["symbol"].upper() == symbol.upper() and s["exchange"].upper() == exchange.upper() for s in watchlist.get("symbols", [])):
        raise HTTPException(status_code=400, detail="Symbol already exists in watchlist")

    watchlist["symbols"].append({
        "symbol": symbol.upper(),
        "exchange": exchange.upper(),
        "added_at": datetime.utcnow().isoformat() + "Z"
    })

    updated_symbols = await fetch_live_data(watchlist["symbols"])
    await Watchlist.update_symbols(user_id, updated_symbols)
    return updated_symbols

# ============================================================== 
# ❌ DELETE /watchlist (remove symbol)
# ============================================================== 
@router.delete("/")
async def remove_symbol(data: dict, user: dict = Depends(authenticate)):
    user_id = str(user["_id"])
    symbol = data.get("symbol")
    exchange = data.get("exchange")

    if not symbol or not exchange:
        raise HTTPException(status_code=400, detail="Symbol and exchange are required")

    watchlist = await Watchlist.find_by_user(user_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    watchlist["symbols"] = [
        s for s in watchlist.get("symbols", [])
        if not (s["symbol"].upper() == symbol.upper() and s["exchange"].upper() == exchange.upper())
    ]

    updated_symbols = await fetch_live_data(watchlist["symbols"])
    await Watchlist.update_symbols(user_id, updated_symbols)
    return updated_symbols

# ============================================================== 
# 🔁 PUT /watchlist (replace full list)
# ============================================================== 
@router.put("/")
async def update_watchlist(data: dict, user: dict = Depends(authenticate)):
    user_id = str(user["_id"])
    symbols = data.get("symbols")

    if symbols is None or not isinstance(symbols, list):
        raise HTTPException(status_code=400, detail="Symbols must be a list")

    for s in symbols:
        s["symbol"] = s.get("symbol", "").upper()
        s["exchange"] = s.get("exchange", "").upper()
        if "added_at" not in s:
            s["added_at"] = datetime.utcnow().isoformat() + "Z"

    updated_symbols = await fetch_live_data(symbols)
    await Watchlist.update_symbols(user_id, updated_symbols)
    return updated_symbols
