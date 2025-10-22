

# from fastapi import APIRouter, Depends, HTTPException, Body, Query, Request
# from typing import Optional
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


# # ---------- Helper: Serialize Order ----------
# def serialize_order(order: dict) -> dict:
#     return {
#         **order,
#         "_id": str(order["_id"]),
#         "userId": str(order["userId"]),
#         "createdAt": order.get("createdAt").isoformat() if order.get("createdAt") else None,
#         "updatedAt": order.get("updatedAt").isoformat() if order.get("updatedAt") else None,
#         "executedPrice": order.get("executedPrice")
#     }


# async def authenticate(req: Request):
#     auth_header = req.headers.get("Authorization")
#     if not auth_header or not auth_header.startswith("Bearer"):
#         raise HTTPException(status_code=401, detail="Access denied. No token provided.")
#     token = auth_header.split(" ")[1]
#     try:
#         payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
#         user = await User.find_by_id(payload["userId"])
#         if not user or not user.get("isActive", True):
#             raise HTTPException(status_code=401, detail="User not found or inactive")
#         return user
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token expired")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=401, detail="Invalid token")


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
#             balance=-order["quantity"] * order["executedPrice"],
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

# #     symbol: str = Body(...),
# #     exchange: str = Body(...),
# #     side: str = Body(..., regex="^(buy|sell)$"),
# #     quantity: float = Body(...),
# #     orderPrice: float = Body(...),
# #     user=Depends(authenticate)
# # ):
# #     total_cost = quantity * orderPrice

# #     # ----- Check balance or holdings -----
# #     if side == "buy":
# #         if user.get("balance", 0) < total_cost:
# #             raise HTTPException(status_code=400, detail="Insufficient balance")
# #     elif side == "sell":
# #         portfolio = await Portfolio.find_by_user(user["_id"])
# #         holding_qty = 0
# #         if portfolio:
# #             h = next(
# #                 (h for h in portfolio.get("holdings", []) if h["symbol"] == symbol and h["exchange"] == exchange),
# #                 None
# #             )
# #             holding_qty = h["quantity"] if h else 0
# #         if holding_qty < quantity:
# #             raise HTTPException(status_code=400, detail="Insufficient holdings to sell")

# #     # ----- Create and execute order immediately -----
# #     order_data = {
# #         "userId": ObjectId(user["_id"]),
# #         "symbol": symbol,
# #         "exchange": exchange,
# #         "side": side,
# #         "quantity": quantity,
# #         "orderPrice": orderPrice,
# #         "status": "active",  # executed immediately
# #         "createdAt": datetime.utcnow(),
# #         "updatedAt": datetime.utcnow(),
# #         "executedPrice": orderPrice
# #     }

# #     order_id = await Order.create(order_data)
# #     order_data["_id"] = ObjectId(order_id)

# #     # ----- Update portfolio and user balance immediately -----
# #     await update_portfolio(order_data, user["_id"])

# #     # Return order in response
# #     return {
# #         "success": True,
# #         "message": "Order executed successfully",
# #         "data": {"order": serialize_order(order_data)}
# #     }
# @router.post("/", summary="Create a new order")
# async def create_order(
#     symbol: str = Body(...),
#     exchange: str = Body(...),
#     side: str = Body(..., regex="^(buy|sell)$"),
#     quantity: float = Body(..., gt=0),
#     orderPrice: float = Body(..., gt=0),
#     user=Depends(authenticate)
# ):
#     total_cost = quantity * orderPrice

#     # --- 1. Validate balance / holdings ---
#     if side == "buy" and user.get("balance", 0) < total_cost:
#         raise HTTPException(status_code=400, detail="Insufficient balance")

#     if side == "sell":
#         portfolio = await Portfolio.find_by_user(user["_id"])
#         holding_qty = 0
#         if portfolio:
#             h = next(
#                 (h for h in portfolio.get("holdings", [])
#                  if h["symbol"] == symbol and h["exchange"] == exchange),
#                 None
#             )
#             holding_qty = h["quantity"] if h else 0
#         if holding_qty < quantity:
#             raise HTTPException(status_code=400, detail="Insufficient holdings to sell")

#     # --- 2. Update user balance immediately ---
#     if side == "buy":
#         # Deduct from balance
#         await User.collection.update_one(
#             {"_id": ObjectId(user["_id"])},
#             {"$inc": {"balance": -total_cost, "margin_used": total_cost}}
#         )
#     else:  # sell
#         # Add to balance
#         await User.collection.update_one(
#             {"_id": ObjectId(user["_id"])},
#             {"$inc": {"balance": total_cost, "margin_used": -total_cost}}
#         )

#     # --- 3. Update portfolio holdings ---
#     portfolio = await Portfolio.find_by_user(user["_id"])
#     if not portfolio:
#         await Portfolio.create(user["_id"])
#         portfolio = await Portfolio.find_by_user(user["_id"])

#     holdings = portfolio.get("holdings", [])
#     idx = next((i for i, h in enumerate(holdings)
#                 if h["symbol"] == symbol and h["exchange"] == exchange), -1)

#     if side == "buy":
#         if idx == -1:
#             holdings.append({
#                 "symbol": symbol,
#                 "exchange": exchange,
#                 "quantity": quantity,
#                 "avgPrice": orderPrice,
#                 "currentPrice": orderPrice,
#                 "pnl": 0
#             })
#         else:
#             h = holdings[idx]
#             total_qty = h["quantity"] + quantity
#             total_val = h["quantity"] * h["avgPrice"] + quantity * orderPrice
#             h["quantity"] = total_qty
#             h["avgPrice"] = total_val / total_qty
#             h["currentPrice"] = orderPrice
#     else:  # sell
#         if idx != -1:
#             h = holdings[idx]
#             h["quantity"] -= quantity
#             if h["quantity"] <= 0:
#                 holdings.pop(idx)

#     total_pnl = sum((h.get("currentPrice", h["avgPrice"]) - h["avgPrice"]) * h["quantity"] for h in holdings)
#     await Portfolio.update_holdings(user["_id"], holdings, total_pnl)

#     # --- 4. Create order in DB ---
#     order_data = {
#         "userId": ObjectId(user["_id"]),
#         "symbol": symbol,
#         "exchange": exchange,
#         "side": side,
#         "quantity": quantity,
#         "orderPrice": orderPrice,
#         "executedPrice": orderPrice*quantity,
#         "status": "active",
#         "createdAt": datetime.utcnow(),
#         "updatedAt": datetime.utcnow()
#     }

#     order_id = await Order.create(order_data)
#     order_data["_id"] = ObjectId(order_id)

#     # --- 5. Return serialized order ---
#     return {
#         "success": True,
#         "message": "Order executed successfully",
#         "data": {"order": serialize_order(order_data)}
#     }

# @router.get("/", summary="Get user orders")
# async def get_orders(
#     page: int = Query(1, ge=1),
#     limit: int = Query(20, ge=1),
#     status: Optional[str] = None,
#     symbol: Optional[str] = None,
#     user=Depends(authenticate)
# ):
#     orders = await Order.find_by_user(user["_id"]) or []

#     # Apply filters
#     if status:
#         orders = [o for o in orders if o["status"] == status]
#     if symbol:
#         orders = [o for o in orders if symbol.lower() in o["symbol"].lower()]

