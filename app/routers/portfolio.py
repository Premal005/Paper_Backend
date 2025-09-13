# from fastapi import APIRouter, Depends, HTTPException, Body
# from typing import List, Optional
# from bson import ObjectId
# from datetime import datetime
# import jwt
# import os

# from app.models.userModel import User
# from app.models.portfolioModel import Portfolio

# router = APIRouter(tags=["Portfolio"])

# JWT_SECRET = os.getenv("JWT_SECRET", "secret")


# # ---------- Authentication Dependency ----------
# async def authenticate(token: str = Depends(lambda: None)):
#     """
#     Dummy Depends to extract token from Authorization header
#     FastAPI recommends OAuth2PasswordBearer, but we mimic Express JWT flow.
#     """
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


# # ---------- Routes ----------
# @router.get("/", summary="Get user portfolio")
# async def get_portfolio(user=Depends(authenticate)):
#     portfolio = await Portfolio.find_by_user(user["_id"])
#     if not portfolio:
#         # Create empty portfolio if it doesn't exist
#         portfolio_id = await Portfolio.create(str(user["_id"]))
#         portfolio = await Portfolio.find_by_user(user["_id"])
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


# @router.get("/holdings", summary="Get portfolio holdings")
# async def get_portfolio_holdings(user=Depends(authenticate)):
#     portfolio = await Portfolio.find_by_user(user["_id"])
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


# @router.put("/update-prices", summary="Update holding prices")
# async def update_holding_prices(priceUpdates: List[dict] = Body(...), user=Depends(authenticate)):
#     portfolio = await Portfolio.find_by_user(user["_id"])
#     if not portfolio:
#         raise HTTPException(status_code=404, detail="Portfolio not found")

#     total_pnl = 0
#     for h in portfolio.get("holdings", []):
#         update = next((p for p in priceUpdates if p["symbol"] == h["symbol"] and p["exchange"] == h["exchange"]), None)
#         if update:
#             h["currentPrice"] = update["currentPrice"]
#             invested = h["quantity"] * h["avgPrice"]
#             current_value = h["quantity"] * h["currentPrice"]
#             h["pnl"] = current_value - invested
#             total_pnl += h["pnl"]

#     await Portfolio.update_holdings(user["_id"], portfolio.get("holdings", []), total_pnl)

#     return {"success": True, "message": "Prices updated successfully", "data": {"totalPnl": round(total_pnl, 2)}}


# @router.get("/performance", summary="Get portfolio performance")
# async def get_portfolio_performance(user=Depends(authenticate)):
#     portfolio = await Portfolio.find_by_user(user["_id"])
#     if not portfolio or not portfolio.get("holdings"):
#         return {"success": True, "data": {"dailyPnl": 0, "weeklyPnl": 0, "monthlyPnl": 0, "totalPnl": 0, "bestPerformer": None, "worstPerformer": None}}

#     performance_data = {
#         "dailyPnl": round((0.5 - 0.5) * 2000, 2),  # Mocked
#         "weeklyPnl": round((0.5 - 0.5) * 5000, 2),
#         "monthlyPnl": round((0.5 - 0.5) * 15000, 2),
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
from datetime import datetime
import jwt
import os

from app.models.userModel import User
from app.models.portfolioModel import Portfolio

router = APIRouter(tags=["Portfolio"])

JWT_SECRET = os.getenv("JWT_SECRET", "secret")


# ---------- Helper: Convert ObjectId to str recursively ----------
def clean_doc(doc):
    """Convert ObjectId to string for JSON serialization recursively"""
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


# ---------- Get user portfolio ----------
@router.get("/", summary="Get user portfolio")
async def get_portfolio(user=Depends(authenticate)):
    portfolio = await Portfolio.find_by_user(user["_id"])
    portfolio = clean_doc(portfolio)

    if not portfolio:
        portfolio_id = await Portfolio.create(str(user["_id"]))
        portfolio = await Portfolio.find_by_user(user["_id"])
        portfolio = clean_doc(portfolio)
        summary = {"totalValue": 0, "totalInvested": 0, "totalPnl": 0, "pnlPercentage": 0}
    else:
        total_invested = sum(h["quantity"] * h["avgPrice"] for h in portfolio.get("holdings", []))
        total_current = sum(h["quantity"] * (h.get("currentPrice") or h["avgPrice"]) for h in portfolio.get("holdings", []))
        total_pnl = total_current - total_invested
        pnl_percentage = (total_pnl / total_invested * 100) if total_invested else 0
        summary = {
            "totalValue": round(total_current, 2),
            "totalInvested": round(total_invested, 2),
            "totalPnl": round(total_pnl, 2),
            "pnlPercentage": round(pnl_percentage, 2)
        }

    return {"success": True, "data": {"portfolio": portfolio, "summary": summary}}


