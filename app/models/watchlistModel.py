
# from bson import ObjectId
# from app.database import db


# class Watchlist:
#     collection = db.watchlists

#     @staticmethod
#     async def create(user_id: str, symbols: list):
#         watchlist_data = {
#             "userId": ObjectId(user_id),
#             "symbols": symbols  # list of {"symbol": str, "exchange": str}
#         }
#         result = await Watchlist.collection.insert_one(watchlist_data)
#         return str(result.inserted_id)

#     @staticmethod
#     async def find_by_user(user_id: str):
#         return await Watchlist.collection.find_one({"userId": ObjectId(user_id)})

#     @staticmethod
#     async def update_symbols(user_id: str, symbols: list):
#         return await Watchlist.collection.update_one(
#             {"userId": ObjectId(user_id)},
#             {"$set": {"symbols": symbols}},
#             upsert=True
#         )
    




#     @staticmethod
#     async def get_all():
#         cursor = Watchlist.collection.find({})
#         return [doc async for doc in cursor]








# from bson import ObjectId
# from datetime import datetime
# from app.database import db


# class Watchlist:
#     collection = db.watchlists

#     @staticmethod
#     async def create(user_id: str, symbols: list):
#         watchlist_data = {
#             "userId": ObjectId(user_id),
#             "symbols": symbols,
#             "last_updated": datetime.utcnow()
#         }
#         result = await Watchlist.collection.insert_one(watchlist_data)
#         return str(result.inserted_id)

#     @staticmethod
#     async def find_by_user(user_id: str):
#         return await Watchlist.collection.find_one({"userId": ObjectId(user_id)})

#     @staticmethod
#     async def update_symbols(user_id: str, symbols: list):
#         """Update the entire symbols array"""
#         return await Watchlist.collection.update_one(
#             {"userId": ObjectId(user_id)},
#             {"$set": {
#                 "symbols": symbols,
#                 "last_updated": datetime.utcnow()
#             }},
#             upsert=True
#         )
    
#     @staticmethod
#     async def update_symbol_data(user_id: str, symbol: str, exchange: str, update_data: dict):
#         """Update specific symbol data without replacing entire array"""
#         return await Watchlist.collection.update_one(
#             {
#                 "userId": ObjectId(user_id),
#                 "symbols": {
#                     "$elemMatch": {
#                         "symbol": symbol.upper(),
#                         "exchange": exchange.upper()
#                     }
#                 }
#             },
#             {
#                 "$set": {
#                     "symbols.$.current_price": update_data.get("current_price", 0),
#                     "symbols.$.day_change": update_data.get("day_change", 0),
#                     "symbols.$.day_change_percentage": update_data.get("day_change_percentage", 0),
#                     "symbols.$.last_updated": update_data.get("last_updated"),
#                     "last_updated": datetime.utcnow()
#                 }
#             }
#         )

#     @staticmethod
#     async def get_all():
#         cursor = Watchlist.collection.find({})
#         return [doc async for doc in cursor]



from bson import ObjectId
from datetime import datetime
from app.database import db

class Watchlist:
    collection = db.watchlists

    @staticmethod
    async def create(user_id: str, symbols: list):
        watchlist_data = {
            "userId": ObjectId(user_id),
            "symbols": symbols,
            "last_updated": datetime.utcnow()
        }
        result = await Watchlist.collection.insert_one(watchlist_data)
        return str(result.inserted_id)

    @staticmethod
    async def find_by_user(user_id: str):
        return await Watchlist.collection.find_one({"userId": ObjectId(user_id)})

    @staticmethod
    async def update_symbols(user_id: str, symbols: list):
        """Update the entire symbols array"""
        return await Watchlist.collection.update_one(
            {"userId": ObjectId(user_id)},
            {"$set": {
                "symbols": symbols,
                "last_updated": datetime.utcnow()
            }},
            upsert=True
        )
    
    @staticmethod
    async def update_symbol_data(user_id: str, symbol: str, exchange: str, update_data: dict):
        """Update specific symbol data without replacing entire array"""
        return await Watchlist.collection.update_one(
            {
                "userId": ObjectId(user_id),
                "symbols": {
                    "$elemMatch": {
                        "symbol": symbol.upper(),
                        "exchange": exchange.upper()
                    }
                }
            },
            {
                "$set": {
                    "symbols.$.current_price": update_data.get("current_price", 0),
                    "symbols.$.day_change": update_data.get("day_change", 0),
                    "symbols.$.day_change_percentage": update_data.get("day_change_percentage", 0),
                    "symbols.$.last_updated": update_data.get("last_updated"),
                    "last_updated": datetime.utcnow()
                }
            }
        )

    @staticmethod
    async def update_single_symbol_data(user_id: str, symbol: str, exchange: str, update_data: dict):
        """Update only specific symbol data - much more efficient"""
        return await Watchlist.collection.update_one(
            {
                "userId": ObjectId(user_id),
                "symbols.symbol": symbol.upper(),
                "symbols.exchange": exchange.upper()
            },
            {
                "$set": {
                    "symbols.$.current_price": update_data.get("current_price"),
                    "symbols.$.day_change": update_data.get("day_change"),
                    "symbols.$.day_change_percentage": update_data.get("day_change_percentage"),
                    "symbols.$.last_updated": update_data.get("last_updated"),
                    "last_updated": datetime.utcnow()
                }
            }
        )
    
    @staticmethod
    async def get_all_symbols_to_track():
        """Get all unique symbols across all watchlists for efficient tracking"""
        pipeline = [
            {"$unwind": "$symbols"},
            {"$group": {
                "_id": {
                    "symbol": "$symbols.symbol",
                    "exchange": "$symbols.exchange"
                },
                "user_ids": {"$addToSet": "$userId"}
            }},
            {"$project": {
                "symbol": "$_id.symbol",
                "exchange": "$_id.exchange", 
                "user_ids": 1,
                "_id": 0
            }}
        ]
        cursor = Watchlist.collection.aggregate(pipeline)
        return [doc async for doc in cursor]

    @staticmethod
    async def get_watchlists_by_symbol(symbol: str, exchange: str):
        """Get all watchlists containing a specific symbol"""
        cursor = Watchlist.collection.find({
            "symbols": {
                "$elemMatch": {
                    "symbol": symbol.upper(),
                    "exchange": exchange.upper()
                }
            }
        })
        return [doc async for doc in cursor]

    @staticmethod
    async def get_all():
        cursor = Watchlist.collection.find({})
        return [doc async for doc in cursor]