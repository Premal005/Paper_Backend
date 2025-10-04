# # from fastapi import APIRouter, Depends, HTTPException, Body
# # from typing import List, Optional
# # from bson import ObjectId
# # from datetime import datetime
# # import jwt
# # import os

# # from app.models.userModel import User
# # from app.models.portfolioModel import Portfolio

# # router = APIRouter(tags=["Portfolio"])

# # JWT_SECRET = os.getenv("JWT_SECRET", "secret")


# # # ---------- Authentication Dependency ----------
# # async def authenticate(token: str = Depends(lambda: None)):
# #     """
# #     Dummy Depends to extract token from Authorization header
# #     FastAPI recommends OAuth2PasswordBearer, but we mimic Express JWT flow.
# #     """
# #     from fastapi import Request
# #     async def _inner(req: Request):
# #         auth_header = req.headers.get("Authorization")
# #         if not auth_header or not auth_header.startswith("Bearer "):
# #             raise HTTPException(status_code=401, detail="Access denied. No token provided.")
# #         token = auth_header.split(" ")[1]
# #         try:
# #             payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
# #             user = await User.find_by_id(payload["userId"])
# #             if not user or not user.get("isActive", True):
# #                 raise HTTPException(status_code=401, detail="User no longer exists or is deactivated")
# #             return user
# #         except jwt.ExpiredSignatureError:
# #             raise HTTPException(status_code=401, detail="Token expired")
# #         except jwt.InvalidTokenError:
# #             raise HTTPException(status_code=401, detail="Invalid token")
# #     return _inner


# # # ---------- Routes ----------
# # @router.get("/", summary="Get user portfolio")
# # async def get_portfolio(user=Depends(authenticate)):
# #     portfolio = await Portfolio.find_by_user(user["_id"])
# #     if not portfolio:
# #         # Create empty portfolio if it doesn't exist
# #         portfolio_id = await Portfolio.create(str(user["_id"]))
# #         portfolio = await Portfolio.find_by_user(user["_id"])
# #         summary = {"totalValue": 0, "totalInvested": 0, "totalPnl": 0, "pnlPercentage": 0}
# #     else:
# #         total_invested = sum(h["quantity"] * h["avgPrice"] for h in portfolio.get("holdings", []))
# #         total_current = sum(h["quantity"] * (h.get("currentPrice") or h["avgPrice"]) for h in portfolio.get("holdings", []))
# #         total_pnl = total_current - total_invested
# #         pnl_percentage = (total_pnl / total_invested * 100) if total_invested else 0
# #         summary = {
# #             "totalValue": round(total_current, 2),
# #             "totalInvested": round(total_invested, 2),
# #             "totalPnl": round(total_pnl, 2),
# #             "pnlPercentage": round(pnl_percentage, 2)
# #         }

# #     return {"success": True, "data": {"portfolio": portfolio, "summary": summary}}


# # @router.get("/holdings", summary="Get portfolio holdings")
# # async def get_portfolio_holdings(user=Depends(authenticate)):
# #     portfolio = await Portfolio.find_by_user(user["_id"])
# #     if not portfolio:
# #         return {"success": True, "data": {"holdings": [], "totalHoldings": 0}}

# #     holdings_with_details = []
# #     for h in portfolio.get("holdings", []):
# #         invested = h["quantity"] * h["avgPrice"]
# #         current_value = h["quantity"] * (h.get("currentPrice") or h["avgPrice"])
# #         pnl = current_value - invested
# #         pnl_percentage = (pnl / invested * 100) if invested else 0
# #         h_detail = h.copy()
# #         h_detail.update({
# #             "invested": round(invested, 2),
# #             "currentValue": round(current_value, 2),
# #             "pnl": round(pnl, 2),
# #             "pnlPercentage": round(pnl_percentage, 2)
# #         })
# #         holdings_with_details.append(h_detail)

# #     return {"success": True, "data": {"holdings": holdings_with_details, "totalHoldings": len(holdings_with_details)}}


# # @router.put("/update-prices", summary="Update holding prices")
# # async def update_holding_prices(priceUpdates: List[dict] = Body(...), user=Depends(authenticate)):
# #     portfolio = await Portfolio.find_by_user(user["_id"])
# #     if not portfolio:
# #         raise HTTPException(status_code=404, detail="Portfolio not found")

