# from fastapi import APIRouter, Depends, HTTPException, Body, Query
# from typing import List, Optional
# from bson import ObjectId
# from datetime import datetime
# import jwt
# import os
# import asyncio

# from app.models.userModel import User
# from app.models.portfolioModel import Portfolio
# from app.models.orderModel import Order

# router = APIRouter(tags=["Orders"])
# JWT_SECRET = os.getenv("JWT_SECRET", "secret")


# # ---------- Authentication Dependency ----------
# async def authenticate(token: str = Depends(lambda: None)):
#     from fastapi import Request
#     async def _inner(req: Request):
#         auth_header = req.headers.get("Authorization")
#         if not auth_header or not auth_header.startswith("Bearer "):
#             raise HTTPException(status_code=401, detail="Access denied. No token provided.")
#         token = auth_header.split(" ")[1]
#         try:
#             payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
#             user = await User.find_by_id(payload["userId"])
#             if not user or not user.get("isActive", True):
#                 raise HTTPException(status_code=401, detail="User no longer exists or is deactivated")
#             return user
#         except jwt.ExpiredSignatureError:
#             raise HTTPException(status_code=401, detail="Token expired")
#         except jwt.InvalidTokenError:
#             raise HTTPException(status_code=401, detail="Invalid token")
#     return _inner


# # ---------- Helper: Update Portfolio ----------
# async def update_portfolio(order, user_id):
#     portfolio = await Portfolio.find_by_user(user_id)
#     if not portfolio:
#         await Portfolio.create(user_id)
#         portfolio = await Portfolio.find_by_user(user_id)

#     holdings = portfolio.get("holdings", [])
#     idx = next((i for i, h in enumerate(holdings) if h["symbol"] == order["symbol"] and h["exchange"] == order["exchange"]), -1)

#     if order["side"] == "buy":
#         if idx == -1:
#             holdings.append({
#                 "symbol": order["symbol"],
#                 "exchange": order["exchange"],
#                 "quantity": order["quantity"],
#                 "avgPrice": order["executedPrice"],
#                 "currentPrice": order["executedPrice"],
#                 "pnl": 0
#             })
#         else:
#             h = holdings[idx]
#             total_qty = h["quantity"] + order["quantity"]
#             total_val = h["quantity"] * h["avgPrice"] + order["quantity"] * order["executedPrice"]
#             h["avgPrice"] = total_val / total_qty
#             h["quantity"] = total_qty
#             h["currentPrice"] = order["executedPrice"]

#         await User.update_balance(
#             user_id,
#             balance=-order["quantity"] * order["executedPrice"],  # adjust accordingly
#             ledger_balance=0,
#             margin_used=order["quantity"] * order["executedPrice"],
#             margin_available=0
#         )

#     elif order["side"] == "sell":
#         if idx != -1:
#             h = holdings[idx]
#             if h["quantity"] == order["quantity"]:
#                 holdings.pop(idx)
#             else:
#                 h["quantity"] -= order["quantity"]

#             await User.update_balance(
#                 user_id,
#                 balance=order["quantity"] * order["executedPrice"],
#                 ledger_balance=0,
#                 margin_used=-order["quantity"] * order["executedPrice"],
#                 margin_available=0
#             )

#     total_pnl = sum((h.get("currentPrice", h["avgPrice"]) - h["avgPrice"]) * h["quantity"] for h in holdings)
#     await Portfolio.update_holdings(user_id, holdings, total_pnl)


# # ---------- Routes ----------

# @router.post("/", summary="Create a new order")
# async def create_order(
#     symbol: str = Body(...),
#     exchange: str = Body(...),
#     side: str = Body(..., regex="^(buy|sell)$"),
#     quantity: float = Body(...),
#     orderPrice: float = Body(...),
#     user=Depends(authenticate)
# ):
#     # Check balance for buy
#     if side == "buy" and user["balance"] < quantity * orderPrice:
#         raise HTTPException(status_code=400, detail="Insufficient balance")

