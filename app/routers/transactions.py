# # # app/routes/transactions.py
# # from fastapi import APIRouter, Depends, HTTPException, Query, status
# # from fastapi.encoders import jsonable_encoder
# # from pydantic import BaseModel, Field
# # from typing import Optional, List
# # from datetime import datetime
# # from bson import ObjectId

# # from app.database import db
# # from app.models.userModel import User
# # from .auth import authenticate as get_current_user

# # router = APIRouter( tags=["Transactions"])

# # # MongoDB collection
# # transaction_collection = db.transactions

# # # Pydantic schemas
# # class TransactionModel(BaseModel):
# #     userId: str
# #     type: str
# #     amount: float
# #     status: str
# #     description: Optional[str] = None
# #     bankDetails: Optional[dict] = None
# #     createdAt: Optional[datetime] = Field(default_factory=datetime.utcnow)

# # class TransactionResponse(BaseModel):
# #     transaction: dict
# #     newBalance: Optional[float] = None
# #     newLedgerBalance: Optional[float] = None
# #     newMarginAvailable: Optional[float] = None

# # # ---------------- JWT Authentication ---------------- #
# # # Uses dependency injection to get current user
# # # get_current_user returns the User object

# # # ---------------- Get Transactions ---------------- #
# # # ---------------- Get Transactions ---------------- #
# # @router.get("/", summary="Get user transactions")
# # async def get_transactions(
# #     page: int = Query(1, ge=1),
# #     limit: int = Query(20, ge=1),
# #     type: Optional[str] = Query(None, regex="^(deposit|withdraw)$"),
# #     status: Optional[str] = Query(None, regex="^(pending|approved|rejected)$"),
# #     startDate: Optional[datetime] = None,
# #     endDate: Optional[datetime] = None,
# #     sortBy: str = "createdAt",
# #     sortOrder: str = "desc",
# #     current_user: dict = Depends(get_current_user)
# # ):
# #     user_id = ObjectId(current_user["_id"])
    
# #     # Build filter
# #     filter_query = {"userId": user_id}
# #     if type:
# #         filter_query["type"] = type
# #     if status:
# #         filter_query["status"] = status
# #     if startDate or endDate:
# #         filter_query["createdAt"] = {}
# #         if startDate:
# #             filter_query["createdAt"]["$gte"] = startDate
# #         if endDate:
# #             filter_query["createdAt"]["$lte"] = endDate

# #     # Sorting
# #     sort_value = -1 if sortOrder == "desc" else 1

# #     # Pagination
# #     skip = (page - 1) * limit

# #     transactions_cursor = transaction_collection.find(filter_query).sort(sortBy, sort_value).skip(skip).limit(limit)
# #     transactions = await transactions_cursor.to_list(length=limit)
    
# #     # Convert ObjectId to str for serialization
# #     for txn in transactions:
# #         txn["_id"] = str(txn["_id"])
# #         txn["userId"] = str(txn["userId"])

# #     total = await transaction_collection.count_documents(filter_query)

# #     # Summary
# #     pipeline = [
# #         {"$match": {"userId": user_id}},
# #         {
# #             "$group": {
# #                 "_id": None,
# #                 "totalDeposits": {"$sum": {"$cond": [{"$eq": ["$type", "deposit"]}, "$amount", 0]}},
# #                 "totalWithdrawals": {"$sum": {"$cond": [{"$eq": ["$type", "withdraw"]}, "$amount", 0]}},
# #                 "pendingTransactions": {"$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}}
# #             }
# #         }
# #     ]
# #     summary_cursor = transaction_collection.aggregate(pipeline)
# #     summary = await summary_cursor.to_list(length=1)
# #     summary_data = summary[0] if summary else {"totalDeposits": 0, "totalWithdrawals": 0, "pendingTransactions": 0}

# #     return {
# #         "success": True,
# #         "data": {
# #             "transactions": transactions,
# #             "summary": summary_data,
# #             "pagination": {
# #                 "currentPage": page,
# #                 "totalPages": (total + limit - 1) // limit,
# #                 "totalTransactions": total,
# #                 "hasNext": page < (total + limit - 1) // limit,
# #                 "hasPrev": page > 1,
# #             }
# #         }
# #     }

# # # ---------------- Create Deposit ---------------- #
# # class DepositRequest(BaseModel):
# #     amount: float
# #     description: Optional[str] = "Account deposit"