# #     total_pnl = 0
# #     for h in portfolio.get("holdings", []):
# #         update = next((p for p in priceUpdates if p["symbol"] == h["symbol"] and p["exchange"] == h["exchange"]), None)
# #         if update:
# #             h["currentPrice"] = update["currentPrice"]
# #             invested = h["quantity"] * h["avgPrice"]
# #             current_value = h["quantity"] * h["currentPrice"]
# #             h["pnl"] = current_value - invested
# #             total_pnl += h["pnl"]

# #     await Portfolio.update_holdings(user["_id"], portfolio.get("holdings", []), total_pnl)

# #     return {"success": True, "message": "Prices updated successfully", "data": {"totalPnl": round(total_pnl, 2)}}


# # @router.get("/performance", summary="Get portfolio performance")
# # async def get_portfolio_performance(user=Depends(authenticate)):
# #     portfolio = await Portfolio.find_by_user(user["_id"])
# #     if not portfolio or not portfolio.get("holdings"):
# #         return {"success": True, "data": {"dailyPnl": 0, "weeklyPnl": 0, "monthlyPnl": 0, "totalPnl": 0, "bestPerformer": None, "worstPerformer": None}}

# #     performance_data = {
# #         "dailyPnl": round((0.5 - 0.5) * 2000, 2),  # Mocked
# #         "weeklyPnl": round((0.5 - 0.5) * 5000, 2),
# #         "monthlyPnl": round((0.5 - 0.5) * 15000, 2),
# #         "totalPnl": portfolio.get("totalPnl", 0)
# #     }

# #     best = None
# #     worst = None
# #     for h in portfolio.get("holdings", []):
# #         pnl_pct = ((h.get("currentPrice") or h["avgPrice"]) - h["avgPrice"]) / h["avgPrice"] * 100 if h["avgPrice"] else 0
# #         entry = {"symbol": h["symbol"], "pnlPercentage": round(pnl_pct, 2), "pnl": h.get("pnl", 0)}
# #         if not best or pnl_pct > best["pnlPercentage"]:
# #             best = entry
# #         if not worst or pnl_pct < worst["pnlPercentage"]:
# #             worst = entry

# #     performance_data.update({"bestPerformer": best, "worstPerformer": worst, "holdingsCount": len(portfolio.get("holdings", []))})
# #     return {"success": True, "data": performance_data}

# from fastapi import APIRouter, Depends, HTTPException, Body, Request
# from typing import List
# from bson import ObjectId
# from datetime import datetime
# import jwt
# import os

# from app.models.userModel import User
# from app.models.portfolioModel import Portfolio

# router = APIRouter(tags=["Portfolio"])

# JWT_SECRET = os.getenv("JWT_SECRET", "secret")


# # ---------- Helper: Convert ObjectId to str recursively ----------
# def clean_doc(doc):
#     """Convert ObjectId to string for JSON serialization recursively"""
#     if not doc:
#         return doc
#     if isinstance(doc, list):
#         return [clean_doc(d) for d in doc]
#     if isinstance(doc, dict):
#         new_doc = {}
#         for key, value in doc.items():
#             if isinstance(value, ObjectId):
#                 new_doc[key] = str(value)
#             elif isinstance(value, dict) or isinstance(value, list):
#                 new_doc[key] = clean_doc(value)
#             else:
#                 new_doc[key] = value
#         return new_doc
#     return doc


# # ---------- Authentication Dependency ----------
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


# # ---------- Get user portfolio ----------
# @router.get("/", summary="Get user portfolio")
# async def get_portfolio(user=Depends(authenticate)):
#     portfolio = await Portfolio.find_by_user(user["_id"])
#     portfolio = clean_doc(portfolio)

#     if not portfolio:
#         portfolio_id = await Portfolio.create(str(user["_id"]))
#         portfolio = await Portfolio.find_by_user(user["_id"])
#         portfolio = clean_doc(portfolio)
#         summary = {"totalValue": 0, "totalInvested": 0, "totalPnl": 0, "pnlPercentage": 0}
#     else:
#         total_invested = sum(h["quantity"] * h["avgPrice"] for h in portfolio.get("holdings", []))
#         total_current = sum(h["quantity"] * (h.get("currentPrice") or h["avgPrice"]) for h in portfolio.get("holdings", []))
#         total_pnl = total_current - total_invested
#         pnl_percentage = (total_pnl / total_invested * 100) if total_invested else 0
#         summary = {
#             "totalValue": round(total_current, 2),
#             "totalInvested": round(total_invested, 2),
#             "totalPnl": round(total_pnl, 2),
#             "pnlPercentage": round(pnl_percentage, 2)
#         }

