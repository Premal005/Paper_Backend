from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from bson import ObjectId
import jwt

from app.models.userModel import User
from app.models.watchlistModel import Watchlist

router = APIRouter( tags=["Watchlist"])
security = HTTPBearer()

# -------------------------
# Authentication Dependency
# -------------------------
async def authenticate(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        decoded = jwt.decode(token, "YOUR_JWT_SECRET", algorithms=["HS256"])
        user = await User.find_by_id(decoded["userId"])
        if not user or not user.get("isActive", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer exists or is deactivated"
            )
        return str(user["_id"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# -------------------------
# Routes
# -------------------------

# GET /watchlist
@router.get("/")
async def get_watchlist(user_id: str = Depends(authenticate)):
    watchlist = await Watchlist.find_by_user(user_id)
    if not watchlist:
        return {"symbols": []}
    return watchlist


# POST /watchlist (add symbol)
@router.post("/")
async def add_symbol(data: dict, user_id: str = Depends(authenticate)):
    symbol = data.get("symbol")
    exchange = data.get("exchange")
    if not symbol or not exchange:
        raise HTTPException(status_code=400, detail="Symbol and exchange are required")
    
    watchlist = await Watchlist.find_by_user(user_id)
    if not watchlist:
        await Watchlist.create(user_id, symbols=[])
        watchlist = await Watchlist.find_by_user(user_id)

    # prevent duplicates
    if any(s["symbol"] == symbol and s["exchange"] == exchange for s in watchlist.get("symbols", [])):
        raise HTTPException(status_code=400, detail="Symbol already exists in watchlist")
    
    watchlist["symbols"].append({"symbol": symbol, "exchange": exchange})
    await Watchlist.update_symbols(user_id, watchlist["symbols"])
    return watchlist


# DELETE /watchlist (remove symbol)
@router.delete("/")
async def remove_symbol(data: dict, user_id: str = Depends(authenticate)):
    symbol = data.get("symbol")
    exchange = data.get("exchange")
    if not symbol or not exchange:
        raise HTTPException(status_code=400, detail="Symbol and exchange are required")
    
    watchlist = await Watchlist.find_by_user(user_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    watchlist["symbols"] = [s for s in watchlist.get("symbols", []) if not (s["symbol"] == symbol and s["exchange"] == exchange)]
    await Watchlist.update_symbols(user_id, watchlist["symbols"])
    return watchlist


# PUT /watchlist (replace full list)
@router.put("/")
async def update_watchlist(data: dict, user_id: str = Depends(authenticate)):
    symbols = data.get("symbols")
    if symbols is None or not isinstance(symbols, list):
        raise HTTPException(status_code=400, detail="Symbols must be a list")
    
    await Watchlist.update_symbols(user_id, symbols)
    watchlist = await Watchlist.find_by_user(user_id)
    return watchlist
