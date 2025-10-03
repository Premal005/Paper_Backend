# import asyncio
# import logging
# import os
# from fastapi import FastAPI, WebSocket, Request
# from fastapi.responses import RedirectResponse, JSONResponse
# from motor.motor_asyncio import AsyncIOMotorClient
# from dotenv import load_dotenv
# # from typing import Dict, List


# # Load environment variables
# load_dotenv()
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # ---- Import your routers ----
# from .routers import auth, market, portfolio, order, trade, watchlist, transactions
# from .services.alpacaService import start_alpaca_feed
# # from .services.fyerService import start_fyers_feed
# # from broker.mt5_service import start_mt5_feed

# # ---- FastAPI App ----
# app = FastAPI()

# # ---- MongoDB Connection ----
# MONGO_URI = os.getenv("MONGO_URI")
# client = AsyncIOMotorClient(MONGO_URI)
# db = client["paper_trading"]

# # ---- WebSocket Connections ----
# # ---- WebSocket Connections ----
# connected_clients: set[WebSocket] = set()

# async def broadcast(message: dict):
#     """Send tick to all connected WebSocket clients"""
#     if not connected_clients:
#         return  # skip if no clients
#     dead_clients = set()
#     for ws in connected_clients:
#         try:
#             await ws.send_json(message)
#         except Exception:
#             dead_clients.add(ws)
#     connected_clients.difference_update(dead_clients)






# @app.websocket("/ws/market")
# async def market_ws(ws: WebSocket):
#     """WebSocket for streaming market ticks to clients"""
#     await ws.accept()
#     connected_clients.add(ws)
#     logger.info(f"🟢 Client connected: {ws.client}")

#     # Send initial welcome
#     await ws.send_json({"msg": "✅ Connected to Market WS"})

#     try:
#         while True:
#             # Wait for incoming pings or just keep connection alive
#             try:
#                 # Wait 1 sec for client message (if none, timeout)
#                 await ws.receive_text()
#             except Exception:
#                 await asyncio.sleep(1)  # no message, keep alive
#     except Exception:
#         logger.info(f"🔴 Client disconnected: {ws.client}")
#     finally:
#         connected_clients.discard(ws)
#         await ws.close()


# # ---- Register Routers ----
# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# app.include_router(market.router, prefix="/api/market", tags=["market"])
# app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
# app.include_router(order.router, prefix="/api/orders", tags=["orders"])
# app.include_router(trade.router, prefix="/api/trades", tags=["trades"])
# app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
# app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])





















































# # ---- Root Endpoint (GET + HEAD) ----
# @app.get("/")
# @app.head("/")
# async def root():
#     return {"message": "Paper Trading Backend is running..."}

# # ---- Fyers Login Endpoint ----
# @app.get("/fyers/login")
# async def fyers_login():
#     from broker.fyers_service import CLIENT_ID, REDIRECT_URI
#     login_url = (
#         f"https://api.fyers.in/api/v2/generate-authcode?client_id={CLIENT_ID}"
#         f"&redirect_uri={REDIRECT_URI}&response_type=code&state=sample"
#     )
#     return RedirectResponse(login_url)

# # ---- Fyers Callback Endpoint ----
# @app.get("/fyers/callback")
# async def fyers_callback(request: Request):
#     from broker.fyers_service import exchange_auth_code
#     code = request.query_params.get("code")
#     if not code:
#         return JSONResponse({"error": "Missing code"}, status_code=400)
#     try:
#         token_data = await exchange_auth_code(code)
#         return {"msg": "Token saved successfully", "token": token_data}
#     except Exception as e:
#         return JSONResponse({"error": str(e)}, status_code=500)



# # ---- Market Data WebSocket ----
# # @app.websocket("/ws/market")
# # async def market_ws(websocket: WebSocket):
# #     await websocket.accept()
# #     connected_clients.add(websocket)
# #     try:
# #         while True:
# #             await websocket.receive_text()
# #     except Exception:
# #         connected_clients.remove(websocket)

# # @app.websocket("/ws/market")
# # async def market_ws(ws: WebSocket):
# #     await ws.accept()
# #     connected_clients.add(ws)
# #     await ws.send_json({"msg": "✅ Connected to Market WS"})

# #     try:
# #         while True:
# #             await asyncio.sleep(10)  # keeps connection alive
# #     except Exception:
# #         connected_clients.remove(ws)
# #         await ws.close()

# from .services import alpacaService
# app.include_router(alpacaService.router, prefix="/api/alpaca", tags=["alpaca"])