#     # Check holdings for sell
#     if side == "sell":
#         portfolio = await Portfolio.find_by_user(user["_id"])
#         holding_qty = 0
#         if portfolio:
#             h = next((h for h in portfolio.get("holdings", []) if h["symbol"] == symbol and h["exchange"] == exchange), None)
#             holding_qty = h["quantity"] if h else 0
#         if holding_qty < quantity:
#             raise HTTPException(status_code=400, detail="Insufficient holdings to sell")

#     order_data = {
#         "userId": ObjectId(user["_id"]),
#         "symbol": symbol,
#         "exchange": exchange,
#         "side": side,
#         "quantity": quantity,
#         "orderPrice": orderPrice,
#         "status": "pending",
#         "createdAt": datetime.utcnow(),
#         "updatedAt": datetime.utcnow()
#     }

#     order_id = await Order.create(order_data)
#     order_data["_id"] = ObjectId(order_id)

#     # Simulate execution after 2 seconds
#     async def execute_order():
#         await asyncio.sleep(2)
#         order_data["status"] = "active"
#         order_data["executedPrice"] = orderPrice
#         order_data["updatedAt"] = datetime.utcnow()
#         await update_portfolio(order_data, user["_id"])

#     asyncio.create_task(execute_order())

#     return {"success": True, "message": "Order created successfully", "data": {"order": order_data}}


# @router.get("/", summary="Get user orders")
# async def get_orders(
#     page: int = Query(1, ge=1),
#     limit: int = Query(20, ge=1),
#     status: Optional[str] = None,
#     symbol: Optional[str] = None,
#     user=Depends(authenticate)
# ):
#     orders = await Order.find_by_user(user["_id"])
#     if status:
#         orders = [o for o in orders if o["status"] == status]
#     if symbol:
#         orders = [o for o in orders if symbol.lower() in o["symbol"].lower()]

#     start = (page - 1) * limit
#     end = start + limit
#     paginated = orders[start:end]
#     total_pages = (len(orders) + limit - 1) // limit

#     return {
#         "success": True,
#         "data": {
#             "orders": paginated,
#             "pagination": {
#                 "currentPage": page,
#                 "totalPages": total_pages,
#                 "totalOrders": len(orders),
#                 "hasNext": page < total_pages,
#                 "hasPrev": page > 1
#             }
#         }
#     }


# @router.get("/{order_id}", summary="Get order by ID")
# async def get_order_by_id(order_id: str, user=Depends(authenticate)):
#     order = next((o for o in await Order.find_by_user(user["_id"]) if str(o["_id"]) == order_id), None)
#     if not order:
#         raise HTTPException(status_code=404, detail="Order not found")
#     return {"success": True, "data": {"order": order}}


# @router.put("/{order_id}/cancel", summary="Cancel an order")
# async def cancel_order(order_id: str, user=Depends(authenticate)):
#     orders = await Order.find_by_user(user["_id"])
#     order = next((o for o in orders if str(o["_id"]) == order_id), None)
#     if not order:
#         raise HTTPException(status_code=404, detail="Order not found")
#     if order["status"] != "pending":
#         raise HTTPException(status_code=400, detail="Only pending orders can be cancelled")
#     await Order.update_status(order_id, "cancelled")
#     order["status"] = "cancelled"
#     order["updatedAt"] = datetime.utcnow()
#     return {"success": True, "message": "Order cancelled successfully", "data": {"order": order}}


# @router.get("/stats", summary="Get order statistics")
# async def get_order_stats(user=Depends(authenticate)):
#     orders = await Order.find_by_user(user["_id"])
#     stats = {}
#     total_orders = len(orders)
#     active_orders = len([o for o in orders if o["status"] in ["pending", "active"]])
#     total_invested = sum(o["quantity"] * o["orderPrice"] for o in orders)
#     active_investment = sum(o["quantity"] * o["orderPrice"] for o in orders if o["status"] in ["pending", "active"])