#     # Pagination
#     start = (page - 1) * limit
#     end = start + limit
#     paginated = [
#         {
#             "id": str(o.get("_id")),
#             "symbol": o.get("symbol"),
#             "exchange": o.get("exchange"),
#             "quantity": o.get("quantity"),
#             "side": o.get("side"),
#             "order_type": o.get("orderType"),
#             "price": o.get("orderPrice"),
#             "status": o.get("status"),
#             "created_at": o.get("createdAt"),
#             "executed_at": o.get("executedAt")
#         }
#         for o in orders[start:end]
#     ]

#     # If no orders exist, return one fake order
#     if not paginated:
#         paginated = [{
#             "id": "fake_id",
#             "symbol": "FAKE",
#             "exchange": "FAKE",
#             "quantity": 0,
#             "side": "fake",
#             "order_type": "fake",
#             "price": 0,
#             "status": "fake",
#             "created_at": "2025-01-01T00:00:00Z",
#             "executed_at": None
#         }]

#     total_pages = (len(orders) + limit - 1) // limit

#     return paginated

# @router.get("/{order_id}", summary="Get order by ID")
# async def get_order_by_id(order_id: str, user=Depends(authenticate)):
#     order = next((o for o in await Order.find_by_user(user["_id"]) if str(o["_id"]) == order_id), None)
#     if not order:
#         raise HTTPException(status_code=404, detail="Order not found")
#     return {"success": True, "data": {"order": serialize_order(order)}}


# # @router.put("/{order_id}/cancel", summary="Cancel an order")
# # async def cancel_order(order_id: str, user=Depends(authenticate)):
# #     orders = await Order.find_by_user(user["_id"])
# #     order = next((o for o in orders if str(o["_id"]) == order_id), None)
# #     if not order:
# #         raise HTTPException(status_code=404, detail="Order not found")
# #     if order["status"] != "pending":
# #         raise HTTPException(status_code=400, detail="Only pending orders can be cancelled")
# #     await Order.update_status(order_id, "cancelled")
# #     order["status"] = "cancelled"
# #     order["updatedAt"] = datetime.utcnow()
# #     return {"success": True, "message": "Order cancelled successfully", "data": {"order": serialize_order(order)}}

# @router.get("/stats/{order_id}", summary="Get order statistics")  # remove {order_id}
# async def get_order_stats(user=Depends(authenticate)):
#     try:
#         orders = await Order.find_by_user(user["_id"])
#     except Exception as e:
#         print("Error fetching orders:", e)  # log it
#         orders = []

#     stats = {}
#     total_orders = len(orders)
#     active_orders = len([o for o in orders if o["status"] == "active"])  # only truly active
#     total_invested = sum(o.get("quantity", 0) * o.get("orderPrice", 0) for o in orders)
#     active_investment = sum(o.get("quantity", 0) * o.get("orderPrice", 0)
#                             for o in orders if o.get("status") == "active")

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

# @router.get("/stats", summary="Get order statistics")
# async def get_order_stats(user=Depends(authenticate)):
#     try:
#         orders = await Order.find_by_user(user["_id"])
#         if not orders:
#             orders = []  # Ensure empty list if nothing found
#     except Exception as e:
#         print("Error fetching orders:", e)
#         orders = []

#     # If there are real orders, calculate stats
#     if orders:
#         total_orders = len(orders)
#         executed_orders = len([o for o in orders if o.get("status") == "executed"])
#         pending_orders = len([o for o in orders if o.get("status") == "pending"])
#         cancelled_orders = len([o for o in orders if o.get("status") == "cancelled"])
#         success_rate = round((executed_orders / total_orders) * 100, 2) if total_orders > 0 else 0.0
#     else:
#         # Fake stats when no orders exist
#         total_orders = 0
#         executed_orders = 0
#         pending_orders = 0
#         cancelled_orders = 0
#         success_rate = 0.0

#     # Always return the same structure
#     return {
#        "success": True,
#         "data": {
#             "total_orders": total_orders,
#             "executed_orders": executed_orders,
#             "pending_orders": pending_orders,
#             "cancelled_orders": cancelled_orders,
#             "success_rate": success_rate
#         }
#     }







# from fastapi import APIRouter, Depends, HTTPException, Body, Query, Request, BackgroundTasks
# from typing import Optional
# from bson import ObjectId
# from datetime import datetime
# import jwt
# import os
# import asyncio

# from app.models.userModel import User
# from app.models.portfolioModel import Portfolio
# from app.models.orderModel import Order
# from app.services import alpacaService, fyerService
# from app.routers.market import get_quote_alpaca, get_quote_fyers, get_quote_mt5

# router = APIRouter(tags=["Orders"])
# JWT_SECRET = os.getenv("JWT_SECRET", "secret")

# # ---------- Helper: Serialize Order ----------
# def serialize_order(order: dict) -> dict:
#     return {
#         **order,
#         "_id": str(order["_id"]),
#         "userId": str(order["userId"]),
#         "createdAt": order.get("createdAt").isoformat() if order.get("createdAt") else None,
#         "updatedAt": order.get("updatedAt").isoformat() if order.get("updatedAt") else None,
#         "executedAt": order.get("executedAt").isoformat() if order.get("executedAt") else None,
#         "executedPrice": order.get("executedPrice"),
#         "triggerPrice": order.get("triggerPrice"),
#         "currentMarketPrice": order.get("currentMarketPrice")
#     }

# async def authenticate(req: Request):
#     auth_header = req.headers.get("Authorization")
#     if not auth_header or not auth_header.startswith("Bearer"):
#         raise HTTPException(status_code=401, detail="Access denied. No token provided.")
#     token = auth_header.split(" ")[1]
#     try:
#         payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
#         user = await User.find_by_id(payload["userId"])
#         if not user or not user.get("isActive", True):
#             raise HTTPException(status_code=401, detail="User not found or inactive")
#         return user
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token expired")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=401, detail="Invalid token")

# # ---------- Helper: Get Current Market Price ----------
# async def get_current_market_price(symbol: str, exchange: str) -> float:
#     """Get current market price for a symbol"""
#     try:
#         if exchange in ["ALPACA", "OPTIONS"]:
#             quote = await get_quote_alpaca(symbol)
#         elif exchange == "FYERS":
#             quote = await get_quote_fyers(symbol)
#         elif exchange in ["FOREX", "CRYPTO", "COMEX", "MT5"]:
#             quote = await get_quote_mt5(symbol)
#         else:
#             quote = None
            
#         if quote and quote.get("last_price"):
#             return quote["last_price"]
#         return 0.0
#     except Exception:
#         return 0.0

# # ---------- Helper: Update Portfolio ----------
# async def update_portfolio(order, user_id):
#     portfolio = await Portfolio.find_by_user(user_id)
#     if not portfolio:
#         await Portfolio.create(user_id)
#         portfolio = await Portfolio.find_by_user(user_id)

#     holdings = portfolio.get("holdings", [])
#     idx = next((i for i, h in enumerate(holdings) if h["symbol"] == order["symbol"] and h["exchange"] == order["exchange"]), -1)

#     # Use executedPrice if available, otherwise fallback to orderPrice
#     executed_price = order.get("executedPrice", order.get("orderPrice", 0))
#     quantity = order["quantity"]
#     total_value = quantity * executed_price

#     if order["side"] == "buy":
#         if idx == -1:
#             holdings.append({
#                 "symbol": order["symbol"],
#                 "exchange": order["exchange"],
#                 "quantity": quantity,
#                 "avgPrice": executed_price,
#                 "currentPrice": executed_price,
#                 "pnl": 0
#             })
#         else:
#             h = holdings[idx]
#             total_qty = h["quantity"] + quantity
#             total_val = h["quantity"] * h["avgPrice"] + quantity * executed_price
#             h["avgPrice"] = total_val / total_qty
#             h["quantity"] = total_qty
#             h["currentPrice"] = executed_price