#     return {"success": True, "data": {"portfolio": portfolio, "summary": summary}}


# # ---------- Get portfolio holdings ----------
# @router.get("/holdings", summary="Get portfolio holdings")
# async def get_portfolio_holdings(user=Depends(authenticate)):
#     portfolio = await Portfolio.find_by_user(user["_id"])
#     portfolio = clean_doc(portfolio)

#     if not portfolio:
#         return {"success": True, "data": {"holdings": [], "totalHoldings": 0}}

#     holdings_with_details = []
#     for h in portfolio.get("holdings", []):
#         invested = h["quantity"] * h["avgPrice"]
#         current_value = h["quantity"] * (h.get("currentPrice") or h["avgPrice"])
#         pnl = current_value - invested
#         pnl_percentage = (pnl / invested * 100) if invested else 0
#         h_detail = h.copy()
#         h_detail.update({
#             "invested": round(invested, 2),
#             "currentValue": round(current_value, 2),
#             "pnl": round(pnl, 2),
#             "pnlPercentage": round(pnl_percentage, 2)
#         })
#         holdings_with_details.append(h_detail)

#     return {"success": True, "data": {"holdings": holdings_with_details, "totalHoldings": len(holdings_with_details)}}


# # ---------- Update holding prices ----------
# # ---------- Update holding prices ----------
# @router.put("/update-prices", summary="Update holding prices")
# async def update_holding_prices(priceUpdates: List[dict] = Body(...), user=Depends(authenticate)):
#     portfolio = await Portfolio.find_by_user(user["_id"])
#     portfolio = clean_doc(portfolio)

#     if not portfolio or not portfolio.get("holdings"):
#         raise HTTPException(status_code=404, detail="Portfolio not found or empty")

#     total_pnl = 0
#     for h in portfolio.get("holdings", []):
#         # Case-insensitive matching for symbol and exchange
#         update = next((p for p in priceUpdates
#                        if p.get("symbol", "").upper() == h.get("symbol", "").upper()
#                        and p.get("exchange", "").upper() == h.get("exchange", "").upper()), None)
#         if update:
#             # Only update if currentPrice is provided
#             current_price = update.get("currentPrice")
#             if current_price is not None:
#                 h["currentPrice"] = current_price

#                 quantity = h.get("quantity", 0)
#                 avg_price = h.get("avgPrice", 0)

#                 invested = quantity * avg_price
#                 current_value = quantity * h["currentPrice"]
#                 h["pnl"] = current_value - invested
#                 total_pnl += h["pnl"]

#     # Save updated holdings back to DB
#     await Portfolio.update_holdings(user["_id"], portfolio.get("holdings", []), total_pnl)

#     return {
#         "success": True,
#         "message": "Prices updated successfully",
#         "data": {
#             "totalPnl": round(total_pnl, 2)
#         }
#     }


# # ---------- Get portfolio performance ----------
# @router.get("/performance", summary="Get portfolio performance")
# async def get_portfolio_performance(user=Depends(authenticate)):
#     portfolio = await Portfolio.find_by_user(user["_id"])
#     portfolio = clean_doc(portfolio)

#     if not portfolio or not portfolio.get("holdings"):
#         return {"success": True, "data": {"dailyPnl": 0, "weeklyPnl": 0, "monthlyPnl": 0, "totalPnl": 0, "bestPerformer": None, "worstPerformer": None}}

#     performance_data = {
#         "dailyPnl": 0,  # Replace with actual calculation
#         "weeklyPnl": 0,
#         "monthlyPnl": 0,
#         "totalPnl": portfolio.get("totalPnl", 0)
#     }