# ---------- Get portfolio holdings ----------
@router.get("/holdings", summary="Get portfolio holdings")
async def get_portfolio_holdings(user=Depends(authenticate)):
    portfolio = await Portfolio.find_by_user(user["_id"])
    portfolio = clean_doc(portfolio)

    if not portfolio:
        return {"success": True, "data": {"holdings": [], "totalHoldings": 0}}

    holdings_with_details = []
    for h in portfolio.get("holdings", []):
        invested = h["quantity"] * h["avgPrice"]
        current_value = h["quantity"] * (h.get("currentPrice") or h["avgPrice"])
        pnl = current_value - invested
        pnl_percentage = (pnl / invested * 100) if invested else 0
        h_detail = h.copy()
        h_detail.update({
            "invested": round(invested, 2),
            "currentValue": round(current_value, 2),
            "pnl": round(pnl, 2),
            "pnlPercentage": round(pnl_percentage, 2)
        })
        holdings_with_details.append(h_detail)

    return {"success": True, "data": {"holdings": holdings_with_details, "totalHoldings": len(holdings_with_details)}}


# ---------- Update holding prices ----------
# ---------- Update holding prices ----------
@router.put("/update-prices", summary="Update holding prices")
async def update_holding_prices(priceUpdates: List[dict] = Body(...), user=Depends(authenticate)):
    portfolio = await Portfolio.find_by_user(user["_id"])
    portfolio = clean_doc(portfolio)

    if not portfolio or not portfolio.get("holdings"):
        raise HTTPException(status_code=404, detail="Portfolio not found or empty")

    total_pnl = 0
    for h in portfolio.get("holdings", []):
        # Case-insensitive matching for symbol and exchange
        update = next((p for p in priceUpdates
                       if p.get("symbol", "").upper() == h.get("symbol", "").upper()
                       and p.get("exchange", "").upper() == h.get("exchange", "").upper()), None)
        if update:
            # Only update if currentPrice is provided
            current_price = update.get("currentPrice")
            if current_price is not None:
                h["currentPrice"] = current_price

                quantity = h.get("quantity", 0)
                avg_price = h.get("avgPrice", 0)

                invested = quantity * avg_price
                current_value = quantity * h["currentPrice"]
                h["pnl"] = current_value - invested
                total_pnl += h["pnl"]

    # Save updated holdings back to DB
    await Portfolio.update_holdings(user["_id"], portfolio.get("holdings", []), total_pnl)

    return {
        "success": True,
        "message": "Prices updated successfully",
        "data": {
            "totalPnl": round(total_pnl, 2)
        }
    }


# ---------- Get portfolio performance ----------
@router.get("/performance", summary="Get portfolio performance")
async def get_portfolio_performance(user=Depends(authenticate)):
    portfolio = await Portfolio.find_by_user(user["_id"])
    portfolio = clean_doc(portfolio)

    if not portfolio or not portfolio.get("holdings"):
        return {"success": True, "data": {"dailyPnl": 0, "weeklyPnl": 0, "monthlyPnl": 0, "totalPnl": 0, "bestPerformer": None, "worstPerformer": None}}

    performance_data = {
        "dailyPnl": 0,  # Replace with actual calculation
        "weeklyPnl": 0,
        "monthlyPnl": 0,
        "totalPnl": portfolio.get("totalPnl", 0)
    }

    best = None
    worst = None
    for h in portfolio.get("holdings", []):
        pnl_pct = ((h.get("currentPrice") or h["avgPrice"]) - h["avgPrice"]) / h["avgPrice"] * 100 if h["avgPrice"] else 0
        entry = {"symbol": h["symbol"], "pnlPercentage": round(pnl_pct, 2), "pnl": h.get("pnl", 0)}
        if not best or pnl_pct > best["pnlPercentage"]:
            best = entry
        if not worst or pnl_pct < worst["pnlPercentage"]:
            worst = entry

    performance_data.update({"bestPerformer": best, "worstPerformer": worst, "holdingsCount": len(portfolio.get("holdings", []))})
    return {"success": True, "data": performance_data}
