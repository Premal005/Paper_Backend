# from datetime import datetime
# from bson import ObjectId
# from motor.motor_asyncio import AsyncIOMotorClient
# from app.config import MONGO_URI

# # Initialize MongoDB connection
# client = AsyncIOMotorClient(MONGO_URI)
# db = client.market_data

# class Transaction:
#     collection = db.transactions

#     @staticmethod
#     async def create(user_id: str, txn_type: str, amount: float, status: str = "pending"):
#         txn_data = {
#             "userId": ObjectId(user_id),
#             "type": txn_type,          # "deposit" or "withdraw"
#             "amount": amount,
#             "status": status,          # defaults to "pending"
#             "createdAt": datetime.utcnow(),
#         }
#         result = await Transaction.collection.insert_one(txn_data)
#         return str(result.inserted_id)

#     @staticmethod
#     async def find_by_user(user_id: str):
#         cursor = Transaction.collection.find({"userId": ObjectId(user_id)})
#         return await cursor.to_list(length=None)

#     @staticmethod
#     async def update_status(transaction_id: str, status: str):
#         return await Transaction.collection.update_one(
#             {"_id": ObjectId(transaction_id)},
#             {"$set": {"status": status}}
#         )





# from bson import ObjectId
# from datetime import datetime
# from app.database import db

# class Transaction:
#     collection = db.transactions

#     @staticmethod
#     async def create(user_id: str, txn_type: str, amount: float, status: str = "pending"):
#         txn_data = {
#             "userId": ObjectId(user_id),
#             "type": txn_type,
#             "amount": amount,
#             "status": status,
#             "createdAt": datetime.utcnow()
#         }
#         result = await Transaction.collection.insert_one(txn_data)
#         return str(result.inserted_id)

#     @staticmethod
#     async def find_by_user(user_id: str):
#         cursor = Transaction.collection.find({"userId": ObjectId(user_id)})
#         return await cursor.to_list(length=None)

#     @staticmethod
#     async def update_status(transaction_id: str, status: str):
#         return await Transaction.collection.update_one(
#             {"_id": ObjectId(transaction_id)},
#             {"$set": {"status": status}}
#         )




from bson import ObjectId
from datetime import datetime
from app.database import db

class Transaction:
    collection = db.transactions

    @staticmethod
    async def create(user_id: str, txn_type: str, amount: float, status: str = "pending"):
        txn_data = {
            "userId": ObjectId(user_id),
            "type": txn_type,
            "amount": amount,
            "status": status,
            "createdAt": datetime.utcnow()
        }
        result = await Transaction.collection.insert_one(txn_data)
        return str(result.inserted_id)

    @staticmethod
    async def find_by_user(user_id: str):
        cursor = Transaction.collection.find({"userId": ObjectId(user_id)})
        return await cursor.to_list(length=None)

    @staticmethod
    async def update_status(transaction_id: str, status: str):
        return await Transaction.collection.update_one(
            {"_id": ObjectId(transaction_id)},
            {"$set": {"status": status}}
        )