#     best = None
#     worst = None
#     for h in portfolio.get("holdings", []):
#         pnl_pct = ((h.get("currentPrice") or h["avgPrice"]) - h["avgPrice"]) / h["avgPrice"] * 100 if h["avgPrice"] else 0
#         entry = {"symbol": h["symbol"], "pnlPercentage": round(pnl_pct, 2), "pnl": h.get("pnl", 0)}
#         if not best or pnl_pct > best["pnlPercentage"]:
#             best = entry
#         if not worst or pnl_pct < worst["pnlPercentage"]:
#             worst = entry

#     performance_data.update({"bestPerformer": best, "worstPerformer": worst, "holdingsCount": len(portfolio.get("holdings", []))})
#     return {"success": True, "data": performance_data}
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from typing import List
from bson import ObjectId
import jwt
import os

from app.models.userModel import User
from app.models.portfolioModel import Portfolio

router = APIRouter(tags=["Portfolio"])
JWT_SECRET = os.getenv("JWT_SECRET", "secret")



# ---------- Helper: Convert ObjectId to str recursively ----------
def clean_doc(doc):
    if not doc:
        return doc
    if isinstance(doc, list):
        return [clean_doc(d) for d in doc]
    if isinstance(doc, dict):
        new_doc = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                new_doc[key] = str(value)
            elif isinstance(value, dict) or isinstance(value, list):
                new_doc[key] = clean_doc(value)
            else:
                new_doc[key] = value
        return new_doc
    return doc


# ---------- Authentication Dependency ----------
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


# ---------- Get user portfolio (Summary) ----------
# @router.get("/", summary="Get user portfolio summary")
# async def get_portfolio(user=Depends(authenticate)):
#     portfolio = await Portfolio.find_by_user(user["_id"])
#     portfolio = clean_doc(portfolio)

#     if not portfolio:
#         portfolio_id = await Portfolio.create(str(user["_id"]))
#         portfolio = await Portfolio.find_by_user(user["_id"])
#         portfolio = clean_doc(portfolio)

#     total_invested = sum(h["quantity"] * h["avgPrice"] for h in portfolio.get("holdings", []))
#     total_current = sum(h["quantity"] * (h.get("currentPrice") or h["avgPrice"]) for h in portfolio.get("holdings", []))
#     total_pnl = total_current - total_invested
#     pnl_percentage = (total_pnl / total_invested * 100) if total_invested else 0

#     # Dummy-style enriched response
#     summary = {
#         "total_value": round(total_current, 2),
#         "total_invested": round(total_invested, 2),
#         "total_pnl": round(total_pnl, 2),
#         "total_pnl_percentage": round(pnl_percentage, 2),
#         "available_balance": 15000.75,   # Placeholder / fetch from DB
#         "margin_used": 45000.00,         # Placeholder
#         "margin_available": 55000.00,    # Placeholder
#         "margin_level": 122.22,          # Placeholder
#         "day_pnl": 1250.25,              # Placeholder
#         "day_pnl_percentage": 1.02,      # Placeholder
#         "buying_power": 70000.75         # Placeholder
#     }

