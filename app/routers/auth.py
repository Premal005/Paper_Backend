# from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from pydantic import BaseModel, EmailStr
# from typing import Optional
# from bson import ObjectId
# import jwt
# import os
# from datetime import datetime, timedelta

# from app.models.userModel import User
# from app.models.TransactionModel import Transaction

# router = APIRouter( tags=["Auth"])

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# JWT_SECRET = os.getenv("JWT_SECRET", "secret")
# JWT_REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET", "refresh_secret")
# JWT_EXPIRE = int(os.getenv("JWT_EXPIRE", 7))  # days
# JWT_REFRESH_EXPIRE = int(os.getenv("JWT_REFRESH_EXPIRE", 30))  # days


# # ---------- Schemas ----------
# class RegisterSchema(BaseModel):
#     name: str
#     email: EmailStr
#     password: str


# class LoginSchema(BaseModel):
#     email: EmailStr
#     password: str


# class ChangePasswordSchema(BaseModel):
#     currentPassword: str
#     newPassword: str


# # ---------- Token Helpers ----------
# def generate_token(user_id: str):
#     payload = {
#         "userId": str(user_id),
#         "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRE)
#     }
#     return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


# def generate_refresh_token(user_id: str):
#     payload = {
#         "userId": str(user_id),
#         "exp": datetime.utcnow() + timedelta(days=JWT_REFRESH_EXPIRE)
#     }
#     return jwt.encode(payload, JWT_REFRESH_SECRET, algorithm="HS256")


# # ---------- Dependency (middleware-like) ----------
# async def authenticate(token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
#         user_id = payload.get("userId")
#         user = await User.find_by_id(user_id)
#         if not user or not user.get("isActive", True):
#             raise HTTPException(status_code=401, detail="User deactivated or not found")
#         return user
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token expired")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=401, detail="Invalid token")


# # ---------- Routes ----------
# @router.post("/register")
# async def register(data: RegisterSchema):
#     # Check if user already exists
#     existing_user = await User.find_by_email(data.email)
#     if existing_user:
#         raise HTTPException(status_code=409, detail="User already exists with this email")

#     # Create user
#     user_data = {
#         "name": data.name.strip(),
#         "email": data.email.lower(),
#         "passwordHash": data.password,   # TODO: hash properly in real implementation
#         "isActive": True
#     }
#     user_id = await User.create(user_data)

#     # Initial deposit transaction
#     await Transaction.create(user_id, "deposit", user_data.get("balance", 100000), "approved")

#     # Generate tokens
#     token = generate_token(user_id)
#     refresh_token = generate_refresh_token(user_id)

#     return {
#         "success": True,
#         "message": "User registered successfully",
#         "data": {
#             "user": {**user_data, "_id": user_id},
#             "token": token,
#             "refreshToken": refresh_token
#         }
#     }


# # @router.post("/login")
# # async def login(data: LoginSchema):
# #     user = await User.find_by_email(data.email)
# #     if not user:
# #         raise HTTPException(status_code=401, detail="Invalid email or password")

# #     if not user.get("isActive", True):
# #         raise HTTPException(status_code=401, detail="Account deactivated")

# #     # Password check (stub: replace with real hash check)
# #     if user.get("passwordHash") != data.password:
# #         raise HTTPException(status_code=401, detail="Invalid email or password")

# #     # Update last login
# #     await User.collection.update_one(
# #         {"_id": ObjectId(user["_id"])},
# #         {"$set": {"lastLogin": datetime.utcnow()}}
# #     )

# #     token = generate_token(str(user["_id"]))
# #     refresh_token = generate_refresh_token(str(user["_id"]))

# #     return {
# #         "success": True,
# #         "message": "Login successful",
# #         "data": {
# #             "user": user,
# #             "token": token,
# #             "refreshToken": refresh_token
# #         }
# #     }
# from datetime import datetime
# from bson import ObjectId
# from fastapi import APIRouter, HTTPException
# # ... other imports ...

# @router.post("/login")
# async def login(data: LoginSchema):
#     # fetch serialized user (User.find_by_email returns serialized doc or None)
#     user = await User.find_by_email(data.email)
#     if not user:
#         raise HTTPException(status_code=401, detail="Invalid email or password")

#     if not user.get("isActive", True):
#         raise HTTPException(status_code=401, detail="Account deactivated")

#     # Password check (stub: replace with real hash check)
#     if user.get("passwordHash") != data.password:
#         raise HTTPException(status_code=401, detail="Invalid email or password")