# # @router.post("/deposit", response_model=TransactionResponse)
# # async def create_deposit(req: DepositRequest, current_user: dict = Depends(get_current_user)):
# #     if req.amount <= 0:
# #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deposit amount must be greater than 0")

# #     txn = {
# #         "userId": ObjectId(current_user["_id"]),
# #         "type": "deposit",
# #         "amount": req.amount,
# #         "description": req.description,
# #         "status": "approved",
# #         "createdAt": datetime.utcnow()
# #     }

# #     result = await transaction_collection.insert_one(txn)

# #     # Update user balance immediately
# #     await db.users.update_one(
# #         {"_id": ObjectId(current_user["_id"])},
# #         {"$inc": {"balance": req.amount, "ledgerBalance": req.amount, "marginAvailable": req.amount}}
# #     )

# #     user = await db.users.find_one({"_id": ObjectId(current_user["_id"])}, {"balance": 1, "ledgerBalance": 1, "marginAvailable": 1})

# #     txn["transactionId"] = str(result.inserted_id)
# #     return {
# #         "transaction": txn,
# #         "newBalance": user["balance"],
# #         "newLedgerBalance": user["ledgerBalance"],
# #         "newMarginAvailable": user["marginAvailable"]
# #     }

# # # ---------------- Create Withdrawal ---------------- #
# # class WithdrawalRequest(BaseModel):
# #     amount: float
# #     description: Optional[str] = "Account withdrawal"
# #     bankDetails: Optional[dict] = None

# # @router.post("/withdraw", response_model=TransactionResponse)
# # async def create_withdrawal(req: WithdrawalRequest, current_user: dict = Depends(get_current_user)):
# #     if req.amount <= 0:
# #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Withdrawal amount must be greater than 0")

# #     user = await db.users.find_one({"_id": ObjectId(current_user["_id"])})
# #     if not user:
# #         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

# #     if user["balance"] < req.amount:
# #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Insufficient balance. Available: {user['balance']}")

# #     MIN_WITHDRAWAL = 10
# #     MAX_WITHDRAWAL = 50000

# #     if req.amount < MIN_WITHDRAWAL:
# #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Minimum withdrawal amount is {MIN_WITHDRAWAL}")
# #     if req.amount > MAX_WITHDRAWAL:
# #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Maximum withdrawal amount is {MAX_WITHDRAWAL}")

# #     txn = {
# #         "userId": ObjectId(current_user["_id"]),
# #         "type": "withdraw",
# #         "amount": req.amount,
# #         "description": req.description,
# #         "bankDetails": req.bankDetails,
# #         "status": "pending",
# #         "createdAt": datetime.utcnow()
# #     }

# #     result = await transaction_collection.insert_one(txn)

# #     # Reserve amount (deduct from available balance)
# #     await db.users.update_one(
# #         {"_id": ObjectId(current_user["_id"])},
# #         {"$inc": {"balance": -req.amount, "marginAvailable": -req.amount}}
# #     )

# #     return {
# #         "transaction": txn,
# #         "currentBalance": user["balance"] - req.amount,
# #         "currentMarginAvailable": user["marginAvailable"] - req.amount
# #     }


# # app/routes/transactions.py
# from fastapi import APIRouter, Depends, HTTPException, Query, status
# from pydantic import BaseModel, Field
# from typing import Optional
# from datetime import datetime
# from bson import ObjectId

# from app.database import db
# from app.models.userModel import User
# from .auth import authenticate as get_current_user

# router = APIRouter(tags=["Transactions"])

# # MongoDB collection
# transaction_collection = db.transactions

# # ---------------- Pydantic Schemas ---------------- #
# class TransactionResponse(BaseModel):
#     transaction: dict
#     newBalance: Optional[float] = None
#     newLedgerBalance: Optional[float] = None
#     newMarginAvailable: Optional[float] = None

# class DepositRequest(BaseModel):
#     amount: float
#     description: Optional[str] = "Account deposit"

# class WithdrawalRequest(BaseModel):
#     amount: float
#     description: Optional[str] = "Account withdrawal"
#     bankDetails: Optional[dict] = None

