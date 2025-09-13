# from fastapi import APIRouter, Query, HTTPException
# from typing import List, Optional

# from app.models.marketModel import MarketData

# router = APIRouter( tags=["Market"])

# # ---------- Search by symbol or partial name ----------
# @router.get("/search")
# async def search_market(query: Optional[str] = Query("", alias="query"), limit: int = Query(50)):
#     try:
#         cursor = MarketData.collection.find({
#             "symbol": {"$regex": query, "$options": "i"}
#         }).limit(limit)
#         results = await cursor.to_list(length=limit)
#         return results
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# # ---------- Get by category / tab: Futures | Options | Forex | Crypto ----------
# @router.get("/category/{type}")
# async def get_market_by_category(type: str):
#     allowed = ["Futures", "Options", "Forex", "Crypto"]
#     if type not in allowed:
#         raise HTTPException(status_code=400, detail="Invalid type")

#     try:
#         cursor = MarketData.collection.find({"instrumentType": type}).limit(200)
#         results = await cursor.to_list(length=200)
#         return results
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# # ---------- Get single symbol latest ----------
# @router.get("/{exchange}/{symbol}")
# async def get_single_market(exchange: str, symbol: str):
#     try:
#         item = await MarketData.collection.find_one({"exchange": exchange.upper(), "symbol": symbol})
#         if not item:
#             raise HTTPException(status_code=404, detail="Not found")
#         return item
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from bson import ObjectId

from app.models.marketModel import MarketData

router = APIRouter(tags=["Market"])


# -------- Helper to fix Mongo ObjectId --------
def clean_doc(doc: dict) -> dict:
    """Convert ObjectId to str so FastAPI can serialize it"""
    if not doc:
        return doc
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])
    return doc


# ---------- Search by symbol or partial name ----------
@router.get("/search")
async def search_market(query: Optional[str] = Query("", alias="query"), limit: int = Query(50)):
    try:
        cursor = MarketData.collection.find({
            "symbol": {"$regex": query, "$options": "i"}
        }).limit(limit)
        results = await cursor.to_list(length=limit)
        return [clean_doc(doc) for doc in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Get by category / tab: Futures | Options | Forex | Crypto ----------
# ---------- Get by category / tab: Futures | Options | Forex | Crypto ----------
@router.get("/category/{type}")
async def get_market_by_category(type: str):
    # Normalize input: strip spaces and uppercase
    type_normalized = type.strip().upper()
    
    # Allowed types in uppercase
    allowed = ["FUTURES", "OPTIONS", "FOREX", "CRYPTO"]
    if type_normalized not in allowed:
        raise HTTPException(status_code=400, detail="Invalid type")

    try:
        # Case-insensitive regex match to avoid DB case issues
        cursor = MarketData.collection.find({
            "exchange": {"$regex": f"^{type_normalized}$", "$options": "i"}
        }).limit(200)
        results = await cursor.to_list(length=200)
        return [clean_doc(doc) for doc in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Get single symbol latest ----------
@router.get("/{exchange}/{symbol}")
async def get_single_market(exchange: str, symbol: str):
    try:
        # Normalize input
        exchange = exchange.strip()
        symbol = symbol.strip()

        # Case-insensitive search using regex
        item = await MarketData.collection.find_one({
            "exchange": {"$regex": f"^{exchange}$", "$options": "i"},
            "symbol": {"$regex": f"^{symbol}$", "$options": "i"}
        })

        if not item:
            raise HTTPException(status_code=404, detail="Not found")

        return clean_doc(item)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

