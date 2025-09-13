# import asyncio
# import logging
# import os
# from fastapi import FastAPI, WebSocket
# from motor.motor_asyncio import AsyncIOMotorClient
# from dotenv import load_dotenv
# from fastapi import Request
# from fastapi.responses import RedirectResponse, JSONResponse


# # Load environment variables
# load_dotenv()
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # ---- Import your routers (like Express routers) ----
# from .routers import auth, market, portfolio, order, trade, watchlist, transactions

# # ---- Import broker feed workers ----
# # from .services.alpacaService import start_alpaca_feed
# from .services.alpacaService import start_alpaca_feed
# from .services.fyerService import start_fyers_feed
# # from broker.mt5_service import start_mt5_feed


# # ---- FastAPI App ----
# app = FastAPI()

# # ---- MongoDB Connection ----
# MONGO_URI = os.getenv("MONGO_URI")
# client = AsyncIOMotorClient(MONGO_URI)
# db = client["paper_trading"]


# # ---- WebSocket Connections ----
# connected_clients = set()

# async def broadcast(message: dict):
#     """Send tick to all connected WebSocket clients"""
#     dead_clients = []
#     for ws in connected_clients:
#         try:
#             await ws.send_json(message)
#         except Exception:
#             dead_clients.append(ws)

#     for ws in dead_clients:
#         connected_clients.remove(ws)


# # ---- Root Endpoint ----
# @app.get("/")
# async def root():
#     return {"message": "Paper Trading Backend is running..."}



# # ---- Fyers Login Endpoint ----
# @app.get("/fyers/login")
# async def fyers_login():
#     """Redirect user to Fyers login page"""
#     from broker.fyers_service import CLIENT_ID, REDIRECT_URI
#     login_url = (
#         f"https://api.fyers.in/api/v2/generate-authcode?client_id={CLIENT_ID}"
#         f"&redirect_uri={REDIRECT_URI}&response_type=code&state=sample"
#     )
#     return RedirectResponse(login_url)


# # ---- Fyers Callback Endpoint ----
# @app.get("/fyers/callback")
# async def fyers_callback(request: Request):
#     """Handle Fyers redirect, exchange code for token"""
#     from broker.fyers_service import exchange_auth_code

#     code = request.query_params.get("code")
#     if not code:
#         return JSONResponse({"error": "Missing code"}, status_code=400)

#     try:
#         token_data = await exchange_auth_code(code)  # async version in fyers_service
#         return {"msg": "Token saved successfully", "token": token_data}
#     except Exception as e:
#         return JSONResponse({"error": str(e)}, status_code=500)


# # ---- Register Routers ----
# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# app.include_router(market.router, prefix="/api/market", tags=["market"])
# app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
# app.include_router(order.router, prefix="/api/orders", tags=["orders"])
# app.include_router(trade.router, prefix="/api/trades", tags=["trades"])
# # app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
# app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
# app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])

# # ---- Market Data WebSocket ----
# @app.websocket("/ws/market")
# async def market_ws(websocket: WebSocket):
#     await websocket.accept()
#     connected_clients.add(websocket)
#     try:
#         while True:
#             await websocket.receive_text()  # keep alive
#     except Exception:
#         connected_clients.remove(websocket)


# # ---- Startup Tasks ----
# @app.on_event("startup")
# async def startup_event():
#     logger.info("🚀 Starting Paper Trading Backend...")

#     # Start broker feeds as background tasks
#     asyncio.create_task(start_alpaca_feed(broadcast))
#     # asyncio.create_task(start_fyers_feed(broadcast))
#     # asyncio.create_task(start_mt5_feed(broadcast, db))

#     logger.info("✅ All feeds launched")


# # ---- Global Error Handlers ----
# @app.on_event("startup")
# async def global_error_handlers():
#     import sys

#     def handle_exception(loop, context):
#         msg = context.get("exception", context["message"])
#         logger.error(f"Unhandled exception: {msg}")

#     loop = asyncio.get_event_loop()
#     loop.set_exception_handler(handle_exception)


# from .services import alpacaService
# app.include_router(alpacaService.router, prefix="/api/alpaca", tags=["alpaca"])



import asyncio
import logging
import os
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import RedirectResponse, JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- Import your routers ----
from .routers import auth, market, portfolio, order, trade, watchlist, transactions
from .services.alpacaService import start_alpaca_feed
# from .services.fyerService import start_fyers_feed
# from broker.mt5_service import start_mt5_feed

# ---- FastAPI App ----
app = FastAPI()

# ---- MongoDB Connection ----
MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client["paper_trading"]

# ---- WebSocket Connections ----
connected_clients = set()

async def broadcast(message: dict):
    """Send tick to all connected WebSocket clients"""
    dead_clients = []
    for ws in connected_clients:
        try:
            await ws.send_json(message)
        except Exception:
            dead_clients.append(ws)

    for ws in dead_clients:
        connected_clients.remove(ws)

# ---- Root Endpoint (GET + HEAD) ----
@app.get("/")
@app.head("/")
async def root():
    return {"message": "Paper Trading Backend is running..."}

# ---- Fyers Login Endpoint ----
@app.get("/fyers/login")
async def fyers_login():
    from broker.fyers_service import CLIENT_ID, REDIRECT_URI
    login_url = (
        f"https://api.fyers.in/api/v2/generate-authcode?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&response_type=code&state=sample"
    )
    return RedirectResponse(login_url)

# ---- Fyers Callback Endpoint ----
@app.get("/fyers/callback")
async def fyers_callback(request: Request):
    from broker.fyers_service import exchange_auth_code
    code = request.query_params.get("code")
    if not code:
        return JSONResponse({"error": "Missing code"}, status_code=400)
    try:
        token_data = await exchange_auth_code(code)
        return {"msg": "Token saved successfully", "token": token_data}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# ---- Register Routers ----
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(market.router, prefix="/api/market", tags=["market"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(order.router, prefix="/api/orders", tags=["orders"])
app.include_router(trade.router, prefix="/api/trades", tags=["trades"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])

# ---- Market Data WebSocket ----
@app.websocket("/ws/market")
async def market_ws(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        connected_clients.remove(websocket)

# ---- Startup Tasks ----
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Paper Trading Backend...")
    asyncio.create_task(start_alpaca_feed(broadcast))
    # asyncio.create_task(start_fyers_feed(broadcast))
    # asyncio.create_task(start_mt5_feed(broadcast, db))
    logger.info("✅ All feeds launched")

    # Attach global error handler
    def handle_exception(loop, context):
        msg = context.get("exception", context["message"])
        logger.error(f"Unhandled exception: {msg}")

    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)

# ---- Include Alpaca Router ----
from .services import alpacaService
app.include_router(alpacaService.router, prefix="/api/alpaca", tags=["alpaca"])

# ---- Render entrypoint ----
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
