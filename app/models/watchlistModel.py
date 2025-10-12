
from bson import ObjectId
from app.database import db

class Watchlist:
    collection = db.watchlists

    @staticmethod
    async def create(user_id: str, symbols: list):
        watchlist_data = {
            "userId": ObjectId(user_id),
            "symbols": symbols  # list of {"symbol": str, "exchange": str}
        }
        result = await Watchlist.collection.insert_one(watchlist_data)
        return str(result.inserted_id)

    @staticmethod
    async def find_by_user(user_id: str):
        return await Watchlist.collection.find_one({"userId": ObjectId(user_id)})

    @staticmethod
    async def update_symbols(user_id: str, symbols: list):
        return await Watchlist.collection.update_one(
            {"userId": ObjectId(user_id)},
            {"$set": {"symbols": symbols}},
            upsert=True
        )
    




    @staticmethod
    async def get_all():
        cursor = Watchlist.collection.find({})
        return [doc async for doc in cursor]