#         # ✅ FIXED: Use correct field names that match User model
#         await User.update_balance(
#             user_id=user_id,
#             balance=-total_value,           # Decrease balance
#             ledger_balance=0,               # No change to ledgerBalance
#             margin_used=total_value,        # Increase marginUsed
#             margin_available=-total_value   # Decrease marginAvailable
#         )

#     elif order["side"] == "sell":
#         if idx != -1:
#             h = holdings[idx]
#             if h["quantity"] == quantity:
#                 holdings.pop(idx)
#             else:
#                 h["quantity"] -= quantity

#             # ✅ FIXED: Use correct field names that match User model
#             await User.update_balance(
#                 user_id=user_id,
#                 balance=total_value,        # Increase balance
#                 ledger_balance=0,           # No change to ledgerBalance  
#                 margin_used=-total_value,   # Decrease marginUsed
#                 margin_available=total_value # Increase marginAvailable
#             )

#     total_pnl = sum((h.get("currentPrice", h["avgPrice"]) - h["avgPrice"]) * h["quantity"] for h in holdings)
#     await Portfolio.update_holdings(user_id, holdings, total_pnl)

# # ---------- Background Task: Process Pending Orders ----------
# async def process_pending_orders():
#     """Background task to check and execute pending orders with DB persistence"""
#     while True:
#         try:
#             # Get FRESH pending orders from database
#             pending_orders = await Order.find_pending_orders()
#             print(f"🔄 Processing {len(pending_orders)} pending orders...")
            
#             for order in pending_orders:
#                 try:
#                     # Get fresh market data
#                     current_price = await get_current_market_price(
#                         order["symbol"], 
#                         order.get("exchange", "ALPACA")
#                     )
                    
#                     if current_price > 0:
#                         order_price = order.get("orderPrice", 0)
#                         trigger_price = order.get("triggerPrice")
#                         condition = order.get("condition")
#                         executed = False
                        
#                         # Check execution conditions
#                         if trigger_price and condition:
#                             # Advanced limit order with conditions
#                             if condition == "less" and current_price <= trigger_price:
#                                 executed = True
#                             elif condition == "greater" and current_price >= trigger_price:
#                                 executed = True
#                         else:
#                             # Basic limit order
#                             if order["side"] == "buy" and current_price <= order_price:
#                                 executed = True
#                             elif order["side"] == "sell" and current_price >= order_price:
#                                 executed = True
                        
#                         if executed:
#                             print(f"✅ Executing order {order['_id']} at price {current_price}")
                            
#                             # Update order status in database FIRST
#                             await Order.update_status(
#                                 str(order["_id"]), 
#                                 "active", 
#                                 current_price
#                             )
                            
#                             # Update portfolio with fresh data
#                             await update_portfolio({
#                                 **order,
#                                 "executedPrice": current_price,
#                                 "status": "active"
#                             }, str(order["userId"]))
                            
#                             print(f"✅ Order {order['_id']} executed successfully")
                            
#                 except Exception as e:
#                     print(f"❌ Error processing order {order.get('_id')}: {e}")
#                     # Log error but continue processing other orders
                    
#         except Exception as e:
#             print(f"❌ Error in process_pending_orders: {e}")
        
#         await asyncio.sleep(10)  # Check every 10 seconds

# # ---------- Routes ----------
# @router.post("/", summary="Create a new order")
# async def create_order(
#     symbol: str = Body(...),
#     exchange: str = Body(...),
#     side: str = Body(..., regex="^(buy|sell)$"),
#     quantity: float = Body(..., gt=0),
#     orderPrice: float = Body(..., gt=0),
#     orderType: str = Body("market", regex="^(market|limit)$"),
#     user=Depends(authenticate)
# ):
#     # Get current user with fresh data from DB
#     current_user = await User.find_by_id(user["_id"])
#     current_price = await get_current_market_price(symbol, exchange)
    
#     if current_price <= 0:
#         raise HTTPException(status_code=400, detail="Unable to get current market price")
    
#     # ✅ FIXED: Market orders execute at CURRENT MARKET PRICE, limit orders at orderPrice
#     if orderType == "market":
#         execution_price = current_price  # Use current market price for execution
#         total_cost = quantity * execution_price
        
#         # Log warning if user specified price differs significantly from market
#         if abs(orderPrice - current_price) > current_price * 0.01:  # More than 1% difference
#             print(f"⚠️ Market order: User specified ${orderPrice}, but executing at market price ${current_price:.2f}")
            
#     else:
#         execution_price = orderPrice  # Will execute at this price when conditions met
#         total_cost = quantity * execution_price

#     # Validate balance/holdings using execution price
#     if side == "buy" and current_user.get("balance", 0) < total_cost:
#         raise HTTPException(status_code=400, detail="Insufficient balance")

#     if side == "sell":
#         portfolio = await Portfolio.find_by_user(current_user["_id"])
#         holding_qty = 0
#         if portfolio:
#             h = next(
#                 (h for h in portfolio.get("holdings", [])
#                  if h["symbol"] == symbol and h["exchange"] == exchange),
#                 None
#             )
#             holding_qty = h["quantity"] if h else 0
#         if holding_qty < quantity:
#             raise HTTPException(status_code=400, detail="Insufficient holdings to sell")

#     # Create order data
#     order_data = {
#         "userId": ObjectId(current_user["_id"]),
#         "symbol": symbol,
#         "exchange": exchange,
#         "side": side,
#         "quantity": quantity,
#         "orderPrice": orderPrice,  # User's intended price (for reference)
#         "orderType": orderType,
#         "status": "pending" if orderType == "limit" else "active",
#         "currentMarketPrice": current_price,
#         "createdAt": datetime.utcnow(),
#         "updatedAt": datetime.utcnow()
#     }

#     # For market orders, execute immediately at CURRENT MARKET PRICE
#     if orderType == "market":
#         order_data["executedPrice"] = current_price  # Use current market price, not orderPrice
#         order_data["status"] = "active"
#         order_data["executedAt"] = datetime.utcnow()
#     else:
#         order_data["executedPrice"] = None
#         order_data["executedAt"] = None

#     # Save order to database
#     order_id = await Order.create(order_data)
#     saved_order = await Order.get_by_id(order_id)
    
#     if not saved_order:
#         raise HTTPException(status_code=500, detail="Failed to save order to database")

#     # Execute market orders immediately at CURRENT MARKET PRICE
#     if orderType == "market":
#         try:
#             await update_portfolio(order_data, current_user["_id"])
#             message = f"Market order executed successfully at current market price ${current_price:.2f}"
            
#         except Exception as e:
#             await Order.update_status(order_id, "failed")
#             raise HTTPException(status_code=500, detail=f"Order execution failed: {str(e)}")
#     else:
#         message = "Limit order placed successfully and will be executed when price condition is met"

#     return {
#         "success": True,
#         "message": message,
#         "data": {
#             "order": serialize_order(saved_order),
#             "databaseSaved": True,
#             "orderId": order_id
#         }
#     }

# @router.post("/close", summary="Close a position")
# async def close_position(
#     symbol: str = Body(...),
#     exchange: str = Body(...),
#     quantity: Optional[float] = Body(None),
#     user=Depends(authenticate)
# ):
#     # Get current portfolio
#     portfolio = await Portfolio.find_by_user(user["_id"])
#     if not portfolio:
#         raise HTTPException(status_code=404, detail="No portfolio found")