#     # Group by status
#     for o in orders:
#         stats[o["status"]] = stats.get(o["status"], {"count": 0, "totalQuantity": 0, "totalValue": 0})
#         stats[o["status"]]["count"] += 1
#         stats[o["status"]]["totalQuantity"] += o["quantity"]
#         stats[o["status"]]["totalValue"] += o["quantity"] * o["orderPrice"]

#     return {
#         "success": True,
#         "data": {
#             "stats": stats,
#             "totalOrders": total_orders,
#             "activeOrders": active_orders,
#             "summary": {
#                 "totalInvested": total_invested,
#                 "activeInvestment": active_investment
#             }
#         }
#     }







from fastapi import APIRouter, Depends, HTTPException, Body, Query, Request
from typing import Optional
from bson import ObjectId
from datetime import datetime
import jwt
import os
import asyncio

from app.models.userModel import User
from app.models.portfolioModel import Portfolio
from app.models.orderModel import Order

router = APIRouter(tags=["Orders"])
JWT_SECRET = os.getenv("JWT_SECRET", "secret")


# ---------- Helper: Serialize Order ----------
def serialize_order(order: dict) -> dict:
    return {
        **order,
        "_id": str(order["_id"]),
        "userId": str(order["userId"]),
        "createdAt": order.get("createdAt").isoformat() if order.get("createdAt") else None,
        "updatedAt": order.get("updatedAt").isoformat() if order.get("updatedAt") else None,
        "executedPrice": order.get("executedPrice")
    }


# ---------- Authentication Dependency ----------
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
#         return user  # user dict
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token expired")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=401, detail="Invalid token")


async def authenticate(req: Request):
    auth_header = req.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer"):
        raise HTTPException(status_code=401, detail="Access denied. No token provided.")
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user = await User.find_by_id(payload["userId"])
        if not user or not user.get("isActive", True):
            raise HTTPException(status_code=401, detail="User not found or inactive")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")





# ---------- Helper: Update Portfolio ----------
async def update_portfolio(order, user_id):
    portfolio = await Portfolio.find_by_user(user_id)
    if not portfolio:
        await Portfolio.create(user_id)
        portfolio = await Portfolio.find_by_user(user_id)

    holdings = portfolio.get("holdings", [])
    idx = next((i for i, h in enumerate(holdings) if h["symbol"] == order["symbol"] and h["exchange"] == order["exchange"]), -1)

    if order["side"] == "buy":
        if idx == -1:
            holdings.append({
                "symbol": order["symbol"],
                "exchange": order["exchange"],
                "quantity": order["quantity"],
                "avgPrice": order["executedPrice"],
                "currentPrice": order["executedPrice"],
                "pnl": 0
            })
        else:
            h = holdings[idx]
            total_qty = h["quantity"] + order["quantity"]
            total_val = h["quantity"] * h["avgPrice"] + order["quantity"] * order["executedPrice"]
            h["avgPrice"] = total_val / total_qty
            h["quantity"] = total_qty
            h["currentPrice"] = order["executedPrice"]

        await User.update_balance(
            user_id,
            balance=-order["quantity"] * order["executedPrice"],
            ledger_balance=0,
            margin_used=order["quantity"] * order["executedPrice"],
            margin_available=0
        )

    elif order["side"] == "sell":
        if idx != -1:
            h = holdings[idx]
            if h["quantity"] == order["quantity"]:
                holdings.pop(idx)
            else:
                h["quantity"] -= order["quantity"]

            await User.update_balance(
                user_id,
                balance=order["quantity"] * order["executedPrice"],
                ledger_balance=0,
                margin_used=-order["quantity"] * order["executedPrice"],
                margin_available=0
            )

    total_pnl = sum((h.get("currentPrice", h["avgPrice"]) - h["avgPrice"]) * h["quantity"] for h in holdings)
    await Portfolio.update_holdings(user_id, holdings, total_pnl)


