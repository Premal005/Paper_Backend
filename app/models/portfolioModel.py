# from bson import ObjectId
# from motor.motor_asyncio import AsyncIOMotorClient
# from app.config import MONGO_URI

# # Initialize MongoDB connection
# client = AsyncIOMotorClient(MONGO_URI)
# db = client.market_data

# class Portfolio:
#     collection = db.portfolios

#     @staticmethod
#     async def create(user_id: str, holdings: list = None):
#         portfolio_data = {
#             "userId": ObjectId(user_id),
#             "holdings": holdings or [],
#             "totalPnl": 0,
#         }
#         result = await Portfolio.collection.insert_one(portfolio_data)
#         return str(result.inserted_id)

#     @staticmethod
#     async def find_by_user(user_id: str):
#         return await Portfolio.collection.find_one({"userId": ObjectId(user_id)})

#     @staticmethod
#     async def update_holdings(user_id: str, holdings: list, total_pnl: float = 0):
#         return await Portfolio.collection.update_one(
#             {"userId": ObjectId(user_id)},
#             {"$set": {"holdings": holdings, "totalPnl": total_pnl}},
#             upsert=True
#         )
from bson import ObjectId
from app.database import db

class Portfolio:
    collection = db.portfolios

    @staticmethod
    async def create(user_id: str, holdings: list = None):
        portfolio_data = {
            "userId": ObjectId(user_id),
            "holdings": holdings or [],
            "totalPnl": 0
        }
        result = await Portfolio.collection.insert_one(portfolio_data)
        return str(result.inserted_id)

    @staticmethod
    async def find_by_user(user_id: str):
        return await Portfolio.collection.find_one({"userId": ObjectId(user_id)})

    @staticmethod
    async def update_holdings(user_id: str, holdings: list, total_pnl: float = 0):
        return await Portfolio.collection.update_one(
            {"userId": ObjectId(user_id)},
            {"$set": {"holdings": holdings, "totalPnl": total_pnl}},
            upsert=True
        )
