import os
import json
import asyncio
import requests
import websockets
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# -------------------
# Config
# -------------------
CLIENT_ID = os.getenv("CLIENT_ID")
SECRET_KEY = os.getenv("SECRET_KEY")
REDIRECT_URI = os.getenv("REDIRECT_URI")  # http://localhost:8000/fyers/callback
FYERS_WS = os.getenv("FYERS_WS")
TOKEN_FILE = os.getenv("TOKEN_PERSIST_FILE", "./tokens.json")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URI)
db = client["market_data"]
market_data = db["fyers"]


# -------------------
# Token Management
# -------------------
def save_token(token_data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f)


def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return None


def exchange_auth_code(auth_code: str):
    url = "https://api.fyers.in/api/v2/token"
    payload = {
        "client_id": CLIENT_ID,
        "secret_key": SECRET_KEY,
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
    }
    res = requests.post(url, json=payload)
    data = res.json()
    if "access_token" in data:
        save_token(data)
        return data
    raise Exception(f"Token exchange failed: {data}")


# -------------------
# WebSocket Feed
# -------------------
def normalize_fyers_message(msg: dict):
    try:
        return {
            "symbol": msg.get("s") or msg.get("symbol"),
            "exchange": "FYERS",
            "brokerSymbol": msg.get("s"),
            "instrumentType": msg.get("instrumentType", "Futures"),
            "ltp": (msg.get("ltpc", {}).get("ltp") if msg.get("ltpc") else msg.get("ltp")),
            "bid": (msg.get("ltpc", {}).get("bid") if msg.get("ltpc") else None),
            "ask": (msg.get("ltpc", {}).get("ask") if msg.get("ltpc") else None),
            "volume": msg.get("vol"),
            "oi": msg.get("oi"),
            "timestamp": datetime.utcnow().timestamp(),
        }
    except Exception:
        return None


async def start_fyers_feed(broadcast=None):
    """Start Fyers WebSocket feed"""
    token_data = load_token()
    if not token_data or "access_token" not in token_data:
        print("⚠️ No Fyers token found, login required.")
        return

    token = token_data["access_token"]
    url = f"{FYERS_WS}{token}"

    async for ws in websockets.connect(url):
        try:
            print("✅ Connected to Fyers WS")

            sub_msg = {"symbol": ["NSE:NIFTY50-INDEX", "NSE:BANKNIFTY-INDEX"]}
            await ws.send(json.dumps(sub_msg))

            async for raw in ws:
                try:
                    msg = json.loads(raw)
                    tick = normalize_fyers_message(msg)
                    if not tick or not tick["symbol"]:
                        continue

                    # Save in MongoDB
                    await market_data.update_one(
                        {"symbol": tick["symbol"], "exchange": "FYERS"},
                        {
                            "$set": {
                                "brokerSymbol": tick["brokerSymbol"],
                                "instrumentType": tick["instrumentType"],
                                "ltp": tick["ltp"],
                                "bid": tick["bid"],
                                "ask": tick["ask"],
                                "volume": tick["volume"],
                                "oi": tick["oi"],
                                "updatedAt": datetime.utcnow(),
                            }
                        },
                        upsert=True,
                    )

                    if broadcast:
                        await broadcast({**tick, "source": "FYERS"})

                except Exception as e:
                    print("❌ Error handling Fyers message:", str(e))

        except Exception as e:
            print("🚨 Fyers WS error:", str(e))
            await asyncio.sleep(5)
