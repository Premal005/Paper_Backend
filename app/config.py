# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI")
    PORT = int(os.getenv("PORT", 8080))

    JWT_SECRET = os.getenv("JWT_SECRET")
    JWT_REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET")
    JWT_EXPIRE = os.getenv("JWT_EXPIRE", "7d")
    JWT_REFRESH_EXPIRE = os.getenv("JWT_REFRESH_EXPIRE", "30d")
    START_BALANCE = float(os.getenv("START_BALANCE", 100000))

    ALPACA_KEY = os.getenv("ALPACA_KEY")
    ALPACA_SECRET = os.getenv("ALPACA_SECRET")
    ALPACA_WS = os.getenv("ALPACA_WS")

    FYERS_CLIENT_ID = os.getenv("CLIENT_ID")
    FYERS_SECRET_KEY = os.getenv("SECRET_KEY")
    FYERS_REDIRECT_URI = os.getenv("REDIRECT_URI")
    FYERS_WS = os.getenv("FYERS_WS")
    TOKEN_PERSIST_FILE = os.getenv("TOKEN_PERSIST_FILE", "./tokens.json")

    REDIS_URL = os.getenv("REDIS_URL")
    MT5_REDIS_CHANNEL = os.getenv("MT5_REDIS_CHANNEL")