#     # Find the holding
#     holding = next(
#         (h for h in portfolio.get("holdings", [])
#          if h["symbol"] == symbol and h["exchange"] == exchange),
#         None
#     )
    
#     if not holding:
#         raise HTTPException(status_code=404, detail="Position not found")

#     # Determine quantity to sell
#     sell_quantity = quantity if quantity else holding["quantity"]
#     if sell_quantity > holding["quantity"]:
#         raise HTTPException(status_code=400, detail="Insufficient holdings")

#     # Get current market price
#     current_price = await get_current_market_price(symbol, exchange)
#     if current_price <= 0:
#         raise HTTPException(status_code=400, detail="Unable to get current market price")

#     # Create sell order
#     order_data = {
#         "userId": ObjectId(user["_id"]),
#         "symbol": symbol,
#         "exchange": exchange,
#         "side": "sell",
#         "quantity": sell_quantity,
#         "orderPrice": current_price,
#         "orderType": "market",
#         "status": "active",
#         "executedPrice": current_price,
#         "isCloseOrder": True,
#         "currentMarketPrice": current_price,
#         "createdAt": datetime.utcnow(),
#         "updatedAt": datetime.utcnow(),
#         "executedAt": datetime.utcnow()
#     }

#     order_id = await Order.create(order_data)
#     order_data["_id"] = ObjectId(order_id)

#     # Update portfolio
#     await update_portfolio(order_data, user["_id"])

#     return {
#         "success": True,
#         "message": f"Position closed successfully for {symbol}",
#         "data": {"order": serialize_order(order_data)}
#     }

# @router.put("/{order_id}/cancel", summary="Cancel a pending order")
# async def cancel_order(order_id: str, user=Depends(authenticate)):
#     orders = await Order.find_by_user(user["_id"])
#     order = next((o for o in orders if str(o["_id"]) == order_id), None)
    
#     if not order:
#         raise HTTPException(status_code=404, detail="Order not found")
    
#     if order["status"] != "pending":
#         raise HTTPException(status_code=400, detail="Only pending orders can be cancelled")
    
#     if order.get("orderType") != "limit":
#         raise HTTPException(status_code=400, detail="Only limit orders can be cancelled")
    
#     await Order.cancel_order(order_id)
    
#     # Fetch updated order
#     updated_order = await Order.get_by_id(order_id)
    
#     return {
#         "success": True, 
#         "message": "Order cancelled successfully", 
#         "data": {"order": serialize_order(updated_order)}
#     }

# @router.post("/limit", summary="Place a limit order with specific conditions")
# async def place_limit_order(
#     symbol: str = Body(...),
#     exchange: str = Body(...),
#     side: str = Body(..., regex="^(buy|sell)$"),
#     quantity: float = Body(..., gt=0),
#     limitPrice: float = Body(..., gt=0),
#     condition: str = Body(..., regex="^(less|greater)$"),
#     triggerPrice: float = Body(None),
#     user=Depends(authenticate)
# ):
#     """
#     Place advanced limit orders:
#     - condition="less": Buy when price is 0.5% less than current
#     - condition="greater": Sell when price is 0.5% more than current
#     - triggerPrice: Specific price to trigger the order
#     """
    
#     current_user = await User.find_by_id(user["_id"])
#     current_price = await get_current_market_price(symbol, exchange)
    
#     # Calculate trigger price if not provided
#     if not triggerPrice:
#         if condition == "less" and side == "buy":
#             triggerPrice = current_price * 0.995  # 0.5% less
#         elif condition == "greater" and side == "sell":
#             triggerPrice = current_price * 1.005  # 0.5% more
#         else:
#             raise HTTPException(
#                 status_code=400, 
#                 detail="Invalid condition for this order side"
#             )

#     # Validate balance/holdings
#     total_cost = quantity * limitPrice
    
#     if side == "buy" and current_user.get("balance", 0) < total_cost:
#         raise HTTPException(status_code=400, detail="Insufficient balance")

#     if side == "sell":
#         portfolio = await Portfolio.find_by_user(current_user["_id"])
#         holding_qty = 0
#         if portfolio:
#             h = next(
#                 (h for h in portfolio.get("holdings", [])
#                  if h["symbol"] == symbol and h["exchange"] == exchange),
#                 None
#             )
#             holding_qty = h["quantity"] if h else 0
#         if holding_qty < quantity:
#             raise HTTPException(status_code=400, detail="Insufficient holdings to sell")

#     # Create advanced limit order
#     order_data = {
#         "userId": ObjectId(current_user["_id"]),
#         "symbol": symbol,
#         "exchange": exchange,
#         "side": side,
#         "quantity": quantity,
#         "orderPrice": limitPrice,
#         "orderType": "limit",
#         "status": "pending",
#         "triggerPrice": triggerPrice,
#         "condition": condition,
#         "currentMarketPrice": current_price,
#         "createdAt": datetime.utcnow(),
#         "updatedAt": datetime.utcnow(),
#         "executedPrice": None
#     }

#     order_id = await Order.create(order_data)
#     saved_order = await Order.get_by_id(order_id)

#     return {
#         "success": True,
#         "message": f"Limit order placed successfully. Will trigger when price is {condition} than {triggerPrice:.2f}",
#         "data": {
#             "order": serialize_order(saved_order),
#             "databaseSaved": True,
#             "orderId": order_id
#         }
#     }

# @router.get("/", summary="Get user orders")
# async def get_orders(
#     page: int = Query(1, ge=1),
#     limit: int = Query(20, ge=1),
#     status: Optional[str] = None,
#     symbol: Optional[str] = None,
#     order_type: Optional[str] = Query(None, alias="type"),
#     user=Depends(authenticate)
# ):
#     orders = await Order.find_by_user(user["_id"]) or []

#     # Apply filters
#     if status:
#         orders = [o for o in orders if o["status"] == status]
#     if symbol:
#         orders = [o for o in orders if symbol.lower() in o["symbol"].lower()]
#     if order_type:
#         orders = [o for o in orders if o.get("orderType") == order_type]

#     # Pagination
#     start = (page - 1) * limit
#     end = start + limit
    
#     paginated = [
#         {
#             "id": str(o.get("_id")),
#             "symbol": o.get("symbol"),
#             "exchange": o.get("exchange"),
#             "quantity": o.get("quantity"),
#             "side": o.get("side"),
#             "order_type": o.get("orderType"),
#             "price": o.get("orderPrice"),
#             "executed_price": o.get("executedPrice"),
#             "status": o.get("status"),
#             "trigger_price": o.get("triggerPrice"),
#             "condition": o.get("condition"),
#             "current_market_price": o.get("currentMarketPrice"),
#             "created_at": o.get("createdAt"),
#             "updated_at": o.get("updatedAt"),
#             "executed_at": o.get("executedAt")
#         }
#         for o in orders[start:end]
#     ]

#     total_pages = (len(orders) + limit - 1) // limit

#     return {
#         "orders": paginated,
#         "pagination": {
#             "page": page,
#             "limit": limit,
#             "total": len(orders),
#             "pages": total_pages
#         }
#     }

# @router.get("/{order_id}", summary="Get order by ID")
# async def get_order_by_id(order_id: str, user=Depends(authenticate)):
#     order = await Order.get_by_id(order_id)
#     if not order or str(order.get("userId")) != user["_id"]:
#         raise HTTPException(status_code=404, detail="Order not found")
#     return {"success": True, "data": {"order": serialize_order(order)}}