# ---------- Routes ----------

#     symbol: str = Body(...),
#     exchange: str = Body(...),
#     side: str = Body(..., regex="^(buy|sell)$"),
#     quantity: float = Body(...),
#     orderPrice: float = Body(...),
#     user=Depends(authenticate)
# ):
#     total_cost = quantity * orderPrice

#     # ----- Check balance or holdings -----
#     if side == "buy":
#         if user.get("balance", 0) < total_cost:
#             raise HTTPException(status_code=400, detail="Insufficient balance")
#     elif side == "sell":
#         portfolio = await Portfolio.find_by_user(user["_id"])
#         holding_qty = 0
#         if portfolio:
#             h = next(
#                 (h for h in portfolio.get("holdings", []) if h["symbol"] == symbol and h["exchange"] == exchange),
#                 None
#             )
#             holding_qty = h["quantity"] if h else 0
#         if holding_qty < quantity:
#             raise HTTPException(status_code=400, detail="Insufficient holdings to sell")

#     # ----- Create and execute order immediately -----
#     order_data = {
#         "userId": ObjectId(user["_id"]),
#         "symbol": symbol,
#         "exchange": exchange,
#         "side": side,
#         "quantity": quantity,
#         "orderPrice": orderPrice,
#         "status": "active",  # executed immediately
#         "createdAt": datetime.utcnow(),
#         "updatedAt": datetime.utcnow(),
#         "executedPrice": orderPrice
#     }

#     order_id = await Order.create(order_data)
#     order_data["_id"] = ObjectId(order_id)

#     # ----- Update portfolio and user balance immediately -----
#     await update_portfolio(order_data, user["_id"])

#     # Return order in response
#     return {
#         "success": True,
#         "message": "Order executed successfully",
#         "data": {"order": serialize_order(order_data)}
#     }
@router.post("/", summary="Create a new order")
async def create_order(
    symbol: str = Body(...),
    exchange: str = Body(...),
    side: str = Body(..., regex="^(buy|sell)$"),
    quantity: float = Body(..., gt=0),
    orderPrice: float = Body(..., gt=0),
    user=Depends(authenticate)
):
    total_cost = quantity * orderPrice

    # --- 1. Validate balance / holdings ---
    if side == "buy" and user.get("balance", 0) < total_cost:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    if side == "sell":
        portfolio = await Portfolio.find_by_user(user["_id"])
        holding_qty = 0
        if portfolio:
            h = next(
                (h for h in portfolio.get("holdings", [])
                 if h["symbol"] == symbol and h["exchange"] == exchange),
                None
            )
            holding_qty = h["quantity"] if h else 0
        if holding_qty < quantity:
            raise HTTPException(status_code=400, detail="Insufficient holdings to sell")

    # --- 2. Update user balance immediately ---
    if side == "buy":
        # Deduct from balance
        await User.collection.update_one(
            {"_id": ObjectId(user["_id"])},
            {"$inc": {"balance": -total_cost, "margin_used": total_cost}}
        )
    else:  # sell
        # Add to balance
        await User.collection.update_one(
            {"_id": ObjectId(user["_id"])},
            {"$inc": {"balance": total_cost, "margin_used": -total_cost}}
        )

    # --- 3. Update portfolio holdings ---
    portfolio = await Portfolio.find_by_user(user["_id"])
    if not portfolio:
        await Portfolio.create(user["_id"])
        portfolio = await Portfolio.find_by_user(user["_id"])

    holdings = portfolio.get("holdings", [])
    idx = next((i for i, h in enumerate(holdings)
                if h["symbol"] == symbol and h["exchange"] == exchange), -1)

    if side == "buy":
        if idx == -1:
            holdings.append({
                "symbol": symbol,
                "exchange": exchange,
                "quantity": quantity,
                "avgPrice": orderPrice,
                "currentPrice": orderPrice,
                "pnl": 0
            })
        else:
            h = holdings[idx]
            total_qty = h["quantity"] + quantity
            total_val = h["quantity"] * h["avgPrice"] + quantity * orderPrice
            h["quantity"] = total_qty
            h["avgPrice"] = total_val / total_qty
            h["currentPrice"] = orderPrice
    else:  # sell
        if idx != -1:
            h = holdings[idx]
            h["quantity"] -= quantity
            if h["quantity"] <= 0:
                holdings.pop(idx)

    total_pnl = sum((h.get("currentPrice", h["avgPrice"]) - h["avgPrice"]) * h["quantity"] for h in holdings)
    await Portfolio.update_holdings(user["_id"], holdings, total_pnl)

    # --- 4. Create order in DB ---
    order_data = {
        "userId": ObjectId(user["_id"]),
        "symbol": symbol,
        "exchange": exchange,
        "side": side,
        "quantity": quantity,
        "orderPrice": orderPrice,
        "executedPrice": orderPrice*quantity,
        "status": "active",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }

    order_id = await Order.create(order_data)
    order_data["_id"] = ObjectId(order_id)

    # --- 5. Return serialized order ---
    return {
        "success": True,
        "message": "Order executed successfully",
        "data": {"order": serialize_order(order_data)}
    }

