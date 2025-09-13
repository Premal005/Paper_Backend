# from datetime import datetime
# from bson import ObjectId
# from motor.motor_asyncio import AsyncIOMotorClient
# from app.config import MONGO_URI

# # Initialize MongoDB connection
# client = AsyncIOMotorClient(MONGO_URI)
# db = client.market_data

# class WithdrawalRequest:
#     collection = db.withdrawal_requests

#     @staticmethod
#     async def create(user_id: str, amount: float, status: str = "pending"):
#         request_data = {
#             "userId": ObjectId(user_id),
#             "amount": amount,
#             "status": status,              # "pending" | "processed" | "rejected"
#             "requestedAt": datetime.utcnow(),
#             "processedAt": None,
#         }
#         result = await WithdrawalRequest.collection.insert_one(request_data)
#         return str(result.inserted_id)

#     @staticmethod
#     async def find_by_user(user_id: str):
#         cursor = WithdrawalRequest.collection.find({"userId": ObjectId(user_id)})
#         return await cursor.to_list(length=None)

#     @staticmethod
#     async def update_status(request_id: str, status: str):
#         update_data = {"status": status}
#         if status == "processed":
#             update_data["processedAt"] = datetime.utcnow()

#         return await WithdrawalRequest.collection.update_one(
#             {"_id": ObjectId(request_id)},
#             {"$set": update_data}
#         )
from bson import ObjectId
from datetime import datetime
from app.database import db

class WithdrawalRequest:
    collection = db.withdrawal_requests

    @staticmethod
    async def create(user_id: str, amount: float, status: str = "pending"):
        request_data = {
            "userId": ObjectId(user_id),
            "amount": amount,
            "status": status,
            "requestedAt": datetime.utcnow(),
            "processedAt": None
        }
        result = await WithdrawalRequest.collection.insert_one(request_data)
        return str(result.inserted_id)

    @staticmethod
    async def find_by_user(user_id: str):
        cursor = WithdrawalRequest.collection.find({"userId": ObjectId(user_id)})
        return await cursor.to_list(length=None)

    @staticmethod
    async def update_status(request_id: str, status: str):
        update_data = {"status": status}
        if status == "processed":
            update_data["processedAt"] = datetime.utcnow()

        return await WithdrawalRequest.collection.update_one(
            {"_id": ObjectId(request_id)},
            {"$set": update_data}
        )