# @router.get("/stats", summary="Get order statistics")
# async def get_order_stats(user=Depends(authenticate)):
#     try:
#         orders = await Order.find_by_user(user["_id"])
#         if not orders:
#             orders = []
#     except Exception as e:
#         print("Error fetching orders:", e)
#         orders = []

#     # Calculate stats
#     total_orders = len(orders)
#     executed_orders = len([o for o in orders if o.get("status") == "active"])
#     pending_orders = len([o for o in orders if o.get("status") == "pending"])
#     cancelled_orders = len([o for o in orders if o.get("status") == "cancelled"])
#     success_rate = round((executed_orders / total_orders) * 100, 2) if total_orders > 0 else 0.0

#     return {
#         "success": True,
#         "data": {
#             "total_orders": total_orders,
#             "executed_orders": executed_orders,
#             "pending_orders": pending_orders,
#             "cancelled_orders": cancelled_orders,
#             "success_rate": success_rate
#         }
#     }

# # Database Verification Endpoints
# @router.get("/debug/verify/{order_id}", summary="Verify order persistence in DB")
# async def verify_order_persistence(order_id: str, user=Depends(authenticate)):
#     """Debug endpoint to verify order is actually saved in database"""
#     # Get from database directly
#     db_order = await Order.get_by_id(order_id)
    
#     if not db_order:
#         return {
#             "success": False,
#             "message": "Order not found in database",
#             "inDatabase": False
#         }
    
#     # Verify user ownership
#     if str(db_order.get("userId")) != user["_id"]:
#         return {
#             "success": False,
#             "message": "Order does not belong to user",
#             "inDatabase": True
#         }
    
#     return {
#         "success": True,
#         "message": "Order found in database",
#         "inDatabase": True,
#         "data": {
#             "order": serialize_order(db_order),
#             "rawDatabaseData": {
#                 "id": str(db_order.get("_id")),
#                 "symbol": db_order.get("symbol"),
#                 "status": db_order.get("status"),
#                 "orderType": db_order.get("orderType"),
#                 "executedPrice": db_order.get("executedPrice"),
#                 "triggerPrice": db_order.get("triggerPrice"),
#                 "condition": db_order.get("condition"),
#                 "currentMarketPrice": db_order.get("currentMarketPrice"),
#                 "createdAt": db_order.get("createdAt"),
#                 "updatedAt": db_order.get("updatedAt")
#             }
#         }
#     }

# @router.get("/debug/all-orders", summary="Get all user orders from DB (debug)")
# async def get_all_orders_debug(user=Depends(authenticate)):
#     """Debug endpoint to see ALL orders from database"""
#     orders = await Order.find_by_user(user["_id"]) or []
    
#     return {
#         "success": True,
#         "totalOrders": len(orders),
#         "data": {
#             "orders": [serialize_order(order) for order in orders],
#             "summary": {
#                 "pending": len([o for o in orders if o.get("status") == "pending"]),
#                 "active": len([o for o in orders if o.get("status") == "active"]),
#                 "cancelled": len([o for o in orders if o.get("status") == "cancelled"]),
#                 "market": len([o for o in orders if o.get("orderType") == "market"]),
#                 "limit": len([o for o in orders if o.get("orderType") == "limit"])
#             }
#         }
#     }

# # Start background task when application starts
# @router.on_event("startup")
# async def start_order_processor():
#     asyncio.create_task(process_pending_orders())


from fastapi import APIRouter, Depends, HTTPException, Body, Query, Request, BackgroundTasks
from typing import Optional
from bson import ObjectId
from datetime import datetime
import jwt
import os
import asyncio

from app.models.userModel import User
from app.models.portfolioModel import Portfolio
from app.models.orderModel import Order
from app.services.pnl_service import PnLService
from app.services import alpacaService, fyerService
from app.routers.market import get_quote_alpaca, get_quote_fyers, get_quote_mt5

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
        "executedAt": order.get("executedAt").isoformat() if order.get("executedAt") else None,
        "executedPrice": order.get("executedPrice"),
        "triggerPrice": order.get("triggerPrice"),
        "currentMarketPrice": order.get("currentMarketPrice")
    }

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

# ---------- Helper: Get Current Market Price ----------
async def get_current_market_price(symbol: str, exchange: str) -> float:
    """Get current market price for a symbol"""
    try:
        if exchange in ["ALPACA", "OPTIONS"]:
            quote = await get_quote_alpaca(symbol)
        elif exchange == "FYERS":
            quote = await get_quote_fyers(symbol)
        elif exchange in ["FOREX", "CRYPTO", "COMEX", "MT5"]:
            quote = await get_quote_mt5(symbol)
        else:
            quote = None
            
        if quote and quote.get("last_price"):
            return quote["last_price"]
        return 0.0
    except Exception:
        return 0.0

# ---------- Helper: Update Portfolio ----------
async def update_portfolio(order, user_id, current_price: float = None):
    """Update portfolio with proper margin and PnL calculations"""
    user = await User.get_full_user(user_id)
    portfolio = await Portfolio.find_by_user(user_id)
    
    if not portfolio:
        await Portfolio.create(user_id)
        portfolio = await Portfolio.find_by_user(user_id)

    # Use executed price or current price
    executed_price = order.get("executedPrice", order.get("orderPrice", 0))
    current_price = current_price or executed_price
    quantity = order["quantity"]
    leverage = order.get("leverage", 20)
    
    # Calculate margin used
    margin_used = await PnLService.calculate_margin_used(executed_price, quantity, leverage)
    total_trade_value = quantity * executed_price

    if order["side"] == "buy":
        # For opening long position
        if order.get("status") == "active" and not order.get("isClosed", False):
            # Update holdings
            holdings = portfolio.get("holdings", [])
            idx = next((i for i, h in enumerate(holdings) if h["symbol"] == order["symbol"] and h["exchange"] == order["exchange"]), -1)

            if idx == -1:
                holdings.append({
                    "symbol": order["symbol"],
                    "exchange": order["exchange"],
                    "quantity": quantity,
                    "avgPrice": executed_price,
                    "currentPrice": current_price,
                    "leverage": leverage,
                    "marginUsed": margin_used,
                    "pnl": 0
                })
            else:
                h = holdings[idx]
                total_qty = h["quantity"] + quantity
                total_val = h["quantity"] * h["avgPrice"] + quantity * executed_price
                h["avgPrice"] = total_val / total_qty
                h["quantity"] = total_qty
                h["currentPrice"] = current_price
                h["marginUsed"] += margin_used

            await User.update_balance(
                user_id=user_id,
                margin_used=margin_used,
                margin_available=-margin_used
            )

    elif order["side"] == "sell":
        # Check if this is closing a position
        holdings = portfolio.get("holdings", [])
        holding_idx = next((i for i, h in enumerate(holdings) if h["symbol"] == order["symbol"] and h["exchange"] == order["exchange"]), -1)
        
        if holding_idx != -1 and order.get("isCloseOrder", False):
            holding = holdings[holding_idx]
            
            # Calculate PnL for this trade
            entry_price = holding["avgPrice"]
            executed_price = order.get("executedPrice", current_price)
            pnl = (executed_price - entry_price) * order["quantity"]
            
            # Calculate margin to release
            margin_to_release = holding["marginUsed"]
            
            # ✅ FIX: Only add PnL to ledger_balance
            # The balance will be automatically recalculated as: ledger_balance - margin_used
            await User.update_balance(
                user_id=user_id,
                ledger_balance=pnl,           # Add PnL to ledger
                margin_used=-margin_to_release, # Release margin
                margin_available=margin_to_release # Add back to available
            )
            
            # Close the matching buy orders
            from app.database import db
            await db.orders.update_many(
                {
                    "userId": ObjectId(user_id),
                    "symbol": order["symbol"],
                    "exchange": order["exchange"], 
                    "side": "buy",
                    "status": "active",
                    "isClosed": False
                },
                {
                    "$set": {
                        "status": "closed",
                        "isClosed": True,
                        "closedAt": datetime.utcnow(),
                        "updatedAt": datetime.utcnow()
                    }
                }
            )

            if order.get("_id"):
                await Order.close_order(str(order["_id"]), pnl)
            
            # Update holding
            if holding["quantity"] == order["quantity"]:
                holdings.pop(holding_idx)
            else:
                holding["quantity"] -= order["quantity"]
                # Recalculate margin for remaining position
                holding["marginUsed"] = await PnLService.calculate_margin_used(
                    holding["avgPrice"], holding["quantity"], holding.get("leverage", 20)
                )

    # Update portfolio with current prices and recalculate PnL
    await PnLService.update_trade_prices(order["symbol"], order["exchange"], current_price)
    active_pnl = await PnLService.calculate_active_pnl(user_id)
    
    await Portfolio.update_holdings(user_id, portfolio.get("holdings", []), active_pnl)
    
