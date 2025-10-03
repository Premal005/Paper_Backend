from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime
import jwt, random
from bson import ObjectId

from app.models.userModel import User
from app.models.portfolioModel import Portfolio
from app.models.orderModel import Order

router = APIRouter( tags=["Trades"])
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
# Helper: Calculate PnL
# -------------------------
def calculate_pnl(trade):
    pnl = 0
    pnl_percentage = 0
    if trade.get("executedPrice") and trade["status"] == "closed":
        if trade["side"] == "buy":
            current_price = trade["executedPrice"] * (1 + (random.random() * 0.1 - 0.05))
            pnl = (current_price - trade["executedPrice"]) * trade["quantity"]
            pnl_percentage = ((current_price - trade["executedPrice"]) / trade["executedPrice"]) * 100
        else:
            pnl = (trade["orderPrice"] - trade["executedPrice"]) * trade["quantity"]
            pnl_percentage = ((trade["orderPrice"] - trade["executedPrice"]) / trade["executedPrice"]) * 100
    return round(pnl, 2), round(pnl_percentage, 2), trade.get("executedPrice")


# -------------------------
# Routes
# -------------------------

# Get all trades
@router.get("/", response_model=List[dict])
async def get_trades(
    user_id: str = Depends(authenticate),
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    symbol: Optional[str] = None,
    exchange: Optional[str] = None,
    side: Optional[str] = None,
    startDate: Optional[str] = None,
    endDate: Optional[str] = None
):
    filter = {"userId": ObjectId(user_id)}
    if status: filter["status"] = status
    if symbol: filter["symbol"] = {"$regex": symbol, "$options": "i"}
    if exchange: filter["exchange"] = exchange
    if side: filter["side"] = side
    if startDate or endDate:
        filter["createdAt"] = {}
        if startDate: filter["createdAt"]["$gte"] = datetime.fromisoformat(startDate)
        if endDate: filter["createdAt"]["$lte"] = datetime.fromisoformat(endDate)
    
    trades = await Order.collection.find(filter).sort("createdAt", -1).skip((page-1)*limit).limit(limit).to_list(length=limit)
    for t in trades:
        pnl, pnl_percentage, current_price = calculate_pnl(t)
        t["pnl"] = pnl
        t["pnlPercentage"] = pnl_percentage
        t["currentPrice"] = current_price or t["orderPrice"]
    return trades


# Get trade by ID
@router.get("/{trade_id}")
async def get_trade_by_id(trade_id: str, user_id: str = Depends(authenticate)):
    trade = await Order.collection.find_one({"_id": ObjectId(trade_id), "userId": ObjectId(user_id)})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    pnl, pnl_percentage, current_price = calculate_pnl(trade)
    trade["pnl"] = pnl
    trade["pnlPercentage"] = pnl_percentage
    trade["currentPrice"] = current_price or trade["orderPrice"]
    return trade


# Create trade
@router.post("/")
async def create_trade(data: dict, user_id: str = Depends(authenticate)):
    symbol = data.get("symbol")
    exchange = data.get("exchange")
    side = data.get("side")
    quantity = data.get("quantity")
    orderPrice = data.get("orderPrice")
    orderType = data.get("orderType", "limit")

    user = await User.find_by_id(user_id)
    if side == "buy" and user["balance"] < quantity * orderPrice:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    if side == "sell":
        portfolio = await Portfolio.find_by_user(user_id)
        holding = next((h for h in portfolio.get("holdings", []) if h["symbol"] == symbol and h["exchange"] == exchange), None)
        if not holding or holding["quantity"] < quantity:
            raise HTTPException(status_code=400, detail="Insufficient holdings to sell")
    
    trade_data = {
        "userId": ObjectId(user_id),
        "symbol": symbol,
        "exchange": exchange,
        "side": side,
        "quantity": quantity,
        "orderPrice": orderPrice,
        "orderType": orderType,
        "status": "pending",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    result = await Order.collection.insert_one(trade_data)
    trade_data["_id"] = result.inserted_id
    return trade_data


# Close trade
@router.put("/{trade_id}/close")
async def close_trade(trade_id: str, data: dict, user_id: str = Depends(authenticate)):
    trade = await Order.collection.find_one({"_id": ObjectId(trade_id), "userId": ObjectId(user_id), "status": "active"})
    if not trade:
        raise HTTPException(status_code=404, detail="Active trade not found")
    
    closePrice = data.get("closePrice")
    if not closePrice or closePrice <= 0:
        raise HTTPException(status_code=400, detail="Valid close price is required")
    
    trade["status"] = "closed"
    trade["executedPrice"] = closePrice
    trade["updatedAt"] = datetime.utcnow()
    await Order.collection.replace_one({"_id": ObjectId(trade_id)}, trade)
    
    pnl = (closePrice - trade["orderPrice"]) * trade["quantity"] if trade["side"] == "buy" else (trade["orderPrice"] - closePrice) * trade["quantity"]
    return {"trade": trade, "pnl": round(pnl,2), "pnlPercentage": round((pnl / (trade["orderPrice"] * trade["quantity"])) * 100, 2)}


# Cancel trade
@router.put("/{trade_id}/cancel")
async def cancel_trade(trade_id: str, user_id: str = Depends(authenticate)):
    trade = await Order.collection.find_one({"_id": ObjectId(trade_id), "userId": ObjectId(user_id), "status": "pending"})
    if not trade:
        raise HTTPException(status_code=404, detail="Pending trade not found or already executed")
    
    trade["status"] = "cancelled"
    trade["updatedAt"] = datetime.utcnow()
    await Order.collection.replace_one({"_id": ObjectId(trade_id)}, trade)
    return trade
