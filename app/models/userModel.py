# from datetime import datetime
# from motor.motor_asyncio import AsyncIOMotorClient
# from app.config import MONGO_URI

# # Initialize MongoDB connection
# client = AsyncIOMotorClient(MONGO_URI)
# db = client.market_data

# class User:
#     collection = db.users

#     @staticmethod
#     async def create(user_data: dict):
#         # Set defaults similar to your Mongoose schema
#         now = datetime.utcnow()
#         user_data.setdefault("balance", 100000)
#         user_data.setdefault("ledgerBalance", 100000)
#         user_data.setdefault("marginUsed", 0)
#         user_data.setdefault("marginAvailable", 100000)
#         user_data.setdefault("profilePic", "")
#         user_data.setdefault("createdAt", now)
#         result = await User.collection.insert_one(user_data)
#         return str(result.inserted_id)

#     @staticmethod
#     async def find_by_email(email: str):
#         return await User.collection.find_one({"email": email.lower()})

#     @staticmethod
#     async def find_by_id(user_id: str):
#         from bson import ObjectId
#         return await User.collection.find_one({"_id": ObjectId(user_id)})

#     @staticmethod
#     async def update_balance(user_id: str, balance: float, ledger_balance: float, margin_used: float, margin_available: float):
#         from bson import ObjectId
#         return await User.collection.update_one(
#             {"_id": ObjectId(user_id)},
#             {
#                 "$set": {
#                     "balance": balance,
#                     "ledgerBalance": ledger_balance,
#                     "marginUsed": margin_used,
#                     "marginAvailable": margin_available
#                 }
#             }
#         )
# from datetime import datetime
# from bson import ObjectId
# from app.database import db

# class User:
#     collection = db.users

#     @staticmethod
#     async def create(user_data: dict):
#         now = datetime.utcnow()
#         user_data.setdefault("balance", 100000)
#         user_data.setdefault("ledgerBalance", 100000)
#         user_data.setdefault("marginUsed", 0)
#         user_data.setdefault("marginAvailable", 100000)
#         user_data.setdefault("profilePic", "")
#         user_data.setdefault("createdAt", now)
#         result = await User.collection.insert_one(user_data)
#         return str(result.inserted_id)

#     @staticmethod
#     async def find_by_email(email: str):
#         return await User.collection.find_one({"email": email.lower()})

#     @staticmethod
#     async def find_by_id(user_id: str):
#         return await User.collection.find_one({"_id": ObjectId(user_id)})

#     @staticmethod
#     async def update_balance(user_id: str, balance: float, ledger_balance: float, margin_used: float, margin_available: float):
#         return await User.collection.update_one(
#             {"_id": ObjectId(user_id)},
#             {"$set": {
#                 "balance": balance,
#                 "ledgerBalance": ledger_balance,
#                 "marginUsed": margin_used,
#                 "marginAvailable": margin_available
#             }}
#         )




from datetime import datetime
from bson import ObjectId
from app.database import db

class User:
    collection = db.users

    @staticmethod
    def serialize(document: dict) -> dict:
        """Convert MongoDB document into JSON-serializable dict"""
        if not document:
            return None
        document["_id"] = str(document["_id"])
        return document

    @staticmethod
    async def create(user_data: dict):
        now = datetime.utcnow()
        user_data.setdefault("balance", 100000)
        user_data.setdefault("ledgerBalance", 100000)
        user_data.setdefault("marginUsed", 0)
        user_data.setdefault("marginAvailable", 100000)
        user_data.setdefault("profilePic", "")
        user_data.setdefault("createdAt", now)
        result = await User.collection.insert_one(user_data)
        return str(result.inserted_id)

    @staticmethod
    async def find_by_email(email: str):
        user = await User.collection.find_one({"email": email.lower()})
        return User.serialize(user)

    @staticmethod
    async def find_by_id(user_id: str):
        user = await User.collection.find_one({"_id": ObjectId(user_id)})
        return User.serialize(user)

    @staticmethod
    async def update_balance(user_id: str, balance: float = 0, ledger_balance: float = 0, margin_used: float = 0, margin_available: float = 0):
        """
        ✅ FIXED: Use $inc to increment/decrement values instead of overwriting
        """
        update_data = {"$inc": {}}
        
        if balance != 0:
            update_data["$inc"]["balance"] = balance
        if ledger_balance != 0:
            update_data["$inc"]["ledgerBalance"] = ledger_balance
        if margin_used != 0:
            update_data["$inc"]["marginUsed"] = margin_used
        if margin_available != 0:
            update_data["$inc"]["marginAvailable"] = margin_available
        
        # Only update if there are changes
        if update_data["$inc"]:
            result = await User.collection.update_one(
                {"_id": ObjectId(user_id)},
                update_data
            )
            return result.modified_count > 0
        return True