# ---------- Background Task: Process Pending Orders ----------
async def process_pending_orders():
    """Background task to check and execute pending orders with margin validation"""
    while True:
        try:
            # Get FRESH pending orders from database
            pending_orders = await Order.find_pending_orders()
            print(f"🔄 Processing {len(pending_orders)} pending orders...")
            
            for order in pending_orders:
                try:
                    # Get fresh market data
                    current_price = await get_current_market_price(
                        order["symbol"], 
                        order.get("exchange", "ALPACA")
                    )
                    
                    if current_price > 0:
                        order_price = order.get("orderPrice", 0)
                        trigger_price = order.get("triggerPrice")
                        condition = order.get("condition")
                        executed = False
                        
                        # Check execution conditions
                        if trigger_price and condition:
                            # Advanced limit order with conditions
                            if condition == "less" and current_price <= trigger_price:
                                executed = True
                            elif condition == "greater" and current_price >= trigger_price:
                                executed = True
                        else:
                            # Basic limit order
                            if order["side"] == "buy" and current_price <= order_price:
                                executed = True
                            elif order["side"] == "sell" and current_price >= order_price:
                                executed = True
                        
                        if executed:
                            print(f"✅ Executing order {order['_id']} at price {current_price}")
                            
                            # Check margin availability before execution
                            user = await User.get_full_user(str(order["userId"]))
                            required_margin = await PnLService.calculate_margin_used(
                                current_price, 
                                order["quantity"], 
                                order.get("leverage", 20)
                            )
                            
                            available_margin = user.get("marginAvailable", 0)
                            
                            if available_margin >= required_margin:
                                # Reserve margin
                                # await User.update_balance(
                                #     user_id=str(order["userId"]),
                                #     margin_used=required_margin,
                                #     margin_available=-required_margin
                                # )
                                
                                # Update order status in database
                                await Order.update_status(
                                    str(order["_id"]), 
                                    "active", 
                                    current_price
                                )
                                
                                # Update order with actual margin used
                                await Order.update_order(str(order["_id"]), {
                                    "marginUsed": required_margin,
                                    "executedPrice": current_price,
                                    "currentMarketPrice": current_price
                                })
                                
                                # Update portfolio with fresh data
                                await update_portfolio({
                                    **order,
                                    "executedPrice": current_price,
                                    "marginUsed": required_margin,
                                    "status": "active"
                                }, str(order["userId"]), current_price)
                                
                                print(f"✅ Order {order['_id']} executed successfully with margin: {required_margin}")
                            else:
                                print(f"❌ Insufficient margin for order {order['_id']}. Available: {available_margin}, Required: {required_margin}")
                                await Order.update_status(str(order["_id"]), "cancelled")
                                
                except Exception as e:
                    print(f"❌ Error processing order {order.get('_id')}: {e}")
                    # Log error but continue processing other orders
                    
        except Exception as e:
            print(f"❌ Error in process_pending_orders: {e}")
        
        await asyncio.sleep(10)  # Check every 10 seconds

# ---------- Routes ----------
@router.post("/", summary="Create a new order")
async def create_order(
    symbol: str = Body(...),
    exchange: str = Body(...),
    side: str = Body(..., regex="^(buy|sell)$"),
    quantity: float = Body(..., gt=0),
    orderPrice: float = Body(..., gt=0),
    orderType: str = Body("market", regex="^(market|limit)$"),
    leverage: int = Body(20, ge=1),  # ✅ PRESET to 20 as default
    user=Depends(authenticate)
):
    # Get current user with fresh data from DB
    current_user = await User.get_full_user(user["_id"])
    current_price = await get_current_market_price(symbol, exchange)
    
    if current_price <= 0:
        raise HTTPException(status_code=400, detail="Unable to get current market price")
    
    # ✅ Calculate required margin with leverage 20
    trade_price = current_price if orderType == "market" else orderPrice
    required_margin = await PnLService.calculate_margin_used(trade_price, quantity, leverage)
    
    # Check margin availability instead of full balance
    available_margin = current_user.get("marginAvailable", 0)
    
    if side == "buy" and available_margin < required_margin:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient margin. Available: {available_margin:.2f}, Required: {required_margin:.2f} (Leverage: {leverage}x)"
        )

    # For sell orders, check if we have the holding (for closing) or enough margin (for shorting)
    if side == "sell":
        portfolio = await Portfolio.find_by_user(current_user["_id"])
        
        # Check if we're closing an existing long position
        existing_holding = None
        if portfolio:
            existing_holding = next(
                (h for h in portfolio.get("holdings", [])
                 if h["symbol"] == symbol and h["exchange"] == exchange),
                None
            )
        
        if existing_holding:
            # Closing long position - check quantity
            if existing_holding["quantity"] < quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient holdings. Available: {existing_holding['quantity']}, Requested: {quantity}"
                )
        else:
            # Opening short position - check margin
            if available_margin < required_margin:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient margin for short. Available: {available_margin:.2f}, Required: {required_margin:.2f} (Leverage: {leverage}x)"
                )

    # ✅ Market orders execute at CURRENT MARKET PRICE, limit orders at orderPrice
    if orderType == "market":
        execution_price = current_price  # Use current market price for execution
        status = "active"
        executed_at = datetime.utcnow()
    else:
        execution_price = orderPrice  # Will execute at this price when conditions met
        status = "pending"
        executed_at = None

    # Create order data with margin information and leverage 20
    order_data = {
        "userId": ObjectId(current_user["_id"]),
        "symbol": symbol,
        "exchange": exchange,
        "side": side,
        "quantity": quantity,
        "orderPrice": orderPrice,  # User's intended price (for reference)
        "orderType": orderType,
        "leverage": leverage,  # ✅ Now preset to 20
        "marginUsed": required_margin,
        "status": status,
        "currentMarketPrice": current_price,
        "executedPrice": execution_price if orderType == "market" else None,
        "executedAt": executed_at,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
        "isClosed": False,
        "pnl": 0
    }

    # Save order to database
    order_id = await Order.create_with_pnl(order_data)
    saved_order = await Order.get_by_id(order_id)
    
    if not saved_order:
        raise HTTPException(status_code=500, detail="Failed to save order to database")

    # For market orders, execute immediately and reserve margin
    if orderType == "market":
        try:
            # Reserve margin immediately for market orders
            # await User.update_balance(
            #     user_id=current_user["_id"],
            #     margin_used=required_margin,
            #     margin_available=-required_margin
            # )

            order_data["_id"] = ObjectId(order_id)
            # Update portfolio with the trade
            await update_portfolio(order_data, current_user["_id"], current_price)
            
            message = f"Market order executed successfully at {current_price:.2f} with {leverage}x leverage (Margin: {required_margin:.2f})"
            
        except Exception as e:
            # If execution fails, revert margin reservation
            await User.update_balance(
                user_id=current_user["_id"],
                margin_used=-required_margin,
                margin_available=required_margin
            )
            await Order.update_status(order_id, "failed")
            raise HTTPException(status_code=500, detail=f"Order execution failed: {str(e)}")
    else:
        # For limit orders, we'll reserve margin when it gets executed
        message = f"Limit order placed successfully with {leverage}x leverage. Will execute when price condition is met"

    return {
        "success": True,
        "message": message,
        "data": {
            "order": serialize_order(saved_order),
            "databaseSaved": True,
            "orderId": order_id,
            "marginUsed": required_margin,
            "leverage": leverage,
            "tradeValue": round(trade_price * quantity, 2),
            "marginPercentage": round((required_margin / (trade_price * quantity)) * 100, 2) if trade_price * quantity > 0 else 0
        }
    }

