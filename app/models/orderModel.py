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









# from datetime import datetime
# from bson import ObjectId
# from app.database import db

# class Order:
#     collection = db.orders

#     @staticmethod
#     async def create(order_data: dict):
#         """
#         Insert order into DB. 'status' is taken from order_data.
#         """
#         now = datetime.utcnow()
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
# import asyncio

# class Order:
#     collection = db.orders

#     @staticmethod
#     async def create(order_data: dict):
#         """
#         Insert order into DB with ALL fields properly saved.
#         """
#         now = datetime.utcnow()
#         order_data["createdAt"] = now
#         order_data["updatedAt"] = now
        
#         # Ensure all fields have proper defaults
#         defaults = {
#             "status": "pending",
#             "orderType": "market",
#             "executedPrice": None,
#             "triggerPrice": None,
#             "condition": None,
#             "isCloseOrder": False,
#             "currentMarketPrice": None,
#             "executedAt": None
#         }
        
#         for key, default in defaults.items():
#             if key not in order_data:
#                 order_data[key] = default
                
#         # Set status based on order type
#         if order_data.get("orderType") == "limit":
#             order_data["status"] = "pending"
#         else:
#             order_data["status"] = "active"
            
#         result = await Order.collection.insert_one(order_data)
#         return str(result.inserted_id)

#     @staticmethod
#     async def find_by_user(user_id: str):
#         cursor = Order.collection.find({"userId": ObjectId(user_id)}).sort("createdAt", -1)
#         return await cursor.to_list(length=None)

#     @staticmethod
#     async def find_pending_orders():
#         """Find all pending orders across all users"""
#         cursor = Order.collection.find({"status": "pending"})
#         return await cursor.to_list(length=None)

#     @staticmethod
#     async def update_status(order_id: str, status: str, executed_price: float = None):
#         update_data = {
#             "status": status, 
#             "updatedAt": datetime.utcnow()
#         }
#         if executed_price is not None:
#             update_data["executedPrice"] = executed_price
#             update_data["executedAt"] = datetime.utcnow()
            
#         return await Order.collection.update_one(
#             {"_id": ObjectId(order_id)},
#             {"$set": update_data}
#         )

#     @staticmethod
#     async def update_order(order_id: str, update_data: dict):
#         update_data["updatedAt"] = datetime.utcnow()
#         return await Order.collection.update_one(
#             {"_id": ObjectId(order_id)},
#             {"$set": update_data}
#         )

#     @staticmethod
#     async def get_by_id(order_id: str):
#         """Get single order by ID"""
#         return await Order.collection.find_one({"_id": ObjectId(order_id)})

#     @staticmethod
#     async def cancel_order(order_id: str):
#         """Cancel an order"""
#         return await Order.collection.update_one(
#             {"_id": ObjectId(order_id)},
#             {"$set": {
#                 "status": "cancelled",
#                 "updatedAt": datetime.utcnow()
#             }}
#         )


from datetime import datetime
from bson import ObjectId
from app.database import db
import asyncio

class Order:
    collection = db.orders

    @staticmethod
    async def create(order_data: dict):
        """
        Insert order into DB with ALL fields properly saved.
        """
        now = datetime.utcnow()
        order_data["createdAt"] = now
        order_data["updatedAt"] = now
        
        # Ensure all fields have proper defaults
        defaults = {
            "status": "pending",
            "orderType": "market",
            "executedPrice": None,
            "triggerPrice": None,
            "condition": None,
            "isCloseOrder": False,
            "currentMarketPrice": None,
            "executedAt": None,
            "leverage": 20,
            "marginUsed": 0,
            "pnl": 0,
            "isClosed": False,
            "closedAt": None
        }
        
        for key, default in defaults.items():
            if key not in order_data:
                order_data[key] = default
                
        # Set status based on order type
        if order_data.get("orderType") == "limit":
            order_data["status"] = "pending"
        else:
            order_data["status"] = "active"
            
        result = await Order.collection.insert_one(order_data)
        return str(result.inserted_id)

    @staticmethod
    async def create_with_pnl(order_data: dict):
        """Create order with PnL tracking"""
        now = datetime.utcnow()
        order_data["createdAt"] = now
        order_data["updatedAt"] = now
        
        # PnL tracking fields
        order_data.setdefault("leverage", 20)
        order_data.setdefault("marginUsed", 0)
        order_data.setdefault("pnl", 0)
        order_data.setdefault("isClosed", False)
        order_data.setdefault("closedAt", None)
        
        result = await Order.collection.insert_one(order_data)
        return str(result.inserted_id)

    @staticmethod
    async def find_by_user(user_id: str):
        cursor = Order.collection.find({"userId": ObjectId(user_id)}).sort("createdAt", -1)
        return await cursor.to_list(length=None)

    @staticmethod
    async def find_pending_orders():
        """Find all pending orders across all users"""
        cursor = Order.collection.find({"status": "pending"})
        return await cursor.to_list(length=None)

    @staticmethod
    async def update_status(order_id: str, status: str, executed_price: float = None):
        update_data = {
            "status": status, 
            "updatedAt": datetime.utcnow()
        }
        if executed_price is not None:
            update_data["executedPrice"] = executed_price
            update_data["executedAt"] = datetime.utcnow()
            
        return await Order.collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": update_data}
        )

    @staticmethod
    async def update_order(order_id: str, update_data: dict):
        update_data["updatedAt"] = datetime.utcnow()
        return await Order.collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": update_data}
        )

    @staticmethod
    async def update_pnl(order_id: str, pnl: float, current_price: float = None):
        """Update PnL for an order"""
        update_data = {
            "pnl": pnl,
            "updatedAt": datetime.utcnow()
        }
        if current_price is not None:
            update_data["currentPrice"] = current_price
            
        return await Order.collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": update_data}
        )

    @staticmethod
    async def close_order(order_id: str, pnl: float = 0):
        """Mark order as closed and record PnL"""
        return await Order.collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {
                "isClosed": True,
                "pnl": pnl,
                "closedAt": datetime.utcnow(),
                "status": "closed",
                "updatedAt": datetime.utcnow()
            }}
        )

    @staticmethod
    async def get_by_id(order_id: str):
        """Get single order by ID"""
        return await Order.collection.find_one({"_id": ObjectId(order_id)})

    @staticmethod
    async def cancel_order(order_id: str):
        """Cancel an order"""
        return await Order.collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {
                "status": "cancelled",
                "updatedAt": datetime.utcnow()
            }}
        )

    @staticmethod
    async def get_active_trades(user_id: str):
        """Get all active trades for a user"""
        cursor = Order.collection.find({
            "userId": ObjectId(user_id),
            "isClosed": False,
            "status": "active"
        })
        return await cursor.to_list(length=None)

    @staticmethod
    async def get_today_pnl(user_id: str):
        """Calculate today's PnL for a user"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        pipeline = [
            {
                "$match": {
                    "userId": ObjectId(user_id),
                    "closedAt": {"$gte": today},
                    "isClosed": True
                }
            },
            {
                "$group": {
                    "_id": None,
                    "todayPnl": {"$sum": "$pnl"}
                }
            }
        ]
        
        cursor = Order.collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        return result[0]["todayPnl"] if result else 0