# # ---- Startup Tasks ----
# @app.on_event("startup")
# async def startup_event():
#     logger.info("🚀 Starting Paper Trading Backend...")
#     asyncio.create_task(alpacaService.start_alpaca_feed(broadcast))
#     # asyncio.create_task(start_fyers_feed(broadcast))
#     # asyncio.create_task(start_mt5_feed(broadcast, db))
#     logger.info("✅ All feeds launched")

#     # Attach global error handler
#     def handle_exception(loop, context):
#         msg = context.get("exception", context["message"])
#         logger.error(f"Unhandled exception: {msg}")

#     loop = asyncio.get_event_loop()
#     loop.set_exception_handler(handle_exception)

# # ---- Include Alpaca Router ----

# # ---- Render entrypoint ----
# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.environ.get("PORT", 8000))
#     uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
# import asyncio
# import logging
# import os
# from fastapi import FastAPI, WebSocket, Request
# from fastapi.responses import RedirectResponse, JSONResponse
# from motor.motor_asyncio import AsyncIOMotorClient
# from dotenv import load_dotenv
# from fastapi.middleware.cors import CORSMiddleware

# # Load environment variables
# load_dotenv()
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # ---- Import routers and services ----
# from .routers import auth, market, portfolio, order, trade, watchlist, transactions
# from .services import alpacaService

# # ---- FastAPI App ----
# app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # <-- you can list specific origins later
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# # ---- MongoDB Connection ----
# MONGO_URI = os.getenv("MONGO_URI")
# client = AsyncIOMotorClient(MONGO_URI)
# db = client["paper_trading"]

# # ---- WebSocket Connections ----
# connected_clients: set[WebSocket] = set()
# subscribed_symbols: set[str] = {"AAPL", "RELI", "SPY"}  # default symbols
# alpaca_ws = None  # will be set when Alpaca WS connects


# async def broadcast(message: dict):
#     """Send tick to all connected WebSocket clients"""
#     if not connected_clients:
#         return
#     dead_clients = set()
#     for ws in connected_clients:
#         try:
#             await ws.send_json(message)
#         except Exception:
#             dead_clients.add(ws)
#     connected_clients.difference_update(dead_clients)


# @app.websocket("/ws/market")
# async def market_ws(ws: WebSocket):
#     """WebSocket for streaming market ticks + symbol subscriptions"""
#     global alpaca_ws

#     await ws.accept()
#     connected_clients.add(ws)
#     logger.info(f"🟢 Client connected: {ws.client}")

#     await ws.send_json({"msg": "✅ Connected to Market WS"})

#     try:
#         while True:
#             data = await ws.receive_json()
#             action = data.get("action")
#             symbol = data.get("symbol")

#             if action == "subscribe" and symbol:
#                 symbol = symbol.upper()
#                 if symbol not in subscribed_symbols:
#                     subscribed_symbols.add(symbol)
#                     await ws.send_json({"msg": f"🟢 Subscribing to {symbol}"})
#                     # Tell Alpaca WS to subscribe live
#                     if alpaca_ws:
#                         try:
#                             await alpaca_ws.send_json({
#                                 "action": "subscribe",
#                                 "quotes": [symbol]
#                             })
#                             logger.info(f"✅ Live subscribed {symbol}")
#                         except Exception as e:
#                             logger.warning(f"⚠️ Failed live subscribe {symbol}: {e}")
#             else:
#                 await ws.send_json({"msg": "❌ Invalid request"})

#     except Exception:
#         logger.info(f"🔴 Client disconnected: {ws.client}")
#     finally:
#         connected_clients.discard(ws)
#         await ws.close()


# # ---- Register Routers ----
# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# app.include_router(market.router, prefix="/api/market", tags=["market"])
# app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
# app.include_router(order.router, prefix="/api/orders", tags=["orders"])
# app.include_router(trade.router, prefix="/api/trades", tags=["trades"])
# app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
# app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
# app.include_router(alpacaService.router, prefix="/api/alpaca", tags=["alpaca"])


# # ---- Root ----
# @app.get("/")
# @app.head("/")
# async def root():
#     return {"message": "Paper Trading Backend is running..."}


# # ---- Fyers Login ----
# @app.get("/fyers/login")
# async def fyers_login():
#     from broker.fyers_service import CLIENT_ID, REDIRECT_URI
#     login_url = (
#         f"https://api.fyers.in/api/v2/generate-authcode?client_id={CLIENT_ID}"
#         f"&redirect_uri={REDIRECT_URI}&response_type=code&state=sample"
#     )
#     return RedirectResponse(login_url)