#     # Update last login (store as UTC datetime)
#     await User.collection.update_one(
#         {"_id": ObjectId(user["_id"])},
#         {"$set": {"lastLogin": datetime.utcnow()}}
#     )

#     # generate tokens (replace with your real implementations)
#     access_token = generate_token(str(user["_id"]))
#     refresh_token = generate_refresh_token(str(user["_id"]))
#     expires_in = 3600  # seconds (adjust if your token generator provides expiry)

#     # Prepare user payload for response (remove sensitive fields)
#     safe_user = dict(user)  # shallow copy
#     # Remove internal/sensitive fields
#     safe_user.pop("passwordHash", None)
#     # Map _id -> id
#     user_id = safe_user.pop("_id", None)
#     # Handle createdAt -> created_at (ISO string)
#     created_at = safe_user.pop("createdAt", None) or safe_user.pop("created_at", None)
#     if isinstance(created_at, datetime):
#         created_at_str = created_at.replace(tzinfo=None).isoformat() + "Z"
#     elif created_at is None:
#         created_at_str = None
#     else:
#         # assume already a string
#         created_at_str = str(created_at)

#     # Build the user object matching dummy shape
#     response_user = {
#         "id": user_id,
#         "email": safe_user.get("email"),
#         "name": safe_user.get("name") or safe_user.get("fullName") or "",
#         "created_at": created_at_str
#     }

#     return {
#         "success": True,
#         "message": "Login successful",
#         "data": {
#             "user": response_user,
#             "tokens": {
#                 "access_token": access_token,
#                 "refresh_token": refresh_token,
#                 "expires_in": expires_in
#             }
#         }
#     }


# @router.post("/refresh")
# async def refresh_token(refreshToken: str):
#     try:
#         payload = jwt.decode(refreshToken, JWT_REFRESH_SECRET, algorithms=["HS256"])
#         user_id = payload.get("userId")

#         user = await User.find_by_id(user_id)
#         if not user or not user.get("isActive", True):
#             raise HTTPException(status_code=401, detail="Invalid refresh token")

#         new_token = generate_token(user_id)
#         new_refresh = generate_refresh_token(user_id)

#         return {
#             "success": True,
#             "message": "Token refreshed successfully",
#             "data": {
#                 "token": new_token,
#                 "refreshToken": new_refresh
#             }
#         }
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Refresh token expired")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=401, detail="Invalid refresh token")


# @router.get("/me")
# async def get_me(user=Depends(authenticate)):
#     return {
#         "success": True,
#         "data": {"user": user}
#     }


# @router.put("/change-password")
# async def change_password(data: ChangePasswordSchema, user=Depends(authenticate)):
#     if user.get("passwordHash") != data.currentPassword:  # TODO: hash check
#         raise HTTPException(status_code=401, detail="Current password incorrect")

#     await User.collection.update_one(
#         {"_id": ObjectId(user["_id"])},
#         {"$set": {"passwordHash": data.newPassword}}
#     )

#     return {"success": True, "message": "Password changed successfully"}
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from bson import ObjectId
from datetime import datetime, timedelta
import jwt, os

from app.models.userModel import User
from app.models.TransactionModel import Transaction
from app.models.portfolioModel import Portfolio