@router.post("/close", summary="Close a position")
async def close_position(
    symbol: str = Body(...),
    exchange: str = Body(...),
    quantity: Optional[float] = Body(None),
    user=Depends(authenticate)
):
    # Get current portfolio
    portfolio = await Portfolio.find_by_user(user["_id"])
    if not portfolio:
        raise HTTPException(status_code=404, detail="No portfolio found")

    # Find the holding
    holding = next(
        (h for h in portfolio.get("holdings", [])
         if h["symbol"] == symbol and h["exchange"] == exchange),
        None
    )
    
    if not holding:
        raise HTTPException(status_code=404, detail="Position not found")

    # Determine quantity to sell
    sell_quantity = quantity if quantity else holding["quantity"]
    if sell_quantity > holding["quantity"]:
        raise HTTPException(status_code=400, detail="Insufficient holdings")

    # Get current market price
    current_price = await get_current_market_price(symbol, exchange)
    if current_price <= 0:
        raise HTTPException(status_code=400, detail="Unable to get current market price")

    # Calculate PnL for this closing trade
    entry_price = holding["avgPrice"]
    pnl = (current_price - entry_price) * sell_quantity
    
    # Calculate margin to be released (proportional to quantity being closed)
    total_margin_used = holding.get("marginUsed", 0)
    margin_to_release = (sell_quantity / holding["quantity"]) * total_margin_used

    # Create sell order for closing
    order_data = {
        "userId": ObjectId(user["_id"]),
        "symbol": symbol,
        "exchange": exchange,
        "side": "sell",
        "quantity": sell_quantity,
        "orderPrice": current_price,
        "orderType": "market",
        "status": "active",
        "executedPrice": current_price,
        "isCloseOrder": True,
        "currentMarketPrice": current_price,
        "leverage": holding.get("leverage", 20),
        "marginUsed": margin_to_release,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
        "executedAt": datetime.utcnow()
    }

    order_id = await Order.create_with_pnl(order_data)
    order_data["_id"] = ObjectId(order_id)

    # Update portfolio and release margin + add PnL
    await update_portfolio(order_data, user["_id"], current_price)
    
    # Mark order as closed with PnL
    # await Order.close_order(order_id, pnl)

    return {
        "success": True,
        "message": f"Position closed successfully for {symbol}. PnL: {pnl:.2f}",
        "data": {
            "order": serialize_order(order_data),
            "pnl": pnl,
            "marginReleased": margin_to_release
        }
    }

@router.put("/{order_id}/cancel", summary="Cancel a pending order")
async def cancel_order(order_id: str, user=Depends(authenticate)):
    orders = await Order.find_by_user(user["_id"])
    order = next((o for o in orders if str(o["_id"]) == order_id), None)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["status"] != "pending":
        raise HTTPException(status_code=400, detail="Only pending orders can be cancelled")
    
    if order.get("orderType") != "limit":
        raise HTTPException(status_code=400, detail="Only limit orders can be cancelled")
    
    await Order.cancel_order(order_id)
    
    # Fetch updated order
    updated_order = await Order.get_by_id(order_id)
    
    return {
        "success": True, 
        "message": "Order cancelled successfully", 
        "data": {"order": serialize_order(updated_order)}
    }

@router.post("/limit", summary="Place a limit order with specific conditions")
async def place_limit_order(
    symbol: str = Body(...),
    exchange: str = Body(...),
    side: str = Body(..., regex="^(buy|sell)$"),
    quantity: float = Body(..., gt=0),
    limitPrice: float = Body(..., gt=0),
    condition: str = Body(..., regex="^(less|greater)$"),
    triggerPrice: float = Body(None),
    leverage: int = Body(20, ge=1),  # ✅ PRESET to 20 as default
    user=Depends(authenticate)
):
    """
    Place advanced limit orders with 20x leverage by default
    """
    
    current_user = await User.get_full_user(user["_id"])
    current_price = await get_current_market_price(symbol, exchange)
    
    # Calculate required margin with leverage 20
    required_margin = await PnLService.calculate_margin_used(limitPrice, quantity, leverage)
    available_margin = current_user.get("marginAvailable", 0)
    
    # Check margin availability
    if available_margin < required_margin:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient margin. Available: {available_margin:.2f}, Required: {required_margin:.2f} (Leverage: {leverage}x)"
        )

    # Calculate trigger price if not provided
    if not triggerPrice:
        if condition == "less" and side == "buy":
            triggerPrice = current_price * 0.995  # 0.5% less
        elif condition == "greater" and side == "sell":
            triggerPrice = current_price * 1.005  # 0.5% more
        else:
            raise HTTPException(
                status_code=400, 
                detail="Invalid condition for this order side"
            )

    # Validate holdings for sell orders
    if side == "sell":
        portfolio = await Portfolio.find_by_user(current_user["_id"])
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

    # Create advanced limit order with leverage 20
    order_data = {
        "userId": ObjectId(current_user["_id"]),
        "symbol": symbol,
        "exchange": exchange,
        "side": side,
        "quantity": quantity,
        "orderPrice": limitPrice,
        "orderType": "limit",
        "leverage": leverage,  # ✅ Now preset to 20
        "marginUsed": required_margin,
        "status": "pending",
        "triggerPrice": triggerPrice,
        "condition": condition,
        "currentMarketPrice": current_price,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
        "executedPrice": None,
        "isClosed": False,
        "pnl": 0
    }

    order_id = await Order.create_with_pnl(order_data)
    saved_order = await Order.get_by_id(order_id)

    return {
        "success": True,
        "message": f"Limit order placed with {leverage}x leverage. Will trigger when price is {condition} than {triggerPrice:.2f}",
        "data": {
            "order": serialize_order(saved_order),
            "databaseSaved": True,
            "orderId": order_id,
            "marginRequired": required_margin,
            "leverage": leverage
        }
    }

