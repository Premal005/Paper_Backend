# from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from typing import List
# from bson import ObjectId
# import jwt

# from app.models.userModel import User
# from app.models.watchlistModel import Watchlist

# router = APIRouter( tags=["Watchlist"])
# security = HTTPBearer()

# # -------------------------
# # Authentication Dependency
# # -------------------------
# async def authenticate(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     token = credentials.credentials
#     try:
#         decoded = jwt.decode(token, "YOUR_JWT_SECRET", algorithms=["HS256"])
#         user = await User.find_by_id(decoded["userId"])
#         if not user or not user.get("isActive", True):
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="User no longer exists or is deactivated"
#             )
#         return str(user["_id"])
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# # -------------------------
# # Routes
# # -------------------------

# # GET /watchlist
# @router.get("/")
# async def get_watchlist(user_id: str = Depends(authenticate)):
#     watchlist = await Watchlist.find_by_user(user_id)
#     if not watchlist:
#         return {"symbols": []}
#     return watchlist


# # POST /watchlist (add symbol)
# @router.post("/")
# async def add_symbol(data: dict, user_id: str = Depends(authenticate)):
#     symbol = data.get("symbol")
#     exchange = data.get("exchange")
#     if not symbol or not exchange:
#         raise HTTPException(status_code=400, detail="Symbol and exchange are required")
    
#     watchlist = await Watchlist.find_by_user(user_id)
#     if not watchlist:
#         await Watchlist.create(user_id, symbols=[])
#         watchlist = await Watchlist.find_by_user(user_id)

#     # prevent duplicates
#     if any(s["symbol"] == symbol and s["exchange"] == exchange for s in watchlist.get("symbols", [])):
#         raise HTTPException(status_code=400, detail="Symbol already exists in watchlist")
    
#     watchlist["symbols"].append({"symbol": symbol, "exchange": exchange})
#     await Watchlist.update_symbols(user_id, watchlist["symbols"])
#     return watchlist


# # DELETE /watchlist (remove symbol)
# @router.delete("/")
# async def remove_symbol(data: dict, user_id: str = Depends(authenticate)):
#     symbol = data.get("symbol")
#     exchange = data.get("exchange")
#     if not symbol or not exchange:
#         raise HTTPException(status_code=400, detail="Symbol and exchange are required")
    
#     watchlist = await Watchlist.find_by_user(user_id)
#     if not watchlist:
#         raise HTTPException(status_code=404, detail="Watchlist not found")
    
#     watchlist["symbols"] = [s for s in watchlist.get("symbols", []) if not (s["symbol"] == symbol and s["exchange"] == exchange)]
#     await Watchlist.update_symbols(user_id, watchlist["symbols"])
#     return watchlist


# # PUT /watchlist (replace full list)
# @router.put("/")
# async def update_watchlist(data: dict, user_id: str = Depends(authenticate)):
#     symbols = data.get("symbols")
#     if symbols is None or not isinstance(symbols, list):
#         raise HTTPException(status_code=400, detail="Symbols must be a list")
    
#     await Watchlist.update_symbols(user_id, symbols)
#     watchlist = await Watchlist.find_by_user(user_id)
#     return watchlist





# --------------------------------------------------------------
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from bson import ObjectId
from datetime import datetime
import jwt,os
JWT_SECRET = os.getenv("JWT_SECRET", "secret")

from app.models.userModel import User
from app.models.watchlistModel import Watchlist

router = APIRouter(tags=["Watchlist"])
security = HTTPBearer()

# -------------------------
# Authentication Dependency
# -------------------------
# async def authenticate(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     token = credentials.credentials
#     try:
#         decoded = jwt.decode(token, "YOUR_JWT_SECRET", algorithms=["HS256"])
#         user = await User.find_by_id(decoded["userId"])
#         if not user or not user.get("isActive", True):
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="User no longer exists or is deactivated"
#             )
#         return str(user["_id"])
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

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

# -------------------------
# Helper: Format Watchlist Response
# -------------------------
def format_watchlist_symbols(symbols: list):
    formatted = []
    for s in symbols:
        formatted.append({
            "symbol": s["symbol"],
            "exchange": s["exchange"],
            "current_price": s.get("current_price", 0.0),
            "day_change": s.get("day_change", 0.0),
            "day_change_percentage": s.get("day_change_percentage", 0.0),
            "added_at": s.get("added_at") or datetime.utcnow().isoformat() + "Z"
        })
    return formatted

# -------------------------
# GET /watchlist
# -------------------------
@router.get("/")
async def get_watchlist(user: dict = Depends(authenticate)):
    user_id = str(user["_id"])
    watchlist = await Watchlist.find_by_user(user_id)
    if not watchlist:
        return []
    return format_watchlist_symbols(watchlist.get("symbols", []))

# -------------------------
# POST /watchlist (add symbol)
# -------------------------
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

    # Prevent duplicates
    if any(s["symbol"] == symbol and s["exchange"] == exchange for s in watchlist.get("symbols", [])):
        raise HTTPException(status_code=400, detail="Symbol already exists in watchlist")
    
    # Add symbol with added_at timestamp
    watchlist["symbols"].append({
        "symbol": symbol,
        "exchange": exchange,
        "added_at": datetime.utcnow().isoformat() + "Z"
    })

    await Watchlist.update_symbols(user_id, watchlist["symbols"])
    return format_watchlist_symbols(watchlist["symbols"])

# -------------------------
# DELETE /watchlist (remove symbol)
# -------------------------
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
        if not (s["symbol"] == symbol and s["exchange"] == exchange)
    ]

    await Watchlist.update_symbols(user_id, watchlist["symbols"])
    return format_watchlist_symbols(watchlist["symbols"])

# -------------------------
# PUT /watchlist (replace full list)
# -------------------------
@router.put("/")
async def update_watchlist(data: dict, user: dict = Depends(authenticate)):
    user_id = str(user["_id"])
    symbols = data.get("symbols")
    if symbols is None or not isinstance(symbols, list):
        raise HTTPException(status_code=400, detail="Symbols must be a list")

    # Ensure each symbol has added_at
    for s in symbols:
        if "added_at" not in s:
            s["added_at"] = datetime.utcnow().isoformat() + "Z"

    await Watchlist.update_symbols(user_id, symbols)
    watchlist = await Watchlist.find_by_user(user_id)
    return format_watchlist_symbols(watchlist.get("symbols", []))