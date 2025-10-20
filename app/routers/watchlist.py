



from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket
from datetime import datetime
import jwt, os, logging, asyncio, json

from app.models.userModel import User
from app.models.watchlistModel import Watchlist
from app.services.concurrentMarketService import concurrent_market_service
from app.services.watchlistWebSocket import watchlist_ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Watchlist"])
JWT_SECRET = os.getenv("JWT_SECRET", "secret")

UPDATE_INTERVAL = 1  # 1 second between updates

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

async def authenticate_websocket(websocket: WebSocket, token: str):
    """Authenticate WebSocket connection"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user = await User.find_by_id(payload["userId"])
        if not user or not user.get("isActive", True):
            await websocket.close(code=1008)
            return None
        return user
    except Exception:
        await websocket.close(code=1008)
        return None

# ============================================================== 
# 🔁 Optimized Background Updater
# ============================================================== 
async def update_all_watchlists_loop():
    """Per-symbol concurrent background updater"""
    logger.info("🚀 Per-symbol watchlist auto-updater started...")
    while True:
        try:
            await concurrent_market_service.update_all_watchlists_concurrently()
        except Exception as e:
            logger.error(f"❌ Error in watchlist update loop: {e}")
        
        await asyncio.sleep(UPDATE_INTERVAL)

def start_watchlist_updater(loop):
    """Starts optimized background updater"""
    try:
        loop.create_task(update_all_watchlists_loop())
        logger.info("✅ Per-symbol watchlist auto-update loop initialized.")
    except Exception as e:
        logger.error(f"Failed to start watchlist updater: {e}")

# ============================================================== 
# 📡 Watchlist WebSocket
# ============================================================== 
@router.websocket("/ws")
async def watchlist_websocket(websocket: WebSocket, token: str):
    """WebSocket for real-time per-symbol watchlist updates"""
    user = await authenticate_websocket(websocket, token)
    if not user:
        return
        
    user_id = str(user["_id"])
    await watchlist_ws_manager.connect(websocket, user_id)
    
    try:
        # Send initial watchlist data
        watchlist = await Watchlist.find_by_user(user_id)
        if watchlist:
            await websocket.send_json({
                "type": "initial_data",
                "data": watchlist.get("symbols", [])
            })
        
        # Keep connection alive and handle individual symbol updates
        while True:
            data = await websocket.receive_text()
            
            # Handle individual symbol refresh requests
            if data.startswith("refresh:"):
                symbol_data = data.replace("refresh:", "")
                try:
                    symbol_info = json.loads(symbol_data)
                    symbol = symbol_info.get("symbol")
                    exchange = symbol_info.get("exchange")
                    
                    if symbol and exchange:
                        # Force immediate update for this symbol
                        await concurrent_market_service.update_single_symbol(symbol, exchange)
                        await websocket.send_json({
                            "type": "refresh_ack",
                            "symbol": symbol,
                            "exchange": exchange,
                            "status": "updating"
                        })
                except Exception as e:
                    logger.error(f"Error handling refresh request: {e}")
            
            # Handle ping/pong
            elif data == "ping":
                await websocket.send_text("pong")
                
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        watchlist_ws_manager.disconnect(user_id)

# ============================================================== 
# 📘 GET /watchlist (Lightweight - uses cached data)
# ============================================================== 
@router.get("/")
async def get_watchlist(user: dict = Depends(authenticate)):
    """Lightweight endpoint - returns cached data without fetching"""
    user_id = str(user["_id"])
    watchlist = await Watchlist.find_by_user(user_id)
    if not watchlist:
        return []
    
    return watchlist.get("symbols", [])

# ============================================================== 
# ➕ POST /watchlist (Add symbol)
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

    # Check if symbol already exists
    if any(s["symbol"].upper() == symbol.upper() and s["exchange"].upper() == exchange.upper() 
           for s in watchlist.get("symbols", [])):
        raise HTTPException(status_code=400, detail="Symbol already exists in watchlist")


    try:
        market_data = await concurrent_market_service.get_symbol_data(symbol.upper(), exchange.upper())
    except Exception as e:
        logger.warning(f"Could not fetch initial data for {symbol}: {e}")
        market_data = None

    # Add new symbol
    new_symbol = {
        "symbol": symbol.upper(),
        "exchange": exchange.upper(),
        "added_at": datetime.utcnow().isoformat() + "Z",
        "current_price": market_data["current_price"] if market_data else 0.0,
        "day_change": market_data["day_change"] if market_data else 0.0,
        "day_change_percentage": market_data["day_change_percentage"] if market_data else 0.0,
        "last_updated": datetime.utcnow().isoformat() + "Z"
    }
    
    watchlist["symbols"].append(new_symbol)
    await Watchlist.update_symbols(user_id, watchlist["symbols"])
    
    # Trigger immediate update for the new symbol
    asyncio.create_task(concurrent_market_service.update_single_symbol(symbol.upper(), exchange.upper()))
    
    return watchlist["symbols"]

# ============================================================== 
# ❌ DELETE /watchlist (Remove symbol)
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

    # Filter out the symbol
    original_count = len(watchlist.get("symbols", []))
    watchlist["symbols"] = [
        s for s in watchlist.get("symbols", [])
        if not (s["symbol"].upper() == symbol.upper() and s["exchange"].upper() == exchange.upper())
    ]
    
    if len(watchlist["symbols"]) == original_count:
        raise HTTPException(status_code=404, detail="Symbol not found in watchlist")

    await Watchlist.update_symbols(user_id, watchlist["symbols"])
    return watchlist["symbols"]

# ============================================================== 
# 🔁 PUT /watchlist (Replace full list)
# ============================================================== 
@router.put("/")
async def update_watchlist(data: dict, user: dict = Depends(authenticate)):
    user_id = str(user["_id"])
    symbols = data.get("symbols")

    if symbols is None or not isinstance(symbols, list):
        raise HTTPException(status_code=400, detail="Symbols must be a list")

    # Prepare symbols with real data
    prepared_symbols = []
    
    # Fetch data for all symbols concurrently
    fetch_tasks = []
    for s in symbols:
        symbol = s.get("symbol", "").upper()
        exchange = s.get("exchange", "").upper()
        task = concurrent_market_service.get_symbol_data(symbol, exchange)
        fetch_tasks.append((symbol, exchange, task))
    
    # Wait for all data to be fetched
    symbol_data_results = []
    for symbol, exchange, task in fetch_tasks:
        market_data = await task
        symbol_data_results.append((symbol, exchange, market_data))

    # Build prepared symbols with real data
    for (symbol, exchange, market_data) in symbol_data_results:
        symbol_data = {
            "symbol": symbol,
            "exchange": exchange,
            "added_at": datetime.utcnow().isoformat() + "Z",
            "current_price": market_data["current_price"] if market_data else 0.0,
            "day_change": market_data["day_change"] if market_data else 0.0,
            "day_change_percentage": market_data["day_change_percentage"] if market_data else 0.0,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        prepared_symbols.append(symbol_data)

    await Watchlist.update_symbols(user_id, prepared_symbols)
    
    # Trigger immediate update for all symbols in this watchlist
    asyncio.create_task(concurrent_market_service.update_single_watchlist(user_id))
    
    return prepared_symbols

# ============================================================== 
# 🔄 POST /watchlist/refresh-symbol (Force refresh single symbol)
# ============================================================== 
@router.post("/refresh-symbol")
async def refresh_symbol(data: dict, user: dict = Depends(authenticate)):
    """Force immediate refresh of a single symbol"""
    user_id = str(user["_id"])
    symbol = data.get("symbol")
    exchange = data.get("exchange")
    
    if not symbol or not exchange:
        raise HTTPException(status_code=400, detail="Symbol and exchange are required")
    
    # Verify the symbol exists in user's watchlist
    watchlist = await Watchlist.find_by_user(user_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    symbol_exists = any(
        s["symbol"].upper() == symbol.upper() and s["exchange"].upper() == exchange.upper()
        for s in watchlist.get("symbols", [])
    )
    
    if not symbol_exists:
        raise HTTPException(status_code=404, detail="Symbol not found in watchlist")
    
    # Trigger immediate update
    asyncio.create_task(concurrent_market_service.update_single_symbol(symbol, exchange))
    
    return {"status": "refresh_triggered", "symbol": symbol, "exchange": exchange}

# ============================================================== 
# 🔍 DEBUG: Check if updates are working
# ============================================================== 
@router.get("/debug/status")
async def debug_watchlist_status(user: dict = Depends(authenticate)):
    """Debug endpoint to check if per-symbol updates are working"""
    user_id = str(user["_id"])
    watchlist = await Watchlist.find_by_user(user_id)
    
    if not watchlist:
        return {"status": "no_watchlist"}
    
    symbols = watchlist.get("symbols", [])
    updated_count = 0
    recent_updates = []
    
    for symbol in symbols:
        if symbol.get("last_updated"):
            # Check if updated in last 2 minutes
            try:
                last_updated_str = symbol["last_updated"].replace('Z', '+00:00')
                last_updated = datetime.fromisoformat(last_updated_str)
                time_diff = (datetime.utcnow() - last_updated).total_seconds()
                
                if time_diff < 120:  # 2 minutes
                    updated_count += 1
                    recent_updates.append({
                        "symbol": symbol["symbol"],
                        "exchange": symbol["exchange"],
                        "last_updated": symbol["last_updated"],
                        "current_price": symbol.get("current_price", 0),
                        "time_diff_seconds": round(time_diff, 2)
                    })
            except Exception as e:
                logger.warning(f"Error parsing last_updated for {symbol['symbol']}: {e}")
    
    # Get unique symbols being tracked
    unique_symbols = await Watchlist.get_all_symbols_to_track()
    
    return {
        "total_symbols": len(symbols),
        "recently_updated": updated_count,
        "recent_updates": recent_updates[:5],
        "watchlist_exists": True,
        "last_updated_db": watchlist.get("last_updated"),
        "system_status": {
            "update_interval_seconds": UPDATE_INTERVAL,
            "unique_symbols_tracked": len(unique_symbols),
            "update_method": "per_symbol_concurrent"
        }
    }