@router.post("/check-margin", summary="Check margin requirement for an order")
async def check_margin_requirement(
    symbol: str = Body(...),
    exchange: str = Body(...),
    side: str = Body(..., regex="^(buy|sell)$"),
    quantity: float = Body(..., gt=0),
    orderPrice: float = Body(..., gt=0),
    leverage: int = Body(20, ge=1),  # ✅ PRESET to 20 as default
    user=Depends(authenticate)
):
    """Check if user has sufficient margin for a proposed order with 20x leverage"""
    current_user = await User.get_full_user(user["_id"])
    current_price = await get_current_market_price(symbol, exchange)
    
    # Use current price for realistic check, order price for limit orders
    check_price = current_price if current_price > 0 else orderPrice
    
    required_margin = await PnLService.calculate_margin_used(check_price, quantity, leverage)
    available_margin = current_user.get("marginAvailable", 0)
    trade_value = check_price * quantity
    
    return {
        "success": True,
        "data": {
            "requiredMargin": round(required_margin, 2),
            "availableMargin": round(available_margin, 2),
            "sufficient": available_margin >= required_margin,
            "leverage": leverage,
            "tradeValue": round(trade_value, 2),
            "marginPercentage": round((required_margin / trade_value) * 100, 2) if trade_value > 0 else 0,
            "buyingPowerUtilization": round((required_margin / available_margin) * 100, 2) if available_margin > 0 else 0,
            "message": f"With {leverage}x leverage, you need {required_margin:.2f} margin for {trade_value:.2f} trade"
        }
    }

@router.get("/", summary="Get user orders")
async def get_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1),
    status: Optional[str] = None,
    symbol: Optional[str] = None,
    order_type: Optional[str] = Query(None, alias="type"),
    user=Depends(authenticate)
):
    orders = await Order.find_by_user(user["_id"]) or []

    # Apply filters
    if status:
        orders = [o for o in orders if o["status"] == status]
    if symbol:
        orders = [o for o in orders if symbol.lower() in o["symbol"].lower()]
    if order_type:
        orders = [o for o in orders if o.get("orderType") == order_type]

    # Pagination
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
            "executed_price": o.get("executedPrice"),
            "status": o.get("status"),
            "leverage": o.get("leverage", 20),
            "margin_used": o.get("marginUsed", 0),
            "pnl": o.get("pnl", 0),
            "trigger_price": o.get("triggerPrice"),
            "condition": o.get("condition"),
            "current_market_price": o.get("currentMarketPrice"),
            "created_at": o.get("createdAt"),
            "updated_at": o.get("updatedAt"),
            "executed_at": o.get("executedAt")
        }
        for o in orders[start:end]
    ]

    total_pages = (len(orders) + limit - 1) // limit

    return {
        "orders": paginated,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": len(orders),
            "pages": total_pages
        }
    }

@router.get("/{order_id}", summary="Get order by ID")
async def get_order_by_id(order_id: str, user=Depends(authenticate)):
    order = await Order.get_by_id(order_id)
    if not order or str(order.get("userId")) != user["_id"]:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"success": True, "data": {"order": serialize_order(order)}}

@router.get("/stats", summary="Get order statistics")
async def get_order_stats(user=Depends(authenticate)):
    try:
        orders = await Order.find_by_user(user["_id"])
        if not orders:
            orders = []
    except Exception as e:
        print("Error fetching orders:", e)
        orders = []

    # Calculate stats
    total_orders = len(orders)
    executed_orders = len([o for o in orders if o.get("status") == "active"])
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

# Database Verification Endpoints
@router.get("/debug/verify/{order_id}", summary="Verify order persistence in DB")
async def verify_order_persistence(order_id: str, user=Depends(authenticate)):
    """Debug endpoint to verify order is actually saved in database"""
    # Get from database directly
    db_order = await Order.get_by_id(order_id)
    
    if not db_order:
        return {
            "success": False,
            "message": "Order not found in database",
            "inDatabase": False
        }
    
    # Verify user ownership
    if str(db_order.get("userId")) != user["_id"]:
        return {
            "success": False,
            "message": "Order does not belong to user",
            "inDatabase": True
        }
    
    return {
        "success": True,
        "message": "Order found in database",
        "inDatabase": True,
        "data": {
            "order": serialize_order(db_order),
            "rawDatabaseData": {
                "id": str(db_order.get("_id")),
                "symbol": db_order.get("symbol"),
                "status": db_order.get("status"),
                "orderType": db_order.get("orderType"),
                "executedPrice": db_order.get("executedPrice"),
                "triggerPrice": db_order.get("triggerPrice"),
                "condition": db_order.get("condition"),
                "currentMarketPrice": db_order.get("currentMarketPrice"),
                "leverage": db_order.get("leverage", 20),
                "marginUsed": db_order.get("marginUsed", 0),
                "createdAt": db_order.get("createdAt"),
                "updatedAt": db_order.get("updatedAt")
            }
        }
    }

@router.get("/debug/all-orders", summary="Get all user orders from DB (debug)")
async def get_all_orders_debug(user=Depends(authenticate)):
    """Debug endpoint to see ALL orders from database"""
    orders = await Order.find_by_user(user["_id"]) or []
    
    return {
        "success": True,
        "totalOrders": len(orders),
        "data": {
            "orders": [serialize_order(order) for order in orders],
            "summary": {
                "pending": len([o for o in orders if o.get("status") == "pending"]),
                "active": len([o for o in orders if o.get("status") == "active"]),
                "cancelled": len([o for o in orders if o.get("status") == "cancelled"]),
                "market": len([o for o in orders if o.get("orderType") == "market"]),
                "limit": len([o for o in orders if o.get("orderType") == "limit"])
            }
        }
    }

@router.post("/debug/fix-order-status", summary="Fix order status issues")
async def fix_order_status(user=Depends(authenticate)):
    """Fix order status for corrupted data"""
    from app.database import db
    
    # Find all active buy orders for ETHUSD that should be closed
    active_buys = await db.orders.find({
        "userId": ObjectId(user["_id"]),
        "symbol": "ETHUSD", 
        "side": "buy",
        "status": "active"
    }).to_list(length=None)
    
    fixed_orders = []
    for order in active_buys:
        # Check if this order has been closed by a sell order
        corresponding_sell = await db.orders.find_one({
            "userId": ObjectId(user["_id"]),
            "symbol": "ETHUSD",
            "side": "sell", 
            "isCloseOrder": True,
            "executedAt": {"$gte": order["executedAt"]}
        })
        
        if corresponding_sell:
            # Mark the buy order as closed
            await db.orders.update_one(
                {"_id": order["_id"]},
                {"$set": {
                    "status": "closed",
                    "isClosed": True,
                    "closedAt": corresponding_sell["executedAt"],
                    "updatedAt": datetime.utcnow()
                }}
            )
            fixed_orders.append(str(order["_id"]))
    
    # Recalculate margin based on actual active orders
    active_orders = await db.orders.find({
        "userId": ObjectId(user["_id"]),
        "status": "active",
        "isClosed": False
    }).to_list(length=None)
    
    total_margin_used = sum(order.get("marginUsed", 0) for order in active_orders)
    
    # Update user margin
    user_data = await db.users.find_one({"_id": ObjectId(user["_id"])})
    ledger_balance = user_data.get("ledgerBalance", 100000)
    
    await db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {
            "marginUsed": total_margin_used,
            "marginAvailable": ledger_balance - total_margin_used
        }}
    )
    
    return {
        "success": True, 
        "message": f"Fixed {len(fixed_orders)} orders",
        "fixed_orders": fixed_orders,
        "current_margin_used": total_margin_used
    }

# Start background task when application starts
@router.on_event("startup")
async def start_order_processor():
    asyncio.create_task(process_pending_orders())