router = APIRouter(tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

JWT_SECRET = os.getenv("JWT_SECRET", "secret")
JWT_REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET", "refresh_secret")
JWT_EXPIRE = int(os.getenv("JWT_EXPIRE", 7))  # days
JWT_REFRESH_EXPIRE = int(os.getenv("JWT_REFRESH_EXPIRE", 30))  # days

# ---------- Schemas ----------
class RegisterSchema(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordSchema(BaseModel):
    currentPassword: str
    newPassword: str

# ---------- Token Helpers ----------
def generate_token(user_id: str):
    payload = {"userId": str(user_id), "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRE)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def generate_refresh_token(user_id: str):
    payload = {"userId": str(user_id), "exp": datetime.utcnow() + timedelta(days=JWT_REFRESH_EXPIRE)}
    return jwt.encode(payload, JWT_REFRESH_SECRET, algorithm="HS256")

# ---------- Authentication Dependency ----------
async def authenticate(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("userId")
        user = await User.find_by_id(user_id)
        if not user or not user.get("isActive", True):
            raise HTTPException(status_code=401, detail="User deactivated or not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ---------- Routes ----------

# @router.post("/register")
# async def register(data: RegisterSchema):
#     existing_user = await User.find_by_email(data.email)
#     if existing_user:
#         raise HTTPException(status_code=409, detail="User already exists with this email")

#     user_data = {
#         "name": data.name.strip(),
#         "email": data.email.lower(),
#         "passwordHash": data.password,  # TODO: hash properly
#         "isActive": True
#     }
#     user_id = await User.create(user_data)

#     await Transaction.create(user_id, "deposit", user_data.get("balance", 100000), "approved")

#     token = generate_token(user_id)
#     refresh_token = generate_refresh_token(user_id)

#     response_user = {
#         "id": str(user_id),
#         "email": user_data["email"],
#         "name": user_data["name"],
#         "created_at": datetime.utcnow().isoformat() + "Z"
#     }

#     return {
#         "success": True,
#         "message": "Registration successful",
#         "data": {
#             "user": response_user,
#             "tokens": {
#                 "access_token": token,
#                 "refresh_token": refresh_token,
#                 "expires_in": 3600
#             }
#         }
#     }
@router.post("/register")
async def register(data: RegisterSchema):
    # Check if user already exists
    existing_user = await User.find_by_email(data.email)
    if existing_user:
        raise HTTPException(status_code=409, detail="User already exists with this email")

    # Prepare user data
    user_data = {
        "name": data.name.strip(),
        "email": data.email.lower(),
        "passwordHash": data.password,  # TODO: hash properly
        "isActive": True
    }

    # Create user
    user_id = await User.create(user_data)

    # Create initial portfolio for the user
    await Portfolio.create(user_id, holdings=[])

    # Create initial transaction (deposit)
    await Transaction.create(user_id, "deposit", user_data.get("balance", 100000), "approved")

    # Generate tokens
    token = generate_token(user_id)
    refresh_token = generate_refresh_token(user_id)

    # Prepare response
    response_user = {
        "id": str(user_id),
        "email": user_data["email"],
        "name": user_data["name"],
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

    return {
        "success": True,
        "message": "Registration successful",
        "data": {
            "user": response_user,
            "tokens": {
                "access_token": token,
                "refresh_token": refresh_token,
                "expires_in": 3600
            }
        }
    }
@router.post("/login")
async def login(data: LoginSchema):
    user = await User.find_by_email(data.email)
    if not user or not user.get("isActive", True) or user.get("passwordHash") != data.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    await User.collection.update_one({"_id": ObjectId(user["_id"])}, {"$set": {"lastLogin": datetime.utcnow()}})

    access_token = generate_token(str(user["_id"]))
    refresh_token = generate_refresh_token(str(user["_id"]))

    response_user = {
        "id": str(user["_id"]),
        "email": user.get("email"),
        "name": user.get("name"),
        "created_at": (user.get("createdAt") or datetime.utcnow()).isoformat() + "Z"
    }

    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "user": response_user,
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": 3600
            }
        }
    }

@router.post("/refresh")
async def refresh_token(refreshToken: str):
    try:
        payload = jwt.decode(refreshToken, JWT_REFRESH_SECRET, algorithms=["HS256"])
        user_id = payload.get("userId")

        user = await User.find_by_id(user_id)
        if not user or not user.get("isActive", True):
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        new_token = generate_token(user_id)
        new_refresh = generate_refresh_token(user_id)

        return {
            "success": True,
            "message": "Token refreshed successfully",
            "data": {
                "tokens": {
                    "access_token": new_token,
                    "refresh_token": new_refresh,
                    "expires_in": 3600
                }
            }
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.get("/me")
async def get_me(user=Depends(authenticate)):
    return {
        "success": True,
        "data": {
            "id": str(user["_id"]),
            "email": user.get("email"),
            "name": user.get("name"),
            "phone": user.get("phone", ""),
            "created_at": (user.get("createdAt") or datetime.utcnow()).isoformat() + "Z",
            "verified": user.get("verified", False)
        }
    }

@router.put("/change-password")
async def change_password(data: ChangePasswordSchema, user=Depends(authenticate)):
    if user.get("passwordHash") != data.currentPassword:  # TODO: hash check
        raise HTTPException(status_code=401, detail="Current password incorrect")

    await User.collection.update_one({"_id": ObjectId(user["_id"])}, {"$set": {"passwordHash": data.newPassword}})

    return {
        "success": True,
        "message": "Password changed successfully"
    }