# @router.get("/", summary="Get user orders")
# async def get_orders(
#     page: int = Query(1, ge=1),
#     limit: int = Query(20, ge=1),
#     status: Optional[str] = None,
#     symbol: Optional[str] = None,
#     user=Depends(authenticate)
# ):
#     orders = await Order.find_by_user(user["_id"])
#     if status:
#         orders = [o for o in orders if o["status"] == status]
#     if symbol:
#         orders = [o for o in orders if symbol.lower() in o["symbol"].lower()]

#     start = (page - 1) * limit
#     end = start + limit
#     paginated = [serialize_order(o) for o in orders[start:end]]
#     total_pages = (len(orders) + limit - 1) // limit

#     return {
#         "success": True,
#         "data": {
#             "orders": paginated,
#             "pagination": {
#                 "currentPage": page,
#                 "totalPages": total_pages,
#                 "totalOrders": len(orders),
#                 "hasNext": page < total_pages,
#                 "hasPrev": page > 1
#             }
#         }
#     }
@router.get("/", summary="Get user orders")
async def get_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1),
    status: Optional[str] = None,
    symbol: Optional[str] = None,
    user=Depends(authenticate)
):
    orders = await Order.find_by_user(user["_id"])
    if status:
        orders = [o for o in orders if o["status"] == status]
    if symbol:
        orders = [o for o in orders if symbol.lower() in o["symbol"].lower()]

    start = (page - 1) * limit
    end = start + limit
    paginated = [
        {
            "id": str(o.get("_id")),
            "symbol": o.get("symbol"),
            "exchange": o.get("exchange"),
            "quantity": o.get("quantity"),
            "side": o.get("side"),
            "order_type": o.get("orderType"),
            "price": o.get("orderPrice"),
            "status": o.get("status"),
            "created_at": o.get("createdAt"),
            "executed_at": o.get("executedAt")
        }
        for o in orders[start:end]
    ]
    total_pages = (len(orders) + limit - 1) // limit

    return {
        "success": True,
        "data": paginated  # 👈 Matches your dummy ordersResponse structure (list only)
    }