# # ---------------- Get Transactions ---------------- #
# @router.get("/", summary="Get user transactions")
# async def get_transactions(
#     page: int = Query(1, ge=1),
#     limit: int = Query(20, ge=1),
#     type: Optional[str] = Query(None, regex="^(deposit|withdraw)$"),
#     status: Optional[str] = Query(None, regex="^(pending|approved|rejected)$"),
#     startDate: Optional[datetime] = None,
#     endDate: Optional[datetime] = None,
#     sortBy: str = "createdAt",
#     sortOrder: str = "desc",
#     current_user: dict = Depends(get_current_user)
# ):
#     user_id = ObjectId(current_user["_id"])
    
#     # Build filter
#     filter_query = {"userId": user_id}
#     if type:
#         filter_query["type"] = type
#     if status:
#         filter_query["status"] = status
#     if startDate or endDate:
#         filter_query["createdAt"] = {}
#         if startDate:
#             filter_query["createdAt"]["$gte"] = startDate
#         if endDate:
#             filter_query["createdAt"]["$lte"] = endDate

#     # Sorting
#     sort_value = -1 if sortOrder == "desc" else 1

#     # Pagination
#     skip = (page - 1) * limit

#     transactions_cursor = transaction_collection.find(filter_query).sort(sortBy, sort_value).skip(skip).limit(limit)
#     transactions = await transactions_cursor.to_list(length=limit)
    
#     # Convert ObjectId to str for serialization
#     for txn in transactions:
#         txn["_id"] = str(txn["_id"])
#         txn["userId"] = str(txn["userId"])

#     total = await transaction_collection.count_documents(filter_query)

#     # Summary
#     pipeline = [
#         {"$match": {"userId": user_id}},
#         {
#             "$group": {
#                 "_id": None,
#                 "totalDeposits": {"$sum": {"$cond": [{"$eq": ["$type", "deposit"]}, "$amount", 0]}},
#                 "totalWithdrawals": {"$sum": {"$cond": [{"$eq": ["$type", "withdraw"]}, "$amount", 0]}},
#                 "pendingTransactions": {"$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}}
#             }
#         }
#     ]
#     summary_cursor = transaction_collection.aggregate(pipeline)
#     summary = await summary_cursor.to_list(length=1)
#     summary_data = summary[0] if summary else {"totalDeposits": 0, "totalWithdrawals": 0, "pendingTransactions": 0}

#     return {
#         "success": True,
#         "data": {
#             "transactions": transactions,
#             "summary": summary_data,
#             "pagination": {
#                 "currentPage": page,
#                 "totalPages": (total + limit - 1) // limit,
#                 "totalTransactions": total,
#                 "hasNext": page < (total + limit - 1) // limit,
#                 "hasPrev": page > 1,
#             }
#         }
#     }

# # ---------------- Create Deposit ---------------- #
# @router.post("/deposit", response_model=TransactionResponse)
# async def create_deposit(req: DepositRequest, current_user: dict = Depends(get_current_user)):
#     if req.amount <= 0:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deposit amount must be greater than 0")

#     txn = {
#         "userId": str(current_user["_id"]),
#         "type": "deposit",
#         "amount": req.amount,
#         "description": req.description,
#         "status": "approved",
#         "createdAt": datetime.utcnow()
#     }

#     result = await transaction_collection.insert_one({**txn, "userId": ObjectId(current_user["_id"])})

#     # Update user balance immediately
#     await db.users.update_one(
#         {"_id": ObjectId(current_user["_id"])},
#         {"$inc": {"balance": req.amount, "ledgerBalance": req.amount, "marginAvailable": req.amount}}
#     )

#     user = await db.users.find_one(
#         {"_id": ObjectId(current_user["_id"])},
#         {"balance": 1, "ledgerBalance": 1, "marginAvailable": 1}
#     )

#     txn["transactionId"] = str(result.inserted_id)
#     return {
#         "transaction": txn,
#         "newBalance": user["balance"],
#         "newLedgerBalance": user["ledgerBalance"],
#         "newMarginAvailable": user["marginAvailable"]
#     }

# # ---------------- Create Withdrawal ---------------- #
# @router.post("/withdraw", response_model=TransactionResponse)
# async def create_withdrawal(req: WithdrawalRequest, current_user: dict = Depends(get_current_user)):
#     if req.amount <= 0:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Withdrawal amount must be greater than 0")

#     user = await db.users.find_one({"_id": ObjectId(current_user["_id"])})
#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

#     if user["balance"] < req.amount:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Insufficient balance. Available: {user['balance']}")

#     MIN_WITHDRAWAL = 10
#     MAX_WITHDRAWAL = 50000

