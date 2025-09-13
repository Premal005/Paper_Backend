# from datetime import datetime
# from bson import ObjectId
# from motor.motor_asyncio import AsyncIOMotorClient
# from app.config import MONGO_URI

# # Initialize MongoDB connection
# client = AsyncIOMotorClient(MONGO_URI)
# db = client.market_data

# class Order:
#     collection = db.orders

#     @staticmethod
#     async def create(order_data: dict):
#         # Add timestamps
#         now = datetime.utcnow()
#         order_data.setdefault("status", "pending")
#         order_data["createdAt"] = now
#         order_data["updatedAt"] = now
#         result = await Order.collection.insert_one(order_data)
#         return str(result.inserted_id)

#     @staticmethod
#     async def find_by_user(user_id: str):
#         cursor = Order.collection.find({"userId": ObjectId(user_id)})
#         return await cursor.to_list(length=None)

#     @staticmethod
#     async def update_status(order_id: str, status: str):
#         return await Order.collection.update_one(
#             {"_id": ObjectId(order_id)},
#             {"$set": {"status": status, "updatedAt": datetime.utcnow()}}
#         )







# from datetime import datetime
# from bson import ObjectId
# from app.database import db

# class Order:
#     collection = db.orders

#     @staticmethod
#     async def create(order_data: dict):
#         now = datetime.utcnow()
#         order_data.setdefault("status", "pending")
#         order_data["createdAt"] = now
#         order_data["updatedAt"] = now
#         result = await Order.collection.insert_one(order_data)
#         return str(result.inserted_id)

#     @staticmethod
#     async def find_by_user(user_id: str):
#         cursor = Order.collection.find({"userId": ObjectId(user_id)})
#         return await cursor.to_list(length=None)

#     @staticmethod
#     async def update_status(order_id: str, status: str):
#         return await Order.collection.update_one(
#             {"_id": ObjectId(order_id)},
#             {"$set": {"status": status, "updatedAt": datetime.utcnow()}}
#         )






from datetime import datetime
from bson import ObjectId
from app.database import db

class Order:
    collection = db.orders

    @staticmethod
    async def create(order_data: dict):
        """
        Insert order into DB. 'status' is taken from order_data.
        """
        now = datetime.utcnow()
        order_data["createdAt"] = now
        order_data["updatedAt"] = now
        result = await Order.collection.insert_one(order_data)
        return str(result.inserted_id)

    @staticmethod
    async def find_by_user(user_id: str):
        cursor = Order.collection.find({"userId": ObjectId(user_id)})
        return await cursor.to_list(length=None)

    @staticmethod
    async def update_status(order_id: str, status: str):
        return await Order.collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": status, "updatedAt": datetime.utcnow()}}
        )