@router.get("/{order_id}", summary="Get order by ID")
async def get_order_by_id(order_id: str, user=Depends(authenticate)):
    order = next((o for o in await Order.find_by_user(user["_id"]) if str(o["_id"]) == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"success": True, "data": {"order": serialize_order(order)}}


# @router.put("/{order_id}/cancel", summary="Cancel an order")
# async def cancel_order(order_id: str, user=Depends(authenticate)):
#     orders = await Order.find_by_user(user["_id"])
#     order = next((o for o in orders if str(o["_id"]) == order_id), None)
#     if not order:
#         raise HTTPException(status_code=404, detail="Order not found")
#     if order["status"] != "pending":
#         raise HTTPException(status_code=400, detail="Only pending orders can be cancelled")
#     await Order.update_status(order_id, "cancelled")
#     order["status"] = "cancelled"
#     order["updatedAt"] = datetime.utcnow()
#     return {"success": True, "message": "Order cancelled successfully", "data": {"order": serialize_order(order)}}

@router.get("/stats/{order_id}", summary="Get order statistics")  # remove {order_id}
async def get_order_stats(user=Depends(authenticate)):
    try:
        orders = await Order.find_by_user(user["_id"])
    except Exception as e:
        print("Error fetching orders:", e)  # log it
        orders = []

    stats = {}
    total_orders = len(orders)
    active_orders = len([o for o in orders if o["status"] == "active"])  # only truly active
    total_invested = sum(o.get("quantity", 0) * o.get("orderPrice", 0) for o in orders)
    active_investment = sum(o.get("quantity", 0) * o.get("orderPrice", 0)
                            for o in orders if o.get("status") == "active")

    for o in orders:
        key = o.get("status", "unknown")
        if key not in stats:
            stats[key] = {"count": 0, "totalQuantity": 0, "totalValue": 0}
        stats[key]["count"] += 1
        stats[key]["totalQuantity"] += o.get("quantity", 0)
        stats[key]["totalValue"] += o.get("quantity", 0) * o.get("orderPrice", 0)

    return {
        "success": True,
        "data": {
            "stats": stats,
            "totalOrders": total_orders,
            "activeOrders": active_orders,
            "summary": {
                "totalInvested": total_invested,
                "activeInvestment": active_investment
            }
        }
    }



# @router.get("/stats", summary="Get order statistics")
# async def get_order_stats(user=Depends(authenticate)):
#     try:
#         orders = await Order.find_by_user(user["_id"]) or []
#     except Exception as e:
#         print("Error fetching orders:", e)
#         orders = []

#     stats = {}
#     total_orders = len(orders)
#     active_orders = len([o for o in orders if o.get("status") == "active"])
#     total_invested = sum(o.get("quantity", 0) * o.get("orderPrice", 0) for o in orders)
#     active_investment = sum(
#         o.get("quantity", 0) * o.get("orderPrice", 0)
#         for o in orders if o.get("status") == "active"
#     )

#     for o in orders:
#         key = o.get("status", "unknown")
#         if key not in stats:
#             stats[key] = {"count": 0, "totalQuantity": 0, "totalValue": 0}
#         stats[key]["count"] += 1
#         stats[key]["totalQuantity"] += o.get("quantity", 0)
#         stats[key]["totalValue"] += o.get("quantity", 0) * o.get("orderPrice", 0)

#     return {
#         "success": True,
#         "data": {
#             "stats": stats,
#             "totalOrders": total_orders,
#             "activeOrders": active_orders,
#             "summary": {
#                 "totalInvested": total_invested,
#                 "activeInvestment": active_investment
#             }
#         }
#     }
@router.get("/stats", summary="Get order statistics")
async def get_order_stats(user=Depends(authenticate)):
    try:
        orders = await Order.find_by_user(user["_id"]) or []
    except Exception as e:
        print("Error fetching orders:", e)
        orders = []

    total_orders = len(orders)
    executed_orders = len([o for o in orders if o.get("status") == "executed"])
    pending_orders = len([o for o in orders if o.get("status") == "pending"])
    cancelled_orders = len([o for o in orders if o.get("status") == "cancelled"])

    success_rate = round((executed_orders / total_orders) * 100, 2) if total_orders > 0 else 0.0

    return {
        "success": True,
        "data": {
            "total_orders": total_orders,
            "executed_orders": executed_orders,
            "pending_orders": pending_orders,
            "cancelled_orders": cancelled_orders,
            "success_rate": success_rate
        }
    }