#     return {"success": True, "data": summary}
# ---------- Get user portfolio (Summary) ----------
@router.get("/", summary="Get user portfolio summary")
async def get_portfolio(user=Depends(authenticate)):
    # Fetch user data for balances
    user_doc = await User.find_by_id(user["_id"])
    
    # Fetch portfolio from DB
    portfolio = await Portfolio.find_by_user(user["_id"])
    
    # If no portfolio exists, create an empty one
    if not portfolio:
        await Portfolio.create(str(user["_id"]))
        portfolio = await Portfolio.find_by_user(user["_id"])

    portfolio = clean_doc(portfolio)

    # Calculate totals from holdings
    holdings = portfolio.get("holdings", [])
    total_invested = sum(h["quantity"] * h["avgPrice"] for h in holdings)
    total_current = sum(h["quantity"] * (h.get("currentPrice") or h["avgPrice"]) for h in holdings)
    total_pnl = total_current - total_invested
    pnl_percentage = (total_pnl / total_invested * 100) if total_invested else 0

    # Build response matching dummy structure
    summary = {
        "total_value": round(total_current, 2),
        "total_invested": round(total_invested, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_percentage": round(pnl_percentage, 2),
        "available_balance": round(user_doc.get("balance", 15000.75), 2),
        "margin_used": round(user_doc.get("marginUsed", 45000.00), 2),
        "margin_available": round(user_doc.get("marginAvailable", 55000.00), 2),
        "margin_level": 122.22,          # Placeholder, can calculate if needed
        "day_pnl": 1250.25,              # Placeholder, can calculate daily PnL
        "day_pnl_percentage": 1.02,      # Placeholder
        "buying_power": 70000.75         # Placeholder
    }

    return {"success": True, "data": summary}

# ---------- Get portfolio holdings ----------
# @router.get("/holdings", summary="Get portfolio holdings")
# async def get_portfolio_holdings(user=Depends(authenticate)):
#     portfolio = await Portfolio.find_by_user(user["_id"])
#     portfolio = clean_doc(portfolio)

#     if not portfolio:
#         return {"success": True, "data": []}

#     holdings_with_details = []
#     for h in portfolio.get("holdings", []):
#         invested = h["quantity"] * h["avgPrice"]
#         current_value = h["quantity"] * (h.get("currentPrice") or h["avgPrice"])
#         pnl = current_value - invested
#         pnl_percentage = (pnl / invested * 100) if invested else 0

#         holdings_with_details.append({
#             "id": str(h.get("_id", ObjectId())),
#             "symbol": h["symbol"],
#             "exchange": h["exchange"],
#             "quantity": h["quantity"],
#             "avg_price": h["avgPrice"],
#             "current_price": h.get("currentPrice") or h["avgPrice"],
#             "invested_value": round(invested, 2),
#             "current_value": round(current_value, 2),
#             "pnl": round(pnl, 2),
#             "pnl_percentage": round(pnl_percentage, 2),
#             "day_change": 15.25,             # Placeholder
#             "day_change_percentage": 0.54    # Placeholder
#         })

#     return {"success": True, "data": holdings_with_details}
# @router.get("/holdings", summary="Get portfolio holdings")
# async def get_portfolio_holdings(user=Depends(authenticate)):
    # Fetch portfolio
    portfolio = await Portfolio.find_by_user(user["_id"])
    portfolio = clean_doc(portfolio)

    # Auto-create portfolio if missing
    if not portfolio:
        await Portfolio.create(str(user["_id"]), holdings=[])
        portfolio = await Portfolio.find_by_user(user["_id"])
        portfolio = clean_doc(portfolio)

    holdings_with_details = []

    # If there are no holdings, create a placeholder with zero values
    if not portfolio.get("holdings"):
        holdings_with_details.append({
            "id": "holding_000",
            "symbol": "",
            "exchange": "",
            "quantity": 0,
            "avg_price": 0.0,
            "current_price": 0.0,
            "invested_value": 0.0,
            "current_value": 0.0,
            "pnl": 0.0,
            "pnl_percentage": 0.0,
            "day_change": 0.0,
            "day_change_percentage": 0.0
        })
    else:
        # Calculate values for actual holdings
        for h in portfolio.get("holdings", []):
            invested = h["quantity"] * h["avgPrice"]
            current_value = h["quantity"] * (h.get("currentPrice") or h["avgPrice"])
            pnl = current_value - invested
            pnl_percentage = (pnl / invested * 100) if invested else 0

            holdings_with_details.append({
                "id": str(h.get("_id", ObjectId())),
                "symbol": h["symbol"],
                "exchange": h["exchange"],
                "quantity": h["quantity"],
                "avg_price": h["avgPrice"],
                "current_price": h.get("currentPrice") or h["avgPrice"],
                "invested_value": round(invested, 2),
                "current_value": round(current_value, 2),
                "pnl": round(pnl, 2),
                "pnl_percentage": round(pnl_percentage, 2),
                "day_change": h.get("dayChange", 0.0),
                "day_change_percentage": h.get("dayChangePercentage", 0.0)
            })

    return {"success": True, "data": holdings_with_details}


@router.get("/holdings", summary="Get portfolio holdings")
async def get_portfolio_holdings(user=Depends(authenticate)):
    # Fetch portfolio
    portfolio = await Portfolio.find_by_user(user["_id"])
    portfolio = clean_doc(portfolio)

    # Auto-create portfolio if missing
    if not portfolio:
        await Portfolio.create(str(user["_id"]), holdings=[])
        portfolio = await Portfolio.find_by_user(user["_id"])
        portfolio = clean_doc(portfolio)

    holdings_with_details = []

    # If there are no holdings, return dummy structure with zero/placeholder values
    if not portfolio.get("holdings"):
        holdings_with_details = [
            {
                "id": "holding_001",
                "symbol": "RELIANCE",
                "exchange": "NSE",
                "quantity": 0,
                "avg_price": 0.0,
                "current_price": 0.0,
                "invested_value": 0.0,
                "current_value": 0.0,
                "pnl": 0.0,
                "pnl_percentage": 0.0,
                "day_change": 0.0,
                "day_change_percentage": 0.0
            },
            {
                "id": "holding_002",
                "symbol": "TCS",
                "exchange": "NSE",
                "quantity": 0,
                "avg_price": 0.0,
                "current_price": 0.0,
                "invested_value": 0.0,
                "current_value": 0.0,
                "pnl": 0.0,
                "pnl_percentage": 0.0,
                "day_change": 0.0,
                "day_change_percentage": 0.0
            }
        ]
    else:
        # Calculate values for actual holdings
        for h in portfolio.get("holdings", []):
            invested = h["quantity"] * h["avgPrice"]
            current_value = h["quantity"] * (h.get("currentPrice") or h["avgPrice"])
            pnl = current_value - invested
            pnl_percentage = (pnl / invested * 100) if invested else 0

            holdings_with_details.append({
                "id": str(h.get("_id", ObjectId())),
                "symbol": h["symbol"],
                "exchange": h["exchange"],
                "quantity": h["quantity"],
                "avg_price": h["avgPrice"],
                "current_price": h.get("currentPrice") or h["avgPrice"],
                "invested_value": round(invested, 2),
                "current_value": round(current_value, 2),
                "pnl": round(pnl, 2),
                "pnl_percentage": round(pnl_percentage, 2),
                "day_change": h.get("dayChange", 0.0),
                "day_change_percentage": h.get("dayChangePercentage", 0.0)
            })

    return holdings_with_details


# ---------- Update holding prices ----------
@router.put("/update-prices", summary="Update holding prices")
async def update_holding_prices(priceUpdates: List[dict] = Body(...), user=Depends(authenticate)):
    portfolio = await Portfolio.find_by_user(user["_id"])
    portfolio = clean_doc(portfolio)

    if not portfolio or not portfolio.get("holdings"):
        raise HTTPException(status_code=404, detail="Portfolio not found or empty")

    total_pnl = 0
    for h in portfolio.get("holdings", []):
        update = next((p for p in priceUpdates
                       if p.get("symbol", "").upper() == h.get("symbol", "").upper()
                       and p.get("exchange", "").upper() == h.get("exchange", "").upper()), None)
        if update:
            current_price = update.get("currentPrice")
            if current_price is not None:
                h["currentPrice"] = current_price
                quantity = h.get("quantity", 0)
                avg_price = h.get("avgPrice", 0)
                invested = quantity * avg_price
                current_value = quantity * h["currentPrice"]
                h["pnl"] = current_value - invested
                total_pnl += h["pnl"]

    await Portfolio.update_holdings(user["_id"], portfolio.get("holdings", []), total_pnl)

    return {"success": True, "data": {"total_pnl": round(total_pnl, 2)}}


# ---------- Get portfolio performance ----------
@router.get("/performance", summary="Get portfolio performance")
async def get_portfolio_performance(user=Depends(authenticate)):
    portfolio = await Portfolio.find_by_user(user["_id"])
    portfolio = clean_doc(portfolio)

    if not portfolio or not portfolio.get("holdings"):
        return {"success": True, "data": {"daily_pnl": [], "monthly_returns": 0, "yearly_returns": 0, "sharpe_ratio": 0, "max_drawdown": 0}}

    # Example dummy response
    performance_data = {
        "daily_pnl": [
            {"date": "2024-01-01", "pnl": 1250.50, "percentage": 1.2},
            {"date": "2024-01-02", "pnl": -850.25, "percentage": -0.8},
            {"date": "2024-01-03", "pnl": 2100.75, "percentage": 2.1},
        ],
        "monthly_returns": 12.5,
        "yearly_returns": 25.0,
        "sharpe_ratio": 1.85,
        "max_drawdown": 8.5
    }

    return {"success": True, "data": performance_data}