# @app.get("/fyers/callback")
# async def fyers_callback(request: Request):
#     from broker.fyers_service import exchange_auth_code
#     code = request.query_params.get("code")
#     if not code:
#         return JSONResponse({"error": "Missing code"}, status_code=400)
#     try:
#         token_data = await exchange_auth_code(code)
#         return {"msg": "Token saved successfully", "token": token_data}
#     except Exception as e:
#         return JSONResponse({"error": str(e)}, status_code=500)


# # ---- Startup ----
# @app.on_event("startup")
# async def startup_event():
#     logger.info("🚀 Starting Paper Trading Backend...")

#     async def start_alpaca():
#         # Pass globals so Alpaca WS can update
#         await alpacaService.start_alpaca_feed(
#             broadcast=broadcast,
#             subscribed_symbols=subscribed_symbols,
#             ws_ref=lambda ws: globals().__setitem__("alpaca_ws", ws)
#         )

#     asyncio.create_task(start_alpaca())

#     logger.info("✅ Feeds launched")

#     def handle_exception(loop, context):
#         msg = context.get("exception", context["message"])
#         logger.error(f"Unhandled exception: {msg}")

#     loop = asyncio.get_event_loop()
#     loop.set_exception_handler(handle_exception)


# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.environ.get("PORT", 8000))
#     uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
import asyncio
import json
import logging
import os
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- Import routers and services ----
from .routers import auth, market, portfolio, order, trade, watchlist, transactions
from .services import alpacaService

# ---- FastAPI App ----
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- MongoDB Connection ----
MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client["paper_trading"]

# ---- WebSocket Connections ----
connected_clients: set[WebSocket] = set()
subscribed_symbols: set[str] = {"AAPL", "RELI", "SPY"}  # default symbols
alpaca_ws = None  # will be set when Alpaca WS connects


async def broadcast(message: dict):
    """Send tick to all connected WebSocket clients"""
    if not connected_clients:
        return
    dead_clients = set()
    for ws in connected_clients:
        try:
            await ws.send_json(message)
        except Exception:
            dead_clients.add(ws)
    connected_clients.difference_update(dead_clients)


@app.websocket("/ws/market")
async def market_ws(ws: WebSocket):
    """WebSocket for streaming market ticks + dynamic symbol subscriptions"""
    global alpaca_ws

    await ws.accept()
    connected_clients.add(ws)
    logger.info(f"🟢 Client connected: {ws.client}")

    await ws.send_json({"msg": "✅ Connected to Market WS"})

    try:
        while True:
            data = await ws.receive_json()
            action = data.get("action")
            symbol = data.get("symbol")

            if action == "subscribe" and symbol:
                symbol = symbol.upper()
                if symbol not in subscribed_symbols:
                    subscribed_symbols.add(symbol)
                    await ws.send_json({"msg": f"🟢 Subscribing to {symbol}"})
                    # Tell Alpaca WS to subscribe live
                    if alpaca_ws:
                        try:
                            await alpaca_ws.send(json.dumps({
                                "action": "subscribe",
                                "quotes": [symbol]
                            }))
                            logger.info(f"✅ Live subscribed {symbol}")
                        except Exception as e:
                            logger.warning(f"⚠️ Failed live subscribe {symbol}: {e}")
            else:
                await ws.send_json({"msg": "❌ Invalid request"})

    except Exception:
        logger.info(f"🔴 Client disconnected: {ws.client}")
    finally:
        connected_clients.discard(ws)
        await ws.close()


# ---- Register Routers ----
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(market.router, prefix="/api/market", tags=["market"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(order.router, prefix="/api/orders", tags=["orders"])
app.include_router(trade.router, prefix="/api/trades", tags=["trades"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(alpacaService.router, prefix="/api/alpaca", tags=["alpaca"])


# ---- Root ----
@app.get("/")
@app.head("/")
async def root():
    return {"message": "Paper Trading Backend is running..."}


# ---- Fyers Login ----
@app.get("/fyers/login")
async def fyers_login():
    from broker.fyers_service import CLIENT_ID, REDIRECT_URI
    login_url = (
        f"https://api.fyers.in/api/v2/generate-authcode?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&response_type=code&state=sample"
    )
    return RedirectResponse(login_url)


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


# ---- Startup ----
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Paper Trading Backend...")

    async def start_alpaca():
        # Pass globals so Alpaca WS can update
        await alpacaService.start_alpaca_feed(
            broadcast=broadcast,
            subscribed_symbols=subscribed_symbols,
            ws_ref=lambda ws: globals().__setitem__("alpaca_ws", ws)
        )

    asyncio.create_task(start_alpaca())

    logger.info("✅ Feeds launched")

    def handle_exception(loop, context):
        msg = context.get("exception", context["message"])
        logger.error(f"Unhandled exception: {msg}")

    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