#     if req.amount < MIN_WITHDRAWAL:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Minimum withdrawal amount is {MIN_WITHDRAWAL}")
#     if req.amount > MAX_WITHDRAWAL:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Maximum withdrawal amount is {MAX_WITHDRAWAL}")

#     txn = {
#         "userId": str(current_user["_id"]),
#         "type": "withdraw",
#         "amount": req.amount,
#         "description": req.description,
#         "bankDetails": req.bankDetails,
#         "status": "approved",
#         "createdAt": datetime.utcnow()
#     }

#     result = await transaction_collection.insert_one({**txn, "userId": ObjectId(current_user["_id"])})

#     # Reserve amount (deduct from available balance)
#     await db.users.update_one(
#         {"_id": ObjectId(current_user["_id"])},
#         {"$inc": {"balance": -req.amount, "marginAvailable": -req.amount}}
#     )

#     txn["transactionId"] = str(result.inserted_id)

#     return {
#         "transaction": txn,
#         "newBalance": user["balance"] - req.amount,
#         "newLedgerBalance": user["ledgerBalance"] - req.amount,
#         "newMarginAvailable": user["marginAvailable"] - req.amount
#     }
from bson import ObjectId
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional

from app.database import db
from app.models.userModel import User
from .auth import authenticate as get_current_user

router = APIRouter(tags=["Transactions"])

# MongoDB collection
transaction_collection = db.transactions


# ---------------- Helper Formatter ---------------- #
def format_transaction(txn: dict) -> dict:
    """Format MongoDB transaction to match dummy response structure."""
    return {
        "id": str(txn["_id"]),
        "type": "withdrawal" if txn["type"] in ["withdraw", "withdrawal"] else "deposit",
        "amount": txn["amount"],
        "status": "completed" if txn["status"] == "approved" else txn["status"],
        "created_at": (
            txn["createdAt"].isoformat() + "Z"
            if isinstance(txn["createdAt"], datetime)
            else txn.get("createdAt")
        ),
        "description": txn.get("description", "")
    }


# ---------------- Pydantic Schemas ---------------- #
class TransactionResponse(BaseModel):
    transaction: dict
    newBalance: Optional[float] = None
    newLedgerBalance: Optional[float] = None
    newMarginAvailable: Optional[float] = None


class DepositRequest(BaseModel):
    amount: float
    description: Optional[str] = "Account deposit"


class WithdrawalRequest(BaseModel):
    amount: float
    description: Optional[str] = "Account withdrawal"
    bankDetails: Optional[dict] = None


