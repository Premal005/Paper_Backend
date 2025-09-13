from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from typing import Optional
from bson import ObjectId
import jwt
import os
from datetime import datetime, timedelta

from app.models.userModel import User
from app.models.TransactionModel import Transaction

router = APIRouter( tags=["Auth"])

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
    payload = {
        "userId": str(user_id),
        "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRE)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def generate_refresh_token(user_id: str):
    payload = {
        "userId": str(user_id),
        "exp": datetime.utcnow() + timedelta(days=JWT_REFRESH_EXPIRE)
    }
    return jwt.encode(payload, JWT_REFRESH_SECRET, algorithm="HS256")


# ---------- Dependency (middleware-like) ----------
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
@router.post("/register")
async def register(data: RegisterSchema):
    # Check if user already exists
    existing_user = await User.find_by_email(data.email)
    if existing_user:
        raise HTTPException(status_code=409, detail="User already exists with this email")

    # Create user
    user_data = {
        "name": data.name.strip(),
        "email": data.email.lower(),
        "passwordHash": data.password,   # TODO: hash properly in real implementation
        "isActive": True
    }
    user_id = await User.create(user_data)

    # Initial deposit transaction
    await Transaction.create(user_id, "deposit", user_data.get("balance", 100000), "approved")

    # Generate tokens
    token = generate_token(user_id)
    refresh_token = generate_refresh_token(user_id)

    return {
        "success": True,
        "message": "User registered successfully",
        "data": {
            "user": {**user_data, "_id": user_id},
            "token": token,
            "refreshToken": refresh_token
        }
    }


@router.post("/login")
async def login(data: LoginSchema):
    user = await User.find_by_email(data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.get("isActive", True):
        raise HTTPException(status_code=401, detail="Account deactivated")

    # Password check (stub: replace with real hash check)
    if user.get("passwordHash") != data.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Update last login
    await User.collection.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {"lastLogin": datetime.utcnow()}}
    )

    token = generate_token(str(user["_id"]))
    refresh_token = generate_refresh_token(str(user["_id"]))

    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "user": user,
            "token": token,
            "refreshToken": refresh_token
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
                "token": new_token,
                "refreshToken": new_refresh
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
        "data": {"user": user}
    }


@router.put("/change-password")
async def change_password(data: ChangePasswordSchema, user=Depends(authenticate)):
    if user.get("passwordHash") != data.currentPassword:  # TODO: hash check
        raise HTTPException(status_code=401, detail="Current password incorrect")

    await User.collection.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {"passwordHash": data.newPassword}}
    )

    return {"success": True, "message": "Password changed successfully"}