# ---------------- Get Transactions ---------------- #
@router.get("/", summary="Get user transactions")
async def get_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1),
    type: Optional[str] = Query(None, regex="^(deposit|withdraw)$"),
    status: Optional[str] = Query(None, regex="^(pending|approved|rejected)$"),
    startDate: Optional[datetime] = None,
    endDate: Optional[datetime] = None,
    sortBy: str = "createdAt",
    sortOrder: str = "desc",
    current_user: dict = Depends(get_current_user)
):
    user_id = ObjectId(current_user["_id"])

    # Build filter
    filter_query = {"userId": user_id}
    if type:
        filter_query["type"] = type
    if status:
        filter_query["status"] = status
    if startDate or endDate:
        filter_query["createdAt"] = {}
        if startDate:
            filter_query["createdAt"]["$gte"] = startDate
        if endDate:
            filter_query["createdAt"]["$lte"] = endDate

    # Sorting
    sort_value = -1 if sortOrder == "desc" else 1

    # Pagination
    skip = (page - 1) * limit

    cursor = transaction_collection.find(filter_query).sort(sortBy, sort_value).skip(skip).limit(limit)
    transactions = await cursor.to_list(length=limit)

    # Format transactions to match dummy response
    transactions = [format_transaction(txn) for txn in transactions]

    total = await transaction_collection.count_documents(filter_query)

    # Summary
    pipeline = [
        {"$match": {"userId": user_id}},
        {
            "$group": {
                "_id": None,
                "totalDeposits": {"$sum": {"$cond": [{"$eq": ["$type", "deposit"]}, "$amount", 0]}},
                "totalWithdrawals": {"$sum": {"$cond": [{"$eq": ["$type", "withdraw"]}, "$amount", 0]}},
                "pendingTransactions": {"$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}}
            }
        }
    ]
    summary_cursor = transaction_collection.aggregate(pipeline)
    summary = await summary_cursor.to_list(length=1)
    summary_data = summary[0] if summary else {
        "totalDeposits": 0,
        "totalWithdrawals": 0,
        "pendingTransactions": 0
    }

    return {
        "success": True,
        "data": {
            "transactions": transactions,
            "summary": summary_data,
            "pagination": {
                "currentPage": page,
                "totalPages": (total + limit - 1) // limit,
                "totalTransactions": total,
                "hasNext": page < (total + limit - 1) // limit,
                "hasPrev": page > 1,
            }
        }
    }


# ---------------- Create Deposit ---------------- #
# @router.post("/deposit", response_model=TransactionResponse)
# async def create_deposit(req: DepositRequest, current_user: dict = Depends(get_current_user)):
#     if req.amount <= 0:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deposit amount must be greater than 0")

#     txn = {
#         "userId": ObjectId(current_user["_id"]),
#         "type": "deposit",
#         "amount": req.amount,
#         "description": req.description,
#         "status": "approved",
#         "createdAt": datetime.utcnow()
#     }

#     result = await transaction_collection.insert_one(txn)

#     # Update user balance
#     await db.users.update_one(
#         {"_id": ObjectId(current_user["_id"])},
#         {"$inc": {"balance": req.amount, "ledgerBalance": req.amount, "marginAvailable": req.amount}}
#     )

#     user = await db.users.find_one(
#         {"_id": ObjectId(current_user["_id"])},
#         {"balance": 1, "ledgerBalance": 1, "marginAvailable": 1}
#     )

#     txn["_id"] = result.inserted_id
#     formatted_txn = format_transaction(txn)

#     return {
#         "transaction": formatted_txn,
#         "newBalance": user["balance"],
#         "newLedgerBalance": user["ledgerBalance"],
#         "newMarginAvailable": user["marginAvailable"]
#     }



@router.post("/deposit", response_model=TransactionResponse)
async def create_deposit(req: DepositRequest, current_user: dict = Depends(get_current_user)):
    if req.amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deposit amount must be greater than 0")

    txn = {
        "userId": ObjectId(current_user["_id"]),
        "type": "deposit",
        "amount": req.amount,
        "description": req.description,
        "status": "approved",
        "createdAt": datetime.utcnow()
    }

    result = await transaction_collection.insert_one(txn)

    # Update user balance - deposit increases both ledger and available margin
    await User.update_balance(
        user_id=ObjectId(current_user["_id"]),
        balance=req.amount,
        ledger_balance=req.amount,
        margin_available=req.amount
    )

    user = await User.get_full_user(current_user["_id"])

    txn["_id"] = result.inserted_id
    formatted_txn = format_transaction(txn)

    return {
        "transaction": formatted_txn,
        "newBalance": user["balance"],
        "newLedgerBalance": user["ledgerBalance"],
        "newMarginAvailable": user["marginAvailable"]
    }




# ---------------- Create Withdrawal ---------------- #
@router.post("/withdraw", response_model=TransactionResponse)
async def create_withdrawal(req: WithdrawalRequest, current_user: dict = Depends(get_current_user)):
    if req.amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Withdrawal amount must be greater than 0")

    user = await db.users.find_one({"_id": ObjectId(current_user["_id"])})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user["balance"] < req.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Insufficient balance. Available: {user['balance']}")

    MIN_WITHDRAWAL = 10
    MAX_WITHDRAWAL = 50000

    if req.amount < MIN_WITHDRAWAL:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Minimum withdrawal amount is {MIN_WITHDRAWAL}")
    if req.amount > MAX_WITHDRAWAL:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Maximum withdrawal amount is {MAX_WITHDRAWAL}")

    txn = {
        "userId": ObjectId(current_user["_id"]),
        "type": "withdraw",
        "amount": req.amount,
        "description": req.description,
        "bankDetails": req.bankDetails,
        "status": "pending",
        "createdAt": datetime.utcnow()
    }

    result = await transaction_collection.insert_one(txn)

    # Deduct from available balance
    await db.users.update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$inc": {"balance": -req.amount, "marginAvailable": -req.amount}}
    )

    txn["_id"] = result.inserted_id
    formatted_txn = format_transaction(txn)

    return {
        "transaction": formatted_txn,
        "newBalance": user["balance"] - req.amount,
        "newLedgerBalance": user["ledgerBalance"] - req.amount,
        "newMarginAvailable": user["marginAvailable"] - req.amount
    }